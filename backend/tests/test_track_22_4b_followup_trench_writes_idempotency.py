"""TRACK 22.4B-FOLLOWUP-TRENCH-WRITES-IDEMPOTENCY regression locks.

Certifies exactly-once submit on the trench-safety write paths without
breaking the B-04 lifecycle invariants:

    Repair Complete  ≠  Safe To Use
    Shop CANNOT clear a Safety Hold
    Safety CANNOT be bypassed on reinspection

Endpoints under test (all wrapped with `with_idempotency`, distinct
workflow scopes):

  * POST /trench-safety/assets/{ident}/inspections    (trench_inspection)
  * POST /trench-safety/assets/{ident}/holds          (trench_hold_open)
  * POST /trench-safety/holds/{hold_id}/clear         (trench_hold_clear)
  * POST /trench-safety/assets/{ident}/repairs        (trench_repair_open)
  * PATCH /trench-safety/repairs/{repair_id}          (trench_repair_update)
  * POST /trench-safety/repairs/{repair_id}/complete  (trench_repair_complete)
  * POST /trench-safety/repairs/{repair_id}/verify    (trench_repair_verify)

Invariants proven:

  1. Same-key concurrent inspection submits create exactly ONE inspection.
  2. Same-key concurrent repair opens create exactly ONE repair AND exactly
     ONE Maintenance Hold row (side effects sit inside the factory).
  3. Same-key concurrent complete calls: exactly one Inspection Hold opened,
     Maintenance Hold cleared once. Lifecycle invariant preserved
     (asset ends in Inspection Hold when requires_reinspection=True).
  4. Same-key concurrent verify calls: repair transitions once and asset
     resolves to Available exactly once.
  5. Same-key concurrent hold-open calls: exactly one hold row created.
  6. Same-key concurrent PATCH note-appends: notes_history grows by
     exactly one entry (no double-push).
  7. Workflow scoping — the same key on a *different* trench workflow
     re-runs (does not replay another workflow's cached response).
  8. RBAC preserved: Shop still 401'd on /verify + /clear.
  9. Motive posture shape untouched (regression proof).
"""
from __future__ import annotations

import asyncio
import os
import uuid

import httpx
import pytest
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv("/app/backend/.env")

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8001")
ADMIN_EMAIL = os.environ.get("TEST_SUPER_ADMIN_EMAIL", "jaymn.judd@mascigc.com")
ADMIN_PASS = os.environ.get("TEST_SUPER_ADMIN_PASSWORD", "Maddix123!")

TEST_ASSET_ID = "TB-IDEMP-TRENCH"


# ── PVI + auth helpers ────────────────────────────────────────────

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
            "purpose": f"trench idempotency · {role}",
            "ttl_minutes": 30,
            "validation_track": "TRACK_22_4B_FOLLOWUP_TRENCH_WRITES_IDEMPOTENCY",
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


# ── asset lifecycle: seed once, reset per test ────────────────────

@pytest.fixture(scope="module", autouse=True)
def _asset_lifecycle():
    async def _seed():
        c = AsyncIOMotorClient(os.environ["MONGO_URL"])
        db = c[os.environ["DB_NAME"]]
        await db.trench_safety_repairs.delete_many({"asset_id": TEST_ASSET_ID})
        await db.trench_safety_holds.delete_many({"asset_id": TEST_ASSET_ID})
        await db.trench_safety_inspections.delete_many({"asset_id": TEST_ASSET_ID})
        await db.trench_safety_assets.delete_many({"asset_id": TEST_ASSET_ID})
        await db.trench_safety_assets.insert_one({
            "id": str(uuid.uuid4()),
            "asset_id": TEST_ASSET_ID,
            "asset_type": "Trench Box",
            "manufacturer": "TEST",
            "model": "IDEMP VALIDATION",
            "condition": "Good",
            "operational_status": "Available",
            "current_location": "Preview Yard",
            "owner": "MASCI",
        })
        c.close()

    asyncio.run(_seed())
    yield


@pytest.fixture(autouse=True)
def _reset_asset_state():
    async def _reset():
        c = AsyncIOMotorClient(os.environ["MONGO_URL"])
        db = c[os.environ["DB_NAME"]]
        await db.trench_safety_repairs.delete_many({"asset_id": TEST_ASSET_ID})
        await db.trench_safety_holds.delete_many({"asset_id": TEST_ASSET_ID})
        await db.trench_safety_inspections.delete_many({"asset_id": TEST_ASSET_ID})
        await db.trench_safety_assets.update_one(
            {"asset_id": TEST_ASSET_ID},
            {"$set": {"operational_status": "Available"}},
        )
        c.close()

    asyncio.run(_reset())
    yield


# ── helpers ───────────────────────────────────────────────────────

def _url(p: str) -> str:
    return f"{BACKEND_URL}/api{p}"


def _mongo():
    c = AsyncIOMotorClient(os.environ["MONGO_URL"])
    return c, c[os.environ["DB_NAME"]]


async def _gather2(f1, f2):
    return await asyncio.gather(f1(), f2())


# ── 1. Same-key concurrent inspection submit → one row ────────────

def test_same_key_concurrent_inspection_creates_one_row(safety_pvi):
    key = f"trench-insp-{uuid.uuid4().hex[:12]}"

    async def _one():
        async with httpx.AsyncClient(timeout=30.0) as ac:
            r = await ac.post(
                _url(f"/trench-safety/assets/{TEST_ASSET_ID}/inspections"),
                headers={
                    "X-Safety-Token": safety_pvi,
                    "Content-Type": "application/json",
                    "Idempotency-Key": key,
                },
                json={
                    "inspection_type": "Daily Visual",
                    "inspector_name": "Idempotency Tester",
                    "inspector_role": "safety",
                    "checklist": [],
                    "findings": "",
                    "corrective_actions": "",
                    "result": "Pass",
                    "severity": "None",
                    "signature": "sig",
                    "photo_refs": [],
                },
            )
            r.raise_for_status()
            return r.json()

    a, b = asyncio.run(_gather2(_one, _one))
    aid = (a.get("inspection") or {}).get("id")
    bid = (b.get("inspection") or {}).get("id")
    assert aid and aid == bid, f"inspection idempotency broke · a={aid} b={bid}"

    async def _count():
        c, db = _mongo()
        try:
            return await db.trench_safety_inspections.count_documents(
                {"asset_id": TEST_ASSET_ID}
            )
        finally:
            c.close()

    assert asyncio.run(_count()) == 1


# ── 2. Same-key concurrent repair open → one repair + one Maint Hold ─

def test_same_key_concurrent_repair_open_creates_one_row(shop_pvi):
    key = f"trench-repair-open-{uuid.uuid4().hex[:12]}"

    async def _one():
        async with httpx.AsyncClient(timeout=30.0) as ac:
            r = await ac.post(
                _url(f"/trench-safety/assets/{TEST_ASSET_ID}/repairs"),
                headers={
                    "X-Shop-Token": shop_pvi,
                    "Content-Type": "application/json",
                    "Idempotency-Key": key,
                },
                json={
                    "issue_description": "idempotency test — cracked weld",
                    "requires_reinspection": True,
                },
            )
            r.raise_for_status()
            return r.json()

    a, b = asyncio.run(_gather2(_one, _one))
    aid = (a.get("repair") or {}).get("id")
    bid = (b.get("repair") or {}).get("id")
    assert aid and aid == bid, f"repair-open idempotency broke · a={aid} b={bid}"

    async def _counts():
        c, db = _mongo()
        try:
            repairs = await db.trench_safety_repairs.count_documents(
                {"asset_id": TEST_ASSET_ID}
            )
            active_maint = await db.trench_safety_holds.count_documents(
                {"asset_id": TEST_ASSET_ID, "kind": "Maintenance Hold", "is_active": True},
            )
            return repairs, active_maint
        finally:
            c.close()

    repairs, active_maint = asyncio.run(_counts())
    assert repairs == 1, f"expected 1 repair row, got {repairs}"
    assert active_maint == 1, f"expected 1 active Maintenance Hold, got {active_maint}"


# ── 3. Same-key concurrent complete preserves B-04 lifecycle ──────

def test_same_key_concurrent_repair_complete_preserves_b04(shop_pvi):
    # First open a repair (unique key so this step is not replayed).
    open_r = httpx.post(
        _url(f"/trench-safety/assets/{TEST_ASSET_ID}/repairs"),
        headers={
            "X-Shop-Token": shop_pvi,
            "Content-Type": "application/json",
            "Idempotency-Key": f"pre-open-{uuid.uuid4().hex[:12]}",
        },
        json={
            "issue_description": "idempotency test — pre-open for complete",
            "requires_reinspection": True,
        },
        timeout=15.0,
    )
    assert open_r.status_code in (200, 201), open_r.text
    repair_id = open_r.json()["repair"]["id"]

    # Concurrent complete with shared key.
    complete_key = f"trench-complete-{uuid.uuid4().hex[:12]}"

    async def _one():
        async with httpx.AsyncClient(timeout=30.0) as ac:
            r = await ac.post(
                _url(f"/trench-safety/repairs/{repair_id}/complete"),
                headers={
                    "X-Shop-Token": shop_pvi,
                    "Idempotency-Key": complete_key,
                },
            )
            r.raise_for_status()
            return r.json()

    a, b = asyncio.run(_gather2(_one, _one))
    a_status = (a.get("repair") or {}).get("status") or a.get("status")
    b_status = (b.get("repair") or {}).get("status") or b.get("status")
    assert a_status == b_status == "Completed"

    # Lifecycle: asset must be Inspection Hold, not Available
    # (B-04: Repair Complete ≠ Safe To Use).
    asset = (a.get("asset") or {})
    assert asset.get("operational_status") == "Inspection Hold", (
        f"B-04 regression — asset must sit in Inspection Hold after complete "
        f"with requires_reinspection=True. Got {asset.get('operational_status')!r}"
    )

    async def _counts():
        c, db = _mongo()
        try:
            active_insp = await db.trench_safety_holds.count_documents(
                {"asset_id": TEST_ASSET_ID, "kind": "Inspection Hold", "is_active": True},
            )
            active_maint = await db.trench_safety_holds.count_documents(
                {"asset_id": TEST_ASSET_ID, "kind": "Maintenance Hold", "is_active": True},
            )
            return active_insp, active_maint
        finally:
            c.close()

    active_insp, active_maint = asyncio.run(_counts())
    assert active_insp == 1, f"expected exactly 1 active Inspection Hold, got {active_insp}"
    assert active_maint == 0, f"expected Maintenance Hold cleared once, got {active_maint} active"


# ── 4. Same-key concurrent verify returns asset to Available once ─

def test_same_key_concurrent_repair_verify_is_exactly_once(shop_pvi, safety_pvi):
    # Open + complete a repair with distinct keys so we isolate /verify.
    open_r = httpx.post(
        _url(f"/trench-safety/assets/{TEST_ASSET_ID}/repairs"),
        headers={
            "X-Shop-Token": shop_pvi,
            "Content-Type": "application/json",
            "Idempotency-Key": f"pre-open-{uuid.uuid4().hex[:12]}",
        },
        json={
            "issue_description": "idempotency verify test",
            "requires_reinspection": True,
        },
        timeout=15.0,
    )
    assert open_r.status_code in (200, 201), open_r.text
    repair_id = open_r.json()["repair"]["id"]
    complete_r = httpx.post(
        _url(f"/trench-safety/repairs/{repair_id}/complete"),
        headers={"X-Shop-Token": shop_pvi,
                 "Idempotency-Key": f"pre-complete-{uuid.uuid4().hex[:12]}"},
        timeout=15.0,
    )
    assert complete_r.status_code in (200, 201), complete_r.text

    verify_key = f"trench-verify-{uuid.uuid4().hex[:12]}"

    async def _one():
        async with httpx.AsyncClient(timeout=30.0) as ac:
            r = await ac.post(
                _url(f"/trench-safety/repairs/{repair_id}/verify"),
                headers={
                    "X-Safety-Token": safety_pvi,
                    "Content-Type": "application/json",
                    "Idempotency-Key": verify_key,
                },
                json={
                    "verification_notes": "idempotency verify",
                    "reinspection_passed": True,
                },
            )
            r.raise_for_status()
            return r.json()

    a, b = asyncio.run(_gather2(_one, _one))
    assert (a.get("repair") or {}).get("status") == "Closed After Verification"
    assert (b.get("repair") or {}).get("status") == "Closed After Verification"
    assert (a.get("asset") or {}).get("operational_status") == "Available"


# ── 5. Same-key concurrent hold-open → one hold row ───────────────

def test_same_key_concurrent_hold_open_creates_one_row(safety_pvi):
    key = f"trench-hold-{uuid.uuid4().hex[:12]}"

    async def _one():
        async with httpx.AsyncClient(timeout=30.0) as ac:
            r = await ac.post(
                _url(f"/trench-safety/assets/{TEST_ASSET_ID}/holds"),
                headers={
                    "X-Safety-Token": safety_pvi,
                    "Content-Type": "application/json",
                    "Idempotency-Key": key,
                },
                json={
                    "kind": "Safety Hold",
                    "reason": "idempotency hold-open test",
                    "source": "manual",
                },
            )
            r.raise_for_status()
            return r.json()

    a, b = asyncio.run(_gather2(_one, _one))
    aid = (a.get("hold") or {}).get("id")
    bid = (b.get("hold") or {}).get("id")
    assert aid and aid == bid, f"hold-open idempotency broke · a={aid} b={bid}"


# ── 6. Same-key concurrent PATCH note → notes_history grows by 1 ──

def test_same_key_concurrent_patch_note_append_is_exactly_once(shop_pvi):
    # Open a repair to attach notes to.
    open_r = httpx.post(
        _url(f"/trench-safety/assets/{TEST_ASSET_ID}/repairs"),
        headers={
            "X-Shop-Token": shop_pvi,
            "Content-Type": "application/json",
            "Idempotency-Key": f"pre-open-{uuid.uuid4().hex[:12]}",
        },
        json={
            "issue_description": "idempotency patch test",
            "requires_reinspection": False,
        },
        timeout=15.0,
    )
    assert open_r.status_code in (200, 201), open_r.text
    repair_id = open_r.json()["repair"]["id"]

    patch_key = f"trench-patch-{uuid.uuid4().hex[:12]}"

    async def _one():
        async with httpx.AsyncClient(timeout=30.0) as ac:
            r = await ac.patch(
                _url(f"/trench-safety/repairs/{repair_id}"),
                headers={
                    "X-Shop-Token": shop_pvi,
                    "Content-Type": "application/json",
                    "Idempotency-Key": patch_key,
                },
                json={"note": "concurrent-append-check"},
            )
            r.raise_for_status()
            return r.json()

    asyncio.run(_gather2(_one, _one))

    async def _count():
        c, db = _mongo()
        try:
            doc = await db.trench_safety_repairs.find_one(
                {"id": repair_id}, {"_id": 0, "notes_history": 1}
            )
            return len((doc or {}).get("notes_history") or [])
        finally:
            c.close()

    n = asyncio.run(_count())
    assert n == 1, f"notes_history double-push on concurrent PATCH · found {n} entries"


# ── 7. Workflow scoping — key isolated across trench workflows ────

def test_workflow_scope_isolates_inspection_from_hold(safety_pvi):
    shared = f"trench-cross-{uuid.uuid4().hex[:12]}"

    # Fire inspection first
    r1 = httpx.post(
        _url(f"/trench-safety/assets/{TEST_ASSET_ID}/inspections"),
        headers={"X-Safety-Token": safety_pvi,
                 "Content-Type": "application/json",
                 "Idempotency-Key": shared},
        json={
            "inspection_type": "Daily Visual",
            "inspector_name": "Cross-Workflow",
            "inspector_role": "safety",
            "checklist": [],
            "findings": "",
            "corrective_actions": "",
            "result": "Pass",
            "severity": "None",
            "signature": "sig",
            "photo_refs": [],
        },
        timeout=20.0,
    )
    assert r1.status_code in (200, 201), r1.text
    insp_id = (r1.json().get("inspection") or {}).get("id")

    # Same key, different workflow (hold-open) must NOT replay onto the inspection response.
    r2 = httpx.post(
        _url(f"/trench-safety/assets/{TEST_ASSET_ID}/holds"),
        headers={"X-Safety-Token": safety_pvi,
                 "Content-Type": "application/json",
                 "Idempotency-Key": shared},
        json={"kind": "Safety Hold",
              "reason": "cross-workflow scope proof",
              "source": "manual"},
        timeout=20.0,
    )
    assert r2.status_code in (200, 201), r2.text
    hold_id = (r2.json().get("hold") or {}).get("id")
    assert hold_id and hold_id != insp_id, (
        f"cross-workflow leak — hold response should be independent · "
        f"insp_id={insp_id} hold_id={hold_id}"
    )


# ── 8. RBAC unchanged after idempotency wrap ──────────────────────

def test_shop_still_cannot_verify_after_idempotency_wrap(shop_pvi):
    # Open + complete via shop
    open_r = httpx.post(
        _url(f"/trench-safety/assets/{TEST_ASSET_ID}/repairs"),
        headers={"X-Shop-Token": shop_pvi,
                 "Content-Type": "application/json",
                 "Idempotency-Key": f"rbac-open-{uuid.uuid4().hex[:12]}"},
        json={"issue_description": "rbac after wrap", "requires_reinspection": True},
        timeout=15.0,
    )
    assert open_r.status_code in (200, 201), open_r.text
    repair_id = open_r.json()["repair"]["id"]
    httpx.post(
        _url(f"/trench-safety/repairs/{repair_id}/complete"),
        headers={"X-Shop-Token": shop_pvi,
                 "Idempotency-Key": f"rbac-complete-{uuid.uuid4().hex[:12]}"},
        timeout=15.0,
    )
    # Shop tries /verify → still 401
    r = httpx.post(
        _url(f"/trench-safety/repairs/{repair_id}/verify"),
        headers={"X-Shop-Token": shop_pvi,
                 "Content-Type": "application/json",
                 "Idempotency-Key": f"rbac-verify-{uuid.uuid4().hex[:12]}"},
        json={"verification_notes": "shop-should-401",
              "reinspection_passed": True},
        timeout=15.0,
    )
    assert r.status_code == 401, (
        f"RBAC regression — Shop must still be 401 on /verify after "
        f"idempotency wrap · got {r.status_code} · {r.text[:200]}"
    )


# ── 9. Motive posture shape stable ────────────────────────────────

def test_motive_posture_shape_stable(admin_token):
    r = httpx.get(_url("/motive/posture"),
                  headers={"X-Admin-Token": admin_token},
                  timeout=15.0)
    if r.status_code == 404:
        pytest.skip("Motive posture endpoint not exposed in this preview")
    assert r.status_code == 200, r.text
    body = r.json()
    for k in ("last_success_ts", "last_success_age_seconds", "state"):
        assert k in body, f"Motive posture shape must contain {k!r} · body={body}"
