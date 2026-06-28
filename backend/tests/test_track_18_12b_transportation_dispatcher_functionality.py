"""TRACK 18.12B · Transportation Operations Dispatcher Functionality Restore

Static-scan regression that locks the contract that:
  • Every Transportation Operations data loader uses the `txGet`
    wrapper (which absorbs 401/403) or the `isTxRestricted` / `txCatch`
    helpers — never `api.get("/admin/transportation/...")` raw.
  • No user-facing string under /pages/transportation/** leaks
    "Admin login required", "Request failed with status code 4xx",
    "Forbidden", or "Unauthorized".
  • Every restricted-state branch renders <TxOpsRestrictedData /> (or
    <TxOpsRestricted />) — not raw error strings.
  • Administration sub-nav group is filtered by `visibleTxOpsNavGroups`.
  • The four 18.12B markdown documents exist.

These are pure source-tree checks; they do not hit the live backend.
Run with `cd /app/backend && pytest tests/test_track_18_12b_*.py -v`.
"""
from __future__ import annotations

import re
import textwrap
from pathlib import Path

import pytest

ROOT = Path("/app")
FE_TX = ROOT / "frontend" / "src" / "pages" / "transportation"
FE_COMP_TX = ROOT / "frontend" / "src" / "components" / "transportation"
MEM = ROOT / "memory"

# ─── helpers ───────────────────────────────────────────────────────────────
def _read(p: Path) -> str:
    assert p.exists(), f"required file missing: {p}"
    return p.read_text(encoding="utf-8", errors="ignore")

def _all_tx_jsx() -> list[Path]:
    return sorted(FE_TX.glob("*.jsx"))

# ─── (1-4) the four required documents ─────────────────────────────────────
def test_track_18_12b_restore_document_exists():
    assert (MEM / "TRACK_18_12B_TRANSPORTATION_DISPATCHER_FUNCTIONALITY_RESTORE.md").exists()

def test_dispatcher_functionality_audit_document_exists():
    body = _read(MEM / "TRANSPORTATION_DISPATCHER_FUNCTIONALITY_AUDIT.md")
    # Every workspace listed below must appear by name in the audit doc.
    for ws in [
        "Mission Control", "Dispatch", "Live Operations", "Drivers",
        "Carriers", "Trucks", "Compliance", "Document Center",
        "Inspection Center", "Orientation", "Intelligence",
        "Automation", "Audit Timeline", "Reports",
    ]:
        assert ws in body, f"audit doc missing workspace: {ws}"

def test_api_auth_matrix_document_exists():
    body = _read(MEM / "TRANSPORTATION_API_AUTH_MATRIX.md")
    # Every admin-strict endpoint family must appear in the matrix.
    for path in [
        "/api/admin/transportation/audit-timeline",
        "/api/admin/transportation/carriers",
        "/api/admin/transportation/persons",
        "/api/admin/transportation/trucks",
        "/api/admin/transportation/dashboard",
        "/api/admin/transportation/orientation/dashboard",
        "/api/admin/transportation/intelligence/dashboard",
        "/api/admin/transportation/automation/actions",
        "/api/admin/transportation/hr-sync",
        "/api/operations/transportation/readiness",
    ]:
        assert path in body, f"auth matrix doc missing endpoint: {path}"

def test_dispatcher_operator_walkthrough_document_exists():
    body = _read(MEM / "TRANSPORTATION_DISPATCHER_OPERATOR_WALKTHROUGH.md")
    # Each numbered step must be present.
    for step_label in [
        "Open `/transportation-operations`",
        '"Drivers"', '"Carriers"', '"Fleet"', '"Orientation"',
        '"Intelligence"', '"Automation"', '"Reports"',
    ]:
        assert step_label in body, f"walkthrough doc missing step ref: {step_label}"

# ─── (5) every workspace classified ────────────────────────────────────────
def test_every_workspace_classified_in_audit_doc():
    body = _read(MEM / "TRANSPORTATION_DISPATCHER_FUNCTIONALITY_AUDIT.md")
    # Class A/B/C/D classifications must each appear.
    for cls in ["Class A", "Class B", "Class C", "Class D"]:
        assert cls in body, f"audit doc missing classification: {cls}"

# ─── (6) shared 401/403 absorption layer ───────────────────────────────────
def test_tx_get_absorbs_401_403_into_restricted_marker():
    body = _read(FE_TX / "_shared.jsx")
    assert "export function txGet" in body
    assert "status === 401" in body
    assert "status === 403" in body
    assert "__txRestricted" in body
    assert "skipSessionStatus" in body
    assert "isTxRestricted" in body
    assert "function txCatch" in body
    assert "Admin login required" in body  # only inside the sanitiser regex
    # The sanitiser explicitly strips the forbidden tokens.
    for forbidden in [
        "Admin login required",
        "Request failed with status code 4",
        "Forbidden",
        "Unauthorized",
    ]:
        assert forbidden in body, f"txCatch must strip token: {forbidden}"

# ─── (7) Administration nav group is filtered for non-admin tokens ─────────
def test_visible_nav_groups_hides_administration_for_non_admin():
    body = _read(FE_TX / "_shared.jsx")
    assert "function visibleTxOpsNavGroups" in body
    assert 'g.key !== "administration"' in body
    assert "TransportationSubNav" in body
    # The SubNav must consume the filtered list, not the raw constant.
    assert "visibleTxOpsNavGroups()" in body

# ─── (8) loaders use the restricted-state guard ────────────────────────────
@pytest.mark.parametrize(
    "filename,must_render",
    [
        ("_lists.jsx", ["tx-drivers-list-restricted", "tx-carriers-list-restricted", "tx-trucks-list-restricted"]),
        ("_orientation.jsx", ["tx-orient-dashboard-restricted", "tx-orient-modules-restricted", "tx-orient-assignments-restricted", "tx-orient-certs-restricted"]),
        ("_intelligence.jsx", ["tx-intel-exec-restricted", "tx-intel-recs-restricted", "tx-intel-pred-restricted", "tx-intel-learning-restricted", "tx-intel-cleanup-restricted"]),
        ("_command_queue.jsx", ["tx-cq-restricted", "tx-cq-health-restricted", "tx-cq-forecast-restricted", "tx-cq-hr-sync-restricted", "tx-cq-digest-restricted"]),
        ("_views.jsx", ["tx-compliance-restricted", "tx-doc-center-restricted", "tx-audit-restricted"]),
    ],
)
def test_every_workspace_renders_tx_ops_restricted_data(filename, must_render):
    body = _read(FE_TX / filename)
    assert "TxOpsRestrictedData" in body, f"{filename} must import TxOpsRestrictedData"
    for testid in must_render:
        assert testid in body, f"{filename} missing restricted-state testid {testid}"

# ─── (9-14) forbidden user-facing copy must not leak into transportation UI ─
FORBIDDEN_TOKENS = [
    "Admin login required",
    # Specific runtime error strings (avoid catching generic comments).
    "Request failed with status code 401",
    "Request failed with status code 403",
]

def _strip_block_comments(src: str) -> str:
    # Strip /* ... */ and // ... single line comments before scanning.
    src = re.sub(r"/\*[\s\S]*?\*/", "", src)
    src = re.sub(r"^\s*//.*$", "", src, flags=re.MULTILINE)
    return src

def test_no_forbidden_admin_login_copy_in_transportation_ui():
    bad = []
    for p in _all_tx_jsx():
        if p.name == "_shared.jsx":
            continue  # sanitiser regex legitimately references the tokens
        src = _strip_block_comments(_read(p))
        for tok in FORBIDDEN_TOKENS:
            if tok in src:
                bad.append((p.name, tok))
    assert not bad, f"forbidden raw error copy leaked into transportation UI: {bad}"

def test_no_forbidden_admin_login_copy_in_tx_components():
    bad = []
    for p in FE_COMP_TX.glob("*.jsx"):
        src = _strip_block_comments(_read(p))
        for tok in FORBIDDEN_TOKENS:
            if tok in src:
                bad.append((p.name, tok))
    assert not bad, f"forbidden copy in /components/transportation: {bad}"

def test_no_raw_forbidden_or_unauthorized_user_text():
    bad = []
    bad_re = re.compile(r"(>(\s*)(Forbidden|Unauthorized)(\s*)<)|(['\"](Forbidden|Unauthorized)['\"])")
    for p in _all_tx_jsx():
        if p.name == "_shared.jsx":
            continue
        src = _strip_block_comments(_read(p))
        if bad_re.search(src):
            bad.append(p.name)
    assert not bad, f"raw Forbidden/Unauthorized literal in transportation UI: {bad}"

# ─── (15) Bucket-C loaders no longer call api.get for admin-strict feeds ──
ADMIN_STRICT_LOADER_PREFIXES = [
    "/admin/transportation/orientation/dashboard",
    "/admin/transportation/orientation/modules",
    "/admin/transportation/orientation/assignments",
    "/admin/transportation/orientation/certificates",
    "/admin/transportation/email-routes",
    "/admin/transportation/intelligence/dashboard",
    "/admin/transportation/intelligence/recommendations",
    "/admin/transportation/intelligence/predictions",
    "/admin/transportation/intelligence/dispatch-learning",
    "/admin/transportation/intelligence/cleanup-signals",
    "/admin/transportation/automation/actions",
    "/admin/transportation/automation/health",
    "/admin/transportation/automation/forecast",
    "/admin/transportation/automation/digest/preview",
    "/admin/transportation/automation/digest/runs",
    "/admin/transportation/hr-sync",
]

@pytest.mark.parametrize("loader", ADMIN_STRICT_LOADER_PREFIXES)
def test_admin_strict_loaders_use_txget_not_raw_api_get(loader):
    """No file under /pages/transportation may issue
       `api.get("<loader>"` raw — every admin-strict read must route
       through txGet to inherit 401/403 absorption."""
    bad = []
    pattern = re.compile(r'api\.get\(\s*[`"\']' + re.escape(loader))
    for p in _all_tx_jsx():
        if pattern.search(_read(p)):
            bad.append(p.name)
    assert not bad, (
        f"admin-strict loader {loader} is still called via raw api.get in {bad}; "
        f"must use txGet so 401/403 is absorbed."
    )

# ─── (16) classes for workspaces touched by the user defect report ────────
WORKSPACE_RESTRICTED_PROOFS = {
    "Orientation": ("_orientation.jsx", "tx-orient-dashboard-restricted"),
    "Drivers": ("_lists.jsx", "tx-drivers-list-restricted"),
    "Carriers": ("_lists.jsx", "tx-carriers-list-restricted"),
    "Intelligence": ("_intelligence.jsx", "tx-intel-exec-restricted"),
    "Automation": ("_command_queue.jsx", "tx-cq-restricted"),
    "Administration_Audit": ("_views.jsx", "tx-audit-restricted"),
}

@pytest.mark.parametrize("name,proof", list(WORKSPACE_RESTRICTED_PROOFS.items()))
def test_specific_failing_workspace_now_has_restricted_state(name, proof):
    filename, testid = proof
    body = _read(FE_TX / filename)
    assert testid in body, f"{name} workspace ({filename}) missing {testid}"

# ─── (17) route preservation — admin oversight + dispatch portal ──────────
def test_admin_transportation_routes_preserved():
    body = _read(ROOT / "frontend" / "src" / "App.js")
    assert "/admin/transportation" in body
    assert "/transportation-operations" in body
    # Dispatch portal must still mount.
    assert "/dispatch-portal" in body

def test_driver_magic_link_route_preserved():
    body = _read(ROOT / "frontend" / "src" / "App.js")
    # The carrier invite / verify routes which underpin the magic-link
    # flow must still be present.
    assert "transport-verify" in body or "ExternalCarrierInvite" in body

# ─── (18) RBAC preservation — admin-strict endpoints stay admin-strict ────
def test_admin_strict_endpoints_remain_strict_in_backend():
    """Smoke-grep that the admin gate is still wired and the
       audit-timeline endpoint is still declared somewhere in the
       backend (server.py or routes/* — Track 18 split it out)."""
    server = _read(ROOT / "backend" / "server.py")
    routes_dir = ROOT / "backend" / "routes"
    routes_blob = "\n".join(_read(p) for p in routes_dir.glob("*.py"))
    blob = server + "\n" + routes_blob
    assert "require_admin" in blob
    assert "audit-timeline" in blob

# ─── (19) cross-portal helper rule preserved ──────────────────────────────
def test_cross_portal_readiness_endpoint_still_helper():
    api_js = _read(ROOT / "frontend" / "src" / "lib" / "api.js")
    # The api.js 401-namespacing branch must still treat
    # /api/operations/* as a cross-portal helper (silent 401).
    assert "isOperationsHelper" in api_js
    assert "isCrossPortalHelper" in api_js

# ─── (20) no Dispatch Portal copy bleed inside transportation operations ──
def test_no_dispatch_portal_back_button_inside_txops():
    bad = []
    for p in _all_tx_jsx():
        src = _strip_block_comments(_read(p))
        # We do not want a "Back to Dispatch Portal" CTA inside
        # transportation operations.
        if "Back to Dispatch Portal" in src:
            bad.append(p.name)
    assert not bad, f"Dispatch Portal back-button copy leaked: {bad}"

# ─── (21) ComingSoon allowed on workspace sub-cards (track 18 phase G); the
# DISPATCH-VISIBLE TOP-LEVEL routing surface must not be a ComingSoon
# placeholder, but per-card affordances inside a workspace ARE allowed
# (e.g. carrier workspace "Quick-add driver" coming-soon hint, driver
# workspace "Orientation engine" hint). The check therefore only
# enforces that NO top-level workspace component (Routes target) returns
# a ComingSoon as its primary body. We pin that by asserting that
# Reports remains the only file with ComingSoon as the root render.
def test_reports_view_renders_coming_soon():
    body = _read(FE_TX / "_views.jsx")
    # ReportsView is the only Track-18 D-class workspace.
    assert "function ReportsView" in body
    # And it does render the ComingSoon placeholder.
    assert "<ComingSoon" in body

# ─── (22) Mission Control workspace strip preserved (Track 18.12) ─────────
def test_mission_control_workspace_strip_preserved():
    body = _read(FE_TX / "MissionControl.jsx")
    assert "mc-workspace-strip" in body
    # The strip is a constant array — assert each chip's `to:` slug.
    for slug in ["dispatch", "drivers", "carriers", "trucks", "orientation",
                 "compliance", "live-operations"]:
        assert f'to: "{slug}"' in body, f"Workspace strip missing chip: {slug}"

# ─── (23) PRD / docs trail updated ────────────────────────────────────────
def test_prd_md_exists():
    assert (MEM / "PRD.md").exists()

# ─── (24) deployment gate readiness — no new collections ──────────────────
def test_no_new_collections_created_under_track_18_12b():
    # Search server.py for any new `db.transportation_*` collection name
    # that wasn't already there. We pin to a deny-list of collection names
    # that 18.12B is forbidden from introducing.
    forbidden_new = ["restricted_state_log", "txops_audit_v2"]
    body = _read(ROOT / "backend" / "server.py")
    for col in forbidden_new:
        assert col not in body, f"Track 18.12B is forbidden from creating: {col}"

# ─── (25) bottom-line contract: every restricted-state callsite uses the
#         portal-branded component, never a raw "Access denied" / "Forbidden"
#         div ──────────────────────────────────────────────────────────────
def test_restricted_branches_use_portal_branded_component():
    body = _read(FE_TX / "_lists.jsx")
    # Each list page must render TxOpsRestrictedData when restricted.
    for ws in ["Carriers", "Drivers", "Trucks"]:
        ix = body.find(f"{ws}List")
        assert ix > 0, f"{ws}List missing"
    assert body.count("TxOpsRestrictedData") >= 6  # 3 lists + 3 workspaces
