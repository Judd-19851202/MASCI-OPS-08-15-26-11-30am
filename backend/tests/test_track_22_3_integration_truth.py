"""TRACK 22.3 · Integration Truth Surface — backend contract tests.

Focused end-to-end verification of the three new admin-only endpoints
that back the /admin/integration-truth UI:

  - GET /api/admin/ai/keys/status
  - GET /api/admin/integrations/truth-status
  - GET /api/admin/dr-v2-alias-telemetry

Requirements (Track 22.3 doctrine):
  1. All three endpoints require the admin (directory) token; 401 without.
  2. AI keys status is read from ``os.environ`` at request time (proves
     the F-01 fix — no dotenv/.env placeholder read).
  3. Raw secret values are NEVER returned — booleans + masked last-4 only.
  4. Integration truth reports config, connectivity, and operational
     states independently and never returns LIVE_VERIFIED from
     configuration alone (F-02 remediation).
  5. Alias telemetry captures every hit to /api/dr-v2/*, exposes both
     detail events and aggregate rows, and enforces a 30-day TTL index
     on the events collection.
"""
from __future__ import annotations

import os
import re
import time

import httpx
import pytest

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8001")
ADMIN_EMAIL = os.environ.get("TEST_SUPER_ADMIN_EMAIL", "jaymn.judd@mascigc.com")
ADMIN_PASS = os.environ.get("TEST_SUPER_ADMIN_PASSWORD", "Maddix123!")


def _admin_token() -> str:
    r = httpx.post(
        f"{BACKEND_URL}/api/auth/multi-login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASS},
        timeout=10.0,
    )
    r.raise_for_status()
    token = (r.json().get("portal_tokens") or {}).get("admin") or ""
    assert token, "admin multi-login did not return an admin portal token"
    return token


@pytest.fixture(scope="module")
def admin_headers() -> dict:
    return {"X-Admin-Token": _admin_token()}


# ─────────────────── 1. Auth gate ─────────────────────────────────

@pytest.mark.parametrize("path", [
    "/api/admin/ai/keys/status",
    "/api/admin/integrations/truth-status",
    "/api/admin/dr-v2-alias-telemetry",
])
def test_endpoints_require_admin(path):
    r = httpx.get(f"{BACKEND_URL}{path}", timeout=10.0)
    assert r.status_code == 401, f"{path} must be admin-gated (got {r.status_code})"


# ─────────────────── 2. AI keys status ────────────────────────────

def test_ai_keys_status_reads_from_environ(admin_headers):
    r = httpx.get(
        f"{BACKEND_URL}/api/admin/ai/keys/status",
        headers=admin_headers,
        timeout=10.0,
    )
    assert r.status_code == 200
    data = r.json()

    # Advertised source must be os.environ — the whole point of F-01 fix.
    assert "os.environ" in (data.get("reads_from") or ""), (
        "AI keys status must explicitly advertise it reads os.environ"
    )

    providers = data.get("providers") or []
    provider_ids = {p["provider"] for p in providers}
    for required in ("emergent_llm", "anthropic", "openai", "gemini"):
        assert required in provider_ids, f"missing provider row: {required}"

    # Emergent LLM key is configured in preview .env; verify runtime pickup.
    emergent = next(p for p in providers if p["provider"] == "emergent_llm")
    assert emergent["key_present"] is True, (
        "EMERGENT_LLM_KEY should be visible at runtime in preview env"
    )
    assert emergent["status"] == "CONFIGURED"


def test_ai_keys_status_never_leaks_raw_secrets(admin_headers):
    r = httpx.get(
        f"{BACKEND_URL}/api/admin/ai/keys/status",
        headers=admin_headers,
        timeout=10.0,
    )
    assert r.status_code == 200
    body = r.text

    # Never return the full universal key.
    full_key = os.environ.get("EMERGENT_LLM_KEY", "")
    if full_key:
        assert full_key not in body, "response must NEVER contain full raw key"

    # last4 masks — allow ellipsis + 4 chars OR **** placeholder only.
    for provider in r.json().get("providers", []):
        last4 = provider.get("key_last4")
        if last4:
            assert re.fullmatch(r"[…\*]{1,4}[A-Za-z0-9]{0,4}", last4), (
                f"masked key '{last4}' does not match last-4 pattern"
            )


# ─────────────────── 3. Integration truth ─────────────────────────

def test_integrations_truth_status_three_state_model(admin_headers):
    r = httpx.get(
        f"{BACKEND_URL}/api/admin/integrations/truth-status",
        headers=admin_headers,
        timeout=15.0,
    )
    assert r.status_code == 200
    data = r.json()

    ids = {row["id"] for row in data.get("integrations") or []}
    for required in ("mongo", "motive", "maintainx", "resend", "emergent_llm"):
        assert required in ids, f"missing integration row: {required}"

    # Every row exposes the three-state model + overall roll-up.
    for row in data["integrations"]:
        for key in (
            "config_status", "connectivity_status",
            "operational_status", "overall",
        ):
            assert key in row, f"{row['id']} missing {key}"

    # F-02 remediation: MaintainX must NEVER appear LIVE_VERIFIED —
    # it is a mocked integration by design.
    mx = next(r for r in data["integrations"] if r["id"] == "maintainx")
    assert mx["overall"] == "MOCKED"
    assert mx["mocked"] is True

    # Overall roll-up must belong to the documented vocabulary.
    allowed = {
        "LIVE_VERIFIED", "CONFIGURED", "PARTIAL", "MISSING_CONFIG",
        "MISSING_SECRET", "UNREACHABLE", "MOCKED", "DISABLED", "ERROR",
    }
    assert data["overall"] in allowed


def test_motive_never_live_verified_from_config_alone(admin_headers):
    """Motive must not report LIVE_VERIFIED unless recent successful
    activity is present. Configuration alone is insufficient.
    """
    r = httpx.get(
        f"{BACKEND_URL}/api/admin/integrations/truth-status",
        headers=admin_headers,
        timeout=15.0,
    )
    row = next(r for r in r.json()["integrations"] if r["id"] == "motive")
    if row["operational_status"] != "LIVE_VERIFIED":
        assert row["overall"] != "LIVE_VERIFIED", (
            "Motive rolled up to LIVE_VERIFIED without recent successful "
            "sync — this is exactly the F-02 lie the truth surface must "
            "prevent."
        )


# ─────────────────── 4. DR-V2 alias telemetry ─────────────────────

def test_dr_v2_alias_telemetry_captures_hits(admin_headers):
    # Fire a couple of legacy alias hits.
    for _ in range(3):
        httpx.get(f"{BACKEND_URL}/api/dr-v2/meta", timeout=5.0)
    time.sleep(0.8)  # background middleware writes are async

    r = httpx.get(
        f"{BACKEND_URL}/api/admin/dr-v2-alias-telemetry",
        headers=admin_headers,
        params={"recent_limit": 10},
        timeout=10.0,
    )
    assert r.status_code == 200
    data = r.json()

    assert data["ttl_days"] == 30
    assert data["route_count"] >= 1
    assert data["lifetime_hits"] >= 3

    meta_row = next(
        (a for a in data["aggregates"] if a["route_key"] == "GET /api/dr-v2/meta"),
        None,
    )
    assert meta_row is not None, "expected an aggregate row for /api/dr-v2/meta"
    assert meta_row["lifetime_hits"] >= 3
    assert meta_row["retirement_recommendation"] in (
        "SAFE_TO_RETIRE", "REVIEW_BEFORE_RETIRE",
    )


def test_dr_v2_alias_events_have_ttl_index():
    """Ensure the detail events collection has the 30-day TTL index.

    Direct Mongo probe — the endpoint doesn't expose the index itself
    but this is the invariant DR-UNIFY-005 depends on.
    """
    from pymongo import MongoClient  # noqa: PLC0415
    client = MongoClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    indexes = list(db["dr_v2_alias_telemetry_events"].list_indexes())
    ttl = next(
        (idx for idx in indexes if idx.get("expireAfterSeconds") is not None),
        None,
    )
    assert ttl is not None, "detail events collection must carry a TTL index"
    assert ttl["expireAfterSeconds"] == 30 * 24 * 60 * 60, (
        f"TTL should be 30 days; got {ttl['expireAfterSeconds']}s"
    )
