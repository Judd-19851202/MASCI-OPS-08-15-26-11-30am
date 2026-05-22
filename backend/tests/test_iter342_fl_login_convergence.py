"""
test_iter342_fl_login_convergence.py — Regression lock for iter342.

The operator P0 complaint: /leadership/login showed a legacy single
shared-password gate ("MASCIGC password"), while every other portal
(HR, Safety, PM, Shop, Dispatch) had modern email+password flow.
The modern per-user FL portal (iter314, FieldLeadershipPortalLogin.jsx)
existed but lived at the secondary URL /field-leadership/portal/login,
so the operator never reached it from natural navigation.

iter342 fix (no destructive changes):
  - /leadership/login now mounts FieldLeadershipPortalLogin (modern)
  - Legacy LeadershipLogin moved to /leadership/legacy-login (hidden compat)
  - FieldLeadershipHub gate now accepts FL token in addition to
    leadership/admin/PM tokens
  - Successful per-user FL login lands directly in the Hub
  - Backend /api/field-leadership/login route + lib/leadershipAuth.js
    untouched (zero backend / auth-helper changes)
  - i18n EN+ES strings for the legacy-disclosure link
"""
from pathlib import Path

ROOT = Path("/app")
APP_JS = ROOT / "frontend/src/App.js"
HUB = ROOT / "frontend/src/pages/FieldLeadershipHub.jsx"
MODERN_LOGIN = ROOT / "frontend/src/pages/FieldLeadershipPortalLogin.jsx"
LEGACY_LOGIN = ROOT / "frontend/src/pages/LeadershipLogin.jsx"
I18N = ROOT / "frontend/src/lib/i18n.js"
LEADERSHIP_AUTH = ROOT / "frontend/src/lib/leadershipAuth.js"
FL_AUTH = ROOT / "frontend/src/lib/flAuth.js"
FL_PORTAL_ROUTES = ROOT / "backend/routes/field_leadership.py"


def test_primary_route_now_renders_modern_login():
    src = APP_JS.read_text()
    assert (
        '<Route path="/leadership/login" element={<FieldLeadershipPortalLogin />} />'
        in src
    ), "modern per-user login is not mounted at /leadership/login"


def test_legacy_login_still_reachable_at_hidden_url():
    src = APP_JS.read_text()
    assert (
        '<Route path="/leadership/legacy-login" element={<LeadershipLogin />} />'
        in src
    ), "legacy shared-password gate must still be reachable at /leadership/legacy-login"


def test_secondary_url_still_works():
    """The original /field-leadership/portal/login URL must keep working
    so existing bookmarks / direct links continue to resolve."""
    src = APP_JS.read_text()
    assert (
        '<Route path="/field-leadership/portal/login" element={<FieldLeadershipPortalLogin />} />'
        in src
    )


def test_hub_accepts_fl_token():
    src = HUB.read_text()
    assert 'import { getFlToken, clearFlToken } from "@/lib/flAuth";' in src
    # Both useState initializer + useEffect re-check accept FL token
    assert src.count("getFlToken()") >= 2


def test_hub_signout_clears_both_tokens():
    src = HUB.read_text()
    # clearLeadershipToken + clearFlToken both called in signOut
    so_block = src.split("const signOut = () => {", 1)[1].split("};", 1)[0]
    assert "clearLeadershipToken()" in so_block
    assert "clearFlToken()" in so_block


def test_modern_login_post_success_navigates_to_hub():
    src = MODERN_LOGIN.read_text()
    # Success path now lands in the Hub directly.
    assert 'navigate("/leadership", { replace: true });' in src
    # must_change_password path still goes to change-password screen.
    assert 'navigate("/field-leadership/portal/change-password"' in src


def test_modern_login_has_legacy_disclosure_link():
    src = MODERN_LOGIN.read_text()
    assert 'data-testid="fl-legacy-login-link"' in src
    assert 'to="/leadership/legacy-login"' in src
    assert "Crew using a shared leadership code? Use the legacy gate" in src


def test_es_translation_for_disclosure_link():
    src = I18N.read_text()
    assert "¿Tu cuadrilla usa un código compartido?" in src
    assert "Crew using a shared leadership code? Use the legacy gate →" in src


def test_backend_legacy_login_route_untouched():
    """Backwards compatibility — the shared-password backend route must
    still exist so the legacy gate continues to work for crews that
    only know the shared code."""
    src = FL_PORTAL_ROUTES.read_text()
    assert '@router.post("/login")' in src


def test_leadership_auth_helper_untouched():
    """lib/leadershipAuth.js is the legacy compat surface — no rewrite."""
    src = LEADERSHIP_AUTH.read_text()
    assert "export async function loginLeadership" in src
    # Still posts to the shared-password backend route
    assert '/field-leadership/login' in src


def test_fl_auth_helper_supports_token_read():
    """The modern per-user FL token lib must expose getFlToken (used by
    the Hub gate to recognize per-user sessions)."""
    src = FL_AUTH.read_text()
    assert "export function getFlToken" in src or "export const getFlToken" in src
