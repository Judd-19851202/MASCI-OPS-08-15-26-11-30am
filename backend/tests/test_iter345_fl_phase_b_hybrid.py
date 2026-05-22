"""
test_iter345_fl_phase_b_hybrid.py — Regression lock for iter345.

FL Phase B · Hybrid · cross-portal Field Leadership grants.

Implements OPTION C (Hybrid) per operator approval:
  1. `field_leadership` added to user_directory.ALLOWED_PORTALS
  2. Admin Access Control panel shows 7th column (Field Leadership)
  3. Multi-login mints X-FL-Token when user has `field_leadership` grant
  4. FL backend Path 3 — if Path 1 (native FL user) fails and Path 2
     (admin fallback) doesn't apply, a directory user with the
     `field_leadership` grant can authenticate with their MASTER
     directory password and receive an X-FL-Token (single password
     cascade per policy 1a)
  5. FL token validator extended to verify directory-granted tokens
     against `user_directory.password_hash` (so password resets cascade)
  6. NO duplicate field_leadership_users row created for directory grants
  7. Native FL users (field_leadership_users) still work unchanged
  8. Identity mirror still excludes FL (no accidental promotion)
  9. HR FL Users panel keeps advisory note
"""
from pathlib import Path

ROOT = Path("/app")
UD = ROOT / "backend/user_directory.py"
AUTH_DIR = ROOT / "backend/routes/auth_directory_routes.py"
FL_PORTAL = ROOT / "backend/routes/field_leadership_portal.py"
FL_USERS_LIB = ROOT / "backend/field_leadership_users.py"
SERVER = ROOT / "backend/server.py"
ADMIN_PANEL = ROOT / "frontend/src/components/AdminAccessControlPanel.jsx"
HR_PANEL = ROOT / "frontend/src/components/AdminFieldLeadershipUsersPanel.jsx"
IDENTITY_MIRROR = ROOT / "backend/lib/identity_mirror.py"


def test_field_leadership_in_allowed_portals():
    src = UD.read_text()
    assert (
        'ALLOWED_PORTALS = ("admin", "pm", "shop", "hr", "safety", "dispatch", "field_leadership")'
        in src
    )


def test_multi_login_accepts_fl_minter_param():
    src = AUTH_DIR.read_text()
    # New minter parameter in build function
    assert "field_leadership_token_minter: Optional[Callable" in src
    # Branch that mints FL token when grant present
    assert '"field_leadership" in portals and field_leadership_token_minter:' in src
    assert 'tokens["field_leadership"] = await _maybe_await(field_leadership_token_minter(row))' in src
    # session_timeout tier map includes FL
    assert '"field_leadership": "ADMIN_FL"' in src


def test_server_wires_directory_fl_minter():
    src = SERVER.read_text()
    assert "def _directory_fl_token(row: Dict[str, Any])" in src
    assert "field_leadership_token_minter=_directory_fl_token" in src
    # Mints same X-FL-Token format that FL routes accept
    assert "make_fl_user_token(uid, pwh)" in src


def test_fl_portal_login_has_path_3():
    src = FL_PORTAL.read_text()
    # Path 3 branch
    assert 'if "field_leadership" in row_portals:' in src
    # Mints X-FL-Token bound to master password_hash (single-pw cascade)
    assert 'fl_tok = make_fl_user_token(row["id"], pwh)' in src
    # Returns kind:"fl" so frontend stores via setFlToken
    assert '"ok": True, "token": fl_tok, "kind": "fl"' in src
    # Exposes "directory_user" + "granted_portals" in user object
    assert '"directory_user": True' in src
    assert '"granted_portals": pub.get("portals") or []' in src
    # Role label for cross-portal users
    assert '"role": "Cross-Portal Grant"' in src
    # Disabled directory users blocked
    assert "not row.get(\"disabled\")" in src


def test_fl_token_validator_accepts_directory_users():
    """is_valid_fl_user_token_async must validate directory-granted FL
    tokens by looking up user_directory when the embedded id isn't in
    field_leadership_users."""
    src = FL_USERS_LIB.read_text()
    assert 'dir_user = await db.user_directory.find_one({"id": user_id}, {"_id": 0})' in src
    assert '"field_leadership" not in (dir_user.get("portals") or [])' in src
    # Verifies HMAC against the directory password_hash
    expected_block = src.split('dir_user = await db.user_directory.find_one', 1)[1]
    assert "expected = make_fl_user_token(user_id, pwh)" in expected_block
    assert "hmac.compare_digest(token, expected)" in expected_block
    # Returns FL-shaped view with _directory_user flag
    assert '"_directory_user": True' in src
    assert '"role": "Cross-Portal Grant"' in src


def test_admin_access_control_has_seven_portals():
    src = ADMIN_PANEL.read_text()
    # 7 PORTAL_OPTIONS entries
    assert 'key: "field_leadership"' in src
    assert 'label: "Field Leadership"' in src
    # Old 6 still present
    for key in ('"admin"', '"pm"', '"shop"', '"hr"', '"safety"', '"dispatch"'):
        assert f'key: {key}' in src


def test_hr_fl_panel_has_advisory_note():
    src = HR_PANEL.read_text()
    assert 'data-testid="fl-users-cross-portal-advisory"' in src
    assert "Admin Access Control" in src
    assert "/leadership/login" in src


def test_identity_mirror_still_excludes_fl():
    """We do NOT auto-mirror legacy field_leadership_users into
    user_directory (avoids accidental mass promotion). Phase B grants
    must be explicit Admin action."""
    src = IDENTITY_MIRROR.read_text()
    # Mirror still does NOT include field_leadership in its source
    # collections list — Phase K7 comment present
    assert "Phase K7" in src or "leadership portal is intentionally absent" in src


def test_native_fl_users_path_unchanged():
    """Path 1 (native field_leadership_users) must remain the first
    authentication attempt — no regression for existing FL users."""
    src = FL_PORTAL.read_text()
    # Path 1 comment block + lookup before any fallback
    assert "Path 1 · per-user FL identity (field_leadership_users)" in src
    # Path 1 returns kind:"fl" for native users
    assert '"ok": True, "token": token, "kind": "fl"' in src
    # The native path uses find_fl_user_by_email (field_leadership_users)
    assert "find_fl_user_by_email(db, email)" in src
