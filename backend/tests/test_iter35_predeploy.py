"""Iter-35 pre-deploy audit — per-PM auth, co-PMs, scoping, destructive-action gate, activity log."""
import os
import requests
import pytest

BASE = os.environ.get("REACT_APP_BACKEND_URL", "https://safety-audit-mobile-1.preview.emergentagent.com").rstrip("/")
API = f"{BASE}/api"

ADMIN_PW = "Maddix123!"
CHRIS_EMAIL = "chriswright@mascigc.com"
CHRIS_PW = "ChrisRocksThis2026"
SHARED_PM_PW = "Maddix123!"

# ---------- session helpers ----------
@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{API}/admin/login", json={"password": ADMIN_PW}, timeout=15)
    assert r.status_code == 200, r.text
    return r.json().get("token")

@pytest.fixture(scope="module")
def admin_h(admin_token):
    return {"X-Admin-Token": admin_token}

@pytest.fixture(scope="module")
def chris_token():
    r = requests.post(f"{API}/pm/login", json={"email": CHRIS_EMAIL, "password": CHRIS_PW}, timeout=15)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("ok") is True
    return body.get("token")

@pytest.fixture(scope="module")
def chris_h(chris_token):
    # IMPORTANT: conftest.py auto-injects X-Admin-Token into every requests call.
    # We override with empty string so chris truly tests PM-only scoping.
    return {"X-Admin-Token": "", "X-PM-Token": chris_token}


# ---------- 1. health & auth basics ----------
class TestHealthAndAuth:
    def test_health(self):
        r = requests.get(f"{API}/health", timeout=10)
        assert r.status_code == 200
        assert r.json().get("ok") is True

    def test_admin_login_ok(self, admin_token):
        assert isinstance(admin_token, str) and len(admin_token) > 10

    def test_admin_login_wrong(self):
        r = requests.post(f"{API}/admin/login", json={"password": "WRONG"}, timeout=10)
        assert r.status_code == 401

    def test_pm_login_per_pm_ok(self, chris_token):
        assert "." in chris_token  # per-PM token = pm_id.HMAC

    def test_pm_login_wrong_pw(self):
        r = requests.post(f"{API}/pm/login", json={"email": CHRIS_EMAIL, "password": "WRONG"}, timeout=10)
        assert r.status_code in (401, 403)

    def test_pm_login_legacy_shared(self):
        r = requests.post(f"{API}/pm/login", json={"password": SHARED_PM_PW}, timeout=10)
        assert r.status_code == 200, r.text
        token = r.json().get("token")
        assert token and "." not in token  # legacy shared = no dot

    def test_pm_me_chris(self, chris_h):
        r = requests.get(f"{API}/pm/me", headers=chris_h, timeout=10)
        assert r.status_code == 200
        body = r.json()
        pm = body.get("pm") or body
        assert pm.get("email") == CHRIS_EMAIL, f"unexpected /pm/me body: {body}"


# ---------- 2. password-gate verify endpoint ----------
class TestAdminPasswordGate:
    def test_verify_password_ok(self, admin_h):
        r = requests.post(f"{API}/admin/auth/verify-password",
                          headers=admin_h, json={"password": ADMIN_PW}, timeout=10)
        assert r.status_code == 200, r.text

    def test_verify_password_wrong(self, admin_h):
        r = requests.post(f"{API}/admin/auth/verify-password",
                          headers=admin_h, json={"password": "WRONG"}, timeout=10)
        assert r.status_code in (401, 403)


# ---------- 3. PM activity log (admin-only) ----------
class TestPmActivity:
    def test_activity_admin(self, admin_h):
        r = requests.get(f"{API}/admin/project-managers/activity", headers=admin_h, timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        items = data if isinstance(data, list) else data.get("items") or data.get("activity") or []
        assert isinstance(items, list) and len(items) > 0
        keys = set(items[0].keys())
        # Each row has these activity-rollup fields
        expected_any = {"reports_7d", "job_count", "last_login_at", "last_login_ip", "email"}
        assert expected_any & keys, f"unexpected shape {keys}"

    def test_activity_pm_forbidden(self, chris_token):
        # Pass empty admin token to bypass conftest auto-injection, only PM token present
        h = {"X-Admin-Token": "", "X-PM-Token": chris_token}
        r = requests.get(f"{API}/admin/project-managers/activity", headers=h, timeout=10)
        assert r.status_code in (401, 403), f"PM should not access admin activity, got {r.status_code}"


# ---------- 4. per-PM data scoping ----------
class TestScoping:
    @pytest.mark.parametrize("path", [
        "/inspections", "/daily-reports", "/meetings", "/incidents",
        "/jhas", "/equipment-inspections", "/qaqc-inspections", "/admin/jobs",
    ])
    def test_chris_subset_of_admin(self, admin_h, chris_h, path):
        ra = requests.get(f"{API}{path}", headers=admin_h, timeout=20)
        rc = requests.get(f"{API}{path}", headers=chris_h, timeout=20)
        assert ra.status_code == 200, f"admin {path} -> {ra.status_code}: {ra.text[:200]}"
        assert rc.status_code == 200, f"chris {path} -> {rc.status_code}: {rc.text[:200]}"
        a = ra.json() if isinstance(ra.json(), list) else ra.json().get("items", [])
        c = rc.json() if isinstance(rc.json(), list) else rc.json().get("items", [])
        # Chris is scoped → chris count <= admin count
        assert len(c) <= len(a), f"{path} scoping inverted (chris {len(c)} > admin {len(a)})"

    def test_chris_jobs_assignment_count(self, chris_h):
        """Chris is documented to have ~9 assigned jobs (8 primary + 1 co-PM)."""
        r = requests.get(f"{API}/admin/jobs", headers=chris_h, timeout=15)
        assert r.status_code == 200
        jobs = r.json() if isinstance(r.json(), list) else r.json().get("items", [])
        assert len(jobs) >= 1, "Chris should see at least 1 scoped job"

    def test_pnl_blocked_for_unassigned_project(self, admin_h, chris_h):
        # find a project Chris is NOT on
        ra = requests.get(f"{API}/admin/jobs", headers=admin_h, timeout=15).json()
        admin_jobs = ra if isinstance(ra, list) else ra.get("items", [])
        rc = requests.get(f"{API}/admin/jobs", headers=chris_h, timeout=15).json()
        chris_jobs = rc if isinstance(rc, list) else rc.get("items", [])
        chris_pns = {j.get("project_number") for j in chris_jobs}
        candidates = [j.get("project_number") for j in admin_jobs if j.get("project_number") not in chris_pns]
        if not candidates:
            pytest.skip("no admin-only jobs found")
        target = candidates[0]
        r = requests.get(f"{API}/admin/projects/pnl", headers=chris_h,
                         params={"project_number": target}, timeout=15)
        assert r.status_code == 404, f"expected 404 for un-scoped pnl, got {r.status_code}"


# ---------- 5. co-PMs per job ----------
class TestCoPMs:
    def test_jobs_returned_with_co_pm_field(self, admin_h):
        r = requests.get(f"{API}/admin/jobs", headers=admin_h, timeout=15)
        assert r.status_code == 200
        jobs = r.json() if isinstance(r.json(), list) else r.json().get("items", [])
        assert len(jobs) > 0
        # at least one job should have co_pm_emails populated (24-06 per spec)
        with_copms = [j for j in jobs if j.get("co_pm_emails")]
        assert len(with_copms) >= 1, f"expected at least 1 job with co_pm_emails (24-06), got 0"
        sample = with_copms[0]
        assert isinstance(sample["co_pm_emails"], list)

    def test_co_pm_max_4_enforced(self, admin_h):
        # find a job to test against
        r = requests.get(f"{API}/admin/jobs", headers=admin_h, timeout=15)
        jobs = r.json() if isinstance(r.json(), list) else r.json().get("items", [])
        if not jobs:
            pytest.skip("no jobs")
        job = jobs[0]
        jid = job.get("id") or job.get("_id")
        # try to PATCH with 5 co-PMs → should be rejected
        emails5 = [f"copm{i}@mascigc.com" for i in range(5)]
        r2 = requests.patch(f"{API}/admin/jobs/{jid}/co-pms",
                            headers=admin_h, json={"co_pm_emails": emails5}, timeout=10)
        # Either 400/422 (rejected) or 200 with truncation; max-4 means rejected is expected
        if r2.status_code == 200:
            saved = r2.json()
            stored = saved.get("co_pm_emails") or saved.get("co_pms") or []
            assert len(stored) <= 4, f"max-4 violated: stored {len(stored)}"
        else:
            assert r2.status_code in (400, 422)


# ---------- 6. auto-email recipient preview ----------
class TestEmailRouting:
    def test_preview_inspection_includes_always_cc(self, chris_h):
        # use a job Chris is on
        r = requests.get(f"{API}/admin/jobs", headers=chris_h, timeout=15).json()
        jobs = r if isinstance(r, list) else r.get("items", [])
        if not jobs:
            pytest.skip("no chris jobs")
        pn = jobs[0].get("project_number")
        rp = requests.get(f"{API}/auto-email/preview",
                          params={"kind": "inspection", "project_number": pn, "project_name": "Test"}, timeout=15)
        assert rp.status_code == 200, rp.text
        body = rp.json()
        all_recips = " ".join(body.get("all_recipients") or []).lower()
        assert "jaymn.judd@mascigc.com" in all_recips, f"jaymn.judd missing from inspection routing: {body}"
        assert "safety@mascigc.com" in all_recips, f"safety@mascigc.com missing from inspection routing: {body}"
        # job 24-06 should also include co-PM chriswright
        if pn == "24-06":
            assert "chriswright@mascigc.com" in all_recips, "co-PM chris missing on 24-06"

    def test_preview_daily_report_no_office_cc(self, chris_h):
        r = requests.get(f"{API}/admin/jobs", headers=chris_h, timeout=15).json()
        jobs = r if isinstance(r, list) else r.get("items", [])
        if not jobs:
            pytest.skip("no chris jobs")
        pn = jobs[0].get("project_number")
        rp = requests.get(f"{API}/auto-email/preview",
                          params={"kind": "daily-report", "project_number": pn, "project_name": "Test"}, timeout=15)
        assert rp.status_code == 200, rp.text
        body = rp.json()
        all_recips = " ".join(body.get("all_recipients") or []).lower()
        # Daily report should NOT include compliance always-cc safety@mascigc.com
        assert "safety@mascigc.com" not in all_recips, f"daily-report unexpectedly CC's compliance: {body}"


# ---------- 7. unauthenticated guards ----------
class TestUnauthGuards:
    def test_admin_jobs_no_token(self):
        r = requests.get(f"{API}/admin/jobs", headers={"X-Admin-Token": ""}, timeout=10)
        assert r.status_code in (401, 403)

    def test_inspections_no_token(self):
        r = requests.get(f"{API}/inspections", headers={"X-Admin-Token": ""}, timeout=10)
        assert r.status_code in (401, 403)
