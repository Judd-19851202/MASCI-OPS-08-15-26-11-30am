"""TRACK 15.76 · Platform Trust Spine — extended regression.

Defends the contracts introduced when onboarding every operational
workflow (daily-report, meeting, jha, incident, inspection, qaqc,
equipment-inspection, dvir, hr-request, dispatch-assignment,
shop-defect):

1. ``emit_record_created`` / ``emit_workflow_stage`` thread the same
   correlation_id when the same record dict is reused.
2. Missing-stage detection — a workflow with events but missing one
   or more expected stages must be AMBER, not green (no fake green).
3. The drill-in endpoint returns the latest events for a workflow
   sorted newest-first and includes the expected_stages contract.
4. The universal dispatcher (audit_written) uses the threaded
   correlation_id, not a fresh one per call.
5. Every workflow declared in WORKFLOW_EXPECTED_STAGES is rendered
   in the dashboard payload, even when idle (so the operator sees
   AMBER-NO-ACTIVITY instead of a silent omission).
"""
from __future__ import annotations

import asyncio
import os
import uuid

import pytest
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv("/app/backend/.env")


def _db():
    cli = AsyncIOMotorClient(os.environ["MONGO_URL"])
    return cli[os.environ["DB_NAME"]]


@pytest.mark.asyncio
async def test_record_helpers_thread_correlation_id():
    """Submitting the same ``record`` through emit_record_created
    then emit_workflow_stage must reuse one correlation_id —
    proving the dashboard can trace a record end-to-end."""
    db = _db()
    from lib.trust_spine import (  # noqa: PLC0415
        emit_record_created, emit_workflow_stage,
        STAGE_ROUTING_RESOLVED, STAGE_COMPLETED,
    )
    record = {"id": f"thread-{uuid.uuid4().hex[:8]}",
              "project_number": "15-76-THREAD"}
    workflow = f"track-15-76-thread-{uuid.uuid4().hex[:6]}"
    try:
        await emit_record_created(
            db, workflow=workflow, record=record, module="tests",
        )
        await emit_workflow_stage(
            db, workflow=workflow, stage=STAGE_ROUTING_RESOLVED,
            record=record, module="tests", status="ok",
        )
        await emit_workflow_stage(
            db, workflow=workflow, stage=STAGE_COMPLETED,
            record=record, module="tests", status="ok",
        )
        cids = set()
        async for r in db.trust_spine_events.find(
            {"workflow": workflow}, {"_id": 0, "correlation_id": 1}
        ):
            cids.add(r["correlation_id"])
        assert len(cids) == 1, (
            f"correlation_id was not threaded across stages: {cids}"
        )
        # And that single cid must equal what was attached to record.
        assert record.get("_trust_cid") in cids
    finally:
        await db.trust_spine_events.delete_many({"workflow": workflow})


@pytest.mark.asyncio
async def test_missing_expected_stage_is_amber_not_green():
    """If a workflow emits events but misses one of its expected
    stages, the dashboard MUST band it AMBER with a missing-stage
    reason. No fake green."""
    db = _db()
    from lib.trust_spine import (  # noqa: PLC0415
        emit_workflow_stage, attach_correlation,
        STAGE_RECORD_CREATED, STAGE_ROUTING_RESOLVED,
        WORKFLOW_EXPECTED_STAGES,
    )
    from routes.admin_trust_spine import make_router  # noqa: PLC0415

    # Use a known workflow with a long expected contract.
    wf = "daily-report"
    cid_record = {"id": f"missing-{uuid.uuid4().hex[:8]}",
                  "project_number": "15-76-MISS"}
    attach_correlation(cid_record)
    # Emit only 2 of the 7 expected stages.
    await emit_workflow_stage(
        db, workflow=wf, stage=STAGE_RECORD_CREATED,
        record=cid_record, module="tests", status="ok",
    )
    await emit_workflow_stage(
        db, workflow=wf, stage=STAGE_ROUTING_RESOLVED,
        record=cid_record, module="tests", status="ok",
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
        row = next(
            (w for w in payload["workflows"] if w["workflow"] == wf), None
        )
        assert row is not None
        # The full contract has 7 stages; we emitted 2.
        assert len(row["missing_stages"]) >= 1
        # If there is any other 24h failure for daily-report in the live
        # DB the band may be red — but partial evidence alone must NEVER
        # be green.
        assert row["band"] in {"amber", "red"}, (
            f"missing-stage workflow returned band={row['band']}, "
            "expected amber (or red if other failures present); "
            "fake-green violation"
        )
        assert WORKFLOW_EXPECTED_STAGES[wf] == row["expected_stages"]
    finally:
        await db.trust_spine_events.delete_many(
            {"correlation_id": cid_record["_trust_cid"]}
        )


@pytest.mark.asyncio
async def test_drilldown_endpoint_returns_recent_events():
    """The drill-in endpoint must return the per-workflow events
    sorted newest-first and include the expected_stages contract."""
    db = _db()
    from lib.trust_spine import emit_workflow_stage, attach_correlation  # noqa: PLC0415
    from routes.admin_trust_spine import make_router  # noqa: PLC0415

    wf = f"track-15-76-drill-{uuid.uuid4().hex[:6]}"
    rec = {"id": "drill-1"}
    attach_correlation(rec)
    for stg in ("record_created", "routing_resolved", "completed"):
        await emit_workflow_stage(
            db, workflow=wf, stage=stg, record=rec, module="tests", status="ok",
        )
        await asyncio.sleep(0.01)
    try:
        async def _pass():
            return None
        router = make_router(db, _pass)
        handler = next(
            r.endpoint for r in router.routes
            if getattr(r, "path", "")
            == "/api/admin/trust-spine/workflow/{workflow}"
        )
        payload = await handler(workflow=wf, limit=10, _=None)
        assert payload["workflow"] == wf
        assert payload["count"] == 3
        # Newest first
        assert payload["events"][0]["stage"] == "completed"
        assert payload["events"][-1]["stage"] == "record_created"
        # expected_stages key always present (empty list for ad-hoc workflows).
        assert "expected_stages" in payload
    finally:
        await db.trust_spine_events.delete_many({"workflow": wf})


@pytest.mark.asyncio
async def test_every_declared_workflow_is_in_dashboard():
    """Every workflow declared in WORKFLOW_EXPECTED_STAGES must appear
    in the dashboard payload — even when idle — so the operator can
    see it as AMBER-NO-ACTIVITY instead of missing entirely."""
    db = _db()
    from lib.trust_spine import WORKFLOW_EXPECTED_STAGES  # noqa: PLC0415
    from routes.admin_trust_spine import make_router  # noqa: PLC0415

    async def _pass():
        return None
    router = make_router(db, _pass)
    handler = next(
        r.endpoint for r in router.routes
        if getattr(r, "path", "") == "/api/admin/trust-spine"
    )
    payload = await handler(_=None)
    rendered = {w["workflow"] for w in payload["workflows"]}
    for declared in WORKFLOW_EXPECTED_STAGES.keys():
        assert declared in rendered, (
            f"workflow {declared!r} declared in expected-stages contract "
            "but missing from dashboard payload"
        )


@pytest.mark.asyncio
async def test_universal_dispatcher_threads_cid_for_audit_written():
    """The universal email dispatcher must call ``emit_workflow_stage``
    (which threads the cid from ``record``) rather than minting a new
    cid for audit_written. This test enforces that contract by
    grepping the dispatcher source."""
    src = open("/app/backend/server.py").read()
    # The old bug: a fresh cid for audit_written. Must be gone.
    bad = "STAGE_AUDIT_WRITTEN" in src and (
        "stage=STAGE_AUDIT_WRITTEN" in src
        and "correlation_id=new_correlation_id()" in src.split("STAGE_AUDIT_WRITTEN", 1)[1].split("\n\n", 1)[0]
    )
    assert not bad, (
        "dispatcher still issues a new correlation_id for "
        "audit_written — Trust Spine lifecycle is no longer threadable"
    )
    # And the new emit_workflow_stage helper must be wired in.
    assert "emit_workflow_stage" in src, (
        "_dispatch_auto_email must use emit_workflow_stage to thread "
        "correlation_id through the lifecycle"
    )
