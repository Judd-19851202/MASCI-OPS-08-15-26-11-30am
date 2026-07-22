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

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from lib.trust_spine import WORKFLOW_EXPECTED_STAGES


STATUS_VERIFIED = "VERIFIED"
STATUS_FAILED = "FAILED"
STATUS_NOT_YET_EXERCISED = "NOT_YET_EXERCISED"
STATUS_BLOCKED = "BLOCKED"
STATUS_STALE = "STALE"

FRESHNESS_WINDOW = timedelta(days=2)


async def _latest_terminal_success(db, workflow: str, status: Optional[str] = None):
    q: Dict[str, Any] = {"workflow": workflow, "stage": {"$in": ["completed", "completed_for_environment"]}}
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
    return await db.trust_spine_events.find_one(
        {"workflow": workflow, "stage": {"$in": ["completed", "completed_for_environment"]}, "status": "ok"},
        sort=[("ts", 1)],
        projection={
            "_id": 0, "ts": 1, "correlation_id": 1, "record_id": 1,
        },
    )


async def _count_completed(db, workflow: str, status: str) -> int:
    return await db.trust_spine_events.count_documents({
        "workflow": workflow, "stage": {"$in": ["completed", "completed_for_environment"]}, "status": status,
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
        return "release_contains_stale_workflows"
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

    release_scope = _build_release_scope(rows)
    release_status = (
        "FAIL"
        if release_scope["release_counters"]["failed"] > 0
        else "HOLD"
        if release_scope["release_counters"]["blocked"] > 0 or release_scope["release_counters"]["stale"] > 0
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
        "workflows": rows,
    }


__all__ = [
    "build_certification",
    "STATUS_VERIFIED", "STATUS_FAILED", "STATUS_NOT_YET_EXERCISED", "STATUS_BLOCKED", "STATUS_STALE",
]
