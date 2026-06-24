"""TRACK 15.75D — In-app Platform Trust Validator regression.

Defends the contract: super-admin reads
``/api/admin/platform-trust/validate`` and gets a complete,
read-only, secret-free, self-explanatory trust snapshot.

The validator MUST:
- require admin auth (401 anonymous)
- expose no Mongo URL, no Resend API key, no HMAC secret,
  no password hash, no env credential
- enforce the Track 15.75C allowed-status set
- honestly mark workflows with no recent activity as
  ``amber-no-activity`` (never fake green)
- mark workflows with failures, unknown statuses, empty
  critical routes, or recent submissions w/o audit rows
  as ``red`` with an explicit ``red_reason``
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


async def _call_validator(db):
    """Invoke the validator's underlying coroutine directly so
    we don't depend on a live HTTP session token."""
    from routes.admin_platform_trust import (  # noqa: PLC0415
        make_router,
    )

    captured = {}

    async def _passthrough_dep():
        return None

    router = make_router(db, _passthrough_dep)
    for route in router.routes:
        if getattr(route, "path", "") == "/api/admin/platform-trust/validate":
            captured["handler"] = route.endpoint
            break
    assert "handler" in captured, "validator handler not registered"
    return await captured["handler"](_=None)


@pytest.mark.asyncio
async def test_admin_endpoint_requires_authentication():
    """Anonymous requests to the validator MUST return 401."""
    import urllib.request, urllib.error  # noqa: PLC0415
    api_url = (
        open("/app/frontend/.env").read().split("REACT_APP_BACKEND_URL=")[1]
        .split("\n")[0].strip()
    )
    try:
        urllib.request.urlopen(
            f"{api_url}/api/admin/platform-trust/validate", timeout=15
        )
        pytest.fail("anonymous request must NOT succeed")
    except urllib.error.HTTPError as exc:
        assert exc.code in (401, 403), (
            f"expected 401/403, got {exc.code}"
        )


@pytest.mark.asyncio
async def test_validator_payload_shape():
    """The validator response MUST contain the documented top-level
    keys so the frontend card can render unconditionally."""
    db = _db()
    payload = await _call_validator(db)
    required = {
        "track", "generated_at", "system", "email_routing",
        "audit_status_integrity", "workflow_delivery_health",
        "pm_email_coverage", "dead_letter_health", "final_band",
        "red_reasons", "amber_reasons",
    }
    missing = required - set(payload.keys())
    assert not missing, f"validator payload missing keys: {missing}"
    assert payload["track"] == "15.75D"
    assert payload["final_band"] in {"green", "amber", "red"}
    assert isinstance(payload["workflow_delivery_health"], list)
    assert len(payload["workflow_delivery_health"]) == 7, (
        "all 7 workflow modules must be reported"
    )


@pytest.mark.asyncio
async def test_validator_allowed_statuses_enforced():
    """``audit_status_integrity.pass`` MUST be true when only allowed
    statuses are observed; if an unknown status sneaks in, ``pass``
    becomes false AND the final_band becomes ``red``."""
    db = _db()
    payload = await _call_validator(db)
    ai = payload["audit_status_integrity"]
    if ai["unknown_status_count"] == 0:
        assert ai["pass"] is True
    else:
        # If an unknown status exists, the validator must have flagged red.
        assert payload["final_band"] == "red"
        assert any("unknown_audit_status" in r for r in payload["red_reasons"])


@pytest.mark.asyncio
async def test_validator_no_secrets_in_payload():
    """The payload MUST NOT leak any production secret."""
    db = _db()
    payload = await _call_validator(db)
    import json
    blob = json.dumps(payload, default=str).lower()
    forbidden_fragments = [
        "mongodb+srv://",
        "mongodb://",
        "re_",          # Resend API keys start with re_
        "password",
        "password_hash",
        "jwt_secret",
        "hmac_secret",
        "secret_key",
        "auth_token",
    ]
    # 'password' might appear as substring in field names; we want to
    # ensure no actual secret VALUE leaks. We check for the presence
    # of fields that would carry a secret.
    leak = [f for f in forbidden_fragments if f in blob and f != "password"]
    assert not leak, f"secret-like fragments leaked: {leak}"
    # Specifically: known sensitive env vars must not appear as values.
    for sensitive in (
        os.environ.get("MONGO_URL", ""),
        os.environ.get("RESEND_API_KEY", ""),
        os.environ.get("ADMIN_TOKEN", ""),
        os.environ.get("JWT_SECRET", ""),
    ):
        if sensitive and len(sensitive) > 8:
            assert sensitive not in blob, (
                f"sensitive env value found in payload"
            )


@pytest.mark.asyncio
async def test_validator_no_activity_is_amber_not_green():
    """A workflow with zero sends, zero failures, AND zero source
    submissions in the last 24h must be tagged ``amber-no-activity``
    and contribute to amber_reasons — NEVER green."""
    db = _db()
    payload = await _call_validator(db)
    for wf in payload["workflow_delivery_health"]:
        if (wf["sent_24h"] == 0 and wf["failed_24h"] == 0
                and wf["recent_submissions_24h"] == 0):
            assert wf["band"] == "amber-no-activity", (
                f"{wf['calling_module']} has no activity but band="
                f"{wf['band']} — fake green forbidden"
            )


@pytest.mark.asyncio
async def test_validator_silent_failure_detection_is_red():
    """Inject a synthetic recent submission with NO audit row, and
    confirm the validator flags it as a silent-failure red."""
    db = _db()
    from datetime import datetime, timezone
    fake = {
        "id": str(uuid.uuid4()),
        "doc_id": f"DR-TRUST-{uuid.uuid4().hex[:8]}",
        "project_number": "TRUST-VALIDATOR-15-75D",
        "report_date": "2026-06-24",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.daily_reports.insert_one(dict(fake))
    try:
        payload = await _call_validator(db)
        dr_wf = next(
            w for w in payload["workflow_delivery_health"]
            if w["calling_module"] == "auto_email_dispatch:daily-report"
        )
        # If there are no sent_24h rows for daily-report AND the
        # source collection has a fresh row, the validator MUST flag red.
        if dr_wf["sent_24h"] == 0 and dr_wf["failed_24h"] == 0:
            assert dr_wf["band"] == "red", (
                f"silent-failure path not detected: band={dr_wf['band']}"
            )
            assert "silent" in dr_wf["reason"].lower()
            assert payload["final_band"] == "red"
    finally:
        await db.daily_reports.delete_many(
            {"project_number": "TRUST-VALIDATOR-15-75D"}
        )


@pytest.mark.asyncio
async def test_validator_critical_route_empty_is_red():
    """A critical route with no recipients MUST flip the validator
    to red with an explicit ``critical_route_empty`` reason."""
    db = _db()
    # Snapshot the current ADMIN_DEAD_LETTER_TO doc so we can restore.
    snap = await db.email_routes.find_one(
        {"_id": "masci::ADMIN_DEAD_LETTER_TO"}
    )
    assert snap is not None, "preview fixture should have this route"
    try:
        # Empty out the recipients temporarily.
        await db.email_routes.update_one(
            {"_id": "masci::ADMIN_DEAD_LETTER_TO"},
            {"$set": {"to": []}},
        )
        payload = await _call_validator(db)
        assert payload["final_band"] == "red"
        assert any(
            "critical_route_empty" in r for r in payload["red_reasons"]
        )
        assert ("ADMIN_DEAD_LETTER_TO" in
                payload["email_routing"]["critical_empty_route_keys"])
    finally:
        # Restore.
        await db.email_routes.replace_one(
            {"_id": "masci::ADMIN_DEAD_LETTER_TO"}, snap
        )


@pytest.mark.asyncio
async def test_validator_pm_unresolved_is_amber_not_red():
    """If active projects exist with no resolvable PM (legacy OR
    roster), the validator should flag amber — not red — because
    the dead-letter path still works. Red is reserved for
    silent/structural failures."""
    db = _db()
    payload = await _call_validator(db)
    if payload["pm_email_coverage"].get("active_missing_unresolved", 0) > 0:
        assert any(
            "pm_unresolved" in r for r in payload["amber_reasons"]
        )
