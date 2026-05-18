"""Pass 5c — Admin onboarding + login-troubleshoot.

Two new public-scope articles authored:
  • onboard-admin-first-week  / tshoot-admin-login

This is the final pair in the Tier-1 identity-triple cleanup. After
Pass 5c, every protected portal (HR, Safety, Shop, Dispatch, PM,
Admin, Field Leadership) has the complete public identity triple.

Discipline: Admin onboarding may reference admin-style activities
(read the audit log, sit beside the current operator, post end-of-day
summaries) but MUST NOT enumerate protected admin workflows
(user-management procedures, backup procedures, role-template editing).
"""
import os
import httpx
import pytest

API_URL = os.environ.get(
    "PUBLIC_API_URL",
    os.environ.get("API_URL", "http://localhost:8001"),
)

PASS_5C_IDS = [
    "onboard-admin-first-week",
    "tshoot-admin-login",
]

BANNED_WORKFLOW_PHRASES = [
    # Workflow enumerations from any portal
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
    # Admin-specific workflow enumerations (most-sensitive)
    "User management — invite",
    "Role templates — define",
    "Audit log — every privileged",
    "Backups & restore — manual triggers",
    "Sessions — who is signed in",
    "Operational inventory & governance",
]


@pytest.mark.parametrize("aid", PASS_5C_IDS)
def test_pass5c_article_is_public_scope(aid):
    import guidance  # noqa: F401
    from guidance.content import _ARTICLES
    a = next((x for x in _ARTICLES if x["id"] == aid), None)
    assert a is not None
    assert a["scopes"] == ["public"]


@pytest.mark.parametrize("aid", PASS_5C_IDS)
def test_pass5c_article_anon_readable(aid):
    r = httpx.get(f"{API_URL}/api/guidance/articles/{aid}", timeout=10.0)
    assert r.status_code == 200
    data = r.json()
    assert data.get("title")
    body = data.get("body") or []
    assert 4 <= len(body) <= 9


@pytest.mark.parametrize("aid", PASS_5C_IDS)
def test_pass5c_article_has_spanish(aid):
    import guidance  # noqa: F401
    from guidance.content import _ARTICLES
    a = next((x for x in _ARTICLES if x["id"] == aid), None)
    assert isinstance(a.get("title_es"), str) and a["title_es"]
    assert isinstance(a.get("body_es"), list) and len(a["body_es"]) >= 4


@pytest.mark.parametrize("aid", PASS_5C_IDS)
def test_pass5c_article_does_not_leak_workflows(aid):
    """Tier-1 admin onboarding must not enumerate protected admin workflows."""
    import guidance  # noqa: F401
    from guidance.content import _ARTICLES
    a = next((x for x in _ARTICLES if x["id"] == aid), None)
    body_text = " ".join(
        (b.get("text") or "") + " " + " ".join(b.get("items") or [])
        for b in a.get("body", [])
    )
    leaks = [t for t in BANNED_WORKFLOW_PHRASES if t in body_text]
    assert not leaks, f"{aid} leaks workflow phrases: {leaks}"


@pytest.mark.parametrize("aid", PASS_5C_IDS)
def test_pass5c_related_links_only_public(aid):
    import guidance  # noqa: F401
    from guidance.content import _ARTICLES
    scope_map = {x["id"]: x.get("scopes") or [] for x in _ARTICLES}
    a = next((x for x in _ARTICLES if x["id"] == aid), None)
    for rel in a.get("related") or []:
        scopes = scope_map.get(rel, [])
        assert "public" in scopes, (
            f"{aid}.related['{rel}'] is not public; would 404 for anon"
        )


def test_identity_triple_drift_fully_cleared():
    """Pass 5c closes the identity-incomplete drift category entirely.

    After this pass, no portal should appear in the
    `portal-identity-incomplete` drift bucket.
    """
    import guidance  # noqa: F401
    from governance.inventory import compute_drift
    d = compute_drift()
    incomplete = [
        it for it in d["items"]
        if it["category"] == "portal-identity-incomplete"
    ]
    assert incomplete == [], (
        f"Pass 5c should fully clear identity-incomplete drift; "
        f"still flagged: {[it['subject'] for it in incomplete]}"
    )


def test_admin_onboarding_emphasizes_caution():
    """Admin onboarding article should explicitly warn about going slow
    and the high-trust nature of the role — that's the entire point of
    the article."""
    import guidance  # noqa: F401
    from guidance.content import _ARTICLES
    a = next(
        (x for x in _ARTICLES if x["id"] == "onboard-admin-first-week"),
        None,
    )
    body = " ".join(
        (b.get("text") or "") + " " + " ".join(b.get("items") or [])
        for b in a.get("body", [])
    ).lower()
    # At least one of these caution-anchoring phrases must be present
    cautions = ["slow", "deliberate", "supervision", "trust", "audit"]
    assert any(c in body for c in cautions), (
        "Admin onboarding must explicitly anchor caution / slowness / "
        "audit-first culture; none of the expected phrases found"
    )
