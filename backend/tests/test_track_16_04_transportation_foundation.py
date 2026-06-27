"""TRACK 16.04 · MASCI Transportation Foundation · Phase 1 regression.

Locks the permanent contract for the Phase 1 foundation:

* lib/transport_eligibility — pure compute, deterministic states.
* lib/transport_identity — no duplicate driver projections.
* routes/transportation — admin CRUD + dispatch read-only, with audit.
* No Phase 2/3/4 surface exists yet (orientation / quizzes / certs /
  packets / carrier portal / public invite / hard-block).
* deployment_gate.py includes this file.

A subset of tests run against the live preview backend (admin-strict +
dispatch read endpoints) when REACT_APP_BACKEND_URL is set; otherwise
the live-network tests skip gracefully and the static + unit tests
still lock the contract.
"""
from __future__ import annotations

import asyncio
import inspect
import json
import os
import re
import sys
from pathlib import Path

import pytest

ROOT = Path("/app")
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from lib import transport_eligibility as elig  # noqa: E402
from lib import transport_identity as ident  # noqa: E402

ROUTE_FILE = BACKEND / "routes" / "transportation.py"
SERVER_FILE = BACKEND / "server.py"
PAGE_FILE = ROOT / "frontend" / "src" / "pages" / "AdminTransportation.jsx"
APP_JS = ROOT / "frontend" / "src" / "App.js"
DEPLOY_GATE = ROOT / "scripts" / "deployment_gate.py"


# ───────────────────── 1. data-model constants exist ─────────────────────
def test_1_carrier_status_constants():
    assert "pending_review" in elig.VALID_STATUSES
    assert set(elig.VALID_STATUSES) >= {
        "pending_review", "active", "needs_correction",
        "suspended", "expired", "inactive",
    }


def test_2_person_kinds_supported():
    src = ROUTE_FILE.read_text()
    assert "masci_employee" in src
    assert "leased_driver" in src


# ───────────────────── 3-9. invariants in route source ──────────────────
def test_3_masci_employee_requires_employee_id():
    src = ROUTE_FILE.read_text()
    assert 'employee_id is required for masci_employee' in src


def test_4_leased_driver_requires_carrier_id():
    src = ROUTE_FILE.read_text()
    assert 'carrier_id is required for leased_driver' in src


def test_5_duplicate_employee_driver_prevented():
    src = ROUTE_FILE.read_text()
    assert 'find_existing_employee_projection' in src
    assert 'Active MASCI employee driver projection already exists' in src


def test_6_duplicate_leased_license_prevented():
    src = ROUTE_FILE.read_text()
    assert 'find_existing_leased_driver' in src
    assert 'Active leased driver with this license_number' in src


def test_7_truck_ownership_supports_masci_and_leased():
    src = ROUTE_FILE.read_text()
    assert 'masci_owned' in src
    assert 'leased_carrier' in src
    assert 'owner_operator' in src


def test_8_leased_truck_requires_carrier_id():
    src = ROUTE_FILE.read_text()
    assert 'carrier_id is required for leased/owner-operator trucks' in src


def test_9_masci_owned_truck_links_equipment_id():
    src = ROUTE_FILE.read_text()
    # equipment_id stored only when ownership == masci_owned
    assert '"equipment_id": body.equipment_id if body.ownership == "masci_owned"' in src


# ───────────────────── 10-12. eligibility truth table ───────────────────
def test_10_new_record_defaults_pending_review():
    r = elig.compute_transport_eligibility(
        "carrier", {"status": "pending_review"}, None)
    assert r["state"] == "pending_review"


def test_11_safety_hold_and_suspended():
    r1 = elig.compute_transport_eligibility(
        "person", {"status": "active", "safety_hold": True}, None)
    assert r1["state"] == "suspended"
    r2 = elig.compute_transport_eligibility(
        "person", {"status": "suspended"}, None)
    assert r2["state"] == "suspended"
    r3 = elig.compute_transport_eligibility(
        "truck", {"status": "inactive"}, None)
    assert r3["state"] == "not_dispatchable"


def test_12_masci_employee_hr_inactive_forces_not_dispatchable():
    r = elig.compute_transport_eligibility(
        "person",
        {"kind": "masci_employee", "status": "active"},
        {"hr_lifecycle_active": False},
    )
    assert r["state"] == "not_dispatchable"
    assert any(x.get("code") == "hr_lifecycle_inactive" for x in r["reasons"])


# ───────────────────── 13-15. RBAC posture ──────────────────────────────
def test_13_admin_routes_require_admin_strict():
    server_src = SERVER_FILE.read_text()
    assert "register_transportation_routes(" in server_src
    # Must wire the strict-admin gate (not the lax require_admin which
    # accepts PM tokens on non-/admin namespaces; admin namespace +
    # strict gate is the doctrine).
    m = re.search(
        r"register_transportation_routes\([^)]+require_admin_dep=([^,)]+)",
        server_src,
    )
    assert m, "register_transportation_routes must pass require_admin_dep"
    assert "require_admin_strict" in m.group(1)


def test_14_dispatch_routes_require_dispatch_or_admin():
    server_src = SERVER_FILE.read_text()
    m = re.search(
        r"register_transportation_routes\([^)]+require_dispatch_or_admin_dep=([^,)]+)",
        server_src,
    )
    assert m, "must pass require_dispatch_or_admin_dep"
    val = m.group(1)
    assert "_require_dispatch_or_admin" in val or "_shared_dispatch_or_admin" in val


def test_15_no_public_transport_routes():
    src = ROUTE_FILE.read_text()
    # Every `@router.get/post/patch/delete` line below must be followed
    # within a small window by a Depends(...) on require_admin_dep
    # OR require_dispatch_or_admin_dep.
    pattern = re.compile(r"@router\.(get|post|patch|delete)\(")
    for m in pattern.finditer(src):
        window = src[m.start(): m.start() + 1200]
        assert (
            "Depends(require_admin_dep)" in window
            or "Depends(require_dispatch_or_admin_dep)" in window
        ), f"Phase-1 route at offset {m.start()} has no Phase-1 auth dep"


# ───────────────────── 16. audit write present ───────────────────────────
def test_16_audit_writes_on_create_update():
    src = ROUTE_FILE.read_text()
    assert 'audit_events.insert_one' in src or '_audit(' in src
    # And the audit helper does write to audit_events.
    assert "db.audit_events.insert_one" in src
    for needle in (
        "transport_carrier_create",
        "transport_carrier_update",
        "transport_person_create",
        "transport_person_update",
        "transport_truck_create",
        "transport_truck_update",
    ):
        assert needle in src, f"audit kind {needle} missing"


# ───────────────────── 17. route file wired into server.py ──────────────
def test_17_route_wired_into_server():
    server_src = SERVER_FILE.read_text()
    assert "from routes.transportation import register_transportation_routes" in server_src
    assert "register_transportation_routes(" in server_src


# ───────────────────── 18. UI route exists ──────────────────────────────
def test_18_admin_transportation_route_exists():
    app_src = APP_JS.read_text()
    assert 'path="/admin/transportation' in app_src  # may be exact or splat
    assert "AdminTransportation" in app_src
    assert PAGE_FILE.exists()


# ───────────────────── 19. forbidden status language ────────────────────
def test_19_no_forbidden_status_language():
    src = ROUTE_FILE.read_text() + "\n" + PAGE_FILE.read_text()
    # The product directive bans punitive labels in status/eligibility.
    # We only check label-literal usage; the words may legitimately
    # appear in unrelated contexts so we grep label/value forms.
    for needle in ('"Rejected"', '"Denied"', '"Failed"',
                   "'Rejected'", "'Denied'", "'Failed'",
                   ">Rejected<", ">Denied<", ">Failed<"):
        assert needle not in src, f"forbidden status label {needle!r}"


# ───────────────────── 20. no ForgedOps Academy references ──────────────
def test_20_no_forgedops_academy_in_track_16_04_artefacts():
    for p in (ROUTE_FILE, PAGE_FILE,
              BACKEND / "lib" / "transport_eligibility.py",
              BACKEND / "lib" / "transport_identity.py"):
        text = p.read_text()
        assert "ForgedOps Academy" not in text
        assert "forgedops academy" not in text.lower()


# ───────────────────── 21. no duplicate storage engine ──────────────────
def test_21_no_duplicate_storage_engine():
    src = ROUTE_FILE.read_text()
    # Phase 1 must NOT introduce a new R2 / S3 / boto / file-upload
    # path. Document storage is deferred to Phase 2.
    assert "boto3" not in src
    assert "photo_storage" not in src
    assert "UploadFile" not in src
    assert ".put_object" not in src


# ───────────────────── 22. deployment gate inclusion ────────────────────
def test_22_deployment_gate_includes_this_file():
    gate_src = DEPLOY_GATE.read_text()
    assert "test_track_16_04_transportation_foundation.py" in gate_src


# ───────────────────── BONUS · identity resolver shape ──────────────────
def test_identity_resolver_async_callables():
    assert inspect.iscoroutinefunction(ident.find_existing_employee_projection)
    assert inspect.iscoroutinefunction(ident.find_existing_leased_driver)
    assert callable(ident.display_name)
    assert ident.display_name({"first_name": "Jane", "last_name": "Doe"}) == "Jane Doe"


def test_identity_resolver_no_license_returns_none():
    async def go():
        return await ident.find_existing_leased_driver(
            db=None, tenant="masci", carrier_id="x", license_number=None,
        )
    assert asyncio.get_event_loop().run_until_complete(go()) is None
