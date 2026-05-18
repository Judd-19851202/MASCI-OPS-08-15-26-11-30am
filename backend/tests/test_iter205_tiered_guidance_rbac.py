"""iter205 — Tiered Guidance RBAC

Operator directive: Guidance is tiered, not all-public or all-locked.

  Tier 1 (public): identity / "what is this portal" / first-week
                   onboarding / login troubleshooting.
  Tier 2 (portal-scoped): operational deep-dives — workflows,
                   approval chains, escalations, audit expectations.
  Tier 3 (admin-sensitive): user mgmt, backups, payroll admin,
                   compliance exports.

These tests verify the public/portal split for the new identity
articles plus the deep portal-<x> training articles, ensure no
cross-portal leakage, and confirm Spanish translations land for both
tiers.
"""
import os
import httpx
import pytest

API_URL = os.environ.get(
    "PUBLIC_API_URL",
    os.environ.get("API_URL", "http://localhost:8001"),
)

IDENTITY_IDS = [
    "portal-hr-identity",
    "portal-safety-identity",
    "portal-shop-identity",
    "portal-dispatch-identity",
    "portal-pm-identity",
    "portal-admin-identity",
]

DEEP_IDS_PROTECTED = {
    "portal-hr":       ("hr", "admin"),
    "portal-safety":   ("safety", "admin"),
    "portal-shop":     ("shop", "admin"),
    "portal-dispatch": ("dispatch", "admin"),
    "portal-pm":       ("pm", "admin"),
    "portal-admin":    ("admin",),
}


# ─────────────────────────────────────────────────────────────────────
# Tier 1 — public identity articles
# ─────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("aid", IDENTITY_IDS)
def test_identity_article_is_public_scope(aid):
    """Every portal-<x>-identity article must be public-scope."""
    import guidance  # noqa: F401
    from guidance.content import _ARTICLES
    a = next((x for x in _ARTICLES if x["id"] == aid), None)
    assert a is not None, f"Article {aid} missing from registry"
    assert a["scopes"] == ["public"], (
        f"{aid} must be public-only; got {a['scopes']}"
    )


@pytest.mark.parametrize("aid", IDENTITY_IDS)
def test_identity_article_readable_by_anonymous(aid):
    """Anonymous user can fetch any portal-<x>-identity article."""
    r = httpx.get(f"{API_URL}/api/guidance/articles/{aid}", timeout=10.0)
    assert r.status_code == 200, f"{aid} anon GET → {r.status_code}"
    data = r.json()
    assert data.get("title")
    body = data.get("body") or []
    assert len(body) >= 4, f"{aid} body must be substantive (>=4 blocks)"


@pytest.mark.parametrize("aid", IDENTITY_IDS)
def test_identity_article_has_spanish(aid):
    """Identity articles must ship with title_es + body_es."""
    import guidance  # noqa: F401
    from guidance.content import _ARTICLES
    a = next((x for x in _ARTICLES if x["id"] == aid), None)
    assert a is not None
    assert isinstance(a.get("title_es"), str) and a["title_es"]
    assert isinstance(a.get("body_es"), list) and len(a["body_es"]) >= 4


# ─────────────────────────────────────────────────────────────────────
# Tier 2 — deep portal-scoped articles
# ─────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("aid,scopes", list(DEEP_IDS_PROTECTED.items()))
def test_deep_portal_article_is_portal_scoped(aid, scopes):
    """Deep portal-<x> articles must NOT be public."""
    import guidance  # noqa: F401
    from guidance.content import _ARTICLES
    a = next((x for x in _ARTICLES if x["id"] == aid), None)
    assert a is not None
    assert "public" not in a["scopes"], (
        f"{aid} must NOT be public-scope; got {a['scopes']}"
    )
    for s in scopes:
        assert s in a["scopes"], f"{aid} must include scope '{s}'"


@pytest.mark.parametrize("aid", list(DEEP_IDS_PROTECTED.keys()))
def test_deep_portal_article_404s_for_anonymous(aid):
    """Anonymous user gets 404 (no title leak) on deep portal training."""
    r = httpx.get(f"{API_URL}/api/guidance/articles/{aid}", timeout=10.0)
    assert r.status_code == 404, (
        f"{aid} anon should be 404; got {r.status_code}"
    )


@pytest.mark.parametrize("aid", list(DEEP_IDS_PROTECTED.keys()))
def test_deep_portal_article_has_spanish(aid):
    """All 6 rebuilt portal-<x> deep articles ship with Spanish."""
    import guidance  # noqa: F401
    from guidance.content import _ARTICLES
    a = next((x for x in _ARTICLES if x["id"] == aid), None)
    assert a is not None
    assert isinstance(a.get("title_es"), str) and a["title_es"]
    assert isinstance(a.get("body_es"), list) and len(a["body_es"]) >= 4


# ─────────────────────────────────────────────────────────────────────
# Tier 2 — admin sees all deep articles, HR sees only HR
# ─────────────────────────────────────────────────────────────────────
def _admin_token():
    r = httpx.post(
        f"{API_URL}/api/admin/login",
        json={"password": os.environ.get("ADMIN_PASSWORD", "MASCI1982!")},
        timeout=10.0,
    )
    return r.json().get("token")


def test_admin_can_read_all_deep_articles():
    token = _admin_token()
    assert token, "Admin login failed"
    for aid in DEEP_IDS_PROTECTED:
        r = httpx.get(
            f"{API_URL}/api/guidance/articles/{aid}",
            headers={"X-Admin-Token": token},
            timeout=10.0,
        )
        assert r.status_code == 200, f"admin → {aid} got {r.status_code}"


def test_hr_token_blocked_from_non_hr_deep_articles():
    r = httpx.post(
        f"{API_URL}/api/hr/login",
        json={"email": "hrmanager@mascigc.com", "password": "HRTesting2026!"},
        timeout=10.0,
    )
    hr = r.json().get("token")
    if not hr:
        pytest.skip("HR seed login unavailable in this env")
    # HR can read its own deep article
    r1 = httpx.get(
        f"{API_URL}/api/guidance/articles/portal-hr",
        headers={"X-HR-Token": hr},
        timeout=10.0,
    )
    assert r1.status_code == 200
    # HR cannot read other portals' deep articles
    for aid in ("portal-safety", "portal-shop", "portal-dispatch",
                "portal-pm", "portal-admin"):
        r2 = httpx.get(
            f"{API_URL}/api/guidance/articles/{aid}",
            headers={"X-HR-Token": hr},
            timeout=10.0,
        )
        assert r2.status_code == 404, (
            f"HR should NOT see {aid}; got {r2.status_code}"
        )


# ─────────────────────────────────────────────────────────────────────
# Frontend guard — Guidance card destinations point at identity articles
# ─────────────────────────────────────────────────────────────────────
def test_frontend_guidance_cards_point_at_identity_articles():
    """OperationalGuidanceCenter portal-directory cards must route the
    PRIMARY 'Open Training' action to the public identity article (so
    anon users land on real content, not a 404).
    """
    fpath = "/app/frontend/src/pages/guidance/OperationalGuidanceCenter.jsx"
    with open(fpath, encoding="utf-8") as fh:
        src = fh.read()
    for portal in ("hr", "safety", "shop", "dispatch", "pm", "admin"):
        assert f'trainingArticle: "portal-{portal}-identity"' in src, (
            f"Card for {portal} must route to portal-{portal}-identity"
        )
    # Leadership keeps its existing identity article id
    assert 'trainingArticle: "portal-leadership-identity"' in src
