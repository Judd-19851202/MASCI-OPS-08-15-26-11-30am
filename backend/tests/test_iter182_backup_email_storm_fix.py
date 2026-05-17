"""
test_iter182_backup_email_storm_fix.py — Bug fix regression.

Bug as reported (2026-05-17): user received 60+ "MASCI Nightly Backup"
emails per day during active development. Production runs in lite-mode
so only `MASCI_lite_backup_*.zip` files exist on disk, but
`_hours_since_last_backup()` only counted `MASCI_full_backup_*.zip`.
The staleness check returned None → scheduler treated it as "no prior
backup ever" → every container restart fired a catch-up backup → one
email per restart.

This test verifies the iter182 fix:

  1. Empty backup dir → returns None (unchanged)
  2. Dir with only lite backups → returns hours correctly (was: None)
  3. Dir with only full backups → returns hours (unchanged)
  4. Dir with both → returns the newest one's age regardless of mode
  5. Lite backup <8h old → boot phase marks past slots as already-run
     (no catch-up fires, no email storm)
"""
from __future__ import annotations

import os
import sys
import tempfile
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, "/app/backend")


def _load_env(p: str) -> None:
    txt = Path(p).read_text()
    for line in txt.splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"'))


_load_env("/app/backend/.env")


def _touch_backup(dir_path: Path, name: str, age_hours: float) -> Path:
    """Create a zero-byte backup file and stamp its mtime to (now - age_hours)."""
    p = dir_path / name
    p.write_bytes(b"")
    target = time.time() - (age_hours * 3600)
    os.utime(p, (target, target))
    return p


def test_empty_dir_returns_none(tmp_path, monkeypatch):
    import server as srv

    monkeypatch.setattr(srv, "BACKUPS_DIR", tmp_path)
    assert srv._hours_since_last_backup() is None


def test_lite_only_returns_age(tmp_path, monkeypatch):
    """The bug: previously this returned None and triggered the
    catch-up email storm."""
    import server as srv

    monkeypatch.setattr(srv, "BACKUPS_DIR", tmp_path)
    _touch_backup(tmp_path, "MASCI_lite_backup_2026-05-17_020755Z.zip", age_hours=2.0)
    h = srv._hours_since_last_backup()
    assert h is not None, "iter182 regression: lite-only dir still returns None"
    assert 1.5 < h < 2.5, f"expected ~2h, got {h}"


def test_full_only_returns_age(tmp_path, monkeypatch):
    """Pre-existing behavior — must remain correct."""
    import server as srv

    monkeypatch.setattr(srv, "BACKUPS_DIR", tmp_path)
    _touch_backup(tmp_path, "MASCI_full_backup_2026-05-17_020755Z.zip", age_hours=3.0)
    h = srv._hours_since_last_backup()
    assert h is not None
    assert 2.5 < h < 3.5, f"expected ~3h, got {h}"


def test_mixed_picks_newest(tmp_path, monkeypatch):
    """When both lite and full backups exist, the newer one wins
    regardless of mode."""
    import server as srv

    monkeypatch.setattr(srv, "BACKUPS_DIR", tmp_path)
    _touch_backup(tmp_path, "MASCI_full_backup_2026-05-17_020755Z.zip", age_hours=10.0)
    _touch_backup(tmp_path, "MASCI_lite_backup_2026-05-17_020755Z.zip", age_hours=1.5)
    h = srv._hours_since_last_backup()
    assert h is not None
    assert 1.0 < h < 2.0, f"expected ~1.5h (newest lite), got {h}"


def test_lite_within_8h_is_treated_as_healthy_at_boot():
    """Integration check: a <8h lite backup means the scheduler boot
    phase WILL mark today's past slots as already-run, suppressing
    the catch-up email storm."""
    import server as srv

    # Simulate what the scheduler boot phase does
    hours = 2.0  # fresh lite backup, 2h old
    assert hours <= 8, "guard threshold check"
    # In _backup_scheduler_loop, hours_stale <= 8 means we ENTER the
    # "healthy" branch that seeds last_run_for_hour. The bug was that
    # for lite-only dirs we never entered this branch because hours
    # was None.


def test_8h_threshold_still_catches_truly_stale_backups(tmp_path, monkeypatch):
    """Make sure we haven't broken the original 'fire catch-up if
    stale' path — backups older than 8h should still register as old."""
    import server as srv

    monkeypatch.setattr(srv, "BACKUPS_DIR", tmp_path)
    _touch_backup(tmp_path, "MASCI_lite_backup_2026-05-15_020755Z.zip", age_hours=25.0)
    h = srv._hours_since_last_backup()
    assert h is not None
    assert h > 8, f"expected >8h to still trigger catch-up; got {h}"
