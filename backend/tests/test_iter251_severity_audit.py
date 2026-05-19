"""iter251 · Severity Audit + Controlled Defect Simulations + Cross-Dept
Workflow Validation.

Operator-approved governance cycle BEFORE Phase B. Three buckets:

  (1) Severity audit endpoint validates table integrity (no missing
      classifications · no orphans · uncertain items surfaced)
  (2) Controlled defect simulations · realistic field scenarios drive
      OOS logic + dispatch visibility + trailer scoping + shop routing
      + safety escalation + audit-trail integrity
  (3) Cross-department workflow validation · Dispatch sees status flips
      · Shop sees defect queue · Safety sees only safety-critical
      categories · all from the same submission

This is the proof-of-life before any driver UX rolls out.
"""
from __future__ import annotations

import os
import uuid
import asyncio
import urllib.request
import urllib.error

import pytest
import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path="/app/backend/.env")

from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402

import fleet_defect_severity as _sev  # noqa: E402
import checklists_fleet as _ck  # noqa: E402


def _read_kv(p, k):
    try:
        for line in open(p):
            if line.startswith(f"{k}="):
                return line.split("=", 1)[1].strip().strip('"').rstrip("/")
    except Exception:
        pass
    return ""


URL = (
    _read_kv("/app/frontend/.env", "REACT_APP_BACKEND_URL")
    or os.environ.get("REACT_APP_BACKEND_URL", "")
).rstrip("/")


def _db():
    cli = AsyncIOMotorClient(os.environ["MONGO_URL"])
    return cli[os.environ["DB_NAME"]]


@pytest.fixture(scope="module")
def admin_token():
    if not URL:
        pytest.skip("REACT_APP_BACKEND_URL not configured")
    r = requests.post(
        f"{URL}/api/admin/login",
        json={"password": os.environ.get("ADMIN_PASSWORD_E2E", "MASCI1982!")},
        timeout=15,
    )
    assert r.status_code == 200
    return r.json()["token"]


# ─── 1 · Severity audit endpoint ─────────────────────────────────────
def test_severity_audit_anon_blocked():
    if not URL:
        pytest.skip()
    req = urllib.request.Request(f"{URL}/api/admin/fleet/severity-audit")
    try:
        urllib.request.urlopen(req, timeout=10)
        pytest.fail("anon should be blocked")
    except urllib.error.HTTPError as e:
        assert e.code in (401, 403)


def test_severity_audit_required_shape(admin_token):
    if not URL:
        pytest.skip()
    r = requests.get(
        f"{URL}/api/admin/fleet/severity-audit",
        headers={"X-Admin-Token": admin_token},
        timeout=20,
    )
    assert r.status_code == 200, r.text[:200]
    d = r.json()
    for k in ("verdict", "verdict_reason", "severity_table_version",
              "total_severity_entries", "total_oos", "total_monitor",
              "oos_to_monitor_ratio", "per_kind_coverage",
              "category_breakdown", "missing_severity", "orphan_severity",
              "missing_metadata", "orphan_metadata",
              "uncertain_items_pending_review", "scope_note"):
        assert k in d, f"missing audit key: {k!r}"
    assert d["verdict"] in (
        "FAIL", "NEEDS_REVIEW", "NEEDS_CLEANUP", "READY_FOR_SAFETY_SIGNOFF",
    )


def test_severity_audit_no_missing_severity(admin_token):
    """ZERO missing severity is a hard pre-deploy gate · every checklist
    item must classify."""
    if not URL:
        pytest.skip()
    r = requests.get(
        f"{URL}/api/admin/fleet/severity-audit",
        headers={"X-Admin-Token": admin_token},
        timeout=20,
    )
    d = r.json()
    assert d["missing_severity"] == [], (
        f"checklist items missing severity (would HTTP 400 in production): "
        f"{d['missing_severity']}"
    )


def test_severity_audit_full_coverage_per_kind(admin_token):
    if not URL:
        pytest.skip()
    r = requests.get(
        f"{URL}/api/admin/fleet/severity-audit",
        headers={"X-Admin-Token": admin_token},
        timeout=20,
    )
    d = r.json()
    for kind, stats in d["per_kind_coverage"].items():
        assert stats["coverage_pct"] == 100.0, (
            f"kind={kind!r} coverage = {stats['coverage_pct']}% · must be 100%"
        )


def test_severity_audit_no_missing_metadata(admin_token):
    """Every severity entry must have rationale + regulation_ref so the
    reasoning survives the original author."""
    if not URL:
        pytest.skip()
    r = requests.get(
        f"{URL}/api/admin/fleet/severity-audit",
        headers={"X-Admin-Token": admin_token},
        timeout=20,
    )
    d = r.json()
    assert d["missing_metadata"] == [], (
        f"severity entries missing metadata: {d['missing_metadata']}"
    )


def test_severity_audit_no_orphan_metadata(admin_token):
    """Metadata entry without a corresponding severity row = drift."""
    if not URL:
        pytest.skip()
    r = requests.get(
        f"{URL}/api/admin/fleet/severity-audit",
        headers={"X-Admin-Token": admin_token},
        timeout=20,
    )
    d = r.json()
    assert d["orphan_metadata"] == [], (
        f"orphan metadata entries: {d['orphan_metadata']}"
    )


def test_severity_audit_table_is_conservative(admin_token):
    """The table must bias toward OOS over monitor · operator goal."""
    if not URL:
        pytest.skip()
    r = requests.get(
        f"{URL}/api/admin/fleet/severity-audit",
        headers={"X-Admin-Token": admin_token},
        timeout=20,
    )
    d = r.json()
    # We want at least 1.5x more OOS than monitor · table is currently
    # ~2.46x. If this drops below 1.5 it suggests over-classification of
    # safety-critical items as monitor.
    assert d["oos_to_monitor_ratio"] is None or d["oos_to_monitor_ratio"] >= 1.5, (
        f"oos-to-monitor ratio {d['oos_to_monitor_ratio']} below conservative threshold 1.5"
    )


# ─── 2 · Controlled defect simulations ──────────────────────────────
# Each simulation submits a realistic DVIR and asserts the operational
# outcome (status flip · defect counts · category routing).

REALISTIC_SCENARIOS = [
    {
        "name": "tractor_brake_failure",
        "fail_items": ["Service brakes — apply firmly · stop straight · no pulling"],
        "expected_severity": "oos",
        "expected_truck_status": "oos",
        "expected_category": "brakes",
        "safety_visible": False,
    },
    {
        "name": "hydraulic_leak_major",
        "fail_items": ["Hydraulic system — no active drip · no leak below MIN reservoir · no leak on bed-lift / boom / outrigger / brake-assist circuit"],
        "expected_severity": "oos",
        "expected_truck_status": "oos",
        "expected_category": "hydraulic",
        "safety_visible": False,
    },
    {
        "name": "backup_alarm_failure",
        "fail_items": ["Backup alarm — audible when reverse engaged"],
        "expected_severity": "oos",
        "expected_truck_status": "oos",
        "expected_category": "alarms",
        "safety_visible": True,  # alarms is in safety scope
    },
    {
        "name": "raised_bed_alarm_failure",
        "fail_items": ["Raised-bed alarm — audible when bed raised"],
        "expected_severity": "oos",
        "expected_truck_status": "oos",
        "expected_category": "alarms",
        "safety_visible": True,
    },
    {
        "name": "fire_extinguisher_missing",
        "fail_items": ["Fire extinguisher — present · charged · sealed · tag current"],
        "expected_severity": "oos",
        "expected_truck_status": "oos",
        "expected_category": "emergency_equipment",
        "safety_visible": True,
    },
    {
        "name": "low_tire_tread_steer",
        "fail_items": ["Steer tire tread depth — ≥ 4/32\" across full width"],
        "expected_severity": "oos",
        "expected_truck_status": "oos",
        "expected_category": "tires",
        "safety_visible": False,
    },
    {
        "name": "cracked_mirror_cosmetic",
        "fail_items": ["Mirror — minor crack / chip with visible image"],
        "expected_severity": "monitor",
        "expected_truck_status": "defect_open",
        "expected_category": "mirrors",
        "safety_visible": False,
    },
    {
        "name": "air_leak_audible",
        "fail_items": ["Airlines / gladhands — no audible leaks · seals intact"],
        "expected_severity": "oos",
        "expected_truck_status": "oos",
        "expected_category": "air_system",
        "safety_visible": False,
    },
    {
        "name": "brake_light_failure",
        "fail_items": ["Brake lights — both sides functional"],
        "expected_severity": "oos",
        "expected_truck_status": "oos",
        "expected_category": "lights",
        "safety_visible": True,
    },
    {
        "name": "cosmetic_body_damage",
        "fail_items": ["Body — cosmetic dings · scrapes · paint"],
        "expected_severity": "monitor",
        "expected_truck_status": "defect_open",
        "expected_category": "body",
        "safety_visible": False,
    },
]


@pytest.mark.parametrize("scenario", REALISTIC_SCENARIOS, ids=[s["name"] for s in REALISTIC_SCENARIOS])
def test_realistic_field_scenarios(scenario, admin_token):
    """One scenario per realistic operator-named field event. Submits a
    DVIR · asserts the defect classification + truck status flip + (if
    applicable) safety-dashboard visibility."""
    if not URL:
        pytest.skip()
    truck = f"SIM-{scenario['name'][:10]}-{uuid.uuid4().hex[:5]}"
    checklist = {item: "pass" for item in _ck.dvir_truck_items()}
    for fail in scenario["fail_items"]:
        checklist[fail] = "fail"

    payload = {
        "kind": "dvir",
        "driver_name": f"Sim Driver {scenario['name']}",
        "inspection_date": "2024-08-15",
        "inspection_time": "07:00",
        "truck_unit_number": truck,
        "truck_checklist": checklist,
        "defect_details": {f: {"note": "simulated", "photos": []}
                           for f in scenario["fail_items"]},
        "submitted_via": "public_tile",
    }
    try:
        r = requests.post(f"{URL}/api/fleet/inspections", json=payload, timeout=30)
        assert r.status_code == 200, r.text[:300]
        out = r.json()
        assert out["truck_status_after"] == scenario["expected_truck_status"], (
            f"scenario {scenario['name']!r}: status flip expected="
            f"{scenario['expected_truck_status']!r} got={out['truck_status_after']!r}"
        )

        async def _verify():
            db = _db()
            d = await db.fleet_defects.find_one(
                {"truck_unit_number": truck}, {"_id": 0}
            )
            assert d is not None, "no defect row created"
            assert d["severity"] == scenario["expected_severity"]
            assert d["category"] == scenario["expected_category"]
            assert d["status"] == "open"
            assert d["inspection_kind"] == "dvir"
            # Audit captured this submission
            audits = await db.fleet_audit.find(
                {"target_id": out["inspection_id"]}, {"_id": 0}
            ).to_list(None)
            assert any(a["action"] == "fleet_inspection_submitted" for a in audits)
            return d
        defect = asyncio.run(_verify())

        # Safety dashboard visibility check
        if scenario["safety_visible"]:
            r2 = requests.get(
                f"{URL}/api/safety/fleet/emergency-equipment",
                headers={"X-Admin-Token": admin_token},
                timeout=15,
            )
            assert r2.status_code == 200
            safety_defects = r2.json()["defects"]
            assert any(sd["id"] == defect["id"] for sd in safety_defects), (
                f"scenario {scenario['name']!r}: defect should be visible "
                f"to Safety but is not"
            )
        else:
            # Non-safety categories should NOT leak into safety view
            r2 = requests.get(
                f"{URL}/api/safety/fleet/emergency-equipment",
                headers={"X-Admin-Token": admin_token},
                timeout=15,
            )
            assert r2.status_code == 200
            safety_defects = r2.json()["defects"]
            assert not any(sd["id"] == defect["id"] for sd in safety_defects), (
                f"scenario {scenario['name']!r}: non-safety category "
                f"({scenario['expected_category']!r}) leaked into Safety view"
            )
    finally:
        async def _cleanup():
            db = _db()
            await db.equipment_inspections.delete_many({"truck_unit_number": truck})
            await db.fleet_defects.delete_many({"truck_unit_number": truck})
            await db.fleet_status.delete_one({"unit_number": truck})
            await db.fleet_audit.delete_many({"target_id": truck})
            # also kill any per-defect audit chain we left
        asyncio.run(_cleanup())


# ─── 3 · Trailer-only scoping (operator-confirmed rule) ─────────────
def test_trailer_only_lighting_does_not_oos_tractor(admin_token):
    """Operator-confirmed: a trailer-only defect must NOT OOS the
    tractor · dispatch can reassign the tractor to a different trailer."""
    if not URL:
        pytest.skip()
    truck = f"TRA-OK-{uuid.uuid4().hex[:6]}"
    trailer = f"TR-BAD-{uuid.uuid4().hex[:6]}"
    payload = {
        "kind": "dvir",
        "driver_name": "Trailer Scope Driver",
        "inspection_date": "2024-08-15",
        "inspection_time": "07:30",
        "truck_unit_number": truck,
        "truck_checklist": {item: "pass" for item in _ck.dvir_truck_items()},
        "trailers": [
            {
                "trailer_unit_number": trailer,
                "checklist": {
                    **{item: "pass" for item in _ck.dvir_trailer_items()},
                    "Trailer brake lights — both sides functional": "fail",
                },
            },
        ],
        "submitted_via": "public_tile",
    }
    try:
        r = requests.post(f"{URL}/api/fleet/inspections", json=payload, timeout=30)
        assert r.status_code == 200
        out = r.json()
        assert out["truck_status_after"] == "available", (
            "tractor must remain available when only the trailer has OOS defects"
        )

        async def _verify_status():
            db = _db()
            ts = await db.fleet_status.find_one({"unit_number": trailer}, {"_id": 0})
            assert ts["status"] == "oos", "trailer must be OOS"
            assert ts["unit_kind"] == "trailer"
        asyncio.run(_verify_status())
    finally:
        async def _cleanup():
            db = _db()
            await db.equipment_inspections.delete_many({"truck_unit_number": truck})
            await db.fleet_defects.delete_many(
                {"$or": [{"truck_unit_number": truck},
                         {"trailer_unit_number": trailer}]}
            )
            await db.fleet_status.delete_many(
                {"unit_number": {"$in": [truck, trailer]}}
            )
        asyncio.run(_cleanup())


# ─── 4 · Cross-department workflow validation ────────────────────────
def test_full_cross_dept_workflow_propagation(admin_token):
    """Single DVIR submission · verify Dispatch / Shop / Safety all see
    the appropriate slice. The driver doesn't see anything (they
    submitted) · dispatch sees status · shop sees queue · safety sees
    only safety-critical category."""
    if not URL:
        pytest.skip()
    truck = f"XDEP-{uuid.uuid4().hex[:6]}"
    H = {"X-Admin-Token": admin_token}
    # Driver submits with two failures: one safety-critical (brake light)
    # + one non-safety (suspension)
    checklist = {item: "pass" for item in _ck.dvir_truck_items()}
    checklist["Brake lights — both sides functional"] = "fail"
    checklist["Suspension — leaf springs · u-bolts · shackles intact"] = "fail"
    payload = {
        "kind": "dvir",
        "driver_name": "X-Dept Driver",
        "inspection_date": "2024-08-15",
        "inspection_time": "08:00",
        "truck_unit_number": truck,
        "truck_checklist": checklist,
        "submitted_via": "public_tile",
    }
    insp_id = None
    try:
        r = requests.post(f"{URL}/api/fleet/inspections", json=payload, timeout=30)
        assert r.status_code == 200
        out = r.json()
        insp_id = out["inspection_id"]
        assert out["truck_status_after"] == "oos"
        assert out["defect_count"] == 2

        # Dispatch sees the truck as OOS
        r1 = requests.get(
            f"{URL}/api/dispatch/fleet/status?status=oos",
            headers=H, timeout=15,
        )
        assert r1.status_code == 200
        oos_units = {u["unit_number"] for u in r1.json()["units"]}
        assert truck in oos_units, "Dispatch must see this truck as OOS"

        # Shop sees both defects in its queue
        r2 = requests.get(
            f"{URL}/api/shop/fleet/defects?unit_number=" + truck,
            headers=H, timeout=15,
        )
        assert r2.status_code == 200
        shop_defects = r2.json()["defects"]
        assert len(shop_defects) == 2, (
            f"Shop must see both defects for the unit · got {len(shop_defects)}"
        )
        shop_categories = {d["category"] for d in shop_defects}
        assert {"lights", "suspension"}.issubset(shop_categories)

        # Safety sees only the brake-light defect (lights category is in scope)
        # NOT the suspension defect (not safety-scoped)
        r3 = requests.get(
            f"{URL}/api/safety/fleet/emergency-equipment",
            headers=H, timeout=15,
        )
        assert r3.status_code == 200
        safety_for_truck = [d for d in r3.json()["defects"]
                            if d.get("truck_unit_number") == truck]
        assert len(safety_for_truck) == 1, (
            f"Safety must see only safety-critical defect · got {len(safety_for_truck)}"
        )
        assert safety_for_truck[0]["category"] == "lights"

        # Shop acknowledges + repairs both · dispatch clears · truck back to available
        for d in shop_defects:
            r4 = requests.post(
                f"{URL}/api/shop/fleet/defects/{d['id']}/acknowledge",
                json={"actor_name": "Cross-Dept Tech"},
                headers=H, timeout=15,
            )
            assert r4.status_code == 200
            r5 = requests.post(
                f"{URL}/api/shop/fleet/defects/{d['id']}/repair",
                json={"actor_name": "Cross-Dept Tech",
                      "notes": f"fixed {d['category']}"},
                headers=H, timeout=15,
            )
            assert r5.status_code == 200

        # After all repairs, dispatch clears each (final operator gate)
        for d in shop_defects:
            r6 = requests.post(
                f"{URL}/api/dispatch/fleet/defects/{d['id']}/clear",
                json={"actor_name": "Cross-Dept Dispatch"},
                headers=H, timeout=15,
            )
            assert r6.status_code == 200

        # Status returns to available
        async def _final_status():
            db = _db()
            return await db.fleet_status.find_one({"unit_number": truck}, {"_id": 0})
        s = asyncio.run(_final_status())
        assert s["status"] == "available", (
            f"truck should be available after all defects cleared · got {s['status']}"
        )
        assert s["open_oos_count"] == 0
        assert s["open_monitor_count"] == 0

        # Audit trail captures the full lifecycle for each defect
        async def _audit_chain():
            db = _db()
            chain_by_defect = {}
            for d in shop_defects:
                events = await db.fleet_audit.find(
                    {"target_id": d["id"]}, {"_id": 0}
                ).to_list(None)
                chain_by_defect[d["id"]] = {e["action"] for e in events}
            return chain_by_defect
        chains = asyncio.run(_audit_chain())
        for defect_id, actions in chains.items():
            assert {"defect_acknowledged", "defect_repaired", "defect_cleared"}.issubset(actions), (
                f"defect {defect_id} missing audit actions · got {actions}"
            )
    finally:
        async def _cleanup():
            db = _db()
            await db.equipment_inspections.delete_many({"truck_unit_number": truck})
            defects = await db.fleet_defects.find(
                {"truck_unit_number": truck}, {"id": 1, "_id": 0}
            ).to_list(None)
            for d in defects:
                await db.fleet_audit.delete_many({"target_id": d["id"]})
            await db.fleet_defects.delete_many({"truck_unit_number": truck})
            await db.fleet_status.delete_one({"unit_number": truck})
            if insp_id:
                await db.fleet_audit.delete_many({"target_id": insp_id})
        asyncio.run(_cleanup())


# ─── 5 · Audit-chain integrity smoke ────────────────────────────────
def test_audit_chain_captures_manual_oos_flip(admin_token):
    """Dispatch manual OOS flip (defect created without an inspection)
    must produce a full audit chain · operator override traceability."""
    if not URL:
        pytest.skip()
    unit = f"MANUAL-OOS-{uuid.uuid4().hex[:6]}"
    H = {"X-Admin-Token": admin_token}
    r = requests.post(
        f"{URL}/api/dispatch/fleet/units/{unit}/oos",
        json={"actor_name": "Dispatch Override",
              "notes": "found puddle of fuel · pulled rig"},
        headers=H, timeout=15,
    )
    assert r.status_code == 200
    defect_id = r.json()["defect_id"]
    try:
        async def _check():
            db = _db()
            d = await db.fleet_defects.find_one({"id": defect_id}, {"_id": 0})
            assert d["severity"] == "oos"
            assert d["inspection_id"] is None
            assert d["inspection_kind"] == "manual_oos"
            audits = await db.fleet_audit.find(
                {"target_id": unit}, {"_id": 0}
            ).to_list(None)
            assert any(a["action"] == "manual_oos_flip" for a in audits)
            status = await db.fleet_status.find_one({"unit_number": unit}, {"_id": 0})
            assert status["status"] == "oos"
        asyncio.run(_check())
    finally:
        async def _cleanup():
            db = _db()
            await db.fleet_defects.delete_many({"id": defect_id})
            await db.fleet_status.delete_one({"unit_number": unit})
            await db.fleet_audit.delete_many({"target_id": unit})
            await db.fleet_audit.delete_many({"target_id": defect_id})
        asyncio.run(_cleanup())


# ─── 6 · Severity table internal cross-checks (pure-function) ───────
def test_severity_table_no_duplicate_keys_after_normalisation():
    """Two checklist items differing only in whitespace would silently
    overwrite in the dict literal · this validates the source loaded
    cleanly (Python already enforces unique keys at parse time, so this
    is mostly a smoke test that the table has expected size)."""
    assert len(_sev.FLEET_DEFECT_SEVERITY) >= 90, (
        f"severity table shrank unexpectedly: {len(_sev.FLEET_DEFECT_SEVERITY)} entries"
    )


def test_severity_table_meta_keys_match_severity_keys():
    sev_keys = set(_sev.FLEET_DEFECT_SEVERITY.keys())
    meta_keys = set(_sev.FLEET_DEFECT_SEVERITY_META.keys())
    assert meta_keys == sev_keys, (
        f"severity / metadata table key drift · "
        f"only-severity={sorted(sev_keys - meta_keys)[:3]} "
        f"only-meta={sorted(meta_keys - sev_keys)[:3]}"
    )


def test_severity_table_uncertain_items_have_uncertainty_note():
    for item, meta in _sev.FLEET_DEFECT_SEVERITY_META.items():
        if meta.get("uncertain"):
            assert meta.get("uncertainty_note"), (
                f"item {item!r} marked uncertain but has no uncertainty_note"
            )
            assert meta.get("regulation_ref"), (
                f"item {item!r} uncertain but missing regulation_ref"
            )


def test_severity_endpoint_registered():
    import sys
    import importlib
    if "server" in sys.modules:
        importlib.reload(sys.modules["server"])
    import server as srv
    paths = {getattr(r, "path", None) for r in srv.app.routes}
    assert "/api/admin/fleet/severity-audit" in paths
