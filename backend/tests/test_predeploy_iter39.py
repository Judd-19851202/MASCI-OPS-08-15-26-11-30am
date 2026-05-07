"""
Iter 39 Pre-Deploy regression suite.

Targets the specific bug classes that previous sweeps missed:
  (a) PDF render produces no escaped HTML (literal '<div', '&lt;' etc.)
  (b) all admin endpoints exist and require token (401 without)
  (c) Safety Forms login accepts 1982 and rejects wrong passwords
  (d) translation endpoint accepts and returns ES->EN
  (e) Activities Performed / Work Performed actually appear in Daily Report PDF
  (f) photo upload payloads accepted and persisted
  (g) PM scoping: chris cannot see admin-only data, PM token rejected on admin endpoints
"""
import os
import io
import urllib.request
import urllib.error
import json
import base64
import pytest
import requests
from pypdf import PdfReader

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/") or os.environ.get("PUBLIC_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    # Fallback to the value in /app/frontend/.env
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip().rstrip("/")
                break

ADMIN_PW = "MASCI1982!"
PM_EMAIL = "chriswright@mascigc.com"
PM_PW = "ChrisRocksThis2026"
SHOP_PW = "Nothappy123!"
SAFETY_PW = "1982"

# 1x1 PNG data URL (real bytes)
TINY_PNG_DATA_URL = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
)


_DEFAULT_HEADERS = {"User-Agent": "Mozilla/5.0 (iter39-qa-bot) Chrome/120 Safari/537.36"}


def _raw_get(path, headers=None):
    """urllib-based GET that bypasses any conftest monkeypatching."""
    h = dict(_DEFAULT_HEADERS)
    if headers:
        h.update(headers)
    req = urllib.request.Request(BASE_URL + path, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def _raw_post(path, body, headers=None):
    h = dict(_DEFAULT_HEADERS)
    h["Content-Type"] = "application/json"
    if headers:
        h.update(headers)
    req = urllib.request.Request(
        BASE_URL + path,
        data=json.dumps(body).encode(),
        headers=h,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


@pytest.fixture(scope="module")
def admin_token():
    code, body = _raw_post("/api/admin/login", {"password": ADMIN_PW})
    assert code == 200, f"admin login failed: {code} {body[:200]}"
    return json.loads(body)["token"]


@pytest.fixture(scope="module")
def pm_token():
    code, body = _raw_post("/api/pm/login", {"email": PM_EMAIL, "password": PM_PW})
    assert code == 200, f"pm login failed: {code} {body[:200]}"
    return json.loads(body)["token"]


@pytest.fixture(scope="module")
def safety_token():
    code, body = _raw_post("/api/safety-forms/login", {"password": SAFETY_PW})
    assert code == 200, f"safety login failed: {code} {body[:200]}"
    return json.loads(body)["token"]


# --- AUTH GATES ---
class TestAuthGates:
    def test_admin_wrong_pw(self):
        code, _ = _raw_post("/api/admin/login", {"password": "wrong"})
        assert code == 401

    def test_safety_wrong_pw(self):
        code, _ = _raw_post("/api/safety-forms/login", {"password": "0000"})
        assert code == 401

    def test_safety_correct_pw(self):
        code, body = _raw_post("/api/safety-forms/login", {"password": SAFETY_PW})
        assert code == 200
        assert "token" in json.loads(body)

    def test_pm_wrong_pw(self):
        code, _ = _raw_post("/api/pm/login", {"email": PM_EMAIL, "password": "wrong"})
        assert code == 401


# --- ADMIN ENDPOINTS REQUIRE TOKEN ---
ADMIN_ENDPOINTS = [
    "/api/admin/jobs",
    "/api/admin/projects/list",
    "/api/admin/equipment-inspections/trends",
    "/api/admin/equipment-inspections/open-items",
    "/api/admin/qaqc-inspections/stats",
    "/api/safety-forms/equipment-issuances",
    "/api/safety-forms/equipment-trainings",
    "/api/admin/project-managers/activity",
]


@pytest.mark.parametrize("path", ADMIN_ENDPOINTS)
def test_admin_endpoint_requires_token(path):
    code, _ = _raw_get(path)
    assert code in (401, 403), f"{path} returned {code}, expected 401/403"


@pytest.mark.parametrize("path", ADMIN_ENDPOINTS)
def test_admin_endpoint_with_token(path, admin_token):
    code, body = _raw_get(path, headers={"X-Admin-Token": admin_token})
    assert code == 200, f"{path} returned {code} for admin token: {body[:150]}"


# --- PM SCOPING ---
class TestPmScoping:
    def test_pm_cannot_hit_admin_only(self, pm_token):
        # activity endpoint is admin-strict; safety-forms admin lists are admin-strict
        for path in ["/api/admin/project-managers/activity", "/api/safety-forms/equipment-issuances"]:
            code, _ = _raw_get(path, headers={"X-PM-Token": pm_token})
            assert code in (401, 403), f"PM token MUST NOT access {path} (got {code})"

    def test_pm_jobs_subset_of_admin(self, pm_token, admin_token):
        c1, b1 = _raw_get("/api/admin/jobs", headers={"X-Admin-Token": admin_token})
        c2, b2 = _raw_get("/api/admin/jobs", headers={"X-PM-Token": pm_token})
        assert c1 == 200 and c2 == 200
        admin_jobs = json.loads(b1)
        pm_jobs = json.loads(b2)
        if isinstance(admin_jobs, dict):
            admin_jobs = admin_jobs.get("jobs") or admin_jobs.get("items") or []
        if isinstance(pm_jobs, dict):
            pm_jobs = pm_jobs.get("jobs") or pm_jobs.get("items") or []
        assert len(pm_jobs) > 0, "PM should see >0 assigned jobs"
        assert len(pm_jobs) < len(admin_jobs), (
            f"PM scoping broken: PM sees {len(pm_jobs)} vs admin {len(admin_jobs)}"
        )


# --- TRANSLATE ---
class TestTranslate:
    def test_es_to_en(self):
        code, body = _raw_post("/api/translate", {"strings": {"a": "El equipo necesita reparación inmediata"}, "target": "en"})
        assert code == 200
        data = json.loads(body)
        # API may return {strings:{...}} or list shape - accept either
        out = data.get("strings") or data
        text = json.dumps(out).lower()
        assert "equipment" in text or "repair" in text, f"ES->EN translate looks wrong: {text[:200]}"


# --- PDF GENERATION + ESCAPED-HTML CHECK ---
def _extract_pdf_text(pdf_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    return "\n".join((p.extract_text() or "") for p in reader.pages)


def _assert_no_escaped_html(text: str, ctx: str):
    bad = ["<div", "<b>", "<span", "&lt;div", "&lt;b&gt;", "&lt;span", "<p>", "</p>"]
    found = [t for t in bad if t in text]
    assert not found, f"{ctx}: escaped/literal HTML found in PDF text: {found}"


def _assert_pdf_magic(b: bytes):
    assert b[:4] == b"%PDF", f"Not a real PDF (first 8 bytes: {b[:8]!r})"


class TestPdfRenders:
    """Render each PDF directly via pdf_render.render_record_pdf and inspect output.

    Note: only safety-forms exposes a /pdf HTTP endpoint; the other 5 kinds are emailed
    or zipped, so we test them via the same render path used in production.
    """

    def _import_render(self):
        import sys
        sys.path.insert(0, "/app/backend")
        from pdf_render import render_record_pdf  # type: ignore
        return render_record_pdf

    def test_safety_issuance_pdf_no_escaped_html(self, safety_token, admin_token):
        payload = {
            "employee_name": "TEST_ITER39 Worker",
            "employee_id": "EMP-T39",
            "project_number": "TEST",
            "project_name": "Iter39 PDF Test",
            "location": "Yard",
            "issued_by": "QA Bot",
            "issued_date": "2026-01-15",
            "condition": "New",
            "items": [{"item_type": "Hard Hat", "description": "Standard hard hat L", "quantity": 1, "unit_value": 25}],
            "acknowledgment": True,
            "supervisor_signature": TINY_PNG_DATA_URL,
            "employee_signature": TINY_PNG_DATA_URL,
            "photos": [TINY_PNG_DATA_URL],
        }
        code, body = _raw_post(
            "/api/safety-forms/equipment-issuances", payload,
            headers={"X-Safety-Forms-Token": safety_token},
        )
        assert code in (200, 201), f"create failed {code}: {body[:300]}"
        rec_id = json.loads(body).get("id") or json.loads(body).get("_id")
        assert rec_id
        c2, pdf = _raw_get(
            f"/api/safety-forms/equipment-issuances/{rec_id}/pdf",
            headers={"X-Admin-Token": admin_token},
        )
        assert c2 == 200, f"pdf fetch {c2}"
        _assert_pdf_magic(pdf)
        assert len(pdf) > 4000
        text = _extract_pdf_text(pdf)
        _assert_no_escaped_html(text, "safety-issuance")
        assert "TEST_ITER39" in text or "Worker" in text

    def test_daily_report_pdf_includes_activities_and_no_escaped_html(self):
        render = self._import_render()
        record = {
            "id": "iter39-dr",
            "report_date": "2026-01-15",
            "project_number": "TEST",
            "project_name": "Iter39 DR Test",
            "location": "Iter39 Site",
            "prepared_by": "QA Foreman",
            "weather_summary": "Clear",
            "general_notes": "ITER39_GENERAL_NOTES_MARKER plain prose work performed text.",
            "activities": [{"activity": "ITER39_ACTIVITY_MARKER concrete pour col A",
                            "notes": "ITER39_ACTIVITY_NOTES extra detail"}],
            "masci_crews": [{"name": "John Smith", "trade": "Carpenter", "hours": 8}],
            "photos": [TINY_PNG_DATA_URL] * 2,
            "prepared_by_signature": TINY_PNG_DATA_URL,
        }
        pdf = render("daily-report", record)
        _assert_pdf_magic(pdf)
        assert len(pdf) > 5000, f"DR PDF too small: {len(pdf)}"
        text = _extract_pdf_text(pdf)
        _assert_no_escaped_html(text, "daily-report")
        assert "ITER39_ACTIVITY_MARKER" in text, "Activities Performed empty (Leandro bug)"
        assert "ITER39_GENERAL_NOTES_MARKER" in text, "General notes missing"
        assert "ForgedOps" in text

    def test_inspection_pdf_no_escaped_html(self):
        render = self._import_render()
        record = {
            "id": "iter39-insp",
            "inspection_date": "2026-01-15",
            "inspection_time": "10:00",
            "project_number": "TEST",
            "project_name": "Iter39 Insp",
            "location": "Iter39 Site",
            "inspector_name": "ITER39_INSPECTOR",
            "foreman_name": "ITER39_FOREMAN",
            "work_activity": "ITER39_OBS plain inspection text.",
            "photos": [TINY_PNG_DATA_URL],
            "inspector_signature": TINY_PNG_DATA_URL,
        }
        pdf = render("inspection", record)
        _assert_pdf_magic(pdf)
        text = _extract_pdf_text(pdf)
        _assert_no_escaped_html(text, "inspection")
        assert "ITER39_INSPECTOR" in text or "ITER39_OBS" in text

    def test_qaqc_pdf_no_escaped_html(self):
        render = self._import_render()
        record = {
            "id": "iter39-qa",
            "form_type": "concrete_form",
            "form_label": "Concrete Form Inspection",
            "inspection_date": "2026-01-15",
            "project_number": "TEST",
            "project_name": "Iter39 QAQC",
            "inspector_name": "ITER39_QA_INSPECTOR",
            "general_notes": "ITER39_QA_NOTES plain text",
            "items": [{"label": "Forms aligned", "status": "PASS"}],
            "photos": [TINY_PNG_DATA_URL] * 4,
            "inspector_signature": TINY_PNG_DATA_URL,
        }
        pdf = render("qaqc", record)
        _assert_pdf_magic(pdf)
        text = _extract_pdf_text(pdf)
        _assert_no_escaped_html(text, "qaqc")

    def test_equipment_inspection_pdf_no_escaped_html(self):
        render = self._import_render()
        record = {
            "id": "iter39-eq",
            "inspection_date": "2026-01-15",
            "project_name": "Iter39 EQ",
            "project_number": "TEST",
            "operator_name": "ITER39_OP",
            "unit_id": "TR-001",
            "make": "Cat", "model": "320",
            "general_notes": "ITER39_EQ_NOTES",
            "items": [{"label": "Brakes", "status": "PASS"}],
            "photos": [TINY_PNG_DATA_URL],
            "operator_signature": TINY_PNG_DATA_URL,
        }
        pdf = render("equipment-inspection", record)
        _assert_pdf_magic(pdf)
        text = _extract_pdf_text(pdf)
        _assert_no_escaped_html(text, "equipment-inspection")


# --- HEALTH ---
def test_health():
    code, _ = _raw_get("/api/")
    assert code in (200, 404)  # tolerate either depending on root mount
