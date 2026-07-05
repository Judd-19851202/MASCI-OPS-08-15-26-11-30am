"""TRACK 22.4b-followup-Safety · B-04 Trench Repair Lifecycle regression.

Proves the fundamental Safety doctrine:

    Repair Complete  ≠  Safe To Use

by exercising the trench-safety repair lifecycle end-to-end with:
  - Shop PVI token  (has the shop role only, no safety powers)
  - Safety PVI token (has the safety role only, no shop powers)

The seven invariants below are the durable proof B-04 is closed:

  1. Shop CAN open a repair (already permitted).
  2. Shop CAN mark that repair Completed.
  3. After Shop marks repair Completed with requires_reinspection=True,
     the asset is NOT back to "Available" — it is now in an Inspection
     Hold (owned by Safety, not Shop).
  4. Shop CANNOT verify the repair (POST /verify → 401).
  5. Shop CANNOT clear a Safety Hold (POST /holds/{id}/clear → 401).
  6. Safety CAN verify the repair with reinspection_passed=True → asset
     returns to Available.
  7. Safety CAN clear a Safety Hold via the /clear endpoint.

The test is written to be **hermetic** — it seeds its own asset
``TB-B04-VALIDATION`` (or reuses it if a prior run left it behind) and
cleans up hold/repair rows tied to it after the run.
"""
from __future__ import annotations

import os
import asyncio
import uuid

import httpx
import pytest
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv("/app/backend/.env")

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8001")
ADMIN_EMAIL = os.environ.get("TEST_SUPER_ADMIN_EMAIL", "jaymn.judd@mascigc.com")
ADMIN_PASS = os.environ.get("TEST_SUPER_ADMIN_PASSWORD", "Maddix123!")

TEST_ASSET_ID = "TB-B04-VALIDATION"


def _admin_token() -> str:
    r = httpx.post(
        f"{BACKEND_URL}/api/auth/multi-login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASS},
        timeout=15.0,
    )
    r.raise_for_status()
    return (r.json().get("portal_tokens") or {}).get("admin") or ""


def _mint(admin_token: str, role: str) -> str:
    r = httpx.post(
        f"{BACKEND_URL}/api/admin/preview-validation-identities/mint",
        headers={"X-Admin-Token": admin_token},
        json={
            "role": role,
            "purpose": f"B-04 trench lifecycle · {role}",
            "ttl_minutes": 30,
            "validation_track": "TRACK_22_4B_FOLLOWUP_SAFETY_B04",
        },
        timeout=15.0,
    )
    r.raise_for_status()
    return r.json()["token"]


@pytest.fixture(scope="module")
def admin_token() -> str:
    return _admin_token()


@pytest.fixture(scope="module")
def shop_pvi(admin_token) -> str:
    return _mint(admin_token, "shop")


@pytest.fixture(scope="module")
def safety_pvi(admin_token) -> str:
    return _mint(admin_token, "safety")


@pytest.fixture(scope="module", autouse=True)
def _asset_lifecycle(admin_token):
    """Seed a dedicated test asset and reset between test-module runs."""

    async def _seed_and_teardown():
        c = AsyncIOMotorClient(os.environ["MONGO_URL"])
        db = c[os.environ["DB_NAME"]]
        # teardown any prior state
        await db.trench_safety_repairs.delete_many({"asset_id": TEST_ASSET_ID})
        await db.trench_safety_holds.delete_many({"asset_id": TEST_ASSET_ID})
        await db.trench_safety_assets.delete_many({"asset_id": TEST_ASSET_ID})
        # seed a fresh asset — Available, no holds, no repairs
        await db.trench_safety_assets.insert_one({
            "id": str(uuid.uuid4()),
            "asset_id": TEST_ASSET_ID,
            "asset_type": "Trench Box",
            "manufacturer": "TEST",
            "model": "B-04 VALIDATION",
            "condition": "Good",
            "operational_status": "Available",
            "current_location": "Preview Yard",
            "owner": "MASCI",
        })
        c.close()

    asyncio.run(_seed_and_teardown())
    yield
    # keep the asset for post-run inspection; only wipe if you want strict cleanup


@pytest.fixture(autouse=True)
def _per_test_reset():
    """Per-test reset — every test starts with a clean Available asset,
    no holds, no repairs. Preserves the module-level asset row."""

    async def _reset():
        c = AsyncIOMotorClient(os.environ["MONGO_URL"])
        db = c[os.environ["DB_NAME"]]
        await db.trench_safety_repairs.delete_many({"asset_id": TEST_ASSET_ID})
        await db.trench_safety_holds.delete_many({"asset_id": TEST_ASSET_ID})
        await db.trench_safety_assets.update_one(
            {"asset_id": TEST_ASSET_ID},
            {"$set": {"operational_status": "Available"}},
        )
        c.close()

    asyncio.run(_reset())
    yield


# ── helpers ────────────────────────────────────────────────────────

def _url(path: str) -> str:
    return f"{BACKEND_URL}/api{path}"


def _open_shop_repair(shop_pvi: str) -> dict:
    r = httpx.post(
        _url(f"/trench-safety/assets/{TEST_ASSET_ID}/repairs"),
        headers={"X-Shop-Token": shop_pvi, "Content-Type": "application/json"},
        json={
            "issue_description": "B-04 lifecycle regression — cracked weld",
            "requires_reinspection": True,
        },
        timeout=15.0,
    )
    assert r.status_code in (200, 201), r.text
    return r.json()


def _complete_shop_repair(shop_pvi: str, repair_id: str) -> dict:
    r = httpx.post(
        _url(f"/trench-safety/repairs/{repair_id}/complete"),
        headers={"X-Shop-Token": shop_pvi},
        timeout=15.0,
    )
    assert r.status_code in (200, 201), r.text
    return r.json()


# ── 1. Shop CAN open a repair ─────────────────────────────────────

def test_shop_can_open_repair(shop_pvi):
    body = _open_shop_repair(shop_pvi)
    assert body["repair"]["status"] == "Open"
    # Auto-opened Maintenance Hold changes operational_status
    assert body["asset"]["operational_status"] == "Maintenance Hold"


# ── 2. Shop CAN mark repair Completed ─────────────────────────────
# ── 3. Repair Completed does NOT return asset to Available ────────

def test_shop_repair_complete_does_not_return_to_service(shop_pvi):
    opened = _open_shop_repair(shop_pvi)
    repair_id = opened["repair"]["id"]
    body = _complete_shop_repair(shop_pvi, repair_id)
    assert body["repair"]["status"] == "Completed"
    # Requires reinspection → Inspection Hold now owns the asset.
    op = body["asset"]["operational_status"]
    assert op == "Inspection Hold", (
        f"Repair Complete ≠ Safe To Use — asset should sit in Inspection Hold, "
        f"not '{op}'."
    )


# ── 4. Shop CANNOT verify a repair ────────────────────────────────

def test_shop_cannot_verify_repair(shop_pvi):
    opened = _open_shop_repair(shop_pvi)
    repair_id = opened["repair"]["id"]
    _complete_shop_repair(shop_pvi, repair_id)
    r = httpx.post(
        _url(f"/trench-safety/repairs/{repair_id}/verify"),
        headers={"X-Shop-Token": shop_pvi, "Content-Type": "application/json"},
        json={"verification_notes": "shop-should-not-be-able-to-do-this",
              "reinspection_passed": True},
        timeout=15.0,
    )
    assert r.status_code == 401, (
        f"Shop must NEVER be able to verify a repair. Got HTTP {r.status_code} · "
        f"{r.text[:200]}"
    )


# ── 5. Shop CANNOT clear a Safety Hold ────────────────────────────

def test_shop_cannot_clear_safety_hold(admin_token, shop_pvi, safety_pvi):
    # Safety opens a Safety Hold on the asset via the PVI helper.
    open_r = httpx.post(
        _url(f"/trench-safety/assets/{TEST_ASSET_ID}/holds"),
        headers={"X-Safety-Token": safety_pvi, "Content-Type": "application/json"},
        json={
            "kind": "Safety Hold",
            "reason": "B-04 regression — Safety opens a hold",
            "source": "manual",
        },
        timeout=15.0,
    )
    assert open_r.status_code in (200, 201), open_r.text
    hold_id = open_r.json()["hold"]["id"]
    # Shop attempts to clear it → must 401.
    clear_r = httpx.post(
        _url(f"/trench-safety/holds/{hold_id}/clear"),
        headers={"X-Shop-Token": shop_pvi, "Content-Type": "application/json"},
        json={"clear_reason": "shop-should-not-be-able-to-do-this",
              "clear_source": "manual"},
        timeout=15.0,
    )
    assert clear_r.status_code == 401, (
        f"Shop must NEVER be able to clear a Safety Hold. Got HTTP {clear_r.status_code} · "
        f"{clear_r.text[:200]}"
    )
    # Clean up the safety hold so subsequent tests can proceed.
    clear_r = httpx.post(
        _url(f"/trench-safety/holds/{hold_id}/clear"),
        headers={"X-Safety-Token": safety_pvi, "Content-Type": "application/json"},
        json={"clear_reason": "test cleanup", "clear_source": "manual"},
        timeout=15.0,
    )
    assert clear_r.status_code == 200


# ── 6. Safety CAN verify + return asset to Available ──────────────

def test_safety_verifies_and_returns_asset_to_service(shop_pvi, safety_pvi):
    opened = _open_shop_repair(shop_pvi)
    repair_id = opened["repair"]["id"]
    _complete_shop_repair(shop_pvi, repair_id)
    r = httpx.post(
        _url(f"/trench-safety/repairs/{repair_id}/verify"),
        headers={"X-Safety-Token": safety_pvi, "Content-Type": "application/json"},
        json={"verification_notes": "Safety verified — reinspection passed",
              "reinspection_passed": True},
        timeout=15.0,
    )
    assert r.status_code in (200, 201), r.text
    body = r.json()
    assert body["repair"]["status"] == "Closed After Verification"
    # Now the asset should be back to Available (no other holds).
    op = body["asset"]["operational_status"]
    assert op == "Available", (
        f"Safety verification with reinspection_passed=True must return the "
        f"asset to Available. Got '{op}'."
    )


# ── 7. Safety CAN clear a Safety Hold ─────────────────────────────

def test_safety_can_clear_safety_hold(safety_pvi):
    # Open + clear
    open_r = httpx.post(
        _url(f"/trench-safety/assets/{TEST_ASSET_ID}/holds"),
        headers={"X-Safety-Token": safety_pvi, "Content-Type": "application/json"},
        json={"kind": "Safety Hold", "reason": "B-04 sign-off proof",
              "source": "manual"},
        timeout=15.0,
    )
    assert open_r.status_code in (200, 201), open_r.text
    hold_id = open_r.json()["hold"]["id"]
    clear_r = httpx.post(
        _url(f"/trench-safety/holds/{hold_id}/clear"),
        headers={"X-Safety-Token": safety_pvi, "Content-Type": "application/json"},
        json={"clear_reason": "B-04 verification complete", "clear_source": "manual"},
        timeout=15.0,
    )
    assert clear_r.status_code == 200, clear_r.text
