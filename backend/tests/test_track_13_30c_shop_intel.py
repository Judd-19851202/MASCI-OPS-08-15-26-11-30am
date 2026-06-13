"""Track 13.30C · Shop Command Center intelligence backend tests.

Covers ``GET /api/shop/units/search`` and ``GET /api/shop/me/summary``.
"""
import os
import uuid
import httpx
import pytest


REACT_APP_BACKEND_URL = (
    os.environ.get("REACT_APP_BACKEND_URL")
    or open("/app/frontend/.env").read().split("REACT_APP_BACKEND_URL=", 1)[-1].splitlines()[0].strip()
)
API = REACT_APP_BACKEND_URL.rstrip("/") + "/api"


def _admin() -> str:
    r = httpx.post(f"{API}/admin/login", json={"password": "MASCI1982!"}, timeout=30)
    if r.status_code != 200:
        pytest.skip(f"admin login failed: {r.status_code}")
    return r.json()["token"]


# ── /units/search ───────────────────────────────────────────────────────


def test_units_search_requires_auth():
    r = httpx.get(f"{API}/shop/units/search", params={"q": "truck"}, timeout=30)
    assert r.status_code == 401


def test_units_search_short_query_returns_empty():
    tok = _admin()
    r = httpx.get(f"{API}/shop/units/search", params={"q": "a"},
                  headers={"X-Admin-Token": tok}, timeout=30)
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 0 and body["results"] == []


def test_units_search_compact_shape_and_limit_enforced():
    tok = _admin()
    r = httpx.get(f"{API}/shop/units/search", params={"q": "tk", "limit": 5},
                  headers={"X-Admin-Token": tok}, timeout=30)
    assert r.status_code == 200
    body = r.json()
    assert "query" in body and "count" in body and "results" in body and "source" in body
    assert body["source"] == "shop_command_center_intel"
    assert len(body["results"]) <= 5
    for row in body["results"]:
        # closed-set fields
        for k in ("unit_number", "asset_name", "asset_type", "status",
                  "open_defects_count", "highest_severity", "assigned_mechanic",
                  "parts_on_order_count", "last_fuel_lube_visit", "links"):
            assert k in row, f"missing field {k}"
        assert row["links"]["manager_queue"] == "/shop/manager/queue"
        # links.unit_history must point to /shop/units/<unit>/history
        if row.get("unit_number"):
            assert row["links"]["unit_history"] == f"/shop/units/{row['unit_number']}/history"
    # no cost / accounting / PO leaks
    blob = repr(body).lower()
    for f in ("cost", "price", "po_number", "tax", "invoice", "margin"):
        assert f not in blob


def test_units_search_finds_by_unit_when_seeded():
    """Seed a real equipment_master row + fleet_defects and verify
    search returns it with non-zero open_defects_count."""
    tok = _admin()
    suffix = uuid.uuid4().hex[:8]
    unit = f"ITESTUNIT{suffix}"
    headers = {"X-Admin-Token": tok, "Content-Type": "application/json"}
    # Seed equipment via existing admin endpoint? Easier to insert via mongo:
    from motor.motor_asyncio import AsyncIOMotorClient
    import asyncio
    e = {}
    for line in open("/app/backend/.env"):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            e[k.strip()] = v.strip().strip('"').strip("'")

    async def seed_and_clean():
        cli = AsyncIOMotorClient(e["MONGO_URL"])
        db = cli[e["DB_NAME"]]
        try:
            await db.equipment_master.insert_one({
                "id": unit, "asset_id": unit, "unit_number": unit,
                "label": f"Test unit {suffix}",
                "type": "skid_steer", "category": "skid_steer", "status": "active",
                "is_active": True,
            })
            await db.fleet_defects.insert_one({
                "id": f"itestdef-{suffix}", "truck_unit_number": unit,
                "status": "open", "severity": "oos", "category": "engine",
                "item_text": "test defect", "reported_at": "2026-06-13T00:00:00Z",
            })
            # Search
            r = httpx.get(f"{API}/shop/units/search", params={"q": unit},
                          headers={"X-Admin-Token": tok}, timeout=30)
            assert r.status_code == 200, r.text
            body = r.json()
            rows = [x for x in body["results"] if x["unit_number"] == unit]
            assert len(rows) == 1
            assert rows[0]["open_defects_count"] >= 1
            assert rows[0]["highest_severity"] == "oos"
            assert rows[0]["status"] == "available"  # equipment_master.status "active" → "available"
        finally:
            await db.equipment_master.delete_one({"id": unit})
            await db.fleet_defects.delete_one({"id": f"itestdef-{suffix}"})

    asyncio.run(seed_and_clean())


def test_units_search_does_not_match_uuid_id_substring():
    """Regression guard for Track 13.30D closeout audit.

    Pre-audit, `units_search` ran a contains-regex against the internal
    ``id`` field (a UUID), causing accidental hits where the UUID
    happened to contain the search digits (e.g. ``q=127`` matched a UUID
    like ``10127b48-…``). Operators saw raw UUIDs surface as
    "unit_number" rows. This test seeds an equipment row whose internal
    UUID contains the search digits but whose ``unit_number`` does NOT,
    and asserts that row is **not** returned.
    """
    tok = _admin()
    headers = {"X-Admin-Token": tok}
    suffix = uuid.uuid4().hex[:6]
    # UUID picked so it contains the literal substring "ZZUUID987" — we
    # use that as the search term so we can't accidentally match real data.
    rigged_id = f"abc-ZZUUID987-{suffix}"
    real_unit = f"REGUNIT{suffix}"  # does NOT contain ZZUUID987

    from motor.motor_asyncio import AsyncIOMotorClient
    import asyncio
    e = {}
    for line in open("/app/backend/.env"):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            e[k.strip()] = v.strip().strip('"').strip("'")

    async def seed_and_check():
        cli = AsyncIOMotorClient(e["MONGO_URL"])
        db = cli[e["DB_NAME"]]
        try:
            await db.equipment_master.insert_one({
                "id": rigged_id, "asset_id": rigged_id,
                "unit_number": real_unit,
                "label": "Search regression seed",
                "type": "skid_steer", "category": "skid_steer",
                "status": "active", "is_active": True,
            })
            # Search for the UUID substring — must NOT return our row.
            r = httpx.get(f"{API}/shop/units/search",
                          params={"q": "ZZUUID987"},
                          headers=headers, timeout=30)
            assert r.status_code == 200, r.text
            body = r.json()
            matching = [
                x for x in body["results"]
                if (x.get("unit_number") == real_unit) or (x.get("links", {}).get("unit_history", "").endswith(f"/{rigged_id}/history"))
            ]
            assert matching == [], (
                f"Search returned row matched only via UUID substring: {matching!r}"
            )
            # Sanity: searching by the REAL unit_number still returns the row.
            r2 = httpx.get(f"{API}/shop/units/search",
                           params={"q": real_unit},
                           headers=headers, timeout=30)
            assert r2.status_code == 200, r2.text
            hits = [x for x in r2.json()["results"] if x.get("unit_number") == real_unit]
            assert len(hits) == 1
            assert hits[0]["links"]["unit_history"] == f"/shop/units/{real_unit}/history"
        finally:
            await db.equipment_master.delete_one({"id": rigged_id})

    asyncio.run(seed_and_check())




# ── /me/summary ─────────────────────────────────────────────────────────


def test_me_summary_requires_auth():
    r = httpx.get(f"{API}/shop/me/summary", timeout=30)
    assert r.status_code == 401


def test_me_summary_admin_returns_manager_counts():
    tok = _admin()
    r = httpx.get(f"{API}/shop/me/summary",
                  headers={"X-Admin-Token": tok}, timeout=30)
    assert r.status_code == 200
    body = r.json()
    assert body["role"] in {"admin", "shop_manager"}
    counts = body["counts"]
    for k in ("unassigned", "pending_review", "in_progress",
              "waiting_parts", "rts_pending", "variance_review_7d"):
        assert k in counts
        assert isinstance(counts[k], int)
        assert counts[k] >= 0
    labels = body["labels"]
    assert labels["unassigned"] == "Unassigned defects"
    assert labels["rts_pending"] == "Ready for RTS verification"
    assert body["source"] == "shop_command_center_intel"
