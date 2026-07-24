from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.backup_runtime import BackupJobOwnershipLost, heartbeat_backup_job  # noqa: E402
from lib.hourly_activation import build_hourly_activation_state, classify_capacity_state  # noqa: E402


def test_hourly_activation_production_enabled_all_guards_pass():
    state = build_hourly_activation_state(
        requested_raw="true",
        environment="production",
        scheduler_healthy=True,
        persistence_available=True,
        backup_active=False,
        restore_active=False,
        stale_job_count=0,
        stale_lock_present=False,
        resource_preflight={"ok": True, "reasons": []},
        r2_configured=True,
        retention_valid=True,
        retention_reason="approved_tiered_retention",
    )
    assert state["r2_hourly_effective"] is True
    assert state["activation_status"] == "ACTIVE"


def test_hourly_activation_preview_enabled_is_blocked_by_environment():
    state = build_hourly_activation_state(
        requested_raw="true",
        environment="preview",
        scheduler_healthy=True,
        persistence_available=True,
        backup_active=False,
        restore_active=False,
        stale_job_count=0,
        stale_lock_present=False,
        resource_preflight={"ok": True, "reasons": []},
        r2_configured=True,
        retention_valid=True,
        retention_reason="approved_tiered_retention",
    )
    assert state["r2_hourly_effective"] is False
    assert state["activation_status"] == "BLOCKED BY ENVIRONMENT"


def test_hourly_activation_disabled_in_production_stays_default_off():
    state = build_hourly_activation_state(
        requested_raw="false",
        environment="production",
        scheduler_healthy=True,
        persistence_available=True,
        backup_active=False,
        restore_active=False,
        stale_job_count=0,
        stale_lock_present=False,
        resource_preflight={"ok": True, "reasons": []},
        r2_configured=True,
        retention_valid=True,
        retention_reason="approved_tiered_retention",
    )
    assert state["r2_hourly_effective"] is False
    assert state["activation_status"] == "READY BUT DISABLED"


def test_hourly_activation_blocks_on_active_restore():
    state = build_hourly_activation_state(
        requested_raw="true",
        environment="production",
        scheduler_healthy=True,
        persistence_available=True,
        backup_active=False,
        restore_active=True,
        stale_job_count=0,
        stale_lock_present=False,
        resource_preflight={"ok": True, "reasons": []},
        r2_configured=True,
        retention_valid=True,
        retention_reason="approved_tiered_retention",
    )
    assert state["activation_status"] == "BLOCKED BY SAFETY GUARD"
    assert any(blocker["code"] == "active_restore_present" for blocker in state["activation_blockers"])


def test_hourly_activation_marks_stale_when_stale_job_present():
    state = build_hourly_activation_state(
        requested_raw="true",
        environment="production",
        scheduler_healthy=True,
        persistence_available=True,
        backup_active=False,
        restore_active=False,
        stale_job_count=1,
        stale_lock_present=False,
        resource_preflight={"ok": True, "reasons": []},
        r2_configured=True,
        retention_valid=True,
        retention_reason="approved_tiered_retention",
    )
    assert state["activation_status"] == "STALE"


def test_capacity_state_mapping_warn_alert_and_missing():
    assert classify_capacity_state(total_bytes=100 * 1024**3, warn_gb=700, alert_gb=820, probe_state="ok")["status"] == "GREEN"
    assert classify_capacity_state(total_bytes=700 * 1024**3, warn_gb=700, alert_gb=820, probe_state="ok")["status"] == "AMBER"
    assert classify_capacity_state(total_bytes=821 * 1024**3, warn_gb=700, alert_gb=820, probe_state="ok")["status"] == "RED"
    assert classify_capacity_state(total_bytes=None, warn_gb=700, alert_gb=820, probe_state="missing")["status"] == "AMBER"
    assert classify_capacity_state(total_bytes=None, warn_gb=700, alert_gb=820, probe_state="failed")["status"] == "RED"


class _UpdateResult:
    def __init__(self, modified_count: int):
        self.modified_count = modified_count


class _Jobs:
    def __init__(self):
        self.state = {"job_id": "j1", "state": "running", "owner_token": "token-1", "ownership_revoked": False}

    async def update_one(self, query, update):
        if query.get("owner_token") != self.state.get("owner_token") or self.state.get("ownership_revoked"):
            return _UpdateResult(0)
        self.state.update(update.get("$set") or {})
        return _UpdateResult(1)


class _DB:
    def __init__(self):
        self.backup_jobs = _Jobs()

    def __getitem__(self, name):
        if name == "backup_jobs":
            return self.backup_jobs
        raise KeyError(name)


def test_stale_owner_cannot_heartbeat_after_revocation():
    db = _DB()
    db.backup_jobs.state["ownership_revoked"] = True

    async def _run():
        await heartbeat_backup_job(db, "j1", owner_token="token-1", extra={"stage": "verification"})

    try:
        asyncio.run(_run())
    except BackupJobOwnershipLost:
        return
    raise AssertionError("expected BackupJobOwnershipLost")
