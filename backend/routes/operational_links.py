"""
routes/operational_links.py — Phase V-Prelude · Wave 1 · Substrate.

The single shared substrate for every cross-artifact relationship from
V-Prelude through V.6+.  See `/app/memory/OPERATIONAL_LINKING_RULES.md`
for the full doctrine — this module implements §1 – §11 of that doc
verbatim. Read it before touching this file.

Doctrine recap (read OPERATIONAL_LINKING_RULES.md for full text):
  * Links are operational CONTEXT, never ownership.
  * Every row carries 11 audit fields — no exceptions.
  * Mutations never alter the source/target artifact.
  * Hard DELETE is forbidden — status flips only (active · archived ·
    voided · superseded).
  * Single canonical direction; reciprocals are display-only.
  * Project-scoped: every link carries denormalized `project_id`.
  * Visibility is role-aware and explicit (never inheritable).
  * TRUST-TIME-1 compliant timestamps (tz-aware ISO with Z suffix).
  * Mongo `_id` excluded from every response.

This module exposes the API surface from §11:
    POST   /api/operational-links
    GET    /api/operational-links?project_id=...
    GET    /api/operational-links/:id
    PATCH  /api/operational-links/:id/status
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


# ── Closed enums (doctrine OPERATIONAL_LINKING_RULES.md §3 + §4) ──────

ARTIFACT_TYPES = {
    "daily_report",
    "incident",
    "inspection",
    "photo",
    "attachment",
    "field_note",
    "operational_constraint",
    "future_rfi",
    "future_schedule_activity",
    "future_schedule_import",
    "future_external_response",
    "safety_record",
    "dispatch_event",
    "equipment_record",
    "employee_record",
    "project",
    "job",
    "meeting",
    "qa_qc_record",
    "trench_record",
    "jha_record",
    # ── Phase V.1 ODR substrate (registered M0.1 · 2026-05-29) ──
    "odr",                     # the ODR record itself
    "odr_section_event",       # append-only field-level transition
    "odr_amendment",           # Super+ amendment row (post 24h window)
    "odr_attachment",          # delivery/haul/CEI/FAA/etc. ticket
    "odr_translation_event",   # bilingual normalization audit
    "odr_preload_attempt",     # public-link continuity gate evaluation
    "production_segment",      # one operation within an ODR
    "work_area",               # geographic sub-area of a project
    "material_event",          # material delivery / consumption / waste
    "safety_event",            # one safety event within an ODR safety block
    # ── Phase V.1 · M1 · Legacy Archive Bridge (2026-05-29) ─────
    # `legacy_daily_report` is TARGET-ONLY per Option C approval.
    # New ODR records may reference legacy archived rows; legacy rows
    # may NEVER become active source artifacts. Enforced by
    # TARGET_ONLY_ARTIFACT_TYPES below + write-time validation.
    "legacy_daily_report",
}

# Doctrine: OPERATIONAL_LINKS_BRIDGE_CERTIFICATION.md
# These artifact types may appear ONLY as `target_type` on an
# operational_link — never as `source_type`. They represent frozen
# historical or system-of-record substrates where mutation is forbidden.
TARGET_ONLY_ARTIFACT_TYPES = {
    "legacy_daily_report",
}

# Canonical relationship directions (storage layer). Inverse views
# (`blocked_by`, `impacted_by`, `escalated_to`) are display-only —
# rejected at write time.
CANONICAL_RELATIONSHIPS = {
    "references",
    "caused_by",
    "blocks",
    "supports",
    "evidence_for",
    "resulted_in",
    "related_to",
    "supersedes",
    "resolved_by",
    "escalated_from",
    "impacts",
    "documents",
    "response_to",
    "generated_from",
}

FORBIDDEN_INVERSE_RELATIONSHIPS = {
    "blocked_by",
    "impacted_by",
    "escalated_to",
}

VISIBILITY_SCOPES = {
    "internal",
    "pm-scope",
    "safety-scope",
    "dispatch-scope",
    "hr-scope",
    "cross-portal-read",
    "external-shared",
    "audit-only",
}

STATUS_VALUES = {"active", "archived", "voided", "superseded"}

# Status transition matrix (doctrine §10). active → any; voided is
# reversible only by admin attestation (enforced via a strict gate
# inside the PATCH endpoint).
ALLOWED_STATUS_TRANSITIONS = {
    "active": {"archived", "voided", "superseded"},
    "archived": {"active"},          # reopen
    "voided": {"active"},             # admin attestation enforced
    "superseded": set(),               # terminal
}


# ── Pydantic models ──────────────────────────────────────────────────


class OperationalLinkCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_type: str
    source_id: str
    target_type: str
    target_id: str
    relationship: str
    project_id: str
    reason: str = Field(default="", max_length=280)
    visibility: str = "internal"


class OperationalLinkOut(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    source_type: str
    source_id: str
    target_type: str
    target_id: str
    relationship: str
    reason: str
    visibility: str
    project_id: str
    status: str
    created_at: str
    created_by: str
    status_changed_at: Optional[str] = None
    status_changed_by: Optional[str] = None


class StatusPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: str
    reason: Optional[str] = Field(default=None, max_length=280)


# ── Helpers ──────────────────────────────────────────────────────────


def _utc_iso(dt: Optional[datetime] = None) -> str:
    """TRUST-TIME-1 — emit explicit `Z`-suffixed UTC ISO."""
    d = dt or datetime.now(timezone.utc)
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.") + \
        f"{d.microsecond // 1000:03d}Z"


def _actor_id(actor: Dict[str, Any]) -> str:
    """Stable, audit-safe identifier for the calling actor."""
    if not isinstance(actor, dict):
        return "system"
    return (
        actor.get("id")
        or actor.get("user_id")
        or actor.get("email")
        or actor.get("name")
        or actor.get("_actor")
        or "unknown"
    )


def _to_out(doc: Dict[str, Any]) -> OperationalLinkOut:
    """Project Mongo doc → response model (excludes `_id`)."""
    return OperationalLinkOut(
        id=doc["id"],
        source_type=doc["source_type"],
        source_id=doc["source_id"],
        target_type=doc["target_type"],
        target_id=doc["target_id"],
        relationship=doc["relationship"],
        reason=doc.get("reason", "") or "",
        visibility=doc.get("visibility", "internal"),
        project_id=doc["project_id"],
        status=doc.get("status", "active"),
        created_at=doc["created_at"],
        created_by=doc.get("created_by", "unknown"),
        status_changed_at=doc.get("status_changed_at"),
        status_changed_by=doc.get("status_changed_by"),
    )


def _validate_relationship(body: OperationalLinkCreate) -> None:
    if body.source_type not in ARTIFACT_TYPES:
        raise HTTPException(422, f"Invalid source_type: {body.source_type}")
    if body.target_type not in ARTIFACT_TYPES:
        raise HTTPException(422, f"Invalid target_type: {body.target_type}")
    # M1 · Option C · target-only artifact gate.
    # `legacy_daily_report` (and any future frozen substrate) may not
    # appear as the source side of a new link. Historical records never
    # generate new outbound chronology — only inbound references.
    if body.source_type in TARGET_ONLY_ARTIFACT_TYPES:
        raise HTTPException(
            422,
            f"'{body.source_type}' is a target-only archive artifact "
            "and cannot be the source of a new operational link "
            "(M1 · Option C · OPERATIONAL_LINKS_BRIDGE_CERTIFICATION.md).",
        )
    if body.relationship in FORBIDDEN_INVERSE_RELATIONSHIPS:
        raise HTTPException(
            422,
            f"'{body.relationship}' is a display-only inverse — store the "
            "canonical direction instead (OPERATIONAL_LINKING_RULES.md §6).",
        )
    if body.relationship not in CANONICAL_RELATIONSHIPS:
        raise HTTPException(422, f"Unknown relationship: {body.relationship}")
    if body.visibility not in VISIBILITY_SCOPES:
        raise HTTPException(422, f"Invalid visibility: {body.visibility}")
    if not body.source_id or not body.target_id or not body.project_id:
        raise HTTPException(422, "source_id, target_id, project_id required")
    if body.source_type == body.target_type and body.source_id == body.target_id:
        raise HTTPException(
            422,
            "Self-link forbidden — source and target may not be identical.",
        )


async def _check_circular_resulted_in(
    db, body: OperationalLinkCreate,
) -> None:
    """Doctrine §10 — A `resulted_in` B AND B `resulted_in` A forbidden."""
    if body.relationship != "resulted_in":
        return
    existing = await db.operational_links.find_one(
        {
            "source_type": body.target_type,
            "source_id": body.target_id,
            "target_type": body.source_type,
            "target_id": body.source_id,
            "relationship": "resulted_in",
            "status": {"$in": ["active", "archived"]},
        },
        {"_id": 0, "id": 1},
    )
    if existing:
        raise HTTPException(
            409,
            "Circular resulted_in relationship forbidden "
            "(OPERATIONAL_LINKING_RULES.md §10).",
        )


# ── Indexes ──────────────────────────────────────────────────────────


async def ensure_operational_links_indexes(db) -> None:
    await db.operational_links.create_index("id", unique=True)
    await db.operational_links.create_index(
        [("project_id", 1), ("created_at", -1)]
    )
    await db.operational_links.create_index(
        [("source_type", 1), ("source_id", 1)]
    )
    await db.operational_links.create_index(
        [("target_type", 1), ("target_id", 1)]
    )
    await db.operational_links.create_index("status")


# ── Router factory ────────────────────────────────────────────────────


def build_operational_links_router(
    db,
    require_actor: Callable[..., Awaitable[Dict[str, Any]]],
    require_admin: Callable[..., Awaitable[Any]],
) -> APIRouter:
    """`require_actor` resolves any portal token → actor dict; admin gate
    is required for status PATCH (archive · void · unvoid)."""

    router = APIRouter(prefix="/api/operational-links", tags=["operational-links"])

    @router.post("", response_model=OperationalLinkOut)
    async def create_link(
        body: OperationalLinkCreate,
        actor: Dict[str, Any] = Depends(require_actor),
    ) -> OperationalLinkOut:
        _validate_relationship(body)
        await _check_circular_resulted_in(db, body)

        now_iso = _utc_iso()
        doc = {
            "id": str(uuid.uuid4()),
            "source_type": body.source_type,
            "source_id": body.source_id,
            "target_type": body.target_type,
            "target_id": body.target_id,
            "relationship": body.relationship,
            "reason": (body.reason or "").strip()[:280],
            "visibility": body.visibility,
            "project_id": body.project_id,
            "status": "active",
            "status_changed_at": None,
            "status_changed_by": None,
            "created_at": now_iso,
            "created_by": _actor_id(actor),
        }

        # supersedes side-effect (doctrine §3): cascade
        # `target.status = superseded` only when the relationship is
        # explicitly `supersedes`. This is the ONLY mutation allowed.
        if body.relationship == "supersedes":
            await db.operational_links.update_many(
                {
                    "source_type": body.target_type,
                    "source_id": body.target_id,
                    "status": "active",
                },
                {
                    "$set": {
                        "status": "superseded",
                        "status_changed_at": now_iso,
                        "status_changed_by": _actor_id(actor),
                    }
                },
            )

        await db.operational_links.insert_one(doc)
        # Mongo mutates `doc` to include `_id` — pop it before returning.
        doc.pop("_id", None)
        return _to_out(doc)

    @router.get("", response_model=List[OperationalLinkOut])
    async def list_links(
        project_id: str = Query(..., min_length=1),
        source_type: Optional[str] = Query(default=None),
        source_id: Optional[str] = Query(default=None),
        target_type: Optional[str] = Query(default=None),
        target_id: Optional[str] = Query(default=None),
        relationship: Optional[str] = Query(default=None),
        status: Optional[str] = Query(default=None),
        limit: int = Query(default=200, ge=1, le=500),
        actor: Dict[str, Any] = Depends(require_actor),
    ) -> List[OperationalLinkOut]:
        q: Dict[str, Any] = {"project_id": project_id}
        if source_type:
            q["source_type"] = source_type
        if source_id:
            q["source_id"] = source_id
        if target_type:
            q["target_type"] = target_type
        if target_id:
            q["target_id"] = target_id
        if relationship:
            q["relationship"] = relationship
        if status:
            if status not in STATUS_VALUES:
                raise HTTPException(422, f"Invalid status filter: {status}")
            q["status"] = status

        # Visibility filter (doctrine §5) — `audit-only` never surfaces
        # to non-admin actors.
        if actor.get("_actor") != "admin":
            q["visibility"] = {"$ne": "audit-only"}

        cur = db.operational_links.find(q, {"_id": 0}).sort(
            "created_at", -1
        ).limit(limit)
        rows = await cur.to_list(length=limit)
        return [_to_out(r) for r in rows]

    @router.get("/{link_id}", response_model=OperationalLinkOut)
    async def get_link(
        link_id: str,
        actor: Dict[str, Any] = Depends(require_actor),
    ) -> OperationalLinkOut:
        doc = await db.operational_links.find_one({"id": link_id}, {"_id": 0})
        if not doc:
            raise HTTPException(404, "Link not found")
        if (
            doc.get("visibility") == "audit-only"
            and actor.get("_actor") != "admin"
        ):
            raise HTTPException(404, "Link not found")
        return _to_out(doc)

    @router.patch("/{link_id}/status", response_model=OperationalLinkOut)
    async def patch_status(
        link_id: str,
        patch: StatusPatch,
        _admin: Any = Depends(require_admin),
    ) -> OperationalLinkOut:
        if patch.status not in STATUS_VALUES:
            raise HTTPException(422, f"Invalid target status: {patch.status}")
        doc = await db.operational_links.find_one({"id": link_id}, {"_id": 0})
        if not doc:
            raise HTTPException(404, "Link not found")
        current = doc.get("status", "active")
        if current == patch.status:
            return _to_out(doc)
        allowed = ALLOWED_STATUS_TRANSITIONS.get(current, set())
        if patch.status not in allowed:
            raise HTTPException(
                409,
                f"Status transition forbidden: {current} → {patch.status} "
                "(OPERATIONAL_LINKING_RULES.md §10).",
            )
        now_iso = _utc_iso()
        actor_id = "admin"  # admin gate already enforced
        update: Dict[str, Any] = {
            "status": patch.status,
            "status_changed_at": now_iso,
            "status_changed_by": actor_id,
        }
        if patch.reason:
            update["status_reason"] = patch.reason.strip()[:280]
        await db.operational_links.update_one(
            {"id": link_id}, {"$set": update}
        )
        doc.update(update)
        return _to_out(doc)

    return router


__all__ = [
    "build_operational_links_router",
    "ensure_operational_links_indexes",
    "ARTIFACT_TYPES",
    "TARGET_ONLY_ARTIFACT_TYPES",
    "CANONICAL_RELATIONSHIPS",
    "FORBIDDEN_INVERSE_RELATIONSHIPS",
    "VISIBILITY_SCOPES",
    "STATUS_VALUES",
]
