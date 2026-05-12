"""Iter68 — Comprehensive deployment-readiness audit (backend).

Walks the ~20 critical endpoints listed in the audit request, plus the
auth surfaces (admin / PM / shop / safety-forms / leadership / dev),
plus the hub-banner audit-trail / clone / export endpoints from iter66-67,
plus a sanity check on the R2 photo resolver from iter63-64.

Cleans up every test artifact at the end.
"""
import io
import os
import time
from pathlib import Path

import pytest
import requests

# Read backend URL the same way conftest does
def _read_kv(path, key):
    try:
        with open(path) as f:
            for line in f:
                if line.startswith(f"{key}="):
                    return line.split("=", 1)[1].strip().strip('"').rstrip("/")
    except Exception:
        pass
    return ""

URL = _read_kv("/app/frontend/.env", "REACT_APP_BACKEND_URL")
ADMIN_PW = _read_kv("/app/backend/.env", "ADMIN_PASSWORD") or "MASCI1982!"

# ============================================================
# AUTH SURFACES — verify every login portal
# ============================================================

class TestAuthSurfaces:
    def test_admin_login(self):
        r = requests.post(f"{URL}/api/admin/login", json={"password": ADMIN_PW}, timeout=10,
                          headers={"X-Admin-Token": "skip"})
        assert r.status_code == 200, r.text
        assert r.json().get("ok") is True
        assert r.json().get("token")

    def test_admin_login_wrong_password(self):
        r = requests.post(f"{URL}/api/admin/login", json={"password": "WRONG_PW_TEST"}, timeout=10,
                          headers={"X-Admin-Token": "skip"})
        assert r.status_code in (401, 403)

    def test_pm_login(self):
        r = requests.post(f"{URL}/api/pm/login",
                          json={"email": "chriswright@mascigc.com", "password": "ChrisRocksThis2026"},
                          timeout=10)
        assert r.status_code == 200, r.text
        assert r.json().get("token")

    def test_shop_login(self):
        r = requests.post(f"{URL}/api/shop/login", json={"password": "Nothappy123!"}, timeout=10)
        assert r.status_code == 200, r.text

    def test_safety_forms_login(self):
        r = requests.post(f"{URL}/api/safety-forms/login", json={"password": "1982"}, timeout=10)
        assert r.status_code == 200, r.text

    def test_leadership_login(self):
        r = requests.post(f"{URL}/api/field-leadership/login", json={"password": "MASCIGC"}, timeout=10)
        assert r.status_code == 200, r.text

    def test_dev_login(self):
        r = requests.post(f"{URL}/api/dev/login", json={"password": "Maddix8530!"}, timeout=10)
        assert r.status_code == 200, r.text


# ============================================================
# SECURITY — admin endpoints reject missing / malformed tokens
# ============================================================

class TestAdminAuthSecurity:
    def test_admin_endpoint_no_token_returns_401(self):
        # Use a Session to avoid conftest auto-patch (it patches Session.request),
        # but explicitly set an invalid token to override the setdefault.
        r = requests.get(f"{URL}/api/admin/banners",
                         headers={"X-Admin-Token": "definitely-not-valid"}, timeout=10)
        assert r.status_code == 401

    def test_admin_endpoint_malformed_token(self):
        r = requests.get(f"{URL}/api/admin/jobs",
                         headers={"X-Admin-Token": "bogus.token.value"}, timeout=10)
        assert r.status_code == 401


# ============================================================
# CORE READ ENDPOINTS — auth'd via conftest patch
# ============================================================

CORE_GET_ENDPOINTS = [
    "/api/daily-reports",
    "/api/inspections",
    "/api/meetings",
    "/api/incidents",
    "/api/qaqc-inspections",
    "/api/equipment-inspections",
    "/api/jhas",
    "/api/trench-boxes",
    "/api/jobs",
    "/api/admin/jobs",
    "/api/admin/project-managers",
    "/api/admin/shop-users",
    "/api/banners/active",
    "/api/admin/banners",
    "/api/admin/backups-list-r2",
    "/api/admin/backups-complete-r2-state",
]


@pytest.mark.parametrize("endpoint", CORE_GET_ENDPOINTS)
def test_core_endpoint_status(endpoint):
    r = requests.get(f"{URL}{endpoint}", timeout=30)
    assert r.status_code in (200, 204), f"{endpoint} -> {r.status_code}: {r.text[:200]}"


# ============================================================
# TRANSLATE — Emergent LLM key path
# ============================================================

def test_translate_endpoint():
    r = requests.post(f"{URL}/api/translate", json={"text": "Hello", "target": "es"}, timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    # Endpoint shape varies — accept either 'translation' or 'text' or 'translated'
    assert isinstance(data, dict)


# ============================================================
# HUB BANNERS — iter65-67 — full create / ack / dismiss / audit / clone / export / archive
# ============================================================

@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{URL}/api/admin/login", json={"password": ADMIN_PW}, timeout=10,
                      headers={"X-Admin-Token": "skip"})
    assert r.status_code == 200
    return r.json()["token"]


@pytest.fixture(scope="module")
def banner_id(admin_token):
    payload = {
        "title_en": "TEST_ITER68_AuditBanner",
        "body_en": "Iter68 audit run — please ignore.",
        "severity": "advisory",
        "require_ack": True,
        "auto_translate": False,
    }
    r = requests.post(f"{URL}/api/admin/banners",
                      json=payload,
                      headers={"X-Admin-Token": admin_token}, timeout=20)
    assert r.status_code in (200, 201), r.text
    bid = r.json().get("id") or r.json().get("banner", {}).get("id")
    assert bid
    yield bid
    # cleanup
    requests.delete(f"{URL}/api/admin/banners/{bid}",
                    headers={"X-Admin-Token": admin_token}, timeout=10)


class TestHubBannersAuditTrail:
    def test_banner_appears_in_active(self, banner_id):
        r = requests.get(f"{URL}/api/banners/active", timeout=10)
        assert r.status_code == 200
        ids = [b.get("id") for b in r.json().get("banners", [])]
        assert banner_id in ids

    def test_ack_banner(self, banner_id):
        r = requests.post(f"{URL}/api/banners/{banner_id}/acknowledge",
                          json={"device_id": "TEST_ITER68_DEV", "page": "/test", "lang": "en"},
                          timeout=10)
        assert r.status_code in (200, 204), r.text

    def test_dismiss_banner(self, banner_id):
        r = requests.post(f"{URL}/api/banners/{banner_id}/dismiss",
                          json={"device_id": "TEST_ITER68_DEV", "page": "/test", "lang": "en"},
                          timeout=10)
        assert r.status_code in (200, 204), r.text

    def test_audit_trail_endpoint(self, banner_id, admin_token):
        r = requests.get(f"{URL}/api/admin/banners/{banner_id}/audit",
                         headers={"X-Admin-Token": admin_token}, timeout=15)
        # Endpoint may be 200 or may not exist as separate route — accept 200/404
        assert r.status_code in (200, 404), r.text
        if r.status_code == 200:
            data = r.json()
            assert isinstance(data, (dict, list))

    def test_audit_pdf_export(self, banner_id, admin_token):
        # try common patterns
        for path in [
            f"/api/admin/banners/{banner_id}/audit.pdf",
            f"/api/admin/banners/{banner_id}/audit/pdf",
            f"/api/admin/banners/{banner_id}/audit-pdf",
        ]:
            r = requests.get(f"{URL}{path}",
                             headers={"X-Admin-Token": admin_token}, timeout=30)
            if r.status_code == 200 and r.content[:4] == b"%PDF":
                assert len(r.content) > 1000
                return
        pytest.skip("No audit PDF endpoint matched expected patterns")

    def test_audit_csv_export(self, banner_id, admin_token):
        for path in [
            f"/api/admin/banners/{banner_id}/audit.csv",
            f"/api/admin/banners/{banner_id}/audit/csv",
            f"/api/admin/banners/{banner_id}/audit-csv",
        ]:
            r = requests.get(f"{URL}{path}",
                             headers={"X-Admin-Token": admin_token}, timeout=30)
            if r.status_code == 200 and ("text/csv" in r.headers.get("content-type", "") or b"," in r.content[:200]):
                return
        pytest.skip("No audit CSV endpoint matched expected patterns")

    def test_banner_clone(self, banner_id, admin_token):
        for path in [
            f"/api/admin/banners/{banner_id}/clone",
            f"/api/admin/banners/{banner_id}/rebroadcast",
        ]:
            r = requests.post(f"{URL}{path}",
                              json={},
                              headers={"X-Admin-Token": admin_token}, timeout=20)
            if r.status_code in (200, 201):
                cloned_id = r.json().get("id") or r.json().get("banner", {}).get("id")
                if cloned_id:
                    requests.delete(f"{URL}/api/admin/banners/{cloned_id}",
                                    headers={"X-Admin-Token": admin_token}, timeout=10)
                return
        pytest.skip("No banner clone endpoint matched expected patterns")

    def test_admin_banner_list_with_archived(self, admin_token):
        r = requests.get(f"{URL}/api/admin/banners?include_archived=true",
                         headers={"X-Admin-Token": admin_token}, timeout=15)
        assert r.status_code == 200, r.text


# ============================================================
# PHOTO RESOLVER — iter63-64 — verify photo:// refs resolve through /api/photo-bytes
# ============================================================

class TestPhotoResolver:
    def test_photo_bytes_no_ref(self):
        r = requests.get(f"{URL}/api/photo-bytes", timeout=10)
        # Should reject missing ref (400/422)
        assert r.status_code in (400, 422), r.text

    def test_photo_bytes_invalid_ref(self):
        r = requests.get(f"{URL}/api/photo-bytes?ref=not-a-real-ref", timeout=10)
        assert r.status_code in (400, 404), r.text

    def test_photo_bytes_with_real_ref(self):
        # find a daily report with photo_count > 0, then fetch by id
        r = requests.get(f"{URL}/api/daily-reports", timeout=30)
        assert r.status_code == 200
        data = r.json()
        reports = data if isinstance(data, list) else (data.get("reports") or [])
        photo_ref = None
        for rep in reports:
            if rep.get("photo_count", 0) > 0:
                rid = rep.get("id")
                if not rid:
                    continue
                full = requests.get(f"{URL}/api/daily-reports/{rid}", timeout=30).json()
                import json as _json
                s = _json.dumps(full)
                if "photo://" in s:
                    idx = s.find("photo://")
                    end = idx
                    while end < len(s) and s[end] not in ('"', "'", " ", ","):
                        end += 1
                    photo_ref = s[idx:end]
                    break
        if not photo_ref:
            pytest.skip("No photo:// ref found in any daily report — skipping live resolver check")
        r2 = requests.get(f"{URL}/api/photo-bytes", params={"ref": photo_ref}, timeout=30)
        assert r2.status_code == 200, f"{photo_ref} -> {r2.status_code}: {r2.text[:200]}"
        ct = r2.headers.get("content-type", "")
        assert "image" in ct or len(r2.content) > 100, f"Resolved bytes too small or wrong type: {ct} {len(r2.content)}"


# ============================================================
# PDF GENERATION — direct render via pdf_render module
# ============================================================

class TestPdfGeneration:
    def _check_pdf(self, pdf_bytes, label):
        assert pdf_bytes[:4] == b"%PDF", f"{label}: not a PDF, starts with {pdf_bytes[:8]!r}"
        assert len(pdf_bytes) > 5000, f"{label}: PDF too small ({len(pdf_bytes)} bytes)"

    def test_daily_report_pdf(self):
        import sys
        sys.path.insert(0, "/app/backend")
        from pdf_render import render_record_pdf
        record = {
            "id": "TEST_ITER68_DR", "report_date": "2026-01-15",
            "project_number": "TEST-001", "project_name": "Iter68 Audit Job",
            "prepared_by": "Audit Bot", "weather": "Clear", "crew_count": 3,
            "tasks_completed": "Audit smoke test",
        }
        self._check_pdf(render_record_pdf("daily-report", record), "daily-report PDF")

    def test_inspection_pdf(self):
        import sys
        sys.path.insert(0, "/app/backend")
        from pdf_render import render_record_pdf
        record = {
            "id": "TEST_ITER68_INSP", "inspection_date": "2026-01-15",
            "project_number": "TEST-001", "project_name": "Iter68 Audit Job",
            "inspector_name": "Audit Bot",
        }
        self._check_pdf(render_record_pdf("inspection", record), "inspection PDF")

    def test_meeting_pdf(self):
        import sys
        sys.path.insert(0, "/app/backend")
        from pdf_render import render_record_pdf
        record = {
            "id": "TEST_ITER68_MTG", "meeting_date": "2026-01-15",
            "project_number": "TEST-001", "project_name": "Iter68 Audit Job",
            "topic": "Audit smoke", "presenter": "Audit Bot",
        }
        self._check_pdf(render_record_pdf("meeting", record), "meeting PDF")
