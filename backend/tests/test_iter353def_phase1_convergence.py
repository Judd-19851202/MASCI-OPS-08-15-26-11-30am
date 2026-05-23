"""
iter353d / iter353e / iter353f — Phase 1 Operational Convergence
================================================================
Single combined test file covering:

* iter353d — FL Operational Accountability Expansion
   - /api/field-leadership/portal/employee/{id}/snapshot
   - /api/field-leadership/portal/incidents-recent
   - /api/field-leadership/portal/notifications-recent
* iter353e — PM Crew Compliance Lens
   - /api/pm/crew/training-records
   - /api/pm/crew/ppe
   - /api/pm/crew/capas
   - /api/pm/crew/summary
* iter353f — HR OSHA & Labor Reach
   - /api/hr/incidents
   - /api/hr/corrective-actions
   - /api/hr/daily-reports
"""
from __future__ import annotations

import os
from typing import Dict

import requests

# Target -----------------------------------------------------------------
_FRONT_ENV = "/app/frontend/.env"
try:
    with open(_FRONT_ENV) as fh:
        for ln in fh:
            if ln.startswith("REACT_APP_BACKEND_URL="):
                API_BASE = ln.split("=", 1)[1].strip() + "/api"
                break
        else:
            API_BASE = "http://localhost:8001/api"
except FileNotFoundError:
    API_BASE = "http://localhost:8001/api"

SUPER_EMAIL = os.environ.get("SUPER_ADMIN_EMAIL", "jaymn.judd@mascigc.com")
SUPER_PW = os.environ.get("SUPER_ADMIN_BOOTSTRAP_PASSWORD", "Maddix123!")
HR_EMAIL = "hrmanager@mascigc.com"
HR_PW = "HRTesting2026!"
FL_EMAIL = "fieldleader@mascigc.com"
FL_PW = "FieldLead2026!"
PM_EMAIL = "chriswright@mascigc.com"
PM_PW = "ChrisRocksThis2026"
SAMPLE_EMP_ID = "250d2712-6be3-440e-9de9-1941c5a735d6"  # Alec Perkins
TIMEOUT = 30


def _multi_login() -> Dict[str, str]:
    r = requests.post(f"{API_BASE}/auth/multi-login",
                      json={"email": SUPER_EMAIL, "password": SUPER_PW},
                      headers={"X-Admin-Token": ""}, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json().get("portal_tokens") or {}


def _hr_token() -> str:
    r = requests.post(f"{API_BASE}/hr/login",
                      json={"email": HR_EMAIL, "password": HR_PW},
                      headers={"X-Admin-Token": ""}, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()["token"]


def _fl_token() -> str:
    r = requests.post(f"{API_BASE}/field-leadership/portal/login",
                      json={"email": FL_EMAIL, "password": FL_PW},
                      headers={"X-Admin-Token": ""}, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()["token"]


def _pm_token() -> str:
    r = requests.post(f"{API_BASE}/pm/login",
                      json={"email": PM_EMAIL, "password": PM_PW},
                      headers={"X-Admin-Token": ""}, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()["token"]


# ═══════════════════════════════════════════════════════════════════════
# iter353d · FL Operational Accountability Expansion
# ═══════════════════════════════════════════════════════════════════════
class TestFlSnapshot:
    def test_fl_snapshot_happy_path(self):
        fl = _fl_token()
        r = requests.get(f"{API_BASE}/field-leadership/portal/employee/{SAMPLE_EMP_ID}/snapshot",
                         headers={"X-FL-Token": fl, "X-Admin-Token": ""}, timeout=TIMEOUT)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["ok"] is True
        assert d["viewer_role"] == "field_leadership"
        assert d["employee"]["id"] == SAMPLE_EMP_ID
        # readiness shape
        for k in ("available_now", "expired_count", "expiring_within_30d",
                  "training_record_count", "ppe_record_count",
                  "incident_count_last_365d"):
            assert k in d["readiness"], f"missing readiness.{k}"
        for k in ("training", "ppe", "expiring_30d", "expired", "as_of"):
            assert k in d

    def test_fl_snapshot_unknown_employee_404(self):
        fl = _fl_token()
        r = requests.get(f"{API_BASE}/field-leadership/portal/employee/nope-xyz/snapshot",
                         headers={"X-FL-Token": fl, "X-Admin-Token": ""}, timeout=TIMEOUT)
        assert r.status_code == 404

    def test_fl_snapshot_anon_blocked(self):
        r = requests.get(f"{API_BASE}/field-leadership/portal/employee/{SAMPLE_EMP_ID}/snapshot",
                         headers={"X-Admin-Token": ""}, timeout=TIMEOUT)
        assert r.status_code in (401, 403)

    def test_fl_snapshot_pm_blocked(self):
        pm = _pm_token()
        r = requests.get(f"{API_BASE}/field-leadership/portal/employee/{SAMPLE_EMP_ID}/snapshot",
                         headers={"X-PM-Token": pm, "X-Admin-Token": ""}, timeout=TIMEOUT)
        assert r.status_code in (401, 403)

    def test_fl_snapshot_get_only(self):
        fl = _fl_token()
        for verb in ("post", "patch", "delete"):
            r = getattr(requests, verb)(
                f"{API_BASE}/field-leadership/portal/employee/{SAMPLE_EMP_ID}/snapshot",
                headers={"X-FL-Token": fl, "X-Admin-Token": ""}, timeout=TIMEOUT)
            assert r.status_code in (401, 403, 404, 405), \
                f"FL snapshot accepted {verb.upper()} (status {r.status_code})"


class TestFlIncidentsRecent:
    def test_fl_incidents_recent_default_window(self):
        fl = _fl_token()
        r = requests.get(f"{API_BASE}/field-leadership/portal/incidents-recent",
                         headers={"X-FL-Token": fl, "X-Admin-Token": ""}, timeout=TIMEOUT)
        assert r.status_code == 200
        d = r.json()
        assert d["ok"] is True
        assert d["window_days"] == 14
        assert isinstance(d["items"], list)

    def test_fl_incidents_recent_custom_window(self):
        fl = _fl_token()
        r = requests.get(f"{API_BASE}/field-leadership/portal/incidents-recent?days=90",
                         headers={"X-FL-Token": fl, "X-Admin-Token": ""}, timeout=TIMEOUT)
        assert r.status_code == 200
        assert r.json()["window_days"] == 90

    def test_fl_incidents_recent_anon_blocked(self):
        r = requests.get(f"{API_BASE}/field-leadership/portal/incidents-recent",
                         headers={"X-Admin-Token": ""}, timeout=TIMEOUT)
        assert r.status_code in (401, 403)

    def test_fl_incidents_no_write_peer(self):
        fl = _fl_token()
        for verb in ("post", "patch", "delete"):
            r = getattr(requests, verb)(f"{API_BASE}/field-leadership/portal/incidents-recent",
                                        headers={"X-FL-Token": fl, "X-Admin-Token": ""}, timeout=TIMEOUT)
            assert r.status_code in (401, 403, 404, 405)


class TestFlNotificationsRecent:
    def test_fl_notifications_recent_happy(self):
        fl = _fl_token()
        r = requests.get(f"{API_BASE}/field-leadership/portal/notifications-recent",
                         headers={"X-FL-Token": fl, "X-Admin-Token": ""}, timeout=TIMEOUT)
        assert r.status_code == 200
        d = r.json()
        assert d["ok"] is True
        assert d["viewer_role"] == "field_leadership"
        assert isinstance(d["items"], list)


# ═══════════════════════════════════════════════════════════════════════
# iter353e · PM Crew Compliance Lens
# ═══════════════════════════════════════════════════════════════════════
class TestPmCrewLens:
    def test_pm_summary_happy(self):
        pm = _pm_token()
        r = requests.get(f"{API_BASE}/pm/crew/summary",
                         headers={"X-PM-Token": pm, "X-Admin-Token": ""}, timeout=TIMEOUT)
        assert r.status_code == 200, r.text
        d = r.json()
        for k in ("scope", "crew_size", "expiring_30d", "expired", "open_capas"):
            assert k in d

    def test_pm_training_happy(self):
        pm = _pm_token()
        r = requests.get(f"{API_BASE}/pm/crew/training-records",
                         headers={"X-PM-Token": pm, "X-Admin-Token": ""}, timeout=TIMEOUT)
        assert r.status_code == 200
        d = r.json()
        assert "items" in d
        # scope should be pm_crew_180d when PM token used (not admin)
        assert d.get("scope") == "pm_crew_180d"

    def test_pm_ppe_happy(self):
        pm = _pm_token()
        r = requests.get(f"{API_BASE}/pm/crew/ppe",
                         headers={"X-PM-Token": pm, "X-Admin-Token": ""}, timeout=TIMEOUT)
        assert r.status_code == 200

    def test_pm_capas_happy(self):
        pm = _pm_token()
        r = requests.get(f"{API_BASE}/pm/crew/capas",
                         headers={"X-PM-Token": pm, "X-Admin-Token": ""}, timeout=TIMEOUT)
        assert r.status_code == 200

    def test_pm_endpoints_block_hr(self):
        hr = _hr_token()
        for ep in ("/pm/crew/summary", "/pm/crew/training-records",
                   "/pm/crew/ppe", "/pm/crew/capas"):
            r = requests.get(f"{API_BASE}{ep}",
                             headers={"X-HR-Token": hr, "X-Admin-Token": ""}, timeout=TIMEOUT)
            assert r.status_code in (401, 403), \
                f"HR token accepted on {ep} (status {r.status_code})"

    def test_pm_endpoints_block_fl(self):
        fl = _fl_token()
        for ep in ("/pm/crew/summary", "/pm/crew/training-records"):
            r = requests.get(f"{API_BASE}{ep}",
                             headers={"X-FL-Token": fl, "X-Admin-Token": ""}, timeout=TIMEOUT)
            assert r.status_code in (401, 403)

    def test_pm_endpoints_block_anon(self):
        for ep in ("/pm/crew/summary", "/pm/crew/training-records",
                   "/pm/crew/ppe", "/pm/crew/capas"):
            r = requests.get(f"{API_BASE}{ep}",
                             headers={"X-Admin-Token": ""}, timeout=TIMEOUT)
            assert r.status_code in (401, 403)

    def test_pm_admin_token_no_scope(self):
        """Admin tokens bypass the PM scope filter and see global data."""
        tokens = _multi_login()
        admin = tokens["admin"]
        r = requests.get(f"{API_BASE}/pm/crew/summary",
                         headers={"X-Admin-Token": admin}, timeout=TIMEOUT)
        assert r.status_code == 200
        assert r.json()["scope"] == "admin_all"

    def test_pm_endpoints_read_only(self):
        pm = _pm_token()
        for ep in ("/pm/crew/summary", "/pm/crew/training-records",
                   "/pm/crew/ppe", "/pm/crew/capas"):
            for verb in ("post", "patch", "delete"):
                r = getattr(requests, verb)(
                    f"{API_BASE}{ep}",
                    headers={"X-PM-Token": pm, "X-Admin-Token": ""}, timeout=TIMEOUT)
                assert r.status_code in (401, 403, 404, 405), \
                    f"{ep} accepted {verb.upper()} (status {r.status_code})"


# ═══════════════════════════════════════════════════════════════════════
# iter353f · HR OSHA & Labor Reach
# ═══════════════════════════════════════════════════════════════════════
class TestHrOshaReach:
    def test_hr_incidents_happy(self):
        hr = _hr_token()
        r = requests.get(f"{API_BASE}/hr/incidents?days=365",
                         headers={"X-HR-Token": hr, "X-Admin-Token": ""}, timeout=TIMEOUT)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["ok"] is True
        assert d["window_days"] == 365
        assert "items" in d and "summary" in d
        for k in ("total_in_window", "recordable_in_window", "open_in_window"):
            assert k in d["summary"]
        assert d["viewer"]["role"] == "hr"

    def test_hr_incidents_search_filter(self):
        hr = _hr_token()
        r = requests.get(f"{API_BASE}/hr/incidents?q=test_no_match_xyz",
                         headers={"X-HR-Token": hr, "X-Admin-Token": ""}, timeout=TIMEOUT)
        assert r.status_code == 200
        # Returns whatever matches; just shape-check
        assert "items" in r.json()

    def test_hr_incidents_pm_blocked(self):
        pm = _pm_token()
        r = requests.get(f"{API_BASE}/hr/incidents",
                         headers={"X-PM-Token": pm, "X-Admin-Token": ""}, timeout=TIMEOUT)
        assert r.status_code in (401, 403)

    def test_hr_incidents_fl_blocked(self):
        fl = _fl_token()
        r = requests.get(f"{API_BASE}/hr/incidents",
                         headers={"X-FL-Token": fl, "X-Admin-Token": ""}, timeout=TIMEOUT)
        assert r.status_code in (401, 403)

    def test_hr_incidents_anon_blocked(self):
        r = requests.get(f"{API_BASE}/hr/incidents",
                         headers={"X-Admin-Token": ""}, timeout=TIMEOUT)
        assert r.status_code in (401, 403)

    def test_hr_capas_happy(self):
        hr = _hr_token()
        r = requests.get(f"{API_BASE}/hr/corrective-actions",
                         headers={"X-HR-Token": hr, "X-Admin-Token": ""}, timeout=TIMEOUT)
        assert r.status_code == 200
        d = r.json()
        assert "items" in d and "summary" in d

    def test_hr_capas_pm_blocked(self):
        pm = _pm_token()
        r = requests.get(f"{API_BASE}/hr/corrective-actions",
                         headers={"X-PM-Token": pm, "X-Admin-Token": ""}, timeout=TIMEOUT)
        assert r.status_code in (401, 403)

    def test_hr_daily_reports_happy(self):
        """HR read-only daily reports — uses pre-existing iter332
        `/hr/daily-reports` namespace (no duplicate created in
        iter353f). Just verifies HR can reach it."""
        hr = _hr_token()
        r = requests.get(f"{API_BASE}/hr/daily-reports?limit=3",
                         headers={"X-HR-Token": hr, "X-Admin-Token": ""}, timeout=TIMEOUT)
        assert r.status_code == 200
        d = r.json()
        assert "items" in d

    def test_hr_daily_reports_fl_blocked(self):
        fl = _fl_token()
        r = requests.get(f"{API_BASE}/hr/daily-reports",
                         headers={"X-FL-Token": fl, "X-Admin-Token": ""}, timeout=TIMEOUT)
        assert r.status_code in (401, 403)

    def test_hr_endpoints_read_only(self):
        hr = _hr_token()
        for ep in ("/hr/incidents", "/hr/corrective-actions", "/hr/daily-reports"):
            for verb in ("post", "patch", "delete"):
                r = getattr(requests, verb)(
                    f"{API_BASE}{ep}",
                    headers={"X-HR-Token": hr, "X-Admin-Token": ""}, timeout=TIMEOUT)
                assert r.status_code in (401, 403, 404, 405), \
                    f"{ep} accepted {verb.upper()} (status {r.status_code})"


# ═══════════════════════════════════════════════════════════════════════
# Frontend wiring locks
# ═══════════════════════════════════════════════════════════════════════
class TestFrontendWiring:
    def test_fl_widget_component_exists(self):
        with open("/app/frontend/src/components/FlAccountabilityWidget.jsx") as fh:
            s = fh.read()
        assert "fl-widget" in s
        assert "fl-widget-readiness" in s
        assert "fl-widget-open-timeline" in s
        # Read-only enforced — no axios.post/patch/delete in the widget.
        assert "axios.post" not in s and "axios.patch" not in s and "axios.delete" not in s

    def test_fl_dq_page_renders_widget_on_row_click(self):
        with open("/app/frontend/src/pages/FieldLeadershipDriverQualification.jsx") as fh:
            s = fh.read()
        assert "FlAccountabilityWidget" in s
        assert "fl-widget-drawer" in s

    def test_fl_dashboard_has_acct_lookup(self):
        with open("/app/frontend/src/pages/FieldLeadershipPortalDashboard.jsx") as fh:
            s = fh.read()
        assert "fl-card-acct-lookup" in s
        assert "FlAccountabilityWidget" in s

    def test_hr_incidents_page_exists(self):
        with open("/app/frontend/src/pages/HrIncidents.jsx") as fh:
            s = fh.read()
        assert "hr-inc-table" in s
        assert "hr-inc-export-csv" in s
        for tile in ("hr-inc-tile-total", "hr-inc-tile-recordable",
                     "hr-inc-tile-open", "hr-inc-tile-shown"):
            assert tile in s

    def test_hr_incidents_route_registered(self):
        with open("/app/frontend/src/App.js") as fh:
            s = fh.read()
        assert 'path="/hr/incidents"' in s
        assert "HrIncidents" in s
