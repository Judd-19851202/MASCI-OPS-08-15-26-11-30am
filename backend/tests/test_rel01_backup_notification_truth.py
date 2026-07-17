from __future__ import annotations

from pathlib import Path


SERVER_PATH = "/app/backend/server.py"


def test_backup_health_rows_store_explicit_notification_truth_fields():
    src = Path(SERVER_PATH).read_text(encoding="utf-8")
    for token in [
        '"notification_outcome"',
        '"notification_recipients"',
        '"notification_recipient_count"',
        '"notification_reason"',
        '"notification_message_id"',
        '"archive_identifier"',
        '"audit_reference"',
    ]:
        assert token in src


def test_complete_r2_and_usage_alert_paths_no_longer_leave_ambiguous_notification_state():
    src = Path(SERVER_PATH).read_text(encoding="utf-8")
    assert 'notification_reason="complete_r2_archive_has_no_direct_email_policy"' in src
    assert 'notification_reason="storage_threshold_observation_only"' in src
    assert 'notification_outcome="notification_not_required"' in src


def test_hourly_archive_lock_fields_remain_present():
    src = Path(SERVER_PATH).read_text(encoding="utf-8")
    assert '"r2_hourly_effective": False' in src
    assert '"r2_hourly_locked_off": True' in src