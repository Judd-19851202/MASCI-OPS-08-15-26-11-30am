"""TRACK 15.76 — Platform Trust Spine regression.

Defends the contract: every onboarded workflow emits at least
``record_created`` + ``routing_resolved`` + ``notification_queued``
+ ``audit_written`` events, and the admin observability endpoint
``/api/admin/trust-spine`` returns honest per-workflow lifecycle
health (no fake-green for inactive workflows).
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


@pytest.mark.asyncio
async def test_emit_stage_writes_event():
    """Emitting a stage must produce one trust_spine_events row with
    the documented shape — no PII (no recipient list, no subject)."""
    db = _db()
    from lib.trust_spine import (  # noqa: PLC0415
        emit_stage, new_correlation_id,
        STAGE_RECORD_CREATED, STAGE_ROUTING_RESOLVED,
    )
    cid = new_correlation_id()
    rec_id = f"TRUST-SPINE-15-76-{uuid.uuid4().hex[:8]}"
    await emit_stage(
        db, workflow="daily-report",
        stage=STAGE_RECORD_CREATED, correlation_id=cid,
        record_id=rec_id, project_number="15-76-TEST",
        module="tests/test_track_15_76_trust_spine",
        status="ok",
    )
    await emit_stage(
        db, workflow="daily-report",
        stage=STAGE_ROUTING_RESOLVED, correlation_id=cid,
        record_id=rec_id, project_number="15-76-TEST",
        module="tests/test_track_15_76_trust_spine",
        status="ok",
    )
    try:
        rows = []
        async for r in db.trust_spine_events.find(
            {"correlation_id": cid}, {"_id": 0}, sort=[("ts", 1)]
        ):
            rows.append(r)
        assert len(rows) == 2
        for row in rows:
            assert row["workflow"] == "daily-report"
            assert row["correlation_id"] == cid
            assert row["status"] == "ok"
            assert row["stage"] in {"record_created", "routing_resolved"}
            # PII-free invariants
            for forbidden in ("recipients", "to", "cc", "bcc",
                              "subject", "email", "body"):
                assert forbidden not in row, (
                    f"trust spine row leaked field: {forbidden}"
                )
    finally:
        await db.trust_spine_events.delete_many({"correlation_id": cid})


@pytest.mark.asyncio
async def test_emit_stage_rejects_unknown_stage_and_status():
    """Unknown stage / unknown status MUST be silently dropped
    (logged, not written) so a bad caller can't corrupt the
    Trust Spine."""
    db = _db()
    from lib.trust_spine import emit_stage, new_correlation_id  # noqa: PLC0415
    cid = new_correlation_id()
    # Unknown stage
    await emit_stage(
        db, workflow="daily-report",
        stage="invalid_stage_xxx",
        correlation_id=cid, status="ok",
    )
    # Unknown status
    await emit_stage(
        db, workflow="daily-report",
        stage="record_created",
        correlation_id=cid, status="weirdo",
    )
    try:
        n = await db.trust_spine_events.count_documents(
            {"correlation_id": cid}
        )
        assert n == 0, (
            f"trust spine accepted invalid emissions: {n} rows"
        )
    finally:
        await db.trust_spine_events.delete_many({"correlation_id": cid})


@pytest.mark.asyncio
async def test_trust_spine_endpoint_no_activity_is_amber_not_green():
    """An empty Trust Spine MUST NOT be reported as green.
    Invokes the route handler directly so we don't need a
    live HTTP session token."""
    db = _db()
    from routes.admin_trust_spine import make_router  # noqa: PLC0415

    async def _pass():
        return None
    router = make_router(db, _pass)
    handler = None
    for r in router.routes:
        if getattr(r, "path", "") == "/api/admin/trust-spine":
            handler = r.endpoint
            break
    assert handler is not None
    payload = await handler(_=None)
    assert payload["track"] == "15.76"
    assert "workflows" in payload
    # Any workflow with zero events_24h MUST be amber-no-activity
    for w in payload["workflows"]:
        if w["events_24h"] == 0:
            assert w["band"] == "amber-no-activity"
            assert "no lifecycle events" in w["reason"]


@pytest.mark.asyncio
async def test_trust_spine_endpoint_failure_event_flips_red():
    """A workflow with at least one failed_24h event MUST be flagged
    red by the dashboard."""
    db = _db()
    from lib.trust_spine import emit_stage, new_correlation_id  # noqa: PLC0415
    from routes.admin_trust_spine import make_router  # noqa: PLC0415

    cid = new_correlation_id()
    await emit_stage(
        db, workflow="track-15-76-failure-fixture",
        stage="audit_written",
        correlation_id=cid,
        record_id="fixture-1",
        status="failed",
        failure_reason="synthetic test failure",
    )
    try:
        async def _pass():
            return None
        router = make_router(db, _pass)
        handler = next(
            r.endpoint for r in router.routes
            if getattr(r, "path", "") == "/api/admin/trust-spine"
        )
        payload = await handler(_=None)
        target = next(
            (w for w in payload["workflows"]
             if w["workflow"] == "track-15-76-failure-fixture"),
            None,
        )
        assert target is not None, (
            "failure-fixture workflow should appear in the dashboard"
        )
        assert target["band"] == "red"
        assert target["failed_24h"] >= 1
        assert target["last_failure"] is not None
    finally:
        await db.trust_spine_events.delete_many(
            {"workflow": "track-15-76-failure-fixture"}
        )


@pytest.mark.asyncio
async def test_admin_endpoint_requires_auth():
    """`/api/admin/trust-spine` MUST 401 anonymously."""
    import urllib.request, urllib.error  # noqa: PLC0415
    api_url = (
        open("/app/frontend/.env").read().split("REACT_APP_BACKEND_URL=")[1]
        .split("\n")[0].strip()
    )
    try:
        urllib.request.urlopen(
            f"{api_url}/api/admin/trust-spine", timeout=15
        )
        pytest.fail("anonymous trust-spine GET MUST NOT succeed")
    except urllib.error.HTTPError as exc:
        assert exc.code in (401, 403)
