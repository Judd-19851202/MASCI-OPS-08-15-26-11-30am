from __future__ import annotations

from datetime import timedelta

from lib.backup_runtime import classify_backup_overlap, is_backup_job_stale, backup_now
from lib.hourly_activation import build_hourly_activation_state


def test_stale_running_backup_is_reclaimable_not_blocking() -> None:
    stale_job = {
        "kind": "complete-r2",
        "state": "running",
        "heartbeat_at": (backup_now() - timedelta(minutes=120)).isoformat(),
    }
    overlap = classify_backup_overlap([stale_job])
    assert overlap["backup_active"] is False
    assert len(overlap["reclaimable_backups"]) == 1
    assert overlap["blocking_backups"] == []


def test_recent_running_backup_remains_blocking() -> None:
    active_job = {
        "kind": "complete-r2",
        "state": "running",
        "heartbeat_at": (backup_now() - timedelta(minutes=5)).isoformat(),
    }
    overlap = classify_backup_overlap([active_job])
    assert overlap["backup_active"] is True
    assert len(overlap["blocking_backups"]) == 1
    assert overlap["reclaimable_backups"] == []


def test_is_backup_job_stale_handles_missing_heartbeat_as_stale() -> None:
    assert is_backup_job_stale({"state": "running", "kind": "complete-r2"}) is True


def test_hourly_activation_ignores_reclaimable_active_jobs() -> None:
    state = build_hourly_activation_state(
        requested_raw="true",
        environment="production",
        scheduler_healthy=True,
        persistence_available=True,
        backup_active=False,
        restore_active=False,
        stale_job_count=0,
        reclaimable_stale_job_count=0,
        stale_lock_present=False,
        resource_preflight={"ok": True, "reasons": []},
        r2_configured=True,
        retention_valid=True,
        retention_reason="approved_tiered_retention",
    )
    assert state["activation_status"] == "ACTIVE"
    assert state["r2_hourly_effective"] is True