"""Auto-Email PM Routing — unit + integration coverage.

Verifies:
  - In-process lookup (PM by job number, prefix, fuzzy job-name fallback).
  - Always-CC distribution rules (jaymn.judd + safety@).
  - Admin-only HTTP endpoints: /api/auto-email/preview and /routing-table.
  - That POST'ing a real form does NOT crash when RESEND_API_KEY is empty.
"""
import os
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pm_routing import (  # noqa: E402
    ALWAYS_CC,
    PM_TABLE,
    auto_email_enabled,
    find_pm_for_record,
    recipients_for_record,
)
from tests.conftest import URL  # noqa: E402


# ---------------- pure-Python unit tests ----------------
def test_always_cc_present():
    assert "jaymn.judd@mascigc.com" in ALWAYS_CC
    assert "safety@mascigc.com" in ALWAYS_CC


def test_pm_table_emails_set():
    for pm, data in PM_TABLE.items():
        assert isinstance(data["email"], str)
        assert "@mascigc.com" in data["email"], f"{pm} has bad email"
        assert len(data["jobs"]) >= 1


def test_lookup_exact_job_number():
    pm = find_pm_for_record({"project_number": "24-06"})
    assert pm is not None
    assert pm[0] == "David Jewett"


def test_lookup_normalized_with_cp_suffix():
    pm = find_pm_for_record({"project_number": "25-01 - CP"})
    assert pm is not None
    assert pm[0] == "David Jewett"


def test_lookup_prefix_match_drops_cp():
    """User types '25-01', table has '25-01-CP' → should still resolve."""
    pm = find_pm_for_record({"project_number": "25-01"})
    assert pm is not None
    assert pm[0] == "David Jewett"


def test_lookup_chris_wright():
    pm = find_pm_for_record({"project_number": "26-09 - CP"})
    assert pm is not None
    assert pm[0] == "Chris Wright"


def test_lookup_ramon_rodriguez():
    pm = find_pm_for_record({"project_number": "25-22-CP"})
    assert pm is not None
    assert pm[0] == "Ramon Rodriguez"


def test_lookup_unknown_returns_none():
    assert find_pm_for_record({"project_number": "99-99"}) is None
    assert find_pm_for_record({}) is None


def test_recipients_includes_pm_plus_always_cc():
    """Compliance forms (inspection/meeting/jha/incident) → PM + always-CC."""
    dist = recipients_for_record({"project_number": "24-06"}, kind="inspection")
    assert dist["pm_email"] == "davidjewett@mascigc.com"
    assert dist["to"] == ["davidjewett@mascigc.com"]
    assert "jaymn.judd@mascigc.com" in dist["cc"]
    assert "safety@mascigc.com" in dist["cc"]
    # No duplicates
    lower = [e.lower() for e in dist["all"]]
    assert len(lower) == len(set(lower))


def test_recipients_when_pm_unknown_falls_back_to_always_cc():
    """Compliance forms with unmapped job → always-CC becomes the to list."""
    dist = recipients_for_record({"project_number": "99-99"}, kind="incident")
    assert dist["pm_email"] is None
    assert dist["to"] == list(ALWAYS_CC)
    assert dist["cc"] == []


def test_recipients_dedup_when_pm_is_already_in_always_cc():
    """Jaymn Judd is on Knox McRae (26-06) AND in always-CC → no duplicate."""
    dist = recipients_for_record({"project_number": "26-06"}, kind="incident")
    lower = [e.lower() for e in dist["all"]]
    assert lower.count("jaymn.judd@mascigc.com") == 1


# ---------------- New per-kind routing rules ----------------
def test_daily_report_pm_only_no_office_cc():
    """Daily reports go ONLY to the assigned PM. No Jaymn / safety@ CC."""
    dist = recipients_for_record({"project_number": "24-06"}, kind="daily-report")
    assert dist["pm_email"] == "davidjewett@mascigc.com"
    assert dist["to"] == ["davidjewett@mascigc.com"]
    assert dist["cc"] == []
    assert "jaymn.judd@mascigc.com" not in [e.lower() for e in dist["all"]]
    assert "safety@mascigc.com" not in [e.lower() for e in dist["all"]]


def test_equipment_pre_op_pm_only_no_office_cc():
    """Equipment pre-ops go ONLY to the assigned PM."""
    dist = recipients_for_record({"project_number": "25-12"}, kind="equipment-inspection")
    assert dist["pm_email"] == "chriswright@mascigc.com"
    assert dist["to"] == ["chriswright@mascigc.com"]
    assert dist["cc"] == []
    assert "safety@mascigc.com" not in [e.lower() for e in dist["all"]]


def test_jaymn_exception_for_knox_mcrae_daily():
    """Jaymn IS the PM on 26-06 (Knox McRae) → he gets daily reports for that
    job naturally as the PM. Still no office CC."""
    dist = recipients_for_record({"project_number": "26-06"}, kind="daily-report")
    assert dist["pm_name"] == "Jaymn Judd"
    assert dist["pm_email"] == "jaymn.judd@mascigc.com"
    assert dist["to"] == ["jaymn.judd@mascigc.com"]
    assert dist["cc"] == []
    assert "safety@mascigc.com" not in [e.lower() for e in dist["all"]]


def test_unmapped_daily_falls_back_to_jaymn_only():
    """Daily/Equipment with custom project number → Jaymn handles
    (better than dropping the report). Still no safety@ CC."""
    dist = recipients_for_record({"project_number": "99-99"}, kind="daily-report")
    assert dist["pm_email"] is None
    assert dist["to"] == ["jaymn.judd@mascigc.com"]
    assert "safety@mascigc.com" not in [e.lower() for e in dist["all"]]


def test_auto_email_disabled_when_key_missing(monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "")
    assert auto_email_enabled() is False


def test_auto_email_default_off_when_key_present_but_flag_unset(monkeypatch):
    """Safety default — explicit opt-in required so preview/test envs
    don't burn through the production Resend quota."""
    monkeypatch.setenv("RESEND_API_KEY", "fake-key")
    monkeypatch.delenv("AUTO_EMAIL_REPORTS", raising=False)
    assert auto_email_enabled() is False


def test_auto_email_disabled_via_explicit_flag(monkeypatch):
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
    r = requests.get(
        f"{URL}/api/auto-email/preview",
        params={"project_number": "26-04"},
        timeout=10,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["pm_name"] == "David Jewett"
    assert body["pm_email"] == "davidjewett@mascigc.com"
    assert "jaymn.judd@mascigc.com" in body["all_recipients"]


def test_preview_unknown_job_falls_back_to_office():
    r = requests.get(
        f"{URL}/api/auto-email/preview",
        params={"project_number": "ZZ-99"},
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
