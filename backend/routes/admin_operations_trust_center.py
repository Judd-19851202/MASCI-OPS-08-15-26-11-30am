"""TRACK 15.76A · Operations Trust Center.

A single read-only admin endpoint that returns *everything* the
operator needs to understand platform trust state in under a minute:

    {
      "trust_score": 94, "score_band": "amber",
      "score_band_label": "Missing evidence",
      "score_reason": "...", "score_inputs": [...],
      "summary": {
        "platform_band": "amber",
        "workflows_trusted": 0, "workflows_amber": 1,
        "workflows_idle": 10, "workflows_red": 0,
        "last_success_at": "...", "last_failure_at": "...",
        "events_24h": 21, "failed_24h": 0,
        "master_data_band": "amber",
      },
      "workflows": [...],  // per-workflow rows with operator-friendly
                           // remediation copy on every red/amber row.
      "master_data": [...],
      "red_alert": {"result": "not_red"|"cooldown"|...},
    }

Admin-gated. No secrets. No PII. Best-effort under the hood — a
failure in master-data collection never breaks the workflow card.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException

from lib.trust_spine import WORKFLOW_EXPECTED_STAGES
from lib.trust_score import compute_score
from lib.master_data_trust import collect_findings, overall_band
from lib import red_alert


# ──────────────────────────────────────────────────────────────────
# Operator-readable remediation copy. Replaces developer-language
# error messages with what-to-do-next sentences.
# ──────────────────────────────────────────────────────────────────
_WORKFLOW_LABELS: Dict[str, str] = {
    "daily-report": "Daily Report",
    "meeting": "Safety Meeting",
    "jha": "JHA / JHP",
    "incident": "Incident",
    "inspection": "Site Inspection",
    "qaqc": "QA/QC",
    "equipment-inspection": "Equipment Pre-Op",
    "dvir": "DVIR",
    "hr-request": "HR Request",
    "dispatch-assignment": "Dispatch Assignment",
    "shop-defect": "Shop Defect",
}

_STAGE_LABELS: Dict[str, str] = {
    "record_created": "the record was saved",
    "validation_complete": "the record passed validation",
    "routing_resolved": "the system resolved who should be notified",
    "recipients_built": "the recipient list was finalized",
    "notification_queued": "the email was queued for delivery",
    "provider_accepted": "the email provider accepted the message",
    "audit_written": "the audit trail row was written",
    "dashboard_updated": "the operator dashboard was updated",
    "completed": "the workflow finished cleanly",
}


def _workflow_label(wf: str) -> str:
    return _WORKFLOW_LABELS.get(wf, wf.replace("-", " ").title())


def _humanize_workflow_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """Replace developer copy with operator-readable strings on the
    workflow row, without touching the original keys (additive)."""
    label = _workflow_label(row.get("workflow") or "")
    band = row.get("band")
    out = dict(row)
    out["workflow_label"] = label
    out["band_label"] = {
        "green": "Trusted",
        "amber": "Missing evidence",
        "amber-no-activity": "No activity 24h",
        "red": "Failing",
    }.get(band, band)

    if band == "red":
        lf = row.get("last_failure") or {}
        fr = lf.get("failure_reason") or ""
        stage = (lf.get("stage") or row.get("failure_stage") or "")
        stage_human = _STAGE_LABELS.get(stage, stage)
        out["operator_summary"] = (
            f"{label} saved, but {stage_human} did not complete: {fr}"
            if stage_human else
            f"{label} failed: {fr or 'see drill-in for details'}"
        )
        out["operator_remediation"] = (
            lf.get("remediation")
            or row.get("remediation")
            or f"Open the {label} drill-in for the failing record_id and "
               "inspect backend logs for that correlation_id."
        )
    elif band == "amber":
        missing = row.get("missing_stages") or []
        miss_label = ", ".join(
            _STAGE_LABELS.get(s, s) for s in missing[:3]
        ) or "one or more lifecycle stages"
        out["operator_summary"] = (
            f"{label} has recent activity but {miss_label} did not "
            "complete on every record."
        )
        out["operator_remediation"] = (
            row.get("remediation")
            or "Submit a new record for this workflow and verify the "
               "drill-in shows every expected stage as ok."
        )
    elif band == "amber-no-activity":
        out["operator_summary"] = (
            f"{label} has not been submitted in the last 24 hours, so "
            "the platform cannot prove it is currently healthy."
        )
        out["operator_remediation"] = (
            "If this workflow is expected to be in daily use, ask the "
            f"field to submit a {label} so the platform can collect fresh "
            "evidence."
        )
    else:  # green
        out["operator_summary"] = (
            f"{label} is fully verified — every expected stage emitted "
            "ok evidence in the last 24h."
        )
        out["operator_remediation"] = None
    return out


def make_router(db, require_admin_only_dep) -> APIRouter:
    router = APIRouter()

    @router.get("/api/admin/operations-trust-center")
    async def operations_trust_center(
        _: Any = Depends(require_admin_only_dep),
    ) -> Dict[str, Any]:
        # 1) Workflow lifecycle rollup — reuse the existing dashboard
        #    aggregator to avoid double-implementation drift.
        from routes.admin_trust_spine import make_router as _spine_router  # noqa: PLC0415
        spine_router = _spine_router(db, lambda: None)
        spine_handler = next(
            r.endpoint for r in spine_router.routes
            if getattr(r, "path", "") == "/api/admin/trust-spine"
        )
        spine_payload = await spine_handler(_=None)

        workflows: List[Dict[str, Any]] = list(spine_payload.get("workflows", []))
        humanized = [_humanize_workflow_row(w) for w in workflows]

        # 2) Master-data trust card.
        try:
            md_findings = await collect_findings(db)
        except Exception:
            md_findings = []
        md_band = overall_band(md_findings)

        # 3) Audit row sanity — count unknown-status rows in 24h on
        #    the canonical email_routing_audit_v2 ledger, plus
        #    silent failures (failed trust-spine events whose
        #    remediation hint is empty — i.e. nobody knows what to do).
        try:
            since_iso = _since_24h_iso()
            unknown_audit = await db.email_routing_audit_v2.count_documents({
                "ts": {"$gte": since_iso},
                "status": {"$nin": [
                    "ok", "sent", "delivered", "failed", "skipped",
                    "dead_letter", "dead-letter", "routed_to_dead_letter",
                    "dry_run", "dry-run", "resolved",
                ]},
            })
        except Exception:
            unknown_audit = 0
        try:
            silent_failures = await db.trust_spine_events.count_documents({
                "ts": {"$gte": _since_24h_iso()},
                "status": "failed",
                "$or": [
                    {"remediation": None}, {"remediation": ""},
                    {"remediation": {"$exists": False}},
                ],
            })
        except Exception:
            silent_failures = 0

        # 4) Trust score.
        score = compute_score(
            workflows=workflows,
            master_data_findings=md_findings,
            unknown_audit_count_24h=unknown_audit,
            silent_failure_count_24h=silent_failures,
            missing_critical_routes=[
                f["summary"] for f in md_findings
                if f.get("code") == "critical_route_missing"
            ],
        )

        # 5) Executive summary strip.
        last_success_at = None
        last_failure_at = None
        for w in workflows:
            ls = (w.get("last_success") or {}).get("ts")
            lf = (w.get("last_failure") or {}).get("ts")
            if ls and (not last_success_at or ls > last_success_at):
                last_success_at = ls
            if lf and (not last_failure_at or lf > last_failure_at):
                last_failure_at = lf

        summary = {
            "platform_band": spine_payload.get("platform_band"),
            "workflow_count": spine_payload.get("workflow_count"),
            "workflows_trusted": sum(1 for w in workflows if w["band"] == "green"),
            "workflows_amber": sum(1 for w in workflows if w["band"] == "amber"),
            "workflows_idle": sum(1 for w in workflows if w["band"] == "amber-no-activity"),
            "workflows_red": sum(1 for w in workflows if w["band"] == "red"),
            "events_24h": spine_payload.get("total_events_24h", 0),
            "failed_24h": spine_payload.get("total_failed_24h", 0),
            "last_success_at": last_success_at,
            "last_failure_at": last_failure_at,
            "master_data_band": md_band,
            "master_data_findings_count": len(md_findings),
            "unknown_audit_count_24h": unknown_audit,
            "silent_failure_count_24h": silent_failures,
        }

        # 6) Red alert hook — fires only on transitions to RED with
        #    cooldown. Always best-effort.
        trust_center_url = (
            os.environ.get("PUBLIC_APP_URL", "")
            or "https://mascidocs.com"
        ) + "/admin/email"
        alert_result = await red_alert.maybe_send(
            db,
            current_band=score["score_band"],
            score=score["trust_score"],
            score_reason=score["score_reason"],
            workflows=workflows,
            trust_center_url=trust_center_url,
        )

        return {
            "track": "15.76A",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            **score,
            "summary": summary,
            "workflows": humanized,
            "master_data": {
                "band": md_band,
                "findings": md_findings,
            },
            "red_alert": alert_result,
        }

    @router.post("/api/admin/operations-trust-center/test-alert")
    async def test_alert(
        _: Any = Depends(require_admin_only_dep),
    ) -> Dict[str, Any]:
        """Manual operator action — fire one dry-run red alert to
        verify the recipient list is correct without actually emailing
        anyone. Useful right after provisioning OPS_ALERT_TO."""
        from routes.admin_trust_spine import make_router as _spine_router  # noqa: PLC0415
        spine = _spine_router(db, lambda: None)
        handler = next(
            r.endpoint for r in spine.routes
            if getattr(r, "path", "") == "/api/admin/trust-spine"
        )
        spine_payload = await handler(_=None)
        return await red_alert.maybe_send(
            db,
            current_band="red",
            score=0,
            score_reason="manual test alert",
            workflows=spine_payload.get("workflows", []),
            trust_center_url=(
                os.environ.get("PUBLIC_APP_URL", "")
                or "https://mascidocs.com"
            ) + "/admin/email",
            dry_run=True,
        )

    return router


def _since_24h_iso() -> str:
    from datetime import datetime as _dt, timedelta, timezone  # noqa: PLC0415
    return (_dt.now(timezone.utc) - timedelta(hours=24)).isoformat()


# Tiny safe re-export so the route module can import.
__all__ = ["make_router", "_humanize_workflow_row"]
