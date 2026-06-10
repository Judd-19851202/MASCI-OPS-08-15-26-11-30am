"""Pytest conftest — auto-attaches the admin token to every requests call.

The MASCI Safety Hub gates GET / DELETE on inspections, meetings, jhas,
incidents, and daily-reports behind a shared admin password (sent via the
X-Admin-Token header). Tests POST publicly (forms are filed by field crews
without auth) but read/delete back through the admin interface, so we want
every requests.{get,post,delete,...} call from inside /app/backend/tests to
include the admin header automatically.

Implementation: at session import time we POST /api/admin/login once to get
a token, then monkey-patch requests.api.request to add the X-Admin-Token
header on any call hitting our backend URL.
"""
import os
from pathlib import Path

import requests
import requests.api  # noqa: F401  (force the module import we patch)


def _read_kv(path, key):
    try:
        with open(path) as f:
            for line in f:
                if line.startswith(f"{key}="):
                    return line.split("=", 1)[1].strip().strip('"').rstrip("/")
    except Exception:
        pass
    return ""


_FRONTEND_ENV = Path("/app/frontend/.env")
_BACKEND_ENV = Path("/app/backend/.env")

URL = (
    _read_kv(_FRONTEND_ENV, "REACT_APP_BACKEND_URL")
    or os.environ.get("REACT_APP_BACKEND_URL", "")
).rstrip("/")

PASSWORD = _read_kv(_BACKEND_ENV, "ADMIN_PASSWORD") or os.environ.get(
    "ADMIN_PASSWORD", ""
)

ADMIN_TOKEN = ""
if URL and PASSWORD:
    try:
        r = requests.post(
            f"{URL}/api/admin/login",
            json={"password": PASSWORD},
            timeout=10,
        )
        if r.status_code == 200:
            ADMIN_TOKEN = r.json().get("token", "")
    except Exception:
        ADMIN_TOKEN = ""


_orig_request = requests.api.request
_orig_session_request = requests.sessions.Session.request


def _patched_request(method, url, **kwargs):
    """Attach X-Admin-Token to any call that hits our backend host."""
    if ADMIN_TOKEN and isinstance(url, str) and URL and url.startswith(URL):
        headers = kwargs.get("headers") or {}
        headers.setdefault("X-Admin-Token", ADMIN_TOKEN)
        kwargs["headers"] = headers
    # DEPLOY-GATE-FIX-002 (2026-06-10): the preview ingress (Cloudflare
    # → k8s) routinely spikes past 10s when the full pw_suite is in
    # flight. Raise tiny per-call timeouts to a 30s floor for our backend
    # host only. We never reduce an explicit larger timeout — only lift
    # small ones. This is a test-harness fix; no product code path
    # observes any change.
    if isinstance(url, str) and URL and url.startswith(URL):
        t = kwargs.get("timeout")
        if t is None or (isinstance(t, (int, float)) and t < 30):
            kwargs["timeout"] = 30
    return _orig_request(method, url, **kwargs)


def _patched_session_request(self, method, url, **kwargs):
    """Same patch but for Session().get / Session().post / etc."""
    if ADMIN_TOKEN and isinstance(url, str) and URL and url.startswith(URL):
        headers = kwargs.get("headers") or {}
        # Don't clobber a header the test explicitly set
        headers.setdefault("X-Admin-Token", ADMIN_TOKEN)
        kwargs["headers"] = headers
    if isinstance(url, str) and URL and url.startswith(URL):
        t = kwargs.get("timeout")
        if t is None or (isinstance(t, (int, float)) and t < 30):
            kwargs["timeout"] = 30
    return _orig_session_request(self, method, url, **kwargs)


# Only patch once — guard against pytest re-importing conftest in some setups.
if not getattr(requests.api.request, "_masci_patched", False):
    _patched_request._masci_patched = True
    requests.api.request = _patched_request

if not getattr(requests.sessions.Session.request, "_masci_patched", False):
    _patched_session_request._masci_patched = True
    requests.sessions.Session.request = _patched_session_request
