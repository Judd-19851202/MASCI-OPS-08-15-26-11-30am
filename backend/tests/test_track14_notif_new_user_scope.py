"""
TRACK 14.0-NOTIF-NEW-USER-SCOPE — regression tests.

Verifies the eligibility filter on the notification feed:

  • New portal users (created today) do NOT inherit historical
    role-broadcast notifications dispatched before they joined.
  • Existing portal users (created earlier) retain visibility into
    role broadcasts dispatched after they joined.
  • Direct-user notifications (`recipient_user_id == actor.id`) bypass
    the eligibility cutoff entirely — direct addressing always wins.
  • Admin (no eligibility filter) sees everything.
  • Asset Admin OR-scope is preserved through the eligibility filter.

Run:
    cd /app/backend && python -m pytest tests/test_track14_notif_new_user_scope.py -v
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import pytest


@pytest.fixture
def make_actor():
    """Build a portal-user actor dict matching what require_any_portal_token
    produces. ``created_at`` is the eligibility cutoff."""
    def _make(
        role: str,
        created_at: datetime | None,
        user_id: str | None = None,
        is_asset_admin: bool = False,
    ) -> Dict[str, Any]:
        actor: Dict[str, Any] = {
            "_actor": role,
            "id": user_id or str(uuid.uuid4()),
            "name": f"test-{role}",
            "email": f"test.{role}@example.com",
        }
        if created_at is not None:
            actor["created_at"] = created_at.isoformat()
        if is_asset_admin:
            actor["is_asset_admin"] = True
        return actor
    return _make


def _build_filter(actor: Dict[str, Any]) -> Dict[str, Any]:
    """Direct call into the module-level filter — exercises the exact
    code path the router uses without needing closure inspection."""
    from routes.tasks_notifications import build_notif_filter
    return build_notif_filter(actor)


def test_admin_actor_returns_open_filter(make_actor):
    actor = make_actor("admin", created_at=None)
    f = _build_filter(actor)
    assert f == {}, "Admin should bypass all notification filters"


def test_new_hr_user_has_eligibility_clause(make_actor):
    join = datetime(2026, 6, 15, tzinfo=timezone.utc)
    actor = make_actor("hr", created_at=join)
    f = _build_filter(actor)
    # Expect $or with role-clause containing an eligibility cutoff
    assert "$or" in f, "Direct-user clause should OR with role clause"
    role_clause = next(
        c for c in f["$or"] if "$and" in c and any(
            "created_at" in cl for cl in c["$and"]
        )
    )
    cutoff_clause = next(c for c in role_clause["$and"] if "created_at" in c)
    assert cutoff_clause["created_at"]["$gte"] == join, (
        "Eligibility cutoff must match actor.created_at"
    )


def test_legacy_user_without_created_at_keeps_old_behaviour(make_actor):
    actor = make_actor("hr", created_at=None)
    f = _build_filter(actor)
    # The role clause should NOT carry a created_at cutoff — preserves
    # backwards compatibility for users without a recorded join date.
    if "$or" in f:
        for c in f["$or"]:
            if "$and" in c:
                assert not any("created_at" in cl for cl in c["$and"]), (
                    "Actors without created_at must not get an eligibility cutoff"
                )


def test_direct_user_clause_bypasses_eligibility(make_actor):
    join = datetime(2026, 6, 15, tzinfo=timezone.utc)
    user_id = "user-direct-123"
    actor = make_actor("hr", created_at=join, user_id=user_id)
    f = _build_filter(actor)
    # The OR'd direct-user clause must be a flat {"recipient_user_id":
    # <id>} with NO created_at filter — direct addressing wins.
    direct_clauses = [c for c in f["$or"] if c.get("recipient_user_id") == user_id]
    assert len(direct_clauses) == 1
    assert "created_at" not in direct_clauses[0], (
        "Direct-user clause must not be eligibility-filtered"
    )


def test_asset_admin_or_scope_with_eligibility(make_actor):
    join = datetime(2026, 6, 15, tzinfo=timezone.utc)
    actor = make_actor("hr", created_at=join, is_asset_admin=True)
    f = _build_filter(actor)
    role_clause = next(c for c in f["$or"] if "$and" in c)
    in_clause = next(c for c in role_clause["$and"] if "recipient_role" in c)
    assert set(in_clause["recipient_role"]["$in"]) == {"hr", "asset_admin"}, (
        "Asset Admin OR-scope must extend role list even with eligibility filter"
    )


def test_eligibility_parses_iso_string(make_actor):
    """Actor.created_at arrives as an ISO string from the auth dep;
    the filter must parse it back to a datetime."""
    actor = {
        "_actor": "hr",
        "id": "u-1",
        "created_at": "2026-06-15T02:08:43.676955+00:00",
    }
    f = _build_filter(actor)
    role_clause = next(c for c in f["$or"] if "$and" in c)
    cutoff = next(c for c in role_clause["$and"] if "created_at" in c)
    cutoff_dt = cutoff["created_at"]["$gte"]
    assert isinstance(cutoff_dt, datetime)
    assert cutoff_dt.tzinfo is not None
    assert cutoff_dt.year == 2026 and cutoff_dt.month == 6 and cutoff_dt.day == 15


def test_unparseable_created_at_falls_back_safely(make_actor):
    actor = {"_actor": "hr", "id": "u-2", "created_at": "not-a-date"}
    f = _build_filter(actor)
    # No eligibility cutoff — preserves backwards-compat / fail-open
    if "$or" in f:
        for c in f["$or"]:
            if "$and" in c:
                assert not any("created_at" in cl for cl in c["$and"])


# ─── End-to-end DB tests (require live MongoDB) ──────────────────────────

@pytest.mark.asyncio
async def test_end_to_end_eligibility_with_mongo(monkeypatch):
    """Integration check: insert a historic role-broadcast + a direct
    notification, then assert the eligibility filter excludes the former
    and includes the latter when queried for a new HR user."""
    pytest.importorskip("motor")
    from motor.motor_asyncio import AsyncIOMotorClient  # noqa: PLC0415
    import os  # noqa: PLC0415
    from dotenv import load_dotenv  # noqa: PLC0415
    load_dotenv()
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")
    if not mongo_url or not db_name:
        pytest.skip("MONGO_URL / DB_NAME not configured")
    cli = AsyncIOMotorClient(mongo_url)
    db = cli[db_name]

    # Synthetic test user — created today
    user_id = f"track-14-notif-eligibility-{uuid.uuid4().hex[:8]}"
    join = datetime.now(timezone.utc)
    # Insert one historic role broadcast (1 year ago) — must be invisible
    historic_id = f"TRACK14-NOTIF-HISTORIC-{uuid.uuid4().hex[:8]}"
    historic = {
        "id": historic_id, "type": "test.role-old", "title": "Old role notif",
        "severity": "Info", "recipient_role": "hr", "recipient_user_id": None,
        "created_at": join - timedelta(days=365),
        "read_by": [], "acknowledged_by": None, "acknowledged_at": None,
        "expires_at": join + timedelta(days=60),
    }
    # Insert one direct notification (also 1 year ago, addressed to user) — must be visible
    direct_id = f"TRACK14-NOTIF-DIRECT-{uuid.uuid4().hex[:8]}"
    direct = {
        "id": direct_id, "type": "test.direct", "title": "Direct old notif",
        "severity": "Info", "recipient_role": "hr", "recipient_user_id": user_id,
        "created_at": join - timedelta(days=365),
        "read_by": [], "acknowledged_by": None, "acknowledged_at": None,
        "expires_at": join + timedelta(days=60),
    }
    # Insert one new role broadcast (now) — must be visible
    new_id = f"TRACK14-NOTIF-NEW-{uuid.uuid4().hex[:8]}"
    new_role = {
        "id": new_id, "type": "test.role-new", "title": "New role notif",
        "severity": "Info", "recipient_role": "hr", "recipient_user_id": None,
        "created_at": join + timedelta(seconds=1),
        "read_by": [], "acknowledged_by": None, "acknowledged_at": None,
        "expires_at": join + timedelta(days=60),
    }
    await db.notifications.insert_many([historic, direct, new_role])
    try:
        actor = {"_actor": "hr", "id": user_id, "created_at": join.isoformat()}
        flt = _build_filter(actor)
        # Direct hit
        cnt_direct = await db.notifications.count_documents({
            "$and": [flt, {"id": direct_id}]
        })
        assert cnt_direct == 1, "Direct user notification must be visible"
        # Historic role broadcast — must be excluded
        cnt_hist = await db.notifications.count_documents({
            "$and": [flt, {"id": historic_id}]
        })
        assert cnt_hist == 0, "Historic role broadcast must be filtered out"
        # New role broadcast — must be visible
        cnt_new = await db.notifications.count_documents({
            "$and": [flt, {"id": new_id}]
        })
        assert cnt_new == 1, "New role broadcast must be visible"
    finally:
        # Cleanup
        await db.notifications.delete_many(
            {"id": {"$in": [historic_id, direct_id, new_id]}}
        )
