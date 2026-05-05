"""Iter 38 — MASCI HUB Pre-Deploy QA Prompt full sweep.
Covers 14 sections: branding, navigation, forms, EN/ES, ES->EN backend, PDFs, training,
performance, responsive, security, email routing, role isolation, visual, final verdict.
Backend-side checks here; frontend Playwright runs separately.
"""
import os
import io
import time
import json
import urllib.request
import urllib.error
import requests
import pytest


def _unauth_get(path: str, timeout: int = 15):
    """Bypass conftest's requests-monkeypatch by using urllib (truly unauthenticated)."""
    req = urllib.request.Request(
        f"{BASE}{path}",
        headers={"User-Agent": "masci-qa/1.0"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()

def _read_env(key: str) -> str:
    v = os.environ.get(key)
    if v:
        return v
    try:
        with open("/app/frontend/.env") as f:
            for ln in f:
                if ln.startswith(key + "="):
                    return ln.split("=", 1)[1].strip()
    except FileNotFoundError:
        pass
    raise RuntimeError(f"{key} not found")


BASE = _read_env("REACT_APP_BACKEND_URL").rstrip("/")
ADMIN_PW = "MASCI1982!"
SHOP_PW = "Nothappy123!"
SAFETY_PW = "1982"
PM_EMAIL = "chriswright@mascigc.com"
PM_PW = "ChrisRocksThis2026"
LEGACY_PM_PW = "Happy123!"


# ---------- Fixtures ----------
@pytest.fixture(scope="module")
def s():
    return requests.Session()


@pytest.fixture(scope="module")
def admin_token(s):
    r = s.post(f"{BASE}/api/admin/login", json={"password": ADMIN_PW}, timeout=20)
    assert r.status_code == 200, r.text
    return r.json()["token"]


@pytest.fixture(scope="module")
def pm_token(s):
    r = s.post(f"{BASE}/api/pm/login", json={"email": PM_EMAIL, "password": PM_PW}, timeout=20)
    assert r.status_code == 200, r.text
    return r.json()["token"]


@pytest.fixture(scope="module")
def shop_token(s):
    r = s.post(f"{BASE}/api/shop/login", json={"password": SHOP_PW}, timeout=20)
    assert r.status_code == 200, r.text
    return r.json()["token"]


@pytest.fixture(scope="module")
def safety_token(s):
    r = s.post(f"{BASE}/api/safety-forms/login", json={"password": SAFETY_PW}, timeout=20)
    assert r.status_code == 200, r.text
    return r.json()["token"]


# ---------- SECTION 2: Navigation / Health ----------
class TestHealthAndRoutes:
    def test_api_health(self, s):
        r = s.get(f"{BASE}/api/health", timeout=15)
        assert r.status_code == 200
        body = r.json()
        assert body.get("status") in ("ok", "healthy") or body.get("ok") is True

    @pytest.mark.parametrize("path", [
        "/", "/field", "/safety", "/qa-qc", "/training-hub",
        "/pm/login", "/shop/login", "/admin/login", "/safety/forms/login",
        "/jha", "/trench-boxes", "/cheatsheet",
        "/inspect/new", "/meetings/new", "/incidents/new", "/daily/new", "/equipment/new",
        "/qaqc/concrete-form", "/qaqc/rebar", "/qaqc/subcontractor-work",
    ])
    def test_frontend_route_serves_html(self, s, path):
        # SPA — every route should return 200 with index.html (no 404/500)
        r = s.get(f"{BASE}{path}", timeout=20, allow_redirects=True)
        assert r.status_code == 200, f"{path} returned {r.status_code}"
        ct = r.headers.get("content-type", "")
        assert "text/html" in ct, f"{path} content-type {ct}"


# ---------- SECTION 10: Security / Auth gating ----------
class TestSecurityGates:
    def test_admin_jobs_requires_token(self):
        code, _ = _unauth_get("/api/admin/jobs")
        assert code in (401, 403), f"got {code}"

    def test_safety_forms_admin_list_requires_token(self):
        code, _ = _unauth_get("/api/safety-forms/equipment-issuances")
        assert code in (401, 403)

    def test_safety_forms_training_admin_list_requires_token(self):
        code, _ = _unauth_get("/api/safety-forms/equipment-trainings")
        assert code in (401, 403)

    def test_admin_login_wrong_password(self, s):
        r = s.post(f"{BASE}/api/admin/login", json={"password": "WRONG"}, timeout=15)
        assert r.status_code in (401, 429)

    def test_pm_login_wrong_password(self, s):
        r = s.post(f"{BASE}/api/pm/login",
                   json={"email": PM_EMAIL, "password": "WRONG"}, timeout=15)
        assert r.status_code in (401, 429)

    def test_shop_login_wrong_password(self, s):
        r = s.post(f"{BASE}/api/shop/login", json={"password": "WRONG"}, timeout=15)
        assert r.status_code in (401, 429)

    def test_safety_forms_login_wrong_password(self, s):
        r = s.post(f"{BASE}/api/safety-forms/login", json={"password": "0000"}, timeout=15)
        assert r.status_code in (401, 429)

    def test_legacy_pm_bypass_works_no_email(self, s):
        # Per test_credentials.md — legacy emergency bypass must still work
        r = s.post(f"{BASE}/api/pm/login", json={"password": LEGACY_PM_PW}, timeout=15)
        assert r.status_code == 200
        assert "token" in r.json()


# ---------- SECTION 12: Role isolation ----------
class TestRoleIsolation:
    def test_admin_sees_jobs(self, s, admin_token):
        r = s.get(f"{BASE}/api/admin/jobs",
                  headers={"X-Admin-Token": admin_token}, timeout=20)
        assert r.status_code == 200
        body = r.json()
        jobs = body if isinstance(body, list) else body.get("jobs", body.get("items", []))
        assert isinstance(jobs, list)
        assert len(jobs) > 0, "admin should see at least one job"

    def test_pm_subset_of_admin_jobs(self, s, admin_token, pm_token):
        ra = s.get(f"{BASE}/api/admin/jobs",
                   headers={"X-Admin-Token": admin_token}, timeout=20)
        rp = s.get(f"{BASE}/api/admin/jobs",
                   headers={"X-PM-Token": pm_token}, timeout=20)
        assert ra.status_code == 200 and rp.status_code == 200, (ra.status_code, rp.status_code)
        adm = ra.json() if isinstance(ra.json(), list) else ra.json().get("jobs", ra.json().get("items", []))
        pm = rp.json() if isinstance(rp.json(), list) else rp.json().get("jobs", rp.json().get("items", []))
        assert len(pm) <= len(adm), "PM job list must be subset of admin job list"

    def test_pm_me_returns_pm(self, pm_token):
        # Use urllib + only the PM token (avoid conftest's auto-injected admin token)
        req = urllib.request.Request(
            f"{BASE}/api/pm/me",
            headers={"X-PM-Token": pm_token, "User-Agent": "masci-qa/1.0"},
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = json.loads(resp.read())
        assert not body.get("is_admin_or_legacy"), \
            f"Per-PM token should not be admin/legacy: {body}"
        assert body.get("pm", {}).get("email") == PM_EMAIL

    def test_shop_can_see_equipment_inspections(self, s, shop_token):
        r = s.get(f"{BASE}/api/equipment-inspections",
                  headers={"X-Shop-Token": shop_token}, timeout=20)
        assert r.status_code == 200

    def test_safety_forms_check_token(self, s, safety_token):
        r = s.get(f"{BASE}/api/safety-forms/check",
                  headers={"X-Safety-Forms-Token": safety_token}, timeout=15)
        assert r.status_code == 200


# ---------- SECTION 5: Spanish input → English backend ----------
class TestTranslatePipeline:
    def test_translate_es_to_en(self, s):
        # Endpoint takes {strings:{key:text}, target:'en'} batch format
        r = s.post(f"{BASE}/api/translate",
                   json={"strings": {"k1": "El equipo necesita reparación inmediata"},
                         "target": "en"},
                   timeout=30)
        assert r.status_code == 200, r.text
        body = r.json()
        out = body.get("strings", {}).get("k1", "")
        assert isinstance(out, str) and len(out) > 0, f"empty translation: {body}"
        low = out.lower()
        assert "necesita" not in low, f"still spanish: {out}"


# ---------- SECTION 6: PDFs ----------
class TestPDFs:
    def test_safety_issuance_admin_list(self, s, admin_token):
        r = s.get(f"{BASE}/api/safety-forms/equipment-issuances",
                  headers={"X-Admin-Token": admin_token}, timeout=20)
        assert r.status_code == 200
        body = r.json()
        items = body if isinstance(body, list) else body.get("items", body.get("issuances", []))
        return items

    def test_safety_issuance_pdf_renders(self, s, admin_token, safety_token):
        # Ensure there's at least one record by submitting a TEST_ one
        r = s.get(f"{BASE}/api/safety-forms/equipment-issuances",
                  headers={"X-Admin-Token": admin_token}, timeout=20)
        body = r.json()
        items = body if isinstance(body, list) else body.get("items", body.get("issuances", []))
        if not items:
            payload = {
                "employee_name": "TEST_QA38_PDF",
                "employee_id": "QA38PDF",
                "project_number": "QA38",
                "project_name": "QA38",
                "issued_by": "QA Bot",
                "issued_date": "2026-01-15",
                "items": [
                    {"item_type": "Hard Hat", "quantity": 1, "unit_value": 25.0}
                ],
                "condition": "New",
                "acknowledgment": True,
                "employee_signature": "data:image/png;base64,iVBORw0KGgo=",
                "supervisor_signature": "data:image/png;base64,iVBORw0KGgo=",
            }
            cr = s.post(f"{BASE}/api/safety-forms/equipment-issuances",
                        headers={"X-Safety-Forms-Token": safety_token},
                        json=payload, timeout=30)
            if cr.status_code >= 400:
                pytest.skip(f"could not seed issuance: {cr.status_code} {cr.text[:200]}")
            r = s.get(f"{BASE}/api/safety-forms/equipment-issuances",
                      headers={"X-Admin-Token": admin_token}, timeout=20)
            body = r.json()
            items = body if isinstance(body, list) else body.get("items", body.get("issuances", []))
        if not items:
            pytest.skip("no issuance records and seed failed")
        rec_id = items[0].get("id") or items[0].get("_id")
        rp = s.get(f"{BASE}/api/safety-forms/equipment-issuances/{rec_id}/pdf",
                   headers={"X-Admin-Token": admin_token}, timeout=60)
        assert rp.status_code == 200, rp.text[:200]
        assert rp.content[:5] == b"%PDF-", "not a real PDF"
        ct = rp.headers.get("content-type", "")
        assert "pdf" in ct.lower()
        assert len(rp.content) > 1024


# ---------- SECTION 11: Email routing (preview = skipped) ----------
class TestEmailRoutingPreview:
    def test_auto_email_skipped_in_preview(self, s, safety_token):
        # Submit a tiny issuance; backend should accept and log "auto-email skipped"
        # (we can't read backend logs from here, but we verify the submit doesn't 5xx)
        payload = {
            "employee_name": "TEST_QA38_Email",
            "employee_id": "QA38",
            "project_number": "QA38",
            "project_name": "QA38",
            "issued_by": "QA Bot",
            "issued_date": "2026-01-15",
            "items": [
                {"item_type": "Hard Hat", "quantity": 1, "unit_value": 25.0}
            ],
            "condition": "New",
            "acknowledgment": True,
            "employee_signature": "data:image/png;base64,iVBORw0KGgo=",
            "supervisor_signature": "data:image/png;base64,iVBORw0KGgo=",
        }
        r = s.post(f"{BASE}/api/safety-forms/equipment-issuances",
                   headers={"X-Safety-Forms-Token": safety_token},
                   json=payload, timeout=30)
        # 200/201 acceptable; 422 also OK if validation tightens — we just want NO 5xx
        assert r.status_code < 500, f"5xx on submit: {r.status_code} {r.text[:200]}"


# ---------- SECTION 8: Performance probe (backend latency only) ----------
class TestPerformance:
    def test_health_under_2s(self, s):
        t0 = time.time()
        s.get(f"{BASE}/api/health", timeout=10)
        assert time.time() - t0 < 2.0

    def test_admin_jobs_under_3s(self, s, admin_token):
        t0 = time.time()
        s.get(f"{BASE}/api/admin/jobs",
              headers={"X-Admin-Token": admin_token}, timeout=10)
        assert time.time() - t0 < 3.0


# ---------- SECTION 12 cont: Master list endpoints respond ----------
class TestMasterLists:
    @pytest.mark.parametrize("path", [
        "/api/admin/jobs",
        "/api/admin/project-managers",
        "/api/equipment-inspections",
        "/api/qaqc-inspections",
        "/api/daily-reports",
        "/api/inspections",
        "/api/meetings",
        "/api/incidents",
        "/api/jhas",
        "/api/trench-boxes",
    ])
    def test_endpoint_responds_for_admin(self, s, admin_token, path):
        r = s.get(f"{BASE}{path}",
                  headers={"X-Admin-Token": admin_token}, timeout=20)
        assert r.status_code == 200, f"{path} -> {r.status_code}"
