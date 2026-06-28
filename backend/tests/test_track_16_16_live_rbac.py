"""TRACK 16.16 · Live RBAC + envelope + performance test against the running backend.

Drives the public REACT_APP_BACKEND_URL endpoint to verify:
  - 401 unauthenticated
  - 200 with X-Admin-Token, X-PM-Token, X-Dispatch-Token (cross-portal)
  - Full envelope keys
  - Response time < 3s
"""
from __future__ import annotations
import os
import time
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    # Read from frontend .env directly as fallback (test infra context).
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip().rstrip("/")
                break

ENDPOINT = f"{BASE_URL}/api/operations/transportation/readiness"
LOGIN = f"{BASE_URL}/api/auth/multi-login"

REQUIRED_KEYS = {
    "ok", "schema_version", "generated_at",
    "overall_readiness", "driver_band", "truck_band", "carrier_band",
    "dispatch_readiness", "capacity", "snapshot", "cleanup",
    "hr_sync", "risks", "links", "note",
}
REQUIRED_SNAPSHOT_KEYS = {
    "available_drivers", "available_trucks", "available_carriers",
    "pending_reviews", "documents_awaiting_review",
    "upcoming_expirations_30d", "blocked_dispatches", "open_action_items",
}
REQUIRED_LINK_KEYS = {
    "transportation_dashboard", "cleanup_companion", "intelligence",
}


@pytest.fixture(scope="module")
def tokens():
    r = requests.post(LOGIN, json={
        "email": "jaymn.judd@mascigc.com",
        "password": "Maddix123!",
    }, timeout=30)
    assert r.status_code == 200, f"multi-login failed: {r.status_code} {r.text[:300]}"
    data = r.json()
    pt = data.get("portal_tokens") or {}
    assert pt.get("admin") and pt.get("pm") and pt.get("dispatch"), \
        f"portal_tokens missing: {list(pt.keys())}"
    return pt


def test_01_unauthenticated_returns_401():
    # Retry once for ingress cold-start jitter.
    last = None
    for _ in range(2):
        try:
            last = requests.get(ENDPOINT, timeout=30)
            break
        except requests.exceptions.ReadTimeout:
            time.sleep(2)
    assert last is not None and last.status_code == 401, \
        f"expected 401, got {last.status_code if last else 'TIMEOUT'}"


def test_02_admin_token_200_and_envelope(tokens):
    t0 = time.time()
    r = requests.get(ENDPOINT, headers={"X-Admin-Token": tokens["admin"]},
                     timeout=10)
    dur = time.time() - t0
    assert r.status_code == 200, f"admin 200 expected, got {r.status_code}: {r.text[:300]}"
    assert dur < 3.0, f"endpoint too slow: {dur:.2f}s"
    body = r.json()
    missing = REQUIRED_KEYS - set(body.keys())
    assert not missing, f"missing envelope keys: {missing}"
    assert body["ok"] is True
    assert body["schema_version"] == "16.16.0"
    snap = body["snapshot"]
    miss_snap = REQUIRED_SNAPSHOT_KEYS - set(snap.keys())
    assert not miss_snap, f"missing snapshot keys: {miss_snap}"
    links = body["links"]
    miss_links = REQUIRED_LINK_KEYS - set(links.keys())
    assert not miss_links, f"missing link keys: {miss_links}"
    # band labels for top-level bands
    for b in ("overall_readiness", "driver_band", "truck_band", "carrier_band"):
        assert "label" in body[b] and "score" in body[b], f"{b} malformed"
    assert isinstance(body["risks"], list)
    print(f"\nLatency={dur*1000:.0f}ms  "
          f"overall={body['overall_readiness']}  "
          f"blocked_dispatches={snap['blocked_dispatches']}  "
          f"open_action_items={snap['open_action_items']}  "
          f"risks={len(body['risks'])}")


def test_03_pm_token_200(tokens):
    r = requests.get(ENDPOINT, headers={"X-PM-Token": tokens["pm"]}, timeout=10)
    assert r.status_code == 200, f"pm 200 expected, got {r.status_code}: {r.text[:300]}"
    assert r.json()["schema_version"] == "16.16.0"


def test_04_dispatch_token_200(tokens):
    r = requests.get(ENDPOINT, headers={"X-Dispatch-Token": tokens["dispatch"]},
                     timeout=10)
    assert r.status_code == 200, f"dispatch 200 expected, got {r.status_code}: {r.text[:300]}"
    assert r.json()["schema_version"] == "16.16.0"


def test_05_cross_portal_consistency(tokens):
    """All three portal reads must return identical envelope shape."""
    bodies = []
    for header, val in (
        ("X-Admin-Token", tokens["admin"]),
        ("X-PM-Token", tokens["pm"]),
        ("X-Dispatch-Token", tokens["dispatch"]),
    ):
        r = requests.get(ENDPOINT, headers={header: val}, timeout=10)
        assert r.status_code == 200
        bodies.append(r.json())
    # Compare key sets and snapshot keys
    key_sets = [set(b.keys()) for b in bodies]
    assert key_sets[0] == key_sets[1] == key_sets[2], \
        f"key sets differ: {key_sets}"
    snap_sets = [set(b["snapshot"].keys()) for b in bodies]
    assert snap_sets[0] == snap_sets[1] == snap_sets[2]


def test_06_no_writes_in_route_file():
    src = open("/app/backend/routes/operations_transportation_integration.py").read()
    for needle in (".insert_one(", ".update_one(", ".delete_one(",
                   ".replace_one(", ".find_one_and_update(",
                   ".insert_many(", ".update_many(", ".delete_many("):
        assert needle not in src, f"Track 16.16 must be read-only — found {needle}"


def test_07_risk_banner_returns_null_when_no_risks():
    src = open("/app/frontend/src/components/operations_transportation_integration.jsx").read()
    idx = src.find("function TransportationRiskBanner(")
    assert idx >= 0
    block = src[idx: idx + 1500]
    import re
    assert re.search(r"risks\.length\s*===\s*0[\s\S]{0,250}return\s+null", block), \
        "TransportationRiskBanner must return null when no risks (no warning fatigue)"
