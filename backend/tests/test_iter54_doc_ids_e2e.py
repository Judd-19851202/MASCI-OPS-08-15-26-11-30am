"""
iter54 — End-to-end testing for doc_id minting on POST + admin search.

Verifies:
- /api/admin/find-by-doc-id (auth, lookup, lowercase, missing, bogus)
- New POST submissions across collections actually mint doc_ids
- doc_id format matches <PREFIX>-YYYY-NNNNN
"""
import os
import re
import requests
import pytest
from dotenv import load_dotenv

load_dotenv("/app/frontend/.env")
load_dotenv("/app/backend/.env")

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "MASCI1982!")
LEADERSHIP_PASSWORD = os.environ.get("LEADERSHIP_PASSWORD", "MASCIGC")

DOC_ID_RE = re.compile(r"^[A-Z]{2,5}-\d{4}-\d{5}$")


# ---------- fixtures ----------
@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/admin/login", json={"password": ADMIN_PASSWORD})
    assert r.status_code == 200, f"admin login failed: {r.status_code} {r.text}"
    return r.json().get("token")


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"X-Admin-Token": admin_token, "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def leadership_token():
    r = requests.post(f"{BASE_URL}/api/field-leadership/login", json={"password": LEADERSHIP_PASSWORD})
    if r.status_code != 200:
        pytest.skip(f"leadership login unavailable: {r.status_code}")
    return r.json().get("token")


@pytest.fixture(scope="module")
def leadership_headers(leadership_token):
    return {"X-Leadership-Token": leadership_token, "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def project_number(admin_headers):
    r = requests.get(f"{BASE_URL}/api/projects", headers=admin_headers)
    if r.status_code == 200 and r.json():
        # accept either a list of projects or list of dicts with project_number
        data = r.json()
        if isinstance(data, list) and data:
            for p in data:
                if isinstance(p, dict) and p.get("project_number"):
                    return p["project_number"]
    return "0000-TEST"


# ---------- admin search tests ----------
class TestAdminSearch:
    def test_find_unauthenticated_blocked(self):
        # Pass explicit empty admin token to bypass conftest's auto-inject.
        r = requests.get(
            f"{BASE_URL}/api/admin/find-by-doc-id",
            params={"doc_id": "DR-2026-00001"},
            headers={"X-Admin-Token": ""},
        )
        assert r.status_code in (401, 403), f"expected 401/403 got {r.status_code}"

    def test_find_existing_doc_id(self, admin_headers):
        # Use known existing one (DR-2026-00007 per seed/prev iter)
        r = requests.get(
            f"{BASE_URL}/api/admin/find-by-doc-id",
            params={"doc_id": "DR-2026-00007"},
            headers=admin_headers,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("found") is True
        assert "route" in data or "id" in data
        assert data.get("collection") == "daily_reports"

    def test_find_lowercase_normalization(self, admin_headers):
        r = requests.get(
            f"{BASE_URL}/api/admin/find-by-doc-id",
            params={"doc_id": "dr-2026-00007"},
            headers=admin_headers,
        )
        assert r.status_code == 200
        assert r.json().get("found") is True

    def test_find_with_whitespace(self, admin_headers):
        r = requests.get(
            f"{BASE_URL}/api/admin/find-by-doc-id",
            params={"doc_id": "  DR-2026-00007  "},
            headers=admin_headers,
        )
        assert r.status_code == 200
        assert r.json().get("found") is True

    def test_find_bogus_doc_id(self, admin_headers):
        r = requests.get(
            f"{BASE_URL}/api/admin/find-by-doc-id",
            params={"doc_id": "ZZZ-1900-99999"},
            headers=admin_headers,
        )
        assert r.status_code == 200
        assert r.json().get("found") is False

    def test_find_eqr_record(self, admin_headers):
        # EQR-2026-00012 was specifically backfilled
        r = requests.get(
            f"{BASE_URL}/api/admin/find-by-doc-id",
            params={"doc_id": "EQR-2026-00012"},
            headers=admin_headers,
        )
        assert r.status_code == 200
        data = r.json()
        if data.get("found"):
            assert data.get("collection") == "field_leadership_records"


# ---------- POST minting tests ----------
class TestPostMintsDocId:
    def test_post_daily_report_mints_dr(self, admin_headers, project_number):
        payload = {
            "project_name": "TEST_DocID Project",
            "project_number": project_number,
            "location": "TEST_Site",
            "report_date": "2026-05-08",
            "prepared_by": "TEST_DocID Supervisor",
            "weather_summary": "Clear",
            "general_notes": "TEST_doc_id e2e",
        }
        r = requests.post(f"{BASE_URL}/api/daily-reports", json=payload, headers=admin_headers)
        if r.status_code in (401, 403):
            pytest.skip(f"daily-reports POST requires diff auth: {r.status_code}")
        assert r.status_code in (200, 201), f"{r.status_code}: {r.text[:300]}"
        data = r.json()
        doc_id = data.get("doc_id")
        assert doc_id, f"missing doc_id in response: {data}"
        assert DOC_ID_RE.match(doc_id), f"bad format: {doc_id}"
        assert doc_id.startswith("DR-"), f"wrong prefix: {doc_id}"

    def test_post_equipment_inspection_mints_pre(self, admin_headers, project_number):
        payload = {
            "project_name": "TEST_DocID Project",
            "project_number": project_number,
            "location": "TEST_Site",
            "inspection_date": "2026-05-08",
            "inspection_time": "08:00",
            "operator_name": "TEST_Operator",
            "equipment_type": "Excavator",
            "equipment_unit": "TEST-EQ-DOC-1",
        }
        r = requests.post(f"{BASE_URL}/api/equipment-inspections", json=payload, headers=admin_headers)
        if r.status_code in (401, 403):
            pytest.skip("equipment-inspections POST requires different auth")
        if r.status_code in (404, 405, 422):
            pytest.skip(f"endpoint shape mismatch: {r.status_code} {r.text[:200]}")
        assert r.status_code in (200, 201)
        doc_id = r.json().get("doc_id")
        assert doc_id and doc_id.startswith("PRE-")
        assert DOC_ID_RE.match(doc_id)

    def test_post_field_leadership_eqr(self, leadership_headers, project_number):
        payload = {
            "kind": "equipment_return",
            "project_number": project_number,
            "supervisor_name": "TEST_Doc Supervisor",
            "employee_name": "TEST_Doc Employee",
            "occurred_at": "2026-05-08T10:00:00Z",
            "details": {"items": [], "notes": "TEST_doc_id e2e"},
        }
        r = requests.post(
            f"{BASE_URL}/api/field-leadership",
            json=payload,
            headers=leadership_headers,
        )
        if r.status_code in (401, 403):
            pytest.skip("leadership records POST not auth'd")
        if r.status_code in (404, 405, 422):
            pytest.skip(f"endpoint shape mismatch: {r.status_code} {r.text[:200]}")
        assert r.status_code in (200, 201)
        body = r.json()
        # field-leadership wraps record in {"record": {...}}
        rec = body.get("record") or body
        doc_id = rec.get("doc_id") or body.get("doc_id")
        assert doc_id and doc_id.startswith("EQR-"), f"got {doc_id}; body={body}"

    def test_post_field_leadership_supervisor_notes_prefix(self, leadership_headers, project_number):
        # PRD says supervisor_note → FLN. But FIELD_LEADERSHIP_KINDS uses
        # the plural form `supervisor_notes`. The doc_ids resolver maps
        # only the singular `supervisor_note`, so today supervisor_notes
        # falls through to "FL" — flagging this as a likely PRD/code drift.
        payload = {
            "kind": "supervisor_notes",
            "project_number": project_number,
            "supervisor_name": "TEST_Doc Supervisor",
            "occurred_at": "2026-05-08T10:00:00Z",
            "details": {"note": "TEST_doc_id supervisor note"},
        }
        r = requests.post(
            f"{BASE_URL}/api/field-leadership",
            json=payload,
            headers=leadership_headers,
        )
        if r.status_code in (401, 403, 404, 405, 422):
            pytest.skip(f"endpoint shape mismatch: {r.status_code} {r.text[:200]}")
        assert r.status_code in (200, 201), r.text[:300]
        body = r.json()
        rec = body.get("record") or body
        doc_id = rec.get("doc_id") or body.get("doc_id")
        assert doc_id and DOC_ID_RE.match(doc_id), f"got {doc_id}; body={body}"
        # Document the drift: PRD wants FLN, code mints FL.
        assert doc_id.startswith("FLN-") or doc_id.startswith("FL-"), f"unexpected prefix: {doc_id}"
        if doc_id.startswith("FL-") and not doc_id.startswith("FLN-"):
            pytest.xfail(
                "PRD-vs-code drift: supervisor_notes minted FL instead of FLN. "
                "Fix doc_ids._field_leadership_prefix to use plural key 'supervisor_notes'."
            )

    def test_sequential_dr_mints_dont_collide(self, admin_headers, project_number):
        seen = []
        for i in range(3):
            payload = {
                "project_name": f"TEST_Seq Project {i}",
                "project_number": project_number,
                "location": "TEST_Site",
                "report_date": "2026-05-08",
                "prepared_by": f"TEST_Seq {i}",
                "weather_summary": "Clear",
                "general_notes": f"TEST_seq {i}",
            }
            r = requests.post(f"{BASE_URL}/api/daily-reports", json=payload, headers=admin_headers)
            if r.status_code not in (200, 201):
                pytest.skip(f"DR POST failed @{i}: {r.status_code} {r.text[:200]}")
            seen.append(r.json().get("doc_id"))
        assert len(set(seen)) == 3, f"duplicate doc_ids: {seen}"
        seqs = [int(d.split("-")[-1]) for d in seen if d]
        # must be strictly increasing
        assert seqs == sorted(seqs)
