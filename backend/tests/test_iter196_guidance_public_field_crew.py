"""iter196 — Operational Guidance · Public Field Crew Training tier.

Operator directive: field crews and new employees may not have portal
logins but still need useful, safe public training. This iter adds 7
public-scoped articles (no portal scope required) so the no-login view
becomes a useful starting point — not an empty shell.

Coverage:
  • All 7 new public articles fetchable by anonymous callers (200)
  • New public articles surface in /api/guidance/articles for anon
  • Anonymous users see at least 10 articles (5 pre-existing + 7 new
    minus role-new-employee which was already public)
  • Public articles are NOT scoped to any restricted portal — they
    must never leak HR/Safety/Shop/Dispatch/PM/Admin operational intel
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
import requests

sys.path.insert(0, "/app/backend")

URL = os.environ.get("PUBLIC_BACKEND_URL") or "http://localhost:8001"

NEW_PUBLIC_IDS = {
    "public-mobile-qr",
    "public-photos",
    "public-daily-report-basics",
    "public-incident-basics",
    "public-cant-login",
    "public-who-to-ask",
    "public-why-documentation",
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


# ─────────────────────────────────────────────────────────────────────
# Anon visibility — every new public article must be fetchable
# ─────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("article_id", sorted(NEW_PUBLIC_IDS))
def test_anon_can_fetch_public_article(article_id):
    r = requests.get(f"{URL}/api/guidance/articles/{article_id}", timeout=10)
    assert r.status_code == 200, f"public article {article_id} not visible to anon"
    body = r.json()
    assert body["id"] == article_id
    assert body.get("title")
    assert isinstance(body.get("body"), list) and len(body["body"]) > 0


def test_anon_list_includes_all_new_public_articles():
    r = requests.get(f"{URL}/api/guidance/articles", timeout=10)
    assert r.status_code == 200
    ids = {a["id"] for a in r.json()["articles"]}
    missing = NEW_PUBLIC_IDS - ids
    assert not missing, f"Anon list missing new public articles: {missing}"


def test_anon_has_minimum_field_crew_tile_count():
    """The landing UI builds 10 curated public tiles. After iter196,
    the anon caller must be able to see at least 9 of those 10
    (role-new-employee + onboard-login + onboard-mobile + 7 new).
    This guarantees the field-crew training section is never empty."""
    r = requests.get(f"{URL}/api/guidance/articles", timeout=10)
    ids = {a["id"] for a in r.json()["articles"]}
    curated_tile_ids = {
        "role-new-employee", "onboard-login", "onboard-mobile",
        "public-mobile-qr", "public-photos", "public-daily-report-basics",
        "public-incident-basics", "public-cant-login", "public-who-to-ask",
        "public-why-documentation",
    }
    visible = curated_tile_ids & ids
    assert len(visible) >= 9, f"Only {len(visible)} of 10 field-crew tiles visible to anon: {visible}"


# ─────────────────────────────────────────────────────────────────────
# RBAC safety — public articles must not be scoped to restricted portals
# ─────────────────────────────────────────────────────────────────────
def test_public_articles_have_no_restricted_portal_scope():
    """Each new public article must have only `public` (and optionally
    cross-cutting scopes that anon already gets). It must NOT include
    hr/safety/shop/dispatch/pm/admin/leadership — those are restricted."""
    from guidance.content import _ARTICLES
    by_id = {a["id"]: a for a in _ARTICLES}
    restricted_scopes = {"hr", "safety", "shop", "dispatch", "pm", "admin", "leadership"}
    for aid in NEW_PUBLIC_IDS:
        a = by_id[aid]
        leak = set(a["scopes"]) & restricted_scopes
        assert not leak, f"Public article {aid} has restricted-portal scope leak: {leak}"
        assert "public" in a["scopes"], f"Public article {aid} missing `public` scope"


# ─────────────────────────────────────────────────────────────────────
# Content quality — public articles should explain WHY where relevant
# ─────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("article_id", [
    "public-photos", "public-daily-report-basics",
    "public-incident-basics", "public-why-documentation",
])
def test_public_why_article_has_why_block(article_id):
    r = requests.get(f"{URL}/api/guidance/articles/{article_id}", timeout=10)
    blocks = r.json().get("body") or []
    types = [b.get("type") for b in blocks if isinstance(b, dict)]
    assert "why" in types, f"Public article {article_id} missing WHY block"


# ─────────────────────────────────────────────────────────────────────
# Cross-link integrity — related ids resolve for anon
# ─────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("article_id", sorted(NEW_PUBLIC_IDS))
def test_public_article_related_links_resolve_for_anon(article_id):
    """Related-article links inside public articles must point only at
    other articles anon can see — otherwise we'd render dead links."""
    r = requests.get(f"{URL}/api/guidance/articles/{article_id}", timeout=10)
    related = r.json().get("related") or []
    # Each related entry should have an id + title (visible)
    for rel in related:
        assert rel.get("id"), f"{article_id} has malformed related entry"
        assert rel.get("title"), f"{article_id} related {rel['id']} missing title (not visible to anon)"


# ─────────────────────────────────────────────────────────────────────
# Coverage Dashboard reflects the growth (admin governance signal)
# ─────────────────────────────────────────────────────────────────────
def test_coverage_dashboard_article_count_post_iter196(admin_token):
    r = requests.get(
        f"{URL}/api/admin/guidance/coverage",
        headers={"X-Admin-Token": admin_token},
        timeout=10,
    )
    assert r.status_code == 200
    # Was ≥85 post-iter193, +7 from iter196 = ≥92
    assert r.json()["article_count"] >= 92


def test_search_finds_new_public_content_for_anon():
    """A real-world anon search ('photo') must surface the new
    public-photos article — otherwise the field-crew can't find it."""
    r = requests.get(f"{URL}/api/guidance/search?q=photo", timeout=10)
    assert r.status_code == 200
    ids = {x["id"] for x in r.json()["results"]}
    assert "public-photos" in ids
