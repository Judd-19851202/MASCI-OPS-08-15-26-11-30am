"""
iter353b-availability · "Drivers Available Right Now" tile.

Verifies the Dispatch-grade operational readiness predicate works
correctly and is identical across Dispatch + FL portals. A driver
counts as available right now ONLY when ALL are true:

- driver_status == "active"
- approved_company_driver == true
- lifecycle_status in ("Active", None) AND is_active in (True, None)
- if CDL holder, cdl_expiration_date >= today
- medical_card_expiration_date is empty OR >= today

Each exclusion rule has a dedicated regression test using a seeded
employee that flips exactly one field at a time.
"""
from __future__ import annotations

import os
import uuid
from datetime import date, timedelta
from typing import Dict, Optional

import pytest
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
TIMEOUT = 30

TODAY = date.today().isoformat()
FAR_FUTURE = (date.today() + timedelta(days=400)).isoformat()
YESTERDAY = (date.today() - timedelta(days=1)).isoformat()


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


def _seed_employee(hr_tok: str, **overrides) -> str:
    """Seed a CDL-holding driver in the AVAILABLE_NOW configuration,
    then apply caller-supplied overrides. Returns the employee id."""
    base = {
        "name": f"iter353b avail {uuid.uuid4().hex[:8]}",
        "trade": "Driver",
        "lifecycle_status": "Active",
        "is_active": True,
        "approved_company_driver": True,
        "cdl_holder": True,
        "driver_status": "active",
        "cdl_expiration_date": FAR_FUTURE,
        "medical_card_expiration_date": FAR_FUTURE,
    }
    body = {**base, **overrides}
    r = requests.post(f"{API_BASE}/hr/employees",
                      headers={"X-HR-Token": hr_tok},
                      json=body,
                      timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()["id"]


def _cleanup(emp_id: str) -> None:
    """Hard cleanup via admin DELETE — HR portal doesn't expose a
    per-employee DELETE, and soft-delete via the admin endpoint is
    sufficient to exclude the row from the iter353b base scope
    (`deleted_at: None` filter)."""
    try:
        admin = _multi_login().get("admin", "")
        if not admin:
            return
        requests.delete(f"{API_BASE}/admin/employees/{emp_id}",
                        headers={"X-Admin-Token": admin},
                        timeout=TIMEOUT)
    except Exception:
        pass


def _dispatch_summary(disp_tok: str) -> Dict:
    r = requests.get(f"{API_BASE}/dispatch/driver-qualification",
                     headers={"X-Dispatch-Token": disp_tok, "X-Admin-Token": ""},
                     timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def _dispatch_available_names(disp_tok: str):
    r = requests.get(f"{API_BASE}/dispatch/driver-qualification?available_now=true",
                     headers={"X-Dispatch-Token": disp_tok, "X-Admin-Token": ""},
                     timeout=TIMEOUT)
    r.raise_for_status()
    return [it["name"] for it in r.json()["items"]]


# ─────────────────────────────────────────────────────────────────────────────
# 1 · Summary payload shape
# ─────────────────────────────────────────────────────────────────────────────
def test_summary_exposes_availability_keys():
    disp = _multi_login()["dispatch"]
    s = _dispatch_summary(disp)["summary"]
    for k in ("available_now", "available_now_cdl", "available_now_non_cdl"):
        assert k in s, f"summary missing availability key {k}"


# ─────────────────────────────────────────────────────────────────────────────
# 2 · Inclusion · happy path
# ─────────────────────────────────────────────────────────────────────────────
def test_happy_path_driver_counted_as_available():
    hr = _hr_token()
    disp = _multi_login()["dispatch"]
    baseline = _dispatch_summary(disp)["summary"]["available_now"]
    emp = _seed_employee(hr)
    try:
        s = _dispatch_summary(disp)["summary"]
        assert s["available_now"] == baseline + 1, \
            f"happy-path driver not counted: baseline={baseline} after={s['available_now']}"
        assert s["available_now_cdl"] >= 1
        names = _dispatch_available_names(disp)
        assert any(n.startswith("iter353b avail") for n in names), \
            "seeded driver missing from filtered list"
    finally:
        _cleanup(emp)


def test_happy_path_non_cdl_approved_counted():
    """A non-CDL approved company driver with all other gates green
    MUST count — non-CDL approved is operationally valid."""
    hr = _hr_token()
    disp = _multi_login()["dispatch"]
    baseline = _dispatch_summary(disp)["summary"]
    emp = _seed_employee(
        hr,
        cdl_holder=False,
        cdl_expiration_date=None,
        # medical card empty is acceptable for non-CDL
        medical_card_expiration_date="",
    )
    try:
        s = _dispatch_summary(disp)["summary"]
        assert s["available_now_non_cdl"] == baseline["available_now_non_cdl"] + 1
        assert s["available_now"] == baseline["available_now"] + 1
    finally:
        _cleanup(emp)


# ─────────────────────────────────────────────────────────────────────────────
# 3 · Exclusion rules (one field flipped at a time)
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("override,reason", [
    ({"driver_status": "suspended"},         "suspended must NOT count"),
    ({"driver_status": "restricted"},        "restricted must NOT count"),
    ({"driver_status": "inactive"},          "inactive must NOT count"),
    ({"driver_status": ""},                  "unspecified driver_status must NOT count"),
    ({"approved_company_driver": False},     "non-approved must NOT count"),
    ({"cdl_expiration_date": YESTERDAY},     "expired CDL must NOT count"),
    ({"medical_card_expiration_date": YESTERDAY}, "expired medical card must NOT count"),
    ({"lifecycle_status": "Terminated"},     "terminated lifecycle must NOT count"),
    ({"lifecycle_status": "Inactive"},       "inactive lifecycle must NOT count"),
])
def test_exclusion_rules(override, reason):
    hr = _hr_token()
    disp = _multi_login()["dispatch"]
    baseline = _dispatch_summary(disp)["summary"]["available_now"]
    emp = _seed_employee(hr, **override)
    try:
        s = _dispatch_summary(disp)["summary"]
        assert s["available_now"] == baseline, \
            f"{reason} — override={override} baseline={baseline} after={s['available_now']}"
        names = _dispatch_available_names(disp)
        # seeded driver MUST be absent from the filtered list too
        emp_name_prefix = "iter353b avail"
        new_avail = [n for n in names if n.startswith(emp_name_prefix)]
        assert not new_avail, f"{reason} — seeded driver leaked into filter: {new_avail}"
    finally:
        _cleanup(emp)


# ─────────────────────────────────────────────────────────────────────────────
# 4 · Dispatch + FL parity (operator boundary)
# ─────────────────────────────────────────────────────────────────────────────
def test_availability_parity_dispatch_and_fl():
    hr = _hr_token()
    disp = _multi_login()["dispatch"]
    fl = _fl_token()
    emp = _seed_employee(hr)
    try:
        d = _dispatch_summary(disp)["summary"]
        f = requests.get(f"{API_BASE}/field-leadership/portal/driver-qualification",
                         headers={"X-FL-Token": fl, "X-Admin-Token": ""},
                         timeout=TIMEOUT).json()["summary"]
        for k in ("available_now", "available_now_cdl", "available_now_non_cdl"):
            assert d[k] == f[k], f"{k} differs: dispatch={d[k]} fl={f[k]}"
    finally:
        _cleanup(emp)


def test_availability_parity_with_hr_endpoint_present_or_absent():
    """If HR dashboard endpoint surfaces these keys, they MUST match
    Dispatch/FL. If not, that's acceptable (HR has the dedicated
    iter286/iter316 dashboard — the shared helper still drives Dispatch
    + FL identically)."""
    hr = _hr_token()
    disp = _multi_login()["dispatch"]
    d = _dispatch_summary(disp)["summary"]
    h = requests.get(f"{API_BASE}/hr/driver-qualification/dashboard",
                     headers={"X-HR-Token": hr, "X-Admin-Token": ""},
                     timeout=TIMEOUT).json().get("summary") or {}
    if "available_now" in h:
        assert h["available_now"] == d["available_now"]


# ─────────────────────────────────────────────────────────────────────────────
# 5 · Filter behavior matches summary count
# ─────────────────────────────────────────────────────────────────────────────
def test_filter_count_matches_summary_count():
    disp = _multi_login()["dispatch"]
    s = _dispatch_summary(disp)["summary"]
    r = requests.get(f"{API_BASE}/dispatch/driver-qualification?available_now=true",
                     headers={"X-Dispatch-Token": disp, "X-Admin-Token": ""},
                     timeout=TIMEOUT).json()
    assert r["count"] == s["available_now"], \
        f"filter count {r['count']} != summary {s['available_now']}"
    # And every returned row really IS available (sanity-check shape)
    for it in r["items"]:
        assert it.get("driver_status") == "active"
        assert it.get("approved_company_driver") is True


# ─────────────────────────────────────────────────────────────────────────────
# 6 · Read-only preserved
# ─────────────────────────────────────────────────────────────────────────────
def test_availability_endpoint_remains_get_only():
    disp = _multi_login()["dispatch"]
    for verb in ("post", "patch", "delete"):
        r = getattr(requests, verb)(
            f"{API_BASE}/dispatch/driver-qualification?available_now=true",
            headers={"X-Dispatch-Token": disp, "X-Admin-Token": ""},
            timeout=TIMEOUT,
        )
        assert r.status_code in (401, 403, 404, 405)


# ─────────────────────────────────────────────────────────────────────────────
# 7 · Frontend tile + filter wired
# ─────────────────────────────────────────────────────────────────────────────
def test_frontend_tile_present_in_shared_component():
    with open("/app/frontend/src/components/DriverQualificationReadOnlyView.jsx") as fh:
        s = fh.read()
    # Tile + click-to-filter wiring + 3 metric data-testids
    assert "availability-tile" in s
    assert "availability-total" in s
    assert "availability-cdl" in s
    assert "availability-non-cdl" in s
    assert "available_now" in s, "frontend must pass available_now query param"
    assert "Drivers Available Right Now" in s
