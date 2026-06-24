"""TRACK 15.74 — Phase 4 (Notification Trust) P1 regression test.

Defends the **dead-letter routing audit trust fix**: when a PM event
falls through to ADMIN_DEAD_LETTER_TO, the
``email_routing_audit_v2`` row MUST reflect the actual number of
resolved dead-letter recipients (not a hardcoded ``to_count=0``)
and MUST NOT label the row as a dry-run when an email was actually
routed.

Before this fix the audit row always read::

    {"resolved_to_count": 0, "status": "dry_run", "dry_run": true}

…which made operator dashboards lie: ``safety@mascigc.com`` was
being notified about every unresolved PM event in production, but
the routing audit looked like a silent drop. This violated the
"no silent failures" + "audit must tell the truth" rules of the
Track 15.74 platform certification.
"""
from __future__ import annotations

import os
import asyncio
import pytest
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv("/app/backend/.env")


def _db():
    cli = AsyncIOMotorClient(os.environ["MONGO_URL"])
    return cli[os.environ["DB_NAME"]]


@pytest.mark.asyncio
async def test_dead_letter_audit_records_actual_recipient_count():
    """When a meeting is routed without a PM, the audit row MUST carry
    the actual count of dead-letter recipients — not zero — and MUST
    NOT be marked as a dry-run (it represents a real routing
    decision, not a simulation)."""
    db = _db()
    from pm_routing import _audit_dead_letter  # noqa: PLC0415

    fake_recipients = ["safety@example.test", "ops@example.test"]
    await _audit_dead_letter(
        db,
        kind="meeting",
        record={"project_number": "TEST-15-74", "project_name": "Track 15.74 fixture"},
        reason="no_primary_pm",
        dead_letter_to=fake_recipients,
        dead_letter_cc=[],
    )

    # Look up the row we just wrote.
    row = await db.email_routing_audit_v2.find_one(
        {"route_key": "ADMIN_DEAD_LETTER_TO",
         "subject": "[PM UNRESOLVED] meeting",
         "calling_module": "pm_routing_dead_letter"},
        sort=[("ts", -1)],
    )
    assert row is not None, "dead-letter audit row was not written"
    try:
        assert row["resolved_to_count"] == len(fake_recipients), (
            f"audit must report actual recipient count, got "
            f"{row.get('resolved_to_count')}"
        )
        assert row["status"] == "routed_to_dead_letter", (
            f"status should be routed_to_dead_letter when recipients exist, "
            f"got {row.get('status')}"
        )
        assert row["dry_run"] is False, (
            "dead-letter routing audit is a real decision row, not a dry-run"
        )
    finally:
        # Clean up the synthetic audit row so we don't pollute observability.
        await db.email_routing_audit_v2.delete_one({"_id": row["_id"]})
        await db.platform_audit.delete_many({
            "event": "pm_unresolved_dead_letter",
            "project_number": "TEST-15-74",
        })


@pytest.mark.asyncio
async def test_dead_letter_audit_flags_unconfigured_when_no_recipients():
    """When ADMIN_DEAD_LETTER_TO is also unconfigured (no env, no DB
    override), the audit row MUST flag that state explicitly via
    ``status='dead_letter_unconfigured'`` so the operator
    dashboard surfaces a true P0 silent-drop risk instead of a
    look-alike ok row."""
    db = _db()
    from pm_routing import _audit_dead_letter  # noqa: PLC0415

    await _audit_dead_letter(
        db,
        kind="daily_report",
        record={"project_number": "TEST-15-74-UNCFG",
                "project_name": "unconfigured fixture"},
        reason="no_primary_pm",
        dead_letter_to=[],
        dead_letter_cc=[],
    )

    row = await db.email_routing_audit_v2.find_one(
        {"route_key": "ADMIN_DEAD_LETTER_TO",
         "subject": "[PM UNRESOLVED] daily_report",
         "calling_module": "pm_routing_dead_letter"},
        sort=[("ts", -1)],
    )
    assert row is not None
    try:
        assert row["resolved_to_count"] == 0
        assert row["status"] == "dead_letter_unconfigured", (
            "unconfigured dead-letter must be flagged explicitly, not "
            "rendered as a normal dry_run"
        )
        # platform_audit row carries the same truth
        pa = await db.platform_audit.find_one(
            {"event": "pm_unresolved_dead_letter",
             "project_number": "TEST-15-74-UNCFG"},
            sort=[("ts", -1)],
        )
        assert pa is not None
        assert pa["dead_letter_configured"] is False
        assert pa["dead_letter_to_count"] == 0
    finally:
        await db.email_routing_audit_v2.delete_one({"_id": row["_id"]})
        await db.platform_audit.delete_many({
            "event": "pm_unresolved_dead_letter",
            "project_number": "TEST-15-74-UNCFG",
        })
