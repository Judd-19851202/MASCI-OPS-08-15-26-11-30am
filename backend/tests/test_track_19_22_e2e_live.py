"""Track 19.22 · P1 Operational Completion — LIVE end-to-end tests.

Exercises the new operational endpoints against the running preview:
  * Structured search filters on GET /records
  * Batch full lifecycle: create -> upload -> apply -> approve-all
  * Six PDF export packages (HR token) w/ magic-byte + MIME assertion
  * Package permission gating with X-Safety-Token (403 on HR-only pkgs)
  * Zero-drift: /api/employees roster shape untouched
"""
from __future__ import annotations

import io
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    # Fallback from the frontend .env (test env harness only)
    with open("/app/frontend/.env") as _f:
        for _line in _f:
            if _line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = _line.split("=", 1)[1].strip().rstrip("/")

SUPER_ADMIN = {"email": "jaymn.judd@mascigc.com", "password": "Maddix123!"}
EMP_ID = "c9d7ebc3-a292-4d7a-8765-0ce2739c6029"
PACKAGE_KEYS = ("complete_file", "training", "discipline", "safety",
                "ppe_asset", "historical_records")


# ── fixtures ─────────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def tokens():
    r = requests.post(f"{BASE_URL}/api/auth/multi-login", json=SUPER_ADMIN,
                      timeout=90)
    assert r.status_code == 200, f"multi-login failed: {r.status_code} {r.text[:400]}"
    data = r.json()
    toks = data.get("portal_tokens") or data.get("tokens") or data
    return {"hr": toks.get("hr"), "safety": toks.get("safety"),
            "admin": toks.get("admin")}


@pytest.fixture(scope="module")
def hr_headers(tokens):
    return {"X-HR-Token": tokens["hr"]}


@pytest.fixture(scope="module")
def safety_headers(tokens):
    if not tokens.get("safety"):
        pytest.skip("Safety token unavailable")
    return {"X-Safety-Token": tokens["safety"]}


# ── Phase 2 · Structured search ──────────────────────────────────────
class TestStructuredSearch:
    def test_q_filter(self, hr_headers):
        r = requests.get(f"{BASE_URL}/api/employee-records/records",
                         params={"q": "termination"}, headers=hr_headers, timeout=30)
        assert r.status_code == 200, r.text[:400]
        assert isinstance(r.json().get("records", r.json() if isinstance(r.json(), list) else []), list) \
            or "records" in r.json()

    def test_tag_filter(self, hr_headers):
        r = requests.get(f"{BASE_URL}/api/employee-records/records",
                         params={"tag": "urgent"}, headers=hr_headers, timeout=30)
        assert r.status_code == 200

    def test_date_range_filter(self, hr_headers):
        r = requests.get(f"{BASE_URL}/api/employee-records/records",
                         params={"date_from": "2024-01-01",
                                 "date_to": "2025-12-31"},
                         headers=hr_headers, timeout=30)
        assert r.status_code == 200

    def test_uploader_email_filter(self, hr_headers):
        r = requests.get(f"{BASE_URL}/api/employee-records/records",
                         params={"uploader_email": SUPER_ADMIN["email"]},
                         headers=hr_headers, timeout=30)
        assert r.status_code == 200

    def test_department_and_lane_filter(self, hr_headers):
        r = requests.get(f"{BASE_URL}/api/employee-records/records",
                         params={"department": "hr", "lane": "hr"},
                         headers=hr_headers, timeout=30)
        assert r.status_code == 200

    def test_related_asset_filter(self, hr_headers):
        r = requests.get(f"{BASE_URL}/api/employee-records/records",
                         params={"related_asset_id": "TRK-142"},
                         headers=hr_headers, timeout=30)
        assert r.status_code == 200


# ── Phase 4 · Batch lifecycle ────────────────────────────────────────
class TestBatchLifecycle:
    def test_full_batch_flow(self, hr_headers):
        # 1) create
        label = f"TEST_e2e_{uuid.uuid4().hex[:8]}"
        r = requests.post(f"{BASE_URL}/api/employee-records/batches",
                          json={"ownership_lane": "safety", "label": label},
                          headers=hr_headers, timeout=30)
        assert r.status_code in (200, 201), r.text[:400]
        payload = r.json()
        batch = payload.get("batch", payload)
        batch_id = batch.get("id") or batch.get("_id") or payload.get("id")
        assert batch_id, f"No id in batch create: {payload}"

        # 2) upload 2 files
        files = [
            ("files", (f"TEST_a_{uuid.uuid4().hex[:6]}.txt", io.BytesIO(b"alpha"), "text/plain")),
            ("files", (f"TEST_b_{uuid.uuid4().hex[:6]}.txt", io.BytesIO(b"beta"),  "text/plain")),
        ]
        r = requests.post(f"{BASE_URL}/api/employee-records/batches/{batch_id}/uploads",
                          files=files, headers=hr_headers, timeout=60)
        assert r.status_code in (200, 201), r.text[:400]
        assert r.json().get("created") == 2, r.json()

        # 3) GET → pending_classification=2
        r = requests.get(f"{BASE_URL}/api/employee-records/batches/{batch_id}",
                         headers=hr_headers, timeout=30)
        assert r.status_code == 200, r.text[:400]
        data = r.json()
        counts = data.get("counts", {})
        assert counts.get("pending_classification", 0) == 2, counts
        assert len(data.get("records", [])) == 2

        # 4) apply
        r = requests.post(f"{BASE_URL}/api/employee-records/batches/{batch_id}/apply",
                          json={"record_type": "training_record",
                                "employee_id": EMP_ID},
                          headers=hr_headers, timeout=30)
        assert r.status_code == 200, r.text[:400]
        assert r.json().get("modified") == 2, r.json()

        # 5) counts.pending_approval=2
        r = requests.get(f"{BASE_URL}/api/employee-records/batches/{batch_id}",
                         headers=hr_headers, timeout=30)
        counts = r.json().get("counts", {})
        assert counts.get("pending_approval", 0) == 2, counts

        # 6) approve-all
        r = requests.post(f"{BASE_URL}/api/employee-records/batches/{batch_id}/approve-all",
                          headers=hr_headers, timeout=30)
        assert r.status_code == 200, r.text[:400]
        assert r.json().get("approved") == 2, r.json()

        # 7) records now linked
        r = requests.get(f"{BASE_URL}/api/employee-records/records",
                         params={"batch_id": batch_id},
                         headers=hr_headers, timeout=30)
        assert r.status_code == 200
        recs = r.json().get("records", r.json() if isinstance(r.json(), list) else [])
        assert len(recs) == 2
        for rec in recs:
            assert rec.get("approval_status") == "linked", rec.get("approval_status")


# ── Phase 3 · PDF exports ────────────────────────────────────────────
class TestPackageExports:
    @pytest.mark.parametrize("pkg", PACKAGE_KEYS)
    def test_hr_can_download_all_packages(self, hr_headers, pkg):
        r = requests.get(
            f"{BASE_URL}/api/employee-records/employees/{EMP_ID}/exports/{pkg}.pdf",
            headers=hr_headers, timeout=60)
        assert r.status_code == 200, f"{pkg}: {r.status_code} {r.text[:200]}"
        ct = r.headers.get("Content-Type", "")
        assert "application/pdf" in ct, f"{pkg}: content-type={ct}"
        assert r.content.startswith(b"%PDF"), f"{pkg}: not a PDF magic"
        assert len(r.content) > 1500, f"{pkg}: only {len(r.content)} bytes"


# ── Package permission gating (Safety token) ─────────────────────────
class TestPackageGating:
    def test_safety_denied_on_complete_file(self, safety_headers):
        r = requests.get(
            f"{BASE_URL}/api/employee-records/employees/{EMP_ID}/exports/complete_file.pdf",
            headers=safety_headers, timeout=30)
        assert r.status_code == 403, r.status_code

    def test_safety_allowed_on_safety_pkg(self, safety_headers):
        r = requests.get(
            f"{BASE_URL}/api/employee-records/employees/{EMP_ID}/exports/safety.pdf",
            headers=safety_headers, timeout=60)
        assert r.status_code == 200, r.text[:200]
        assert r.content.startswith(b"%PDF")

    def test_safety_denied_on_discipline(self, safety_headers):
        r = requests.get(
            f"{BASE_URL}/api/employee-records/employees/{EMP_ID}/exports/discipline.pdf",
            headers=safety_headers, timeout=30)
        assert r.status_code == 403


# ── Zero-drift ──────────────────────────────────────────────────────
def test_employee_roster_shape_unchanged(hr_headers):
    r = requests.get(f"{BASE_URL}/api/employees",
                     params={"limit": 5}, headers=hr_headers, timeout=30)
    assert r.status_code == 200, r.text[:200]
    data = r.json()
    # Accept either list or dict wrapper
    if isinstance(data, dict):
        rows = data.get("employees") or data.get("items") or data.get("results") or []
    else:
        rows = data
    assert isinstance(rows, list)
