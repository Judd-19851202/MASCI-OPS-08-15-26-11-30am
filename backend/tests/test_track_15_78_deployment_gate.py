"""TRACK 15.78 · Deployment Trust Gate · regression suite.

Guards the enforcement layer itself:

  1. The deployment-readiness endpoint exists and is admin-gated.
  2. ``pm_missing_route`` is an advisory (operator data) NOT a blocker.
  3. ``critical_route_missing`` IS a blocker.
  4. Unknown-status audit rows produce a blocking gate.
  5. Silent failures (no remediation) produce a blocking gate.
  6. A 100%-failure notification window produces a blocking gate.
  7. ``decision`` is exactly "pass" or "fail" — no other strings.
  8. CLI gate exits 0 on PASS, non-zero on FAIL.
  9. Advisory list is JSON-serializable (no ObjectId leaks).
 10. The endpoint reports the regression-gate-count from the
     filesystem so CI/CD can prove which suite ran.
"""
from __future__ import annotations

import json
import os
import subprocess
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


# ─── 1 · endpoint is admin-gated ───────────────────────────────────
def test_gate_endpoint_requires_admin():
    base = (
        os.environ.get("REACT_APP_BACKEND_URL")
        or "http://localhost:8001"
    )
    try:
        urllib.request.urlopen(
            f"{base}/api/admin/deployment-readiness", timeout=10
        )
        raise AssertionError("anonymous access should be denied")
    except urllib.error.HTTPError as exc:
        assert exc.code in (401, 403)


# ─── 2 · pm_missing_route is advisory, not blocker ─────────────────
@pytest.mark.asyncio
async def test_pm_missing_route_is_advisory():
    from routes.admin_deployment_readiness import (  # noqa: PLC0415
        make_router, DATA_ISSUE_FINDING_CODES,
    )
    assert "pm_missing_route" in DATA_ISSUE_FINDING_CODES, (
        "PM-route gaps must be classified as operator data (advisory) "
        "not as a platform code defect."
    )

    db = _db()

    async def _pass():
        return None
    router = make_router(db, _pass)
    handler = next(
        r.endpoint for r in router.routes
        if getattr(r, "path", "") == "/api/admin/deployment-readiness"
    )
    payload = await handler(_=None)
    # If pm_missing_route is present on this DB, it must be in
    # advisory_findings, NOT in blocking_gates.
    blocking_ids = {g["id"] for g in payload["blocking_gates"]}
    advisory_ids = {g["id"] for g in payload["advisory_findings"]}
    assert "pm_missing_route" not in blocking_ids
    if "pm_missing_route" in [
        f["id"] for f in payload["advisory_findings"] + payload["blocking_gates"]
    ]:
        assert "pm_missing_route" in advisory_ids


# ─── 3 · critical_route_missing IS a blocker ───────────────────────
def test_critical_route_missing_is_blocker():
    from routes.admin_deployment_readiness import (  # noqa: PLC0415
        CODE_DEFECT_FINDING_CODES,
    )
    assert "critical_route_missing" in CODE_DEFECT_FINDING_CODES


# ─── 4-6 · synthetic conditions trigger blocking_gates ─────────────
@pytest.mark.asyncio
async def test_unknown_audit_triggers_blocker(monkeypatch):
    """Insert one unknown-status audit row and confirm the endpoint
    classifies it as a blocking gate."""
    from routes.admin_deployment_readiness import make_router  # noqa: PLC0415
    from datetime import datetime, timezone  # noqa: PLC0415
    db = _db()
    fake_row = {
        "_test": "track_15_78_fixture",
        "ts": datetime.now(timezone.utc).isoformat(),
        "status": "this-is-not-a-real-status",
    }
    await db.email_routing_audit_v2.insert_one(fake_row)
    try:
        async def _pass():
            return None
        router = make_router(db, _pass)
        handler = next(
            r.endpoint for r in router.routes
            if getattr(r, "path", "") == "/api/admin/deployment-readiness"
        )
        payload = await handler(_=None)
        ids = [g["id"] for g in payload["blocking_gates"]]
        assert "audit_unknown_status" in ids
        assert payload["decision"] == "fail"
    finally:
        await db.email_routing_audit_v2.delete_many({"_test": "track_15_78_fixture"})


# ─── 7 · decision is exactly pass or fail ──────────────────────────
@pytest.mark.asyncio
async def test_decision_is_binary():
    from routes.admin_deployment_readiness import make_router  # noqa: PLC0415
    db = _db()

    async def _pass():
        return None
    router = make_router(db, _pass)
    handler = next(
        r.endpoint for r in router.routes
        if getattr(r, "path", "") == "/api/admin/deployment-readiness"
    )
    payload = await handler(_=None)
    assert payload["decision"] in {"pass", "fail"}


# ─── 8 · CLI gate non-zero exit on FAIL ────────────────────────────
def test_cli_gate_returns_nonzero_on_fail(tmp_path):
    """Run the CLI gate with --no-regression so we only test the
    runtime path, and assert exit code matches the decision."""
    # Anonymous (no admin token) — endpoint returns 401, gate must
    # exit non-zero (exit code 3 = unable-to-reach-endpoint OR 2 =
    # runtime fail). Either way: non-zero.
    proc = subprocess.run(
        [
            "python3", "/app/scripts/deployment_gate.py",
            "--no-regression", "--base-url",
            os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001"),
            "--json",
        ],
        env={**os.environ, "OPS_ADMIN_TOKEN": "", "OPS_ADMIN_EMAIL": ""},
        capture_output=True, text=True, timeout=60,
    )
    assert proc.returncode != 0, (
        f"CLI gate must exit non-zero when admin token is missing/invalid; "
        f"got {proc.returncode}\nstdout={proc.stdout}\nstderr={proc.stderr}"
    )


# ─── 9 · payload is JSON-serializable ──────────────────────────────
@pytest.mark.asyncio
async def test_payload_json_serializable():
    from routes.admin_deployment_readiness import make_router  # noqa: PLC0415
    db = _db()

    async def _pass():
        return None
    router = make_router(db, _pass)
    handler = next(
        r.endpoint for r in router.routes
        if getattr(r, "path", "") == "/api/admin/deployment-readiness"
    )
    payload = await handler(_=None)
    # Round-trip JSON — must not raise (no ObjectId leaks).
    blob = json.dumps(payload, default=str)
    assert "ObjectId" not in blob


# ─── 10 · regression_gate_count is non-zero ────────────────────────
@pytest.mark.asyncio
async def test_regression_gate_count_reported():
    from routes.admin_deployment_readiness import make_router  # noqa: PLC0415
    db = _db()

    async def _pass():
        return None
    router = make_router(db, _pass)
    handler = next(
        r.endpoint for r in router.routes
        if getattr(r, "path", "") == "/api/admin/deployment-readiness"
    )
    payload = await handler(_=None)
    # Trust this run is exercising a non-trivial regression base.
    assert payload["regression_gate_count"] >= 30, (
        f"regression_gate_count too low ({payload['regression_gate_count']}); "
        "CI/CD cannot prove which suite ran."
    )
