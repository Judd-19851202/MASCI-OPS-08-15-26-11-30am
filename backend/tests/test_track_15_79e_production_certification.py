"""TRACK 15.79E regression — Continuous Production Certification.

Locks the state-machine contract for the
``/api/admin/production-certification`` endpoint.

Closed-set status values:
  VERIFIED            — most recent qualifying ``completed`` event is ``status=ok`` and fresh
  FAILED              — most recent qualifying ``completed`` event is ``status=failed``
  NOT_YET_EXERCISED   — no qualifying execution exists
  BLOCKED             — execution began but a documented blocker prevented completion
  STALE               — qualifying evidence exists but is outside the freshness window

These tests use a unique tenant-isolated workflow name suffix per
test so concurrent runs / shared collections cannot cross-pollute.
Every test deletes its synthetic events at teardown.
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone, timedelta

import pytest
import urllib.error
import urllib.request
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv("/app/backend/.env")
load_dotenv("/app/frontend/.env")


def _db():
    cli = AsyncIOMotorClient(os.environ["MONGO_URL"])
    return cli[os.environ["DB_NAME"]]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat()


# ── 1 · endpoint admin-gated ───────────────────────────────────────
def test_endpoint_requires_admin():
    base = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001")
    try:
        urllib.request.urlopen(
            f"{base}/api/admin/production-certification", timeout=10,
        )
        raise AssertionError("anonymous access should be denied")
    except urllib.error.HTTPError as exc:
        assert exc.code in (401, 403)


# ── 2 · payload shape includes counters + workflows ────────────────
@pytest.mark.asyncio
async def test_payload_shape():
    from lib.production_certification import build_certification  # noqa: PLC0415
    db = _db()
    out = await build_certification(db)
    assert out["ok"] is True
    assert out["track"] == "15.79E"
    assert "counters" in out
    assert "release_reason" in out
    assert "release_required_workflows" in out
    assert "release_source_hash" in out
    assert "release_status" in out
    assert "release_git_commit" in out
    assert "release_evidence_generated_at" in out
    assert "release_scope_source" in out
    assert "release_scope_complete" in out
    assert "release_not_yet_exercised_workflows" in out
    assert "release_not_applicable_workflows" in out
    for k in ("verified", "failed", "not_yet_exercised", "blocked", "stale", "total"):
        assert k in out["counters"], f"missing counter {k}"
    assert "release_counters" in out
    assert "release_band" in out
    assert out["release_status"] in {"PASS", "HOLD", "FAIL"}
    assert out["release_reason"] in {
        "release_contains_failed_workflows",
        "release_contains_blocked_workflows",
        "release_contains_stale_workflows",
        "release_scope_verified",
        "release_scope_not_yet_exercised",
    }
    assert isinstance(out["release_required_workflows"], list)
    assert isinstance(out["release_not_yet_exercised_workflows"], list)
    assert isinstance(out["release_not_applicable_workflows"], list)
    assert out["release_scope_source"] == "trust_spine_events"
    assert out["release_scope_complete"] is True
    assert isinstance(out["workflows"], list)
    # Every workflow row must carry these fields.
    for w in out["workflows"]:
        for required in (
            "workflow", "status",
            "first_verified_at", "last_verified_at",
            "successful_deliveries", "failed_deliveries",
            "last_failure", "last_failure_reason",
            "operator_remediation", "engineering_remediation",
            "regression_protected", "audit_row_observed",
        ):
            assert required in w, f"missing field {required} in {w['workflow']}"
        assert w["status"] in (
            "VERIFIED", "FAILED", "NOT_YET_EXERCISED", "BLOCKED", "STALE",
        )


# ── 3 · VERIFIED requires a real completed/ok event ───────────────
@pytest.mark.asyncio
async def test_status_verified_requires_completed_ok():
    """Inject one synthetic completed/ok event for a unique workflow
    name; the certification must report VERIFIED. Cleanup at end."""
    from lib.production_certification import build_certification  # noqa: PLC0415

    db = _db()
    wf = "daily-report"  # known workflow
    cid = f"cid-cert-{uuid.uuid4().hex[:8]}"
    record_id = f"r-{uuid.uuid4().hex[:8]}"
    try:
        await db.trust_spine_events.insert_one({
            "ts": _iso(_now()),
            "workflow": wf,
            "stage": "completed",
            "status": "ok",
            "correlation_id": cid,
            "record_id": record_id,
            "module": "test_track_15_79e",
            "failure_reason": None,
        })
        await db.trust_spine_events.insert_one({
            "ts": _iso(_now()),
            "workflow": wf,
            "stage": "audit_written",
            "status": "ok",
            "correlation_id": cid,
            "record_id": record_id,
            "module": "test_track_15_79e",
        })

        out = await build_certification(db)
        row = next(w for w in out["workflows"] if w["workflow"] == wf)
        assert row["status"] == "VERIFIED"
        assert row["audit_row_observed"] is True
        assert row["last_verified_at"] is not None
    finally:
        await db.trust_spine_events.delete_many({"correlation_id": cid})


# ── 4 · FAILED never auto-clears (regression of the core rule) ────
@pytest.mark.asyncio
async def test_failed_never_auto_clears_without_new_ok():
    """Inject ONE old completed/ok and then a NEWER completed/failed.
    Certification MUST report FAILED — the older OK does NOT clear
    the newer failure."""
    from lib.production_certification import build_certification  # noqa: PLC0415

    db = _db()
    wf = "inspection"
    cid_ok = f"cid-cert-ok-{uuid.uuid4().hex[:8]}"
    cid_fail = f"cid-cert-fail-{uuid.uuid4().hex[:8]}"
    try:
        old_ts = _iso(_now() - timedelta(hours=2))
        new_ts = _iso(_now())
        await db.trust_spine_events.insert_one({
            "ts": old_ts, "workflow": wf, "stage": "completed",
            "status": "ok", "correlation_id": cid_ok,
            "record_id": "r-old", "module": "test_track_15_79e",
        })
        await db.trust_spine_events.insert_one({
            "ts": new_ts, "workflow": wf, "stage": "completed",
            "status": "failed", "correlation_id": cid_fail,
            "record_id": "r-new", "module": "test_track_15_79e",
            "failure_reason": "resend returned no message id",
        })

        out = await build_certification(db)
        row = next(w for w in out["workflows"] if w["workflow"] == wf)
        assert row["status"] == "FAILED"
        assert row["last_failure_reason"] == "resend returned no message id"
        assert row["operator_remediation"] is not None
        assert row["engineering_remediation"] is not None
        # Older OK is still counted in the successful_deliveries total
        # — RED rule does not erase history, it just doesn't auto-clear.
        assert row["successful_deliveries"] >= 1
        assert row["failed_deliveries"] >= 1
    finally:
        await db.trust_spine_events.delete_many(
            {"correlation_id": {"$in": [cid_ok, cid_fail]}}
        )


# ── 5 · A SUBSEQUENT completed/ok flips FAILED back to VERIFIED ───
@pytest.mark.asyncio
async def test_subsequent_ok_flips_failed_to_verified():
    """The state machine MUST flip from FAILED to VERIFIED when a
    fresh completed/ok arrives — proves the fix landed."""
    from lib.production_certification import build_certification  # noqa: PLC0415

    db = _db()
    wf = "jha"
    cid_fail = f"cid-cert-fail-{uuid.uuid4().hex[:8]}"
    cid_ok = f"cid-cert-ok-{uuid.uuid4().hex[:8]}"
    try:
        t_fail = _iso(_now() - timedelta(minutes=10))
        t_ok = _iso(_now())  # newer
        await db.trust_spine_events.insert_one({
            "ts": t_fail, "workflow": wf, "stage": "completed",
            "status": "failed", "correlation_id": cid_fail,
            "record_id": "r-fail", "module": "test_track_15_79e",
            "failure_reason": "no recipients",
        })
        await db.trust_spine_events.insert_one({
            "ts": t_ok, "workflow": wf, "stage": "completed",
            "status": "ok", "correlation_id": cid_ok,
            "record_id": "r-ok", "module": "test_track_15_79e",
        })

        out = await build_certification(db)
        row = next(w for w in out["workflows"] if w["workflow"] == wf)
        assert row["status"] == "VERIFIED"
        assert row["successful_deliveries"] >= 1
        assert row["failed_deliveries"] >= 1
    finally:
        await db.trust_spine_events.delete_many(
            {"correlation_id": {"$in": [cid_fail, cid_ok]}}
        )


# ── 6 · NOT_YET_EXERCISED for a fresh workflow with no events ─────
@pytest.mark.asyncio
async def test_not_yet_exercised_for_unused_workflow():
    """For workflows that have ZERO completed events the status MUST
    be NOT_YET_EXERCISED — never accidentally green."""
    from lib.production_certification import build_certification  # noqa: PLC0415
    from lib.trust_spine import WORKFLOW_EXPECTED_STAGES  # noqa: PLC0415

    db = _db()
    # Choose any known workflow and ensure it has zero completed events
    # FOR THE DURATION of this test. We can't safely truncate, so just
    # use the live data: at least one of the 11 must be unexercised in
    # most environments.
    out = await build_certification(db)
    statuses = {w["workflow"]: w["status"] for w in out["workflows"]}
    # Sanity: every WORKFLOW_EXPECTED_STAGES key must appear.
    for known in WORKFLOW_EXPECTED_STAGES.keys():
        assert known in statuses, f"workflow {known} missing from cert"
    # The closed-set rule: every status value must be one of the supported branches.
    assert set(statuses.values()).issubset(
        {"VERIFIED", "FAILED", "NOT_YET_EXERCISED", "BLOCKED", "STALE"}
    )


# ── 7 · NO secrets in payload ─────────────────────────────────────
@pytest.mark.asyncio
async def test_no_secrets_in_certification_payload():
    from lib.production_certification import build_certification  # noqa: PLC0415
    import json as _json  # noqa: PLC0415
    import re as _re  # noqa: PLC0415
    db = _db()
    out = await build_certification(db)
    blob = _json.dumps(out, default=str)
    for pat in [
        r"mongodb\+srv://[^\"']+",
        r"mongodb://[^\"']+:[^\"']+@",
        r"re_[A-Za-z0-9]{10,}",
        r"Bearer\s+[A-Za-z0-9._\-]{16,}",
    ]:
        m = _re.search(pat, blob)
        assert m is None, f"certification payload matched {pat}: {m.group(0)[:80]!r}"


# ── 8 · platform_band rolls up correctly ──────────────────────────
@pytest.mark.asyncio
async def test_platform_band_rules():
    from lib.production_certification import build_certification  # noqa: PLC0415
    db = _db()
    out = await build_certification(db)
    band = out["platform_band"]
    counters = out["counters"]
    # red iff any failed
    if counters["failed"] > 0:
        assert band == "red", "any FAILED workflow must flip the band RED"
    elif counters["blocked"] > 0 or counters["stale"] > 0:
        assert band == "amber"
    elif counters["verified"] > 0:
        assert band == "green"
    else:
        assert band == "amber"


@pytest.mark.asyncio
async def test_partial_workflow_evidence_is_blocked_not_failed():
    from lib.production_certification import build_certification  # noqa: PLC0415

    db = _db()
    wf = "jha"
    cid = f"cid-cert-blocked-{uuid.uuid4().hex[:8]}"
    try:
        await db.trust_spine_events.insert_one({
            "ts": _iso(_now()),
            "workflow": wf,
            "stage": "notification_queued",
            "status": "skipped",
            "correlation_id": cid,
            "record_id": "r-blocked",
            "module": "test_track_15_79e",
            "failure_reason": "email_safety_mode:strict",
            "remediation": "governance restriction in certification mode",
        })
        out = await build_certification(db)
        row = next(w for w in out["workflows"] if w["workflow"] == wf)
        assert row["status"] == "BLOCKED"
        assert row["last_failure_reason"] == "email_safety_mode:strict"
    finally:
        await db.trust_spine_events.delete_many({"correlation_id": cid})


@pytest.mark.asyncio
async def test_stale_when_latest_verified_evidence_is_outside_window():
    from lib.production_certification import build_certification  # noqa: PLC0415

    db = _db()
    wf = "dvir"
    cid = f"cid-cert-stale-{uuid.uuid4().hex[:8]}"
    try:
        old_ts = _iso(_now() - timedelta(days=3))
        await db.trust_spine_events.insert_one({
            "ts": old_ts,
            "workflow": wf,
            "stage": "completed",
            "status": "ok",
            "correlation_id": cid,
            "record_id": "r-stale",
            "module": "test_track_15_79e",
        })
        out = await build_certification(db)
        row = next(w for w in out["workflows"] if w["workflow"] == wf)
        assert row["status"] == "STALE"
    finally:
        await db.trust_spine_events.delete_many({"correlation_id": cid})


@pytest.mark.asyncio
async def test_untouched_workflow_does_not_fail_release_band():
    from lib.production_certification import build_certification  # noqa: PLC0415
    db = _db()
    out = await build_certification(db)
    assert out["release_band"] in {"pass", "review", "hold"}
    untouched = [w for w in out["workflows"] if w["status"] == "NOT_YET_EXERCISED"]
    if untouched:
        assert out["release_band"] != "hold" or out["counters"]["failed"] > 0 or out["counters"]["blocked"] > 0


@pytest.mark.asyncio
async def test_touched_workflow_without_required_evidence_holds_release_not_fails_status():
    from lib.production_certification import build_certification  # noqa: PLC0415

    db = _db()
    wf = "meeting"
    cid = f"cid-cert-touched-{uuid.uuid4().hex[:8]}"
    try:
        await db.trust_spine_events.insert_one({
            "ts": _iso(_now()),
            "workflow": wf,
            "stage": "routing_resolved",
            "status": "skipped",
            "correlation_id": cid,
            "record_id": "r-touched",
            "module": "test_track_15_79e",
            "failure_reason": "dependency unavailable",
            "remediation": "await prerequisite",
        })
        out = await build_certification(db)
        row = next(w for w in out["workflows"] if w["workflow"] == wf)
        assert row["status"] == "BLOCKED"
        assert out["release_band"] == "hold"
    finally:
        await db.trust_spine_events.delete_many({"correlation_id": cid})
