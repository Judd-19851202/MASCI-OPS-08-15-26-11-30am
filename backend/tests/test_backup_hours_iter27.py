"""Iter27 — Multi-window backup scheduler config.

Tests the BACKUP_HOURS_UTC env-var parsing so the field crew always has
two off-site recovery points per workday (default = nightly 02:00 UTC +
mid-day 18:00 UTC).
"""
import os
import importlib


def _reload_server():
    import server  # noqa: F401
    return importlib.reload(__import__("server"))


def test_default_hours_when_env_unset(monkeypatch):
    monkeypatch.delenv("BACKUP_HOURS_UTC", raising=False)
    monkeypatch.delenv("BACKUP_HOUR_UTC", raising=False)
    s = _reload_server()
    # Default: legacy hour (2) + mid-day (18)
    assert s.BACKUP_HOURS_UTC == [2, 18]


def test_explicit_two_windows(monkeypatch):
    monkeypatch.setenv("BACKUP_HOURS_UTC", "3,15")
    s = _reload_server()
    assert s.BACKUP_HOURS_UTC == [3, 15]


def test_single_window(monkeypatch):
    monkeypatch.setenv("BACKUP_HOURS_UTC", "5")
    s = _reload_server()
    assert s.BACKUP_HOURS_UTC == [5]


def test_invalid_entries_are_dropped(monkeypatch):
    monkeypatch.setenv("BACKUP_HOURS_UTC", "2, 99, foo, 18, -1, 0")
    s = _reload_server()
    # 99 and foo and -1 dropped; 0, 2, 18 kept and sorted
    assert s.BACKUP_HOURS_UTC == [0, 2, 18]


def test_empty_falls_back_to_legacy(monkeypatch):
    monkeypatch.setenv("BACKUP_HOURS_UTC", "")
    monkeypatch.setenv("BACKUP_HOUR_UTC", "7")
    s = _reload_server()
    # Empty BACKUP_HOURS_UTC → falls back to "{BACKUP_HOUR_UTC},18" default
    assert 7 in s.BACKUP_HOURS_UTC
    assert 18 in s.BACKUP_HOURS_UTC


def test_duplicates_collapsed(monkeypatch):
    monkeypatch.setenv("BACKUP_HOURS_UTC", "2,2,18,18,2")
    s = _reload_server()
    assert s.BACKUP_HOURS_UTC == [2, 18]


def teardown_module(_module):
    """Restore server module to whatever the live env says."""
    # Don't leave stale env-var state for other test files.
    os.environ.pop("BACKUP_HOURS_UTC", None)
    importlib.reload(__import__("server"))
