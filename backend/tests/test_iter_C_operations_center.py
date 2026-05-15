"""Iter C · Operations Center — backend completeness tests.

Confirms the GET /api/operations-center endpoint:
  * gates on portal token (anon → 401)
  * returns role-aware cards per ROLE_VISIBILITY
  * audit_coverage card returns a valid {modules, covered, total,
    coverage_pct} dict on admin
  * cards include 'severity', 'url', 'key' fields
  * 'count' cards have integer count >= 0
"""
import os
from pathlib import Path

import pytest
import requests


def _kv(p, k):
    try:
        with open(p) as f:
            for ln in f:
                if ln.startswith(f"{k}="):
                    return ln.split("=", 1)[1].strip().strip('"').rstrip("/")
    except Exception:
        pass
    return ""


BASE_URL = (_kv(Path("/app/frontend/.env"), "REACT_APP_BACKEND_URL")
            or os.environ.get("REACT_APP_BACKEND_URL", "")).rstrip("/")
NO_ADMIN = {"X-Admin-Token": ""}


def _safety_token():
    r = requests.post(f"{BASE_URL}/api/safety/login",
                       json={"email": "safety@mascigc.com",
                             "password": "SafetyTest2026!"}, timeout=20)
    if r.status_code != 200:
        pytest.skip(f"Safety login failed: {r.status_code}")
    return r.json()["token"]


def _hr_token():
    r = requests.post(f"{BASE_URL}/api/hr/login",
                       json={"email": "hrmanager@mascigc.com",
                             "password": "HRTesting2026!"}, timeout=20)
    if r.status_code != 200:
        pytest.skip(f"HR login failed: {r.status_code}")
    return r.json()["token"]


def test_anon_returns_401():
    r = requests.get(f"{BASE_URL}/api/operations-center",
                      headers=NO_ADMIN, timeout=20)
    assert r.status_code == 401


def test_admin_returns_full_cards():
    """Conftest auto-injects admin token. Admin sees all 15 visibility keys."""
    r = requests.get(f"{BASE_URL}/api/operations-center", timeout=20)
    assert r.status_code == 200
    d = r.json()
    assert d["role"] == "admin"
    keys = {c["key"] for c in d["cards"]}
    expected = {
        "tasks_overdue", "tasks_open",
        "po_pending_approval", "po_missing_receipt", "po_overdue_receipt",
        "doc_exp_expiring", "doc_exp_expired",
        "incidents_open", "ca_overdue",
        "equipment_down", "equipment_holds",
        "preop_failed_recent",
        "integration_health", "audit_coverage",
    }
    assert expected.issubset(keys), f"missing keys: {expected - keys}"


def test_safety_scope():
    tok = _safety_token()
    r = requests.get(f"{BASE_URL}/api/operations-center",
                      headers={"X-Safety-Token": tok, **NO_ADMIN}, timeout=20)
    assert r.status_code == 200
    d = r.json()
    assert d["role"] == "safety"
    keys = {c["key"] for c in d["cards"]}
    # Safety should see incidents/CAs/doc_exp/tasks
    assert "incidents_open" in keys
    assert "ca_overdue" in keys
    assert "doc_exp_expiring" in keys
    assert "tasks_overdue" in keys
    # Safety should NOT see equipment_down / po_pending_approval cards
    assert "equipment_down" not in keys
    assert "po_pending_approval" not in keys


def test_hr_scope():
    tok = _hr_token()
    r = requests.get(f"{BASE_URL}/api/operations-center",
                      headers={"X-HR-Token": tok, **NO_ADMIN}, timeout=20)
    assert r.status_code == 200
    d = r.json()
    assert d["role"] == "hr"
    keys = {c["key"] for c in d["cards"]}
    assert "lifecycle_pending_offboarding" in keys
    assert "doc_exp_expired" in keys
    assert "po_missing_receipt" in keys
    # HR should not see incidents/equipment/CAs cards
    assert "incidents_open" not in keys
    assert "equipment_down" not in keys
    assert "ca_overdue" not in keys


def test_card_shape():
    """Every card must carry key/label/severity/url and EITHER count OR value."""
    r = requests.get(f"{BASE_URL}/api/operations-center", timeout=20)
    d = r.json()
    for c in d["cards"]:
        assert c["key"]
        assert c["label"]
        assert c["severity"] in ("Critical", "Warning", "Info")
        assert "url" in c
        assert ("count" in c) or ("value" in c)
        if "count" in c:
            assert isinstance(c["count"], int) and c["count"] >= 0


def test_audit_coverage_card():
    r = requests.get(f"{BASE_URL}/api/operations-center", timeout=20)
    d = r.json()
    ac = next((c for c in d["cards"] if c["key"] == "audit_coverage"), None)
    assert ac is not None
    v = ac["value"]
    assert "modules" in v
    assert "covered" in v and "total" in v and "coverage_pct" in v
    assert isinstance(v["coverage_pct"], int)
    assert 0 <= v["coverage_pct"] <= 100
    # Expected three modules
    mods = {m["module"] for m in v["modules"]}
    assert {"po_requests", "employees", "incidents"}.issubset(mods)


def test_admin_role_override():
    """Admin can preview another role's center."""
    r = requests.get(f"{BASE_URL}/api/operations-center",
                      params={"role_override": "hr"}, timeout=20)
    d = r.json()
    assert d["role"] == "hr"
    keys = {c["key"] for c in d["cards"]}
    assert "lifecycle_pending_offboarding" in keys


def test_non_admin_role_override_ignored():
    """Non-admin cannot use role_override (would be a leak)."""
    tok = _safety_token()
    r = requests.get(f"{BASE_URL}/api/operations-center",
                      params={"role_override": "admin"},
                      headers={"X-Safety-Token": tok, **NO_ADMIN}, timeout=20)
    d = r.json()
    assert d["role"] == "safety"  # ignored
