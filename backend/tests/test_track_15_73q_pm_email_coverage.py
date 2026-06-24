"""TRACK 15.73Q · PM-Email Coverage Endpoint — pytest gate.

Verifies that the admin observability endpoint is mounted, gated, and
returns the expected shape.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest
import requests
from dotenv import load_dotenv


load_dotenv(Path("/app/backend/.env"))
load_dotenv(Path("/app/frontend/.env"))

API_BASE = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
SUPER = os.environ.get("SUPER_ADMIN_EMAIL", "jaymn.judd@mascigc.com")
PWD = os.environ.get("SUPER_ADMIN_BOOTSTRAP_PASSWORD", "Maddix123!")


@pytest.fixture(scope="module")
def admin_token() -> str:
    r = requests.post(
        f"{API_BASE}/api/auth/multi-login",
        json={"email": SUPER, "password": PWD},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()["portal_tokens"]["admin"]


def test_pm_email_coverage_endpoint_requires_admin():
    r = requests.get(f"{API_BASE}/api/admin/pm-email-coverage", timeout=30)
    assert r.status_code in (401, 403), (
        f"PM-email coverage endpoint must require admin auth — got HTTP {r.status_code}"
    )


def test_pm_email_coverage_returns_expected_shape(admin_token: str):
    r = requests.get(
        f"{API_BASE}/api/admin/pm-email-coverage",
        headers={"X-Admin-Token": admin_token},
        timeout=60,
    )
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text[:200]}"
    body = r.json()
    # Required top-level keys
    for k in (
        "track", "summary", "active_projects_total",
        "active_projects_missing_pm_email",
        "active_projects_with_recent_drs_and_no_pm_email",
        "missing_rows_top_25", "remediation_note",
    ):
        assert k in body, f"missing key in response: {k}"
    # Summary counter keys
    for k in (
        "active_total", "active_with_pm_email", "active_missing_pm_email",
        "active_with_pm_name_no_email", "active_with_co_pm_email_only",
        "active_total_no_pm_no_copm", "active_malformed_pm_email",
    ):
        assert k in body["summary"], f"missing summary key: {k}"
    # Invariant: total = with_email + missing + malformed
    s = body["summary"]
    assert s["active_total"] == s["active_with_pm_email"] + s["active_missing_pm_email"] + s["active_malformed_pm_email"], (
        f"counter math broken: {s}"
    )
    # Top-25 rows must each carry the required fields
    for row in body["missing_rows_top_25"]:
        for k in ("project_number", "project_name", "pm_name", "pm_email",
                  "co_pm_emails", "recent_dr_count", "last_dr_date", "status"):
            assert k in row, f"missing field in missing-row: {k}  row={row}"


def test_pm_email_coverage_no_pii_leakage(admin_token: str):
    """The endpoint must NOT leak credentials, tokens, or session secrets."""
    r = requests.get(
        f"{API_BASE}/api/admin/pm-email-coverage",
        headers={"X-Admin-Token": admin_token},
        timeout=60,
    )
    body_text = r.text
    forbidden = ["password", "secret", "MONGO_URL", "RESEND_API_KEY", "Bearer "]
    for f in forbidden:
        assert f not in body_text, f"PM-email-coverage leaks {f!r}"
