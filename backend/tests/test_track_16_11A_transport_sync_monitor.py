"""TRACK 16.11A · HR Visibility + Transportation Consistency Engine.

Hard contract locks + pure-function tests + end-to-end shape tests for
the read-only HR ↔ Transportation sync monitor introduced in this
track. HR remains the absolute source of truth.
"""
from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

import pytest  # noqa: F401  (pytest auto-discovers tests below)

ROOT = Path("/app")
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

LIB = BACKEND / "lib" / "transport_sync_monitor.py"
HR_LIB = BACKEND / "lib" / "transport_hr_lifecycle.py"
ROUTE = BACKEND / "routes" / "transportation_automation.py"
HR_ROUTE = BACKEND / "routes" / "employee_lifecycle.py"
FE_HRHUB = ROOT / "frontend" / "src" / "pages" / "HrHub.jsx"
FE_HREMP = ROOT / "frontend" / "src" / "pages" / "HrEmployees.jsx"
FE_TXVIEWS = ROOT / "frontend" / "src" / "pages" / "transportation" / "_views.jsx"
FE_TXCQ = ROOT / "frontend" / "src" / "pages" / "transportation" / "_command_queue.jsx"
GATE = ROOT / "scripts" / "deployment_gate.py"


# ===========================================================================
# In-memory fake DB (matches Track 16.11 test harness)
# ===========================================================================
def _matches(row: Dict[str, Any], q: Dict[str, Any]) -> bool:
    for k, v in (q or {}).items():
        if k == "$or":
            if not any(_matches(row, sub) for sub in v):
                return False
            continue
        if k == "$in":
            return row in v
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


class _Cur:
    def __init__(self, items): self._items = list(items)

    def sort(self, *args, **__):
        # Best-effort 1-key sort; suitable for tests.
        if args and isinstance(args[0], list) and args[0]:
            key, direction = args[0][0]
            reverse = direction == -1
            self._items.sort(key=lambda r: r.get(key) or "", reverse=reverse)
        elif args and isinstance(args[0], str):
            direction = args[1] if len(args) > 1 else 1
            self._items.sort(key=lambda r: r.get(args[0]) or "",
                             reverse=direction == -1)
        return self

    def limit(self, _): return self

    async def to_list(self, _n=None): return list(self._items)


class _Coll:
    def __init__(self): self.rows: List[Dict[str, Any]] = []

    def find(self, q=None, *_, **__):
        return _Cur([r for r in self.rows if _matches(r, q or {})])

    async def find_one(self, q=None, *_, **kwargs):
        rows = [r for r in self.rows if _matches(r, q or {})]
        sort = kwargs.get("sort")
        if sort:
            key, direction = sort[0]
            rows.sort(key=lambda r: r.get(key) or "", reverse=direction == -1)
        return rows[0] if rows else None

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


def _seed_emp(db, **kw) -> Dict[str, Any]:
    emp = {
        "id": "emp-1", "employee_id": "E2001", "name": "Pat Hauler",
        "lifecycle_status": "Active", "is_active": True,
        "role": "CDL Driver", "trade": "driver",
        "approved_company_driver": True, "cdl_holder": True,
        "driver_status": "active",
        "updated_at": "2026-02-09T12:00:00+00:00",
        "deleted_at": None,
    }
    emp.update(kw)
    db.employees.rows.append(emp)
    return emp


def _seed_person(db, *, employee_id="E2001", projection=None, **kw):
    person = {
        "_id": "tp-x", "id": "tp-x", "tenant": "masci",
        "kind": "masci_employee", "employee_id": employee_id,
        "first_name": "Pat", "last_name": "Hauler",
        "status": "active",
    }
    if projection is not None:
        person["hr_projection"] = projection
    person.update(kw)
    db.transport_persons.rows.append(person)
    return person


def _seed_elig(db, *, person_id="tp-x", state="eligible", reasons=None):
    db.transport_eligibility_state.rows.append({
        "tenant": "masci", "target_type": "person",
        "target_id": person_id, "state": state,
        "reasons": reasons or [], "computed_at": "2026-02-09T12:00:00+00:00",
    })


# ===========================================================================
# 1 — Module exists
# ===========================================================================
def test_01_sync_monitor_exists():
    assert LIB.exists()
    src = LIB.read_text()
    assert "async def scan_hr_transport_consistency" in src
    assert "async def derive_employee_transport_status" in src
    assert "async def hr_dashboard_transport_readiness" in src
    assert "async def transportation_dashboard_hr_health" in src


# ===========================================================================
# 2 — Classifier is pure (no I/O, no async)
# ===========================================================================
def test_02_classifier_pure():
    from lib.transport_sync_monitor import classify_mismatch
    out = classify_mismatch(hr_record=None, transport_person=None,
                            projection=None, eligibility=None)
    assert out == []


# ===========================================================================
# 3 — Missing HR linkage produces 'linkage_missing'
# ===========================================================================
def test_03_linkage_missing():
    from lib.transport_sync_monitor import classify_mismatch
    out = classify_mismatch(
        hr_record=None,
        transport_person={"id": "tp-1", "employee_id": "E1"},
        projection=None, eligibility=None,
    )
    codes = [r["code"] for r in out]
    assert "linkage_missing" in codes
    assert out[0]["severity"] in ("block", "critical")


# ===========================================================================
# 4 — Stale projection detected
# ===========================================================================
def test_04_projection_stale():
    from lib.transport_sync_monitor import classify_mismatch
    now = datetime.now(timezone.utc)
    old = (now - timedelta(days=30)).isoformat()
    out = classify_mismatch(
        hr_record={"id": "e1", "employee_id": "E1", "lifecycle_status": "Active"},
        transport_person={"id": "tp-1", "employee_id": "E1"},
        projection={"transport_state": "eligible", "synced_at": old,
                    "reason_codes": []},
        eligibility={"state": "eligible"},
        now=now, stale_days=7,
    )
    assert any(r["code"] == "projection_stale" for r in out)


# ===========================================================================
# 5 — Termination mismatch detected
# ===========================================================================
def test_05_termination_mismatch():
    from lib.transport_sync_monitor import classify_mismatch
    out = classify_mismatch(
        hr_record={"id": "e1", "employee_id": "E1",
                   "lifecycle_status": "Terminated"},
        transport_person={"id": "tp-1", "employee_id": "E1"},
        projection={"transport_state": "eligible", "reason_codes": []},
        eligibility={"state": "eligible"},
    )
    codes = [r["code"] for r in out]
    assert "termination_mismatch" in codes


# ===========================================================================
# 6 — Leave mismatch detected
# ===========================================================================
def test_06_leave_mismatch():
    from lib.transport_sync_monitor import classify_mismatch
    out = classify_mismatch(
        hr_record={"id": "e1", "employee_id": "E1",
                   "lifecycle_status": "Leave of Absence"},
        transport_person={"id": "tp-1", "employee_id": "E1"},
        projection={"transport_state": "suspended", "reason_codes": []},
        eligibility={"state": "eligible"},
    )
    codes = [r["code"] for r in out]
    assert "leave_mismatch" in codes


# ===========================================================================
# 7 — Role mismatch detected
# ===========================================================================
def test_07_role_mismatch():
    from lib.transport_sync_monitor import classify_mismatch
    out = classify_mismatch(
        hr_record={"id": "e1", "employee_id": "E1",
                   "lifecycle_status": "Active", "role": "Office"},
        transport_person={"id": "tp-1", "employee_id": "E1"},
        projection={"transport_state": "needs_correction",
                    "reason_codes": ["hr_role_not_driver"]},
        eligibility={"state": "needs_correction"},
    )
    assert any(r["code"] == "role_mismatch" for r in out)


# ===========================================================================
# 8 — HR status unknown surfaces
# ===========================================================================
def test_08_hr_status_unknown():
    from lib.transport_sync_monitor import classify_mismatch
    out = classify_mismatch(
        hr_record={"id": "e1", "employee_id": "E1",
                   "lifecycle_status": "Mystery"},
        transport_person={"id": "tp-1", "employee_id": "E1"},
        projection={"transport_state": "pending_review",
                    "reason_codes": ["hr_status_unknown"]},
        eligibility={"state": "pending_review"},
    )
    assert any(r["code"] == "hr_status_unknown" for r in out)


# ===========================================================================
# 9 — Scanner produces healthy report when zero mismatches
# ===========================================================================
def test_09_scanner_healthy_empty_db():
    from lib.transport_sync_monitor import scan_hr_transport_consistency
    db = _DB()
    out = _run(scan_hr_transport_consistency(db, create_action_items=False))
    assert out["health"] == "healthy"
    assert out["counts"]["sync_mismatches"] == 0


# ===========================================================================
# 10 — Scanner walks both transport_persons and HR
# ===========================================================================
def test_10_scanner_counts_population():
    from lib.transport_sync_monitor import scan_hr_transport_consistency
    db = _DB()
    _seed_emp(db)
    _seed_person(db)
    out = _run(scan_hr_transport_consistency(db, create_action_items=False))
    assert out["counts"]["drivers_checked"] == 1
    assert out["counts"]["employees_checked"] == 1


# ===========================================================================
# 11 — Scanner detects termination_mismatch end-to-end
# ===========================================================================
def test_11_scanner_termination_mismatch():
    from lib.transport_sync_monitor import scan_hr_transport_consistency
    db = _DB()
    _seed_emp(db, lifecycle_status="Terminated")
    _seed_person(db, projection={"transport_state": "eligible",
                                   "reason_codes": []})
    _seed_elig(db, state="eligible")
    out = _run(scan_hr_transport_consistency(db))
    codes = [m["code"] for m in out["mismatches"]]
    assert "termination_mismatch" in codes
    assert out["health"] == "critical"


# ===========================================================================
# 12 — Scanner creates idempotent action items
# ===========================================================================
def test_12_scanner_action_items_idempotent():
    from lib.transport_sync_monitor import scan_hr_transport_consistency
    db = _DB()
    _seed_emp(db, lifecycle_status="Terminated")
    _seed_person(db, projection={"transport_state": "eligible",
                                   "reason_codes": []})
    _seed_elig(db, state="eligible")
    _run(scan_hr_transport_consistency(db))
    first = len(db.transport_action_items.rows)
    _run(scan_hr_transport_consistency(db))
    second = len(db.transport_action_items.rows)
    assert first == second, "duplicate action items must not be created"


# ===========================================================================
# 13 — Scanner never mutates the HR record
# ===========================================================================
def test_13_scanner_never_mutates_hr():
    from lib.transport_sync_monitor import scan_hr_transport_consistency
    db = _DB()
    emp = _seed_emp(db, lifecycle_status="Terminated")
    _seed_person(db, projection={"transport_state": "eligible",
                                   "reason_codes": []})
    _seed_elig(db, state="eligible")
    snap = {k: v for k, v in emp.items() if k != "_id"}
    _run(scan_hr_transport_consistency(db))
    after = {k: v for k, v in db.employees.rows[0].items() if k != "_id"}
    assert after == snap


# ===========================================================================
# 14 — Scanner records audit row 'transport_hr_sync_scanner_completed'
# ===========================================================================
def test_14_scanner_audit_row():
    from lib.transport_sync_monitor import scan_hr_transport_consistency
    db = _DB()
    _run(scan_hr_transport_consistency(db, create_action_items=False))
    kinds = [a.get("kind") for a in db.audit_events.rows]
    assert "transport_hr_sync_scanner_completed" in kinds


# ===========================================================================
# 15 — Scanner persists a run summary
# ===========================================================================
def test_15_scanner_persists_run():
    from lib.transport_sync_monitor import scan_hr_transport_consistency
    db = _DB()
    _run(scan_hr_transport_consistency(db, create_action_items=False))
    assert len(db.transport_hr_sync_runs.rows) == 1


# ===========================================================================
# 16 — derive_employee_transport_status: missing employee
# ===========================================================================
def test_16_chip_missing_employee():
    from lib.transport_sync_monitor import derive_employee_transport_status
    db = _DB()
    out = _run(derive_employee_transport_status(db, "E404"))
    assert out["linked"] is False
    assert out["reason"] == "hr_employee_missing"


# ===========================================================================
# 17 — derive_employee_transport_status: not linked
# ===========================================================================
def test_17_chip_not_linked():
    from lib.transport_sync_monitor import derive_employee_transport_status
    db = _DB()
    _seed_emp(db)
    out = _run(derive_employee_transport_status(db, "E2001"))
    assert out["linked"] is False
    assert out["reason"] == "not_linked"
    assert out["hr_status"] == "Active"


# ===========================================================================
# 18 — derive_employee_transport_status: linked + eligibility surfaced
# ===========================================================================
def test_18_chip_linked_eligible():
    from lib.transport_sync_monitor import derive_employee_transport_status
    db = _DB()
    _seed_emp(db)
    _seed_person(db, projection={"transport_state": "eligible",
                                   "source_status": "Active",
                                   "synced_at": "2026-02-09T12:00:00+00:00",
                                   "synced_trigger": "hr.test",
                                   "reason_codes": []})
    _seed_elig(db, state="eligible", reasons=[
        {"code": "hr_status_active", "label": "HR employment is active"},
    ])
    out = _run(derive_employee_transport_status(db, "E2001"))
    assert out["linked"] is True
    assert out["transport_status"] == "eligible"
    assert out["projection_state"] == "eligible"
    assert out["view_workspace_path"] == "/admin/transportation/drivers/tp-x"


# ===========================================================================
# 19 — chip is read-only (returns no write fields)
# ===========================================================================
def test_19_chip_read_only():
    from lib.transport_sync_monitor import derive_employee_transport_status
    db = _DB()
    _seed_emp(db)
    _seed_person(db, projection={"transport_state": "eligible",
                                   "reason_codes": []})
    out = _run(derive_employee_transport_status(db, "E2001"))
    for forbidden in ("token", "delete_url", "edit_url", "write_path"):
        assert forbidden not in out


# ===========================================================================
# 20 — Transportation Dashboard widget aggregation
# ===========================================================================
def test_20_transportation_dashboard_hr_health():
    from lib.transport_sync_monitor import (
        scan_hr_transport_consistency, transportation_dashboard_hr_health,
    )
    db = _DB()
    _seed_emp(db, lifecycle_status="Terminated")
    _seed_person(db, projection={"transport_state": "eligible",
                                   "reason_codes": []})
    _seed_elig(db, state="eligible")
    _run(scan_hr_transport_consistency(db))
    out = _run(transportation_dashboard_hr_health(db))
    assert out["health"] == "critical"
    assert "counts" in out


# ===========================================================================
# 21 — HR Dashboard widget aggregation
# ===========================================================================
def test_21_hr_dashboard_readiness():
    from lib.transport_sync_monitor import hr_dashboard_transport_readiness
    db = _DB()
    _seed_elig(db, person_id="tp-1", state="eligible")
    _seed_elig(db, person_id="tp-2", state="suspended")
    _seed_elig(db, person_id="tp-3", state="not_dispatchable")
    out = _run(hr_dashboard_transport_readiness(db))
    assert out["states"]["eligible"] == 1
    assert out["states"]["suspended"] == 1
    assert out["states"]["not_dispatchable"] == 1


# ===========================================================================
# 22 — Severity classifier coverage
# ===========================================================================
def test_22_severity_levels():
    from lib.transport_sync_monitor import _severity_for
    assert _severity_for("termination_mismatch") == "critical"
    assert _severity_for("leave_mismatch") == "block"
    assert _severity_for("projection_stale") == "warn"
    assert _severity_for("dispatch_conflict") == "critical"


# ===========================================================================
# 23 — Mismatch dicts carry recommended_action
# ===========================================================================
def test_23_recommended_action_present():
    from lib.transport_sync_monitor import classify_mismatch
    out = classify_mismatch(
        hr_record={"id": "e1", "employee_id": "E1",
                   "lifecycle_status": "Terminated"},
        transport_person={"id": "tp-1", "employee_id": "E1"},
        projection=None, eligibility={"state": "eligible"},
    )
    for m in out:
        assert "recommended_action" in m
        assert "reason" in m


# ===========================================================================
# 24 — Duplicate transport_person rows surface duplicate_linkage
# ===========================================================================
def test_24_duplicate_linkage_detected():
    from lib.transport_sync_monitor import scan_hr_transport_consistency
    db = _DB()
    _seed_emp(db)
    _seed_person(db, employee_id="E2001", projection={
        "transport_state": "eligible", "reason_codes": []})
    db.transport_persons.rows.append({
        "_id": "tp-y", "id": "tp-y", "tenant": "masci",
        "kind": "masci_employee", "employee_id": "E2001",
        "first_name": "Pat", "last_name": "Hauler", "status": "active",
        "hr_projection": {"transport_state": "eligible", "reason_codes": []},
    })
    out = _run(scan_hr_transport_consistency(db, create_action_items=False))
    codes = [m["code"] for m in out["mismatches"]]
    assert "duplicate_linkage" in codes


# ===========================================================================
# 25 — HR active driver-relevant employee without linkage surfaces
# ===========================================================================
def test_25_hr_active_no_linkage():
    from lib.transport_sync_monitor import scan_hr_transport_consistency
    db = _DB()
    _seed_emp(db)  # Active, driver-relevant, no transport_person linked.
    out = _run(scan_hr_transport_consistency(db, create_action_items=False))
    codes = [m["code"] for m in out["mismatches"]]
    assert "hr_active_no_linkage" in codes


# ===========================================================================
# 26 — Scanner reports projection_failed when last sync had no source
# ===========================================================================
def test_26_projection_failed_detected():
    from lib.transport_sync_monitor import scan_hr_transport_consistency
    db = _DB()
    _seed_emp(db)
    _seed_person(db, projection={"transport_state": "needs_correction",
                                   "reason_codes": ["hr_employee_missing"]})
    _seed_elig(db, state="needs_correction")
    out = _run(scan_hr_transport_consistency(db, create_action_items=False))
    codes = [m["code"] for m in out["mismatches"]]
    assert "projection_failed" in codes


# ===========================================================================
# 27 — Read-only API endpoints exist
# ===========================================================================
def test_27_api_endpoints():
    src = ROUTE.read_text()
    assert "/admin/transportation/hr-sync" in src
    assert "/admin/transportation/hr-sync/report" in src
    assert "/admin/hr/transportation-status" in src
    assert "/admin/hr/transportation-readiness" in src


# ===========================================================================
# 28 — No write endpoints introduced under hr-sync namespace
# ===========================================================================
def test_28_no_write_endpoints():
    src = ROUTE.read_text()
    # All four new endpoints must use @router.get
    for path in (
        "/admin/transportation/hr-sync",
        "/admin/transportation/hr-sync/report",
        "/admin/hr/transportation-status",
        "/admin/hr/transportation-readiness",
    ):
        idx = src.find(path)
        # find the @router. line immediately above
        prefix = src[max(0, idx - 200):idx]
        assert "@router.get(" in prefix or "@router.get" in prefix, \
            f"{path} must be read-only"


# ===========================================================================
# 29 — Scheduler integration (extends existing automation loop)
# ===========================================================================
def test_29_scheduler_calls_scanner():
    src = ROUTE.read_text()
    assert "scan_hr_transport_consistency" in src
    # Must be inside the transport_automation_scheduler_loop, not a new loop.
    loop_start = src.find("async def transport_automation_scheduler_loop")
    scanner_call = src.find("scan_hr_transport_consistency(db)")
    assert loop_start > 0 and scanner_call > loop_start


# ===========================================================================
# 30 — No NEW scheduler loop function was introduced
# ===========================================================================
def test_30_no_new_scheduler_loop():
    src = ROUTE.read_text()
    # We must NOT introduce a new top-level *scheduler_loop function
    # specific to sync. The scan runs inside the existing automation loop.
    assert "transport_hr_sync_monitor_scheduler_loop" not in src
    assert "transport_sync_monitor_scheduler_loop" not in src


# ===========================================================================
# 31 — Route key bootstrapped internal-only & disabled by default
# ===========================================================================
def test_31_route_key_bootstrap():
    src = ROUTE.read_text()
    assert "TRANSPORT_HR_SYNC_MONITOR_ALERT" in src


# ===========================================================================
# 32 — Track 16.10A's existing internal_only invariant is preserved
# ===========================================================================
def test_32_existing_internal_only_string_preserved():
    src = ROUTE.read_text()
    assert 'internal_only": route_key == "TRANSPORT_COMMAND_DIGEST_WEEKLY"' in src


# ===========================================================================
# 33 — HR Hub renders Transportation Readiness widget
# ===========================================================================
def test_33_hr_hub_widget():
    src = FE_HRHUB.read_text()
    assert "hr-transportation-readiness-widget" in src
    assert "TransportationReadinessWidget" in src
    assert "/admin/hr/transportation-readiness" in src


# ===========================================================================
# 34 — HR Employee drawer has Transportation tab
# ===========================================================================
def test_34_hr_drawer_tx_tab():
    src = FE_HREMP.read_text()
    assert "hremp-tab-transportation" in src
    assert "TransportationStatusPanel" in src
    assert "hremp-tx-panel" in src or "hremp-tx-not-linked" in src


# ===========================================================================
# 35 — Transportation Dashboard renders HR Health widget
# ===========================================================================
def test_35_tx_dashboard_hr_health_widget():
    src = FE_TXVIEWS.read_text()
    assert "tx-dashboard-hr-health" in src
    assert "HrHealthWidget" in src


# ===========================================================================
# 36 — Command Queue renders HR Sync Health card
# ===========================================================================
def test_36_command_queue_hr_sync_card():
    src = FE_TXCQ.read_text()
    assert "tx-cq-hr-sync-card" in src
    assert "HrSyncHealthCard" in src


# ===========================================================================
# 37 — HR UI never introduces Transportation write controls
# ===========================================================================
def test_37_hr_ui_read_only():
    src = FE_HREMP.read_text()
    # Inside the Transportation panel block, ensure there are no
    # write-style verbs / fetch POST / DELETE calls related to transport.
    panel_start = src.find("function TransportationStatusPanel")
    panel_end = src.find("function Row2")
    panel = src[panel_start:panel_end] if panel_start > 0 else ""
    assert panel, "TransportationStatusPanel must be present"
    for forbidden in ("method: \"POST\"", "method: 'POST'",
                       "method: \"PATCH\"", "method: 'PATCH'",
                       "method: \"DELETE\"", "method: 'DELETE'"):
        assert forbidden not in panel
    assert "transport_persons" not in panel


# ===========================================================================
# 38 — No SMS / Twilio / push references in sync monitor
# ===========================================================================
def test_38_no_sms_push():
    src = LIB.read_text()
    for forbidden in ("twilio", "TWILIO", "sendSms", "push_notification",
                       "fcm.googleapis"):
        assert forbidden not in src


# ===========================================================================
# 39 — Forbidden punitive vocabulary not introduced
# ===========================================================================
def test_39_no_punitive_language():
    src = LIB.read_text()
    for forbidden in ("Rejected", "Denied", "Failed —", "rejected!", "denied!"):
        assert forbidden not in src


# ===========================================================================
# 40 — Deployment gate includes Track 16.11A tests
# ===========================================================================
def test_40_deployment_gate_includes_track_16_11A():
    src = GATE.read_text()
    assert "test_track_16_11A_transport_sync_monitor" in src


# ===========================================================================
# 41 — Track 16.11 tests still wired
# ===========================================================================
def test_41_track_16_11_preserved():
    src = GATE.read_text()
    assert "test_track_16_11_transport_hr_lifecycle_integration" in src


# ===========================================================================
# 42 — HR routes still preserved
# ===========================================================================
def test_42_hr_routes_preserved():
    src = HR_ROUTE.read_text()
    for route in (
        '@router.get("/api/hr/employees")',
        '@router.post("/api/hr/employees")',
        '@router.patch("/api/hr/employees/{employee_id}")',
        '@router.post("/api/hr/employees/{employee_id}/status")',
        '@router.post("/api/hr/employees/{employee_id}/reactivate")',
    ):
        assert route in src


# ===========================================================================
# 43 — No destructive Mongo operations in the monitor
# ===========================================================================
def test_43_no_destructive_ops():
    src = LIB.read_text()
    for forbidden in ("drop_collection", "delete_many", "drop_indexes",
                       "db.employees.update_one"):
        assert forbidden not in src


# ===========================================================================
# 44 — Action items always include related_event_key + dedupe-safe
# ===========================================================================
def test_44_action_items_have_event_key():
    src = LIB.read_text()
    assert "related_event_key" in src
    assert "_event_key" in src


# ===========================================================================
# 45 — Track 16.04 → 16.10A tests preserved in gate
# ===========================================================================
def test_45_all_prior_transport_tracks_in_gate():
    src = GATE.read_text()
    for f in (
        "test_track_16_04_transportation_foundation",
        "test_track_16_05_transportation_onboarding_compliance_center",
        "test_track_16_06_transportation_experience_layer",
        "test_track_16_07_transportation_workflow_activation",
        "test_track_16_08_transportation_orientation",
        "test_track_16_09_transportation_dispatch_gate_email_pilot",
        "test_track_16_10_transportation_automation_engine",
        "test_track_16_10a_transport_command_digest",
        "test_track_16_11_transport_hr_lifecycle_integration",
    ):
        assert f in src
