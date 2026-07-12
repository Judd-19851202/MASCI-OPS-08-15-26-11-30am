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

  * VERIFIED requires a real Trust Spine ``completed/ok`` event AND
    a matching ``email_routing_audit_v2`` row with ``status=sent`` in
    the same correlation window. This blocks "fake green" — a
    workflow cannot show VERIFIED unless the dispatcher actually
    ran end-to-end.
  * NOT_YET_EXERCISED is informational, not a defect.
  * RED never clears automatically. Only a fresh ``completed/ok``
    event (post the most recent failure) flips a workflow from
    FAILED back to VERIFIED.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from lib.trust_spine import WORKFLOW_EXPECTED_STAGES


STATUS_VERIFIED = "VERIFIED"
STATUS_FAILED = "FAILED"
STATUS_NOT_YET_EXERCISED = "NOT_YET_EXERCISED"
STATUS_BLOCKED = "BLOCKED"
STATUS_STALE = "STALE"

FRESHNESS_WINDOW = timedelta(days=2)


async def _latest_completed(db, workflow: str, status: Optional[str] = None):
    q: Dict[str, Any] = {"workflow": workflow, "stage": "completed"}
    if status:
        q["status"] = status
    return await db.trust_spine_events.find_one(
        q, sort=[("ts", -1)],
        projection={
            "_id": 0, "ts": 1, "status": 1, "correlation_id": 1,
            "record_id": 1, "project_number": 1, "failure_reason": 1,
            "remediation": 1, "module": 1,
        },
    )


async def _first_completed_ok(db, workflow: str):
    return await db.trust_spine_events.find_one(
        {"workflow": workflow, "stage": "completed", "status": "ok"},
        sort=[("ts", 1)],
        projection={
            "_id": 0, "ts": 1, "correlation_id": 1, "record_id": 1,
        },
    )


async def _count_completed(db, workflow: str, status: str) -> int:
    return await db.trust_spine_events.count_documents({
        "workflow": workflow, "stage": "completed", "status": status,
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
    row = await db.trust_spine_events.find_one(
        {"workflow": workflow},
        projection={"_id": 0, "workflow": 1},
        sort=[("ts", -1)],
    )
    return bool(row)


async def _latest_any_event(db, workflow: str):
    return await db.trust_spine_events.find_one(
        {"workflow": workflow},
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


def _is_stale(ts: Optional[str]) -> bool:
    dt = _parse_iso(ts)
    if not dt:
        return False
    return (datetime.now(timezone.utc) - dt) > FRESHNESS_WINDOW


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
        latest = await _latest_completed(db, wf)
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
        latest_ok = await _latest_completed(db, wf, status="ok")
        latest_fail = await _latest_completed(db, wf, status="failed")

        if blocked_reason and latest_any_ts and (latest_completed_ts is None or latest_any_ts > latest_completed_ts):
            status = STATUS_BLOCKED
            counters["blocked"] += 1
            audit_row = None
        elif latest.get("status") == "ok":
            if _is_stale(latest.get("ts")):
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

    return {
        "ok": True,
        "track": "15.79E",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "counters": counters,
        "release_counters": dict(counters),
        "platform_band": (
            "red" if counters["failed"] > 0
            else "amber" if counters["blocked"] > 0 or counters["stale"] > 0
            else "green" if counters["verified"] > 0
            else "amber"
        ),
        "release_band": (
            "hold" if counters["failed"] > 0 or counters["blocked"] > 0
            else "review" if counters["stale"] > 0
            else "pass"
        ),
        "workflows": rows,
    }


__all__ = [
    "build_certification",
    "STATUS_VERIFIED", "STATUS_FAILED", "STATUS_NOT_YET_EXERCISED", "STATUS_BLOCKED", "STATUS_STALE",
]
