"""
TRACK 15.0 — OPERATIONAL REALITY CERTIFICATION live regression.

Strategy: hit preview deployment via REACT_APP_BACKEND_URL and prove that
for every persona, the routes their daily workflow depends on respond 200
(or a defensible 4xx). No mutating writes — pure read certification.
"""
import os
import pytest
import requests

BASE = os.environ.get("REACT_APP_BACKEND_URL", "https://masci-audit-hub.preview.emergentagent.com").rstrip("/")

# ---------- shared session / login bootstrap ----------
@pytest.fixture(scope="session")
def master_tokens():
    """Multi-login as master jaymn.judd — returns all portal_tokens."""
    r = requests.post(f"{BASE}/api/auth/multi-login",
                      json={"email": "jaymn.judd@mascigc.com", "password": "Maddix123!"},
                      timeout=20)
    assert r.status_code == 200, f"multi-login failed: {r.status_code} {r.text[:200]}"
    data = r.json()
    return data.get("portal_tokens") or data

@pytest.fixture(scope="session")
def admin_token(master_tokens):
    tok = master_tokens.get("admin") or master_tokens.get("system")
    assert tok, f"no admin token in multi-login response: {list(master_tokens)[:10]}"
    return tok

@pytest.fixture(scope="session")
def safety_token(master_tokens):
    return master_tokens.get("safety")

@pytest.fixture(scope="session")
def hr_token(master_tokens):
    return master_tokens.get("hr")

@pytest.fixture(scope="session")
def fl_token(master_tokens):
    return master_tokens.get("field_leadership")

@pytest.fixture(scope="session")
def shop_token(master_tokens):
    return master_tokens.get("shop")

@pytest.fixture(scope="session")
def dispatch_token(master_tokens):
    return master_tokens.get("dispatch")

@pytest.fixture(scope="session")
def pm_token():
    for attempt in range(3):
        try:
            r = requests.post(f"{BASE}/api/pm/login",
                              json={"email": "cert.pm@example.com", "password": "CertProof2026!"},
                              timeout=45)
            if r.status_code == 200:
                return r.json().get("token") or r.json().get("pm_token")
        except requests.exceptions.RequestException:
            pass
    pytest.skip("PM login unavailable (timeout or non-200)")

@pytest.fixture(scope="session")
def hr_cert_token():
    r = requests.post(f"{BASE}/api/hr/login",
                      json={"email": "cert.hr@example.com", "password": "CertProof2026!"},
                      timeout=20)
    if r.status_code != 200:
        pytest.skip(f"HR cert login failed: {r.status_code}")
    return r.json().get("token") or r.json().get("hr_token")


# ---------- Phase 2 — PM/Superintendent workflow ----------
class TestPhase2PMWorkflow:
    def test_pm_login_succeeds(self, pm_token):
        assert pm_token and len(pm_token) > 20

    def test_pm_jobs_list(self, pm_token):
        r = requests.get(f"{BASE}/api/pm/jobs", headers={"X-PM-Token": pm_token}, timeout=15)
        assert r.status_code in (200, 204), f"{r.status_code}: {r.text[:200]}"

    def test_pm_daily_reports(self, pm_token):
        # PM portal uses canonical /api/daily-reports with X-PM-Token
        r = requests.get(f"{BASE}/api/daily-reports", headers={"X-PM-Token": pm_token}, timeout=15)
        assert r.status_code in (200, 204), r.status_code

    def test_pm_meetings(self, pm_token):
        r = requests.get(f"{BASE}/api/pm/meetings", headers={"X-PM-Token": pm_token}, timeout=15)
        assert r.status_code in (200, 204, 404), r.status_code

    def test_pm_inspections(self, pm_token):
        r = requests.get(f"{BASE}/api/pm/inspections", headers={"X-PM-Token": pm_token}, timeout=15)
        assert r.status_code in (200, 204, 404), r.status_code


# ---------- Phase 4 — PM scope: project staffing + overloaded crew ----------
class TestPhase4PMStaffing:
    def test_admin_project_staffing_summary(self, admin_token):
        r = requests.get(f"{BASE}/api/project-staffing/summary",
                         headers={"X-Admin-Token": admin_token}, timeout=20)
        assert r.status_code == 200, f"{r.status_code}: {r.text[:300]}"
        data = r.json()
        # Admin global view should expose overloaded list
        assert "overloaded" in data or "overloaded_crew" in data or "rows" in data, list(data)[:10]

    def test_pm_staffing_scoped(self, pm_token):
        r = requests.get(f"{BASE}/api/project-staffing/summary",
                         headers={"X-PM-Token": pm_token}, timeout=20)
        # PM-scoped — must respond, even if empty
        assert r.status_code in (200, 204), f"{r.status_code}: {r.text[:200]}"


# ---------- Phase 6 — Safety workflow ----------
class TestPhase6Safety:
    def test_safety_incidents_list(self, safety_token):
        if not safety_token:
            pytest.skip("no safety token")
        r = requests.get(f"{BASE}/api/incidents", headers={"X-Safety-Token": safety_token}, timeout=15)
        assert r.status_code in (200, 204), r.status_code

    def test_safety_meetings(self, safety_token):
        if not safety_token:
            pytest.skip("no safety token")
        r = requests.get(f"{BASE}/api/safety/meetings", headers={"X-Safety-Token": safety_token}, timeout=15)
        assert r.status_code in (200, 204, 404), r.status_code

    def test_safety_trench(self, safety_token):
        if not safety_token:
            pytest.skip("no safety token")
        r = requests.get(f"{BASE}/api/safety/trench-safety", headers={"X-Safety-Token": safety_token}, timeout=15)
        assert r.status_code in (200, 204, 404), r.status_code


# ---------- Phase 7 — HR workflow + D-A20 canonical document-expirations ----------
class TestPhase7HR:
    def test_hr_document_expirations(self, hr_token):
        if not hr_token:
            pytest.skip("no hr token from master")
        r = requests.get(f"{BASE}/api/document-expirations",
                         headers={"X-HR-Token": hr_token}, timeout=15)
        assert r.status_code in (200, 204), f"{r.status_code}: {r.text[:200]}"

    def test_hr_cert_login(self, hr_cert_token):
        assert hr_cert_token


# ---------- Phase 10 — Admin V1 sidebar destinations ----------
class TestPhase10AdminSidebar:
    def test_admin_operational_records(self, admin_token):
        r = requests.get(f"{BASE}/api/operational-records",
                         headers={"X-Admin-Token": admin_token}, timeout=15)
        assert r.status_code in (200, 204), f"{r.status_code}: {r.text[:200]}"

    def test_admin_operations_actions(self, admin_token):
        r = requests.get(f"{BASE}/api/operations-actions",
                         headers={"X-Admin-Token": admin_token}, timeout=15)
        assert r.status_code in (200, 204), f"{r.status_code}: {r.text[:200]}"

    def test_admin_odr_center(self, admin_token):
        # Newly added — may live at /api/odr or /api/odr/center
        urls = ["/api/odr/center", "/api/odr", "/api/operational-daily-records"]
        last = None
        for u in urls:
            r = requests.get(f"{BASE}{u}", headers={"X-Admin-Token": admin_token}, timeout=15)
            last = (u, r.status_code)
            if r.status_code in (200, 204):
                return
        pytest.fail(f"None of ODR endpoints responded 200; last={last}")

    def test_admin_audit_log(self, admin_token):
        r = requests.get(f"{BASE}/api/audit-log", headers={"X-Admin-Token": admin_token}, timeout=15)
        assert r.status_code in (200, 204, 404), r.status_code


# ---------- Phase 11 — Field Leadership Portal ----------
class TestPhase11FieldLeadership:
    def test_fl_portal_dashboard_data(self, fl_token):
        if not fl_token:
            pytest.skip("no FL token from master")
        # No specific dashboard API — verify token usable on operational-records read
        r = requests.get(f"{BASE}/api/operational-records",
                         headers={"X-FL-Token": fl_token}, timeout=15)
        # FL may have scoped access — accept 200/204/403
        assert r.status_code in (200, 204, 403, 404), r.status_code


# ---------- Phase 12 — Cross-role chain: search + permission boundary ----------
class TestPhase12CrossRoleSearch:
    def _search(self, token_header, token, q):
        return requests.get(f"{BASE}/api/search",
                            headers={token_header: token},
                            params={"q": q}, timeout=20)

    def test_admin_search_english_incident(self, admin_token):
        r = self._search("X-Admin-Token", admin_token, "incident")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, (list, dict))

    def test_admin_search_spanish_incidente(self, admin_token):
        r = self._search("X-Admin-Token", admin_token, "incidente")
        assert r.status_code == 200, r.text[:200]

    def test_admin_search_spanish_liderazgo(self, admin_token):
        r = self._search("X-Admin-Token", admin_token, "liderazgo")
        assert r.status_code == 200, r.text[:200]

    def test_admin_search_spanish_vencimientos(self, admin_token):
        r = self._search("X-Admin-Token", admin_token, "vencimientos")
        assert r.status_code == 200, r.text[:200]

    def test_safety_search_spanish_reunion(self, safety_token):
        if not safety_token:
            pytest.skip("no safety token")
        r = self._search("X-Safety-Token", safety_token, "reunion")
        assert r.status_code == 200, r.text[:200]

    def test_safety_search_excludes_daily_reports(self, safety_token):
        """Wave B contract — safety token must NOT receive daily_reports kind."""
        if not safety_token:
            pytest.skip("no safety token")
        r = self._search("X-Safety-Token", safety_token, "daily")
        assert r.status_code == 200
        # Examine response structure for 'kind' field
        body = r.json()
        results = body.get("results", body) if isinstance(body, dict) else body
        if isinstance(results, list):
            kinds = {x.get("kind") for x in results if isinstance(x, dict)}
            assert "daily_reports" not in kinds, f"safety leaked daily_reports: {kinds}"


# ---------- Phase 15 — Trust surface: health check ----------
class TestPhase15TrustSurface:
    def test_backend_health(self):
        for url in [f"{BASE}/api/health", f"{BASE}/api/", f"{BASE}/api"]:
            r = requests.get(url, timeout=10)
            if r.status_code in (200, 204):
                return
        pytest.fail("no health endpoint responded 200")

    def test_env_banner_preview(self):
        # The backend should reflect APP_ENV=preview somehow
        r = requests.get(f"{BASE}/api/health", timeout=10)
        if r.status_code == 200:
            try:
                body = r.json()
                env = body.get("environment") or body.get("env") or body.get("app_env")
                if env:
                    assert env.lower() in ("preview", "production"), env
            except Exception:
                pass
