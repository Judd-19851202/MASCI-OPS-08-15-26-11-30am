from __future__ import annotations

from datetime import datetime, timedelta, timezone

from lib.backup_runtime import (
    BACKUP_JOB_KIND_RESTORE_DRILL,
    is_restore_certification_stale,
    restore_certification_guard_slot,
    restore_certification_terminal_slot,
)


def test_preview_guard_slot_is_environment_scoped() -> None:
    assert restore_certification_guard_slot("preview") == "restore-certification::preview"
    assert restore_certification_guard_slot("production") == "restore-certification::production"
    assert restore_certification_guard_slot("preview") != restore_certification_guard_slot("production")


def test_terminal_slot_releases_without_confusing_environment_scope() -> None:
    released = restore_certification_terminal_slot("preview", "bjob-123", "released")
    assert released.startswith("restore-certification::preview::released::bjob-123")


def test_restore_certification_stale_false_when_lease_current() -> None:
    now = datetime.now(timezone.utc)
    row = {
        "state": "running",
        "heartbeat_at": now.isoformat(),
        "lease_expires_at": (now + timedelta(minutes=15)).isoformat(),
        "kind": BACKUP_JOB_KIND_RESTORE_DRILL,
    }
    assert not is_restore_certification_stale(row, now=now, lease_minutes=45)


def test_restore_certification_stale_true_when_lease_expired_and_heartbeat_old() -> None:
    now = datetime.now(timezone.utc)
    row = {
        "state": "running",
        "heartbeat_at": (now - timedelta(minutes=90)).isoformat(),
        "lease_expires_at": (now - timedelta(minutes=1)).isoformat(),
        "kind": BACKUP_JOB_KIND_RESTORE_DRILL,
    }
    assert is_restore_certification_stale(row, now=now, lease_minutes=45)


def test_restore_certification_stale_false_for_terminal_state() -> None:
    now = datetime.now(timezone.utc)
    row = {
        "state": "completed",
        "heartbeat_at": (now - timedelta(minutes=120)).isoformat(),
        "lease_expires_at": (now - timedelta(minutes=60)).isoformat(),
    }
    assert not is_restore_certification_stale(row, now=now, lease_minutes=45)