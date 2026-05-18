"""Pass 5b — Shop + Dispatch onboarding + login-troubleshoot.

Four new public-scope articles authored:
  • onboard-shop-first-week      / tshoot-shop-login
  • onboard-dispatch-first-week  / tshoot-dispatch-login

Same Tier-1 discipline as Pass 5a:
  • public-scope (anonymous-readable)
  • Tier-1 in content (no enumerated portal workflows)
  • bilingual (title_es + body_es)
  • cross-linked only to public articles
"""
import os
import httpx
import pytest

API_URL = os.environ.get(
    "PUBLIC_API_URL",
    os.environ.get("API_URL", "http://localhost:8001"),
)

PASS_5B_IDS = [
    "onboard-shop-first-week",
    "tshoot-shop-login",
    "onboard-dispatch-first-week",
    "tshoot-dispatch-login",
]

BANNED_WORKFLOW_PHRASES = [
    "Time verification — comparing",
    "Employee accountability — write-ups",
    "Corrective actions — what gets fixed",
    "Fire extinguishers — inventory",
    "Pre-Op review — every field Pre-Op",
    "Damage reporting — what got bent",
    "Movement events — job-to-job",
    "Holds & transfers —",
    "Utilisation reports —",
    "Project dashboard — scope-filtered",
    "User management — invite",
    "Audit log — every privileged",
    "Backups & restore — manual triggers",
]


@pytest.mark.parametrize("aid", PASS_5B_IDS)
def test_pass5b_article_is_public_scope(aid):
    import guidance  # noqa: F401
    from guidance.content import _ARTICLES
    a = next((x for x in _ARTICLES if x["id"] == aid), None)
    assert a is not None
    assert a["scopes"] == ["public"]


@pytest.mark.parametrize("aid", PASS_5B_IDS)
def test_pass5b_article_anon_readable(aid):
    r = httpx.get(f"{API_URL}/api/guidance/articles/{aid}", timeout=10.0)
    assert r.status_code == 200, f"{aid} anon GET → {r.status_code}"
    data = r.json()
    assert data.get("title")
    body = data.get("body") or []
    assert 4 <= len(body) <= 9, (
        f"{aid} body should be 4-9 blocks; got {len(body)}"
    )


@pytest.mark.parametrize("aid", PASS_5B_IDS)
def test_pass5b_article_has_spanish(aid):
    import guidance  # noqa: F401
    from guidance.content import _ARTICLES
    a = next((x for x in _ARTICLES if x["id"] == aid), None)
    assert isinstance(a.get("title_es"), str) and a["title_es"]
    assert isinstance(a.get("body_es"), list) and len(a["body_es"]) >= 4


@pytest.mark.parametrize("aid", PASS_5B_IDS)
def test_pass5b_article_does_not_leak_workflows(aid):
    """Tier-1 articles must not enumerate operational workflows."""
    import guidance  # noqa: F401
    from guidance.content import _ARTICLES
    a = next((x for x in _ARTICLES if x["id"] == aid), None)
    body_text = " ".join(
        (b.get("text") or "") + " " + " ".join(b.get("items") or [])
        for b in a.get("body", [])
    )
    leaks = [t for t in BANNED_WORKFLOW_PHRASES if t in body_text]
    assert not leaks, f"{aid} leaks workflow phrases: {leaks}"


@pytest.mark.parametrize("aid", PASS_5B_IDS)
def test_pass5b_related_links_only_public(aid):
    """Related cross-links must all be public so anon never dead-ends."""
    import guidance  # noqa: F401
    from guidance.content import _ARTICLES
    scope_map = {x["id"]: x.get("scopes") or [] for x in _ARTICLES}
    a = next((x for x in _ARTICLES if x["id"] == aid), None)
    for rel in a.get("related") or []:
        scopes = scope_map.get(rel, [])
        assert "public" in scopes, (
            f"{aid}.related['{rel}'] is not public-scope; would 404 for anon"
        )


def test_drift_cleared_for_pass5b_personas():
    """Shop + Dispatch should clear the identity-incomplete drift after
    Pass 5b. Only Admin should remain (Pass 5c)."""
    import guidance  # noqa: F401
    from governance.inventory import compute_drift
    d = compute_drift()
    flagged = {
        it["subject"] for it in d["items"]
        if it["category"] == "portal-identity-incomplete"
    }
    for cleared in ("hr", "safety", "pm", "shop", "dispatch"):
        assert cleared not in flagged, (
            f"Pass 5a/5b cleared {cleared}; should not be in drift. "
            f"Currently flagged: {flagged}"
        )
    assert "admin" in flagged, (
        "Admin still pending Pass 5c — must still be in drift"
    )
