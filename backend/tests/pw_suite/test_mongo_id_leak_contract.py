"""TRUST-1 · Wave 1 · TF-015 · 2026-05-27.

`_id` leak contract test for admin + PM read-only namespaces.

Doctrine
--------
MongoDB ObjectId is not JSON-serialisable for the frontend and a leaked
`_id` indicates the route is forgetting the standard `{"_id": 0}`
projection. iter442 already covered `/api/draft-telemetry/recent`; this
test extends that contract to a representative sample of the wider
admin and PM read namespaces so that a future drift regression
surfaces at deploy time instead of in the field.

Method
------
Acquire an admin token, then hit a list of safe, read-only,
side-effect-free GET endpoints. For each, assert:
  * HTTP 200
  * Response is valid JSON
  * The raw body text does NOT contain the substring `"_id":`

Skipped on 4xx (route renamed / behind a permission). NEVER call write
endpoints; this is a contract-only probe.
"""
from __future__ import annotations

import json
from typing import List

import pytest
import requests
from dotenv import dotenv_values

BACKEND_ENV = dotenv_values("/app/backend/.env")


def _strip(v: str | None) -> str:
    return (v or "").strip().strip('"').strip("'")


def _admin_token(base_url: str) -> str:
    pw = _strip(BACKEND_ENV.get("ADMIN_PASSWORD"))
    assert pw, "ADMIN_PASSWORD missing from backend/.env"
    r = requests.post(
        f"{base_url}/api/admin/login",
        json={"password": pw},
        timeout=10,
    )
    r.raise_for_status()
    tok = r.json().get("token")
    assert tok, f"login response missing token: {r.text}"
    return tok


# Representative sample of read-only, idempotent admin/PM endpoints.
# Each MUST be a safe GET that returns JSON. Keep the list small —
# this is a contract probe, not a coverage sweep.
SAMPLED_ENDPOINTS: List[str] = [
    "/api/admin/analytics/summary",
    "/api/admin/analytics/routes",
    "/api/admin/analytics/portals",
    "/api/admin/analytics/health",
    "/api/admin/governance/summary",
    "/api/admin/operational-inventory",
    "/api/admin/operational-inventory/portals",
    "/api/admin/notifications/digest",
    "/api/draft-telemetry/recent?limit=5",
    "/api/draft-telemetry/health",
]


@pytest.mark.parametrize("path", SAMPLED_ENDPOINTS)
def test_no_mongo_id_leak(base_url: str, path: str):
    tok = _admin_token(base_url)
    r = requests.get(
        f"{base_url}{path}",
        headers={"X-Admin-Token": tok},
        timeout=15,
    )
    if r.status_code in (400, 401, 403, 404):
        pytest.skip(f"{path} unavailable (status {r.status_code}); skipping leak contract")
    assert r.status_code == 200, (
        f"{path} returned {r.status_code} · body={r.text[:200]!r}"
    )
    # Parse to confirm valid JSON contract.
    try:
        body = r.json()
    except json.JSONDecodeError as e:
        pytest.fail(f"{path} returned non-JSON body: {e}")
    # Stringify and search for the leak signature. Strict on the
    # ObjectId-style key shape.
    raw = json.dumps(body)
    assert '"_id":' not in raw, (
        f"{path} leaks MongoDB _id field. "
        f"Add a `{{'_id': 0}}` projection to the find() call. "
        f"snippet={raw[:300]!r}"
    )
    # Belt-and-braces: top-level array OR {items:[...]} should not
    # have any item with an `_id` key.
    items = []
    if isinstance(body, list):
        items = body
    elif isinstance(body, dict) and isinstance(body.get("items"), list):
        items = body["items"]
    for it in items[:20]:
        if isinstance(it, dict):
            assert "_id" not in it, (
                f"{path} item has _id key: {list(it.keys())[:10]}"
            )
