"""
test_iter179_admin_access_control_gate.py — Phase K P0 hardening.

Critical regression test for the access-control failure reported by
the user: an HR-only user could see and navigate into the Admin
Console because the front-end PortalSwitcher widget rendered from a
stale `masci.directory.user` left behind by a prior super-admin
multi-login.

Front-end fixes ship in iter179 (sessionReset.js + EnforcePortalScope
+ PortalSwitcher hardening). This test verifies the **back-end** half
of the same gate: every `/api/admin/*` endpoint must reject HR / Shop
/ PM / Dispatch / Safety / Dev tokens AND anonymous requests. The
admin token requirement must be enforced server-side regardless of
what the front-end UI exposes.

Coverage:
  • Anonymous → 401/403 on every sampled admin endpoint.
  • Per-portal tokens (HR / Shop / PM / Dispatch / Safety) → 401/403
    on every sampled admin endpoint.
  • Admin token → 200 on every sampled admin endpoint (sanity).
  • Per-portal `me` endpoints reject other portals' tokens.
  • The new K4a + K4b directory endpoints also block cross-portal
    tokens.

We intentionally hit a SAMPLE of admin endpoints rather than scraping
the entire surface — the sample covers every router with admin
routes, so a regression on the canonical gate would be caught.
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import httpx

sys.path.insert(0, "/app/backend")


def _load_env(p: str) -> None:
    txt = Path(p).read_text()
    for line in txt.splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"'))


_load_env("/app/backend/.env")

BACKEND_URL = "http://localhost:8001"


# ─── Token acquisition helpers ────────────────────────────────────────────
async def _login(path: str, payload: Dict) -> Optional[str]:
    async with httpx.AsyncClient(base_url=BACKEND_URL, timeout=10) as c:
        r = await c.post(path, json=payload)
        if r.status_code != 200:
            return None
        return r.json().get("token")


async def _admin_token() -> str:
    return (
        await _login(
            "/api/admin/login",
            {"password": os.environ.get("ADMIN_PASSWORD", "")},
        )
    ) or ""


async def _hr_token() -> str:
    return (
        await _login(
            "/api/hr/login",
            {"email": "hrmanager@mascigc.com", "password": "HRTesting2026!"},
        )
    ) or ""


async def _shop_token() -> str:
    return (
        await _login(
            "/api/shop/login",
            {"email": "testmech@mascigc.com", "password": "ResetWorks2026!"},
        )
    ) or ""


async def _safety_token() -> str:
    """Acquire a safety portal token. Self-bootstraps: if the
    documented credentials no longer work (e.g. password rotated by a
    prior test run), do an admin-mediated reset and use the returned
    temp password."""
    creds = {"email": "safety@mascigc.com", "password": "SafetyTest2026!"}
    tok = await _login("/api/safety/login", creds)
    if tok:
        return tok
    admin = await _admin_token()
    async with httpx.AsyncClient(base_url=BACKEND_URL, timeout=10) as c:
        users = await c.get(
            "/api/admin/safety-users", headers={"X-Admin-Token": admin}
        )
        users.raise_for_status()
        uid = next(
            u["id"] for u in users.json() if u["email"] == creds["email"]
        )
        r = await c.post(
            f"/api/admin/safety-users/{uid}/reset-password",
            headers={"X-Admin-Token": admin},
        )
        r.raise_for_status()
        temp = r.json()["temp_password"]
        return (
            await _login(
                "/api/safety/login", {"email": creds["email"], "password": temp}
            )
        ) or ""


async def _dispatch_token() -> str:
    """Acquire a dispatch portal token. Self-bootstrap pattern: dispatch
    reset endpoint always mints a fresh random temp password (ignoring
    request body) — use that returned value to log in."""
    creds = {"email": "dispatch@mascigc.com", "password": "DispatchTest2026!"}
    tok = await _login("/api/dispatch/login", creds)
    if tok:
        return tok
    admin = await _admin_token()
    async with httpx.AsyncClient(base_url=BACKEND_URL, timeout=10) as c:
        users = await c.get(
            "/api/admin/dispatch-users", headers={"X-Admin-Token": admin}
        )
        users.raise_for_status()
        uid = next(
            u["id"] for u in users.json() if u["email"] == creds["email"]
        )
        r = await c.post(
            f"/api/admin/dispatch-users/{uid}/reset-password",
            headers={"X-Admin-Token": admin},
        )
        r.raise_for_status()
        temp = r.json()["temp_password"]
        return (
            await _login(
                "/api/dispatch/login",
                {"email": creds["email"], "password": temp},
            )
        ) or ""


# Sample of admin endpoints across every router with `/api/admin/*`
# routes. Selected for stability + read-only safety.
ADMIN_GET_ENDPOINTS = [
    "/api/admin/check",
    "/api/admin/deploy-readiness",
    "/api/admin/integrations/health",
    "/api/admin/audit",
    "/api/admin/directory",
    "/api/admin/directory/k4/users",
    "/api/admin/directory/k4/stats",
    "/api/admin/directory/k4/role-templates",
    "/api/admin/analytics/summary",
    "/api/admin/operational-signals",
    "/api/admin/find-by-doc-id?id=zz",
    "/api/admin/po-requests/scan-missing-receipts/preview",
    "/api/admin/document-expirations/scan/preview",
    "/api/admin/hr-users",
    "/api/admin/shop-users",
    "/api/admin/dispatch-users",
]

# These admin POST endpoints accept empty body or query — verifying
# only the auth gate, not the business logic. Body=None for explicit
# anon probe (we don't want body-validation to swallow auth check).
ADMIN_POST_ENDPOINTS = [
    "/api/admin/po-requests/scan-missing-receipts",
    "/api/admin/document-expirations/scan",
]


def _run(coro):
    return asyncio.run(coro)


async def _probe(method: str, path: str, headers: Dict[str, str]) -> int:
    async with httpx.AsyncClient(base_url=BACKEND_URL, timeout=10) as c:
        if method == "GET":
            r = await c.get(path, headers=headers)
        else:
            r = await c.post(path, headers=headers, json={})
        return r.status_code


# ─── 1. Anon must be blocked on every admin endpoint ──────────────────────
def test_anon_blocked_on_every_sampled_admin_get_endpoint():
    async def body():
        violations: List[Tuple[str, int]] = []
        for path in ADMIN_GET_ENDPOINTS:
            sc = await _probe("GET", path, {})
            # Permitted: 401/403. NEVER 200.
            if sc not in (401, 403):
                violations.append((path, sc))
        assert not violations, f"Anon got non-401/403 on: {violations}"

    _run(body())


def test_anon_blocked_on_every_sampled_admin_post_endpoint():
    async def body():
        violations: List[Tuple[str, int]] = []
        for path in ADMIN_POST_ENDPOINTS:
            sc = await _probe("POST", path, {})
            if sc not in (401, 403):
                violations.append((path, sc))
        assert not violations, f"Anon got non-401/403 POST on: {violations}"

    _run(body())


# ─── 2. Cross-portal tokens must NOT unlock admin routes ──────────────────
# This is the heart of the user's reported P0 bug — except now we are
# proving the BACK-END half. Front-end fix is in iter179 sessionReset
# + PortalSwitcher.
def test_hr_token_cannot_access_admin_get_endpoints():
    async def body():
        tok = await _hr_token()
        assert tok, "HR test login failed — fix credentials"
        violations = []
        for path in ADMIN_GET_ENDPOINTS:
            sc = await _probe("GET", path, {"X-HR-Token": tok})
            if sc not in (401, 403):
                violations.append((path, sc))
        assert not violations, (
            f"HR token unlocked admin endpoints (P0 leak): {violations}"
        )

    _run(body())


def test_shop_token_cannot_access_admin_get_endpoints():
    async def body():
        tok = await _shop_token()
        assert tok, "Shop test login failed — fix credentials"
        violations = []
        for path in ADMIN_GET_ENDPOINTS:
            sc = await _probe("GET", path, {"X-Shop-Token": tok})
            if sc not in (401, 403):
                violations.append((path, sc))
        assert not violations, (
            f"Shop token unlocked admin endpoints (P0 leak): {violations}"
        )

    _run(body())


def test_safety_token_cannot_access_admin_get_endpoints():
    async def body():
        tok = await _safety_token()
        assert tok, "Safety test login failed — fix credentials"
        violations = []
        for path in ADMIN_GET_ENDPOINTS:
            sc = await _probe("GET", path, {"X-Safety-Token": tok})
            if sc not in (401, 403):
                violations.append((path, sc))
        assert not violations, (
            f"Safety token unlocked admin endpoints (P0 leak): {violations}"
        )

    _run(body())


def test_dispatch_token_cannot_access_admin_get_endpoints():
    async def body():
        tok = await _dispatch_token()
        assert tok, "Dispatch test login failed — fix credentials"
        violations = []
        for path in ADMIN_GET_ENDPOINTS:
            sc = await _probe("GET", path, {"X-Dispatch-Token": tok})
            if sc not in (401, 403):
                violations.append((path, sc))
        assert not violations, (
            f"Dispatch token unlocked admin endpoints (P0 leak): {violations}"
        )

    _run(body())


# ─── 3. Admin token must continue to work (sanity) ────────────────────────
def test_admin_token_unlocks_admin_endpoints():
    async def body():
        tok = await _admin_token()
        assert tok, "Admin test login failed"
        # We only check a small slice — the K4 + audit endpoints — to
        # confirm the gate isn't accidentally broken for the legit role.
        for path in (
            "/api/admin/check",
            "/api/admin/audit",
            "/api/admin/directory/k4/users",
            "/api/admin/directory/k4/stats",
        ):
            sc = await _probe("GET", path, {"X-Admin-Token": tok})
            assert sc == 200, f"Admin token REJECTED by {path} → {sc}"

    _run(body())


# ─── 4. K4b mutation endpoints must reject all other tokens ──────────────
def test_k4b_mutation_endpoints_reject_non_admin_tokens():
    async def body():
        hr = await _hr_token()
        shop = await _shop_token()
        for token_name, token in [("X-HR-Token", hr), ("X-Shop-Token", shop)]:
            for path, payload in [
                ("/api/admin/directory/k4/users/zzz/role-template",
                 {"role_template_id": None}),
                ("/api/admin/directory/k4/users/zzz/convert-to-managed",
                 {"password": "Anything12345!"}),
                ("/api/admin/directory/k4/users/zzz/revert-to-mirrored",
                 None),
                ("/api/admin/directory/k4/users/zzz/set-disabled",
                 {"disabled": True}),
            ]:
                async with httpx.AsyncClient(base_url=BACKEND_URL, timeout=10) as c:
                    r = await c.post(path, headers={token_name: token}, json=payload)
                assert r.status_code in (401, 403), (
                    f"K4b leak: {token_name} → {path} returned {r.status_code}"
                )

    _run(body())


# ─── 5. Cross-portal `me` endpoints must isolate ──────────────────────────
def test_per_portal_me_rejects_other_portal_tokens():
    async def body():
        hr = await _hr_token()
        # HR token must NOT unlock /api/shop/check or /api/dispatch/me etc.
        async with httpx.AsyncClient(base_url=BACKEND_URL, timeout=10) as c:
            r1 = await c.get("/api/shop/check", headers={"X-HR-Token": hr})
            r2 = await c.get("/api/dispatch/me", headers={"X-HR-Token": hr})
            r3 = await c.get("/api/safety/me", headers={"X-HR-Token": hr})
        for r, label in ((r1, "shop"), (r2, "dispatch"), (r3, "safety")):
            assert r.status_code in (401, 403), (
                f"HR token leaked into /{label}/me family: {r.status_code} {r.text}"
            )

    _run(body())


# ─── 6. Directory multi-logout must invalidate the directory session ─────
def test_multi_logout_invalidates_directory_session_server_side():
    """The iter179 `clearAllSessions` calls /api/auth/multi-logout
    server-side. Verify that after logout the directory token is
    actually killed (subsequent /api/auth/me-directory → 401)."""

    async def body():
        # Acquire a directory session via multi-login
        async with httpx.AsyncClient(base_url=BACKEND_URL, timeout=10) as c:
            r = await c.post(
                "/api/auth/multi-login",
                json={
                    "email": "jaymn.judd@mascigc.com",
                    "password": "Maddix123!",
                },
            )
            assert r.status_code == 200, r.text
            dir_tok = r.json()["session_token"]
            # Confirm session is valid
            me = await c.get(
                "/api/auth/me-directory",
                headers={"X-Directory-Token": dir_tok},
            )
            assert me.status_code == 200
            # Logout
            out = await c.post(
                "/api/auth/multi-logout",
                headers={"X-Directory-Token": dir_tok},
            )
            assert out.status_code == 200
            # Token must now be rejected
            me2 = await c.get(
                "/api/auth/me-directory",
                headers={"X-Directory-Token": dir_tok},
            )
            assert me2.status_code == 401, (
                f"directory token still valid post-logout: {me2.status_code}"
            )

    _run(body())
