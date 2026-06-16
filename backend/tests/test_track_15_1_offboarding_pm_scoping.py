"""
TRACK 15.1 LIVE PRODUCTION DEFECT SWEEP — regression suite.

Defect 1: PM Notification Leakage.
Before fix: every PM in the directory received "Offboarding <employee>"
notifications whenever HR offboarded anyone, because the playbook PM
row used `assignee_role="pm"` with no `recipient_user_id` → role
broadcast.

After fix: the PM playbook row is scoped per-project. Only PMs of
projects the offboarded employee was actively staffed on receive a
task, and the notification carries `recipient_user_id=<that PM>` so
it is hidden from the role broadcast (other PMs see nothing).

This test exercises the two new code paths in isolation against a
scratch Mongo (no network, no real users), proving the contract is
enforced. Cleanup is total: every fixture row is deleted in the
finally block.

Run:
  cd /app/backend && python -m pytest tests/test_track_15_1_offboarding_pm_scoping.py -v
"""
from __future__ import annotations

import asyncio
import os
import uuid

import pytest
from motor.motor_asyncio import AsyncIOMotorClient


TAG = f"track-15-1-{uuid.uuid4().hex[:8]}"


async def _get_db():
    url = os.environ["MONGO_URL"]
    db_name = os.environ.get("DB_NAME") or "masci_safety_preview"
    cli = AsyncIOMotorClient(url)
    return cli, cli[db_name]


@pytest.mark.asyncio
async def test_resolve_offboarding_pm_targets_returns_empty_when_no_assignments():
    """No active assignments → no PM targets → no PM task → no broadcast."""
    from routes.employee_lifecycle import _resolve_offboarding_pm_targets

    cli, db = await _get_db()
    try:
        emp = {"id": f"emp-{TAG}-noasn", "name": "RC1-LIVE-DEFECT-SWEEP-emp", "email": f"{TAG}-noasn@test.local"}
        targets = await _resolve_offboarding_pm_targets(db, emp)
        assert targets == [], (
            "Employee with no project_team_assignments must yield no PM "
            f"targets, got {targets!r}"
        )
    finally:
        cli.close()


@pytest.mark.asyncio
async def test_resolve_offboarding_pm_targets_scopes_to_project_pms_only():
    """Employee staffed on Project A → only Project A's PM is targeted,
    PMs of unrelated projects must not appear in the target list."""
    from routes.employee_lifecycle import _resolve_offboarding_pm_targets

    cli, db = await _get_db()
    proj_a = f"RC1-LIVE-DEFECT-SWEEP-{TAG}-A"
    proj_b = f"RC1-LIVE-DEFECT-SWEEP-{TAG}-B"
    pm_a = {"id": f"pm-{TAG}-A", "email": f"{TAG}-pm-a@test.local", "name": "RC1-LIVE-DEFECT-SWEEP-PM-A"}
    pm_b = {"id": f"pm-{TAG}-B", "email": f"{TAG}-pm-b@test.local", "name": "RC1-LIVE-DEFECT-SWEEP-PM-B"}
    emp = {"id": f"emp-{TAG}-scoped", "name": "RC1-LIVE-DEFECT-SWEEP-emp-scoped", "email": f"{TAG}-emp@test.local"}
    try:
        await db.user_directory.insert_one(pm_a)
        await db.user_directory.insert_one(pm_b)
        await db.jobs_master.insert_one({
            "project_number": proj_a, "pm_email": pm_a["email"], "co_pm_emails": [],
        })
        await db.jobs_master.insert_one({
            "project_number": proj_b, "pm_email": pm_b["email"], "co_pm_emails": [],
        })
        # Employee is staffed on Project A only.
        await db.project_team_assignments.insert_one({
            "id": f"asn-{TAG}-A",
            "project_number": proj_a,
            "assignment_role": "foreman",
            "active": True,
            "employee_id": emp["id"],
            "email": emp["email"],
        })

        targets = await _resolve_offboarding_pm_targets(db, emp)
        target_user_ids = {t["user_id"] for t in targets}
        target_projects = {t["project_number"] for t in targets}

        assert target_user_ids == {pm_a["id"]}, (
            f"Expected only PM-A in targets (employee was only on Project A), "
            f"got {target_user_ids!r}"
        )
        assert target_projects == {proj_a}, (
            f"Expected only Project A in target projects, got {target_projects!r}"
        )
        assert pm_b["id"] not in target_user_ids, (
            "PM-B must not appear — employee was NOT staffed on Project B. "
            "If this fails, the leakage bug has regressed."
        )
    finally:
        # Cleanup is mandatory per Track 15.1 cert artifact rules.
        await db.user_directory.delete_many({"id": {"$in": [pm_a["id"], pm_b["id"]]}})
        await db.jobs_master.delete_many({"project_number": {"$in": [proj_a, proj_b]}})
        await db.project_team_assignments.delete_many({"id": f"asn-{TAG}-A"})
        cli.close()


@pytest.mark.asyncio
async def test_resolve_offboarding_pm_targets_includes_co_pms():
    """Co-PMs of the employee's project are also targeted (everyone
    responsible for project coverage hears about backfill)."""
    from routes.employee_lifecycle import _resolve_offboarding_pm_targets

    cli, db = await _get_db()
    proj = f"RC1-LIVE-DEFECT-SWEEP-{TAG}-CO"
    primary_pm = {"id": f"pm-{TAG}-primary", "email": f"{TAG}-primary@test.local", "name": "RC1-PM-primary"}
    co_pm = {"id": f"pm-{TAG}-co", "email": f"{TAG}-co@test.local", "name": "RC1-PM-co"}
    emp = {"id": f"emp-{TAG}-co", "name": "RC1-emp-co", "email": f"{TAG}-emp-co@test.local"}
    try:
        await db.user_directory.insert_one(primary_pm)
        await db.user_directory.insert_one(co_pm)
        await db.jobs_master.insert_one({
            "project_number": proj,
            "pm_email": primary_pm["email"],
            "co_pm_emails": [co_pm["email"]],
        })
        await db.project_team_assignments.insert_one({
            "id": f"asn-{TAG}-co",
            "project_number": proj,
            "assignment_role": "foreman",
            "active": True,
            "employee_id": emp["id"],
            "email": emp["email"],
        })

        targets = await _resolve_offboarding_pm_targets(db, emp)
        target_user_ids = {t["user_id"] for t in targets}
        assert target_user_ids == {primary_pm["id"], co_pm["id"]}, (
            f"Both primary PM and co-PM should be targeted, got {target_user_ids!r}"
        )
    finally:
        await db.user_directory.delete_many({"id": {"$in": [primary_pm["id"], co_pm["id"]]}})
        await db.jobs_master.delete_many({"project_number": proj})
        await db.project_team_assignments.delete_many({"id": f"asn-{TAG}-co"})
        cli.close()


@pytest.mark.asyncio
async def test_task_create_passes_recipient_user_id_when_targeted():
    """Track 15.1 — task_service.create must propagate
    `assignee_user_id` → notification.recipient_user_id so the
    notification is hidden from the role-broadcast lane and only the
    targeted PM sees it."""
    from routes.tasks_notifications import task_service

    cli, db = await _get_db()
    target_user_id = f"rc1-live-defect-sweep-target-{TAG}"
    task_id = None
    try:
        task_id = await task_service.create(db, {
            "title": f"RC1-LIVE-DEFECT-SWEEP-task-{TAG}",
            "description": "regression test — must be person-targeted",
            "source_module": "admin.manual",
            "assignee_role": "pm",
            "assignee_user_id": target_user_id,
            "linked_project_number": f"RC1-LIVE-DEFECT-SWEEP-{TAG}",
            "priority": "Medium",
            "created_by": {"role": "system", "name": "rc1-cert"},
        })
        # The notification fanout writes a row to db.notifications. Find
        # it and verify recipient_user_id is set, so role-broadcast
        # filter (which excludes rows with recipient_user_id set) hides
        # it from non-targeted PMs.
        notif = await db.notifications.find_one(
            {"linked_task_id": task_id}, {"_id": 0},
        )
        assert notif is not None, "notification fanout did not write a row"
        assert notif.get("recipient_user_id") == target_user_id, (
            f"Track 15.1 contract violated: notification.recipient_user_id "
            f"must equal the task's assignee_user_id; got "
            f"{notif.get('recipient_user_id')!r}"
        )
        assert notif.get("recipient_role") == "pm", (
            "recipient_role must still carry the scope guard"
        )
    finally:
        # Cleanup mandatory.
        if task_id:
            await db.tasks.delete_many({"id": task_id})
            await db.notifications.delete_many({"linked_task_id": task_id})
        cli.close()


@pytest.mark.asyncio
async def test_task_create_role_broadcast_when_no_user_id():
    """Pre-existing producers that DON'T set assignee_user_id continue
    to broadcast (backward-compatible — no regression)."""
    from routes.tasks_notifications import task_service

    cli, db = await _get_db()
    task_id = None
    try:
        task_id = await task_service.create(db, {
            "title": f"RC1-LIVE-DEFECT-SWEEP-role-broadcast-{TAG}",
            "description": "regression test — must be role-broadcast",
            "source_module": "admin.manual",
            "assignee_role": "shop",
            "priority": "Medium",
            "created_by": {"role": "system", "name": "rc1-cert"},
        })
        notif = await db.notifications.find_one(
            {"linked_task_id": task_id}, {"_id": 0},
        )
        assert notif is not None
        # Should be None (role broadcast) or whatever the ownership
        # resolver returns (which is None for admin.manual with no
        # linked_project_number).
        assert notif.get("recipient_user_id") is None, (
            f"Expected role-broadcast (no recipient_user_id), got "
            f"{notif.get('recipient_user_id')!r}"
        )
        assert notif.get("recipient_role") == "shop"
    finally:
        if task_id:
            await db.tasks.delete_many({"id": task_id})
            await db.notifications.delete_many({"linked_task_id": task_id})
        cli.close()


if __name__ == "__main__":  # pragma: no cover
    asyncio.run(test_resolve_offboarding_pm_targets_returns_empty_when_no_assignments())
    asyncio.run(test_resolve_offboarding_pm_targets_scopes_to_project_pms_only())
    asyncio.run(test_resolve_offboarding_pm_targets_includes_co_pms())
    asyncio.run(test_task_create_passes_recipient_user_id_when_targeted())
    asyncio.run(test_task_create_role_broadcast_when_no_user_id())
    print("All Track 15.1 regression tests passed.")
