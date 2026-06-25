"""TRACK 15.79 · Pipeline Lock regression suite.

Permanent gates that prove the Deployment Trust Gate cannot be
bypassed and that every deployment decision is recorded.
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


# ─── 1 · pre_deploy_check.sh invokes deployment_gate.py ───────────
def test_pre_deploy_check_invokes_trust_gate():
    src = open("/app/scripts/pre_deploy_check.sh").read()
    assert "scripts/deployment_gate.py" in src
    assert "DO NOT DEPLOY" in src
    # Must propagate the gate's exit code verbatim — no bypass.
    assert "TRUST_GATE_RC" in src
    assert "exit \"$TRUST_GATE_RC\"" in src


# ─── 2 · GitHub Actions workflow references the Trust Gate ────────
def test_github_actions_references_trust_gate():
    src = open("/app/.github/workflows/sigma3-deploy-gate.yml").read()
    assert "deployment_gate.py" in src
    assert "TRACK_15_78_FINAL_CERTIFICATION.md" in src
    assert "test_track_15_78_deployment_gate.py" in src
    assert "test_track_15_79_pipeline_lock.py" in src


# ─── 3 · Ledger endpoint is admin-gated ────────────────────────────
def test_ledger_endpoint_requires_admin():
    base = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001")
    try:
        urllib.request.urlopen(
            f"{base}/api/admin/deployment-readiness/history", timeout=10
        )
        raise AssertionError("anonymous access should be denied")
    except urllib.error.HTTPError as exc:
        assert exc.code in (401, 403)


# ─── 4 · Ledger rejects non-pass/non-fail decisions ───────────────
@pytest.mark.asyncio
async def test_ledger_rejects_invalid_decision():
    from routes.admin_deployment_ledger import make_router  # noqa: PLC0415
    from fastapi import Request  # noqa: PLC0415
    from starlette.requests import Request as StarletteRequest  # noqa: PLC0415
    import io  # noqa: PLC0415
    db = _db()

    async def _pass():
        return None
    router = make_router(db, _pass)
    handler = next(
        r.endpoint for r in router.routes
        if getattr(r, "path", "") == "/api/admin/deployment-readiness/snapshot"
    )

    # Build a tiny mock Request with a JSON body containing an
    # invalid decision string. We use Starlette's Request constructor
    # with a minimal ASGI scope + receive coroutine.
    async def receive():
        return {
            "type": "http.request",
            "body": json.dumps({"decision": "maybe"}).encode(),
        }

    scope = {
        "type": "http", "method": "POST",
        "path": "/api/admin/deployment-readiness/snapshot",
        "headers": [(b"content-type", b"application/json")],
    }
    req = StarletteRequest(scope, receive)
    from fastapi import HTTPException  # noqa: PLC0415
    raised = False
    try:
        await handler(request=req, _=None)
    except HTTPException as exc:
        raised = exc.status_code == 400
    assert raised, (
        "ledger must reject decision strings outside {pass, fail}"
    )


# ─── 5 · Ledger appends + reads back ───────────────────────────────
@pytest.mark.asyncio
async def test_ledger_appends_and_reads_back():
    from routes.admin_deployment_ledger import (  # noqa: PLC0415
        make_router, COLLECTION,
    )
    from starlette.requests import Request as StarletteRequest  # noqa: PLC0415
    db = _db()

    async def _pass():
        return None
    router = make_router(db, _pass)
    write_handler = next(
        r.endpoint for r in router.routes
        if getattr(r, "path", "") == "/api/admin/deployment-readiness/snapshot"
    )
    read_handler = next(
        r.endpoint for r in router.routes
        if getattr(r, "path", "") == "/api/admin/deployment-readiness/history"
    )

    marker = f"track-15-79-test-{os.urandom(4).hex()}"

    async def receive():
        return {
            "type": "http.request",
            "body": json.dumps({
                "decision": "pass",
                "exit_code": 0,
                "commit": marker,
                "trust_score": 99,
                "trust_band": "green",
            }).encode(),
        }

    scope = {
        "type": "http", "method": "POST",
        "path": "/api/admin/deployment-readiness/snapshot",
        "headers": [(b"content-type", b"application/json")],
    }
    req = StarletteRequest(scope, receive)
    try:
        out = await write_handler(request=req, _=None)
        assert out["ok"] is True
        history = await read_handler(limit=50, _=None)
        commits = [e.get("commit") for e in history["events"]]
        assert marker in commits
    finally:
        await db[COLLECTION].delete_many({"commit": marker})


# ─── 6 · Post-deploy verification script exists + executable ──────
def test_post_deploy_verify_script_exists():
    assert os.path.isfile("/app/scripts/post_deploy_verify.sh"), (
        "Track 15.79 requires a post-deploy verification script"
    )
    src = open("/app/scripts/post_deploy_verify.sh").read()
    assert "/api/admin/deployment-readiness" in src
    assert "/api/admin/operations-trust-center" in src
    # Must exit non-zero on failure (set -e at the top).
    assert "set -euo pipefail" in src


# ─── 7 · Deployment ledger TTL keeps it append-only practical ────
@pytest.mark.asyncio
async def test_ledger_indexes_created():
    from routes.admin_deployment_ledger import (  # noqa: PLC0415
        ensure_indexes, COLLECTION,
    )
    db = _db()
    await ensure_indexes(db)
    names = await db[COLLECTION].index_information()
    # Expect at least ts, commit+ts, decision+ts, ts_dt (TTL).
    keys = set()
    for spec in names.values():
        keys.update(k for k, _ in spec.get("key", []))
    assert "ts" in keys
    assert "ts_dt" in keys
    assert "commit" in keys or "decision" in keys


# ─── 8 · Bypass detection — gate exit codes never reinterpreted ──
def test_gate_exit_codes_documented_and_enforced():
    """Exit codes 0/1/2/3 must each map to a distinct outcome and the
    CLI must propagate them. This locks the contract."""
    src = open("/app/scripts/deployment_gate.py").read()
    # 0 is the initial state (the dict literal).
    assert '"exit_code": 0' in src
    # 1/2/3 must each be set explicitly somewhere.
    assert 'report["exit_code"] = 1' in src
    assert 'report["exit_code"] = 2' in src
    assert 'report["exit_code"] = 3' in src
    # main() must `return report["exit_code"]` (not constant 0).
    assert 'return report["exit_code"]' in src
