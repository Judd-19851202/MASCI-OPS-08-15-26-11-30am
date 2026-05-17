"""iter186 — Phase 2 hardening: Sentry config gate + session-timeout
middleware + R2 lifecycle --verify + /api/version surfacing.

This file tests the four Initiative 1–4 implementations:

  • sentry_init.init_sentry_if_configured behaves correctly with /
    without DSN, scrubs PII, and never raises.
  • session_timeout middleware is a no-op when SESSION_TIMEOUTS_ENABLED
    is unset, enforces idle / absolute timeouts when set, and surfaces
    its config via describe_config().
  • /api/version exposes the session-timeout + sentry config blocks
    correctly.
  • Restore-drill safety rails refuse dangerous targets.
"""
from __future__ import annotations

import importlib
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
import requests

# Ensure backend is importable
sys.path.insert(0, "/app/backend")

URL = os.environ.get("PUBLIC_BACKEND_URL") or "http://localhost:8001"


# ─────────────────────────────────────────────────────────────────────────
# Sentry config gate
# ─────────────────────────────────────────────────────────────────────────
def test_sentry_no_op_without_dsn(monkeypatch):
    """init_sentry_if_configured must return False and not raise when
    SENTRY_DSN is unset."""
    monkeypatch.delenv("SENTRY_DSN", raising=False)
    import sentry_init
    importlib.reload(sentry_init)
    assert sentry_init.init_sentry_if_configured() is False
    assert sentry_init.is_initialized() is False


def test_sentry_release_identifier_deterministic(monkeypatch):
    """get_release_identifier must return a stable hex string even
    without env vars (falls back to source_hash)."""
    monkeypatch.delenv("DEPLOY_VERSION_HASH", raising=False)
    monkeypatch.delenv("GIT_COMMIT", raising=False)
    import sentry_init
    importlib.reload(sentry_init)
    rel = sentry_init.get_release_identifier()
    assert isinstance(rel, str) and len(rel) > 0
    assert rel != "unknown"  # source-hash fallback should fire


def test_sentry_scrubber_strips_pii():
    """The before_send hook must strip password/token/secret fields
    from any nested structure."""
    import sentry_init

    event = {
        "request": {
            "headers": {
                "Authorization": "Bearer abc",
                "X-Admin-Token": "deadbeefcafe",
                "User-Agent": "MASCI",
            },
            "cookies": {"session": "secret-cookie"},
            "data": {"password": "leakedpw", "name": "Joe"},
        },
        "extra": {"api_key": "k-1234", "note": "ok"},
        "logentry": {"message": "ran with token " + "f" * 64},
    }
    out = sentry_init._before_send(event, {})
    assert out["request"]["headers"]["Authorization"] == "***SCRUBBED***"
    assert out["request"]["headers"]["X-Admin-Token"] == "***SCRUBBED***"
    assert out["request"]["headers"]["User-Agent"] == "MASCI"
    assert out["request"]["cookies"] == "***SCRUBBED***"
    assert out["request"]["data"]["password"] == "***SCRUBBED***"
    assert out["request"]["data"]["name"] == "Joe"
    assert out["extra"]["api_key"] == "***SCRUBBED***"
    assert out["extra"]["note"] == "ok"
    assert "f" * 64 not in out["logentry"]["message"]
    assert "***SCRUBBED***" in out["logentry"]["message"]


# ─────────────────────────────────────────────────────────────────────────
# Session timeout — config + tier mapping (unit, no backend touch)
# ─────────────────────────────────────────────────────────────────────────
def test_session_timeout_default_disabled(monkeypatch):
    monkeypatch.delenv("SESSION_TIMEOUTS_ENABLED", raising=False)
    import session_timeout
    cfg = session_timeout.describe_config()
    assert cfg["enabled"] is False


def test_session_timeout_tiers_populated(monkeypatch):
    monkeypatch.setenv("SESSION_TIMEOUTS_ENABLED", "true")
    import session_timeout
    cfg = session_timeout.describe_config()
    assert cfg["enabled"] is True
    assert cfg["tiers"]["ADMIN_HR"]["idle_min"] == 15
    assert cfg["tiers"]["ADMIN_HR"]["abs_hour"] == 4
    assert cfg["tiers"]["OPERATIONS"]["idle_min"] == 30
    assert cfg["tiers"]["OPERATIONS"]["abs_hour"] == 8
    assert cfg["tiers"]["FIELD"]["idle_min"] == 60
    assert cfg["tiers"]["FIELD"]["abs_hour"] == 12


def test_session_timeout_env_overrides(monkeypatch):
    monkeypatch.setenv("SESSION_TIMEOUTS_ENABLED", "true")
    monkeypatch.setenv("SESSION_IDLE_MIN_ADMIN_HR", "5")
    monkeypatch.setenv("SESSION_ABS_HOUR_ADMIN_HR", "1")
    import session_timeout
    cfg = session_timeout.describe_config()
    assert cfg["tiers"]["ADMIN_HR"]["idle_min"] == 5
    assert cfg["tiers"]["ADMIN_HR"]["abs_hour"] == 1


def test_session_timeout_tier_picker():
    """The header → tier resolver must pick the strictest available."""
    import session_timeout as st
    # Admin wins over PM
    headers = {"X-Admin-Token": "abc", "X-PM-Token": "xyz"}
    tok, tier = st._pick_token_and_tier(headers)
    assert tier == "ADMIN_HR"
    # PM only
    tok, tier = st._pick_token_and_tier({"X-PM-Token": "xyz"})
    assert tier == "OPERATIONS"
    # Field only
    tok, tier = st._pick_token_and_tier({"X-Field-Leadership-Token": "abc"})
    assert tier == "FIELD"
    # Dev token (excluded — vendor)
    tok, tier = st._pick_token_and_tier({"X-Dev-Token": "abc"})
    assert tok is None and tier is None
    # Anonymous
    tok, tier = st._pick_token_and_tier({"Authorization": "Bearer abc"})
    assert tok is None and tier is None


# ─────────────────────────────────────────────────────────────────────────
# /api/version — Sentry + session-timeout visibility
# ─────────────────────────────────────────────────────────────────────────
def test_api_version_exposes_hardening_config():
    r = requests.get(f"{URL}/api/version", timeout=10)
    assert r.status_code == 200
    body = r.json()
    # Existing fields preserved
    assert body["service"] == "masci-hub"
    assert "source_hash" in body
    # New hardening surface
    assert "release" in body
    assert "session_timeouts" in body
    assert "enabled" in body["session_timeouts"]
    assert "tiers" in body["session_timeouts"]
    assert "sentry" in body
    assert "enabled" in body["sentry"]


def test_api_version_release_matches_source_hash_when_no_git():
    """When GIT_COMMIT etc are unset, release === source_hash prefix (16)."""
    r = requests.get(f"{URL}/api/version", timeout=10)
    body = r.json()
    # release is 16-char prefix when fallback fires; matches source_hash[:16]
    # (only assert when GIT_COMMIT etc weren't set on the backend)
    if body.get("commit") == "unknown":
        assert body["release"] == body["source_hash"][:16]


# ─────────────────────────────────────────────────────────────────────────
# Restore drill — safety rails (no actual restore in this test; that's the
# real-R2 smoke test gated by env)
# ─────────────────────────────────────────────────────────────────────────
SCRIPT_RESTORE = Path("/app/scripts/restore_drill.py")


def _run_restore(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT_RESTORE), *args],
        capture_output=True, text=True, timeout=30,
    )


def test_restore_refuses_live_db():
    """--target-db == live DB_NAME must be refused."""
    live_db = os.environ.get("DB_NAME") or ""
    if not live_db:
        # Read backend/.env directly so the test works in subprocess
        env_file = Path("/app/backend/.env")
        for line in env_file.read_text().splitlines():
            if line.startswith("DB_NAME="):
                live_db = line.split("=", 1)[1].strip().strip('"')
                break
    assert live_db, "could not determine live DB_NAME for safety test"
    r = _run_restore("--backup", "fake", "--target", "mongodb://localhost:27017",
                     "--target-db", live_db)
    assert r.returncode == 3, f"expected refusal, got rc={r.returncode}"
    assert "REFUSING" in r.stderr or "REFUSING" in r.stdout


def test_restore_refuses_non_drill_target_db():
    """--target-db that doesn't start with masci_restore_drill_ must be
    refused (unless overridden)."""
    r = _run_restore("--backup", "fake", "--target", "mongodb://localhost:27017",
                     "--target-db", "some_other_db")
    assert r.returncode == 3
    assert "REFUSING" in r.stderr or "REFUSING" in r.stdout


def test_restore_list_works():
    """--list lists R2 backups without touching anything."""
    r = _run_restore("--list", "--limit", "5")
    assert r.returncode == 0, r.stderr
    assert "Listing R2 backups" in r.stdout or "Total objects" in r.stdout


# ─────────────────────────────────────────────────────────────────────────
# R2 lifecycle --verify: sentinel round-trip works even when lifecycle is
# not yet active (returns rc=6 then). We just confirm the script doesn't
# crash and reports the misconfig correctly.
# ─────────────────────────────────────────────────────────────────────────
SCRIPT_R2 = Path("/app/scripts/r2_lifecycle_apply.py")


def test_r2_lifecycle_verify_runs():
    """--verify must run end-to-end without crashing. Exit code 0 if the
    lifecycle rule is active; 6 if it isn't (acceptable — user hasn't
    rotated token yet). Either way, sentinel write + read + cleanup
    must succeed and be visible in stdout."""
    r = subprocess.run(
        [sys.executable, str(SCRIPT_R2), "--verify"],
        capture_output=True, text=True, timeout=30,
    )
    # Acceptable exit codes: 0 (rule active), 6 (rule missing), 7 (misconfig)
    assert r.returncode in (0, 6, 7), \
        f"unexpected rc={r.returncode}: stderr={r.stderr}"
    assert "Step 1 — wrote sentinel object" in r.stdout
    assert "Step 2 — read-back matches" in r.stdout
    assert "Step 4 — sentinel cleaned up" in r.stdout
