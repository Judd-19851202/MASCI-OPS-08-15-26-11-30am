"""TRACK 27.00 · HR Filter Trust — regression tests."""
from __future__ import annotations

import asyncio
import os
import uuid
from typing import Any, Dict, List, Optional

import httpx
import pytest
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from lib.employee_status import (  # noqa: E402
    BUCKET_STATUSES, bucket_of, mongo_clause_for_bucket,
    status_belongs_to_bucket, validate_bucket,
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


def _seed_docs(tag: str) -> List[Dict[str, Any]]:
    return [
        {"id": f"{tag}-a1", "name": f"{tag} Active One",       "lifecycle_status": "Active",           "is_active": True,  "trade": "Driver",   "crew": "Paving",   "supervisor": "Jason",       "deleted_at": None},
        {"id": f"{tag}-a2", "name": f"{tag} Active Two",       "lifecycle_status": "Seasonal",         "is_active": True,  "trade": "Operator", "crew": "Paving",   "supervisor": "Jason",       "deleted_at": None},
        {"id": f"{tag}-a3", "name": f"{tag} On Leave",         "lifecycle_status": "Leave of Absence", "is_active": True,  "trade": "Driver",   "crew": "Utility",  "supervisor": "David",       "deleted_at": None},
        {"id": f"{tag}-a4", "name": f"{tag} Legacy Active",                                            "is_active": True,  "trade": "Operator", "crew": "",         "supervisor": "",            "deleted_at": None},
        {"id": f"{tag}-p1", "name": f"{tag} Pending One",      "lifecycle_status": "Pending Hire",     "is_active": True,  "trade": "Driver",   "crew": "Paving",   "supervisor": "Jason",       "deleted_at": None},
        {"id": f"{tag}-o1", "name": f"{tag} Off One",          "lifecycle_status": "Inactive",         "is_active": False, "trade": "Driver",   "crew": "Paving",   "supervisor": "Jason",       "deleted_at": None},
        {"id": f"{tag}-o2", "name": f"{tag} Suspended",        "lifecycle_status": "Suspended",        "is_active": False, "trade": "Operator", "crew": "Shop",     "supervisor": None,          "deleted_at": None},
        {"id": f"{tag}-o3", "name": f"{tag} Legacy Inactive",                                          "is_active": False, "trade": "Driver",   "crew": None,       "supervisor": None,          "deleted_at": None},
        {"id": f"{tag}-t1", "name": f"{tag} Terminated One",   "lifecycle_status": "Terminated",       "is_active": False, "trade": "Driver",   "crew": "Paving",   "supervisor": "Jason",       "deleted_at": None},
        {"id": f"{tag}-t2", "name": f"{tag} Resigned",         "lifecycle_status": "Resigned",         "is_active": False, "trade": "Operator", "crew": "Paving",   "supervisor": "David",       "deleted_at": None},
        {"id": f"{tag}-r1", "name": f"{tag} Retired One",      "lifecycle_status": "Retired",          "is_active": False, "trade": "Foreman",  "crew": "Concrete", "supervisor": "David",       "deleted_at": None},
        {"id": f"{tag}-d1", "name": f"{tag} Deleted",          "lifecycle_status": "Active",           "is_active": True,  "trade": "Driver",   "crew": "Paving",   "supervisor": "Jason",       "deleted_at": "2026-01-01T00:00:00Z"},
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
        db = client[os.environ["DB_NAME"]]
        await db.employees.insert_many(_seed_docs(tag))
    finally:
        client.close()


async def _cleanup_async(tag: str) -> None:
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    try:
        db = client[os.environ["DB_NAME"]]
        await db.employees.delete_many({"id": {"$regex": f"^{tag}-"}})
    finally:
        client.close()


async def _fetch_ids_async(clause: Optional[Dict[str, Any]], tag: str) -> List[str]:
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    try:
        db = client[os.environ["DB_NAME"]]
        q = {"deleted_at": None, "id": {"$regex": f"^{tag}-"}}
        if clause:
            q.update(clause)
        return sorted([d["id"] async for d in db.employees.find(q, {"_id": 0, "id": 1})])
    finally:
        client.close()


async def _hr_call_async(path: str, params: Dict[str, Any]) -> Dict[str, Any]:
    tok = await _admin_token_async()
    async with httpx.AsyncClient(timeout=30) as ac:
        r = await ac.get(f"{BASE}{path}", params=params,
                         headers={"X-Admin-Token": tok})
        r.raise_for_status()
        return r.json()


@pytest.fixture(scope="module")
def tag():
    """Seed once per module, cleanup once at end. Session-level scope
    avoids the per-test motor-client / event-loop churn that made the
    old per-test teardown flaky."""
    t = f"trk27-{uuid.uuid4().hex[:8]}"
    # Belt-and-suspenders: purge any orphans from previous failed runs
    # (defensive — should already be empty).
    asyncio.run(_cleanup_async("trk27"))
    asyncio.run(_seed_async(t))
    yield t
    asyncio.run(_cleanup_async(t))


def _run(coro):
    return asyncio.run(coro)


# ── Unit tests on the canonical bucket module ────────────────────────
def test_bucket_of_maps_every_canonical_status():
    """T-1 · Every status maps back to its own bucket."""
    for bucket, statuses in BUCKET_STATUSES.items():
        for s in statuses:
            assert bucket_of({"lifecycle_status": s}) == bucket, s


def test_bucket_of_legacy_row_shapes():
    """T-2 · Legacy rows resolve via is_active."""
    assert bucket_of({"is_active": True}) == "active"
    assert bucket_of({"is_active": False}) == "off_roll"
    assert bucket_of({"is_active": None}) == "active"
    assert bucket_of({}) == "active"


def test_status_belongs_to_bucket_guards_impossible_pairs():
    """T-3 · Impossible bucket + status pairs must be catchable."""
    assert status_belongs_to_bucket("Terminated", "active") is False
    assert status_belongs_to_bucket("Retired", "terminated") is False
    assert status_belongs_to_bucket("Retired", "retired") is True
    assert status_belongs_to_bucket("Active", "active") is True


def test_validate_bucket_rejects_junk():
    """T-4 · API fails loudly on bogus bucket values."""
    assert validate_bucket(None) == "any"
    assert validate_bucket("") == "any"
    assert validate_bucket("active") == "active"
    with pytest.raises(ValueError):
        validate_bucket("garbage")


# ── Integration tests against real Mongo ─────────────────────────────
def test_active_bucket_matches_kpi_definition(tag):
    ids = _run(_fetch_ids_async(mongo_clause_for_bucket("active"), tag))
    assert ids == sorted([f"{tag}-a1", f"{tag}-a2", f"{tag}-a3", f"{tag}-a4"])


def test_terminated_bucket_returns_terminated_and_resigned(tag):
    ids = _run(_fetch_ids_async(mongo_clause_for_bucket("terminated"), tag))
    assert ids == sorted([f"{tag}-t1", f"{tag}-t2"])


def test_retired_bucket_is_first_class(tag):
    ids = _run(_fetch_ids_async(mongo_clause_for_bucket("retired"), tag))
    assert ids == [f"{tag}-r1"]


def test_retired_excluded_from_active(tag):
    ids = _run(_fetch_ids_async(mongo_clause_for_bucket("active"), tag))
    assert f"{tag}-r1" not in ids


def test_pending_hire_not_in_active_bucket(tag):
    active_ids = _run(_fetch_ids_async(mongo_clause_for_bucket("active"), tag))
    pending_ids = _run(_fetch_ids_async(mongo_clause_for_bucket("pending"), tag))
    assert f"{tag}-p1" not in active_ids
    assert pending_ids == [f"{tag}-p1"]


def test_off_roll_includes_suspended_and_legacy_inactive(tag):
    ids = _run(_fetch_ids_async(mongo_clause_for_bucket("off_roll"), tag))
    assert ids == sorted([f"{tag}-o1", f"{tag}-o2", f"{tag}-o3"])


def test_soft_deleted_never_appears(tag):
    for bucket in ["active", "pending", "off_roll", "terminated", "retired"]:
        ids = _run(_fetch_ids_async(mongo_clause_for_bucket(bucket), tag))
        assert f"{tag}-d1" not in ids, f"deleted row leaked into {bucket}"


# ── End-to-end HTTP tests ────────────────────────────────────────────
def test_endpoint_bucket_active_returns_only_active_bucket_rows(tag):
    body = _run(_hr_call_async("/hr/employees", {"bucket": "active", "q": tag, "limit": 100}))
    for item in body["items"]:
        assert bucket_of(item) == "active", item.get("lifecycle_status")
    ids = {i["id"] for i in body["items"]}
    assert {f"{tag}-a1", f"{tag}-a2", f"{tag}-a3", f"{tag}-a4"}.issubset(ids)
    assert not (ids & {f"{tag}-p1", f"{tag}-t1", f"{tag}-r1"})


def test_endpoint_impossible_intersection_reports_warning(tag):
    body = _run(_hr_call_async("/hr/employees", {
        "bucket": "active", "lifecycle_status": "Terminated", "q": tag,
    }))
    assert body["count"] == 0
    assert body["items"] == []
    assert body.get("warning", {}).get("code") == "impossible_intersection"


def test_endpoint_retired_visible_only_via_retired_filter(tag):
    active = _run(_hr_call_async("/hr/employees", {"bucket": "active", "q": tag}))
    retired = _run(_hr_call_async("/hr/employees", {"bucket": "retired", "q": tag}))
    assert f"{tag}-r1" in {i["id"] for i in retired["items"]}
    assert f"{tag}-r1" not in {i["id"] for i in active["items"]}


def test_endpoint_crew_and_supervisor_filters_compose(tag):
    body = _run(_hr_call_async("/hr/employees", {
        "bucket": "active", "crew": "Paving", "supervisor": "Jason", "q": tag,
    }))
    for item in body["items"]:
        assert item.get("crew") == "Paving"
        assert item.get("supervisor") == "Jason"


def test_endpoint_search_matches_name_field(tag):
    body = _run(_hr_call_async("/hr/employees", {
        "bucket": "any", "q": f"{tag} Active One",
    }))
    assert f"{tag}-a1" in {i["id"] for i in body["items"]}


def test_endpoint_unassigned_supervisor_filter(tag):
    body = _run(_hr_call_async("/hr/employees", {
        "bucket": "any", "supervisor": "(unassigned)", "q": tag,
    }))
    ids = {i["id"] for i in body["items"]}
    assert f"{tag}-a4" in ids
    assert f"{tag}-o2" in ids
    assert f"{tag}-o3" in ids
    assert f"{tag}-a1" not in ids


def test_endpoint_missing_supervisor_view_excludes_inactive(tag):
    body = _run(_hr_call_async("/hr/employees", {
        "bucket": "active", "supervisor": "(unassigned)", "q": tag,
    }))
    ids = {i["id"] for i in body["items"]}
    assert f"{tag}-r1" not in ids
    assert f"{tag}-t1" not in ids
    assert f"{tag}-o1" not in ids


def test_endpoint_facets_contain_retired_bucket_and_dynamic_values():
    payload = _run(_hr_call_async("/hr/employees/facets", {}))
    bucket_values = {b["value"] for b in payload["buckets"]}
    assert {"active", "pending", "off_roll", "terminated", "retired"}.issubset(bucket_values)
    assert isinstance(payload["crews"], list)
    assert isinstance(payload["supervisors"], list)
    assert isinstance(payload["trades"], list)


def test_endpoint_export_status_ok_with_bucket(tag):
    async def go():
        tok = await _admin_token_async()
        async with httpx.AsyncClient(timeout=30) as ac:
            return await ac.get(f"{BASE}/hr/employees/export.xlsx",
                                params={"bucket": "retired", "q": tag},
                                headers={"X-Admin-Token": tok})
    r = _run(go())
    assert r.status_code == 200
    assert r.headers["content-type"].startswith(
        "application/vnd.openxmlformats"
    )


# ── Backfill idempotency & non-overwrite (Phase A) ───────────────────
def test_backfill_is_idempotent():
    """T-21 · Running the backfill twice against non-test data must
    be a noop. The seeded fixture data (which intentionally includes
    a row without lifecycle_status to prove legacy-row handling)
    is excluded from this assertion."""
    async def go():
        from scripts.track_27_backfill_lifecycle_status import dry_run as backfill_dry
        client = AsyncIOMotorClient(os.environ["MONGO_URL"])
        try:
            db = client[os.environ["DB_NAME"]]
            dry = await backfill_dry(db)
            # Non-test rows should be fully backfilled (Phase A done).
            # Filter out any synthetic seed rows this suite created.
            real_active = [
                r for r in dry["sample_active"] if not str(r.get("id", "")).startswith("trk")
            ]
            real_inactive = [
                r for r in dry["sample_inactive"] if not str(r.get("id", "")).startswith("trk")
            ]
            assert not real_active, real_active
            assert not real_inactive, real_inactive
        finally:
            client.close()
    _run(go())


def test_backfill_never_overwrites_existing_status():
    async def go():
        from scripts.track_27_backfill_lifecycle_status import apply as backfill_apply
        client = AsyncIOMotorClient(os.environ["MONGO_URL"])
        try:
            db = client[os.environ["DB_NAME"]]
            canary_id = f"trk27-canary-{uuid.uuid4().hex[:6]}"
            await db.employees.insert_one({
                "id": canary_id, "name": "Canary",
                "lifecycle_status": "Terminated",
                "is_active": False, "deleted_at": None,
            })
            try:
                await backfill_apply(db)
                row = await db.employees.find_one(
                    {"id": canary_id}, {"_id": 0, "lifecycle_status": 1},
                )
                assert row["lifecycle_status"] == "Terminated"
            finally:
                await db.employees.delete_one({"id": canary_id})
        finally:
            client.close()
    _run(go())
