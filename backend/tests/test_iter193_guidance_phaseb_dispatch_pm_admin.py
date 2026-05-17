"""iter193 — Operational Guidance · Phase B Iteration 3
(Dispatch + PM + Admin saturation + governance infrastructure, preview only).

Backend coverage:
  • New Dispatch articles visible to Dispatch + Admin; not anon/other portals
  • New PM articles visible to PM + Admin; not anon/other portals
  • New Admin articles visible only to Admin
  • Cross-workflow connection articles respect multi-scope grants
  • portal-dispatch / portal-pm now exist (operator-required coverage)
  • Coverage Dashboard (/api/admin/guidance/coverage) — admin-only, returns
    structural per-portal × per-section matrix
  • Search-zero-results logging — captures query + ts + scope, no PII
  • /api/admin/guidance/search-misses — admin-only aggregated demand signal
"""
from __future__ import annotations

import os
import sys
import time
import uuid
from pathlib import Path

import pytest
import requests

sys.path.insert(0, "/app/backend")

URL = os.environ.get("PUBLIC_BACKEND_URL") or "http://localhost:8001"

# Strictly dispatch-scoped (["dispatch", "admin"]) — in portals section
DISPATCH_PORTAL_IDS = {
    "portal-dispatch",
    "dispatch-equipment-movement",
    "dispatch-availability-management",
    "dispatch-holds-transfers",
}
DISPATCH_KNOWLEDGE_IDS = {
    "dispatch-field-coordination",     # dispatch, leadership, pm, admin
    "dispatch-accuracy-why",           # dispatch, shop, leadership, pm, admin
}
PM_PORTAL_IDS = {
    "portal-pm",
    "pm-project-review-cadence",
    "pm-labor-documentation",
    "pm-reporting-workflows",
}
PM_KNOWLEDGE_IDS = {
    "pm-cross-project-visibility",  # pm, admin
    "pm-coordination",              # pm, admin
}
ADMIN_PORTAL_IDS = {
    "admin-user-management",
    "admin-audit-forensics",
    "admin-system-health",
    "admin-backup-restore",
    "admin-data-portability",
    "admin-sentry-observability",
    "admin-role-templates",
}
ADMIN_KNOWLEDGE_IDS = {
    "admin-governance-why",  # admin
}
NEW_CONNECTION_IDS = {
    "connect-pm-field-review",   # field, leadership, pm, admin
    "connect-admin-controls",    # admin
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


@pytest.fixture
def dispatch_token(admin_token):
    """Login as the seeded dispatch user. Self-bootstrap via admin reset if
    the stored credential is stale (mirrors iter179 pattern)."""
    r = requests.post(
        f"{URL}/api/dispatch/login",
        json={"email": "dispatch@mascigc.com", "password": "DispatchTest2026!"},
        timeout=10,
    )
    if r.status_code == 200:
        return r.json()["token"]
    users = requests.get(
        f"{URL}/api/admin/dispatch-users",
        headers={"X-Admin-Token": admin_token},
        timeout=10,
    ).json()
    users = users if isinstance(users, list) else users.get("items", [])
    target = next((u for u in users if u.get("email") == "dispatch@mascigc.com"), None)
    if not target:
        pytest.skip("Dispatch seed user not present")
    rp = requests.post(
        f"{URL}/api/admin/dispatch-users/{target['id']}/reset-password",
        json={},
        headers={"X-Admin-Token": admin_token},
        timeout=10,
    )
    if rp.status_code != 200:
        pytest.skip(f"Dispatch password reset failed (status={rp.status_code})")
    temp_pw = rp.json().get("temp_password")
    if not temp_pw:
        pytest.skip("Dispatch reset returned no temp_password")
    r2 = requests.post(
        f"{URL}/api/dispatch/login",
        json={"email": "dispatch@mascigc.com", "password": temp_pw},
        timeout=10,
    )
    if r2.status_code != 200:
        pytest.skip(f"Dispatch bootstrap login failed (status={r2.status_code})")
    return r2.json()["token"]


@pytest.fixture
def pm_token():
    """Login as the seeded per-PM user (Chris Wright)."""
    r = requests.post(
        f"{URL}/api/pm/login",
        json={"email": "chriswright@mascigc.com", "password": "ChrisRocksThis2026"},
        timeout=10,
    )
    if r.status_code != 200:
        pytest.skip(f"PM seed login unavailable (status={r.status_code})")
    return r.json()["token"]


# ─────────────────────────────────────────────────────────────────────
# Dispatch articles
# ─────────────────────────────────────────────────────────────────────
def test_admin_sees_all_dispatch_articles(admin_token):
    r = requests.get(
        f"{URL}/api/guidance/articles",
        headers={"X-Admin-Token": admin_token},
        timeout=10,
    )
    ids = {a["id"] for a in r.json()["articles"]}
    assert (DISPATCH_PORTAL_IDS | DISPATCH_KNOWLEDGE_IDS).issubset(ids)


def test_dispatch_token_sees_dispatch_articles(dispatch_token):
    r = requests.get(
        f"{URL}/api/guidance/articles",
        headers={"X-Dispatch-Token": dispatch_token},
        timeout=10,
    )
    assert r.status_code == 200
    ids = {a["id"] for a in r.json()["articles"]}
    missing = DISPATCH_PORTAL_IDS - ids
    assert not missing, f"Dispatch token should see all new dispatch articles; missing {missing}"


def test_anon_does_not_see_dispatch_only_articles():
    r = requests.get(f"{URL}/api/guidance/articles", timeout=10)
    ids = {a["id"] for a in r.json()["articles"]}
    leaked = DISPATCH_PORTAL_IDS & ids
    assert not leaked


@pytest.mark.parametrize("article_id", sorted(DISPATCH_PORTAL_IDS))
def test_anon_single_dispatch_404(article_id):
    r = requests.get(f"{URL}/api/guidance/articles/{article_id}", timeout=10)
    assert r.status_code == 404


# ─────────────────────────────────────────────────────────────────────
# PM articles
# ─────────────────────────────────────────────────────────────────────
def test_admin_sees_all_pm_articles(admin_token):
    r = requests.get(
        f"{URL}/api/guidance/articles",
        headers={"X-Admin-Token": admin_token},
        timeout=10,
    )
    ids = {a["id"] for a in r.json()["articles"]}
    assert (PM_PORTAL_IDS | PM_KNOWLEDGE_IDS).issubset(ids)


def test_pm_token_sees_pm_articles(pm_token):
    r = requests.get(
        f"{URL}/api/guidance/articles",
        headers={"X-PM-Token": pm_token},
        timeout=10,
    )
    assert r.status_code == 200
    ids = {a["id"] for a in r.json()["articles"]}
    missing = PM_PORTAL_IDS - ids
    assert not missing


def test_anon_does_not_see_pm_only_articles():
    r = requests.get(f"{URL}/api/guidance/articles", timeout=10)
    ids = {a["id"] for a in r.json()["articles"]}
    leaked = PM_PORTAL_IDS & ids
    assert not leaked


# ─────────────────────────────────────────────────────────────────────
# Admin articles
# ─────────────────────────────────────────────────────────────────────
def test_admin_sees_all_admin_articles(admin_token):
    r = requests.get(
        f"{URL}/api/guidance/articles",
        headers={"X-Admin-Token": admin_token},
        timeout=10,
    )
    ids = {a["id"] for a in r.json()["articles"]}
    assert (ADMIN_PORTAL_IDS | ADMIN_KNOWLEDGE_IDS).issubset(ids)


def test_anon_does_not_see_admin_articles():
    r = requests.get(f"{URL}/api/guidance/articles", timeout=10)
    ids = {a["id"] for a in r.json()["articles"]}
    leaked = (ADMIN_PORTAL_IDS | ADMIN_KNOWLEDGE_IDS) & ids
    assert not leaked, f"Anon must not see admin articles; leaked {leaked}"


def test_hr_does_not_see_admin_articles(hr_token):
    r = requests.get(
        f"{URL}/api/guidance/articles",
        headers={"X-HR-Token": hr_token},
        timeout=10,
    )
    ids = {a["id"] for a in r.json()["articles"]}
    leaked = (ADMIN_PORTAL_IDS | ADMIN_KNOWLEDGE_IDS) & ids
    assert not leaked, f"HR must not see admin articles; leaked {leaked}"


@pytest.mark.parametrize("article_id", sorted(ADMIN_PORTAL_IDS))
def test_anon_single_admin_article_404(article_id):
    r = requests.get(f"{URL}/api/guidance/articles/{article_id}", timeout=10)
    assert r.status_code == 404


# ─────────────────────────────────────────────────────────────────────
# Cross-workflow connection articles
# ─────────────────────────────────────────────────────────────────────
def test_connect_pm_field_review_visible_to_leadership(leadership_token):
    """connect-pm-field-review scopes: field, leadership, pm, admin."""
    r = requests.get(
        f"{URL}/api/guidance/articles/connect-pm-field-review",
        headers={"X-Leadership-Token": leadership_token},
        timeout=10,
    )
    assert r.status_code == 200


def test_connect_admin_controls_admin_only(admin_token, hr_token):
    """connect-admin-controls scoped admin-only."""
    r1 = requests.get(
        f"{URL}/api/guidance/articles/connect-admin-controls",
        headers={"X-Admin-Token": admin_token},
        timeout=10,
    )
    assert r1.status_code == 200
    r2 = requests.get(
        f"{URL}/api/guidance/articles/connect-admin-controls",
        headers={"X-HR-Token": hr_token},
        timeout=10,
    )
    assert r2.status_code == 404


# ─────────────────────────────────────────────────────────────────────
# Coverage Dashboard (governance endpoint)
# ─────────────────────────────────────────────────────────────────────
def test_coverage_dashboard_admin_only_anon_401():
    r = requests.get(f"{URL}/api/admin/guidance/coverage", timeout=10)
    assert r.status_code == 401


def test_coverage_dashboard_admin_only_hr_blocked(hr_token):
    """Admin-strict endpoint must reject HR tokens."""
    r = requests.get(
        f"{URL}/api/admin/guidance/coverage",
        headers={"X-HR-Token": hr_token},
        timeout=10,
    )
    assert r.status_code in (401, 403)


def test_coverage_dashboard_returns_all_seven_portals(admin_token):
    r = requests.get(
        f"{URL}/api/admin/guidance/coverage",
        headers={"X-Admin-Token": admin_token},
        timeout=10,
    )
    assert r.status_code == 200
    data = r.json()
    assert "portals" in data
    assert "totals" in data
    assert "article_count" in data
    portal_ids = {p["portal"] for p in data["portals"]}
    assert {"hr", "safety", "shop", "dispatch", "pm", "leadership", "admin"}.issubset(portal_ids)


def test_coverage_dashboard_marks_all_portals_mature(admin_token):
    """Post-iter193, every portal should have at least one article in
    each required section (roles, portals, troubleshooting, knowledge)."""
    r = requests.get(
        f"{URL}/api/admin/guidance/coverage",
        headers={"X-Admin-Token": admin_token},
        timeout=10,
    )
    data = r.json()
    not_mature = [p for p in data["portals"] if not p.get("mature")]
    assert not not_mature, f"Portals missing required-section coverage: {not_mature}"


def test_coverage_dashboard_article_count_reflects_growth(admin_token):
    r = requests.get(
        f"{URL}/api/admin/guidance/coverage",
        headers={"X-Admin-Token": admin_token},
        timeout=10,
    )
    data = r.json()
    # Phase A=31, iter191=+15 → 46, iter192=+17 → 63, iter193=+22 → 85
    assert data["article_count"] >= 85, f"article_count={data['article_count']}"


# ─────────────────────────────────────────────────────────────────────
# Search-zero-results logging (governance endpoint)
# ─────────────────────────────────────────────────────────────────────
def test_search_miss_is_logged_and_visible_to_admin(admin_token):
    """A unique zero-result query must (a) return 0 results and
    (b) surface in /api/admin/guidance/search-misses."""
    unique_term = f"zzz_iter193_{uuid.uuid4().hex[:12]}"
    r = requests.get(f"{URL}/api/guidance/search?q={unique_term}", timeout=10)
    assert r.status_code == 200
    assert r.json()["results"] == []
    time.sleep(0.5)  # let the fire-and-forget insert land
    r2 = requests.get(
        f"{URL}/api/admin/guidance/search-misses?limit=200",
        headers={"X-Admin-Token": admin_token},
        timeout=10,
    )
    assert r2.status_code == 200
    queries = [row.get("query") for row in r2.json().get("recent", [])]
    assert unique_term in queries, f"miss for '{unique_term}' was not logged"


def test_search_HIT_does_NOT_log_miss(admin_token):
    """A query that returns results must NOT create a miss row."""
    unique_term = f"hit_iter193_{uuid.uuid4().hex[:12]}"
    # 'session' is a public-visible match, so this should return results
    r = requests.get(f"{URL}/api/guidance/search?q=session", timeout=10)
    assert r.status_code == 200
    assert len(r.json()["results"]) > 0
    time.sleep(0.3)
    r2 = requests.get(
        f"{URL}/api/admin/guidance/search-misses?limit=200",
        headers={"X-Admin-Token": admin_token},
        timeout=10,
    )
    queries = [row.get("query") for row in r2.json().get("recent", [])]
    # 'session' should not appear because it had results
    assert "session" not in queries


def test_search_misses_admin_only_anon_401():
    r = requests.get(f"{URL}/api/admin/guidance/search-misses", timeout=10)
    assert r.status_code == 401


def test_search_misses_top_aggregation(admin_token):
    """Repeated misses for the same query should aggregate in the `top` list."""
    term = f"agg_iter193_{uuid.uuid4().hex[:8]}"
    for _ in range(3):
        requests.get(f"{URL}/api/guidance/search?q={term}", timeout=10)
    time.sleep(0.5)
    r = requests.get(
        f"{URL}/api/admin/guidance/search-misses?limit=500",
        headers={"X-Admin-Token": admin_token},
        timeout=10,
    )
    top = r.json().get("top", [])
    matching = [t for t in top if t["query"] == term]
    assert matching and matching[0]["count"] >= 3


def test_search_miss_no_pii_logged(admin_token):
    """Miss rows must contain only query / ts / scopes — no IP, no actor."""
    term = f"pii_check_{uuid.uuid4().hex[:8]}"
    requests.get(f"{URL}/api/guidance/search?q={term}", timeout=10)
    time.sleep(0.3)
    r = requests.get(
        f"{URL}/api/admin/guidance/search-misses?limit=200",
        headers={"X-Admin-Token": admin_token},
        timeout=10,
    )
    row = next((x for x in r.json()["recent"] if x.get("query") == term), None)
    assert row, "miss row not found"
    allowed_keys = {"query", "ts", "scopes"}
    extra = set(row.keys()) - allowed_keys
    assert not extra, f"Miss row contains unexpected keys: {extra}"


# ─────────────────────────────────────────────────────────────────────
# Section totals
# ─────────────────────────────────────────────────────────────────────
def test_admin_sections_counts_post_iter193(admin_token):
    r = requests.get(
        f"{URL}/api/guidance/sections",
        headers={"X-Admin-Token": admin_token},
        timeout=10,
    )
    sections = {s["id"]: s for s in r.json()["sections"]}
    # Portals gained: 4 dispatch + 4 pm + 7 admin = +15 (was ≥24, now ≥39)
    assert sections["portals"]["count"] >= 39, f"portals count {sections['portals']['count']}"
    # Knowledge gained: 2 dispatch + 2 pm + 1 admin + 2 connect = +7 (was ≥20, now ≥27)
    assert sections["knowledge"]["count"] >= 27, f"knowledge count {sections['knowledge']['count']}"


# ─────────────────────────────────────────────────────────────────────
# Content quality smoke
# ─────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("article_id", sorted(
    DISPATCH_PORTAL_IDS | PM_PORTAL_IDS | ADMIN_PORTAL_IDS - {"portal-dispatch", "portal-pm"}
))
def test_major_iter193_article_has_why_callout(article_id, admin_token):
    """Every deep iter193 article (excluding the lightweight quick-starts)
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
