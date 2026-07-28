"""
TRACK 28.09D · Backup Health Severity Aggregator Repair · Regression Contract.

Locks the two bugs fixed in `occ_health_aggregator._eval_recovery_snapshot`:

  Bug 1 (pill_map coverage):  "amber" was missing from the pill map, so
  AMBER pills silently became "unknown" and, in the frontend, could
  render as CRITICAL.

  Bug 2 (action-by-reason):   every RED shared one hardcoded action
  ("Investigate scheduler + R2 sync now.") even when the true cause
  was a null restore drill, bucket-capacity, integrity failure, etc.
  Fixed by deriving a reason_code from the actual evidence and routing
  a specific recommended_action off that code.

Both are truthfulness / operator-trust defects. Regression-locked so a
future edit cannot silently reintroduce either.
"""
from __future__ import annotations

from datetime import datetime, timezone

from routes.occ_health_aggregator import _eval_recovery_snapshot

CHECKED_AT = datetime.now(timezone.utc).isoformat()


def _base_body(**over):
    body = {
        "pill": "GREEN",
        "last_backup": {"ok": True, "ts": "2026-07-11T00:00:00Z", "filename": "b.zip"},
        "backup_age_minutes": 53.3,
        "backup_age_target_minutes": 60,
        "archive_count": {"r2_total": 95, "last_7d": 30, "last_30d": 85},
        "rpo": {"target_min": 60, "actual_min": 53.3, "status": "GREEN"},
        "rto": {"target_min": 15, "last_drill_min": None, "status": "AMBER"},
        "bucket_usage": {"gb": 12.5, "warn_gb": 45, "alert_gb": 50, "status": "GREEN"},
        "scheduler": {"alive": True, "is_healthy": True},
        "warnings": [],
        "failures_7d": 0,
        "computed_at": CHECKED_AT,
    }
    body.update(over)
    return body


# ------------------------------------------------------------------
# Bug 1 · pill map must accept AMBER (recovery_dashboard uses that
# vocabulary, not "yellow").
# ------------------------------------------------------------------

def test_amber_pill_maps_to_yellow_status():
    out = _eval_recovery_snapshot(_base_body(pill="AMBER"), None, CHECKED_AT)
    assert out["status"] == "DEGRADED", (
        "TRACK 28.09D regression: pill=AMBER must map to status=DEGRADED, "
        f"got {out['status']!r}. Previous bug: only `yellow` was in the "
        "map, so AMBER became `unknown`."
    )


def test_green_pill_healthy_evidence_produces_healthy_card():
    out = _eval_recovery_snapshot(_base_body(pill="GREEN"), None, CHECKED_AT)
    assert out["status"] == "VERIFIED"
    assert out["evidence"]["reason_code"] == "healthy"
    assert out["recommended_action"] == ""


def test_red_pill_with_bucket_alert_produces_bucket_action():
    body = _base_body(
        pill="RED",
        bucket_usage={"gb": 55, "warn_gb": 45, "alert_gb": 50, "status": "RED"},
    )
    out = _eval_recovery_snapshot(body, None, CHECKED_AT)
    assert out["status"] == "MISMATCH"
    assert out["evidence"]["reason_code"] == "bucket_over_alert"
    assert "R2 Lifecycle" in out["recommended_action"], (
        "TRACK 28.09D regression: RED caused by bucket alert must "
        "recommend R2 Lifecycle action, not scheduler/R2 sync."
    )


# ------------------------------------------------------------------
# Bug 2 · reason-specific recommended actions.
# ------------------------------------------------------------------

def test_healthy_backup_with_null_drill_does_not_recommend_scheduler_investigation():
    body = _base_body(
        pill="GREEN",
        rto={"target_min": 15, "last_drill_min": None, "status": "AMBER"},
    )
    out = _eval_recovery_snapshot(body, None, CHECKED_AT)
    assert out["status"] == "VERIFIED", (
        "TRACK 28.09D regression: a healthy backup with a missing "
        f"restore drill must not itself flip the OCC card. Got "
        f"status={out['status']!r}."
    )
    action = out["recommended_action"].lower()
    assert "scheduler" not in action and "r2 sync" not in action, (
        "TRACK 28.09D regression: healthy backup + healthy scheduler + "
        "healthy R2 must not recommend `Investigate scheduler + R2 sync "
        f"now`. Got action={out['recommended_action']!r}."
    )


def test_backup_stale_produces_freshness_action_not_scheduler_action():
    body = _base_body(pill="AMBER", backup_age_minutes=1500)
    out = _eval_recovery_snapshot(body, None, CHECKED_AT)
    assert out["status"] == "DEGRADED"
    assert out["evidence"]["reason_code"] in {"backup_stale", "backup_stale_critical"}
    action = out["recommended_action"].lower()
    assert "next backup" in action or "scheduler" not in action


def test_backup_failed_produces_verification_action():
    body = _base_body(
        pill="RED",
        last_backup={"ok": False, "ts": "2026-07-11T00:00:00Z", "filename": "b.zip"},
    )
    out = _eval_recovery_snapshot(body, None, CHECKED_AT)
    assert out["status"] == "MISMATCH"
    assert out["evidence"]["reason_code"] == "backup_failed"
    action = out["recommended_action"].lower()
    assert "backup verification" in action or "re-trigger" in action


# ------------------------------------------------------------------
# Contract 3 · card summary always separates backup freshness from
# restore readiness so operators see both dimensions.
# ------------------------------------------------------------------

def test_summary_reports_both_backup_age_and_restore_drill_state():
    body = _base_body(pill="GREEN")
    out = _eval_recovery_snapshot(body, None, CHECKED_AT)
    summary = out["summary"]
    assert "Backup" in summary or "backup" in summary
    assert "Restore drill" in summary
    assert "not yet run" in summary or "completed" in summary


def test_evidence_exposes_reason_code_field():
    """The frontend and downstream aggregators rely on `reason_code`
    to render the correct icon/color/badge. It must always be present."""
    out = _eval_recovery_snapshot(_base_body(), None, CHECKED_AT)
    assert "reason_code" in out["evidence"]
    assert "reason" in out["evidence"]


def test_summary_uses_rpo_target_not_24h_posture_target():
    out = _eval_recovery_snapshot(_base_body(), None, CHECKED_AT)
    assert "target ≤ 60m" in out["summary"]
