"""
iter299 · Lane D regression tests · operational hygiene visibility log.

Scope guard: this iteration MUST remain visibility-only. No new endpoints,
no new collections, no new prune behavior. These tests lock that boundary
along with verifying the log line composition.
"""
from __future__ import annotations

import inspect
import logging

import pytest


@pytest.fixture(scope="module")
def server_module():
    import sys
    if "/app/backend" not in sys.path:
        sys.path.insert(0, "/app/backend")
    import server as srv  # type: ignore
    return srv


def test_iter299_warn_watermark_constant_present(server_module):
    """The 85% warning threshold is configured separately from the
    existing 75% prune threshold and the 90% hard-abort line."""
    assert hasattr(server_module, "BACKUP_DISK_WARN_WATERMARK"), (
        "iter299 must expose BACKUP_DISK_WARN_WATERMARK"
    )
    assert server_module.BACKUP_DISK_WARN_WATERMARK == 85, (
        "default warn watermark must be 85% per operator direction"
    )
    # And it must sit strictly between the existing 75 prune and 90 abort lines.
    assert (
        server_module.BACKUP_DISK_HIGH_WATERMARK
        < server_module.BACKUP_DISK_WARN_WATERMARK
        < 90
    ), "warn watermark must sit between prune (75) and abort (90)"


def test_iter299_hygiene_helper_is_async(server_module):
    """Hygiene helper must be a coroutine — fired from startup event +
    inside the scheduled backup runner."""
    fn = server_module._log_operational_hygiene
    assert inspect.iscoroutinefunction(fn), (
        "_log_operational_hygiene must be async"
    )


def test_iter299_hygiene_helper_signature(server_module):
    """Signature lock — `reason` + `db` keyword args, defaults sensible."""
    sig = inspect.signature(server_module._log_operational_hygiene)
    params = sig.parameters
    assert "reason" in params
    assert "db" in params
    assert params["reason"].default == "startup"
    assert params["db"].default is None


def test_iter299_no_new_endpoints_added(server_module):
    """Bounded-scope guard — iter299 must not have registered new API
    endpoints. Operational hygiene is log-only."""
    routes = [r.path for r in server_module.app.routes]
    BANNED_PATTERNS = [
        "/admin/disk-pressure",
        "/admin/ops-hygiene",
        "/admin/backup-health-summary",
        "/admin/disk-warn",
        "/api/admin/disk-pressure",
        "/api/admin/ops-hygiene",
    ]
    for pat in BANNED_PATTERNS:
        assert pat not in routes, (
            f"iter299 scope violation: endpoint {pat} registered "
            "(hygiene must remain visibility-only)"
        )


def test_iter299_no_new_collections_referenced(server_module):
    """Bounded-scope guard — the hygiene helper must NOT create or write
    to any new Mongo collection. It only READS the existing
    `backup_health` collection. Source-level inspection."""
    src = inspect.getsource(server_module._log_operational_hygiene)
    # Forbid any write-style call on collections inside this helper.
    BANNED_WRITE_CALLS = [
        ".insert_one(",
        ".insert_many(",
        ".update_one(",
        ".update_many(",
        ".replace_one(",
        ".delete_one(",
        ".delete_many(",
        ".create_collection(",
    ]
    for bad in BANNED_WRITE_CALLS:
        assert bad not in src, (
            f"iter299 scope violation: hygiene helper uses {bad} "
            "(must be read-only)"
        )
    # Read access ONLY against backup_health.
    BANNED_NEW_COLLECTIONS = [
        "ops_hygiene_log",
        "disk_pressure_events",
        "hygiene_runs",
    ]
    for c in BANNED_NEW_COLLECTIONS:
        assert c not in src, (
            f"iter299 scope violation: hygiene references new collection {c}"
        )


def test_iter299_hygiene_helper_emits_ops_hygiene_tag(server_module, caplog):
    """When invoked, the helper emits at least one log line tagged
    `[ops-hygiene]` — that's how operators grep for it."""
    import asyncio
    caplog.set_level(logging.INFO, logger="server")
    asyncio.run(server_module._log_operational_hygiene(reason="pytest", db=None))
    matching = [r for r in caplog.records if "[ops-hygiene]" in r.getMessage()]
    assert matching, (
        "hygiene helper must emit at least one `[ops-hygiene]` tagged log line"
    )
    # And the line must include the three operator-required signals.
    composite = " ".join(r.getMessage() for r in matching)
    assert "disk=" in composite, "log line must show disk%"
    assert "retention_days=" in composite, "log line must show retention config"
    assert "lite=" in composite, "log line must show lite-backup count separately"


def test_iter299_disk_pressure_severity_escalation(server_module, caplog, monkeypatch):
    """At ≥85% disk, log level must be WARNING (not INFO) so operators
    surface it via `grep WARNING`. Below 85, it's INFO."""
    import asyncio

    # Mock disk pressure → 90% (above warn threshold)
    monkeypatch.setattr(server_module, "_disk_pct_used", lambda *a, **k: 90)
    caplog.clear()
    caplog.set_level(logging.INFO, logger="server")
    asyncio.run(server_module._log_operational_hygiene(reason="pytest-high", db=None))
    high = [r for r in caplog.records if "[ops-hygiene]" in r.getMessage() and "pytest-high" in r.getMessage()]
    assert high, "expected at least one ops-hygiene line at high disk"
    assert any(r.levelno == logging.WARNING for r in high), (
        "≥85% disk must escalate to WARNING level"
    )
    assert any("DISK_PRESSURE" in r.getMessage() for r in high), (
        "high-disk log must include DISK_PRESSURE marker"
    )

    # Mock disk pressure → 50% (below warn threshold)
    monkeypatch.setattr(server_module, "_disk_pct_used", lambda *a, **k: 50)
    caplog.clear()
    asyncio.run(server_module._log_operational_hygiene(reason="pytest-low", db=None))
    low = [r for r in caplog.records if "[ops-hygiene]" in r.getMessage() and "pytest-low" in r.getMessage()]
    assert low, "expected at least one ops-hygiene line at low disk"
    assert all(r.levelno == logging.INFO for r in low), (
        "<85% disk must stay at INFO level"
    )


def test_iter299_existing_prune_logic_unchanged(server_module):
    """Bounded-scope guard — iter299 MUST NOT have altered the existing
    emergency-prune function signature or the BACKUP_KEEP_MAX/BACKUP_RETENTION_DAYS
    defaults (which would silently change retention behavior)."""
    assert hasattr(server_module, "_emergency_prune_backups")
    assert server_module.BACKUP_KEEP_MAX == 3, (
        "BACKUP_KEEP_MAX default must remain 3 (iter299 is visibility-only)"
    )
    assert server_module.BACKUP_RETENTION_DAYS == 14, (
        "BACKUP_RETENTION_DAYS default must remain 14 (iter299 is visibility-only)"
    )
    assert server_module.BACKUP_DISK_HIGH_WATERMARK == 75, (
        "BACKUP_DISK_HIGH_WATERMARK (prune trigger) must remain 75"
    )
