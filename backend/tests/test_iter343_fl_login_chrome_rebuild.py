"""
test_iter343_fl_login_chrome_rebuild.py — Regression lock for iter343.

The iter342 fix routed /leadership/login to the modern per-user form, but
the form itself was a generic centered card that did NOT match the
HR / Safety / PM / Shop / Dispatch login chrome. Operator flagged:
visually different, partial ES, no admin-aware path, no Remember-me,
no PortalLoginHelp section, footer/layout off, super-admin behavior
undocumented.

iter343 rebuilds FieldLeadershipPortalLogin.jsx to mirror HrLogin.jsx
STRUCTURALLY — same blueprint-bg + caution-stripe + slate-900 header,
same MasciLogo placement, same card chrome, same form pattern + button
rhythm + footer + PortalLoginHelp + Remember-me checkbox + admin-aware
helper banner + complete ES translations.

This regression locks every chrome contract.
"""
from pathlib import Path

ROOT = Path("/app")
FL = ROOT / "frontend/src/pages/FieldLeadershipPortalLogin.jsx"
HR = ROOT / "frontend/src/pages/HrLogin.jsx"
I18N = ROOT / "frontend/src/lib/i18n.js"
APP_JS = ROOT / "frontend/src/App.js"


def test_fl_login_uses_blueprint_bg_and_caution_stripe():
    src = FL.read_text()
    assert 'blueprint-bg flex flex-col' in src, "must use blueprint background"
    assert 'caution-stripe' in src, "must include caution-stripe band"


def test_fl_login_uses_slate900_header_with_red_accent():
    src = FL.read_text()
    assert 'bg-slate-900 border-b-4 border-red-700' in src, \
        "header must use platform-standard slate-900 + portal-palette accent"
    assert 'max-w-6xl mx-auto px-5 sm:px-8 py-4' in src, \
        "header inner must use HR-pattern max-w-6xl rhythm"


def test_fl_login_has_masci_logo_with_dual_size():
    src = FL.read_text()
    assert 'MasciLogo variant="mark" size="lg" className="hidden sm:block"' in src
    assert 'MasciLogo variant="mark" size="md" className="sm:hidden"' in src


def test_fl_login_has_lang_toggle_in_header():
    src = FL.read_text()
    # LangToggle imported AND used inside the header (not just at top)
    assert 'import { LangToggle }' in src
    # appears inside header block
    header_block = src.split('<header', 1)[1].split('</header>', 1)[0]
    assert '<LangToggle' in header_block, "LangToggle must live inside header"


def test_fl_login_form_uses_hr_pattern_inputs():
    """h-12 inputs with mail icon prefix + border-2 focus ring red."""
    src = FL.read_text()
    assert 'h-12 pl-9 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-red-700' in src
    assert 'Mail className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none"' in src


def test_fl_login_has_remember_me_checkbox():
    src = FL.read_text()
    assert 'data-testid="fl-remember-me"' in src
    assert 'accent-red-700' in src
    assert 'Remember me on this device' in src


def test_fl_login_uses_full_width_uppercase_submit_button():
    """Same h-12 uppercase tracking-wide pattern as HR's purple-700 button."""
    src = FL.read_text()
    assert 'w-full h-12 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-sm border-b-2 border-red-900' in src


def test_fl_login_mounts_portal_login_help():
    """The HR/PM/Shop/Safety/Dispatch login screens all surface PortalLoginHelp.
    FL must too — same operational onboarding/troubleshooting links."""
    src = FL.read_text()
    assert 'import { PortalLoginHelp }' in src
    assert '<PortalLoginHelp portal="leadership"' in src


def test_fl_login_has_admin_aware_helper_block():
    """Operators asked: clearly document what Admin should do here.
    Solution: when an admin token is detected, show a calm helper that
    routes them straight to the Hub (which their token already
    satisfies via isAdmin())."""
    src = FL.read_text()
    assert 'data-testid="fl-admin-aware"' in src
    assert 'data-testid="fl-admin-continue"' in src
    assert "You're already signed in as Admin" in src


def test_fl_login_has_forgot_password_dialog():
    src = FL.read_text()
    assert 'data-testid="fl-forgot-dialog"' in src
    assert 'data-testid="fl-forgot-submit"' in src
    assert 'data-testid="fl-forgot-email"' in src
    # Posts to the correct backend endpoint
    assert '"/field-leadership/portal/forgot-password"' in src


def test_fl_login_has_legacy_disclosure_link():
    src = FL.read_text()
    assert 'data-testid="fl-legacy-login-link"' in src
    assert 'to="/leadership/legacy-login"' in src


def test_fl_login_has_platform_standard_footer():
    src = FL.read_text()
    # Same footer rhythm as HrLogin: max-w-6xl, py-6, mono kicker, ForgedOps
    assert 'footer className="max-w-6xl mx-auto px-5 sm:px-8 py-6 flex flex-col items-center gap-3"' in src
    assert 'MASCI · Field Leadership Portal' in src
    assert 'ForgedOpsAttribution variant="login"' in src
    # Footer must appear exactly ONCE (no double-footer regression)
    assert src.count('<footer') == 1


def test_fl_login_uses_calm_error_sanitizer():
    src = FL.read_text()
    assert 'from "@/lib/errors"' in src
    assert 'operationalError' in src


def test_es_translations_complete_for_fl_login():
    src = I18N.read_text()
    required_es = [
        ('"Field Leadership"', '"Liderazgo de Campo"'),
        ('"Field Leadership Sign In"', '"Inicio de Sesión · Liderazgo de Campo"'),
        ('"Work Email"',),  # already present from HR, just confirm it exists
        ('"Remember me on this device"',),
        ('"Forgot password?"',),
        ('"Sign In"',),
        ('"Invalid email or password"', '"Correo o contraseña incorrectos"'),
        ('"You\'re already signed in as Admin"', '"Ya iniciaste sesión como Admin"'),
        ('"Continue to Field Leadership Hub"', '"Continuar al Centro de Liderazgo de Campo"'),
        ('"MASCI · Field Leadership Portal"', '"MASCI · Portal de Liderazgo de Campo"'),
        ('"Crew using a shared leadership code? Use the legacy gate →"',
         '"¿Tu cuadrilla usa un código compartido? Usa el acceso heredado →"'),
    ]
    for entry in required_es:
        if len(entry) == 2:
            en_key, es_value = entry
            # Pairs must appear together: "EN_KEY": "ES_VALUE"
            assert f'{en_key}: {es_value}' in src, f"missing pair: {en_key} → {es_value}"
        else:
            assert entry[0] in src, f"missing ES key: {entry[0]}"


def test_route_mounting_unchanged():
    """iter342 routing held — /leadership/login still mounts the modern form."""
    src = APP_JS.read_text()
    assert '<Route path="/leadership/login" element={<FieldLeadershipPortalLogin />} />' in src
    assert '<Route path="/leadership/legacy-login" element={<LeadershipLogin />} />' in src
