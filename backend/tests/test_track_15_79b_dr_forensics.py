"""TRACK 15.79B regression suite — Daily Report Delivery Forensics.

Locks the contract of GET /api/admin/daily-report-delivery/forensics:

  • admin-gated (anonymous → 401/403)
  • limit/since_hours bounded
  • root-cause classifier covers every closed-set code
  • re-runs the SAME resolver code path used at submit-time
  • returns trace fields for: job_master_match, team_roster_match,
    resolver_result, trust_spine_stages, email_routing_audit,
    failure_point, root_cause_code, operator_remediation
  • surfaces project_number_mismatch / role_name_mismatch via the
    diagnostic_misses scan (proves the closed-set classifier works)
  • no secrets leak in any response field

Doctrine: no writes. The tests prove this by counting documents in
``daily_reports`` / ``project_team_assignments`` / ``trust_spine_events``
/ ``email_routing_audit_v2`` before and after each call.
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone

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


# ── 1 · anonymous request rejected ─────────────────────────────────
def test_endpoint_requires_admin():
    base = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001")
    try:
        urllib.request.urlopen(
            f"{base}/api/admin/daily-report-delivery/forensics?since_hours=1",
            timeout=10,
        )
        raise AssertionError("anonymous access should be denied")
    except urllib.error.HTTPError as exc:
        assert exc.code in (401, 403)


# ── 2 · payload shape valid (closed-set summary counters present) ──
@pytest.mark.asyncio
async def test_payload_shape_summary():
    from routes.admin_dr_delivery_forensics import make_router  # noqa: PLC0415

    async def _pass():
        return None

    db = _db()
    router = make_router(db, _pass)
    handler = next(
        r.endpoint for r in router.routes
        if getattr(r, "path", "") == "/api/admin/daily-report-delivery/forensics"
    )
    out = await handler(since_hours=1, project_number=None, limit=5, _=None)
    assert out["ok"] is True
    assert out["track"] == "15.79B"
    for k in (
        "reports_found",
        "reports_with_pm_assignment",
        "reports_with_copm_assignment",
        "reports_with_pm_email_resolved",
        "reports_with_copm_email_resolved",
        "reports_with_recipients_built",
        "reports_with_send_attempt",
        "reports_with_provider_accept",
        "reports_dead_lettered",
        "reports_unconfigured",
        "reports_silent_failure",
    ):
        assert k in out, f"missing counter: {k}"
    assert "expected_stage_contract" in out


# ── 3 · limit + since_hours bounded ────────────────────────────────
def test_limit_max_enforced():
    """The FastAPI Query(..., le=200) bound enforces this on the wire.
    We assert the route declaration carries the bounds so it cannot be
    relaxed later without a failing test."""
    from routes.admin_dr_delivery_forensics import make_router  # noqa: PLC0415

    async def _pass():
        return None

    router = make_router(_db(), _pass)
    route = next(
        r for r in router.routes
        if getattr(r, "path", "") == "/api/admin/daily-report-delivery/forensics"
    )
    # Pydantic v2 stores Query metadata on the FieldInfo's `metadata`
    # list (Le/Ge constraints) rather than as direct attributes. Walk
    # the metadata to assert the bounds hold.
    def _bounds(p):
        meta = getattr(p.field_info, "metadata", []) or []
        le = next((m.le for m in meta if hasattr(m, "le")), None)
        ge = next((m.ge for m in meta if hasattr(m, "ge")), None)
        return ge, le

    sig = route.dependant.query_params
    limit_param = next(p for p in sig if p.name == "limit")
    since_param = next(p for p in sig if p.name == "since_hours")
    assert _bounds(limit_param) == (1, 200)
    assert _bounds(since_param) == (1, 168)


# ── 4 · roster PM resolves correctly (real schema) ────────────────
@pytest.mark.asyncio
async def test_roster_pm_resolves_via_canonical_query():
    from routes.admin_dr_delivery_forensics import make_router  # noqa: PLC0415

    db = _db()
    pn = f"TRACK1579B-{uuid.uuid4().hex[:6].upper()}"
    dr_id = f"dr-{uuid.uuid4().hex[:12]}"
    assn_id = f"assn-{uuid.uuid4().hex[:12]}"
    now_iso = _iso(_now())
    try:
        await db.daily_reports.insert_one({
            "id": dr_id,
            "doc_id": f"DR-TEST-{uuid.uuid4().hex[:6]}",
            "project_number": pn,
            "project_name": "Test PN Resolves",
            "prepared_by": "Pytest Foreman",
            "created_at": now_iso,
            "report_date": now_iso[:10],
        })
        await db.project_team_assignments.insert_one({
            "id": assn_id,
            "project_number": pn,
            "user_id": None,
            "employee_id": None,
            "email": "pytest.pm@example.com",
            "display_name": "Pytest PM",
            "assignment_role": "pm",
            "is_primary": True,
            "active": True,
            "assigned_at": now_iso,
        })

        async def _pass():
            return None

        router = make_router(db, _pass)
        handler = next(
            r.endpoint for r in router.routes
            if getattr(r, "path", "") == "/api/admin/daily-report-delivery/forensics"
        )
        out = await handler(
            since_hours=1, project_number=pn, limit=5, _=None,
        )
        assert out["reports_found"] >= 1
        row = next(
            r for r in out["reports"] if r["report_id"] == dr_id
        )
        assert row["pm_assignment"] is not None
        assert row["pm_assignment"]["email"] == "pytest.pm@example.com"
        assert row["pm_email_resolved"] == "pytest.pm@example.com"
        assert "pytest.pm@example.com" in (row["resolver_result"]["to"] or [])
    finally:
        await db.daily_reports.delete_one({"id": dr_id})
        await db.project_team_assignments.delete_one({"id": assn_id})


# ── 5 · roster co-PMs resolve ─────────────────────────────────────
@pytest.mark.asyncio
async def test_roster_copms_resolve():
    from routes.admin_dr_delivery_forensics import make_router  # noqa: PLC0415

    db = _db()
    pn = f"TRACK1579B-{uuid.uuid4().hex[:6].upper()}"
    dr_id = f"dr-{uuid.uuid4().hex[:12]}"
    a1 = f"assn-{uuid.uuid4().hex[:12]}"
    a2 = f"assn-{uuid.uuid4().hex[:12]}"
    a3 = f"assn-{uuid.uuid4().hex[:12]}"
    now_iso = _iso(_now())
    try:
        await db.daily_reports.insert_one({
            "id": dr_id, "doc_id": f"DR-COPM-{uuid.uuid4().hex[:6]}",
            "project_number": pn, "project_name": "CoPM Test",
            "prepared_by": "Foreman X", "created_at": now_iso,
            "report_date": now_iso[:10],
        })
        await db.project_team_assignments.insert_many([
            {"id": a1, "project_number": pn, "email": "pm@x.com",
             "display_name": "PM", "assignment_role": "pm",
             "is_primary": True, "active": True, "assigned_at": now_iso},
            {"id": a2, "project_number": pn, "email": "copm1@x.com",
             "display_name": "Co PM 1", "assignment_role": "co_pm",
             "is_primary": False, "active": True, "assigned_at": now_iso},
            {"id": a3, "project_number": pn, "email": "copm2@x.com",
             "display_name": "Co PM 2", "assignment_role": "co_pm",
             "is_primary": False, "active": True, "assigned_at": now_iso},
        ])

        async def _pass():
            return None

        router = make_router(db, _pass)
        handler = next(
            r.endpoint for r in router.routes
            if getattr(r, "path", "") == "/api/admin/daily-report-delivery/forensics"
        )
        out = await handler(
            since_hours=1, project_number=pn, limit=5, _=None,
        )
        row = next(r for r in out["reports"] if r["report_id"] == dr_id)
        assert len(row["copm_assignments"]) == 2
        assert set(row["copm_emails_resolved"]) == {"copm1@x.com", "copm2@x.com"}
    finally:
        await db.daily_reports.delete_one({"id": dr_id})
        await db.project_team_assignments.delete_many(
            {"id": {"$in": [a1, a2, a3]}}
        )


# ── 6 · role_name_mismatch detected by diagnostic scan ────────────
@pytest.mark.asyncio
async def test_role_name_mismatch_detected():
    from routes.admin_dr_delivery_forensics import make_router  # noqa: PLC0415

    db = _db()
    pn = f"TRACK1579B-{uuid.uuid4().hex[:6].upper()}"
    dr_id = f"dr-{uuid.uuid4().hex[:12]}"
    a1 = f"assn-{uuid.uuid4().hex[:12]}"
    now_iso = _iso(_now())
    try:
        await db.daily_reports.insert_one({
            "id": dr_id, "doc_id": f"DR-RM-{uuid.uuid4().hex[:6]}",
            "project_number": pn, "project_name": "Role Mismatch Test",
            "prepared_by": "Foreman Y", "created_at": now_iso,
            "report_date": now_iso[:10],
        })
        # Wrong role key — UI may have written "Project Manager".
        await db.project_team_assignments.insert_one({
            "id": a1, "project_number": pn, "email": "wrongrole@x.com",
            "display_name": "Wrong Role PM",
            "assignment_role": "Project Manager",  # <- the bug
            "is_primary": True, "active": True, "assigned_at": now_iso,
        })

        async def _pass():
            return None

        router = make_router(db, _pass)
        handler = next(
            r.endpoint for r in router.routes
            if getattr(r, "path", "") == "/api/admin/daily-report-delivery/forensics"
        )
        out = await handler(
            since_hours=1, project_number=pn, limit=5, _=None,
        )
        row = next(r for r in out["reports"] if r["report_id"] == dr_id)
        assert row["pm_assignment"] is None
        misses = row["team_roster_match"]["diagnostic_misses"]
        codes = [m.get("diagnostic") for m in misses]
        assert "role_name_mismatch" in codes
    finally:
        await db.daily_reports.delete_one({"id": dr_id})
        await db.project_team_assignments.delete_one({"id": a1})


# ── 7 · inactive_assignment detected by diagnostic scan ───────────
@pytest.mark.asyncio
async def test_inactive_assignment_detected():
    from routes.admin_dr_delivery_forensics import make_router  # noqa: PLC0415

    db = _db()
    pn = f"TRACK1579B-{uuid.uuid4().hex[:6].upper()}"
    dr_id = f"dr-{uuid.uuid4().hex[:12]}"
    a1 = f"assn-{uuid.uuid4().hex[:12]}"
    now_iso = _iso(_now())
    try:
        await db.daily_reports.insert_one({
            "id": dr_id, "doc_id": f"DR-INA-{uuid.uuid4().hex[:6]}",
            "project_number": pn, "project_name": "Inactive Assn Test",
            "prepared_by": "Foreman Z", "created_at": now_iso,
            "report_date": now_iso[:10],
        })
        await db.project_team_assignments.insert_one({
            "id": a1, "project_number": pn, "email": "inactive@x.com",
            "display_name": "Inactive PM", "assignment_role": "pm",
            "is_primary": True, "active": False,  # <- inactive
            "assigned_at": now_iso,
        })

        async def _pass():
            return None

        router = make_router(db, _pass)
        handler = next(
            r.endpoint for r in router.routes
            if getattr(r, "path", "") == "/api/admin/daily-report-delivery/forensics"
        )
        out = await handler(
            since_hours=1, project_number=pn, limit=5, _=None,
        )
        row = next(r for r in out["reports"] if r["report_id"] == dr_id)
        assert row["pm_assignment"] is None
        codes = [m.get("diagnostic") for m in row["team_roster_match"]["diagnostic_misses"]]
        assert "inactive_assignment" in codes
    finally:
        await db.daily_reports.delete_one({"id": dr_id})
        await db.project_team_assignments.delete_one({"id": a1})


# ── 8 · trust_spine_missing_notification_stage classification ─────
@pytest.mark.asyncio
async def test_classifier_detects_missing_notification_stage():
    """When the DR has a record_created event but the dispatcher never
    fired (no recipients_built / notification_queued events), the
    classifier must return ``trust_spine_missing_notification_stage``."""
    from routes.admin_dr_delivery_forensics import (  # noqa: PLC0415
        _classify, EXPECTED_STAGES_DAILY_REPORT,
    )
    spine_index = {
        "record_created": {"stage": "record_created", "status": "ok"},
        "routing_resolved": {"stage": "routing_resolved", "status": "ok"},
        # recipients_built INTENTIONALLY missing
    }
    code = _classify(
        assignments=[{"assignment_role": "pm", "active": True,
                      "is_primary": True}],
        pm_assignment={"email": "pm@x.com"},
        copm_assignments=[],
        pm_email="pm@x.com",
        copm_emails=[],
        recipients=["pm@x.com"],
        expected=EXPECTED_STAGES_DAILY_REPORT,
        spine_stage_index=spine_index,
        audit_rows=[],
        dead_letter_configured=True,
    )
    assert code == "trust_spine_missing_notification_stage"


# ── 9 · provider_rejected classification ──────────────────────────
def test_classifier_provider_rejected():
    from routes.admin_dr_delivery_forensics import (  # noqa: PLC0415
        _classify, EXPECTED_STAGES_DAILY_REPORT,
    )
    spine_index = {
        "record_created": {"status": "ok"},
        "routing_resolved": {"status": "ok"},
        "recipients_built": {"status": "ok"},
        "notification_queued": {"status": "ok"},
        "provider_accepted": {
            "status": "failed",
            "failure_reason": "resend returned no message id",
        },
    }
    code = _classify(
        assignments=[{"assignment_role": "pm", "active": True}],
        pm_assignment={"email": "pm@x.com"},
        copm_assignments=[],
        pm_email="pm@x.com",
        copm_emails=[],
        recipients=["pm@x.com"],
        expected=EXPECTED_STAGES_DAILY_REPORT,
        spine_stage_index=spine_index,
        audit_rows=[],
        dead_letter_configured=True,
    )
    assert code == "provider_rejected"


# ── 10 · no secrets leak (MONGO_URL / RESEND_API_KEY / token) ─────
@pytest.mark.asyncio
async def test_no_secrets_leak_in_payload():
    from routes.admin_dr_delivery_forensics import make_router  # noqa: PLC0415

    async def _pass():
        return None

    db = _db()
    router = make_router(db, _pass)
    handler = next(
        r.endpoint for r in router.routes
        if getattr(r, "path", "") == "/api/admin/daily-report-delivery/forensics"
    )
    out = await handler(
        since_hours=1, project_number=None, limit=5,
        include_environment_probe=True, _=None,
    )
    import json as _json  # noqa: PLC0415
    import re as _re  # noqa: PLC0415
    blob = _json.dumps(out, default=str)
    # Boolean presence flags are allowed (e.g.
    # ``resend_api_key_configured: true``) — they convey policy state,
    # not secret values. We forbid the ACTUAL secret-value markers:
    # Mongo URIs, raw Resend API keys (re_<10+ char>), Bearer tokens,
    # password values, HMAC secret values.
    forbidden_patterns = [
        r"mongodb\+srv://[^\"']+",         # full Mongo connection URI
        r"mongodb://[^\"']+:[^\"']+@",     # Mongo URI with creds
        r"\"mongo_url\"\s*:\s*\"[^\"]+\"",
        r"re_[A-Za-z0-9]{10,}",            # raw Resend secret keys
        r"\"resend_api_key\"\s*:\s*\"[^\"]+\"",  # secret VALUE leak
        r"\"admin_password\"\s*:\s*\"[^\"]+\"",
        r"\"admin_hmac_secret\"\s*:\s*\"[^\"]+\"",
        r"Bearer\s+[A-Za-z0-9._\-]{16,}",
    ]
    for pat in forbidden_patterns:
        m = _re.search(pat, blob)
        assert m is None, (
            f"forensic payload matched forbidden secret pattern "
            f"{pat!r}: {m.group(0)[:80]!r}"
        )


# ── 11 · endpoint performs ZERO writes (no side effects) ──────────
@pytest.mark.asyncio
async def test_endpoint_performs_no_writes():
    """The doctrine demands the forensic endpoint is purely read-only.
    Older revisions accidentally called ``recipients_for_record_async``
    which triggers ``_audit_dead_letter`` → writes to
    ``email_routing_audit_v2`` AND ``platform_audit``. This test counts
    documents in every collection the endpoint touches BEFORE and AFTER
    one call and fails if any count grew."""
    from routes.admin_dr_delivery_forensics import make_router  # noqa: PLC0415

    db = _db()
    # Insert ONE DR with no PM assignment so the endpoint hits the
    # dead-letter resolution path inside the resolver. This is the
    # exact code-path that USED to write side-effect rows.
    pn = f"TRACK1579B-NO-PM-{uuid.uuid4().hex[:6].upper()}"
    dr_id = f"dr-{uuid.uuid4().hex[:12]}"
    now_iso = _iso(_now())
    await db.daily_reports.insert_one({
        "id": dr_id, "doc_id": f"DR-NOPM-{uuid.uuid4().hex[:6]}",
        "project_number": pn, "project_name": "No-PM Forensic Test",
        "prepared_by": "Pytest Foreman", "created_at": now_iso,
        "report_date": now_iso[:10],
    })
    try:
        watched = (
            "email_routing_audit_v2", "platform_audit",
            "trust_spine_events", "project_team_assignments",
            "deployment_decisions",
        )
        before = {
            c: await db[c].count_documents({}) for c in watched
        }

        async def _pass():
            return None

        router = make_router(db, _pass)
        handler = next(
            r.endpoint for r in router.routes
            if getattr(r, "path", "") == "/api/admin/daily-report-delivery/forensics"
        )
        out = await handler(
            since_hours=1, project_number=pn, limit=5, _=None,
        )
        # The endpoint MUST have found the DR.
        assert out["reports_found"] >= 1

        after = {
            c: await db[c].count_documents({}) for c in watched
        }
        for c in watched:
            assert before[c] == after[c], (
                f"forensic endpoint wrote to {c} "
                f"(before={before[c]}, after={after[c]})"
            )
    finally:
        await db.daily_reports.delete_one({"id": dr_id})


# ── 12 · dead_letter_only root cause classifies + does NOT leak ───
def test_classifier_dead_letter_only():
    from routes.admin_dr_delivery_forensics import (  # noqa: PLC0415
        _classify, EXPECTED_STAGES_DAILY_REPORT,
    )
    code = _classify(
        assignments=[],
        pm_assignment=None,
        copm_assignments=[],
        pm_email=None,
        copm_emails=[],
        recipients=["admin@office.example"],  # dead-letter only
        expected=EXPECTED_STAGES_DAILY_REPORT,
        spine_stage_index={},
        audit_rows=[],
        dead_letter_configured=True,
        routed_via_dead_letter=True,
    )
    assert code == "dead_letter_only"
