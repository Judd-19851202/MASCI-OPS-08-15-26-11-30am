"""Track 15.37 — Restore Upload Ceiling Tests
==============================================
Verifies the env-driven restore upload ceiling introduced in Track 15.37.
Old hard-coded 500 MB rejected every current hourly archive (~600 MB).
New ceiling is configurable via `RESTORE_MAX_UPLOAD_MB` env, default 2048 MB.

These tests run against the live preview backend on localhost:8001.
"""
from __future__ import annotations

import io
import os
import sys
import zipfile

# Ensure the parent dir is importable so we can pull _restore_max_bytes
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))


def test_restore_max_bytes_default_is_2gb(monkeypatch):
    """Default should be 2048 MB = 2 GiB · accepts ~632 MB hourlies + headroom."""
    monkeypatch.delenv("RESTORE_MAX_UPLOAD_MB", raising=False)
    # Re-import after env clear to recompute the constant fresh
    import importlib
    import server
    importlib.reload(server)
    assert server._restore_max_bytes() == 2048 * 1024 * 1024


def test_restore_max_bytes_respects_env(monkeypatch):
    monkeypatch.setenv("RESTORE_MAX_UPLOAD_MB", "1024")
    import importlib
    import server
    importlib.reload(server)
    assert server._restore_max_bytes() == 1024 * 1024 * 1024


def test_restore_max_bytes_clamps_below_64mb(monkeypatch):
    """Anything <64 MB is clamped up — too small to hold a real archive."""
    monkeypatch.setenv("RESTORE_MAX_UPLOAD_MB", "10")
    import importlib
    import server
    importlib.reload(server)
    assert server._restore_max_bytes() == 64 * 1024 * 1024


def test_restore_max_bytes_clamps_above_8gb(monkeypatch):
    """Anything >8 GiB is clamped down — defense against upload-stream attacks."""
    monkeypatch.setenv("RESTORE_MAX_UPLOAD_MB", "99999")
    import importlib
    import server
    importlib.reload(server)
    assert server._restore_max_bytes() == 8192 * 1024 * 1024


def test_restore_max_bytes_invalid_env_falls_back_to_default(monkeypatch):
    monkeypatch.setenv("RESTORE_MAX_UPLOAD_MB", "not-a-number")
    import importlib
    import server
    importlib.reload(server)
    assert server._restore_max_bytes() == 2048 * 1024 * 1024


def test_backup_hours_utc_accepts_6_hour_cadence(monkeypatch):
    """Cadence parser accepts the recommended 6-hour grid."""
    monkeypatch.setenv("BACKUP_HOURS_UTC", "0,6,12,18")
    import importlib
    import server
    importlib.reload(server)
    assert sorted(server._parse_backup_hours()) == [0, 6, 12, 18]


def test_backup_hours_utc_rejects_invalid_hours(monkeypatch):
    """Cadence parser drops hours outside 0-23 + non-integer tokens."""
    monkeypatch.setenv("BACKUP_HOURS_UTC", "-1,25,abc,3")
    import importlib
    import server
    importlib.reload(server)
    # Only "3" should survive; the rest are invalid
    assert server._parse_backup_hours() == [3]


def test_backup_hours_utc_empty_falls_back_to_defaults(monkeypatch):
    monkeypatch.setenv("BACKUP_HOURS_UTC", "")
    import importlib
    import server
    importlib.reload(server)
    # The parser falls back to a sensible default (currently [3])
    hours = server._parse_backup_hours()
    assert isinstance(hours, list)
    assert all(0 <= h <= 23 for h in hours)
