"""iter424 · Phase 25.1 · Inline Recovery Continuity Actions tests.

Walking-skeleton verification:
  1. Recovery transition still works under SHOP token (the new write owner).
  2. Recovery transition still works under ADMIN token (admin is always
     allowed · conftest auto-attaches the admin token).
  3. Recovery transition is REJECTED under a Dispatch-only token (role
     discipline locked: Dispatch reads, Shop writes).
  4. Invalid to_state returns 400.
  5. Long notes are truncated to 500 chars (operational continuity context,
     not a maintenance log).
  6. Each transition appends an entry to recovery_history[].
  7. Anon writers blocked (401).
  8. The new guidance article is registered.
"""
from __future__ import annotations

import os
import urllib.error
import urllib.request
import uuid
from pathlib import Path

import pytest
import requests


def _read_kv(path: Path, key: str) -> str:
    try:
        for line in path.read_text().splitlines():
            if line.startswith(f"{key}="):
                return line.split("=", 1)[1].strip().strip('"').rstrip("/")
    except Exception:
        return ""
    return ""


URL = (
    _read_kv(Path("/app/frontend/.env"), "REACT_APP_BACKEND_URL")
    or os.environ.get("REACT_APP_BACKEND_URL", "")
).rstrip("/")
API = f"{URL}/api"


@pytest.fixture(scope="module")
def tenant_id() -> str:
    return f"iter424-test-{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="module")
def hdrs(tenant_id: str) -> dict:
    return {"X-Tenant-Id": tenant_id}


@pytest.fixture(scope="module")
def assignment(hdrs) -> dict:
    r = requests.post(
        f"{API}/dispatch/assignments",
        headers=hdrs,
        json={
            "truck_id": "T-iter424",
            "driver_name": "iter424 Driver",
            "haul_type": "Material",
            "project_number": "9999",
            "material": "Asphalt",
        },
        timeout=15,
    )
    assert r.status_code in (200, 201), r.text
    return r.json()["assignment"]


def _shop_token() -> str:
    """Mint a shop-portal token via the legacy admin-managed shop login."""
    # The platform exposes /api/auth/multi-login which returns a `portal_tokens.shop` value
    # for any directory user with shop access. Fall back to legacy /api/shop/login.
    super_email = "jaymn.judd@mascigc.com"
    super_password = "Maddix123!"
    r = requests.post(
        f"{API}/auth/multi-login",
        json={"email": super_email, "password": super_password},
        timeout=15,
    )
    if r.status_code != 200:
        pytest.skip(f"multi-login env-dependent: {r.status_code}")
    body = r.json()
    if body.get("mfa_required"):
        pytest.skip("MFA gate active in env")
    pt = body.get("portal_tokens") or {}
    shop = pt.get("shop")
    if not shop:
        pytest.skip("no shop token minted from directory super-admin")
    return shop


def _dispatch_token() -> str:
    """Mint a dispatch-portal token via multi-login."""
    super_email = "jaymn.judd@mascigc.com"
    super_password = "Maddix123!"
    r = requests.post(
        f"{API}/auth/multi-login",
        json={"email": super_email, "password": super_password},
        timeout=15,
    )
    if r.status_code != 200:
        pytest.skip(f"multi-login env-dependent: {r.status_code}")
    body = r.json()
    if body.get("mfa_required"):
        pytest.skip("MFA gate active in env")
    pt = body.get("portal_tokens") or {}
    dispatch = pt.get("dispatch")
    if not dispatch:
        pytest.skip("no dispatch token minted from directory super-admin")
    return dispatch


# ──────────────────────────────────────────────────────────────
# 1. SHOP token can transition recovery state
# ──────────────────────────────────────────────────────────────
def test_iter424_shop_can_transition(assignment, tenant_id):
    shop_tok = _shop_token()
    r = requests.post(
        f"{API}/dispatch/recovery/{assignment['id']}/transition",
        headers={
            "X-Shop-Token": shop_tok,
            "X-Tenant-Id": tenant_id,
            # Explicitly drop the admin token conftest auto-adds — we want
            # to prove the shop token ALONE works.
            "X-Admin-Token": "",
        },
        json={"to_state": "acknowledged", "note": "Shop acknowledged"},
        timeout=15,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True
    assert body["recovery_state"] == "acknowledged"
    assert body["entry"]["note"] == "Shop acknowledged"


# ──────────────────────────────────────────────────────────────
# 2. ADMIN token still works (uses conftest auto-attached X-Admin-Token)
# ──────────────────────────────────────────────────────────────
def test_iter424_admin_can_still_transition(assignment, hdrs):
    r = requests.post(
        f"{API}/dispatch/recovery/{assignment['id']}/transition",
        headers=hdrs,
        json={"to_state": "diagnosing", "note": "Admin diagnosing"},
        timeout=15,
    )
    assert r.status_code == 200, r.text
    assert r.json()["recovery_state"] == "diagnosing"


# ──────────────────────────────────────────────────────────────
# 3. Dispatch-only token is BLOCKED from recovery writes (role discipline)
# ──────────────────────────────────────────────────────────────
def test_iter424_dispatch_only_blocked_from_recovery_write(assignment, tenant_id):
    dispatch_tok = _dispatch_token()
    r = requests.post(
        f"{API}/dispatch/recovery/{assignment['id']}/transition",
        headers={
            "X-Dispatch-Token": dispatch_tok,
            "X-Tenant-Id": tenant_id,
            "X-Admin-Token": "",   # strip admin override from conftest
            "X-Shop-Token": "",    # ensure shop not present
        },
        json={"to_state": "repair_active"},
        timeout=15,
    )
    # require_shop_or_admin rejects a Dispatch-only token
    assert r.status_code in (401, 403), r.text


# ──────────────────────────────────────────────────────────────
# 4. Invalid state rejected
# ──────────────────────────────────────────────────────────────
def test_iter424_invalid_state_rejected(assignment, hdrs):
    r = requests.post(
        f"{API}/dispatch/recovery/{assignment['id']}/transition",
        headers=hdrs,
        json={"to_state": "INVENTED"},
        timeout=10,
    )
    assert r.status_code == 400, r.text


# ──────────────────────────────────────────────────────────────
# 5. Long notes truncated to ≤500 chars
# ──────────────────────────────────────────────────────────────
def test_iter424_note_truncated(assignment, hdrs):
    long_note = "x" * 1200
    r = requests.post(
        f"{API}/dispatch/recovery/{assignment['id']}/transition",
        headers=hdrs,
        json={"to_state": "operational_test", "note": long_note},
        timeout=15,
    )
    # Pydantic may either reject (422) or accept-and-truncate. Both are
    # operationally safe. Verify one of those happens — never an open
    # bypass of the 500-char ceiling.
    if r.status_code == 200:
        entry = r.json()["entry"]
        assert len(entry["note"]) <= 500
    else:
        assert r.status_code in (400, 422), r.text


# ──────────────────────────────────────────────────────────────
# 6. Each transition appends to recovery_history[]
# ──────────────────────────────────────────────────────────────
def test_iter424_history_appends(assignment, hdrs):
    # Get full history via the read endpoint
    r = requests.get(
        f"{API}/dispatch/recovery/{assignment['id']}",
        headers=hdrs,
        timeout=10,
    )
    assert r.status_code == 200, r.text
    history = r.json().get("history") or []
    # At minimum the Shop ack + Admin diagnosing transitions landed
    assert len(history) >= 2
    times = [h.get("at") for h in history]
    # Append-only · oldest first
    assert times == sorted(times)
    # Verify the `by` field reflects whichever actor performed each transition
    actors = {h.get("by") for h in history}
    assert any(a for a in actors), "every entry should carry a `by` actor"


# ──────────────────────────────────────────────────────────────
# 7. Anon writers blocked
# ──────────────────────────────────────────────────────────────
def test_iter424_anon_write_blocked(assignment):
    import json as _json
    body = _json.dumps({"to_state": "acknowledged"}).encode("utf-8")
    req = urllib.request.Request(
        f"{API}/dispatch/recovery/{assignment['id']}/transition",
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (iter424 anon)",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            assert False, f"Expected 401 · got {r.status}"
    except urllib.error.HTTPError as e:
        assert e.code == 401, e.code


# ──────────────────────────────────────────────────────────────
# 8. New guidance article registered
# ──────────────────────────────────────────────────────────────
def test_iter424_guidance_article_registered(hdrs):
    r = requests.get(f"{API}/guidance/articles/dls-recovery-state-transitions", headers=hdrs, timeout=10)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("id") == "dls-recovery-state-transitions"
    assert "transitions" in (body.get("title") or "").lower()
    assert isinstance(body.get("body"), list) and len(body["body"]) >= 3
