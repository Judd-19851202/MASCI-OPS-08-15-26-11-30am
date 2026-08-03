"""TRACK 19.02A · Transportation Fleet Adoption Hardening tests.

Coverage:
  · Adoption Preview (read-only)
  · Bulk adoption + idempotency
  · Bulk rollback
  · Per-equipment adopt (legacy single-row CTA still works)
  · Overlay PATCH — editable vs protected field policy
  · Permission gates (anon · dispatch · admin)
  · Audit events emitted (transport_asset_adopt, transport_bulk_adoption_completed,
    transport_bulk_adoption_rolled_back, transport_overlay_update)
"""
from __future__ import annotations

import asyncio
import os

import pytest
import requests
from dotenv import load_dotenv

load_dotenv("/app/backend/.env")
from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402

API = os.environ.get(
    "REACT_APP_BACKEND_URL",
    "https://masci-audit-hub.preview.emergentagent.com",
).rstrip("/")
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"
MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]


# ─────────────────────── fixtures ───────────────────────


@pytest.fixture(scope="module")
def tokens():
    last = None
    for _ in range(3):
        try:
            r = requests.post(
                f"{API}/api/auth/multi-login",
                json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
                timeout=60,
            )
            r.raise_for_status()
            pt = r.json().get("portal_tokens") or {}
            return {"admin": pt["admin"], "dispatch": pt["dispatch"]}
        except Exception as exc:  # noqa: BLE001
            last = exc
    raise RuntimeError(f"multi-login failed: {last}")


def _ah(t): return {"X-Admin-Token": t, "Content-Type": "application/json"}
def _dh(t): return {"X-Dispatch-Token": t, "Content-Type": "application/json"}


def _db():
    return AsyncIOMotorClient(MONGO_URL)[DB_NAME]


async def _cleanup_overlays_for_eq(eq_ids):
    db = _db()
    if eq_ids:
        await db.transport_trucks.delete_many(
            {"tenant": "masci", "equipment_id": {"$in": list(eq_ids)}})
        await db.transport_eligibility_state.delete_many(
            {"target_type": "truck"})
    db.client.close()


async def _cleanup_batch(batch_id):
    db = _db()
    overlays = await db.transport_trucks.find(
        {"tenant": "masci", "bulk_adoption_batch_id": batch_id}).to_list(5000)
    ids = [o["id"] for o in overlays]
    await db.transport_trucks.delete_many(
        {"tenant": "masci", "bulk_adoption_batch_id": batch_id})
    await db.transport_eligibility_state.delete_many(
        {"target_type": "truck", "target_id": {"$in": ids}})
    db.client.close()


@pytest.fixture(autouse=True)
def _clean_before_after():
    """Each test starts with no batch adoptions present."""
    async def _clean():
        db = _db()
        # Remove any overlay rows that point at equipment_master rows (those
        # belong to this test domain). Leave leased_carrier rows alone.
        await db.transport_trucks.delete_many({
            "tenant": "masci",
            "equipment_id": {"$ne": None, "$exists": True},
        })
        await db.transport_eligibility_state.delete_many(
            {"target_type": "truck"})
        db.client.close()
    asyncio.run(_clean())
    yield
    asyncio.run(_clean())


# ─────────────────────── 1 · Preview ───────────────────────


def test_preview_is_read_only(tokens):
    r = requests.get(
        f"{API}/api/admin/transportation/fleet/adoption-preview",
        headers=_dh(tokens["dispatch"]), timeout=30)
    assert r.status_code == 200
    body = r.json()
    s = body["summary"]
    assert body["categories_in_scope"]
    assert "category_totals" in body
    assert s["would_adopt"] >= 100, \
        f"expected >=100 transport-capable assets, got {s['would_adopt']}"
    # Preview must NOT have written anything.
    r2 = requests.get(
        f"{API}/api/admin/transportation/fleet/equipment?limit=2000",
        headers=_dh(tokens["dispatch"]), timeout=30)
    assert r2.json()["summary"]["masci_fleet_adopted"] == 0


def test_preview_excludes_passenger_categories(tokens):
    r = requests.get(
        f"{API}/api/admin/transportation/fleet/adoption-preview",
        headers=_dh(tokens["dispatch"]), timeout=30)
    cats = r.json()["categories_in_scope"]
    assert "Pickup Trucks" not in cats
    assert "Supervisor / Mgmt Trucks" not in cats
    assert "Excavators" not in cats
    assert "Dump Trucks" in cats and "Tractor Trailer Trucks" in cats


def test_preview_anon_rejected():
    r = requests.get(
        f"{API}/api/admin/transportation/fleet/adoption-preview",
        timeout=15)
    assert r.status_code in (401, 403)


# ─────────────────────── 2 · Bulk adoption ───────────────────────


def test_bulk_dry_run_writes_nothing(tokens):
    r = requests.post(
        f"{API}/api/admin/transportation/fleet/adoption-bulk",
        headers=_ah(tokens["admin"]), json={"dry_run": True}, timeout=30)
    assert r.status_code == 200
    body = r.json()
    assert body["dry_run"] is True
    assert body["created"] == 0
    assert body["would_create"] >= 100
    assert body["batch_id"] is None
    # Verify projection is still 0 adopted.
    r2 = requests.get(
        f"{API}/api/admin/transportation/fleet/equipment?limit=2000",
        headers=_ah(tokens["admin"]), timeout=30)
    assert r2.json()["summary"]["masci_fleet_adopted"] == 0


def test_bulk_adoption_creates_and_is_idempotent(tokens):
    r1 = requests.post(
        f"{API}/api/admin/transportation/fleet/adoption-bulk",
        headers=_ah(tokens["admin"]), json={}, timeout=30)
    assert r1.status_code == 200
    body1 = r1.json()
    assert body1["created"] >= 100
    batch_id = body1["batch_id"]
    assert batch_id and len(batch_id) >= 8
    try:
        # Re-running the same operator action must NOT duplicate.
        r2 = requests.post(
            f"{API}/api/admin/transportation/fleet/adoption-bulk",
            headers=_ah(tokens["admin"]), json={}, timeout=30)
        body2 = r2.json()
        assert body2["created"] == 0
        assert body2["skipped_already_adopted"] == body1["created"]
        # And a third time.
        r3 = requests.post(
            f"{API}/api/admin/transportation/fleet/adoption-bulk",
            headers=_ah(tokens["admin"]), json={}, timeout=30)
        assert r3.json()["created"] == 0
        # Projection now reports adopted = created count.
        r4 = requests.get(
            f"{API}/api/admin/transportation/fleet/equipment?limit=2000",
            headers=_ah(tokens["admin"]), timeout=30)
        assert r4.json()["summary"]["masci_fleet_adopted"] == body1["created"]
    finally:
        asyncio.run(_cleanup_batch(batch_id))


def test_bulk_adoption_dispatch_rejected(tokens):
    r = requests.post(
        f"{API}/api/admin/transportation/fleet/adoption-bulk",
        headers=_dh(tokens["dispatch"]), json={}, timeout=30)
    assert r.status_code in (401, 403)


def test_bulk_adoption_anon_rejected():
    r = requests.post(
        f"{API}/api/admin/transportation/fleet/adoption-bulk",
        json={}, timeout=15)
    assert r.status_code in (401, 403)


def test_bulk_adoption_no_duplicate_overlays(tokens):
    r = requests.post(
        f"{API}/api/admin/transportation/fleet/adoption-bulk",
        headers=_ah(tokens["admin"]), json={}, timeout=30)
    batch_id = r.json()["batch_id"]
    try:
        # Verify uniqueness invariant: each equipment_id appears in at
        # most one overlay row.
        async def _verify():
            db = _db()
            pipeline = [
                {"$match": {"tenant": "masci",
                            "equipment_id": {"$ne": None, "$exists": True}}},
                {"$group": {"_id": "$equipment_id", "count": {"$sum": 1}}},
                {"$match": {"count": {"$gt": 1}}},
            ]
            dups = await db.transport_trucks.aggregate(pipeline).to_list(50)
            db.client.close()
            return dups
        dups = asyncio.run(_verify())
        assert dups == [], \
            f"duplicate overlays present after bulk adoption: {dups}"
    finally:
        asyncio.run(_cleanup_batch(batch_id))


# ─────────────────────── 3 · Rollback ───────────────────────


def test_rollback_removes_only_named_batch(tokens):
    r = requests.post(
        f"{API}/api/admin/transportation/fleet/adoption-bulk",
        headers=_ah(tokens["admin"]), json={}, timeout=30)
    batch_id = r.json()["batch_id"]
    created = r.json()["created"]
    # Sanity: projection shows adopted.
    assert requests.get(
        f"{API}/api/admin/transportation/fleet/equipment?limit=2000",
        headers=_ah(tokens["admin"]), timeout=30,
    ).json()["summary"]["masci_fleet_adopted"] == created
    # Rollback.
    rr = requests.post(
        f"{API}/api/admin/transportation/fleet/adoption-bulk/{batch_id}/rollback",
        headers=_ah(tokens["admin"]), timeout=30)
    assert rr.status_code == 200
    assert rr.json()["removed"] == created
    # Projection now reports zero adopted.
    final = requests.get(
        f"{API}/api/admin/transportation/fleet/equipment?limit=2000",
        headers=_ah(tokens["admin"]), timeout=30,
    ).json()["summary"]
    assert final["masci_fleet_adopted"] == 0
    # Leased rows still intact.
    assert final["leased_total"] >= 1


def test_rollback_admin_only(tokens):
    rr = requests.post(
        f"{API}/api/admin/transportation/fleet/adoption-bulk/nonexistentbatch/rollback",
        headers=_dh(tokens["dispatch"]), timeout=15)
    assert rr.status_code in (401, 403)


def test_rollback_invalid_batch_id(tokens):
    rr = requests.post(
        f"{API}/api/admin/transportation/fleet/adoption-bulk/abc/rollback",
        headers=_ah(tokens["admin"]), timeout=15)
    assert rr.status_code == 422


def test_rollback_unknown_batch_id_is_idempotent(tokens):
    rr = requests.post(
        f"{API}/api/admin/transportation/fleet/adoption-bulk/ffffffffffff/rollback",
        headers=_ah(tokens["admin"]), timeout=15)
    assert rr.status_code == 200
    assert rr.json()["removed"] == 0


# ─────────────────────── 4 · Overlay PATCH ───────────────────────


def _adopt_one(tokens):
    r = requests.get(
        f"{API}/api/admin/transportation/fleet/equipment?category=Dump%20Trucks&limit=1",
        headers=_ah(tokens["admin"]), timeout=20)
    eq_id = r.json()["items"][0]["id"]
    requests.post(
        f"{API}/api/admin/transportation/fleet/equipment/{eq_id}/adopt",
        headers=_ah(tokens["admin"]), timeout=15)
    return eq_id


def test_overlay_patch_dispatch_can_edit_operational(tokens):
    eq_id = _adopt_one(tokens)
    r = requests.patch(
        f"{API}/api/admin/transportation/fleet/equipment/{eq_id}/overlay",
        headers=_dh(tokens["dispatch"]),
        json={
            "transportation_classification": "end_dump",
            "dispatch_ready": True,
            "transportation_notes": "Ready for Phoenix yard",
            "operational_tags": ["heavy_haul", "yard_a"],
        },
        timeout=15,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["transportation_classification"] == "end_dump"
    assert body["dispatch_ready"] is True
    assert body["operational_tags"] == ["heavy_haul", "yard_a"]


def test_overlay_patch_protected_field_blocked(tokens):
    eq_id = _adopt_one(tokens)
    # Just verify the policy works on a single representative protected
    # field; iterating all of them only exercises the same code path and
    # is unnecessarily chatty against the preview URL.
    for field in ("vin", "make", "engine_hours", "category"):
        r = requests.patch(
            f"{API}/api/admin/transportation/fleet/equipment/{eq_id}/overlay",
            headers=_ah(tokens["admin"]),
            json={field: "anything"}, timeout=30)
        assert r.status_code == 422, f"{field}: {r.text}"
        detail = r.json()["detail"]
        assert field in detail["protected_fields"]
        assert "Enterprise" in detail["message"]


def test_overlay_patch_invalid_classification(tokens):
    eq_id = _adopt_one(tokens)
    r = requests.patch(
        f"{API}/api/admin/transportation/fleet/equipment/{eq_id}/overlay",
        headers=_ah(tokens["admin"]),
        json={"transportation_classification": "unicorn_carrier"},
        timeout=15)
    assert r.status_code == 422


def test_overlay_patch_missing_overlay_404(tokens):
    # Pick a row that hasn't been adopted.
    r = requests.get(
        f"{API}/api/admin/transportation/fleet/equipment?category=Service%20Trucks&limit=1",
        headers=_ah(tokens["admin"]), timeout=15)
    eq_id = r.json()["items"][0]["id"]
    rr = requests.patch(
        f"{API}/api/admin/transportation/fleet/equipment/{eq_id}/overlay",
        headers=_ah(tokens["admin"]),
        json={"transportation_classification": "service_truck"},
        timeout=15)
    assert rr.status_code == 404


def test_overlay_patch_anon_rejected():
    r = requests.patch(
        f"{API}/api/admin/transportation/fleet/equipment/anything/overlay",
        json={"dispatch_ready": True}, timeout=15)
    assert r.status_code in (401, 403)


def test_overlay_patch_silently_ignores_unknown_fields(tokens):
    eq_id = _adopt_one(tokens)
    r = requests.patch(
        f"{API}/api/admin/transportation/fleet/equipment/{eq_id}/overlay",
        headers=_ah(tokens["admin"]),
        json={"dispatch_ready": True, "weird_unknown_field": "value"},
        timeout=15)
    # Allowed key present → 200, unknown silently dropped.
    assert r.status_code == 200
    assert r.json()["dispatch_ready"] is True


# ─────────────────────── 5 · Audit events ───────────────────────


def test_audit_events_emitted(tokens):
    r = requests.post(
        f"{API}/api/admin/transportation/fleet/adoption-bulk",
        headers=_ah(tokens["admin"]), json={}, timeout=30)
    batch_id = r.json()["batch_id"]
    try:
        async def _check():
            db = _db()
            # Per-overlay adopt audits.
            per = await db.audit_events.count_documents(
                {"kind": "transport_asset_adopt"})
            # Bulk completion audit.
            bulk = await db.audit_events.count_documents(
                {"kind": "transport_bulk_adoption_completed",
                 "entity_id": batch_id})
            db.client.close()
            return per, bulk
        per, bulk = asyncio.run(_check())
        assert per >= 100, f"per-adopt audits not emitted, got {per}"
        assert bulk == 1, \
            f"expected exactly one bulk-completed audit, got {bulk}"
        # Edit one overlay and confirm audit fires.
        em_id = requests.get(
            f"{API}/api/admin/transportation/fleet/equipment?limit=1",
            headers=_ah(tokens["admin"]), timeout=15
        ).json()["items"][0]["id"]
        requests.patch(
            f"{API}/api/admin/transportation/fleet/equipment/{em_id}/overlay",
            headers=_ah(tokens["admin"]),
            json={"transportation_notes": "audit-test"}, timeout=15)

        async def _check_edit():
            db = _db()
            n = await db.audit_events.count_documents(
                {"kind": "transport_overlay_update"})
            db.client.close()
            return n
        assert asyncio.run(_check_edit()) >= 1

        # Rollback emits its own audit event.
        requests.post(
            f"{API}/api/admin/transportation/fleet/adoption-bulk/{batch_id}/rollback",
            headers=_ah(tokens["admin"]), timeout=30)

        async def _check_rb():
            db = _db()
            n = await db.audit_events.count_documents(
                {"kind": "transport_bulk_adoption_rolled_back",
                 "entity_id": batch_id})
            db.client.close()
            return n
        assert asyncio.run(_check_rb()) == 1
    finally:
        asyncio.run(_cleanup_batch(batch_id))


# ─────────────────────── 6 · Performance ───────────────────────


def test_preview_fast(tokens):
    import time
    t0 = time.time()
    r = requests.get(
        f"{API}/api/admin/transportation/fleet/adoption-preview",
        headers=_ah(tokens["admin"]), timeout=10)
    elapsed = time.time() - t0
    assert r.status_code == 200
    assert elapsed < 3.0, f"preview too slow: {elapsed:.2f}s"


def test_bulk_adoption_fast(tokens):
    """Server-side elapsed must be production-fast.
    Wall-clock round-trip varies with preview URL latency, so we only
    assert the elapsed_ms reported by the server."""
    r = requests.post(
        f"{API}/api/admin/transportation/fleet/adoption-bulk",
        headers=_ah(tokens["admin"]), json={}, timeout=60)
    batch_id = r.json()["batch_id"]
    try:
        assert r.status_code == 200
        # Server-side elapsed_ms is the true performance signal.
        assert r.json()["elapsed_ms"] < 5000, \
            f"server reported {r.json()['elapsed_ms']}ms"
    finally:
        asyncio.run(_cleanup_batch(batch_id))
