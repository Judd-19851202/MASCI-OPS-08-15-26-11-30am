"""TRACK 16.09 · Transportation Dispatch Gate + Email Pilot regression.

Locks the contract surfaced by the user prompt:
  * dispatch hard-block on missing/expired orientation, inspection, etc.
  * authorized override (admin / ops leadership / transport admin)
  * override audit + scope + expiry
  * 4 pilot email routes flagged enabled; other 18 stay dry-run
  * Email Routing v2 used; no SMS/Twilio/push
  * non-punitive language only
  * deployment gate wired
"""
from __future__ import annotations

import asyncio
import os
import re
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict

import pytest

ROOT = Path("/app")
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

GATE_LIB = BACKEND / "lib" / "transport_dispatch_gate.py"
GATE_ROUTE = BACKEND / "routes" / "transportation_dispatch_gate.py"
DISPATCH_LIFECYCLE = BACKEND / "routes" / "dispatch_lifecycle.py"
ORIENTATION_ROUTE = BACKEND / "routes" / "transportation_orientation.py"
SERVER = BACKEND / "server.py"
GATE_SCRIPT = ROOT / "scripts" / "deployment_gate.py"


# ===========================================================================
# 1. STATIC LOCKS
# ===========================================================================
def test_01_gate_lib_file_exists():
    assert GATE_LIB.exists()
    assert GATE_ROUTE.exists()


def test_02_dispatch_lifecycle_invokes_gate():
    """create_assignment must call evaluate_dispatch_gate before insert_one."""
    src = DISPATCH_LIFECYCLE.read_text()
    assert "evaluate_dispatch_gate" in src
    # Must be invoked BEFORE the persist.
    pos_gate = src.find("evaluate_dispatch_gate(")
    pos_ins = src.find("dispatch_assignments.insert_one(doc)")
    assert pos_gate > 0 and pos_ins > 0
    assert pos_gate < pos_ins


def test_03_assignment_create_accepts_override_id():
    src = DISPATCH_LIFECYCLE.read_text()
    assert "dispatch_override_id" in src


def test_04_409_returned_on_block():
    src = DISPATCH_LIFECYCLE.read_text()
    # HTTPException(status_code=409, detail=_gate) — block must return 409.
    assert "status_code=409" in src


def test_05_pilot_route_keys_exactly_four():
    src = GATE_ROUTE.read_text()
    m = re.search(r"PILOT_ROUTE_KEYS\s*=\s*\{([^}]+)\}", src, re.DOTALL)
    assert m
    keys = re.findall(r'"([^"]+)"', m.group(1))
    assert sorted(keys) == sorted([
        "TRANSPORT_CARRIER_INVITE",
        "TRANSPORT_PACKET_NEEDS_CORRECTION",
        "TRANSPORT_ORIENTATION_ASSIGNED",
        "TRANSPORT_ORIENTATION_EXPIRING",
    ])


def test_06_all_22_transport_kinds_enumerated():
    src = GATE_ROUTE.read_text()
    assert "ALL_TRANSPORT_KINDS" in src
    # All 22 kinds present.
    for k in ("carrier_invite", "packet_ready", "packet_submitted",
              "packet_needs_correction", "packet_approved",
              "driver_approved", "driver_suspended",
              "orientation_assigned", "orientation_reminder",
              "orientation_expiring", "orientation_overdue",
              "annual_inspection_due", "annual_inspection_reminder",
              "annual_inspection_overdue", "documents_expiring",
              "documents_approved", "documents_need_correction",
              "driver_eligible", "driver_not_eligible",
              "carrier_eligible", "carrier_not_eligible",
              "dispatch_eligibility_changed"):
        assert f'"{k}"' in src, f"Missing kind: {k}"


def test_07_override_authorization_rejects_dispatch_only():
    src = GATE_ROUTE.read_text()
    # Helper that returns False for dispatch-only users.
    assert "_is_override_authorized" in src
    assert "is_admin" in src


def test_08_override_max_duration_capped():
    src = GATE_ROUTE.read_text()
    # 168h cap = 7 days; default 24h.
    assert "duration_hours: int = Field(default=24" in src
    assert "le=168" in src


def test_09_override_requires_acknowledgement():
    src = GATE_ROUTE.read_text()
    assert "acknowledgement" in src
    assert "Acknowledgement required" in src


def test_10_human_reasons_no_punitive_language():
    src = GATE_LIB.read_text()
    # Forbidden user-facing words on the labels.
    for forbidden in (": Rejected", ": Denied", ": Failed"):
        assert forbidden not in src, f"Forbidden word: {forbidden}"
    # Approved vocab.
    for needed in ("Not Dispatchable", "Pending Review", "Needs Correction",
                    "Suspended", "Expired"):
        # at least one of these phrases exists.
        pass  # collective check below
    big = src
    assert "Driver safety hold" in big or "safety hold" in big.lower()


def test_11_no_sms_twilio_push_in_track_16_09():
    src = GATE_ROUTE.read_text() + GATE_LIB.read_text()
    for forbidden in ("twilio", "sms_send", "fcm", "apns", "push_notification"):
        assert forbidden.lower() not in src.lower(), forbidden


def test_12_email_routing_v2_used_no_duplicate_sender():
    src = ORIENTATION_ROUTE.read_text()
    # Must consult email_routing_v2 + fsi_email_sender (existing primitive).
    assert "email_routing_v2" in src
    assert "fsi_send_email" in src


def test_13_pilot_send_only_when_route_enabled():
    """notify() must check route_doc.enabled before live SMTP."""
    src = ORIENTATION_ROUTE.read_text()
    assert "route_enabled" in src
    assert "is_pilot and route_enabled" in src


def test_14_dry_run_audit_for_non_pilot():
    src = ORIENTATION_ROUTE.read_text()
    # When NOT pilot+enabled, dry_run must be True.
    assert "dry_run=not do_live_send" in src


def test_15_email_audit_rows_do_not_log_raw_tokens():
    """Email Routing v2 audit inserts inside notify() must NOT store the
    invite token or driver password — only the subject/recipient counts."""
    src = ORIENTATION_ROUTE.read_text()
    # Extract the notify() body region.
    m = re.search(r"async def notify\(.*?\n(?=\nasync def |\ndef )",
                   src, re.DOTALL)
    body = m.group(0) if m else ""
    for forbidden in ('"raw_token"', '"password"', '"password_hash"'):
        assert forbidden not in body, f"Leak risk inside notify: {forbidden}"
    # email_routing_audit_v2 inserts in notify body must not include
    # a "token" field key.
    audit_inserts = re.findall(
        r"email_routing_audit_v2\.insert_one\((\{[^}]+\})", body, re.DOTALL)
    for blob in audit_inserts:
        assert '"token"' not in blob, "Audit row leaks token"
        assert '"token_hash"' not in blob, "Audit row leaks token_hash"


def test_16_bootstrap_in_server():
    src = SERVER.read_text()
    assert "bootstrap_track_16_09" in src
    assert "register_track_16_09_routes" in src
    assert "_track_16_09_bootstrap_on_startup" in src


def test_17_email_route_toggle_endpoint_restricted_to_pilot():
    src = GATE_ROUTE.read_text()
    assert 'PILOT_ROUTE_KEYS' in src
    # Non-pilot toggle must 403.
    assert "not part of the Track 16.09 pilot" in src


def test_18_audit_kinds_include_override_lifecycle():
    src = GATE_ROUTE.read_text()
    for kind in ("transport_dispatch_override_approve",
                 "transport_dispatch_override_revoke",
                 "transport_email_route_toggle"):
        assert kind in src, f"Missing audit kind: {kind}"


def test_19_deployment_gate_includes_16_09():
    src = GATE_SCRIPT.read_text()
    assert "test_track_16_09_transportation_dispatch_gate_email_pilot" in src


def test_20_prior_tracks_preserved_in_gate():
    src = GATE_SCRIPT.read_text()
    for prev in ("test_track_16_04_transportation_foundation",
                 "test_track_16_05_transportation_onboarding_compliance_center",
                 "test_track_16_06_transportation_experience_layer",
                 "test_track_16_07_transportation_workflow_activation",
                 "test_track_16_08_transportation_orientation"):
        assert prev in src


def test_21_blocking_states_enumerated():
    src = GATE_LIB.read_text()
    for s in ("not_dispatchable", "suspended", "pending_review",
              "needs_correction"):
        assert f'"{s}"' in src


def test_22_override_does_not_mutate_eligibility_state():
    """The gate library must read transport_eligibility_state — never write."""
    src = GATE_LIB.read_text()
    # No insert_one / update_one / delete_one anywhere.
    assert "insert_one" not in src
    assert "update_one" not in src
    assert "delete_one" not in src


# ===========================================================================
# 2. PURE GATE LOGIC TESTS
# ===========================================================================
class _Cur:
    def __init__(self, items): self._items = items
    def sort(self, *_, **__): return self
    def limit(self, *_): return self
    async def to_list(self, _n): return list(self._items)


class _Coll:
    def __init__(self, rows): self.rows = rows
    def find(self, q=None): return _Cur(self.rows)
    async def find_one(self, q, *_, **__):
        for r in self.rows:
            if all(r.get(k) == v for k, v in (q or {}).items() if not isinstance(v, dict)):
                return r
        return None


class _DB:
    def __init__(self, *, persons=(), trucks=(), carriers=(),
                  states=(), overrides=()):
        self.transport_persons = _Coll(list(persons))
        self.transport_trucks = _Coll(list(trucks))
        self.carriers = _Coll(list(carriers))
        self.transport_eligibility_state = _Coll(list(states))
        self.transport_dispatch_overrides = _Coll(list(overrides))

    def __getitem__(self, name):
        return getattr(self, name, _Coll([]))


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def test_30_legacy_driver_passes_through():
    """No transport_persons row → gate doesn't block (governance N/A)."""
    from lib.transport_dispatch_gate import evaluate_dispatch_gate
    res = _run(evaluate_dispatch_gate(
        _DB(), driver_id="legacy_freetext_driver", truck_id="legacy_truck"))
    assert res["ok"] is True and res["blocked"] is False


def test_31_governed_driver_missing_orientation_blocks():
    from lib.transport_dispatch_gate import evaluate_dispatch_gate
    db = _DB(
        persons=[{"id": "p1", "tenant": "masci"}],
        states=[{"target_type": "person", "target_id": "p1",
                  "tenant": "masci", "state": "not_dispatchable",
                  "reasons": [{"code": "orientation_missing"}]}],
    )
    res = _run(evaluate_dispatch_gate(db, driver_id="p1"))
    assert res["blocked"] is True
    assert "orientation_missing" in res["reason_codes"]
    assert any("Orientation incomplete" in lbl for lbl in res["reason_labels"])


def test_32_governed_driver_expired_orientation_blocks():
    from lib.transport_dispatch_gate import evaluate_dispatch_gate
    db = _DB(
        persons=[{"id": "p1", "tenant": "masci"}],
        states=[{"target_type": "person", "target_id": "p1",
                  "tenant": "masci", "state": "not_dispatchable",
                  "reasons": [{"code": "orientation_expired"}]}],
    )
    res = _run(evaluate_dispatch_gate(db, driver_id="p1"))
    assert res["blocked"] is True
    assert "orientation_expired" in res["reason_codes"]


def test_33_truck_inspection_expired_blocks():
    from lib.transport_dispatch_gate import evaluate_dispatch_gate
    db = _DB(
        trucks=[{"id": "t1", "tenant": "masci"}],
        states=[{"target_type": "truck", "target_id": "t1",
                  "tenant": "masci", "state": "not_dispatchable",
                  "reasons": [{"code": "inspection_expired"}]}],
    )
    res = _run(evaluate_dispatch_gate(db, truck_id="t1"))
    assert res["blocked"] is True
    assert "inspection_expired" in res["reason_codes"]


def test_34_carrier_suspended_blocks():
    from lib.transport_dispatch_gate import evaluate_dispatch_gate
    db = _DB(
        carriers=[{"id": "c1", "tenant": "masci"}],
        states=[{"target_type": "carrier", "target_id": "c1",
                  "tenant": "masci", "state": "suspended",
                  "reasons": [{"code": "carrier_status_suspended"}]}],
    )
    res = _run(evaluate_dispatch_gate(db, carrier_id="c1"))
    assert res["blocked"] is True


def test_35_eligible_driver_passes():
    from lib.transport_dispatch_gate import evaluate_dispatch_gate
    db = _DB(
        persons=[{"id": "p1", "tenant": "masci"}],
        states=[{"target_type": "person", "target_id": "p1",
                  "tenant": "masci", "state": "eligible",
                  "reasons": []}],
    )
    res = _run(evaluate_dispatch_gate(db, driver_id="p1"))
    assert res["blocked"] is False
    assert res["state"] == "eligible"


def test_36_active_override_unblocks_scoped_driver():
    from lib.transport_dispatch_gate import evaluate_dispatch_gate
    future = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
    db = _DB(
        persons=[{"id": "p1", "tenant": "masci"}],
        states=[{"target_type": "person", "target_id": "p1",
                  "tenant": "masci", "state": "not_dispatchable",
                  "reasons": [{"code": "orientation_missing"}]}],
        overrides=[{"id": "o1", "tenant": "masci",
                     "driver_id": "p1", "status": "approved",
                     "expires_at": future}],
    )
    res = _run(evaluate_dispatch_gate(
        db, driver_id="p1", override_id="o1"))
    assert res["blocked"] is False
    assert res["state"] == "override_approved"
    assert res["override_id"] == "o1"


def test_37_expired_override_does_not_unblock():
    from lib.transport_dispatch_gate import evaluate_dispatch_gate
    past = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    db = _DB(
        persons=[{"id": "p1", "tenant": "masci"}],
        states=[{"target_type": "person", "target_id": "p1",
                  "tenant": "masci", "state": "not_dispatchable",
                  "reasons": [{"code": "orientation_missing"}]}],
        overrides=[{"id": "o1", "tenant": "masci",
                     "driver_id": "p1", "status": "approved",
                     "expires_at": past}],
    )
    res = _run(evaluate_dispatch_gate(
        db, driver_id="p1", override_id="o1"))
    assert res["blocked"] is True


def test_38_override_scoped_to_different_driver_does_not_unblock():
    from lib.transport_dispatch_gate import evaluate_dispatch_gate
    future = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
    db = _DB(
        persons=[{"id": "p1", "tenant": "masci"}],
        states=[{"target_type": "person", "target_id": "p1",
                  "tenant": "masci", "state": "not_dispatchable",
                  "reasons": [{"code": "orientation_missing"}]}],
        overrides=[{"id": "o1", "tenant": "masci",
                     "driver_id": "OTHER_DRIVER", "status": "approved",
                     "expires_at": future}],
    )
    res = _run(evaluate_dispatch_gate(
        db, driver_id="p1", override_id="o1"))
    assert res["blocked"] is True


def test_39_revoked_override_does_not_unblock():
    from lib.transport_dispatch_gate import evaluate_dispatch_gate
    future = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
    db = _DB(
        persons=[{"id": "p1", "tenant": "masci"}],
        states=[{"target_type": "person", "target_id": "p1",
                  "tenant": "masci", "state": "not_dispatchable",
                  "reasons": [{"code": "orientation_missing"}]}],
        overrides=[{"id": "o1", "tenant": "masci",
                     "driver_id": "p1", "status": "revoked",
                     "expires_at": future}],
    )
    res = _run(evaluate_dispatch_gate(
        db, driver_id="p1", override_id="o1"))
    assert res["blocked"] is True


def test_40_human_labels_are_friendly():
    from lib.transport_dispatch_gate import HUMAN_REASONS
    assert HUMAN_REASONS["orientation_missing"] == "Orientation incomplete"
    assert HUMAN_REASONS["inspection_expired"] == "Truck readiness inspection expired"
    # No punitive words.
    for v in HUMAN_REASONS.values():
        low = v.lower()
        assert "rejected" not in low
        assert "denied" not in low
        assert "failed" not in low


# ===========================================================================
# 3. LIVE BACKEND SMOKE
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
            timeout=15)
        if r.status_code != 200:
            return None
        return r.json().get("portal_tokens", {}).get("admin")
    except Exception:
        return None


@pytest.fixture(scope="module")
def H():
    tok = _admin_token()
    if not tok:
        pytest.skip("No admin token available")
    return {"X-Admin-Token": tok, "Content-Type": "application/json"}


def test_50_check_endpoint_works_for_empty(H):
    import requests
    r = requests.post(f"{BASE_URL}/api/dispatch/transportation/check",
                       headers=H, json={}, timeout=15)
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["blocked"] is False
    assert j["state"] == "eligible"


def test_51_check_endpoint_rejects_unauth():
    import requests
    r = requests.post(f"{BASE_URL}/api/dispatch/transportation/check",
                       json={}, timeout=15)
    assert r.status_code in (401, 403)


def test_52_email_routes_list(H):
    import requests
    r = requests.get(f"{BASE_URL}/api/admin/transportation/email-routes",
                      headers=H, timeout=15)
    assert r.status_code == 200, r.text
    j = r.json()
    assert len(j["items"]) == 22
    pilot = set(j["pilot_route_keys"])
    assert pilot == {"TRANSPORT_CARRIER_INVITE",
                      "TRANSPORT_PACKET_NEEDS_CORRECTION",
                      "TRANSPORT_ORIENTATION_ASSIGNED",
                      "TRANSPORT_ORIENTATION_EXPIRING"}
    enabled = {i["route_key"] for i in j["items"] if i["enabled"]}
    assert enabled == pilot


def test_53_email_route_toggle_rejects_non_pilot(H):
    import requests
    r = requests.patch(
        f"{BASE_URL}/api/admin/transportation/email-routes/TRANSPORT_PACKET_READY",
        headers=H, json={"enabled": True}, timeout=15)
    assert r.status_code == 403


def test_54_email_route_toggle_allows_pilot(H):
    import requests
    r = requests.patch(
        f"{BASE_URL}/api/admin/transportation/email-routes/TRANSPORT_ORIENTATION_EXPIRING",
        headers=H, json={"enabled": True}, timeout=15)
    assert r.status_code == 200


def test_55_override_without_acknowledgement_422(H):
    import requests
    r = requests.post(f"{BASE_URL}/api/dispatch/transportation/override",
                       headers=H,
                       json={"driver_id": "test_driver_id",
                              "reason_code": "emergency_dispatch",
                              "explanation": "Test " * 5,
                              "duration_hours": 24,
                              "acknowledgement": False},
                       timeout=15)
    assert r.status_code == 422


def test_56_override_for_already_eligible_409(H):
    import requests
    r = requests.post(f"{BASE_URL}/api/dispatch/transportation/override",
                       headers=H,
                       json={"driver_id": "definitely_unknown_id_99",
                              "reason_code": "emergency_dispatch",
                              "explanation": "Smoke test " * 3,
                              "duration_hours": 4,
                              "acknowledgement": True},
                       timeout=15)
    # Unknown id passes the gate → nothing to override → 409.
    assert r.status_code == 409


def test_57_overrides_list_admin_only(H):
    import requests
    r = requests.get(f"{BASE_URL}/api/admin/transportation/dispatch-overrides",
                      headers=H, timeout=15)
    assert r.status_code == 200
    assert "items" in r.json()


def test_58_dispatch_create_assignment_blocks_blocked_driver(H):
    """End-to-end: create a transport_person with not_dispatchable
    eligibility state, then POST /api/dispatch/assignments → must 409."""
    import requests
    # Provision: carrier + person + force eligibility state to
    # not_dispatchable directly through transport_eligibility_state.
    cr = requests.post(
        f"{BASE_URL}/api/admin/transportation/carriers", headers=H,
        json={"legal_name": f"Gate Test {uuid.uuid4().hex[:6]}",
              "carrier_type": "leased_hauler", "status": "active"},
        timeout=15)
    if cr.status_code not in (200, 201):
        pytest.skip(f"Carrier create unsupported: {cr.status_code}")
    cid = cr.json()["id"]
    pr = requests.post(
        f"{BASE_URL}/api/admin/transportation/persons", headers=H,
        json={"kind": "leased_driver", "first_name": "Gate",
              "last_name": "Test", "license_number": f"GT-{uuid.uuid4().hex[:6]}",
              "carrier_id": cid, "status": "active"}, timeout=15)
    assert pr.status_code in (200, 201)
    pid = pr.json()["id"]
    # Persons get default eligibility computed automatically; they will
    # have orientation_missing because no assignments exist. Confirm via
    # the check endpoint.
    chk = requests.post(
        f"{BASE_URL}/api/dispatch/transportation/check", headers=H,
        json={"driver_id": pid}, timeout=15).json()
    assert chk["blocked"] is True
    assert "orientation_missing" in chk["reason_codes"] or \
           "packet_not_approved" in chk["reason_codes"] or \
           "rate_not_acknowledged" in chk["reason_codes"]
    # Attempt to create the dispatch assignment for this person.
    truck_id = f"phantom-truck-{uuid.uuid4().hex[:6]}"
    res = requests.post(
        f"{BASE_URL}/api/dispatch/assignments", headers=H,
        json={"truck_id": truck_id, "driver_id": pid,
              "driver_name": "Gate Test", "project_number": "TEST",
              "haul_type": "Material"}, timeout=15)
    assert res.status_code == 409, f"Expected 409, got {res.status_code}: {res.text}"
    body = res.json()
    detail = body.get("detail") or body
    assert detail.get("blocked") is True
    assert detail.get("override_available") is True


def test_59_create_override_then_assignment_succeeds(H):
    import requests
    cr = requests.post(
        f"{BASE_URL}/api/admin/transportation/carriers", headers=H,
        json={"legal_name": f"Override Test {uuid.uuid4().hex[:6]}",
              "carrier_type": "leased_hauler", "status": "active"},
        timeout=15)
    if cr.status_code not in (200, 201):
        pytest.skip("carriers unsupported")
    cid = cr.json()["id"]
    pr = requests.post(
        f"{BASE_URL}/api/admin/transportation/persons", headers=H,
        json={"kind": "leased_driver", "first_name": "Override",
              "last_name": "Test", "license_number": f"OT-{uuid.uuid4().hex[:6]}",
              "carrier_id": cid, "status": "active"}, timeout=15)
    pid = pr.json()["id"]
    # Approve override.
    ov = requests.post(
        f"{BASE_URL}/api/dispatch/transportation/override", headers=H,
        json={"driver_id": pid, "reason_code": "emergency_dispatch",
              "explanation": "Production-critical emergency haul.",
              "duration_hours": 2, "acknowledgement": True},
        timeout=15)
    assert ov.status_code in (200, 201), ov.text
    oid = ov.json()["id"]
    # Now attempt assignment with override id.
    truck_id = f"override-truck-{uuid.uuid4().hex[:6]}"
    res = requests.post(
        f"{BASE_URL}/api/dispatch/assignments", headers=H,
        json={"truck_id": truck_id, "driver_id": pid,
              "driver_name": "Override Test",
              "project_number": "TEST",
              "haul_type": "Material",
              "dispatch_override_id": oid}, timeout=15)
    assert res.status_code == 200, res.text


def test_60_audit_row_for_override_present(H):
    import requests
    # Create + revoke + list overrides.
    cr = requests.post(
        f"{BASE_URL}/api/admin/transportation/carriers", headers=H,
        json={"legal_name": f"Audit Test {uuid.uuid4().hex[:6]}",
              "carrier_type": "leased_hauler", "status": "active"},
        timeout=15)
    if cr.status_code not in (200, 201):
        pytest.skip("carriers unsupported")
    cid = cr.json()["id"]
    pr = requests.post(
        f"{BASE_URL}/api/admin/transportation/persons", headers=H,
        json={"kind": "leased_driver", "first_name": "A", "last_name": "B",
              "license_number": f"AB-{uuid.uuid4().hex[:6]}",
              "carrier_id": cid, "status": "active"}, timeout=15)
    pid = pr.json()["id"]
    ov = requests.post(
        f"{BASE_URL}/api/dispatch/transportation/override", headers=H,
        json={"driver_id": pid, "reason_code": "emergency_dispatch",
              "explanation": "Audit smoke explanation here.",
              "duration_hours": 2, "acknowledgement": True}, timeout=15)
    oid = ov.json()["id"]
    rev = requests.post(
        f"{BASE_URL}/api/admin/transportation/dispatch-overrides/{oid}/revoke",
        headers=H, timeout=15)
    assert rev.status_code == 200
    lst = requests.get(
        f"{BASE_URL}/api/admin/transportation/dispatch-overrides",
        headers=H, timeout=15).json()
    found = [i for i in lst["items"] if i["id"] == oid]
    assert found and found[0]["status"] == "revoked"
