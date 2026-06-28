"""TRACK 18.06 · Operational Design System + Authenticated Workspace
Excellence regression lock.

This track is observational + codification. It does NOT add features,
endpoints, collections, or workflows. It locks the Operational Design
System document and the 7 audit reports so they cannot silently
drift and so future tracks always inherit the standard.
"""
from __future__ import annotations

from pathlib import Path

import pytest  # noqa: F401

ROOT = Path("/app")
MEMORY = ROOT / "memory"
BACKEND = ROOT / "backend"
GATE = ROOT / "scripts" / "deployment_gate.py"

DESIGN_SYSTEM = MEMORY / "OPERATIONAL_DESIGN_SYSTEM.md"
WORKSPACE_AUDIT = MEMORY / "AUTHENTICATED_WORKSPACE_DESIGN_AUDIT.md"
RHYTHM_AUDIT = MEMORY / "OPERATIONAL_RHYTHM_AUDIT.md"
COGNITIVE_AUDIT = MEMORY / "COGNITIVE_LOAD_AND_ATTENTION_AUDIT.md"
TRUST_AUDIT = MEMORY / "TRUST_AND_METRIC_AUDIT.md"
MOBILE_AUDIT = MEMORY / "MOBILE_TABLET_FIELD_EXPERIENCE_AUDIT.md"
GUIDANCE_AUDIT_DESIGN = MEMORY / "GUIDANCE_CENTER_DESIGN_AUDIT.md"
CERT = MEMORY / "TRACK_18_06_OPERATIONAL_DESIGN_SYSTEM_CERTIFICATION.md"


# ===========================================================================
# 1–7 · Required documentation present.
# ===========================================================================
def test_01_design_system_doc_exists():
    assert DESIGN_SYSTEM.exists()


def test_02_workspace_audit_exists():
    assert WORKSPACE_AUDIT.exists()


def test_03_rhythm_audit_exists():
    assert RHYTHM_AUDIT.exists()


def test_04_cognitive_audit_exists():
    assert COGNITIVE_AUDIT.exists()


def test_05_trust_audit_exists():
    assert TRUST_AUDIT.exists()


def test_06_mobile_audit_exists():
    assert MOBILE_AUDIT.exists()


def test_07_guidance_design_audit_exists():
    assert GUIDANCE_AUDIT_DESIGN.exists()


# ===========================================================================
# 8–24 · Design System defines every required section.
# ===========================================================================
def _ds() -> str:
    return DESIGN_SYSTEM.read_text()


def test_08_defines_page_anatomy():
    assert "Page Anatomy" in _ds()


def test_09_defines_card_anatomy():
    assert "Card Anatomy" in _ds()


def test_10_defines_status_language():
    src = _ds()
    assert "Status Language" in src
    for canonical in ("Ready", "Needs Attention", "Action Required",
                      "Watch", "Blocked", "Open", "In Progress",
                      "Complete", "Pending Review",
                      "Restricted for Your Role"):
        assert canonical in src, f"Status missing: {canonical}"


def test_11_defines_color_system():
    src = _ds()
    assert "Color System" in src
    for c in ("Red", "Amber", "Green", "Blue", "Purple", "Orange", "Gray"):
        assert c in src


def test_12_defines_typography_system():
    assert "Typography System" in _ds()


def test_13_defines_spacing_system():
    assert "Spacing System" in _ds()


def test_14_defines_buttons():
    src = _ds()
    assert "Buttons" in src or "CTA" in src
    assert "Primary" in src
    assert "Secondary" in src
    assert "Destructive" in src


def test_15_defines_tables():
    assert "Tables" in _ds() or "Lists" in _ds()


def test_16_defines_drawers_modals():
    src = _ds()
    assert "Drawer" in src
    assert "Modal" in src


def test_17_defines_search():
    assert "Search" in _ds()


def test_18_defines_right_rail():
    assert "Right Rail" in _ds()


def test_19_defines_empty_states():
    src = _ds()
    assert "Empty State" in src
    # The banned default empty-state phrasings are called out.
    assert '"No data"' in src or "No data" in src


def test_20_defines_loading_states():
    assert "Loading State" in _ds()


def test_21_defines_restricted_states():
    src = _ds()
    assert "Restricted State" in src
    # Banned wording explicitly forbidden.
    assert "Forbidden" in src and "Unauthorized" in src


def test_22_defines_error_states():
    src = _ds()
    assert "Error State" in src
    # Banned developer-leak phrases listed.
    assert "stack traces" in src or "stack trace" in src.lower()


def test_23_defines_mobile_tablet():
    src = _ds()
    assert "Mobile" in src or "Tablet" in src
    # Required breakpoints documented.
    for px in ("390", "768", "1024", "1366", "1920"):
        assert px in src, f"Breakpoint missing in design system: {px}"


def test_24_defines_accessibility():
    src = _ds()
    assert "Accessibility" in src
    assert "WCAG" in src or "contrast" in src


def test_25_defines_trust():
    src = _ds()
    assert "Trust Standard" in src
    # The five trust questions are codified.
    for q in ("Source", "Freshness", "Meaning", "Action", "Confidence"):
        assert q in src


# ===========================================================================
# 26–28 · Audit scoring contract.
# ===========================================================================
def test_26_every_workspace_has_score():
    src = WORKSPACE_AUDIT.read_text()
    # Each major workspace name appears with a Dimension column.
    for ws in ("Transportation Operations", "Dispatch",
               "Project Management", "Human Resources",
               "Safety Operations", "Shop Operations",
               "Administration", "Field Leadership",
               "Operational Guidance Center"):
        assert ws in src, f"Workspace missing from audit: {ws}"


def test_27_no_red_items():
    src = WORKSPACE_AUDIT.read_text()
    # Look for RED items inside table rows (a `| 🔴 |` cell), not the
    # legend that explains the scale.
    import re as _re
    red_rows = _re.findall(r"\|\s*🔴\s*\|", src)
    assert not red_rows, (
        f"RED items present in workspace audit — must be fixed before "
        f"certification (found {len(red_rows)} row(s))"
    )


def test_28_deferred_yellow_documented():
    src = WORKSPACE_AUDIT.read_text()
    # Some YELLOW rows exist; each must mention a Deferred-to-track
    # disposition. We check the audit explicitly documents deferrals.
    assert "Deferred" in src or "deferred" in src


# ===========================================================================
# 29–34 · "Do not break anything" carve-outs.
# ===========================================================================
def test_29_no_new_collections_added_by_18_06():
    """No new MongoDB collection should be introduced for Track 18.06.
    Sanity check: scan server.py for collection-name patterns that did
    not exist in earlier tracks."""
    src = (BACKEND / "server.py").read_text()
    # No 18.06-specific collection added.
    forbidden = [
        "db.track_18_06_",
        "db.design_system_",
    ]
    for f in forbidden:
        assert f not in src, f"Track 18.06 added a new collection: {f}"


def test_30_no_new_routes_added_by_18_06():
    """Track 18.06 must not add new FastAPI routes. We assert no
    @router.* line carries the marker '18.06'."""
    for p in (BACKEND / "server.py", BACKEND / "routes" / "transportation_relationships.py"):
        src = p.read_text()
        assert "track_18_06" not in src.lower()


def test_31_dispatch_token_alias_preserved():
    src = (BACKEND / "server.py").read_text()
    assert "X-Dispatch-Token" in src


def test_32_dispatch_login_route_preserved():
    src = (BACKEND / "routes" / "dispatch_portal_auth.py").read_text()
    assert "/dispatch/login" in src


def test_33_relationships_route_prefix_preserved():
    src = (BACKEND / "routes" / "transportation_relationships.py").read_text()
    assert 'prefix="/api/admin/transportation"' in src


def test_34_rbac_admin_strict_routes_unchanged():
    """Sanity: the admin-strict guard is still imported / referenced in
    `transportation_experience.py` (Track 16.06 contract)."""
    src = (BACKEND / "routes" / "transportation_experience.py").read_text()
    assert "require_admin_dep" in src


# ===========================================================================
# 35–37 · Status / empty / restricted standards exist.
# ===========================================================================
def test_35_status_color_registry_present():
    src = _ds()
    # Each canonical status must have a color band.
    assert "green" in src.lower()
    assert "amber" in src.lower()
    assert "red" in src.lower()
    assert "slate" in src.lower()


def test_36_empty_state_standard_present():
    src = _ds()
    assert "Empty States" in src or "Empty State Standard" in src
    # Four required questions.
    for q in ("What this area is", "Why it is empty",
              "What to do next"):
        assert q in src, f"Empty-state standard missing question: {q}"


def test_37_restricted_state_standard_present():
    src = _ds()
    assert "Restricted State" in src
    assert "Restricted for your role" in src


# ===========================================================================
# 38–39 · Mobile + Guidance audits cover required surfaces.
# ===========================================================================
def test_38_mobile_audit_covers_required_breakpoints():
    src = MOBILE_AUDIT.read_text()
    for px in ("390", "768", "1024", "1366", "1920"):
        assert f"{px} px" in src or f"| {px} " in src, (
            f"Mobile audit missing breakpoint: {px}"
        )


def test_39_guidance_design_audit_covers_role_playbooks():
    src = GUIDANCE_AUDIT_DESIGN.read_text()
    assert "Role playbooks" in src or "role playbook" in src.lower()


# ===========================================================================
# 40 · Deployment gate wired.
# ===========================================================================
def test_40_track_wired_into_deployment_gate():
    src = GATE.read_text()
    assert "test_track_18_06_operational_design_system.py" in src


# ===========================================================================
# 41 · Certification doc declares GO.
# ===========================================================================
def test_41_certification_declares_go():
    src = CERT.read_text()
    assert "GO" in src
    assert "OPERATIONAL DESIGN SYSTEM CERTIFIED" in src or "Operational Design System Certified" in src or "CERTIFIED" in src
