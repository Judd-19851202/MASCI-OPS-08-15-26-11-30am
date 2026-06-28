"""TRACK 18.04 · Platform Language Migration regression.

Locks the platform-wide vocabulary cutover declared by the Platform
Language Constitution (Track 18.03) into the running codebase:

* Homepage / Hub uses canonical workspace names.
* Login chrome uses canonical names.
* Top-bar shells, breadcrumbs, sidebars, and access-management UI use
  canonical names.
* Email templates and footers use canonical workspace names (no
  user-facing legacy "Portal" terminology).
* Backend routes, collection names, auth tokens, and Python identifiers
  are intentionally UNCHANGED (carve-out per the Constitution).
* Guidance Center articles use canonical names.
* Track 18.04 supporting documentation exists.
* Track 18.04 wired into deployment_gate.py.

The Constitution permits backend identifiers and route paths to keep
legacy `portal`/`hub`/`admin` namespacing for engineering stability —
this file ONLY scans user-facing strings.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest  # noqa: F401

ROOT = Path("/app")
FRONTEND_SRC = ROOT / "frontend" / "src"
MEMORY = ROOT / "memory"
GATE = ROOT / "scripts" / "deployment_gate.py"

# Constitution + Track 18.04 artifacts.
CONSTITUTION = MEMORY / "TRACK_18_03_PLATFORM_LANGUAGE_CONSTITUTION.md"
TRACK_18_04 = MEMORY / "TRACK_18_04_PLATFORM_LANGUAGE_MIGRATION.md"
REGISTRY = MEMORY / "PLATFORM_LANGUAGE_CONSTITUTION_APPLIED_REGISTRY.md"
INVENTORY = MEMORY / "PLATFORM_LANGUAGE_MIGRATION_INVENTORY.md"
GUIDANCE_AUDIT = MEMORY / "OPERATIONAL_GUIDANCE_CENTER_AUDIT.md"

# Primary user-facing surfaces we lock in this track.
HUB = FRONTEND_SRC / "pages" / "Hub.jsx"
CHEAT = FRONTEND_SRC / "components" / "CheatSheetCard.jsx"
ADMIN_SHELL = FRONTEND_SRC / "components" / "AdminShell.jsx"
HR_SHELL = FRONTEND_SRC / "components" / "HrPageShell.jsx"
PM_SHELL = FRONTEND_SRC / "components" / "PmShell.jsx"
SAFETY_SHELL = FRONTEND_SRC / "components" / "SafetyShell.jsx"
BACK_LINK = FRONTEND_SRC / "components" / "BackLink.jsx"
PORTAL_SWITCHER = FRONTEND_SRC / "components" / "PortalSwitcher.jsx"
PORTAL_LOADER = FRONTEND_SRC / "components" / "PortalHydratingLoader.jsx"
PORTAL_LOGIN_HELP = FRONTEND_SRC / "components" / "PortalLoginHelp.jsx"
PORTAL_CONTEXT_BANNER = FRONTEND_SRC / "components" / "PortalContextBanner.jsx"
DISPATCH_LOGIN = FRONTEND_SRC / "pages" / "DispatchLogin.jsx"
HR_LOGIN = FRONTEND_SRC / "pages" / "HrLogin.jsx"
PM_LOGIN = FRONTEND_SRC / "pages" / "PmLogin.jsx"
SAFETY_LOGIN = FRONTEND_SRC / "pages" / "SafetyLogin.jsx"
SAFETY_FORMS_LOGIN = FRONTEND_SRC / "pages" / "SafetyFormsLogin.jsx"
GUIDANCE_PAGE = FRONTEND_SRC / "pages" / "guidance" / "OperationalGuidanceCenter.jsx"
GUIDANCE_CONTENT = ROOT / "backend" / "guidance" / "content.py"

# User-facing-only Admin panels (access management).
ADMIN_DISPATCH_PANEL = FRONTEND_SRC / "components" / "AdminDispatchUsersPanel.jsx"
ADMIN_HR_PANEL = FRONTEND_SRC / "components" / "AdminHRUsersPanel.jsx"
ADMIN_SAFETY_PANEL = FRONTEND_SRC / "components" / "AdminSafetyUsersPanel.jsx"
ADMIN_FL_PANEL = FRONTEND_SRC / "components" / "AdminFieldLeadershipUsersPanel.jsx"

# Backend artifacts that must keep their internal identifiers intact.
BACKEND = ROOT / "backend"
SERVER = BACKEND / "server.py"
RELS = BACKEND / "routes" / "transportation_relationships.py"
BRANDED_EMAILS = BACKEND / "branded_portal_emails.py"
OPERATIONAL_FOOTER = BACKEND / "operational_footer.py"


# ───────────────────────────────────────────────────────────────────
# Helpers
# ───────────────────────────────────────────────────────────────────
def _read(p: Path) -> str:
    return p.read_text()


def _strip_comments(src: str) -> str:
    """Remove `// ...`, `/* ... */`, and Python `# ...` comments.

    The Constitution governs only what the user sees on screen. Comments
    and docstrings may keep legacy names for historical context.

    Order matters: strip JS line comments FIRST so URL paths like
    `/api/*` that live inside `// ...` comments don't trip the
    block-comment regex.
    """
    # 1. Strip JS/TS line comments first. Only treat `//` as a comment
    #    when it does NOT immediately follow `:` (which would indicate a
    #    URL like `https://`) and is not inside a JSX/HTML attribute. We
    #    accept some false positives — this scanner only needs a "good
    #    enough" view of comments-stripped code.
    out_lines = []
    for line in src.splitlines():
        # Treat `//` as a comment ONLY when preceded by whitespace or
        # start-of-line, and not preceded by `:` (URL guard).
        stripped = re.sub(r"(?<![:/'\"])(^|\s)//[^\n]*$", r"\1", line)
        out_lines.append(stripped)
    src = "\n".join(out_lines)

    # 2. Now strip block comments.
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    return src


# ===========================================================================
# 1 · Constitution + 18.04 documentation present.
# ===========================================================================
def test_01_constitution_present():
    assert CONSTITUTION.exists(), "Track 18.03 Constitution must exist"


def test_02_track_18_04_doc_present():
    assert TRACK_18_04.exists(), (
        f"Track 18.04 deliverable doc missing: {TRACK_18_04}"
    )


def test_03_applied_registry_present():
    assert REGISTRY.exists(), (
        f"Applied registry missing: {REGISTRY}"
    )


def test_04_inventory_present():
    assert INVENTORY.exists(), (
        f"Language migration inventory missing: {INVENTORY}"
    )


def test_05_guidance_audit_present():
    assert GUIDANCE_AUDIT.exists(), (
        f"Operational Guidance Center audit missing: {GUIDANCE_AUDIT}"
    )


# ===========================================================================
# 2 · Homepage / Hub — Operations section + canonical card titles.
# ===========================================================================
def test_06_hub_renamed_office_portals_section():
    src = _strip_comments(_read(HUB))
    assert "Office Portals" not in src, (
        "Hub still references legacy 'Office Portals' section title"
    )
    assert 'title={authed ? t("Your Workspaces") : t("Operations")}' in src


def test_07_hub_card_transportation_operations():
    src = _read(HUB)
    assert 'title: t("Transportation Operations")' in src
    assert "Dispatch, live map, fleet, drivers, carriers" in src


def test_08_hub_card_project_management():
    src = _read(HUB)
    assert 'title: t("Project Management")' in src


def test_09_hub_card_human_resources():
    src = _read(HUB)
    assert 'title: t("Human Resources")' in src


def test_10_hub_card_safety_operations():
    src = _read(HUB)
    assert 'title: t("Safety Operations")' in src


def test_11_hub_card_shop_operations():
    src = _read(HUB)
    assert 'title: t("Shop Operations")' in src


def test_12_hub_card_administration():
    src = _read(HUB)
    assert 'title: t("Administration")' in src


def test_13_hub_no_legacy_workspace_titles():
    """Card titles on the Hub must NOT use legacy names. We scan the
    portalDefs block specifically — historical comments elsewhere in
    Hub.jsx are allowed."""
    src = _strip_comments(_read(HUB))
    # The portalDefs block starts with `const portalDefs = [` and ends
    # at the next `];` on its own line.
    m = re.search(r"const portalDefs\s*=\s*\[(.*?)\];", src, re.S)
    assert m, "portalDefs block not found in Hub.jsx"
    block = m.group(1)
    for legacy in ("PM Portal", "HR Portal", "Safety Portal",
                   "Shop Portal", "Admin Portal", "Admin Console",
                   "Dispatch Portal"):
        assert legacy not in block, (
            f"Hub portalDefs still uses legacy term: {legacy}"
        )


# ===========================================================================
# 3 · Login chrome — canonical workspace names.
# ===========================================================================
def test_14_dispatch_login_uses_transportation_operations():
    src = _read(DISPATCH_LOGIN)
    assert "Transportation Operations Sign In" in src
    assert "MASCI · Transportation Operations" in src
    # Body of the login screen must not show legacy title — comments OK.
    visible = _strip_comments(src)
    assert "Dispatch Portal Sign In" not in visible


def test_15_hr_login_uses_human_resources():
    src = _strip_comments(_read(HR_LOGIN))
    assert "Human Resources Sign In" in src
    assert "HR Portal Sign In" not in src


def test_16_pm_login_uses_project_management():
    src = _strip_comments(_read(PM_LOGIN))
    assert "Project Management Sign In" in src
    assert "PM Portal Sign In" not in src


def test_17_safety_login_uses_safety_operations():
    src = _strip_comments(_read(SAFETY_LOGIN))
    assert "Safety Operations Sign In" in src
    assert "MASCI · Safety Operations" in src
    assert "Safety Portal Sign In" not in src


def test_18_safety_forms_login_uses_safety_operations():
    src = _strip_comments(_read(SAFETY_FORMS_LOGIN))
    assert "Safety Operations Ownership" in src
    assert "Safety Portal Ownership" not in src


# ===========================================================================
# 4 · Shells / top bars / breadcrumbs.
# ===========================================================================
def test_19_admin_shell_uses_administration():
    src = _strip_comments(_read(ADMIN_SHELL))
    assert "Administration" in src
    assert "Admin Console" not in src
    assert "Admin Portal" not in src


def test_20_pm_shell_uses_project_management():
    src = _strip_comments(_read(PM_SHELL))
    assert "Project Management" in src
    assert "PM Portal" not in src


def test_21_hr_shell_uses_human_resources():
    src = _strip_comments(_read(HR_SHELL))
    assert "Human Resources" in src
    assert "HR Portal" not in src


def test_22_safety_shell_uses_safety_operations():
    src = _strip_comments(_read(SAFETY_SHELL))
    assert "Safety Operations" in src
    assert "Safety Portal" not in src


def test_23_back_link_uses_canonical_labels():
    src = _strip_comments(_read(BACK_LINK))
    assert "Administration" in src
    assert "Project Management" in src
    assert "Human Resources" in src
    assert "Shop Operations" in src
    for legacy in ("Admin Console", "PM Hub", "HR Portal", "Shop Portal"):
        assert legacy not in src, (
            f"BackLink still references legacy term: {legacy}"
        )


def test_24_portal_switcher_uses_canonical_labels():
    src = _strip_comments(_read(PORTAL_SWITCHER))
    assert "Administration" in src
    assert "Project Management" in src
    assert "Human Resources" in src
    assert "Safety Operations" in src
    assert "Shop Operations" in src
    assert "Transportation Operations" in src
    for legacy in ("Admin Console", "PM Portal", "HR Portal",
                   "Safety Portal", "Shop Portal", "Dispatch Portal"):
        assert legacy not in src, (
            f"PortalSwitcher still references legacy term: {legacy}"
        )


def test_25_portal_loader_uses_canonical_labels():
    src = _strip_comments(_read(PORTAL_LOADER))
    for canonical in ("Administration", "Project Management",
                      "Human Resources", "Shop Operations",
                      "Safety Operations", "Transportation Operations"):
        assert canonical in src, (
            f"PortalHydratingLoader missing canonical name: {canonical}"
        )


def test_26_portal_login_help_uses_canonical_labels():
    src = _strip_comments(_read(PORTAL_LOGIN_HELP))
    for canonical in ("Human Resources", "Safety Operations",
                      "Shop Operations", "Transportation Operations",
                      "Project Management", "Administration"):
        assert canonical in src


def test_27_portal_context_banner_uses_canonical_labels():
    src = _strip_comments(_read(PORTAL_CONTEXT_BANNER))
    for canonical in ("Safety Operations", "Human Resources",
                      "Shop Operations", "Transportation Operations"):
        assert canonical in src


# ===========================================================================
# 5 · Access-management UI — Workspace language.
# ===========================================================================
def test_28_admin_dispatch_panel_uses_transportation_operations():
    src = _strip_comments(_read(ADMIN_DISPATCH_PANEL))
    assert "Transportation Operations" in src
    # The eyebrow label must NOT show "Dispatch Portal" — comments allowed.
    assert "Dispatch Portal\n" not in src


def test_29_admin_hr_panel_uses_human_resources():
    src = _strip_comments(_read(ADMIN_HR_PANEL))
    assert "Human Resources" in src
    # Eyebrow user-facing block must not show legacy 'HR Portal' header
    assert ">\n              HR Portal\n            <" not in src


def test_30_admin_safety_panel_uses_safety_operations():
    src = _strip_comments(_read(ADMIN_SAFETY_PANEL))
    assert "Safety Operations" in src
    assert ">\n              Safety Portal\n            <" not in src


def test_31_admin_fl_panel_uses_human_resources_for_dir_label():
    src = _strip_comments(_read(ADMIN_FL_PANEL))
    assert "Human Resources" in src
    assert ">\n              HR Portal\n            <" not in src


# ===========================================================================
# 6 · Email + footer language.
# ===========================================================================
def test_32_branded_email_themes_use_canonical_workspace_names():
    src = _read(BRANDED_EMAILS)
    # The user-visible sub_eyebrow on every branded email theme must
    # carry the canonical workspace name.
    assert '"sub_eyebrow": "Project Management · Account"' in src
    assert '"sub_eyebrow": "Shop Operations · Account"' in src
    assert '"sub_eyebrow": "Human Resources · Account"' in src
    assert '"sub_eyebrow": "Safety Operations · Account"' in src
    assert '"sub_eyebrow": "Transportation Operations · Account"' in src


def test_33_operational_footer_resolves_portal_codes_to_canonical_names():
    """The operational footer renderer must map internal portal codes to
    canonical workspace names in the user-facing output."""
    import sys
    sys.path.insert(0, str(BACKEND))
    from operational_footer import (
        render_operational_footer_text,
        render_operational_footer_html,
    )
    txt = render_operational_footer_text(portal="HR")
    assert "Human Resources" in txt
    assert "HR Portal" not in txt
    txt = render_operational_footer_text(portal="Dispatch")
    assert "Transportation Operations" in txt
    assert "Dispatch Portal" not in txt
    txt = render_operational_footer_text(portal="Admin")
    assert "Administration" in txt
    assert "Admin Portal" not in txt
    html = render_operational_footer_html(portal="Shop")
    assert "Shop Operations" in html


def test_34_email_subjects_use_canonical_workspace_names():
    """User-facing email subjects must NOT use legacy portal names."""
    subject_files = [
        SERVER,
        BACKEND / "routes" / "pm_routes.py",
        BACKEND / "routes" / "safety_portal" / "auth_users.py",
        BACKEND / "routes" / "field_leadership_portal.py",
        BACKEND / "routes" / "hr_portal.py",
    ]
    for f in subject_files:
        src = f.read_text()
        # Match only literal email subject strings: `[MASCI] ... XXX Portal`
        bad_patterns = [
            r'"\[MASCI\][^"]*PM Portal',
            r'"\[MASCI\][^"]*HR Portal',
            r'"\[MASCI\][^"]*Safety Portal',
            r'"\[MASCI\][^"]*Shop Portal',
            r'"\[MASCI\][^"]*Dispatch Portal',
            r'"\[MASCI\][^"]*Admin Portal',
            r'"\[MASCI\][^"]*Admin Console',
            r'"\[MASCI\][^"]*Field Leadership Portal',
        ]
        for pat in bad_patterns:
            assert not re.search(pat, src), (
                f"{f.name} still emits a legacy subject matching {pat}"
            )


def test_35_email_welcome_headlines_use_canonical_workspace_names():
    """User-facing email `headline=` strings must use canonical names."""
    files = [
        SERVER,
        BACKEND / "routes" / "pm_admin.py",
        BACKEND / "routes" / "safety_portal" / "auth_users.py",
        BACKEND / "routes" / "field_leadership_portal.py",
        BACKEND / "routes" / "hr_portal.py",
    ]
    for f in files:
        src = f.read_text()
        # Match only literal `headline="..."` strings containing legacy
        # portal names.
        bad_patterns = [
            r'headline="[^"]*PM Portal',
            r'headline="[^"]*HR Portal',
            r'headline="[^"]*Safety Portal',
            r'headline="[^"]*Shop Portal',
            r'headline="[^"]*Dispatch Portal',
            r'headline="[^"]*Field Leadership Portal',
        ]
        for pat in bad_patterns:
            assert not re.search(pat, src), (
                f"{f.name} still emits a legacy headline matching {pat}"
            )


# ===========================================================================
# 7 · Guidance Center articles — canonical names.
# ===========================================================================
def test_36_guidance_center_top_articles_renamed():
    src = _read(GUIDANCE_CONTENT)
    for canonical_title in (
        '"title": "Human Resources Guidance"',
        '"title": "Safety Operations Guidance"',
        '"title": "Transportation Operations Guidance"',
        '"title": "Project Management Guidance"',
        '"title": "Administration Guidance"',
        '"title": "Shop Operations Guidance"',
        '"title": "Human Resources — Overview"',
        '"title": "Safety Operations — Overview"',
        '"title": "Transportation Operations — Overview"',
        '"title": "Project Management — Overview"',
        '"title": "Administration — Overview"',
        '"title": "Shop Operations — Overview"',
    ):
        assert canonical_title in src, (
            f"Guidance article title missing: {canonical_title}"
        )


def test_37_guidance_page_workspace_chips_use_canonical_names():
    src = _strip_comments(_read(GUIDANCE_PAGE))
    for canonical in ("Human Resources", "Safety Operations",
                      "Shop Operations", "Transportation Operations",
                      "Project Management", "Administration",
                      "Field Leadership"):
        assert canonical in src
    # Page-level "Sign-In Required · Your Workspaces" copy.
    assert "Sign-In Required · Your Workspaces" in src


# ===========================================================================
# 8 · Backend carve-out — internal identifiers / routes preserved.
# ===========================================================================
def test_38_backend_admin_route_prefix_unchanged():
    rels = _read(RELS)
    assert 'prefix="/api/admin/transportation"' in rels


def test_39_backend_dispatch_token_alias_preserved():
    src = _read(SERVER)
    assert "X-Dispatch-Token" in src


def test_40_backend_dispatch_portal_routes_unchanged():
    """Dispatch login endpoint is mounted under /api/dispatch/login.
    URL contract must stay unchanged."""
    src = (BACKEND / "routes" / "dispatch_portal_auth.py").read_text()
    assert '/dispatch/login' in src
    assert '/dispatch/change-password' in src
    assert '/dispatch/reset-password' in src


# ===========================================================================
# 9 · Deployment gate wiring.
# ===========================================================================
def test_41_track_wired_into_deployment_gate():
    src = _read(GATE)
    assert "test_track_18_04_platform_language_migration.py" in src, (
        "Track 18.04 regression must be wired into deployment_gate.py"
    )


# ===========================================================================
# 10 · Constitution document remains the source of truth.
# ===========================================================================
def test_42_constitution_naming_registry_intact():
    src = _read(CONSTITUTION)
    for canonical in (
        "Transportation Operations",
        "Project Workspace",
        "HR Workspace",
        "Safety Workspace",
        "Shop Workspace",
        "Operations Console",
    ):
        assert canonical in src, (
            f"Constitution missing canonical entry: {canonical}"
        )


# ===========================================================================
# 11 · No empty guidance shells — every key article has body content.
# ===========================================================================
def test_43_guidance_articles_have_body():
    src = _read(GUIDANCE_CONTENT)
    # Sanity: every renamed article still has a non-trivial body. We
    # inspect the file as text and confirm each canonical title is
    # followed (within 600 chars) by a `"body":` declaration.
    for canonical in (
        '"title": "Human Resources Guidance"',
        '"title": "Transportation Operations Guidance"',
        '"title": "Administration Guidance"',
    ):
        idx = src.find(canonical)
        assert idx >= 0
        window = src[idx: idx + 800]
        assert '"body":' in window
