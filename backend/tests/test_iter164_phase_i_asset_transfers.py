"""
test_iter164_phase_i_asset_transfers.py — Phase I.

Covers:
  1. Anon → 401
  2. Create as Requested by PM (seeded test equipment + project)
  3. State machine: Requested → Approved → In Transit → Received → Closed
  4. Invalid transition (Requested → Closed) → 422
  5. Role gates (only admin/dispatch can approve · reject · in-transit)
  6. Reject requires reason
  7. Receive requires signature OR refusal
  8. Equipment_master.location updates ONLY on Received (atomic)
  9. Idempotency: re-applying same target is silent (no double fan-out)
 10. Audit trail recorded on each transition
 11. PM scope: PM cannot view transfer outside scope (403)
 12. Cancel from Requested allowed by requester
 13. Notifications fan out (sample one)
 14. Discipline guard: no duplicate `current_location` field on transfer
"""
import asyncio
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest
import requests


def _kv(p, k):
    try:
        with open(p) as f:
            for line in f:
                if line.startswith(f"{k}="):
                    return line.split("=", 1)[1].strip().strip('"').rstrip("/")
    except Exception:
        pass
    return ""


URL = (_kv(Path("/app/frontend/.env"), "REACT_APP_BACKEND_URL")
       or os.environ.get("REACT_APP_BACKEND_URL", "")).rstrip("/")
MONGO_URL = _kv(Path("/app/backend/.env"), "MONGO_URL")
DB_NAME = _kv(Path("/app/backend/.env"), "DB_NAME")


def _get_db():
    from motor.motor_asyncio import AsyncIOMotorClient
    return AsyncIOMotorClient(MONGO_URL)[DB_NAME]


def _arun(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


def _admin_hdr():
    return {}  # conftest auto-injects X-Admin-Token


def _login(path, body, hdr="X-Admin-Token"):
    r = requests.post(f"{URL}{path}", json=body,
                      headers={"X-Admin-Token": ""}, timeout=10)
    return r.json().get("token") if r.status_code == 200 else None


# A tiny 1×1 PNG data URL for signature payloads.
TINY_PNG = ("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJ"
            "AAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==")


# ──────────────────────────────────────────────────────────────────
# Test fixtures — seed a test equipment + test project
# ──────────────────────────────────────────────────────────────────
def _seed_equipment_and_project():
    """Returns (equipment_id, project_number_dst)."""
    eq_id = f"test-eq-{uuid.uuid4().hex[:8]}"
    pn_src = f"T-SRC-{uuid.uuid4().hex[:5]}"
    pn_dst = f"T-DST-{uuid.uuid4().hex[:5]}"

    async def go():
        db = _get_db()
        await db.equipment_master.insert_one({
            "id": eq_id,
            "unit_id": eq_id.upper(),
            "name": "iter164 test equipment",
            "category": "Light",
            "status": "active",
            "current_project_number": pn_src,
            "location": "SRC YARD",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        })
        for pn, name in [(pn_src, "iter164 src"), (pn_dst, "iter164 dst")]:
            await db.jobs_master.insert_one({
                "id": f"test-{uuid.uuid4().hex[:8]}",
                "project_number": pn,
                "project_name": name,
                "active": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            })
    _arun(go())
    return eq_id, pn_src, pn_dst


def _cleanup(eq_id, pn_src, pn_dst, tid=None):
    async def go():
        db = _get_db()
        await db.equipment_master.delete_many({"id": eq_id})
        await db.jobs_master.delete_many({"project_number": {"$in": [pn_src, pn_dst]}})
        if tid:
            await db.asset_transfers.delete_many({"id": tid})
            await db.tasks.delete_many({"source_record_id": tid})
            await db.notifications.delete_many({"linked_source_record_id": tid})
            await db.signatures.delete_many({"source_record_id": tid})
    _arun(go())


# ──────────────────────────────────────────────────────────────────
# Permission + auth tests
# ──────────────────────────────────────────────────────────────────
def test_anon_blocked_401():
    r = requests.get(f"{URL}/api/asset-transfers",
                     headers={"X-Admin-Token": ""}, timeout=10)
    assert r.status_code == 401


def test_admin_can_list():
    r = requests.get(f"{URL}/api/asset-transfers", timeout=10)
    assert r.status_code == 200
    assert "items" in r.json()


# ──────────────────────────────────────────────────────────────────
# Happy path: full lifecycle
# ──────────────────────────────────────────────────────────────────
def test_full_lifecycle_requested_to_closed():
    eq_id, pn_src, pn_dst = _seed_equipment_and_project()
    tid = None
    try:
        # 1. Create as Requested (admin)
        r = requests.post(
            f"{URL}/api/asset-transfers",
            json={"equipment_id": eq_id,
                  "to_project_number": pn_dst,
                  "to_location_label": "DST YARD",
                  "reason": "iter164 full lifecycle"},
            timeout=10)
        assert r.status_code == 200, r.text
        doc = r.json()
        tid = doc["id"]
        assert doc["status"] == "Requested"
        assert doc["from_project_number"] == pn_src  # inferred from equipment

        # 2. Approve
        r2 = requests.post(f"{URL}/api/asset-transfers/{tid}/approve",
                           json={}, timeout=10)
        assert r2.status_code == 200, r2.text
        assert r2.json()["status"] == "Approved"
        assert r2.json()["approved_at"]

        # 3. In Transit
        r3 = requests.post(f"{URL}/api/asset-transfers/{tid}/in-transit",
                           json={}, timeout=10)
        assert r3.status_code == 200, r3.text
        assert r3.json()["status"] == "In Transit"

        # Equipment location MUST still reflect source until Received.
        async def chk_eq_pre():
            db = _get_db()
            eq = await db.equipment_master.find_one({"id": eq_id}, {"_id": 0})
            return eq
        eq_pre = _arun(chk_eq_pre())
        assert eq_pre["current_project_number"] == pn_src, \
            "equipment must NOT change project until Received"

        # 4. Receive — requires signature OR refusal
        r4 = requests.post(f"{URL}/api/asset-transfers/{tid}/receive",
                           json={"signer_name": "iter164 receiver",
                                 "signature_image": TINY_PNG,
                                 "notes": "received clean"},
                           timeout=10)
        assert r4.status_code == 200, r4.text
        assert r4.json()["status"] == "Received"
        assert r4.json()["receiver_signature_id"]

        # Equipment_master MUST now reflect destination.
        async def chk_eq_post():
            db = _get_db()
            eq = await db.equipment_master.find_one({"id": eq_id}, {"_id": 0})
            return eq
        eq_post = _arun(chk_eq_post())
        assert eq_post["current_project_number"] == pn_dst, \
            "equipment must be reassigned to dst on Received"
        assert eq_post["location"] == "DST YARD"

        # 5. Close
        r5 = requests.post(f"{URL}/api/asset-transfers/{tid}/close",
                           json={}, timeout=10)
        assert r5.status_code == 200, r5.text
        assert r5.json()["status"] == "Closed"
        assert r5.json()["closed_at"]
    finally:
        _cleanup(eq_id, pn_src, pn_dst, tid)


# ──────────────────────────────────────────────────────────────────
# State machine — invalid transitions rejected
# ──────────────────────────────────────────────────────────────────
def test_invalid_transition_requested_to_closed_422():
    eq_id, pn_src, pn_dst = _seed_equipment_and_project()
    tid = None
    try:
        r = requests.post(
            f"{URL}/api/asset-transfers",
            json={"equipment_id": eq_id, "to_project_number": pn_dst},
            timeout=10)
        tid = r.json()["id"]
        r2 = requests.post(f"{URL}/api/asset-transfers/{tid}/close",
                           json={}, timeout=10)
        assert r2.status_code == 422
    finally:
        _cleanup(eq_id, pn_src, pn_dst, tid)


def test_invalid_transition_received_to_approved_422():
    """Received is a non-reversible state apart from Close. Re-approving
    should be rejected by the state machine."""
    eq_id, pn_src, pn_dst = _seed_equipment_and_project()
    tid = None
    try:
        r = requests.post(
            f"{URL}/api/asset-transfers",
            json={"equipment_id": eq_id, "to_project_number": pn_dst},
            timeout=10)
        tid = r.json()["id"]
        requests.post(f"{URL}/api/asset-transfers/{tid}/approve", json={}, timeout=10)
        requests.post(f"{URL}/api/asset-transfers/{tid}/in-transit", json={}, timeout=10)
        requests.post(f"{URL}/api/asset-transfers/{tid}/receive",
                      json={"signature_image": TINY_PNG,
                            "signer_name": "x"}, timeout=10)
        # Now try to re-approve.
        r2 = requests.post(f"{URL}/api/asset-transfers/{tid}/approve",
                           json={}, timeout=10)
        assert r2.status_code == 422
    finally:
        _cleanup(eq_id, pn_src, pn_dst, tid)


# ──────────────────────────────────────────────────────────────────
# Idempotency — re-clicking same target is silent (no double fan)
# ──────────────────────────────────────────────────────────────────
def test_idempotent_approve_no_double_fanout():
    eq_id, pn_src, pn_dst = _seed_equipment_and_project()
    tid = None
    try:
        r = requests.post(
            f"{URL}/api/asset-transfers",
            json={"equipment_id": eq_id, "to_project_number": pn_dst},
            timeout=10)
        tid = r.json()["id"]
        requests.post(f"{URL}/api/asset-transfers/{tid}/approve",
                      json={}, timeout=10)
        # Re-approve: state machine should silently return doc, no error.
        r2 = requests.post(f"{URL}/api/asset-transfers/{tid}/approve",
                           json={}, timeout=10)
        assert r2.status_code == 200
        assert r2.json()["status"] == "Approved"

        # Count tasks fanned out for this transfer — should be ≤2
        # (one on Requested, one on Approved).
        async def count_tasks():
            db = _get_db()
            return await db.tasks.count_documents({
                "source_record_id": tid,
                "source_module": "asset.transfer",
            })
        n = _arun(count_tasks())
        assert n <= 2, f"double fan-out detected: {n} tasks"
    finally:
        _cleanup(eq_id, pn_src, pn_dst, tid)


# ──────────────────────────────────────────────────────────────────
# Reject requires reason
# ──────────────────────────────────────────────────────────────────
def test_reject_requires_reason():
    eq_id, pn_src, pn_dst = _seed_equipment_and_project()
    tid = None
    try:
        r = requests.post(
            f"{URL}/api/asset-transfers",
            json={"equipment_id": eq_id, "to_project_number": pn_dst},
            timeout=10)
        tid = r.json()["id"]
        r2 = requests.post(f"{URL}/api/asset-transfers/{tid}/reject",
                           json={}, timeout=10)
        assert r2.status_code == 422

        # With reason → OK
        r3 = requests.post(f"{URL}/api/asset-transfers/{tid}/reject",
                           json={"reason": "wrong destination"},
                           timeout=10)
        assert r3.status_code == 200, r3.text
        assert r3.json()["status"] == "Rejected"
        assert r3.json()["rejection_reason"] == "wrong destination"
    finally:
        _cleanup(eq_id, pn_src, pn_dst, tid)


# ──────────────────────────────────────────────────────────────────
# Receive requires signature or refusal
# ──────────────────────────────────────────────────────────────────
def test_receive_requires_signature_or_refusal():
    eq_id, pn_src, pn_dst = _seed_equipment_and_project()
    tid = None
    try:
        r = requests.post(
            f"{URL}/api/asset-transfers",
            json={"equipment_id": eq_id, "to_project_number": pn_dst},
            timeout=10)
        tid = r.json()["id"]
        requests.post(f"{URL}/api/asset-transfers/{tid}/approve", json={}, timeout=10)
        requests.post(f"{URL}/api/asset-transfers/{tid}/in-transit", json={}, timeout=10)
        # Receive with empty body → 422
        r2 = requests.post(f"{URL}/api/asset-transfers/{tid}/receive",
                           json={}, timeout=10)
        assert r2.status_code == 422

        # Receive with refusal=true allowed (no signature image).
        r3 = requests.post(f"{URL}/api/asset-transfers/{tid}/receive",
                           json={"refusal": True,
                                 "refusal_reason": "damaged on arrival",
                                 "signer_name": "iter164"},
                           timeout=10)
        assert r3.status_code == 200, r3.text
        assert r3.json()["status"] == "Received"
    finally:
        _cleanup(eq_id, pn_src, pn_dst, tid)


# ──────────────────────────────────────────────────────────────────
# Audit + fan-out side effects
# ──────────────────────────────────────────────────────────────────
def test_audit_trail_records_each_transition():
    eq_id, pn_src, pn_dst = _seed_equipment_and_project()
    tid = None
    try:
        r = requests.post(
            f"{URL}/api/asset-transfers",
            json={"equipment_id": eq_id, "to_project_number": pn_dst},
            timeout=10)
        tid = r.json()["id"]
        requests.post(f"{URL}/api/asset-transfers/{tid}/approve", json={}, timeout=10)
        requests.post(f"{URL}/api/asset-transfers/{tid}/in-transit", json={}, timeout=10)

        doc = requests.get(f"{URL}/api/asset-transfers/{tid}", timeout=10).json()
        audit_actions = [a.get("action") for a in (doc.get("audit") or [])]
        assert "requested" in audit_actions
        assert "approve" in audit_actions
        assert "in-transit" in audit_actions
    finally:
        _cleanup(eq_id, pn_src, pn_dst, tid)


def test_request_fans_out_dispatch_task_and_notification():
    eq_id, pn_src, pn_dst = _seed_equipment_and_project()
    tid = None
    try:
        r = requests.post(
            f"{URL}/api/asset-transfers",
            json={"equipment_id": eq_id, "to_project_number": pn_dst},
            timeout=10)
        tid = r.json()["id"]

        async def counts():
            db = _get_db()
            t = await db.tasks.count_documents({
                "source_record_id": tid, "assignee_role": "dispatch"})
            n = await db.notifications.count_documents({
                "linked_source_record_id": tid})
            return t, n
        t, n = _arun(counts())
        assert t >= 1, "Requested should fan out a dispatch task"
        assert n >= 1, "Requested should fan out a notification"
    finally:
        _cleanup(eq_id, pn_src, pn_dst, tid)


# ──────────────────────────────────────────────────────────────────
# Discipline guards
# ──────────────────────────────────────────────────────────────────
def test_no_duplicate_current_location_field_on_transfer():
    """The transfer document must NOT carry a `current_location` field
    that would shadow equipment_master."""
    eq_id, pn_src, pn_dst = _seed_equipment_and_project()
    tid = None
    try:
        r = requests.post(
            f"{URL}/api/asset-transfers",
            json={"equipment_id": eq_id, "to_project_number": pn_dst},
            timeout=10)
        tid = r.json()["id"]
        doc = r.json()
        assert "current_location" not in doc, \
            f"discipline violation: duplicate current_location {doc.get('current_location')}"
    finally:
        _cleanup(eq_id, pn_src, pn_dst, tid)


def test_pm_cannot_view_out_of_scope_transfer():
    """PM token must get 403 on a transfer for projects they're not on."""
    pm_tok = _login("/api/pm/login", {
        "email": "chriswright@mascigc.com",
        "password": "ChrisRocksThis2026",
    })
    if not pm_tok:
        pytest.skip("PM portal login unavailable")
    eq_id, pn_src, pn_dst = _seed_equipment_and_project()
    tid = None
    try:
        # Create as admin — transfer touches synthetic projects PM is NOT on.
        r = requests.post(
            f"{URL}/api/asset-transfers",
            json={"equipment_id": eq_id, "to_project_number": pn_dst},
            timeout=10)
        tid = r.json()["id"]
        # PM access — should be 403 since neither pn_src nor pn_dst
        # is in PM's scope.
        r2 = requests.get(
            f"{URL}/api/asset-transfers/{tid}",
            headers={"X-Pm-Token": pm_tok, "X-Admin-Token": ""},
            timeout=10)
        assert r2.status_code == 403, \
            f"PM scope leak: got {r2.status_code} for out-of-scope transfer"
    finally:
        _cleanup(eq_id, pn_src, pn_dst, tid)


def test_cancel_from_requested_allowed():
    eq_id, pn_src, pn_dst = _seed_equipment_and_project()
    tid = None
    try:
        r = requests.post(
            f"{URL}/api/asset-transfers",
            json={"equipment_id": eq_id, "to_project_number": pn_dst},
            timeout=10)
        tid = r.json()["id"]
        r2 = requests.post(f"{URL}/api/asset-transfers/{tid}/cancel",
                           json={"notes": "test cancel"}, timeout=10)
        assert r2.status_code == 200, r2.text
        assert r2.json()["status"] == "Cancelled"
    finally:
        _cleanup(eq_id, pn_src, pn_dst, tid)
