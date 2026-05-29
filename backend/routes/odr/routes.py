"""
routes/odr/routes.py — Phase V.1 · ODR substrate routes (M0.1).

Substrate-level API. UI + projectors + PDFs ship in M0.2+. Build
once, build right.

Endpoints:
  POST   /api/odr                       create draft
  GET    /api/odr                       list (FLL-aware scope)
  GET    /api/odr/{id}                  detail (FLL-aware projection)
  PATCH  /api/odr/{id}                  partial update (draft only)
  POST   /api/odr/{id}/submit           transition draft → submitted
  POST   /api/odr/{id}/section-event    append telemetry row
  GET    /api/odr/{id}/section-events   audit trail read

Doctrine compliance:
  * Mongo `_id` excluded from every response.
  * Hard DELETE forbidden — submitted ODRs are never deletable.
  * TRUST-TIME-1 timestamps everywhere (Z-suffixed UTC ISO).
  * Append-only `odr_section_events` writes on every mutation.
  * Submitted ODRs emit an `operational_links` row so they appear
    in the project chronology / timeline automatically.
  * FLL-aware scope filter + field projection on every read.
"""
from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict

from .models import (
    AmendmentCreate, ODR, ODRCreate, ODRPatch, ODRSubmit, SectionEventCreate,
)
from .visibility import apply_field_projection, build_odr_scope_filter, resolve_fll

logger = logging.getLogger(__name__)


DEFAULT_AMEND_WINDOW_HOURS = 24


# ── Helpers ──────────────────────────────────────────────────────────


def _utc_iso(dt: Optional[datetime] = None) -> str:
    """TRUST-TIME-1 emit · Z-suffixed UTC ISO."""
    d = dt or datetime.now(timezone.utc)
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.") + \
        f"{d.microsecond // 1000:03d}Z"


def _actor_uid(actor: Dict[str, Any]) -> str:
    if not isinstance(actor, dict):
        return "system"
    return (
        actor.get("id")
        or actor.get("user_id")
        or actor.get("uid")
        or actor.get("email")
        or actor.get("name")
        or "unknown"
    )


def _value_sha256(v: Any) -> str:
    import json
    return hashlib.sha256(
        json.dumps(v, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()


async def _next_doc_id(db, year: int) -> str:
    """Year-scoped sequence — ODR-YYYY-NNNNN."""
    res = await db.odr_counters.find_one_and_update(
        {"_id": f"odr-{year}"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True,
    )
    seq = res.get("seq", 1) if res else 1
    return f"ODR-{year}-{seq:05d}"


def _strip_id(doc: Dict[str, Any]) -> Dict[str, Any]:
    if doc is None:
        return doc
    doc.pop("_id", None)
    return doc


# ── Readiness engine (M0.1 minimal · expanded in M0.2) ───────────────


def _evaluate_readiness(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Substrate-grade readiness pass.

    M0.1 enforces only the doctrine HARD STOPS (Safety per O9). Soft
    coaching prompts are emitted as `prompt_key` references; the
    Operational Guidance Center resolves them per (key, lang) at
    surface render. No coaching content is hardcoded here.
    """
    hard_stops: List[str] = []
    missing_required: List[str] = []
    coaching_prompts: List[Dict[str, Any]] = []

    project = doc.get("project") or {}
    crew = doc.get("crew_profile") or {}

    if not project.get("project_id"):
        missing_required.append("project.project_id")
    if not project.get("report_date"):
        missing_required.append("project.report_date")
    if not project.get("foreman_uid"):
        missing_required.append("project.foreman_uid")
    if not crew.get("crew_id"):
        missing_required.append("crew_profile.crew_id")

    safety = doc.get("safety") or {}
    any_event = bool(safety.get("any_event")) or any(
        bool(safety.get(k))
        for k in (
            "accident", "incident", "near_miss",
            "property_damage", "environmental_release", "injury",
        )
    )
    if any_event:
        events = safety.get("events") or []
        if not events:
            hard_stops.append("safety.events_required_when_any_event_true")
        else:
            for i, ev in enumerate(events):
                if not ev.get("notified_safety"):
                    hard_stops.append(f"safety.events[{i}].notified_safety_required")
                if not ev.get("incident_report_complete"):
                    hard_stops.append(f"safety.events[{i}].incident_report_complete_required")

    # Foreman signature acknowledgement (O31)
    sig = (doc.get("signature") or {}).get("foreman_acknowledgement") or {}
    if not sig.get("acknowledged"):
        hard_stops.append("signature.foreman_acknowledgement.acknowledged_required")

    # Lightweight coaching nudges (prompt_key only · catalog resolves text)
    if not (doc.get("tomorrow") or {}).get("planned_work", {}).get("text"):
        coaching_prompts.append({
            "prompt_key": "tomorrow.planned_work.add_summary",
            "text": {"text": ""},
            "section_anchor": "tomorrow",
            "severity": "suggest",
        })
    if not doc.get("production_segments"):
        coaching_prompts.append({
            "prompt_key": "production.add_first_segment",
            "text": {"text": ""},
            "section_anchor": "production_segments",
            "severity": "strong_suggest",
        })

    if hard_stops:
        score = "blocked"
    elif missing_required:
        score = "needs_attention"
    elif coaching_prompts:
        score = "ready"
    else:
        score = "ready"

    return {
        "evaluated_at_utc": _utc_iso(),
        "missing_required": missing_required,
        "coaching_prompts": coaching_prompts,
        "hard_stops": hard_stops,
        "score": score,
    }


# ── Audit append-only ────────────────────────────────────────────────


async def _append_section_event(
    db,
    odr_id: str,
    project_id: str,
    actor: Dict[str, Any],
    section: str,
    action: str,
    note: Optional[str] = None,
    old_value: Any = None,
    new_value: Any = None,
) -> None:
    row = {
        "event_id": str(uuid.uuid4()),
        "odr_id": odr_id,
        "project_id": project_id,
        "section": section,
        "action": action,
        "note": (note or "")[:500],
        "old_value_sha256": _value_sha256(old_value) if old_value is not None else None,
        "new_value_sha256": _value_sha256(new_value) if new_value is not None else None,
        "at_utc": _utc_iso(),
        "actor_uid": _actor_uid(actor),
        "actor_portal": (actor.get("_actor") or "unknown"),
    }
    await db.odr_section_events.insert_one(row)


# ── Timeline emission via operational_links ──────────────────────────


async def _emit_timeline_link(
    db,
    odr_id: str,
    project_id: str,
    actor: Dict[str, Any],
    relationship: str = "references",
    target_type: str = "project",
    target_id: Optional[str] = None,
    reason: str = "",
) -> None:
    """Emit an `operational_links` row so the ODR appears in the
    project chronology / timeline. This is the substrate's tie-in to
    the V-Prelude Wave 1 timeline doctrine.

    Failure is non-blocking — substrate writes its own audit event,
    timeline emission is best-effort.
    """
    try:
        link = {
            "id": str(uuid.uuid4()),
            "source_type": "odr",
            "source_id": odr_id,
            "target_type": target_type,
            "target_id": target_id or project_id,
            "relationship": relationship,
            "reason": (reason or "")[:280],
            "visibility": "cross-portal-read",
            "project_id": project_id,
            "status": "active",
            "status_changed_at": None,
            "status_changed_by": None,
            "created_at": _utc_iso(),
            "created_by": _actor_uid(actor),
        }
        await db.operational_links.insert_one(link)
    except Exception as exc:  # noqa: BLE001
        logger.warning("ODR timeline emission failed for %s: %s", odr_id, exc)


# ── Router factory ───────────────────────────────────────────────────


def build_odr_router(
    db,
    require_actor: Callable[..., Awaitable[Dict[str, Any]]],
) -> APIRouter:
    """`require_actor` is the existing `_require_any_portal_token`
    dependency — no auth expansion."""

    router = APIRouter(prefix="/api/odr", tags=["odr"])

    # ── POST /api/odr — create draft ─────────────────────────────────

    @router.post("")
    async def create_draft(
        body: ODRCreate,
        actor: Dict[str, Any] = Depends(require_actor),
    ) -> Dict[str, Any]:
        now = _utc_iso()
        year = datetime.now(timezone.utc).year
        new_id = str(uuid.uuid4())
        doc_id = await _next_doc_id(db, year)

        project = body.project.model_dump()
        # Stamp times if foreman omitted them.
        if not project.get("time_created_utc"):
            project["time_created_utc"] = now
        if not project.get("time_created_local"):
            project["time_created_local"] = now

        skeleton = ODR(
            id=new_id,
            doc_id=doc_id,
            schema_version=2,
            project=body.project,
            crew_profile=body.crew_profile,
            status="draft",
            created_at=now,
            last_edited_at=now,
            last_edited_by_uid=_actor_uid(actor),
        ).model_dump()
        # Replace serialized project with our patched copy.
        skeleton["project"] = project

        await db.odr.insert_one(dict(skeleton))
        await _append_section_event(
            db, new_id, project.get("project_id", ""),
            actor, "envelope", "draft_created",
            note=f"doc_id={doc_id}",
            new_value={"id": new_id, "doc_id": doc_id},
        )
        return _strip_id(skeleton)

    # ── GET /api/odr — list with FLL scope ───────────────────────────

    @router.get("")
    async def list_odrs(
        project_id: Optional[str] = Query(default=None),
        crew_id: Optional[str] = Query(default=None),
        status: Optional[str] = Query(default=None),
        report_date_from: Optional[str] = Query(default=None),
        report_date_to: Optional[str] = Query(default=None),
        limit: int = Query(default=50, ge=1, le=200),
        actor: Dict[str, Any] = Depends(require_actor),
    ) -> Dict[str, Any]:
        q, fll, verb = build_odr_scope_filter(
            actor,
            requested_project_id=project_id,
            requested_crew_id=crew_id,
        )
        if status:
            q["status"] = status
        if report_date_from or report_date_to:
            rd: Dict[str, Any] = {}
            if report_date_from:
                rd["$gte"] = report_date_from
            if report_date_to:
                rd["$lte"] = report_date_to
            q["project.report_date"] = rd

        cur = db.odr.find(q, {"_id": 0}).sort(
            "project.report_date", -1
        ).limit(limit)
        rows = await cur.to_list(length=limit)
        rows = [apply_field_projection(r, fll, verb) for r in rows]
        return {
            "items": rows,
            "fll": fll,
            "verb": verb,
            "count": len(rows),
        }

    # ── GET /api/odr/{id} — detail with field projection ─────────────

    @router.get("/{odr_id}")
    async def get_odr(
        odr_id: str,
        actor: Dict[str, Any] = Depends(require_actor),
    ) -> Dict[str, Any]:
        doc = await db.odr.find_one({"id": odr_id}, {"_id": 0})
        if not doc:
            raise HTTPException(404, "ODR not found")
        # Authorization-shaped doctrine: even with auth, a non-admin
        # who is not part of the visibility set sees 404, not 403, so
        # the existence of the record is not leaked.
        scope_q, fll, verb = build_odr_scope_filter(
            actor,
            requested_project_id=(doc.get("project") or {}).get("project_id"),
            requested_crew_id=(doc.get("crew_profile") or {}).get("crew_id"),
        )
        if scope_q:
            scope_q_full = {**scope_q, "id": odr_id}
            check = await db.odr.find_one(scope_q_full, {"_id": 0, "id": 1})
            if not check and fll not in ("FLL-6",):
                raise HTTPException(404, "ODR not found")
        return apply_field_projection(doc, fll, verb)

    # ── PATCH /api/odr/{id} — partial update (draft + edit window) ───

    @router.patch("/{odr_id}")
    async def patch_odr(
        odr_id: str,
        patch: ODRPatch,
        actor: Dict[str, Any] = Depends(require_actor),
    ) -> Dict[str, Any]:
        existing = await db.odr.find_one({"id": odr_id}, {"_id": 0})
        if not existing:
            raise HTTPException(404, "ODR not found")

        status = existing.get("status", "draft")
        now = _utc_iso()

        if status in ("submitted", "approved"):
            # Foreman-tier amendments allowed only inside the
            # `amend_allowed_until_utc` window.
            limit = existing.get("amend_allowed_until_utc")
            if limit:
                try:
                    limit_dt = datetime.fromisoformat(limit.replace("Z", "+00:00"))
                    if datetime.now(timezone.utc) > limit_dt:
                        raise HTTPException(
                            403,
                            "ODR edit window has closed. Submit an amendment "
                            "via the field leadership portal (Super+).",
                        )
                except HTTPException:
                    raise
                except Exception:
                    pass
            else:
                raise HTTPException(
                    403,
                    "Submitted ODRs require an open edit window to patch.",
                )
        elif status == "returned":
            # Returned drafts may be re-edited.
            pass

        # Apply patch — only present keys.
        update_dict: Dict[str, Any] = {}
        patch_dict = patch.model_dump(exclude_unset=True)
        for k, v in patch_dict.items():
            update_dict[k] = v
        update_dict["last_edited_at"] = now
        update_dict["last_edited_by_uid"] = _actor_uid(actor)

        await db.odr.update_one({"id": odr_id}, {"$set": update_dict})
        for k in patch_dict.keys():
            await _append_section_event(
                db, odr_id,
                (existing.get("project") or {}).get("project_id", ""),
                actor, k, "patched",
                old_value=existing.get(k),
                new_value=update_dict.get(k),
            )

        new_doc = await db.odr.find_one({"id": odr_id}, {"_id": 0})
        fll = resolve_fll(actor)
        from .visibility import odr_verb as _verb
        return apply_field_projection(new_doc, fll, _verb(fll))

    # ── POST /api/odr/{id}/submit — readiness pass + status flip ─────

    @router.post("/{odr_id}/submit")
    async def submit_odr(
        odr_id: str,
        body: ODRSubmit = Body(default_factory=ODRSubmit),
        actor: Dict[str, Any] = Depends(require_actor),
    ) -> Dict[str, Any]:
        existing = await db.odr.find_one({"id": odr_id}, {"_id": 0})
        if not existing:
            raise HTTPException(404, "ODR not found")
        if existing.get("status") not in ("draft", "returned"):
            raise HTTPException(
                409,
                f"Cannot submit ODR in status '{existing.get('status')}'."
            )

        # Apply optional final signature + fingerprint.
        sig = (existing.get("signature") or {})
        ack = sig.get("foreman_acknowledgement") or {}
        if body.signature_text:
            ack.setdefault("text", body.signature_text)
        ack.setdefault("acknowledged", True)
        ack["acknowledged_at_utc"] = _utc_iso()
        ack["acknowledged_by_uid"] = _actor_uid(actor)
        if body.device_fingerprint is not None:
            ack["acknowledged_from_fingerprint"] = body.device_fingerprint.model_dump()
        sig["foreman_acknowledgement"] = ack

        # Evaluate readiness.
        proposed = {**existing, "signature": sig}
        readiness = _evaluate_readiness(proposed)
        if readiness["hard_stops"]:
            # Persist readiness state but refuse status flip.
            await db.odr.update_one(
                {"id": odr_id},
                {"$set": {"readiness": readiness, "signature": sig}},
            )
            raise HTTPException(
                409,
                {
                    "error": "ODR submission blocked by hard stops",
                    "hard_stops": readiness["hard_stops"],
                    "score": readiness["score"],
                },
            )

        now = _utc_iso()
        submitted_at = now
        amend_until = (
            datetime.now(timezone.utc)
            + timedelta(hours=DEFAULT_AMEND_WINDOW_HOURS)
        )
        amend_until_iso = _utc_iso(amend_until)

        update: Dict[str, Any] = {
            "status": "submitted",
            "submitted_at": submitted_at,
            "submitted_by_uid": _actor_uid(actor),
            "last_edited_at": now,
            "last_edited_by_uid": _actor_uid(actor),
            "signature": sig,
            "readiness": readiness,
            "amend_allowed_until_utc": amend_until_iso,
        }
        if body.location_at_submit is not None:
            update["location_at_submit"] = body.location_at_submit.model_dump()
            if body.location_at_submit.accuracy_m is not None:
                update["location_accuracy_m"] = body.location_at_submit.accuracy_m

        await db.odr.update_one({"id": odr_id}, {"$set": update})
        await _append_section_event(
            db, odr_id,
            (existing.get("project") or {}).get("project_id", ""),
            actor, "envelope", "submitted",
            new_value={"submitted_at": submitted_at, "doc_id": existing.get("doc_id")},
        )
        # Emit timeline link so the project chronology surfaces the ODR.
        await _emit_timeline_link(
            db, odr_id,
            (existing.get("project") or {}).get("project_id", ""),
            actor,
            relationship="documents",
            target_type="project",
            reason=f"ODR {existing.get('doc_id')} submitted",
        )

        new_doc = await db.odr.find_one({"id": odr_id}, {"_id": 0})
        fll = resolve_fll(actor)
        from .visibility import odr_verb as _verb
        return apply_field_projection(new_doc, fll, _verb(fll))

    # ── POST /api/odr/{id}/section-event — append-only telemetry ─────

    @router.post("/{odr_id}/section-event")
    async def post_section_event(
        odr_id: str,
        body: SectionEventCreate,
        actor: Dict[str, Any] = Depends(require_actor),
    ) -> Dict[str, Any]:
        existing = await db.odr.find_one(
            {"id": odr_id}, {"_id": 0, "project": 1},
        )
        if not existing:
            raise HTTPException(404, "ODR not found")
        row = {
            "event_id": str(uuid.uuid4()),
            "odr_id": odr_id,
            "project_id": (existing.get("project") or {}).get("project_id", ""),
            "section": body.section,
            "action": body.action,
            "note": (body.note or "")[:500],
            "old_value_sha256": body.old_value_hash,
            "new_value_sha256": body.new_value_hash,
            "at_utc": _utc_iso(),
            "actor_uid": _actor_uid(actor),
            "actor_portal": (actor.get("_actor") or "unknown"),
        }
        await db.odr_section_events.insert_one(row)
        row.pop("_id", None)
        return row

    # ── GET /api/odr/{id}/section-events — audit trail read ──────────

    @router.get("/{odr_id}/section-events")
    async def list_section_events(
        odr_id: str,
        limit: int = Query(default=200, ge=1, le=500),
        actor: Dict[str, Any] = Depends(require_actor),
    ) -> Dict[str, Any]:
        existing = await db.odr.find_one(
            {"id": odr_id}, {"_id": 0, "project": 1, "crew_profile": 1},
        )
        if not existing:
            raise HTTPException(404, "ODR not found")
        # Scope check — caller must be allowed to read the ODR itself
        # (re-uses the same FLL projector).
        scope_q, fll, _ = build_odr_scope_filter(
            actor,
            requested_project_id=(existing.get("project") or {}).get("project_id"),
            requested_crew_id=(existing.get("crew_profile") or {}).get("crew_id"),
        )
        if scope_q:
            scope_q_full = {**scope_q, "id": odr_id}
            check = await db.odr.find_one(scope_q_full, {"_id": 0, "id": 1})
            if not check and fll != "FLL-6":
                raise HTTPException(404, "ODR not found")

        cur = db.odr_section_events.find(
            {"odr_id": odr_id}, {"_id": 0}
        ).sort("at_utc", 1).limit(limit)
        events = await cur.to_list(length=limit)
        return {"odr_id": odr_id, "events": events, "count": len(events)}

    return router


__all__ = ["build_odr_router"]
