"""TRACK 15.87 · Multi-Portal Access Authority Fix · regression suite.

Locks the P0 directory-grant → portal-login contract introduced by
Track 15.87. Twenty regression tests that cover:

  * One canonical helper exists (``lib/directory_portal_login.py``).
  * Every portal-login endpoint imports it.
  * Every directory portal minter is wired into its router builder.
  * No RBAC weakening: granting Shop does NOT unlock PM, etc.
  * Disabled users / must_change_password users do NOT receive tokens.
  * The retired ``_is_valid_admin_token`` Track 15.32 lock is intact.

These are pure source-level static checks — no DB writes, no live
auth probes — so they run in <100 ms inside the deployment gate.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

BACKEND = Path("/app/backend")
HELPER_PATH = BACKEND / "lib" / "directory_portal_login.py"


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


# ─── 1. Canonical helper exists + has the right shape ────────────


def test_directory_portal_login_helper_exists():
    assert HELPER_PATH.exists(), (
        "Track 15.87: lib/directory_portal_login.py must exist — it "
        "is the single canonical helper that lets every per-portal "
        "login endpoint accept a directory-granted user."
    )


def test_helper_exposes_try_directory_portal_login():
    src = _read(HELPER_PATH)
    assert "async def try_directory_portal_login" in src, (
        "Track 15.87: helper must expose async "
        "`try_directory_portal_login`."
    )


def test_helper_requires_portal_in_directory_portals_array():
    """The helper must verify the directory user has the
    ``required_portal`` key in their ``portals`` array — granting
    Shop must NOT unlock PM (no over-grant)."""
    src = _read(HELPER_PATH)
    assert "if required_portal not in portals:" in src, (
        "Track 15.87 P0 RBAC: helper must reject directory users "
        "whose `portals` array does NOT include `required_portal`. "
        "Otherwise granting Shop would unlock PM (role escalation)."
    )


def test_helper_rejects_disabled_directory_users():
    src = _read(HELPER_PATH)
    assert 'if row.get("disabled"):' in src, (
        "Track 15.87: disabled directory users MUST NOT receive a "
        "portal token via the new directory path."
    )


def test_helper_blocks_must_change_password_users():
    """Mirrors multi-login: a user owing a temp-password rotation
    cannot receive portal tokens until they rotate."""
    src = _read(HELPER_PATH)
    assert 'must_change_password' in src, (
        "Track 15.87: helper must mirror multi-login behaviour and "
        "block portal-token mint when must_change_password=true."
    )


def test_helper_uses_canonical_user_directory_authenticate():
    """The helper must call ``user_directory.authenticate`` — the
    same bcrypt-verifying entry point that multi-login uses. No
    duplicate password verification logic."""
    src = _read(HELPER_PATH)
    assert "_ud.authenticate(" in src, (
        "Track 15.87: helper must authenticate via "
        "`user_directory.authenticate` — the canonical bcrypt path."
    )


def test_helper_does_not_introduce_shared_admin_password_bypass():
    """No shared-admin password / HMAC bypass leaked into the new
    helper. Track 15.32's retired shared-ADMIN-PASSWORD HMAC pattern
    must stay retired."""
    src = _read(HELPER_PATH)
    for needle in ["ADMIN_PASSWORD", "MASCI1982", "shared_admin",
                   "_is_valid_admin_token"]:
        assert needle not in src, (
            f"Track 15.87 SECURITY: helper must not reference "
            f"`{needle}` — this would re-introduce the Track 15.32-"
            "retired shared-admin bypass."
        )


# ─── 2. Each portal-login endpoint calls the helper ───────────────


PORTAL_LOGIN_FILES = {
    "hr":       BACKEND / "routes" / "hr_portal.py",
    "dispatch": BACKEND / "routes" / "dispatch_portal_auth.py",
    "safety":   BACKEND / "routes" / "safety_portal" / "auth_users.py",
    "pm":       BACKEND / "routes" / "pm_routes.py",
    "shop":     BACKEND / "server.py",
}


@pytest.mark.parametrize("portal,path", PORTAL_LOGIN_FILES.items())
def test_portal_login_imports_canonical_helper(portal, path):
    src = _read(path)
    assert "try_directory_portal_login" in src, (
        f"Track 15.87: {portal} login endpoint at {path} must "
        "import + call `try_directory_portal_login` so the "
        "Admin People & Access grant produces a working login."
    )


@pytest.mark.parametrize("portal,path", PORTAL_LOGIN_FILES.items())
def test_portal_login_requires_correct_portal_key(portal, path):
    """Each login endpoint must pass its own portal key as
    ``required_portal`` — a PM endpoint requiring 'pm', not 'admin',
    not 'shop'."""
    src = _read(path)
    pat = rf'required_portal\s*=\s*"{re.escape(portal)}"'
    assert re.search(pat, src), (
        f"Track 15.87 RBAC: {portal} login endpoint must require "
        f"`required_portal=\"{portal}\"` so granting another portal "
        "does NOT unlock this one."
    )


@pytest.mark.parametrize("portal,path", PORTAL_LOGIN_FILES.items())
def test_portal_login_kind_field_matches_portal(portal, path):
    """The directory-grant fallback returns ``kind`` matching its
    portal so the SPA stores the token under the right localStorage
    key (`masci.pm.token`, `masci.shop.token`, etc.)."""
    src = _read(path)
    # Each call passes kind="<portal>" within the helper call.
    pat = rf'kind\s*=\s*"{re.escape(portal)}"'
    assert re.search(pat, src), (
        f"Track 15.87: {portal} login must pass `kind=\"{portal}\"` "
        "in its directory-grant call so the SPA routes the token to "
        f"the correct portal-specific storage key."
    )


# ─── 3. Server.py wires every per-portal minter into its router ──


SERVER = BACKEND / "server.py"


def test_hr_router_built_with_directory_portal_minter():
    src = _read(SERVER)
    assert re.search(
        r"build_hr_portal_router\(.*?directory_portal_minter\s*=\s*lambda row:\s*_directory_hr_token\(row\)",
        src, re.S,
    ), "Track 15.87: HR router must be built with directory_portal_minter wired to _directory_hr_token."


def test_dispatch_router_built_with_directory_portal_minter():
    src = _read(SERVER)
    assert re.search(
        r"build_dispatch_router\(.*?directory_portal_minter\s*=\s*lambda row:\s*_directory_dispatch_token\(row\)",
        src, re.S,
    ), "Track 15.87: Dispatch router must be built with directory_portal_minter wired to _directory_dispatch_token."


def test_safety_router_built_with_directory_portal_minter():
    src = _read(SERVER)
    assert re.search(
        r"build_safety_router\(.*?directory_portal_minter\s*=\s*lambda row:\s*_directory_safety_token\(row\)",
        src, re.S,
    ), "Track 15.87: Safety router must be built with directory_portal_minter wired to _directory_safety_token."


def test_pm_router_built_with_directory_pm_minter_fn_in_login_deps():
    src = _read(SERVER)
    assert re.search(
        r'"directory_pm_minter_fn"\s*:\s*lambda row:\s*_directory_pm_token\(row\)',
        src,
    ), "Track 15.87: PM router must be built with `directory_pm_minter_fn` wired to _directory_pm_token in login_deps."


def test_shop_login_uses_directory_shop_token_minter():
    """Shop login lives inline in server.py — verify it references
    `_directory_shop_token` in its directory fallback path."""
    src = _read(SERVER)
    # find the shop_login function and confirm the new helper call uses _directory_shop_token
    m = re.search(r"async def shop_login\(.*?@api_router\.post", src, re.S)
    assert m, "shop_login route not found"
    body = m.group(0)
    assert "_directory_shop_token" in body, (
        "Track 15.87: shop_login must use `_directory_shop_token` as "
        "its portal_token_minter in the directory-grant fallback."
    )
    assert 'required_portal="shop"' in body, (
        "Track 15.87: shop_login must require `shop` in the "
        "directory user's portals array."
    )


# ─── 4. Portal-grant ALIAS list is the canonical 7 portals ───────


def test_canonical_portal_grant_keys_remain_seven():
    src = _read(BACKEND / "user_directory.py")
    assert (
        'ALLOWED_PORTALS = ("admin", "pm", "shop", "hr", "safety", '
        '"dispatch", "field_leadership")'
    ) in src, (
        "Track 15.87: ALLOWED_PORTALS must remain the canonical 7 "
        "portal keys. Adding/renaming requires Track 15.87 follow-up."
    )


# ─── 5. Admin Console People & Access UI writes canonical keys ───


def test_access_control_panel_writes_canonical_portal_keys():
    """The Admin Console → Access Control Center UI MUST write
    canonical portal keys to /admin/directory/:id. No alias drift."""
    src = _read(BACKEND.parent / "frontend" / "src" /
                "components" / "AdminAccessControlPanel.jsx")
    # Locate the PORTAL_OPTIONS array and assert canonical keys.
    for key in ["admin", "pm", "shop", "hr", "safety", "dispatch",
                "field_leadership"]:
        assert f'key: "{key}"' in src, (
            f"Track 15.87: AdminAccessControlPanel must keep canonical "
            f"PORTAL_OPTIONS entry for `{key}`. Drift here would write "
            "a non-canonical grant the backend cannot honor."
        )
    # Sanity: writes to PATCH /admin/directory/{id} with `{portals: [...]}`.
    assert "/admin/directory/${user.id}" in src and "portals: next" in src, (
        "Track 15.87: AdminAccessControlPanel must PATCH "
        "/admin/directory/{id} with `{portals: <array>}`."
    )


# ─── 6. Retired Track 15.32 admin-token stub stays hard-False ─────


def test_track_15_32_retired_admin_stub_preserved():
    """Track 15.87 must NOT touch the Track 15.32 retired-stub
    security lock — `_is_valid_admin_token` remains hard-False."""
    import sys
    sys.path.insert(0, str(BACKEND))
    from server import _is_valid_admin_token as fn  # type: ignore
    for tok in (None, "", "anything", "ADMIN", "MASCI1982"):
        assert fn(tok) is False, (
            f"Track 15.87 P0 SECURITY REGRESSION: "
            f"_is_valid_admin_token({tok!r}) returned True — Track "
            "15.32 retired this. Track 15.87 must not re-enable it."
        )


# ─── 7. Multi-login still uses portals array (no regression) ─────


def test_multi_login_still_reads_directory_portals():
    src = _read(BACKEND / "routes" / "auth_directory_routes.py")
    assert 'portals = set(row.get("portals") or [])' in src, (
        "Track 15.87: multi-login must still read the canonical "
        "`portals` array — Track 15.87 extends per-portal logins "
        "with the SAME contract."
    )


# ─── 8. Track 15.85 / 15.86 regression files preserved ───────────


def test_track_15_85_and_15_86_test_files_still_present():
    for needle in [
        "test_track_15_85_mandatory_full_platform_certification.py",
        "test_track_15_86_browser_smoke_gate.py",
    ]:
        p = BACKEND / "tests" / needle
        assert p.exists(), (
            f"Track 15.87: Track 15.85/15.86 regression file `{needle}` "
            "must remain in place — Track 15.87 extends, not replaces."
        )


# ─── 9. Helper is referenced by the deployment gate ──────────────


def test_track_15_87_wired_into_deployment_gate():
    gate = _read(BACKEND.parent / "scripts" / "deployment_gate.py")
    assert "test_track_15_87" in gate, (
        "Track 15.87: scripts/deployment_gate.py must include the "
        "Track 15.87 regression file in REGRESSION_FILES."
    )
