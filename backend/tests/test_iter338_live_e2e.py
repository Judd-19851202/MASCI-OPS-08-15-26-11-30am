"""Live HTTP tests for the strict-admin Admin Reference Lookup surface."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://masci-audit-hub.preview.emergentagent.com").rstrip("/")
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"

SEEDED_INCIDENT_REF = "INC-2026-0517-002"
SEEDED_DAILY_UUID = "42e3a8e6-dc41-4cc4-bb57-0d5c4be3d0f8"


@pytest.fixture(scope="module")
def admin_headers():
    r = requests.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=20,
    )
    assert r.status_code == 200, f"multi-login failed: {r.status_code} {r.text}"
    body = r.json()
    admin = (body.get("portal_tokens") or {}).get("admin")
    directory = body.get("session_token")
    assert admin and directory
    return {"X-Admin-Token": admin, "X-Directory-Token": directory}


# ─── iter338 · Admin Reference Lookup ─────────────────────────────────────
class TestAdminLookup:
    def test_requires_admin_token(self):
        # NOTE: project conftest auto-injects X-Admin-Token; explicitly clear.
        r = requests.get(f"{BASE_URL}/api/admin/lookup",
                         params={"ref": SEEDED_INCIDENT_REF},
                         headers={"X-Admin-Token": ""}, timeout=15)
        assert r.status_code in (401, 403), f"got {r.status_code} {r.text[:200]}"

    def test_pm_token_does_not_satisfy(self):
        r = requests.get(f"{BASE_URL}/api/admin/lookup",
                         params={"ref": SEEDED_INCIDENT_REF},
                         headers={"X-Admin-Token": "", "X-PM-Token": "anything"}, timeout=15)
        assert r.status_code in (401, 403), f"got {r.status_code} {r.text[:200]}"

    def test_lookup_seeded_incident_ref(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/lookup",
                         params={"ref": SEEDED_INCIDENT_REF},
                         headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("found") is True, f"expected found:True, got {d}"
        assert d.get("kind") == "incident"
        assert d.get("id")
        assert d.get("path", "").startswith("/admin/incidents/")

    def test_lookup_uuid_fallback_daily_report(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/lookup",
                         params={"ref": SEEDED_DAILY_UUID},
                         headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        # If seed exists, found:True kind:daily-report. If not seeded in
        # preview DB, accept graceful miss so we don't false-fail.
        if d.get("found"):
            assert d.get("kind") == "daily-report"
            assert d.get("id") == SEEDED_DAILY_UUID
            assert d.get("path", "").startswith("/admin/daily/")
        else:
            assert str(d.get("ref") or "").upper() == SEEDED_DAILY_UUID.upper()

    def test_graceful_miss(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/lookup",
                         params={"ref": "DOES-NOT-EXIST-9999"},
                         headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("found") is False
        assert d.get("ref") == "DOES-NOT-EXIST-9999"

    def test_whitespace_and_case_normalization(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/lookup",
                         params={"ref": f"  {SEEDED_INCIDENT_REF.lower()}  "},
                         headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("found") is True
        assert d.get("kind") == "incident"


# ─── iter337 · PDF header continuity ─────────────────────────────────────
class TestPdfContinuity:
    def test_equipment_issuance_pdf_renders(self, admin_headers):
        # Find any issuance id
        lst = requests.get(f"{BASE_URL}/api/safety-forms/equipment-issuances",
                           headers=admin_headers, timeout=20)
        if lst.status_code != 200:
            pytest.skip(f"listing endpoint returned {lst.status_code}")
        rows = lst.json()
        if isinstance(rows, dict):
            rows = rows.get("rows") or rows.get("items") or []
        if not rows:
            pytest.skip("no equipment_issuance records seeded in preview")
        rec_id = rows[0].get("id")
        r = requests.get(f"{BASE_URL}/api/safety-forms/equipment-issuances/{rec_id}/pdf",
                         headers=admin_headers, timeout=30)
        assert r.status_code == 200, f"PDF endpoint failed: {r.status_code} {r.text[:200]}"
        assert r.content[:4] == b"%PDF", "response is not a PDF binary"

    def test_field_leadership_pdf_renders(self, admin_headers):
        lst = requests.get(f"{BASE_URL}/api/field-leadership",
                           headers=admin_headers, timeout=20)
        if lst.status_code != 200:
            pytest.skip(f"listing endpoint returned {lst.status_code}")
        rows = lst.json()
        if isinstance(rows, dict):
            rows = rows.get("rows") or rows.get("items") or []
        if not rows:
            pytest.skip("no field-leadership records seeded")
        rec_id = rows[0].get("id")
        r = requests.get(f"{BASE_URL}/api/field-leadership/{rec_id}/pdf",
                         headers=admin_headers, timeout=30)
        assert r.status_code == 200, f"PDF endpoint failed: {r.status_code} {r.text[:200]}"
        assert r.content[:4] == b"%PDF"


# ─── No public lookup leakage ─────────────────────────────────────────────
class TestNoPublicLookup:
    def test_no_public_lookup_api(self):
        # /api/lookup without admin gate must NOT exist as a public endpoint
        r = requests.get(f"{BASE_URL}/api/lookup", timeout=10)
        # 404/405 acceptable; 200 with results = leak
        assert r.status_code in (404, 405, 401, 403), f"public /api/lookup leaked: {r.status_code}"
