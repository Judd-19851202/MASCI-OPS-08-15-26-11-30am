from __future__ import annotations

import os
import uuid

import pytest
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv("/app/backend/.env")


def _db():
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    return client[os.environ["DB_NAME"]]


def _route_handler(router, path: str):
    return next(r.endpoint for r in router.routes if getattr(r, "path", "") == path)


@pytest.mark.asyncio
async def test_trust_spine_complete_evidence_maps_to_validated(monkeypatch):
    db = _db()
    from lib.trust_spine import attach_correlation, emit_workflow_stage
    import routes.admin_trust_spine as trust_spine_module

    workflow = f"cp6-complete-{uuid.uuid4().hex[:6]}"
    monkeypatch.setattr(trust_spine_module, "WORKFLOW_EXPECTED_STAGES", {workflow: ["record_created", "routing_resolved", "completed"]})

    record = {"id": f"rec-{uuid.uuid4().hex[:6]}"}
    attach_correlation(record)
    for stage in ["record_created", "routing_resolved", "completed"]:
        await emit_workflow_stage(db, workflow=workflow, stage=stage, record=record, module="tests", status="ok")

    try:
        async def _pass():
            return None

        router = trust_spine_module.make_router(db, _pass)
        payload = await _route_handler(router, "/api/admin/trust-spine")(_=None)
        row = next(w for w in payload["workflows"] if w["workflow"] == workflow)
        assert row["band"] == "green"
        assert row["ots_truth"]["permitted_claim"] == "VALIDATED"
        assert row["ots_truth"]["claim_ceiling"] == "VALIDATED"
        assert row["ots_truth"]["audit_reference"] == "OTS-C6-TRUST-SPINE-WORKFLOW"
        assert payload["ots_truth"]["permitted_claim"] == "VALIDATED"
        assert payload["compatibility"]["breaking_api_changes"] == 0
    finally:
        await db.trust_spine_events.delete_many({"correlation_id": record["_trust_cid"]})


@pytest.mark.asyncio
async def test_trust_spine_partial_evidence_maps_to_verified(monkeypatch):
    db = _db()
    from lib.trust_spine import attach_correlation, emit_workflow_stage
    import routes.admin_trust_spine as trust_spine_module

    workflow = f"cp6-partial-{uuid.uuid4().hex[:6]}"
    monkeypatch.setattr(trust_spine_module, "WORKFLOW_EXPECTED_STAGES", {workflow: ["record_created", "routing_resolved", "completed"]})

    record = {"id": f"rec-{uuid.uuid4().hex[:6]}"}
    attach_correlation(record)
    for stage in ["record_created", "routing_resolved"]:
        await emit_workflow_stage(db, workflow=workflow, stage=stage, record=record, module="tests", status="ok")

    try:
        async def _pass():
            return None

        router = trust_spine_module.make_router(db, _pass)
        payload = await _route_handler(router, "/api/admin/trust-spine")(_=None)
        row = next(w for w in payload["workflows"] if w["workflow"] == workflow)
        assert row["band"] == "amber"
        assert row["ots_truth"]["permitted_claim"] == "VERIFIED"
        assert row["ots_truth"]["truth_evaluation"] == "DEGRADED"
        assert row["ots_truth"]["unknowns"]
        assert payload["ots_truth"]["permitted_claim"] == "VERIFIED"
    finally:
        await db.trust_spine_events.delete_many({"correlation_id": record["_trust_cid"]})


@pytest.mark.asyncio
async def test_trust_spine_missing_or_stale_evidence_maps_to_observed(monkeypatch):
    db = _db()
    import routes.admin_trust_spine as trust_spine_module

    workflow = f"cp6-stale-{uuid.uuid4().hex[:6]}"
    monkeypatch.setattr(trust_spine_module, "WORKFLOW_EXPECTED_STAGES", {workflow: ["record_created", "completed"]})

    stale_cid = f"cp6-stale-cid-{uuid.uuid4().hex[:6]}"
    await db.trust_spine_events.insert_one({
        "workflow": workflow,
        "stage": "record_created",
        "status": "ok",
        "correlation_id": stale_cid,
        "module": "tests",
        "record_id": "stale-row",
        "ts": "2020-01-01T00:00:00+00:00",
    })

    try:
        async def _pass():
            return None

        router = trust_spine_module.make_router(db, _pass)
        payload = await _route_handler(router, "/api/admin/trust-spine")(_=None)
        row = next(w for w in payload["workflows"] if w["workflow"] == workflow)
        assert row["band"] == "amber-no-activity"
        assert row["ots_truth"]["permitted_claim"] == "OBSERVED"
        assert row["ots_truth"]["evidence_state"] == "stale"
        assert row["ots_truth"]["unknowns"]
    finally:
        await db.trust_spine_events.delete_many({"correlation_id": stale_cid})


@pytest.mark.asyncio
async def test_trust_spine_contradictions_downgrade_claim(monkeypatch):
    db = _db()
    from lib.trust_spine import attach_correlation, emit_workflow_stage
    import routes.admin_trust_spine as trust_spine_module

    monkeypatch.setattr(trust_spine_module, "WORKFLOW_EXPECTED_STAGES", {"daily-report": ["record_created", "routing_resolved"]})

    record = {"id": f"rec-{uuid.uuid4().hex[:6]}", "project_number": "CP6-CONTRADICTION"}
    attach_correlation(record)
    for stage in [
        "record_created",
        "routing_resolved",
        "recipients_built",
        "notification_queued",
        "audit_written",
        "provider_accepted",
        "delivery_captured_preview",
    ]:
        await emit_workflow_stage(db, workflow="daily-report", stage=stage, record=record, module="tests", status="ok")

    try:
        async def _pass():
            return None

        router = trust_spine_module.make_router(db, _pass)
        payload = await _route_handler(router, "/api/admin/trust-spine")(_=None)
        row = next(w for w in payload["workflows"] if w["workflow"] == "daily-report")
        assert row["ots_truth"]["permitted_claim"] == "CORRELATED"
        assert row["ots_truth"]["contradictory_evidence"]
        assert payload["ots_truth"]["contradictory_evidence"]
        assert payload["ots_truth"]["permitted_claim"] == "CORRELATED"
        assert payload["truth_relationship"]["has_conflict"] is True
    finally:
        await db.trust_spine_events.delete_many({"correlation_id": record["_trust_cid"]})


@pytest.mark.asyncio
async def test_trust_spine_preserves_legacy_fields_and_adds_ots(monkeypatch):
    db = _db()
    import routes.admin_trust_spine as trust_spine_module

    workflow = f"cp6-preserve-{uuid.uuid4().hex[:6]}"
    monkeypatch.setattr(trust_spine_module, "WORKFLOW_EXPECTED_STAGES", {workflow: ["record_created"]})

    async def _pass():
        return None

    router = trust_spine_module.make_router(db, _pass)
    payload = await _route_handler(router, "/api/admin/trust-spine")(_=None)
    for field in [
        "track",
        "generated_at",
        "platform_band",
        "canonical_status",
        "truth_surface",
        "truth_relationship",
        "total_events_24h",
        "total_failed_24h",
        "workflow_count",
        "workflows",
        "allowed_stages",
        "ots_truth",
        "compatibility",
    ]:
        assert field in payload
    assert payload["compatibility"]["preserved_fields"] == 11
    assert payload["compatibility"]["new_additive_fields"] == 2
    assert payload["compatibility"]["breaking_api_changes"] == 0
    row = next(w for w in payload["workflows"] if w["workflow"] == workflow)
    assert "ots_truth" in row
    assert "truth_relationship" in row
