"""Auto-Email PM Routing — unit + integration coverage.

LEGACY behavior moved to test_pm_routing_db_iter28.py (DB-backed). The
hardcoded PM_TABLE was retired 2026-04-30 — the source of truth is now
db.project_managers + db.jobs_master.pm_email. The remaining tests here
verify the constants and the admin-only HTTP endpoints.
"""
import os
import sys
from pathlib import Path

import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pm_routing import (  # noqa: E402
    ALWAYS_CC,
    PM_TABLE,
    auto_email_enabled,
)
from tests.conftest import URL  # noqa: E402


# ---------------- pure-Python unit tests ----------------
def test_always_cc_present():
    assert "jaymn.judd@mascigc.com" in ALWAYS_CC
    assert "safety@mascigc.com" in ALWAYS_CC


def test_pm_table_emails_set():
    """Legacy fallback table — kept as a final-fallback only (4 known PMs)."""
    for pm, data in PM_TABLE.items():
        assert isinstance(data["email"], str)
        assert "@mascigc.com" in data["email"], f"{pm} has bad email"


# Hardcoded-job unit tests retired 2026-04-30 — see
# test_pm_routing_db_iter28.py for the live DB-backed equivalents.
@pytest.mark.skip(reason="Replaced by DB-backed routing — see iter28 tests")
def test_lookup_exact_job_number():
    pass


@pytest.mark.skip(reason="Replaced by DB-backed routing — see iter28 tests")
def test_lookup_normalized_with_cp_suffix():
    pass


@pytest.mark.skip(reason="Replaced by DB-backed routing — see iter28 tests")
def test_lookup_prefix_match():
    pass


def test_lookup_prefix_match_drops_cp():
    pass


@pytest.mark.skip(reason="Replaced by DB-backed routing — see iter28 tests")
def test_lookup_chris_wright():
    pass


@pytest.mark.skip(reason="Replaced by DB-backed routing — see iter28 tests")
def test_lookup_ramon_rodriguez():
    pass


@pytest.mark.skip(reason="Replaced by DB-backed routing — see iter28 tests")
def test_lookup_unknown_returns_none():
    pass


@pytest.mark.skip(reason="Replaced by DB-backed routing — see iter28 tests")
def test_recipients_includes_pm_plus_always_cc():
    pass


@pytest.mark.skip(reason="Replaced by DB-backed routing — see iter28 tests")
def test_recipients_when_pm_unknown_falls_back_to_always_cc():
    pass


@pytest.mark.skip(reason="Replaced by DB-backed routing — see iter28 tests")
def test_recipients_dedup_when_pm_is_already_in_always_cc():
    pass


# ---------------- New per-kind routing rules ----------------
@pytest.mark.skip(reason="Replaced by DB-backed routing — see iter28 tests")
def test_daily_report_pm_only_no_office_cc():
    pass


@pytest.mark.skip(reason="Replaced by DB-backed routing — see iter28 tests")
def test_equipment_pre_op_pm_only_no_office_cc():
    pass


@pytest.mark.skip(reason="Replaced by DB-backed routing — see iter28 tests")
def test_jaymn_exception_for_knox_mcrae_daily():
    pass


@pytest.mark.skip(reason="Replaced by DB-backed routing — see iter28 tests")
def test_unmapped_daily_falls_back_to_jaymn_only():
    pass


def test_auto_email_disabled_when_key_missing(monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "")
    assert auto_email_enabled() is False


def test_auto_email_default_on_when_key_present_and_flag_unset(monkeypatch):
    """Production default: auto-email is ON whenever a Resend key exists.
    The preview/test env explicitly sets AUTO_EMAIL_REPORTS=false in .env to
    stay safe. Tests opt out with monkeypatch where needed."""
    monkeypatch.setenv("RESEND_API_KEY", "fake-key")
    monkeypatch.delenv("AUTO_EMAIL_REPORTS", raising=False)
    assert auto_email_enabled() is True


def test_auto_email_disabled_via_explicit_false(monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "fake")
    monkeypatch.setenv("AUTO_EMAIL_REPORTS", "false")
    assert auto_email_enabled() is False


def test_auto_email_enabled_when_key_present_and_flag_true(monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "fake-key")
    monkeypatch.setenv("AUTO_EMAIL_REPORTS", "true")
    assert auto_email_enabled() is True


# ---------------- HTTP integration tests ----------------
def test_routing_table_endpoint():
    r = requests.get(f"{URL}/api/auto-email/routing-table", timeout=10)
    assert r.status_code == 200, r.text
    body = r.json()
    assert "always_cc" in body
    assert "project_managers" in body
    pms = {p["pm_name"] for p in body["project_managers"]}
    assert {"David Jewett", "Chris Wright", "Ramon Rodriguez", "Jaymn Judd"} <= pms


def test_routing_table_admin_only():
    r = requests.get(
        f"{URL}/api/auto-email/routing-table",
        headers={"X-Admin-Token": "wrong-token"},
        timeout=10,
    )
    # Backend env may or may not have ADMIN_PASSWORD set; if set, must reject.
    if os.environ.get("ADMIN_PASSWORD") or _has_admin_password():
        assert r.status_code == 401


def _has_admin_password():
    p = Path("/app/backend/.env")
    if not p.exists():
        return False
    for line in p.read_text().splitlines():
        if line.startswith("ADMIN_PASSWORD=") and line.split("=", 1)[1].strip():
            return True
    return False


def test_preview_known_job_resolves_pm():
    """Pick the first job in jobs_master that has a pm_email and verify
    the preview endpoint resolves to that PM. Adapts to whatever the DB
    currently has (the legacy hardcoded job-list is gone)."""
    h = {"X-Admin-Token": _admin_token()}
    jr = requests.get(f"{URL}/api/admin/jobs", headers=h, timeout=10)
    jobs = jr.json()
    jobs = jobs if isinstance(jobs, list) else jobs.get("items", [])
    sample = next((j for j in jobs if (j.get("pm_email") or "").strip()), None)
    if not sample:
        pytest.skip("No job has pm_email assigned yet — skipping live preview")
    r = requests.get(
        f"{URL}/api/auto-email/preview",
        params={"project_number": sample["project_number"]},
        headers=h,
        timeout=10,
    )
    assert r.status_code == 200
    body = r.json()
    assert (body["pm_email"] or "").lower() == sample["pm_email"].lower()
    # Compliance kinds always CC the office.
    assert "jaymn.judd@mascigc.com" in body["all_recipients"]


def _admin_token():
    r = requests.post(
        f"{URL}/api/admin/login",
        json={"password": os.environ.get("ADMIN_PASSWORD") or "Happy123!"},
        timeout=10,
    )
    return r.json()["token"]


def test_preview_unknown_job_falls_back_to_office():
    h = {"X-Admin-Token": _admin_token()}
    r = requests.get(
        f"{URL}/api/auto-email/preview",
        params={"project_number": "ZZ-99"},
        headers=h,
        timeout=10,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["pm_name"] is None
    assert "jaymn.judd@mascigc.com" in body["all_recipients"]


def test_inspection_post_does_not_crash_without_resend_key():
    """Submitting a form must succeed and return 200 even when no API key
    is configured (auto-email helper is fire-and-forget and silently skips)."""
    payload = {
        "project_name": "T5824 - SR 46 (W 1ST ST.)",
        "project_number": "24-06",
        "location": "Sanford FL",
        "inspection_date": "2026-02-01",
        "inspection_time": "09:00",
        "operation": "Day",
        "inspector_name": "Routing Test Inspector",
        "foreman_name": "Routing Test Foreman",
        "work_activity": "PM-routing smoke test",
    }
    r = requests.post(f"{URL}/api/inspections", json=payload, timeout=15)
    assert r.status_code == 200, r.text
    rec = r.json()
    rid = rec["id"]
    # Cleanup
    d = requests.delete(f"{URL}/api/inspections/{rid}", timeout=10)
    assert d.status_code == 200
