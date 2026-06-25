"""TRACK 15.77 · FINAL PRODUCTION HARDENING · REGRESSION LOCK.

This file is the permanent **regression lock**: every defect class
discovered between Tracks 15.74 and 15.76B is asserted here so it
cannot silently return. It is the canonical entry point CI/CD must
run before any production deploy.

Each test is a contract gate. If any of them fails, deploy is NO-GO.
"""
from __future__ import annotations

import asyncio
import importlib
import json
import os
import urllib.error
import urllib.request

import pytest
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv("/app/backend/.env")
load_dotenv("/app/frontend/.env")


def _db():
    cli = AsyncIOMotorClient(os.environ["MONGO_URL"])
    return cli[os.environ["DB_NAME"]]


# ─────────────────────────────────────────────────────────────────────
# Gate 1 · Workflow lifecycle contracts are intact.
# ─────────────────────────────────────────────────────────────────────
def test_gate_1_workflow_lifecycle_contracts_present():
    from lib.trust_spine import WORKFLOW_EXPECTED_STAGES  # noqa: PLC0415
    declared = set(WORKFLOW_EXPECTED_STAGES.keys())
    required = {
        "daily-report", "meeting", "jha", "incident", "inspection",
        "qaqc", "equipment-inspection", "dvir", "hr-request",
        "dispatch-assignment", "shop-defect",
    }
    missing = required - declared
    assert not missing, (
        f"workflow lifecycle contract regressed — missing: {missing}"
    )


# ─────────────────────────────────────────────────────────────────────
# Gate 2 · The universal dispatcher uses threaded correlation_id.
# ─────────────────────────────────────────────────────────────────────
def test_gate_2_dispatcher_threads_cid():
    src = open("/app/backend/server.py").read()
    assert "emit_workflow_stage" in src
    # The legacy "new cid per audit" bug must stay dead.
    section = src.split("STAGE_AUDIT_WRITTEN", 1)[1].split("\n\n", 1)[0]
    assert "new_correlation_id()" not in section


# ─────────────────────────────────────────────────────────────────────
# Gate 3 · render_email_html never raises NameError for any kind.
# ─────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("kind", [
    "daily-report", "meeting", "inspection", "incident",
    "jha", "qaqc", "equipment-inspection", "dvir",
])
def test_gate_3_render_email_html_does_not_raise(kind):
    from pdf_render import render_email_html  # noqa: PLC0415
    html = render_email_html(
        kind,
        {"id": "lock", "project_number": "20-07"},
        note="Routine.",
    )
    assert html and "MASCI" in html


# ─────────────────────────────────────────────────────────────────────
# Gate 4 · PM routing must not regress to the legacy single-source.
# ─────────────────────────────────────────────────────────────────────
def test_gate_4_pm_routing_reads_project_team_assignments_first():
    src = open("/app/backend/pm_routing.py").read()
    assert "project_team_assignments" in src, (
        "pm_routing must read project_team_assignments as the canonical "
        "PM source (Track 15.75A) — the legacy jobs_master.pm_email lookup "
        "is a fallback only."
    )
    assert "assignment_role" in src


# ─────────────────────────────────────────────────────────────────────
# Gate 5 · Trust Spine emits + audit row exist for every email-bound
#          workflow on submit (introspect source for the emit_record_
#          created helper).
# ─────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("file_path,workflow", [
    ("/app/backend/routes/daily_reports.py", "daily-report"),
    ("/app/backend/routes/safety.py", "meeting"),
    ("/app/backend/routes/safety.py", "jha"),
    ("/app/backend/routes/safety.py", "incident"),
    ("/app/backend/routes/safety.py", "inspection"),
    ("/app/backend/routes/qaqc.py", "qaqc"),
    ("/app/backend/routes/equipment.py", "equipment-inspection"),
    ("/app/backend/routes/employee_requests.py", "hr-request"),
    ("/app/backend/routes/dispatch_lifecycle.py", "dispatch-assignment"),
    ("/app/backend/routes/fleet_ops.py", "shop-defect"),
])
def test_gate_5_workflow_submit_emits_record_created(file_path, workflow):
    src = open(file_path).read()
    assert "emit_record_created" in src, (
        f"{file_path} must emit STAGE_RECORD_CREATED for {workflow!r}"
    )
    assert workflow in src


# ─────────────────────────────────────────────────────────────────────
# Gate 6 · Operations Trust Center band rules: no fake-green.
# ─────────────────────────────────────────────────────────────────────
def test_gate_6_no_fake_green():
    from lib.trust_score_v2 import compute_categorized_score  # noqa: PLC0415
    out = compute_categorized_score(
        workflows=[{"band": "green"}, {"band": "red"}],
        master_data_findings=[],
    )
    assert out["score_band"] != "green", (
        "fake-green regression: red workflow leaked through to GREEN"
    )


# ─────────────────────────────────────────────────────────────────────
# Gate 7 · Red alert hook cooldown.
# ─────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_gate_7_red_alert_cooldown():
    from lib import red_alert as ra  # noqa: PLC0415
    db = _db()
    await db.red_alert_state.delete_one({"_id": ra.ALERT_DOC_ID})
    try:
        await ra.maybe_send(
            db, current_band="red", score=20,
            score_reason="lock-test",
            workflows=[{"workflow": "x", "band": "red"}],
            trust_center_url="https://example.com/admin/email",
            dry_run=True,
        )
        r2 = await ra.maybe_send(
            db, current_band="red", score=20,
            score_reason="lock-test",
            workflows=[{"workflow": "x", "band": "red"}],
            trust_center_url="https://example.com/admin/email",
            dry_run=True,
        )
        assert r2["result"] in {"cooldown", "unchanged", "disabled"}
    finally:
        await db.red_alert_state.delete_one({"_id": ra.ALERT_DOC_ID})


# ─────────────────────────────────────────────────────────────────────
# Gate 8 · No secret leakage in the Operations Trust Center payload.
# ─────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_gate_8_no_secret_leakage():
    from routes.admin_operations_trust_center import make_router  # noqa: PLC0415
    db = _db()

    async def _pass():
        return None
    router = make_router(db, _pass)
    handler = next(
        r.endpoint for r in router.routes
        if getattr(r, "path", "") == "/api/admin/operations-trust-center"
    )
    payload = await handler(trend_hours=24, _=None)
    blob = json.dumps(payload, default=str)
    for forbidden in (
        os.environ.get("ADMIN_HMAC_SECRET"),
        os.environ.get("RESEND_API_KEY"),
        os.environ.get("MONGO_URL"),
    ):
        if forbidden and len(forbidden) > 8:
            assert forbidden not in blob, (
                "secret leaked into Operations Trust Center payload"
            )
    # bcrypt hash prefixes must never appear either.
    assert "$2b$" not in blob and "$2a$" not in blob


# ─────────────────────────────────────────────────────────────────────
# Gate 9 · Anonymous access blocked on all admin trust endpoints.
# ─────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("path", [
    "/api/admin/trust-spine",
    "/api/admin/operations-trust-center",
    "/api/admin/platform-trust/validate",
])
def test_gate_9_anonymous_access_blocked(path):
    base = (
        os.environ.get("REACT_APP_BACKEND_URL")
        or "http://localhost:8001"
    )
    try:
        urllib.request.urlopen(f"{base}{path}", timeout=10)
        raise AssertionError(f"anonymous access to {path} should be denied")
    except urllib.error.HTTPError as exc:
        assert exc.code in (401, 403), (
            f"{path} returned {exc.code}, expected 401/403"
        )


# ─────────────────────────────────────────────────────────────────────
# Gate 10 · Cross-page consistency — Trust Spine workflow_count
#           must equal the Operations Trust Center workflow_count.
# ─────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_gate_10_cross_page_workflow_count_consistency():
    from routes.admin_trust_spine import make_router as spine_router  # noqa: PLC0415
    from routes.admin_operations_trust_center import (  # noqa: PLC0415
        make_router as otc_router,
    )
    db = _db()

    async def _pass():
        return None

    spine = spine_router(db, _pass)
    spine_handler = next(
        r.endpoint for r in spine.routes
        if getattr(r, "path", "") == "/api/admin/trust-spine"
    )
    spine_payload = await spine_handler(_=None)

    otc = otc_router(db, _pass)
    otc_handler = next(
        r.endpoint for r in otc.routes
        if getattr(r, "path", "") == "/api/admin/operations-trust-center"
    )
    otc_payload = await otc_handler(trend_hours=24, _=None)

    assert (
        spine_payload["workflow_count"]
        == otc_payload["summary"]["workflow_count"]
    ), (
        "workflow_count drift between Trust Spine and Operations Trust "
        "Center — the two pages are showing different truths."
    )


# ─────────────────────────────────────────────────────────────────────
# Gate 11 · Cross-page consistency — the per-band counts in the OTC
#           summary must match the actual workflows[] rollup.
# ─────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_gate_11_otc_band_count_self_consistency():
    from routes.admin_operations_trust_center import make_router  # noqa: PLC0415
    db = _db()

    async def _pass():
        return None
    router = make_router(db, _pass)
    handler = next(
        r.endpoint for r in router.routes
        if getattr(r, "path", "") == "/api/admin/operations-trust-center"
    )
    payload = await handler(trend_hours=24, _=None)
    workflows = payload["workflows"]
    summary = payload["summary"]
    counts = {
        "workflows_trusted": sum(1 for w in workflows if w["band"] == "green"),
        "workflows_amber":   sum(1 for w in workflows if w["band"] == "amber"),
        "workflows_idle":    sum(1 for w in workflows if w["band"] == "amber-no-activity"),
        "workflows_red":     sum(1 for w in workflows if w["band"] == "red"),
    }
    for k, expected in counts.items():
        assert summary[k] == expected, (
            f"summary.{k} = {summary[k]} but workflows[] says {expected} "
            "— cross-page count drift"
        )


# ─────────────────────────────────────────────────────────────────────
# Gate 12 · Master Data findings must each carry severity AND a
#           remediation_link (operator deep-link).
# ─────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_gate_12_master_data_findings_actionable():
    from lib.master_data_trust import collect_findings  # noqa: PLC0415
    db = _db()
    findings = await collect_findings(db)
    for f in findings:
        assert f.get("severity") in {"critical", "warning", "cleanup"}, (
            f"finding {f.get('code')} missing severity"
        )
        assert f.get("remediation_link", "").startswith("/"), (
            f"finding {f.get('code')} missing operator deep-link"
        )
        assert f.get("remediation"), (
            f"finding {f.get('code')} missing remediation copy"
        )


# ─────────────────────────────────────────────────────────────────────
# Gate 13 · Headline ETA never includes cleanup actions.
# ─────────────────────────────────────────────────────────────────────
def test_gate_13_headline_eta_critical_only():
    from routes.admin_operations_trust_center import (  # noqa: PLC0415
        _build_operator_actions,
    )
    actions = _build_operator_actions(
        workflows=[],
        findings=[
            {"code": "c", "severity": "critical", "summary": "c",
             "remediation": "r", "remediation_link": "/c",
             "estimated_remediation_seconds": 60},
            {"code": "x", "severity": "cleanup", "summary": "x",
             "remediation": "r", "remediation_link": "/x",
             "estimated_remediation_seconds": 100000},
        ],
    )
    eta = sum(
        a.get("estimated_remediation_seconds", 0)
        for a in actions if a.get("priority") == "critical"
    )
    assert eta == 60


# ─────────────────────────────────────────────────────────────────────
# Gate 14 · The universal email dispatcher's exception handler MUST
#          emit a Trust Spine `completed` failure event before
#          swallowing the exception. Other cleanup paths (orphan
#          file unlinks, cache invalidation, format fallthrough) are
#          explicitly allowed.
# ─────────────────────────────────────────────────────────────────────
def test_gate_14_dispatcher_exception_emits_trust_spine_failure():
    src = open("/app/backend/server.py").read()
    needle = 'logger.exception(f"auto-email failed'
    assert needle in src, (
        "_dispatch_auto_email outer except handler is missing"
    )
    handler_block = src.split(needle, 1)[1].split("\n\n", 2)[0]
    assert "emit_workflow_stage" in handler_block, (
        "dispatcher exception handler must emit a Trust Spine "
        "`completed` failure event before swallowing — otherwise "
        "a workflow can fail silently."
    )
    assert "status=\"failed\"" in handler_block
    assert "remediation=" in handler_block


# ─────────────────────────────────────────────────────────────────────
# Gate 15 · Universal dispatcher emits failure event with a
#           remediation hint on every exception.
# ─────────────────────────────────────────────────────────────────────
def test_gate_15_dispatcher_failure_carries_remediation():
    src = open("/app/backend/server.py").read()
    # The exception handler block in _dispatch_auto_email must emit
    # the `completed` stage with status="failed" + remediation=...
    needle = 'stage=STAGE_COMPLETED'
    failure_block = src.split('logger.exception(f"auto-email failed')[1]
    assert needle in failure_block
    assert 'remediation=' in failure_block, (
        "dispatcher failure path must include a remediation hint so the "
        "Trust Center can render an actionable operator action."
    )
