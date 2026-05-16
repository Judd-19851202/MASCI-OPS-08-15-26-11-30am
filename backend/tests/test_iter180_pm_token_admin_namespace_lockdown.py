"""
test_iter180_pm_token_admin_namespace_lockdown.py — Phase K P0 follow-up.

User mandate (2026-05-16, post-iter179 testing-agent finding):
> "PM should NOT unlock Admin read endpoints. PM users are not Admin
>  users and should not have access to /api/admin/* unless a specific
>  endpoint is intentionally exposed through a separate PM-safe API."

Iter180 closes that surface by changing the `require_admin` gate in
server.py to reject PM tokens on any path under `/api/admin/`. Non-
admin routes (jobs, equipment, safety, etc.) that PMs legitimately
read continue to accept PM tokens — the change is namespace-scoped.

This test verifies BOTH halves of the new contract:

  A. PM token → 401 on every sampled `/api/admin/*` endpoint
  B. PM token → 200 on a sample of legitimately PM-readable
     non-`/admin/*` endpoints (so we don't over-tighten)
  C. Admin token → 200 on the same admin endpoints (sanity)
  D. PM token can still self-validate via `/api/pm/me`

Sample is intentionally broad — covers EVERY router under /admin/* that
historically routed through require_admin (server.py natives + router
files at hr_portal, dispatch_portal_auth, hub_banners, training_center,
deploy_readiness, integration_health, operational_signals, master_lookup,
signature_migration).
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

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


async def _admin_token() -> str:
    async with httpx.AsyncClient(base_url=BACKEND_URL, timeout=10) as c:
        r = await c.post(
            "/api/admin/login",
            json={"password": os.environ.get("ADMIN_PASSWORD", "")},
        )
        r.raise_for_status()
        return r.json()["token"]


async def _pm_token() -> str:
    """PM user used for the tightening regression. We deliberately
    use the seeded `chriswright@mascigc.com` PM account — same
    credential the iter179 testing agent used to find the leak."""
    async with httpx.AsyncClient(base_url=BACKEND_URL, timeout=10) as c:
        r = await c.post(
            "/api/pm/login",
            json={
                "email": "chriswright@mascigc.com",
                "password": "ChrisRocksThis2026",
            },
        )
        r.raise_for_status()
        return r.json()["token"]


# Endpoints the testing-agent specifically flagged as leaking under PM
# tokens, PLUS one sample per router that previously took `require_admin`.
ADMIN_GET_ENDPOINTS = [
    # core
    "/api/admin/check",
    "/api/admin/logout",  # POST in reality — added separately below
    # user management
    "/api/admin/hr-users",
    "/api/admin/shop-users",
    "/api/admin/dispatch-users",
    "/api/admin/project-managers",
    # ops / health / deploy
    "/api/admin/deploy-readiness",
    "/api/admin/integrations/health",
    "/api/admin/analytics/summary",
    "/api/admin/operational-signals",
    "/api/admin/persistence-check",
    # data admin
    "/api/admin/employees/status",
    "/api/admin/suppliers/status",
    "/api/admin/equipment-master/status",
    "/api/admin/equipment-master/archive",
    "/api/admin/jobs/export",
    "/api/admin/jobs/archive",
    "/api/admin/projects/list",
    # admin-only audit / directory (already strict; sanity)
    "/api/admin/audit",
    "/api/admin/directory",
    "/api/admin/directory/k4/users",
    "/api/admin/directory/k4/stats",
    # banners / training / master lookup
    "/api/admin/banners",
    "/api/admin/training/stats",
    "/api/admin/calculators/stats",
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


# ─── A. PM token blocked on every /api/admin/* GET sampled ──────────────
def test_pm_token_blocked_on_every_admin_get_endpoint():
    """The exact bug class the testing agent flagged after iter179.
    PM token must NEVER unlock a /api/admin/* endpoint."""

    async def body():
        pm = await _pm_token()
        violations: List[Tuple[str, int]] = []
        # Admin /logout is POST-only — skip in GET pass and probe in POST pass.
        for path in [p for p in ADMIN_GET_ENDPOINTS if p != "/api/admin/logout"]:
            sc = await _probe("GET", path, {"X-PM-Token": pm})
            if sc not in (401, 403):
                violations.append((path, sc))
        assert not violations, (
            "PM token still unlocks /api/admin/* endpoints "
            f"(iter180 tightening regressed): {violations}"
        )

    _run(body())


# ─── A2. PM token blocked on POST /api/admin/logout too ─────────────────
def test_pm_token_blocked_on_admin_logout_post():
    async def body():
        pm = await _pm_token()
        sc = await _probe("POST", "/api/admin/logout", {"X-PM-Token": pm})
        assert sc in (401, 403), f"PM token still unlocks /api/admin/logout: {sc}"

    _run(body())


# ─── A3. PM token blocked on K4b mutation endpoints ─────────────────────
def test_pm_token_blocked_on_k4b_mutations():
    async def body():
        pm = await _pm_token()
        for path, payload in [
            ("/api/admin/directory/k4/users/zzz/role-template",
             {"role_template_id": None}),
            ("/api/admin/directory/k4/users/zzz/convert-to-managed",
             {"password": "Anything12345!"}),
            ("/api/admin/directory/k4/users/zzz/set-disabled",
             {"disabled": True}),
        ]:
            async with httpx.AsyncClient(base_url=BACKEND_URL, timeout=10) as c:
                r = await c.post(path, headers={"X-PM-Token": pm}, json=payload)
            assert r.status_code in (401, 403), (
                f"PM token still unlocks K4b mutation {path}: {r.status_code}"
            )

    _run(body())


# ─── B. PM token must STILL work on legitimate non-/admin/* PM reads ────
def test_pm_token_still_works_on_pm_namespace_endpoints():
    """We must not over-tighten — PM users still need their portal
    endpoints to function."""

    async def body():
        pm = await _pm_token()
        async with httpx.AsyncClient(base_url=BACKEND_URL, timeout=10) as c:
            r = await c.get("/api/pm/me", headers={"X-PM-Token": pm})
        assert r.status_code == 200, f"/api/pm/me regressed for PM: {r.status_code}"

    _run(body())


def test_pm_token_still_reads_pm_scoped_business_data():
    """Sanity that scoped business-data routes (NOT under /admin/) keep
    accepting PM tokens. Sample picks endpoints PMs use day-to-day."""

    async def body():
        pm = await _pm_token()
        async with httpx.AsyncClient(base_url=BACKEND_URL, timeout=10) as c:
            for path in (
                "/api/jobs",
                "/api/inspections",
                "/api/job-hazard-plans",
                "/api/trench-boxes",
            ):
                r = await c.get(path, headers={"X-PM-Token": pm})
                assert r.status_code == 200, (
                    f"PM lost access to legitimate non-admin route {path}: "
                    f"{r.status_code}"
                )

    _run(body())


# ─── C. Admin token still unlocks the same /api/admin/* endpoints ──────
def test_admin_token_still_unlocks_admin_endpoints():
    async def body():
        admin = await _admin_token()
        violations = []
        for path in [p for p in ADMIN_GET_ENDPOINTS if p != "/api/admin/logout"]:
            sc = await _probe("GET", path, {"X-Admin-Token": admin})
            # Some admin endpoints validly return 404 (e.g. legacy
            # routes whose DB collection hasn't seeded) — only flag
            # 401/403 as gate regressions.
            if sc in (401, 403):
                violations.append((path, sc))
        assert not violations, (
            "Admin token was wrongly rejected by /api/admin/* endpoints "
            f"(gate is now over-strict): {violations}"
        )

    _run(body())


# ─── D. Anon still blocked everywhere (iter179 regression carry-through)
def test_anon_still_blocked_on_admin_namespace():
    async def body():
        violations = []
        for path in [p for p in ADMIN_GET_ENDPOINTS if p != "/api/admin/logout"]:
            sc = await _probe("GET", path, {})
            if sc not in (401, 403):
                violations.append((path, sc))
        assert not violations, f"Anon got non-401/403 on: {violations}"

    _run(body())


# ─── E. Error message contract — admin namespace returns "Admin login required"
# (not "Admin or PM login required") so the API is honest about the gate.
def test_admin_namespace_error_message_no_longer_mentions_pm():
    async def body():
        async with httpx.AsyncClient(base_url=BACKEND_URL, timeout=10) as c:
            r = await c.get("/api/admin/check")
        assert r.status_code in (401, 403), r.text
        body_text = r.text.lower()
        # Must be admin-only language. Must not lure PMs into thinking
        # they can authenticate against /api/admin/*.
        assert "admin" in body_text
        assert " pm " not in body_text and "pm login" not in body_text, (
            f"Admin error still mentions PM (gate signal regression): {r.text}"
        )

    _run(body())
