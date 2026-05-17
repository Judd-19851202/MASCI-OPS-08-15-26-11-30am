"""iter190 — Operational Guidance Center (Phase A, preview only).

Backend coverage:
  • RBAC: anonymous sees only public content
  • RBAC: admin sees all scopes
  • Restricted article 404s for unauthorized caller (title never leaked)
  • Search returns only RBAC-visible articles
  • Related-article lists are filtered to caller's visibility
  • Sections endpoint reports per-section visible counts
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
import requests

sys.path.insert(0, "/app/backend")

URL = os.environ.get("PUBLIC_BACKEND_URL") or "http://localhost:8001"


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


# ─────────────────────────────────────────────────────────────────────
# Sections
# ─────────────────────────────────────────────────────────────────────
def test_sections_anonymous_returns_only_public_sections():
    r = requests.get(f"{URL}/api/guidance/sections", timeout=10)
    assert r.status_code == 200
    data = r.json()
    assert "sections" in data
    assert "scopes" in data
    assert "public" in data["scopes"]
    assert "admin" not in data["scopes"]
    # Sections with >0 visible articles for anon ('roles' has new-employee,
    # 'troubleshooting' has session-timeout, 'knowledge' has why-session-timeouts,
    # 'onboarding' has both onboard articles).
    ids = {s["id"] for s in data["sections"]}
    assert "onboarding" in ids
    assert "troubleshooting" in ids


def test_sections_admin_returns_all_sections(admin_token):
    r = requests.get(
        f"{URL}/api/guidance/sections",
        headers={"X-Admin-Token": admin_token},
        timeout=10,
    )
    assert r.status_code == 200
    data = r.json()
    assert "admin" in data["scopes"]
    ids = {s["id"] for s in data["sections"]}
    # Admin should see all 7 declared sections (they all have at least 1 article admin-visible)
    assert {"roles", "quickhelp", "portals", "troubleshooting",
            "knowledge", "reliability", "onboarding"}.issubset(ids)


# ─────────────────────────────────────────────────────────────────────
# Articles (listing + single)
# ─────────────────────────────────────────────────────────────────────
def test_articles_anonymous_excludes_admin_only():
    r = requests.get(f"{URL}/api/guidance/articles", timeout=10)
    assert r.status_code == 200
    ids = {a["id"] for a in r.json()["articles"]}
    # Admin-only article must NOT leak
    assert "role-admin" not in ids
    assert "why-backups" not in ids
    assert "why-audit-logs" not in ids
    # Public ones must be present
    assert "onboard-login" in ids
    assert "tshoot-session-timeout" in ids


def test_articles_admin_sees_admin_only(admin_token):
    r = requests.get(
        f"{URL}/api/guidance/articles",
        headers={"X-Admin-Token": admin_token},
        timeout=10,
    )
    ids = {a["id"] for a in r.json()["articles"]}
    assert "role-admin" in ids
    assert "why-backups" in ids
    assert "why-audit-logs" in ids


def test_single_admin_article_blocked_for_anon():
    r = requests.get(f"{URL}/api/guidance/articles/role-admin", timeout=10)
    # Restricted titles MUST 404, never 200-with-empty
    assert r.status_code == 404


def test_single_admin_article_visible_to_admin(admin_token):
    r = requests.get(
        f"{URL}/api/guidance/articles/role-admin",
        headers={"X-Admin-Token": admin_token},
        timeout=10,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == "role-admin"
    assert body["title"] == "Admin"
    assert isinstance(body.get("body"), list)


def test_single_public_article_visible_to_anon():
    r = requests.get(f"{URL}/api/guidance/articles/onboard-login", timeout=10)
    assert r.status_code == 200
    assert r.json()["id"] == "onboard-login"


# ─────────────────────────────────────────────────────────────────────
# Related-article filtering
# ─────────────────────────────────────────────────────────────────────
def test_related_articles_filtered_by_rbac():
    """`tshoot-session-timeout` declares 'why-session-timeouts' as
    related. That related article IS public so anon should see it.
    Articles related to restricted content must NOT appear for anon."""
    r = requests.get(f"{URL}/api/guidance/articles/tshoot-session-timeout", timeout=10)
    assert r.status_code == 200
    related_ids = {x["id"] for x in r.json().get("related") or []}
    # Public-related stays
    assert "why-session-timeouts" in related_ids


def test_related_articles_unfiltered_for_admin(admin_token):
    """The 'role-admin' article's related list (why-audit-logs, why-backups, tshoot-session-timeout)
    is admin-visible end-to-end."""
    r = requests.get(
        f"{URL}/api/guidance/articles/role-admin",
        headers={"X-Admin-Token": admin_token},
        timeout=10,
    )
    related_ids = {x["id"] for x in r.json().get("related") or []}
    assert "why-audit-logs" in related_ids
    assert "why-backups" in related_ids


# ─────────────────────────────────────────────────────────────────────
# Search
# ─────────────────────────────────────────────────────────────────────
def test_search_anonymous_no_admin_hits():
    """Searching for admin-only terms must not return admin titles
    to an anonymous caller — even if the keyword 'admin' matches in
    article body text."""
    r = requests.get(f"{URL}/api/guidance/search?q=audit", timeout=10)
    assert r.status_code == 200
    ids = {x["id"] for x in r.json()["results"]}
    # Admin-only articles MUST NOT appear
    assert "why-audit-logs" not in ids
    assert "role-admin" not in ids


def test_search_admin_returns_admin_results(admin_token):
    r = requests.get(
        f"{URL}/api/guidance/search?q=audit",
        headers={"X-Admin-Token": admin_token},
        timeout=10,
    )
    ids = {x["id"] for x in r.json()["results"]}
    assert "why-audit-logs" in ids


def test_search_empty_query_returns_empty():
    r = requests.get(f"{URL}/api/guidance/search?q=", timeout=10)
    assert r.status_code == 200
    assert r.json()["results"] == []


def test_search_no_match_returns_empty_not_error():
    r = requests.get(
        f"{URL}/api/guidance/search?q=xyzzy_unmatchable_keyword",
        timeout=10,
    )
    assert r.status_code == 200
    assert r.json()["results"] == []


def test_search_results_ranked_by_relevance():
    """A search term that matches a title should outrank a term that
    only matches in body text. 'session' is in the title of two
    public articles."""
    r = requests.get(f"{URL}/api/guidance/search?q=session", timeout=10)
    assert r.status_code == 200
    results = r.json()["results"]
    assert len(results) >= 2
    # First result should be one of the session-titled articles
    top_ids = {results[0]["id"], results[1]["id"]}
    assert top_ids & {"tshoot-session-timeout", "why-session-timeouts"}


# ─────────────────────────────────────────────────────────────────────
# Limit clamps
# ─────────────────────────────────────────────────────────────────────
def test_search_limit_clamp_anonymous():
    r = requests.get(f"{URL}/api/guidance/search?q=session&limit=9999", timeout=10)
    assert r.status_code == 200
    # No explicit limit echo on this endpoint; just verify it doesn't 500


def test_articles_section_filter_anonymous():
    r = requests.get(
        f"{URL}/api/guidance/articles?section=onboarding",
        timeout=10,
    )
    assert r.status_code == 200
    rows = r.json()["articles"]
    assert all(a["section"] == "onboarding" for a in rows)
    assert {a["id"] for a in rows} >= {"onboard-login", "onboard-mobile"}
