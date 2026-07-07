"""TRACK 23.10-C · Trench Project Linker + ODS Facts — lock envelope.

Covers:
  * 6-rung resolution ladder (explicit · daily-report · parent · deployment ·
    current-asset · ambiguous · missing).
  * 7 canonical physical fact emitters (idempotent, natural-keyed).
  * B-04 invariant lock: Repair Complete ≠ Safe To Use.
  * Companion `trench_verification_fact` fires on transition.
  * 4 derived views (deployment · asset_utilization · release · activity).
  * Backfill script idempotency.
  * ODS FACT_TYPES extension.
  * Router shape + PM/Safety scope.
  * Regression: 23.10-B untouched.
"""
from __future__ import annotations

import asyncio
import re
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

import pytest

BACKEND = Path(__file__).resolve().parents[1]


def _r(p: Path) -> str:
    return p.read_text(encoding="utf-8")


# ─── In-memory Mongo double (mirror of 23.10-B fixture) ─────────────
class _Cursor:
    def __init__(self, docs):
        self._docs = docs

    def sort(self, *a, **k):
        return self

    def limit(self, n):
        self._docs = self._docs[:n]
        return self

    async def to_list(self, n):
        return list(self._docs)[: n or 100000]

    def __aiter__(self):
        self._i = 0
        return self

    async def __anext__(self):
        if self._i >= len(self._docs):
            raise StopAsyncIteration
        d = self._docs[self._i]; self._i += 1
        return d


def _match(doc, q):
    for k, v in q.items():
        if k == "$and":
            if not all(_match(doc, s) for s in v):
                return False
            continue
        if k == "$or":
            if not any(_match(doc, s) for s in v):
                return False
            continue
        # payload.field  →  nested lookup
        if "." in k:
            parts = k.split(".")
            cur = doc
            for p in parts:
                if isinstance(cur, dict):
                    cur = cur.get(p)
                else:
                    cur = None; break
            if isinstance(v, dict):
                for op, opv in v.items():
                    if op == "$ne":
                        if cur == opv:
                            return False
                    elif op == "$in":
                        if cur not in opv:
                            return False
                    elif op == "$gte":
                        if cur is None or cur < opv:
                            return False
                    elif op == "$lte":
                        if cur is None or cur > opv:
                            return False
                    elif op == "$exists":
                        exists = cur is not None
                        if bool(opv) != exists:
                            return False
                    else:
                        return False
                continue
            if cur != v:
                return False
            continue
        if isinstance(v, dict):
            for op, opv in v.items():
                dv = doc.get(k)
                if op == "$in":
                    if dv not in opv:
                        return False
                elif op == "$exists":
                    if bool(opv) != (k in doc):
                        return False
                elif op == "$ne":
                    if dv == opv:
                        return False
                elif op == "$gte":
                    if dv is None or dv < opv:
                        return False
                elif op == "$lte":
                    if dv is None or dv > opv:
                        return False
                else:
                    return False
            continue
        if doc.get(k) != v:
            return False
    return True


class _Coll:
    def __init__(self, name):
        self.name = name
        self.docs: List[Dict[str, Any]] = []

    def find(self, q=None, projection=None):
        q = q or {}
        return _Cursor([d for d in self.docs if _match(d, q)])

    def aggregate(self, pipeline):
        return self.find(pipeline[0]["$match"] if pipeline and "$match" in pipeline[0] else {})

    async def find_one(self, q, projection=None):
        for d in self.docs:
            if _match(d, q):
                return dict(d)
        return None

    async def insert_one(self, d):
        self.docs.append(dict(d))
        return type("R", (), {"inserted_id": d.get("id")})()

    async def insert_many(self, docs, ordered=True):
        for d in docs:
            self.docs.append(dict(d))
        return type("R", (), {"inserted_ids": [x.get("id") for x in docs]})()

    async def update_one(self, q, update):
        for d in self.docs:
            if _match(d, q):
                for k, v in (update.get("$set") or {}).items():
                    d[k] = v
                return type("R", (), {"matched_count": 1, "modified_count": 1})()
        return type("R", (), {"matched_count": 0, "modified_count": 0})()

    async def update_many(self, q, update):
        n = 0
        for d in self.docs:
            if _match(d, q):
                for k, v in (update.get("$set") or {}).items():
                    d[k] = v
                n += 1
        return type("R", (), {"matched_count": n, "modified_count": n})()

    async def count_documents(self, q):
        return sum(1 for d in self.docs if _match(d, q))

    async def create_index(self, *a, **k):
        return "ok"


class _DB:
    def __init__(self):
        self._colls: Dict[str, _Coll] = {}

    def __getitem__(self, name):
        return self._colls.setdefault(name, _Coll(name))

    def __getattr__(self, name):
        return self._colls.setdefault(name, _Coll(name))


@pytest.fixture
def db():
    return _DB()


def _iso(d):
    return d.isoformat() if isinstance(d, datetime) else d


NOW = datetime.now(timezone.utc)


# =====================================================================
# 1) Static lock tests
# =====================================================================

def test_track_23_10_c_files_exist():
    for p in (
        BACKEND / "services" / "trench_safety" / "__init__.py",
        BACKEND / "services" / "trench_safety" / "project_linker.py",
        BACKEND / "services" / "trench_safety" / "facts_emitter.py",
        BACKEND / "services" / "trench_safety" / "derived_views.py",
        BACKEND / "routes" / "trench_project_intelligence.py",
        BACKEND / "scripts" / "backfill_track_23_10_c_trench_facts.py",
    ):
        assert p.exists(), f"missing {p}"


def test_ods_fact_types_extended_with_trench_facts():
    src = _r(BACKEND / "services" / "ods_spine" / "model.py")
    for t in (
        "excavation_day_fact", "trench_inspection_fact",
        "trench_hold_fact", "trench_repair_fact",
        "trench_verification_fact",
        "competent_person_assignment_fact",
        "project_excavation_summary_fact",
    ):
        assert t in src, f"model.py missing {t}"


def test_router_mounted_in_server():
    src = _r(BACKEND / "server.py")
    assert "from routes.trench_project_intelligence import" in src
    assert "build_trench_project_intelligence_router" in src
    assert "_track_23_10_c_trench_backfill_bootstrap" in src


def test_no_pdf_email_or_dr_v3_edits_in_23_10_c():
    """23.10-C ships NO consumer wire-ups. Repo-level guard."""
    grep_targets = [
        BACKEND / "services" / "trench_safety",
        BACKEND / "routes" / "trench_project_intelligence.py",
        BACKEND / "scripts" / "backfill_track_23_10_c_trench_facts.py",
    ]
    banned = re.compile(
        r"(pdf_render|email_routing|daily_report_v3_pdf|"
        r"send_email_via_resend|scheduling_readiness_writer|"
        r"routes/daily_reports_v3\.py|_write_daily_report)",
    )
    for base in grep_targets:
        paths = [base] if base.is_file() else list(base.rglob("*.py"))
        for p in paths:
            content = p.read_text(encoding="utf-8", errors="ignore")
            m = banned.search(content)
            assert m is None, f"forbidden coupling in {p}: {m.group(0)}"


def test_router_paths_declared():
    from routes.trench_project_intelligence import (
        build_trench_project_intelligence_router,
    )
    r = build_trench_project_intelligence_router(
        None, require_read_dep=lambda: None, require_admin_dep=lambda: None,
    )
    got = {(tuple(sorted(rt.methods)), rt.path) for rt in r.routes}
    required = {
        (("GET",), "/api/trench-intelligence/projects/{project_number}/summary"),
        (("GET",), "/api/trench-intelligence/projects/{project_number}/excavations"),
        (("GET",), "/api/trench-intelligence/projects/{project_number}/inspections"),
        (("GET",), "/api/trench-intelligence/projects/{project_number}/holds"),
        (("GET",), "/api/trench-intelligence/projects/{project_number}/repairs"),
        (("GET",), "/api/trench-intelligence/projects/{project_number}/competent-persons"),
        (("GET",), "/api/trench-intelligence/projects/{project_number}/deployments"),
        (("GET",), "/api/trench-intelligence/projects/{project_number}/asset-utilization"),
        (("GET",), "/api/trench-intelligence/projects/{project_number}/releases"),
        (("GET",), "/api/trench-intelligence/projects/{project_number}/activity"),
        (("GET",), "/api/trench-intelligence/projects/{project_number}/readiness"),
        (("GET",), "/api/trench-intelligence/company/summary"),
        (("POST",), "/api/trench-intelligence/backfill"),
        (("POST",), "/api/trench-intelligence/projects/{project_number}/recompute-summary"),
        (("GET",), "/api/trench-intelligence/link-resolve/{collection}/{record_id}"),
    }
    missing = required - got
    assert not missing, f"missing routes: {missing}"


# =====================================================================
# 2) Project Linker — 6-rung ladder
# =====================================================================

def test_explicit_project_wins(db):
    from services.trench_safety.project_linker import resolve_project
    row = {"id": "r1", "project_number": "24-12", "asset_id": "A1"}
    linkage = asyncio.get_event_loop().run_until_complete(
        resolve_project(db, row))
    assert linkage.project_number == "24-12"
    assert linkage.project_link_status == "explicit"
    assert linkage.confidence == "high"


def test_daily_report_link(db):
    from services.trench_safety.project_linker import resolve_project
    db.daily_reports.docs.append({
        "id": "DR1", "project_number": "25-05",
        "day_setup": {"project_number": "25-05"},
    })
    row = {"id": "r2", "daily_report_doc_id": "DR1", "asset_id": "A1"}
    linkage = asyncio.get_event_loop().run_until_complete(
        resolve_project(db, row))
    assert linkage.project_number == "25-05"
    assert linkage.project_link_status == "inherited_from_daily_report"
    assert linkage.confidence == "high"


def test_parent_record_link(db):
    from services.trench_safety.project_linker import resolve_project
    db.trench_safety_inspections.docs.append(
        {"id": "I1", "project_number": "26-01", "asset_id": "A1"})
    row = {"id": "r3", "source_ref": "I1",
           "source_ref_kind": "trench_safety_inspections",
           "asset_id": "A1"}
    linkage = asyncio.get_event_loop().run_until_complete(
        resolve_project(db, row))
    assert linkage.project_number == "26-01"
    assert linkage.project_link_status == "inherited_from_parent_record"


def test_deployment_window_link_medium(db):
    from services.trench_safety.project_linker import resolve_project
    t = NOW.isoformat()
    db.trench_safety_deployments.docs.append({
        "id": "D1", "asset_id": "A1",
        "project_number": "27-02", "project_name": "P27-02",
        "assigned_at": (NOW - timedelta(days=3)).isoformat(),
        "returned_at": None,
    })
    row = {"id": "r4", "asset_id": "A1", "opened_at": t}
    linkage = asyncio.get_event_loop().run_until_complete(
        resolve_project(db, row))
    assert linkage.project_number == "27-02"
    assert linkage.project_link_status == "inferred_from_assignment"
    assert linkage.confidence == "medium"


def test_deployment_ambiguous_when_multiple(db):
    from services.trench_safety.project_linker import resolve_project
    t = NOW.isoformat()
    for i, pn in enumerate(("28-01", "28-02")):
        db.trench_safety_deployments.docs.append({
            "id": f"D{i}", "asset_id": "A1",
            "project_number": pn,
            "assigned_at": (NOW - timedelta(days=5)).isoformat(),
            "returned_at": None,
        })
    row = {"id": "r5", "asset_id": "A1", "opened_at": t}
    linkage = asyncio.get_event_loop().run_until_complete(
        resolve_project(db, row))
    assert linkage.project_number is None
    assert linkage.project_link_status == "ambiguous"


def test_missing_when_no_link_available(db):
    from services.trench_safety.project_linker import resolve_project
    row = {"id": "orphan", "asset_id": "A99"}
    linkage = asyncio.get_event_loop().run_until_complete(
        resolve_project(db, row))
    assert linkage.project_number is None
    assert linkage.project_link_status == "missing"
    assert linkage.confidence == "none"


def test_never_promotes_low_confidence(db):
    """Rung 5 must stay `low`. Never returns `high` from asset current-project."""
    from services.trench_safety.project_linker import resolve_project
    t = (NOW - timedelta(hours=1)).isoformat()
    db.trench_safety_assets.docs.append({
        "id": "AX", "asset_id": "AX",
        "current_project_number": "29-09",
        "updated_at": NOW.isoformat(),
    })
    row = {"id": "r7", "asset_id": "AX", "opened_at": t}
    linkage = asyncio.get_event_loop().run_until_complete(
        resolve_project(db, row))
    assert linkage.project_link_status == "inferred_from_current_asset"
    assert linkage.confidence == "low"


# =====================================================================
# 3) Facts emitter — idempotency + B-04 invariant lock
# =====================================================================

def test_excavation_day_fact_idempotent(db):
    from services.trench_safety.facts_emitter import (
        emit_excavation_day_fact,
    )
    row = {"id": "E1", "project_number": "30-01",
           "date_of_work": "2026-02-06",
           "excavation_type": "trench",
           "max_depth_ft": 6.0,
           "protective_system": "trench_box",
           "inspection_completed": True}
    asyncio.get_event_loop().run_until_complete(
        emit_excavation_day_fact(db, row))
    asyncio.get_event_loop().run_until_complete(
        emit_excavation_day_fact(db, row))
    current = [f for f in db.operational_facts.docs
               if f.get("fact_type") == "excavation_day_fact"
               and f.get("is_current") is True]
    assert len(current) == 1
    payload = current[0]["payload"]
    assert payload["max_depth_ft"] == 6.0
    assert payload["linkage"]["project_number"] == "30-01"


def test_repair_fact_b04_invariant_locked(db):
    """Repair Complete ≠ Safe To Use. Locked forever."""
    from services.trench_safety.facts_emitter import emit_trench_repair_fact
    # status=completed but verified_at=None → safe_to_use_verified MUST be False.
    row = {"id": "R1", "project_number": "31-01",
           "status": "completed",
           "verified_at": None,
           "reinspection_passed": False,
           "asset_id": "A1"}
    asyncio.get_event_loop().run_until_complete(
        emit_trench_repair_fact(db, row))
    facts = [f for f in db.operational_facts.docs
             if f.get("fact_type") == "trench_repair_fact"
             and f.get("is_current") is True]
    assert len(facts) == 1
    assert facts[0]["payload"]["safe_to_use_verified"] is False
    # No verification companion fact must have been emitted.
    vfs = [f for f in db.operational_facts.docs
           if f.get("fact_type") == "trench_verification_fact"]
    assert vfs == []


def test_repair_fact_safe_only_when_verified_and_reinspected(db):
    from services.trench_safety.facts_emitter import emit_trench_repair_fact
    row = {"id": "R2", "project_number": "31-02",
           "status": "completed",
           "verified_at": "2026-02-06T00:00:00Z",
           "reinspection_passed": True,
           "asset_id": "A2"}
    asyncio.get_event_loop().run_until_complete(
        emit_trench_repair_fact(db, row))
    facts = [f for f in db.operational_facts.docs
             if f.get("fact_type") == "trench_repair_fact"
             and f.get("is_current") is True]
    assert facts[0]["payload"]["safe_to_use_verified"] is True
    # Verification companion fact WAS emitted.
    vfs = [f for f in db.operational_facts.docs
           if f.get("fact_type") == "trench_verification_fact"
           and f.get("is_current") is True]
    assert len(vfs) == 1


def test_hold_fact_carries_is_active(db):
    from services.trench_safety.facts_emitter import emit_trench_hold_fact
    row = {"id": "H1", "project_number": "32-01",
           "asset_id": "A1", "kind": "safety",
           "opened_at": NOW.isoformat(),
           "cleared_at": None,
           "is_active": True}
    asyncio.get_event_loop().run_until_complete(
        emit_trench_hold_fact(db, row))
    facts = [f for f in db.operational_facts.docs
             if f.get("fact_type") == "trench_hold_fact"
             and f.get("is_current") is True]
    assert facts[0]["payload"]["is_active"] is True


def test_inspection_fact_project_linked(db):
    from services.trench_safety.facts_emitter import emit_trench_inspection_fact
    # Use deployment window rung 4 — no explicit project_number.
    t = NOW.isoformat()
    db.trench_safety_deployments.docs.append({
        "id": "D9", "asset_id": "A9",
        "project_number": "33-01",
        "assigned_at": (NOW - timedelta(days=1)).isoformat(),
        "returned_at": None,
    })
    row = {"id": "IX1", "asset_id": "A9", "opened_at": t,
           "inspection_type": "pre_use", "result": "pass"}
    asyncio.get_event_loop().run_until_complete(
        emit_trench_inspection_fact(db, row))
    f = [x for x in db.operational_facts.docs
         if x.get("fact_type") == "trench_inspection_fact"][0]
    assert f["project_id"] == "33-01"
    assert f["payload"]["linkage"]["confidence"] == "medium"


def test_competent_person_assignment_fact_consumes_snapshot_verbatim(db):
    from services.trench_safety.facts_emitter import (
        emit_competent_person_assignment_fact,
    )
    snap = {
        "qualification_id": "Q1",
        "qualification_type": "COMPETENT_PERSON",
        "employee_id": "E1", "employee_master_id": "E1",
        "person_name_snapshot": "Alice",
        "person_trade_snapshot": "Foreman",
        "person_crew_snapshot": "Concrete",
        "verification_status_at_selection": "active",
        "expires_at_at_selection": "2027-02-06",
        "is_active_at_selection": True,
        "snapshot_at": "2026-02-06T00:00:00+00:00",
    }
    asyncio.get_event_loop().run_until_complete(
        emit_competent_person_assignment_fact(
            db, project_number="34-01",
            consumer_collection="daily_reports",
            consumer_source_id="daily_reports",
            consumer_row_id="DR-001",
            qualification_snapshot=snap,
            date_of_work="2026-02-06",
        ))
    f = [x for x in db.operational_facts.docs
         if x.get("fact_type") == "competent_person_assignment_fact"][0]
    pl = f["payload"]
    assert pl["qualification_id"] == "Q1"
    assert pl["person_name_snapshot"] == "Alice"
    assert pl["cert_valid_at_report"] is True
    assert pl["project_number"] == "34-01"


def test_summary_recompute_aggregates(db):
    from services.trench_safety.facts_emitter import (
        emit_excavation_day_fact,
        emit_trench_hold_fact,
        emit_trench_repair_fact,
        recompute_project_excavation_summary,
    )
    proj = "35-01"
    asyncio.get_event_loop().run_until_complete(
        emit_excavation_day_fact(db, {
            "id": "e1", "project_number": proj, "max_depth_ft": 8.0,
            "inspection_completed": True, "date_of_work": "2026-02-06",
        }))
    asyncio.get_event_loop().run_until_complete(
        emit_trench_hold_fact(db, {
            "id": "h1", "project_number": proj, "asset_id": "A1",
            "kind": "safety", "opened_at": NOW.isoformat(),
            "cleared_at": None, "is_active": True,
        }))
    asyncio.get_event_loop().run_until_complete(
        emit_trench_repair_fact(db, {
            "id": "rp1", "project_number": proj, "status": "completed",
            "verified_at": NOW.isoformat(),
            "reinspection_passed": True, "asset_id": "A1",
        }))
    asyncio.get_event_loop().run_until_complete(
        recompute_project_excavation_summary(db, proj))
    summaries = [f for f in db.operational_facts.docs
                 if f.get("fact_type") == "project_excavation_summary_fact"
                 and f.get("is_current") is True]
    assert len(summaries) == 1
    pl = summaries[0]["payload"]
    assert pl["excavation_day_count"] == 1
    assert pl["open_trench_holds"] == 1
    assert pl["trench_safe_to_use_verified_count"] == 1
    assert pl["max_depth_observed_ft"] == 8.0


# =====================================================================
# 4) Backfill script — idempotency
# =====================================================================

def test_backfill_idempotent(db):
    from scripts.backfill_track_23_10_c_trench_facts import run_backfill
    # Seed a couple of rows.
    db.trench_excavations.docs.append({
        "id": "EBF", "project_number": "40-01",
        "date_of_work": "2026-02-06", "max_depth_ft": 5.0,
        "excavation_type": "trench",
    })
    db.trench_safety_holds.docs.append({
        "id": "HBF", "project_number": "40-01", "asset_id": "A1",
        "kind": "safety", "opened_at": NOW.isoformat(),
        "is_active": True,
    })
    r1 = asyncio.get_event_loop().run_until_complete(
        run_backfill(db, boot_mode=False))
    r2 = asyncio.get_event_loop().run_until_complete(
        run_backfill(db, boot_mode=False))
    # After 2 runs, still exactly 1 current fact per (row, type).
    excs = [f for f in db.operational_facts.docs
            if f.get("fact_type") == "excavation_day_fact"
            and f.get("is_current") is True]
    assert len(excs) == 1
    holds = [f for f in db.operational_facts.docs
             if f.get("fact_type") == "trench_hold_fact"
             and f.get("is_current") is True]
    assert len(holds) == 1
    # Summary fact recomputed with same project.
    summs = [f for f in db.operational_facts.docs
             if f.get("fact_type") == "project_excavation_summary_fact"
             and f.get("is_current") is True]
    assert len(summs) == 1
    assert isinstance(r1["projects_resolved"], int)
    assert r2["projects_resolved"] == r1["projects_resolved"]


# =====================================================================
# 5) Derived views — reads only, never new fact_types
# =====================================================================

def test_derived_views_do_not_write_facts(db):
    """The 4 derived views must be pure reads — they never write to
    `operational_facts`. This test catches accidental fact emissions."""
    from services.trench_safety.derived_views import (
        deployment_view, trench_asset_utilization,
        trench_release_view, excavation_activity_view,
    )
    before = len(db.operational_facts.docs)
    asyncio.get_event_loop().run_until_complete(
        deployment_view(db, project_number="41-01"))
    asyncio.get_event_loop().run_until_complete(
        trench_asset_utilization(db, "41-01"))
    asyncio.get_event_loop().run_until_complete(
        trench_release_view(db, project_number="41-01"))
    asyncio.get_event_loop().run_until_complete(
        excavation_activity_view(db, "41-01"))
    after = len(db.operational_facts.docs)
    assert before == after


def test_asset_utilization_counts_open_deployments(db):
    from services.trench_safety.derived_views import trench_asset_utilization
    db.trench_safety_deployments.docs.append({
        "id": "D-U", "asset_id": "A-U", "project_number": "42-01",
        "assigned_at": (NOW - timedelta(days=5)).isoformat(),
        "returned_at": None,
    })
    rows = asyncio.get_event_loop().run_until_complete(
        trench_asset_utilization(db, "42-01"))
    assert len(rows) == 1
    assert rows[0]["active"] is True
    assert rows[0]["deployment_count"] == 1


# =====================================================================
# 6) Regression — 23.10-B untouched
# =====================================================================

def test_23_10_b_qualification_registry_still_shape():
    """Do not regress the Qualifications Engine."""
    from services.certifications.qualification_registry import (
        is_active,
    )
    from services.certifications.qualification_types import (
        QUALIFICATION_ENGINE_TYPES,
    )
    assert "COMPETENT_PERSON" in QUALIFICATION_ENGINE_TYPES
    assert callable(is_active)
