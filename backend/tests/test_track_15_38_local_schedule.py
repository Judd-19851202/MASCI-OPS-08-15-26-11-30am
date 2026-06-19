"""Track 15.38 — Tenant-Local Backup Schedule Tests
======================================================
Verifies the white-label tenant-local-time backup schedule introduced in
Track 15.38. Operators in Florida, Texas, Arizona, etc. configure
`BACKUP_HOURS_LOCAL=0,6,12,18` + `BACKUP_TIMEZONE=America/New_York`
(or equivalent) instead of mentally converting to UTC.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))


def _reload():
    import importlib
    import server
    importlib.reload(server)
    return server


def test_florida_eastern_local_hours_convert_to_utc(monkeypatch):
    """0,6,12,18 local Florida time → 5,11,17,23 UTC (EST) OR 4,10,16,22 (EDT)."""
    monkeypatch.setenv("BACKUP_HOURS_LOCAL", "0,6,12,18")
    monkeypatch.setenv("BACKUP_TIMEZONE", "America/New_York")
    monkeypatch.delenv("BACKUP_HOURS_UTC", raising=False)
    server = _reload()
    hours = server._parse_backup_hours()
    # Compute what the result SHOULD be at the current wall-clock day
    tz = ZoneInfo("America/New_York")
    today_local = datetime.now(tz).date()
    expected = sorted({
        datetime(today_local.year, today_local.month, today_local.day, h, 0, tzinfo=tz)
        .astimezone(timezone.utc).hour
        for h in [0, 6, 12, 18]
    })
    assert hours == expected


def test_arizona_no_dst_local_hours_convert_to_utc(monkeypatch):
    """Arizona doesn't observe DST → stable UTC offset of -7 → 7,13,19,1 UTC."""
    monkeypatch.setenv("BACKUP_HOURS_LOCAL", "0,6,12,18")
    monkeypatch.setenv("BACKUP_TIMEZONE", "America/Phoenix")
    monkeypatch.delenv("BACKUP_HOURS_UTC", raising=False)
    server = _reload()
    hours = server._parse_backup_hours()
    # Phoenix is UTC-7 year-round → 0+7=7, 6+7=13, 12+7=19, 18+7=25→1
    assert hours == [1, 7, 13, 19]


def test_utc_legacy_path_still_works(monkeypatch):
    """No BACKUP_HOURS_LOCAL → fall back to BACKUP_HOURS_UTC."""
    monkeypatch.delenv("BACKUP_HOURS_LOCAL", raising=False)
    monkeypatch.delenv("BACKUP_TIMEZONE", raising=False)
    monkeypatch.setenv("BACKUP_HOURS_UTC", "0,6,12,18")
    server = _reload()
    assert server._parse_backup_hours() == [0, 6, 12, 18]


def test_invalid_timezone_falls_back_gracefully(monkeypatch):
    """Bad BACKUP_TIMEZONE → log warning → fall back to BACKUP_HOURS_UTC."""
    monkeypatch.setenv("BACKUP_HOURS_LOCAL", "0,6,12,18")
    monkeypatch.setenv("BACKUP_TIMEZONE", "Not/A_Real/Zone")
    monkeypatch.setenv("BACKUP_HOURS_UTC", "3,15")
    server = _reload()
    assert server._parse_backup_hours() == [3, 15]


def test_local_hours_empty_falls_back_to_utc(monkeypatch):
    """BACKUP_HOURS_LOCAL empty → use BACKUP_HOURS_UTC."""
    monkeypatch.setenv("BACKUP_HOURS_LOCAL", "")
    monkeypatch.setenv("BACKUP_TIMEZONE", "America/New_York")
    monkeypatch.setenv("BACKUP_HOURS_UTC", "5,17")
    server = _reload()
    assert server._parse_backup_hours() == [5, 17]


def test_local_hours_drops_invalid_and_dedupes(monkeypatch):
    """Bad tokens are dropped, valid ones kept, duplicates removed."""
    monkeypatch.setenv("BACKUP_HOURS_LOCAL", "0,6,abc,99,-1,6,18")
    monkeypatch.setenv("BACKUP_TIMEZONE", "America/Phoenix")  # stable UTC-7
    monkeypatch.delenv("BACKUP_HOURS_UTC", raising=False)
    server = _reload()
    # Valid local hours after parse: {0, 6, 18} → UTC: {7, 13, 1}
    assert server._parse_backup_hours() == [1, 7, 13]
