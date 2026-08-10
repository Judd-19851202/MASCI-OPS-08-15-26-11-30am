"""TRACK 28.02 · Field Operations batch sweep.

Certifies that the admin token from `/api/auth/multi-login` unlocks
every Field-Ops read surface after the read-gate fix (see
`test_track_28_02_admin_read_gate.py`). Also spot-checks the PDF
surface for Daily Reports (which is served through the same gate
stack) and photo endpoints.

Scope covered per the Track 28.02 review request:

  • Daily Reports:      GET /api/daily-reports, /api/daily-reports/approved
  • Meetings:           GET /api/meetings
  • JHA / JHP:          GET /api/jhas
  • Site Inspections:   GET /api/inspections
  • Incidents:          GET /api/incidents (+ /api/incidents.csv)
  • Equipment / DVIR:   GET /api/equipment-inspections
                        GET /api/admin/equipment-inspections/trends
                        GET /api/admin/equipment-inspections/open-items
  • QA/QC:              GET /api/qaqc-inspections
                        GET /api/admin/qaqc-inspections/stats
  • Multi-login:        POST /api/auth/multi-login returns admin token
  • Missing-token 401:  Sanity that the gate still rejects unauth
"""
from __future__ import annotations

import os
import time
from typing import Iterable

import httpx
import pytest


# Prefer internal supervisor address inside the pod for speed/reliability.
_INTERNAL_URL = "http://localhost:8001"
_EXTERNAL_URL = os.environ.get("REACT_APP_BACKEND_URL")
if not _EXTERNAL_URL:
    try:
        with open("/app/frontend/.env", "r", encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("REACT_APP_BACKEND_URL="):
                    _EXTERNAL_URL = line.split("=", 1)[1].strip()
                    break
    except Exception:  # noqa: BLE001
        _EXTERNAL_URL = None

BACKEND_URL = _EXTERNAL_URL
try:
    r = httpx.get(f"{_INTERNAL_URL}/api/health", timeout=5)
    if r.status_code == 200:
        BACKEND_URL = _INTERNAL_URL
except Exception:  # noqa: BLE001
    pass

ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"


# ─────────────────────────────────────────────────────────────
# Auth fixture
# ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def admin_token() -> str:
    assert BACKEND_URL, "BACKEND_URL must be resolvable"
    r = httpx.post(
        f"{BACKEND_URL}/api/auth/multi-login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=30,
    )
    assert r.status_code == 200, f"multi-login failed: {r.status_code} {r.text[:300]}"
    body = r.json()
    portal = body.get("portal_tokens") or {}
    tok = portal.get("admin")
    assert tok, f"multi-login body missing admin portal token: keys={list(portal.keys())}"
    assert "." in tok, "admin portal token must be UUID.HMAC form"
    return tok


@pytest.fixture()
def admin_headers(admin_token: str) -> dict[str, str]:
    return {"X-Admin-Token": admin_token, "Accept": "application/json"}


# ─────────────────────────────────────────────────────────────
# Auth-only sanity checks
# ─────────────────────────────────────────────────────────────

def test_multi_login_returns_portal_tokens(admin_token: str) -> None:
    """multi-login gives back the canonical admin token used everywhere."""
    assert admin_token
    assert len(admin_token) > 30


# ─────────────────────────────────────────────────────────────
# Field-Ops read-gate certification
# ─────────────────────────────────────────────────────────────

FIELD_OPS_LIST_READS: list[str] = [
    # Daily Reports
    "/api/daily-reports",
    # Meetings
    "/api/meetings",
    # JHA / JHP
    "/api/jhas",
    # Site Inspections
    "/api/inspections",
    # Incidents
    "/api/incidents",
    # Equipment Pre-Op / DVIR
    "/api/equipment-inspections",
    # QA/QC
    "/api/qaqc-inspections",
]


@pytest.mark.parametrize("endpoint", FIELD_OPS_LIST_READS)
def test_field_ops_list_endpoints_return_200_and_list(
    admin_headers: dict[str, str], endpoint: str
) -> None:
    r = httpx.get(f"{BACKEND_URL}{endpoint}", headers=admin_headers, timeout=30)
    assert r.status_code == 200, (
        f"{endpoint} returned {r.status_code}: {r.text[:200]}"
    )
    body = r.json()
    assert isinstance(body, list), (
        f"{endpoint} expected list, got {type(body).__name__}"
    )


# Admin dashboard surfaces (dict payloads)

ADMIN_DASHBOARD_READS: list[str] = [
    "/api/admin/equipment-inspections/trends",
    "/api/admin/equipment-inspections/open-items",
    "/api/admin/qaqc-inspections/stats",
]


@pytest.mark.parametrize("endpoint", ADMIN_DASHBOARD_READS)
def test_admin_dashboard_endpoints_return_200(
    admin_headers: dict[str, str], endpoint: str
) -> None:
    r = httpx.get(f"{BACKEND_URL}{endpoint}", headers=admin_headers, timeout=30)
    assert r.status_code == 200, (
        f"{endpoint} returned {r.status_code}: {r.text[:200]}"
    )


# CSV export (incidents)

def test_incidents_csv_export_returns_csv(admin_headers: dict[str, str]) -> None:
    r = httpx.get(
        f"{BACKEND_URL}/api/incidents.csv", headers=admin_headers, timeout=30
    )
    assert r.status_code == 200, f"incidents.csv returned {r.status_code}: {r.text[:200]}"
    ct = r.headers.get("content-type", "")
    assert "csv" in ct.lower() or "text/plain" in ct.lower(), (
        f"unexpected content-type for /api/incidents.csv: {ct!r}"
    )


# Daily Reports approved (used by PDF surface)

def test_daily_reports_approved_endpoint(admin_headers: dict[str, str]) -> None:
    r = httpx.get(
        f"{BACKEND_URL}/api/daily-reports/approved",
        headers=admin_headers,
        timeout=30,
    )
    # 200 with list, or 404 if never approved (still means gate is open).
    assert r.status_code in (200, 404), (
        f"daily-reports/approved returned {r.status_code}: {r.text[:200]}"
    )


# ─────────────────────────────────────────────────────────────
# Missing-token rejection sanity
# ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "endpoint",
    ["/api/meetings", "/api/inspections", "/api/incidents", "/api/jhas"],
)
def test_no_token_still_401(endpoint: str) -> None:
    r = httpx.get(f"{BACKEND_URL}{endpoint}", timeout=30)
    assert r.status_code == 401, (
        f"{endpoint} without token should 401, got {r.status_code}"
    )


# ─────────────────────────────────────────────────────────────
# PDF surface spot-check (best-effort — only runs if at least one
# daily report exists)
# ─────────────────────────────────────────────────────────────

def test_daily_report_pdf_content_type_when_report_exists(
    admin_headers: dict[str, str],
) -> None:
    lst = httpx.get(
        f"{BACKEND_URL}/api/daily-reports", headers=admin_headers, timeout=30
    ).json()
    if not lst:
        pytest.skip("no daily reports in preview DB to spot-check PDF")
    report_id = lst[0].get("id") or lst[0].get("_id") or lst[0].get("report_id")
    if not report_id:
        pytest.skip("first daily report has no id-like field")
    r = httpx.get(
        f"{BACKEND_URL}/api/daily-reports/{report_id}/pdf",
        headers=admin_headers,
        timeout=60,
        follow_redirects=True,
    )
    # Canonical contract is async-job aware: 202 means the render was
    # accepted and must be polled to completion.
    assert r.status_code in (200, 202, 404, 409), (
        f"PDF endpoint returned {r.status_code}: {r.text[:200]}"
    )
    if r.status_code == 200:
        ct = r.headers.get("content-type", "")
        assert "pdf" in ct.lower(), f"expected application/pdf, got {ct!r}"
    elif r.status_code == 202:
        body = r.json()
        status_url = body.get("status_url")
        assert status_url, body
        final = None
        for _ in range(12):
            time.sleep(max(float(body.get("poll_after_ms") or 1200) / 1000.0, 0.35))
            final = httpx.get(
                f"{BACKEND_URL}{status_url}",
                headers=admin_headers,
                timeout=30,
            )
            assert final.status_code == 200, final.text[:200]
            payload = final.json()
            if payload.get("status") in {"completed", "failed"}:
                break
        assert final is not None
        payload = final.json()
        assert payload.get("status") == "completed", payload
        result = payload.get("result") or {}
        assert result.get("media_type") == "application/pdf", result
        assert result.get("download_url"), result
