"""iter192 — Operational Guidance · Phase B Iteration 2
(Safety + Shop/Fleet saturation, preview only).

Backend coverage:
  • New Safety articles visible to Safety + Admin; NOT visible to anon / shop / hr
  • New Shop articles visible to Shop + Admin; NOT visible to anon / safety / hr
  • Cross-portal articles (operator-emphasized) respect multi-scope visibility:
      - connect-shop-to-dispatch (shop, dispatch, leadership, pm, admin)
      - connect-equipment-lifecycle (shop, dispatch, hr, leadership, admin)
  • safety-photo-quality cross-portal (field, leadership, safety, shop, admin)
  • safety-near-miss-importance / safety-escalation-chain cross-portal (field, leadership, safety, admin)
  • Search remains RBAC-aware for new Safety/Shop content
  • Titles never leak via 404 for unauthorized callers
  • Cross-portal isolation: Safety doesn't see Shop-only, Shop doesn't see Safety-only
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
import requests

sys.path.insert(0, "/app/backend")

URL = os.environ.get("PUBLIC_BACKEND_URL") or "http://localhost:8001"

# Strictly safety-scoped (["safety", "admin"]) — in portals section
SAFETY_PORTAL_IDS = {
    "safety-incident-investigation",
    "safety-corrective-actions-workflow",
    "safety-audits-workflow",
    "safety-fire-extinguishers",
    "safety-training-compliance",
}
# Safety-led but cross-scope (knowledge section)
SAFETY_CROSS_IDS = {
    "safety-near-miss-importance",   # field, leadership, safety, admin
    "safety-escalation-chain",       # field, leadership, safety, admin
    "safety-photo-quality",          # field, leadership, safety, shop, admin
}
# Strictly shop-scoped (["shop", "admin"]) — in portals section
SHOP_PORTAL_IDS = {
    "shop-preop-deep",
    "shop-failed-preop-workflow",
    "shop-damage-reporting",
    "shop-maintenance-coordination",
    "shop-equipment-return",
}
# Shop knowledge — cross-portal where appropriate
SHOP_KNOWLEDGE_IDS = {
    "shop-operator-responsibilities",  # field, leadership, shop, admin
    "shop-downtime-logic",             # shop, dispatch, admin
}
NEW_CONNECTION_IDS = {
    "connect-shop-to-dispatch",       # shop, dispatch, leadership, pm, admin
    "connect-equipment-lifecycle",    # shop, dispatch, hr, leadership, admin
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
    r = requests.post(
        f"{URL}/api/hr/login",
        json={"email": "hrmanager@mascigc.com", "password": "HRTesting2026!"},
        timeout=10,
    )
    if r.status_code != 200:
        pytest.skip(f"HR seed login unavailable (status={r.status_code})")
    return r.json()["token"]


@pytest.fixture
def safety_token():
    """Login as the seeded Safety user.
    Self-bootstraps via admin password-reset if the stored credential is stale
    (mirrors the iter179 dispatch self-bootstrap pattern documented in
    test_credentials.md)."""
    r = requests.post(
        f"{URL}/api/safety/login",
        json={"email": "safety@mascigc.com", "password": "SafetyTest2026!"},
        timeout=10,
    )
    if r.status_code == 200:
        return r.json()["token"]
    # Stale credential — self-bootstrap via admin reset
    pw = _env("ADMIN_PASSWORD")
    if not pw:
        pytest.skip("ADMIN_PASSWORD not configured")
    a = requests.post(f"{URL}/api/admin/login", json={"password": pw}, timeout=10)
    if a.status_code != 200:
        pytest.skip(f"Admin login failed for safety bootstrap (status={a.status_code})")
    admin_tok = a.json()["token"]
    users = requests.get(
        f"{URL}/api/admin/safety-users",
        headers={"X-Admin-Token": admin_tok},
        timeout=10,
    ).json()
    users = users if isinstance(users, list) else users.get("items", [])
    target = next((u for u in users if u.get("email") == "safety@mascigc.com"), None)
    if not target:
        pytest.skip("Safety seed user not present in directory")
    rp = requests.post(
        f"{URL}/api/admin/safety-users/{target['id']}/reset-password",
        json={},
        headers={"X-Admin-Token": admin_tok},
        timeout=10,
    )
    if rp.status_code != 200:
        pytest.skip(f"Safety password reset failed (status={rp.status_code})")
    temp_pw = rp.json().get("temp_password")
    if not temp_pw:
        pytest.skip("Safety reset returned no temp_password")
    r2 = requests.post(
        f"{URL}/api/safety/login",
        json={"email": "safety@mascigc.com", "password": temp_pw},
        timeout=10,
    )
    if r2.status_code != 200:
        pytest.skip(f"Safety bootstrap login failed (status={r2.status_code})")
    return r2.json()["token"]


@pytest.fixture
def leadership_token():
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
# Safety articles visibility
# ─────────────────────────────────────────────────────────────────────
def test_safety_token_sees_all_safety_portal_articles(safety_token):
    r = requests.get(
        f"{URL}/api/guidance/articles",
        headers={"X-Safety-Token": safety_token},
        timeout=10,
    )
    assert r.status_code == 200
    ids = {a["id"] for a in r.json()["articles"]}
    missing = SAFETY_PORTAL_IDS - ids
    assert not missing, f"Safety token should see all new Safety portal articles; missing {missing}"


def test_admin_sees_all_new_safety_articles(admin_token):
    r = requests.get(
        f"{URL}/api/guidance/articles",
        headers={"X-Admin-Token": admin_token},
        timeout=10,
    )
    ids = {a["id"] for a in r.json()["articles"]}
    assert (SAFETY_PORTAL_IDS | SAFETY_CROSS_IDS).issubset(ids)


def test_anon_does_not_see_any_safety_only_articles():
    r = requests.get(f"{URL}/api/guidance/articles", timeout=10)
    ids = {a["id"] for a in r.json()["articles"]}
    leaked = SAFETY_PORTAL_IDS & ids  # Strict safety-only set
    assert not leaked, f"Anon must not see safety-only articles; leaked {leaked}"
    # The cross-scope ones (near-miss / escalation-chain / photo-quality)
    # also do NOT include 'public' so anon must not see them either
    leaked_cross = SAFETY_CROSS_IDS & ids
    assert not leaked_cross, f"Anon must not see safety cross-scope articles; leaked {leaked_cross}"


@pytest.mark.parametrize("article_id", sorted(SAFETY_PORTAL_IDS))
def test_anon_single_safety_portal_404(article_id):
    r = requests.get(f"{URL}/api/guidance/articles/{article_id}", timeout=10)
    assert r.status_code == 404


@pytest.mark.parametrize("article_id", sorted(SAFETY_PORTAL_IDS))
def test_safety_single_article_200(article_id, safety_token):
    r = requests.get(
        f"{URL}/api/guidance/articles/{article_id}",
        headers={"X-Safety-Token": safety_token},
        timeout=10,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == article_id
    assert body.get("title")


# ─────────────────────────────────────────────────────────────────────
# Shop articles visibility
# ─────────────────────────────────────────────────────────────────────
def test_admin_sees_all_new_shop_articles(admin_token):
    r = requests.get(
        f"{URL}/api/guidance/articles",
        headers={"X-Admin-Token": admin_token},
        timeout=10,
    )
    ids = {a["id"] for a in r.json()["articles"]}
    assert (SHOP_PORTAL_IDS | SHOP_KNOWLEDGE_IDS).issubset(ids)


def test_anon_does_not_see_any_shop_only_articles():
    r = requests.get(f"{URL}/api/guidance/articles", timeout=10)
    ids = {a["id"] for a in r.json()["articles"]}
    leaked = SHOP_PORTAL_IDS & ids
    assert not leaked


@pytest.mark.parametrize("article_id", sorted(SHOP_PORTAL_IDS))
def test_anon_single_shop_portal_404(article_id):
    r = requests.get(f"{URL}/api/guidance/articles/{article_id}", timeout=10)
    assert r.status_code == 404


# ─────────────────────────────────────────────────────────────────────
# Cross-portal isolation: HR cannot see safety-only / shop-only
# ─────────────────────────────────────────────────────────────────────
def test_hr_token_does_NOT_see_safety_only_articles(hr_token):
    r = requests.get(
        f"{URL}/api/guidance/articles",
        headers={"X-HR-Token": hr_token},
        timeout=10,
    )
    ids = {a["id"] for a in r.json()["articles"]}
    leaked = SAFETY_PORTAL_IDS & ids
    assert not leaked, f"HR must not see safety-only articles; leaked {leaked}"


def test_hr_token_does_NOT_see_shop_only_articles(hr_token):
    r = requests.get(
        f"{URL}/api/guidance/articles",
        headers={"X-HR-Token": hr_token},
        timeout=10,
    )
    ids = {a["id"] for a in r.json()["articles"]}
    leaked = SHOP_PORTAL_IDS & ids
    assert not leaked, f"HR must not see shop-only articles; leaked {leaked}"


def test_safety_token_does_NOT_see_shop_only_articles(safety_token):
    r = requests.get(
        f"{URL}/api/guidance/articles",
        headers={"X-Safety-Token": safety_token},
        timeout=10,
    )
    ids = {a["id"] for a in r.json()["articles"]}
    leaked = SHOP_PORTAL_IDS & ids
    assert not leaked, f"Safety must not see shop-only articles; leaked {leaked}"


# ─────────────────────────────────────────────────────────────────────
# Cross-scope: safety-photo-quality should be visible to multiple portals
# ─────────────────────────────────────────────────────────────────────
def test_safety_photo_quality_visible_to_leadership(leadership_token):
    r = requests.get(
        f"{URL}/api/guidance/articles/safety-photo-quality",
        headers={"X-Leadership-Token": leadership_token},
        timeout=10,
    )
    assert r.status_code == 200


def test_safety_photo_quality_visible_to_hr_via_field_scope(hr_token):
    """`safety-photo-quality` scopes include `field` — and ALL authenticated
    users get the `field` scope by design (see guidance.content.caller_scopes).
    So HR can read this cross-portal photo-evidence guide. This is intentional:
    HR reviews photo-bearing records and benefits from the same standards."""
    r = requests.get(
        f"{URL}/api/guidance/articles/safety-photo-quality",
        headers={"X-HR-Token": hr_token},
        timeout=10,
    )
    assert r.status_code == 200


def test_near_miss_visible_to_field_leadership(leadership_token):
    r = requests.get(
        f"{URL}/api/guidance/articles/safety-near-miss-importance",
        headers={"X-Leadership-Token": leadership_token},
        timeout=10,
    )
    assert r.status_code == 200


# ─────────────────────────────────────────────────────────────────────
# Cross-workflow connection articles
# ─────────────────────────────────────────────────────────────────────
def test_connect_shop_to_dispatch_visible_to_leadership(leadership_token):
    r = requests.get(
        f"{URL}/api/guidance/articles/connect-shop-to-dispatch",
        headers={"X-Leadership-Token": leadership_token},
        timeout=10,
    )
    assert r.status_code == 200


def test_connect_equipment_lifecycle_visible_to_hr(hr_token):
    r = requests.get(
        f"{URL}/api/guidance/articles/connect-equipment-lifecycle",
        headers={"X-HR-Token": hr_token},
        timeout=10,
    )
    assert r.status_code == 200


def test_connect_equipment_lifecycle_NOT_visible_to_safety(safety_token):
    """Equipment lifecycle's scopes are [shop, dispatch, hr, leadership, admin]
    — Safety is intentionally NOT in scope (Safety touches incidents and audits,
    not asset accountability)."""
    r = requests.get(
        f"{URL}/api/guidance/articles/connect-equipment-lifecycle",
        headers={"X-Safety-Token": safety_token},
        timeout=10,
    )
    assert r.status_code == 404


def test_connect_articles_not_visible_to_anon():
    for art_id in NEW_CONNECTION_IDS:
        r = requests.get(f"{URL}/api/guidance/articles/{art_id}", timeout=10)
        assert r.status_code == 404, f"{art_id} leaked to anon"


# ─────────────────────────────────────────────────────────────────────
# Search — RBAC-aware on new content
# ─────────────────────────────────────────────────────────────────────
def test_search_extinguisher_hidden_from_anon():
    r = requests.get(f"{URL}/api/guidance/search?q=extinguisher", timeout=10)
    ids = {x["id"] for x in r.json()["results"]}
    assert "safety-fire-extinguishers" not in ids


def test_search_extinguisher_visible_to_safety(safety_token):
    r = requests.get(
        f"{URL}/api/guidance/search?q=extinguisher",
        headers={"X-Safety-Token": safety_token},
        timeout=10,
    )
    ids = {x["id"] for x in r.json()["results"]}
    assert "safety-fire-extinguishers" in ids


def test_search_failed_preop_hidden_from_anon():
    r = requests.get(f"{URL}/api/guidance/search?q=failed+pre-op", timeout=10)
    ids = {x["id"] for x in r.json()["results"]}
    assert "shop-failed-preop-workflow" not in ids


def test_search_failed_preop_visible_to_admin(admin_token):
    r = requests.get(
        f"{URL}/api/guidance/search?q=failed+pre-op",
        headers={"X-Admin-Token": admin_token},
        timeout=10,
    )
    ids = {x["id"] for x in r.json()["results"]}
    assert "shop-failed-preop-workflow" in ids


def test_search_near_miss_visible_to_leadership(leadership_token):
    r = requests.get(
        f"{URL}/api/guidance/search?q=near-miss",
        headers={"X-Leadership-Token": leadership_token},
        timeout=10,
    )
    ids = {x["id"] for x in r.json()["results"]}
    assert "safety-near-miss-importance" in ids


# ─────────────────────────────────────────────────────────────────────
# Section counts — verify portals + knowledge grew
# ─────────────────────────────────────────────────────────────────────
def test_admin_sections_counts_post_iter192(admin_token):
    r = requests.get(
        f"{URL}/api/guidance/sections",
        headers={"X-Admin-Token": admin_token},
        timeout=10,
    )
    sections = {s["id"]: s for s in r.json()["sections"]}
    # Portals gained 5 safety + 5 shop = +10 (now 14 → 24)
    assert sections["portals"]["count"] >= 24, f"portals count {sections['portals']['count']}"
    # Knowledge gained 3 safety + 2 shop + 2 connection = +7 (was 13 → 20)
    assert sections["knowledge"]["count"] >= 20, f"knowledge count {sections['knowledge']['count']}"


# ─────────────────────────────────────────────────────────────────────
# Related-link RBAC filtering
# ─────────────────────────────────────────────────────────────────────
def test_safety_incident_investigation_related_filtered(safety_token):
    r = requests.get(
        f"{URL}/api/guidance/articles/safety-incident-investigation",
        headers={"X-Safety-Token": safety_token},
        timeout=10,
    )
    assert r.status_code == 200
    related_ids = {x["id"] for x in r.json().get("related") or []}
    assert "safety-corrective-actions-workflow" in related_ids
    assert "safety-near-miss-importance" in related_ids
    assert "connect-incident-to-audit" in related_ids


def test_shop_failed_preop_related_filtered_admin(admin_token):
    r = requests.get(
        f"{URL}/api/guidance/articles/shop-failed-preop-workflow",
        headers={"X-Admin-Token": admin_token},
        timeout=10,
    )
    assert r.status_code == 200
    related_ids = {x["id"] for x in r.json().get("related") or []}
    assert "shop-preop-deep" in related_ids
    assert "connect-shop-to-dispatch" in related_ids
    assert "role-dispatch" in related_ids  # admin can see dispatch role


# ─────────────────────────────────────────────────────────────────────
# Content quality smoke (operator directive: HOW + WHY + WHAT-NEXT)
# ─────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("article_id", sorted(SAFETY_PORTAL_IDS | SHOP_PORTAL_IDS))
def test_major_portal_article_has_why_callout(article_id, admin_token):
    r = requests.get(
        f"{URL}/api/guidance/articles/{article_id}",
        headers={"X-Admin-Token": admin_token},
        timeout=10,
    )
    assert r.status_code == 200
    blocks = r.json().get("body") or []
    types = [b.get("type") for b in blocks if isinstance(b, dict)]
    assert "why" in types, f"{article_id} missing a WHY callout (operator-required)"


@pytest.mark.parametrize("article_id", sorted(SAFETY_PORTAL_IDS | SHOP_PORTAL_IDS))
def test_major_portal_article_has_next_or_mistakes(article_id, admin_token):
    """Every deep workflow article should explain what happens after the action
    (next) OR call out common mistakes (mistakes) — usually both."""
    r = requests.get(
        f"{URL}/api/guidance/articles/{article_id}",
        headers={"X-Admin-Token": admin_token},
        timeout=10,
    )
    blocks = r.json().get("body") or []
    types = [b.get("type") for b in blocks if isinstance(b, dict)]
    assert ("next" in types) or ("mistakes" in types), (
        f"{article_id} should explain consequences (next) or pitfalls (mistakes)"
    )
