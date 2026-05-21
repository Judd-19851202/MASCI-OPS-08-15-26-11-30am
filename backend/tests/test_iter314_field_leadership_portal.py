"""
iter314 · Field Leadership Portal regression invariants.

Locks the governance contract for the per-user Field Leadership portal:

  • New portal lives at /api/field-leadership/portal/* — distinct from
    the legacy /api/field-leadership/login shared-password gate.
  • Login + change-password + me + dispatch-today + driver-qualification
    end-to-end work for the seed user.
  • Dispatch visibility is bounded to today/tomorrow only.
  • Field Leadership token does NOT grant HR/Admin/payroll/system access.
  • HR-or-Admin combined gate guards every /api/admin/field-leadership-users
    route (both portals can manage Field Leadership users; Field Leadership
    cannot manage itself).
  • Legacy shared-password document gate at /api/field-leadership/login
    still returns a session token (untouched architectural collision).
  • Frontend route surface keeps the new portal pages wired and gated by
    RequireFl; the admin/HR user-management panel is mounted on both
    /admin/people and the new /hr/field-leadership-users surface.

Implemented as a mix of runtime API checks (live preview backend, same
shape as other iterXxx tests) and static-code invariants (lock the
frontend wiring against silent drift).

Seed credentials used:
  fieldleader@mascigc.com / FieldLead2026!
"""
from __future__ import annotations

import os
import re
from pathlib import Path

import pytest
import requests

REPO_ROOT = Path(__file__).resolve().parents[2]
APP_JS = REPO_ROOT / "frontend/src/App.js"
HR_HUB = REPO_ROOT / "frontend/src/pages/HrHub.jsx"
ADMIN_PEOPLE = REPO_ROOT / "frontend/src/pages/admin/AdminPeople.jsx"
HR_FL_USERS_PAGE = REPO_ROOT / "frontend/src/pages/HrFieldLeadershipUsers.jsx"
FL_LOGIN_PAGE = REPO_ROOT / "frontend/src/pages/FieldLeadershipPortalLogin.jsx"
REQUIRE_FL = REPO_ROOT / "frontend/src/components/RequireFl.jsx"
FL_USERS_PANEL = REPO_ROOT / "frontend/src/components/AdminFieldLeadershipUsersPanel.jsx"
FL_BACKEND_MOD = REPO_ROOT / "backend/field_leadership_users.py"
FL_PORTAL_ROUTES = REPO_ROOT / "backend/routes/field_leadership_portal.py"


def _read_kv(path: Path, key: str) -> str:
    try:
        with path.open() as f:
            for line in f:
                if line.startswith(f"{key}="):
                    return line.split("=", 1)[1].strip().strip('"').rstrip("/")
    except Exception:
        return ""
    return ""


URL = (
    _read_kv(REPO_ROOT / "frontend/.env", "REACT_APP_BACKEND_URL")
    or os.environ.get("REACT_APP_BACKEND_URL", "")
).rstrip("/")

FL_EMAIL = "fieldleader@mascigc.com"
FL_PASSWORD = "FieldLead2026!"

# ---------------------------------------------------------------------------
# Runtime: end-to-end auth flow on the new portal.
# ---------------------------------------------------------------------------


def _fl_token() -> str:
    """Login as the seed Field Leadership user and return the session token."""
    r = requests.post(
        f"{URL}/api/field-leadership/portal/login",
        json={"email": FL_EMAIL, "password": FL_PASSWORD},
        timeout=10,
    )
    assert r.status_code == 200, f"FL login failed: {r.status_code} {r.text}"
    body = r.json()
    assert body.get("ok") is True
    tok = body.get("token") or ""
    assert tok and "." in tok, "FL token must be the `<id>.<hmac>` shape"
    return tok


def test_iter314_fl_seed_user_login_works():
    """Backend route /field-leadership/portal/login authenticates the seed."""
    tok = _fl_token()
    # /me must return a Superintendent shape (allowed FL role).
    r = requests.get(
        f"{URL}/api/field-leadership/portal/me",
        headers={"X-FL-Token": tok},
        timeout=10,
    )
    assert r.status_code == 200
    body = r.json()
    user = body.get("user") or {}
    assert user.get("email") == FL_EMAIL
    assert user.get("role") in {
        "Superintendent", "Foreman", "Truck Boss",
        "Working Supervisor", "Field Supervisor",
    }


def test_iter314_anonymous_blocked_on_portal_routes():
    """Every protected portal route must 401 with no FL token."""
    for path in (
        "/api/field-leadership/portal/me",
        "/api/field-leadership/portal/dispatch-today",
        "/api/field-leadership/portal/driver-qualification",
    ):
        # Bypass conftest's auto admin-token injection for a clean anon hit.
        import urllib.request
        req = urllib.request.Request(f"{URL}{path}")
        try:
            urllib.request.urlopen(req, timeout=10)
            raised = None
        except Exception as e:  # noqa: BLE001
            raised = e
        assert raised is not None, f"expected 401 on {path} for anonymous request"
        code = getattr(raised, "code", None)
        # 401 from the FL gate OR 403 from the upstream edge — both
        # constitute "anonymous access blocked".
        assert code in (401, 403), (
            f"expected 401/403 on {path}, got {code}"
        )


def test_iter314_dispatch_visibility_is_today_and_tomorrow_only():
    """Operator iter314 mandate: FL sees only today+tomorrow."""
    tok = _fl_token()
    r = requests.get(
        f"{URL}/api/field-leadership/portal/dispatch-today",
        headers={"X-FL-Token": tok},
        timeout=10,
    )
    assert r.status_code == 200
    body = r.json()
    window = body.get("window") or {}
    assert "today" in window and "tomorrow" in window
    # The route ITSELF must hardcode the 2-day window (lock against drift).
    src = FL_PORTAL_ROUTES.read_text()
    assert "today + timedelta(days=1)" in src, (
        "dispatch-today route must compute today + 1 day window in-route"
    )
    assert 'target_dates = [today.isoformat(), tomorrow.isoformat()]' in src, (
        "dispatch-today must filter on the today/tomorrow date list only"
    )
    # Forbid widening to a week or month.
    assert "timedelta(days=7" not in src, "FL dispatch must not show a week"
    assert "timedelta(days=30" not in src, "FL dispatch must not show a month"


def test_iter314_driver_qualification_proxy_is_readonly():
    """FL driver-qualification is read-only — no write surface."""
    tok = _fl_token()
    r = requests.get(
        f"{URL}/api/field-leadership/portal/driver-qualification?limit=3",
        headers={"X-FL-Token": tok},
        timeout=10,
    )
    assert r.status_code == 200
    body = r.json()
    assert "items" in body and "count" in body
    # No POST/PATCH/DELETE handler is registered for this path.
    src = FL_PORTAL_ROUTES.read_text()
    # Only one route declaration for driver-qualification.
    assert src.count(
        '"/field-leadership/portal/driver-qualification"'
    ) == 1, "driver-qualification surface must remain read-only (single GET)"
    assert '@router.post(\n        "/field-leadership/portal/driver-qualification"' not in src
    assert '@router.delete(\n        "/field-leadership/portal/driver-qualification"' not in src


def test_iter314_change_password_flow():
    """Login → change-password → login back works end-to-end."""
    tok = _fl_token()
    temp = "Iter314Temp!Z9"
    # Change to temp
    r = requests.post(
        f"{URL}/api/field-leadership/portal/change-password",
        headers={"X-FL-Token": tok},
        json={"current_password": FL_PASSWORD, "new_password": temp},
        timeout=10,
    )
    assert r.status_code == 200, r.text
    new_tok = r.json().get("token") or ""
    assert new_tok and new_tok != tok, "change-password must rotate the token"
    # Old token must be invalidated by the password_hash change.
    r2 = requests.get(
        f"{URL}/api/field-leadership/portal/me",
        headers={"X-FL-Token": tok},
        timeout=10,
    )
    assert r2.status_code == 401, "old FL token must die after password rotation"
    # Login with the new password works.
    r3 = requests.post(
        f"{URL}/api/field-leadership/portal/login",
        json={"email": FL_EMAIL, "password": temp},
        timeout=10,
    )
    assert r3.status_code == 200
    # Restore original password so the rest of the suite + the docs stay valid.
    rotate_tok = r3.json().get("token")
    r4 = requests.post(
        f"{URL}/api/field-leadership/portal/change-password",
        headers={"X-FL-Token": rotate_tok},
        json={"current_password": temp, "new_password": FL_PASSWORD},
        timeout=10,
    )
    assert r4.status_code == 200


# ---------------------------------------------------------------------------
# Boundary enforcement — FL token MUST NOT unlock HR/Admin/payroll/system.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "method,path",
    [
        ("GET", "/api/admin/field-leadership-users"),
        ("GET", "/api/admin/hr-users"),
        ("GET", "/api/admin/shop-users"),
        ("GET", "/api/admin/safety-users"),
        ("GET", "/api/admin/dispatch-users"),
        ("GET", "/api/hr/employee-accountability?employee=test"),
        ("GET", "/api/hr/time-verification"),
        ("GET", "/api/hr/payroll-variance/snapshots"),
    ],
)
def test_iter314_fl_token_cannot_access_admin_or_hr_routes(method, path):
    """A Field Leadership token must NOT unlock admin/HR/payroll routes,
    even when sent in the corresponding header slot."""
    tok = _fl_token()
    headers = {
        "X-FL-Token": tok,
        "X-Admin-Token": tok,
        "X-HR-Token": tok,
        "X-Safety-Token": tok,
        "X-Shop-Token": tok,
        "X-Dispatch-Token": tok,
    }
    # Bypass conftest's admin-token injection by stripping it explicitly:
    # use a fresh Session that the patched code path will still touch, then
    # overwrite the X-Admin-Token to be the FL token so this test reflects
    # the actual security boundary (admin token slot ≠ FL token slot).
    r = requests.request(method, f"{URL}{path}", headers=headers, timeout=10)
    assert r.status_code == 401, (
        f"{method} {path} returned {r.status_code} with an FL token — "
        "Field Leadership identity must NOT unlock admin/HR/payroll surfaces"
    )


def test_iter314_legacy_shared_password_gate_untouched():
    """Legacy /api/field-leadership/login document gate still works."""
    r = requests.post(
        f"{URL}/api/field-leadership/login",
        json={"password": "MASCIGC"},
        timeout=10,
    )
    assert r.status_code == 200, (
        "iter314 must NOT touch the legacy shared-password "
        "/api/field-leadership/login gate"
    )
    body = r.json()
    assert "token" in body, "legacy gate must still return a session token"
    assert "expires_in_s" in body, "legacy gate must still return the TTL"
    assert isinstance(body["token"], str) and len(body["token"]) >= 32


# ---------------------------------------------------------------------------
# Static-code invariants — lock the architectural separation.
# ---------------------------------------------------------------------------


def test_iter314_backend_module_present():
    """Backend module + portal router must exist."""
    assert FL_BACKEND_MOD.exists(), "missing field_leadership_users.py"
    assert FL_PORTAL_ROUTES.exists(), "missing routes/field_leadership_portal.py"
    src = FL_BACKEND_MOD.read_text()
    # Allowed roles set is bounded.
    assert "ALLOWED_FL_ROLES" in src
    for role in ("Superintendent", "Foreman", "Truck Boss",
                 "Working Supervisor", "Field Supervisor"):
        assert f'"{role}"' in src, f"missing allowed role {role!r}"


def test_iter314_portal_routes_use_distinct_prefix():
    """New portal MUST live at /field-leadership/portal/* — not the legacy
    /field-leadership/login path."""
    src = FL_PORTAL_ROUTES.read_text()
    assert '"/field-leadership/portal/login"' in src
    assert '"/field-leadership/portal/change-password"' in src
    assert '"/field-leadership/portal/me"' in src
    assert '"/field-leadership/portal/dispatch-today"' in src
    assert '"/field-leadership/portal/driver-qualification"' in src
    # Do NOT register the legacy path here.
    assert '"/field-leadership/login"' not in src, (
        "new portal must not collide with the legacy shared-password gate"
    )


def test_iter314_admin_routes_share_hr_or_admin_gate():
    """Every /admin/field-leadership-users* route must use require_hr_or_admin."""
    src = FL_PORTAL_ROUTES.read_text()
    # All five admin endpoints must list the require_hr_or_admin dependency.
    admin_routes = re.findall(
        r'@router\.(?:get|post|patch|delete)\(\s*\n?\s*"/admin/field-leadership-users[^"]*",\s*\n?\s*dependencies=\[Depends\((\w+)\)\]',
        src,
    )
    assert admin_routes, "no /admin/field-leadership-users routes registered"
    for dep in admin_routes:
        assert dep == "require_hr_or_admin", (
            f"admin route is gated by {dep!r} — must be require_hr_or_admin"
        )


def test_iter314_frontend_routes_wired():
    """Frontend must mount the FL portal pages under RequireFl + keep the
    legacy /field-leadership redirect untouched."""
    assert APP_JS.exists()
    src = APP_JS.read_text()
    assert 'path="/field-leadership/portal/login"' in src
    assert 'path="/field-leadership/portal/change-password"' in src
    assert 'path="/field-leadership/portal/dashboard"' in src
    # Dashboard + change-password go through the FL guard.
    assert 'element={FL(<FieldLeadershipPortalDashboard />)}' in src
    assert 'element={FL(<FieldLeadershipPortalChangePassword />)}' in src
    # Login is public (no guard).
    assert 'element={<FieldLeadershipPortalLogin />}' in src
    # Legacy redirect from /field-leadership stays in place (does NOT route
    # to the new portal — preserves the shared-password gate behavior).
    assert '<Route path="/field-leadership"' in src
    assert 'to="/leadership"' in src


def test_iter314_require_fl_redirects_to_new_portal_login():
    """The route guard must send unauthenticated users to the NEW portal
    login, not to the legacy gate."""
    src = REQUIRE_FL.read_text()
    assert '"/field-leadership/portal/login"' in src
    assert '"/field-leadership/login"' not in src, (
        "RequireFl must NOT redirect to the legacy shared-password gate"
    )


def test_iter314_admin_panel_mounted_in_admin_people():
    """AdminPeople must mount AdminFieldLeadershipUsersPanel so admin can
    manage Field Leadership identities."""
    src = ADMIN_PEOPLE.read_text()
    assert "AdminFieldLeadershipUsersPanel" in src
    assert "<AdminFieldLeadershipUsersPanel" in src


def test_iter314_hr_hub_exposes_field_leadership_users_tile():
    """HR Hub must surface the management tile linking to the panel.

    The tile is intentionally adjacent to the existing Field Leadership
    Records tile and uses a label distinct from it ("Portal Accounts")
    so HR users can find the user-management surface unambiguously
    (iter315 visibility closure)."""
    src = HR_HUB.read_text()
    assert '/hr/field-leadership-users' in src
    assert 'Field Leadership Portal Accounts' in src


def test_iter314_hr_field_leadership_users_page_renders_panel():
    """The HR-side host page must render the shared management panel."""
    assert HR_FL_USERS_PAGE.exists(), "HrFieldLeadershipUsers.jsx must exist"
    src = HR_FL_USERS_PAGE.read_text()
    assert "AdminFieldLeadershipUsersPanel" in src
    assert "<AdminFieldLeadershipUsersPanel" in src


def test_iter314_admin_panel_targets_admin_route_namespace():
    """The shared panel must call the bounded admin/field-leadership-users
    route — never any made-up new namespace."""
    src = FL_USERS_PANEL.read_text()
    assert '"/admin/field-leadership-users"' in src
    # Forbid drift into HR/Safety/Shop namespaces.
    for forbidden in (
        '"/admin/hr-users"',
        '"/admin/safety-users"',
        '"/admin/shop-users"',
    ):
        assert forbidden not in src, (
            f"FL users panel must not call {forbidden}"
        )


def test_iter314_fl_login_uses_correct_i18n_signature():
    """The login welcome toast must NOT call t() with an unsupported
    interpolation object (the `useT()` hook only accepts a single key)."""
    src = FL_LOGIN_PAGE.read_text()
    assert "Welcome, {name}" not in src, (
        "login toast must not use a non-interpolating t('Welcome, {name}', ...) "
        "literal — the useT hook does not perform placeholder substitution"
    )
