"""TRACK 18.01 · Human Operability Review + Usability Hardening.

Locks the human-readiness contract for Transportation Operations:
  · Audit doc + role walkthrough checklists exist.
  · Findability + actionability matrices documented.
  · Restricted-state copy reads as Transportation Operations.
  · No Admin Console / Admin Portal wording inside the shell.
  · No raw JSON / null / undefined / stack-trace copy in user-facing JSX.
  · Search placeholder is human-readable.
  · TopBar nav labels are operational language (no developer jargon).
  · Visible CTAs carry hrefs (no dead buttons).
  · Mobile hamburger preserved.
  · Every preceding phase preserved (A · B · C · D · E · 18.00E-FIX · F · G).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path("/app")
MEMORY = ROOT / "memory"
AUDIT_DOC = MEMORY / "TRACK_18_01_HUMAN_OPERABILITY_REVIEW.md"
TX_DIR = ROOT / "frontend" / "src" / "pages" / "transportation"
COMP_TX_DIR = ROOT / "frontend" / "src" / "components" / "transportation"
TOPBAR = COMP_TX_DIR / "TransportationOpsTopBar.jsx"
RESTRICTED = COMP_TX_DIR / "TxOpsRestricted.jsx"
SHELL = TX_DIR / "TransportationWorkspaceShell.jsx"
SEARCH = TX_DIR / "TransportationSearch.jsx"
TX_APP = TX_DIR / "TransportationApp.jsx"
APP_JS = ROOT / "frontend" / "src" / "App.js"
SERVER = ROOT / "backend" / "server.py"
GATE = ROOT / "scripts" / "deployment_gate.py"


# ===========================================================================
# 1 — Human operability audit document exists with role sections.
# ===========================================================================
def test_01_audit_document_exists():
    assert AUDIT_DOC.exists(), f"missing {AUDIT_DOC}"
    src = AUDIT_DOC.read_text()
    assert "Human Operability" in src or "human operability" in src.lower()


# ===========================================================================
# 2 — Dispatch role walkthrough checklist present in audit doc.
# ===========================================================================
def test_02_dispatch_walkthrough_in_doc():
    src = AUDIT_DOC.read_text()
    assert "Dispatch" in src
    # Walkthrough surfaces named.
    for needle in ("Hub", "Board", "Map", "Mission Control"):
        assert needle in src


# ===========================================================================
# 3 — Transportation Manager walkthrough checklist present.
# ===========================================================================
def test_03_transportation_manager_in_doc():
    src = AUDIT_DOC.read_text()
    assert "Transportation Manager" in src
    for needle in ("Drivers", "Carriers", "Fleet", "Compliance"):
        assert needle in src


# ===========================================================================
# 4 — Fleet / Shop walkthrough present.
# ===========================================================================
def test_04_fleet_shop_in_doc():
    src = AUDIT_DOC.read_text()
    assert "Fleet" in src and "Shop" in src
    assert "Inspections" in src or "inspection" in src.lower()


# ===========================================================================
# 5 — HR walkthrough present.
# ===========================================================================
def test_05_hr_in_doc():
    src = AUDIT_DOC.read_text()
    assert "HR" in src
    assert "driver readiness" in src.lower() or "drivers" in src.lower()


# ===========================================================================
# 6 — Safety walkthrough present.
# ===========================================================================
def test_06_safety_in_doc():
    src = AUDIT_DOC.read_text()
    assert "Safety" in src
    assert "risk" in src.lower() or "hold" in src.lower()


# ===========================================================================
# 7 — PM / Operations walkthrough present.
# ===========================================================================
def test_07_pm_operations_in_doc():
    src = AUDIT_DOC.read_text()
    assert "PM" in src or "Project Manager" in src
    assert "project" in src.lower()


# ===========================================================================
# 8 — Findability matrix exists with core objects.
# ===========================================================================
def test_08_findability_matrix_present():
    src = AUDIT_DOC.read_text()
    assert "Findability" in src
    for obj in ("driver", "carrier", "truck", "assignment",
                "project", "document"):
        assert obj in src.lower(), f"findability matrix missing {obj}"


# ===========================================================================
# 9 — Actionability matrix exists.
# ===========================================================================
def test_09_actionability_matrix_present():
    src = AUDIT_DOC.read_text()
    assert "Actionability" in src
    # Mandated language buckets from the prompt.
    for term in ("Needs attention", "Action required", "Ready",
                 "Restricted"):
        assert term in src


# ===========================================================================
# 10 — Restricted-state language uses Transportation wording.
# ===========================================================================
def test_10_restricted_state_language():
    src = RESTRICTED.read_text()
    assert "restricted for your role" in src
    assert "Transportation Operations" in src
    assert "not available for your role" in src


# ===========================================================================
# 11 — No "Admin Console" wording inside the Transportation shell (any
#       user-facing JSX, comments stripped).
# ===========================================================================
def test_11_no_admin_console_wording():
    for d in (TX_DIR, COMP_TX_DIR):
        for jsx in d.rglob("*.jsx"):
            src = jsx.read_text()
            stripped = re.sub(r"/\*.*?\*/", "", src, flags=re.DOTALL)
            stripped = re.sub(r"//.*", "", stripped)
            assert "Admin Console" not in stripped, f"in {jsx}"
            assert "Admin Portal" not in stripped, f"in {jsx}"


# ===========================================================================
# 12 — No raw error tokens leaking into user-facing copy across the shell.
# ===========================================================================
def test_12_no_raw_error_copy():
    forbidden_text = (
        ">undefined<", ">null<", '"undefined"', '"null"',
        "JSON.stringify(err",  # never display raw stack
        "Error stack",
        "Forbidden",  # 403 wording; we use "restricted" instead
        "Unauthorized",  # 401 wording; we use "restricted" / Sign in
    )
    for d in (TX_DIR, COMP_TX_DIR):
        for jsx in d.rglob("*.jsx"):
            src = jsx.read_text()
            stripped = re.sub(r"/\*.*?\*/", "", src, flags=re.DOTALL)
            stripped = re.sub(r"//.*", "", stripped)
            for bad in forbidden_text:
                assert bad not in stripped, (
                    f"raw error/error-token copy '{bad}' in {jsx}")


# ===========================================================================
# 13 — Search placeholder is human-readable.
# ===========================================================================
def test_13_search_placeholder_humanized():
    src = SEARCH.read_text()
    m = re.search(r'placeholder="([^"]+)"', src)
    assert m, "search input has no placeholder"
    ph = m.group(1)
    # Mention the core objects users actually search for.
    assert "drivers" in ph.lower()
    assert "trucks" in ph.lower() or "truck" in ph.lower()
    assert "carriers" in ph.lower() or "carrier" in ph.lower()


# ===========================================================================
# 14 — TopBar nav labels are operational language.
# ===========================================================================
def test_14_topbar_nav_labels_operational():
    src = TOPBAR.read_text()
    # Five required user-facing labels.
    for label in ("Mission Control", "Dispatch", "Drivers", "Carriers",
                  "Compliance", "Live Operations"):
        assert f'"{label}"' in src or f"'{label}'" in src, (
            f"nav label missing: {label}")
    # Avoid developer/system jargon as labels.
    for jargon in (
        '"endpoint"', '"payload"', '"queue handler"',
        '"composer"', '"router"',
    ):
        assert jargon not in src, f"jargon label leaked: {jargon}"


# ===========================================================================
# 15 — Every visible NAV_GROUPS item carries an href (no dead buttons).
# ===========================================================================
def test_15_visible_ctas_have_href():
    src = TOPBAR.read_text()
    m = re.search(r"const NAV_GROUPS\s*=\s*\[(.*?)\];", src, re.DOTALL)
    assert m
    block = m.group(1)
    for label_match in re.finditer(r"\{\s*label:", block):
        idx = label_match.end()
        window = block[idx:idx + 200]
        assert "href:" in window


# ===========================================================================
# 16 — No "Coming Soon" placeholders mounted on primary workflow surfaces.
#       (Existing ComingSoon usages live on driver workspace side-cards
#       and a reports CSV — secondary, non-blocking. Lock them there.)
# ===========================================================================
def test_16_coming_soon_only_on_secondary_surfaces():
    # ComingSoon must not appear on the main Mission Control dashboard,
    # the shell, the TopBar, or the search/right rail.
    primary = [
        TX_DIR / "MissionControl.jsx",
        SHELL,
        TOPBAR,
        SEARCH,
    ]
    for path in primary:
        if not path.exists():
            continue
        src = path.read_text()
        assert "<ComingSoon" not in src, f"primary surface has ComingSoon: {path.name}"


# ===========================================================================
# 17 — Mobile hamburger toggle still wired (preserved from Phase F).
# ===========================================================================
def test_17_mobile_hamburger_preserved():
    src = TOPBAR.read_text()
    assert "txops-portal-topbar-mobile-toggle" in src
    assert "txops-portal-topbar-mobile-nav" in src


# ===========================================================================
# 18 — Mission Control still indexed in TransportationApp.
# ===========================================================================
def test_18_mission_control_loads():
    src = TX_APP.read_text()
    assert "TransportationDashboard" in src


# ===========================================================================
# 19 — Dispatch board route preserved.
# ===========================================================================
def test_19_dispatch_board_route_preserved():
    src = APP_JS.read_text()
    assert "/dispatch-portal/board" in src


# ===========================================================================
# 20 — Dispatch map route preserved.
# ===========================================================================
def test_20_dispatch_map_route_preserved():
    src = APP_JS.read_text()
    assert "/dispatch-portal/map" in src


# ===========================================================================
# 21 — Dispatch haul-ledger route preserved.
# ===========================================================================
def test_21_dispatch_haul_ledger_route_preserved():
    src = APP_JS.read_text()
    assert "/dispatch-portal/haul-ledger" in src


# ===========================================================================
# 22 — Dispatch driver-qualification route preserved.
# ===========================================================================
def test_22_dispatch_driver_q_preserved():
    src = APP_JS.read_text()
    assert "/dispatch-portal/driver-qualification" in src


# ===========================================================================
# 23 — Dispatch fleet route preserved with TopBar (Phase G lock).
# ===========================================================================
def test_23_dispatch_fleet_preserved():
    src = APP_JS.read_text()
    line = next(
        (l for l in src.splitlines() if '"/dispatch-portal/fleet"' in l), "")
    assert "TransportationOpsTopBar" in line
    assert 'scope="dispatch"' in line


# ===========================================================================
# 24 — Right rail testid contract preserved (Phase D + Phase F).
# ===========================================================================
def test_24_right_rail_testid_contract():
    src = SHELL.read_text()
    for testid in (
        "txops-right-rail",
        "txops-rail-recent-activity",
        "txops-rail-timeline",
        "txops-rail-related",
        "txops-rail-open-actions",
        "txops-rail-audit",
        "txops-rail-entity-banner",
    ):
        assert testid in src, f"right rail testid missing: {testid}"


# ===========================================================================
# 25 — Search testid contract preserved (Phase C).
# ===========================================================================
def test_25_search_testid_contract():
    src = SEARCH.read_text()
    assert 'data-testid="txops-search"' in src
    assert 'data-testid="txops-search-input"' in src


# ===========================================================================
# 26 — Track 18.01 wired into deployment gate.
# ===========================================================================
def test_26_wired_into_deployment_gate():
    src = GATE.read_text()
    assert "test_track_18_01_human_operability_review.py" in src


# ===========================================================================
# 27 — Phase A through G chain preserved (single sanity check).
# ===========================================================================
def test_27_phase_chain_preserved():
    src = SERVER.read_text()
    assert "register_track_18_00_phase_c_routes" in src  # Phase C
    assert "register_track_18_00_phase_d_routes" in src  # Phase D
    assert "register_transportation_experience_routes" in src  # Phase F
    sys.path.insert(0, str(ROOT / "backend"))
    from routes.transportation_relationships import SCHEMA_VERSION
    assert SCHEMA_VERSION == "18.00D"


# ===========================================================================
# 28 — Audit doc declares a final human-readiness verdict.
# ===========================================================================
def test_28_audit_doc_has_final_verdict():
    src = AUDIT_DOC.read_text()
    assert "Final" in src and ("GO" in src or "READY" in src.upper())


# ===========================================================================
# 29 — Audit doc lists at least one usability scorecard with the
#       colour buckets defined in the prompt.
# ===========================================================================
def test_29_audit_doc_scorecard():
    src = AUDIT_DOC.read_text()
    assert "GREEN" in src
    assert "YELLOW" in src
    assert "RED" in src


# ===========================================================================
# 30 — Audit doc lists deferred polish items explicitly.
# ===========================================================================
def test_30_audit_doc_deferrals():
    src = AUDIT_DOC.read_text()
    assert "Deferral" in src or "Deferred" in src or "DEFERRAL" in src


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
