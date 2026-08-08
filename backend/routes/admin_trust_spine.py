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

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends

from lib.canonical_truth import canonical_truth_surface
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


def _workflow_policy_window_hours(workflow: str) -> int:
    policy = WORKFLOW_CERTIFICATION_POLICIES.get(workflow)
    return int(getattr(policy, "stale_threshold_hours", 24) or 24)


def _hours_since(ts: Optional[str], now: datetime) -> Optional[float]:
    dt = _parse_iso(ts)
    if not dt:
        return None
    return round((now - dt).total_seconds() / 3600.0, 1)


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
    missing = list(slot.get("missing_stages") or [])
    freshness = str(slot.get("freshness_status") or "unknown")
    latest_module = (slot.get("latest") or {}).get("module") or "unknown emitter"
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
        },
        "current_value_state": {
            "reason": slot.get("reason"),
            "events_24h": slot.get("events_24h"),
            "events_policy_window": slot.get("events_policy_window"),
            "missing_stages": slot.get("missing_stages"),
            "latest_evidence_ts": latest.get("ts"),
            "last_success_ts": last_success.get("ts"),
        },
        "expected_value_state": {
            "freshness_window_hours": slot.get("freshness_window_hours"),
            "terminal_success_criteria": slot.get("terminal_success_criteria"),
            "expected_stages": slot.get("expected_stages"),
        },
        "freshness": {
            "status": slot.get("freshness_status"),
            "age_hours": slot.get("freshness_age_hours"),
            "window_hours": slot.get("freshness_window_hours"),
            "last_success_ts": last_success.get("ts"),
        },
        "failing_dependency": _workflow_failing_dependency(slot),
        "affected_workflows": [slot.get("workflow")],
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

            expected = WORKFLOW_EXPECTED_STAGES.get(wf, [])
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
            slot["expected_stages"] = list(expected)
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

        return {
            "track": "15.76",
            "generated_at": now.isoformat(),
            "platform_band": platform_band,
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
