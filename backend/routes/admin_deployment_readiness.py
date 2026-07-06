"""TRACK 15.78 · Deployment Readiness contract.

Read-only admin endpoint that answers exactly one question:

  "Is the platform's *code* safe to deploy right now?"

The answer **must distinguish platform code defects from operator
data issues**. The Trust Center surfaces both in the same dashboard
(by design — the operator needs both), but a deployment gate must
only block on code defects. An operator data issue (e.g. 5 active
projects with no PM assignment) is a *data fix*, not a code fix,
and blocking deployment on it would be wrong.

Endpoint response::

    {
      "track": "15.78",
      "decision": "pass" | "fail",
      "blocking_gates": [{
        "id": "...", "category": "workflow|routing|notification|...",
        "summary": "...", "evidence": "...", "remediation": "...",
      }],
      "advisory_findings": [...],   # operator data — NEVER blocks
      "summary": {...},             # gate-by-gate counters
      "trust_score": int,           # categorized score (ref only)
      "trust_band": "green"|"amber"|"red",
      "regression_gate_count": int,
    }

This endpoint is **read-only**, **admin-gated**, **secret-free**.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, Depends

from lib.trust_score_v2 import compute_categorized_score
from lib.master_data_trust import collect_findings


# ──────────────────────────────────────────────────────────────────
# Gate classification — every "RED" condition is mapped to either
# CODE_DEFECT (blocks deploy) or DATA_ISSUE (advisory, surfaced
# but never blocks).
# ──────────────────────────────────────────────────────────────────
DATA_ISSUE_FINDING_CODES = {
    # Operator must assign PMs in project_team_assignments. Not a
    # code defect — the resolver works correctly when data is present.
    "pm_missing_route",
    # Operator must populate canonical unit_number/employee_id. Not
    # a code defect.
    "equipment_missing_unit_number",
    "employee_missing_id",
}

# Findings that ARE code defects — these block deploy:
CODE_DEFECT_FINDING_CODES = {
    # If a critical email route (always-cc, safety inbox, dead-letter)
    # is missing, the platform CAN dead-letter silently. This is a
    # platform configuration defect, not operator data drift.
    "critical_route_missing",
}


def make_router(db, require_admin_only_dep) -> APIRouter:
    router = APIRouter()

    @router.get("/api/admin/deployment-readiness")
    async def deployment_readiness(
        _: Any = Depends(require_admin_only_dep),
    ) -> Dict[str, Any]:
        # 1) Workflow lifecycle rollup.
        from routes.admin_trust_spine import make_router as _spine_router  # noqa: PLC0415
        spine_router = _spine_router(db, lambda: None)
        spine_handler = next(
            r.endpoint for r in spine_router.routes
            if getattr(r, "path", "") == "/api/admin/trust-spine"
        )
        spine_payload = await spine_handler(_=None)
        workflows: List[Dict[str, Any]] = list(
            spine_payload.get("workflows", [])
        )

        # 2) Master data.
        try:
            findings = await collect_findings(db)
        except Exception:
            findings = []

        # 3) Audit unknowns.
        try:
            since = (
                datetime.now(timezone.utc).isoformat()[:13]
                + ":00:00+00:00"  # truncate to the hour, 24h window below
            )
            del since  # placeholder; below uses real 24h
        except Exception:
            pass
        from datetime import timedelta  # noqa: PLC0415
        since_iso = (
            datetime.now(timezone.utc) - timedelta(hours=24)
        ).isoformat()
        try:
            unknown_audit = await db.email_routing_audit_v2.count_documents({
                "ts": {"$gte": since_iso},
                "status": {"$nin": [
                    "ok", "sent", "delivered", "failed", "skipped",
                    "dead_letter", "dead-letter", "routed_to_dead_letter",
                    "dry_run", "dry-run", "resolved",
                    # TRACK 22.5A · `needs_configuration` is the audit
                    # status recorded when a routing rule matches but
                    # the target has no resolvable recipient (e.g. a
                    # project without PM email). The underlying fact
                    # is already surfaced as a `master_data` advisory
                    # finding — do not double-count it as an audit
                    # anomaly.
                    "needs_configuration",
                ]},
            })
        except Exception:
            unknown_audit = 0
        try:
            silent_failures = await db.trust_spine_events.count_documents({
                "ts": {"$gte": since_iso},
                "status": "failed",
                "$or": [
                    {"remediation": None}, {"remediation": ""},
                    {"remediation": {"$exists": False}},
                ],
            })
        except Exception:
            silent_failures = 0

        # 4) Score (reference only).
        score = compute_categorized_score(
            workflows=workflows,
            master_data_findings=findings,
            unknown_audit_count_24h=unknown_audit,
            silent_failure_count_24h=silent_failures,
            missing_critical_routes=sum(
                1 for f in findings if f.get("code") == "critical_route_missing"
            ),
        )

        # 5) Build the gate list.
        blocking: List[Dict[str, Any]] = []
        advisory: List[Dict[str, Any]] = []

        # Workflow integrity — a RED workflow with a failure event
        # that has a code-level reason (no remediation hint, or hint
        # mentions "log" / "code" / "exception") is a code defect.
        for w in workflows:
            if w.get("band") != "red":
                continue
            lf = w.get("last_failure") or {}
            reason = (lf.get("failure_reason") or "").lower()
            # Heuristic: if the recent failure's remediation links to
            # operator-managed data (project_team_assignments, env
            # variable), classify as advisory. Otherwise — and by
            # default — classify as a code defect to be safe.
            is_data_issue = any(
                phrase in reason
                for phrase in (
                    "no pm resolved", "no recipient",
                    "dead-letter unconfigured",
                )
            )
            entry = {
                "id": f"workflow_red:{w.get('workflow')}",
                "category": "workflow",
                "summary": (
                    f"{w.get('workflow_label') or w.get('workflow')} "
                    "workflow is failing"
                ),
                "evidence": (
                    f"failed at stage={lf.get('stage')} · "
                    f"record={lf.get('record_id')} · {reason[:160]}"
                ),
                "remediation": (
                    lf.get("remediation")
                    or "Open Operations Trust Center drill-in for this "
                       "workflow's failing record_id."
                ),
            }
            (advisory if is_data_issue else blocking).append(entry)

        # Master data — classify by code.
        for f in findings:
            entry = {
                "id": f.get("code"),
                "category": "master_data",
                "summary": f.get("summary"),
                "evidence": f"samples={f.get('samples', [])[:5]}",
                "remediation": f.get("remediation"),
                "remediation_link": f.get("remediation_link"),
            }
            if f.get("code") in CODE_DEFECT_FINDING_CODES:
                blocking.append(entry)
            else:
                advisory.append(entry)

        # Audit integrity — any unknown-status audit row in 24h is a
        # code defect (it means the platform wrote a status string
        # not in our allow-list, which is a contract violation).
        if unknown_audit > 0:
            blocking.append({
                "id": "audit_unknown_status",
                "category": "audit",
                "summary": (
                    f"{unknown_audit} audit row(s) with unknown status "
                    "in the last 24h"
                ),
                "evidence": "email_routing_audit_v2.status outside contract",
                "remediation": (
                    "Inspect the most recent dispatcher write paths and "
                    "ensure every audit insertion uses one of the "
                    "documented status strings."
                ),
            })

        # Silent failures — failed Trust Spine events without a
        # remediation hint = code defect.
        if silent_failures > 0:
            blocking.append({
                "id": "silent_failure",
                "category": "trust_spine",
                "summary": (
                    f"{silent_failures} failed lifecycle event(s) with "
                    "no remediation hint"
                ),
                "evidence": (
                    "trust_spine_events with status=failed and empty "
                    "remediation field"
                ),
                "remediation": (
                    "Update the emit point so every failure path "
                    "supplies a remediation hint operators can act on."
                ),
            })

        # Notification integrity — provider 100% failure rate is a
        # code/config defect.
        notif_total = sum(
            w.get("events_24h", 0) for w in workflows
        )
        notif_failed = sum(
            w.get("failed_24h", 0) for w in workflows
        )
        if notif_total > 0 and notif_failed == notif_total:
            blocking.append({
                "id": "notification_100pct_failure",
                "category": "notification",
                "summary": (
                    "every lifecycle event in the last 24h failed — "
                    "notification pipeline is fully down"
                ),
                "evidence": (
                    f"trust_spine: failed_24h={notif_failed} "
                    f"events_24h={notif_total}"
                ),
                "remediation": (
                    "Verify RESEND_API_KEY, AUTO_EMAIL_REPORTS=true, and "
                    "PROVIDER reachability."
                ),
            })

        # TRACK 15.93 · System bootstrap state. The platform must run
        # its own canonical bootstrap on every startup; if that run
        # was missing, failed, or reports missing items, the deploy
        # is NOT ready. This is the gate that closes the manual-seed
        # dependency permanently.
        bootstrap_block: Dict[str, Any] = {
            "version": None,
            "completed_at": None,
            "ok": False,
            "missing_items": [],
            "ran": False,
        }
        try:
            from lib.system_bootstrap import read_latest_bootstrap_status  # noqa: PLC0415
            bs = await read_latest_bootstrap_status(db)
        except Exception:
            bs = None
        if bs:
            bootstrap_block.update({
                "version": bs.get("version"),
                "completed_at": bs.get("completed_at"),
                "ok": bool(bs.get("ok")),
                "missing_items": list(bs.get("missing_items") or []),
                "ran": True,
            })
        if not bootstrap_block["ran"]:
            blocking.append({
                "id": "bootstrap_never_ran",
                "category": "platform",
                "summary": (
                    "System bootstrap has never executed on this "
                    "deployment — required initialization is unverified."
                ),
                "evidence": (
                    "db.system_bootstrap_status has no 'latest' doc"
                ),
                "remediation": (
                    "Restart the backend so the @app.on_event('startup') "
                    "bootstrap hook runs."
                ),
            })
        elif not bootstrap_block["ok"]:
            missing = bootstrap_block["missing_items"]
            blocking.append({
                "id": "bootstrap_incomplete",
                "category": "platform",
                "summary": (
                    "System bootstrap completed with unresolved items "
                    "— required initialization is incomplete."
                ),
                "evidence": (
                    "missing_items=" + ", ".join(missing[:8])
                    if missing else "bootstrap result ok=False"
                ),
                "remediation": (
                    "Inspect /api/admin/deployment-readiness bootstrap "
                    "block · check server logs for [system-bootstrap] "
                    "errors · verify required env vars are set."
                ),
            })

        decision = "fail" if blocking else "pass"

        return {
            "track": "15.78",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "decision": decision,
            "blocking_gates": blocking,
            "advisory_findings": advisory,
            "bootstrap": bootstrap_block,
            "summary": {
                "blocking_count": len(blocking),
                "advisory_count": len(advisory),
                "categories_red": [
                    k for k, v in score["categories"].items()
                    if v["band"] == "red"
                ],
                "categories_amber": [
                    k for k, v in score["categories"].items()
                    if v["band"] == "amber"
                ],
                "workflows_red": sum(1 for w in workflows if w["band"] == "red"),
                "workflows_amber": sum(1 for w in workflows if w["band"] == "amber"),
                "workflows_idle": sum(1 for w in workflows if w["band"] == "amber-no-activity"),
                "workflows_trusted": sum(1 for w in workflows if w["band"] == "green"),
                "unknown_audit_count_24h": unknown_audit,
                "silent_failure_count_24h": silent_failures,
            },
            "trust_score": score["trust_score"],
            "trust_band": score["score_band"],
            "regression_gate_count": _count_regression_gates(),
        }

    return router


def _count_regression_gates() -> int:
    """Return a fast, repeatable count of the regression tests that
    CI/CD must run. Used purely as a transparency signal in the
    response — does not affect the pass/fail decision."""
    import glob  # noqa: PLC0415
    count = 0
    for path in glob.glob("/app/backend/tests/test_track_15_7*.py"):
        try:
            src = open(path).read()
            # Conservative count: one per function whose name starts
            # with `test_`. Parametrized cases are folded into a
            # single entry here — pytest discovers the explosion.
            count += src.count("def test_")
        except Exception:
            pass
    return count
