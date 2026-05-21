"""iter322-B · Workflow Continuity Wiring Completion.

The previous iter322 added the PortalContextBanner + AuthRequiredBanner
components but did NOT wire them through the `<Require*>` guards.
Operator feedback confirmed: Safety Hub → Incidents/Audits/Training
STILL felt like a cold-login wall because:
- guards passed only `state.from`, not `state.continuity`
- login pages did not render AuthRequiredBanner
- Safety + Dispatch login did not honor `state.from` post-login redirect

iter322-B closes that wiring:
- `lib/portalContinuity.js` builds rich continuity descriptors from a
  protected-path URL (workflow label · role · returnTo · continueTo).
- All 6 `<Require*>` guards attach the descriptor to navigation state.
- All 6 portal login pages render <AuthRequiredBanner /> + honor the
  intended-destination redirect after successful auth.
- Bilingual gate satisfied for all new copy.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
FRONTEND = ROOT / "frontend/src"
HELPER = FRONTEND / "lib/portalContinuity.js"
BANNER = FRONTEND / "components/PortalContextBanner.jsx"
I18N = FRONTEND / "lib/i18n.js"

GUARDS = [
    "RequireSafety.jsx",
    "RequireHr.jsx",
    "RequireShop.jsx",
    "RequireAdmin.jsx",
    "RequireDispatch.jsx",
    "RequirePm.jsx",
]

LOGINS = [
    "SafetyLogin.jsx",
    "HrLogin.jsx",
    "ShopLogin.jsx",
    "AdminLogin.jsx",
    "DispatchLogin.jsx",
    "PmLogin.jsx",
]


# ─── Continuity helper ───────────────────────────────────────────────────

def test_iter322b_helper_present():
    """portalContinuity.js exists, exports buildContinuity(), maps the
    most-hit Safety workflows (Incidents/Audits/CA/Training) explicitly."""
    assert HELPER.exists()
    src = HELPER.read_text()
    assert "export function buildContinuity" in src
    # Most-hit Safety workflows reported by operator are explicitly mapped.
    for marker in (
        '"Incident Reports"',
        '"Audits & Inspections"',
        '"Corrective Actions"',
        '"Training & Certifications"',
    ):
        assert marker in src, f"buildContinuity missing workflow label {marker}"
    # 7 portals registered.
    for key in ("safety:", "hr:", "shop:", "admin:", "pm:", "dispatch:", "leadership:"):
        assert key in src, f"PORTAL registry missing {key}"


# ─── Guards now pass state.continuity ───────────────────────────────────

def test_iter322b_all_guards_pass_continuity():
    """Every `<Require*>` guard imports buildContinuity and attaches
    `continuity: buildContinuity(...)` to navigation state."""
    failures = []
    for guard in GUARDS:
        path = FRONTEND / "components" / guard
        src = path.read_text()
        if "buildContinuity" not in src:
            failures.append(f"{guard}: missing buildContinuity import/use")
        elif "continuity: buildContinuity(" not in src:
            failures.append(f"{guard}: continuity not attached to Navigate state")
    assert not failures, f"Guard wiring incomplete: {failures}"


# ─── Login pages render AuthRequiredBanner ───────────────────────────────

def test_iter322b_login_pages_render_banner():
    """Every portal login page imports AuthRequiredBanner and renders
    `<AuthRequiredBanner />` above the form card."""
    failures = []
    for login in LOGINS:
        path = FRONTEND / "pages" / login
        src = path.read_text()
        if "AuthRequiredBanner" not in src:
            failures.append(f"{login}: missing AuthRequiredBanner import")
        elif "<AuthRequiredBanner />" not in src:
            failures.append(f"{login}: AuthRequiredBanner not rendered")
    assert not failures, f"Login wiring incomplete: {failures}"


# ─── Login pages honor state.from / state.continuity.continueTo ─────────

def test_iter322b_safety_login_honors_continueto():
    src = (FRONTEND / "pages/SafetyLogin.jsx").read_text()
    assert "location.state?.continuity?.continueTo" in src
    assert "location.state?.from" in src
    assert "nav(intended, { replace: true })" in src


def test_iter322b_dispatch_login_honors_continueto():
    src = (FRONTEND / "pages/DispatchLogin.jsx").read_text()
    assert "location.state?.continuity?.continueTo" in src
    assert "nav(intended, { replace: true })" in src


# ─── Banner copy is the rich variant ─────────────────────────────────────

def test_iter322b_banner_rich_copy_present():
    """AuthRequiredBanner renders the rich 'You selected {workflow}
    from {origin}.' + 'After sign-in, you'll continue to {workflow}.'
    variants — not the prior generic placeholder."""
    src = BANNER.read_text()
    assert 'You selected {workflow} from {origin}.' in src
    assert "After sign-in, you'll continue to {workflow}." in src
    assert 'This workflow requires {role} access.' in src
    # Banner exposes a back-link testid for downstream regression.
    assert '"auth-required-back-link"' in src


# ─── Bilingual parity (Rule 8) ──────────────────────────────────────────

def test_iter322b_bilingual_translations_present():
    """All iter322-B copy has ES entries — banner copy + the workflow
    labels users will see in the 'You selected X' line."""
    src = I18N.read_text()
    required = [
        '"Sign-in required": "Se requiere iniciar sesión"',
        '"You selected {workflow} from {origin}.": "Seleccionaste {workflow} desde {origin}."',
        '"This workflow requires {role} access.": "Este flujo requiere acceso de {role}."',
        '"After sign-in, you\'ll continue to {workflow}.": "Después de iniciar sesión, continuarás a {workflow}."',
        '"Incident Reports": "Reportes de Incidentes"',
        '"Audits & Inspections": "Auditorías e Inspecciones"',
        '"Corrective Actions": "Acciones Correctivas"',
        '"Training & Certifications": "Capacitación y Certificaciones"',
        '"Fire Extinguishers": "Extintores"',
        '"Safety Portal": "Portal de Seguridad"',
    ]
    for entry in required:
        assert entry in src, f"i18n.js missing ES entry: {entry}"


# ─── Wording correctness — no PM/Admin role leakage for Safety paths ────

def test_iter322b_wording_no_pm_admin_leak_for_safety():
    """Operator complaint check: Safety paths must not produce
    'PM/Admin' wording. The buildContinuity helper must return
    role='Safety Portal' for every /safety-portal/* path."""
    src = HELPER.read_text()
    # Find the Safety Portal block — every Safety workflow entry must
    # be tagged with the "safety" portal key, never "pm" or "admin".
    safety_lines = [
        line for line in src.splitlines()
        if "/^\\/safety-portal" in line
    ]
    assert safety_lines, "No Safety Portal workflow entries found"
    for line in safety_lines:
        assert '"safety"' in line, (
            f"Safety workflow tagged with wrong portal: {line.strip()}"
        )


# ─── Family contract still green (sanity) ───────────────────────────────

def test_iter322b_family_contract_still_at_nine():
    """The 9-hub family contract is untouched by iter322-B."""
    contract_src = (ROOT / "backend/tests/test_platform_family_contract.py").read_text()
    fam_start = contract_src.index("FAMILY_HUBS = [")
    fam_end = contract_src.index("]", fam_start)
    fam_block = contract_src[fam_start:fam_end]
    members = fam_block.count('.jsx",')
    assert members == 9, f"FAMILY_HUBS must remain at 9; got {members}"
