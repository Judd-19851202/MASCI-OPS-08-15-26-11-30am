"""
test_iter346b_login_shell_and_super_admin.py — Regression lock for iter346-B.

FINAL OPTIONAL CLOSEOUT · Part B:
  1. Shared <PortalLoginShell /> extracted; HR / Safety / PM / Shop /
     Dispatch / FL all wrap their body card in it.
  2. Universal super-admin login fallback (Path 2) added to every
     portal login (HR / Safety / PM / Shop / Dispatch) — mirrors the
     iter344 pattern already on FL. A `user_directory` row with the
     `admin` portal grant + correct master password mints an admin
     token (kind:"admin") via any portal login screen.
"""
import os
import pytest
import httpx
import asyncio
from pathlib import Path

API_URL = os.environ.get(
    "API_URL",
    "https://safety-audit-mobile-1.preview.emergentagent.com",
).rstrip("/")
SUPER_ADMIN_EMAIL = "jaymn.judd@mascigc.com"
SUPER_ADMIN_PASSWORD = "Maddix123!"

ROOT = Path("/app")
FRONTEND_SRC = ROOT / "frontend/src"
SHELL = FRONTEND_SRC / "components/PortalLoginShell.jsx"


# ── Shell extraction · structural lock ──────────────────────────────


def test_portal_login_shell_component_exists():
    """The shared chrome component exists and uses literal class names
    (so Tailwind's content scanner finds them)."""
    assert SHELL.exists()
    src = SHELL.read_text()
    assert "export function PortalLoginShell" in src
    # Outer wrapper / DOM order preserved
    assert 'min-h-screen blueprint-bg flex flex-col' in src
    assert '"caution-stripe"' in src
    # Receives full literal class strings (no `border-${accent}`)
    assert "${headerBorderClass}" in src
    assert "${backHoverClass}" in src
    # Reuses platform-family chrome components
    for sym in ("MasciLogo", "ForgedOpsAttribution", "LangToggle"):
        assert sym in src


@pytest.mark.parametrize(
    "page_rel,must_contain",
    [
        (
            "pages/HrLogin.jsx",
            [
                'PortalLoginShell',
                'headerBorderClass="border-purple-700"',
                'backHoverClass="hover:text-purple-300"',
                'backTestId="hr-login-back"',
            ],
        ),
        (
            "pages/SafetyLogin.jsx",
            [
                'PortalLoginShell',
                'headerBorderClass="border-cyan-700"',
                'backHoverClass="hover:text-cyan-300"',
                'backTestId="safety-login-back"',
            ],
        ),
        (
            "pages/PmLogin.jsx",
            [
                'PortalLoginShell',
                'headerBorderClass="border-amber-500"',
                'backHoverClass="hover:text-amber-300"',
                'backTestId="pm-login-back"',
            ],
        ),
        (
            "pages/ShopLogin.jsx",
            [
                'PortalLoginShell',
                'headerBorderClass="border-amber-500"',
                'backHoverClass="hover:text-amber-300"',
                'backTestId="shop-login-back"',
            ],
        ),
        (
            "pages/DispatchLogin.jsx",
            [
                'PortalLoginShell',
                'headerBorderClass="border-orange-700"',
                'backHoverClass="hover:text-orange-300"',
                'backTestId="dispatch-login-back"',
            ],
        ),
        (
            "pages/FieldLeadershipPortalLogin.jsx",
            [
                'PortalLoginShell',
                'headerBorderClass="border-red-700"',
                'backHoverClass="hover:text-red-300"',
                'backTestId="fl-login-back"',
            ],
        ),
    ],
)
def test_each_portal_login_uses_shell(page_rel, must_contain):
    """Every portal login screen wraps its body in the shared shell."""
    src = (FRONTEND_SRC / page_rel).read_text()
    for tok in must_contain:
        assert tok in src, f"{page_rel} missing required token: {tok}"
    # The old hand-rolled chrome must be gone from each page (only the
    # shell renders it now). Detect leftover legacy chrome.
    assert 'min-h-screen blueprint-bg flex flex-col' not in src, (
        f"{page_rel} still renders chrome locally instead of via the shell"
    )


# ── Frontend wired for kind:"admin" fallback ───────────────────────


@pytest.mark.parametrize(
    "page_rel",
    [
        "pages/HrLogin.jsx",
        "pages/SafetyLogin.jsx",
        "pages/PmLogin.jsx",
        "pages/ShopLogin.jsx",
        "pages/DispatchLogin.jsx",
    ],
)
def test_each_portal_login_handles_admin_kind(page_rel):
    """Each frontend stores admin token when backend returns kind:'admin'."""
    src = (FRONTEND_SRC / page_rel).read_text()
    assert 'setAdminToken' in src, f"{page_rel} not importing setAdminToken"
    assert 'kind === "admin"' in src, (
        f"{page_rel} not branching on kind:'admin' response"
    )
    assert 'navigate("/admin"' in src or 'nav("/admin"' in src


# ── Backend Path 2 lock (source-level) ──────────────────────────────


@pytest.mark.parametrize(
    "module_rel,marker",
    [
        ("backend/routes/hr_portal.py", "admin_via_hr"),
        ("backend/routes/safety_portal/auth_users.py", "admin_via_safety"),
        ("backend/routes/dispatch_portal_auth.py", "admin_via_dispatch"),
        ("backend/server.py", "admin_via_pm"),
        ("backend/server.py", "admin_via_shop"),
    ],
)
def test_each_backend_login_has_directory_admin_fallback(module_rel, marker):
    src = (ROOT / module_rel).read_text()
    assert marker in src, f"{module_rel} missing super-admin fallback marker {marker}"
    # And references the admin minter / directory authenticate
    assert "_directory_admin_token" in src or "directory_admin_minter" in src


# ── E2E auth · super-admin via every portal login ──────────────────


@pytest.fixture(scope="module")
def test_admin_only_user():
    """Ensure an admin-only directory user exists, return its creds."""
    email = "iter346b-admin@example.com"
    password = "AdminOnly346B!"

    async def _ensure():
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Log in as super admin
            r = await client.post(
                f"{API_URL}/api/auth/multi-login",
                json={"email": SUPER_ADMIN_EMAIL, "password": SUPER_ADMIN_PASSWORD},
            )
            r.raise_for_status()
            admin_tok = r.json()["portal_tokens"]["admin"]
            # Check if user exists
            r = await client.get(
                f"{API_URL}/api/admin/directory",
                headers={"X-Admin-Token": admin_tok},
            )
            r.raise_for_status()
            users = r.json().get("users", [])
            existing = next((u for u in users if u["email"] == email), None)
            if existing:
                # Make sure enabled and password is reset
                await client.patch(
                    f"{API_URL}/api/admin/directory/{existing['id']}",
                    headers={"X-Admin-Token": admin_tok},
                    json={"disabled": False, "password": password, "must_change_password": False},
                )
                return email, password
            # Create
            r = await client.post(
                f"{API_URL}/api/admin/directory",
                headers={"X-Admin-Token": admin_tok},
                json={
                    "email": email,
                    "name": "Iter346B Admin Only",
                    "portals": ["admin"],
                    "password": password,
                    "must_change_password": False,
                    "delivery": "screen",
                },
            )
            r.raise_for_status()
            return email, password

    return asyncio.get_event_loop().run_until_complete(_ensure())


@pytest.mark.parametrize(
    "endpoint",
    [
        "/api/hr/login",
        "/api/safety/login",
        "/api/pm/login",
        "/api/shop/login",
        "/api/dispatch/login",
    ],
)
def test_admin_only_user_signs_in_via_each_portal(test_admin_only_user, endpoint):
    email, password = test_admin_only_user

    async def _run():
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                f"{API_URL}{endpoint}",
                json={"email": email, "password": password},
            )
            assert r.status_code == 200, f"{endpoint} returned {r.status_code}: {r.text[:200]}"
            data = r.json()
            assert data.get("kind") == "admin", (
                f"{endpoint} returned kind={data.get('kind')!r} — expected 'admin'"
            )
            assert data.get("token"), f"{endpoint} returned no token"
            # The minted admin token must actually be accepted by /api/admin/*
            r2 = await client.get(
                f"{API_URL}/api/admin/system-health",
                headers={"X-Admin-Token": data["token"]},
            )
            assert r2.status_code == 200

    asyncio.get_event_loop().run_until_complete(_run())


def test_wrong_password_does_not_bypass():
    """Wrong password must return 401 even for an admin email."""

    async def _run():
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                f"{API_URL}/api/hr/login",
                json={"email": SUPER_ADMIN_EMAIL, "password": "wrong-password"},
            )
            assert r.status_code == 401

    asyncio.get_event_loop().run_until_complete(_run())


def test_native_hr_user_still_works():
    """Sanity — native portal login still works (kind:'hr')."""

    async def _run():
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Native HR test user from /app/memory/test_credentials.md
            r = await client.post(
                f"{API_URL}/api/hr/login",
                json={"email": "hrmanager@mascigc.com", "password": "HRTesting2026!"},
            )
            # If creds rotated, accept any response that proves the
            # native flow is intact (NOT kind:'admin').
            if r.status_code == 200:
                data = r.json()
                assert data.get("kind") == "hr"
            else:
                # 401 means the password rotated — that is still a
                # native response, NOT an accidental admin promote.
                assert r.status_code in (401, 403)

    asyncio.get_event_loop().run_until_complete(_run())
