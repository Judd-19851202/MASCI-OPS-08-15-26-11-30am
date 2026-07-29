"""
routes/photo_governance.py — Phase V-Prelude · Wave 1 · Substrate.

Photo Governance — see `/app/memory/PHOTO_GOVERNANCE_STANDARD.md`.

Wave 1 substrate ONLY. We do NOT touch the upload pipeline (TRUST-1
IDB queue stays as-is) or the existing /api/admin/job-photos library
indexer. We add the THIN governance layer:

  * PATCH /api/photos/:id              — caption, tags, operational_context,
                                          discipline (operator-overridable)
  * POST  /api/photos/:id/link         — explicit link to another artifact
                                          (creates an operational_links row;
                                          canonical direction `evidence_for`
                                          when target is a constraint/incident)
  * GET   /api/photos/:id/governance   — read-only governance metadata
                                          (links, tags, age, capture-vs-upload
                                          delta). NO blob bytes.

Doctrine guards:
  * NO new collection. Governance metadata lives on the existing
    `job_photos` row as a thin extension (`governance` subdoc).
  * Linkage is recorded in `operational_links` — single source of truth.
  * NO facial recognition. NO GPS render. NO AI auto-tag.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from lib.enterprise_governance import require_governed_action

logger = logging.getLogger(__name__)

OPERATIONAL_CONTEXT_VALUES = {
    "field-evidence",
    "close-out",
    "before-and-after",
    "safety",
    "qc",
    "other",
}

DISCIPLINES = {
    "utilities",
    "access",
    "MOT",
    "survey",
    "QC",
    "FAA",
    "subcontractor",
    "general",
    "safety",
    "other",
}

MAX_TAGS = 8
MAX_TAG_LEN = 32


# ── Pydantic models ──────────────────────────────────────────────────


class PhotoPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    caption: Optional[str] = Field(default=None, max_length=280)
    tags: Optional[List[str]] = None
    discipline: Optional[str] = None
    operational_context: Optional[str] = None


class PhotoLinkRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    target_type: str
    target_id: str
    relationship: str = "evidence_for"
    project_id: str
    reason: str = Field(default="", max_length=280)
    visibility: str = "internal"


class PhotoGovernanceOut(BaseModel):
    model_config = ConfigDict(extra="forbid")
    photo_id: str
    caption: str = ""
    tags: List[str] = []
    discipline: Optional[str] = None
    operational_context: Optional[str] = None
    project_id: Optional[str] = None
    parent_kind: Optional[str] = None
    parent_id: Optional[str] = None
    uploaded_at: Optional[str] = None
    captured_at: Optional[str] = None
    capture_upload_delta_minutes: Optional[int] = None
    linked_count: int = 0
    linked_to: List[Dict[str, str]] = []


# ── Helpers ──────────────────────────────────────────────────────────


def _utc_iso(dt: Optional[datetime] = None) -> str:
    d = dt or datetime.now(timezone.utc)
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.") + \
        f"{d.microsecond // 1000:03d}Z"


def _actor_id(actor: Dict[str, Any]) -> str:
    return (
        (actor or {}).get("id")
        or (actor or {}).get("user_id")
        or (actor or {}).get("email")
        or (actor or {}).get("name")
        or (actor or {}).get("_actor")
        or "unknown"
    )


def _governed_actor(actor: Dict[str, Any]) -> Dict[str, Any]:
    raw = dict(actor or {})
    role = str(raw.get("_actor") or raw.get("role") or "").strip().lower()
    role_aliases = {
        "fl": "field_leadership",
        "leadership": "executive",
        "dispatcher": "dispatch",
        "shop manager": "shop",
        "project manager": "pm",
        "safety": "safety",
        "hr": "hr",
        "admin": "admin",
    }
    role = role_aliases.get(role, role)
    raw.setdefault("id", _actor_id(actor))
    raw.setdefault("email", f"{role or 'operator'}@photo-governance.local")
    raw["_actor"] = role or "admin"
    raw["role"] = role or "admin"
    return raw


def _sanitize_tags(tags: List[str]) -> List[str]:
    cleaned: List[str] = []
    seen = set()
    for t in tags or []:
        s = str(t or "").strip().lower()[:MAX_TAG_LEN]
        if not s or s in seen:
            continue
        seen.add(s)
        cleaned.append(s)
        if len(cleaned) >= MAX_TAGS:
            break
    return cleaned


def _parse_iso(s: str) -> Optional[datetime]:
    try:
        ts = s.replace("Z", "+00:00") if s.endswith("Z") else s
        d = datetime.fromisoformat(ts)
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d
    except Exception:
        return None


# ── Indexes ──────────────────────────────────────────────────────────


async def ensure_photo_governance_indexes(db) -> None:
    """`job_photos` already exists with its own indexes (see job_photos.py).
    We only add a thin index for the governance.tags array for filtering."""
    try:
        await db.job_photos.create_index("governance.tags")
    except Exception:  # noqa: BLE001
        # Index already exists or collection not yet populated — safe.
        pass


# ── Router factory ────────────────────────────────────────────────────


def build_photo_governance_router(
    db,
    require_actor: Callable[..., Awaitable[Dict[str, Any]]],
) -> APIRouter:
    router = APIRouter(prefix="/api/photos", tags=["photo-governance"])

    async def _require_photo_access(
        *,
        actor: Dict[str, Any],
        request: Request,
        action_key: str,
        photo_doc: Dict[str, Any],
    ) -> None:
        await require_governed_action(
            db,
            actor=_governed_actor(actor),
            action_key=action_key,
            resource_type="photo_governance",
            resource={
                "id": photo_doc.get("photo_id") or photo_doc.get("id") or "photo",
                "photo_id": photo_doc.get("photo_id") or photo_doc.get("id") or "photo",
                "project_number": photo_doc.get("project_number") or photo_doc.get("project_id") or "",
                "source_kind": photo_doc.get("source_kind") or photo_doc.get("parent_kind") or "",
            },
            requested_context={
                "module": "photo_governance",
                "project_number": photo_doc.get("project_number") or photo_doc.get("project_id") or "",
                "photo_id": photo_doc.get("photo_id") or photo_doc.get("id") or "photo",
            },
            request=request,
        )

    @router.patch("/{photo_id}", response_model=PhotoGovernanceOut)
    async def patch_photo(
        photo_id: str,
        body: PhotoPatch,
        request: Request,
        actor: Dict[str, Any] = Depends(require_actor),
    ) -> PhotoGovernanceOut:
        if body.discipline is not None and body.discipline not in DISCIPLINES:
            raise HTTPException(422, f"Invalid discipline: {body.discipline}")
        if (
            body.operational_context is not None
            and body.operational_context not in OPERATIONAL_CONTEXT_VALUES
        ):
            raise HTTPException(
                422,
                f"Invalid operational_context: {body.operational_context}",
            )
        existing = await db.job_photos.find_one(
            {"photo_id": photo_id}, {"_id": 0}
        )
        if not existing:
            raise HTTPException(404, "Photo not found")
        await _require_photo_access(
            actor=actor,
            request=request,
            action_key="photo_governance.manage",
            photo_doc=existing,
        )

        gov = existing.get("governance", {}) or {}
        if body.caption is not None:
            gov["caption"] = body.caption.strip()[:280]
        if body.tags is not None:
            gov["tags"] = _sanitize_tags(body.tags)
        if body.discipline is not None:
            gov["discipline"] = body.discipline
        if body.operational_context is not None:
            gov["operational_context"] = body.operational_context
        gov["updated_at"] = _utc_iso()
        gov["updated_by"] = _actor_id(actor)

        await db.job_photos.update_one(
            {"photo_id": photo_id},
            {"$set": {"governance": gov}},
        )
        existing["governance"] = gov
        return await _build_governance_out(db, existing)

    @router.post("/{photo_id}/link", response_model=Dict[str, Any])
    async def link_photo(
        photo_id: str,
        body: PhotoLinkRequest,
        request: Request,
        actor: Dict[str, Any] = Depends(require_actor),
    ) -> Dict[str, Any]:
        # Verify the photo exists. We do NOT mutate it — the linkage is
        # recorded in operational_links per doctrine §1.
        existing = await db.job_photos.find_one(
            {"photo_id": photo_id}, {"_id": 0}
        )
        if not existing:
            raise HTTPException(404, "Photo not found")
        await _require_photo_access(
            actor=actor,
            request=request,
            action_key="photo_governance.manage",
            photo_doc=existing,
        )

        # Import lazily to avoid circular import on router build.
        from routes.operational_links import (
            ARTIFACT_TYPES, CANONICAL_RELATIONSHIPS,
            FORBIDDEN_INVERSE_RELATIONSHIPS, VISIBILITY_SCOPES,
        )
        if body.target_type not in ARTIFACT_TYPES:
            raise HTTPException(422, f"Invalid target_type: {body.target_type}")
        if body.relationship in FORBIDDEN_INVERSE_RELATIONSHIPS:
            raise HTTPException(422, "Display-only inverse rejected.")
        if body.relationship not in CANONICAL_RELATIONSHIPS:
            raise HTTPException(422, f"Invalid relationship: {body.relationship}")
        if body.visibility not in VISIBILITY_SCOPES:
            raise HTTPException(422, f"Invalid visibility: {body.visibility}")

        now_iso = _utc_iso()
        doc = {
            "id": str(uuid.uuid4()),
            "source_type": "photo",
            "source_id": photo_id,
            "target_type": body.target_type,
            "target_id": body.target_id,
            "relationship": body.relationship,
            "reason": body.reason.strip()[:280],
            "visibility": body.visibility,
            "project_id": body.project_id,
            "status": "active",
            "status_changed_at": None,
            "status_changed_by": None,
            "created_at": now_iso,
            "created_by": _actor_id(actor),
        }
        await db.operational_links.insert_one(doc)
        doc.pop("_id", None)
        return {"ok": True, "link": doc}

    @router.get("/{photo_id}/governance", response_model=PhotoGovernanceOut)
    async def get_governance(
        photo_id: str,
        request: Request,
        actor: Dict[str, Any] = Depends(require_actor),  # noqa: ARG001
    ) -> PhotoGovernanceOut:
        existing = await db.job_photos.find_one(
            {"photo_id": photo_id}, {"_id": 0}
        )
        if not existing:
            raise HTTPException(404, "Photo not found")
        await _require_photo_access(
            actor=actor,
            request=request,
            action_key="photo_governance.read",
            photo_doc=existing,
        )
        return await _build_governance_out(db, existing)

    return router


async def _build_governance_out(
    db, photo_doc: Dict[str, Any],
) -> PhotoGovernanceOut:
    photo_id = photo_doc.get("photo_id") or photo_doc.get("id") or ""
    gov = photo_doc.get("governance", {}) or {}

    # Compute capture vs upload delta in minutes.
    uploaded_at = photo_doc.get("uploaded_at") or photo_doc.get("captured_at")
    captured_at = photo_doc.get("captured_at")
    delta_min: Optional[int] = None
    if uploaded_at and captured_at:
        u, c = _parse_iso(uploaded_at), _parse_iso(captured_at)
        if u and c:
            delta_min = int(round(abs((u - c).total_seconds()) / 60))

    # Pull active links involving this photo.
    cur = db.operational_links.find(
        {
            "$or": [
                {"source_type": "photo", "source_id": photo_id, "status": "active"},
                {"target_type": "photo", "target_id": photo_id, "status": "active"},
            ]
        },
        {"_id": 0, "source_type": 1, "source_id": 1, "target_type": 1,
         "target_id": 1, "relationship": 1},
    ).limit(50)
    rows = await cur.to_list(length=50)
    linked_to: List[Dict[str, str]] = []
    for r in rows:
        if r["source_type"] == "photo" and r["source_id"] == photo_id:
            linked_to.append({
                "kind": r["target_type"],
                "id": r["target_id"],
                "relationship": r["relationship"],
            })
        else:
            linked_to.append({
                "kind": r["source_type"],
                "id": r["source_id"],
                "relationship": r["relationship"],
            })

    return PhotoGovernanceOut(
        photo_id=photo_id,
        caption=gov.get("caption", "") or "",
        tags=gov.get("tags", []) or [],
        discipline=gov.get("discipline"),
        operational_context=gov.get("operational_context"),
        project_id=photo_doc.get("project_number") or photo_doc.get("project_id"),
        parent_kind=photo_doc.get("source_kind") or photo_doc.get("parent_kind"),
        parent_id=photo_doc.get("source_id") or photo_doc.get("parent_id"),
        uploaded_at=uploaded_at,
        captured_at=captured_at,
        capture_upload_delta_minutes=delta_min,
        linked_count=len(linked_to),
        linked_to=linked_to,
    )


__all__ = [
    "build_photo_governance_router",
    "ensure_photo_governance_indexes",
    "OPERATIONAL_CONTEXT_VALUES",
    "DISCIPLINES",
]
