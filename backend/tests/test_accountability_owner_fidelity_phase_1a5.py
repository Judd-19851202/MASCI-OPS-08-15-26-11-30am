"""Pillar 1 · Phase 1A-5 · Owner-fidelity resolver certification.

Unit-level tests of the new async resolver helpers:

    lib.accountability_projection.project_po_request_resolved(db, row)
    lib.accountability_projection.project_incident_resolved(db, row)

These prove:
  - Resolved owners surface when authoritative routing data exists.
  - Fallback placeholders are preserved when data is absent.
  - The resolver never mutates the source row.
  - The canonical 23-field projection shape is unchanged by resolution.
  - Pillar 1B reservation invariant (escalation_level=0) is preserved.

Mock DB fixture only — no live HTTP. (Live-HTTP coverage of the
end-to-end Command Center surface lives in 1A-4 service suite, which
runs against the same code path after Phase 1A-5 promotion.)
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

import pytest

from lib.accountability_projection import (
    project_incident_resolved,
    project_po_request_resolved,
)


# ─── Async helpers ───────────────────────────────────────────────────
def _run(coro):
    return asyncio.run(coro)


class _FakeCollection:
    def __init__(self, docs):
        self.docs = list(docs)

    async def find_one(self, query, _proj=None, sort=None):
        # Minimal matcher: top-level $or, top-level equality clauses,
        # status:{$in:[...]}, assigned_to_name:{$nin:[...]} support.
        def matches(doc):
            for k, v in query.items():
                if k == "$or":
                    if not any(matches_clause(doc, c) for c in v):
                        return False
                elif isinstance(v, dict) and "$in" in v:
                    if doc.get(k) not in v["$in"]:
                        return False
                elif isinstance(v, dict) and "$nin" in v:
                    if doc.get(k) in v["$nin"]:
                        return False
                else:
                    if doc.get(k) != v:
                        return False
            return True

        def matches_clause(doc, clause):
            return all(doc.get(k) == v for k, v in clause.items())

        candidates = [d for d in self.docs if matches(d)]
        if sort:
            field, order = sort[0]
            candidates.sort(key=lambda d: d.get(field) or "",
                            reverse=(order == -1))
        return candidates[0] if candidates else None


class _FakeDB:
    def __init__(self, jobs_master=None, corrective_actions=None):
        self.jobs_master = _FakeCollection(jobs_master or [])
        self.corrective_actions = _FakeCollection(corrective_actions or [])


NOW = datetime.now(timezone.utc)
PAST_4D = (NOW - timedelta(days=4)).isoformat()
PAST_2D = (NOW - timedelta(days=2)).isoformat()


# ════════════════════════════════════════════════════════════════════
# § PO PM-routing resolver
# ════════════════════════════════════════════════════════════════════
def _po_row(**overrides):
    base = {
        "id": "po-1",
        "doc_id": "PO-2026-0042",
        "vendor": "Acme",
        "status": "Pending Approval",
        "project_number": "24-15",
        "requested_by_name": "Chris PM",
        "requested_by_role": "pm",
        "created_at": PAST_4D,
        "audit": [],
    }
    base.update(overrides)
    return base


def test_po_resolved_owner_promotes_pm_when_jobs_master_links():
    db = _FakeDB(jobs_master=[
        {"project_number": "24-15", "primary_pm_name": "Tom Project",
         "primary_pm_email": "tom@mascigc.com",
         "primary_pm_user_id": "user-pm-tom"},
    ])
    p = _run(project_po_request_resolved(db, _po_row()))
    assert p["owner_role"] == "pm"
    assert p["owner_user_id"] == "user-pm-tom"
    assert p["owner_display_name"] == "Tom Project"


def test_po_resolved_falls_back_when_no_jobs_master_link():
    """Mirrors the live preview data — most pending POs do NOT link to
    a jobs_master row with a PM. Fallback "Pending Approver" must
    survive."""
    db = _FakeDB(jobs_master=[])
    p = _run(project_po_request_resolved(db, _po_row()))
    assert p["owner_role"] == "approver_per_routing"
    assert p["owner_display_name"] == "Pending Approver"


def test_po_resolved_falls_back_when_jobs_master_pm_name_empty():
    db = _FakeDB(jobs_master=[
        {"project_number": "24-15", "primary_pm_name": "",
         "primary_pm_email": ""},
    ])
    p = _run(project_po_request_resolved(db, _po_row()))
    assert p["owner_display_name"] == "Pending Approver"


def test_po_resolved_falls_back_when_no_project_number():
    db = _FakeDB(jobs_master=[
        {"project_number": "24-15", "primary_pm_name": "Tom"},
    ])
    p = _run(project_po_request_resolved(db, _po_row(project_number=None)))
    assert p["owner_display_name"] == "Pending Approver"


def test_po_resolved_terminal_cancelled_keeps_requester():
    """Rejected/Cancelled POs are terminal — base projection's
    requester ownership is preserved (Lifecycle §4.3)."""
    db = _FakeDB(jobs_master=[
        {"project_number": "24-15", "primary_pm_name": "Tom"},
    ])
    p = _run(project_po_request_resolved(db, _po_row(status="Rejected")))
    # base projection sets requester role+name on cancelled
    assert p["status"] == "cancelled"
    assert p["owner_display_name"] == "Chris PM"  # the requester


def test_po_resolved_preserves_canonical_shape():
    db = _FakeDB()
    p = _run(project_po_request_resolved(db, _po_row()))
    required = {
        "accountability_id", "source_module", "source_record_id", "title",
        "owner_role", "owner_user_id", "owner_employee_id",
        "owner_display_name",
        "assigned_at", "assigned_by", "due_at", "status", "priority",
        "first_viewed_at", "first_viewed_by",
        "last_activity_at", "last_activity_kind",
        "escalation_level",
        "resolved_at", "resolved_by", "resolution_notes",
        "overdue", "timeline_events",
    }
    assert set(p.keys()) == required


def test_po_resolved_never_mutates_input_row():
    db = _FakeDB(jobs_master=[
        {"project_number": "24-15", "primary_pm_name": "Tom"},
    ])
    row = _po_row()
    snapshot = dict(row)
    _run(project_po_request_resolved(db, row))
    assert row == snapshot


def test_po_resolved_pillar_1b_reservation():
    db = _FakeDB(jobs_master=[
        {"project_number": "24-15", "primary_pm_name": "Tom"},
    ])
    p = _run(project_po_request_resolved(db, _po_row()))
    assert p["escalation_level"] == 0


def test_po_resolved_db_failure_falls_back_gracefully():
    """If the PM lookup raises, the base projection must survive."""
    class _BrokenJobs:
        async def find_one(self, *args, **kwargs):
            raise RuntimeError("simulated index miss")
    class _BrokenDB:
        jobs_master = _BrokenJobs()
        corrective_actions = _FakeCollection([])

    p = _run(project_po_request_resolved(_BrokenDB(), _po_row()))
    assert p["owner_display_name"] == "Pending Approver"


# ════════════════════════════════════════════════════════════════════
# § Incident CA-assignee resolver
# ════════════════════════════════════════════════════════════════════
def _inc_row(**overrides):
    base = {
        "id": "inc-1",
        "doc_id": "INC-2026-0099",
        "severity": "critical",
        "osha_recordable": "No",
        "corrected_on_site": "No",
        "created_at": PAST_2D,
    }
    base.update(overrides)
    return base


def test_incident_resolved_promotes_open_ca_assignee():
    db = _FakeDB(corrective_actions=[
        {"id": "ca-9", "source_id": "inc-1",
         "status": "In Progress",
         "assigned_to_name": "Alice Auditor",
         "employee_master_id": "emp-alice",
         "created_at": PAST_2D},
    ])
    p = _run(project_incident_resolved(db, _inc_row()))
    assert p["owner_display_name"] == "Alice Auditor"
    assert p["owner_role"] == "safety"
    assert p["owner_employee_id"] == "emp-alice"


def test_incident_resolved_prefers_open_ca_over_closed():
    db = _FakeDB(corrective_actions=[
        {"id": "ca-old", "source_id": "inc-1",
         "status": "Closed",
         "assigned_to_name": "Bob Legacy",
         "created_at": "2025-01-01T00:00:00+00:00"},
        {"id": "ca-new", "source_id": "inc-1",
         "status": "Open",
         "assigned_to_name": "Cara Current",
         "created_at": PAST_2D},
    ])
    p = _run(project_incident_resolved(db, _inc_row()))
    assert p["owner_display_name"] == "Cara Current"


def test_incident_resolved_promotes_any_ca_when_no_open_ca():
    """When all linked CAs are closed, the most-recent named assignee
    is still surfaced (preferable to "Safety" placeholder)."""
    db = _FakeDB(corrective_actions=[
        {"id": "ca-closed", "source_id": "inc-1",
         "status": "Closed",
         "assigned_to_name": "Dean Historic",
         "created_at": PAST_2D},
    ])
    p = _run(project_incident_resolved(db, _inc_row()))
    assert p["owner_display_name"] == "Dean Historic"


def test_incident_resolved_falls_back_when_no_linked_ca():
    """Mirrors the live preview data — no linked CA with assignee.
    "Safety" fallback must survive."""
    db = _FakeDB(corrective_actions=[])
    p = _run(project_incident_resolved(db, _inc_row()))
    assert p["owner_display_name"] == "Safety"
    assert p["owner_role"] == "safety"


def test_incident_resolved_falls_back_when_ca_has_no_assignee_name():
    """CA exists but assigned_to_name is empty — fallback preserved."""
    db = _FakeDB(corrective_actions=[
        {"id": "ca-1", "source_id": "inc-1", "status": "Open",
         "assigned_to_name": ""},
    ])
    p = _run(project_incident_resolved(db, _inc_row()))
    assert p["owner_display_name"] == "Safety"


def test_incident_resolved_matches_via_incident_id_field():
    """Some CA rows store the link as `incident_id` instead of
    `source_id` — the resolver must match either."""
    db = _FakeDB(corrective_actions=[
        {"id": "ca-1", "incident_id": "inc-1", "status": "Open",
         "assigned_to_name": "Eli Linked",
         "created_at": PAST_2D},
    ])
    p = _run(project_incident_resolved(db, _inc_row()))
    assert p["owner_display_name"] == "Eli Linked"


def test_incident_resolved_preserves_canonical_shape():
    db = _FakeDB()
    p = _run(project_incident_resolved(db, _inc_row()))
    required = {
        "accountability_id", "source_module", "source_record_id", "title",
        "owner_role", "owner_user_id", "owner_employee_id",
        "owner_display_name",
        "assigned_at", "assigned_by", "due_at", "status", "priority",
        "first_viewed_at", "first_viewed_by",
        "last_activity_at", "last_activity_kind",
        "escalation_level",
        "resolved_at", "resolved_by", "resolution_notes",
        "overdue", "timeline_events",
    }
    assert set(p.keys()) == required


def test_incident_resolved_never_mutates_input_row():
    db = _FakeDB(corrective_actions=[
        {"id": "ca-1", "source_id": "inc-1", "status": "Open",
         "assigned_to_name": "Alice"},
    ])
    row = _inc_row()
    snapshot = dict(row)
    _run(project_incident_resolved(db, row))
    assert row == snapshot


def test_incident_resolved_pillar_1b_reservation():
    db = _FakeDB(corrective_actions=[
        {"id": "ca-1", "source_id": "inc-1", "status": "Open",
         "assigned_to_name": "Alice"},
    ])
    p = _run(project_incident_resolved(db, _inc_row()))
    assert p["escalation_level"] == 0


def test_incident_resolved_db_failure_falls_back_gracefully():
    """If the resolver-specific CA lookup raises, the base projection
    must survive and the resolver returns the base fallback owner.
    (The base projection's own CA lookup is exercised separately.)
    """
    # Partial broken collection: the base projection's lookup (queries
    # status:{$in:[Closed,...]}) succeeds with `None`; the resolver's
    # lookup (queries assigned_to_name:{$nin:[None,""]}) raises.
    class _PartialBroken:
        async def find_one(self, query, _proj=None, sort=None):
            if "assigned_to_name" in query:
                raise RuntimeError("simulated index miss on resolver query")
            return None  # base projection: no closed CA = unresolved
    class _PartialDB:
        corrective_actions = _PartialBroken()

    p = _run(project_incident_resolved(_PartialDB(), _inc_row()))
    assert p["owner_display_name"] == "Safety"


# ════════════════════════════════════════════════════════════════════
# § Cross-resolver invariants
# ════════════════════════════════════════════════════════════════════
def test_both_resolvers_emit_no_escalated_event_kind():
    """Even when authoritative routing data exists, neither resolver
    introduces an `escalated` event — Pillar 1B reservation."""
    db_po = _FakeDB(jobs_master=[
        {"project_number": "24-15", "primary_pm_name": "Tom"},
    ])
    db_inc = _FakeDB(corrective_actions=[
        {"id": "ca-1", "source_id": "inc-1", "status": "Open",
         "assigned_to_name": "Alice"},
    ])
    p_po = _run(project_po_request_resolved(db_po, _po_row()))
    p_inc = _run(project_incident_resolved(db_inc, _inc_row()))
    for ev in p_po["timeline_events"] + p_inc["timeline_events"]:
        assert ev["event_kind"] != "escalated"
