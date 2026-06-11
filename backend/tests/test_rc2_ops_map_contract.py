"""RC-2 · TRACK-6 GUARDRAIL — Operations Map Contract.

Tightly-scoped smoke confirming the `/api/operations-map/snapshot`
contract Track 6 certified. Fails fast if the shape regresses.

Auth is fetched via multi-login using the super-admin test account
(test_credentials.md). The snapshot is gated behind portal auth;
expose only what's documented.
"""
from __future__ import annotations

import pytest
import requests
from dotenv import dotenv_values

FRONTEND_ENV = dotenv_values("/app/frontend/.env")
BACKEND_ENV = dotenv_values("/app/backend/.env")
BASE = (FRONTEND_ENV.get("REACT_APP_BACKEND_URL") or "").rstrip("/")

EMAIL = "jaymn.judd@mascigc.com"
PASSWORD = "Maddix123!"

BANNED_VOCAB = [
    "TODO", "FIXME", "lorem ipsum", "placeholder",
    "test data", "sample data", "DEMO ONLY",
]


@pytest.fixture(scope="module")
def admin_token() -> str:
    r = requests.post(
        f"{BASE}/api/auth/multi-login",
        json={"email": EMAIL, "password": PASSWORD},
        timeout=60,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    token = (data.get("portal_tokens") or {}).get("admin")
    assert token, f"No admin token in response: {data}"
    return token


def test_rc2_operations_map_snapshot_contract(admin_token: str):
    r = requests.get(
        f"{BASE}/api/operations-map/snapshot",
        headers={"X-Admin-Token": admin_token},
        timeout=45,
    )
    assert r.status_code == 200, r.text
    snap = r.json()

    # Top-level required keys.
    for key in ("operational_summary", "attention_breakdown",
                "project_rollups", "feed_status"):
        assert key in snap, f"Missing top-level key: {key}"

    op = snap["operational_summary"]
    # Required tiles + first tile is attention.
    assert isinstance(op, list) and op, "operational_summary must be a non-empty list"
    first_id = op[0].get("id") or op[0].get("kind")
    assert first_id == "attention", (
        f"First operational_summary tile must be 'attention', got id={first_id!r}: {op[0]}"
    )

    # attention_breakdown shape.
    ab = snap["attention_breakdown"]
    assert isinstance(ab, list), "attention_breakdown must be a list"
    if ab:
        sample = ab[0]
        assert "owner" in sample, f"attention_breakdown row missing owner: {sample}"

    # project_rollups shape.
    rollups = snap["project_rollups"]
    assert isinstance(rollups, list), "project_rollups must be a list"
    if rollups:
        sample = rollups[0]
        for key in ("dominant_reason", "dominant_owner", "next_action"):
            assert key in sample, f"project_rollup missing {key}: {sample}"

    # feed_status sanity.
    fs = snap["feed_status"]
    assert isinstance(fs, dict) and fs, "feed_status must be a non-empty dict"

    # Mathematical consistency on operational_summary counts.
    counts = {
        (tile.get("id") or tile.get("kind")): int(tile.get("value") or tile.get("count") or 0)
        for tile in op
    }
    if "total" in counts:
        component_sum = sum(
            counts.get(k, 0) for k in ("attention", "offline", "working", "idle")
            if k in counts
        )
        # Allow `total` ≥ component_sum (rollup category extras), but never less.
        assert counts["total"] >= component_sum, (
            f"operational_summary total={counts['total']} less than components sum={component_sum}"
        )


def test_rc2_operations_map_vocab_clean(admin_token: str):
    r = requests.get(
        f"{BASE}/api/operations-map/snapshot",
        headers={"X-Admin-Token": admin_token},
        timeout=45,
    )
    assert r.status_code == 200, r.text
    blob = r.text.lower()
    leaks = [w for w in BANNED_VOCAB if w.lower() in blob]
    assert not leaks, f"Operations-map snapshot leaks banned vocab: {leaks}"
