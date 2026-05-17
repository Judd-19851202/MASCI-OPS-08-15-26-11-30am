"""iter191 — Operational Guidance · Phase B Iteration 1
(HR Portal + Field Leadership saturation, preview only).

Backend coverage:
  • New HR articles visible to HR + Admin; NOT visible to anon / leadership-only
  • New Field Leadership articles visible to Leadership + Admin; NOT to anon / HR-only
  • Cross-workflow connection articles respect multi-scope visibility
  • Search remains RBAC-aware for new HR/Field content
  • Titles never leak via 404 for unauthorized callers
  • portal-leadership only visible to leadership/admin
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
import requests

sys.path.insert(0, "/app/backend")

URL = os.environ.get("PUBLIC_BACKEND_URL") or "http://localhost:8001"

# Article IDs added in iter191 — kept as a fixture set so tests can verify the
# whole drop landed and is RBAC-gated correctly.
NEW_HR_IDS = {
    "hr-onboarding-new-hire",
    "hr-time-verification-deep",
    "hr-writeups-correctives",
    "hr-offboarding",
    "hr-cross-portal-reads",
    "hr-audit-trail",
}
NEW_LEADERSHIP_IDS = {
    "portal-leadership",
    "field-daily-report-howto",
    "field-equipment-checkout",
    "field-coaching-documentation",
    "field-incident-escalation",
    "field-writeup-authoring",
    "field-project-scope",
}
NEW_CONNECTION_IDS = {
    "connect-field-to-payroll",
    "connect-incident-to-audit",
}


def _env(key: str) -> str:
    p = Path("/app/backend/.env")
    if not p.exists():
        return ""
    for line in p.read_text().splitlines():
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1].strip().strip('"')
    return ""


@pytest.fixture
def admin_token():
    pw = _env("ADMIN_PASSWORD")
    if not pw:
        pytest.skip("ADMIN_PASSWORD not configured")
    r = requests.post(f"{URL}/api/admin/login", json={"password": pw}, timeout=10)
    r.raise_for_status()
    return r.json()["token"]


@pytest.fixture
def hr_token():
    """Login as the seeded HR manager."""
    r = requests.post(
        f"{URL}/api/hr/login",
        json={"email": "hrmanager@mascigc.com", "password": "HRTesting2026!"},
        timeout=10,
    )
    if r.status_code != 200:
        pytest.skip(f"HR seed login unavailable (status={r.status_code})")
    return r.json()["token"]


@pytest.fixture
def leadership_token():
    """Login via the shared MASCIGC Field Leadership password."""
    pw = _env("LEADERSHIP_PASSWORD") or "MASCIGC"
    r = requests.post(
        f"{URL}/api/field-leadership/login",
        json={"password": pw},
        timeout=10,
    )
    if r.status_code != 200:
        pytest.skip(f"Field Leadership login unavailable (status={r.status_code})")
    return r.json()["token"]


# ─────────────────────────────────────────────────────────────────────
# HR articles — visible to HR + Admin, not to anon or other portals
# ─────────────────────────────────────────────────────────────────────
def test_hr_token_sees_all_new_hr_articles(hr_token):
    r = requests.get(
        f"{URL}/api/guidance/articles",
        headers={"X-HR-Token": hr_token},
        timeout=10,
    )
    assert r.status_code == 200
    ids = {a["id"] for a in r.json()["articles"]}
    missing = NEW_HR_IDS - ids
    assert not missing, f"HR token should see all new HR articles; missing {missing}"


def test_admin_sees_all_new_hr_articles(admin_token):
    r = requests.get(
        f"{URL}/api/guidance/articles",
        headers={"X-Admin-Token": admin_token},
        timeout=10,
    )
    ids = {a["id"] for a in r.json()["articles"]}
    assert NEW_HR_IDS.issubset(ids)


def test_anon_does_not_see_any_new_hr_articles():
    r = requests.get(f"{URL}/api/guidance/articles", timeout=10)
    ids = {a["id"] for a in r.json()["articles"]}
    leaked = NEW_HR_IDS & ids
    assert not leaked, f"Anon must not see HR-scoped articles; leaked {leaked}"


@pytest.mark.parametrize("article_id", sorted(NEW_HR_IDS))
def test_anon_single_hr_article_404(article_id):
    r = requests.get(f"{URL}/api/guidance/articles/{article_id}", timeout=10)
    assert r.status_code == 404, f"{article_id} must 404 for anon (no title leak)"


@pytest.mark.parametrize("article_id", sorted(NEW_HR_IDS))
def test_hr_single_article_200(article_id, hr_token):
    r = requests.get(
        f"{URL}/api/guidance/articles/{article_id}",
        headers={"X-HR-Token": hr_token},
        timeout=10,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == article_id
    assert body.get("title")
    assert isinstance(body.get("body"), list) and len(body["body"]) > 0


# ─────────────────────────────────────────────────────────────────────
# Field Leadership articles — visible to leadership + Admin
# ─────────────────────────────────────────────────────────────────────
def test_leadership_token_sees_all_new_leadership_articles(leadership_token):
    r = requests.get(
        f"{URL}/api/guidance/articles",
        headers={"X-Leadership-Token": leadership_token},
        timeout=10,
    )
    assert r.status_code == 200
    ids = {a["id"] for a in r.json()["articles"]}
    missing = NEW_LEADERSHIP_IDS - ids
    assert not missing, f"Leadership token should see all new field articles; missing {missing}"


def test_admin_sees_all_new_leadership_articles(admin_token):
    r = requests.get(
        f"{URL}/api/guidance/articles",
        headers={"X-Admin-Token": admin_token},
        timeout=10,
    )
    ids = {a["id"] for a in r.json()["articles"]}
    assert NEW_LEADERSHIP_IDS.issubset(ids)


def test_anon_does_not_see_any_new_leadership_articles():
    r = requests.get(f"{URL}/api/guidance/articles", timeout=10)
    ids = {a["id"] for a in r.json()["articles"]}
    leaked = NEW_LEADERSHIP_IDS & ids
    assert not leaked, f"Anon must not see leadership articles; leaked {leaked}"


@pytest.mark.parametrize("article_id", sorted(NEW_LEADERSHIP_IDS))
def test_anon_single_leadership_article_404(article_id):
    r = requests.get(f"{URL}/api/guidance/articles/{article_id}", timeout=10)
    assert r.status_code == 404


# ─────────────────────────────────────────────────────────────────────
# Strict RBAC cross-isolation: HR token cannot see Field-only content
# and vice versa. (Admin scope crosses both; that's expected.)
# ─────────────────────────────────────────────────────────────────────
def test_hr_token_does_NOT_see_leadership_only_articles(hr_token):
    """HR-only scope should be blind to leadership-scoped articles.
    The `connect-*` articles are intentionally cross-scope and are
    excluded from this assertion."""
    r = requests.get(
        f"{URL}/api/guidance/articles",
        headers={"X-HR-Token": hr_token},
        timeout=10,
    )
    ids = {a["id"] for a in r.json()["articles"]}
    leadership_only = NEW_LEADERSHIP_IDS  # none of these include 'hr' in scopes
    leaked = leadership_only & ids
    assert not leaked, f"HR must not see leadership-only articles; leaked {leaked}"


def test_leadership_token_does_NOT_see_hr_only_articles(leadership_token):
    r = requests.get(
        f"{URL}/api/guidance/articles",
        headers={"X-Leadership-Token": leadership_token},
        timeout=10,
    )
    ids = {a["id"] for a in r.json()["articles"]}
    # All NEW_HR_IDS are scoped ["hr", "admin"] only
    leaked = NEW_HR_IDS & ids
    assert not leaked, f"Leadership must not see HR-only articles; leaked {leaked}"


# ─────────────────────────────────────────────────────────────────────
# Cross-workflow connection articles — multi-scope
# ─────────────────────────────────────────────────────────────────────
def test_connect_field_to_payroll_visible_to_hr(hr_token):
    """`connect-field-to-payroll` has scopes [field, leadership, hr, pm, admin]
    — HR should see it (the article teaches HR's side of the workflow)."""
    r = requests.get(
        f"{URL}/api/guidance/articles/connect-field-to-payroll",
        headers={"X-HR-Token": hr_token},
        timeout=10,
    )
    assert r.status_code == 200
    assert r.json()["id"] == "connect-field-to-payroll"


def test_connect_field_to_payroll_visible_to_leadership(leadership_token):
    r = requests.get(
        f"{URL}/api/guidance/articles/connect-field-to-payroll",
        headers={"X-Leadership-Token": leadership_token},
        timeout=10,
    )
    assert r.status_code == 200


def test_connect_incident_to_audit_visible_to_leadership(leadership_token):
    r = requests.get(
        f"{URL}/api/guidance/articles/connect-incident-to-audit",
        headers={"X-Leadership-Token": leadership_token},
        timeout=10,
    )
    assert r.status_code == 200


def test_connect_articles_not_visible_to_anon():
    """The connection articles are deliberately scoped — none include
    'public' — so anon must NOT see them."""
    for art_id in NEW_CONNECTION_IDS:
        r = requests.get(f"{URL}/api/guidance/articles/{art_id}", timeout=10)
        assert r.status_code == 404, f"{art_id} leaked to anon"


# ─────────────────────────────────────────────────────────────────────
# Search — RBAC-aware on new content
# ─────────────────────────────────────────────────────────────────────
def test_search_offboarding_hidden_from_anon():
    """'Offboarding' is HR-scoped — anon search must not return the title."""
    r = requests.get(f"{URL}/api/guidance/search?q=offboarding", timeout=10)
    assert r.status_code == 200
    ids = {x["id"] for x in r.json()["results"]}
    assert "hr-offboarding" not in ids


def test_search_offboarding_visible_to_hr(hr_token):
    r = requests.get(
        f"{URL}/api/guidance/search?q=offboarding",
        headers={"X-HR-Token": hr_token},
        timeout=10,
    )
    ids = {x["id"] for x in r.json()["results"]}
    assert "hr-offboarding" in ids


def test_search_writeup_returns_authoring_for_leadership(leadership_token):
    r = requests.get(
        f"{URL}/api/guidance/search?q=write-up",
        headers={"X-Leadership-Token": leadership_token},
        timeout=10,
    )
    ids = {x["id"] for x in r.json()["results"]}
    assert "field-writeup-authoring" in ids


def test_search_writeup_hr_does_not_leak_field_authoring(hr_token):
    """HR-scoped search should find the HR-side write-up article but NOT
    the leadership-only field-writeup-authoring article."""
    r = requests.get(
        f"{URL}/api/guidance/search?q=write-up",
        headers={"X-HR-Token": hr_token},
        timeout=10,
    )
    ids = {x["id"] for x in r.json()["results"]}
    assert "hr-writeups-correctives" in ids
    assert "field-writeup-authoring" not in ids


# ─────────────────────────────────────────────────────────────────────
# Sections coverage — portals section grows; counts reflect new articles
# ─────────────────────────────────────────────────────────────────────
def test_admin_sections_counts_grew(admin_token):
    r = requests.get(
        f"{URL}/api/guidance/sections",
        headers={"X-Admin-Token": admin_token},
        timeout=10,
    )
    sections = {s["id"]: s for s in r.json()["sections"]}
    # Portals section gained: 5 HR articles (in portals section) + 7 leadership articles → +12
    # Knowledge section gained: hr-cross-portal-reads, hr-audit-trail, field-project-scope,
    # connect-field-to-payroll, connect-incident-to-audit → +5
    assert sections["portals"]["count"] >= 12  # was 4 (HR/Safety/Shop/Admin), now ≥ 16
    assert sections["knowledge"]["count"] >= 13  # was 8, now ≥ 13


def test_hr_token_only_sees_hr_relevant_portal_articles(hr_token):
    """An HR-token caller browsing the portals section should see HR-portal
    articles + portal-hr — and explicitly NOT portal-leadership / portal-shop."""
    r = requests.get(
        f"{URL}/api/guidance/articles?section=portals",
        headers={"X-HR-Token": hr_token},
        timeout=10,
    )
    ids = {a["id"] for a in r.json()["articles"]}
    assert "portal-hr" in ids
    assert NEW_HR_IDS.issubset(ids | {"hr-cross-portal-reads", "hr-audit-trail"})  # 4 HR portal articles
    # leadership-only portal article should NOT appear
    assert "portal-leadership" not in ids
    assert "portal-shop" not in ids


# ─────────────────────────────────────────────────────────────────────
# Related-link RBAC filtering on new articles
# ─────────────────────────────────────────────────────────────────────
def test_hr_onboarding_related_filtered_for_hr_caller(hr_token):
    """hr-onboarding-new-hire declares related: hr-offboarding,
    hr-audit-trail, task-verify-time, role-hr — all visible to HR."""
    r = requests.get(
        f"{URL}/api/guidance/articles/hr-onboarding-new-hire",
        headers={"X-HR-Token": hr_token},
        timeout=10,
    )
    assert r.status_code == 200
    related_ids = {x["id"] for x in r.json().get("related") or []}
    assert "hr-offboarding" in related_ids
    assert "hr-audit-trail" in related_ids
    assert "role-hr" in related_ids


def test_field_daily_report_related_filtered_for_leadership(leadership_token):
    """field-daily-report-howto's related list includes the cross-workflow
    article connect-field-to-payroll — leadership scope sees it."""
    r = requests.get(
        f"{URL}/api/guidance/articles/field-daily-report-howto",
        headers={"X-Leadership-Token": leadership_token},
        timeout=10,
    )
    assert r.status_code == 200
    related_ids = {x["id"] for x in r.json().get("related") or []}
    assert "why-daily-reports" in related_ids
    assert "connect-field-to-payroll" in related_ids


# ─────────────────────────────────────────────────────────────────────
# Content quality smoke (operator directive: HOW + WHY + WHAT HAPPENS NEXT)
# ─────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("article_id", sorted(NEW_HR_IDS | NEW_LEADERSHIP_IDS - {"portal-leadership", "field-project-scope"}))
def test_major_article_has_why_callout(article_id, admin_token):
    """Every major Phase B article (excluding the 2 short quick-starts)
    must explicitly explain WHY it matters — operator directive."""
    r = requests.get(
        f"{URL}/api/guidance/articles/{article_id}",
        headers={"X-Admin-Token": admin_token},
        timeout=10,
    )
    assert r.status_code == 200
    blocks = r.json().get("body") or []
    types = [b.get("type") for b in blocks if isinstance(b, dict)]
    assert "why" in types, f"{article_id} missing a WHY callout (operator-required)"
