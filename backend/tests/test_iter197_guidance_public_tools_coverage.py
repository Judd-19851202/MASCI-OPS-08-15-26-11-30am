"""iter197 — Operational Guidance · Public Field Tools Coverage.

Operator directive: every public/no-login surface in the actual platform
must have a public guidance article. The route audit (App.js) identified:
  - /equipment/submit       → Equipment Pre-Op (public)
  - /meetings/submit        → Safety Meeting / Toolbox Talk (public)
  - /qaqc, /qaqc/:slug/new  → QA/QC (public)
  - /field/calculators      → Material Calculator (public)
  - /submit, /inspections/submit → Site Inspection (public)
  - /jha, /trench-boxes     → Reference posters (public)
  - /cheatsheet             → Cheat sheet (public)
  - /daily/submit           → Daily Report (already covered)
  - /incidents/submit       → Incident (already covered, near-miss added)

iter197 adds:
  - public-preop-basics
  - public-toolbox-talks
  - public-qaqc-basics
  - public-material-calculator
  - public-tools-map (the index article)

And asserts no restricted-portal scope leakage.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
import requests

sys.path.insert(0, "/app/backend")

URL = os.environ.get("PUBLIC_BACKEND_URL") or "http://localhost:8001"

NEW_ITER197_IDS = {
    "public-preop-basics",
    "public-toolbox-talks",
    "public-qaqc-basics",
    "public-material-calculator",
    "public-tools-map",
}

# Full curated field-crew tile set the landing renders (15 tiles post-iter197)
CURATED_FIELD_TILES = {
    "public-tools-map",
    "role-new-employee", "onboard-login", "onboard-mobile",
    "public-mobile-qr", "public-photos", "public-daily-report-basics",
    "public-preop-basics", "public-toolbox-talks", "public-qaqc-basics",
    "public-material-calculator",
    "public-incident-basics", "public-cant-login", "public-who-to-ask",
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
# Every new iter197 article is fetchable by anonymous users
# ─────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("article_id", sorted(NEW_ITER197_IDS))
def test_anon_can_fetch_iter197_article(article_id):
    r = requests.get(f"{URL}/api/guidance/articles/{article_id}", timeout=10)
    assert r.status_code == 200, f"public article {article_id} not visible to anon"
    body = r.json()
    assert body["id"] == article_id
    assert body.get("title")
    assert isinstance(body.get("body"), list) and len(body["body"]) > 0


def test_full_curated_field_tile_set_visible_to_anon():
    """All 15 curated field-crew tile articles must be visible to anon
    — otherwise the public landing page can't render the full tile set."""
    r = requests.get(f"{URL}/api/guidance/articles", timeout=10)
    ids = {a["id"] for a in r.json()["articles"]}
    missing = CURATED_FIELD_TILES - ids
    assert not missing, f"Curated field tiles missing for anon: {missing}"


# ─────────────────────────────────────────────────────────────────────
# Operator-required topic coverage — each of the 7 operator items must
# be covered by at least one public article
# ─────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("topic,required_id", [
    ("Equipment Pre-Op Checks",          "public-preop-basics"),
    ("Safety Meetings / Toolbox Talks",  "public-toolbox-talks"),
    ("Accident / Incident / Near-Miss",  "public-incident-basics"),
    ("QA/QC System Basics",              "public-qaqc-basics"),
    ("Material Calculator / Field Tools","public-material-calculator"),
    ("Public Field Forms / Tools Overview", "public-tools-map"),
    ("General Mobile Use",               "onboard-mobile"),
])
def test_operator_required_topic_has_public_article(topic, required_id):
    r = requests.get(f"{URL}/api/guidance/articles/{required_id}", timeout=10)
    assert r.status_code == 200, f"Operator topic '{topic}' missing article {required_id}"


# ─────────────────────────────────────────────────────────────────────
# RBAC safety: no public article has a restricted-portal scope leak
# ─────────────────────────────────────────────────────────────────────
def test_no_iter197_public_article_leaks_restricted_scope():
    from guidance.content import _ARTICLES
    by_id = {a["id"]: a for a in _ARTICLES}
    restricted = {"hr", "safety", "shop", "dispatch", "pm", "admin", "leadership"}
    for aid in NEW_ITER197_IDS:
        a = by_id[aid]
        leak = set(a["scopes"]) & restricted
        assert not leak, f"Public article {aid} leaks restricted scope: {leak}"
        assert "public" in a["scopes"]


def test_no_public_article_anywhere_leaks_restricted_scope():
    """Hardening: ALL public-scoped articles (not just iter197) must be
    safe to show to anon. Catches any future regression that adds a
    restricted scope to a public article."""
    from guidance.content import _ARTICLES
    restricted = {"hr", "safety", "shop", "dispatch", "pm", "admin", "leadership"}
    leaks = []
    for a in _ARTICLES:
        scopes = set(a.get("scopes") or [])
        if "public" in scopes:
            leaked = scopes & restricted
            if leaked:
                leaks.append((a["id"], sorted(leaked)))
    assert not leaks, f"Public articles leaking restricted scopes: {leaks}"


# ─────────────────────────────────────────────────────────────────────
# Content quality — operational topics need WHY blocks
# ─────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("article_id", [
    "public-preop-basics", "public-toolbox-talks",
    "public-qaqc-basics", "public-material-calculator",
])
def test_public_iter197_article_has_why_block(article_id):
    r = requests.get(f"{URL}/api/guidance/articles/{article_id}", timeout=10)
    blocks = r.json().get("body") or []
    types = [b.get("type") for b in blocks if isinstance(b, dict)]
    assert "why" in types, f"Public article {article_id} missing WHY block"


# ─────────────────────────────────────────────────────────────────────
# Near-miss callout — iter197 added a TIP block to public-incident-basics
# ─────────────────────────────────────────────────────────────────────
def test_public_incident_basics_has_near_miss_callout():
    r = requests.get(f"{URL}/api/guidance/articles/public-incident-basics", timeout=10)
    body_text = " ".join(
        b.get("text", "") for b in r.json().get("body", []) if isinstance(b, dict)
    ).lower()
    assert "near-miss" in body_text, "public-incident-basics must mention near-miss"


# ─────────────────────────────────────────────────────────────────────
# Search reaches the new content
# ─────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("query,must_include", [
    ("pre-op",       "public-preop-basics"),
    ("toolbox",      "public-toolbox-talks"),
    ("qa/qc",        "public-qaqc-basics"),
    ("calculator",   "public-material-calculator"),
])
def test_anon_search_finds_new_public_content(query, must_include):
    r = requests.get(f"{URL}/api/guidance/search", params={"q": query}, timeout=10)
    assert r.status_code == 200
    ids = {x["id"] for x in r.json()["results"]}
    assert must_include in ids, f"Anon search '{query}' did not surface {must_include}"


# ─────────────────────────────────────────────────────────────────────
# Coverage Dashboard reflects post-iter197 article count
# ─────────────────────────────────────────────────────────────────────
def test_coverage_dashboard_count_post_iter197(admin_token):
    r = requests.get(
        f"{URL}/api/admin/guidance/coverage",
        headers={"X-Admin-Token": admin_token},
        timeout=10,
    )
    # Post-iter196 was ≥92. iter197 adds 5 new → ≥97
    assert r.json()["article_count"] >= 97
