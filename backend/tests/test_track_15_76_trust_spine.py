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
from datetime import datetime, timedelta, timezone
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
async def test_trust_spine_endpoint_no_evidence_is_amber_not_green():
    """A workflow with no evidence MUST remain amber-no-activity.
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
    no_evidence_rows = [
        w for w in payload["workflows"]
        if w.get("freshness_status") == "unavailable"
    ]
    assert no_evidence_rows, "expected at least one unexercised workflow fixture"
    for w in no_evidence_rows[:5]:
        assert w["band"] == "amber-no-activity"
        assert "no lifecycle evidence" in w["reason"]


@pytest.mark.asyncio
async def test_trust_spine_policy_current_weekly_evidence_can_be_green_without_24h_events():
    """Weekly / event-driven workflows stay green when their most
    recent successful evidence is still inside the governed freshness
    window, even if they emitted nothing in the last 24h."""
    db = _db()
    from routes.admin_trust_spine import make_router  # noqa: PLC0415

    cid = f"trust-policy-{uuid.uuid4().hex[:8]}"
    ts = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
    workflow = "meeting"
    record_id = f"TRUST-POLICY-{uuid.uuid4().hex[:8]}"
    docs = []
    for stage in [
        "record_created",
        "routing_resolved",
        "recipients_built",
        "notification_queued",
        "provider_accepted",
        "audit_written",
        "completed",
    ]:
        docs.append({
            "ts": ts,
            "workflow": workflow,
            "stage": stage,
            "correlation_id": cid,
            "record_id": record_id,
            "project_number": "15-76-POLICY",
            "module": "tests/test_track_15_76_trust_spine",
            "status": "ok",
        })
    await db.trust_spine_events.insert_many(docs)
    try:
        async def _pass():
            return None
        router = make_router(db, _pass)
        handler = next(
            r.endpoint for r in router.routes
            if getattr(r, "path", "") == "/api/admin/trust-spine"
        )
        payload = await handler(_=None)
        target = next(w for w in payload["workflows"] if w["workflow"] == workflow)
        assert target["events_24h"] == 0
        assert target["freshness_status"] == "current"
        assert target["band"] == "green"
        assert target["events_policy_window"] >= 7
    finally:
        await db.trust_spine_events.delete_many({"correlation_id": cid})


@pytest.mark.asyncio
async def test_trust_spine_degraded_component_register_contains_root_cause_fields():
    db = _db()
    from routes.admin_trust_spine import make_router  # noqa: PLC0415

    async def _pass():
        return None
    router = make_router(db, _pass)
    handler = next(
        r.endpoint for r in router.routes
        if getattr(r, "path", "") == "/api/admin/trust-spine"
    )
    payload = await handler(_=None)
    degraded = payload.get("degraded_components") or []
    assert degraded, "expected degraded components while preview evidence remains open"
    row = degraded[0]
    for key in [
        "workflow",
        "source_authority",
        "current_value_state",
        "expected_value_state",
        "freshness",
        "failing_dependency",
        "downstream_impact",
        "c6_c7_c8_c9_impact",
        "operator_data_trustworthy",
        "root_cause",
    ]:
        assert key in row, f"missing {key} in degraded component entry"


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
