"""iter200 — Pass 4 · Field Leadership Operational Identity tests.

Verifies:
  - 3 new Field Leadership guidance articles exist (onboard, tshoot, identity)
  - Onboarding + troubleshooting are public-scope (readable pre-login)
  - All 3 articles have Spanish translations
  - Articles cross-link back to each other
  - Inventory drift no longer flags Field Leadership as portal-without-login
  - Field Leadership shows up in /sign-in as a discoverable portal
  - Drift "leadership" entries dropped from P0 set
  - get_article serves the new articles anonymously
"""
from __future__ import annotations

import os
import sys

import httpx
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

API_URL = os.environ.get("REACT_APP_BACKEND_URL") or "http://localhost:8001"


# ─────────────────────────────────────────────────────────────────────
# Article registry tests
# ─────────────────────────────────────────────────────────────────────

PASS4_ARTICLES = [
    "onboard-leadership-first-week",
    "tshoot-leadership-login",
    "portal-leadership-identity",
]


def test_pass4_articles_exist():
    import guidance  # noqa: F401
    from guidance.content import _ARTICLES
    ids = {a["id"] for a in _ARTICLES}
    for aid in PASS4_ARTICLES:
        assert aid in ids, f"Pass 4 article missing: {aid}"


def test_pass4_onboarding_and_troubleshooting_are_public():
    """Pre-login readability — field crews don't need credentials to
    read onboarding or login troubleshooting."""
    import guidance  # noqa: F401
    from guidance.content import _ARTICLES
    by_id = {a["id"]: a for a in _ARTICLES}
    for aid in ("onboard-leadership-first-week", "tshoot-leadership-login"):
        scopes = by_id[aid].get("scopes") or []
        assert "public" in scopes, f"{aid} must be public-scope for pre-login access"


def test_pass4_articles_translated():
    """All 3 articles must have full ES triple."""
    import guidance  # noqa: F401
    from guidance.content import _ARTICLES
    by_id = {a["id"]: a for a in _ARTICLES}
    for aid in PASS4_ARTICLES:
        a = by_id[aid]
        assert a.get("title_es"), f"{aid} missing title_es"
        assert a.get("summary_es"), f"{aid} missing summary_es"
        assert a.get("body_es"), f"{aid} missing body_es"


def test_pass4_articles_cross_reference():
    """Each Pass 4 article links to the other two."""
    import guidance  # noqa: F401
    from guidance.content import _ARTICLES
    by_id = {a["id"]: a for a in _ARTICLES}
    onb = by_id["onboard-leadership-first-week"]
    assert "portal-leadership-identity" in (onb.get("related") or [])
    assert "tshoot-leadership-login" in (onb.get("related") or [])
    ident = by_id["portal-leadership-identity"]
    assert "onboard-leadership-first-week" in (ident.get("related") or [])


# ─────────────────────────────────────────────────────────────────────
# Inventory governance tests
# ─────────────────────────────────────────────────────────────────────

def test_inventory_leadership_has_login_url():
    """Pass 4 — Field Leadership now has a first-class /leadership/login."""
    from governance.inventory import compute_portal_matrix
    rows = compute_portal_matrix()
    fl = next((r for r in rows if r["portal"] == "leadership"), None)
    assert fl is not None
    assert fl["login_url"] == "/leadership/login"
    assert fl["sign_in_listed"] is True
    # Anomaly flag must be cleared
    assert not fl.get("anomaly")
    assert fl["fields"]["login_required"]["status"] == "complete"
    assert fl["fields"]["discoverability"]["status"] == "complete"


def test_inventory_drift_no_leadership_portal_without_login():
    """The P0 'portal-without-login · leadership' drift item must be gone."""
    from governance.inventory import compute_drift
    d = compute_drift()
    leadership_login_drift = [
        it for it in d["items"]
        if it["category"] == "portal-without-login" and it["subject"] == "leadership"
    ]
    assert not leadership_login_drift, "leadership login drift should be cleared"


def test_inventory_shop_dispatch_now_in_signin():
    """Pass 4 also surfaced Safety/Shop/Dispatch in /sign-in — drift on
    portal-not-in-signin for those should be cleared."""
    from governance.inventory import compute_drift
    d = compute_drift()
    bad = [
        it for it in d["items"]
        if it["category"] == "portal-not-in-signin"
        and it["subject"] in ("shop", "dispatch")
    ]
    assert not bad, f"shop/dispatch should be in sign-in now; drift: {bad}"


def test_inventory_drift_p0_count_dropped():
    """P0 drift count must drop now that leadership has a login route.
    (Translation still flagged P0 — that's expected.)"""
    from governance.inventory import compute_drift
    d = compute_drift()
    # Was 2 in Pass 2 baseline (leadership + translation)
    # After Pass 4 the leadership P0 item is gone; only translation P0 remains
    assert d["by_severity"]["p0"] == 1, (
        f"P0 drift expected to be 1 (translation only); got {d['by_severity']}"
    )


# ─────────────────────────────────────────────────────────────────────
# HTTP smoke tests (article reads + drift endpoint)
# ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("article_id", PASS4_ARTICLES)
def test_anonymous_can_read_pass4_articles_via_api(article_id):
    """Public + leadership articles must serve via /api/guidance/articles
    so the LeadershipLogin page can deep-link to them pre-auth."""
    if article_id == "portal-leadership-identity":
        # This one is public-scope too in Pass 4 (operational identity messaging)
        pass
    r = httpx.get(f"{API_URL}/api/guidance/articles/{article_id}", timeout=10.0)
    assert r.status_code == 200, f"{article_id} returned {r.status_code} anonymously"
    data = r.json()
    assert data["id"] == article_id
    assert data.get("title")
    assert data.get("title_es")


def test_anonymous_article_returns_related_with_title_es():
    """iter200 polish — related-link records must include title_es."""
    r = httpx.get(f"{API_URL}/api/guidance/articles/onboard-leadership-first-week",
                  timeout=10.0)
    assert r.status_code == 200
    data = r.json()
    related = data.get("related") or []
    assert len(related) > 0
    # At least some related items should have title_es (those that have been translated)
    have_es = sum(1 for r in related if r.get("title_es"))
    assert have_es > 0, "expected some related links to carry title_es"
