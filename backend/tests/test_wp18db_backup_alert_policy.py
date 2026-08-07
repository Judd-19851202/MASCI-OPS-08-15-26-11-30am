from __future__ import annotations

from pathlib import Path

from routes.recovery_dashboard import _compute_pill


def test_backup_alert_policy_keeps_running_complete_backup_out_of_red_between_target_and_alert():
    assert _compute_pill(
        last_backup_ok=True,
        backup_age_minutes=76,
        backup_age_target_minutes=60,
        failures_7d=0,
        bucket_usage_status="GREEN",
        alert_threshold_minutes=75,
        backup_in_progress=True,
    ) == "AMBER"


def test_backup_alert_policy_still_turns_red_when_no_running_backup_exists_past_alert_threshold():
    assert _compute_pill(
        last_backup_ok=True,
        backup_age_minutes=76,
        backup_age_target_minutes=60,
        failures_7d=0,
        bucket_usage_status="GREEN",
        alert_threshold_minutes=75,
        backup_in_progress=False,
    ) == "RED"


def test_server_backup_entrypoints_use_stale_sweep_overlap_helper():
    src = Path('/app/backend/server.py').read_text(encoding='utf-8')
    assert '_sweep_and_classify_backup_overlap' in src
    assert 'overlap = await _sweep_and_classify_backup_overlap(db)' in src