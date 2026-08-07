from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from lib.backup_runtime import BACKUP_ACTIVE_STALE_MINUTES, is_backup_job_stale


def _job_with_heartbeat(minutes_ago: int):
    now = datetime.now(timezone.utc)
    return {
        "state": "running",
        "host": "some-other-host",
        "pid": 99999,
        "heartbeat_at": (now - timedelta(minutes=minutes_ago)).isoformat(),
    }, now


def test_backup_job_becomes_stale_after_30_minutes_not_90():
    row, now = _job_with_heartbeat(BACKUP_ACTIVE_STALE_MINUTES + 1)
    assert BACKUP_ACTIVE_STALE_MINUTES == 30
    assert is_backup_job_stale(row, now=now) is True


def test_backup_job_under_threshold_remains_blocking():
    row, now = _job_with_heartbeat(BACKUP_ACTIVE_STALE_MINUTES - 1)
    assert is_backup_job_stale(row, now=now) is False


def test_server_runtime_state_uses_shared_backup_stale_threshold_constant():
    src = Path('/app/backend/server.py').read_text(encoding='utf-8')
    assert 'BACKUP_ACTIVE_STALE_MINUTES' in src