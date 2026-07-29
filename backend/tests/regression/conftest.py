"""
MASCI Operational Certification — regression harness conftest.

Reads:
  - REACT_APP_BACKEND_URL  from /app/frontend/.env (the live preview pod URL)
  - SUPER_ADMIN_EMAIL / SUPER_ADMIN_BOOTSTRAP_PASSWORD from /app/backend/.env

Provides a session-scoped `tokens` fixture that performs a single
`POST /api/auth/multi-login` and exposes every per-portal token, plus a
session-scoped `base_url` fixture so tests don't hardcode hosts.

The fixture also fails fast if the live `/api/version` endpoint reports
this pod is NOT pointed at a `*_preview` database — guaranteeing the
regression suite can never accidentally hit production data.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
import requests
import requests.api
import requests.sessions
from dotenv import dotenv_values

# ---------------------------------------------------------------------------
# The parent /app/backend/tests/conftest.py auto-attaches X-Admin-Token to
# every requests call (legacy convenience). That subverts our cross-portal
# isolation and no-auth-401 tests. Restore the original requests behaviour
# by reaching into the parent module and pulling the unpatched callables it
# stashed at import time.
# ---------------------------------------------------------------------------
try:
    import sys as _sys
    _parent = _sys.modules.get("conftest")  # parent tests/conftest.py
    if _parent is not None and hasattr(_parent, "_orig_request"):
        requests.api.request = _parent._orig_request
    if _parent is not None and hasattr(_parent, "_orig_session_request"):
        requests.sessions.Session.request = _parent._orig_session_request
except Exception:  # pragma: no cover — best-effort unpatch
    pass

# Load the two relevant env files explicitly so the test harness is
# self-contained (no reliance on the pytest invocation environment).
FRONTEND_ENV = dotenv_values("/app/frontend/.env")
BACKEND_ENV = dotenv_values("/app/backend/.env")


def _strip(val: str | None) -> str:
    if val is None:
        return ""
    return val.strip().strip('"').strip("'")


@pytest.fixture(scope="session")
def base_url() -> str:
    url = _strip(FRONTEND_ENV.get("REACT_APP_BACKEND_URL"))
    if not url:
        pytest.exit("REACT_APP_BACKEND_URL missing from /app/frontend/.env", returncode=2)
    return url.rstrip("/")


@pytest.fixture(scope="session")
def super_admin_creds() -> dict:
    email = _strip(BACKEND_ENV.get("SUPER_ADMIN_EMAIL"))
    pw = _strip(BACKEND_ENV.get("SUPER_ADMIN_BOOTSTRAP_PASSWORD"))
    if not email or not pw:
        pytest.exit(
            "SUPER_ADMIN_EMAIL / SUPER_ADMIN_BOOTSTRAP_PASSWORD missing from /app/backend/.env",
            returncode=2,
        )
    return {"email": email, "password": pw}


@pytest.fixture(scope="session")
def env_identity(base_url: str) -> dict:
    """Fail fast if the live pod is not pointed at a `*_preview` DB.

    This is the load-bearing guardrail: it guarantees the regression
    suite can never write to or read from production data.
    """
    r = requests.get(f"{base_url}/api/version", timeout=10)
    r.raise_for_status()
    payload = r.json()
    app_env = (payload.get("app_env") or "").lower()
    db_name = payload.get("db_name") or ""
    if app_env != "preview" or not db_name.endswith("_preview"):
        pytest.exit(
            f"REFUSING TO RUN: live pod reports app_env={app_env!r} db={db_name!r}. "
            "Regression suite only runs against a `*_preview` database.",
            returncode=3,
        )
    return payload


@pytest.fixture(scope="session")
def tokens(base_url: str, super_admin_creds: dict, env_identity: dict) -> dict:
    """One multi-login per session. Returns the full payload."""
    r = requests.post(
        f"{base_url}/api/auth/multi-login",
        json=super_admin_creds,
        timeout=15,
    )
    if r.status_code != 200:
        pytest.exit(
            f"Super-admin multi-login failed: HTTP {r.status_code} body={r.text[:200]}",
            returncode=4,
        )
    data = r.json()
    if not data.get("ok") or not data.get("portal_tokens"):
        pytest.exit(
            f"Multi-login response malformed: keys={list(data.keys())}",
            returncode=4,
        )
    return data


@pytest.fixture(scope="session")
def admin_headers(tokens: dict) -> dict:
    headers = {"X-Admin-Token": tokens["portal_tokens"]["admin"]}
    if tokens.get("session_token"):
        headers["X-Directory-Token"] = tokens["session_token"]
    return headers


@pytest.fixture(scope="session")
def hr_headers(tokens: dict) -> dict:
    return {"X-HR-Token": tokens["portal_tokens"]["hr"]}


@pytest.fixture(scope="session")
def pm_headers(tokens: dict) -> dict:
    return {"X-PM-Token": tokens["portal_tokens"]["pm"]}


@pytest.fixture(scope="session")
def shop_headers(tokens: dict) -> dict:
    return {"X-Shop-Token": tokens["portal_tokens"]["shop"]}


@pytest.fixture(scope="session")
def safety_headers(tokens: dict) -> dict:
    return {"X-Safety-Token": tokens["portal_tokens"]["safety"]}


@pytest.fixture(scope="session")
def dispatch_headers(tokens: dict) -> dict:
    return {"X-Dispatch-Token": tokens["portal_tokens"]["dispatch"]}


@pytest.fixture(scope="session")
def fl_headers(tokens: dict) -> dict:
    return {"X-FL-Token": tokens["portal_tokens"]["field_leadership"]}
