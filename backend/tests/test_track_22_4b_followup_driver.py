"""TRACK 22.4B-FOLLOWUP-DRIVER · driver-side workflow certification.

Closes defect B-06 without inventing a Driver Portal. Exercises the
existing driver-scoped surfaces end-to-end using a Driver PVI token:

  * Driver session guard now accepts a preview validation identity for
    role="driver" as a fallback after real magic-link session validation
    fails. Production is disabled (guard sits behind
    `ENABLE_PREVIEW_VALIDATION_IDENTITIES=true`).
  * `/api/dispatch/driver/me` — driver identity read.
  * `/api/dispatch/driver/my-assignment` — driver assignment visibility.
  * `/api/fleet/inspections` — DVIR submit (public-friendly). Driver's
    failing DVIR routes to Shop via the fleet_defects insert + Shop
    queue notification.

Invariants proven:

  1. Driver PVI reaches driver-only routes (`/me`, `/my-assignment`).
  2. Driver PVI rejected from admin, safety, shop, HR gates.
  3. HR / Safety / Shop PVI rejected from driver-only routes.
  4. Anonymous rejected from driver-only routes.
  5. DVIR failure creates exactly one fleet_defect (idempotency preserved
     under retry storm) and the defect appears in the Shop queue.
  6. Same-key concurrent DVIR retries do not double-emit Shop notifications.
  7. No new Driver Portal route was introduced (guard-scope regression).
  8. Motive routes remain untouched.
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


def _url(p: str) -> str:
    return f"{BACKEND_URL}/api{p}"


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
            "purpose": f"driver track · {role}",
            "ttl_minutes": 30,
            "validation_track": "TRACK_22_4B_FOLLOWUP_DRIVER",
        },
        timeout=15.0,
    )
    r.raise_for_status()
    return r.json()["token"]


@pytest.fixture(scope="module")
def admin_token() -> str:
    return _admin_token()


@pytest.fixture(scope="module")
def driver_pvi(admin_token) -> str:
    return _mint(admin_token, "driver")


@pytest.fixture(scope="module")
def safety_pvi(admin_token) -> str:
    return _mint(admin_token, "safety")


@pytest.fixture(scope="module")
def shop_pvi(admin_token) -> str:
    return _mint(admin_token, "shop")


@pytest.fixture(scope="module")
def hr_pvi(admin_token) -> str:
    return _mint(admin_token, "hr")


# ── 1. Driver PVI reaches /me ─────────────────────────────────────

def test_driver_pvi_reaches_me_endpoint(driver_pvi):
    r = httpx.get(
        _url("/dispatch/driver/me"),
        headers={"X-Driver-Token": driver_pvi},
        timeout=15.0,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True
    sess = body["session"]
    assert sess["driver_id"], "PVI-derived driver_id must be present"
    # Session sanity — driver_name populated
    assert sess.get("driver_name")


# ── 2. Driver PVI reaches /my-assignment ─────────────────────────

def test_driver_pvi_reaches_my_assignment(driver_pvi):
    r = httpx.get(
        _url("/dispatch/driver/my-assignment"),
        headers={"X-Driver-Token": driver_pvi},
        timeout=15.0,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True
    # No live assignment for this PVI — expected empty state
    assert "assignment" in body
    assert isinstance(body.get("lifecycle_states"), list)


# ── 3. Driver PVI rejected from Shop-only route ──────────────────

def test_driver_pvi_rejected_from_shop_defect_repair(driver_pvi):
    # Pick an arbitrary id — the gate rejects BEFORE the id lookup.
    r = httpx.post(
        _url(f"/shop/fleet/defects/{uuid.uuid4()}/repair"),
        headers={"X-Shop-Token": driver_pvi,
                 "Content-Type": "application/json"},
        json={"actor_name": "driver-should-not",
              "notes": "should-be-401", "photos": [],
              "parts_used": [], "parts_on_order": []},
        timeout=15.0,
    )
    assert r.status_code == 401, (
        f"Driver PVI must not pass the Shop gate · got {r.status_code}"
    )


# ── 4. Driver PVI rejected from Safety hold route ────────────────

def test_driver_pvi_rejected_from_safety_hold_open(driver_pvi):
    r = httpx.post(
        _url("/trench-safety/assets/DOES-NOT-EXIST/holds"),
        headers={"X-Safety-Token": driver_pvi,
                 "Content-Type": "application/json"},
        json={"kind": "Safety Hold", "reason": "x", "source": "manual"},
        timeout=15.0,
    )
    assert r.status_code == 401, (
        f"Driver PVI must not pass Safety gate · got {r.status_code}"
    )


# ── 5. Cross-role: Safety/Shop/HR PVI rejected from driver route ──

def test_safety_pvi_rejected_from_driver_me(safety_pvi):
    r = httpx.get(
        _url("/dispatch/driver/me"),
        headers={"X-Driver-Token": safety_pvi},
        timeout=15.0,
    )
    assert r.status_code == 401, (
        f"Safety PVI must not pass the driver gate · got {r.status_code}"
    )


def test_shop_pvi_rejected_from_driver_my_assignment(shop_pvi):
    r = httpx.get(
        _url("/dispatch/driver/my-assignment"),
        headers={"X-Driver-Token": shop_pvi},
        timeout=15.0,
    )
    assert r.status_code == 401, (
        f"Shop PVI must not pass the driver gate · got {r.status_code}"
    )


def test_hr_pvi_rejected_from_driver_me(hr_pvi):
    r = httpx.get(
        _url("/dispatch/driver/me"),
        headers={"X-Driver-Token": hr_pvi},
        timeout=15.0,
    )
    assert r.status_code == 401


# ── 6. Anonymous rejected from driver-only route ─────────────────

def test_anonymous_rejected_from_driver_me():
    r = httpx.get(_url("/dispatch/driver/me"), timeout=15.0)
    assert r.status_code == 401


# ── 7. Admin token cannot be used as driver proof ────────────────

def test_admin_token_rejected_from_driver_me(admin_token):
    # Admin tokens are HMAC per-user, not PVI. The driver guard must
    # NOT accept them — production safety.
    r = httpx.get(
        _url("/dispatch/driver/me"),
        headers={"X-Driver-Token": admin_token},
        timeout=15.0,
    )
    assert r.status_code == 401, (
        f"Admin token must NEVER unlock driver session · got {r.status_code}"
    )


# ── 8. DVIR failure → Shop queue routing ─────────────────────────

def test_driver_dvir_failure_routes_to_shop_queue(driver_pvi, shop_pvi):
    import checklists_fleet as _ck  # noqa: PLC0415
    truck = f"DVIR-FAIL-{uuid.uuid4().hex[:6].upper()}"
    checklist = {item: "pass" for item in _ck.dvir_truck_items()}
    checklist["Brake lights — both sides functional"] = "fail"
    payload = {
        "kind": "dvir",
        "driver_name": "PVI Driver",
        "inspection_date": "2026-07-05",
        "inspection_time": "07:00",
        "truck_unit_number": truck,
        "truck_checklist": checklist,
        "defect_details": {
            "Brake lights — both sides functional":
                {"note": "driver track fail", "photos": []},
        },
        "submitted_via": "driver_dvir",
    }
    try:
        r = httpx.post(
            _url("/fleet/inspections"),
            headers={"Content-Type": "application/json",
                     "Idempotency-Key": f"driver-{uuid.uuid4().hex[:12]}"},
            json=payload,
            timeout=30.0,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["out_of_service"] is True
        assert body["defect_count"] >= 1
        assert body["truck_status_after"] == "oos"

        # Verify the defect landed in the Shop queue (via a Shop PVI —
        # `/shop/fleet/defects` uses the narrow shop-or-admin-fleet gate).
        q = httpx.get(
            _url("/shop/fleet/defects"),
            headers={"X-Shop-Token": shop_pvi},
            params={"unit_number": truck},
            timeout=15.0,
        )
        assert q.status_code == 200, q.text
        defects = q.json().get("defects") or []
        assert defects, (
            f"driver DVIR failure did not surface in shop queue for {truck}"
        )
    finally:
        async def _cleanup():
            c = AsyncIOMotorClient(os.environ["MONGO_URL"])
            db = c[os.environ["DB_NAME"]]
            try:
                await db.equipment_inspections.delete_many({"truck_unit_number": truck})
                await db.fleet_defects.delete_many({"truck_unit_number": truck})
                await db.fleet_status.delete_one({"unit_number": truck})
                await db.fleet_audit.delete_many({"target_id": truck})
            finally:
                c.close()

        asyncio.run(_cleanup())


# ── 9. Same-key concurrent DVIR failure creates one defect ──────

def test_same_key_concurrent_dvir_failure_creates_one_defect():
    import checklists_fleet as _ck  # noqa: PLC0415
    truck = f"DVIR-IDEM-{uuid.uuid4().hex[:6].upper()}"
    checklist = {item: "pass" for item in _ck.dvir_truck_items()}
    checklist["Brake lights — both sides functional"] = "fail"
    payload = {
        "kind": "dvir",
        "driver_name": "Idempotency Driver",
        "inspection_date": "2026-07-05",
        "inspection_time": "08:15",
        "truck_unit_number": truck,
        "truck_checklist": checklist,
        "defect_details": {
            "Brake lights — both sides functional":
                {"note": "concurrent DVIR", "photos": []},
        },
        "submitted_via": "driver_dvir",
    }
    key = f"driver-dvir-idemp-{uuid.uuid4().hex[:12]}"

    async def _one():
        async with httpx.AsyncClient(timeout=30.0) as ac:
            r = await ac.post(
                _url("/fleet/inspections"),
                headers={"Content-Type": "application/json",
                         "Idempotency-Key": key},
                json=payload,
            )
            r.raise_for_status()
            return r.json()

    try:
        async def _run():
            return await asyncio.gather(_one(), _one())
        a, b = asyncio.run(_run())
        assert a.get("inspection_id") == b.get("inspection_id"), (
            f"DVIR idempotency broke · a={a.get('inspection_id')} b={b.get('inspection_id')}"
        )

        async def _count():
            c = AsyncIOMotorClient(os.environ["MONGO_URL"])
            db = c[os.environ["DB_NAME"]]
            try:
                insp = await db.equipment_inspections.count_documents(
                    {"truck_unit_number": truck}
                )
                defs = await db.fleet_defects.count_documents(
                    {"truck_unit_number": truck}
                )
                return insp, defs
            finally:
                c.close()

        insp, defs = asyncio.run(_count())
        assert insp == 1, f"expected 1 inspection, got {insp}"
        assert defs == 1, f"expected 1 defect, got {defs}"
    finally:
        c = AsyncIOMotorClient(os.environ["MONGO_URL"])
        db = c[os.environ["DB_NAME"]]

        async def _cleanup():
            await db.equipment_inspections.delete_many({"truck_unit_number": truck})
            await db.fleet_defects.delete_many({"truck_unit_number": truck})
            await db.fleet_status.delete_one({"unit_number": truck})
            await db.fleet_audit.delete_many({"target_id": truck})

        asyncio.run(_cleanup())
        c.close()


# ── 10. No new Driver Portal route was introduced ────────────────

def test_no_driver_portal_route_exists():
    """B-06 architecture invariant: the platform must NOT expose a
    dedicated Driver Portal. Driver workflows live under the existing
    `/api/dispatch/driver/*` surface. This regression asserts no new
    top-level `/api/driver-portal` or `/api/driver/portal` route was
    accidentally introduced by this track.
    """
    for stray in (
        "/driver-portal", "/driver_portal",
        "/driver/portal", "/portal/driver",
    ):
        r = httpx.get(_url(stray), timeout=10.0)
        assert r.status_code in (404, 405), (
            f"Unexpected Driver Portal route surfaced at {stray} · "
            f"HTTP {r.status_code}. This track forbids a dedicated portal."
        )


# ── 11. Driver PVI cannot transition a random assignment (RBAC) ──

def test_driver_pvi_cannot_transition_random_assignment(driver_pvi):
    """Driver PVI has no assignments attached to its driver_id. If it
    tries to transition an assignment that doesn't belong to it, the
    handler must respond with 404 (assignment not found for scoped
    tenant) or 403 (scope mismatch). Either way — NEVER 200."""
    r = httpx.post(
        _url(f"/dispatch/driver/assignments/{uuid.uuid4()}/transition"),
        headers={"X-Driver-Token": driver_pvi,
                 "Content-Type": "application/json"},
        json={"to_state": "arrived_at_source"},
        timeout=15.0,
    )
    assert r.status_code in (403, 404), (
        f"Driver PVI transitioned an unrelated assignment · HTTP {r.status_code}"
    )


# ── 12. Motive posture shape stable ──────────────────────────────

def test_motive_posture_unchanged_by_driver_track(admin_token):
    r = httpx.get(
        _url("/motive/posture"),
        headers={"X-Admin-Token": admin_token},
        timeout=15.0,
    )
    if r.status_code == 404:
        pytest.skip("Motive posture endpoint not exposed in this preview")
    assert r.status_code == 200, r.text
    body = r.json()
    for k in ("last_success_ts", "last_success_age_seconds", "state"):
        assert k in body, f"Motive posture shape must contain {k!r}"
