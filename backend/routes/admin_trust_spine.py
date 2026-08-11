"""TRACK 15.76 · Platform Trust Spine — admin observability.

Admin-gated endpoint that aggregates ``trust_spine_events`` and
returns per-workflow lifecycle health alongside the Track 15.75D
audit-row health. The frontend Platform Trust Dashboard renders
these counters next to the per-workflow delivery table, giving the
operator a single screen with both audit-side and lifecycle-side
proof.

The endpoint is **READ-ONLY**, **admin-gated**, **secret-free**,
and **never mutates** anything.

Band rules (no fake-green):

* RED   — any failed_24h event OR contradicted dashboard
* AMBER — current-policy evidence exists but one or more expected stages are missing
* AMBER-NO-ACTIVITY — no current evidence within the workflow freshness policy
* GREEN — evidence is current for the workflow policy, no failures, all expected stages observed
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends

from lib.canonical_truth import canonical_truth_surface
from lib.governed_certification_lane import GOVERNED_CERTIFICATION_PROJECT_NUMBER
from lib.ots_truth import (
    CORRELATED,
    OBSERVED,
    VALIDATED,
    VERIFIED,
    canonical_truth_card,
    compatibility_projection,
    projected_truth_relationship,
    public_ots_projection,
)
from lib.production_certification import WORKFLOW_CERTIFICATION_POLICIES
from lib.synthetic_safety_filter import (
    INSPECTION_FIELDS,
    JHA_FIELDS,
    is_synthetic_safety_doc,
)
from lib.trust_spine import (
    WORKFLOW_EXPECTED_STAGES,
    canonical_workflows_for_event,
    workflow_family,
)


PREVIEW_SAFE_DELIVERY_WORKFLOWS = {
    "daily-report",
    "meeting",
    "inspection",
    "incident",
    "jha",
    "qaqc",
    "equipment-inspection",
    "dvir",
}

HEALTH_HEALTHY = "healthy"
HEALTH_HEALTHY_QUIET = "healthy_quiet"
HEALTH_AGING = "aging"
HEALTH_STALE = "stale"
HEALTH_DEGRADED = "degraded"
HEALTH_NOT_YET_EXERCISED = "not_yet_exercised"
HEALTH_BLOCKED = "blocked"
HEALTH_UNKNOWN = "unknown"


def _current_week_ending(today: Optional[date] = None) -> str:
    anchor = today or datetime.now(timezone.utc).date()
    delta = (anchor.weekday() + 1) % 7
    return (anchor - timedelta(days=delta)).isoformat()


def _parse_date_only(value: Any) -> Optional[date]:
    text = str(value or "").strip()[:10]
    if not text:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def _is_certification_project(doc: Optional[Dict[str, Any]]) -> bool:
    if not doc:
        return False
    return str(doc.get("project_number") or "").strip() == GOVERNED_CERTIFICATION_PROJECT_NUMBER


async def _latest_non_synthetic_safety_doc(db, collection: str, fields: tuple[str, ...]) -> Optional[Dict[str, Any]]:
    cursor = db[collection].find({}, {"_id": 0}).sort("created_at", -1).limit(40)
    async for doc in cursor:
        if _is_certification_project(doc):
            continue
        if is_synthetic_safety_doc(doc, fields):
            continue
        return doc
    return None


async def _find_event_record(db, workflow: str, record_id: str) -> List[Dict[str, Any]]:
    if not record_id:
        return []
    return await db.trust_spine_events.find(
        {"workflow": workflow, "record_id": record_id},
        {"_id": 0, "ts": 1, "stage": 1, "status": 1, "module": 1, "failure_reason": 1, "record_id": 1},
    ).sort("ts", 1).to_list(30)


def _workflow_policy_window_hours(workflow: str) -> int:
    policy = WORKFLOW_CERTIFICATION_POLICIES.get(workflow)
    return int(getattr(policy, "stale_threshold_hours", 24) or 24)


def _hours_since(ts: Optional[str], now: datetime) -> Optional[float]:
    dt = _parse_iso(ts)
    if not dt:
        return None
    return round((now - dt).total_seconds() / 3600.0, 1)


async def _apply_cadence_semantics(db, slot: Dict[str, Any], *, now: datetime) -> None:
    workflow = str(slot.get("workflow") or "")
    last_success = slot.get("last_success") or {}
    last_success_ts = _parse_iso(last_success.get("ts"))

    slot.setdefault("health_state", HEALTH_UNKNOWN)
    slot.setdefault("cadence_classification", "UNKNOWN")
    slot.setdefault("current_freshness_policy", f"{slot.get('freshness_window_hours')}h workflow freshness window")
    slot.setdefault("downstream_consumers", [])

    if workflow == "dispatch-assignment":
        latest = await db.dispatch_assignments.find_one({}, {"_id": 0, "id": 1, "project_number": 1, "created_at": 1, "updated_at": 1}, sort=[("created_at", -1)])
        latest_created = _parse_iso((latest or {}).get("created_at"))
        has_new_activity = bool(last_success_ts and latest_created and latest_created > last_success_ts)
        slot.update({
            "business_purpose": "Creates governed dispatch assignments only when a real transportation move is scheduled.",
            "evidence_source_detail": "dispatch_assignments + trust_spine_events(dispatch-assignment)",
            "expected_cadence": "event-driven",
            "source_latest_activity": latest,
            "current_freshness_policy": f"{slot.get('freshness_window_hours')}h flat window before cadence override",
            "new_business_activity_expected": "only when a new dispatch assignment is created",
            "lack_of_activity_normal": "yes",
            "downstream_consumers": ["Dispatch workspace", "transportation execution", "admin operations views"],
            "regression_guard": "Any dispatch assignment created after the last successful Trust Spine completion must leave quiet-green immediately.",
        })
        if last_success_ts and not has_new_activity:
            slot.update({
                "cadence_classification": "C",
                "health_state": HEALTH_HEALTHY_QUIET,
                "band": "green",
                "freshness_status": "quiet_current",
                "reason": "No recent applicable dispatch assignment occurred; the most recent governed assignment processed correctly.",
                "remediation": None,
            })
        return

    if workflow == "inspection":
        latest_doc = await _latest_non_synthetic_safety_doc(db, "inspections", INSPECTION_FIELDS)
        latest_created = _parse_iso((latest_doc or {}).get("created_at"))
        latest_doc_id = str((latest_doc or {}).get("doc_id") or "")
        latest_events = await _find_event_record(db, workflow, latest_doc_id)
        latest_completed = any(row.get("stage") in {"completed", "completed_for_environment"} and row.get("status") == "ok" for row in latest_events)
        has_new_legit_activity = bool(last_success_ts and latest_created and latest_created > last_success_ts)
        slot.update({
            "business_purpose": "Routes a legitimate safety inspection through governed delivery proof when an inspection is filed.",
            "evidence_source_detail": "inspections + trust_spine_events(inspection)",
            "expected_cadence": "event-driven",
            "source_latest_activity": latest_doc,
            "current_freshness_policy": f"{slot.get('freshness_window_hours')}h flat window before cadence override",
            "new_business_activity_expected": "only when a legitimate inspection is submitted",
            "lack_of_activity_normal": "yes",
            "downstream_consumers": ["Safety dashboard", "field leadership", "executive safety rollups"],
            "regression_guard": "A newer legitimate inspection than the last successful Trust Spine completion must not remain quiet-green unless its lifecycle completes.",
        })
        if latest_completed or (last_success_ts and latest_created and latest_created <= last_success_ts):
            slot.update({
                "cadence_classification": "C",
                "health_state": HEALTH_HEALTHY_QUIET,
                "band": "green",
                "freshness_status": "quiet_current",
                "reason": "No newer legitimate inspection requires processing after the last successful inspection lifecycle.",
                "remediation": None,
            })
        elif has_new_legit_activity:
            slot.update({
                "cadence_classification": "A",
                "health_state": HEALTH_DEGRADED,
                "band": "amber",
                "reason": "A newer legitimate inspection exists, but its Trust Spine lifecycle never reached a truthful terminal stage.",
                "remediation": "Repair the inspection submission path so legitimate inspections emit a complete or completed-for-environment terminal event.",
            })
        return

    if workflow == "jha":
        latest_doc = await _latest_non_synthetic_safety_doc(db, "jhas", JHA_FIELDS)
        latest_doc_id = str((latest_doc or {}).get("doc_id") or "")
        latest_events = await _find_event_record(db, workflow, latest_doc_id)
        latest_completed = any(row.get("stage") in {"completed", "completed_for_environment"} and row.get("status") == "ok" for row in latest_events)
        latest_created = _parse_iso((latest_doc or {}).get("created_at"))
        slot.update({
            "business_purpose": "Captures a governed Job Hazard Analysis and its proof-chain when a legitimate JHA is submitted.",
            "evidence_source_detail": "jhas + trust_spine_events(jha)",
            "expected_cadence": "event-driven",
            "source_latest_activity": latest_doc,
            "current_freshness_policy": f"{slot.get('freshness_window_hours')}h flat window before cadence override",
            "new_business_activity_expected": "only when a legitimate JHA is submitted",
            "lack_of_activity_normal": "yes",
            "downstream_consumers": ["Safety dashboard", "field leadership", "executive safety rollups"],
            "regression_guard": "A controlled certification JHA must produce a truthful terminal Trust Spine stage before JHA can be marked healthy.",
        })
        if latest_completed or (last_success_ts and (latest_created is None or latest_created <= last_success_ts)):
            slot.update({
                "cadence_classification": "C",
                "health_state": HEALTH_HEALTHY_QUIET,
                "band": "green",
                "freshness_status": "quiet_current",
                "reason": "The latest legitimate or controlled-certification JHA already produced terminal proof and no newer JHA is pending.",
                "remediation": None,
            })
        else:
            slot.update({
                "cadence_classification": "E",
                "health_state": HEALTH_NOT_YET_EXERCISED,
                "band": "amber-no-activity",
                "reason": "A current governed preview certification chain for a legitimate JHA has not yet produced terminal proof, so executable readiness remains unproven.",
                "remediation": "Run one clearly tagged controlled-certification JHA through the real submission path and verify terminal Trust Spine proof.",
            })
        return

    if workflow == "operational-events-materialization":
        latest_source = await db.motive_events.find_one({}, {"_id": 0, "id": 1, "event_at": 1, "created_at": 1, "event_family": 1}, sort=[("created_at", -1)])
        latest_target = await db.operational_events.find_one({}, {"_id": 0, "id": 1, "occurred_at": 1, "updated_at": 1, "event_type": 1}, sort=[("updated_at", -1)])
        source_created = _parse_iso((latest_source or {}).get("created_at") or (latest_source or {}).get("event_at"))
        target_updated = _parse_iso((latest_target or {}).get("updated_at") or (latest_target or {}).get("occurred_at"))
        if source_created and target_updated and source_created > target_updated:
            slot.update({
                "cadence_classification": "D",
                "health_state": HEALTH_STALE,
                "band": "amber",
                "business_purpose": "Normalizes raw Motive presence events into canonical operational_events.",
                "evidence_source_detail": "motive_events → operational_events via routes.operational_events.materialize",
                "expected_cadence": "backlog-driven / infrastructure",
                "source_latest_activity": latest_source,
                "current_freshness_policy": f"{slot.get('freshness_window_hours')}h flat window before backlog-aware override",
                "new_business_activity_expected": "yes while newer raw motive_events exist",
                "lack_of_activity_normal": "no when raw motive_events are newer than operational_events",
                "downstream_consumers": ["Equipment Location", "operational intelligence", "transport verification"],
                "reason": "Raw motive_events are newer than the canonical operational_events read model, so the operational-events materialization state is truly stale.",
                "remediation": "Run the real materialization workflow against the current backlog and verify operational_events catches up to motive_events.",
                "regression_guard": "If motive_events.created_at is newer than operational_events.updated_at, materialization must not report healthy.",
            })
        elif source_created and target_updated and source_created <= target_updated:
            slot.update({
                "cadence_classification": "C",
                "health_state": HEALTH_HEALTHY_QUIET,
                "band": "green",
                "freshness_status": "quiet_current",
                "business_purpose": "Normalizes raw Motive presence events into canonical operational_events.",
                "evidence_source_detail": "motive_events → operational_events via routes.operational_events.materialize",
                "expected_cadence": "backlog-driven / infrastructure",
                "source_latest_activity": latest_source,
                "current_freshness_policy": f"{slot.get('freshness_window_hours')}h flat window before backlog-aware override",
                "new_business_activity_expected": "only when newer raw motive_events arrive than the current operational_events read model",
                "lack_of_activity_normal": "yes when no newer raw motive_events exist",
                "downstream_consumers": ["Equipment Location", "operational intelligence", "transport verification"],
                "reason": "No newer raw motive_events exist beyond the canonical operational_events read model, so the materialization workflow is healthy but quiet.",
                "remediation": None,
                "regression_guard": "If motive_events.created_at moves ahead of operational_events.updated_at, materialization must leave quiet-green immediately.",
            })
        return

    if workflow == "oppc-cost-code-plan":
        latest = await db.jobs_master.find_one(
            {"oppc_planning_lifecycle.last_mutated_at": {"$exists": True}},
            {"_id": 0, "project_number": 1, "oppc_planning_lifecycle": 1, "oppc_last_weekly_rollover": 1},
            sort=[("oppc_planning_lifecycle.last_mutated_at", -1)],
        )
        lifecycle = (latest or {}).get("oppc_planning_lifecycle") or {}
        rollover = (latest or {}).get("oppc_last_weekly_rollover") or {}
        latest_mutated = _parse_iso(lifecycle.get("last_mutated_at"))
        rollover_applied = _parse_iso(rollover.get("applied_at"))
        mutation_is_rollover_side_effect = bool(
            latest_mutated and rollover_applied and abs((latest_mutated - rollover_applied).total_seconds()) <= 90
        )
        if last_success_ts and latest_mutated and (latest_mutated <= last_success_ts or mutation_is_rollover_side_effect):
            slot.update({
                "cadence_classification": "F",
                "health_state": HEALTH_HEALTHY_QUIET,
                "band": "green",
                "freshness_status": "source_current",
                "business_purpose": "Tracks governed project schedule / cost-code plan edits when the planning source changes.",
                "evidence_source_detail": "jobs_master.oppc_planning_lifecycle + trust_spine_events(oppc-cost-code-plan)",
                "expected_cadence": "on-demand / source-mutation driven",
                "source_latest_activity": latest,
                "new_business_activity_expected": "only when a planner changes the cost-code schedule or planning lifecycle",
                "lack_of_activity_normal": "yes",
                "downstream_consumers": ["PM schedule workspace", "Monday review", "forecasting"],
                "reason": "No newer direct cost-code-plan mutation exists after the last successful lifecycle; the prior weekly freshness rule was too broad for this mutation-driven workflow.",
                "remediation": None,
                "regression_guard": "Compare oppc_planning_lifecycle.last_mutated_at to the latest successful Trust Spine completion before downgrading this workflow.",
            })
        return

    if workflow == "oppc-forecasting":
        latest_job = None
        latest_row = None
        async for job in db.jobs_master.find({"oppc_forecast_overrides.0": {"$exists": True}}, {"_id": 0, "project_number": 1, "oppc_forecast_overrides": 1}):
            for row in (job.get("oppc_forecast_overrides") or []):
                updated = _parse_iso(row.get("updated_at") or row.get("created_at"))
                if updated and (latest_row is None or updated > latest_row):
                    latest_row = updated
                    latest_job = {"project_number": job.get("project_number"), "override": row}
        if last_success_ts and latest_row and latest_row <= last_success_ts:
            slot.update({
                "cadence_classification": "F",
                "health_state": HEALTH_HEALTHY_QUIET,
                "band": "green",
                "freshness_status": "source_current",
                "business_purpose": "Captures governed forecast overrides only when forecast assumptions change.",
                "evidence_source_detail": "jobs_master.oppc_forecast_overrides + trust_spine_events(oppc-forecasting)",
                "expected_cadence": "on-demand / source-mutation driven",
                "source_latest_activity": latest_job,
                "new_business_activity_expected": "only when forecast assumptions or override windows change",
                "lack_of_activity_normal": "yes",
                "downstream_consumers": ["Forecasting workspace", "portfolio intelligence", "earned-value consumers"],
                "reason": "No newer forecasting mutation exists after the last successful forecasting lifecycle; the prior weekly freshness rule was too broad for this governed on-demand workflow.",
                "remediation": None,
                "regression_guard": "Compare the latest forecast override mutation to the latest successful Trust Spine completion before downgrading forecasting.",
            })
        return

    if workflow == "oppc-monday-look-behind":
        current_week = _current_week_ending(now.date())
        latest_completed_week = None
        async for row in db.trust_spine_events.find({"workflow": workflow, "stage": "completed", "status": "ok"}, {"_id": 0, "record_id": 1, "ts": 1}).sort("ts", -1).limit(1):
            latest_completed_week = str(row.get("record_id") or "").split(":")[-1]
        if latest_completed_week == current_week:
            slot.update({
                "cadence_classification": "B",
                "health_state": HEALTH_HEALTHY,
                "band": "green",
                "freshness_status": "cadence_current",
                "business_purpose": "Captures the weekly Monday look-behind review for the current governed week-ending cycle.",
                "evidence_source_detail": "jobs_master.oppc_monday_reviews + trust_spine_events(oppc-monday-look-behind)",
                "expected_cadence": "weekly / business-due",
                "new_business_activity_expected": f"yes — current cycle {current_week}",
                "lack_of_activity_normal": "no once the weekly cycle is due",
                "downstream_consumers": ["Monday review", "recovery planning", "C7/C8/C9 parity consumers"],
                "reason": f"The current Monday look-behind cycle for week ending {current_week} is complete and current.",
                "remediation": None,
                "regression_guard": "The current week-ending cycle must complete before Monday look-behind can remain healthy.",
            })
        else:
            slot.update({
                "cadence_classification": "E",
                "health_state": HEALTH_NOT_YET_EXERCISED,
                "band": "amber-no-activity",
                "business_purpose": "Captures the weekly Monday look-behind review for the current governed week-ending cycle.",
                "evidence_source_detail": "jobs_master.oppc_monday_reviews + trust_spine_events(oppc-monday-look-behind)",
                "expected_cadence": "weekly / business-due",
                "new_business_activity_expected": f"yes — current cycle {current_week}",
                "lack_of_activity_normal": "no once the weekly cycle is due",
                "downstream_consumers": ["Monday review", "recovery planning", "C7/C8/C9 parity consumers"],
                "reason": f"The current Monday look-behind cycle for week ending {current_week} has not been completed in this environment, so current certification evidence is missing.",
                "remediation": "Run one clearly tagged current-cycle Monday look-behind certification through start → review → complete.",
                "regression_guard": "The current week-ending cycle must complete before Monday look-behind can be marked healthy.",
            })
        return

    if workflow == "oppc-monday-morning-briefing":
        current_week = _current_week_ending(now.date())
        latest_doc = await db.oppc_monday_briefings.find_one({}, {"_id": 0, "week_ending": 1, "status": 1, "generated_at": 1, "approved_at": 1, "frozen_at": 1, "updated_at": 1}, sort=[("frozen_at", -1), ("updated_at", -1)])
        latest_frozen_week = str((latest_doc or {}).get("week_ending") or "") if str((latest_doc or {}).get("status") or "") == "frozen" else ""
        if latest_frozen_week == current_week:
            slot.update({
                "cadence_classification": "B",
                "health_state": HEALTH_HEALTHY,
                "band": "green",
                "freshness_status": "cadence_current",
                "business_purpose": "Generates, approves, and freezes the weekly Monday Morning Briefing package.",
                "evidence_source_detail": "oppc_monday_briefings + trust_spine_events(oppc-monday-morning-briefing)",
                "expected_cadence": "weekly / business-due",
                "new_business_activity_expected": f"yes — current cycle {current_week}",
                "lack_of_activity_normal": "no once the weekly cycle is due",
                "downstream_consumers": ["Executive Monday briefing", "PM briefing packet"],
                "reason": f"The current Monday briefing cycle for week ending {current_week} is frozen and current.",
                "remediation": None,
                "regression_guard": "The current week-ending cycle must remain frozen before Monday briefing can remain healthy.",
            })
        else:
            slot.update({
                "cadence_classification": "E",
                "health_state": HEALTH_NOT_YET_EXERCISED,
                "band": "amber-no-activity",
                "business_purpose": "Generates, approves, and freezes the weekly Monday Morning Briefing package.",
                "evidence_source_detail": "oppc_monday_briefings + trust_spine_events(oppc-monday-morning-briefing)",
                "expected_cadence": "weekly / business-due",
                "new_business_activity_expected": f"yes — current cycle {current_week}",
                "lack_of_activity_normal": "no once the weekly cycle is due",
                "downstream_consumers": ["Executive Monday briefing", "PM briefing packet"],
                "reason": f"The current Monday briefing cycle for week ending {current_week} has not been frozen in this environment, so current certification evidence is missing.",
                "remediation": "Run one clearly tagged current-cycle Monday briefing certification through generate → approve → freeze.",
                "regression_guard": "The current week-ending cycle must be frozen before Monday briefing can be marked healthy.",
            })
        return

    if workflow == "oppc-weekly-rollover":
        latest = await db.jobs_master.find_one({"oppc_last_weekly_rollover.applied_at": {"$exists": True}}, {"_id": 0, "project_number": 1, "oppc_last_weekly_rollover": 1}, sort=[("oppc_last_weekly_rollover.applied_at", -1)])
        rollover = (latest or {}).get("oppc_last_weekly_rollover") or {}
        anchor = _parse_date_only(rollover.get("rollover_anchor_date"))
        next_due = anchor + timedelta(days=7) if anchor else None
        if next_due and now.date() < next_due:
            slot.update({
                "cadence_classification": "B",
                "health_state": HEALTH_HEALTHY,
                "band": "green",
                "freshness_status": "cadence_current",
                "business_purpose": "Applies the governed weekly rollover when the next planning-cycle anchor is due.",
                "evidence_source_detail": "jobs_master.oppc_last_weekly_rollover + trust_spine_events(oppc-weekly-rollover)",
                "expected_cadence": "weekly / due-date anchored",
                "source_latest_activity": latest,
                "new_business_activity_expected": f"only when the next rollover anchor {next_due.isoformat()} is due",
                "lack_of_activity_normal": "yes before the next due anchor date",
                "downstream_consumers": ["Project schedule workspace", "Monday review planning window"],
                "reason": f"Weekly rollover is still within its governed cadence; the next rollover is not due until {next_due.isoformat()}.",
                "remediation": None,
                "regression_guard": "Do not downgrade weekly rollover before its next due anchor date.",
            })
        return

    if workflow == "shop-defect":
        latest = await db.fleet_defects.find_one({"inspection_kind": "manual_oos"}, {"_id": 0, "id": 1, "truck_unit_number": 1, "status": 1, "inspection_kind": 1}, sort=[("_id", -1)])
        latest_id = str((latest or {}).get("id") or "")
        last_record_id = str((last_success or {}).get("record_id") or "")
        if latest_id and latest_id == last_record_id:
            slot.update({
                "cadence_classification": "C",
                "health_state": HEALTH_HEALTHY_QUIET,
                "band": "green",
                "freshness_status": "quiet_current",
                "business_purpose": "Tracks manual out-of-service shop defects only when Dispatch flips a unit OOS.",
                "evidence_source_detail": "fleet_defects(manual_oos) + trust_spine_events(shop-defect)",
                "expected_cadence": "event-driven",
                "source_latest_activity": latest,
                "new_business_activity_expected": "only when a manual OOS flip occurs",
                "lack_of_activity_normal": "yes",
                "downstream_consumers": ["Shop defect panel", "dispatch / fleet OOS visibility"],
                "reason": "No recent applicable manual OOS flip occurred after the last successful shop-defect lifecycle.",
                "remediation": None,
                "regression_guard": "A new manual OOS defect after the last successful lifecycle must leave quiet-green immediately.",
            })
        return


def _workflow_impact_profile(workflow: str) -> Dict[str, str]:
    if workflow.startswith("oppc-"):
        return {
            "downstream_impact": "Project Controls, Monday Review, executive portfolio intelligence, and downstream C7/C8/C9 surfaces may reflect stale or incomplete planning evidence.",
            "c6_c7_c8_c9_impact": "Affects C6 operational intelligence lineage and can cascade into C7 forecasting, C8 earned value, and C9 portfolio truth if current planning evidence is incomplete.",
            "trustworthiness": "bounded_historical_only",
        }
    if workflow in {"incident", "inspection", "jha", "meeting", "qaqc", "equipment-inspection", "dvir"}:
        return {
            "downstream_impact": "Safety and field-compliance dashboards may only be trustworthy up to the latest captured evidence for this workflow.",
            "c6_c7_c8_c9_impact": "Indirect downstream impact via executive and operational dashboards; no direct C7/C8/C9 planning writeback.",
            "trustworthiness": "bounded_historical_only",
        }
    if workflow in {"dispatch-assignment", "shop-defect", "operational-events-materialization"}:
        return {
            "downstream_impact": "Admin operations, recovery, and dispatch/shop visibility can drift from the latest operational state until this evidence refreshes.",
            "c6_c7_c8_c9_impact": "Indirect trust-layer impact; stale materialization can hide or delay downstream truth propagation.",
            "trustworthiness": "bounded_historical_only",
        }
    if workflow == "hr-request":
        return {
            "downstream_impact": "Employee lifecycle queues and HR operational counts remain trustworthy only up to the latest captured request evidence.",
            "c6_c7_c8_c9_impact": "No direct C7/C8/C9 writeback; affects admin truth and staffing operational awareness.",
            "trustworthiness": "bounded_historical_only",
        }
    return {
        "downstream_impact": "Downstream consumers should treat the displayed data as incomplete until fresh lifecycle evidence is restored.",
        "c6_c7_c8_c9_impact": "No direct downstream impact mapping has been registered yet.",
        "trustworthiness": "no",
    }


def _workflow_root_cause(slot: Dict[str, Any]) -> str:
    workflow = str(slot.get("workflow") or "")
    classification = str(slot.get("cadence_classification") or "")
    missing = list(slot.get("missing_stages") or [])
    freshness = str(slot.get("freshness_status") or "unknown")
    latest_module = (slot.get("latest") or {}).get("module") or "unknown emitter"
    if classification == "C":
        return "No recent applicable business event occurred after the last legitimate successful lifecycle; the workflow is healthy but quiet."
    if classification == "B":
        return "The workflow is still inside its governed due-date cadence, so older evidence remains current."
    if classification == "E":
        return "The workflow lacks current governed certification evidence for the active cycle, so executable readiness is not yet proven in this environment."
    if classification == "F":
        return "The previous freshness policy was broader than the workflow semantics; this workflow should be judged by source mutation or due-date readiness rather than elapsed wall-clock time alone."
    if classification == "D":
        return "The underlying business or infrastructure state is genuinely stale relative to newer source activity, so downstream truth is behind."
    if workflow == "oppc-enterprise-resource-coordination" and missing:
        return (
            "The enterprise OPPC read paths emitted only dashboard_updated evidence, so the workflow never satisfied its "
            f"required lifecycle contract ({', '.join(missing)} missing) even when the screen rendered successfully."
        )
    if slot.get("failed_24h"):
        return str(((slot.get("last_failure") or {}).get("failure_reason")) or "A current lifecycle stage emitted a failed Trust Spine event.")
    if freshness == "stale":
        return (
            f"No fresh lifecycle evidence was captured inside the governed {slot.get('freshness_window_hours')}h window. "
            "The workflow has historical proof, but the current environment has not refreshed it within policy."
        )
    if freshness == "unavailable":
        return "No successful lifecycle evidence exists in trust_spine_events for this workflow yet, so current truth cannot be claimed."
    if missing:
        return (
            f"Current evidence exists, but {latest_module} did not emit the full expected lifecycle contract; "
            f"missing stage(s): {', '.join(missing)}."
        )
    return str(slot.get("reason") or "Lifecycle evidence is degraded.")


def _workflow_failing_dependency(slot: Dict[str, Any]) -> str:
    classification = str(slot.get("cadence_classification") or "")
    if classification == "C":
        return "none — waiting for the next real business event is normal for this workflow"
    if classification == "B":
        return "none — current cadence window has not reached the next due event"
    if classification == "E":
        return "controlled certification evidence for the active governed cycle has not yet been exercised"
    if classification == "F":
        return "Trust Spine freshness policy was broader than the workflow's actual cadence semantics"
    if classification == "D":
        return "current source activity exists beyond the latest canonical processed evidence"
    if slot.get("failed_24h"):
        return str(((slot.get("last_failure") or {}).get("module")) or ((slot.get("latest") or {}).get("module")) or "unresolved failing module")
    if slot.get("missing_stages"):
        return str(((slot.get("latest") or {}).get("module")) or "workflow emitter is not writing the full expected-stage contract")
    if str(slot.get("freshness_status") or "") == "stale":
        return "governed runtime exercise / certification refresh for this workflow is outside the allowed freshness window"
    if str(slot.get("freshness_status") or "") == "unavailable":
        return "no lifecycle execution has yet produced a successful trust-spine evidence chain for this workflow"
    return "none"


def _workflow_degradation_entry(slot: Dict[str, Any]) -> Dict[str, Any]:
    latest = slot.get("latest") or {}
    last_success = slot.get("last_success") or {}
    profile = _workflow_impact_profile(str(slot.get("workflow") or ""))
    return {
        "workflow": slot.get("workflow"),
        "band": slot.get("band"),
        "source_authority": {
            "canonical_collection": "trust_spine_events",
            "workflow_family": workflow_family(str(slot.get("workflow") or "")),
            "latest_emitter_module": latest.get("module") or last_success.get("module") or "—",
            "route": "/api/admin/trust-spine",
            "evidence_source_detail": slot.get("evidence_source_detail"),
        },
        "current_value_state": {
            "reason": slot.get("reason"),
            "health_state": slot.get("health_state"),
            "cadence_classification": slot.get("cadence_classification"),
            "events_24h": slot.get("events_24h"),
            "events_policy_window": slot.get("events_policy_window"),
            "missing_stages": slot.get("missing_stages"),
            "latest_evidence_ts": latest.get("ts"),
            "last_success_ts": last_success.get("ts"),
            "current_freshness_policy": slot.get("current_freshness_policy"),
        },
        "expected_value_state": {
            "freshness_window_hours": slot.get("freshness_window_hours"),
            "terminal_success_criteria": slot.get("terminal_success_criteria"),
            "expected_stages": slot.get("expected_stages"),
            "expected_cadence": slot.get("expected_cadence"),
            "new_business_activity_expected": slot.get("new_business_activity_expected"),
            "lack_of_activity_normal": slot.get("lack_of_activity_normal"),
        },
        "business_purpose": slot.get("business_purpose"),
        "last_legitimate_evidence": slot.get("source_latest_activity") or last_success,
        "freshness": {
            "status": slot.get("freshness_status"),
            "age_hours": slot.get("freshness_age_hours"),
            "window_hours": slot.get("freshness_window_hours"),
            "last_success_ts": last_success.get("ts"),
        },
        "failing_dependency": _workflow_failing_dependency(slot),
        "affected_workflows": [slot.get("workflow")],
        "downstream_consumers": slot.get("downstream_consumers") or [],
        "downstream_impact": profile["downstream_impact"],
        "c6_c7_c8_c9_impact": profile["c6_c7_c8_c9_impact"],
        "operator_data_trustworthy": profile["trustworthiness"],
        "root_cause": _workflow_root_cause(slot),
    }


def _parse_iso(ts: Optional[str]) -> Optional[datetime]:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts)
    except Exception:
        return None


def _latest_timestamp(*timestamps: Optional[str]) -> Optional[str]:
    latest: Optional[datetime] = None
    latest_raw: Optional[str] = None
    for ts in timestamps:
        dt = _parse_iso(ts)
        if dt and (latest is None or dt > latest):
            latest = dt
            latest_raw = ts
    return latest_raw


def _workflow_truth_projection(slot: Dict[str, Any], *, now_iso: str) -> Dict[str, Any]:
    contradictions: List[str] = []
    if slot.get("delivery_path") == "contradictory":
        contradictions.append(
            "Conflicting delivery-path evidence observed in the evaluation window: both provider acceptance and preview capture were recorded."
        )
    if slot.get("band") == "green" and slot.get("missing_stages"):
        contradictions.append(
            "Workflow was marked green while expected stages were still missing."
        )
    if slot.get("band") == "green" and int(slot.get("failed_24h") or 0) > 0:
        contradictions.append(
            "Workflow was marked green while failed lifecycle events were present."
        )

    latest_ts = _latest_timestamp(
        (slot.get("latest") or {}).get("ts"),
        (slot.get("last_success") or {}).get("ts"),
        (slot.get("last_failure") or {}).get("ts"),
    )

    failed_24h = int(slot.get("failed_24h") or 0)
    events_24h = int(slot.get("events_24h") or 0)
    missing_stages = list(slot.get("missing_stages") or [])

    freshness_status = str(slot.get("freshness_status") or "unknown")

    if contradictions:
        evidence_state = "contradicted"
        evidence_quality = "CORRELATED"
        evidence_confidence = "MEDIUM"
        truth_evaluation = "MISMATCH"
        permitted_claim = CORRELATED
    elif failed_24h > 0:
        evidence_state = "validated_failure"
        evidence_quality = "VALIDATED"
        evidence_confidence = "HIGH"
        truth_evaluation = "MISMATCH"
        permitted_claim = VALIDATED
    elif freshness_status == "stale":
        evidence_state = "stale"
        evidence_quality = "DURABLE_OBSERVED"
        evidence_confidence = "LOW"
        truth_evaluation = "DEGRADED"
        permitted_claim = OBSERVED
    elif freshness_status == "unavailable":
        evidence_state = "unavailable"
        evidence_quality = "UNAVAILABLE"
        evidence_confidence = "UNKNOWN"
        truth_evaluation = "DEGRADED"
        permitted_claim = OBSERVED
    elif missing_stages:
        evidence_state = "partial"
        evidence_quality = "VALIDATED"
        evidence_confidence = "MEDIUM"
        truth_evaluation = "DEGRADED"
        permitted_claim = VERIFIED
    else:
        evidence_state = "validated"
        evidence_quality = "VALIDATED"
        evidence_confidence = "HIGH"
        truth_evaluation = "VERIFIED"
        permitted_claim = VALIDATED

    degradation_reasons: List[str] = []
    if slot.get("band") in {"red", "amber", "amber-no-activity"}:
        degradation_reasons.append(str(slot.get("reason") or "Lifecycle evidence is degraded."))

    unknowns: List[str] = []
    if freshness_status == "stale":
        unknowns.append(
            f"Latest successful evidence is {slot.get('freshness_age_hours')}h old, beyond the governed {slot.get('freshness_window_hours')}h freshness window."
        )
    elif freshness_status == "unavailable":
        unknowns.append("No successful lifecycle evidence has been captured for this workflow yet.")
    elif missing_stages:
        unknowns.append("The expected-stage contract is incomplete in the current evaluation window.")

    claim_basis = [
        "trust_spine_events",
        "expected_stage_contract",
        "events_24h",
    ]
    if slot.get("delivery_path"):
        claim_basis.append(f"delivery_path:{slot['delivery_path']}")
    if latest_ts:
        claim_basis.append("latest_workflow_event")
    if failed_24h > 0:
        claim_basis.append("failed_lifecycle_event")

    truth_card = canonical_truth_card(
        truth_subject="workflow_lifecycle_truth",
        canonical_owner="trust_spine",
        truth_surface_id="trust_spine",
        evidence_state=evidence_state,
        evidence_quality=evidence_quality,
        evidence_confidence=evidence_confidence,
        truth_evaluation=truth_evaluation,
        permitted_claim=permitted_claim,
        claim_ceiling=VALIDATED,
        claim_basis=claim_basis,
        prohibited_claims=[
            "platform-wide health",
            "recovery readiness",
            "deployment readiness",
            "operational certification",
            "CERTIFIED",
        ],
        degradation_reasons=degradation_reasons,
        unknowns=unknowns,
        contradictory_evidence=contradictions,
        evidence_timestamp=latest_ts or now_iso,
        evaluation_timestamp=now_iso,
        audit_reference="OTS-C6-TRUST-SPINE-WORKFLOW",
        evidence_required_to_raise_claim=[
            "independent certification decision evidence for any broader operational claim",
            "cross-domain evidence outside workflow lifecycle scope",
        ],
        notes=[
            "This workflow projection validates lifecycle evidence only.",
            "Expected-stage completion does not imply platform health, recovery readiness, or deployment readiness.",
        ],
    )
    return {
        "ots_truth": public_ots_projection(truth_card),
        "truth_relationship": projected_truth_relationship(
            surface_id="trust_spine",
            card=truth_card,
            canonical_owner_route="/api/admin/trust-spine",
            derivation_explanation=f"{slot.get('workflow') or 'workflow'} lifecycle truth is projected from trust_spine_events, the expected-stage contract, and the workflow-specific freshness policy.",
            derived_status=truth_card["truth_evaluation"],
        ),
    }


def _route_truth_projection(
    *,
    rows: List[Dict[str, Any]],
    total_events_24h: int,
    total_failed_24h: int,
    platform_band: str,
    canonical_status: str,
    now_iso: str,
) -> Dict[str, Any]:
    contradictions: List[str] = []
    idle_count = 0
    partial_count = 0
    failed_count = 0
    latest_ts: Optional[str] = None
    for row in rows:
        row_truth = row.get("ots_truth") or {}
        contradictions.extend(list(row_truth.get("contradictory_evidence") or []))
        latest_ts = _latest_timestamp(latest_ts, row_truth.get("evidence_timestamp"))
        if row.get("band") == "amber-no-activity":
            idle_count += 1
        elif row.get("band") == "amber":
            partial_count += 1
        elif row.get("band") == "red":
            failed_count += 1

    if platform_band == "green" and (idle_count or partial_count or failed_count):
        contradictions.append(
            "Aggregate platform band was green while one or more workflows were degraded or failing."
        )

    if contradictions:
        evidence_state = "contradicted"
        evidence_quality = "CORRELATED"
        evidence_confidence = "MEDIUM"
        permitted_claim = CORRELATED
    elif total_events_24h == 0:
        evidence_state = "observed"
        evidence_quality = "DURABLE_OBSERVED"
        evidence_confidence = "LOW"
        permitted_claim = OBSERVED
    elif partial_count or idle_count:
        evidence_state = "partial"
        evidence_quality = "VALIDATED"
        evidence_confidence = "MEDIUM"
        permitted_claim = VERIFIED
    else:
        evidence_state = "validated"
        evidence_quality = "VALIDATED"
        evidence_confidence = "HIGH"
        permitted_claim = VALIDATED

    degradation_reasons: List[str] = []
    if failed_count:
        degradation_reasons.append(f"{failed_count} workflow(s) emitted failed lifecycle evidence in the current window.")
    if partial_count:
        degradation_reasons.append(f"{partial_count} workflow(s) are missing one or more expected stages.")
    if idle_count:
        degradation_reasons.append(f"{idle_count} workflow(s) have no current lifecycle evidence inside their governed freshness windows.")

    unknowns: List[str] = []
    if total_events_24h == 0:
        unknowns.append("No workflow emitted lifecycle evidence in the last 24 hours.")
    elif idle_count:
        unknowns.append("Stale or unavailable workflows remain evidence gaps, not proof of workflow health.")

    truth_card = canonical_truth_card(
        truth_subject="workflow_lifecycle_truth",
        canonical_owner="trust_spine",
        truth_surface_id="trust_spine",
        evidence_state=evidence_state,
        evidence_quality=evidence_quality,
        evidence_confidence=evidence_confidence,
        truth_evaluation=canonical_status,
        permitted_claim=permitted_claim,
        claim_ceiling=VALIDATED,
        claim_basis=[
            "trust_spine_events",
            "expected_stage_contract",
            "per_workflow_rollup_24h",
            "workflow_specific_freshness_policy",
            "workflow_band_summary",
        ],
        prohibited_claims=[
            "platform-wide health",
            "recovery readiness",
            "deployment readiness",
            "operational certification",
            "CERTIFIED",
        ],
        degradation_reasons=degradation_reasons,
        unknowns=unknowns,
        contradictory_evidence=sorted(set(contradictions)),
        evidence_timestamp=latest_ts or now_iso,
        evaluation_timestamp=now_iso,
        audit_reference="OTS-C6-TRUST-SPINE",
        evidence_required_to_raise_claim=[
            "independent certification decision evidence for any broader operational claim",
            "cross-domain owner evidence outside workflow lifecycle scope",
        ],
        notes=[
            "Trust Spine validates workflow lifecycle evidence only.",
            "Completed expected-stage rollups do not imply recovery readiness, deployment readiness, or platform-wide health.",
        ],
    )
    return {
        "ots_truth": public_ots_projection(truth_card),
        "truth_relationship": projected_truth_relationship(
            surface_id="trust_spine",
            card=truth_card,
            canonical_owner_route="/api/admin/trust-spine",
            derivation_explanation="Workflow lifecycle truth is evaluated from trust_spine_events and the expected-stage contract without upgrading broader operational claims.",
            derived_status=truth_card["truth_evaluation"],
        ),
        "compatibility": compatibility_projection(
            preserved_fields=11,
            deprecated_fields=0,
            new_fields=2,
            alias_fields=[],
            breaking_changes=0,
        ),
    }


def make_router(db, require_admin_only_dep) -> APIRouter:
    router = APIRouter()

    @router.get("/api/admin/trust-spine")
    async def trust_spine(_: Any = Depends(require_admin_only_dep)) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        since_24h = (now - timedelta(hours=24)).isoformat()

        # Aggregate per workflow / stage / status counts (last 24h)
        workflows: Dict[str, Dict[str, Any]] = {}
        async for row in db.trust_spine_events.aggregate([
            {"$match": {"ts": {"$gte": since_24h}}},
            {"$group": {
                "_id": {"workflow": "$workflow", "stage": "$stage", "status": "$status"},
                "n": {"$sum": 1},
            }},
        ]):
            source_wf = (row["_id"].get("workflow") or "") or "unknown"
            stage = row["_id"].get("stage") or "unknown"
            status = row["_id"].get("status") or "unknown"
            for wf in canonical_workflows_for_event(source_wf):
                slot = workflows.setdefault(wf, {
                    "workflow": wf,
                    "events_24h": 0,
                    "ok_24h": 0,
                    "failed_24h": 0,
                    "skipped_24h": 0,
                    "stages_seen": {},
                    "stages_failed": {},
                })
                n = int(row["n"])
                slot["events_24h"] += n
                slot[f"{status}_24h"] = slot.get(f"{status}_24h", 0) + n
                slot["stages_seen"][stage] = slot["stages_seen"].get(stage, 0) + n
                if status == "failed":
                    slot["stages_failed"][stage] = slot["stages_failed"].get(stage, 0) + n

        # Ensure every workflow listed in the expected contract appears
        # in the dashboard — even if it produced zero events — so the
        # operator can see idle workflows as AMBER-NO-ACTIVITY rather
        # than missing entirely.
        for known_wf in WORKFLOW_EXPECTED_STAGES.keys():
            workflows.setdefault(known_wf, {
                "workflow": known_wf,
                "events_24h": 0,
                "ok_24h": 0,
                "failed_24h": 0,
                "skipped_24h": 0,
                "stages_seen": {},
                "stages_failed": {},
            })

        for wf, slot in workflows.items():
            wf_selector = {"workflow": {"$in": workflow_family(wf)}} if len(workflow_family(wf)) > 1 else {"workflow": wf}
            latest = await db.trust_spine_events.find_one(
                wf_selector, sort=[("ts", -1)],
                projection={"_id": 0},
            )
            slot["latest"] = latest
            slot["last_failure"] = await db.trust_spine_events.find_one(
                {**wf_selector, "status": "failed"},
                sort=[("ts", -1)],
                projection={"_id": 0},
            )
            last_ok = await db.trust_spine_events.find_one(
                {**wf_selector, "status": "ok"},
                sort=[("ts", -1)],
                projection={"_id": 0, "ts": 1, "stage": 1, "record_id": 1},
            )
            slot["last_success"] = last_ok

            policy_window_hours = _workflow_policy_window_hours(wf)
            policy_since_iso = (now - timedelta(hours=policy_window_hours)).isoformat()
            policy_stage_counts: Dict[str, int] = {}
            policy_stage_failures: Dict[str, int] = {}
            policy_events = 0
            partial_chain_missing: List[str] = []
            async for policy_row in db.trust_spine_events.aggregate([
                {"$match": {**wf_selector, "ts": {"$gte": policy_since_iso}}},
                {"$group": {
                    "_id": {"stage": "$stage", "status": "$status"},
                    "n": {"$sum": 1},
                }},
            ]):
                stage = policy_row["_id"].get("stage") or "unknown"
                status = policy_row["_id"].get("status") or "unknown"
                n = int(policy_row.get("n") or 0)
                policy_events += n
                policy_stage_counts[stage] = policy_stage_counts.get(stage, 0) + n
                if status == "failed":
                    policy_stage_failures[stage] = policy_stage_failures.get(stage, 0) + n

            slot["policy_since"] = policy_since_iso
            slot["events_policy_window"] = policy_events
            slot["freshness_window_hours"] = policy_window_hours
            slot["policy_stages_seen"] = policy_stage_counts
            slot["policy_stages_failed"] = policy_stage_failures
            policy = WORKFLOW_CERTIFICATION_POLICIES.get(wf)
            slot["terminal_success_criteria"] = getattr(policy, "terminal_success_criteria", "Complete expected-stage contract with current evidence.")

            latest_success_ts = (last_ok or {}).get("ts")
            freshness_age_hours = _hours_since(latest_success_ts or (latest or {}).get("ts"), now)
            slot["freshness_age_hours"] = freshness_age_hours
            if latest_success_ts and freshness_age_hours is not None and freshness_age_hours <= policy_window_hours:
                slot["freshness_status"] = "current"
            elif latest_success_ts:
                slot["freshness_status"] = "stale"
            else:
                slot["freshness_status"] = "unavailable"

            base_expected = list(WORKFLOW_EXPECTED_STAGES.get(wf, []))
            expected = list(base_expected)
            seen_ok_stages = set()
            if wf in PREVIEW_SAFE_DELIVERY_WORKFLOWS:
                provider_ok = policy_stage_counts.get("provider_accepted", 0) - policy_stage_failures.get("provider_accepted", 0) > 0
                preview_ok = policy_stage_counts.get("delivery_captured_preview", 0) - policy_stage_failures.get("delivery_captured_preview", 0) > 0
                completed_ok = policy_stage_counts.get("completed", 0) - policy_stage_failures.get("completed", 0) > 0
                completed_env_ok = policy_stage_counts.get("completed_for_environment", 0) - policy_stage_failures.get("completed_for_environment", 0) > 0
                dvir_no_alert_path = wf == "dvir" and not (provider_ok or preview_ok or policy_stage_counts.get("notification_queued", 0) > 0)
                if dvir_no_alert_path:
                    expected = [
                        "record_created", "validation_complete",
                        "audit_written", "dashboard_updated", "completed",
                    ]
                else:
                    expected = [
                        "record_created", "routing_resolved", "recipients_built",
                        "notification_queued", "audit_written",
                    ]
                if provider_ok and preview_ok:
                    expected = [*expected, "provider_accepted", "delivery_captured_preview", "completed", "completed_for_environment"]
                elif provider_ok:
                    expected = [*expected, "provider_accepted", "completed"]
                elif preview_ok:
                    expected = [*expected, "delivery_captured_preview", "completed_for_environment"]
                elif not dvir_no_alert_path:
                    expected = [*expected, "provider_accepted"]
                slot["delivery_path"] = (
                    "contradictory" if provider_ok and preview_ok else
                    "provider_live" if provider_ok else
                    "preview_capture" if preview_ok else
                    "not_required" if dvir_no_alert_path else
                    "unresolved"
                )
                slot["delivery_terminal_stage_ok"] = provider_ok or preview_ok or completed_ok or completed_env_ok
            # A stage is "satisfied" only if we have at least one ok
            # event for it inside the workflow freshness window.
            for stg in expected:
                if policy_stage_counts.get(stg, 0) - policy_stage_failures.get(stg, 0) > 0:
                    seen_ok_stages.add(stg)
            missing_stages = [s for s in expected if s not in seen_ok_stages]
            if wf == "daily-report" and expected and policy_events > 0:
                latest_chain = await db.trust_spine_events.aggregate([
                    {"$match": {**wf_selector, "ts": {"$gte": policy_since_iso}, "correlation_id": {"$exists": True, "$ne": None}}},
                    {"$group": {
                        "_id": {"correlation_id": "$correlation_id", "stage": "$stage", "status": "$status"},
                        "latest_ts": {"$max": "$ts"},
                    }},
                    {"$group": {
                        "_id": "$_id.correlation_id",
                        "stage_statuses": {"$push": {"stage": "$_id.stage", "status": "$_id.status"}},
                        "latest_ts": {"$max": "$latest_ts"},
                    }},
                    {"$sort": {"latest_ts": -1}},
                    {"$limit": 1},
                ]).to_list(1)
                for chain in latest_chain:
                    chain_seen_ok = {
                        entry.get("stage")
                        for entry in (chain.get("stage_statuses") or [])
                        if entry.get("status") == "ok"
                    }
                    if not chain_seen_ok:
                        continue
                    chain_missing = [stage for stage in expected if stage not in chain_seen_ok]
                    if chain_missing:
                        partial_chain_missing = chain_missing
                        break
            if partial_chain_missing:
                missing_stages = partial_chain_missing
            slot["expected_stages"] = base_expected
            slot["missing_stages"] = missing_stages

            # Band logic.
            success_rate_24h = (
                (slot["ok_24h"] / slot["events_24h"]) if slot["events_24h"] else 0.0
            )
            slot["success_rate_24h"] = round(success_rate_24h, 3)

            if slot["failed_24h"] > 0:
                slot["band"] = "red"
                # Surface the most recent failure's specific stage.
                lf = slot["last_failure"] or {}
                slot["failure_stage"] = lf.get("stage") or "unknown"
                slot["reason"] = (
                    f"{slot['failed_24h']} failed lifecycle event(s) at "
                    f"{slot['failure_stage']}: "
                    f"{(lf.get('failure_reason') or '—')[:120]}"
                )
                slot["remediation"] = lf.get("remediation") or (
                    "Inspect backend logs and re-run the failing workflow."
                )
            elif missing_stages and policy_events > 0:
                slot["band"] = "amber"
                slot["failure_stage"] = missing_stages[0]
                slot["reason"] = (
                    f"current evidence is missing expected stage(s): {', '.join(missing_stages)}"
                )
                slot["remediation"] = (
                    "Wire missing stages into this workflow; partial evidence "
                    "is not green."
                )
            elif slot["freshness_status"] == "current":
                slot["band"] = "green"
                slot["failure_stage"] = None
                slot["reason"] = (
                    f"evidence is current inside the {policy_window_hours}h policy window with "
                    f"{len(seen_ok_stages)}/{len(expected) or 1} expected stage(s) satisfied"
                )
                slot["remediation"] = None
            elif slot["events_24h"] == 0:
                slot["band"] = "amber-no-activity"
                slot["failure_stage"] = None
                if slot["freshness_status"] == "stale":
                    slot["reason"] = (
                        f"latest successful evidence is {freshness_age_hours}h old, beyond the governed {policy_window_hours}h freshness window"
                    )
                    slot["remediation"] = "Refresh this workflow through its governed runtime path so current evidence is captured."
                else:
                    slot["reason"] = "no lifecycle evidence has been captured for this workflow yet"
                    slot["remediation"] = "Exercise the governed runtime path for this workflow to establish an initial evidence chain."
            else:
                slot["band"] = "green"
                slot["failure_stage"] = None
                slot["reason"] = (
                    f"evidence is current inside the {policy_window_hours}h policy window with "
                    f"{len(seen_ok_stages)}/{len(expected) or 1} expected stage(s) satisfied"
                )
                slot["remediation"] = None

            await _apply_cadence_semantics(db, slot, now=now)

            profile = _workflow_impact_profile(wf)
            slot["root_cause"] = _workflow_root_cause(slot)
            slot["failing_dependency"] = _workflow_failing_dependency(slot)
            slot["downstream_impact"] = profile["downstream_impact"]
            slot["c6_c7_c8_c9_impact"] = profile["c6_c7_c8_c9_impact"]
            slot["operator_data_trustworthy"] = profile["trustworthiness"]

            slot.update(_workflow_truth_projection(slot, now_iso=now.isoformat()))

        # Sort rows: red first, then amber-no-activity, then amber, then green.
        band_order = {"red": 0, "amber": 1, "amber-no-activity": 2, "green": 3}
        rows: List[Dict[str, Any]] = sorted(
            workflows.values(),
            key=lambda r: (band_order.get(r["band"], 99), -r["events_24h"], r["workflow"]),
        )

        # Total counters.
        total_events_24h = await db.trust_spine_events.count_documents(
            {"ts": {"$gte": since_24h}}
        )
        total_failed_24h = await db.trust_spine_events.count_documents(
            {"ts": {"$gte": since_24h}, "status": "failed"}
        )

        # Universal platform band: red if ANY workflow is red, amber if
        # any workflow is amber (incl. no-activity), else green.
        if any(r["band"] == "red" for r in rows):
            platform_band = "red"
            canonical_status = "MISMATCH"
        elif any(r["band"] in {"amber", "amber-no-activity"} for r in rows):
            platform_band = "amber"
            canonical_status = "DEGRADED"
        else:
            platform_band = "green"
            canonical_status = "VERIFIED"

        route_truth = _route_truth_projection(
            rows=rows,
            total_events_24h=total_events_24h,
            total_failed_24h=total_failed_24h,
            platform_band=platform_band,
            canonical_status=canonical_status,
            now_iso=now.isoformat(),
        )

        public_platform_band = "yellow" if platform_band == "amber" else platform_band

        return {
            "track": "15.76",
            "generated_at": now.isoformat(),
            "platform_band": public_platform_band,
            "platform_band_internal": platform_band,
            "canonical_status": canonical_status,
            "truth_surface": canonical_truth_surface("trust_spine"),
            "ots_truth": route_truth["ots_truth"],
            "truth_relationship": route_truth["truth_relationship"],
            "compatibility": route_truth["compatibility"],
            "total_events_24h": total_events_24h,
            "total_failed_24h": total_failed_24h,
            "workflow_count": len(rows),
            "workflows": rows,
            "degraded_components": [
                _workflow_degradation_entry(row)
                for row in rows
                if row.get("band") != "green"
            ],
            "allowed_stages": sorted([
                "record_created", "validation_complete", "routing_resolved",
                "recipients_built", "notification_queued", "delivery_captured_preview",
                "provider_accepted", "audit_written", "dashboard_updated", "completed",
                "completed_for_environment",
            ]),
        }

    @router.get("/api/admin/trust-spine/workflow/{workflow}")
    async def trust_spine_workflow_drilldown(
        workflow: str,
        limit: int = 50,
        _: Any = Depends(require_admin_only_dep),
    ) -> Dict[str, Any]:
        """Drill-in: last ``limit`` lifecycle events for a single workflow.

        Lets the operator see the exact record_ids, stages, and failure
        reasons without leaving the dashboard or running a Mongo query.
        """
        limit = max(1, min(int(limit or 50), 500))
        rows: List[Dict[str, Any]] = []
        wf_family = workflow_family(workflow)
        cursor = db.trust_spine_events.find(
            {"workflow": {"$in": wf_family}} if len(wf_family) > 1 else {"workflow": workflow},
            {"_id": 0},
            sort=[("ts", -1)],
            limit=limit,
        )
        async for r in cursor:
            rows.append(r)
        return {
            "workflow": workflow,
            "count": len(rows),
            "expected_stages": WORKFLOW_EXPECTED_STAGES.get(workflow, []),
            "events": rows,
        }

    return router
