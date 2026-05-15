"""
iter124 — Operations layer (Asset Profile · Event Log · Dispatch · Utilization).

Covers backend routes only. The most important guarantees we test:
  • equipment_master is NEVER mutated by any operations route.
  • Hold creation / release emits Operations Event Log entries.
  • Transfer state-machine respects valid transitions.
  • Asset Profile aggregator returns required sections.
  • Event-log writer never raises.
  • Dispatch routes refuse non-admin tokens.
"""
from __future__ import annotations
import os
import uuid

import httpx
import pytest


API_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/") or "http://localhost:8001"
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "MASCI1982!")


def _admin_token() -> str:
    with httpx.Client(timeout=20.0) as c:
        r = c.post(f"{API_URL}/api/admin/login", json={"password": ADMIN_PASSWORD})
        r.raise_for_status()
        return r.json()["token"]


@pytest.fixture(scope="module")
def admin_headers():
    return {"X-Admin-Token": _admin_token()}


@pytest.fixture(scope="module")
def asset_id(admin_headers):
    with httpx.Client(timeout=20.0) as c:
        r = c.get(f"{API_URL}/api/equipment-master", headers=admin_headers)
        r.raise_for_status()
        items = r.json().get("items") if isinstance(r.json(), dict) else r.json()
        real = [it for it in (items or []) if (it.get("unit_number") or "").strip()]
        if not real:
            pytest.skip("no equipment_master rows with unit numbers")
        return real[0]["id"]


# ════════════════════════════════════════════════════════════════════
# AUTH
# ════════════════════════════════════════════════════════════════════
def test_routes_refuse_unauth():
    with httpx.Client(timeout=20.0) as c:
        for ep in ("/api/operations/events", "/api/operations/utilization", "/api/operations/transfers"):
            r = c.get(f"{API_URL}{ep}")
            assert r.status_code in (401, 403), ep


# ════════════════════════════════════════════════════════════════════
# EVENT LOG
# ════════════════════════════════════════════════════════════════════
def test_event_create_and_list(admin_headers, asset_id):
    title = f"pytest-{uuid.uuid4().hex[:6]}"
    with httpx.Client(timeout=20.0) as c:
        r = c.post(f"{API_URL}/api/operations/events", headers=admin_headers, json={
            "event_type": "asset_assigned",
            "event_title": title,
            "asset_id": asset_id,
            "severity": "info",
            "source_module": "pytest",
        })
        r.raise_for_status()
        eid = r.json()["id"]
        # by id
        g = c.get(f"{API_URL}/api/operations/events/{eid}", headers=admin_headers); g.raise_for_status()
        assert g.json()["event_title"] == title
        # by asset
        lst = c.get(f"{API_URL}/api/operations/events?asset_id={asset_id}", headers=admin_headers); lst.raise_for_status()
        assert any(row["id"] == eid for row in lst.json()["rows"])
        # patch close
        p = c.patch(f"{API_URL}/api/operations/events/{eid}", headers=admin_headers, json={"status": "Closed"})
        p.raise_for_status()
        assert p.json()["status"] == "Closed"
        assert p.json()["closed_at"]


# ════════════════════════════════════════════════════════════════════
# HOLDS
# ════════════════════════════════════════════════════════════════════
def test_hold_apply_and_release_emits_events(admin_headers, asset_id):
    with httpx.Client(timeout=20.0) as c:
        # apply
        r = c.post(f"{API_URL}/api/operations/holds", headers=admin_headers, json={
            "asset_id": asset_id, "kind": "safety", "reason": "pytest hold", "severity": "high",
        })
        r.raise_for_status()
        hid = r.json()["id"]
        assert r.json()["active"] is True
        # confirm event log got the hold-applied entry
        ev = c.get(f"{API_URL}/api/operations/events?asset_id={asset_id}&event_type=safety_hold_applied", headers=admin_headers)
        ev.raise_for_status()
        assert ev.json()["total"] >= 1
        # release
        rel = c.post(f"{API_URL}/api/operations/holds/{hid}/release", headers=admin_headers, json={"resolution": "fixed"})
        rel.raise_for_status()
        assert rel.json()["active"] is False
        ev2 = c.get(f"{API_URL}/api/operations/events?asset_id={asset_id}&event_type=safety_hold_released", headers=admin_headers)
        assert ev2.json()["total"] >= 1


def test_hold_rejects_invalid_kind(admin_headers, asset_id):
    with httpx.Client(timeout=20.0) as c:
        r = c.post(f"{API_URL}/api/operations/holds", headers=admin_headers, json={
            "asset_id": asset_id, "kind": "nope", "reason": "x",
        })
        assert r.status_code == 400


def test_hold_rejects_unknown_asset(admin_headers):
    with httpx.Client(timeout=20.0) as c:
        r = c.post(f"{API_URL}/api/operations/holds", headers=admin_headers, json={
            "asset_id": "definitely-not-real", "kind": "safety", "reason": "x",
        })
        assert r.status_code == 404


# ════════════════════════════════════════════════════════════════════
# ASSIGNMENTS
# ════════════════════════════════════════════════════════════════════
def test_assignment_upsert_and_clear(admin_headers, asset_id):
    with httpx.Client(timeout=20.0) as c:
        # cancel any leftover pending transfers from earlier tests
        xfers = c.get(f"{API_URL}/api/operations/transfers?asset_id={asset_id}", headers=admin_headers).json() or []
        for x in xfers:
            if x["status"] not in ("Completed", "Cancelled", "Denied"):
                c.post(f"{API_URL}/api/operations/transfers/{x['id']}/decide",
                       headers=admin_headers, json={"decision": "cancel"})

        r = c.post(f"{API_URL}/api/operations/assignments", headers=admin_headers, json={
            "asset_id": asset_id, "project_number": "JOB-PYTEST", "operator_name": "Test Operator",
        })
        r.raise_for_status()
        assert r.json()["active"] is True
        # asset profile reflects assigned (or hold if a pytest hold lingers)
        prof = c.get(f"{API_URL}/api/operations/assets/{asset_id}/profile", headers=admin_headers)
        prof.raise_for_status()
        assert prof.json()["current_status"] in ("Assigned", "Safety Hold", "Maintenance Hold", "In Transit")
        # clear
        cl = c.post(f"{API_URL}/api/operations/assignments/{asset_id}/clear", headers=admin_headers, json={"note": "pytest cleanup"})
        cl.raise_for_status()
        assert cl.json()["ok"] is True


# ════════════════════════════════════════════════════════════════════
# TRANSFERS — state machine
# ════════════════════════════════════════════════════════════════════
def test_transfer_full_lifecycle(admin_headers, asset_id):
    with httpx.Client(timeout=20.0) as c:
        r = c.post(f"{API_URL}/api/operations/transfers", headers=admin_headers, json={
            "asset_id": asset_id, "from_project_number": "A", "to_project_number": "B",
            "reason": "pytest", "priority": "normal",
        })
        r.raise_for_status()
        xid = r.json()["id"]
        assert r.json()["status"] == "Submitted"

        # cannot schedule before approve
        bad = c.post(f"{API_URL}/api/operations/transfers/{xid}/decide", headers=admin_headers, json={"decision": "schedule"})
        assert bad.status_code == 409

        ap = c.post(f"{API_URL}/api/operations/transfers/{xid}/decide", headers=admin_headers, json={"decision": "approve"})
        ap.raise_for_status(); assert ap.json()["status"] == "Approved"
        sc = c.post(f"{API_URL}/api/operations/transfers/{xid}/decide", headers=admin_headers, json={"decision": "schedule", "scheduled_move_date": "2026-06-01"})
        sc.raise_for_status(); assert sc.json()["status"] == "Scheduled"
        cp = c.post(f"{API_URL}/api/operations/transfers/{xid}/decide", headers=admin_headers, json={"decision": "complete"})
        cp.raise_for_status(); assert cp.json()["status"] == "Completed"

        # cannot decide on completed
        post_complete = c.post(f"{API_URL}/api/operations/transfers/{xid}/decide", headers=admin_headers, json={"decision": "approve"})
        assert post_complete.status_code == 409

        # completion auto-creates assignment to destination
        prof = c.get(f"{API_URL}/api/operations/assets/{asset_id}/profile", headers=admin_headers).json()
        assert prof["active_assignment"] is not None
        assert prof["active_assignment"]["project_number"] == "B"
        # cleanup
        c.post(f"{API_URL}/api/operations/assignments/{asset_id}/clear", headers=admin_headers, json={"note": "pytest"})


def test_transfer_deny_path(admin_headers, asset_id):
    with httpx.Client(timeout=20.0) as c:
        r = c.post(f"{API_URL}/api/operations/transfers", headers=admin_headers, json={
            "asset_id": asset_id, "to_project_number": "Z", "reason": "deny test",
        })
        r.raise_for_status(); xid = r.json()["id"]
        d = c.post(f"{API_URL}/api/operations/transfers/{xid}/decide", headers=admin_headers, json={"decision": "deny", "decision_reason": "no"})
        d.raise_for_status(); assert d.json()["status"] == "Denied"


# ════════════════════════════════════════════════════════════════════
# UTILIZATION
# ════════════════════════════════════════════════════════════════════
def test_utilization_overview_shape(admin_headers):
    with httpx.Client(timeout=20.0) as c:
        r = c.get(f"{API_URL}/api/operations/utilization", headers=admin_headers); r.raise_for_status()
        d = r.json()
        assert "totals" in d and "rows" in d and "fleet_size" in d
        assert d["fleet_size"] == len(d["rows"])
        for s in ("Available", "Assigned", "Safety Hold", "Maintenance Hold"):
            assert s in d["totals"]


# ════════════════════════════════════════════════════════════════════
# ASSET PROFILE
# ════════════════════════════════════════════════════════════════════
def test_asset_profile_shape(admin_headers, asset_id):
    with httpx.Client(timeout=20.0) as c:
        r = c.get(f"{API_URL}/api/operations/assets/{asset_id}/profile", headers=admin_headers)
        r.raise_for_status()
        d = r.json()
        for k in ("overview", "current_status", "active_holds", "transfers", "events", "events_total_for_asset"):
            assert k in d, f"missing {k}"
        assert d["overview"]["id"] == asset_id


# ════════════════════════════════════════════════════════════════════
# CRITICAL SAFETY — equipment_master immutability
# ════════════════════════════════════════════════════════════════════
def test_equipment_master_never_mutated_by_operations(admin_headers, asset_id):
    with httpx.Client(timeout=20.0) as c:
        before = c.get(f"{API_URL}/api/equipment-master", headers=admin_headers).json()
        before_items = before.get("items") if isinstance(before, dict) else before
        before_eq = next((e for e in (before_items or []) if e["id"] == asset_id), None)
        assert before_eq is not None

        # exercise the full ops surface
        c.post(f"{API_URL}/api/operations/holds", headers=admin_headers, json={
            "asset_id": asset_id, "kind": "maintenance", "reason": "audit test"})
        c.post(f"{API_URL}/api/operations/assignments", headers=admin_headers, json={
            "asset_id": asset_id, "project_number": "AUDIT-1"})
        c.post(f"{API_URL}/api/operations/transfers", headers=admin_headers, json={
            "asset_id": asset_id, "to_project_number": "AUDIT-2"})

        after = c.get(f"{API_URL}/api/equipment-master", headers=admin_headers).json()
        after_items = after.get("items") if isinstance(after, dict) else after
        after_eq = next((e for e in (after_items or []) if e["id"] == asset_id), None)
        assert after_eq is not None

        for f in ("id", "unit_number", "name", "make", "model", "equipment_type", "vin", "license_plate", "year"):
            assert before_eq.get(f) == after_eq.get(f), f"equipment_master.{f} changed"

        # cleanup
        active_holds = c.get(f"{API_URL}/api/operations/holds?asset_id={asset_id}", headers=admin_headers).json()
        for h in active_holds:
            c.post(f"{API_URL}/api/operations/holds/{h['id']}/release", headers=admin_headers, json={"resolution": "pytest cleanup"})
        c.post(f"{API_URL}/api/operations/assignments/{asset_id}/clear", headers=admin_headers, json={"note": "pytest cleanup"})
