from __future__ import annotations

from datetime import datetime, timedelta, timezone
import sys

import pytest

sys.path.insert(0, "/app/backend")


@pytest.mark.asyncio
async def test_blocked_workflow_surfaces_block_reason_and_remediation(monkeypatch):
    import lib.production_certification as pc  # noqa: PLC0415

    now = datetime.now(timezone.utc)
    older = (now - timedelta(hours=3)).isoformat()
    newer = (now - timedelta(hours=1)).isoformat()

    monkeypatch.setattr(pc, "WORKFLOW_EXPECTED_STAGES", {"jha": ["submitted", "completed"]})

    async def _latest_terminal_success(_db, workflow, status=None):
        assert workflow == "jha"
        if status == "ok":
            return {"ts": older, "status": "ok", "correlation_id": "cid-ok", "record_id": "rec-ok"}
        if status == "failed":
            return None
        return {"ts": older, "status": "ok", "correlation_id": "cid-ok", "record_id": "rec-ok"}

    async def _latest_any_event(_db, workflow):
        assert workflow == "jha"
        return {
            "ts": newer,
            "status": "skipped",
            "stage": "notification_queued",
            "correlation_id": "cid-blocked",
            "record_id": "rec-blocked",
            "failure_reason": "email_safety_mode:strict",
            "remediation": "governance restriction in certification mode",
        }

    async def _count_completed(_db, workflow, status):
        assert workflow == "jha"
        return 1 if status == "ok" else 0

    async def _first_completed_ok(_db, workflow):
        assert workflow == "jha"
        return {"ts": older, "correlation_id": "cid-ok", "record_id": "rec-ok"}

    monkeypatch.setattr(pc, "_latest_terminal_success", _latest_terminal_success)
    monkeypatch.setattr(pc, "_latest_any_event", _latest_any_event)
    monkeypatch.setattr(pc, "_count_completed", _count_completed)
    monkeypatch.setattr(pc, "_first_completed_ok", _first_completed_ok)
    async def _audit_row(_db, _cid):
        return None

    monkeypatch.setattr(pc, "_audit_row_for_correlation", _audit_row)

    out = await pc.build_certification(object())
    row = out["workflows"][0]

    assert row["status"] == pc.STATUS_BLOCKED
    assert row["last_failure_reason"] == "email_safety_mode:strict"
    assert row["operator_remediation"] == "Complete the blocked dependency or governance prerequisite, then rerun the workflow."
    assert row["engineering_remediation"] == "Ensure the workflow can emit a canonical completed event once its blocker clears."
    assert row["evidence_age_hours"] is not None


@pytest.mark.asyncio
async def test_stale_workflow_isolated_from_runtime_dataset(monkeypatch):
    import lib.production_certification as pc  # noqa: PLC0415

    stale_ts = (datetime.now(timezone.utc) - timedelta(hours=pc.WORKFLOW_CERTIFICATION_POLICIES["dvir"].stale_threshold_hours + 2)).isoformat()

    monkeypatch.setattr(pc, "WORKFLOW_EXPECTED_STAGES", {"dvir": ["submitted", "completed"]})

    async def _latest_terminal_success(_db, workflow, status=None):
        assert workflow == "dvir"
        if status == "failed":
            return None
        return {"ts": stale_ts, "status": "ok", "correlation_id": "cid-stale", "record_id": "rec-stale"}

    async def _latest_any_event(_db, workflow):
        assert workflow == "dvir"
        return {"ts": stale_ts, "status": "ok", "stage": "completed", "correlation_id": "cid-stale", "record_id": "rec-stale"}

    async def _count_completed(_db, workflow, status):
        assert workflow == "dvir"
        return 1 if status == "ok" else 0

    async def _first_completed_ok(_db, workflow):
        assert workflow == "dvir"
        return {"ts": stale_ts, "correlation_id": "cid-stale", "record_id": "rec-stale"}

    monkeypatch.setattr(pc, "_latest_terminal_success", _latest_terminal_success)
    monkeypatch.setattr(pc, "_latest_any_event", _latest_any_event)
    monkeypatch.setattr(pc, "_count_completed", _count_completed)
    monkeypatch.setattr(pc, "_first_completed_ok", _first_completed_ok)
    async def _audit_row(_db, _cid):
        return None

    monkeypatch.setattr(pc, "_audit_row_for_correlation", _audit_row)

    out = await pc.build_certification(object())
    row = out["workflows"][0]

    assert row["status"] == pc.STATUS_STALE
    assert row["last_verified_at"] == stale_ts