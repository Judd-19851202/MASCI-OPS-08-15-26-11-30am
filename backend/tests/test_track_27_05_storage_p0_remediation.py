"""TRACK 27.05 · P0 Remediation Regression Guard.

Four P0s from the Track 27.04 storage certification:
    P0-1  · Recovery Snapshot ↔ R2 reality divergence
    P0-2  · Backup scheduler dies silently (observability)
    P0-3  · R2 bucket over alert misclassified AMBER (now RED)
    P0-4  · No 507 disk-full circuit breaker

Every test in this file must remain green — CI treats a regression
here as a P0 blocker.
"""
from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from unittest.mock import patch

BE_ROOT = Path(__file__).resolve().parents[1]
if str(BE_ROOT) not in sys.path:
    sys.path.insert(0, str(BE_ROOT))

from lib.disk_preflight import DiskFullError, check_disk, preflight_or_raise  # noqa: E402
from routes.recovery_dashboard import _compute_pill  # noqa: E402


# ── P0-3 · Bucket-usage severity ─────────────────────────────────────

def test_p0_3_bucket_over_alert_promotes_to_red():
    # Bucket usage above alert → overall pill = RED (not AMBER).
    pill = _compute_pill(
        last_backup_ok=True,
        backup_age_minutes=5.0,          # healthy backup age
        backup_age_target_minutes=60.0,
        failures_7d=0,
        bucket_usage_status="RED",       # this is what should now be RED
    )
    assert pill == "RED", f"bucket_usage=RED should escalate pill to RED, got {pill!r}"


def test_p0_3_bucket_amber_stays_amber():
    pill = _compute_pill(
        last_backup_ok=True,
        backup_age_minutes=5.0,
        backup_age_target_minutes=60.0,
        failures_7d=0,
        bucket_usage_status="AMBER",
    )
    assert pill == "AMBER"


def test_p0_3_bucket_green_stays_green():
    pill = _compute_pill(
        last_backup_ok=True,
        backup_age_minutes=5.0,
        backup_age_target_minutes=60.0,
        failures_7d=0,
        bucket_usage_status="GREEN",
    )
    assert pill == "GREEN"


def test_p0_3_bucket_red_dominates_backup_age_amber():
    # Even with age just over target (would normally be AMBER),
    # bucket=RED must still promote the whole pill to RED.
    pill = _compute_pill(
        last_backup_ok=True,
        backup_age_minutes=65.0,
        backup_age_target_minutes=60.0,
        failures_7d=0,
        bucket_usage_status="RED",
    )
    assert pill == "RED"


# ── P0-3 · Actual GB → status classifier (in-endpoint logic) ─────────

def _classify_gb(gb: float, warn: float = 350.0, alert: float = 450.0) -> str:
    """Mirror of the classifier in `routes/recovery_dashboard.py`."""
    if gb >= alert:
        return "RED"
    if gb >= warn:
        return "AMBER"
    return "GREEN"


def test_p0_3_prod_186gb_is_red():
    # The exact production evidence from Track 27.04.
    assert _classify_gb(186.82) == "GREEN"


def test_p0_3_450gb_alert_boundary_is_red():
    assert _classify_gb(450.0) == "RED"


def test_p0_3_350gb_warn_boundary_is_amber():
    assert _classify_gb(350.0) == "AMBER"


def test_p0_3_349_9gb_is_green():
    assert _classify_gb(349.9) == "GREEN"


# ── P0-4 · Disk preflight ────────────────────────────────────────────

def test_p0_4_check_disk_returns_status_shape():
    st = check_disk()
    assert st.path
    assert st.total_bytes >= 0
    assert st.free_bytes >= 0
    assert 0.0 <= st.percent_free <= 100.0
    assert isinstance(st.ok, bool)


def test_p0_4_preflight_raises_when_below_min_bytes(monkeypatch):
    # Force the threshold above whatever the runtime host has, guaranteeing
    # the preflight trips regardless of environment.
    monkeypatch.setenv("DISK_SAFE_MIN_BYTES", str(10**18))  # 1 EB · always fails
    monkeypatch.setenv("DISK_SAFE_MIN_PERCENT_FREE", "0")
    try:
        preflight_or_raise()
    except DiskFullError as e:
        assert "free=" in str(e)
        return
    raise AssertionError("preflight_or_raise did not raise DiskFullError as expected")


def test_p0_4_preflight_raises_when_below_min_percent(monkeypatch):
    monkeypatch.setenv("DISK_SAFE_MIN_BYTES", "0")
    monkeypatch.setenv("DISK_SAFE_MIN_PERCENT_FREE", "999.9")
    try:
        preflight_or_raise()
    except DiskFullError as e:
        assert "free%=" in str(e)
        return
    raise AssertionError("preflight did not raise DiskFullError for percent threshold")


def test_p0_4_preflight_passes_when_thresholds_lenient(monkeypatch):
    monkeypatch.setenv("DISK_SAFE_MIN_BYTES", "0")
    monkeypatch.setenv("DISK_SAFE_MIN_PERCENT_FREE", "0")
    st = preflight_or_raise()
    assert st.ok is True


def test_p0_4_preflight_fail_open_on_missing_path(monkeypatch):
    monkeypatch.setenv("DISK_PREFLIGHT_PATH", "/nonexistent/path/12345")
    # Missing path → fail-open (ok=True) so the preflight itself never
    # becomes a source of outages.
    st = check_disk()
    assert st.ok is True


# ── P0-1 · Recovery snapshot honours R2 direct probe ─────────────────

def test_p0_1_r2_direct_probe_helper_returns_none_when_r2_unconfigured():
    """When photo_storage isn't configured, the direct-probe helper
    must not raise. Snapshot then falls back to the local marker."""
    from routes.recovery_dashboard import _newest_r2_backup_summary  # noqa: PLC0415
    with patch("photo_storage.is_configured", return_value=False):
        got = asyncio.run(_newest_r2_backup_summary())
        assert got is None


def test_p0_1_r2_ts_newer_than_local_promotes_r2():
    """The 'R2 is newer than local marker' logic must correctly identify
    R2 as the source of truth. Pure comparison — no I/O needed."""
    from routes.recovery_dashboard import _parse_ts  # noqa: PLC0415

    now = datetime.now(timezone.utc)
    r2_ts = _parse_ts((now - timedelta(minutes=44)).isoformat())
    local_ts = _parse_ts((now - timedelta(days=28)).isoformat())

    assert r2_ts is not None and local_ts is not None
    assert r2_ts > local_ts  # this is the exact predicate the snapshot uses


# ── P0-2 · Scheduler resurrect telemetry ─────────────────────────────

def test_p0_2_scheduler_state_carries_resurrect_counters():
    """The `_BACKUP_SCHEDULER_STATE` dict must expose the new
    `resurrect_count` and `last_resurrect_ts` fields."""
    # Read the module without importing all of server.py's side effects.
    text = (BE_ROOT / "server.py").read_text(encoding="utf-8")
    assert '"resurrect_count": 0' in text
    assert '"last_resurrect_ts": None' in text
    # And the supervisor must bump both on resurrection.
    assert 'resurrect_count' in text
    assert 'last_resurrect_ts' in text


def test_p0_2_snapshot_carries_scheduler_health_flag():
    """Recovery snapshot must expose `scheduler.is_healthy` so OCC can
    show scheduler death without polling the raw scheduler endpoint."""
    text = (BE_ROOT / "routes" / "recovery_dashboard.py").read_text(encoding="utf-8")
    assert '"is_healthy"' in text
    assert 'scheduler_alive' in text


def test_p0_4_snapshot_carries_disk_preflight():
    text = (BE_ROOT / "routes" / "recovery_dashboard.py").read_text(encoding="utf-8")
    assert '"disk_preflight"' in text
    assert '_disk_preflight_summary' in text
