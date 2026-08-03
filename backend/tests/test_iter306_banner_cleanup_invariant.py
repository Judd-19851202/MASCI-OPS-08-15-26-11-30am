"""
iter306 · Hub banner cleanup invariant lock.

Bounded operational-trust fix following the iter305 deploy gate:
the operator observed a stuck TEST heat-warning banner rendering on
preview after prior cleanup. Root cause: `test_hub_banners_iter65.py`
writes test banners against the live preview backend (`REACT_APP_BACKEND_URL`)
because there is no separate test database — and the cleanup fixture
silently swallowed exceptions, leaving 9 TEST_*-titled orphans in the
preview DB after an interrupted test run.

Real-world trust impact: crews conditioned to ignore banners because a
seeded TEST advisory survived prior cleanup. This is a HIGH operational-
trust hazard even though the underlying code change is tiny.

This test locks the invariant:

  1. The `cleanup_banners` fixture in `test_hub_banners_iter65.py` runs
     a TEST_-prefix sweep BEFORE yield (self-healing for prior-run leaks)
     AND AFTER yield (catches anything created mid-test that escaped the
     created_ids list).

  2. `GET /api/banners/active` returns an empty list (or at least no
     banner whose title starts with `TEST_`) when called against the
     live preview backend — proves the DB is operationally clean right
     now.

  3. No autonomous startup seeding of TEST banners exists in server.py
     (regression guard: future iterations must not introduce auto-seed
     of demo/test banners that would leak across environments).

Scope discipline (operator-bounded):
  - NO redesign of the banner system.
  - NO new endpoints.
  - NO new collections.
  - NO env-separation enforcement (separate test DB) — that's a future
    decision the operator can make explicitly. For now we rely on the
    self-healing TEST_-prefix sweep.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

import pytest
import requests

REPO_ROOT = Path(__file__).resolve().parents[2]
SERVER_PY = REPO_ROOT / "backend/server.py"
HUB_BANNERS_PY = REPO_ROOT / "backend/routes/hub_banners.py"
TEST_FIXTURE_FILE = REPO_ROOT / "backend/tests/test_hub_banners_iter65.py"

BASE_URL = os.environ.get(
    "REACT_APP_BACKEND_URL",
    "https://masci-audit-hub.preview.emergentagent.com",
).rstrip("/")


def test_iter306_no_test_banner_leaks_in_active_feed():
    """Live invariant: no TEST_-titled banner appears in /api/banners/active.

    Calling without a device_id returns the unfiltered active feed —
    any TEST_-titled banner showing here means orphan leak from a test
    run is currently rendering on every preview page load.
    """
    try:
        r = requests.get(f"{BASE_URL}/api/banners/active", timeout=15)
    except Exception as e:
        pytest.skip(f"preview backend unreachable: {e}")
    assert r.status_code == 200, f"/api/banners/active failed: {r.status_code} {r.text[:200]}"
    payload = r.json() or {}
    assert payload.get("ok") is True, f"ok flag missing: {payload}"
    leaked = [
        b for b in (payload.get("banners") or [])
        if (b.get("title_en") or "").startswith("TEST_")
        or (b.get("title_es") or "").startswith("TEST_")
        or (b.get("title_es") or "").startswith("PRUEBA_")
    ]
    assert not leaked, (
        f"OPERATIONAL-TRUST REGRESSION: {len(leaked)} TEST banner(s) leaked into "
        f"the live active feed and will render on every preview page load. "
        f"Leaked titles: {[b.get('title_en') for b in leaked]}"
    )


def test_iter306_pretest_sweep_present_in_fixture():
    """The cleanup_banners fixture must run a TEST_-prefix sweep BEFORE
    yield. Without this self-healing pass, any prior-run interrupt
    leaves orphan banners that render on the next preview session and
    condition crews to ignore real advisories."""
    text = TEST_FIXTURE_FILE.read_text()
    # Locate the cleanup fixture body — scan from the def line to the
    # next top-level definition (zero-indent `def ` or `class `).
    start = text.find("def cleanup_banners(")
    assert start > 0, "cleanup_banners fixture not found in test_hub_banners_iter65.py"
    rest = text[start:]
    # Find the next zero-indent top-level definition AFTER the fixture body.
    end_match = re.search(r"\n(?:def |class |@pytest)", rest[1:])
    body = rest if not end_match else rest[: end_match.start() + 1]
    # The sweep must reference the TEST_ prefix contract.
    assert 'TEST_' in body, (
        "cleanup_banners fixture missing TEST_-prefix sweep — orphan-leak protection lost"
    )
    # Sweep must run BEFORE yield (self-heal pass). Find the actual
    # `yield` STATEMENT (newline + indent + yield), not the word "yield"
    # inside the docstring.
    yield_match = re.search(r"\n    yield(\s|$)", body)
    assert yield_match, "cleanup_banners must contain a yield statement"
    yield_idx = yield_match.start()
    pre_yield = body[:yield_idx]
    assert "TEST_" in pre_yield or "_sweep_test_prefix" in pre_yield, (
        "cleanup_banners fixture must run a TEST_-prefix sweep BEFORE yield "
        "(self-healing pre-test pass). Found TEST_ only after yield, which "
        "means prior-run leaks persist into the new test run."
    )
    # Sweep must also run AFTER yield (post-test belt-and-suspenders).
    post_yield = body[yield_idx:]
    assert "TEST_" in post_yield or "_sweep_test_prefix" in post_yield, (
        "cleanup_banners fixture must also run a TEST_-prefix sweep AFTER yield "
        "to catch banners created but never appended to created_ids."
    )


def test_iter306_no_autonomous_banner_seeding_in_server():
    """Regression guard: server.py must not insert banners at startup
    or during request handling outside the explicit POST /admin/banners
    path. Any autonomous seed would re-create demo/test banners after
    cleanup and break the operational-trust invariant.
    """
    text = SERVER_PY.read_text()
    # The only legitimate use of hub_banners in server.py is the router
    # registration. No insert_one / insert_many / update_one targeting
    # the hub_banners collection should appear outside the routes module.
    BANNED_PATTERNS = [
        r'hub_banners.*insert_one',
        r'hub_banners.*insert_many',
        r'db\["hub_banners"\]\s*\.\s*insert',
        r"db\['hub_banners'\]\s*\.\s*insert",
        r'banners\.insert_one.*TEST_',
        r'banners\.insert_one.*Heat',
        r'banners\.insert_one.*Advisory',
    ]
    for pat in BANNED_PATTERNS:
        m = re.search(pat, text)
        assert m is None, (
            f"server.py contains autonomous banner seeding pattern {pat!r} at "
            f"position {m.start()}. Banners must only be created via explicit "
            f"admin POST — any startup seed leaks across environments."
        )


def test_iter306_router_module_has_no_demo_seed():
    """Same guard, applied to the router module. The only allowed
    insert_one calls are inside the `create_banner` and `clone_banner`
    handler bodies (both gated by admin auth)."""
    text = HUB_BANNERS_PY.read_text()
    # Count insert_one calls — must be exactly 2 (create + clone).
    inserts = re.findall(r'banners\.insert_one\(', text)
    assert len(inserts) == 2, (
        f"hub_banners.py has {len(inserts)} banners.insert_one calls; expected "
        f"exactly 2 (admin create + admin clone). Extra inserts may be "
        f"autonomous seeds — verify before deploy."
    )
    # No `TEST_`-prefixed string literals in the router (defense-in-depth
    # against accidentally hardcoding a seeded TEST advisory).
    assert "TEST_" not in text, (
        "hub_banners.py contains a TEST_ literal — possible seeded demo banner."
    )


def test_iter306_banner_expiration_filter_lives_in_active_feed():
    """Defensive lock on the existing expiration filter. The /banners/
    active endpoint must continue to exclude banners with `expires_at`
    in the past — operational-trust depends on expired alerts truly
    disappearing.
    """
    text = HUB_BANNERS_PY.read_text()
    # Find the /banners/active handler body.
    m = re.search(
        r'@router\.get\("/banners/active"\)(.*?)(?=@router\.|def build_)',
        text,
        re.DOTALL,
    )
    assert m, "/banners/active handler not found in hub_banners.py"
    body = m.group(1)
    assert "expires_at" in body, (
        "/banners/active handler missing expires_at filter — expired banners "
        "would render forever, conditioning crews to ignore real alerts."
    )
    # Verify the comparison "exp_dt < now" remains the guard.
    assert "exp_dt < now" in body, (
        "/banners/active expiration comparison drifted from `exp_dt < now`. "
        "Verify expired banners are still excluded from the active feed."
    )
