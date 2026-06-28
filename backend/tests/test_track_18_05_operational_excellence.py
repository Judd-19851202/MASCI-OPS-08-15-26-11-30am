"""TRACK 18.05 · Operational Excellence Certification + Case Style regression.

Locks the operational refinements and case-style decisions made during
the Track 18.05 audit so future commits cannot drift back into mixed
case or legacy phrasing.

What this protects:

* Public homepage hero — kicker uses canonical brand, subtext uses
  generic-category sentence-case prose (no awkward
  Title-Case-mid-sentence).
* Workspace card titles stay canonical Title Case.
* Card descriptions stay sentence-case.
* Section headers stay Title Case.
* Track 18.05 deliverables (audit + case-style guide + roadmap) exist.
* Deployment gate runs this file.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path("/app")
FRONTEND_SRC = ROOT / "frontend" / "src"
MEMORY = ROOT / "memory"
GATE = ROOT / "scripts" / "deployment_gate.py"

HUB = FRONTEND_SRC / "pages" / "Hub.jsx"
I18N = FRONTEND_SRC / "lib" / "i18n.js"

# Deliverable docs.
TRACK_18_05 = MEMORY / "TRACK_18_05_OPERATIONAL_EXCELLENCE.md"
CASE_GUIDE = MEMORY / "PLATFORM_CASE_STYLE_GUIDE.md"
FRICTION = MEMORY / "TRACK_18_05_WORKFLOW_FRICTION_REPORT.md"
CLICK_REPORT = MEMORY / "TRACK_18_05_CLICK_REDUCTION_REPORT.md"
NAV_REPORT = MEMORY / "TRACK_18_05_NAVIGATION_REPORT.md"
ROADMAP = MEMORY / "TRACK_18_05_ROADMAP.md"


# ===========================================================================
# 1 · Deliverable docs exist.
# ===========================================================================
def test_01_certification_doc_exists():
    assert TRACK_18_05.exists(), (
        f"Track 18.05 certification doc missing: {TRACK_18_05}"
    )


def test_02_case_style_guide_exists():
    assert CASE_GUIDE.exists(), (
        f"Platform Case Style Guide missing: {CASE_GUIDE}"
    )


def test_03_friction_report_exists():
    assert FRICTION.exists()


def test_04_click_reduction_report_exists():
    assert CLICK_REPORT.exists()


def test_05_navigation_report_exists():
    assert NAV_REPORT.exists()


def test_06_roadmap_exists():
    assert ROADMAP.exists()


# ===========================================================================
# 2 · Homepage hero case-style decisions are locked.
# ===========================================================================
def test_07_hero_subtext_uses_option_c_generic_categories():
    src = HUB.read_text()
    # Option C wording (lowercase generic categories, no
    # Title-Case-mid-sentence).
    assert (
        "workforce accountability, transportation, and project operations"
        in src
    ), "Hero subtext must use the Option C generic-category wording"


def test_08_hero_subtext_does_not_mix_title_case_with_lowercase():
    src = HUB.read_text()
    # The pre-amendment wording embedded Title Case mid-sentence.
    bad = ("workforce accountability, Transportation Operations, "
           "and project operations")
    assert bad not in src, (
        "Hero subtext still mixes Title-Case workspace name with "
        "lowercase generic categories"
    )


def test_09_hero_kicker_is_canonical_brand():
    src = HUB.read_text()
    assert 't("MASCI Operations Platform")' in src


def test_10_hero_i18n_entry_uses_option_c():
    src = I18N.read_text()
    # The dictionary entry for the hero subtext must match the Option C
    # canonical phrasing.
    needle = ('"Field reporting, safety, quality, equipment, workforce '
              'accountability, transportation, and project operations —')
    assert needle in src, (
        "i18n dictionary missing the Option C hero subtext entry"
    )


# ===========================================================================
# 3 · Workspace card titles + descriptions follow the case-style guide.
# ===========================================================================
def test_11_workspace_card_titles_are_title_case():
    src = HUB.read_text()
    # All six workspace cards must use canonical Title Case names.
    for title in (
        't("Transportation Operations")',
        't("Project Management")',
        't("Human Resources")',
        't("Safety Operations")',
        't("Shop Operations")',
        't("Administration")',
    ):
        assert title in src, f"Workspace card title missing: {title}"


def test_12_workspace_card_descriptions_are_sentence_case():
    """Descriptions should START with capital letter and otherwise read
    as natural sentences — no inline ALL CAPS or shouting."""
    src = HUB.read_text()
    descriptions = [
        "Project management, PO requests",
        "Fleet maintenance, inspections, repairs",
        "Employee records, onboarding",
        "Incidents, audits, inspections",
        "Dispatch, live map, fleet, drivers",
        "System administration, user management",
    ]
    for d in descriptions:
        assert d in src, f"Card description not found verbatim: {d}"
        # Sanity: no ALL CAPS shouting inside the description.
        assert not re.search(r"\b[A-Z]{4,}\b", d), (
            f"Description contains all-caps shouting: {d}"
        )


def test_13_section_headers_are_title_case():
    src = HUB.read_text()
    for header in (
        't("Today in the Field")',
        't("Leadership Tools")',
        't("Operations")',
        't("Reference")',
        't("Your Workspaces")',
    ):
        assert header in src, f"Section header missing: {header}"


# ===========================================================================
# 4 · CTA case-style — Hub uses Title Case CTA source strings.
# ===========================================================================
def test_14_hub_signed_in_cta_label_is_title_case():
    src = HUB.read_text()
    # The Hub workspace cards expose `signedInLabel: t("Open Workspace")`.
    assert 'signedInLabel: t("Open Workspace")' in src, (
        "Hub workspace CTA source string must be 'Open Workspace' "
        "(Title Case)"
    )
    # The legacy mixed cases must be gone.
    assert 'signedInLabel: t("Open Portal")' not in src
    assert 'signedInLabel: t("Open Console")' not in src


# ===========================================================================
# 5 · Case-style guide content reflects the amendment decisions.
# ===========================================================================
def test_15_case_guide_documents_title_case_rule():
    src = CASE_GUIDE.read_text()
    assert "Title Case" in src
    assert "sentence case" in src
    # Hero example must be present.
    assert "transportation, and project operations" in src


def test_16_case_guide_documents_workspace_names():
    src = CASE_GUIDE.read_text()
    for canonical in (
        "Transportation Operations",
        "Project Management",
        "Human Resources",
        "Safety Operations",
        "Shop Operations",
        "Administration",
    ):
        assert canonical in src


# ===========================================================================
# 6 · Deployment gate wired.
# ===========================================================================
def test_17_track_wired_into_deployment_gate():
    src = GATE.read_text()
    assert "test_track_18_05_operational_excellence.py" in src, (
        "Track 18.05 regression must be wired into deployment_gate.py"
    )


# ===========================================================================
# 7 · No regression of Track 18.04 vocabulary.
# ===========================================================================
def test_18_no_legacy_workspace_terms_in_hub_portaldefs():
    src = HUB.read_text()
    m = re.search(r"const portalDefs\s*=\s*\[(.*?)\];", src, re.S)
    assert m, "portalDefs block not found"
    block = m.group(1)
    for legacy in ("PM Portal", "HR Portal", "Safety Portal",
                   "Shop Portal", "Admin Portal", "Admin Console",
                   "Dispatch Portal"):
        assert legacy not in block, (
            f"Hub portalDefs regressed legacy term: {legacy}"
        )


def test_19_no_legacy_office_portals_anywhere_in_hub():
    src = HUB.read_text()
    # Strip line comments; only allow the term in JS comments.
    no_comments = []
    for line in src.splitlines():
        stripped = re.sub(r"(?<![:/'\"])(^|\s)//[^\n]*$", r"\1", line)
        no_comments.append(stripped)
    no_comments = "\n".join(no_comments)
    no_comments = re.sub(r"/\*.*?\*/", "", no_comments, flags=re.S)
    assert "Office Portals" not in no_comments


# ===========================================================================
# 8 · Final certification declaration present in doc.
# ===========================================================================
def test_20_certification_doc_declares_go():
    src = TRACK_18_05.read_text()
    assert ("OPERATIONAL EXCELLENCE CERTIFIED" in src
            or "Final certification: GO" in src)
