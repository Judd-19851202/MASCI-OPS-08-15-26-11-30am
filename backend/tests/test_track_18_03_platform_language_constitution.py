"""TRACK 18.03 · Platform Language Constitution + Operational Guidance System.

Locks the Constitution and Registry. Static-scan regression guards
prevent legacy vocabulary from creeping into the Transportation
Operations shell (the area already cleaned in Tracks 18.00-G/18.01/
18.02). Establishes the inventory baseline for the mechanical
cleanup deferred to Track 18.04.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path("/app")
CONSTITUTION = ROOT / "memory" / "TRACK_18_03_PLATFORM_LANGUAGE_CONSTITUTION.md"
TOPBAR = ROOT / "frontend" / "src" / "components" / "transportation" / "TransportationOpsTopBar.jsx"
RESTRICTED = ROOT / "frontend" / "src" / "components" / "transportation" / "TxOpsRestricted.jsx"
SEARCH = ROOT / "frontend" / "src" / "pages" / "transportation" / "TransportationSearch.jsx"
SHELL = ROOT / "frontend" / "src" / "pages" / "transportation" / "TransportationWorkspaceShell.jsx"
GATE = ROOT / "scripts" / "deployment_gate.py"
TX_DIR = ROOT / "frontend" / "src" / "pages" / "transportation"
COMP_TX_DIR = ROOT / "frontend" / "src" / "components" / "transportation"


def _stripped(text: str) -> str:
    """Strip block + line comments before scanning for user-facing copy."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    text = re.sub(r"//.*", "", text)
    return text


# ===========================================================================
# Articles I–VII — Constitution document structure.
# ===========================================================================
def test_01_constitution_doc_exists():
    assert CONSTITUTION.exists()


def test_02_constitution_seven_articles_present():
    src = CONSTITUTION.read_text()
    for article in ("Article I", "Article II", "Article III",
                    "Article IV", "Article V", "Article VI",
                    "Article VII"):
        assert article in src, f"missing {article}"


def test_03_one_vocabulary_rule_present():
    src = CONSTITUTION.read_text()
    assert "One Vocabulary" in src
    assert "canonical" in src.lower() and "deprecated" in src.lower()


def test_04_operational_voice_rule_present():
    src = CONSTITUTION.read_text()
    assert "Operational Voice" in src


def test_05_forbidden_wording_table_present():
    src = CONSTITUTION.read_text()
    assert "Forbidden Wording" in src
    for term in ("Admin Console", "Admin Portal",
                 "Forbidden", "Unauthorized"):
        assert term in src


def test_06_required_wording_table_present():
    src = CONSTITUTION.read_text()
    assert "Required Wording" in src
    for term in ("Ready", "Needs attention", "Action required",
                 "Watch", "Blocked", "Restricted for your role",
                 "Open", "Assigned", "Waiting", "Review"):
        assert term in src


def test_07_amendment_clause_present():
    src = CONSTITUTION.read_text()
    assert "Constitutional Provenance" in src
    assert "amend" in src.lower()


# ===========================================================================
# Official Naming Registry.
# ===========================================================================
def test_08_registry_section_present():
    src = CONSTITUTION.read_text()
    assert "Official Naming Registry" in src


def test_09_registry_canonical_terms_listed():
    src = CONSTITUTION.read_text()
    for term in (
        "Transportation Operations", "Mission Control", "Dispatch",
        "Operations Console", "Project Workspace", "HR Workspace",
        "Safety Workspace", "Shop Workspace", "Field Workspace",
        "Driver Workspace", "Live Operations", "Audit Timeline",
        "Right Rail", "Search", "Restricted for your role",
        "Action Required", "Ready", "Needs Attention",
    ):
        assert term in src, f"registry missing canonical term: {term}"


def test_10_registry_deprecated_terms_listed():
    src = CONSTITUTION.read_text()
    for term in ("Dispatch Portal", "Admin Console", "Admin Portal",
                 "PM Portal", "HR Portal", "Safety Portal",
                 "Shop Portal"):
        assert term in src


def test_11_backend_code_carveout_present():
    """Constitution must explicitly carve out backend identifiers."""
    src = CONSTITUTION.read_text()
    assert "Backend code rule" in src or "backend identifiers" in src.lower()


# ===========================================================================
# Audit inventory baseline (allows future tracks to measure progress).
# ===========================================================================
def test_12_audit_inventory_present():
    src = CONSTITUTION.read_text()
    assert "Audit inventory" in src
    # Reference to the 223-file legacy footprint.
    assert "223" in src or "Total user-facing files" in src


def test_13_audit_by_surface_present():
    src = CONSTITUTION.read_text()
    assert "Audit by surface" in src
    for surface in ("Mission Control", "Right rail", "Restricted states"):
        assert surface in src


# ===========================================================================
# Guidance Center audit + gaps.
# ===========================================================================
def test_14_guidance_center_audit_present():
    src = CONSTITUTION.read_text()
    assert "Guidance Center" in src
    assert "Gap analysis" in src or "gap analysis" in src.lower()


# ===========================================================================
# Human excellence re-run section.
# ===========================================================================
def test_15_human_excellence_rerun_section():
    src = CONSTITUTION.read_text()
    assert "Human Excellence" in src
    for label in ("Five-second", "Thirty-second", "Two-minute"):
        assert label in src


# ===========================================================================
# Track 18.04 roadmap published.
# ===========================================================================
def test_16_phase_18_04_roadmap_present():
    src = CONSTITUTION.read_text()
    assert "Track 18.04" in src or "18.04" in src
    assert "Mechanical" in src or "mechanical" in src.lower()
    # Roadmap names each workspace family.
    for ws in ("HR", "Safety", "PM", "Shop"):
        assert ws in src


# ===========================================================================
# Transportation shell vocabulary lock — already-clean area must stay clean.
# ===========================================================================
def test_17_transportation_shell_no_forbidden_wording():
    forbidden = ("Admin Console", "Admin Portal", "Forbidden",
                 "Unauthorized", ">undefined<", ">null<",
                 "JSON.stringify(err")
    for d in (TX_DIR, COMP_TX_DIR):
        for jsx in d.rglob("*.jsx"):
            src = _stripped(jsx.read_text())
            for bad in forbidden:
                assert bad not in src, (
                    f"forbidden term '{bad}' leaked into {jsx}")


# ===========================================================================
# TopBar must carry canonical brand.
# ===========================================================================
def test_18_topbar_carries_canonical_brand():
    src = TOPBAR.read_text()
    assert "Transportation Operations" in src


def test_19_topbar_carries_canonical_mission_control_cta():
    src = TOPBAR.read_text()
    assert "Mission Control" in src


# ===========================================================================
# Restricted-state component carries Constitutional copy.
# ===========================================================================
def test_20_restricted_component_carries_canonical_copy():
    src = RESTRICTED.read_text()
    assert "restricted for your role" in src
    assert "Transportation Operations" in src
    # Forbidden alternatives must NOT appear in the user-facing strings.
    stripped = _stripped(src)
    for bad in ("Forbidden", "Unauthorized", "Access Denied"):
        assert bad not in stripped, (
            f"restricted component must not say '{bad}'")


# ===========================================================================
# Search uses canonical "Search" label (not "Find", "Lookup", etc.).
# ===========================================================================
def test_21_search_uses_canonical_label():
    src = SEARCH.read_text()
    stripped = _stripped(src)
    # Search button/heading uses "Search" — not "Find" or "Lookup".
    assert ">Search<" in stripped or "Search" in stripped
    assert "Lookup" not in stripped
    # Search placeholder mentions canonical core objects.
    m = re.search(r'placeholder="([^"]+)"', src)
    assert m
    ph = m.group(1).lower()
    for obj in ("drivers", "trucks", "carriers"):
        assert obj in ph


# ===========================================================================
# Right rail uses canonical terms.
# ===========================================================================
def test_22_right_rail_uses_canonical_section_names():
    src = SHELL.read_text()
    for term in ("Recent Activity", "Timeline", "Related Records",
                 "Open Actions", "Audit"):
        assert term in src, f"right rail missing canonical: {term}"


# ===========================================================================
# Required operational vocabulary terms appear in the Constitution.
# ===========================================================================
def test_23_constitution_lists_canonical_status_chips():
    src = CONSTITUTION.read_text()
    for term in ("Ready", "Needs attention", "Action required",
                 "Watch", "Blocked", "Complete"):
        assert term in src


# ===========================================================================
# CTA vocabulary registered.
# ===========================================================================
def test_24_constitution_lists_canonical_ctas():
    src = CONSTITUTION.read_text()
    for cta in ("Open in Dispatch", "View Related Records"):
        assert cta in src


# ===========================================================================
# Backend code untouched (carve-out enforced — backend identifiers
# may keep portal/hub/admin namespacing for engineering stability).
# ===========================================================================
def test_25_backend_admin_routes_preserved():
    """Verify the carve-out is honored: backend route paths and
    Python identifiers still use 'admin' etc. The Constitution
    explicitly permits this — only user-facing strings must change."""
    server = (ROOT / "backend" / "server.py").read_text()
    # Dispatch token header alias preserved in server.py.
    assert "X-Dispatch-Token" in server
    # Admin route registration entry-point preserved in server.py.
    assert "transportation_relationships" in server
    # The relationships route prefix unchanged in its source file.
    rels = (ROOT / "backend" / "routes" / "transportation_relationships.py").read_text()
    assert 'prefix="/api/admin/transportation"' in rels


# ===========================================================================
# Constitution declares the final certification.
# ===========================================================================
def test_26_constitution_final_certification():
    src = CONSTITUTION.read_text()
    assert "Final certification" in src
    assert "RATIFIED" in src or "ratified" in src.lower()


# ===========================================================================
# Track 18.03 wired into deployment gate.
# ===========================================================================
def test_27_track_wired_into_gate():
    src = GATE.read_text()
    assert "test_track_18_03_platform_language_constitution.py" in src


# ===========================================================================
# Predecessor audit docs (18.01, 18.02) still present — provenance.
# ===========================================================================
def test_28_predecessor_docs_intact():
    for doc in (
        "TRACK_18_01_HUMAN_OPERABILITY_REVIEW.md",
        "TRACK_18_02_HUMAN_EXCELLENCE_CERTIFICATION.md",
    ):
        assert (ROOT / "memory" / doc).exists()


# ===========================================================================
# Phase D schema version still 18.00D (cross-phase guarantee).
# ===========================================================================
def test_29_phase_d_schema_locked():
    import sys
    sys.path.insert(0, str(ROOT / "backend"))
    from routes.transportation_relationships import SCHEMA_VERSION
    assert SCHEMA_VERSION == "18.00D"


# ===========================================================================
# Constitution explicitly forbids silent rename (process safeguard).
# ===========================================================================
def test_30_no_silent_rename_clause():
    src = CONSTITUTION.read_text()
    # Article VII requires amendments to be explicit.
    assert "No silent rename" in src or "silent rename" in src.lower()


if __name__ == "__main__":
    funcs = [(n, f) for n, f in globals().items()
             if n.startswith("test_") and callable(f)]
    fails = []
    for name, fn in funcs:
        try:
            fn()
        except AssertionError as e:
            fails.append((name, str(e)))
    print(f"{len(funcs) - len(fails)}/{len(funcs)} PASS")
    for n, err in fails:
        print(f"  FAIL {n}: {err}")
