"""routes/field_memory.py · iter432 · Phase 30 · Part 6.

Field Memory Continuity System — append-only operational wisdom store.

Doctrine
--------
This is **operational memory**, not analytics.

A field memory note is a short, append-only operator observation that
captures recurring operational truth about a project, piece of
equipment, assignment, or recovery event — the institutional wisdom
that normally lives in heads, radio chatter, and post-shift
conversations.

Examples (taken from the Phase 30 directive):
  - "Oxford Road repeatedly bottlenecks near STA 112+00 during asphalt
    haul staging."
  - "Taxiway escort delays impact haul continuity after 3 PM."
  - "Truck 47 repeatedly loses hydraulic pressure during high-temp
    paving cycles."

Doctrine guards
---------------
- **APPEND-ONLY.** Notes can be added, listed, and resolved (marked
  as "no-longer-applies"). They cannot be edited or hard-deleted by
  any role. Operational truth is permanent.
- **NO scoring, NO ranking, NO AI suggestions, NO recommendations.**
- **NO incident-blame fields.** Notes describe operational conditions,
  not people. No author-shaming surfaces.
- **Role-aware visibility.** Field Leadership, Dispatch, PM, Shop,
  Safety, HR, Admin can READ. Field Leadership, PM, Safety, Admin can
  WRITE. Shop and Dispatch can write notes scoped to their own
  domain (equipment / assignment) but never to project-wide.
- **Bilingual at the surface.** Note body is plain text · render in
  whatever language the operator wrote it in · do not auto-translate.

Schema (one collection: `field_memory_notes`)
---------------------------------------------
    {
      "id": "fm-<uuid>",                   # canonical id
      "tenant_id": "masci",
      "subject_kind": "project|equipment|assignment|recovery_event",
      "subject_id": "<id of the target row>",
      "subject_label": "Oxford Road",      # snapshotted display label
      "body": "Repeatedly bottlenecks near STA 112+00 …",
      "tags": ["sequencing", "haul-staging"], # operator-defined
      "captured_by": "Chris Wright",
      "captured_by_role": "field_leadership",
      "captured_at": "2026-05-25T18:00:00+00:00",
      "resolved": false,
      "resolved_at": null,
      "resolved_by": null,
      "resolved_reason": null,             # 'no_longer_applies' | 'condition_addressed'
    }

Endpoints
---------
    POST /api/field-memory                 (write · role-gated)
    GET  /api/field-memory                 (list by subject_kind/subject_id)
    POST /api/field-memory/{id}/resolve    (mark as no-longer-applies)
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Request
from pydantic import BaseModel, Field

from lib.enterprise_governance import require_governed_action

logger = logging.getLogger("field_memory")


_VALID_SUBJECT_KINDS = {"project", "equipment", "assignment", "recovery_event"}
_VALID_RESOLVE_REASONS = {"no_longer_applies", "condition_addressed"}
_BODY_MAX = 2000
_LABEL_MAX = 240
_TAG_MAX = 40


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _resolve_tenant(x_tenant: Optional[str]) -> str:
    return (x_tenant or "masci").strip().lower()[:64]


def _actor_meta(actor: Dict[str, Any]) -> Dict[str, str]:
    """Resolve actor → {name, role} where role is the portal-kind slug.

    The upstream `_require_any_portal_token` dep returns the user doc with
    an injected `_actor` field carrying the portal kind ('admin', 'dispatch',
    'shop', 'pm', 'safety', 'hr', 'fl', 'leadership'). The plain `role`
    field on a user doc carries the human-readable job title
    ('Dispatcher', 'Shop Manager', 'Superintendent', …) which must NOT
    be used for RBAC. Prefer `_actor` when present; fall back to `role`
    so unit tests that mock the dep directly with a slug still work.
    Alias `fl` / `leadership` → `field_leadership` to match the write
    matrix in `_can_write_subject`.
    """
    if not isinstance(actor, dict):
        return {"name": "Admin", "role": "admin"}
    raw_role = actor.get("_actor") or actor.get("role") or "admin"
    role = str(raw_role).strip().lower()
    if role in ("fl", "leadership"):
        role = "field_leadership"
    return {
        "name": actor.get("name") or actor.get("email") or "Operator",
        "role": role,
    }


def _write_action_for_subject(subject_kind: str) -> str:
    return f"field_memory.write.{subject_kind}"


class FieldMemoryCreate(BaseModel):
    subject_kind: str
    subject_id: str
    subject_label: Optional[str] = ""
    body: str
    tags: Optional[List[str]] = Field(default_factory=list)


class FieldMemoryResolve(BaseModel):
    reason: str
    note: Optional[str] = ""


def build_field_memory_router(
    *,
    db,
    require_any_portal_token_dep: Callable[..., Awaitable[Dict[str, Any]]],
) -> APIRouter:
    """Build the field memory router. Every endpoint requires SOME
    authenticated portal — there are no public field-memory surfaces."""
    router = APIRouter(prefix="/api/field-memory", tags=["field-memory"])

    def _public(doc: Dict[str, Any]) -> Dict[str, Any]:
        out = {k: v for k, v in doc.items() if k != "_id"}
        return out

    async def _require_field_memory_access(
        *,
        actor: Dict[str, Any],
        request: Request,
        action_key: str,
        subject_kind: Optional[str],
        subject_id: Optional[str],
        subject_label: str = "",
    ) -> None:
        meta = _actor_meta(actor)
        governed_actor = dict(actor or {})
        governed_actor.setdefault("id", f"field-memory-{meta['role']}")
        governed_actor.setdefault("email", f"{meta['role']}@field-memory.local")
        governed_actor["_actor"] = meta["role"]
        governed_actor["role"] = meta["role"]
        await require_governed_action(
            db,
            actor=governed_actor,
            action_key=action_key,
            resource_type="field_memory_note",
            resource={
                "id": subject_id or "field-memory",
                "subject_kind": subject_kind or "all",
                "subject_id": subject_id or "",
                "subject_label": subject_label or "",
            },
            requested_context={
                "module": "field_memory",
                "subject_kind": subject_kind or "all",
                "subject_id": subject_id or "",
            },
            request=request,
        )

    @router.post("")
    async def create_note(
        body: FieldMemoryCreate,
        request: Request,
        actor: Dict[str, Any] = Depends(require_any_portal_token_dep),
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
    ):
        if body.subject_kind not in _VALID_SUBJECT_KINDS:
            raise HTTPException(400, f"subject_kind must be one of {sorted(_VALID_SUBJECT_KINDS)}")
        if not body.subject_id or not body.subject_id.strip():
            raise HTTPException(400, "subject_id is required")
        text = (body.body or "").strip()
        if not text:
            raise HTTPException(400, "body is required")
        if len(text) > _BODY_MAX:
            raise HTTPException(400, f"body exceeds {_BODY_MAX} chars")

        meta = _actor_meta(actor)
        await _require_field_memory_access(
            actor=actor,
            request=request,
            action_key=_write_action_for_subject(body.subject_kind),
            subject_kind=body.subject_kind,
            subject_id=body.subject_id.strip(),
            subject_label=(body.subject_label or "").strip(),
        )

        tags = []
        for t in (body.tags or []):
            t = str(t or "").strip().lower()[:_TAG_MAX]
            if t and t not in tags:
                tags.append(t)
            if len(tags) >= 12:
                break

        doc = {
            "id": f"fm-{uuid.uuid4().hex}",
            "tenant_id": _resolve_tenant(x_tenant_id),
            "subject_kind": body.subject_kind,
            "subject_id": body.subject_id.strip(),
            "subject_label": (body.subject_label or "").strip()[:_LABEL_MAX],
            "body": text,
            "tags": tags,
            "captured_by": meta["name"],
            "captured_by_role": meta["role"],
            "captured_at": _now(),
            "resolved": False,
            "resolved_at": None,
            "resolved_by": None,
            "resolved_reason": None,
        }
        await db.field_memory_notes.insert_one(doc)
        return _public(doc)

    @router.get("/recent")
    async def recent_notes(
        request: Request,
        limit: int = 5,
        subject_kind: Optional[str] = None,
        actor: Dict[str, Any] = Depends(require_any_portal_token_dep),  # noqa: ARG001
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
    ):
        """Most recent UNRESOLVED notes for this tenant.

        Tiny additive surface for role hubs · calm read-only.
        - Any portal token can read (matches the list endpoint).
        - Defaults to limit=5 · hard cap 25 to keep the surface calm.
        - Optional subject_kind filter (project/equipment/assignment/recovery_event).
        - No subject_id required (this is the "what's on the platform's mind"
          glance · NOT a search · NOT analytics · NOT ranked).
        """
        n = max(1, min(int(limit or 5), 25))
        q: Dict[str, Any] = {
            "tenant_id": _resolve_tenant(x_tenant_id),
            "resolved": False,
        }
        if subject_kind:
            if subject_kind not in _VALID_SUBJECT_KINDS:
                raise HTTPException(400, f"subject_kind must be one of {sorted(_VALID_SUBJECT_KINDS)}")
            q["subject_kind"] = subject_kind
        await _require_field_memory_access(
            actor=actor,
            request=request,
            action_key="field_memory.read",
            subject_kind=subject_kind,
            subject_id=None,
        )
        items: List[Dict[str, Any]] = []
        cur = db.field_memory_notes.find(q, {"_id": 0}).sort("captured_at", -1).limit(n)
        async for d in cur:
            items.append(d)
        return {"count": len(items), "items": items}

    @router.get("")
    async def list_notes(
        request: Request,
        subject_kind: str,
        subject_id: str,
        include_resolved: bool = False,
        actor: Dict[str, Any] = Depends(require_any_portal_token_dep),  # noqa: ARG001
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
    ):
        if subject_kind not in _VALID_SUBJECT_KINDS:
            raise HTTPException(400, f"subject_kind must be one of {sorted(_VALID_SUBJECT_KINDS)}")
        await _require_field_memory_access(
            actor=actor,
            request=request,
            action_key="field_memory.read",
            subject_kind=subject_kind,
            subject_id=subject_id.strip(),
        )
        q: Dict[str, Any] = {
            "tenant_id": _resolve_tenant(x_tenant_id),
            "subject_kind": subject_kind,
            "subject_id": subject_id.strip(),
        }
        if not include_resolved:
            q["resolved"] = False
        items: List[Dict[str, Any]] = []
        cur = db.field_memory_notes.find(q, {"_id": 0}).sort("captured_at", -1).limit(500)
        async for d in cur:
            items.append(d)
        return {
            "subject_kind": subject_kind,
            "subject_id": subject_id,
            "count": len(items),
            "items": items,
        }

    @router.post("/{note_id}/resolve")
    async def resolve_note(
        note_id: str,
        body: FieldMemoryResolve,
        request: Request,
        actor: Dict[str, Any] = Depends(require_any_portal_token_dep),
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
    ):
        if body.reason not in _VALID_RESOLVE_REASONS:
            raise HTTPException(400, f"reason must be one of {sorted(_VALID_RESOLVE_REASONS)}")
        tenant_id = _resolve_tenant(x_tenant_id)
        existing = await db.field_memory_notes.find_one(
            {"id": note_id, "tenant_id": tenant_id},
            {"_id": 0},
        )
        if not existing:
            raise HTTPException(404, "field memory note not found")
        if existing.get("resolved"):
            raise HTTPException(400, "field memory note is already resolved")
        meta = _actor_meta(actor)
        await _require_field_memory_access(
            actor=actor,
            request=request,
            action_key=_write_action_for_subject(existing.get("subject_kind") or ""),
            subject_kind=existing.get("subject_kind"),
            subject_id=existing.get("subject_id"),
            subject_label=existing.get("subject_label") or "",
        )
        await db.field_memory_notes.update_one(
            {"id": note_id, "tenant_id": tenant_id},
            {"$set": {
                "resolved": True,
                "resolved_at": _now(),
                "resolved_by": meta["name"],
                "resolved_by_role": meta["role"],
                "resolved_reason": body.reason,
                "resolved_note": (body.note or "").strip()[:_BODY_MAX],
            }},
        )
        return {"ok": True, "id": note_id}

    return router


async def ensure_field_memory_indexes(db) -> None:
    """Idempotent index ensures. Safe to call on every startup."""
    try:
        await db.field_memory_notes.create_index(
            [("tenant_id", 1), ("subject_kind", 1), ("subject_id", 1),
             ("resolved", 1), ("captured_at", -1)],
            name="ix_field_memory_subject_unresolved",
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"[field-memory] subject index ensure failed: {exc}")
    try:
        await db.field_memory_notes.create_index(
            [("id", 1)], unique=True, name="ix_field_memory_id",
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"[field-memory] id index ensure failed: {exc}")
