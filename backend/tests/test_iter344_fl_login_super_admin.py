"""
test_iter344_fl_login_super_admin.py — Regression lock for iter344.

The operator's P0 complaint after iter343: super-admin credentials
(`jaymn.judd@mascigc.com` / `Maddix123!`) still failed at the FL login
form with "Invalid email or password". The operator's expectation:
super-admin should access ANY portal, including FL.

iter344 fix:
  - Backend FL portal login now falls back to `user_directory` auth
    when the per-user FL lookup fails. If the directory user has the
    `admin` portal grant, an admin token (same format as /api/admin/*)
    is minted and returned with `kind:"admin"`.
  - Frontend reads `kind` from response: if `admin`, stores via
    `setAdminToken()`; otherwise stores via `setFlToken()`.
  - Hub gate already accepts admin tokens via `isAdmin()` (since iter342).
  - No duplicate identity. No new collection. RBAC boundary preserved
    (only `admin` portal grant unlocks the fallback; HR-only / PM-only /
    Dispatch-only directory users still get 401).

This regression locks the contract.
"""
from pathlib import Path

ROOT = Path("/app")
FL_PORTAL = ROOT / "backend/routes/field_leadership_portal.py"
SERVER = ROOT / "backend/server.py"
FL_LOGIN_JSX = ROOT / "frontend/src/pages/FieldLeadershipPortalLogin.jsx"


def test_backend_fl_portal_login_accepts_directory_admin_minter():
    src = FL_PORTAL.read_text()
    # Builder signature must accept directory_admin_minter
    assert "directory_admin_minter: Optional[Callable] = None" in src
    # The login route must reference it
    assert "if directory_admin_minter is not None:" in src


def test_backend_fl_login_falls_back_to_user_directory():
    src = FL_PORTAL.read_text()
    # Falls back to user_directory.authenticate
    assert "import user_directory as _ud" in src
    assert "await _ud.authenticate(db, email=email, password=payload.password)" in src
    # Only admins (not HR/PM/Safety/Dispatch/Shop-only) bypass via Path 2.
    # iter345 · Phase B Hybrid landed Path 3 below this check, so the
    # admin gate now reads `row_portals` (set after the unified
    # disabled-check). Both shapes are valid.
    assert (
        '"admin" in (row.get("portals") or [])' in src
        or '"admin" in row_portals' in src
    )
    # Returns kind:"admin" so frontend knows which token domain
    assert '"kind": "admin"' in src
    # FL happy path returns kind:"fl"
    assert '"kind": "fl"' in src


def test_server_wires_lazy_directory_admin_minter():
    """server.py builds _fl_portal_router BEFORE _directory_admin_token is
    defined (line ~9157 vs ~10510). A lazy lambda wrapper defers name
    resolution to call time."""
    src = SERVER.read_text()
    assert "directory_admin_minter=lambda row: _directory_admin_token(row)" in src


def test_frontend_handles_admin_kind_response():
    src = FL_LOGIN_JSX.read_text()
    # Imports the admin-token setter
    assert "setAdminToken" in src
    # Reads kind from response
    assert 'const kind = r?.data?.kind || "fl";' in src
    # Branches on kind
    assert 'if (kind === "admin")' in src
    # Stores admin token correctly
    assert "setAdminToken(tok, { remember: rememberMe })" in src
    # FL branch still stores FL token + user
    assert "setFlToken(tok, rememberMe)" in src
    assert "setFlUser(user)" in src


def test_frontend_welcomes_admin_with_admin_label():
    """Welcome toast should adapt — Admin sees 'Admin', FL user sees 'Field Leader'."""
    src = FL_LOGIN_JSX.read_text()
    assert '${t("Welcome,")} ${user?.name || t("Admin")}' in src
    assert '${t("Welcome,")} ${user?.name || t("Field Leader")}' in src


def test_no_duplicate_fl_identity_created_for_admin():
    """Admin path must NOT call setFlToken / setFlUser / mint an FL
    identity. The Hub gate accepts admin via isAdmin() — no duplicate."""
    src = FL_LOGIN_JSX.read_text()
    # Extract the admin branch
    admin_block = src.split('if (kind === "admin") {', 1)[1].split('} else {', 1)[0]
    assert "setFlToken" not in admin_block, "admin branch must not mint FL identity"
    assert "setFlUser" not in admin_block, "admin branch must not write FL user"
