"""
test_iter427_legacy_backup_prune.py · Phase 26.1 · iter427
─────────────────────────────────────────────────────────────────────
Verifies the `_emergency_prune_backups` helper sweeps legacy backup
naming patterns (`MASCI_lite_backup_*.zip` and
`MASCI_complete_backup_*.zip` from pre-iter425) when they are past
the configured retention window, in addition to the canonical
`MASCI_full_backup_*.zip` pattern.

Pre-iter425, the local backups directory accumulated 318+ legacy
"lite" archives forever because the prune logic only globbed the
new `MASCI_full_backup_*.zip` pattern. iter427 (Phase 26.1) extends
the prune sweep to also clean up these legacy files past retention.
"""
import os
import time
from pathlib import Path
import importlib


def test_iter427_emergency_prune_sweeps_legacy_patterns(tmp_path, monkeypatch):
    """Legacy lite + complete patterns must be cleaned past retention."""
    # Point BACKUPS_DIR at a tmp dir so the test isolates from prod.
    monkeypatch.setenv("BACKUP_RETENTION_DAYS", "14")
    monkeypatch.setenv("BACKUP_KEEP_MAX", "3")

    import server
    importlib.reload(server)

    backups_dir = tmp_path / "backups"
    backups_dir.mkdir()
    server.BACKUPS_DIR = backups_dir

    # Seed: a fresh full backup (must be kept), a young lite, an OLD lite,
    # an OLD complete, and a young .tmp orphan (must be kept — could be active).
    now = time.time()
    fresh_full = backups_dir / "MASCI_full_backup_2026-05-25_001500Z.zip"
    young_lite = backups_dir / "MASCI_lite_backup_2026-05-23_001500Z.zip"
    old_lite = backups_dir / "MASCI_lite_backup_2026-05-01_001500Z.zip"
    old_complete = backups_dir / "MASCI_complete_backup_2026-04-25_001500Z.zip"
    young_tmp = backups_dir / "MASCI_full_backup_2026-05-25_010000Z.zip.tmp.abcd1234"
    for p in (fresh_full, young_lite, old_lite, old_complete, young_tmp):
        p.write_bytes(b"x" * 32)

    # Backdate the OLD ones beyond the 14-day retention.
    old_ts = now - (15 * 86400)
    os.utime(old_lite, (old_ts, old_ts))
    os.utime(old_complete, (old_ts, old_ts))
    # Backdate the young lite to 5 days ago (should survive retention).
    young_ts = now - (5 * 86400)
    os.utime(young_lite, (young_ts, young_ts))

    pruned = server._emergency_prune_backups(reason="test_iter427_legacy")

    # 2 legacy files should be deleted; fresh files should remain.
    assert pruned >= 2, f"expected ≥2 pruned, got {pruned}"
    assert fresh_full.exists(), "fresh full backup must be kept"
    assert young_lite.exists(), "young lite (within retention) must be kept"
    assert young_tmp.exists(), "young .tmp orphan (<10 min) must be kept"
    assert not old_lite.exists(), "old lite (past retention) must be pruned"
    assert not old_complete.exists(), "old complete (past retention) must be pruned"


def test_iter427_prune_preserves_young_legacy(tmp_path, monkeypatch):
    """Legacy files WITHIN retention window must NOT be touched.

    Defensive guard — only past-retention files are swept.
    """
    monkeypatch.setenv("BACKUP_RETENTION_DAYS", "14")
    monkeypatch.setenv("BACKUP_KEEP_MAX", "3")

    import server
    importlib.reload(server)

    backups_dir = tmp_path / "backups"
    backups_dir.mkdir()
    server.BACKUPS_DIR = backups_dir

    now = time.time()
    one_day_old_lite = backups_dir / "MASCI_lite_backup_2026-05-24_001500Z.zip"
    one_day_old_complete = backups_dir / "MASCI_complete_backup_2026-05-24_002500Z.zip"
    for p in (one_day_old_lite, one_day_old_complete):
        p.write_bytes(b"x" * 32)
        os.utime(p, (now - 86400, now - 86400))  # 1 day old

    server._emergency_prune_backups(reason="test_iter427_young_legacy_kept")

    assert one_day_old_lite.exists(), "young legacy lite must survive"
    assert one_day_old_complete.exists(), "young legacy complete must survive"
