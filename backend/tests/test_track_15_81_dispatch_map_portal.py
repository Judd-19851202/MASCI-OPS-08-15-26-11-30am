"""TRACK 15.81 · Dispatch Map Portal Access Failure — regression lock.

Production failure mode
-----------------------
A Super Admin (or pure Dispatcher) signed into ``/dispatch-portal``
clicked an action on the Live Fleet Map and was bounced to
``/operations-map`` — a route wrapped in ``RequireAdmin``. Without an
admin token in scope, the ``AccessDenied`` page rendered a misleading
"403 · Access Restricted · You don't have access to Admin Console"
even though every backend ``/api/operations-map/*`` endpoint already
accepts ``X-Dispatch-Token`` via
``make_require_any_portal_token``.

Six-pillar fix (Phase 4 — Preferred Fix A "Correct the Dispatch Link")
----------------------------------------------------------------------
1. A new Dispatch-owned route ``/dispatch-portal/map`` was added in
   ``App.js``, gated by ``RequireDispatch``, rendering the SAME
   ``OperationsMapPage`` component.
2. Every Dispatch-portal-rendered link that previously targeted
   ``/operations-map`` now targets ``/dispatch-portal/map``:
     * ``DispatchMapHero.jsx`` — asset click, count tiles, Open Full
       Live Map CTA.
     * ``DispatchLiveSnapshot.jsx`` — empty-state link, tile clicks,
       Open Full Live Map CTA.
3. The Admin Console route ``/operations-map`` itself is UNCHANGED —
   still wrapped by ``RequireAdmin``. Admin Console RBAC is NOT
   weakened by this fix.

This regression test enforces all three properties so the bug can
never silently come back.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

import pytest
import requests
from dotenv import dotenv_values

FRONTEND_SRC = Path("/app/frontend/src")
APP_JS = FRONTEND_SRC / "App.js"
# TRACK 22.5A · re-anchor to current routing shell.
APP_ROUTES = FRONTEND_SRC / "app" / "routing" / "AppRoutes.jsx"
DISPATCH_HERO = FRONTEND_SRC / "components/DispatchMapHero.jsx"
DISPATCH_SNAPSHOT = FRONTEND_SRC / "components/DispatchLiveSnapshot.jsx"

FRONTEND_ENV = dotenv_values("/app/frontend/.env")
BASE = (FRONTEND_ENV.get("REACT_APP_BACKEND_URL") or "").rstrip("/")

SUPER_ADMIN_EMAIL = "jaymn.judd@mascigc.com"
SUPER_ADMIN_PASSWORD = "Maddix123!"


# ─── Frontend static guards ───────────────────────────────────────


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_dispatch_portal_owned_map_route_exists():
    """``/dispatch-portal/map`` MUST be registered under the Dispatch
    guard (``DP(...)``) so Dispatch tokens can reach the live map page
    without bouncing through ``RequireAdmin``.

    Track 15.82 update: the route now renders ``DispatchOperationsMapPage``
    (a thin Dispatch-themed wrapper around the same ``OperationsMapPage``
    canvas). Both forms satisfy this regression.
    """
    src = (_read(APP_JS) + "\n" + _read(APP_ROUTES))
    pattern = re.compile(
        r'<Route\s+path="/dispatch-portal/map"\s+element=\{DP\('
        r'<(?:OperationsMapPage|DispatchOperationsMapPage)\s*/>\)\}'
    )
    assert pattern.search(src), (
        "Track 15.81/15.82 regression: `<Route path=\"/dispatch-portal/map\" "
        "element={DP(<DispatchOperationsMapPage />)} />` (or the legacy "
        "OperationsMapPage form) is missing from App.js. "
        "Dispatch users will hit 403 again on map clicks."
    )


def test_admin_operations_map_route_still_admin_only():
    """The legacy Admin Console route ``/operations-map`` MUST remain
    wrapped by ``RequireAdmin`` (``A(...)``). The fix does NOT widen
    Admin Console access."""
    src = (_read(APP_JS) + "\n" + _read(APP_ROUTES))
    pattern = re.compile(
        r'<Route\s+path="/operations-map"\s+element=\{A\(<OperationsMapPage\s*/>\)\}'
    )
    assert pattern.search(src), (
        "Track 15.81 regression: `<Route path=\"/operations-map\" "
        "element={A(<OperationsMapPage />)} />` must stay admin-only. "
        "Do NOT weaken Admin Console RBAC."
    )


def test_dispatch_map_hero_has_no_admin_console_links():
    """No link rendered inside the Dispatch portal hero may route to
    the Admin Console ``/operations-map`` URL."""
    src = _read(DISPATCH_HERO)
    # Allowed: comments referencing `/operations-map` for context.
    # Forbidden: any JSX `to="/operations-map"` or `navigate("/operations-map`.
    offenders = re.findall(r'to="/operations-map"', src)
    offenders += re.findall(r'navigate\(\s*[`"\']/operations-map', src)
    assert not offenders, (
        f"Track 15.81 regression: DispatchMapHero.jsx still routes to "
        f"the admin-only `/operations-map` URL ({len(offenders)} hit(s)). "
        f"Use `/dispatch-portal/map` instead."
    )
    # Must explicitly target the Dispatch-owned alias.
    assert "/dispatch-portal/map" in src, (
        "Track 15.81 regression: DispatchMapHero.jsx must link to "
        "`/dispatch-portal/map` (the Dispatch-owned map route)."
    )


def test_dispatch_live_snapshot_has_no_admin_console_links():
    """No link rendered inside the Dispatch portal snapshot strip may
    route to the Admin Console ``/operations-map`` URL."""
    src = _read(DISPATCH_SNAPSHOT)
    offenders = re.findall(r'to="/operations-map"', src)
    offenders += re.findall(r'navigate\(\s*[`"\']/operations-map', src)
    assert not offenders, (
        f"Track 15.81 regression: DispatchLiveSnapshot.jsx still "
        f"routes to admin-only `/operations-map` ({len(offenders)} hit(s)). "
        f"Use `/dispatch-portal/map` instead."
    )
    assert "/dispatch-portal/map" in src, (
        "Track 15.81 regression: DispatchLiveSnapshot.jsx must link to "
        "`/dispatch-portal/map`."
    )


def test_no_dispatch_portal_component_links_to_admin_operations_map():
    """Broad sweep: scan every Dispatch-portal-namespaced component
    (pages/Dispatch*, components/Dispatch*, components/dispatch/**)
    and assert none of them link to ``/operations-map``."""
    targets: list[Path] = []
    for pattern in ("pages/Dispatch*.jsx", "components/Dispatch*.jsx"):
        targets.extend(FRONTEND_SRC.glob(pattern))
    dispatch_dir = FRONTEND_SRC / "components" / "dispatch"
    if dispatch_dir.is_dir():
        targets.extend(dispatch_dir.rglob("*.jsx"))
        targets.extend(dispatch_dir.rglob("*.js"))

    bad: list[str] = []
    for path in targets:
        try:
            body = path.read_text(encoding="utf-8")
        except Exception:
            continue
        # Only flag JSX link targets, not comments / API URLs.
        if re.search(r'to="/operations-map"', body):
            bad.append(str(path.relative_to(FRONTEND_SRC)))
        if re.search(r'navigate\(\s*[`"\']/operations-map', body):
            bad.append(str(path.relative_to(FRONTEND_SRC)))
    assert not bad, (
        "Track 15.81 regression: Dispatch portal components must NOT "
        f"link to admin-only `/operations-map`. Offenders: {sorted(set(bad))}"
    )


# ─── Backend RBAC trust (live preview) ────────────────────────────


@pytest.fixture(scope="module")
def super_admin_portal_tokens() -> dict:
    """Super Admin via /api/auth/multi-login returns every portal token,
    including ``portal_tokens.dispatch``."""
    if not BASE:
        pytest.skip("REACT_APP_BACKEND_URL not configured")
    r = requests.post(
        f"{BASE}/api/auth/multi-login",
        json={"email": SUPER_ADMIN_EMAIL, "password": SUPER_ADMIN_PASSWORD},
        timeout=60,
    )
    assert r.status_code == 200, f"multi-login failed: {r.status_code} {r.text}"
    data = r.json()
    tokens = data.get("portal_tokens") or {}
    assert tokens.get("dispatch"), f"Super admin should expose dispatch token, got: {tokens.keys()}"
    assert tokens.get("admin"), f"Super admin should expose admin token, got: {tokens.keys()}"
    return tokens


def test_operations_map_snapshot_accepts_dispatch_token(super_admin_portal_tokens):
    """A Dispatch token MUST be able to read the operations-map
    snapshot. If this fails, the Dispatch-owned `/dispatch-portal/map`
    page would still be 401/403 on data load."""
    dispatch_tok = super_admin_portal_tokens["dispatch"]
    r = requests.get(
        f"{BASE}/api/operations-map/snapshot",
        headers={"X-Dispatch-Token": dispatch_tok},
        timeout=45,
    )
    assert r.status_code == 200, (
        f"Dispatch token rejected by /api/operations-map/snapshot: "
        f"{r.status_code} {r.text[:200]}"
    )
    body = r.json()
    assert "feed_status" in body
    assert "operational_summary" in body


def test_operations_map_timeline_accepts_dispatch_token(super_admin_portal_tokens):
    dispatch_tok = super_admin_portal_tokens["dispatch"]
    r = requests.get(
        f"{BASE}/api/operations-map/timeline?limit=5",
        headers={"X-Dispatch-Token": dispatch_tok},
        timeout=45,
    )
    assert r.status_code == 200, (
        f"Dispatch token rejected by /api/operations-map/timeline: "
        f"{r.status_code} {r.text[:200]}"
    )


def test_operations_map_search_accepts_dispatch_token(super_admin_portal_tokens):
    dispatch_tok = super_admin_portal_tokens["dispatch"]
    r = requests.get(
        f"{BASE}/api/operations-map/search?q=truck",
        headers={"X-Dispatch-Token": dispatch_tok},
        timeout=45,
    )
    assert r.status_code == 200, (
        f"Dispatch token rejected by /api/operations-map/search: "
        f"{r.status_code} {r.text[:200]}"
    )


def test_operations_map_anonymous_still_rejected():
    """Anonymous (no portal token) callers MUST still be rejected.
    Track 15.81 does NOT widen the auth contract."""
    if not BASE:
        pytest.skip("REACT_APP_BACKEND_URL not configured")
    r = requests.get(f"{BASE}/api/operations-map/snapshot", timeout=30)
    assert r.status_code in (401, 403), (
        f"Anonymous call to /api/operations-map/snapshot must be "
        f"rejected, got {r.status_code} {r.text[:200]}"
    )
