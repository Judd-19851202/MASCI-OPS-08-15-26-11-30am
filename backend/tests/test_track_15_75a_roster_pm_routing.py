"""TRACK 15.75A — PM/Co-PM roster-driven routing regression.

Defends the source-chain mismatch fix: when `jobs_master.pm_email`
is blank but the Job Master "Team Roster" (`project_team_assignments`,
`assignment_role='pm'`, `is_primary=True`, `active=True`) carries
an active primary PM, the routing resolver MUST resolve to that
PM's email — not dead-letter as a "missing PM" silent failure.

Before this fix the resolver ignored `project_team_assignments`
entirely; production Job Master UI showed `David Jewett` /
`Jaymn Judd` as the assigned PM on projects 20-07 and 26-07,
but submitted Daily Reports dead-lettered to
`safety@mascigc.com` because the resolver only consulted the
legacy `jobs_master.pm_email` column.

Co-PMs from the roster are likewise unioned into the
`co_pm_emails` recipient list at routing time so the Team
Roster co-PM chips are honored even when the legacy
`jobs_master.co_pm_emails` array is stale.
"""
from __future__ import annotations

import os
import asyncio
import uuid
import pytest
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv("/app/backend/.env")


def _db():
    cli = AsyncIOMotorClient(os.environ["MONGO_URL"])
    return cli[os.environ["DB_NAME"]]


PROJECT = "TRACK-15-75A-TEST"


async def _seed(db, *, with_pm_email=False, with_roster_pm=False,
                with_legacy_co_pm=False, with_roster_co_pm=False):
    """Create a fresh project_number + matching roster rows. Returns
    the project_number used."""
    pn = f"{PROJECT}-{uuid.uuid4().hex[:6]}"
    job_doc = {
        "id": str(uuid.uuid4()),
        "project_number": pn,
        "project_name": f"Track 15.75A fixture {pn}",
        "project_manager": "",
        "pm_email": "pm.legacy@example.test" if with_pm_email else "",
        "co_pm_emails": (
            ["copm.legacy@example.test"] if with_legacy_co_pm else []
        ),
        "active": True,
    }
    await db.jobs_master.insert_one(dict(job_doc))
    if with_roster_pm:
        await db.project_team_assignments.insert_one({
            "id": str(uuid.uuid4()),
            "project_number": pn,
            "assignment_role": "pm",
            "is_primary": True,
            "active": True,
            "email": "pm.roster@example.test",
            "display_name": "Roster PM",
            "assigned_at": "2026-01-01T00:00:00+00:00",
        })
    if with_roster_co_pm:
        await db.project_team_assignments.insert_one({
            "id": str(uuid.uuid4()),
            "project_number": pn,
            "assignment_role": "co_pm",
            "is_primary": False,
            "active": True,
            "email": "copm.roster@example.test",
            "display_name": "Roster Co-PM",
            "assigned_at": "2026-01-01T00:00:00+00:00",
        })
    return pn


async def _cleanup(db, pn):
    await db.jobs_master.delete_many({"project_number": pn})
    await db.project_team_assignments.delete_many({"project_number": pn})


@pytest.mark.asyncio
async def test_legacy_pm_email_still_wins_when_present():
    """Backward compatibility — when jobs_master.pm_email is set,
    the resolver MUST keep using it even if the roster carries a
    different PM. No silent override."""
    db = _db()
    pn = await _seed(db, with_pm_email=True, with_roster_pm=True)
    try:
        from pm_routing import resolve_pm_for_record_async  # noqa: PLC0415
        result = await resolve_pm_for_record_async(
            db, {"project_number": pn}
        )
        assert result is not None
        _name, email = result
        assert email == "pm.legacy@example.test", (
            f"legacy pm_email must win when set, got {email}"
        )
    finally:
        await _cleanup(db, pn)


@pytest.mark.asyncio
async def test_roster_pm_resolves_when_legacy_blank():
    """🔥 TRACK 15.75A core fix — when jobs_master.pm_email is blank
    but the Team Roster carries an active primary PM, route to
    that PM. Previously the resolver dead-lettered silently."""
    db = _db()
    pn = await _seed(db, with_pm_email=False, with_roster_pm=True)
    try:
        from pm_routing import resolve_pm_for_record_async  # noqa: PLC0415
        result = await resolve_pm_for_record_async(
            db, {"project_number": pn}
        )
        assert result is not None, (
            "resolver MUST find the roster PM when legacy column is blank"
        )
        _name, email = result
        assert email == "pm.roster@example.test"
    finally:
        await _cleanup(db, pn)


@pytest.mark.asyncio
async def test_no_pm_anywhere_dead_letters():
    """When neither legacy column nor roster has a PM, resolver
    returns None → routing falls to ADMIN_DEAD_LETTER_TO with the
    truthful audit row from Track 15.74."""
    db = _db()
    pn = await _seed(db, with_pm_email=False, with_roster_pm=False)
    try:
        from pm_routing import resolve_pm_for_record_async  # noqa: PLC0415
        result = await resolve_pm_for_record_async(
            db, {"project_number": pn}
        )
        assert result is None
    finally:
        await _cleanup(db, pn)


@pytest.mark.asyncio
async def test_roster_co_pms_unioned_with_legacy():
    """Co-PMs from project_team_assignments MUST union with
    jobs_master.co_pm_emails — never drop a legacy co-PM, never
    skip a roster co-PM."""
    db = _db()
    pn = await _seed(db,
                     with_pm_email=True,
                     with_legacy_co_pm=True,
                     with_roster_co_pm=True)
    try:
        from pm_routing import recipients_for_record_async  # noqa: PLC0415
        res = await recipients_for_record_async(
            db, {"project_number": pn}, kind="daily-report",
        )
        # On a PM_ONLY kind, co-PMs are in CC.
        cc = [e.lower() for e in res.get("cc", [])]
        assert "copm.legacy@example.test" in cc, (
            "legacy co-PM must remain in CC"
        )
        assert "copm.roster@example.test" in cc, (
            "TRACK 15.75A: roster co-PM must also be in CC"
        )
    finally:
        await _cleanup(db, pn)


@pytest.mark.asyncio
async def test_inactive_roster_pm_is_ignored():
    """A roster row with active=False MUST NOT resolve as the PM —
    otherwise removed PMs would silently continue receiving mail."""
    db = _db()
    pn = await _seed(db, with_pm_email=False, with_roster_pm=False)
    # Insert an INACTIVE roster PM row directly.
    await db.project_team_assignments.insert_one({
        "id": str(uuid.uuid4()),
        "project_number": pn,
        "assignment_role": "pm",
        "is_primary": True,
        "active": False,
        "email": "removed.pm@example.test",
        "assigned_at": "2026-01-01T00:00:00+00:00",
    })
    try:
        from pm_routing import resolve_pm_for_record_async  # noqa: PLC0415
        result = await resolve_pm_for_record_async(
            db, {"project_number": pn}
        )
        assert result is None, (
            "inactive roster PM must not resolve — would leak to "
            "removed PMs otherwise"
        )
    finally:
        await _cleanup(db, pn)


@pytest.mark.asyncio
async def test_non_primary_roster_pm_is_ignored():
    """A roster row with active=True but is_primary=False MUST NOT
    resolve as the primary PM."""
    db = _db()
    pn = await _seed(db, with_pm_email=False, with_roster_pm=False)
    await db.project_team_assignments.insert_one({
        "id": str(uuid.uuid4()),
        "project_number": pn,
        "assignment_role": "pm",
        "is_primary": False,
        "active": True,
        "email": "backup.pm@example.test",
        "assigned_at": "2026-01-01T00:00:00+00:00",
    })
    try:
        from pm_routing import resolve_pm_for_record_async  # noqa: PLC0415
        result = await resolve_pm_for_record_async(
            db, {"project_number": pn}
        )
        assert result is None, (
            "non-primary roster PM must not resolve as the primary"
        )
    finally:
        await _cleanup(db, pn)
