"""TRACK 16.11 · Transportation HR Lifecycle Integration regression.

HR is the absolute source of truth. Transportation projects HR
lifecycle facts and reacts. These tests:

* lock the contract (mapper, sync helper, hooks, eligibility, audit)
* verify HR write paths are NEVER mutated or blocked by sync failures
* prove the UI panel renders HR lifecycle data without writing HR
* prove the dispatch gate surfaces human-readable HR reasons
* keep every prior Track 16.xx regression file wired
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest

ROOT = Path("/app")
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

LIB = BACKEND / "lib" / "transport_hr_lifecycle.py"
ELIG = BACKEND / "lib" / "transport_eligibility.py"
GATE_LIB = BACKEND / "lib" / "transport_dispatch_gate.py"
HR_ROUTE = BACKEND / "routes" / "employee_lifecycle.py"
TRANS_ROUTE = BACKEND / "routes" / "transportation.py"
EXP_ROUTE = BACKEND / "routes" / "transportation_experience.py"
FE_LISTS = ROOT / "frontend" / "src" / "pages" / "transportation" / "_lists.jsx"
GATE = ROOT / "scripts" / "deployment_gate.py"


# ===========================================================================
# In-memory fake DB used by sync-helper tests (mirrors 16.10A pattern).
# ===========================================================================
class _Cur:
    def __init__(self, items): self._items = items
    def sort(self, *_, **__): return self
    def limit(self, *_): return self
    async def to_list(self, _n=None): return list(self._items)


def _matches(row: Dict[str, Any], q: Dict[str, Any]) -> bool:
    for k, v in (q or {}).items():
        if k == "$or":
            if not any(_matches(row, sub) for sub in v):
                return False
            continue
        if isinstance(v, dict) and "$in" in v:
            if row.get(k) not in v["$in"]:
                return False
            continue
        if isinstance(v, dict) and "$ne" in v:
            if row.get(k) == v["$ne"]:
                return False
            continue
        if row.get(k) != v:
            return False
    return True


class _Coll:
    def __init__(self): self.rows: List[Dict[str, Any]] = []

    def find(self, q=None, *_, **__):
        return _Cur([r for r in self.rows if _matches(r, q or {})])

    async def find_one(self, q=None, *_, **__):
        for r in self.rows:
            if _matches(r, q or {}):
                return r
        return None

    async def insert_one(self, doc):
        if "_id" not in doc:
            doc["_id"] = f"_id_{len(self.rows)}"
        self.rows.append(doc)
        return type("R", (), {"inserted_id": doc["_id"]})()

    async def update_one(self, q, update, upsert=False):
        for r in self.rows:
            if _matches(r, q or {}):
                if "$set" in update:
                    r.update(update["$set"])
                return type("R", (), {"matched_count": 1, "modified_count": 1})()
        if upsert:
            doc = dict((update or {}).get("$set", {}))
            doc.update((update or {}).get("$setOnInsert", {}))
            doc.update(q or {})
            await self.insert_one(doc)
            return type("R", (), {"matched_count": 0, "modified_count": 0,
                                  "upserted_id": doc.get("_id")})()
        return type("R", (), {"matched_count": 0, "modified_count": 0})()


class _DB:
    def __init__(self):
        self._c: Dict[str, _Coll] = {}

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        if name not in self._c:
            self._c[name] = _Coll()
        return self._c[name]

    def __getitem__(self, k):
        return getattr(self, k)


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _seed_employee(db, **overrides) -> Dict[str, Any]:
    emp = {
        "id": "emp-uuid-1",
        "employee_id": "E1001",
        "name": "Jane Driver",
        "lifecycle_status": "Active",
        "is_active": True,
        "role": "CDL Driver",
        "trade": "driver",
        "department": "Trucking",
        "approved_company_driver": True,
        "cdl_holder": True,
        "driver_status": "active",
        "updated_at": "2026-02-10T12:00:00+00:00",
        "deleted_at": None,
    }
    emp.update(overrides)
    db.employees.rows.append(emp)
    return emp


def _seed_transport_person(db, employee_id="E1001", **overrides):
    person = {
        "_id": "tp-1", "id": "tp-uuid-1", "tenant": "masci",
        "kind": "masci_employee", "employee_id": employee_id,
        "first_name": "Jane", "last_name": "Driver",
        "status": "active", "safety_hold": False,
    }
    person.update(overrides)
    db.transport_persons.rows.append(person)
    return person


# ===========================================================================
# 1 — Mapper exists
# ===========================================================================
def test_01_mapper_exists():
    assert LIB.exists()
    src = LIB.read_text()
    assert "def map_hr_lifecycle_to_transport" in src
    assert "async def sync_transport_person_from_hr" in src


# ===========================================================================
# 2 — Mapper does not mutate employee record
# ===========================================================================
def test_02_mapper_pure():
    from lib.transport_hr_lifecycle import map_hr_lifecycle_to_transport
    emp = {"lifecycle_status": "Active", "role": "Driver",
           "approved_company_driver": True}
    snapshot = dict(emp)
    map_hr_lifecycle_to_transport(emp)
    assert emp == snapshot


# ===========================================================================
# 3 — Active employee maps to non-blocking HR context
# ===========================================================================
def test_03_active_maps_eligible():
    from lib.transport_hr_lifecycle import map_hr_lifecycle_to_transport
    proj = map_hr_lifecycle_to_transport({
        "lifecycle_status": "Active", "role": "CDL Driver",
        "approved_company_driver": True,
    })
    assert proj["transport_state"] == "eligible"
    assert proj["hr_active"] is True


# ===========================================================================
# 4 — Terminated employee → not_dispatchable
# ===========================================================================
def test_04_terminated_blocks():
    from lib.transport_hr_lifecycle import map_hr_lifecycle_to_transport
    proj = map_hr_lifecycle_to_transport({"lifecycle_status": "Terminated"})
    assert proj["transport_state"] == "not_dispatchable"
    assert "hr_status_terminated" in proj["reason_codes"]


# ===========================================================================
# 5 — Inactive employee → not_dispatchable
# ===========================================================================
def test_05_inactive_blocks():
    from lib.transport_hr_lifecycle import map_hr_lifecycle_to_transport
    proj = map_hr_lifecycle_to_transport({"lifecycle_status": "Inactive"})
    assert proj["transport_state"] == "not_dispatchable"
    assert "hr_status_inactive" in proj["reason_codes"]


# ===========================================================================
# 6 — Suspended employee → suspended
# ===========================================================================
def test_06_suspended_blocks():
    from lib.transport_hr_lifecycle import map_hr_lifecycle_to_transport
    proj = map_hr_lifecycle_to_transport({"lifecycle_status": "Suspended"})
    assert proj["transport_state"] == "suspended"
    assert "hr_status_suspended" in proj["reason_codes"]


# ===========================================================================
# 7 — Leave of Absence → suspended (MASCI semantics)
# ===========================================================================
def test_07_leave_blocks():
    from lib.transport_hr_lifecycle import map_hr_lifecycle_to_transport
    proj = map_hr_lifecycle_to_transport({"lifecycle_status": "Leave of Absence"})
    assert proj["transport_state"] == "suspended"
    assert "hr_status_on_leave" in proj["reason_codes"]


# ===========================================================================
# 8 — Unknown HR status → pending_review
# ===========================================================================
def test_08_unknown_status_pending_review():
    from lib.transport_hr_lifecycle import map_hr_lifecycle_to_transport
    proj = map_hr_lifecycle_to_transport({"lifecycle_status": "Mystery"})
    assert proj["transport_state"] == "pending_review"
    assert "hr_status_unknown" in proj["reason_codes"]


# ===========================================================================
# 9 — Role changed away from driver → needs_correction reason
# ===========================================================================
def test_09_role_change_needs_review():
    from lib.transport_hr_lifecycle import map_hr_lifecycle_to_transport
    proj = map_hr_lifecycle_to_transport({
        "lifecycle_status": "Active", "role": "Office Admin",
        "trade": "admin", "approved_company_driver": False,
        "cdl_holder": False,
    })
    assert proj["transport_state"] == "needs_correction"
    assert "hr_role_not_driver" in proj["reason_codes"]


# ===========================================================================
# 10 — Missing employee_id linkage → needs_correction
# ===========================================================================
def test_10_missing_linkage_needs_correction():
    from lib.transport_hr_lifecycle import map_hr_lifecycle_to_transport
    proj = map_hr_lifecycle_to_transport(None)
    assert proj["transport_state"] == "needs_correction"
    assert "hr_employee_missing" in proj["reason_codes"]


# ===========================================================================
# 11 — Sync helper locates existing masci_employee transport_person
# ===========================================================================
def test_11_sync_locates_existing_person():
    from lib.transport_hr_lifecycle import sync_transport_person_from_hr
    db = _DB()
    _seed_employee(db)
    _seed_transport_person(db)
    out = _run(sync_transport_person_from_hr(
        db, "E1001", trigger="hr.test", actor="hr@masci"))
    assert out["status"] == "synced"
    assert out["transport_person_id"] == "tp-uuid-1"


# ===========================================================================
# 12 — Sync helper does not duplicate transport_person rows
# ===========================================================================
def test_12_sync_does_not_duplicate():
    from lib.transport_hr_lifecycle import sync_transport_person_from_hr
    db = _DB()
    _seed_employee(db)
    _seed_transport_person(db)
    _run(sync_transport_person_from_hr(db, "E1001", trigger="hr.test"))
    _run(sync_transport_person_from_hr(db, "E1001", trigger="hr.test"))
    assert len(db.transport_persons.rows) == 1


# ===========================================================================
# 13 — Sync helper NEVER mutates the HR employee record
# ===========================================================================
def test_13_sync_never_mutates_hr():
    from lib.transport_hr_lifecycle import sync_transport_person_from_hr
    db = _DB()
    emp = _seed_employee(db)
    _seed_transport_person(db)
    snap = {k: v for k, v in emp.items() if k != "_id"}
    _run(sync_transport_person_from_hr(db, "E1001", trigger="hr.test"))
    after = {k: v for k, v in db.employees.rows[0].items() if k != "_id"}
    assert after == snap


# ===========================================================================
# 14 — Sync helper only creates transport_person for driver-relevant
# employees. (And in this implementation, it NEVER creates — operators
# explicitly link via Transportation admin.)
# ===========================================================================
def test_14_sync_never_auto_creates_person():
    from lib.transport_hr_lifecycle import sync_transport_person_from_hr
    db = _DB()
    _seed_employee(db, role="Office Manager", approved_company_driver=False,
                   cdl_holder=False, trade="admin")
    out = _run(sync_transport_person_from_hr(db, "E1001", trigger="hr.test"))
    assert out["status"] == "no_transport_person"
    assert len(db.transport_persons.rows) == 0


# ===========================================================================
# 15 — HR hooks fire only AFTER successful HR writes
# ===========================================================================
def test_15_hr_hooks_after_write():
    src = HR_ROUTE.read_text()
    # The hook import must appear ONLY after `await db.employees.insert_one`
    # / `update_one` etc.
    assert "safe_sync_after_hr_write" in src
    create_idx = src.find("await db.employees.insert_one(doc)")
    hook_idx = src.find("safe_sync_after_hr_write")
    assert create_idx > 0 and hook_idx > create_idx, \
        "Create hook must be placed after employees.insert_one"


# ===========================================================================
# 16 — HR write is not blocked by Transportation sync failure
# ===========================================================================
def test_16_sync_failure_is_swallowed():
    from lib.transport_hr_lifecycle import safe_sync_after_hr_write

    class BoomDB:
        def __getattr__(self, _):
            raise RuntimeError("boom")
        def __getitem__(self, _):
            raise RuntimeError("boom")

    # Must NOT raise — HR write success is sacred.
    _run(safe_sync_after_hr_write(BoomDB(), "E1001", trigger="hr.test"))


# ===========================================================================
# 17 — Sync failure creates an action queue item
# ===========================================================================
def test_17_sync_failure_creates_action_item():
    from lib.transport_hr_lifecycle import sync_transport_person_from_hr
    db = _DB()
    # No employee row → triggers hr_not_found path.
    out = _run(sync_transport_person_from_hr(
        db, "E9999", trigger="hr.test", actor="hr@masci"))
    assert out["status"] == "hr_not_found"
    assert any(a["action_type"] == "hr_employee_missing"
               for a in db.transport_action_items.rows)


# ===========================================================================
# 18 — Eligibility includes HR lifecycle facts
# ===========================================================================
def test_18_eligibility_consumes_hr_projection():
    from lib.transport_eligibility import compute_transport_eligibility
    record = {"kind": "masci_employee", "status": "active"}
    ctx = {
        "hr_transport_state": "not_dispatchable",
        "hr_reason_codes": ["hr_status_terminated"],
        "hr_reason_labels": ["Employee is terminated in HR"],
        "hr_source_status": "Terminated",
    }
    out = compute_transport_eligibility("person", record, ctx)
    assert out["state"] == "not_dispatchable"
    assert any(r["code"] == "hr_status_terminated" for r in out["reasons"])


# ===========================================================================
# 19 — Terminated HR status blocks dispatch (via gate human map)
# ===========================================================================
def test_19_terminated_label_in_gate_map():
    from lib.transport_dispatch_gate import HUMAN_REASONS
    assert HUMAN_REASONS.get("hr_status_terminated") == \
        "Employee is terminated in HR"


# ===========================================================================
# 20 — On-leave HR status blocks dispatch (via gate human map)
# ===========================================================================
def test_20_on_leave_label_in_gate_map():
    from lib.transport_dispatch_gate import HUMAN_REASONS
    assert HUMAN_REASONS.get("hr_status_on_leave") == \
        "Employee is on leave in HR"


# ===========================================================================
# 21 — Role mismatch surfaces in the gate envelope
# ===========================================================================
def test_21_role_mismatch_label_in_gate_map():
    from lib.transport_dispatch_gate import HUMAN_REASONS
    assert HUMAN_REASONS.get("hr_role_not_driver") == \
        "Employee role requires Transportation review"


# ===========================================================================
# 22 — Driver workspace UI includes HR lifecycle panel
# ===========================================================================
def test_22_ui_driver_workspace_panel():
    src = FE_LISTS.read_text()
    assert "driver-hr-lifecycle-panel" in src
    assert "HR lifecycle projection" in src
    assert "driver-hr-projection-chip" in src


# ===========================================================================
# 23 — HR UI is not cluttered with Transportation write controls
# ===========================================================================
def test_23_hr_ui_no_transport_writes():
    """The HR-side employee surface must remain free of Transportation
    write actions in this track. We only verify the HR routes file
    introduces no NEW writeable transportation endpoints — the only
    HR-side touch is the additive sync hook (read-only effect)."""
    src = HR_ROUTE.read_text()
    # Track 16.11 must NOT introduce new transport write endpoints in
    # the HR file. (No POST/PATCH/DELETE definitions for transportation
    # paths.)
    for forbidden in (
        '"/transport',
        '"/api/transport',
        "transport_persons.update_one",
        "transport_persons.insert_one",
    ):
        assert forbidden not in src, f"HR route file must not write transport: {forbidden}"


# ===========================================================================
# 24 — Audit rows written for sync attempt / success / failure
# ===========================================================================
def test_24_audit_rows_written():
    from lib.transport_hr_lifecycle import sync_transport_person_from_hr
    db = _DB()
    _seed_employee(db, lifecycle_status="Terminated")
    _seed_transport_person(db)
    _run(sync_transport_person_from_hr(
        db, "E1001", trigger="hr.test", actor="hr@masci"))
    kinds = [a.get("kind") for a in db.audit_events.rows]
    assert "transport_hr_sync_succeeded" in kinds


# ===========================================================================
# 25 — No duplicate employee identity introduced
# ===========================================================================
def test_25_no_new_employee_collection():
    src = LIB.read_text()
    # We must read from db.employees (HR source); never create
    # a parallel collection like db.hr_employees / db.transport_employees.
    assert "db.employees.find_one" in src
    forbidden_collections = ("db.hr_employees", "db.transport_employees",
                              "db.employee_directory")
    for c in forbidden_collections:
        assert c not in src


# ===========================================================================
# 26 — No destructive HR migration introduced
# ===========================================================================
def test_26_no_destructive_hr_migration():
    src = LIB.read_text()
    src_hr = HR_ROUTE.read_text()
    for forbidden in ("drop_collection", "delete_many", "drop_indexes"):
        assert forbidden not in src
    # HR route file may still call delete_many elsewhere, so check
    # we did not ADD any such call in this track.
    # (Heuristic: ensure no occurrence of "db.employees.delete_many" near
    # the new hook.)
    assert "db.employees.delete_many" not in src_hr


# ===========================================================================
# 27 — No HR route removals or renames
# ===========================================================================
def test_27_hr_routes_preserved():
    src = HR_ROUTE.read_text()
    for route in (
        '@router.get("/api/hr/employees")',
        '@router.post("/api/hr/employees")',
        '@router.patch("/api/hr/employees/{employee_id}")',
        '@router.post("/api/hr/employees/{employee_id}/status")',
        '@router.post("/api/hr/employees/{employee_id}/reactivate")',
    ):
        assert route in src, f"HR route missing: {route}"


# ===========================================================================
# 28 — Optional email route added in this track is internal_only + dry_run
# ===========================================================================
def test_28_email_route_internal_dry_run():
    """If TRANSPORT_HR_LIFECYCLE_SYNC_ALERT exists in the codebase, it
    must default to internal_only=True / enabled=False / dry_run=True.
    Track 16.11 does NOT enable any new external send."""
    # Action items reference the route key — verify the helper writes it.
    src = LIB.read_text()
    assert "TRANSPORT_HR_LIFECYCLE_SYNC_ALERT" in src
    # And the helper must NEVER auto-enable / auto-send. No send/dispatch
    # calls in the lifecycle lib at all.
    assert "_send_via_routing_v2" not in src
    assert "resolve_and_audit" not in src


# ===========================================================================
# 29 — No SMS / Twilio / push references
# ===========================================================================
def test_29_no_sms_or_push():
    src = LIB.read_text()
    for forbidden in ("twilio", "TWILIO", "sendSms", "push_notification",
                       "fcm.googleapis"):
        assert forbidden not in src


# ===========================================================================
# 30 — Forbidden punitive vocabulary not introduced in user-facing labels
# ===========================================================================
def test_30_no_punitive_language():
    src = LIB.read_text()
    # Look at the human label dict + reason builders.
    for forbidden in ("Rejected", "Denied", "Failed —", "rejected!", "denied!"):
        assert forbidden not in src, f"Punitive word leaked: {forbidden}"


# ===========================================================================
# 31 — Track 16.10A tests still wired into the gate
# ===========================================================================
def test_31_track_16_10a_preserved():
    src = GATE.read_text()
    assert "test_track_16_10a_transport_command_digest" in src


# ===========================================================================
# 32 — deployment_gate.py includes Track 16.11 tests
# ===========================================================================
def test_32_deployment_gate_includes_track_16_11():
    src = GATE.read_text()
    assert "test_track_16_11_transport_hr_lifecycle_integration" in src


# ===========================================================================
# Bonus end-to-end shape tests — projection is persisted on the
# transport_person and surfaced to the workspace API.
# ===========================================================================
def test_99_projection_persisted_on_person():
    from lib.transport_hr_lifecycle import sync_transport_person_from_hr
    db = _DB()
    _seed_employee(db, lifecycle_status="Leave of Absence")
    _seed_transport_person(db)
    _run(sync_transport_person_from_hr(db, "E1001", trigger="hr.test"))
    person = db.transport_persons.rows[0]
    assert person["hr_projection"]["transport_state"] == "suspended"
    assert person["hr_projection"]["source_status"] == "Leave of Absence"
    assert person["hr_projection"]["synced_at"]


def test_99b_eligibility_state_recomputed():
    from lib.transport_hr_lifecycle import sync_transport_person_from_hr
    db = _DB()
    _seed_employee(db, lifecycle_status="Terminated")
    _seed_transport_person(db)
    _run(sync_transport_person_from_hr(db, "E1001", trigger="hr.test"))
    elig = db.transport_eligibility_state.rows
    assert elig, "eligibility row must be upserted"
    assert elig[0]["state"] == "not_dispatchable"
    assert any(r["code"] == "hr_status_terminated"
               for r in elig[0]["reasons"])
