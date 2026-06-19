"""DR-FIX-1 · Constitutional Remediation Sprint regression.

Covers R1 (production surface), R2 (constraints surface), R3 (schedule_delays
PDF key fix). Pure end-to-end: POST a DR with production rows + constraint
rows + schedule_delays=Yes, then verify Mongo storage + PDF rendering.

Doctrine: /app/memory/DR_AUDIT_001_FULL_CONSTITUTIONAL_AUDIT.md
"""
from __future__ import annotations
import asyncio
import json
import os
import urllib.error
import urllib.request
from typing import Dict, Any, Optional

import pytest


BACKEND = os.environ.get("BACKEND_URL", "http://localhost:8001")
API = f"{BACKEND}/api"


def _req(method: str, path: str, *, body: Optional[Dict[str, Any]] = None,
         token: str = "", token_header: str = "X-Admin-Token",
         accept_json: bool = True) -> Dict[str, Any]:
    url = f"{API}{path}"
    data = None
    headers = {"Content-Type": "application/json"}
    if token:
        headers[token_header] = token
    if body is not None:
        data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
            if accept_json:
                try:
                    return {"status": resp.status, "json": json.loads(raw.decode() or "{}")}
                except Exception:
                    return {"status": resp.status, "raw": raw}
            return {"status": resp.status, "raw": raw}
    except urllib.error.HTTPError as e:
        body_txt = e.read().decode()
        try:
            parsed = json.loads(body_txt)
        except Exception:
            parsed = {"detail": body_txt}
        return {"status": e.code, "json": parsed}


@pytest.fixture(scope="module")
def admin_token():
    pwd = os.environ.get("ADMIN_PASSWORD", "Maddix123!")
    r = _req("POST", "/admin/login", body={"password": pwd})
    assert r["status"] == 200, r
    return r["json"]["token"]


@pytest.fixture(scope="module")
def submitted_dr(admin_token):
    """Submit a DR with all three failure modes exercised."""
    body = {
        "project_name": "DR-FIX-1 · Pytest Project",
        "project_number": "JOB-FIX1-PYTEST",
        "location": "Test Site",
        "report_date": "2026-06-08",
        "prepared_by": "Pytest Foreman",
        "superintendent": "Pytest Super",
        "weather_summary": "Sunny · 78°F",
        # R3 · canonical key
        "schedule_delays": "Yes",
        "schedule_delays_notes": "Delayed by survey",
        "weather_impact": "No",
        "safety_incidents_today": "No",
        "injuries_reported": "No",
        "general_notes": "DR-FIX-1 regression doc",
        # Required min photo content (1×1 px PNG)
        "photos": [
            "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkAAIAAAoAAv/lxKUAAAAASUVORK5CYII="
        ] * 6,
        # R1 · structured production rows
        "production": [
            {"description": "RCP install", "quantity": 250, "unit": "LF",
             "station_from": "12+50", "station_to": "13+00",
             "notes": "Pytest R1 production row 1"},
            {"description": "Type S-III mat", "quantity": 800, "unit": "TON",
             "notes": "Pytest R1 production row 2"},
        ],
        # R2 · structured constraint rows (one weather, one utility)
        "constraints": [
            {"constraint_type": "weather", "hours_impact": 1.5,
             "notes": "Pytest R2 weather constraint"},
            {"constraint_type": "utility", "hours_impact": 3.0,
             "notes": "Pytest R2 utility constraint"},
        ],
        # Signatures (1×1 PNG base64)
        "prepared_by_signature": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkAAIAAAoAAv/lxKUAAAAASUVORK5CYII=",
    }
    r = _req("POST", "/daily-reports", token=admin_token, body=body)
    assert r["status"] == 200, f"Submit failed: {r}"
    return r["json"]


# ── R3 · schedule_delays canonical key ─────────────────────────────
def test_r3_schedule_delays_stored_correctly(submitted_dr, admin_token):
    """R3: Mongo persists `schedule_delays` (not `schedule_delay_today`)."""
    r = _req("GET", f"/daily-reports/{submitted_dr['id']}", token=admin_token)
    assert r["status"] == 200, r
    assert r["json"].get("schedule_delays") == "Yes"


def test_r3_pdf_renders_schedule_delays_value(submitted_dr, admin_token):
    """R3: PDF Section 03 must include 'Schedule Delays · Yes'."""
    from pdf_render import render_record_pdf  # noqa: PLC0415
    # Use the freshly persisted record to drive the renderer.
    r = _req("GET", f"/daily-reports/{submitted_dr['id']}", token=admin_token)
    pdf_bytes = render_record_pdf("daily-report", r["json"])
    assert pdf_bytes and len(pdf_bytes) > 1000, "PDF appears empty"
    # render_record_pdf returns bytes — we substring-check the underlying
    # HTML by also calling the html renderer directly.
    from pdf_render import render_email_html  # noqa: PLC0415
    html = render_email_html("daily-report", r["json"])
    # The HTML renderer emits a brief blurb; the meaningful surface is
    # the PDF HTML which we can also fetch through the same internal
    # body builder.
    from pdf_render import _render_daily  # noqa: PLC0415
    inner = _render_daily(r["json"])
    assert "Schedule Delays" in inner, "R3 label missing — canonical key not surfaced"
    assert ">Yes<" in inner, "R3 value 'Yes' not rendered next to Schedule Delays"
    # And the broken key must NOT be substituted as a fallback path.
    assert "Schedule Delay Today" not in inner, "R3 stale label still present"


# ── R1 · Production surfaced on PDF ─────────────────────────────────
def test_r1_production_persisted(submitted_dr, admin_token):
    r = _req("GET", f"/daily-reports/{submitted_dr['id']}", token=admin_token)
    prods = r["json"].get("production") or []
    assert len(prods) == 2, f"Expected 2 production rows, got {len(prods)}"
    assert prods[0]["description"] == "RCP install"
    assert prods[0]["unit"] == "LF"
    assert prods[1]["unit"] == "TON"


def test_r1_pdf_renders_production_section(submitted_dr, admin_token):
    from pdf_render import _render_daily  # noqa: PLC0415
    r = _req("GET", f"/daily-reports/{submitted_dr['id']}", token=admin_token)
    inner = _render_daily(r["json"])
    assert "09b" in inner and "Production" in inner, "R1 Production section missing"
    assert "RCP install" in inner, "R1 row content not rendered"
    assert "Type S-III mat" in inner, "R1 second row not rendered"
    assert "LF" in inner and "TON" in inner


def test_r1_pdf_omits_production_section_when_empty(admin_token):
    """The new section must NOT appear when production[] is empty."""
    from pdf_render import _render_daily  # noqa: PLC0415
    minimal = {
        "project_name": "X", "report_date": "2026-06-08",
        "prepared_by": "Tester", "production": [], "constraints": [],
    }
    inner = _render_daily(minimal)
    assert "09b" not in inner
    assert "09c" not in inner


# ── R2 · Constraints surfaced on PDF ────────────────────────────────
def test_r2_constraints_persisted_with_advisory_flags(submitted_dr, admin_token):
    r = _req("GET", f"/daily-reports/{submitted_dr['id']}", token=admin_token)
    cons = r["json"].get("constraints") or []
    assert len(cons) == 2, f"Expected 2 constraint rows, got {len(cons)}"
    # Server-derived advisory flags: weather → schedule, utility → RFI+schedule
    weather = next(c for c in cons if c["constraint_type"] == "weather")
    utility = next(c for c in cons if c["constraint_type"] == "utility")
    assert weather["may_affect_schedule"] is True
    assert weather["may_require_rfi"] is False
    assert utility["may_require_rfi"] is True
    assert utility["may_affect_schedule"] is True


def test_r2_pdf_renders_constraints_section(submitted_dr, admin_token):
    from pdf_render import _render_daily  # noqa: PLC0415
    r = _req("GET", f"/daily-reports/{submitted_dr['id']}", token=admin_token)
    inner = _render_daily(r["json"])
    assert "09c" in inner and ("Constraints" in inner or "Delays" in inner)
    assert "weather" in inner.lower()
    assert "utility" in inner.lower()
    # Advisory flags surfaced
    assert "RFI" in inner
    assert "Schedule" in inner
    # Hours impact
    assert "1.5 h" in inner or "1.5" in inner
    assert "3.0 h" in inner or "3" in inner


# ── R1+R2 · ViewDailyReport contract (frontend source-level check) ──
def test_view_daily_report_renders_production_and_constraints():
    """Static guard: ViewDailyReport.jsx must reference the new testids
    and the structured fields. Prevents accidental regression of the
    frontend surfaces."""
    path = "/app/frontend/src/pages/ViewDailyReport.jsx"
    src = open(path, "r", encoding="utf-8").read()
    assert 'data-testid="dr-view-production"' in src, "Production testid missing"
    assert 'data-testid="dr-view-constraints"' in src, "Constraints testid missing"
    assert "data.production" in src
    assert "data.constraints" in src
    assert "may_require_rfi" in src
    assert "may_affect_schedule" in src


def test_r3_pdf_render_no_stale_key():
    """Static guard: the pdf_render.py module must not read the broken
    `schedule_delay_today` key any longer."""
    src = open("/app/backend/pdf_render.py", "r", encoding="utf-8").read()
    assert 'd.get("schedule_delay_today")' not in src, (
        "Stale schedule_delay_today key still present — R3 regression"
    )
    assert 'd.get("schedule_delays")' in src, (
        "Canonical schedule_delays key missing from PDF renderer"
    )
