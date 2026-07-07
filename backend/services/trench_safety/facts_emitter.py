"""TRACK 23.10-C · Canonical ODS emitters for Trench Safety.

Ships seven physical fact types (idempotent, project-nullable). Emits
into `db.operational_facts` via the ODS spine
(`services/ods_spine/store.py`).

Fact types
----------
* `excavation_day_fact`               — one per `trench_excavations` row.
* `trench_inspection_fact`            — one per `trench_safety_inspections` row.
* `trench_hold_fact`                  — one per `trench_safety_holds` row
                                        (also re-emitted on `cleared_at` update).
* `trench_repair_fact`                — one per `trench_safety_repairs` row.
* `trench_verification_fact`          — emitted only when
                                        `safe_to_use_verified` transitions
                                        False → True.
* `competent_person_assignment_fact`  — emitted by consumer surfaces
                                        (Daily Report, inspection, deployment)
                                        when a competent-person snapshot is
                                        attached. Consumers pass the
                                        23.10-B snapshot dict verbatim.
* `project_excavation_summary_fact`   — per-project rollup — recomputed
                                        at the end of every batch.

B-04 invariant lock (Track 22.4B)
----------------------------------
* `safe_to_use_verified` is DERIVED at emit time from
  `verified_at IS NOT NULL AND reinspection_passed IS TRUE`. Never
  read from `status="completed"` alone.

Idempotency
-----------
* Natural key = `(source_type, source_id, source_item_id, fact_type)`.
* Emitters call `supersede_facts()` before writing so `is_current=True`
  is monotonically owned by the newest emission.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Optional, Tuple

from services.ods_spine.model import now_iso
from services.ods_spine.store import (
    COLL_FACTS, record_ingestion_run, supersede_facts, write_facts,
)

from .project_linker import ProjectLinkage, resolve_project


TENANT_DEFAULT = "masci"
SOURCE_TYPE_TRENCH = "safety_form"           # existing enum in ods_spine.model

TRENCH_FACT_TYPES: Tuple[str, ...] = (
    "excavation_day_fact",
    "trench_inspection_fact",
    "trench_hold_fact",
    "trench_repair_fact",
    "trench_verification_fact",
    "competent_person_assignment_fact",
    "project_excavation_summary_fact",
)


# ─── Helpers ──────────────────────────────────────────────────────────
def _proj_id_for_fact(linkage: Optional[ProjectLinkage]) -> str:
    """ODS envelope requires a truthy project_id. `unknown` sentinel
    filters cleanly downstream — aggregators treat it as MISSING."""
    if linkage is None or not linkage.project_number:
        return "unknown"
    return str(linkage.project_number)


def _date_from_record(record: Mapping[str, Any]) -> str:
    for k in ("date", "date_of_work", "opened_at", "created_at",
              "inspection_datetime", "verified_at"):
        v = record.get(k)
        if not v:
            continue
        s = str(v)
        return s[:10] if len(s) >= 10 else datetime.now(timezone.utc).date().isoformat()
    return datetime.now(timezone.utc).date().isoformat()


def _linkage_payload(linkage: Optional[ProjectLinkage]) -> Dict[str, Any]:
    if linkage is None:
        return {
            "project_number": None,
            "project_link_status": "missing",
            "confidence": "none",
            "linker_notes": "no linkage attempted",
        }
    return {
        "project_number": linkage.project_number,
        "project_name_snapshot": linkage.project_name_snapshot,
        "project_id_snapshot": linkage.project_id_snapshot,
        "project_link_status": linkage.project_link_status,
        "confidence": linkage.confidence,
        "linker_notes": linkage.linker_notes,
        "matched_deployment_id": linkage.matched_deployment_id,
    }


def _envelope(
    fact_type: str,
    project_id: str,
    date: str,
    source_item_id: str,
    payload: Dict[str, Any],
    *,
    submitted_by: str,
    ingestion_run_id: str,
    confidence: float,
    trace_id: str,
) -> Dict[str, Any]:
    return {
        "fact_id": uuid.uuid4().hex,
        "fact_type": fact_type,
        "tenant_id": TENANT_DEFAULT,
        "project_id": project_id,
        "date": date,
        "source_type": SOURCE_TYPE_TRENCH,
        "source_id": "trench_safety",
        "source_item_id": source_item_id,
        "source_version": 0,
        "source_status": "full",
        "is_current": True,
        "submitted_by": submitted_by or "system",
        "verified_identity": True,
        "confidence": confidence,
        "trace_id": trace_id or source_item_id,
        "ingestion_run_id": ingestion_run_id,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "payload": payload,
    }


async def _run(db, trigger: str, actor: str = "system") -> str:
    return await record_ingestion_run(
        db, source_type=SOURCE_TYPE_TRENCH, source_id="trench_safety",
        source_version=0, actor=actor, trigger=trigger,
    )


async def _supersede_prior(db, source_item_id: str, fact_type: str) -> None:
    """Mark prior current fact for this natural key as superseded."""
    await db[COLL_FACTS].update_many(
        {
            "source_type": SOURCE_TYPE_TRENCH,
            "source_id": "trench_safety",
            "source_item_id": source_item_id,
            "fact_type": fact_type,
            "is_current": True,
        },
        {"$set": {
            "is_current": False,
            "source_status": "superseded",
            "updated_at": now_iso(),
        }},
    )


# ─── Excavation day fact ──────────────────────────────────────────────
async def emit_excavation_day_fact(
    db, excavation: Mapping[str, Any], *, actor: str = "system",
    trigger: str = "trench_excavations.write",
) -> Optional[str]:
    """One fact per `trench_excavations` row. Carries the operational
    excavation-day signal. Does NOT double-count with formal inspections."""
    src_id = excavation.get("id")
    if not src_id:
        return None
    linkage = await resolve_project(db, excavation)
    run_id = await _run(db, trigger, actor)
    fact = _envelope(
        "excavation_day_fact",
        _proj_id_for_fact(linkage),
        _date_from_record(excavation),
        src_id,
        {
            "excavation_id": src_id,
            "report_id": excavation.get("report_id"),
            "date_of_work": excavation.get("date_of_work"),
            "excavation_type": excavation.get("excavation_type"),
            "max_depth_ft": excavation.get("max_depth_ft") or excavation.get("depth_ft"),
            "max_depth_unit": excavation.get("max_depth_unit") or "ft",
            "excavation_count": excavation.get("excavation_count") or 1,
            "protective_system": excavation.get("protective_system"),
            "trench_box_id": excavation.get("trench_box_id"),
            "trench_box_label_snapshot": excavation.get("trench_box_label"),
            "inspection_completed": bool(excavation.get("inspection_completed")),
            "hold_issued": bool(excavation.get("hold_issued")),
            "utilities_status": excavation.get("utilities_status"),
            "tomorrow_planned": bool(excavation.get("tomorrow_planned")),
            "crew": excavation.get("crew"),
            "assigned_asset_ids": excavation.get("assigned_asset_ids") or [],
            "competent_person_name_snapshot": excavation.get("competent_person_name"),
            "competent_person_confirmed": bool(excavation.get("competent_person_confirmed")),
            "linkage": _linkage_payload(linkage),
        },
        submitted_by=str(excavation.get("submitted_by") or ""),
        ingestion_run_id=run_id,
        confidence=1.0,
        trace_id=src_id,
    )
    await _supersede_prior(db, src_id, "excavation_day_fact")
    await write_facts(db, [fact], ingestion_run_id=run_id)
    return fact["fact_id"]


# ─── Trench inspection fact ───────────────────────────────────────────
async def emit_trench_inspection_fact(
    db, insp: Mapping[str, Any], *, actor: str = "system",
    trigger: str = "trench_safety_inspections.write",
) -> Optional[str]:
    src_id = insp.get("id")
    if not src_id:
        return None
    linkage = await resolve_project(db, insp)
    run_id = await _run(db, trigger, actor)
    fact = _envelope(
        "trench_inspection_fact",
        _proj_id_for_fact(linkage),
        _date_from_record(insp),
        src_id,
        {
            "inspection_id": src_id,
            "asset_id": insp.get("asset_id"),
            "asset_label": insp.get("asset_label"),
            "inspection_type": insp.get("inspection_type"),
            "result": insp.get("result"),
            "inspector_name": insp.get("inspector_name")
                or insp.get("inspector_email"),
            "competent_person_confirmed": bool(insp.get("competent_person_confirmed")),
            "corrective_actions_count": len(insp.get("corrective_actions") or []),
            "severity": insp.get("severity"),
            "linkage": _linkage_payload(linkage),
        },
        submitted_by=str(insp.get("inspector_name") or ""),
        ingestion_run_id=run_id,
        confidence=1.0,
        trace_id=src_id,
    )
    await _supersede_prior(db, src_id, "trench_inspection_fact")
    await write_facts(db, [fact], ingestion_run_id=run_id)
    return fact["fact_id"]


# ─── Trench hold fact ─────────────────────────────────────────────────
async def emit_trench_hold_fact(
    db, hold: Mapping[str, Any], *, actor: str = "system",
    trigger: str = "trench_safety_holds.write",
) -> Optional[str]:
    src_id = hold.get("id")
    if not src_id:
        return None
    linkage = await resolve_project(db, hold)
    run_id = await _run(db, trigger, actor)
    fact = _envelope(
        "trench_hold_fact",
        _proj_id_for_fact(linkage),
        _date_from_record(hold),
        src_id,
        {
            "hold_id": src_id,
            "asset_id": hold.get("asset_id"),
            "kind": hold.get("kind"),                    # safety/engineering/etc.
            "reason": hold.get("reason"),
            "opened_at": hold.get("opened_at"),
            "opened_by": hold.get("opened_by"),
            "cleared_at": hold.get("cleared_at"),
            "cleared_by": hold.get("cleared_by"),
            "is_active": bool(hold.get("is_active") if hold.get("is_active") is not None else not hold.get("cleared_at")),
            "source": hold.get("source"),
            "source_ref": hold.get("source_ref"),
            "linkage": _linkage_payload(linkage),
        },
        submitted_by=str(hold.get("opened_by") or ""),
        ingestion_run_id=run_id,
        confidence=1.0,
        trace_id=src_id,
    )
    await _supersede_prior(db, src_id, "trench_hold_fact")
    await write_facts(db, [fact], ingestion_run_id=run_id)
    return fact["fact_id"]


# ─── Trench repair fact + B-04 verification ───────────────────────────
def _safe_to_use_verified(repair: Mapping[str, Any]) -> bool:
    """Track 22.4B B-04 invariant — Repair Complete ≠ Safe To Use.

    Safe-to-use ONLY iff `verified_at IS NOT NULL AND reinspection_passed IS TRUE`.
    Never inferred from `status="completed"` alone.
    """
    return bool(repair.get("verified_at")) and bool(repair.get("reinspection_passed"))


async def emit_trench_repair_fact(
    db, repair: Mapping[str, Any], *, actor: str = "system",
    trigger: str = "trench_safety_repairs.write",
) -> Optional[str]:
    src_id = repair.get("id")
    if not src_id:
        return None
    linkage = await resolve_project(db, repair)
    run_id = await _run(db, trigger, actor)
    safe = _safe_to_use_verified(repair)
    fact = _envelope(
        "trench_repair_fact",
        _proj_id_for_fact(linkage),
        _date_from_record(repair),
        src_id,
        {
            "repair_id": src_id,
            "asset_id": repair.get("asset_id"),
            "status": repair.get("status"),
            "opened_at": repair.get("opened_at"),
            "opened_by": repair.get("opened_by"),
            "verified_at": repair.get("verified_at"),
            "verified_by": repair.get("verified_by"),
            "requires_reinspection": bool(repair.get("requires_reinspection")),
            "reinspection_passed": bool(repair.get("reinspection_passed")),
            # B-04 invariant — DERIVED at emit time. Never inferred from status.
            "safe_to_use_verified": safe,
            "linkage": _linkage_payload(linkage),
        },
        submitted_by=str(repair.get("opened_by") or ""),
        ingestion_run_id=run_id,
        confidence=1.0,
        trace_id=src_id,
    )
    await _supersede_prior(db, src_id, "trench_repair_fact")
    await write_facts(db, [fact], ingestion_run_id=run_id)

    # Companion verification fact — emitted ONLY when safe transitions
    # False → True. Idempotent per repair_id.
    if safe:
        prior = await db[COLL_FACTS].find_one(
            {
                "source_type": SOURCE_TYPE_TRENCH,
                "source_id": "trench_safety",
                "source_item_id": src_id,
                "fact_type": "trench_verification_fact",
                "is_current": True,
            },
            {"_id": 0},
        )
        if not prior:
            await emit_trench_verification_fact(
                db, repair, linkage=linkage,
                actor=actor, trigger="trench_repair.verified",
            )
    return fact["fact_id"]


async def emit_trench_verification_fact(
    db, repair: Mapping[str, Any], *,
    linkage: Optional[ProjectLinkage] = None,
    actor: str = "system", trigger: str = "trench_repair.verified",
) -> Optional[str]:
    """Fires the moment a repair transitions to safe-to-use verified."""
    src_id = repair.get("id")
    if not src_id:
        return None
    if not _safe_to_use_verified(repair):
        return None
    if linkage is None:
        linkage = await resolve_project(db, repair)
    run_id = await _run(db, trigger, actor)
    fact = _envelope(
        "trench_verification_fact",
        _proj_id_for_fact(linkage),
        _date_from_record(repair),
        src_id,
        {
            "repair_id": src_id,
            "asset_id": repair.get("asset_id"),
            "verified_at": repair.get("verified_at"),
            "verified_by": repair.get("verified_by"),
            "reinspection_passed": True,
            "safe_to_use_verified": True,
            "linkage": _linkage_payload(linkage),
        },
        submitted_by=str(repair.get("verified_by") or ""),
        ingestion_run_id=run_id,
        confidence=1.0,
        trace_id=src_id,
    )
    await _supersede_prior(db, src_id, "trench_verification_fact")
    await write_facts(db, [fact], ingestion_run_id=run_id)
    return fact["fact_id"]


# ─── Competent Person assignment fact ────────────────────────────────
async def emit_competent_person_assignment_fact(
    db, *,
    project_number: Optional[str],
    consumer_collection: str,
    consumer_source_id: str,
    consumer_row_id: str,
    qualification_snapshot: Optional[Mapping[str, Any]],
    date_of_work: Optional[str] = None,
    actor: str = "system",
    trigger: str = "consumer.competent_person_selected",
) -> Optional[str]:
    """Consumers (Daily Report V3 · trench inspection · scheduling)
    call this with the 23.10-B `qualification_snapshot` dict verbatim.

    We do NOT re-fetch or re-derive the snapshot — the caller owns the
    freeze semantics per 23.10-B §3.
    """
    if not consumer_row_id:
        return None
    run_id = await _run(db, trigger, actor)
    snap = dict(qualification_snapshot or {})
    fact_project = project_number or "unknown"
    fact = {
        "fact_id": uuid.uuid4().hex,
        "fact_type": "competent_person_assignment_fact",
        "tenant_id": TENANT_DEFAULT,
        "project_id": str(fact_project),
        "date": (date_of_work or datetime.now(timezone.utc).date().isoformat())[:10],
        "source_type": SOURCE_TYPE_TRENCH,
        "source_id": consumer_source_id or consumer_collection,
        "source_item_id": consumer_row_id,
        "source_version": 0,
        "source_status": "full",
        "is_current": True,
        "submitted_by": snap.get("actor_email") or "system",
        "verified_identity": True,
        "confidence": 1.0,
        "trace_id": consumer_row_id,
        "ingestion_run_id": run_id,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "payload": {
            "consumer_collection": consumer_collection,
            "consumer_row_id": consumer_row_id,
            "project_number": project_number,
            "qualification_id": snap.get("qualification_id"),
            "qualification_type": snap.get("qualification_type"),
            "employee_id": snap.get("employee_id"),
            "employee_master_id": snap.get("employee_master_id"),
            "person_name_snapshot": snap.get("person_name_snapshot"),
            "person_trade_snapshot": snap.get("person_trade_snapshot"),
            "person_crew_snapshot": snap.get("person_crew_snapshot"),
            "verification_status_at_selection": snap.get("verification_status_at_selection"),
            "expires_at_at_selection": snap.get("expires_at_at_selection"),
            "cert_valid_at_report": bool(snap.get("is_active_at_selection")),
            "snapshot_at": snap.get("snapshot_at") or now_iso(),
        },
    }
    # Idempotent per (consumer_row_id, fact_type).
    await db[COLL_FACTS].update_many(
        {
            "source_type": SOURCE_TYPE_TRENCH,
            "source_id": consumer_source_id or consumer_collection,
            "source_item_id": consumer_row_id,
            "fact_type": "competent_person_assignment_fact",
            "is_current": True,
        },
        {"$set": {
            "is_current": False,
            "source_status": "superseded",
            "updated_at": now_iso(),
        }},
    )
    await write_facts(db, [fact], ingestion_run_id=run_id)
    return fact["fact_id"]


# ─── Project excavation summary ──────────────────────────────────────
async def recompute_project_excavation_summary(
    db, project_number: str, *, actor: str = "system",
    trigger: str = "trench_facts.summary_recompute",
) -> Optional[str]:
    """Aggregate the physical facts into one summary fact per project.

    Idempotent: supersedes prior current summary for the project before
    writing a fresh one.
    """
    if not project_number:
        return None
    q_base = {
        "source_type": SOURCE_TYPE_TRENCH,
        "source_id": "trench_safety",
        "project_id": str(project_number),
        "is_current": True,
    }

    async def _count(fact_type: str, extra: Optional[Dict[str, Any]] = None) -> int:
        q = {**q_base, "fact_type": fact_type}
        if extra:
            q.update(extra)
        return await db[COLL_FACTS].count_documents(q)

    async def _sum_payload_field(fact_type: str, field: str) -> float:
        total = 0.0
        cursor = db[COLL_FACTS].find(
            {**q_base, "fact_type": fact_type}, {"_id": 0, "payload": 1},
        )
        async for f in cursor:
            v = (f.get("payload") or {}).get(field)
            try:
                total += float(v or 0)
            except (TypeError, ValueError):
                pass
        return total

    excavation_days = await _count("excavation_day_fact")
    inspections = await _count("trench_inspection_fact")
    open_holds = await _count("trench_hold_fact", {"payload.is_active": True})
    total_holds = await _count("trench_hold_fact")
    verifications = await _count("trench_verification_fact")
    cp_assignments = await _count("competent_person_assignment_fact")
    max_depth = 0.0
    cursor = db[COLL_FACTS].find(
        {**q_base, "fact_type": "excavation_day_fact"},
        {"_id": 0, "payload.max_depth_ft": 1},
    )
    async for f in cursor:
        v = (f.get("payload") or {}).get("max_depth_ft")
        try:
            fv = float(v or 0)
            if fv > max_depth:
                max_depth = fv
        except (TypeError, ValueError):
            pass

    # Repair fact aggregates — respect B-04 invariant.
    repairs_open = 0
    repairs_completed = 0
    repairs_safe_to_use = 0
    cursor = db[COLL_FACTS].find(
        {**q_base, "fact_type": "trench_repair_fact"}, {"_id": 0, "payload": 1},
    )
    async for f in cursor:
        pl = f.get("payload") or {}
        if pl.get("safe_to_use_verified"):
            repairs_safe_to_use += 1
        if pl.get("status") == "completed":
            repairs_completed += 1
        elif pl.get("status") in ("open", "in_progress", None):
            repairs_open += 1

    run_id = await _run(db, trigger, actor)
    fact = _envelope(
        "project_excavation_summary_fact",
        str(project_number),
        datetime.now(timezone.utc).date().isoformat(),
        f"summary:{project_number}",
        {
            "project_number": project_number,
            "excavation_day_count": excavation_days,
            "trench_inspection_count": inspections,
            "trench_hold_count": total_holds,
            "open_trench_holds": open_holds,
            "trench_repair_open_count": repairs_open,
            "trench_repair_completed_count": repairs_completed,
            "trench_safe_to_use_verified_count": repairs_safe_to_use,
            "trench_verification_events": verifications,
            "competent_person_assignments": cp_assignments,
            "max_depth_observed_ft": max_depth,
        },
        submitted_by="system", ingestion_run_id=run_id, confidence=1.0,
        trace_id=f"summary:{project_number}",
    )
    await _supersede_prior(
        db, f"summary:{project_number}", "project_excavation_summary_fact",
    )
    await write_facts(db, [fact], ingestion_run_id=run_id)
    return fact["fact_id"]
