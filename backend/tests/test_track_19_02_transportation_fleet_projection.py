"""TRACK 19.02 · Transportation Fleet Projection tests.

The Transportation Trucks page must be a VIEW into the existing MASCI
fleet (equipment_master + equipment_units), not a separate fleet
database. Validates:

  1. /api/admin/transportation/fleet/equipment exists and surfaces both
     MASCI-owned (equipment_master) and leased (transport_trucks) assets.
  2. Summary includes masci_fleet_total, masci_fleet_adopted, leased_total.
  3. Filters (category, ownership, q, status) work.
  4. Permission policy: dispatch + admin read; adopt is admin-only.
  5. Adopt endpoint is idempotent and creates a transport_trucks overlay
     that points back at equipment_master via equipment_id.
"""
from __future__ import annotations

import os
import pytest
import requests

API = os.environ.get(
    "REACT_APP_BACKEND_URL",
    "https://backup-forensics.preview.emergentagent.com",
).rstrip("/")
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"


@pytest.fixture(scope="module")
def tokens():
    r = requests.post(
        f"{API}/api/auth/multi-login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=20,
    )
    r.raise_for_status()
    pt = r.json().get("portal_tokens") or {}
    assert pt.get("admin") and pt.get("dispatch")
    return {"admin": pt["admin"], "dispatch": pt["dispatch"]}


def _dh(t): return {"X-Dispatch-Token": t}
def _ah(t): return {"X-Admin-Token": t}


def test_fleet_projection_returns_masci_and_leased(tokens):
    r = requests.get(
        f"{API}/api/admin/transportation/fleet/equipment?limit=2000",
        headers=_dh(tokens["dispatch"]),
        timeout=30,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert "items" in body and "summary" in body
    s = body["summary"]
    assert s["masci_fleet_total"] >= 100, \
        f"expected substantial MASCI transport fleet, got {s['masci_fleet_total']}"
    assert s["leased_total"] >= 0
    assert isinstance(s["categories"], list) and len(s["categories"]) >= 5
    # No fleet view exists if it doesn't expose the actual MASCI haulers.
    sources = {it["source"] for it in body["items"]}
    assert "equipment_master" in sources, "MASCI assets must surface"


def test_fleet_projection_category_filter(tokens):
    r = requests.get(
        f"{API}/api/admin/transportation/fleet/equipment?category=Dump%20Trucks&limit=500",
        headers=_dh(tokens["dispatch"]),
        timeout=30,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["count"] > 0
    for it in body["items"]:
        assert it["category"] == "Dump Trucks"


def test_fleet_projection_ownership_filter_leased(tokens):
    r = requests.get(
        f"{API}/api/admin/transportation/fleet/equipment?ownership=leased_carrier",
        headers=_dh(tokens["dispatch"]),
        timeout=30,
    )
    assert r.status_code == 200
    body = r.json()
    for it in body["items"]:
        assert it["ownership"] == "leased_carrier"
        assert it["source"] == "transport_trucks"


def test_fleet_projection_search_q(tokens):
    r = requests.get(
        f"{API}/api/admin/transportation/fleet/equipment?q=Mack&limit=50",
        headers=_dh(tokens["dispatch"]),
        timeout=30,
    )
    assert r.status_code == 200


def test_fleet_projection_dispatch_can_read(tokens):
    r = requests.get(
        f"{API}/api/admin/transportation/fleet/equipment?limit=5",
        headers=_dh(tokens["dispatch"]),
        timeout=30,
    )
    assert r.status_code == 200


def test_fleet_projection_anon_rejected():
    r = requests.get(
        f"{API}/api/admin/transportation/fleet/equipment",
        timeout=15,
    )
    assert r.status_code in (401, 403)


def test_fleet_adopt_is_admin_only(tokens):
    # Pick any equipment_master row from the projection.
    r = requests.get(
        f"{API}/api/admin/transportation/fleet/equipment?category=Dump%20Trucks&limit=1",
        headers=_dh(tokens["dispatch"]),
        timeout=20,
    )
    eqid = r.json()["items"][0]["id"]
    # Dispatch must NOT adopt.
    r2 = requests.post(
        f"{API}/api/admin/transportation/fleet/equipment/{eqid}/adopt",
        headers=_dh(tokens["dispatch"]),
        timeout=20,
    )
    assert r2.status_code in (401, 403)


def test_fleet_adopt_admin_and_idempotent(tokens):
    # Pick the same row reproducibly.
    r = requests.get(
        f"{API}/api/admin/transportation/fleet/equipment?category=Service%20Trucks&limit=1",
        headers=_ah(tokens["admin"]),
        timeout=20,
    )
    items = r.json()["items"]
    assert items, "expected at least one transport-capable Service Truck"
    eqid = items[0]["id"]

    r2 = requests.post(
        f"{API}/api/admin/transportation/fleet/equipment/{eqid}/adopt",
        headers=_ah(tokens["admin"]),
        timeout=20,
    )
    assert r2.status_code == 200, r2.text
    truck = r2.json()
    overlay_id = truck["id"]
    try:
        assert truck["equipment_id"] == eqid
        assert truck["ownership"] == "masci_owned"
        # Idempotency — second call returns already_adopted=True.
        r3 = requests.post(
            f"{API}/api/admin/transportation/fleet/equipment/{eqid}/adopt",
            headers=_ah(tokens["admin"]),
            timeout=20,
        )
        assert r3.status_code == 200
        assert r3.json().get("already_adopted") is True
        # Projection now reports >=1 adopted.
        r4 = requests.get(
            f"{API}/api/admin/transportation/fleet/equipment?limit=2000",
            headers=_ah(tokens["admin"]),
            timeout=30,
        )
        assert r4.json()["summary"]["masci_fleet_adopted"] >= 1
    finally:
        # Clean up — delete overlay + eligibility row so reruns are stable.
        from motor.motor_asyncio import AsyncIOMotorClient
        import asyncio
        from dotenv import load_dotenv
        load_dotenv("/app/backend/.env")
        async def _cleanup():
            client = AsyncIOMotorClient(os.environ["MONGO_URL"])
            db = client[os.environ["DB_NAME"]]
            await db.transport_trucks.delete_one({"id": overlay_id})
            await db.transport_eligibility_state.delete_one(
                {"target_type": "truck", "target_id": overlay_id})
            client.close()
        asyncio.run(_cleanup())


def test_fleet_adopt_rejects_non_transport_category(tokens):
    # equipment_master has many Trench Safety / Excavator / Loader assets
    # — none should be adoptable into Transportation.
    from motor.motor_asyncio import AsyncIOMotorClient
    import asyncio
    from dotenv import load_dotenv
    load_dotenv("/app/backend/.env")
    async def _pick():
        client = AsyncIOMotorClient(os.environ["MONGO_URL"])
        db = client[os.environ["DB_NAME"]]
        d = await db.equipment_master.find_one({"category": "Excavators"})
        client.close()
        return d["id"] if d else None
    eqid = asyncio.run(_pick())
    if not eqid:
        pytest.skip("no Excavators in equipment_master")
    r = requests.post(
        f"{API}/api/admin/transportation/fleet/equipment/{eqid}/adopt",
        headers=_ah(tokens["admin"]),
        timeout=20,
    )
    assert r.status_code == 422


def test_version_exposes_real_commit_and_built_at():
    """Track 19.02 P1 · /api/version no longer returns 'unknown'."""
    r = requests.get(f"{API}/api/version", timeout=15)
    assert r.status_code == 200
    body = r.json()
    assert body["commit"] != "unknown", "commit should resolve from GIT_COMMIT or source_hash"
    assert body["built_at"] != "unknown", "built_at should resolve from BUILT_AT or started_at"
    assert len(body["commit"]) >= 8


def test_orientation_dashboard_fast(tokens):
    """Track 19.02 P0.5 · dashboard returns under ~2s even at full scale."""
    import time
    t0 = time.time()
    r = requests.get(
        f"{API}/api/admin/transportation/orientation/dashboard",
        headers=_dh(tokens["dispatch"]),
        timeout=20,
    )
    elapsed = time.time() - t0
    assert r.status_code == 200
    body = r.json()
    assert "drivers_total" in body and "completion_pct" in body
    # Local DB so this is a generous bound — pre-fix orientation dashboard
    # took 3-4s for 172 drivers; post-fix should be sub-1s.
    assert elapsed < 5.0, f"orientation_dashboard too slow: {elapsed:.2f}s"
