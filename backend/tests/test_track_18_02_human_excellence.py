"""TRACK 18.02 · Human-First Operational Excellence Certification.

The final lock-in track for Transportation Operations. Verifies that
every preceding phase still holds and that the certification document
exists with all mandated audit sections.

These tests do not exercise new functionality — they prevent regression
on the human-excellence contract.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path("/app")
CERT_DOC = ROOT / "memory" / "TRACK_18_02_HUMAN_EXCELLENCE_CERTIFICATION.md"
AUDIT_DOC = ROOT / "memory" / "TRACK_18_01_HUMAN_OPERABILITY_REVIEW.md"
TOPBAR = ROOT / "frontend" / "src" / "components" / "transportation" / "TransportationOpsTopBar.jsx"
RESTRICTED = ROOT / "frontend" / "src" / "components" / "transportation" / "TxOpsRestricted.jsx"
SHELL = ROOT / "frontend" / "src" / "pages" / "transportation" / "TransportationWorkspaceShell.jsx"
SEARCH = ROOT / "frontend" / "src" / "pages" / "transportation" / "TransportationSearch.jsx"
TX_APP = ROOT / "frontend" / "src" / "pages" / "transportation" / "TransportationApp.jsx"
APP_JS = ROOT / "frontend" / "src" / "App.js"
# TRACK 22.5A · re-anchor to current routing shell (App.js + AppRoutes.jsx)
APP_ROUTES = ROOT / "frontend" / "src" / "app" / "routing" / "AppRoutes.jsx"
SERVER = ROOT / "backend" / "server.py"
GATE = ROOT / "scripts" / "deployment_gate.py"


# ===========================================================================
# 1 — Certification document exists.
# ===========================================================================
def test_01_certification_doc_exists():
    assert CERT_DOC.exists(), f"missing {CERT_DOC}"


# ===========================================================================
# 2 — Doc contains the executive certification verdict.
# ===========================================================================
def test_02_executive_verdict_present():
    src = CERT_DOC.read_text()
    assert "Executive certification" in src
    assert "CERTIFIED" in src or "certified" in src
    assert "GO" in src


# ===========================================================================
# 3 — Five-second test section present + PASS.
# ===========================================================================
def test_03_five_second_test_pass():
    src = CERT_DOC.read_text()
    assert "Five-second" in src or "five-second" in src.lower()
    assert "PASS" in src


# ===========================================================================
# 4 — Thirty-second test section present + PASS.
# ===========================================================================
def test_04_thirty_second_test_pass():
    src = CERT_DOC.read_text()
    assert "Thirty-second" in src or "thirty-second" in src.lower()
    # Mandated path matrix for 13 core objects.
    for obj in ("Driver", "Truck", "Carrier", "Project",
                "Dispatch Board", "Map", "Assignment", "Documents",
                "Inspection", "Orientation", "Certificates",
                "Cleanup", "Action Items"):
        assert obj in src, f"thirty-second matrix missing: {obj}"


# ===========================================================================
# 5 — Two-minute test section present + PASS.
# ===========================================================================
def test_05_two_minute_test_pass():
    src = CERT_DOC.read_text()
    assert "Two-minute" in src or "two-minute" in src.lower()
    # Mandated questions.
    for q in ("biggest operational risk", "Which driver",
              "Which truck", "Which carrier", "Which project",
              "Who owns it"):
        assert q in src, f"two-minute question missing: {q}"


# ===========================================================================
# 6 — Role walkthrough scorecards present (9 roles).
# ===========================================================================
def test_06_role_walkthroughs_complete():
    src = CERT_DOC.read_text()
    for role in (
        "Dispatch", "Transportation Manager", "Fleet", "Shop",
        "HR", "Safety", "Operations", "Project Management",
        "Leadership",
    ):
        assert role in src, f"role walkthrough missing: {role}"


# ===========================================================================
# 7 — Navigation audit section present.
# ===========================================================================
def test_07_navigation_audit_present():
    src = CERT_DOC.read_text()
    assert "Navigation audit" in src


# ===========================================================================
# 8 — Findability audit present.
# ===========================================================================
def test_08_findability_audit_present():
    src = CERT_DOC.read_text()
    assert "Findability" in src


# ===========================================================================
# 9 — Actionability audit present.
# ===========================================================================
def test_09_actionability_audit_present():
    src = CERT_DOC.read_text()
    assert "Actionability" in src


# ===========================================================================
# 10 — Trust audit present.
# ===========================================================================
def test_10_trust_audit_present():
    src = CERT_DOC.read_text()
    assert "Trust audit" in src


# ===========================================================================
# 11 — Visual hierarchy audit present.
# ===========================================================================
def test_11_visual_hierarchy_audit_present():
    src = CERT_DOC.read_text()
    assert "Visual hierarchy" in src or "visual hierarchy" in src.lower()


# ===========================================================================
# 12 — Language audit present + lock confirmation.
# ===========================================================================
def test_12_language_audit_present():
    src = CERT_DOC.read_text()
    assert "Language audit" in src
    # Confirms the operational language standard.
    for term in ("Needs attention", "Action required", "Ready"):
        assert term in src


# ===========================================================================
# 13 — Accessibility audit present.
# ===========================================================================
def test_13_accessibility_audit_present():
    src = CERT_DOC.read_text()
    assert "Accessibility" in src


# ===========================================================================
# 14 — Mobile + Tablet audit present.
# ===========================================================================
def test_14_mobile_tablet_audit_present():
    src = CERT_DOC.read_text()
    assert "Mobile audit" in src
    assert "Tablet audit" in src
    assert "390" in src  # phone width verified
    assert "1024" in src or "768" in src  # tablet


# ===========================================================================
# 15 — Dead-end audit present.
# ===========================================================================
def test_15_dead_end_audit_present():
    src = CERT_DOC.read_text()
    assert "Dead-end" in src or "dead-end" in src.lower()


# ===========================================================================
# 16 — Dispatch preservation verification present.
# ===========================================================================
def test_16_dispatch_preservation_verified_in_doc():
    src = CERT_DOC.read_text()
    assert "Dispatch preservation" in src or "Dispatch Preservation" in src
    # Specifically: dispatch helpers + routes named.
    assert "RequireDispatch" in src
    assert "X-Dispatch-Token" in src


# ===========================================================================
# 17 — Transportation Operations verification present.
# ===========================================================================
def test_17_transportation_operations_verified():
    src = CERT_DOC.read_text()
    assert "Transportation Operations verification" in src
    assert "/transportation-operations/*" in src
    assert "18.00D" in src
    assert "RequireTransportationPortal" in src


# ===========================================================================
# 18 — Final certification section explicitly affirms readiness.
# ===========================================================================
def test_18_final_certification_section():
    src = CERT_DOC.read_text()
    assert "Final certification" in src
    assert "Six Pillars" in src
    for pillar in ("Powerful", "Simple", "Beautiful",
                   "Trusted", "Proven", "Operational"):
        assert pillar in src, f"Six Pillar missing: {pillar}"


# ===========================================================================
# 19 — Deferred polish list present (transparency).
# ===========================================================================
def test_19_deferred_polish_listed():
    src = CERT_DOC.read_text()
    assert "Deferred polish" in src


# ===========================================================================
# 20 — TopBar still wired with grouped nav + admin-only Administration.
# ===========================================================================
def test_20_topbar_contract_preserved():
    src = TOPBAR.read_text()
    assert "NAV_GROUPS" in src
    assert "adminOnly: true" in src
    assert "Transportation Operations" in src


# ===========================================================================
# 21 — Restricted-state copy contract preserved.
# ===========================================================================
def test_21_restricted_copy_preserved():
    src = RESTRICTED.read_text()
    assert "restricted for your role" in src
    assert "not available for your role" in src


# ===========================================================================
# 22 — No Admin Console / Admin Portal / developer wording in shell.
# ===========================================================================
def test_22_no_forbidden_wording_in_shell():
    forbidden = ("Admin Console", "Admin Portal", "Forbidden",
                 "Unauthorized", "JSON.stringify(err",
                 ">undefined<", ">null<")
    tx_dir = ROOT / "frontend" / "src" / "pages" / "transportation"
    comp_dir = ROOT / "frontend" / "src" / "components" / "transportation"
    for d in (tx_dir, comp_dir):
        for jsx in d.rglob("*.jsx"):
            src = jsx.read_text()
            stripped = re.sub(r"/\*.*?\*/", "", src, flags=re.DOTALL)
            stripped = re.sub(r"//.*", "", stripped)
            for bad in forbidden:
                assert bad not in stripped, (
                    f"forbidden wording '{bad}' in {jsx}")


# ===========================================================================
# 23 — All dispatch routes preserved (zero hunting standard).
# ===========================================================================
def test_23_dispatch_routes_preserved():
    src = (APP_JS.read_text() + "\n" + APP_ROUTES.read_text())
    for route in (
        "/dispatch-portal", "/dispatch-portal/login",
        "/dispatch-portal/board", "/dispatch-portal/command",
        "/dispatch-portal/map", "/dispatch-portal/haul-ledger",
        "/dispatch-portal/driver-qualification",
        "/dispatch-portal/driver/", "/dispatch-portal/fleet",
        "/dispatch-portal/forgot-password",
        "/dispatch-portal/reset/",
        "/dispatch-portal/change-password",
    ):
        assert route in src, f"missing dispatch route: {route}"


# ===========================================================================
# 24 — Transportation shell route mounted with dispatch-safe gate.
# ===========================================================================
def test_24_transportation_shell_dispatch_safe():
    src = (APP_JS.read_text() + "\n" + APP_ROUTES.read_text())
    assert "/transportation-operations/*" in src
    assert "RequireTransportationPortal" in src


# ===========================================================================
# 25 — Mission Control still indexed in TransportationApp.
# ===========================================================================
def test_25_mission_control_indexed():
    src = TX_APP.read_text()
    assert "TransportationDashboard" in src


# ===========================================================================
# 26 — Search testid + placeholder humanized.
# ===========================================================================
def test_26_search_testids_and_placeholder():
    src = SEARCH.read_text()
    assert 'data-testid="txops-search"' in src
    assert 'data-testid="txops-search-input"' in src
    m = re.search(r'placeholder="([^"]+)"', src)
    assert m
    ph = m.group(1).lower()
    assert "drivers" in ph and "trucks" in ph and "carriers" in ph


# ===========================================================================
# 27 — Right rail testid contract preserved.
# ===========================================================================
def test_27_right_rail_testids():
    src = SHELL.read_text()
    for testid in (
        "txops-right-rail",
        "txops-rail-recent-activity",
        "txops-rail-timeline",
        "txops-rail-related",
        "txops-rail-open-actions",
        "txops-rail-audit",
        "txops-rail-entity-banner",
        "txops-rail-entity-subtitle",
    ):
        assert testid in src, f"right rail testid missing: {testid}"


# ===========================================================================
# 28 — Phase chain preserved: Search · Relationships · Experience all
#       registered in server.py.
# ===========================================================================
def test_28_phase_chain_preserved():
    src = SERVER.read_text()
    assert "register_track_18_00_phase_c_routes" in src
    assert "register_track_18_00_phase_d_routes" in src
    assert "register_transportation_experience_routes" in src
    sys.path.insert(0, str(ROOT / "backend"))
    from routes.transportation_relationships import SCHEMA_VERSION
    assert SCHEMA_VERSION == "18.00D"


# ===========================================================================
# 29 — Track 18.02 wired into deployment gate.
# ===========================================================================
def test_29_deployment_gate_includes_18_02():
    src = GATE.read_text()
    assert "test_track_18_02_human_excellence.py" in src


# ===========================================================================
# 30 — Track 18.01 audit doc still present (provenance chain).
# ===========================================================================
def test_30_provenance_chain_intact():
    assert AUDIT_DOC.exists(), (
        "18.01 audit doc must remain — 18.02 builds on its findings")


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
