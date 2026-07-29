"""
routes/operational_constraints.py — Phase V-Prelude · Wave 1 · Substrate.

Operational blocker memory — see
`/app/memory/OPERATIONAL_CONSTRAINT_FOUNDATION.md` for the full doctrine.

This is NOT scheduling, NOT CPM, NOT predecessor logic. A constraint
records a real-world operational blocker (utility conflict · owner hold ·
access · MOT · survey · QC · FAA · sub delay · other) so the platform
keeps memory of WHY work paused.

Calm rules:
  * Single-red doctrine — only `high` severity renders red.
  * Aging surfaces calmly — `3d` / `8d`, never panic copy.
  * Status changes append to chronology — never overwrite history.
  * TRUST-TIME-1 timestamps everywhere (Z-suffixed UTC ISO).
  * Mongo `_id` excluded from every response.
  * Hard delete forbidden (status "void" instead).
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field

from lib.enterprise_governance import require_governed_action

logger = logging.getLogger(__name__)


# ── Doctrine enums ────────────────────────────────────────────────────

DISCIPLINES = {
    "utilities",
    "access",
    "MOT",
    "survey",
    "QC",
    "FAA",
    "subcontractor",
    "other",
}

KINDS = {
    "utility-conflict",
    "owner-hold",
    "access",
    "MOT",
    "survey",
    "QC-fail",
    "FAA-closure",
    "sub-delay",
    "other",
}

SEVERITIES = {"low", "medium", "high"}
STATUSES = {"open", "monitoring", "resolved", "void"}


# ── Pydantic models ──────────────────────────────────────────────────


class ConstraintCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1, max_length=140)
    discipline: str
    kind: str
    severity: str = "medium"
    owner: str = Field(default="", max_length=200)
    operational_impact: str = Field(default="", max_length=500)
    notes: str = Field(default="", max_length=4000)


class ConstraintPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: Optional[str] = Field(default=None, max_length=140)
    discipline: Optional[str] = None
    kind: Optional[str] = None
    severity: Optional[str] = None
    owner: Optional[str] = Field(default=None, max_length=200)
    operational_impact: Optional[str] = Field(default=None, max_length=500)
    notes: Optional[str] = Field(default=None, max_length=4000)


class ResolveBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    resolution_note: str = Field(..., min_length=1, max_length=500)


class ChronologyEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    at: str
    by: str
    action: str
    note: str = ""


class ConstraintOut(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    project_id: str
    title: str
    discipline: str
    kind: str
    severity: str
    status: str
    owner: str
    operational_impact: str
    notes: str
    chronology: List[ChronologyEvent]
    created_by: str
    created_at: str
    updated_at: str
    resolved_at: Optional[str] = None
    age_days: int = 0


# ── Helpers ──────────────────────────────────────────────────────────


def _utc_iso(dt: Optional[datetime] = None) -> str:
    d = dt or datetime.now(timezone.utc)
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.") + \
        f"{d.microsecond // 1000:03d}Z"


def _actor_id(actor: Dict[str, Any]) -> str:
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


def _governed_actor(actor: Dict[str, Any]) -> Dict[str, Any]:
    raw = dict(actor or {})
    role = str(raw.get("_actor") or raw.get("role") or "").strip().lower()
    role = {
        "fl": "field_leadership",
        "leadership": "executive",
        "dispatcher": "dispatch",
        "shop manager": "shop",
        "project manager": "pm",
        "safety": "safety",
        "hr": "hr",
        "admin": "admin",
    }.get(role, role)
    raw.setdefault("id", _actor_id(actor))
    raw.setdefault("email", f"{role or 'operator'}@constraints.local")
    raw["_actor"] = role or "admin"
    raw["role"] = role or "admin"
    return raw


def _compute_age_days(created_at: str, now: Optional[datetime] = None) -> int:
    try:
        # tolerate both `+00:00` and `Z` suffixes
        ts = created_at.replace("Z", "+00:00") if created_at.endswith("Z") else created_at
        d = datetime.fromisoformat(ts)
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
    except Exception:
        return 0
    n = now or datetime.now(timezone.utc)
    return max(0, (n - d).days)


def _to_out(doc: Dict[str, Any]) -> ConstraintOut:
    return ConstraintOut(
        id=doc["id"],
        project_id=doc["project_id"],
        title=doc.get("title", ""),
        discipline=doc.get("discipline", "other"),
        kind=doc.get("kind", "other"),
        severity=doc.get("severity", "medium"),
        status=doc.get("status", "open"),
        owner=doc.get("owner", "") or "",
        operational_impact=doc.get("operational_impact", "") or "",
        notes=doc.get("notes", "") or "",
        chronology=[ChronologyEvent(**e) for e in doc.get("chronology", [])],
        created_by=doc.get("created_by", "unknown"),
        created_at=doc["created_at"],
        updated_at=doc.get("updated_at", doc["created_at"]),
        resolved_at=doc.get("resolved_at"),
        age_days=_compute_age_days(doc["created_at"]),
    )


def _validate_enums(
    discipline: Optional[str],
    kind: Optional[str],
    severity: Optional[str],
) -> None:
    if discipline is not None and discipline not in DISCIPLINES:
        raise HTTPException(422, f"Invalid discipline: {discipline}")
    if kind is not None and kind not in KINDS:
        raise HTTPException(422, f"Invalid kind: {kind}")
    if severity is not None and severity not in SEVERITIES:
        raise HTTPException(422, f"Invalid severity: {severity}")


# ── Indexes ──────────────────────────────────────────────────────────


async def ensure_operational_constraints_indexes(db) -> None:
    await db.operational_constraints.create_index("id", unique=True)
    await db.operational_constraints.create_index(
        [("project_id", 1), ("status", 1), ("created_at", -1)]
    )
    await db.operational_constraints.create_index("status")


# ── Router factory ────────────────────────────────────────────────────


def build_operational_constraints_router(
    db,
    require_actor: Callable[..., Awaitable[Dict[str, Any]]],
) -> APIRouter:
    router = APIRouter(prefix="/api/constraints", tags=["operational-constraints"])

    async def _require_constraints_access(
        *,
        actor: Dict[str, Any],
        request: Request,
        action_key: str,
        project_id: str,
        constraint_id: str = "",
    ) -> None:
        await require_governed_action(
            db,
            actor=_governed_actor(actor),
            action_key=action_key,
            resource_type="operational_constraint",
            resource={
                "id": constraint_id or project_id or "constraint",
                "project_number": project_id or "",
                "project_id": project_id or "",
            },
            requested_context={
                "module": "operational_constraints",
                "project_number": project_id or "",
                "constraint_id": constraint_id or "",
            },
            request=request,
        )

    @router.post("", response_model=ConstraintOut)
    async def create_constraint(
        body: ConstraintCreate,
        request: Request,
        actor: Dict[str, Any] = Depends(require_actor),
    ) -> ConstraintOut:
        await _require_constraints_access(
            actor=actor,
            request=request,
            action_key="operational_constraints.manage",
            project_id=body.project_id,
        )
        _validate_enums(body.discipline, body.kind, body.severity)

        now_iso = _utc_iso()
        actor_id = _actor_id(actor)
        doc = {
            "id": str(uuid.uuid4()),
            "project_id": body.project_id,
            "title": body.title.strip(),
            "discipline": body.discipline,
            "kind": body.kind,
            "severity": body.severity,
            "status": "open",
            "owner": body.owner.strip(),
            "operational_impact": body.operational_impact.strip(),
            "notes": body.notes.strip(),
            "chronology": [{
                "at": now_iso,
                "by": actor_id,
                "action": "created",
                "note": "",
            }],
            "created_by": actor_id,
            "created_at": now_iso,
            "updated_at": now_iso,
            "resolved_at": None,
        }
        await db.operational_constraints.insert_one(doc)
        doc.pop("_id", None)
        return _to_out(doc)

    @router.get("", response_model=List[ConstraintOut])
    async def list_constraints(
        request: Request,
        project_id: Optional[str] = Query(default=None),
        status: Optional[str] = Query(default=None),
        severity: Optional[str] = Query(default=None),
        discipline: Optional[str] = Query(default=None),
        limit: int = Query(default=200, ge=1, le=500),
        actor: Dict[str, Any] = Depends(require_actor),  # noqa: ARG001
    ) -> List[ConstraintOut]:
        await _require_constraints_access(
            actor=actor,
            request=request,
            action_key="operational_constraints.read",
            project_id=project_id or "",
        )
        q: Dict[str, Any] = {}
        if project_id:
            q["project_id"] = project_id
        if status:
            if status not in STATUSES:
                raise HTTPException(422, f"Invalid status filter: {status}")
            q["status"] = status
        if severity:
            if severity not in SEVERITIES:
                raise HTTPException(422, f"Invalid severity filter: {severity}")
            q["severity"] = severity
        if discipline:
            if discipline not in DISCIPLINES:
                raise HTTPException(422, f"Invalid discipline filter: {discipline}")
            q["discipline"] = discipline
        cur = db.operational_constraints.find(q, {"_id": 0}).sort(
            "created_at", -1
        ).limit(limit)
        rows = await cur.to_list(length=limit)
        return [_to_out(r) for r in rows]

    @router.get("/{constraint_id}", response_model=ConstraintOut)
    async def get_constraint(
        constraint_id: str,
        request: Request,
        actor: Dict[str, Any] = Depends(require_actor),  # noqa: ARG001
    ) -> ConstraintOut:
        doc = await db.operational_constraints.find_one(
            {"id": constraint_id}, {"_id": 0}
        )
        if not doc:
            raise HTTPException(404, "Constraint not found")
        await _require_constraints_access(
            actor=actor,
            request=request,
            action_key="operational_constraints.read",
            project_id=doc.get("project_id") or "",
            constraint_id=constraint_id,
        )
        return _to_out(doc)

    @router.patch("/{constraint_id}", response_model=ConstraintOut)
    async def patch_constraint(
        constraint_id: str,
        body: ConstraintPatch,
        request: Request,
        actor: Dict[str, Any] = Depends(require_actor),
    ) -> ConstraintOut:
        _validate_enums(body.discipline, body.kind, body.severity)
        existing = await db.operational_constraints.find_one(
            {"id": constraint_id}, {"_id": 0}
        )
        if not existing:
            raise HTTPException(404, "Constraint not found")
        await _require_constraints_access(
            actor=actor,
            request=request,
            action_key="operational_constraints.manage",
            project_id=existing.get("project_id") or "",
            constraint_id=constraint_id,
        )
        if existing.get("status") in {"resolved", "void"}:
            raise HTTPException(
                409,
                f"Cannot edit a {existing['status']} constraint — "
                "create a follow-up instead.",
            )

        update: Dict[str, Any] = {}
        for field in (
            "title", "discipline", "kind", "severity",
            "owner", "operational_impact", "notes",
        ):
            value = getattr(body, field)
            if value is not None:
                update[field] = value.strip() if isinstance(value, str) else value

        if not update:
            return _to_out(existing)

        now_iso = _utc_iso()
        update["updated_at"] = now_iso
        existing.setdefault("chronology", []).append({
            "at": now_iso,
            "by": _actor_id(actor),
            "action": "edited",
            "note": ", ".join(sorted(update.keys() - {"updated_at"})),
        })
        update["chronology"] = existing["chronology"]
        await db.operational_constraints.update_one(
            {"id": constraint_id}, {"$set": update}
        )
        existing.update(update)
        return _to_out(existing)

    @router.post("/{constraint_id}/resolve", response_model=ConstraintOut)
    async def resolve_constraint(
        constraint_id: str,
        body: ResolveBody,
        request: Request,
        actor: Dict[str, Any] = Depends(require_actor),
    ) -> ConstraintOut:
        existing = await db.operational_constraints.find_one(
            {"id": constraint_id}, {"_id": 0}
        )
        if not existing:
            raise HTTPException(404, "Constraint not found")
        await _require_constraints_access(
            actor=actor,
            request=request,
            action_key="operational_constraints.manage",
            project_id=existing.get("project_id") or "",
            constraint_id=constraint_id,
        )
        if existing.get("status") == "resolved":
            return _to_out(existing)
        if existing.get("status") == "void":
            raise HTTPException(409, "Voided constraint cannot be resolved.")

        now_iso = _utc_iso()
        chronology = existing.get("chronology", []) + [{
            "at": now_iso,
            "by": _actor_id(actor),
            "action": "resolved",
            "note": body.resolution_note.strip()[:500],
        }]
        update = {
            "status": "resolved",
            "resolved_at": now_iso,
            "updated_at": now_iso,
            "chronology": chronology,
        }
        await db.operational_constraints.update_one(
            {"id": constraint_id}, {"$set": update}
        )
        existing.update(update)
        return _to_out(existing)

    @router.post("/{constraint_id}/chronology", response_model=ConstraintOut)
    async def append_chronology(
        constraint_id: str,
        request: Request,
        body: Dict[str, Any] = Body(...),
        actor: Dict[str, Any] = Depends(require_actor),
    ) -> ConstraintOut:
        """Append an operator-supplied chronology note (e.g., "owner
        contacted"). Read-only fields above stay untouched."""
        action = str(body.get("action", "note") or "note").strip()[:80]
        note = str(body.get("note", "") or "").strip()[:500]
        if not action and not note:
            raise HTTPException(422, "action or note required")
        existing = await db.operational_constraints.find_one(
            {"id": constraint_id}, {"_id": 0}
        )
        if not existing:
            raise HTTPException(404, "Constraint not found")
        await _require_constraints_access(
            actor=actor,
            request=request,
            action_key="operational_constraints.manage",
            project_id=existing.get("project_id") or "",
            constraint_id=constraint_id,
        )

        now_iso = _utc_iso()
        chronology = existing.get("chronology", []) + [{
            "at": now_iso,
            "by": _actor_id(actor),
            "action": action or "note",
            "note": note,
        }]
        await db.operational_constraints.update_one(
            {"id": constraint_id},
            {"$set": {"chronology": chronology, "updated_at": now_iso}},
        )
        existing["chronology"] = chronology
        existing["updated_at"] = now_iso
        return _to_out(existing)

    return router


__all__ = [
    "build_operational_constraints_router",
    "ensure_operational_constraints_indexes",
    "DISCIPLINES",
    "KINDS",
    "SEVERITIES",
    "STATUSES",
]
