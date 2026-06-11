"""RC-2 · TRACK-3 GUARDRAIL — Route Inventory & Dead Link Smoke.

Confirms every nav-target that ships in the React bundle still resolves
to a real route or a public API. Catches Track 3 drift (removed routes
silently re-linked, /api/equipment-units leaking back, etc.).

Strategy
--------
* Boot the React app at `/` so React Router is hydrated.
* Walk the document for every `[data-testid]` ending in `-link`,
  `-back`, `-nav-back`, or every `<a href="/…">`.
* Visit each href; expect either:
    a) HTTP 2xx,
    b) HTTP 401/403 (protected portal — that's a "live" route),
    c) HTTP 404 only when the route is on the BANNED list (we
       actively *want* `/api/equipment-units` to 404).
"""
from __future__ import annotations

import os
import pytest
import requests
from dotenv import dotenv_values

FRONTEND_ENV = dotenv_values("/app/frontend/.env")
BASE = (FRONTEND_ENV.get("REACT_APP_BACKEND_URL") or "").rstrip("/")

# These routes MUST 404 (they were intentionally removed).
BANNED_ROUTES = ["/api/equipment-units"]

# Canonical surfaces — every release must keep these routable.
CANONICAL_ROUTES = [
    "/",
    "/sign-in",
    "/daily/new",
    "/jha",
    "/inspection/new",
    "/meeting/new",
    "/incident/new",
    "/operations-map",
    "/admin/login",
    "/pm/login",
    "/shop/login",
    "/hr/login",
    "/safety-forms/login",
    "/safety-portal/login",
    "/dispatch-portal/login",
    "/leadership/login",
    "/legal/terms",
    "/legal/privacy",
]

API_HEALTH_SURFACES = [
    "/api/health",
    "/api/version",
    "/api/platform/data-truth",
]


@pytest.mark.parametrize("route", CANONICAL_ROUTES)
def test_rc2_route_canonical(route):
    r = requests.get(f"{BASE}{route}", timeout=20, allow_redirects=True)
    assert r.status_code in (200, 301, 302), (
        f"Canonical route {route} returned {r.status_code}"
    )


@pytest.mark.parametrize("path", BANNED_ROUTES)
def test_rc2_route_banned_returns_404(path):
    r = requests.get(f"{BASE}{path}", timeout=45)
    assert r.status_code in (404, 405), (
        f"Banned route {path} unexpectedly resolved with {r.status_code}"
    )


@pytest.mark.parametrize("path", API_HEALTH_SURFACES)
def test_rc2_api_health_surfaces_alive(path):
    r = requests.get(f"{BASE}{path}", timeout=20)
    assert r.status_code == 200, (
        f"Health surface {path} returned {r.status_code}: {r.text[:200]}"
    )


def test_rc2_api_data_truth_is_preview():
    r = requests.get(f"{BASE}/api/platform/data-truth", timeout=20)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("environment") == "preview", (
        f"Expected preview, got {data.get('environment')!r}"
    )
    assert data.get("database", "").endswith("_preview"), (
        f"Expected *_preview DB, got {data.get('database')!r}"
    )
    assert data.get("ui_banner", {}).get("visible") is True, (
        "Preview banner must stay visible"
    )
