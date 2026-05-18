"""iter195 — Operational Guidance unification + RBAC lockdown.

After operator review identified four critical issues:
  1. "Hub" terminology must be removed from guidance/training surfaces
  2. Safety + Dispatch must be visually first-class portal tracks
  3. /api/training-center/* was unrestricted (RBAC failure) — must inherit
     the same portal-access boundaries as /api/guidance/*
  4. /ops-training frontend was an unrestricted side door — must redirect
     into the unified Operational Guidance Center

Backend coverage:
  • /api/training-center/portals filtered by caller scopes (anon = 0 portals)
  • /api/training-center/guides?portal=X with portal user can't see → 403
  • /api/training-center/guide/{slug} on out-of-scope portal → 404 (no leak)
  • /api/training-center/guide/{slug}/pdf on out-of-scope portal → 404
  • Admin sees everything (cross-portal)
  • HR can see HR guides but NOT safety/shop/dispatch/integration
  • Safety can see Safety guides but NOT HR/admin guides
  • Content registry validation: validate_registry() detects malformed
    articles without crashing the import (the actual runtime guarantee
    that earlier operator concern called out).
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
def safety_token(admin_token):
    r = requests.post(
        f"{URL}/api/safety/login",
        json={"email": "safety@mascigc.com", "password": "SafetyTest2026!"},
        timeout=10,
    )
    if r.status_code == 200:
        return r.json()["token"]
    # Self-bootstrap via admin reset (mirrors iter192 pattern)
    users = requests.get(
        f"{URL}/api/admin/safety-users",
        headers={"X-Admin-Token": admin_token},
        timeout=10,
    ).json()
    users = users if isinstance(users, list) else users.get("items", [])
    target = next((u for u in users if u.get("email") == "safety@mascigc.com"), None)
    if not target:
        pytest.skip("Safety seed user not present")
    rp = requests.post(
        f"{URL}/api/admin/safety-users/{target['id']}/reset-password",
        json={},
        headers={"X-Admin-Token": admin_token},
        timeout=10,
    )
    if rp.status_code != 200:
        pytest.skip(f"Safety password reset failed ({rp.status_code})")
    temp_pw = rp.json().get("temp_password")
    if not temp_pw:
        pytest.skip("Safety reset returned no temp_password")
    r2 = requests.post(
        f"{URL}/api/safety/login",
        json={"email": "safety@mascigc.com", "password": temp_pw},
        timeout=10,
    )
    if r2.status_code != 200:
        pytest.skip(f"Safety bootstrap login failed ({r2.status_code})")
    return r2.json()["token"]


# ─────────────────────────────────────────────────────────────────────
# Training-Center RBAC lockdown — anonymous callers
# ─────────────────────────────────────────────────────────────────────
def test_anon_training_center_portals_is_empty():
    """Iter195: anon callers must see zero portals — the entire training-
    center used to be 'public-read'. That side door is now closed."""
    r = requests.get(f"{URL}/api/training-center/portals", timeout=10)
    assert r.status_code == 200
    assert r.json()["portals"] == [], "Anon must see zero training-center portals"


def test_anon_training_center_guides_unfiltered_is_empty():
    """Even without a portal filter, anon must get zero guides (entries
    are gated by their portal scope, not by the absence of a filter)."""
    r = requests.get(f"{URL}/api/training-center/guides", timeout=10)
    assert r.status_code == 200
    assert r.json()["guides"] == []
    assert r.json()["total"] == 0


def test_anon_training_center_guides_with_portal_filter_403():
    """Explicit ?portal=safety from anon must HARD 403 — never silently
    return an empty list, which would mask the RBAC failure."""
    for portal in ("safety", "hr", "dispatch", "shop", "pm", "admin", "integration", "reliability"):
        r = requests.get(
            f"{URL}/api/training-center/guides?portal={portal}",
            timeout=10,
        )
        assert r.status_code == 403, (
            f"Anon ?portal={portal} returned {r.status_code} (must be 403)"
        )


# ─────────────────────────────────────────────────────────────────────
# Cross-portal isolation — HR / Safety can only see their own portal
# ─────────────────────────────────────────────────────────────────────
def test_hr_sees_only_hr_training_center_portals(hr_token):
    r = requests.get(
        f"{URL}/api/training-center/portals",
        headers={"X-HR-Token": hr_token},
        timeout=10,
    )
    keys = {p["key"] for p in r.json()["portals"]}
    assert keys == {"hr"}, f"HR caller saw portals {keys} (expected just hr)"


def test_hr_blocked_from_safety_guides(hr_token):
    r = requests.get(
        f"{URL}/api/training-center/guides?portal=safety",
        headers={"X-HR-Token": hr_token},
        timeout=10,
    )
    assert r.status_code == 403


def test_hr_blocked_from_dispatch_guides(hr_token):
    r = requests.get(
        f"{URL}/api/training-center/guides?portal=dispatch",
        headers={"X-HR-Token": hr_token},
        timeout=10,
    )
    assert r.status_code == 403


def test_hr_blocked_from_admin_guides(hr_token):
    r = requests.get(
        f"{URL}/api/training-center/guides?portal=admin",
        headers={"X-HR-Token": hr_token},
        timeout=10,
    )
    assert r.status_code == 403


def test_hr_blocked_from_integration_guides(hr_token):
    """Integration + reliability guides are admin-only — HR cannot see them."""
    r = requests.get(
        f"{URL}/api/training-center/guides?portal=integration",
        headers={"X-HR-Token": hr_token},
        timeout=10,
    )
    assert r.status_code == 403


def test_safety_sees_only_safety_training_center_portals(safety_token):
    r = requests.get(
        f"{URL}/api/training-center/portals",
        headers={"X-Safety-Token": safety_token},
        timeout=10,
    )
    keys = {p["key"] for p in r.json()["portals"]}
    assert keys == {"safety"}, f"Safety caller saw portals {keys}"


def test_safety_blocked_from_hr_guides(safety_token):
    r = requests.get(
        f"{URL}/api/training-center/guides?portal=hr",
        headers={"X-Safety-Token": safety_token},
        timeout=10,
    )
    assert r.status_code == 403


# ─────────────────────────────────────────────────────────────────────
# Admin sees everything (cross-portal expected)
# ─────────────────────────────────────────────────────────────────────
def test_admin_sees_all_training_center_portals(admin_token):
    r = requests.get(
        f"{URL}/api/training-center/portals",
        headers={"X-Admin-Token": admin_token},
        timeout=10,
    )
    keys = {p["key"] for p in r.json()["portals"]}
    # All 9 portals should be visible to admin
    assert keys >= {"admin", "safety", "hr", "dispatch", "shop", "pm"}


def test_admin_can_filter_any_portal(admin_token):
    for portal in ("safety", "hr", "dispatch", "admin", "integration", "reliability"):
        r = requests.get(
            f"{URL}/api/training-center/guides?portal={portal}",
            headers={"X-Admin-Token": admin_token},
            timeout=10,
        )
        assert r.status_code == 200, f"Admin ?portal={portal} got {r.status_code}"


# ─────────────────────────────────────────────────────────────────────
# Direct deep-link RBAC — never leak titles via 404
# ─────────────────────────────────────────────────────────────────────
def test_anon_direct_guide_returns_404_not_403(admin_token):
    """Iter195: anon callers hitting a real safety guide slug must get
    404 (Guide not found) — NOT 403 (which would confirm the slug exists)
    and NOT 200 (the previous broken behaviour)."""
    # Pick a real slug from the admin's guide list
    r = requests.get(
        f"{URL}/api/training-center/guides?portal=safety",
        headers={"X-Admin-Token": admin_token},
        timeout=10,
    )
    guides = r.json().get("guides", [])
    if not guides:
        pytest.skip("No safety guides seeded yet — cannot validate leak protection")
    slug = guides[0]["slug"]
    # Anon hits the same slug
    r2 = requests.get(f"{URL}/api/training-center/guide/{slug}", timeout=10)
    assert r2.status_code == 404, (
        f"Anon direct-link to safety slug returned {r2.status_code} (must be 404 to avoid title leak)"
    )


def test_hr_cannot_deep_link_into_safety_guide(admin_token, hr_token):
    r = requests.get(
        f"{URL}/api/training-center/guides?portal=safety",
        headers={"X-Admin-Token": admin_token},
        timeout=10,
    )
    guides = r.json().get("guides", [])
    if not guides:
        pytest.skip("No safety guides seeded yet")
    slug = guides[0]["slug"]
    r2 = requests.get(
        f"{URL}/api/training-center/guide/{slug}",
        headers={"X-HR-Token": hr_token},
        timeout=10,
    )
    assert r2.status_code == 404


def test_anon_pdf_download_blocked(admin_token):
    """PDF downloads of restricted-portal guides must 404 for unauthorized callers."""
    r = requests.get(
        f"{URL}/api/training-center/guides?portal=safety",
        headers={"X-Admin-Token": admin_token},
        timeout=10,
    )
    guides = r.json().get("guides", [])
    if not guides:
        pytest.skip("No safety guides seeded yet")
    slug = guides[0]["slug"]
    r2 = requests.get(f"{URL}/api/training-center/guide/{slug}/pdf", timeout=10)
    # Must be 404 (no leak) — never 200
    assert r2.status_code in (404, 401), (
        f"Anon PDF download returned {r2.status_code} (must not be 200)"
    )


# ─────────────────────────────────────────────────────────────────────
# Frontend route — /ops-training has been retired into /guidance
# ─────────────────────────────────────────────────────────────────────
def test_app_js_ops_training_redirects_to_guidance():
    """Source-level guardrail: /ops-training must be a redirect to
    /guidance, NEVER mount OpsTrainingCenter again."""
    src = Path("/app/frontend/src/App.js").read_text()
    assert 'path="/ops-training"' in src, "ops-training route must remain (as redirect)"
    # Must redirect to /guidance, not mount the legacy component
    assert "OpsTrainingCenter" not in src, (
        "OpsTrainingCenter must no longer be imported/mounted (iter195 retirement)"
    )
    assert 'Navigate to="/guidance" replace' in src, (
        "ops-training must redirect to /guidance"
    )


def test_no_portal_hub_links_to_ops_training():
    """No portal hub should still link to the old /ops-training surface.
    These are the side doors operator called out — verifying at source level."""
    bad_links = []
    for stem in (
        "DispatchHub.jsx", "ShopHub.jsx", "HrHub.jsx", "SafetyHub.jsx",
        "PmHub.jsx", "FieldLeadershipHub.jsx",
    ):
        p = Path(f"/app/frontend/src/pages/{stem}")
        if p.exists() and '"/ops-training' in p.read_text():
            bad_links.append(stem)
    assert not bad_links, (
        f"These portal hubs still link to retired /ops-training: {bad_links}"
    )


def test_admin_shell_links_to_guidance_not_ops_training():
    src = Path("/app/frontend/src/components/AdminShell.jsx").read_text()
    assert '"/ops-training"' not in src
    assert '"/guidance"' in src


# ─────────────────────────────────────────────────────────────────────
# Frontend wording — "Training Hub" terminology cleanup
# ─────────────────────────────────────────────────────────────────────
def test_guidance_center_does_not_use_hub_terminology():
    """The Operational Guidance Center must not refer to itself as a
    'hub' in user-visible text (operator directive)."""
    src = Path("/app/frontend/src/pages/guidance/OperationalGuidanceCenter.jsx").read_text()
    # Allowable: comments referencing the legacy /training (which IS still
    # called TrainingHub at the route level). Forbidden: visible labels
    # that call THIS surface a "hub".
    forbidden_visible = [
        "data-testid=\"guidance-hub-header\"",
        "data-testid=\"guidance-hub-empty\"",
        "data-testid=\"guidance-back-to-hub\"",
        ">Training Hub<",
        ">Ops Training Center<",
        "legacy-ops-training-link",
    ]
    leaks = [f for f in forbidden_visible if f in src]
    assert not leaks, f"Operational Guidance Center still contains 'hub' wording: {leaks}"


# ─────────────────────────────────────────────────────────────────────
# Content registry validation safety net
# ─────────────────────────────────────────────────────────────────────
def test_registry_validation_passes():
    """The registry must pass its own integrity check at all times."""
    from guidance.content import validate_registry
    issues = validate_registry(strict=False)
    assert issues == [], f"guidance registry has integrity issues: {issues}"


def test_registry_validation_catches_malformed_article(monkeypatch):
    """Defensive: a deliberately bad article must surface a clear issue."""
    from guidance import content
    bad = {
        "id": "fuzz-bad-article",
        "section": "no-such-section",  # invalid
        "title": "Bad",
        "summary": "",
        "scopes": [],  # invalid (empty)
        "body": "not a list",  # invalid type
    }
    monkeypatch.setattr(content, "_ARTICLES", content._ARTICLES + [bad])
    issues = content.validate_registry(strict=False)
    joined = "\n".join(issues)
    assert "fuzz-bad-article" in joined
    assert "section" in joined.lower() or "scopes" in joined.lower() or "body" in joined.lower()
