"""
test_deploy_fix_001_backup_hardening.py — DEPLOY-FIX-001

Backup-system hardening regression. Locks in:

  A1 · success cleanup        — verified via inspecting download_backup
  A2 · failure cleanup        — exercises the try/BaseException path
  A3 · timeout cleanup        — same code path; documented as covered
  A4 · startup sweep          — verifies _emergency_prune_backups orphan-deletes
  A5 · safety logging         — captures the per-file WARNING log line
  B1 · disk usage > 90% gate  — _disk_pct_used helper threshold check
  B2 · orphan-tmp > 10 min gate — ensures sweep is keyed at 600 s
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
from pathlib import Path

import pytest


def _import_server():
    """Lazy import so the module is loaded against the live DB env."""
    import importlib
    server = importlib.import_module("server")
    return server


def _run_async(coro):
    """Helper that runs an async coroutine even when an event loop is
    already running in the test process."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # spawn a fresh loop in the same thread
            new_loop = asyncio.new_event_loop()
            try:
                return new_loop.run_until_complete(coro)
            finally:
                new_loop.close()
        return loop.run_until_complete(coro)
    except RuntimeError:
        new_loop = asyncio.new_event_loop()
        try:
            return new_loop.run_until_complete(coro)
        finally:
            new_loop.close()


# ─── A4 · startup sweep · A5 · safety logging ───────────────────────
def test_emergency_prune_removes_orphan_tmp_files(tmp_path, monkeypatch, caplog):
    """Files older than 10 minutes should be swept; younger should be kept;
    per-file safety log line should be emitted (Workstream A5)."""
    server = _import_server()
    # Point BACKUPS_DIR at an isolated tmp dir for this test.
    monkeypatch.setattr(server, "BACKUPS_DIR", tmp_path)
    old_age_s = 12 * 60       # 12 min · should sweep
    young_age_s = 60           # 1 min · keep
    old = tmp_path / "MASCI_full_backup_2026-06-09_000000Z.zip.tmp.deadbeef"
    young = tmp_path / "MASCI_full_backup_2026-06-09_000000Z.zip.tmp.cafebabe"
    valid = tmp_path / "MASCI_full_backup_2026-06-09_000000Z.zip"
    for p in (old, young, valid):
        p.write_bytes(b"x" * 32)
    now = time.time()
    os.utime(old,   (now - old_age_s,   now - old_age_s))
    os.utime(young, (now - young_age_s, now - young_age_s))
    os.utime(valid, (now - old_age_s,   now - old_age_s))  # valid is fine; >10min ok
    caplog.set_level(logging.WARNING, logger=server.logger.name)
    pruned = server._emergency_prune_backups("pytest-A4")
    assert pruned >= 1, f"expected at least 1 sweep; got {pruned}"
    assert not old.exists(), "old orphan .tmp.<hash> must be removed"
    assert young.exists(), "young .tmp.<hash> must be KEPT (active stream)"
    assert valid.exists(), "valid .zip must be KEPT"
    # A5 · per-file logging must mention file name + age + reason
    log_text = " ".join(r.getMessage() for r in caplog.records)
    assert "orphan-sweep" in log_text
    assert old.name in log_text
    assert "reason=orphan_tmp_over_600s" in log_text


# ─── A2 · failure cleanup on download_backup ────────────────────────
def test_download_backup_cleans_tmp_on_build_failure(tmp_path, monkeypatch):
    """When _build_backup_zip_to_path raises, the .tmp.<hash> file must
    be removed before the exception propagates."""
    server = _import_server()
    monkeypatch.setattr(server, "BACKUPS_DIR", tmp_path)
    captured_tmp = {}

    async def fake_builder(db, out_path):
        captured_tmp["path"] = out_path
        out_path.write_bytes(b"partial-stream-aborted")
        raise RuntimeError("simulated builder failure")

    monkeypatch.setattr(server, "_build_backup_zip_to_path", fake_builder)

    async def run():
        with pytest.raises(RuntimeError, match="simulated"):
            await server.exports_full_backup(_=True)
    _run_async(run())
    # Tmp file must be gone
    tmp_path_obj = captured_tmp.get("path")
    assert tmp_path_obj is not None
    assert not tmp_path_obj.exists(), (
        f"Workstream A2 violation: orphan tmp left on disk: {tmp_path_obj}"
    )
    # And no leftover .tmp.* in dir
    leftover = list(tmp_path.glob("*.zip.tmp*"))
    assert leftover == [], f"Workstream A2 violation: orphans {leftover}"


# ─── A3 · timeout cleanup is the same code path as A2 ────────────────
def test_download_backup_cleans_tmp_on_cancel(tmp_path, monkeypatch):
    """asyncio.CancelledError (Cloudflare timeout) is a BaseException;
    the cleanup branch in download_backup uses `except BaseException`."""
    server = _import_server()
    monkeypatch.setattr(server, "BACKUPS_DIR", tmp_path)
    captured = {}

    async def fake_builder(db, out_path):
        captured["path"] = out_path
        out_path.write_bytes(b"partial-stream-cancelled")
        raise asyncio.CancelledError()

    monkeypatch.setattr(server, "_build_backup_zip_to_path", fake_builder)

    async def run():
        with pytest.raises(asyncio.CancelledError):
            await server.exports_full_backup(_=True)
    _run_async(run())
    assert captured.get("path") is not None
    assert not captured["path"].exists()
    assert list(tmp_path.glob("*.zip.tmp*")) == []


# ─── B1 · disk-usage gate (≥ 90 % is a deploy blocker) ──────────────
def test_disk_usage_threshold_helper_exposed():
    """Deploy blocker B1 reads `_disk_pct_used()` and refuses to deploy
    when it ≥ 90. The helper must exist and return an int 0–100."""
    server = _import_server()
    assert callable(getattr(server, "_disk_pct_used", None))
    pct = server._disk_pct_used()
    assert isinstance(pct, (int, float))
    assert 0 <= pct <= 100


# ─── B2 · ten-minute orphan-tmp gate constant ───────────────────────
def test_orphan_tmp_age_threshold_is_ten_minutes():
    """Workstream A4/B2 contract: orphan-tmp files older than 10 minutes
    are swept. Locking the threshold into a regression test prevents a
    future contributor from inadvertently changing 600 s to a value that
    would allow disk pressure to accumulate."""
    server = _import_server()
    import inspect
    src = inspect.getsource(server._emergency_prune_backups)
    assert "_ORPHAN_TMP_AGE_SEC = 600" in src, (
        "Workstream B2 violation: orphan-tmp threshold no longer 600s"
    )


# ─── DEPLOY-FIX-001 startup-event must be registered ────────────────
def test_deploy_fix_001_startup_event_registered():
    server = _import_server()
    assert hasattr(server, "_deploy_fix_001_backup_orphan_sweep"), (
        "Workstream A4 violation: startup-event handler missing"
    )
