"""TRACK 28.02 · Regression lock for the admin-token read-gate fix.

Guards against re-introducing the P0 regression discovered during
Field Operations certification: the sync `_is_valid_admin_token`
(retired in TRACK 15.32) unconditionally returns False, which meant
that per-user admin tokens issued by `/api/auth/multi-login` were
silently rejected by every Safety/Admin/PM read gate and every
Safety/Admin write gate driven by the `make_require_safety_*`
factories in `routes/safety_portal/_deps.py`.

The fix threads `is_valid_admin_token_async` (delegating to
`_is_valid_directory_admin_token_async`) through every factory
callsite in server.py, and adds a new `is_valid_admin_token_async`
parameter to:

  • make_require_safety_or_admin
  • make_require_safety_or_admin_fleet
  • make_require_safety_admin_or_pm
  • make_require_shop_or_admin_fleet   (shop parity)
  • make_require_dispatch_or_admin     (dispatch parity)

These tests exercise the live wiring by hitting the real endpoints
against the running backend (preview) with an admin token minted by
the canonical `/api/auth/multi-login` path.
"""
from __future__ import annotations

import os
import pytest
import httpx


BACKEND_URL = os.environ.get("REACT_APP_BACKEND_URL") or os.environ.get(
    "PREVIEW_BACKEND_URL",
)
# When run inside the pod the preview URL is reachable but may time out
# from within the container. Prefer the internal supervisor address if
# it responds — falls back to the external URL otherwise.
_INTERNAL_URL = "http://localhost:8001"
try:
    r = httpx.get(f"{_INTERNAL_URL}/api/health", timeout=5)
    if r.status_code == 200:
        BACKEND_URL = _INTERNAL_URL
except Exception:  # noqa: BLE001
    pass
if not BACKEND_URL:
    # Try to fall back to frontend .env
    try:
        with open("/app/frontend/.env", "r", encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("REACT_APP_BACKEND_URL="):
                    BACKEND_URL = line.split("=", 1)[1].strip()
                    break
    except Exception:  # noqa: BLE001
        pass

ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"

READ_ENDPOINTS_UNDER_GATE = [
    "/api/meetings",
    "/api/inspections",
    "/api/incidents",
    "/api/jhas",
]


@pytest.fixture(scope="module")
def admin_token() -> str:
    assert BACKEND_URL, "REACT_APP_BACKEND_URL must be set for this test module"
    r = httpx.post(
        f"{BACKEND_URL}/api/auth/multi-login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=30,
    )
    r.raise_for_status()
    tok = (r.json().get("portal_tokens") or {}).get("admin")
    assert tok, "Multi-login did not return an admin portal token"
    assert "." in tok, "Admin token should be UUID.HMAC form"
    return tok


@pytest.mark.parametrize("endpoint", READ_ENDPOINTS_UNDER_GATE)
def test_admin_token_unlocks_safety_admin_pm_read_gate(admin_token: str, endpoint: str) -> None:
    """The Track 28.02 fix: X-Admin-Token must unlock the
    `make_require_safety_admin_or_pm` read gate. Previously returned
    401 "Safety, Admin, or PM login required" because the sync
    admin-token validator was retired and unconditionally False.
    """
    r = httpx.get(
        f"{BACKEND_URL}{endpoint}",
        headers={"X-Admin-Token": admin_token},
        timeout=30,
    )
    assert r.status_code == 200, f"{endpoint} returned {r.status_code}: {r.text[:200]}"
    payload = r.json()
    assert isinstance(payload, list), f"{endpoint} should return a list, got {type(payload).__name__}"


def test_missing_token_still_rejected(admin_token: str) -> None:
    """Sanity: gate still rejects when no token is provided at all."""
    # admin_token fixture is only listed to ensure module-level auth works.
    del admin_token  # noqa: ERA001
    r = httpx.get(f"{BACKEND_URL}/api/meetings", timeout=30)
    assert r.status_code == 401, f"expected 401, got {r.status_code}"
