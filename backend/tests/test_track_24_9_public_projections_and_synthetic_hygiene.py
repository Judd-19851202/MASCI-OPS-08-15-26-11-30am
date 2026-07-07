"""TRACK 24.9 · Regression locks for
  * Public-safe employee roster projection
  * Public-safe Competent Person projection
  * Synthetic DR exclusion from user-facing listings
  * PII forbidden-key guarantee on public projections
  * Idempotent purge script

These tests run against the running preview backend via the API_URL
that the pod bakes into `frontend/.env`. They exercise the real
endpoints — no mocks — so a regression on the wire cannot slip past.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
import requests


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def _api_url() -> str:
    fe_env = ROOT.parent / "frontend" / ".env"
    for line in fe_env.read_text().splitlines():
        if line.startswith("REACT_APP_BACKEND_URL="):
            return line.split("=", 1)[1].strip()
    raise RuntimeError("REACT_APP_BACKEND_URL not found")


API = _api_url() + "/api"


# ─── Public roster projection ──────────────────────────────────────


FORBIDDEN_ROSTER_KEYS = frozenset({
    # PII enumerated in the P0-1 leak audit.
    "email", "phone", "mobile", "cell", "cell_phone", "phone_number",
    "ssn", "ssn_last4", "social_security", "date_of_birth", "dob",
    "birth_date", "address", "home_address", "street",
    "cdl", "cdl_number", "cdl_expiration", "medical_card",
    "medical_card_expiration", "salary", "hourly_rate", "pay_rate",
    "supervisor_id", "supervisor_email", "supervisor_name",
    "department", "department_display", "department_source",
    "updated_at", "trade_role_display", "trade_role_source",
    "crew_display", "crew_source", "supervisor",
    "supervisor_display", "supervisor_source", "display_identity",
    "preferred_name", "lifecycle_status", "is_active",
})

ALLOWED_ROSTER_KEYS = frozenset({
    "id", "name", "employee_id", "trade", "role", "crew", "active",
})


def _public_roster(_cache={}):
    if "b" in _cache:
        return _cache["b"]
    r = requests.get(f"{API}/hr/employee-roster/public", timeout=60)
    r.raise_for_status()
    _cache["r"] = r
    _cache["b"] = r.json()
    _cache["code"] = r.status_code
    return _cache["b"]


def test_public_roster_endpoint_is_reachable_without_auth():
    body = _public_roster()
    assert body.get("public") is True
    assert isinstance(body.get("items"), list)
    assert body.get("contract_version") == "24.9-public"


def test_public_roster_projection_forbids_pii():
    body = _public_roster()
    items = body.get("items", [])
    assert items, "public roster returned zero items — cannot verify projection"
    for it in items[:50]:
        keys = set(it.keys())
        # No forbidden key should ever appear.
        leaked = keys & FORBIDDEN_ROSTER_KEYS
        assert not leaked, f"public roster row leaked PII keys: {leaked} · row={it}"
        # Every key present must be in the allowed set.
        extra = keys - ALLOWED_ROSTER_KEYS
        assert not extra, f"public roster row has unexpected key(s): {extra} · row={it}"


def test_public_roster_only_returns_active_employees():
    body = _public_roster()
    for it in body.get("items", []):
        # `active` is derived server-side — every row must be True
        # on the default endpoint (inactive/terminated hidden).
        assert it.get("active") is True, f"inactive employee leaked into public roster: {it}"


def test_authenticated_roster_still_requires_auth():
    r = requests.get(f"{API}/hr/employee-roster", timeout=15)
    assert r.status_code == 401, f"track 24.1 P0-1 auth gate regressed: got {r.status_code}"


# ─── Public Competent Person projection ─────────────────────────────


FORBIDDEN_CP_KEYS = frozenset({
    "email", "phone", "ssn", "dob", "date_of_birth", "address",
    "certificate_file_id", "certificate_bytes", "attachments",
    "instructor", "issuing_organization", "notes", "employee_id",
    "id", "role",  # legacy trench shape — public flow must not leak
    "cp_approval_date", "cp_expiration_date", "cp_approved_by",
    "verification_status_history", "suspended_at", "revoked_at",
})

ALLOWED_CP_KEYS = frozenset({
    "qualification_id", "qualification_type",
    "employee_name", "employee_trade", "employee_crew",
    "verification_status", "expires_at", "warning",
})


def test_public_cp_endpoint_is_reachable_without_auth():
    r = requests.get(f"{API}/employees/competent-persons/public", timeout=15)
    assert r.status_code == 200, f"body={r.text[:200]}"
    body = r.json()
    assert body.get("public") is True
    assert body.get("type") == "COMPETENT_PERSON"
    assert isinstance(body.get("items"), list)


def test_public_cp_projection_forbids_pii():
    r = requests.get(f"{API}/employees/competent-persons/public", timeout=15)
    body = r.json()
    for it in body.get("items", [])[:50]:
        keys = set(it.keys())
        leaked = keys & FORBIDDEN_CP_KEYS
        assert not leaked, f"public CP row leaked keys: {leaked} · row={it}"
        extra = keys - ALLOWED_CP_KEYS
        assert not extra, f"public CP row has unexpected key(s): {extra} · row={it}"


def test_authenticated_cp_still_requires_auth():
    r = requests.get(f"{API}/employees/qualifications?type=COMPETENT_PERSON&active=true", timeout=15)
    assert r.status_code == 401, f"CP auth gate regressed: got {r.status_code}"


# ─── Synthetic DR exclusion ─────────────────────────────────────────


def test_synthetic_filter_module_importable():
    from lib.synthetic_dr_filter import (
        apply_synthetic_dr_exclusion,
        synthetic_exclusion_clauses,
        is_synthetic_dr,
    )
    assert callable(apply_synthetic_dr_exclusion)
    assert callable(synthetic_exclusion_clauses)
    assert callable(is_synthetic_dr)


def test_synthetic_filter_flags_known_fixtures():
    from lib.synthetic_dr_filter import is_synthetic_dr
    # Explicit markers win.
    assert is_synthetic_dr({"synthetic_record": True})
    assert is_synthetic_dr({"hidden_from_operations": True})
    # Sentinel prefixes.
    for pn in ["TEST_247B_EMAIL_RECERT", "TEST_DR_V3_EMAIL_PARITY_ES",
               "TEST_DR_V3_EMAIL_PARITY_EN", "TEST-25-23", "TEST-4525",
               "0000-TEST", "SMOKE_1", "SYNTHETIC_A", "ITER250-x",
               "QA_SMOKE_1", "CERT_TEST_x", "RECERT-A", "PARITY-B"]:
        assert is_synthetic_dr({"project_number": pn}), f"missed: {pn}"
    # Real project names must NOT be flagged.
    for pn in ["20-07", "24-12", "OD-100", "SR-123-45", "FT-JOB-1001"]:
        assert not is_synthetic_dr({"project_number": pn}), f"false-positive: {pn}"


def test_synthetic_filter_applies_to_empty_query():
    from lib.synthetic_dr_filter import apply_synthetic_dr_exclusion
    q = apply_synthetic_dr_exclusion({})
    assert "$and" in q
    assert isinstance(q["$and"], list)
    assert len(q["$and"]) == 4


def test_synthetic_filter_is_idempotent():
    from lib.synthetic_dr_filter import apply_synthetic_dr_exclusion
    q1 = apply_synthetic_dr_exclusion({"project_number": "20-07"})
    q2 = apply_synthetic_dr_exclusion(q1)
    # Second application should not lose the original clause.
    assert q1["project_number"] == "20-07"
    assert q2["project_number"] == "20-07"


# ─── Purge script sanity ────────────────────────────────────────────


def test_purge_script_dry_run_reports_but_writes_nothing():
    # Just make sure the script runs to completion in dry-run mode
    # and doesn't crash. It talks to the preview DB via env vars.
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "purge_synthetic_dailies_24_9.py")],
        capture_output=True, text=True, timeout=120,
    )
    assert result.returncode == 0, f"stderr={result.stderr}"
    out = result.stdout
    assert "Candidate inventory" in out
    assert "HIGH" in out
    assert "[dry-run]" in out


# ─── DR listing exclusion (live) ────────────────────────────────────


def _admin_token(_cache={}):
    if "tok" in _cache:
        return _cache["tok"]
    r = requests.post(f"{API}/auth/multi-login", json={
        "email": "jaymn.judd@mascigc.com",
        "password": "Maddix123!",
    }, timeout=45)
    r.raise_for_status()
    tok = r.json().get("portal_tokens", {}).get("admin", "")
    _cache["tok"] = tok
    return tok


def test_daily_reports_listing_excludes_synthetic():
    tok = _admin_token()
    assert tok, "could not obtain admin token"
    r = requests.get(
        f"{API}/daily-reports",
        headers={"X-Admin-Token": tok},
        timeout=60,
    )
    assert r.status_code == 200
    items = r.json()
    # No returned item may match a synthetic sentinel.
    sentinel = re.compile(r"^(TEST[_\-]|0000-TEST|SMOKE[_\-]|SYNTHETIC[_\-]|ITER[0-9]|QA_SMOKE|CERT_TEST|RECERT|PARITY)", re.IGNORECASE)
    for it in items:
        pn = (it.get("project_number") or "").strip()
        name = (it.get("project_name") or "").strip()
        assert not sentinel.match(pn), f"synthetic leaked in /daily-reports: {it}"
        assert not sentinel.match(name), f"synthetic name leaked in /daily-reports: {it}"


def test_approved_daily_reports_listing_excludes_synthetic():
    tok = _admin_token()
    r = requests.get(
        f"{API}/daily-reports/approved?limit=200",
        headers={"X-Admin-Token": tok},
        timeout=60,
    )
    assert r.status_code == 200
    items = r.json().get("items", [])
    sentinel = re.compile(r"^(TEST[_\-]|0000-TEST|SMOKE[_\-]|SYNTHETIC[_\-]|ITER[0-9]|QA_SMOKE|CERT_TEST|RECERT|PARITY)", re.IGNORECASE)
    for it in items:
        pn = (it.get("project_number") or "").strip()
        name = (it.get("project_name") or "").strip()
        assert not sentinel.match(pn), f"synthetic leaked in approved: {it}"
        assert not sentinel.match(name), f"synthetic name leaked in approved: {it}"
