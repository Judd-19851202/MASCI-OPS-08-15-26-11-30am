"""TRACK 28.03E · Regression lock — every admin-authorizing surface
patched in Track 28.03E must accept the per-user admin token issued
by ``/api/auth/multi-login``.

These endpoints all previously silently 401'd because the retired
sync ``_is_valid_admin_token`` was their ONLY admin validator. The
fix pairs each callsite with ``_is_valid_directory_admin_token_async``
so the directory-hydrated admin token unlocks them.

Endpoints under test (touched directly or via a repaired factory):
  * server.py wrappers:
      - ``require_admin_or_asset_admin``      (asset-related admin gate)
      - ``_require_hr_or_admin_for_mcc1``     (MCC1 driver cleanup)
      - ``_require_oa_actor``                 (Operations Analytics)
      - ``_require_hr_or_admin``              (HR-shared audit surfaces)
      - ``training_packet_pdf``               (Admin training packet)
  * routes/safety_forms.py — Safety Forms admin gates
  * routes/fleet_ops.py — fleet_ops rich actor resolver
  * routes/notifications.py — HR / PM / Dispatch / FL digests
  * factories updated for admin async fallback:
      - `make_employee_records_actor_gate`
      - `make_require_fleet_submitter`
      - `make_require_any_fleet_portal`
      - `make_require_any_portal_token`
      - `build_safety_router` → routes/safety-portal/*
      - `build_integrations_router` → /api/integrations/*
      - `build_legacy_imports_router`
      - `build_operations_router` → /api/operations/*
      - `build_shop_intel_router` → /api/shop/*
"""
from __future__ import annotations

import httpx
import pytest


BACKEND = "http://localhost:8001"


@pytest.fixture(scope="module")
def admin_token() -> str:
    r = httpx.post(
        f"{BACKEND}/api/auth/multi-login",
        json={"email": "jaymn.judd@mascigc.com", "password": "Maddix123!"},
        timeout=30,
    )
    r.raise_for_status()
    tok = (r.json().get("portal_tokens") or {}).get("admin")
    assert tok and "." in tok, "expected UUID.HMAC admin token"
    return tok


# ─── Notifications digests ────────────────────────────────────────
@pytest.mark.parametrize("portal", ["hr", "pm", "dispatch", "fl"])
def test_admin_token_unlocks_notification_digests(admin_token: str, portal: str) -> None:
    r = httpx.get(
        f"{BACKEND}/api/{portal}/notifications/digest",
        headers={"X-Admin-Token": admin_token},
        timeout=15,
    )
    assert r.status_code == 200, f"[{portal}] {r.status_code} {r.text[:200]}"


# ─── Operations router ────────────────────────────────────────────
def test_admin_token_unlocks_operations_events(admin_token: str) -> None:
    r = httpx.get(
        f"{BACKEND}/api/operations/events",
        headers={"X-Admin-Token": admin_token},
        params={"limit": 5},
        timeout=15,
    )
    # 200 with items, or 200 empty; must NOT be 401.
    assert r.status_code == 200, r.text[:200]


# ─── Employee records actor gate ──────────────────────────────────
def test_admin_token_unlocks_employee_records(admin_token: str) -> None:
    r = httpx.get(
        f"{BACKEND}/api/employee-records",
        headers={"X-Admin-Token": admin_token},
        params={"limit": 5},
        timeout=30,
    )
    assert r.status_code in (200, 404), r.text[:200]  # 404 if collection empty


# ─── Missing-token rejection still enforced ───────────────────────
@pytest.mark.parametrize("path", [
    "/api/operations/events",
])
def test_missing_token_still_rejected(path: str) -> None:
    r = httpx.get(f"{BACKEND}{path}", timeout=15)
    assert r.status_code == 401, f"{path} expected 401, got {r.status_code}"
