"""
TRACK 28.09A · Environment Separation & Deployment Integrity — Permanent
Regression Contract.

Locks the invariants proven during the 28.09A audit:

  1. `server.py` startup consistency guard exits non-zero when
     MONGO_URL contains the wrong environment's user.
  2. `db_isolation_failsafe.py` runs on startup and can hard-exit.
  3. `/api/version` exposes a safe `environment_identity` block with
     zero credentials.
  4. Zero preview URL hardcoded in production runtime source.
  5. Preview production-safety flags remain correct in preview
     (`AUTO_EMAIL_REPORTS=false`, `SCHEDULER_ENABLED=false`,
     `MAINTAINX_WRITE_ENABLED=false`).

Companion runtime probes live in `test_rc1_predeploy_isolation.py`.
This suite adds source-level structural + endpoint-shape assertions
so future edits cannot silently drop the crossover guarantees.
"""
from __future__ import annotations

import re
from pathlib import Path

import httpx
import pytest


BACKEND = "http://localhost:8001"
SERVER_PY = Path("/app/backend/server.py")
DB_FAILSAFE = Path("/app/backend/db_isolation_failsafe.py")


def _get_version_with_retry():
    """The backend is behind supervisor + hot-reload; occasionally the
    first httpx request after a reload times out. Retry up to 3× with
    increasing timeouts so the structural contract is not blocked by
    transient network flakes."""
    import time as _time
    last = None
    for delay in (0, 2, 4):
        if delay:
            _time.sleep(delay)
        try:
            r = httpx.get(f"{BACKEND}/api/version", timeout=15.0)
            if r.status_code == 200:
                return r
            last = f"status={r.status_code}"
        except httpx.HTTPError as e:
            last = f"{type(e).__name__}: {e}"
    pytest.fail(f"/api/version unreachable after 3 retries: {last}")


def _read(path: Path) -> str:
    assert path.exists(), f"missing file: {path}"
    return path.read_text(encoding="utf-8")


# ------------------------------------------------------------------
# Phase 10 · Environment assertion guards (structural)
# ------------------------------------------------------------------

def test_server_boot_guard_covers_preview_user():
    src = _read(SERVER_PY)
    # The preview/prod consistency check must remain in place.
    assert "_PREVIEW_USER = 'masci_preview_user'" in src, (
        "TRACK 28.09A regression: preview user constant removed from "
        "server.py startup guard. Restore lines 40-65."
    )
    assert "_PROD_USER = 'masci_prod_user'" in src, (
        "TRACK 28.09A regression: prod user constant removed from "
        "server.py startup guard."
    )
    assert "sys.exit(98)" in src, (
        "TRACK 28.09A regression: sys.exit(98) removed from server.py "
        "consistency guard. Guard must hard-exit on env crossover."
    )


def test_db_isolation_failsafe_module_intact():
    src = _read(DB_FAILSAFE)
    assert "PREVIEW_DB" in src and "PROD_DB" in src
    assert "ENFORCE_DB_ISOLATION" in src
    assert "sys.exit(99)" in src, (
        "TRACK 28.09A regression: db_isolation_failsafe.py must still "
        "hard-exit non-zero when ENFORCE_DB_ISOLATION=true and the probe "
        "detects cross-env visibility."
    )


def test_db_isolation_failsafe_wired_into_server():
    src = _read(SERVER_PY)
    assert "from db_isolation_failsafe import assert_db_isolation" in src, (
        "TRACK 28.09A regression: db_isolation_failsafe.assert_db_isolation "
        "is not imported by server.py. The failsafe must run on startup."
    )


# ------------------------------------------------------------------
# Phase 11 · Runtime Identity Endpoint shape
# ------------------------------------------------------------------

REQUIRED_IDENTITY_KEYS = {
    "app_env",
    "db_name",
    "db_isolation_enforced",
    "storage_bucket",
    "storage_endpoint_present",
    "scheduler_enabled",
    "email_safety_mode",
    "auto_email_reports",
    "resend_webhook_secret_present",
    "dev_endpoints_enabled",
    "maintainx_write_enabled",
    "ai_provider_key_present",
    "delete_engine_status",
}


def test_version_endpoint_exposes_environment_identity():
    r = _get_version_with_retry()
    body = r.json()
    ident = body.get("environment_identity") or {}
    missing = REQUIRED_IDENTITY_KEYS - set(ident.keys())
    assert not missing, (
        f"TRACK 28.09A regression: /api/version environment_identity is "
        f"missing keys: {missing}. All safe identity labels must remain "
        "exposed for operator visibility."
    )


def test_version_endpoint_does_not_leak_secrets():
    r = _get_version_with_retry()
    body_text = r.text
    forbidden = [
        "mongodb+srv://",  # never expose the URI
        "mongodb://",
        "cloudflarestorage.com",  # never expose R2 endpoint
        "sk-",  # generic API key prefix
        "re_",  # Resend key prefix (needs care)
    ]
    for pat in forbidden:
        # `re_` is a common substring — only flag if followed by API-key-like chars.
        if pat == "re_":
            m = re.search(r"\bre_[A-Za-z0-9]{20,}", body_text)
            if m:
                pytest.fail(
                    f"TRACK 28.09A regression: /api/version leaks Resend "
                    f"API key material: {m.group(0)[:12]}..."
                )
            continue
        assert pat not in body_text, (
            f"TRACK 28.09A regression: /api/version leaks forbidden "
            f"pattern `{pat}`. Environment identity must remain "
            "label-only, no credentials."
        )


def test_version_endpoint_reports_delete_engine_disabled():
    r = _get_version_with_retry()
    ident = r.json().get("environment_identity") or {}
    assert ident.get("delete_engine_status") == "DISABLED", (
        "TRACK 28.09A regression: environment_identity.delete_engine_status "
        f"MUST be 'DISABLED' (Track 27.07 gate). Got: "
        f"{ident.get('delete_engine_status')!r}"
    )


# ------------------------------------------------------------------
# Phase 9 · Codebase hardcode scan
# ------------------------------------------------------------------

PREVIEW_URL_PATTERN = re.compile(r"safety-audit-mobile-1\.preview\.emergentagent\.com")
BACKEND_RUNTIME_DIRS = [
    Path("/app/backend/lib"),
    Path("/app/backend/routes"),
    Path("/app/backend/services"),
]

# Files where preview identity is intentionally referenced (memory, tests,
# constants used by the isolation guard).
ALLOWED_PREVIEW_REFERENCE_FILES = {
    "backend/db_isolation_failsafe.py",  # explicit constants
    "backend/server.py",  # explicit guard constants
    "backend/routes/cluster_capacity.py",  # dual-cluster observability endpoint (safe read-only)
}


def test_no_preview_hostname_in_backend_runtime_source():
    offenders = []
    for root in BACKEND_RUNTIME_DIRS:
        if not root.exists():
            continue
        for p in root.rglob("*.py"):
            rel = p.relative_to(Path("/app")).as_posix()
            if rel in ALLOWED_PREVIEW_REFERENCE_FILES:
                continue
            try:
                text = p.read_text(encoding="utf-8")
            except Exception:
                continue
            if PREVIEW_URL_PATTERN.search(text):
                offenders.append(rel)
    assert not offenders, (
        f"TRACK 28.09A regression: preview hostname hardcoded in backend "
        f"runtime source (would leak in production): {offenders}. Fix by "
        "reading from env or removing the hostname reference."
    )


# ------------------------------------------------------------------
# Phase 6 · Preview scheduler safety
# ------------------------------------------------------------------

def test_preview_env_prevents_auto_email_broadcast():
    """Preview .env must NOT enable AUTO_EMAIL_REPORTS. This test reads
    the on-disk file directly (via the loaded environment) so drift is
    caught even if the process was launched with a different env."""
    import os as _os
    from dotenv import load_dotenv as _load
    _load("/app/backend/.env")
    flag = (_os.environ.get("AUTO_EMAIL_REPORTS") or "").strip().lower()
    if _os.environ.get("APP_ENV", "").strip().lower() == "preview":
        assert flag in ("false", "0", "no", "off", ""), (
            f"TRACK 28.09A regression: preview environment must have "
            f"AUTO_EMAIL_REPORTS disabled. Current={flag!r}"
        )


def test_preview_env_prevents_production_scheduler_execution():
    """Preview must NOT run production schedulers by default."""
    import os as _os
    from dotenv import load_dotenv as _load
    _load("/app/backend/.env")
    if _os.environ.get("APP_ENV", "").strip().lower() != "preview":
        pytest.skip("this invariant only applies in preview environment")
    flag = (_os.environ.get("SCHEDULER_ENABLED") or "").strip().lower()
    assert flag in ("false", "0", "no", "off", ""), (
        f"TRACK 28.09A regression: preview environment must have "
        f"SCHEDULER_ENABLED disabled. Current={flag!r}"
    )


def test_preview_env_prevents_maintainx_write():
    """Preview must NOT be able to write to Motive/MaintainX externals."""
    import os as _os
    from dotenv import load_dotenv as _load
    _load("/app/backend/.env")
    if _os.environ.get("APP_ENV", "").strip().lower() != "preview":
        pytest.skip("preview-only")
    write_flag = (_os.environ.get("MAINTAINX_WRITE_ENABLED") or "").strip().lower()
    sync_flag = (_os.environ.get("MAINTAINX_SYNC_ENABLED") or "").strip().lower()
    assert write_flag in ("false", "0", "no", "off", ""), (
        f"MAINTAINX_WRITE_ENABLED must be false in preview; got {write_flag!r}"
    )
    assert sync_flag in ("false", "0", "no", "off", ""), (
        f"MAINTAINX_SYNC_ENABLED must be false in preview; got {sync_flag!r}"
    )


# ------------------------------------------------------------------
# Phase 5 · R2 delete engine gate
# ------------------------------------------------------------------

def test_r2_delete_engine_reports_disabled():
    src = Path("/app/backend/routes/admin_r2_lifecycle.py").read_text(encoding="utf-8")
    assert '"delete_engine_status": "DISABLED"' in src, (
        "TRACK 28.09A regression: admin_r2_lifecycle.py no longer reports "
        "`delete_engine_status: DISABLED`. Track 27.07 delete engine gate "
        "must remain locked."
    )
