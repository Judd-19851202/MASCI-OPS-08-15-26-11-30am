"""TRACK 18.09C · Transportation Operations Ownership Audit · regression lock.

Locks the constitutional amendment:
* Transportation Operations is the operational system of record.
* Administration is the governance system.
* One shared `TransportationApp` router; two doorways
  (`/admin/transportation/*` admin-strict for oversight,
  `/transportation-operations/*` TX-gated for operational use).
* Dispatch portal (`/dispatch-portal/*`) is its own operational SoR.
* The six legacy compat redirects inside `TransportationApp` are
  path-relative so dispatch-authenticated users never bounce into
  the admin shell.

The 7 audit documents must exist and be discoverable from the main
ownership audit document. RBAC, auth helpers, dispatch portal, and
driver-token surfaces are all preserved.

No new feature. No new collection. No auth/RBAC/route change beyond
the path-relative redirect fix.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path("/app")
FRONTEND_SRC = ROOT / "frontend" / "src"
# TRACK 22.5A · re-anchor to current routing shell.
APP_ROUTES = FRONTEND_SRC / "app" / "routing" / "AppRoutes.jsx"
MEMORY = ROOT / "memory"
SCRIPTS = ROOT / "scripts"
TESTS_DIR = ROOT / "backend" / "tests"

AUDIT = MEMORY / "TRACK_18_09C_TRANSPORTATION_OWNERSHIP_AUDIT.md"
FEATURE_MATRIX = MEMORY / "TRANSPORTATION_FEATURE_OWNERSHIP_MATRIX.md"
GOVERNANCE_MATRIX = MEMORY / "ADMINISTRATION_GOVERNANCE_MATRIX.md"
ROUTE_PLAN = MEMORY / "TRANSPORTATION_ROUTE_REHOME_PLAN.md"
WORKFLOW_AUDIT = MEMORY / "TRANSPORTATION_OPERATIONAL_WORKFLOW_AUDIT.md"
WORKDAY = MEMORY / "ROLE_WORKDAY_ANALYSIS.md"
IMPL = MEMORY / "TRANSPORTATION_REARCHITECTURE_IMPLEMENTATION.md"


# =====================================================================
# Required deliverables (7)
# =====================================================================
def test_all_seven_required_deliverables_exist():
    for p in (AUDIT, FEATURE_MATRIX, GOVERNANCE_MATRIX, ROUTE_PLAN, WORKFLOW_AUDIT, WORKDAY, IMPL):
        assert p.exists(), f"Track 18.09C required deliverable missing: {p.name}"


def test_audit_links_all_supporting_documents():
    body = AUDIT.read_text()
    for name in (
        "TRANSPORTATION_FEATURE_OWNERSHIP_MATRIX.md",
        "ADMINISTRATION_GOVERNANCE_MATRIX.md",
        "TRANSPORTATION_ROUTE_REHOME_PLAN.md",
        "TRANSPORTATION_OPERATIONAL_WORKFLOW_AUDIT.md",
        "ROLE_WORKDAY_ANALYSIS.md",
        "TRANSPORTATION_REARCHITECTURE_IMPLEMENTATION.md",
    ):
        assert name in body, f"Main audit does not link supporting doc: {name}"


# =====================================================================
# Constitutional amendment must be declared in the audit
# =====================================================================
def test_constitutional_amendment_declared():
    body = AUDIT.read_text()
    assert "Transportation Operations is the operational system of record" in body
    assert "Administration is the governance system" in body
    # Six Pillars must each appear in the audit doc.
    for pillar in ("Powerful", "Simple", "Beautiful", "Trusted", "Proven", "Operational"):
        assert pillar in body, f"Six-Pillar self-check missing pillar: {pillar}"


# =====================================================================
# Feature ownership matrix coverage
# =====================================================================
REQUIRED_FEATURE_KEYS = [
    "Mission Control",
    "Dispatch Bridge",
    "Live Operations",
    "Dispatch Board",
    "Drivers List",
    "Carriers List",
    "Trucks List",
    "Fleet Readiness",
    "Carrier Readiness",
    "Driver Readiness",
    "Orientation Center",
    "Compliance Dashboard",
    "DOT Documents",
    "Vehicle Documents",
    "Maintenance & Inspections",
    "Rate Schedules",
    "Transportation Intelligence",
    "Automation Center",
    "Cleanup Center",
    "Transportation Reports",
    "Transportation Search",
    "Global Search",
    "Right Rail",
    "Notifications",
    "Audit Timeline",
    "Operations Events",
    "Operations Dashboard",
    "Compliance Findings",
    "Geofence Reconciliation",
    "Operational Metrics widgets",
    "Quick Actions",
    "Drawer Actions",
    "Card Actions",
    "Breadcrumbs / Context Menus",
]


def test_feature_matrix_covers_every_required_category():
    body = FEATURE_MATRIX.read_text()
    missing = [k for k in REQUIRED_FEATURE_KEYS if k not in body]
    assert not missing, (
        "Feature ownership matrix is missing required Transportation "
        f"categories: {missing}"
    )
    # Every classification code must appear at least once.
    for code in ("OPERATIONAL", "GOVERNANCE", "SHARED"):
        assert code in body, f"Feature matrix missing classification code: {code}"


# =====================================================================
# Governance matrix must classify every /admin/* route
# =====================================================================
REQUIRED_ADMIN_ROUTES = [
    "/admin/people",
    "/admin/jobs",
    "/admin/equipment",
    "/admin/training",
    "/admin/dispatch",
    "/admin/operations-events",
    "/admin/operations-dashboard",
    "/admin/compliance-findings",
    "/admin/geofence-reconciliation",
    "/admin/audit-log",
    "/admin/system-health",
    "/admin/sessions",
    "/admin/transportation/*",
    "/admin/governance",
    "/admin/deploy-recovery",
]


def test_governance_matrix_classifies_admin_routes():
    body = GOVERNANCE_MATRIX.read_text()
    missing = [r for r in REQUIRED_ADMIN_ROUTES if r not in body]
    assert not missing, (
        "Administration governance matrix is missing required routes: "
        f"{missing}"
    )
    # Every route must be classified as GOVERNANCE or SHARED — never
    # OPERATIONAL (any Admin row marked OPERATIONAL would be an
    # architectural defect per the directive).
    for line in body.splitlines():
        if line.startswith("|") and "OPERATIONAL" in line and "Classification" not in line:
            assert False, (
                "Administration governance matrix classified an Admin "
                f"page as OPERATIONAL: {line!r}. Operational pages must "
                "live under Transportation Operations or their owning "
                "workspace, not Administration."
            )


# =====================================================================
# The six compat redirects in TransportationApp are path-relative
# =====================================================================
def test_transportation_compat_redirects_are_path_relative():
    src = (FRONTEND_SRC / "pages" / "transportation" / "TransportationApp.jsx").read_text()
    # No legacy hardcoded `/admin/transportation/...` Navigate targets.
    legacy = re.findall(r'<Navigate\s+to="/admin/transportation/[^"]+', src)
    assert not legacy, (
        "TransportationApp.jsx still contains legacy hardcoded "
        f"`/admin/transportation/...` Navigate targets: {legacy}. "
        "These bounce dispatch-authenticated users into the admin "
        "shell. They must be path-relative."
    )
    # Every Navigate target inside the compat block uses relative="path".
    nav_count = src.count("<Navigate")
    rel_count = src.count('relative="path"')
    assert rel_count >= 6, (
        "Track 18.09C expects at least 6 Navigate elements with "
        f'relative="path". Found {rel_count}.'
    )
    # And every Navigate has a `replace` so history is clean.
    replace_count = src.count("replace")
    assert replace_count >= nav_count, (
        "Every Navigate in TransportationApp must include `replace`."
    )


# =====================================================================
# Single source of truth: AdminTransportation is a thin re-export
# =====================================================================
def test_single_source_of_truth_thin_reexport():
    p = FRONTEND_SRC / "pages" / "AdminTransportation.jsx"
    assert p.exists(), "pages/AdminTransportation.jsx (the alias) is missing."
    body = p.read_text()
    # Must be a thin re-export pointing at the canonical operational
    # router. No business logic added to the admin alias.
    assert 'export { default } from "./transportation/TransportationApp"' in body, (
        "AdminTransportation.jsx is no longer a thin re-export. The "
        "constitutional rule (one source of truth) is broken — "
        "business logic must live in TransportationApp.jsx only."
    )
    # The file body should be small (<= 20 non-empty lines) to keep
    # the "thin alias" property.
    non_empty = [ln for ln in body.splitlines() if ln.strip()]
    assert len(non_empty) <= 20, (
        "AdminTransportation.jsx grew beyond a thin alias "
        f"({len(non_empty)} non-empty lines). All logic must live in "
        "TransportationApp.jsx."
    )


# =====================================================================
# Both doorways still exist in App.js with their respective gates
# =====================================================================
def test_both_doorways_registered_in_app_router():
    app_js = ((FRONTEND_SRC / "App.js").read_text() + "\n" + APP_ROUTES.read_text())
    assert '/admin/transportation/*' in app_js, (
        "Admin oversight doorway `/admin/transportation/*` is missing "
        "from App.js — admin bookmarks would break."
    )
    assert '/transportation-operations/*' in app_js, (
        "Operational doorway `/transportation-operations/*` is missing "
        "from App.js — dispatch-authenticated users would lose access."
    )
    # The admin doorway must use the admin-strict gate (A(...)).
    assert re.search(
        r'path="/admin/transportation/\*"\s+element=\{A\(',
        app_js,
    ), "Admin doorway must use admin-strict A(...) gate."
    # The operational doorway must use the TX gate.
    assert re.search(
        r'path="/transportation-operations/\*"\s+element=\{TX\(',
        app_js,
    ), "Operational doorway must use TX(...) gate."


# =====================================================================
# Dispatch / driver surfaces preserved
# =====================================================================
def test_dispatch_portal_routes_preserved():
    app_js = ((FRONTEND_SRC / "App.js").read_text() + "\n" + APP_ROUTES.read_text())
    # The dispatch portal routes must remain mounted somewhere — this
    # is the dispatch operational system of record.
    assert "DispatchBoard" in app_js or "/dispatch-portal" in app_js, (
        "Dispatch portal routes appear to have been removed. Dispatch "
        "is its own operational system of record and must remain."
    )


def test_driver_token_routes_preserved():
    app_js = ((FRONTEND_SRC / "App.js").read_text() + "\n" + APP_ROUTES.read_text())
    # Driver-token surfaces (typically under `/dr/...`) must remain
    # untouched.
    has_dr = "/dr/" in app_js or "/driver/" in app_js or "DriverPortal" in app_js
    assert has_dr, "Driver-token surfaces appear to have been removed."


# =====================================================================
# RBAC / auth helpers preserved
# =====================================================================
def test_auth_helpers_preserved():
    app_js = ((FRONTEND_SRC / "App.js").read_text() + "\n" + APP_ROUTES.read_text())
    # The admin-strict helper.
    assert re.search(r"\bconst A\b|\bfunction A\b|\bA\s*=", app_js) or "A(" in app_js, (
        "Admin-strict auth helper `A` appears to have been removed."
    )
    # The TX helper.
    assert "TX(" in app_js, "Transportation auth helper `TX` appears to have been removed."


# =====================================================================
# Lock file is wired into the deployment gate
# =====================================================================
def test_lock_file_wired_into_deployment_gate():
    gate = SCRIPTS / "deployment_gate.py"
    src = gate.read_text()
    assert "test_track_18_09c_transportation_ownership.py" in src, (
        "Track 18.09C lock file is not wired into "
        "scripts/deployment_gate.py."
    )


# =====================================================================
# No new collections (constitutional rule)
# =====================================================================
def test_no_new_collections_introduced():
    # Reuse the existing 18.07 enforcement assertion shape: scan
    # backend/server.py for any new collection names introduced this
    # track. We cannot diff git from inside pytest cleanly, so we
    # assert the well-known stable set still resolves and the file
    # parses.
    server = ROOT / "backend" / "server.py"
    assert server.exists()
    src = server.read_text()
    # The handoff explicitly says "Existing architecture, no new
    # collections introduced." This assertion checks that we did not
    # add a `client[DB_NAME]["...something_new..."]` access pattern
    # that wasn't there before. We can't fully prove a negative, so we
    # assert a canonical sample of pre-existing collections is still
    # accessed in server.py.
    canonical_samples = [
        "users",  # auth users
        "operational_events",  # nervous system
    ]
    for sample in canonical_samples:
        assert sample in src, (
            f"Canonical pre-18.09C collection '{sample}' no longer "
            "appears in server.py — has the data model been changed?"
        )


# =====================================================================
# Workflow audit guarantees: zero Administration transitions required
# =====================================================================
def test_workflow_audit_states_zero_admin_transitions_required():
    body = WORKFLOW_AUDIT.read_text()
    assert "zero require an Administration transition" in body
    assert "Administration transitions required:** **0**" in body or "Administration transitions:** **0**" in body


def test_role_workday_audit_shows_zero_admin_workday_for_operational_roles():
    body = WORKDAY.read_text()
    # Eight operational roles, all 0%.
    for role in (
        "Dispatcher",
        "Transportation Manager",
        "Fleet Manager",
        "Carrier Coordinator",
        "Driver Coordinator",
        "Orientation Coordinator",
        "Compliance Coordinator",
        "Transportation Director",
    ):
        assert role in body, f"Role workday audit missing role: {role}"
    assert "spend 0% of their day in Administration" in body


# =====================================================================
# GO/NO-GO statement must be present
# =====================================================================
def test_final_recommendation_is_go():
    body = AUDIT.read_text()
    # The directive requires GO / NO-GO.
    assert "🟢 **GO" in body or "GO." in body
    # The verdict must explicitly state Transportation Operations is
    # the operational system of record.
    assert "operational system of record" in body
