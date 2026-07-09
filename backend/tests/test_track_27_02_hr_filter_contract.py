"""TRACK 27.02 · HR Filter Contract Completion — regression tests.

Defends the Track 27.02 fixes against the two prod bugs:

  Bug 1: Detailed Status = Active returned only rows with the exact
         `lifecycle_status: "Active"` string, missing legacy rows
         that resolve to Active via `is_active`. Bucket = Active
         returned all of them (canonical path), so KPI = 236 but
         Detailed Status = Active dropdown filter = 27.

  Bug 2: Supervisor facet grouped by raw stored value with no
         normalization. Different case / whitespace variants
         produced misleading facet counts that didn't match what a
         strict-match query returned. E.g. facet showed
         "LENNY WITKOWSKI · 3" but selecting returned 0.

  Bug 3 (caught during this fix): Detailed Status = Terminated with
         no bucket param stacked the active-umbrella AND the exact
         status, producing an empty $and. Silent mystery-zero.
"""
from __future__ import annotations

import asyncio
import os
import uuid
from typing import Any, Dict, List

import httpx
import pytest
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from lib.employee_status import (  # noqa: E402
    mongo_clause_for_status, mongo_clause_for_facet,
    normalize_facet_value, is_unassigned_sentinel,
)


def _api_base() -> str:
    v = os.environ.get("REACT_APP_BACKEND_URL")
    if not v:
        for line in open("/app/frontend/.env"):
            if line.startswith("REACT_APP_BACKEND_URL="):
                v = line.strip().split("=", 1)[1]
                break
    return v.rstrip("/") + "/api"


BASE = _api_base()


# ── Prod-shaped dirty seed (fires both bugs) ──────────────────────────
def _seed_docs(tag: str) -> List[Dict[str, Any]]:
    return [
        # Three legacy rows without lifecycle_status — Bug 1 mechanism.
        {"id": f"{tag}-lg1", "name": f"{tag} Legacy One",   "is_active": True,                                          "trade": "Driver",   "crew": "Paving",   "supervisor": "  LENNY WITKOWSKI  ",  "deleted_at": None},
        {"id": f"{tag}-lg2", "name": f"{tag} Legacy Two",   "is_active": True,                                          "trade": "Operator", "crew": "Paving",   "supervisor": "lenny witkowski",       "deleted_at": None},
        {"id": f"{tag}-lg3", "name": f"{tag} Legacy Three", "is_active": True,                                          "trade": "Driver",   "crew": "Paving",   "supervisor": "Lenny Witkowski",       "deleted_at": None},
        # Modern active row with dirty crew/supervisor — Bug 2 mechanism.
        {"id": f"{tag}-a1",  "name": f"{tag} Active Ana",   "lifecycle_status": "Active",           "is_active": True,  "trade": "Driver",   "crew": "  Paving  ", "supervisor": "Lenny  Witkowski",     "deleted_at": None},
        # Cross-bucket rows.
        {"id": f"{tag}-t1",  "name": f"{tag} Terminated",   "lifecycle_status": "Terminated",       "is_active": False, "trade": "Driver",   "crew": "Paving",   "supervisor": "LENNY WITKOWSKI",       "deleted_at": None},
        {"id": f"{tag}-r1",  "name": f"{tag} Retired",      "lifecycle_status": "Retired",          "is_active": False, "trade": "Foreman",  "crew": "Concrete", "supervisor": "David Puma",             "deleted_at": None},
        {"id": f"{tag}-p1",  "name": f"{tag} Pending",      "lifecycle_status": "Pending Hire",     "is_active": True,  "trade": "Operator", "crew": "Paving",   "supervisor": "Lenny Witkowski",       "deleted_at": None},
    ]


async def _admin_token_async() -> str:
    async with httpx.AsyncClient(timeout=30) as ac:
        r = await ac.post(f"{BASE}/auth/multi-login", json={
            "email": "jaymn.judd@mascigc.com", "password": "Maddix123!",
        })
        r.raise_for_status()
        return r.json()["portal_tokens"]["admin"]


async def _seed_async(tag: str) -> None:
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    try:
        await client[os.environ["DB_NAME"]].employees.insert_many(_seed_docs(tag))
    finally:
        client.close()


async def _cleanup_async(tag: str) -> None:
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    try:
        await client[os.environ["DB_NAME"]].employees.delete_many({"id": {"$regex": f"^{tag}-"}})
    finally:
        client.close()


async def _hr_call_async(**params: Any) -> Dict[str, Any]:
    tok = await _admin_token_async()
    params.setdefault("limit", 100)
    async with httpx.AsyncClient(timeout=30) as ac:
        r = await ac.get(f"{BASE}/hr/employees", params=params,
                         headers={"X-Admin-Token": tok})
        r.raise_for_status()
        return r.json()


def _run(coro):
    return asyncio.run(coro)


@pytest.fixture(scope="module")
def tag():
    t = f"trk2702-{uuid.uuid4().hex[:8]}"
    asyncio.run(_cleanup_async("trk2702"))     # purge orphans
    asyncio.run(_seed_async(t))
    yield t
    asyncio.run(_cleanup_async(t))


# ── Unit tests on the canonical resolvers ────────────────────────────
def test_normalize_facet_value_handles_dirty_input():
    """T-27.02-U1 · normalize_facet_value trims + collapses whitespace,
    preserves case."""
    assert normalize_facet_value("  Lenny  Witkowski  ") == "Lenny Witkowski"
    assert normalize_facet_value("LENNY WITKOWSKI") == "LENNY WITKOWSKI"
    assert normalize_facet_value("") is None
    assert normalize_facet_value("   ") is None
    assert normalize_facet_value(None) is None
    assert normalize_facet_value("Lenny\tWitkowski") == "Lenny Witkowski"


def test_is_unassigned_sentinel():
    """T-27.02-U2 · Sentinel detection."""
    assert is_unassigned_sentinel("(unassigned)") is True
    assert is_unassigned_sentinel("Lenny") is False
    assert is_unassigned_sentinel(None) is False


def test_mongo_clause_for_facet_matches_case_insensitive_and_trim():
    """T-27.02-U3 · The facet clause must be a case-insensitive regex
    anchored with whitespace slop so 'Lenny Witkowski' matches
    ' LENNY WITKOWSKI '."""
    clause = mongo_clause_for_facet("supervisor", "Lenny Witkowski")
    regex_spec = clause["supervisor"]
    assert regex_spec["$options"] == "i"
    # Pattern should have leading + trailing \s* and \s+ for spaces.
    assert regex_spec["$regex"].startswith(r"^\s*")
    assert regex_spec["$regex"].endswith(r"\s*$")


def test_mongo_clause_for_status_includes_legacy_for_active():
    """T-27.02-U4 · Detailed Status = Active must OR in legacy rows
    with no lifecycle_status. Bug 1 root cause."""
    clause = mongo_clause_for_status("Active")
    branches = clause["$or"]
    assert {"lifecycle_status": "Active"} in branches
    # At least one legacy branch matching missing-field-with-truthy-is_active.
    assert any(b.get("lifecycle_status") is None and b.get("is_active") == {"$ne": False}
               for b in branches)


def test_mongo_clause_for_status_strict_for_terminated():
    """T-27.02-U5 · Detailed Status = Terminated must be strict (no
    legacy row has ever displayed as Terminated). Confirms the
    canonical resolver does the right thing at both ends of the
    spectrum."""
    clause = mongo_clause_for_status("Terminated")
    branches = clause["$or"]
    assert branches == [{"lifecycle_status": "Terminated"}]


# ── Integration tests through the live HTTP endpoint ─────────────────
def test_detailed_status_active_returns_all_active_including_legacy(tag):
    """T-27.02-I1 · The prod bug: Detailed Status = Active must
    include the 3 legacy rows + the 1 modern-Active row = 4 total.
    Before the fix this returned 1 (only the modern row)."""
    body = _run(_hr_call_async(q=tag, **{"lifecycle_status": "Active"}))
    assert body["count"] == 4, body


def test_detailed_status_terminated_returns_terminated_no_umbrella(tag):
    """T-27.02-I2 · Bug 3 caught during fix: Detailed Status = Terminated
    with no bucket must NOT stack the active umbrella. Before the fix
    this returned 0."""
    body = _run(_hr_call_async(q=tag, **{"lifecycle_status": "Terminated"}))
    assert body["count"] == 1


def test_detailed_status_retired_no_bucket(tag):
    """T-27.02-I3 · Same defense for Retired."""
    body = _run(_hr_call_async(q=tag, **{"lifecycle_status": "Retired"}))
    assert body["count"] == 1


def test_supervisor_facet_normalization_matches_dirty_data(tag):
    """T-27.02-I4 · Prod bug: LENNY WITKOWSKI · 3 → 0. Now: selecting
    "Lenny Witkowski" (any case) must match ALL variants across the
    seeded rows (6 rows total)."""
    for query_value in ("Lenny Witkowski", "LENNY WITKOWSKI",
                        "  lenny witkowski  ", "lenny  witkowski"):
        body = _run(_hr_call_async(q=tag, bucket="any", supervisor=query_value))
        assert body["count"] == 6, f"variant {query_value!r}: {body}"


def test_crew_facet_normalization_matches_dirty_data(tag):
    """T-27.02-I5 · Crew=Paving with whitespace variants."""
    for query_value in ("Paving", "  Paving  ", "PAVING"):
        body = _run(_hr_call_async(q=tag, bucket="any", crew=query_value))
        assert body["count"] == 6, f"variant {query_value!r}: {body}"


def test_bucket_active_and_supervisor_narrow_correctly(tag):
    """T-27.02-I6 · Combination: Active + Supervisor=Lenny must
    return the 4 active-bucket rows even with dirty casings."""
    body = _run(_hr_call_async(q=tag, bucket="active", supervisor="Lenny Witkowski"))
    assert body["count"] == 4


def test_bucket_terminated_and_supervisor_narrow_correctly(tag):
    """T-27.02-I7 · Terminated + Supervisor=Lenny narrows to 1."""
    body = _run(_hr_call_async(q=tag, bucket="terminated", supervisor="Lenny Witkowski"))
    assert body["count"] == 1


def test_full_intersection_active_crew_supervisor_trade(tag):
    """T-27.02-I8 · Active + Crew=Paving + Supervisor=Lenny + Trade=Driver."""
    body = _run(_hr_call_async(
        q=tag, bucket="active", crew="Paving",
        supervisor="Lenny Witkowski", trade="Driver",
    ))
    # Legacy One (Driver+Paving+Lenny variants) +
    # Legacy Three (Driver+Paving+Lenny) +
    # Active Ana (Driver+Paving+Lenny variant) = 3.
    assert body["count"] == 3


def test_missing_supervisor_view_excludes_our_rows(tag):
    """T-27.02-I9 · Missing Supervisor + Active view: none of our
    seeded active rows lack a supervisor, so returns 0."""
    body = _run(_hr_call_async(q=tag, bucket="active", supervisor="(unassigned)"))
    assert body["count"] == 0


def test_impossible_intersection_still_warns(tag):
    """T-27.02-I10 · Regression guard: bucket=active + status=Terminated
    still returns 0 with the warning code, not a silent zero."""
    body = _run(_hr_call_async(q=tag, bucket="active", **{"lifecycle_status": "Terminated"}))
    assert body["count"] == 0
    assert body["items"] == []
    assert body.get("warning", {}).get("code") == "impossible_intersection"


def test_export_bucket_active_returns_ok(tag):
    """T-27.02-I11 · Export .xlsx accepts bucket param and returns 200."""
    async def go():
        tok = await _admin_token_async()
        async with httpx.AsyncClient(timeout=30) as ac:
            return await ac.get(f"{BASE}/hr/employees/export.xlsx",
                                params={"bucket": "active", "q": tag},
                                headers={"X-Admin-Token": tok})
    r = _run(go())
    assert r.status_code == 200


def test_facet_endpoint_deduplicates_case_and_whitespace_variants(tag):
    """T-27.02-I12 · The facet endpoint must return ONE entry for
    "Lenny Witkowski" regardless of casing/whitespace variants in
    the DB. Count for that entry must include every variant row."""
    async def go():
        tok = await _admin_token_async()
        async with httpx.AsyncClient(timeout=30) as ac:
            return (await ac.get(f"{BASE}/hr/employees/facets",
                                 headers={"X-Admin-Token": tok})).json()
    payload = _run(go())
    lenny_entries = [
        s for s in payload["supervisors"]
        if "lenny" in s["label"].lower() and "witkowski" in s["label"].lower()
    ]
    # Exactly one entry for Lenny Witkowski (all variants collapsed).
    assert len(lenny_entries) == 1, [e["label"] for e in lenny_entries]
    # The entry's count must be ≥ 6 (our 6 seeded Lenny rows; may
    # include real-world Lenny rows if the DB has any, that's fine).
    assert lenny_entries[0]["count"] >= 6
