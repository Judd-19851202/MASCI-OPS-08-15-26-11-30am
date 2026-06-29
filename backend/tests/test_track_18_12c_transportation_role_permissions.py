"""TRACK 18.12C · Transportation Role Permissions Real Functionality
Fix · static-scan lock.

Locks:
  • The OPS-GUARD alias on every endpoint reclassified to dispatcher-
    operational read-access.
  • Every admin-strict endpoint that MUST remain strict.
  • The `txHeaders()` helper in the frontend that fans out BOTH
    X-Admin-Token AND X-Dispatch-Token to admin-paths.
  • The VISIBLE = USABLE doctrine in `visibleTxOpsNavGroups()` and the
    per-page sub-tab filters (orientation, command-queue).
  • The four required Track 18.12C markdown documents exist.

These are pure source-tree checks; they do not hit the live backend.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path("/app")
BE_ROUTES = ROOT / "backend" / "routes"
FE_TX = ROOT / "frontend" / "src" / "pages" / "transportation"
MEM = ROOT / "memory"
SERVER = ROOT / "backend" / "server.py"


def _read(p: Path) -> str:
    assert p.exists(), f"required file missing: {p}"
    return p.read_text(encoding="utf-8", errors="ignore")


# ─── (1) Required documents ───────────────────────────────────────────────
def test_track_18_12c_fix_document_exists():
    assert (MEM / "TRACK_18_12C_TRANSPORTATION_ROLE_PERMISSIONS_FIX.md").exists()


def test_role_permission_matrix_document_exists():
    body = _read(MEM / "TRANSPORTATION_ROLE_PERMISSION_MATRIX.md")
    for needle in [
        "OPS-GUARD",
        "ADMIN-STRICT",
        "/api/admin/transportation/carriers",
        "/api/admin/transportation/persons",
        "/api/admin/transportation/trucks",
        "/api/admin/transportation/orientation/dashboard",
        "/api/admin/transportation/intelligence/cleanup-signals",
        "/api/admin/transportation/automation/actions",
        "/api/admin/transportation/automation/forecast",
        "/api/admin/transportation/audit-timeline",
        "/api/admin/transportation/hr-sync",
        "/api/admin/transportation/email-routes",
    ]:
        assert needle in body, f"role matrix missing: {needle}"


def test_workspace_functionality_audit_document_exists():
    body = _read(MEM / "TRANSPORTATION_WORKSPACE_FUNCTIONALITY_AUDIT.md")
    for ws in [
        "Mission Control", "Dispatch", "Live Operations", "Drivers",
        "Carriers", "Trucks", "Compliance", "Orientation",
        "Automation", "Cleanup", "Administration",
    ]:
        assert ws in body


# ─── (2) Backend gates · reclassified endpoints use OPS-GUARD ─────────────
DISPATCHER_OPERATIONAL_ENDPOINTS = [
    # (file, decorator-substring, must-include-token)
    ("transportation.py", '"/admin/transportation/carriers")',           "require_dispatch_or_admin_dep"),
    ("transportation.py", '"/admin/transportation/carriers/{cid}"',      "require_dispatch_or_admin_dep"),
    ("transportation.py", '"/admin/transportation/persons")',            "require_dispatch_or_admin_dep"),
    ("transportation.py", '"/admin/transportation/persons/{pid}"',       "require_dispatch_or_admin_dep"),
    ("transportation.py", '"/admin/transportation/trucks")',             "require_dispatch_or_admin_dep"),
    ("transportation.py", '"/admin/transportation/trucks/{tid}"',        "require_dispatch_or_admin_dep"),
    ("transportation.py", '"/admin/transportation/eligibility/{target_type}/{target_id}"', "require_dispatch_or_admin_dep"),
    ("transportation_experience.py",  '"/admin/transportation/documents/queue"',  "ops_guard"),
    ("transportation_experience.py",  '"/admin/transportation/inspections/queue"', "ops_guard"),
    ("transportation_experience.py",  '"/admin/transportation/carriers/{cid}/workspace"', "ops_guard"),
    ("transportation_experience.py",  '"/admin/transportation/persons/{pid}/workspace"',  "ops_guard"),
    ("transportation_experience.py",  '"/admin/transportation/trucks/{tid}/workspace"',   "ops_guard"),
    ("transportation_experience.py",  '"/admin/transportation/timeline/{entity_type}/{entity_id}"', "ops_guard"),
    ("transportation_orientation.py", '@router.get("/admin/transportation/orientation/dashboard"',    "ops_guard"),
    ("transportation_orientation.py", '@router.get("/admin/transportation/orientation/modules")',     "ops_guard"),
    ("transportation_orientation.py", '@router.get("/admin/transportation/orientation/assignments"',  "ops_guard"),
    ("transportation_orientation.py", '@router.get("/admin/transportation/orientation/certificates"', "ops_guard"),
    ("transportation_automation.py",  '"/admin/transportation/automation/actions")',      "require_dispatch_or_admin_dep"),
    ("transportation_automation.py",  '"/admin/transportation/automation/forecast"',      "require_dispatch_or_admin_dep"),
    ("transportation_intelligence.py", '"/cleanup-signals")',                              "ops_guard"),
    ("transportation_intelligence.py", '"/cleanup-signals/{signal_key}")',                 "ops_guard"),
]


@pytest.mark.parametrize("filename,decorator,gate", DISPATCHER_OPERATIONAL_ENDPOINTS)
def test_endpoint_uses_dispatch_or_admin_gate(filename, decorator, gate):
    body = _read(BE_ROUTES / filename)
    idx = body.find(decorator)
    assert idx > 0, f"decorator not found in {filename}: {decorator}"
    window = body[idx:idx + 1500]
    assert gate in window, (
        f"{filename}::{decorator} must depend on the dispatch-or-admin "
        f"gate ({gate}); window did not contain that identifier."
    )


# ─── (3) Backend · admin-strict endpoints stay strict ─────────────────────
ADMIN_STRICT_ENDPOINTS = [
    # (file, decorator-substring)
    ("transportation_experience.py", '"/admin/transportation/audit-timeline"'),
    ("transportation_intelligence.py", '"/cleanup-signals/{signal_key}/materialize-actions"'),
    ("transportation_intelligence.py", '"/dashboard"'),
    ("transportation_intelligence.py", '"/recommendations"'),
    ("transportation_intelligence.py", '"/predictions"'),
    ("transportation_intelligence.py", '"/dispatch-learning"'),
]


@pytest.mark.parametrize("filename,decorator", ADMIN_STRICT_ENDPOINTS)
def test_endpoint_remains_admin_strict(filename, decorator):
    body = _read(BE_ROUTES / filename)
    idx = body.find(decorator)
    assert idx > 0, f"decorator missing in {filename}: {decorator}"
    # Bound the window to the function body only (next decorator marks
    # the next route) so we don't accidentally grab a neighbour route.
    next_dec = body.find("@router.", idx + 1)
    end = next_dec if next_dec > 0 else idx + 1500
    window = body[idx:end]
    assert "Depends(require_admin_dep)" in window, (
        f"{filename}::{decorator} MUST remain admin-strict")
    # Must not have been silently widened to the dispatch-or-admin gate
    # WITHIN this endpoint's own body.
    assert "Depends(ops_guard)" not in window, (
        f"{filename}::{decorator} body must not depend on ops_guard")
    assert "Depends(require_dispatch_or_admin_dep)" not in window


# ─── (4) server.py wires the dispatch gate into the right registrations ──
def test_server_wires_experience_dispatch_gate():
    body = _read(SERVER)
    # The transportation experience router gets the dispatch dep.
    assert (
        "require_dispatch_or_admin_dep=_require_dispatch_or_admin"
        in body
    ), "server.py must pass the dispatch dep into the experience router"


def test_server_wires_orientation_dispatch_gate():
    body = _read(SERVER)
    # The transportation orientation router gets the dispatch dep.
    block = body
    assert "register_transportation_orientation_routes" in block
    # The orientation register-call must include the dispatch dep.
    # We look for the call site, then assert the dispatch dep token
    # appears within the next ~400 chars (the keyword-arg block).
    idx = block.find("register_transportation_orientation_routes(")
    assert idx > 0
    window = block[idx:idx + 600]
    assert "require_dispatch_or_admin_dep=_require_dispatch_or_admin" in window


def test_server_wires_intelligence_dispatch_gate():
    body = _read(SERVER)
    idx = body.find("register_track_16_12_routes(")
    assert idx > 0
    window = body[idx:idx + 600]
    assert "require_dispatch_or_admin_dep=_require_dispatch_or_admin" in window


# ─── (5) Frontend txHeaders helper sends BOTH tokens ──────────────────────
def test_tx_headers_sends_both_tokens():
    body = _read(FE_TX / "_shared.jsx")
    assert "function txHeaders()" in body
    # Must read the admin token AND the dispatch token.
    assert "getAdminToken()" in body
    assert "getDispatchToken()" in body
    # Must send both headers.
    head_block = body[body.find("function txHeaders()") : body.find("function txHeaders()") + 800]
    assert '"X-Admin-Token"' in head_block
    assert '"X-Dispatch-Token"' in head_block


def test_tx_get_routes_through_tx_headers():
    body = _read(FE_TX / "_shared.jsx")
    # The txGet wrapper must use the dual-header bundle, not the
    # legacy admin-only one — otherwise dispatchers can't authenticate
    # against the migrated endpoints.
    tx_get_start = body.find("export function txGet")
    assert tx_get_start > 0
    window = body[tx_get_start : tx_get_start + 1200]
    assert "txHeaders()" in window, "txGet must call txHeaders()"


# ─── (6) VISIBLE = USABLE — Administration + Intelligence hidden ─────────
def test_visible_nav_groups_hides_admin_governance_for_dispatch():
    body = _read(FE_TX / "_shared.jsx")
    assert "function visibleTxOpsNavGroups" in body
    # Administration group filtered out for non-admin.
    assert 'g.key !== "administration"' in body
    # Individual Class-C item filter set declared.
    assert "DISPATCH_HIDDEN_NAV_ITEMS" in body
    # Intelligence (admin-only deep analytics) must be in the hidden set.
    assert '"txops-nav-intelligence"' in body


def test_command_queue_hides_admin_sub_tabs_from_dispatch():
    body = _read(FE_TX / "_command_queue.jsx")
    assert "SUB_TABS_ALL" in body
    # The Health sub-tab must be marked NOT dispatch-visible.
    assert (
        '"tx-cq-tab-health"' in body
        and 'dispatch: false' in body
    ), "Command Queue health tab must be hidden from dispatchers"
    assert "isAdmin()" in body
    # The runtime filter must drop non-dispatch tabs for dispatchers.
    assert 'admin ? SUB_TABS_ALL : SUB_TABS_ALL.filter((t) => t.dispatch)' in body


def test_orientation_hides_admin_sub_tabs_from_dispatch():
    body = _read(FE_TX / "_orientation.jsx")
    assert "SUB_TABS_ALL" in body
    # Email Pilot is admin-only CMS — hidden from dispatch.
    assert (
        '"tx-orient-tab-emails"' in body
        and 'dispatch: false' in body
    )
    assert "isAdmin()" in body


# ─── (7) Admin paths remain registered (no route breakage) ────────────────
def test_admin_transportation_routes_still_mounted():
    body = _read(ROOT / "frontend" / "src" / "App.js")
    assert "/admin/transportation" in body
    assert "/transportation-operations" in body
    assert "/dispatch-portal" in body


# ─── (8) RBAC preservation — admin gate still wired on writes ─────────────
def test_carrier_write_endpoints_opened_to_dispatch_or_admin_track_19_00():
    """Track 19.00 (operator-approved) intentionally opened
    POST/PATCH /carriers from admin-only to `require_dispatch_or_admin_dep`.
    Visible = Usable doctrine: dispatchers must be able to manage the
    carrier base from inside Transportation Operations. Admin-only
    governance endpoints (audit timeline, intelligence admin, automation
    health, email pilot, HR sync) are NOT affected by this change."""
    body = _read(BE_ROUTES / "transportation.py")
    idx = body.find('@router.post("/admin/transportation/carriers")')
    assert idx > 0
    window = body[idx:idx + 800]
    assert "Depends(require_dispatch_or_admin_dep)" in window, (
        "Track 19.00 expects carrier POST to accept dispatch OR admin."
    )
    # PATCH must also be dispatch+admin.
    idx2 = body.find('@router.patch("/admin/transportation/carriers/{cid}")')
    assert idx2 > 0
    window2 = body[idx2:idx2 + 800]
    assert "Depends(require_dispatch_or_admin_dep)" in window2


def test_truck_write_endpoints_remain_admin_strict():
    body = _read(BE_ROUTES / "transportation.py")
    idx = body.find('@router.post("/admin/transportation/trucks")')
    assert idx > 0
    window = body[idx:idx + 800]
    assert "Depends(require_admin_dep)" in window


# ─── (9) No new collections under 18.12C ──────────────────────────────────
def test_no_new_collections():
    body = _read(SERVER)
    for col in [
        "dispatch_role_overrides",
        "transportation_role_permission_log",
        "txops_visible_state",
    ]:
        assert col not in body, f"forbidden new collection: {col}"


# ─── (10) The Mission Control workspace strip still intact ───────────────
def test_mission_control_workspace_strip_intact():
    body = _read(FE_TX / "MissionControl.jsx")
    assert "mc-workspace-strip" in body
    for slug in ["dispatch", "drivers", "carriers", "trucks", "orientation",
                 "compliance", "live-operations"]:
        assert f'to: "{slug}"' in body
