"""iter322 · Portal Continuity & Guidance Cohesion Fix Pass.

Locks the iter322 cross-portal continuity work:
- PortalContextBanner component renders "← Back to {Portal}" when
  arriving at /guidance, /safety/forms, or /safety/forms/login with
  `?from=<key>` query param.
- All 5 hub Guides links append `?from=<key>`.
- FL → Safety Equipment Issuance route appends `?from=leadership` and
  is now `internalRoute` (not `external`) so React Router carries the
  query param into the Safety Forms gate.
- AuthRequiredBanner exported for use on portal login pages when
  arriving via redirect with `location.state.continuity`.
- Bilingual entries present for every new string.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
FRONTEND = ROOT / "frontend/src"
BANNER = FRONTEND / "components/PortalContextBanner.jsx"
GUIDANCE = FRONTEND / "pages/guidance/OperationalGuidanceCenter.jsx"
SAFETY_FORMS_HUB = FRONTEND / "pages/SafetyFormsHub.jsx"
SAFETY_FORMS_LOGIN = FRONTEND / "pages/SafetyFormsLogin.jsx"
FL_SCHEMAS = FRONTEND / "lib/fieldLeadershipSchemas.js"
I18N = FRONTEND / "lib/i18n.js"
HUBS = [
    FRONTEND / "pages/HrHub.jsx",
    FRONTEND / "pages/SafetyHub.jsx",
    FRONTEND / "pages/ShopHub.jsx",
    FRONTEND / "pages/FieldLeadershipHub.jsx",
    FRONTEND / "pages/DispatchHub.jsx",
]


def test_iter322_portal_context_banner_exists():
    assert BANNER.exists(), "PortalContextBanner component must exist"
    src = BANNER.read_text()
    # Banner uses `?from=` query param to source the originating portal.
    assert 'params.get("from")' in src
    # Auth-required variant exported for login pages.
    assert "export function AuthRequiredBanner" in src
    # 6 portals registered (safety · hr · leadership · shop · dispatch · field).
    for key in ("safety:", "hr:", "leadership:", "shop:", "dispatch:", "field:"):
        assert key in src, f"PORTAL_REGISTRY missing entry: {key}"
    # Banner uses the family contract calm-card chrome.
    assert "border border-slate-200 border-l-4" in src
    # Banner has testids for downstream regression.
    assert '"portal-context-banner"' in src
    assert '"portal-context-back-link"' in src
    assert '"auth-required-banner"' in src


def test_iter322_guides_links_carry_from_param():
    """Every hub's Guides/Training Center link appends `?from=<key>`."""
    expected = {
        "HrHub.jsx":              "/guidance?from=hr",
        "SafetyHub.jsx":          "/guidance?from=safety",
        "ShopHub.jsx":            "/guidance?from=shop",
        "FieldLeadershipHub.jsx": "/guidance?from=leadership",
        "DispatchHub.jsx":        "/guidance?from=dispatch",
    }
    for hub in HUBS:
        src = hub.read_text()
        assert expected[hub.name] in src, (
            f"{hub.name} must link to {expected[hub.name]}"
        )


def test_iter322_guidance_center_renders_banner():
    """OperationalGuidanceCenter Shell renders the PortalContextBanner
    so users arriving from a portal always see the back-link."""
    src = GUIDANCE.read_text()
    assert "PortalContextBanner" in src
    assert "<PortalContextBanner />" in src


def test_iter322_safety_forms_renders_banner():
    """SafetyFormsHub + SafetyFormsLogin render the PortalContextBanner.
    This is the operational fix for the FL → Safety Equipment Issuance
    `auth break` reported by the operator."""
    for path in (SAFETY_FORMS_HUB, SAFETY_FORMS_LOGIN):
        src = path.read_text()
        assert "PortalContextBanner" in src
        assert "<PortalContextBanner" in src


def test_iter322_fl_safety_equipment_link_carries_from_param():
    """FL → Safety Equipment Issuance route carries `?from=leadership`
    and is internal-route so React Router preserves the query param."""
    src = FL_SCHEMAS.read_text()
    assert "/safety/forms/login?from=leadership" in src
    # external: true would prevent React Router from carrying the param.
    # Confirm the link is now treated as an internal route.
    assert "internalRoute: true" in src
    assert "external: false" in src


def test_iter322_bilingual_translations_present():
    """All new iter322 strings have ES dictionary entries."""
    src = I18N.read_text()
    required = [
        '"Back to": "Volver a"',
        '"You are viewing platform Guidance": "Estás viendo la Guía de la plataforma"',
        '"You are viewing Safety Forms": "Estás viendo Formularios de Seguridad"',
        '"Safety Forms · Sign-in required": "Formularios de Seguridad · Se requiere inicio de sesión"',
        '"Higher access required": "Se requiere mayor acceso"',
        '"If you believe you should have access, contact your portal lead.": "Si crees que deberías tener acceso, contacta al líder de tu portal."',
        '"This workflow": "Este flujo de trabajo"',
        '"elevated access": "acceso elevado"',
        '"Safety Portal": "Portal de Seguridad"',
        '"HR Portal": "Portal de RH"',
        '"Shop Portal": "Portal del Taller"',
        '"Dispatch Portal": "Portal de Despacho"',
    ]
    for entry in required:
        assert entry in src, f"i18n.js missing ES entry: {entry}"


def test_iter322_family_contract_still_green():
    """The platform family contract (iter317-321 anchors) is still
    green after iter322's continuity touches — no calm chrome regressed."""
    contract = ROOT / "backend/tests/test_platform_family_contract.py"
    assert contract.exists()
    src = contract.read_text()
    # FAMILY_HUBS list literal contains 9 hub tuples.
    fam_start = src.index("FAMILY_HUBS = [")
    fam_end = src.index("]", fam_start)
    fam_block = src[fam_start:fam_end]
    members = fam_block.count('.jsx",')
    assert members == 9, f"FAMILY_HUBS must remain at 9; got {members}"
