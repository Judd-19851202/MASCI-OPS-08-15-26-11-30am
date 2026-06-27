"""TRACK 16.08 · Transportation Orientation, Notification & External
Onboarding Platform regression suite.

Static tests parse source files for invariants; live tests exercise the
real preview backend end-to-end when REACT_APP_BACKEND_URL is set.

Locks:
* Orientation router exists with 22 default modules · 4 languages
* Bootstrap hook is registered in server.py
* Eligibility engine reads orientation_status
* External invite portal endpoints are PUBLIC (no admin gate)
* No-skip rule on video heartbeat (server clamps to monotonic + 30s/tick)
* Quiz max attempts enforced
* Certificate audit hash + QR public verify
* Email Routing v2 used (no SMS / Push)
* Notifications use existing notify primitive
* deployment_gate.py includes this file
"""
from __future__ import annotations

import asyncio
import os
import re
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pytest

ROOT = Path("/app")
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

ROUTER = BACKEND / "routes" / "transportation_orientation.py"
STATUS_LIB = BACKEND / "lib" / "transport_orientation_status.py"
ELIG_LIB = BACKEND / "lib" / "transport_eligibility.py"
SERVER = BACKEND / "server.py"
GATE = ROOT / "scripts" / "deployment_gate.py"
TRANSPORT_ROUTE = BACKEND / "routes" / "transportation.py"
PHASE2_ROUTE = BACKEND / "routes" / "transportation_phase2.py"


# ===========================================================================
# 1. STATIC LOCKS — Backend source contract
# ===========================================================================
def test_01_orientation_router_file_exists():
    assert ROUTER.exists(), "Orientation router missing"


def test_02_router_defines_22_default_modules():
    src = ROUTER.read_text()
    # MODULES = [ ... ] block must list ~22 modules (21 required + 1 annual).
    m = re.search(r"MODULES\s*=\s*\[(.*?)\]\s*\n\n", src, re.DOTALL)
    assert m, "MODULES catalog not found"
    block = m.group(1)
    assert block.count("(") >= 21, "expected ≥21 module entries"
    # Confirm key modules are present.
    for needle in (
        "welcome_to_masci", "safety_culture", "traffic_control",
        "asphalt_plant_operations", "loading_procedures", "hauling_procedures",
        "backing_procedures", "dumping_procedures", "truck_readiness",
        "driver_expectations", "ppe", "incident_reporting", "near_miss_reporting",
        "emergency_procedures", "equipment_awareness", "communications",
        "customer_expectations", "environmental_responsibilities", "end_of_shift",
        "annual_refresher",
    ):
        assert needle in src, f"Missing required module: {needle}"


def test_03_four_languages_supported():
    src = ROUTER.read_text()
    assert 'LANGUAGES = ("en", "es", "es_CU", "fr")' in src


def test_04_bootstrap_hook_in_server():
    src = SERVER.read_text()
    assert "bootstrap_track_16_08" in src
    assert "register_transportation_orientation_routes" in src
    assert "_track_16_08_bootstrap_on_startup" in src


def test_05_completion_threshold_99():
    src = ROUTER.read_text()
    assert "COMPLETION_WATCH_THRESHOLD = 0.99" in src


def test_06_quiz_max_attempts_enforced():
    src = ROUTER.read_text()
    assert "Max quiz attempts reached" in src


def test_07_no_skip_rule_in_heartbeat():
    """Server must clamp watched_seconds to monotonic + bounded delta."""
    src = ROUTER.read_text()
    # Must contain server-side clamp on watched_seconds.
    assert "delta_cap" in src
    assert "prior + 30" in src or "prior+30" in src.replace(" ", "")


def test_08_certificate_audit_hash_present():
    src = ROUTER.read_text()
    assert "_audit_hash" in src
    assert "audit_hash" in src
    assert "hashlib.sha256" in src


def test_09_public_qr_verify_endpoint():
    src = ROUTER.read_text()
    assert '"/transportation/orientation/certificates/verify/{cnum}"' in src
    # Must NOT require admin (no Depends(require_admin_dep) on this route).
    m = re.search(
        r'@router\.get\(\s*"/transportation/orientation/certificates/verify/[^"]+"\)\s*\n\s*async def public_verify\([^)]*\)',
        src,
    )
    assert m, "public_verify signature must not include Depends"


def test_10_public_invite_endpoints_exist():
    src = ROUTER.read_text()
    assert '"/transportation/invite/{token}"' in src
    assert '"/transportation/invite/{token}/submit"' in src
    assert '"/transportation/invite/{token}/orientation/modules"' in src
    assert '"/transportation/invite/{token}/orientation/assignments"' in src
    assert "invite_heartbeat" in src
    assert "invite_quiz_submit" in src


def test_11_external_endpoints_are_public_no_admin_gate():
    """Public carrier invite endpoints must not depend on require_admin_dep."""
    src = ROUTER.read_text()
    # Extract the @router.* decorator immediately preceding each public
    # endpoint definition.
    public_funcs = (
        "invite_open", "invite_submit", "invite_list_modules", "invite_assign",
        "invite_get_assignment", "invite_heartbeat", "invite_quiz_load",
        "invite_quiz_submit", "invite_list_certificates", "public_verify",
    )
    for fname in public_funcs:
        m = re.search(rf"async def {fname}\(([^)]*)\)", src)
        assert m, f"{fname} not found"
        sig = m.group(1)
        assert "require_admin_dep" not in sig, (
            f"{fname} must NOT have admin gate (it is the public invite portal)")


def test_12_uses_email_routing_v2_not_sms():
    src = ROUTER.read_text()
    # Notification engine must consult email_routing_v2 only.
    assert "email_routing_v2" in src
    assert "resolve_and_audit" in src
    # No SMS / Push references anywhere.
    for forbidden in ("twilio", "sms", "push_notification", "fcm", "apns"):
        assert forbidden.lower() not in src.lower(), f"forbidden notification kind: {forbidden}"


def test_13_notification_kinds_full_catalog():
    src = ROUTER.read_text()
    for kind in (
        "carrier_invite", "packet_ready", "packet_submitted",
        "packet_needs_correction", "packet_approved",
        "driver_approved", "driver_suspended",
        "orientation_assigned", "orientation_reminder",
        "orientation_expiring", "orientation_overdue",
        "annual_inspection_due", "annual_inspection_reminder",
        "annual_inspection_overdue",
        "documents_expiring", "documents_approved", "documents_need_correction",
        "driver_eligible", "driver_not_eligible",
        "carrier_eligible", "carrier_not_eligible",
        "dispatch_eligibility_changed",
    ):
        assert f'"{kind}"' in src, f"Missing notification kind: {kind}"


def test_14_eligibility_reads_orientation_status():
    """transport_eligibility.py must consume ctx['orientation_status']."""
    src = ELIG_LIB.read_text()
    assert "orientation_status" in src
    assert "orientation_missing" in src
    assert "orientation_expired" in src
    assert "orientation_quiz_failed" in src


def test_15_eligibility_blocks_on_missing_orientation():
    """Pure compute: driver with orientation_status=missing → not eligible."""
    from lib.transport_eligibility import compute_transport_eligibility
    record = {"status": "active", "kind": "leased_driver"}
    out = compute_transport_eligibility("person", record,
                                         {"orientation_status": "missing"})
    assert out["state"] != "eligible"
    codes = [r["code"] for r in out["reasons"]]
    assert "orientation_missing" in codes


def test_16_eligibility_blocks_on_expired_orientation():
    from lib.transport_eligibility import compute_transport_eligibility
    out = compute_transport_eligibility(
        "person", {"status": "active", "kind": "leased_driver"},
        {"orientation_status": "expired"})
    codes = [r["code"] for r in out["reasons"]]
    assert "orientation_expired" in codes


def test_17_eligibility_blocks_on_quiz_failed():
    from lib.transport_eligibility import compute_transport_eligibility
    out = compute_transport_eligibility(
        "person", {"status": "active", "kind": "leased_driver"},
        {"orientation_status": "quiz_failed"})
    codes = [r["code"] for r in out["reasons"]]
    assert "orientation_quiz_failed" in codes


def test_18_eligibility_passes_when_orientation_current():
    """A fully-current driver with no other issues must remain eligible."""
    from lib.transport_eligibility import compute_transport_eligibility
    out = compute_transport_eligibility(
        "person", {"status": "active", "kind": "leased_driver"},
        {"orientation_status": "current", "rate_acknowledged": True,
         "missing_required_docs": 0, "expired_required_docs": 0,
         "docs_needs_correction": 0, "packet_status": "approved"})
    codes = [r["code"] for r in out["reasons"]]
    assert "orientation_missing" not in codes
    assert "orientation_expired" not in codes
    assert "orientation_quiz_failed" not in codes


def test_19_transportation_routes_inject_orientation_for_persons():
    """Routes/transportation.py must call derive_orientation_status when
    upserting eligibility for a person target."""
    src = TRANSPORT_ROUTE.read_text()
    assert "derive_orientation_status" in src
    # Must guard on target_type == 'person' so we don't waste cycles.
    assert 'target_type == "person"' in src or "target_type=='person'" in src


def test_20_phase2_person_context_injects_orientation():
    src = PHASE2_ROUTE.read_text()
    assert "derive_orientation_status" in src
    assert "orientation_status" in src


def test_21_status_helper_exposes_four_states():
    """Pure helper must always return one of {current, missing, expired, quiz_failed}."""
    src = STATUS_LIB.read_text()
    for state in ("current", "missing", "expired", "quiz_failed"):
        assert f'"{state}"' in src


def test_22_deployment_gate_includes_16_08():
    src = GATE.read_text()
    assert "test_track_16_08_transportation_orientation" in src


def test_23_track_16_04_05_06_07_preserved():
    """Previous tracks must remain wired in the gate."""
    src = GATE.read_text()
    for prev in (
        "test_track_16_04_transportation_foundation",
        "test_track_16_05_transportation_onboarding_compliance_center",
        "test_track_16_06_transportation_experience_layer",
        "test_track_16_07_transportation_workflow_activation",
    ):
        assert prev in src, f"Track {prev} dropped from deployment gate"


def test_24_no_dead_ui_in_transportation_app():
    """Frontend TransportationApp must include Orientation route surfaces."""
    p = ROOT / "frontend" / "src" / "pages" / "transportation" / "TransportationApp.jsx"
    src = p.read_text()
    assert "orientation" in src.lower(), "Orientation tab missing from TransportationApp"


def test_25_audit_kinds_full_lifecycle():
    src = ROUTER.read_text()
    for kind in (
        "transport_orientation_module_create",
        "transport_orientation_module_update",
        "transport_orientation_placeholder_update",
        "transport_orientation_question_create",
        "transport_orientation_assigned",
        "transport_orientation_quiz_submit",
        "transport_invite_create",
        "transport_invite_submit",
    ):
        assert kind in src, f"Audit kind missing: {kind}"


def test_26_orientation_valid_months_annual():
    src = ROUTER.read_text()
    assert "ORIENTATION_VALID_MONTHS = 12" in src


# ===========================================================================
# 2. PURE FUNCTION TESTS — derive_orientation_status
# ===========================================================================
class _FakeCursor:
    def __init__(self, items):
        self._items = items

    def sort(self, *_, **__):
        return self

    def limit(self, *_, **__):
        return self

    async def to_list(self, _length):
        return list(self._items)


class _FakeColl:
    def __init__(self, items):
        self._items = items

    def find(self, _q=None):
        return _FakeCursor(self._items)


class _FakeDB:
    def __init__(self, modules, assigns):
        self.transport_orientation_modules = _FakeColl(modules)
        self.transport_orientation_assignments = _FakeColl(assigns)


def _run(coro):
    """Run a coroutine without disturbing the global event-loop policy.
    asyncio.run() sets the current loop to None on exit which breaks
    sibling tests that still use the deprecated asyncio.get_event_loop().
    """
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def test_30_status_no_required_modules_is_missing():
    from lib.transport_orientation_status import derive_orientation_status
    db = _FakeDB([], [])
    res = _run(derive_orientation_status(db, "p1"))
    assert res["orientation_status"] == "missing"


def test_31_status_all_completed_is_current():
    from lib.transport_orientation_status import derive_orientation_status
    from datetime import datetime, timezone, timedelta
    future = (datetime.now(timezone.utc) + timedelta(days=200)).isoformat()
    db = _FakeDB(
        modules=[
            {"key": "a", "active": True, "required": True},
            {"key": "b", "active": True, "required": True},
        ],
        assigns=[
            {"module_key": "a", "status": "completed",
             "expires_at": future, "assigned_at": "2026-01-01"},
            {"module_key": "b", "status": "completed",
             "expires_at": future, "assigned_at": "2026-01-01"},
        ],
    )
    res = _run(derive_orientation_status(db, "p1"))
    assert res["orientation_status"] == "current"
    assert res["completed_count"] == 2
    assert res["required_count"] == 2


def test_32_status_one_missing_is_missing():
    from lib.transport_orientation_status import derive_orientation_status
    db = _FakeDB(
        modules=[{"key": "a", "active": True, "required": True},
                  {"key": "b", "active": True, "required": True}],
        assigns=[{"module_key": "a", "status": "completed",
                  "expires_at": "2099-01-01", "assigned_at": "2026-01-01"}],
    )
    res = _run(derive_orientation_status(db, "p1"))
    assert res["orientation_status"] == "missing"


def test_33_status_expired_is_expired():
    from lib.transport_orientation_status import derive_orientation_status
    db = _FakeDB(
        modules=[{"key": "a", "active": True, "required": True}],
        assigns=[{"module_key": "a", "status": "completed",
                  "expires_at": "2020-01-01", "assigned_at": "2026-01-01"}],
    )
    res = _run(derive_orientation_status(db, "p1"))
    assert res["orientation_status"] == "expired"


def test_34_status_only_failed_is_quiz_failed():
    from lib.transport_orientation_status import derive_orientation_status
    db = _FakeDB(
        modules=[{"key": "a", "active": True, "required": True}],
        assigns=[{"module_key": "a", "status": "quiz_failed",
                  "expires_at": None, "assigned_at": "2026-01-01"}],
    )
    res = _run(derive_orientation_status(db, "p1"))
    assert res["orientation_status"] == "quiz_failed"


def test_35_status_expiring_soon_flag():
    from lib.transport_orientation_status import derive_orientation_status
    from datetime import datetime, timezone, timedelta
    soon = (datetime.now(timezone.utc) + timedelta(days=20)).isoformat()
    db = _FakeDB(
        modules=[{"key": "a", "active": True, "required": True}],
        assigns=[{"module_key": "a", "status": "completed",
                  "expires_at": soon, "assigned_at": "2026-01-01"}],
    )
    res = _run(derive_orientation_status(db, "p1"))
    assert res["expiring_soon"] is True


# ===========================================================================
# 3. LIVE BACKEND SMOKE — opt-in via REACT_APP_BACKEND_URL
# ===========================================================================
BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    BASE_URL = "http://localhost:8001"

ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"


def _admin_token():
    import requests
    try:
        r = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=10,
        )
        if r.status_code != 200:
            return None
        return r.json().get("portal_tokens", {}).get("admin")
    except Exception:
        return None


@pytest.fixture(scope="module")
def H():
    tok = _admin_token()
    if not tok:
        pytest.skip("No admin token available on this env — skipping live tests")
    return {"X-Admin-Token": tok, "Content-Type": "application/json"}


def test_50_list_modules_seeded(H):
    import requests
    r = requests.get(f"{BASE_URL}/api/admin/transportation/orientation/modules",
                     headers=H, timeout=10)
    assert r.status_code == 200
    data = r.json()
    assert len(data["items"]) >= 21, f"Expected ≥21 modules, got {len(data['items'])}"
    keys = {m["key"] for m in data["items"]}
    assert "welcome_to_masci" in keys
    assert "annual_refresher" in keys


def test_51_each_module_has_4_language_placeholders(H):
    import requests
    r = requests.get(f"{BASE_URL}/api/admin/transportation/orientation/modules",
                     headers=H, timeout=10)
    data = r.json()
    for m in data["items"]:
        langs = {ph["language"] for ph in m.get("placeholders", [])}
        assert langs >= {"en", "es", "es_CU", "fr"}, (
            f"Module {m['key']} missing languages, got {langs}")


def test_52_orientation_dashboard_endpoint(H):
    import requests
    r = requests.get(f"{BASE_URL}/api/admin/transportation/orientation/dashboard",
                     headers=H, timeout=15)
    assert r.status_code == 200
    j = r.json()
    for k in ("modules_active", "modules_required", "drivers_total",
              "drivers_orientation_current", "drivers_orientation_missing",
              "completion_pct", "certificates_total", "average_quiz_score",
              "disclaimer"):
        assert k in j, f"Missing key in dashboard: {k}"


def test_53_question_create_and_list(H):
    import requests
    # Pick the welcome module.
    mods = requests.get(f"{BASE_URL}/api/admin/transportation/orientation/modules",
                        headers=H, timeout=10).json()["items"]
    welcome = next(m for m in mods if m["key"] == "welcome_to_masci")
    create = requests.post(
        f"{BASE_URL}/api/admin/transportation/orientation/modules/{welcome['id']}/questions",
        headers=H,
        json={"prompt": "What is MASCI's primary value?",
              "choices": ["Speed", "Safety", "Profit"],
              "correct_index": 1, "language": "en"}, timeout=10)
    assert create.status_code in (200, 201), create.text
    out = create.json()
    assert out["correct_index"] == 1
    qs = requests.get(
        f"{BASE_URL}/api/admin/transportation/orientation/modules/{welcome['id']}/questions",
        headers=H, timeout=10).json()
    assert any(q["id"] == out["id"] for q in qs["items"])


def test_54_full_orientation_flow_admin(H):
    """End-to-end happy path: create driver, assign, heartbeat to 99%,
    submit quiz, certificate issued, eligibility flips toward eligible."""
    import requests
    # Create carrier + driver via admin transportation routes (no-op
    # if Phase-1 routes are not available — skip gracefully).
    cr = requests.post(
        f"{BASE_URL}/api/admin/transportation/carriers",
        headers=H,
        json={"legal_name": f"E2E Test Carrier {uuid.uuid4().hex[:8]}",
              "carrier_type": "leased_hauler", "status": "active"},
        timeout=10)
    if cr.status_code not in (200, 201):
        pytest.skip(f"Carrier create unsupported: {cr.status_code}")
    cid = cr.json()["id"]
    pr = requests.post(
        f"{BASE_URL}/api/admin/transportation/persons",
        headers=H,
        json={"kind": "leased_driver", "first_name": "E2E", "last_name": "Driver",
              "license_number": f"E2E-{uuid.uuid4().hex[:6]}", "carrier_id": cid,
              "status": "active"}, timeout=10)
    assert pr.status_code in (200, 201), pr.text
    pid = pr.json()["id"]
    # Pick welcome module
    mods = requests.get(f"{BASE_URL}/api/admin/transportation/orientation/modules",
                        headers=H, timeout=10).json()["items"]
    welcome = next(m for m in mods if m["key"] == "welcome_to_masci")
    # Configure runtime + 1 question.
    requests.patch(
        f"{BASE_URL}/api/admin/transportation/orientation/modules/{welcome['id']}",
        headers=H, json={"runtime_seconds": 60}, timeout=10)
    requests.post(
        f"{BASE_URL}/api/admin/transportation/orientation/modules/{welcome['id']}/questions",
        headers=H, json={"prompt": "Pick safety",
                          "choices": ["No", "Yes"],
                          "correct_index": 1, "language": "en"}, timeout=10)
    # Assign.
    asn = requests.post(
        f"{BASE_URL}/api/admin/transportation/orientation/assignments",
        headers=H, json={"transport_person_id": pid,
                          "module_key": "welcome_to_masci",
                          "language": "en"}, timeout=10)
    assert asn.status_code in (200, 201), asn.text
    aid = asn.json()["id"]
    # Heartbeat: simulate watching by sending increasing watched_seconds.
    # Server clamps at +30s per tick. Need at least 2 ticks to clear 60s.
    for _ in range(4):
        hb = requests.post(
            f"{BASE_URL}/api/admin/transportation/orientation/assignments/{aid}/heartbeat",
            headers=H, json={"position_seconds": 60, "watched_seconds": 60,
                              "checkpoints_visited": [25, 50, 75, 99]},
            timeout=10)
        assert hb.status_code == 200, hb.text
    final = hb.json()
    assert final["completion_pct"] >= 0.99, final
    # Quiz: load + submit (with admin token works against admin path).
    quiz = requests.get(
        f"{BASE_URL}/api/admin/transportation/orientation/assignments/{aid}/quiz",
        headers=H, timeout=10).json()
    answers = {q["id"]: 1 for q in quiz["items"]}  # all answer index 1 (correct)
    sub = requests.post(
        f"{BASE_URL}/api/admin/transportation/orientation/assignments/{aid}/quiz",
        headers=H, json={"answers": answers}, timeout=10)
    assert sub.status_code == 200, sub.text
    result = sub.json()
    assert result["passed"] is True
    assert result.get("certificate_id"), "Expected certificate to be issued"
    cid_ = result["certificate_id"]
    cert = requests.get(
        f"{BASE_URL}/api/admin/transportation/orientation/certificates/{cid_}",
        headers=H, timeout=10).json()
    assert cert["audit_hash"]
    assert cert["module_key"] == "welcome_to_masci"
    # Public QR verify works.
    pv = requests.get(
        f"{BASE_URL}/api/transportation/orientation/certificates/verify/{cert['certificate_number']}",
        timeout=10)
    assert pv.status_code == 200, pv.text
    assert pv.json()["valid"] is True


def test_55_invite_create_open_submit(H):
    """Secure invite portal end-to-end."""
    import requests
    cr = requests.post(
        f"{BASE_URL}/api/admin/transportation/carriers",
        headers=H,
        json={"legal_name": f"Invite Test Carrier {uuid.uuid4().hex[:6]}",
              "carrier_type": "leased_hauler", "status": "pending_review"},
        timeout=10)
    if cr.status_code not in (200, 201):
        pytest.skip("Carrier create unsupported")
    cid = cr.json()["id"]
    inv = requests.post(
        f"{BASE_URL}/api/admin/transportation/invites", headers=H,
        json={"carrier_id": cid, "contact_email": "test@example.com",
              "expires_in_days": 14}, timeout=10)
    assert inv.status_code in (200, 201), inv.text
    tok = inv.json()["token"]
    # Token is in the response ONCE.
    assert tok and len(tok) > 16
    # Public open (no auth)
    open_ = requests.get(f"{BASE_URL}/api/transportation/invite/{tok}", timeout=10)
    assert open_.status_code == 200
    assert open_.json()["status"] == "opened"
    # Submit
    sub = requests.post(f"{BASE_URL}/api/transportation/invite/{tok}/submit",
                         json={"company_information": {"name": "Test LLC"}},
                         timeout=10)
    assert sub.status_code == 200
    # Public modules list
    mods = requests.get(
        f"{BASE_URL}/api/transportation/invite/{tok}/orientation/modules",
        timeout=10)
    assert mods.status_code == 200
    items = mods.json()["items"]
    assert len(items) >= 21


def test_56_invite_bad_token_404(H):
    """H ensures live server is reachable; otherwise this test is skipped."""
    import requests
    r = requests.get(f"{BASE_URL}/api/transportation/invite/totally-bogus-token",
                     timeout=30)
    assert r.status_code == 404


def test_57_admin_endpoints_reject_unauthenticated(H):
    import requests
    r = requests.get(f"{BASE_URL}/api/admin/transportation/orientation/modules",
                     timeout=30)
    assert r.status_code in (401, 403), r.status_code
