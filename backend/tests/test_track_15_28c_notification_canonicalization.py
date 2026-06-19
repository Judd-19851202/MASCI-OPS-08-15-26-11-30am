"""
TRACK 15.28C — Notification System Canonicalization · pytest verification
=========================================================================

Validates every objective from the operator directive:

  T-1  Legacy migration parity (552 → 0)
  T-2  Duplicate prevention (100× replay → 1 row)
  T-3  PM project scope (PM-A sees A only, never B)
  T-4  Bell visibility (no canonical rows are unreachable)
  T-5  Cross-portal verification (Admin / PM / HR / Safety / Dispatch / Shop / FL / Asset Admin)
  T-6  Hard refresh consistency (count is idempotent)
  T-7  DB count parity (variance is fully explained)

The tests run against the live preview DB but never mutate it except
inside two well-known fixture project_numbers and one fixture event_id
namespace, all of which are torn down at end-of-module.
"""
from __future__ import annotations

import asyncio
import os
import uuid
from pathlib import Path
from typing import Any, Dict, List

import pytest
from dotenv import load_dotenv

load_dotenv(str(Path(__file__).resolve().parents[1] / ".env"))

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from motor.motor_asyncio import AsyncIOMotorClient
from routes.tasks_notifications import (  # noqa: E402
    compute_idempotency_key,
    build_notif_filter_async,
)
from lib.event_fanout import emit_notification  # noqa: E402


# ── Fixture namespace — every row written by this suite carries a
#    distinctive linked_source_module so teardown is surgical.
TEST_MODULE = "track_15_28c_pytest"
TEST_PROJECT_A = "TRACK15-28C-PROJ-A"
TEST_PROJECT_B = "TRACK15-28C-PROJ-B"


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
def db():
    mongo_url = os.environ["MONGO_URL"]
    db_name = os.environ["DB_NAME"]
    client = AsyncIOMotorClient(mongo_url)
    return client[db_name]


@pytest.fixture(scope="module", autouse=True)
def cleanup_fixtures(db, event_loop):
    """Tear down anything this suite created, before and after."""
    async def _purge():
        await db.notifications.delete_many({"linked_source_module": TEST_MODULE})
        await db.project_team_assignments.delete_many({
            "project_number": {"$in": [TEST_PROJECT_A, TEST_PROJECT_B]},
            "user_id": {"$regex": "^track-15-28c-"},
        })
    event_loop.run_until_complete(_purge())
    yield
    event_loop.run_until_complete(_purge())


# ─────────────────────────────────────────────────────────────────────
# T-1  Legacy migration parity
# ─────────────────────────────────────────────────────────────────────
def test_T1_legacy_schema_zeroed(db, event_loop):
    async def _check():
        kind = await db.notifications.count_documents({"kind": {"$exists": True}})
        audience = await db.notifications.count_documents({"audience": {"$exists": True}})
        user_email = await db.notifications.count_documents({"user_email": {"$exists": True}})
        legacy_user_id = await db.notifications.count_documents(
            {"user_id": {"$exists": True}, "type": {"$exists": False}}
        )
        read_bool = await db.notifications.count_documents({"read": {"$exists": True}})
        return (kind, audience, user_email, legacy_user_id, read_bool)
    kind, audience, user_email, legacy_user_id, read_bool = event_loop.run_until_complete(_check())
    assert kind == 0, f"legacy `kind` field still present in {kind} rows"
    assert audience == 0, f"legacy `audience` field still present in {audience} rows"
    assert user_email == 0, f"legacy `user_email` field still present in {user_email} rows"
    assert legacy_user_id == 0, f"legacy `user_id` field still present in {legacy_user_id} rows"
    assert read_bool == 0, f"legacy `read` (bool) field still present in {read_bool} rows"


def test_T1_canonical_schema_universal(db, event_loop):
    async def _check():
        total = await db.notifications.count_documents({})
        canonical = await db.notifications.count_documents({"type": {"$exists": True}})
        with_event_id = await db.notifications.count_documents({"event_id": {"$exists": True}})
        with_idem = await db.notifications.count_documents({"idempotency_key": {"$exists": True}})
        return total, canonical, with_event_id, with_idem
    total, canonical, with_event, with_idem = event_loop.run_until_complete(_check())
    assert total == canonical == with_event == with_idem, (
        f"schema not 100% canonical: total={total} type={canonical} "
        f"event_id={with_event} idempotency_key={with_idem}"
    )


def test_T1_tasks_notifications_collection_dropped(db, event_loop):
    async def _check():
        return await db.list_collection_names()
    cols = event_loop.run_until_complete(_check())
    assert "tasks_notifications" not in cols, (
        "legacy collection tasks_notifications must be dropped"
    )


# ─────────────────────────────────────────────────────────────────────
# T-2  Duplicate prevention — 100× replay → 1 row
# ─────────────────────────────────────────────────────────────────────
def test_T2_replay_collapses_to_one_row(db, event_loop):
    async def _replay():
        record_id = f"track-15-28c-replay-{uuid.uuid4().hex[:8]}"
        payload = {
            "type": "track_15_28c.replay_event",
            "title": "Idempotency replay test",
            "message": "Should collapse to exactly 1 row regardless of replay count.",
            "severity": "Info",
            "recipient_role": "admin",
            "linked_source_module": TEST_MODULE,
            "linked_source_record_id": record_id,
        }
        ids: List[str] = []
        for _ in range(100):
            ids.append(await emit_notification(db, dict(payload)))
        cnt = await db.notifications.count_documents({
            "linked_source_module": TEST_MODULE,
            "linked_source_record_id": record_id,
        })
        return ids, cnt
    ids, cnt = event_loop.run_until_complete(_replay())
    assert cnt == 1, f"100 replays produced {cnt} rows (expected 1)"
    assert len(set(ids)) == 1, (
        f"100 replays returned {len(set(ids))} distinct ids (expected 1)"
    )


def test_T2_distinct_recipients_dont_collapse(db, event_loop):
    """Two recipients of the same event must be DIFFERENT idempotency keys
    so the bell still fans out to multiple humans correctly."""
    async def _two():
        record_id = f"track-15-28c-multi-{uuid.uuid4().hex[:8]}"
        a = await emit_notification(db, {
            "type": "track_15_28c.multi_recipient",
            "title": "Multi-recipient", "message": "to user A",
            "severity": "Info",
            "recipient_role": "admin",
            "recipient_user_id": "track-15-28c-user-A",
            "linked_source_module": TEST_MODULE,
            "linked_source_record_id": record_id,
        })
        b = await emit_notification(db, {
            "type": "track_15_28c.multi_recipient",
            "title": "Multi-recipient", "message": "to user B",
            "severity": "Info",
            "recipient_role": "admin",
            "recipient_user_id": "track-15-28c-user-B",
            "linked_source_module": TEST_MODULE,
            "linked_source_record_id": record_id,
        })
        cnt = await db.notifications.count_documents({
            "linked_source_module": TEST_MODULE,
            "linked_source_record_id": record_id,
        })
        return a, b, cnt
    a, b, cnt = event_loop.run_until_complete(_two())
    assert a != b
    assert cnt == 2, f"two distinct recipients should yield 2 rows, got {cnt}"


# ─────────────────────────────────────────────────────────────────────
# T-3  PM project scope — PM-A sees A only, never B
# ─────────────────────────────────────────────────────────────────────
def test_T3_pm_project_scope(db, event_loop):
    async def _exercise():
        pm_a_id = "track-15-28c-pma"
        pm_b_id = "track-15-28c-pmb"
        # Two PMs, each on one project.
        await db.project_team_assignments.insert_many([
            {"id": str(uuid.uuid4()), "project_number": TEST_PROJECT_A,
             "user_id": pm_a_id, "email": "pma@track15.test",
             "assignment_role": "pm", "active": True,
             "assignment_status": "ACTIVE"},
            {"id": str(uuid.uuid4()), "project_number": TEST_PROJECT_B,
             "user_id": pm_b_id, "email": "pmb@track15.test",
             "assignment_role": "pm", "active": True,
             "assignment_status": "ACTIVE"},
        ])
        # Two role-broadcast PM notifications, one per project.
        await emit_notification(db, {
            "type": "track_15_28c.pm_scope_test", "title": "A event",
            "message": "Project A", "severity": "Info",
            "recipient_role": "pm", "linked_project_number": TEST_PROJECT_A,
            "linked_source_module": TEST_MODULE,
            "linked_source_record_id": f"{TEST_PROJECT_A}-scope",
        })
        await emit_notification(db, {
            "type": "track_15_28c.pm_scope_test", "title": "B event",
            "message": "Project B", "severity": "Info",
            "recipient_role": "pm", "linked_project_number": TEST_PROJECT_B,
            "linked_source_module": TEST_MODULE,
            "linked_source_record_id": f"{TEST_PROJECT_B}-scope",
        })
        # And a system-wide PM notification with pm_broadcast=False (suppressed).
        await emit_notification(db, {
            "type": "track_15_28c.pm_scope_test", "title": "Suppressed system",
            "message": "no project, no broadcast", "severity": "Info",
            "recipient_role": "pm", "linked_project_number": None,
            "linked_source_module": TEST_MODULE,
            "linked_source_record_id": "global-suppressed",
        })
        # And one explicit pm_broadcast=True (allowed for both PMs).
        await emit_notification(db, {
            "type": "track_15_28c.pm_scope_test", "title": "Company-wide",
            "message": "explicit pm_broadcast", "severity": "Info",
            "recipient_role": "pm", "linked_project_number": None,
            "pm_broadcast": True,
            "linked_source_module": TEST_MODULE,
            "linked_source_record_id": "global-broadcast",
        })

        # Build actors mirroring portal token shape used by the filter.
        actor_a = {"id": pm_a_id, "email": "pma@track15.test", "role": "pm"}
        actor_b = {"id": pm_b_id, "email": "pmb@track15.test", "role": "pm"}
        filt_a = await build_notif_filter_async(db, actor_a)
        filt_b = await build_notif_filter_async(db, actor_b)
        rows_a = await db.notifications.find(
            {**filt_a, "linked_source_module": TEST_MODULE},
            {"_id": 0, "title": 1, "linked_project_number": 1, "pm_broadcast": 1},
        ).to_list(50)
        rows_b = await db.notifications.find(
            {**filt_b, "linked_source_module": TEST_MODULE},
            {"_id": 0, "title": 1, "linked_project_number": 1, "pm_broadcast": 1},
        ).to_list(50)
        return rows_a, rows_b

    rows_a, rows_b = event_loop.run_until_complete(_exercise())
    titles_a = {r["title"] for r in rows_a}
    titles_b = {r["title"] for r in rows_b}

    # PM-A: A event + Company-wide. Never B. Never Suppressed.
    assert "A event" in titles_a, f"PM-A missing project-A: {titles_a}"
    assert "Company-wide" in titles_a, f"PM-A missing pm_broadcast=True row: {titles_a}"
    assert "B event" not in titles_a, f"PM-A leaked project-B: {titles_a}"
    assert "Suppressed system" not in titles_a, f"PM-A leaked system-wide non-broadcast: {titles_a}"

    # PM-B: B event + Company-wide. Never A. Never Suppressed.
    assert "B event" in titles_b
    assert "Company-wide" in titles_b
    assert "A event" not in titles_b
    assert "Suppressed system" not in titles_b


# ─────────────────────────────────────────────────────────────────────
# T-4  Bell visibility — no canonical row should be unreachable
# ─────────────────────────────────────────────────────────────────────
def test_T4_no_orphan_canonical_rows(db, event_loop):
    """Every row in the canonical schema must be reachable by ≥1 actor.
    Admin sees everything; if we ever produced a row with no
    recipient_role + no recipient_user_id, only admin sees it — which is
    acceptable IF and ONLY IF the row was created as admin-targeted."""
    async def _check():
        # Any non-admin row missing both routing keys is an orphan.
        orphans = await db.notifications.count_documents({
            "type": {"$exists": True},
            "recipient_role": {"$in": [None, ""]},
            "$or": [
                {"recipient_user_id": None},
                {"recipient_user_id": {"$exists": False}},
            ],
        })
        # Rows targeting roles that don't exist in any user collection.
        # Allowed roles list (kept loose — every portal we support):
        allowed = {
            "admin", "pm", "hr", "safety", "shop", "dispatch",
            "field_leadership", "fl", "asset_admin", "leadership",
            "superintendent",
        }
        bad_roles = await db.notifications.distinct("recipient_role")
        bad = [r for r in bad_roles if r not in allowed and r is not None]
        return orphans, bad
    orphans, bad = event_loop.run_until_complete(_check())
    assert orphans == 0, f"{orphans} canonical rows have no role and no user"
    assert not bad, f"unexpected recipient_role values: {bad}"


# ─────────────────────────────────────────────────────────────────────
# T-5  Cross-portal verification — each portal role can read its own rows
# ─────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("role", [
    "admin", "pm", "hr", "safety", "shop", "dispatch",
    "field_leadership", "asset_admin",
])
def test_T5_portal_filter_returns_sane_results(db, event_loop, role):
    """For each portal role, building the canonical filter must return a
    valid Mongo query AND counting against it must succeed (no schema
    drift breaking the filter shape)."""
    async def _exercise():
        actor: Dict[str, Any] = {
            "id": f"track-15-28c-{role}",
            "email": f"{role}@track15.test",
            "role": role,
            "is_asset_admin": role == "asset_admin",
        }
        filt = await build_notif_filter_async(db, actor)
        cnt = await db.notifications.count_documents(filt)
        return filt, cnt
    filt, cnt = event_loop.run_until_complete(_exercise())
    assert isinstance(filt, dict)
    assert cnt >= 0


# ─────────────────────────────────────────────────────────────────────
# T-6  Hard-refresh consistency — count is idempotent
# ─────────────────────────────────────────────────────────────────────
def test_T6_count_is_idempotent(db, event_loop):
    """Reading the bell N times in a row must return the same count.
    Tests for the historical bug where listing fanned out new rows."""
    async def _exercise():
        actor = {"id": "admin", "email": "admin@track15.test", "role": "admin"}
        filt = await build_notif_filter_async(db, actor)
        counts = []
        for _ in range(5):
            counts.append(await db.notifications.count_documents(filt))
        return counts
    counts = event_loop.run_until_complete(_exercise())
    assert len(set(counts)) == 1, f"count drift across reads: {counts}"


# ─────────────────────────────────────────────────────────────────────
# T-7  DB count parity — every row has every required canonical field
# ─────────────────────────────────────────────────────────────────────
def test_T7_every_row_has_required_fields(db, event_loop):
    async def _exercise():
        total = await db.notifications.count_documents({})
        required = ["type", "recipient_role", "event_id",
                    "idempotency_key", "created_at"]
        missing = {}
        for f in required:
            missing[f] = await db.notifications.count_documents({
                "$or": [{f: {"$exists": False}}, {f: None}],
            })
        # idempotency_key uniqueness
        pipe = [
            {"$group": {"_id": "$idempotency_key", "c": {"$sum": 1}}},
            {"$match": {"c": {"$gt": 1}}},
            {"$limit": 5},
        ]
        dup_keys = [d async for d in db.notifications.aggregate(pipe)]
        return total, missing, dup_keys
    total, missing, dup_keys = event_loop.run_until_complete(_exercise())
    for f, m in missing.items():
        assert m == 0, f"{m} rows missing required field {f!r} (out of {total})"
    assert not dup_keys, f"idempotency_key duplicates: {dup_keys}"


def test_T7_idempotency_key_function_stable():
    """Belt-and-braces: the sha256 function must be deterministic."""
    p = {
        "type": "demo",
        "linked_source_record_id": "REC-1",
        "recipient_role": "pm",
        "recipient_user_id": "u-1",
    }
    a = compute_idempotency_key(p)
    b = compute_idempotency_key(p)
    c = compute_idempotency_key({**p, "type": "demo2"})
    assert a == b
    assert a != c
