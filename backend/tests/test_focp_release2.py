"""FOCP Release 2 · TR-0001 + TR-0002 integration tests.

Hits the preview backend via REACT_APP_BACKEND_URL. Covers:
  • Endpoint registration (no 404)
  • Auth gates (admin-only endpoints reject unauthenticated callers)
  • Public POST /jha-acknowledgements validation cases
  • workflow_undo bad-workflow + missing-record paths
  • Recovery stream admin gate

This file uses ``requests`` and is meant to be run via:

    python -m pytest backend/tests/test_focp_release2.py -x

Production-key handling: admin endpoints expect an ADMIN_PASSWORD-derived
token; we read ADMIN_PASSWORD from the preview .env (NEVER from chat) and
only run the admin checks when present.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
import requests

# Reach the preview backend the same way the frontend does.
ENV_PATH = Path(__file__).resolve().parents[2] / "frontend" / ".env"
BACKEND_URL = ""
if ENV_PATH.exists():
    for line in ENV_PATH.read_text().splitlines():
        if line.startswith("REACT_APP_BACKEND_URL="):
            BACKEND_URL = line.split("=", 1)[1].strip()
            break

if not BACKEND_URL:
    pytest.skip("REACT_APP_BACKEND_URL not configured", allow_module_level=True)

API = f"{BACKEND_URL}/api"
TIMEOUT = 30


def test_health():
    r = requests.get(f"{API}/health", timeout=30)
    assert r.status_code == 200


# ── TR-0001 ─────────────────────────────────────────────────────

def test_ack_me_empty_returns_empty_list_for_no_email():
    r = requests.get(f"{API}/jha-acknowledgements/me", timeout=30)
    assert r.status_code == 200
    body = r.json()
    assert body == {"items": [], "count": 0}


def test_ack_post_rejects_missing_body():
    r = requests.post(f"{API}/jha-acknowledgements", json={}, timeout=30)
    assert r.status_code in (400, 422)


def test_ack_post_rejects_signature_too_short():
    r = requests.post(
        f"{API}/jha-acknowledgements",
        json={
            "project_number": "DOES-NOT-EXIST-999",
            "jha_file_id": "no-such-file",
            "employee_email": "noone@example.com",
            "signature": "x",
        },
        timeout=30,
    )
    assert r.status_code == 422
    detail = r.json().get("detail") or {}
    assert detail.get("code") == "signature_required_min3"


def test_ack_post_rejects_unknown_employee():
    r = requests.post(
        f"{API}/jha-acknowledgements",
        json={
            "project_number": "DOES-NOT-EXIST-999",
            "jha_file_id": "no-such-file",
            "employee_email": "noone@noonemascigc.example",
            "signature": "Jane Doe",
        },
        timeout=30,
    )
    # Either employee_not_found OR employee_email_invalid (regex catches
    # malformed emails first); both prove validation is wired.
    assert r.status_code in (404, 422)
    code = (r.json().get("detail") or {}).get("code", "")
    assert code in ("employee_not_found", "employee_email_invalid")


def test_ack_admin_endpoints_require_admin():
    """Use explicit empty X-Admin-Token so conftest.py's setdefault
    doesn't auto-attach the real admin token."""
    bypass = {"X-Admin-Token": ""}
    for path in (
        "/jha-acknowledgements/by-project/X",
        "/jha-acknowledgements/by-employee/Y",
        "/jha-acknowledgements/compliance",
    ):
        r = requests.get(f"{API}{path}", headers=bypass, timeout=30)
        assert r.status_code in (401, 403), f"{path} not admin-gated: {r.status_code}"


# ── TR-0002 ─────────────────────────────────────────────────────

def test_undo_endpoint_admin_gated():
    r = requests.post(
        f"{API}/workflows/incident/anything/undo-last-transition",
        json={"reason": "test reason"},
        headers={"X-Admin-Token": ""},
        timeout=30,
    )
    assert r.status_code in (401, 403)


def test_recovery_stream_admin_gated():
    r = requests.get(f"{API}/admin/recovery/transitions",
                     headers={"X-Admin-Token": ""}, timeout=30)
    assert r.status_code in (401, 403)


def test_last_transition_admin_gated():
    r = requests.get(
        f"{API}/workflows/incident/anything/last-transition",
        headers={"X-Admin-Token": ""},
        timeout=30,
    )
    assert r.status_code in (401, 403)


# ── Admin-token paths (only when ADMIN_PASSWORD is present) ─────

def _admin_token():
    """Build the admin token the same way server.py does."""
    pw = os.environ.get("ADMIN_PASSWORD", "")
    if not pw:
        # Try to read from backend/.env
        bp = Path(__file__).resolve().parents[1] / ".env"
        if bp.exists():
            for line in bp.read_text().splitlines():
                if line.startswith("ADMIN_PASSWORD="):
                    pw = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    if not pw:
        return None
    # Re-use the same HMAC the server uses. Import server module.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from server import _admin_token_for  # noqa: PLC0415
    return _admin_token_for(pw)


def test_admin_recovery_stream_succeeds_with_token():
    tok = _admin_token()
    if not tok:
        pytest.skip("ADMIN_PASSWORD not present in environment")
    r = requests.get(
        f"{API}/admin/recovery/transitions",
        headers={"X-Admin-Token": tok},
        timeout=30,
    )
    assert r.status_code == 200
    body = r.json()
    assert "events" in body
    assert "supported_workflows" in body
    assert set(body["supported_workflows"]) >= {
        "incident", "daily_report", "qaqc_inspection",
        "site_inspection", "payroll_variance",
    }


def test_admin_compliance_succeeds_with_token():
    tok = _admin_token()
    if not tok:
        pytest.skip("ADMIN_PASSWORD not present in environment")
    r = requests.get(
        f"{API}/jha-acknowledgements/compliance",
        headers={"X-Admin-Token": tok},
        timeout=30,
    )
    assert r.status_code == 200
    body = r.json()
    assert "projects" in body
    assert "totals" in body


def test_admin_undo_unsupported_workflow_returns_422():
    tok = _admin_token()
    if not tok:
        pytest.skip("ADMIN_PASSWORD not present in environment")
    r = requests.post(
        f"{API}/workflows/not-a-workflow/abc/undo-last-transition",
        headers={"X-Admin-Token": tok, "Content-Type": "application/json"},
        json={"reason": "five chars minimum"},
        timeout=30,
    )
    assert r.status_code == 422
    code = (r.json().get("detail") or {}).get("code", "")
    assert code == "workflow_not_supported"


def test_admin_undo_short_reason_returns_422():
    tok = _admin_token()
    if not tok:
        pytest.skip("ADMIN_PASSWORD not present in environment")
    r = requests.post(
        f"{API}/workflows/incident/anything/undo-last-transition",
        headers={"X-Admin-Token": tok, "Content-Type": "application/json"},
        json={"reason": "x"},
        timeout=30,
    )
    assert r.status_code == 422
    code = (r.json().get("detail") or {}).get("code", "")
    assert code == "undo_reason_required_min5"


def test_admin_undo_missing_record_returns_404():
    tok = _admin_token()
    if not tok:
        pytest.skip("ADMIN_PASSWORD not present in environment")
    r = requests.post(
        f"{API}/workflows/incident/this-record-id-does-not-exist-9999/undo-last-transition",
        headers={"X-Admin-Token": tok, "Content-Type": "application/json"},
        json={"reason": "structural integration test"},
        timeout=30,
    )
    assert r.status_code == 404
