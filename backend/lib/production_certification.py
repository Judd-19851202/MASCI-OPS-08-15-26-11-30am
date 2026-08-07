"""TRACK 15.79E · Continuous Production Certification.

Derives per-workflow operational certification from the existing
``trust_spine_events`` collection (single source of truth — no
dual-write, no separate state, no drift).

Status state machine (closed set):

  VERIFIED          ─ most recent qualifying ``completed`` event has
                      ``status=ok`` and evidence is current
  FAILED            ─ most recent qualifying ``completed`` event has
                      ``status=failed``
  NOT_YET_EXERCISED ─ no qualifying execution exists
  BLOCKED           ─ execution began (or was required) but could not
                      complete because of a documented blocker
  STALE             ─ qualifying evidence exists but is outside the
                      freshness window

Rules locked by regression:

  * VERIFIED requires a real Trust Spine terminal success event. For
    live-provider paths that is ``completed/ok``. For preview-safe
    capture paths that is ``completed_for_environment/ok``.
  * NOT_YET_EXERCISED is informational, not a defect.
  * RED never clears automatically. Only a fresh ``completed/ok``
    event (post the most recent failure) flips a workflow from
    FAILED back to VERIFIED.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from lib.trust_spine import WORKFLOW_EXPECTED_STAGES, workflow_family


STATUS_VERIFIED = "VERIFIED"
STATUS_FAILED = "FAILED"
STATUS_NOT_YET_EXERCISED = "NOT_YET_EXERCISED"
STATUS_BLOCKED = "BLOCKED"
STATUS_STALE = "STALE"

FRESHNESS_WINDOW = timedelta(days=2)


@dataclass(frozen=True)
class WorkflowCertificationPolicy:
    workflow: str
    evidence_type: str
    freshness_sla_hours: float
    acceptable_execution_frequency: str
    terminal_success_criteria: str
    stale_threshold_hours: float
    failure_threshold: str
    not_applicable_behavior: str
    rationale: str


WORKFLOW_CERTIFICATION_POLICIES: Dict[str, WorkflowCertificationPolicy] = {
    "daily-report": WorkflowCertificationPolicy(
        workflow="daily-report",
        evidence_type="daily report submission + notification proof chain",
        freshness_sla_hours=36,
        acceptable_execution_frequency="daily / every operating day",
        terminal_success_criteria="completed or completed_for_environment with status=ok after routing, recipients, queue/audit chain",
        stale_threshold_hours=36,
        failure_threshold="most recent terminal event is failed",
        not_applicable_behavior="never silently pass; remains NOT_YET_EXERCISED until a terminal success exists",
        rationale="Daily reports are expected frequently enough that evidence older than roughly one workday is stale.",
    ),
    "meeting": WorkflowCertificationPolicy(
        workflow="meeting",
        evidence_type="meeting record delivery lifecycle",
        freshness_sla_hours=168,
        acceptable_execution_frequency="at least weekly when the workflow is in active operational use",
        terminal_success_criteria="completed status=ok after provider accepted and audit written",
        stale_threshold_hours=168,
        failure_threshold="most recent terminal event is failed",
        not_applicable_behavior="if the workflow is not used in the period, retain NOT_YET_EXERCISED; do not auto-promote to VERIFIED",
        rationale="Meeting workflows are recurring but not guaranteed daily, so a weekly freshness window is operationally defensible.",
    ),
    "inspection": WorkflowCertificationPolicy(
        workflow="inspection",
        evidence_type="inspection submission + delivery lifecycle",
        freshness_sla_hours=168,
        acceptable_execution_frequency="at least weekly while inspection workflows are active",
        terminal_success_criteria="completed status=ok after provider accepted and audit written",
        stale_threshold_hours=168,
        failure_threshold="most recent terminal event is failed",
        not_applicable_behavior="NOT_YET_EXERCISED until real evidence exists",
        rationale="Inspections are operationally frequent but not guaranteed multiple times per day across all tenants.",
    ),
    "incident": WorkflowCertificationPolicy(
        workflow="incident",
        evidence_type="incident submission + delivery lifecycle",
        freshness_sla_hours=336,
        acceptable_execution_frequency="event-driven; evidence should refresh within 14 days in a live safety program",
        terminal_success_criteria="completed status=ok after provider accepted and audit written",
        stale_threshold_hours=336,
        failure_threshold="most recent terminal event is failed",
        not_applicable_behavior="do not fabricate green when no incidents occur; remain NOT_YET_EXERCISED or STALE based on last real evidence",
        rationale="Incident workflows are event-driven, so the window must be longer than daily scheduled workflows.",
    ),
    "jha": WorkflowCertificationPolicy(
        workflow="jha",
        evidence_type="JHA submission + delivery lifecycle",
        freshness_sla_hours=168,
        acceptable_execution_frequency="at least weekly on active crews",
        terminal_success_criteria="completed status=ok after provider accepted and audit written",
        stale_threshold_hours=168,
        failure_threshold="most recent terminal event is failed",
        not_applicable_behavior="NOT_YET_EXERCISED until a real JHA lifecycle succeeds",
        rationale="JHAs are common field workflows and should show fresh evidence at least weekly.",
    ),
    "qaqc": WorkflowCertificationPolicy(
        workflow="qaqc",
        evidence_type="QA/QC submission + delivery lifecycle",
        freshness_sla_hours=168,
        acceptable_execution_frequency="at least weekly on active work",
        terminal_success_criteria="completed status=ok after provider accepted and audit written",
        stale_threshold_hours=168,
        failure_threshold="most recent terminal event is failed",
        not_applicable_behavior="NOT_YET_EXERCISED until a real QA/QC lifecycle succeeds",
        rationale="QA/QC workflows are recurring but not guaranteed daily.",
    ),
    "equipment-inspection": WorkflowCertificationPolicy(
        workflow="equipment-inspection",
        evidence_type="equipment inspection submission + delivery lifecycle",
        freshness_sla_hours=72,
        acceptable_execution_frequency="multiple times per week while equipment operations are active",
        terminal_success_criteria="completed status=ok after provider accepted and audit written",
        stale_threshold_hours=72,
        failure_threshold="most recent terminal event is failed",
        not_applicable_behavior="NOT_YET_EXERCISED until inspection evidence exists",
        rationale="Equipment inspections are higher-cadence operational safety checks and should remain fresher than generic weekly workflows.",
    ),
    "dvir": WorkflowCertificationPolicy(
        workflow="dvir",
        evidence_type="DVIR submission + delivery lifecycle",
        freshness_sla_hours=36,
        acceptable_execution_frequency="daily while fleet operations are active",
        terminal_success_criteria="completed status=ok after provider accepted and audit written",
        stale_threshold_hours=36,
        failure_threshold="most recent terminal event is failed",
        not_applicable_behavior="NOT_YET_EXERCISED until a real DVIR lifecycle succeeds",
        rationale="DVIR is a daily fleet-safety workflow and needs a tighter SLA.",
    ),
    "hr-request": WorkflowCertificationPolicy(
        workflow="hr-request",
        evidence_type="HR request intake lifecycle",
        freshness_sla_hours=168,
        acceptable_execution_frequency="weekly or on demand",
        terminal_success_criteria="completed status=ok after validation, routing, dashboard update, and audit write",
        stale_threshold_hours=168,
        failure_threshold="most recent terminal event is failed",
        not_applicable_behavior="NOT_YET_EXERCISED until an HR request lifecycle succeeds",
        rationale="HR requests are important but event-driven; a weekly SLA is operationally reasonable.",
    ),
    "dispatch-assignment": WorkflowCertificationPolicy(
        workflow="dispatch-assignment",
        evidence_type="dispatch assignment routing lifecycle",
        freshness_sla_hours=72,
        acceptable_execution_frequency="several times per week in active dispatch operations",
        terminal_success_criteria="completed status=ok after routing, dashboard update, and audit write",
        stale_threshold_hours=72,
        failure_threshold="most recent terminal event is failed",
        not_applicable_behavior="NOT_YET_EXERCISED until real dispatch evidence exists",
        rationale="Dispatch is operationally frequent and should not stay unverified for long.",
    ),
    "operational-events-materialization": WorkflowCertificationPolicy(
        workflow="operational-events-materialization",
        evidence_type="system materialization lifecycle",
        freshness_sla_hours=24,
        acceptable_execution_frequency="multiple times per day",
        terminal_success_criteria="completed status=ok after validation, routing, audit write, and dashboard update",
        stale_threshold_hours=24,
        failure_threshold="most recent terminal event is failed",
        not_applicable_behavior="never not applicable in a live production system",
        rationale="Operational event materialization underpins trust dashboards and must stay very fresh.",
    ),
    "shop-defect": WorkflowCertificationPolicy(
        workflow="shop-defect",
        evidence_type="shop defect lifecycle",
        freshness_sla_hours=168,
        acceptable_execution_frequency="weekly or on demand",
        terminal_success_criteria="completed status=ok after routing, dashboard update, and audit write",
        stale_threshold_hours=168,
        failure_threshold="most recent terminal event is failed",
        not_applicable_behavior="NOT_YET_EXERCISED until real defect evidence exists",
        rationale="Shop defects are operational but event-driven.",
    ),
    "oppc-cost-code-plan": WorkflowCertificationPolicy(
        workflow="oppc-cost-code-plan",
        evidence_type="OPPC cost code planning run",
        freshness_sla_hours=168,
        acceptable_execution_frequency="weekly planning cadence",
        terminal_success_criteria="completed status=ok after validation, audit, and dashboard update",
        stale_threshold_hours=168,
        failure_threshold="most recent terminal event is failed",
        not_applicable_behavior="NOT_YET_EXERCISED until a valid planning run exists",
        rationale="Cost-code planning aligns with weekly operational planning.",
    ),
    "oppc-weekly-rollover": WorkflowCertificationPolicy(
        workflow="oppc-weekly-rollover",
        evidence_type="weekly rollover automation",
        freshness_sla_hours=192,
        acceptable_execution_frequency="weekly",
        terminal_success_criteria="completed status=ok after validation, audit, and dashboard update",
        stale_threshold_hours=192,
        failure_threshold="most recent terminal event is failed",
        not_applicable_behavior="never silently pass; stale once beyond the weekly window",
        rationale="Weekly rollover is a true weekly control and should allow a small scheduling buffer.",
    ),
    "oppc-daily-actuals": WorkflowCertificationPolicy(
        workflow="oppc-daily-actuals",
        evidence_type="daily actuals rollup",
        freshness_sla_hours=36,
        acceptable_execution_frequency="daily / every operating day",
        terminal_success_criteria="completed status=ok after validation, audit, and dashboard update",
        stale_threshold_hours=36,
        failure_threshold="most recent terminal event is failed",
        not_applicable_behavior="never silently pass in active production",
        rationale="Daily actuals are a daily executive metric dependency.",
    ),
    "oppc-payroll-reconciliation": WorkflowCertificationPolicy(
        workflow="oppc-payroll-reconciliation",
        evidence_type="payroll reconciliation run",
        freshness_sla_hours=192,
        acceptable_execution_frequency="weekly",
        terminal_success_criteria="completed status=ok after validation, audit, and dashboard update",
        stale_threshold_hours=192,
        failure_threshold="most recent terminal event is failed",
        not_applicable_behavior="NOT_YET_EXERCISED until a real payroll reconciliation run succeeds",
        rationale="Payroll reconciliation is periodic, not daily.",
    ),
    "oppc-monday-look-behind": WorkflowCertificationPolicy(
        workflow="oppc-monday-look-behind",
        evidence_type="Monday look-behind planning run",
        freshness_sla_hours=192,
        acceptable_execution_frequency="weekly on Monday cadence",
        terminal_success_criteria="completed status=ok after validation, audit, and dashboard update",
        stale_threshold_hours=192,
        failure_threshold="most recent terminal event is failed",
        not_applicable_behavior="STALE once beyond weekly cadence; do not auto-green between weeks",
        rationale="Monday look-behind is inherently weekly.",
    ),
    "oppc-variance-intelligence": WorkflowCertificationPolicy(
        workflow="oppc-variance-intelligence",
        evidence_type="variance intelligence run",
        freshness_sla_hours=168,
        acceptable_execution_frequency="weekly or more often during active forecasting cycles",
        terminal_success_criteria="completed status=ok after validation, audit, and dashboard update",
        stale_threshold_hours=168,
        failure_threshold="most recent terminal event is failed",
        not_applicable_behavior="NOT_YET_EXERCISED until a valid variance run exists",
        rationale="Variance intelligence informs weekly operational decisions.",
    ),
    "oppc-recovery-intelligence": WorkflowCertificationPolicy(
        workflow="oppc-recovery-intelligence",
        evidence_type="recovery intelligence run",
        freshness_sla_hours=168,
        acceptable_execution_frequency="weekly",
        terminal_success_criteria="completed status=ok after validation, audit, and dashboard update",
        stale_threshold_hours=168,
        failure_threshold="most recent terminal event is failed",
        not_applicable_behavior="NOT_YET_EXERCISED until a real recovery run exists",
        rationale="Recovery intelligence is planning-oriented and does not need a daily SLA.",
    ),
    "oppc-enterprise-resource-coordination": WorkflowCertificationPolicy(
        workflow="oppc-enterprise-resource-coordination",
        evidence_type="resource coordination run",
        freshness_sla_hours=168,
        acceptable_execution_frequency="weekly",
        terminal_success_criteria="completed status=ok after validation, audit, and dashboard update",
        stale_threshold_hours=168,
        failure_threshold="most recent terminal event is failed",
        not_applicable_behavior="NOT_YET_EXERCISED until a valid coordination run exists",
        rationale="Resource coordination is periodic planning evidence.",
    ),
    "oppc-forecasting": WorkflowCertificationPolicy(
        workflow="oppc-forecasting",
        evidence_type="forecasting run",
        freshness_sla_hours=168,
        acceptable_execution_frequency="weekly or more often in active forecasting periods",
        terminal_success_criteria="completed status=ok after validation, audit, and dashboard update",
        stale_threshold_hours=168,
        failure_threshold="most recent terminal event is failed",
        not_applicable_behavior="NOT_YET_EXERCISED until a valid forecasting run exists",
        rationale="Forecasting is periodic, not per-request interactive evidence.",
    ),
    "oppc-monday-morning-briefing": WorkflowCertificationPolicy(
        workflow="oppc-monday-morning-briefing",
        evidence_type="Monday briefing package run",
        freshness_sla_hours=192,
        acceptable_execution_frequency="weekly on Monday cadence",
        terminal_success_criteria="completed status=ok after validation, audit, and dashboard update",
        stale_threshold_hours=192,
        failure_threshold="most recent terminal event is failed",
        not_applicable_behavior="STALE once beyond weekly cadence; do not auto-green between weeks",
        rationale="Monday briefing is a weekly executive artifact.",
    ),
    "oppc-production-confidence": WorkflowCertificationPolicy(
        workflow="oppc-production-confidence",
        evidence_type="production confidence rollup",
        freshness_sla_hours=168,
        acceptable_execution_frequency="weekly",
        terminal_success_criteria="completed status=ok after validation, audit, and dashboard update",
        stale_threshold_hours=168,
        failure_threshold="most recent terminal event is failed",
        not_applicable_behavior="NOT_YET_EXERCISED until a confidence rollup succeeds",
        rationale="Production confidence is an executive rollup with at least weekly expectations.",
    ),
    "oppc-daily-report-proof-chain": WorkflowCertificationPolicy(
        workflow="oppc-daily-report-proof-chain",
        evidence_type="daily report proof-chain control run",
        freshness_sla_hours=36,
        acceptable_execution_frequency="daily / every operating day",
        terminal_success_criteria="completed status=ok after routing, recipients, queue, audit, and proof-chain completion",
        stale_threshold_hours=36,
        failure_threshold="most recent terminal event is failed",
        not_applicable_behavior="never silently pass in active production",
        rationale="The proof chain protects daily report executive trust and should remain on a daily cadence.",
    ),
}

WORKFLOW_FRESHNESS_WINDOWS: Dict[str, timedelta] = {
    workflow: timedelta(hours=policy.freshness_sla_hours)
    for workflow, policy in WORKFLOW_CERTIFICATION_POLICIES.items()
}


def _policy_for_workflow(workflow: str) -> WorkflowCertificationPolicy:
    return WORKFLOW_CERTIFICATION_POLICIES.get(
        workflow,
        WorkflowCertificationPolicy(
            workflow=workflow,
            evidence_type="workflow terminal success evidence",
            freshness_sla_hours=FRESHNESS_WINDOW.total_seconds() / 3600.0,
            acceptable_execution_frequency="operator-defined",
            terminal_success_criteria="completed terminal stage with status=ok",
            stale_threshold_hours=FRESHNESS_WINDOW.total_seconds() / 3600.0,
            failure_threshold="most recent terminal event is failed",
            not_applicable_behavior="remain NOT_YET_EXERCISED unless an explicit policy marks the workflow not applicable",
            rationale="Fallback policy for unclassified workflow; classify explicitly before executive closeout.",
        ),
    )


def _policy_payload(workflow: str) -> Dict[str, Any]:
    policy = _policy_for_workflow(workflow)
    return {
        "workflow": policy.workflow,
        "evidence_type": policy.evidence_type,
        "freshness_sla_hours": policy.freshness_sla_hours,
        "acceptable_execution_frequency": policy.acceptable_execution_frequency,
        "terminal_success_criteria": policy.terminal_success_criteria,
        "stale_threshold_hours": policy.stale_threshold_hours,
        "failure_threshold": policy.failure_threshold,
        "not_applicable_behavior": policy.not_applicable_behavior,
        "rationale": policy.rationale,
    }


async def _latest_terminal_success(db, workflow: str, status: Optional[str] = None):
    wf_family = workflow_family(workflow)
    q: Dict[str, Any] = {
        "workflow": {"$in": wf_family} if len(wf_family) > 1 else workflow,
        "stage": {"$in": ["completed", "completed_for_environment"]},
    }
    if status:
        q["status"] = status
    return await db.trust_spine_events.find_one(
        q, sort=[("ts", -1)],
        projection={
            "_id": 0, "ts": 1, "status": 1, "stage": 1, "correlation_id": 1,
            "record_id": 1, "project_number": 1, "failure_reason": 1,
            "remediation": 1, "module": 1,
        },
    )


async def _first_completed_ok(db, workflow: str):
    wf_family = workflow_family(workflow)
    return await db.trust_spine_events.find_one(
        {
            "workflow": {"$in": wf_family} if len(wf_family) > 1 else workflow,
            "stage": {"$in": ["completed", "completed_for_environment"]},
            "status": "ok",
        },
        sort=[("ts", 1)],
        projection={
            "_id": 0, "ts": 1, "correlation_id": 1, "record_id": 1,
        },
    )


async def _count_completed(db, workflow: str, status: str) -> int:
    wf_family = workflow_family(workflow)
    return await db.trust_spine_events.count_documents({
        "workflow": {"$in": wf_family} if len(wf_family) > 1 else workflow,
        "stage": {"$in": ["completed", "completed_for_environment"]},
        "status": status,
    })


async def _audit_row_for_correlation(db, cid: str) -> Optional[Dict[str, Any]]:
    """Find the ``email_routing_audit_v2`` row matching a Trust Spine
    correlation_id. The dispatcher writes the audit row in the same
    transaction window so the correlation_id flows through ``calling_module``
    + timestamp proximity — but the column is not directly stored.
    We confirm via the related ``audit_written`` spine event instead."""
    if not cid:
        return None
    aw = await db.trust_spine_events.find_one(
        {"stage": "audit_written", "correlation_id": cid},
        sort=[("ts", -1)],
        projection={"_id": 0, "ts": 1, "status": 1, "module": 1},
    )
    return aw


async def _workflow_has_any_evidence(db, workflow: str) -> bool:
    wf_family = workflow_family(workflow)
    row = await db.trust_spine_events.find_one(
        {"workflow": {"$in": wf_family}} if len(wf_family) > 1 else {"workflow": workflow},
        projection={"_id": 0, "workflow": 1},
        sort=[("ts", -1)],
    )
    return bool(row)


async def _latest_any_event(db, workflow: str):
    wf_family = workflow_family(workflow)
    return await db.trust_spine_events.find_one(
        {"workflow": {"$in": wf_family}} if len(wf_family) > 1 else {"workflow": workflow},
        sort=[("ts", -1)],
        projection={
            "_id": 0, "ts": 1, "status": 1, "stage": 1, "correlation_id": 1,
            "record_id": 1, "project_number": 1, "failure_reason": 1,
            "remediation": 1, "module": 1,
        },
    )


def _parse_iso(ts: Optional[str]) -> Optional[datetime]:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts)
    except Exception:
        return None


def _freshness_window_for_workflow(workflow: str) -> timedelta:
    return WORKFLOW_FRESHNESS_WINDOWS.get(workflow, FRESHNESS_WINDOW)


def _evidence_age_hours(ts: Optional[str]) -> Optional[float]:
    dt = _parse_iso(ts)
    if not dt:
        return None
    return round((datetime.now(timezone.utc) - dt).total_seconds() / 3600.0, 2)


def _is_stale(ts: Optional[str], workflow: str) -> bool:
    dt = _parse_iso(ts)
    if not dt:
        return False
    return (datetime.now(timezone.utc) - dt) > _freshness_window_for_workflow(workflow)


def _blocked_reason_from_event(event: Optional[Dict[str, Any]]) -> Optional[str]:
    if not event:
        return None
    fr = str(event.get("failure_reason") or "").strip()
    rm = str(event.get("remediation") or "").strip()
    combined = " ".join([fr.lower(), rm.lower()]).strip()
    blockers = [
        "email_safety_mode:strict",
        "immutable",
        "governance",
        "blocked",
        "dependency",
        "unavailable prerequisite",
        "prerequisite",
        "requires operator",
    ]
    if any(b in combined for b in blockers):
        return fr or rm or "workflow_blocked"
    if event.get("status") == "skipped" and (fr or rm):
        return fr or rm
    return None


def _operator_remediation_for_failure(failure_reason: Optional[str]) -> str:
    """Map known Trust Spine failure_reason strings to operator-facing
    actions. Falls back to a generic message that points at the
    forensic endpoint."""
    fr = (failure_reason or "").lower()
    if "no recipients" in fr or "recipients_empty" in fr:
        return (
            "Assign a PM to this project in Admin → People & Access → "
            "Multi-Portal Directory, or configure ADMIN_DEAD_LETTER_TO."
        )
    if "resend returned no message id" in fr:
        return (
            "Resend rejected the send. Verify RESEND_API_KEY validity and "
            "Resend dashboard status."
        )
    if "auto-email disabled" in fr:
        return (
            "Set RESEND_API_KEY and AUTO_EMAIL_REPORTS=true in backend env, "
            "then redeploy."
        )
    if "shop_recipient_unconfigured" in fr or "pre_op_fail_fallback" in fr:
        return (
            "Configure the Shop Manager via Admin → Shop Users (role = "
            "'Shop Manager') or set PRE_OP_FAIL_FALLBACK in Email & Routing."
        )
    return (
        "Open Admin → Operations → DR Delivery Forensics for the matching "
        "report; the closed-set root_cause_code names the exact gap."
    )


def _engineering_remediation_for_failure(failure_reason: Optional[str]) -> str:
    fr = (failure_reason or "").lower()
    if "_wl" in fr or "name " in fr and "is not defined" in fr:
        return (
            "PDF/email render referenced an undefined variable. Inspect "
            "pdf_render.py for the named symbol; regression in "
            "test_track_15_76_email_render_wl_regression.py."
        )
    if "resend returned no message id" in fr:
        return (
            "Provider response missing 'id'. Inspect resend.Emails.send "
            "return for the failing correlation_id; check Resend status "
            "and verify the sending domain SPF/DKIM."
        )
    if "no recipients" in fr:
        return (
            "Resolver returned empty list AND dead-letter fallback also "
            "returned empty. Inspect pm_routing.resolve_pm_for_record_async "
            "for the record's project_number."
        )
    return (
        "Inspect backend logs around the failure_reason ts for the "
        "stack trace. Reproduce via the forensic endpoint."
    )


def _build_release_scope(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    touched = [row for row in rows if row.get("status") != STATUS_NOT_YET_EXERCISED]
    untouched = [row for row in rows if row.get("status") == STATUS_NOT_YET_EXERCISED]

    def _workflows_with(status: str) -> List[str]:
        return [row["workflow"] for row in touched if row.get("status") == status]

    release_verified = _workflows_with(STATUS_VERIFIED)
    release_failed = _workflows_with(STATUS_FAILED)
    release_blocked = _workflows_with(STATUS_BLOCKED)
    release_stale = _workflows_with(STATUS_STALE)
    release_counters = {
        "verified": len(release_verified),
        "failed": len(release_failed),
        "blocked": len(release_blocked),
        "stale": len(release_stale),
        "not_yet_exercised": 0,
        "untouched": len(untouched),
        "total": len(touched),
    }
    if release_counters["failed"] > 0 or release_counters["blocked"] > 0:
        release_band = "hold"
    elif release_counters["stale"] > 0:
        release_band = "review"
    else:
        release_band = "pass"

    return {
        "release_band": release_band,
        "release_counters": release_counters,
        "release_touched_workflows": [row["workflow"] for row in touched],
        "release_untouched_workflows": [row["workflow"] for row in untouched],
        "release_verified_workflows": release_verified,
        "release_failed_workflows": release_failed,
        "release_blocked_workflows": release_blocked,
        "release_stale_workflows": release_stale,
        "release_reason": _release_reason_for_scope({
            "release_failed_workflows": release_failed,
            "release_blocked_workflows": release_blocked,
            "release_stale_workflows": release_stale,
            "release_touched_workflows": [row["workflow"] for row in touched],
        }),
        "release_required_workflows": [row["workflow"] for row in touched],
    }


def _release_reason_for_scope(release_scope: Dict[str, Any]) -> str:
    if release_scope["release_failed_workflows"]:
        return "release_contains_failed_workflows"
    if release_scope["release_blocked_workflows"]:
        return "release_contains_blocked_workflows"
    if release_scope["release_stale_workflows"]:
        return "release_contains_stale_evidence"
    if release_scope["release_touched_workflows"]:
        return "release_scope_verified"
    return "release_scope_not_yet_exercised"


def _release_source_hash() -> Optional[str]:
    try:
        from server import _SOURCE_HASH  # noqa: PLC0415
        return _SOURCE_HASH
    except Exception:  # noqa: BLE001
        return None


def _release_git_commit() -> Optional[str]:
    try:
        from server import _RESOLVED_COMMIT  # noqa: PLC0415
        return _RESOLVED_COMMIT
    except Exception:  # noqa: BLE001
        return None


async def build_certification(db) -> Dict[str, Any]:
    """Build the full per-workflow certification payload.

    Read-only. No writes. Safe to call from any admin endpoint."""
    workflows_known: List[str] = list(WORKFLOW_EXPECTED_STAGES.keys())

    rows: List[Dict[str, Any]] = []
    counters = {
        "verified": 0, "failed": 0, "not_yet_exercised": 0, "blocked": 0, "stale": 0,
        "total": len(workflows_known),
    }
    for wf in workflows_known:
        latest = await _latest_terminal_success(db, wf)
        latest_any = await _latest_any_event(db, wf)
        blocked_reason = _blocked_reason_from_event(latest_any)
        latest_any_ts = _parse_iso((latest_any or {}).get("ts"))
        latest_completed_ts = _parse_iso((latest or {}).get("ts"))
        if latest is None:
            if blocked_reason:
                status = STATUS_BLOCKED
                counters["blocked"] += 1
            else:
                status = STATUS_NOT_YET_EXERCISED
                counters["not_yet_exercised"] += 1
            rows.append({
                "workflow": wf,
                "status": status,
                "first_verified_at": None,
                "last_verified_at": None,
                "successful_deliveries": 0,
                "failed_deliveries": 0,
                "last_failure": None,
                "last_failure_reason": blocked_reason,
                "operator_remediation": (
                    "Complete the blocked dependency or governance prerequisite, then rerun the workflow."
                    if status == STATUS_BLOCKED else None
                ),
                "engineering_remediation": (
                    "Ensure the workflow can emit a canonical completed event once its blocker clears."
                    if status == STATUS_BLOCKED else None
                ),
                "regression_protected": True,
                "audit_row_observed": None,
            })
            continue

        ok_count = await _count_completed(db, wf, "ok")
        fail_count = await _count_completed(db, wf, "failed")
        first_ok = await _first_completed_ok(db, wf)
        latest_ok = await _latest_terminal_success(db, wf, status="ok")
        latest_fail = await _latest_terminal_success(db, wf, status="failed")

        if blocked_reason and latest_any_ts and (latest_completed_ts is None or latest_any_ts > latest_completed_ts):
            status = STATUS_BLOCKED
            counters["blocked"] += 1
            audit_row = None
        elif latest.get("status") == "ok":
            if _is_stale(latest.get("ts"), wf):
                status = STATUS_STALE
                counters["stale"] += 1
            else:
                status = STATUS_VERIFIED
                counters["verified"] += 1
            audit_row = (
                await _audit_row_for_correlation(db, latest.get("correlation_id"))
                if latest.get("correlation_id") else None
            )
        else:
            status = STATUS_FAILED
            counters["failed"] += 1
            audit_row = None

        rows.append({
            "workflow": wf,
            "status": status,
            "freshness_window_hours": round(_freshness_window_for_workflow(wf).total_seconds() / 3600.0, 2),
            "freshness_policy_source": "default_global" if wf not in WORKFLOW_FRESHNESS_WINDOWS else "workflow_override",
            "evidence_age_hours": _evidence_age_hours((latest or {}).get("ts")),
            "policy": _policy_payload(wf),
            "first_verified_at": (first_ok or {}).get("ts"),
            "last_verified_at": (latest_ok or {}).get("ts"),
            "successful_deliveries": ok_count,
            "failed_deliveries": fail_count,
            "last_failure": (latest_fail or {}).get("ts"),
            "last_failure_reason": (latest_fail or {}).get("failure_reason"),
            "last_failure_record_id": (latest_fail or {}).get("record_id"),
            "operator_remediation": (
                _operator_remediation_for_failure(
                    (latest_fail or {}).get("failure_reason")
                ) if status == STATUS_FAILED else None
            ),
            "engineering_remediation": (
                _engineering_remediation_for_failure(
                    (latest_fail or {}).get("failure_reason")
                ) if status == STATUS_FAILED else None
            ),
            "regression_protected": True,
            "audit_row_observed": bool(audit_row),
        })

    release_scope = _build_release_scope(rows)
    release_status = (
        "FAIL"
        if release_scope["release_counters"]["failed"] > 0
        else "HOLD"
        if release_scope["release_counters"]["blocked"] > 0
        else "REVIEW"
        if release_scope["release_counters"]["stale"] > 0
        else "PASS"
    )
    release_not_yet_exercised = [row["workflow"] for row in rows if row.get("status") == STATUS_NOT_YET_EXERCISED]
    release_not_applicable: List[str] = []

    return {
        "ok": True,
        "track": "15.79E",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "counters": counters,
        "release_counters": release_scope["release_counters"],
        "platform_band": (
            "red" if counters["failed"] > 0
            else "amber" if counters["blocked"] > 0 or counters["stale"] > 0
            else "green" if counters["verified"] > 0
            else "amber"
        ),
        "release_band": release_scope["release_band"],
        "release_touched_workflows": release_scope["release_touched_workflows"],
        "release_untouched_workflows": release_scope["release_untouched_workflows"],
        "release_verified_workflows": release_scope["release_verified_workflows"],
        "release_failed_workflows": release_scope["release_failed_workflows"],
        "release_not_yet_exercised_workflows": release_not_yet_exercised,
        "release_blocked_workflows": release_scope["release_blocked_workflows"],
        "release_stale_workflows": release_scope["release_stale_workflows"],
        "release_not_applicable_workflows": release_not_applicable,
        "release_status": release_status,
        "release_reason": release_scope["release_reason"],
        "release_required_workflows": release_scope["release_required_workflows"],
        "release_source_hash": _release_source_hash(),
        "release_git_commit": _release_git_commit(),
        "release_evidence_generated_at": datetime.now(timezone.utc).isoformat(),
        "release_scope_source": "trust_spine_events",
        "release_scope_complete": True,
        "freshness_policy": {
            "default_window_hours": round(FRESHNESS_WINDOW.total_seconds() / 3600.0, 2),
            "workflow_overrides": {
                key: round(value.total_seconds() / 3600.0, 2)
                for key, value in WORKFLOW_FRESHNESS_WINDOWS.items()
            },
            "workflow_policies": {
                workflow: _policy_payload(workflow)
                for workflow in WORKFLOW_EXPECTED_STAGES.keys()
            },
        },
        "kpi_metadata": {
            "kpi_name": "Production Certification Freshness",
            "business_definition": "Workflow certification states require terminal business-success evidence within defined freshness windows.",
            "source_of_truth": "trust_spine_events",
            "api_endpoint": "/api/admin/production-certification",
            "formula": {
                "default_freshness_window_hours": round(FRESHNESS_WINDOW.total_seconds() / 3600.0, 2),
                "statuses": [STATUS_VERIFIED, STATUS_FAILED, STATUS_NOT_YET_EXERCISED, STATUS_BLOCKED, STATUS_STALE],
                "workflow_specific_policy_count": len(WORKFLOW_CERTIFICATION_POLICIES),
            },
            "confidence": "HIGH",
            "status_reason": "A workflow does not become VERIFIED from HTTP reachability alone; terminal business evidence is required.",
            "drilldown_source": "/admin/diagnostics",
            "owner": "production-certification",
        },
        "workflows": rows,
    }


__all__ = [
    "build_certification",
    "STATUS_VERIFIED", "STATUS_FAILED", "STATUS_NOT_YET_EXERCISED", "STATUS_BLOCKED", "STATUS_STALE",
]
