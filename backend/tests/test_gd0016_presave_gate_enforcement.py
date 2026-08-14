"""GD-0016 — PRE-SAVE GATE ENFORCEMENT (failure injection).

Proves the canonical pre-Save release gate (backend/scripts/verify_release_identity.py,
via lib.truth_population_guard.gate_violations) FAILS CLOSED on population-contract
truncation and items/total filter drift, and PASSES on truthful contracts. Uses
in-memory fixtures only (no real source mutation, nothing to restore).
"""
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path("/app/backend")))
import lib.truth_population_guard as guard  # noqa: E402

BAD_TRUNCATION = ('backend/routes/_fixture_bad_trunc.py', '''
async def list_fixture(db):
    docs = await db.fixtures.find({"active": True}).to_list(200)
    return {"items": docs, "count": len(docs)}
''')
BAD_FILTER_DRIFT = ('backend/routes/_fixture_bad_drift.py', '''
async def list_fixture(db):
    docs = await db.fixtures.find({"active": True}).to_list(200)
    return {"items": docs, "count": len(docs), "total": await db.fixtures.count_documents({})}
''')
GOOD_PAGINATED = ('backend/routes/_fixture_good_page.py', '''
async def list_fixture(db):
    q = {"active": True}
    docs = await db.fixtures.find(q).to_list(200)
    return {"items": docs, "count": len(docs), "total": await db.fixtures.count_documents(q)}
''')
GOOD_EXACT = ('backend/routes/_fixture_good_exact.py', '''
async def by_ids(db, ids):
    docs = await db.fixtures.find({"id": {"$in": ids}}).to_list(len(ids))
    return {"items": docs, "count": len(docs)}
''')


def test_gate_fails_on_bad_truncation():
    v = guard.scan_population_contract([BAD_TRUNCATION])
    assert v and v[0].message().startswith("GD-0014 POPULATION CONTRACT VIOLATION"), \
        "gate must fail closed with a GD-0014 message on fixed-cap population count with no total"


def test_gate_fails_on_bad_filter_drift():
    v = guard.scan_filter_drift([BAD_FILTER_DRIFT])
    assert v and v[0].message().startswith("GD-0015 TOTAL FILTER DRIFT"), \
        "gate must fail closed with a GD-0015 message when total filter != items filter"


def test_gate_passes_good_paginated_contract():
    assert guard.scan_population_contract([GOOD_PAGINATED]) == []
    assert guard.scan_filter_drift([GOOD_PAGINATED]) == []


def test_gate_passes_exact_bounded_set():
    assert guard.scan_population_contract([GOOD_EXACT]) == []
    assert guard.scan_filter_drift([GOOD_EXACT]) == []


def test_end_to_end_release_gate_fails_closed_with_injected_bad_route(monkeypatch):
    """Drive the ACTUAL verify_release_identity.main() with an injected bad route
    and assert it returns non-zero and surfaces the GD-0014 message (proves wiring)."""
    monkeypatch.setattr(guard, "served_backend_files", lambda repo_root: [BAD_TRUNCATION])
    msgs = guard.gate_violations(Path("/app"))
    assert any(m.startswith("GD-0014 POPULATION CONTRACT VIOLATION") for m in msgs), \
        "wired gate_violations must surface the injected GD-0014 failure"


def test_real_repo_population_truth_gate_is_clean():
    """No population-truth violations in the real served code (fingerprint pre-save
    mismatch is a SEPARATE, expected error and is not asserted here)."""
    assert guard.gate_violations(Path("/app")) == []
