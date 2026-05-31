"""Pillar 2 · Phase A · Command Center scoring tests.

Pure-function tests over the per-card scoring builders. Uses an
in-memory fake `db` and drives async builders via asyncio.run() (no
pytest-asyncio dependency).
"""

from __future__ import annotations

import asyncio
import os
import sys
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List

# Ensure backend is importable from tests/ (matches sibling tests)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from routes.command_center import (  # noqa: E402
    DEFAULT_THRESHOLDS,
    _build_jobs_card,
    _build_safety_card,
    _build_equipment_card,
    _build_accountability_card,
    _build_approvals_card,
    _worst_pill,
)


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _hours_ago(h: float) -> str:
    return _iso(datetime.now(timezone.utc) - timedelta(hours=h))


def _days_ago(d: float) -> str:
    return _iso(datetime.now(timezone.utc) - timedelta(days=d))


class _FakeCursor:
    def __init__(self, docs: List[Dict[str, Any]]):
        self._docs = list(docs)

    def sort(self, *_a, **_kw):
        return self

    def limit(self, _n):
        return self

    async def to_list(self, length=None):
        return list(self._docs if length is None else self._docs[: int(length)])


class _FakeCollection:
    def __init__(self, docs: List[Dict[str, Any]]):
        self._docs = docs

    def _match(self, doc: Dict[str, Any], filt: Dict[str, Any]) -> bool:
        for k, v in filt.items():
            if k == "$or":
                if not any(self._match(doc, sub) for sub in v):
                    return False
                continue
            if k == "$and":
                if not all(self._match(doc, sub) for sub in v):
                    return False
                continue
            if k == "$expr":
                # Crude: tests using $expr (severity lowercase $in) — match any if severity in list
                try:
                    target = v.get("$in", [None, []])[1]
                    field = (doc.get("severity") or "").lower()
                    if field not in target:
                        return False
                    continue
                except Exception:
                    continue
            actual = doc.get(k)
            if isinstance(v, dict):
                if "$in" in v and actual not in v["$in"]:
                    return False
                if "$ne" in v and actual == v["$ne"]:
                    return False
                if "$exists" in v:
                    has = k in doc
                    if has != bool(v["$exists"]):
                        return False
                if "$lt" in v and (actual is None or not (actual < v["$lt"])):
                    return False
                if "$lte" in v and (actual is None or not (actual <= v["$lte"])):
                    return False
                if "$gte" in v and (actual is None or not (actual >= v["$gte"])):
                    return False
                if "$gt" in v and (actual is None or not (actual > v["$gt"])):
                    return False
                if "$regex" in v:
                    import re as _re
                    flags = _re.IGNORECASE if "i" in (v.get("$options") or "") else 0
                    if actual is None or not _re.search(v["$regex"], str(actual), flags):
                        return False
            else:
                if actual != v:
                    return False
        return True

    def find(self, filt: Dict[str, Any] = None, _proj=None, **_kw):
        return _FakeCursor([d for d in self._docs if self._match(d, filt or {})])

    async def find_one(self, filt: Dict[str, Any] = None, _proj=None, **_kw):
        for d in self._docs:
            if self._match(d, filt or {}):
                return d
        return None

    async def count_documents(self, filt: Dict[str, Any]):
        return sum(1 for d in self._docs if self._match(d, filt))


class _FakeDb:
    def __init__(self):
        self.jobs_master = _FakeCollection([])
        self.daily_reports = _FakeCollection([])
        self.incidents = _FakeCollection([])
        self.corrective_actions = _FakeCollection([])
        self.fleet_defects = _FakeCollection([])
        self.tasks = _FakeCollection([])
        self.po_requests = _FakeCollection([])


def _run(coro):
    return asyncio.run(coro)


# ── unit tests (synchronous wrappers) ────────────────────────────


def test_worst_pill_priority():
    assert _worst_pill("GREEN", "GREEN") == "GREEN"
    assert _worst_pill("GREEN", "AMBER") == "AMBER"
    assert _worst_pill("AMBER", "RED") == "RED"
    assert _worst_pill("RED", "GREEN") == "RED"


def test_default_thresholds_have_all_required_rules():
    required = {
        "JOBS-DR-MISSING", "JOBS-ISSUE-NO-OWNER", "JOBS-ISSUE-NO-PATH",
        "SAF-CRITICAL-UNRESOLVED", "SAF-OSHA-OPEN", "SAF-CA-OVERDUE", "SAF-CA-CHRONIC",
        "EQP-OOS-OLD", "EQP-OOS-NEW", "EQP-BACKLOG",
        "ACC-HIGH-OVERDUE", "ACC-STALE",
        "APP-AMBER", "APP-RED", "APP-WEEK",
    }
    assert required.issubset(set(DEFAULT_THRESHOLDS["rules"].keys()))
    for rid, r in DEFAULT_THRESHOLDS["rules"].items():
        assert "predicate" in r, f"{rid} missing predicate"
        assert "operational_risk" in r, f"{rid} missing operational_risk"
        assert "leadership_action" in r, f"{rid} missing leadership_action"
        assert "owner_role" in r, f"{rid} missing owner_role"
        assert "expected_resolution" in r, f"{rid} missing expected_resolution"


def test_jobs_card_green_when_all_active_jobs_have_dr():
    db = _FakeDb()
    db.jobs_master = _FakeCollection([
        {"id": "j1", "project_number": "P1", "status": "Active",
         "primary_pm_name": "Alice"},
    ])
    db.daily_reports = _FakeCollection([
        {"id": "d1", "project_number": "P1", "created_at": _hours_ago(2)},
    ])
    card = _run(_build_jobs_card(db, DEFAULT_THRESHOLDS["rules"]))
    assert card["card_id"] == "jobs"
    assert card["pill"] == "GREEN"
    assert card["warnings"] == []


def test_jobs_card_red_when_many_jobs_missing_dr():
    db = _FakeDb()
    db.jobs_master = _FakeCollection([
        {"id": f"j{i}", "project_number": f"P{i}", "status": "Active",
         "primary_pm_name": f"PM{i}"}
        for i in range(6)
    ])
    card = _run(_build_jobs_card(db, DEFAULT_THRESHOLDS["rules"]))
    assert card["pill"] == "RED"
    assert any(w["rule_id"] == "JOBS-DR-MISSING" and w["severity"] == "red"
               for w in card["warnings"])


def test_jobs_card_red_when_unowned_corrective_action():
    db = _FakeDb()
    db.corrective_actions = _FakeCollection([
        {"id": "ca1", "status": "Open", "title": "Unowned CA",
         "assigned_to_name": None},
    ])
    card = _run(_build_jobs_card(db, DEFAULT_THRESHOLDS["rules"]))
    assert card["pill"] == "RED"
    assert any(w["rule_id"] == "JOBS-ISSUE-NO-OWNER" for w in card["warnings"])


def test_safety_card_red_when_critical_incident_unresolved_48h():
    db = _FakeDb()
    db.incidents = _FakeCollection([
        {"id": "inc1", "severity": "Critical",
         "created_at": _hours_ago(50), "doc_id": "INC-001"},
    ])
    card = _run(_build_safety_card(db, DEFAULT_THRESHOLDS["rules"]))
    assert card["pill"] == "RED"
    assert any(w["rule_id"] == "SAF-CRITICAL-UNRESOLVED" and w["severity"] == "red"
               for w in card["warnings"])


def test_safety_card_amber_when_critical_incident_24h_only():
    db = _FakeDb()
    db.incidents = _FakeCollection([
        {"id": "inc1", "severity": "High", "created_at": _hours_ago(30)},
    ])
    card = _run(_build_safety_card(db, DEFAULT_THRESHOLDS["rules"]))
    assert card["pill"] == "AMBER"


def test_safety_card_red_on_osha_open_24h():
    db = _FakeDb()
    db.incidents = _FakeCollection([
        {"id": "inc1", "severity": "Warning",
         "osha_recordable": "Yes", "created_at": _hours_ago(48)},
    ])
    card = _run(_build_safety_card(db, DEFAULT_THRESHOLDS["rules"]))
    assert any(w["rule_id"] == "SAF-OSHA-OPEN" for w in card["warnings"])


def test_equipment_card_red_when_oos_72h():
    db = _FakeDb()
    db.fleet_defects = _FakeCollection([
        {"id": "fd1", "severity": "oos", "status": "open",
         "created_at": _hours_ago(80), "truck_unit_number": "T-1"},
    ])
    card = _run(_build_equipment_card(db, DEFAULT_THRESHOLDS["rules"]))
    assert card["pill"] == "RED"


def test_equipment_card_red_on_backlog():
    db = _FakeDb()
    docs = [
        {"id": f"fd{i}", "severity": "monitor", "status": "open",
         "created_at": _hours_ago(2), "truck_unit_number": f"T-{i}"}
        for i in range(25)
    ]
    db.fleet_defects = _FakeCollection(docs)
    card = _run(_build_equipment_card(db, DEFAULT_THRESHOLDS["rules"]))
    assert card["pill"] == "RED"
    assert any(w["rule_id"] == "EQP-BACKLOG" for w in card["warnings"])


def test_accountability_red_when_many_high_overdue():
    db = _FakeDb()
    db.tasks = _FakeCollection([
        {"id": f"t{i}", "priority": "High", "status": "Open",
         "due_at": _hours_ago(48)}
        for i in range(10)
    ])
    card = _run(_build_accountability_card(db, DEFAULT_THRESHOLDS["rules"]))
    assert card["pill"] == "RED"


def test_accountability_green_when_no_overdue():
    db = _FakeDb()
    db.tasks = _FakeCollection([
        # low-priority task is excluded from the rule (priorities_action_required)
        {"id": "t1", "priority": "Low", "status": "Open",
         "due_at": _hours_ago(48)},
    ])
    card = _run(_build_accountability_card(db, DEFAULT_THRESHOLDS["rules"]))
    assert card["pill"] == "GREEN"


def test_approvals_red_when_po_aged_5_days():
    db = _FakeDb()
    db.po_requests = _FakeCollection([
        {"id": "p1", "status": "Pending Approval",
         "created_at": _days_ago(6), "estimated_amount": 1000,
         "vendor": "Acme", "doc_id": "PO-001"},
    ])
    card = _run(_build_approvals_card(db, DEFAULT_THRESHOLDS["rules"]))
    assert card["pill"] == "RED"
    assert any(w["rule_id"] in ("APP-RED", "APP-WEEK") for w in card["warnings"])


def test_approvals_amber_when_po_aged_3_days():
    db = _FakeDb()
    db.po_requests = _FakeCollection([
        {"id": "p1", "status": "Pending Approval",
         "created_at": _days_ago(3.5), "estimated_amount": 500,
         "vendor": "Acme"},
    ])
    card = _run(_build_approvals_card(db, DEFAULT_THRESHOLDS["rules"]))
    assert card["pill"] == "AMBER"
