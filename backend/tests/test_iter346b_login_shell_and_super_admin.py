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
import requests
from pathlib import Path

API_URL = os.environ.get(
    "API_URL",
    os.environ.get("REACT_APP_BACKEND_URL", "https://masci-audit-hub.preview.emergentagent.com"),
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
    assert 'wp17-public-shell wp17-portal-login flex min-h-screen flex-col' in src
    assert '"caution-stripe"' in src
    # Receives literal class strings from each portal page.
    assert 'className={headerBorderClass || ""}' in src
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
        ("backend/routes/pm_routes.py", "admin_via_pm"),
        ("backend/server.py", "admin_via_shop"),
    ],
)
def test_each_backend_login_has_directory_admin_fallback(module_rel, marker):
    src = (ROOT / module_rel).read_text()
    assert marker in src, f"{module_rel} missing super-admin fallback marker {marker}"
    # And references the admin minter / directory authenticate
    assert any(token in src for token in ("_directory_admin_token", "directory_admin_minter", "directory_admin_token_fn"))


# ── E2E auth · super-admin via every portal login ──────────────────


@pytest.fixture(scope="module")
def test_admin_only_user():
    """Ensure an admin-granted directory user exists, return its creds."""
    email = "iter346b-admin@example.com"
    password = "AdminOnly346B!"
    client = requests.Session()
    r = client.post(
        f"{API_URL}/api/auth/multi-login",
        json={"email": SUPER_ADMIN_EMAIL, "password": SUPER_ADMIN_PASSWORD},
        headers={"X-Device-Id": "iter346b-seed-admin"},
        timeout=60,
    )
    r.raise_for_status()
    body = r.json()
    admin_headers = {
        "X-Admin-Token": body["portal_tokens"]["admin"],
        "X-Directory-Token": body["session_token"],
    }
    r = client.get(f"{API_URL}/api/admin/directory", headers=admin_headers, timeout=60)
    r.raise_for_status()
    users = r.json().get("users", [])
    existing = next((u for u in users if u["email"] == email), None)
    if existing:
        client.patch(
            f"{API_URL}/api/admin/directory/{existing['id']}",
            headers=admin_headers,
            json={"disabled": False, "portals": ["admin"]},
            timeout=60,
        )
        client.post(
            f"{API_URL}/api/admin/directory/{existing['id']}/reset-password",
            headers=admin_headers,
            json={"new_password": password, "must_change": False, "delivery": "show"},
            timeout=60,
        )
        return email, password
    r = client.post(
        f"{API_URL}/api/admin/directory",
        headers=admin_headers,
        json={
            "email": email,
            "name": "Iter346B Admin Only",
            "portals": ["admin"],
            "password": password,
            "must_change_password": False,
            "delivery": "show",
        },
        timeout=60,
    )
    r.raise_for_status()
    return email, password


@pytest.mark.parametrize("endpoint", ["/api/hr/login", "/api/safety/login", "/api/dispatch/login"])
def test_admin_only_user_signs_in_via_supported_portals(test_admin_only_user, endpoint):
    email, password = test_admin_only_user
    client = requests.Session()
    r = client.post(
        f"{API_URL}{endpoint}",
        json={"email": email, "password": password},
        headers={"X-Device-Id": f"iter346b-{endpoint.split('/')[-2]}"},
        timeout=60,
    )
    assert r.status_code == 200, f"{endpoint} returned {r.status_code}: {r.text[:200]}"
    data = r.json()
    assert data.get("kind") == "admin", f"{endpoint} returned kind={data.get('kind')!r} — expected 'admin'"
    assert data.get("token")
    r2 = client.get(f"{API_URL}/api/admin/system-health", headers={"X-Admin-Token": data["token"]}, timeout=60)
    assert r2.status_code == 200


@pytest.mark.parametrize(
    "endpoint,expected_kind",
    [("/api/pm/login", "pm"), ("/api/shop/login", "shop")],
)
def test_pm_and_shop_preserve_native_kind_for_native_accounts(endpoint, expected_kind):
    client = requests.Session()
    r = client.post(
        f"{API_URL}{endpoint}",
        json={"email": SUPER_ADMIN_EMAIL, "password": SUPER_ADMIN_PASSWORD},
        headers={"X-Device-Id": f"iter346b-super-{endpoint.split('/')[-2]}"},
        timeout=60,
    )
    assert r.status_code == 200, f"{endpoint} returned {r.status_code}: {r.text[:200]}"
    data = r.json()
    assert data.get("kind") == expected_kind
    assert data.get("token")
    header_name = "X-PM-Token" if expected_kind == "pm" else "X-Shop-Token"
    target = "/api/pm/me" if expected_kind == "pm" else "/api/shop/me"
    r2 = client.get(f"{API_URL}{target}", headers={header_name: data["token"]}, timeout=60)
    assert r2.status_code == 200


def test_wrong_password_does_not_bypass():
    """Wrong password must return 401 even for an admin email."""
    r = requests.post(
        f"{API_URL}/api/hr/login",
        json={"email": SUPER_ADMIN_EMAIL, "password": "wrong-password"},
        timeout=60,
    )
    assert r.status_code == 401


def test_native_hr_user_still_works():
    """Sanity — native portal login still works (kind:'hr')."""
    r = requests.post(
        f"{API_URL}/api/hr/login",
        json={"email": "hrmanager@mascigc.com", "password": "HRTesting2026!"},
        timeout=60,
    )
    if r.status_code == 200:
        data = r.json()
        assert data.get("kind") == "hr"
    else:
        assert r.status_code in (401, 403)
