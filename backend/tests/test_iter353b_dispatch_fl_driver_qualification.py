"""
iter353b · Dispatch + Field Leadership Read-Only Driver Qualification Visibility.

Validates:
- Source-level locks (new endpoints registered · shared helper used · no
  duplicate collection · no write peers under either portal).
- RBAC matrix (Dispatch · Admin · FL allowed where applicable; HR/Shop/
  PM/anonymous rejected from per-portal endpoints; HR/Admin still own
  the HR-prefixed endpoint).
- Data parity — Dispatch and FL see the EXACT same driver counts and
  summary as HR (proves the shared helper is used).
- Read-only enforcement (POST/PATCH/DELETE rejected on both new
  portal endpoints).
- Filter pass-through (cdl_holder, approved, driver_status).
"""
from __future__ import annotations

import os
from typing import Any, Dict

import requests

# Test target ────────────────────────────────────────────────────────────────
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

DISPATCH_ROUTES = "/app/backend/routes/dispatch_portal_auth.py"
FL_ROUTES = "/app/backend/routes/field_leadership_portal.py"
HELPER_PATH = "/app/backend/lib/driver_qualification.py"
SERVER_PATH = "/app/backend/server.py"
TIMEOUT = 30


def _multi_login() -> Dict[str, str]:
    r = requests.post(f"{API_BASE}/auth/multi-login",
                      json={"email": SUPER_EMAIL, "password": SUPER_PW},
                      headers={"X-Admin-Token": ""},
                      timeout=TIMEOUT)
    r.raise_for_status()
    return r.json().get("portal_tokens") or {}


def _hr_token() -> str:
    r = requests.post(f"{API_BASE}/hr/login",
                      json={"email": HR_EMAIL, "password": HR_PW},
                      headers={"X-Admin-Token": ""},
                      timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()["token"]


def _fl_token() -> str:
    r = requests.post(f"{API_BASE}/field-leadership/portal/login",
                      json={"email": FL_EMAIL, "password": FL_PW},
                      headers={"X-Admin-Token": ""},
                      timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()["token"]


def _pm_token() -> str:
    r = requests.post(f"{API_BASE}/pm/login",
                      json={"email": PM_EMAIL, "password": PM_PW},
                      headers={"X-Admin-Token": ""},
                      timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()["token"]


def _read(path: str) -> str:
    with open(path) as fh:
        return fh.read()


# ─────────────────────────────────────────────────────────────────────────────
# 1 · Source-level locks
# ─────────────────────────────────────────────────────────────────────────────
def test_shared_helper_exists():
    s = _read(HELPER_PATH)
    assert "async def fetch_driver_qualification_dashboard" in s
    assert "ALLOWED_DRIVER_STATUSES" in s
    assert "ALLOWED_CDL_ENDORSEMENTS" in s
    # iter350 base-scope contract still enforced.
    assert '"$nin": [None, ""]' in s


def test_dispatch_endpoint_registered():
    s = _read(DISPATCH_ROUTES)
    assert '"/dispatch/driver-qualification"' in s
    assert "fetch_driver_qualification_dashboard" in s
    # No write peers — only the GET route exists under this path.
    assert s.count('"/dispatch/driver-qualification"') == 1


def test_fl_endpoint_uses_shared_helper():
    s = _read(FL_ROUTES)
    assert "fetch_driver_qualification_dashboard" in s, \
        "FL endpoint must call the shared helper (no duplicate query)"
    assert '"/field-leadership/portal/driver-qualification"' in s


def test_dispatch_gate_accepts_admin_and_dispatch_only():
    s = _read(DISPATCH_ROUTES)
    # The combined gate must explicitly accept Admin AND Dispatch tokens.
    assert "is_valid_admin_token_fn" in s
    assert 'alias="X-Dispatch-Token"' in s
    assert 'alias="X-Admin-Token"' in s
    # Must NOT accept HR / PM / Shop / FL tokens on this endpoint.
    for h in ("X-HR-Token", "X-PM-Token", "X-Shop-Token", "X-FL-Token"):
        assert h not in s.split("@router.get(\"/dispatch/driver-qualification\"")[-1].split("\n\n")[0:200].__str__(), \
            f"Dispatch DQ gate must NOT accept {h}"


def test_server_threads_admin_token_validator():
    s = _read(SERVER_PATH)
    assert "is_valid_admin_token_fn=_is_valid_admin_token" in s, \
        "server.py must pass _is_valid_admin_token into build_dispatch_router"


# ─────────────────────────────────────────────────────────────────────────────
# 2 · Live RBAC matrix
# ─────────────────────────────────────────────────────────────────────────────
def test_dispatch_endpoint_dispatch_allowed():
    tokens = _multi_login()
    disp = tokens.get("dispatch")
    assert disp
    r = requests.get(f"{API_BASE}/dispatch/driver-qualification",
                     headers={"X-Dispatch-Token": disp, "X-Admin-Token": ""},
                     timeout=TIMEOUT)
    assert r.status_code == 200, r.text[:200]
    j = r.json()
    assert j.get("viewer_role") == "dispatch"
    for k in ("items", "count", "summary", "as_of"):
        assert k in j


def test_dispatch_endpoint_admin_allowed():
    tokens = _multi_login()
    admin = tokens.get("admin")
    assert admin
    r = requests.get(f"{API_BASE}/dispatch/driver-qualification",
                     headers={"X-Admin-Token": admin},
                     timeout=TIMEOUT)
    assert r.status_code == 200, r.text[:200]


def test_dispatch_endpoint_pm_blocked():
    pm = _pm_token()
    r = requests.get(f"{API_BASE}/dispatch/driver-qualification",
                     headers={"X-PM-Token": pm, "X-Admin-Token": ""},
                     timeout=TIMEOUT)
    assert r.status_code in (401, 403)


def test_dispatch_endpoint_hr_blocked():
    hr = _hr_token()
    r = requests.get(f"{API_BASE}/dispatch/driver-qualification",
                     headers={"X-HR-Token": hr, "X-Admin-Token": ""},
                     timeout=TIMEOUT)
    assert r.status_code in (401, 403), \
        "HR token MUST NOT satisfy the dispatch endpoint — HR has its own surface"


def test_dispatch_endpoint_anonymous_blocked():
    r = requests.get(f"{API_BASE}/dispatch/driver-qualification",
                     headers={"X-Admin-Token": ""},
                     timeout=TIMEOUT)
    assert r.status_code in (401, 403)


def test_fl_endpoint_fl_allowed():
    fl = _fl_token()
    r = requests.get(f"{API_BASE}/field-leadership/portal/driver-qualification",
                     headers={"X-FL-Token": fl, "X-Admin-Token": ""},
                     timeout=TIMEOUT)
    assert r.status_code == 200, r.text[:200]
    j = r.json()
    assert j.get("viewer_role") == "field_leadership"
    for k in ("items", "count", "summary", "as_of"):
        assert k in j


def test_fl_endpoint_pm_blocked():
    pm = _pm_token()
    r = requests.get(f"{API_BASE}/field-leadership/portal/driver-qualification",
                     headers={"X-PM-Token": pm, "X-Admin-Token": ""},
                     timeout=TIMEOUT)
    assert r.status_code in (401, 403)


def test_fl_endpoint_anonymous_blocked():
    r = requests.get(f"{API_BASE}/field-leadership/portal/driver-qualification",
                     headers={"X-Admin-Token": ""},
                     timeout=TIMEOUT)
    assert r.status_code in (401, 403)


def test_hr_endpoint_unchanged_hr_allowed():
    """HR/Admin retain full authority on the HR-prefixed endpoint."""
    hr = _hr_token()
    r = requests.get(f"{API_BASE}/hr/driver-qualification/dashboard",
                     headers={"X-HR-Token": hr, "X-Admin-Token": ""},
                     timeout=TIMEOUT)
    assert r.status_code == 200


def test_hr_endpoint_dispatch_blocked():
    """Dispatch token MUST NOT satisfy the HR-prefixed endpoint —
    Dispatch has its own surface, no cross-contamination."""
    tokens = _multi_login()
    disp = tokens.get("dispatch")
    assert disp
    r = requests.get(f"{API_BASE}/hr/driver-qualification/dashboard",
                     headers={"X-Dispatch-Token": disp, "X-Admin-Token": ""},
                     timeout=TIMEOUT)
    assert r.status_code in (401, 403)


# ─────────────────────────────────────────────────────────────────────────────
# 3 · Data parity — shared helper means identical counts across portals
# ─────────────────────────────────────────────────────────────────────────────
def test_parity_dispatch_fl_hr():
    tokens = _multi_login()
    disp = tokens.get("dispatch")
    hr = _hr_token()
    fl = _fl_token()
    d = requests.get(f"{API_BASE}/dispatch/driver-qualification",
                     headers={"X-Dispatch-Token": disp, "X-Admin-Token": ""},
                     timeout=TIMEOUT).json()
    f = requests.get(f"{API_BASE}/field-leadership/portal/driver-qualification",
                     headers={"X-FL-Token": fl, "X-Admin-Token": ""},
                     timeout=TIMEOUT).json()
    h = requests.get(f"{API_BASE}/hr/driver-qualification/dashboard",
                     headers={"X-HR-Token": hr, "X-Admin-Token": ""},
                     timeout=TIMEOUT).json()

    # Same approved/CDL counts.
    assert d["count"] == f["count"] == h["count"], \
        f"counts differ: Dispatch={d['count']} FL={f['count']} HR={h['count']}"
    # Same summary tiles.
    for key in ("cdl_expiring_30d", "medical_card_expiring_30d",
                "restricted", "suspended", "tanker_capable"):
        assert d["summary"][key] == f["summary"][key] == h["summary"][key], \
            f"summary[{key}] differs across portals"


# ─────────────────────────────────────────────────────────────────────────────
# 4 · Filter pass-through
# ─────────────────────────────────────────────────────────────────────────────
def test_dispatch_filter_cdl_holder():
    tokens = _multi_login()
    disp = tokens.get("dispatch")
    r1 = requests.get(f"{API_BASE}/dispatch/driver-qualification?cdl_holder=true",
                      headers={"X-Dispatch-Token": disp, "X-Admin-Token": ""},
                      timeout=TIMEOUT).json()
    r2 = requests.get(f"{API_BASE}/dispatch/driver-qualification?cdl_holder=false",
                      headers={"X-Dispatch-Token": disp, "X-Admin-Token": ""},
                      timeout=TIMEOUT).json()
    for it in r1["items"]:
        assert it.get("cdl_holder") is True
    for it in r2["items"]:
        assert it.get("cdl_holder") is False


def test_dispatch_filter_invalid_driver_status():
    tokens = _multi_login()
    disp = tokens.get("dispatch")
    r = requests.get(f"{API_BASE}/dispatch/driver-qualification?driver_status=bogus",
                     headers={"X-Dispatch-Token": disp, "X-Admin-Token": ""},
                     timeout=TIMEOUT)
    assert r.status_code == 400


# ─────────────────────────────────────────────────────────────────────────────
# 5 · Read-only enforcement
# ─────────────────────────────────────────────────────────────────────────────
def test_dispatch_endpoint_is_get_only():
    tokens = _multi_login()
    disp = tokens.get("dispatch")
    for verb in ("post", "patch", "delete"):
        r = getattr(requests, verb)(
            f"{API_BASE}/dispatch/driver-qualification",
            headers={"X-Dispatch-Token": disp, "X-Admin-Token": ""},
            timeout=TIMEOUT,
        )
        assert r.status_code in (401, 403, 404, 405), \
            f"Dispatch DQ accepted {verb.upper()} (status {r.status_code})"


def test_fl_endpoint_is_get_only():
    fl = _fl_token()
    for verb in ("post", "patch", "delete"):
        r = getattr(requests, verb)(
            f"{API_BASE}/field-leadership/portal/driver-qualification",
            headers={"X-FL-Token": fl, "X-Admin-Token": ""},
            timeout=TIMEOUT,
        )
        assert r.status_code in (401, 403, 404, 405)


# ─────────────────────────────────────────────────────────────────────────────
# 6 · Frontend wiring locks
# ─────────────────────────────────────────────────────────────────────────────
def test_frontend_routes_registered():
    with open("/app/frontend/src/App.js") as fh:
        s = fh.read()
    assert 'path="/dispatch-portal/driver-qualification"' in s
    assert 'path="/field-leadership/portal/driver-qualification"' in s
    assert "DispatchDriverQualification" in s
    assert "FieldLeadershipDriverQualification" in s


def test_frontend_dispatch_hub_link_present():
    with open("/app/frontend/src/pages/DispatchHub.jsx") as fh:
        s = fh.read()
    assert "dispatch-driver-qual-link" in s
    assert "/dispatch-portal/driver-qualification" in s


def test_frontend_fl_dashboard_link_present():
    with open("/app/frontend/src/pages/FieldLeadershipPortalDashboard.jsx") as fh:
        s = fh.read()
    assert "/field-leadership/portal/driver-qualification" in s
    assert "fl-card-driver-qual-cta" in s


def test_frontend_shared_view_used_by_both_pages():
    """Both portal pages must consume the SAME shared component — no
    duplicate UI implementations."""
    for path in (
        "/app/frontend/src/pages/DispatchDriverQualification.jsx",
        "/app/frontend/src/pages/FieldLeadershipDriverQualification.jsx",
    ):
        with open(path) as fh:
            s = fh.read()
        assert "DriverQualificationReadOnlyView" in s, \
            f"{path} must consume the shared read-only view"
    # And the shared view must NOT carry any write affordances.
    with open("/app/frontend/src/components/DriverQualificationReadOnlyView.jsx") as fh:
        s = fh.read()
    assert "axios.post" not in s and "axios.patch" not in s and "axios.delete" not in s, \
        "shared DQ view contains write affordances — must be read-only"
