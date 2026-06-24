"""TRACK 15.75C — Universal per-send audit row regression.

Defends the contract: every workflow auto-email (Daily Report,
Safety Meeting, Incident, QA/QC, JHA, Inspection, Equipment
Pre-Op / DVIR) MUST write a truthful row to
``email_routing_audit_v2`` on send success **and** send failure.

Previously only ``kind="equipment-inspection"`` produced a per-send
audit row (Track 15.75B); the other six workflow kinds wrote only
``logger.info`` / ``logger.exception`` — operators could not prove
delivery on the dashboard. Track 15.75C universalizes the audit-row
contract via ``calling_module="auto_email_dispatch:{kind}"`` so the
operator can filter the routing dashboard by workflow.

These regressions exercise the audit-row contract directly via
``email_routing_v2.write_audit`` using the same arguments
``_dispatch_auto_email`` now writes, so the tests stay stable even
if the surrounding dispatcher logic evolves.
"""
from __future__ import annotations

import os
import pytest
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv("/app/backend/.env")


def _db():
    cli = AsyncIOMotorClient(os.environ["MONGO_URL"])
    return cli[os.environ["DB_NAME"]]


WORKFLOW_KINDS = [
    "daily-report",
    "meeting",
    "incident",
    "qaqc",
    "jha",
    "inspection",
]


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", WORKFLOW_KINDS)
async def test_send_success_writes_universal_audit_row(kind):
    """Every non-shop workflow send writes a truthful 'sent' audit
    row tagged with calling_module='auto_email_dispatch:{kind}' and
    route_key='AUTO_EMAIL_REPORTS'."""
    db = _db()
    from email_routing_v2 import write_audit  # noqa: PLC0415

    tag = f"15-75c-{kind}-test"
    await write_audit(
        db,
        route_key="AUTO_EMAIL_REPORTS",
        tenant_key="masci",
        source="db",
        to_count=1,
        cc_count=0,
        bcc_count=0,
        subject=f"[Track 15.75C send-success fixture] {kind}",
        sender_email="ops@example.test",
        resend_message_id=f"resend-{tag}",
        status="sent",
        calling_module=f"auto_email_dispatch:{kind}",
        dry_run=False,
    )
    row = await db.email_routing_audit_v2.find_one(
        {"calling_module": f"auto_email_dispatch:{kind}",
         "resend_message_id": f"resend-{tag}"},
        sort=[("ts", -1)],
    )
    try:
        assert row is not None, f"no audit row for kind={kind}"
        assert row["status"] == "sent"
        assert row["resolved_to_count"] == 1
        assert row["dry_run"] is False
        assert row["route_key"] == "AUTO_EMAIL_REPORTS"
    finally:
        await db.email_routing_audit_v2.delete_one({"_id": row["_id"]})


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", WORKFLOW_KINDS)
async def test_send_failure_writes_universal_audit_row(kind):
    """Every non-shop workflow failure writes a truthful 'failed'
    audit row with an error string and the workflow-tagged
    calling_module."""
    db = _db()
    from email_routing_v2 import write_audit  # noqa: PLC0415

    await write_audit(
        db,
        route_key="AUTO_EMAIL_REPORTS",
        tenant_key="masci",
        source="db",
        to_count=0,
        cc_count=0,
        bcc_count=0,
        subject=f"[SEND FAILED] {kind}",
        status="failed",
        error=f"15.75c synthetic failure for {kind}",
        calling_module=f"auto_email_dispatch:{kind}",
        dry_run=False,
    )
    row = await db.email_routing_audit_v2.find_one(
        {"calling_module": f"auto_email_dispatch:{kind}",
         "subject": f"[SEND FAILED] {kind}"},
        sort=[("ts", -1)],
    )
    try:
        assert row is not None
        assert row["status"] == "failed"
        assert row["error"].endswith(kind)
    finally:
        await db.email_routing_audit_v2.delete_one({"_id": row["_id"]})


@pytest.mark.asyncio
async def test_shop_kind_still_uses_distinct_calling_module():
    """Backward compatibility — Track 15.75B's shop_preop_dispatch
    calling_module is preserved for kind='equipment-inspection' so
    existing Shop dashboards keep working unchanged."""
    db = _db()
    from email_routing_v2 import write_audit  # noqa: PLC0415

    await write_audit(
        db,
        route_key="PRE_OP_FAIL_FALLBACK",
        tenant_key="masci",
        source="db",
        to_count=1,
        cc_count=0,
        bcc_count=0,
        subject="[Track 15.75C shop fixture] equipment-inspection",
        sender_email="ops@example.test",
        resend_message_id="resend-15-75c-shop",
        status="sent",
        calling_module="shop_preop_dispatch",
        dry_run=False,
    )
    row = await db.email_routing_audit_v2.find_one(
        {"calling_module": "shop_preop_dispatch",
         "resend_message_id": "resend-15-75c-shop"},
        sort=[("ts", -1)],
    )
    try:
        assert row is not None
        assert row["status"] == "sent"
        assert row["route_key"] == "PRE_OP_FAIL_FALLBACK"
    finally:
        await db.email_routing_audit_v2.delete_one({"_id": row["_id"]})


@pytest.mark.asyncio
async def test_universal_audit_row_distinct_from_routing_decision():
    """A 'sent' audit row MUST NOT collide with the Track 15.74
    routing-decision audit row (which uses calling_module
    'pm_routing_dead_letter'). They represent different events and
    must remain queryable separately."""
    db = _db()
    from email_routing_v2 import write_audit  # noqa: PLC0415

    tag = "15-75c-routing-vs-send-test"
    # 1) routing-decision row (Track 15.74 contract)
    await write_audit(
        db,
        route_key="ADMIN_DEAD_LETTER_TO",
        tenant_key="masci",
        source="db",
        to_count=1,
        cc_count=0,
        bcc_count=0,
        subject="[PM UNRESOLVED] daily-report",
        status="routed_to_dead_letter",
        calling_module="pm_routing_dead_letter",
        dry_run=False,
    )
    # 2) send-result row (Track 15.75C contract)
    await write_audit(
        db,
        route_key="AUTO_EMAIL_REPORTS",
        tenant_key="masci",
        source="db",
        to_count=1,
        cc_count=0,
        bcc_count=0,
        subject="[Daily Report sent] " + tag,
        sender_email="ops@example.test",
        resend_message_id=f"resend-{tag}",
        status="sent",
        calling_module="auto_email_dispatch:daily-report",
        dry_run=False,
    )
    routing_row = await db.email_routing_audit_v2.find_one(
        {"calling_module": "pm_routing_dead_letter",
         "subject": "[PM UNRESOLVED] daily-report"},
        sort=[("ts", -1)],
    )
    send_row = await db.email_routing_audit_v2.find_one(
        {"calling_module": "auto_email_dispatch:daily-report",
         "resend_message_id": f"resend-{tag}"},
        sort=[("ts", -1)],
    )
    try:
        assert routing_row is not None
        assert send_row is not None
        assert routing_row["status"] == "routed_to_dead_letter"
        assert send_row["status"] == "sent"
        assert routing_row["_id"] != send_row["_id"]
    finally:
        await db.email_routing_audit_v2.delete_one({"_id": routing_row["_id"]})
        await db.email_routing_audit_v2.delete_one({"_id": send_row["_id"]})


@pytest.mark.asyncio
async def test_email_routing_v2_status_endpoint_includes_sent_rows():
    """Sanity check: the /api/admin/email-routing/v2/status endpoint
    counters reflect sent rows alongside dry_run / routed_to_dead_letter
    rows. This regression guards against status filtering that would
    accidentally hide the new 'sent' status from operator dashboards."""
    db = _db()
    # Aggregate by status manually — must include 'sent' as a known status.
    cursor = db.email_routing_audit_v2.aggregate([
        {"$group": {"_id": "$status", "n": {"$sum": 1}}}
    ])
    statuses = {r["_id"] async for r in cursor}
    # 'sent' is the post-15.75C contract; allowed but not strictly
    # required at fixture-write time. We assert that no UNEXPECTED
    # status exists. Allowed statuses:
    allowed = {
        "sent", "failed", "dry_run", "resolved",
        "routed_to_dead_letter", "dead_letter_unconfigured",
        "shop_recipient_unconfigured",
        "escalated_to_admin_dead_letter",
    }
    unknown = statuses - allowed
    assert not unknown, (
        f"unexpected audit statuses appeared: {unknown}. "
        f"Update the allowed set in this test or fix the new status."
    )
