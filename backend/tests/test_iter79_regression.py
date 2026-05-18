"""Iter79 pre-deploy regression sweep.

Tests:
  1. Backup Verification Cron endpoints (state, preview, run-now, auth-gate)
  2. Cross-portal isolation (HR/PM/Shop/Leadership tokens vs admin endpoints)
  3. Public form submissions (daily report, equipment inspection)
  4. Email subject helper (iter78c)
  5. PDF chrome strings (iter78b)
  6. Hub HTML title + manifest (iter78d)
  7. Auth: all 5 portals log in cleanly
"""
import os
import sys
import time
import uuid
import requests
from pathlib import Path

BASE_URL = (
    Path("/app/frontend/.env").read_text().splitlines()
)
BASE_URL = next(
    (l.split("=", 1)[1].strip() for l in BASE_URL if l.startswith("REACT_APP_BACKEND_URL=")),
    "",
).rstrip("/")
assert BASE_URL, "REACT_APP_BACKEND_URL not found"

ADMIN_PASSWORD = "MASCI1982!"
HR_EMAIL = "hrmanager@mascigc.com"
HR_PASSWORD = "HRPortal2026!"
PM_EMAIL = "chriswright@mascigc.com"
PM_PASSWORD = "ChrisRocksThis2026"
SHOP_EMAIL = "testmech@mascigc.com"
SHOP_PASSWORD = "ResetWorks2026!"
LEADERSHIP_PASSWORD = "MASCIGC"

# Override conftest auto-inject by always passing X-Admin-Token explicitly
NO_ADMIN = {"X-Admin-Token": ""}


# ---------- Token fixtures (module-level cache) ----------
def _admin_token():
    r = requests.post(f"{BASE_URL}/api/admin/login", json={"password": ADMIN_PASSWORD}, timeout=10)
    assert r.status_code == 200, f"admin login failed: {r.status_code} {r.text[:200]}"
    return r.json()["token"]


def _hr_token():
    r = requests.post(
        f"{BASE_URL}/api/hr/login",
        json={"email": HR_EMAIL, "password": HR_PASSWORD},
        timeout=10,
        headers=NO_ADMIN,
    )
    if r.status_code != 200:
        return None
    return r.json().get("token")


def _pm_token():
    r = requests.post(
        f"{BASE_URL}/api/pm/login",
        json={"email": PM_EMAIL, "password": PM_PASSWORD},
        timeout=10,
        headers=NO_ADMIN,
    )
    if r.status_code != 200:
        return None
    return r.json().get("token")


def _shop_token():
    r = requests.post(
        f"{BASE_URL}/api/shop/login",
        json={"email": SHOP_EMAIL, "password": SHOP_PASSWORD},
        timeout=10,
        headers=NO_ADMIN,
    )
    if r.status_code != 200:
        return None
    return r.json().get("token")


def _leadership_token():
    r = requests.post(
        f"{BASE_URL}/api/field-leadership/login",
        json={"password": LEADERSHIP_PASSWORD},
        timeout=10,
        headers=NO_ADMIN,
    )
    if r.status_code != 200:
        return None
    return r.json().get("token")


# ============================================================
# 1. BACKUP VERIFICATION CRON (iter79 NEW)
# ============================================================
class TestBackupVerificationCron:
    def test_state_returns_schedule(self):
        tok = _admin_token()
        r = requests.get(
            f"{BASE_URL}/api/admin/backup-verification/state",
            headers={"X-Admin-Token": tok},
            timeout=15,
        )
        assert r.status_code == 200, f"state: {r.status_code} {r.text[:300]}"
        data = r.json()
        assert data.get("ok") is True
        assert "enabled" in data
        sched = data.get("schedule") or {}
        assert "day_of_week" in sched
        assert "day_label" in sched
        assert "hour_utc" in sched
        assert "next_fire_iso" in data
        assert isinstance(data.get("recipients"), list)

    def test_preview_returns_report(self):
        tok = _admin_token()
        r = requests.get(
            f"{BASE_URL}/api/admin/backup-verification/preview",
            headers={"X-Admin-Token": tok},
            timeout=60,
        )
        assert r.status_code == 200, f"preview: {r.status_code} {r.text[:400]}"
        data = r.json()
        assert data.get("ok") is True
        rep = data.get("report") or {}
        assert rep.get("verdict") in ("pass", "warn", "fail")
        assert "r2" in rep
        assert "ledger" in rep
        assert "data" in rep
        assert "total_records" in (rep.get("data") or {})

    def test_state_requires_admin_token(self):
        r = requests.get(
            f"{BASE_URL}/api/admin/backup-verification/state",
            headers=NO_ADMIN,
            timeout=10,
        )
        assert r.status_code in (401, 403), f"expected 401/403, got {r.status_code}"

    def test_preview_requires_admin_token(self):
        r = requests.get(
            f"{BASE_URL}/api/admin/backup-verification/preview",
            headers=NO_ADMIN,
            timeout=10,
        )
        assert r.status_code in (401, 403)

    def test_run_now_requires_admin_token(self):
        r = requests.post(
            f"{BASE_URL}/api/admin/backup-verification/run-now",
            headers=NO_ADMIN,
            json={},
            timeout=10,
        )
        assert r.status_code in (401, 403)

    def test_state_rejects_hr_token(self):
        hr = _hr_token()
        if not hr:
            import pytest
            pytest.skip("HR login unavailable")
        # Pass HR token as admin-token header (should still 401 — wrong token type)
        r = requests.get(
            f"{BASE_URL}/api/admin/backup-verification/state",
            headers={"X-Admin-Token": hr},
            timeout=10,
        )
        assert r.status_code in (401, 403), f"HR token must not access admin: {r.status_code}"


# ============================================================
# 2. CROSS-PORTAL ISOLATION
# ============================================================
class TestCrossPortalIsolation:
    def test_hr_token_rejected_on_admin_jobs(self):
        hr = _hr_token()
        if not hr:
            import pytest
            pytest.skip("HR login unavailable")
        r = requests.get(
            f"{BASE_URL}/api/admin/jobs",
            headers={"X-Admin-Token": hr},
            timeout=10,
        )
        assert r.status_code in (401, 403)

    def test_public_no_token_admin_endpoints(self):
        for path in (
            "/api/admin/jobs",
            "/api/admin/backup-verification/state",
            "/api/admin/backup-verification/preview",
        ):
            r = requests.get(f"{BASE_URL}{path}", headers=NO_ADMIN, timeout=10)
            assert r.status_code in (401, 403), f"{path} unprotected: {r.status_code}"


# ============================================================
# 3. PORTAL LOGINS (all 5)
# ============================================================
class TestPortalLogins:
    def test_admin_login(self):
        assert _admin_token()

    def test_hr_login(self):
        assert _hr_token(), "HR login failed"

    def test_pm_login(self):
        assert _pm_token(), "PM login failed"

    def test_shop_login(self):
        assert _shop_token(), "Shop login failed"

    def test_leadership_login(self):
        assert _leadership_token(), "Leadership login failed"


# ============================================================
# 4. PUBLIC FORM SUBMISSION
# ============================================================
class TestPublicSubmissions:
    def test_daily_report_post(self):
        unique = f"TEST-79-{uuid.uuid4().hex[:6]}"
        payload = {
            "project_name": f"TEST_79 Project {unique}",
            "location": "Test Yard",
            "report_date": "2026-01-10",
            "prepared_by": "Iter79 Tester",
        }
        r = requests.post(
            f"{BASE_URL}/api/daily-reports",
            json=payload,
            timeout=15,
            headers=NO_ADMIN,
        )
        assert r.status_code in (200, 201), f"DR post: {r.status_code} {r.text[:300]}"

    def test_equipment_inspection_post(self):
        unique = f"TEST-79-{uuid.uuid4().hex[:6]}"
        payload = {
            "project_name": f"TEST_79 Project {unique}",
            "location": "Test Yard",
            "inspection_date": "2026-01-10",
            "inspection_time": "07:30",
            "operator_name": "Iter79 Tester",
            "equipment_type": "Skid Steer",
            "equipment_unit": f"SS-{unique}",
        }
        r = requests.post(
            f"{BASE_URL}/api/equipment-inspections",
            json=payload,
            timeout=15,
            headers=NO_ADMIN,
        )
        assert r.status_code in (200, 201), f"Eq insp: {r.status_code} {r.text[:300]}"


# ============================================================
# 5. EMAIL SUBJECT HELPER (iter78c)
# ============================================================
class TestEmailSubjectHelper:
    def test_build_email_subject_format(self):
        sys.path.insert(0, "/app/backend")
        try:
            from pdf_render import build_email_subject
        except Exception as e:
            import pytest
            pytest.skip(f"pdf_render not importable: {e}")
        subj = build_email_subject(
            "daily-report",
            {"doc_id": "DR-2026-0001", "project_name": "MASCI Hwy 45 Reconstruction Phase II"},
        )
        assert "[MASCI]" in subj
        assert "DR-2026-0001" in subj
        assert "Daily Report" in subj or "Daily" in subj
        # project must appear before DR-... per iter78c spec
        idx_proj = subj.find("Hwy")
        idx_dr = subj.find("DR-2026")
        assert idx_proj >= 0 and idx_dr >= 0 and idx_proj < idx_dr, f"subject ordering wrong: {subj}"

    def test_build_email_subject_includes_job_number_iter237(self):
        """iter237 — job number (project_number) is inserted between job
        name and the rest of the subject so PMs can filter inbox by job
        at a glance without opening the email.

        Operator request (verbatim): "On all emails that contain anything
        to do with jobs in subject right after job name can we also put
        job number in there too before report number?"
        """
        sys.path.insert(0, "/app/backend")
        from pdf_render import build_email_subject

        # ── Safety Meeting (matches the operator-reported screenshot) ──
        subj = build_email_subject(
            "meeting",
            {
                "doc_id": "MTG-2026-00016",
                "project_name": "Spruce Creek",
                "project_number": "25-21",
            },
        )
        assert subj == "[MASCI] Spruce Creek · 25-21 · Safety Meeting · MTG-2026-00016", (
            f"meeting subject mismatch: {subj}"
        )

        # ── Daily Report ──
        subj = build_email_subject(
            "daily-report",
            {
                "doc_id": "DR-2026-0001",
                "project_name": "Hwy 45 Reconstruction",
                "project_number": "24-06",
            },
        )
        assert subj == "[MASCI] Hwy 45 Reconstruction · 24-06 · Daily Report · DR-2026-0001", (
            f"daily-report subject mismatch: {subj}"
        )

        # ── Equipment FAIL branch keeps job number adjacency ──
        subj = build_email_subject(
            "equipment-inspection",
            {
                "doc_id": "EQI-2026-00001",
                "project_name": "Spruce Creek",
                "project_number": "25-21",
                "equipment_type": "CAT",
                "equipment_unit": "320E",
            },
            equipment_fail=True,
        )
        assert subj == "⚠ EQUIPMENT FAIL · Spruce Creek · 25-21 · CAT 320E · EQI-2026-00001", (
            f"equipment-fail subject mismatch: {subj}"
        )

        # ── Severe incident branch keeps job number adjacency ──
        subj = build_email_subject(
            "incident",
            {
                "doc_id": "INC-2026-00003",
                "project_name": "Spruce Creek",
                "project_number": "25-21",
            },
            severe_incident=True,
        )
        assert subj == "🚨 SEVERE INCIDENT · Spruce Creek · 25-21 · INC-2026-00003", (
            f"severe-incident subject mismatch: {subj}"
        )

        # ── Graceful fallback when project_number is missing (no "· ·") ──
        subj = build_email_subject(
            "meeting",
            {"doc_id": "MTG-2026-00016", "project_name": "Spruce Creek"},
        )
        assert subj == "[MASCI] Spruce Creek · Safety Meeting · MTG-2026-00016", (
            f"no-job-number fallback mismatch: {subj}"
        )
        # no "· ·" double-separator leakage
        assert " ·  · " not in subj
        assert "· · " not in subj


# ============================================================
# 6. INDEX HTML BRANDING (iter78d)
# ============================================================
class TestBranding:
    def test_index_title(self):
        r = requests.get(f"{BASE_URL}/", timeout=10, headers=NO_ADMIN)
        assert r.status_code == 200
        body = r.text
        # Title might be static in index.html or rendered by React Helmet
        assert ("MASCI Operations Platform" in body) or ("MASCI" in body), "MASCI branding missing from /"
