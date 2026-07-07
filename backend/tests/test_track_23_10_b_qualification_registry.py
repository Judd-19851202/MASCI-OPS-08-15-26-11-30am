"""TRACK 23.10-B · Qualifications Engine — lock envelope + logic tests.

Covers the 25-item Definition-of-Done from
`/app/memory/TRACK_23_10B_HANDOFF.md` §9.

Split into two families:

* **Static lock tests** — repo-shape guarantees that the engine
  files, migration, router mount, ODS fact type extension, and
  legacy-consumer delegation exist and stay wired.
* **Behavioural tests** — invoke the pure services with an in-memory
  Mongo double so we exercise the registry rule matrix (active /
  expired / suspended / revoked / pending / warning boundary) without
  needing a live database.
"""
from __future__ import annotations

import asyncio
import os
import re
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest


BACKEND = Path(__file__).resolve().parents[1]


def _r(p: Path) -> str:
    return p.read_text(encoding="utf-8")


# ─────────────────────────────────────────────────────────────────
# In-memory Mongo double — the smallest surface the engine needs.
# ─────────────────────────────────────────────────────────────────
class _Cursor:
    def __init__(self, docs: List[Dict[str, Any]]):
        self._docs = docs

    def sort(self, *a, **k):
        return self

    async def to_list(self, n):
        return list(self._docs)[: n or 100000]

    def __aiter__(self):
        self._i = 0
        return self

    async def __anext__(self):
        if self._i >= len(self._docs):
            raise StopAsyncIteration
        d = self._docs[self._i]
        self._i += 1
        return d


def _match(doc: Dict[str, Any], q: Dict[str, Any]) -> bool:
    for k, v in q.items():
        if k == "$and":
            if not all(_match(doc, sub) for sub in v):
                return False
            continue
        if k == "$or":
            if not any(_match(doc, sub) for sub in v):
                return False
            continue
        if isinstance(v, dict):
            for op, opv in v.items():
                dv = doc.get(k)
                if op == "$in":
                    if dv not in opv:
                        return False
                elif op == "$exists":
                    exists = k in doc
                    if bool(opv) != bool(exists):
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
    def __init__(self, name: str):
        self.name = name
        self.docs: List[Dict[str, Any]] = []

    def find(self, q: Dict[str, Any] = None, projection: Dict[str, Any] = None):
        q = q or {}
        return _Cursor([d for d in self.docs if _match(d, q)])

    async def find_one(self, q, projection=None):
        for d in self.docs:
            if _match(d, q):
                return dict(d)
        return None

    async def insert_one(self, d):
        self.docs.append(dict(d))
        return type("R", (), {"inserted_id": d.get("id") or d.get("_id")})()

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

    async def delete_one(self, q):
        for i, d in enumerate(self.docs):
            if _match(d, q):
                self.docs.pop(i)
                return type("R", (), {"deleted_count": 1})()
        return type("R", (), {"deleted_count": 0})()

    async def count_documents(self, q):
        return sum(1 for d in self.docs if _match(d, q))

    async def create_index(self, *a, **k):
        return "ok"


class _DB:
    def __init__(self):
        self._colls: Dict[str, _Coll] = {}

    def __getitem__(self, name: str) -> _Coll:
        return self._colls.setdefault(name, _Coll(name))

    def __getattr__(self, name: str) -> _Coll:
        return self._colls.setdefault(name, _Coll(name))


@pytest.fixture
def db():
    return _DB()


def _today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _plus_days(d: int) -> str:
    return (datetime.now(timezone.utc).date() + timedelta(days=d)).isoformat()


def _mk_emp(db, eid: str, name: str, trade: str = "General Laborer", crew: str = "Shop") -> Dict[str, Any]:
    doc = {
        "id": eid, "name": name, "employee_id": eid,
        "trade": trade, "crew": crew, "is_active": True,
    }
    db.employees.docs.append(doc)
    return doc


def _mk_qual(db, employee_id: str, *, qtype: str = "COMPETENT_PERSON",
             status: str = "active", expires_in: Optional[int] = 365,
             suspended: bool = False, revoked: bool = False,
             cert_type_legacy: Optional[str] = None) -> Dict[str, Any]:
    row = {
        "id": str(uuid.uuid4()),
        "employee_id": employee_id,
        "employee_master_id": employee_id,
        "employee_name": f"emp-{employee_id}",
        "qualification_type": qtype,
        "certification_type": cert_type_legacy or qtype,
        "training_name": qtype.replace("_", " ").title(),
        "completed_date": _today(),
        "expiration_date": _plus_days(expires_in) if expires_in is not None else None,
        "verification_status": status,
        "verification_status_history": [],
        "suspended_at": _today() if suspended else None,
        "revoked_at": _today() if revoked else None,
        "issuing_organization": "MASCI",
    }
    db.safety_training_records.docs.append(row)
    return row


# =====================================================================
# 1) Static lock tests — repo shape must not drift.
# =====================================================================

def test_engine_files_exist():
    for p in (
        BACKEND / "services" / "certifications" / "__init__.py",
        BACKEND / "services" / "certifications" / "qualification_types.py",
        BACKEND / "services" / "certifications" / "qualification_registry.py",
        BACKEND / "services" / "certifications" / "qualification_facts.py",
        BACKEND / "routes" / "qualifications.py",
        BACKEND / "scripts" / "migrate_track_23_10_b_qualification_engine.py",
    ):
        assert p.exists(), f"missing {p}"


def test_qualification_enum_seeds_all_16_types():
    from services.certifications.qualification_types import (
        QUALIFICATION_ENGINE_TYPES,
    )
    required = {
        "COMPETENT_PERSON", "OSHA_10", "OSHA_30", "FIRST_AID_CPR",
        "SIGNAL_PERSON", "CONFINED_SPACE", "RIGGING", "CRANE_OPERATOR",
        "EQUIPMENT_OPERATOR", "TRAFFIC_CONTROL_FLAGGER", "MSHA",
        "HAZWOPER", "DOT_MEDICAL", "CDL_ENDORSEMENT",
        "MANUFACTURER_CERT", "COMPANY_SPECIFIC",
    }
    got = set(QUALIFICATION_ENGINE_TYPES)
    missing = required - got
    assert not missing, f"missing types: {missing}"


def test_ods_fact_types_extended():
    src = _r(BACKEND / "services" / "ods_spine" / "model.py")
    for token in (
        "qualification_certification_fact",
        "qualification_expiration_fact",
        "qualification_assignment_fact",
    ):
        assert token in src, f"ods_spine/model.py missing {token}"


def test_qualifications_router_mounted_in_server():
    src = _r(BACKEND / "server.py")
    assert "from routes.qualifications import build_qualifications_router" in src
    assert "build_qualifications_router(" in src
    assert "_track_23_10_b_qualification_migration_bootstrap" in src


def test_trench_safety_delegates_to_engine():
    """Track 24.1 · P0-2 · The duplicate `/api/employees/competent-persons`
    handler previously registered in `routes.trench_safety.competent_persons`
    was REMOVED because it shipped without an auth dep and silently
    overrode the auth-gated `routes.qualifications:get_competent_persons`.
    The delegation is no longer needed here — the single canonical
    handler in `routes.qualifications` serves both consumer shapes
    (the legacy trench-safety EmployeePicker keys AND the new
    registry keys) inside its response, so downstream consumers keep
    working.  This test now locks the ABSENCE of the duplicate."""
    src = _r(BACKEND / "routes" / "trench_safety" / "competent_persons.py")
    assert '@api_router.get("/employees/competent-persons")' not in src, (
        "Duplicate route on /api/employees/competent-persons must NOT be "
        "re-added to routes/trench_safety/competent_persons.py — the "
        "auth-gated handler in routes/qualifications.py is the ONE source "
        "of truth (Track 24.1 P0-2)."
    )
    # Sanity: the qualifications router still delegates to the engine.
    qsrc = _r(BACKEND / "routes" / "qualifications.py")
    assert "from services.certifications.qualification_registry import" in qsrc
    assert "list_active_qualifications" in qsrc


def test_qualification_router_uses_api_prefix():
    src = _r(BACKEND / "routes" / "qualifications.py")
    assert 'APIRouter(prefix="/api"' in src


# =====================================================================
# 2) Behavioural tests — engine logic must be locked.
# =====================================================================

def test_is_active_excludes_expired():
    from services.certifications.qualification_registry import is_active
    row = {"verification_status": "active",
           "expiration_date": _plus_days(-1)}
    assert is_active(row) is False


def test_is_active_includes_no_expiration():
    from services.certifications.qualification_registry import is_active
    row = {"verification_status": "active"}
    assert is_active(row) is True


def test_is_active_excludes_suspended_revoked():
    from services.certifications.qualification_registry import is_active
    assert is_active({"verification_status": "active",
                      "expiration_date": _plus_days(30),
                      "suspended_at": _today()}) is False
    assert is_active({"verification_status": "active",
                      "expiration_date": _plus_days(30),
                      "revoked_at": _today()}) is False


def test_registry_excludes_all_inactive_statuses(db):
    from services.certifications.qualification_registry import (
        list_active_qualifications,
    )
    _mk_emp(db, "e1", "Alice")
    _mk_qual(db, "e1", status="active")
    _mk_qual(db, "e1", status="expired", expires_in=-10)
    _mk_qual(db, "e1", status="suspended", suspended=True)
    _mk_qual(db, "e1", status="revoked", revoked=True)
    _mk_qual(db, "e1", status="pending")
    rows = asyncio.get_event_loop().run_until_complete(
        list_active_qualifications(db, qualification_type="COMPETENT_PERSON")
    )
    assert len(rows) == 1
    assert rows[0]["verification_status"] == "active"


def test_warning_boundary(db):
    from services.certifications.qualification_registry import (
        list_active_qualifications,
    )
    _mk_emp(db, "e1", "Alice")
    _mk_emp(db, "e2", "Bob")
    _mk_emp(db, "e3", "Cara")
    _mk_qual(db, "e1", expires_in=29)       # inside window
    _mk_qual(db, "e2", expires_in=30)       # boundary — inside
    _mk_qual(db, "e3", expires_in=31)       # outside window
    rows = asyncio.get_event_loop().run_until_complete(
        list_active_qualifications(db, qualification_type="COMPETENT_PERSON",
                                   warning_days=30)
    )
    warns = {r["employee_id"]: r["warning"] for r in rows}
    assert warns["e1"] is True
    assert warns["e2"] is True
    assert warns["e3"] is False


def test_resolve_active_for_employee_prefers_latest(db):
    from services.certifications.qualification_registry import (
        resolve_active_for_employee,
    )
    _mk_emp(db, "e1", "Alice")
    r_short = _mk_qual(db, "e1", expires_in=10)
    r_long = _mk_qual(db, "e1", expires_in=200)
    got = asyncio.get_event_loop().run_until_complete(
        resolve_active_for_employee(db, "e1", "COMPETENT_PERSON")
    )
    assert got is not None
    assert got["qualification_id"] == r_long["id"]


def test_resolve_active_returns_none_when_only_expired(db):
    from services.certifications.qualification_registry import (
        resolve_active_for_employee,
    )
    _mk_emp(db, "e1", "Alice")
    _mk_qual(db, "e1", status="expired", expires_in=-5)
    got = asyncio.get_event_loop().run_until_complete(
        resolve_active_for_employee(db, "e1", "COMPETENT_PERSON")
    )
    assert got is None


def test_identity_fields_from_normalizer(db):
    from services.certifications.qualification_registry import (
        list_active_qualifications,
    )
    _mk_emp(db, "e1", "Alice", trade="Foreman", crew="Concrete")
    _mk_qual(db, "e1")
    rows = asyncio.get_event_loop().run_until_complete(
        list_active_qualifications(db, qualification_type="COMPETENT_PERSON")
    )
    assert rows[0]["employee_trade"] == "Foreman"
    assert rows[0]["employee_crew"] == "Concrete"
    # display_identity comes from the shared normaliser
    assert rows[0]["employee_name"].startswith("Alice")


def test_snapshot_freezes_person_and_status(db):
    from services.certifications.qualification_registry import (
        get_qualification_snapshot,
    )
    _mk_emp(db, "e1", "Alice", trade="Signal Person")
    row = _mk_qual(db, "e1", expires_in=45)
    snap = asyncio.get_event_loop().run_until_complete(
        get_qualification_snapshot(db, row["id"])
    )
    assert snap["qualification_id"] == row["id"]
    assert snap["verification_status_at_selection"] == "active"
    assert snap["is_active_at_selection"] is True
    assert snap["person_trade_snapshot"] == "Signal Person"
    assert snap["expires_at_at_selection"] == row["expiration_date"]


def test_summary_bucket_counts(db):
    from services.certifications.qualification_registry import (
        qualification_summary,
    )
    _mk_emp(db, "e1", "A")
    _mk_qual(db, "e1", status="active", expires_in=100)
    _mk_qual(db, "e1", status="active", expires_in=-1)  # expired
    _mk_qual(db, "e1", status="suspended", suspended=True)
    _mk_qual(db, "e1", status="revoked", revoked=True)
    _mk_qual(db, "e1", status="pending")
    _mk_qual(db, "e1", status="active", expires_in=15)  # warning
    s = asyncio.get_event_loop().run_until_complete(
        qualification_summary(db, qualification_type="COMPETENT_PERSON")
    )
    assert s["active_count"] == 2
    assert s["expiring_within_count"] == 1
    assert s["expired_count"] == 1
    assert s["suspended_count"] == 1
    assert s["revoked_count"] == 1
    assert s["pending_count"] == 1


def test_type_metadata_validation():
    from services.certifications.qualification_types import (
        validate_type_metadata,
    )
    assert validate_type_metadata("CDL_ENDORSEMENT", {"sub_code": "H"}) is None
    assert validate_type_metadata("CDL_ENDORSEMENT", {}) is not None
    assert validate_type_metadata("MANUFACTURER_CERT",
                                  {"manufacturer": "Cat"}) is not None
    assert validate_type_metadata("MANUFACTURER_CERT",
                                  {"manufacturer": "Cat",
                                   "product_model": "D6"}) is None
    assert validate_type_metadata("COMPANY_SPECIFIC", {}) is not None
    assert validate_type_metadata("COMPANY_SPECIFIC",
                                  {"program_name": "MASCI-Ops"}) is None
    # Unknown type → error string.
    assert validate_type_metadata("HYPERDRIVE", {}) is not None
    # COMPETENT_PERSON has no required metadata — empty/None both ok.
    assert validate_type_metadata("COMPETENT_PERSON", None) is None


def test_is_engine_type():
    from services.certifications.qualification_types import is_engine_type
    assert is_engine_type("COMPETENT_PERSON") is True
    assert is_engine_type("OSHA_10") is True
    assert is_engine_type("UNKNOWN") is False
    assert is_engine_type(None) is False
    assert is_engine_type("") is False


def test_registry_filter_by_type(db):
    from services.certifications.qualification_registry import (
        list_active_qualifications,
    )
    _mk_emp(db, "e1", "A"); _mk_emp(db, "e2", "B")
    _mk_qual(db, "e1", qtype="COMPETENT_PERSON")
    _mk_qual(db, "e2", qtype="OSHA_10")
    cp = asyncio.get_event_loop().run_until_complete(
        list_active_qualifications(db, qualification_type="COMPETENT_PERSON")
    )
    osha = asyncio.get_event_loop().run_until_complete(
        list_active_qualifications(db, qualification_type="OSHA_10")
    )
    assert {r["employee_id"] for r in cp} == {"e1"}
    assert {r["employee_id"] for r in osha} == {"e2"}


def test_registry_never_leaks_pending_or_suspended(db):
    from services.certifications.qualification_registry import (
        list_active_qualifications,
    )
    _mk_emp(db, "e1", "A")
    _mk_qual(db, "e1", status="pending")
    _mk_qual(db, "e1", status="active", suspended=True)
    rows = asyncio.get_event_loop().run_until_complete(
        list_active_qualifications(db, qualification_type="COMPETENT_PERSON")
    )
    assert rows == []


def test_migration_is_idempotent(db):
    from scripts.migrate_track_23_10_b_qualification_engine import (
        run_migration,
    )
    _mk_emp(db, "e1", "Alice")
    _mk_qual(db, "e1", qtype="", cert_type_legacy="COMPETENT_PERSON",
             status="")  # legacy — no verification_status
    # Wipe the derived fields to simulate a truly-legacy row.
    row = db.safety_training_records.docs[0]
    row.pop("qualification_type", None)
    row.pop("verification_status", None)
    row.pop("verification_status_history", None)
    r1 = asyncio.get_event_loop().run_until_complete(
        run_migration(db, emit_facts=False)
    )
    r2 = asyncio.get_event_loop().run_until_complete(
        run_migration(db, emit_facts=False)
    )
    # Second run must NOT double-write history.
    row_after = db.safety_training_records.docs[0]
    assert row_after["verification_status"] in ("active", "expired")
    assert row_after["qualification_type"] == "COMPETENT_PERSON"
    assert len(row_after["verification_status_history"]) == 1
    assert r1["updated"] >= r2["updated"]


def test_migration_backfills_cp_designation(db):
    """Employees flagged competent_person_designated must materialise as
    a safety_training_records row after migration."""
    from scripts.migrate_track_23_10_b_qualification_engine import (
        run_migration,
    )
    db.employees.docs.append({
        "id": "e42", "name": "Legacy CP", "employee_id": "e42",
        "competent_person_designated": True,
        "cp_active": True,
        "cp_approval_date": "2026-01-01",
        "cp_expiration_date": "2027-01-01",
        "cp_approved_by": "admin",
        "is_active": True,
    })
    asyncio.get_event_loop().run_until_complete(
        run_migration(db, emit_facts=False)
    )
    rows = db.safety_training_records.docs
    matches = [r for r in rows
               if r.get("employee_id") == "e42"
               and (r.get("qualification_type") == "COMPETENT_PERSON"
                    or r.get("certification_type") == "COMPETENT_PERSON")]
    assert len(matches) == 1
    # Re-run — still one row (idempotent).
    asyncio.get_event_loop().run_until_complete(
        run_migration(db, emit_facts=False)
    )
    matches2 = [r for r in db.safety_training_records.docs
                if r.get("employee_id") == "e42"
                and r.get("qualification_type") == "COMPETENT_PERSON"]
    assert len(matches2) == 1


def test_expiration_fact_dedupes_daily(db):
    """`qualification_expiration_fact` is de-duped per (row, day)."""
    from services.certifications.qualification_facts import (
        emit_qualification_expiration_facts_daily,
    )
    _mk_emp(db, "e1", "A")
    _mk_qual(db, "e1", expires_in=15)
    asyncio.get_event_loop().run_until_complete(
        emit_qualification_expiration_facts_daily(db)
    )
    # Second run same day — old fact superseded, new emitted.
    asyncio.get_event_loop().run_until_complete(
        emit_qualification_expiration_facts_daily(db)
    )
    current = [f for f in db.operational_facts.docs
               if f.get("fact_type") == "qualification_expiration_fact"
               and f.get("is_current") is True]
    assert len(current) == 1


def test_certification_fact_idempotent_on_repeat(db):
    """Emitting the certification fact twice keeps only one current row."""
    from services.certifications.qualification_facts import (
        emit_qualification_certification_fact,
    )
    _mk_emp(db, "e1", "A")
    row = _mk_qual(db, "e1")
    asyncio.get_event_loop().run_until_complete(
        emit_qualification_certification_fact(db, row)
    )
    asyncio.get_event_loop().run_until_complete(
        emit_qualification_certification_fact(db, row)
    )
    current = [f for f in db.operational_facts.docs
               if f.get("fact_type") == "qualification_certification_fact"
               and f.get("is_current") is True]
    assert len(current) == 1


def test_certification_fact_skips_non_engine_types(db):
    from services.certifications.qualification_facts import (
        emit_qualification_certification_fact,
    )
    _mk_emp(db, "e1", "A")
    row = _mk_qual(db, "e1", qtype="ANNUAL_TRUCK_SAFETY",
                   cert_type_legacy="ANNUAL_TRUCK_SAFETY")
    fid = asyncio.get_event_loop().run_until_complete(
        emit_qualification_certification_fact(db, row)
    )
    assert fid is None
    facts = db.operational_facts.docs
    assert not facts


def test_employee_list_returns_all_statuses(db):
    """Employee Lifecycle Qualifications tab requires ALL rows for the
    employee — active + expired + suspended + revoked + pending."""
    from services.certifications.qualification_registry import (
        list_employee_qualifications,
    )
    _mk_emp(db, "e1", "A")
    _mk_qual(db, "e1", status="active")
    _mk_qual(db, "e1", status="expired", expires_in=-1)
    _mk_qual(db, "e1", status="suspended", suspended=True)
    rows = asyncio.get_event_loop().run_until_complete(
        list_employee_qualifications(db, employee_id="e1")
    )
    statuses = sorted(r["verification_status"] for r in rows)
    assert statuses == ["active", "expired", "suspended"]
    for r in rows:
        assert "is_active" in r


def test_snapshot_of_missing_qualification_returns_none(db):
    from services.certifications.qualification_registry import (
        get_qualification_snapshot,
    )
    got = asyncio.get_event_loop().run_until_complete(
        get_qualification_snapshot(db, "nope")
    )
    assert got is None


# =====================================================================
# 3) HTTP surface lock tests (route-shape).
# =====================================================================

def test_router_declares_all_required_routes():
    """The router builder must declare the full 23.10-B contract."""
    from routes.qualifications import build_qualifications_router
    r = build_qualifications_router(None, lambda: None, lambda: None)
    paths = {(tuple(sorted(route.methods)), route.path) for route in r.routes}
    required = {
        (("GET",), "/api/employees/qualifications/types"),
        (("GET",), "/api/employees/qualifications"),
        (("GET",), "/api/employees/competent-persons"),
        (("GET",), "/api/employees/qualifications/summary"),
        (("GET",), "/api/employees/{employee_id}/qualifications"),
        (("GET",), "/api/hr/qualifications/{qualification_id}/snapshot"),
        (("POST",), "/api/hr/qualifications"),
        (("PATCH",), "/api/hr/qualifications/{qid}"),
        (("POST",), "/api/hr/qualifications/{qid}/suspend"),
        (("POST",), "/api/hr/qualifications/{qid}/revoke"),
        (("POST",), "/api/hr/qualifications/{qid}/reinstate"),
        (("POST",), "/api/hr/qualifications/{qid}/renew"),
    }
    missing = required - paths
    assert not missing, f"missing routes: {missing}"


def test_no_new_collections_created():
    """23.10-B ships zero new collections. Verified by grep — the
    engine references only `safety_training_records`, `employees`,
    `operational_facts`, `hr_audit`, and `operational_ingestion_runs`.
    """
    src = _r(BACKEND / "routes" / "qualifications.py") + \
          _r(BACKEND / "services" / "certifications" / "qualification_registry.py") + \
          _r(BACKEND / "services" / "certifications" / "qualification_facts.py")
    banned = re.compile(
        r"db\.(competent_persons|qualifications_registry|"
        r"employee_certifications|competent_person_registry)",
    )
    m = banned.search(src)
    assert m is None, f"forbidden collection reference: {m.group(0)}"


def test_no_provisional_picker_in_23_10_b():
    """23.10-B does NOT ship any picker component. The permanent
    picker `CompetentPersonCombo` is shipped by Track 23.10-E in
    `frontend/src/components/daily-report-v3/` — that path is
    whitelisted here."""
    front = BACKEND.parent / "frontend" / "src"
    picker_names = ("CompetentPersonCombo", "CompetentPersonPicker",
                    "QualificationPicker")
    hits = []
    if front.exists():
        for p in front.rglob("*.jsx"):
            # Track 23.10-E ships the CompetentPersonCombo under
            # `components/daily-report-v3/`. Anything else = violation.
            if "daily-report-v3" in p.as_posix():
                continue
            txt = p.read_text(encoding="utf-8", errors="ignore")
            for name in picker_names:
                if f"function {name}" in txt or f"const {name} =" in txt or f"export {name}" in txt.replace(" default ", " "):
                    hits.append((p.name, name))
    assert not hits, f"provisional picker exists outside 23.10-E scope: {hits}"
