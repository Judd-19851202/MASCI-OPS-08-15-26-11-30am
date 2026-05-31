"""Pillar 1 · Phase 1A-2 · Accountability Projection certification suite.

Tests the read-only projection library exclusively. Mocks `db` for
incident projection's CA lookup; no real DB writes; no source workflow
mutation; no Command Center change.

Coverage per directive:
    1. Tasks                  - sync projection
    2. Corrective Actions     - sync projection
    3. Purchase Approvals     - sync projection
    4. Fleet Defects          - sync projection
    5. Incidents              - async projection (CA lookup)
    6. Virtual Signals        - sync projection
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

import pytest

from lib.accountability_projection import (
    ALLOWED_PRIORITIES,
    CANONICAL_EVENT_KINDS,
    CANONICAL_STATUSES,
    project,
    project_corrective_action,
    project_fleet_defect,
    project_incident,
    project_po_request,
    project_task,
    project_virtual_signal,
)


# ─── Fake async db for incident projection ──────────────────────────
class _FakeCollection:
    def __init__(self, docs):
        self.docs = docs

    async def find_one(self, query, _proj=None):
        # Very narrow matcher: supports {"$or": [...], "status": {"$in": [...]}}
        ors = query.get("$or") or [{}]
        status_in = (query.get("status") or {}).get("$in") or []
        for d in self.docs:
            matched_or = any(
                all(d.get(k) == v for k, v in clause.items()) for clause in ors
            )
            matched_status = (not status_in) or (d.get("status") in status_in)
            if matched_or and matched_status:
                return d
        return None


class _FakeDB:
    def __init__(self, corrective_actions=None):
        self.corrective_actions = _FakeCollection(corrective_actions or [])


def _run(coro):
    return asyncio.run(coro)


# ─── Shared fixtures ─────────────────────────────────────────────────
NOW = datetime.now(timezone.utc)
ISO = NOW.isoformat()
PAST_2D = (NOW - timedelta(days=2)).isoformat()
PAST_4D = (NOW - timedelta(days=4)).isoformat()
PAST_6D = (NOW - timedelta(days=6)).isoformat()
PAST_8D = (NOW - timedelta(days=8)).isoformat()
FUTURE_2D_ISO = (NOW + timedelta(days=2)).isoformat()


# ════════════════════════════════════════════════════════════════════
# § Contract invariants
# ════════════════════════════════════════════════════════════════════
def test_canonical_statuses_closed_set():
    assert CANONICAL_STATUSES == (
        "open", "in_progress", "pending_review", "resolved", "closed", "cancelled",
    )


def test_canonical_event_kinds_excludes_escalated():
    # Pillar 1B reservation — `escalated` must NOT be in the emitted set.
    assert "escalated" not in CANONICAL_EVENT_KINDS


def test_priority_enum_unchanged():
    assert set(ALLOWED_PRIORITIES) == {"Low", "Medium", "High", "Critical"}


# ════════════════════════════════════════════════════════════════════
# § Source #1 · Tasks
# ════════════════════════════════════════════════════════════════════
def _task_row(**overrides):
    base = {
        "id": "task-1",
        "title": "Close CA-2026-0042",
        "status": "Open",
        "priority": "High",
        "due_at": FUTURE_2D_ISO,
        "created_at": PAST_2D,
        "updated_at": PAST_2D,
        "assignee_role": "safety",
        "assignee_user_id": "user-77",
        "assignee_employee_id": None,
        "audit": [
            {"at": PAST_2D, "by": {"role": "system", "name": "system"},
             "action": "created"},
        ],
        "closed_at": None,
        "completion_notes": None,
        "created_by": {"role": "system", "name": "system"},
    }
    base.update(overrides)
    return base


def test_task_open_projection_shape():
    p = project_task(_task_row())
    assert p["source_module"] == "tasks"
    assert p["accountability_id"] == "task-1"
    assert p["status"] == "open"
    assert p["owner_role"] == "safety"
    assert p["owner_user_id"] == "user-77"
    assert p["priority"] == "High"
    assert p["escalation_level"] == 0
    assert p["timeline_events"][0]["event_kind"] == "created"


def test_task_status_completed_maps_to_resolved():
    row = _task_row(status="Completed", closed_at=ISO,
                    completion_notes="done by Tom")
    p = project_task(row)
    assert p["status"] == "resolved"
    assert p["resolved_at"] is not None
    assert p["resolution_notes"] == "done by Tom"


def test_task_status_closed_maps_to_closed():
    row = _task_row(status="Closed", closed_at=ISO)
    p = project_task(row)
    assert p["status"] == "closed"


def test_task_status_cancelled_maps_to_cancelled():
    p = project_task(_task_row(status="Cancelled"))
    assert p["status"] == "cancelled"


def test_task_legacy_overdue_native_maps_to_open():
    p = project_task(_task_row(status="Overdue"))
    assert p["status"] == "open"


def test_task_overdue_overlay_true_when_past_due():
    row = _task_row(status="Open",
                    due_at=(NOW - timedelta(days=1)).isoformat())
    p = project_task(row)
    assert p["overdue"] is True


def test_task_overdue_overlay_false_when_future():
    p = project_task(_task_row(status="Open"))
    assert p["overdue"] is False


def test_task_audit_status_change_emits_double_event():
    audit = [
        {"at": PAST_4D, "by": {"role": "system"}, "action": "created"},
        {"at": PAST_2D, "by": {"role": "safety", "name": "Sara"},
         "action": "updated",
         "changes": {"status": {"from": "Open", "to": "In Progress"}}},
    ]
    p = project_task(_task_row(audit=audit, status="In Progress"))
    kinds = [e["event_kind"] for e in p["timeline_events"]]
    # Expect: created, status_changed, updated
    assert kinds == ["created", "status_changed", "updated"]
    sc = p["timeline_events"][1]
    assert sc["from_status"] == "open"
    assert sc["to_status"] == "in_progress"


# ════════════════════════════════════════════════════════════════════
# § Source #2 · Corrective Actions
# ════════════════════════════════════════════════════════════════════
def _ca_row(**overrides):
    base = {
        "id": "ca-1",
        "title": "Replace damaged guardrail",
        "status": "Open",
        "priority": "High",
        "due_date": FUTURE_2D_ISO[:10],
        "assigned_to_name": "Sara Safety",
        "assigned_to_email": "sara@mascigc.com",
        "created_at": PAST_4D,
        "updated_at": PAST_4D,
        "status_history": [],
        "completion_notes": "",
    }
    base.update(overrides)
    return base


def test_ca_open_projection_owner_real_name():
    p = project_corrective_action(_ca_row())
    assert p["source_module"] == "safety.corrective_actions"
    assert p["status"] == "open"
    assert p["owner_role"] == "safety"
    assert p["owner_display_name"] == "Sara Safety"


def test_ca_verified_maps_to_resolved():
    row = _ca_row(status="Verified", verified_at=ISO,
                  verified_by_name="Tom Verifier",
                  completion_notes="reviewed and closed")
    p = project_corrective_action(row)
    assert p["status"] == "resolved"
    assert p["resolved_at"] is not None
    assert p["resolved_by"]["name"] == "Tom Verifier"
    assert p["resolution_notes"] == "reviewed and closed"


def test_ca_closed_verified_native_maps_to_closed():
    p = project_corrective_action(_ca_row(status="Closed - Verified"))
    assert p["status"] == "closed"


def test_ca_status_history_translated_to_status_changed_events():
    history = [
        {"from": "Open", "to": "In Progress", "by_name": "Sara",
         "at": PAST_4D, "note": "starting work"},
        {"from": "In Progress", "to": "Verified", "by_name": "Tom",
         "at": PAST_2D, "note": "verified onsite"},
    ]
    p = project_corrective_action(_ca_row(status="Verified",
                                          status_history=history,
                                          verified_at=PAST_2D,
                                          verified_by_name="Tom"))
    kinds = [e["event_kind"] for e in p["timeline_events"]]
    # Expected: status_changed, status_changed, resolved (derived)
    assert kinds == ["status_changed", "status_changed", "resolved"]
    assert p["timeline_events"][0]["from_status"] == "open"
    assert p["timeline_events"][1]["to_status"] == "resolved"


def test_ca_due_date_passes_through():
    p = project_corrective_action(_ca_row(due_date="2026-06-15"))
    assert p["due_at"].startswith("2026-06-15")


# ════════════════════════════════════════════════════════════════════
# § Source #3 · Purchase Approvals (po_requests)
# ════════════════════════════════════════════════════════════════════
def _po_row(**overrides):
    base = {
        "id": "po-1",
        "doc_id": "PO-2026-0042",
        "vendor": "Acme Supply",
        "status": "Pending Approval",
        "urgency": "High",
        "created_at": PAST_4D,
        "updated_at": PAST_4D,
        "requested_by_role": "pm",
        "requested_by_name": "Chris PM",
        "requested_by_user_id": "user-pm-1",
        "requested_by_employee_id": "emp-pm-1",
        "audit": [
            {"at": PAST_4D, "by": {"role": "pm", "name": "Chris PM"},
             "action": "submitted"},
        ],
    }
    base.update(overrides)
    return base


def test_po_pending_owner_is_approver_not_requester():
    """Audit A-05 / Integration §3.5: aged PO owner is the approver,
    NOT the requester. Pre-Pillar 1 Command Center attributed the
    requester here — this test guarantees the projection corrects it."""
    p = project_po_request(_po_row())
    assert p["status"] == "open"  # Pending Approval → open per Lifecycle §4.3
    assert p["owner_role"] == "approver_per_routing"
    assert p["owner_display_name"] == "Pending Approver"
    assert p["owner_display_name"] != "Chris PM"


def test_po_clarification_needed_maps_to_in_progress():
    p = project_po_request(_po_row(status="Clarification Needed"))
    assert p["status"] == "in_progress"


def test_po_pending_receipt_maps_to_pending_review():
    p = project_po_request(_po_row(status="Pending Receipt"))
    assert p["status"] == "pending_review"


def test_po_approved_maps_to_resolved_with_actor_capture():
    audit = [
        {"at": PAST_4D, "by": {"role": "pm", "name": "Chris PM"},
         "action": "submitted"},
        {"at": PAST_2D, "by": {"role": "leadership", "name": "Leo Approver"},
         "action": "approved"},
    ]
    p = project_po_request(_po_row(status="Approved", audit=audit))
    assert p["status"] == "resolved"
    assert p["resolved_at"] is not None
    assert p["resolved_by"]["name"] == "Leo Approver"


def test_po_rejected_owner_is_requester():
    """Terminal-cancelled PO: requester is the de-facto owner since no
    further action is expected. Distinct from Pending Approval."""
    p = project_po_request(_po_row(status="Rejected"))
    assert p["status"] == "cancelled"
    assert p["owner_role"] == "pm"  # the requester role
    assert p["owner_display_name"] == "Chris PM"


def test_po_due_at_derived_from_created_plus_3_days():
    p = project_po_request(_po_row(created_at=PAST_6D))
    # due_at = created_at + 3 days → already in the past → overdue
    assert p["due_at"] is not None
    assert p["overdue"] is True


def test_po_audit_translated_with_no_kind_loss():
    audit = [
        {"at": PAST_8D, "by": {"role": "pm", "name": "Chris"},
         "action": "submitted"},
        {"at": PAST_6D, "by": {"role": "approver", "name": "Leo"},
         "action": "clarification_requested",
         "details": {"note": "need more info"}},
        {"at": PAST_4D, "by": {"role": "pm", "name": "Chris"},
         "action": "clarification_response"},
        {"at": PAST_2D, "by": {"role": "approver", "name": "Leo"},
         "action": "approved"},
    ]
    p = project_po_request(_po_row(status="Approved", audit=audit))
    kinds = [e["event_kind"] for e in p["timeline_events"]]
    assert kinds == ["created", "commented", "commented", "resolved"]


# ════════════════════════════════════════════════════════════════════
# § Source #4 · Fleet Defects (equipment.dvir)
# ════════════════════════════════════════════════════════════════════
def _defect_row(**overrides):
    base = {
        "id": "def-1",
        "doc_id": "DEF-2026-00012",
        "truck_unit_number": "412",
        "trailer_unit_number": None,
        "item_text": "Brake light out",
        "severity": "oos",
        "status": "open",
        "reported_at": PAST_2D,
        "reported_by_name": "Driver Doe",
        "reported_by_employee_id": "emp-driver-1",
        "acknowledged_at": None,
        "acknowledged_by_name": None,
        "repaired_at": None,
        "cleared_at": None,
    }
    base.update(overrides)
    return base


def test_defect_open_owner_default_shop():
    p = project_fleet_defect(_defect_row())
    assert p["source_module"] == "equipment.dvir"
    assert p["status"] == "open"
    assert p["owner_role"] == "shop"
    assert p["owner_display_name"] == "Shop"  # Audit A-02: no acknowledger yet


def test_defect_acknowledged_maps_to_in_progress_with_name():
    p = project_fleet_defect(_defect_row(
        status="acknowledged",
        acknowledged_at=PAST_2D, acknowledged_by_name="Mike Mechanic"))
    assert p["status"] == "in_progress"
    assert p["owner_display_name"] == "Mike Mechanic"


def test_defect_repaired_maps_to_pending_review():
    p = project_fleet_defect(_defect_row(
        status="repaired", acknowledged_at=PAST_4D,
        acknowledged_by_name="Mike", repaired_at=PAST_2D,
        repaired_by_name="Mike", repair_notes="new bulb"))
    assert p["status"] == "pending_review"


def test_defect_cleared_maps_to_closed_with_resolver():
    p = project_fleet_defect(_defect_row(
        status="cleared", acknowledged_at=PAST_4D,
        acknowledged_by_name="Mike", repaired_at=PAST_2D,
        repaired_by_name="Mike", cleared_at=ISO,
        cleared_by_name="Shop Manager", repair_notes="verified"))
    assert p["status"] == "closed"
    assert p["resolved_at"] is not None
    assert p["resolved_by"]["name"] == "Shop Manager"


def test_defect_oos_due_at_72h():
    p = project_fleet_defect(_defect_row(severity="oos", reported_at=PAST_4D))
    # 4 days > 72h → overdue
    assert p["overdue"] is True


def test_defect_synthesized_timeline_order():
    p = project_fleet_defect(_defect_row(
        status="cleared", acknowledged_at=PAST_6D,
        acknowledged_by_name="A", repaired_at=PAST_4D,
        repaired_by_name="A", cleared_at=PAST_2D, cleared_by_name="A"))
    kinds = [e["event_kind"] for e in p["timeline_events"]]
    assert kinds == ["created", "status_changed", "status_changed",
                     "status_changed", "closed"]


# ════════════════════════════════════════════════════════════════════
# § Source #5 · Incidents (async, CA-aware)
# ════════════════════════════════════════════════════════════════════
def _incident_row(**overrides):
    base = {
        "id": "inc-1",
        "doc_id": "INC-2026-0099",
        "severity": "critical",
        "osha_recordable": "No",
        "corrected_on_site": "No",
        "created_at": PAST_2D,
        "updated_at": PAST_2D,
        "type_of_incident": "near_miss",
    }
    base.update(overrides)
    return base


def test_incident_open_when_no_closure_signal():
    db = _FakeDB(corrective_actions=[])
    p = _run(project_incident(db, _incident_row()))
    assert p["source_module"] == "safety.incidents"
    assert p["status"] == "open"
    assert p["owner_role"] == "safety"


def test_incident_resolved_when_corrected_on_site_yes():
    db = _FakeDB(corrective_actions=[])
    p = _run(project_incident(db,
        _incident_row(corrected_on_site="Yes",
                      updated_at=ISO)))
    assert p["status"] == "resolved"
    resolved_evs = [e for e in p["timeline_events"]
                    if e["event_kind"] == "resolved"]
    assert resolved_evs and resolved_evs[0]["notes"] == "corrected_on_site=Yes"


def test_incident_resolved_via_linked_closed_ca():
    cas = [{"id": "ca-9", "source_id": "inc-1", "status": "Closed"}]
    db = _FakeDB(corrective_actions=cas)
    p = _run(project_incident(db, _incident_row()))
    assert p["status"] == "resolved"


def test_incident_resolved_via_linked_verified_ca():
    cas = [{"id": "ca-9", "incident_id": "inc-1", "status": "Verified"}]
    db = _FakeDB(corrective_actions=cas)
    p = _run(project_incident(db, _incident_row()))
    assert p["status"] == "resolved"


def test_incident_in_progress_when_only_open_ca_linked():
    cas = [{"id": "ca-9", "source_id": "inc-1", "status": "In Progress"}]
    db = _FakeDB(corrective_actions=cas)
    p = _run(project_incident(db, _incident_row()))
    assert p["status"] == "in_progress"


def test_incident_osha_due_at_24h():
    db = _FakeDB(corrective_actions=[])
    p = _run(project_incident(db,
        _incident_row(osha_recordable="Yes",
                      created_at=(NOW - timedelta(hours=30)).isoformat())))
    # 30h > 24h → overdue
    assert p["overdue"] is True


def test_incident_critical_due_at_48h():
    db = _FakeDB(corrective_actions=[])
    p = _run(project_incident(db,
        _incident_row(severity="critical",
                      created_at=(NOW - timedelta(hours=50)).isoformat())))
    assert p["overdue"] is True


def test_incident_priority_mapped_from_severity():
    db = _FakeDB(corrective_actions=[])
    p = _run(project_incident(db, _incident_row(severity="critical")))
    assert p["priority"] == "Critical"


# ════════════════════════════════════════════════════════════════════
# § Source #6 · Virtual Signals
# ════════════════════════════════════════════════════════════════════
def test_virtual_signal_dr_missing():
    p = project_virtual_signal(signal_kind="dr_missing", payload={
        "what_wrong": "No daily report filed for 24-15 in last 36h",
        "owner_role": "pm",
        "owner": "Chris PM",
        "created_at": ISO,
    })
    assert p["source_module"] == "virtual.dr_missing"
    assert p["status"] == "open"
    assert p["owner_role"] == "pm"
    assert p["owner_display_name"] == "Chris PM"


def test_virtual_signal_default_owner_operations_leadership():
    p = project_virtual_signal(signal_kind="issue_no_owner", payload={
        "what_wrong": "Unowned issue surface",
    })
    assert p["owner_role"] == "operations_leadership"


def test_virtual_signal_timeline_empty():
    p = project_virtual_signal(signal_kind="dr_missing", payload={})
    assert p["timeline_events"] == []


# ════════════════════════════════════════════════════════════════════
# § Dispatch (single entry point)
# ════════════════════════════════════════════════════════════════════
def test_dispatch_routes_correctly_by_source_module():
    db = _FakeDB()
    p_t = _run(project(db, "tasks", _task_row()))
    p_c = _run(project(db, "safety.corrective_actions", _ca_row()))
    p_p = _run(project(db, "po.requests", _po_row()))
    p_d = _run(project(db, "equipment.dvir", _defect_row()))
    p_i = _run(project(db, "safety.incidents", _incident_row()))
    p_v = _run(project(db, "virtual.dr_missing", {"what_wrong": "x"}))
    sources = {p["source_module"] for p in (p_t, p_c, p_p, p_d, p_i, p_v)}
    assert sources == {
        "tasks", "safety.corrective_actions", "po.requests",
        "equipment.dvir", "safety.incidents", "virtual.dr_missing",
    }


def test_dispatch_rejects_unknown_source_module():
    db = _FakeDB()
    with pytest.raises(ValueError):
        _run(project(db, "unknown.workflow", {}))


# ════════════════════════════════════════════════════════════════════
# § Cross-source uniformity (success condition · directive)
# ════════════════════════════════════════════════════════════════════
def _projection_field_set(p):
    return set(p.keys())


def test_all_six_sources_produce_identical_field_set():
    """Success condition from the directive:
    'A Task, Corrective Action, Purchase Approval, Fleet Defect,
    Incident, and Virtual Signal can all be represented by the same
    accountability shape.'
    """
    db = _FakeDB()
    projections = [
        _run(project(db, "tasks", _task_row())),
        _run(project(db, "safety.corrective_actions", _ca_row())),
        _run(project(db, "po.requests", _po_row())),
        _run(project(db, "equipment.dvir", _defect_row())),
        _run(project(db, "safety.incidents", _incident_row())),
        _run(project(db, "virtual.dr_missing", {})),
    ]
    field_sets = [_projection_field_set(p) for p in projections]
    # Every projection must expose the SAME 24 fields.
    for fs in field_sets[1:]:
        assert fs == field_sets[0]


def test_all_six_sources_status_in_canonical_set():
    db = _FakeDB()
    projections = [
        _run(project(db, "tasks", _task_row())),
        _run(project(db, "safety.corrective_actions", _ca_row())),
        _run(project(db, "po.requests", _po_row())),
        _run(project(db, "equipment.dvir", _defect_row())),
        _run(project(db, "safety.incidents", _incident_row())),
        _run(project(db, "virtual.dr_missing", {})),
    ]
    for p in projections:
        assert p["status"] in CANONICAL_STATUSES


def test_escalation_level_always_zero_in_phase_1a2():
    """Pillar 1B reservation invariant — escalation must not be active."""
    db = _FakeDB()
    projections = [
        _run(project(db, "tasks", _task_row())),
        _run(project(db, "safety.corrective_actions", _ca_row())),
        _run(project(db, "po.requests", _po_row())),
        _run(project(db, "equipment.dvir", _defect_row())),
        _run(project(db, "safety.incidents", _incident_row())),
        _run(project(db, "virtual.dr_missing", {})),
    ]
    for p in projections:
        assert p["escalation_level"] == 0


def test_every_projection_has_accountability_id():
    db = _FakeDB()
    projections = [
        _run(project(db, "tasks", _task_row())),
        _run(project(db, "safety.corrective_actions", _ca_row())),
        _run(project(db, "po.requests", _po_row())),
        _run(project(db, "equipment.dvir", _defect_row())),
        _run(project(db, "safety.incidents", _incident_row())),
        _run(project(db, "virtual.dr_missing", {"what_wrong": "x"})),
    ]
    ids = [p["accountability_id"] for p in projections]
    assert all(isinstance(x, str) and len(x) > 0 for x in ids)
    assert len(set(ids)) == 6   # all distinct


def test_accountability_id_is_deterministic_per_source_row():
    """Same row → same id every time (Architecture §3.1)."""
    db = _FakeDB()
    p1 = _run(project(db, "safety.corrective_actions", _ca_row()))
    p2 = _run(project(db, "safety.corrective_actions", _ca_row()))
    assert p1["accountability_id"] == p2["accountability_id"]


# ════════════════════════════════════════════════════════════════════
# § Source workflow preservation (no schema regression)
# ════════════════════════════════════════════════════════════════════
def test_projection_never_mutates_input_row_tasks():
    row = _task_row()
    snapshot = dict(row)
    project_task(row)
    assert row == snapshot


def test_projection_never_mutates_input_row_ca():
    row = _ca_row()
    snapshot = dict(row)
    project_corrective_action(row)
    assert row == snapshot


def test_projection_never_mutates_input_row_po():
    row = _po_row()
    snapshot = dict(row)
    project_po_request(row)
    assert row == snapshot


def test_projection_never_mutates_input_row_defect():
    row = _defect_row()
    snapshot = dict(row)
    project_fleet_defect(row)
    assert row == snapshot
