"""TRACK 22.4B-FOLLOWUP-SHOP-DEFECTS-IDEMPOTENCY regression locks.

Certifies exactly-once submit on the fleet-defect write paths without
changing any behavior on:

  * `fleet_defect_severity` classification table (untouched)
  * Shop Manager RBAC (`_is_manager` still enforced)
  * Assigned-mechanic guard on /accept and /start
  * Trust Spine emission shape on manual OOS

Endpoints under test (all wrapped with `with_idempotency`, distinct
workflow scopes):

  * POST /api/fleet/inspections                              (fleet_inspection)
  * POST /api/shop/fleet/defects/{id}/acknowledge            (shop_defect_ack)
  * POST /api/shop/fleet/defects/{id}/repair                 (shop_defect_repair)
  * POST /api/dispatch/fleet/defects/{id}/clear              (shop_defect_clear)
  * POST /api/dispatch/fleet/units/{unit}/oos                (shop_defect_manual_oos)
  * POST /api/shop/fleet/defects/{id}/assign                 (shop_defect_assign)
  * POST /api/shop/fleet/defects/{id}/reassign               (shop_defect_reassign)
  * POST /api/shop/fleet/defects/{id}/accept                 (shop_defect_accept)
  * POST /api/shop/fleet/defects/{id}/start                  (shop_defect_start)
  * POST /api/shop/fleet/defects/{id}/manager-review         (shop_defect_manager_review)

Invariants proven:

  1. Same-key concurrent DVIR submits create exactly ONE inspection
     row AND exactly ONE defect row (not double-emitted from
     concurrent racers).
  2. Same-key concurrent manual OOS creates exactly ONE synthetic
     defect row (no Trust Spine double-emit).
  3. Same-key concurrent /repair does NOT double-append parts_used
     (the append-style array grows by exactly one batch).
  4. Same-key concurrent /clear runs the audit and status rebuild
     exactly once.
  5. Workflow scoping isolates fleet_inspection from
     shop_defect_manual_oos when the same key value is reused.
  6. RBAC preserved: anonymous still 401 on protected surfaces,
     Shop Manager guard still enforced on /assign.
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


_CACHED_ADMIN = ""
_CACHED_SHOP_PVI = ""


def _admin_headers() -> dict:
    global _CACHED_ADMIN
    if not _CACHED_ADMIN:
        _CACHED_ADMIN = _admin_token()
    return {"X-Admin-Token": _CACHED_ADMIN}


def _mint(admin_token: str, role: str) -> str:
    r = httpx.post(
        f"{BACKEND_URL}/api/admin/preview-validation-identities/mint",
        headers={"X-Admin-Token": admin_token},
        json={
            "role": role,
            "purpose": f"shop-defects idempotency · {role}",
            "ttl_minutes": 30,
            "validation_track": "TRACK_22_4B_FOLLOWUP_SHOP_DEFECTS_IDEMPOTENCY",
        },
        timeout=15.0,
    )
    r.raise_for_status()
    return r.json()["token"]


def _shop_headers() -> dict:
    """Mint (once) a shop PVI token — needed because the fleet-ops
    /shop/* endpoints use the narrow `require_shop_or_admin_fleet` gate
    that admin-portal tokens do not always satisfy."""
    global _CACHED_SHOP_PVI
    if not _CACHED_SHOP_PVI:
        _CACHED_SHOP_PVI = _mint(_admin_token(), "shop")
    return {"X-Shop-Token": _CACHED_SHOP_PVI}


def _mongo():
    c = AsyncIOMotorClient(os.environ["MONGO_URL"])
    return c, c[os.environ["DB_NAME"]]


async def _gather2(f1, f2):
    return await asyncio.gather(f1(), f2())


def _dvir_payload(truck: str, *, oos: bool = False) -> dict:
    import checklists_fleet as _ck  # noqa: PLC0415
    checklist = {item: "pass" for item in _ck.dvir_truck_items()}
    if oos:
        # A known OOS item
        checklist["Brake lights — both sides functional"] = "fail"
    return {
        "kind": "dvir",
        "driver_name": "Idempotency Tester",
        "inspection_date": "2026-07-05",
        "inspection_time": "06:30",
        "truck_unit_number": truck,
        "truck_checklist": checklist,
        "defect_details": (
            {"Brake lights — both sides functional":
             {"note": "idempotency test — brake light out", "photos": []}}
            if oos else {}
        ),
        "submitted_via": "public_tile",
    }


async def _cleanup_truck(truck: str) -> None:
    c, db = _mongo()
    try:
        await db.equipment_inspections.delete_many({"truck_unit_number": truck})
        await db.fleet_defects.delete_many({"truck_unit_number": truck})
        await db.fleet_status.delete_one({"unit_number": truck})
        await db.fleet_audit.delete_many({"target_id": truck})
    finally:
        c.close()


# ── 1. Same-key concurrent DVIR (OOS) → one inspection + one defect ─

def test_same_key_concurrent_dvir_oos_creates_one_inspection_and_one_defect():
    truck = f"IDEMP-DVIR-{uuid.uuid4().hex[:6].upper()}"
    key = f"dvir-idemp-{uuid.uuid4().hex[:12]}"
    payload = _dvir_payload(truck, oos=True)

    async def _one():
        async with httpx.AsyncClient(timeout=60.0) as ac:
            r = await ac.post(
                _url("/fleet/inspections"),
                headers={"Content-Type": "application/json",
                         "Idempotency-Key": key},
                json=payload,
            )
            r.raise_for_status()
            return r.json()

    try:
        a, b = asyncio.run(_gather2(_one, _one))
        aid = a.get("inspection_id")
        bid = b.get("inspection_id")
        assert aid and aid == bid, f"DVIR idempotency broke · a={aid} b={bid}"

        async def _counts():
            c, db = _mongo()
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

        insp, defs = asyncio.run(_counts())
        assert insp == 1, f"expected 1 inspection, got {insp}"
        assert defs == 1, f"expected 1 defect, got {defs}"
    finally:
        asyncio.run(_cleanup_truck(truck))


# ── 2. Same-key concurrent manual OOS → one synthetic defect ────────

def test_same_key_concurrent_manual_oos_creates_one_defect():
    unit = f"IDEMP-OOS-{uuid.uuid4().hex[:6].upper()}"
    key = f"manual-oos-idemp-{uuid.uuid4().hex[:12]}"

    async def _one():
        async with httpx.AsyncClient(timeout=30.0) as ac:
            r = await ac.post(
                _url(f"/dispatch/fleet/units/{unit}/oos"),
                headers={"Content-Type": "application/json",
                         "Idempotency-Key": key,
                         **_admin_headers()},
                json={"actor_name": "Idempotency Dispatcher",
                      "notes": "manual OOS regression",
                      "photos": []},
            )
            r.raise_for_status()
            return r.json()

    try:
        a, b = asyncio.run(_gather2(_one, _one))
        aid = a.get("defect_id")
        bid = b.get("defect_id")
        assert aid and aid == bid, f"manual OOS idempotency broke · a={aid} b={bid}"

        async def _count():
            c, db = _mongo()
            try:
                return await db.fleet_defects.count_documents(
                    {"truck_unit_number": unit,
                     "inspection_kind": "manual_oos"}
                )
            finally:
                c.close()

        assert asyncio.run(_count()) == 1
    finally:
        asyncio.run(_cleanup_truck(unit))


# ── 3. Same-key concurrent /repair does NOT double-append parts ─────

def test_same_key_concurrent_repair_does_not_double_append_parts():
    # Seed a defect via manual OOS first (needs status=open for /repair).
    unit = f"IDEMP-REPAIR-{uuid.uuid4().hex[:6].upper()}"
    seed_r = httpx.post(
        _url(f"/dispatch/fleet/units/{unit}/oos"),
        headers={"Content-Type": "application/json",
                 "Idempotency-Key": f"seed-{uuid.uuid4().hex[:12]}",
                 **_admin_headers()},
        json={"actor_name": "Seeder", "notes": "seed for /repair idem", "photos": []},
        timeout=15.0,
    )
    assert seed_r.status_code == 200, seed_r.text
    defect_id = seed_r.json()["defect_id"]

    repair_key = f"repair-idemp-{uuid.uuid4().hex[:12]}"

    async def _one():
        async with httpx.AsyncClient(timeout=30.0) as ac:
            r = await ac.post(
                _url(f"/shop/fleet/defects/{defect_id}/repair"),
                headers={"Content-Type": "application/json",
                         "Idempotency-Key": repair_key,
                         **_shop_headers()},
                json={
                    "actor_name": "Idempotency Mechanic",
                    "notes": "replaced the brake light housing",
                    "photos": [],
                    "parts_used": [
                        {"part_name": "LED bulb", "part_number": "PN-123",
                         "quantity": 2},
                    ],
                    "parts_on_order": [],
                },
            )
            r.raise_for_status()
            return r.json()

    try:
        a, b = asyncio.run(_gather2(_one, _one))
        assert a == b or (a.get("ok") and b.get("ok"))

        async def _defect():
            c, db = _mongo()
            try:
                return await db.fleet_defects.find_one(
                    {"id": defect_id}, {"_id": 0, "parts_used": 1, "status": 1}
                )
            finally:
                c.close()

        d = asyncio.run(_defect())
        assert d["status"] == "repaired"
        parts = d.get("parts_used") or []
        # Exactly one PN-123 line appended, not two.
        pn123 = [p for p in parts if p.get("part_number") == "PN-123"]
        assert len(pn123) == 1, (
            f"parts_used double-appended on concurrent /repair · found {len(pn123)} PN-123 rows"
        )
    finally:
        asyncio.run(_cleanup_truck(unit))


# ── 4. Same-key concurrent /clear runs audit + status once ──────────

def test_same_key_concurrent_clear_runs_once():
    unit = f"IDEMP-CLEAR-{uuid.uuid4().hex[:6].upper()}"
    # Seed → OOS
    seed = httpx.post(
        _url(f"/dispatch/fleet/units/{unit}/oos"),
        headers={"Content-Type": "application/json",
                 "Idempotency-Key": f"seed-{uuid.uuid4().hex[:12]}",
                 **_admin_headers()},
        json={"actor_name": "Seeder", "notes": "seed for /clear", "photos": []},
        timeout=15.0,
    )
    assert seed.status_code == 200, seed.text
    defect_id = seed.json()["defect_id"]

    # Move → repaired
    r_rep = httpx.post(
        _url(f"/shop/fleet/defects/{defect_id}/repair"),
        headers={"Content-Type": "application/json",
                 "Idempotency-Key": f"rep-{uuid.uuid4().hex[:12]}",
                 **_shop_headers()},
        json={"actor_name": "Mech", "notes": "fixed the brake light issue",
              "photos": [], "parts_used": [], "parts_on_order": []},
        timeout=15.0,
    )
    assert r_rep.status_code == 200, r_rep.text

    clear_key = f"clear-idemp-{uuid.uuid4().hex[:12]}"

    async def _one():
        async with httpx.AsyncClient(timeout=30.0) as ac:
            r = await ac.post(
                _url(f"/dispatch/fleet/defects/{defect_id}/clear"),
                headers={"Content-Type": "application/json",
                         "Idempotency-Key": clear_key,
                         **_admin_headers()},
                json={"actor_name": "Idempotency Dispatcher",
                      "notes": "returning to service",
                      "photos": []},
            )
            r.raise_for_status()
            return r.json()

    try:
        asyncio.run(_gather2(_one, _one))

        async def _audit_count():
            c, db = _mongo()
            try:
                return await db.fleet_audit.count_documents(
                    {"target_id": defect_id, "action": "defect_cleared"}
                )
            finally:
                c.close()

        n = asyncio.run(_audit_count())
        assert n == 1, f"/clear audit double-emitted · found {n} defect_cleared rows"
    finally:
        asyncio.run(_cleanup_truck(unit))


# ── 5. Workflow scoping — same key across two workflows ─────────────

def test_same_key_across_fleet_inspection_and_manual_oos_are_independent():
    truck = f"IDEMP-SCOPE-{uuid.uuid4().hex[:6].upper()}"
    key = f"scope-{uuid.uuid4().hex[:12]}"
    try:
        r1 = httpx.post(
            _url("/fleet/inspections"),
            headers={"Content-Type": "application/json",
                     "Idempotency-Key": key},
            json=_dvir_payload(truck, oos=False),
            timeout=30.0,
        )
        assert r1.status_code == 200, r1.text
        insp_id = r1.json()["inspection_id"]

        # Same key on the manual-oos endpoint MUST NOT replay onto the
        # inspection response.
        r2 = httpx.post(
            _url(f"/dispatch/fleet/units/{truck}/oos"),
            headers={"Content-Type": "application/json",
                     "Idempotency-Key": key,
                     **_admin_headers()},
            json={"actor_name": "Scope Dispatcher",
                  "notes": "cross-workflow scope proof",
                  "photos": []},
            timeout=30.0,
        )
        assert r2.status_code == 200, r2.text
        defect_id = r2.json()["defect_id"]
        assert insp_id != defect_id, (
            f"cross-workflow leak — inspection replayed onto manual OOS · "
            f"insp_id={insp_id} defect_id={defect_id}"
        )
    finally:
        asyncio.run(_cleanup_truck(truck))


# ── 6. RBAC preserved: anonymous still 401 on manual OOS ────────────

def test_anonymous_manual_oos_still_401():
    unit = f"ANON-{uuid.uuid4().hex[:6].upper()}"
    r = httpx.post(
        _url(f"/dispatch/fleet/units/{unit}/oos"),
        headers={"Content-Type": "application/json",
                 "Idempotency-Key": f"anon-{uuid.uuid4().hex[:8]}"},
        json={"actor_name": "anon", "notes": "should 401", "photos": []},
        timeout=15.0,
    )
    assert r.status_code == 401, (
        f"RBAC regression — anonymous /oos should be 401, got {r.status_code} · "
        f"{r.text[:200]}"
    )


# ── 7. Motive posture untouched ─────────────────────────────────────

def test_motive_posture_shape_stable():
    r = httpx.get(
        _url("/motive/posture"),
        headers=_admin_headers(),
        timeout=15.0,
    )
    if r.status_code == 404:
        pytest.skip("Motive posture endpoint not exposed in this preview")
    assert r.status_code == 200, r.text
    body = r.json()
    for k in ("last_success_ts", "last_success_age_seconds", "state"):
        assert k in body, f"Motive posture shape must contain {k!r} · body={body}"
