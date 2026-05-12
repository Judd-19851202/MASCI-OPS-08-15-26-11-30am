"""
iter69 — Regression test for the shop-portal "View does nothing" bug.

Root cause: per-shop-user accounts (mechanic / shop-manager / parts-
coordinator) flowed through ``compute_pm_scope``. Their email did not
match any PM-assigned job in ``jobs_master``, so the helper returned an
empty PM scope and every project-scoped detail endpoint blanket-404'd.

This test locks the fix in place so a future refactor of
``compute_pm_scope`` or ``require_shop_or_admin`` cannot reintroduce
the bug silently. The shop manager's flow is:

    Shop login (email + password)
       └── GET /api/equipment-inspections → 200 (list)
       └── click View on a row
            └── GET /api/equipment-inspections/{id} → MUST return 200

Plus the two other shop-accessible scope-bearing endpoints that were
silently broken by the same bug class:

    GET /api/admin/equipment-inspections/trends?days=90  → MUST 200
    GET /api/admin/equipment-inspections/open-items     → MUST 200
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
import requests

# Read REACT_APP_BACKEND_URL directly. The pytest conftest also reads
# this — we duplicate the logic here so the test runs even when the
# conftest path resolution shifts.
def _read_kv(path, key):
    try:
        with open(path) as f:
            for line in f:
                if line.startswith(f"{key}="):
                    return line.split("=", 1)[1].strip().strip('"').rstrip("/")
    except Exception:
        pass
    return ""


URL = (
    _read_kv("/app/frontend/.env", "REACT_APP_BACKEND_URL")
    or os.environ.get("REACT_APP_BACKEND_URL", "")
).rstrip("/")

SHOP_TEST_EMAIL = "testmech@mascigc.com"
SHOP_TEST_PASSWORD = "ResetWorks2026!"


@pytest.fixture(scope="module")
def shop_token() -> str:
    """Authenticate a real per-shop-user account and return the token."""
    if not URL:
        pytest.skip("REACT_APP_BACKEND_URL not configured")
    r = requests.post(
        f"{URL}/api/shop/login",
        json={"email": SHOP_TEST_EMAIL, "password": SHOP_TEST_PASSWORD},
        timeout=15,
    )
    assert r.status_code == 200, f"shop login failed: {r.status_code} {r.text}"
    token = r.json().get("token")
    assert token and "." in token, f"per-user token expected (with '.'), got: {token!r}"
    return token


@pytest.fixture(scope="module")
def shop_headers(shop_token: str) -> dict:
    # IMPORTANT: do NOT include X-Admin-Token. We want to test the
    # shop-only auth path. The conftest patches `requests.api.request`,
    # so we have to bypass it by using a fresh Session.
    return {"X-Shop-Token": shop_token}


def _shop_get(url: str, headers: dict) -> requests.Response:
    """Hit the API with ONLY the shop token. Uses a fresh Session so
    the conftest's auto-injected X-Admin-Token does not piggyback and
    accidentally make the request succeed via admin auth."""
    s = requests.Session()
    # Strip any defaults the conftest may have set.
    s.headers.clear()
    s.headers.update({"Accept": "application/json"})
    return s.get(url, headers=headers, timeout=15)


class TestShopUserCanReadInspections:
    """Per-shop-user must be able to load list + detail without 404."""

    def test_list_inspections_returns_200(self, shop_headers):
        r = _shop_get(f"{URL}/api/equipment-inspections?limit=5", shop_headers)
        assert r.status_code == 200, f"list 200 expected, got {r.status_code}: {r.text[:200]}"
        items = r.json()
        assert isinstance(items, list), f"list expected, got {type(items).__name__}"

    def test_inspection_detail_returns_200_not_404(self, shop_headers):
        """The exact bug the shop manager hit. Pull the first inspection
        from the list, fetch its detail, expect 200. Before iter69 this
        returned 404 because compute_pm_scope treated the shop user as
        a zero-job PM."""
        # Fetch list first to find a real id.
        lst = _shop_get(f"{URL}/api/equipment-inspections?limit=1", shop_headers)
        assert lst.status_code == 200, f"list 200 expected, got {lst.status_code}"
        items = lst.json()
        if not items:
            pytest.skip("No equipment inspections in this environment")
        inspection_id = items[0]["id"]

        r = _shop_get(f"{URL}/api/equipment-inspections/{inspection_id}", shop_headers)
        assert r.status_code == 200, (
            f"REGRESSION: per-shop-user got {r.status_code} on detail "
            f"endpoint. Bug: compute_pm_scope is not honoring the "
            f"_actor_kind='shop_user' tag from require_shop_or_admin. "
            f"Body: {r.text[:300]}"
        )
        doc = r.json()
        assert doc.get("id") == inspection_id, f"wrong doc returned: {doc!r}"

    def test_trends_endpoint_returns_200_with_data(self, shop_headers):
        """Same bug class — shop users could not read the trends
        leaderboard because compute_pm_scope produced an impossible
        Mongo filter."""
        r = _shop_get(
            f"{URL}/api/admin/equipment-inspections/trends?days=90",
            shop_headers,
        )
        assert r.status_code == 200, f"trends 200 expected, got {r.status_code}: {r.text[:200]}"
        data = r.json()
        # The shape doesn't matter — just that the endpoint resolved.
        assert "equipment" in data or "totals" in data, f"unexpected shape: {list(data.keys())}"

    def test_open_items_endpoint_returns_200(self, shop_headers):
        """Same bug class — open shop items list was silently empty
        for per-shop-user accounts before iter69."""
        r = _shop_get(
            f"{URL}/api/admin/equipment-inspections/open-items?severity=all",
            shop_headers,
        )
        assert r.status_code == 200, f"open-items 200 expected, got {r.status_code}: {r.text[:200]}"
        data = r.json()
        assert "items" in data, f"open-items missing 'items' key: {data!r}"


class TestActorKindTagging:
    """Pin the contract: require_shop_or_admin MUST tag per-shop-user
    actors so compute_pm_scope can short-circuit. If someone removes
    the tag in a refactor, this test fires immediately."""

    def test_compute_pm_scope_admin_actor(self):
        """admin / legacy bypass → is_admin True (unrestricted)."""
        import asyncio
        sys.path.insert(0, "/app/backend")
        from pm_auth import compute_pm_scope  # noqa: WPS433
        # `True` is what require_admin returns for the admin password.
        scope = asyncio.run(compute_pm_scope(None, True))
        assert scope.is_admin is True
        assert scope.allows("0000-TEST") is True

    def test_compute_pm_scope_shop_user_actor(self):
        """The fix: shop-user-tagged dict → is_admin True."""
        import asyncio
        sys.path.insert(0, "/app/backend")
        from pm_auth import compute_pm_scope  # noqa: WPS433
        # Simulate what require_shop_or_admin returns for a per-shop-user.
        actor = {
            "id": "shop-user-uuid",
            "email": "testmech@mascigc.com",
            "role": "Mechanic",
            "_actor_kind": "shop_user",
        }
        scope = asyncio.run(compute_pm_scope(None, actor))
        assert scope.is_admin is True, (
            "REGRESSION: shop user must get unrestricted scope. "
            "The _actor_kind tag is no longer being honored by "
            "compute_pm_scope."
        )
        assert scope.allows("ANY-PROJECT") is True

    def test_compute_pm_scope_pm_actor_still_scoped(self):
        """Anti-regression: actual PM users must STILL be properly
        scoped. The shop fix must not have leaked admin access to PMs."""
        import asyncio
        sys.path.insert(0, "/app/backend")
        try:
            from dotenv import load_dotenv
            load_dotenv("/app/backend/.env")
        except Exception:
            pass
        from pm_auth import compute_pm_scope  # noqa: WPS433
        # PM dict has no _actor_kind tag — it's a normal PM record.
        actor = {
            "id": "pm-uuid",
            "email": "somepm@example.com",
            "is_admin_or_legacy": False,
        }
        from motor.motor_asyncio import AsyncIOMotorClient
        mongo_url = os.environ.get("MONGO_URL")
        db_name = os.environ.get("DB_NAME")
        if not mongo_url or not db_name:
            pytest.skip("MONGO_URL/DB_NAME not configured")
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        scope = asyncio.run(compute_pm_scope(db, actor))
        # PM with no assigned jobs → is_admin False, empty project set.
        assert scope.is_admin is False, (
            "REGRESSION: the shop fix accidentally granted admin scope to "
            "regular PM tokens. compute_pm_scope must only short-circuit "
            "when _actor_kind == 'shop_user'."
        )
