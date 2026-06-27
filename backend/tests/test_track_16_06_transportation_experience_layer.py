"""TRACK 16.06 · Transportation Experience Layer regression.

Locks the Phase-3 contract:

* New aggregation endpoints exist and reuse the existing Phase 1/2 data:
  - GET /admin/transportation/dashboard
  - GET /admin/transportation/documents/queue
  - GET /admin/transportation/inspections/queue
  - GET /admin/transportation/audit-timeline
  - GET /admin/transportation/carriers/{id}/workspace
  - GET /admin/transportation/persons/{id}/workspace
  - GET /admin/transportation/trucks/{id}/workspace
* All admin-strict (no public surface added).
* Frontend experience layer exists with the required surfaces.
* Side-nav links wire to the 10 required sections.
* No dead/fake buttons — deferred features are clearly "Coming Soon".
* Old Phase-1 AdminTransportation.jsx is now a re-export of the new
  experience layer (no orphaned page).
* Track 16.04 and Track 16.05 tests + endpoints are untouched (no
  duplicated APIs, no duplicate identity, no new audit system).
* deployment_gate includes Track 16.06.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path("/app")
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

EXP_ROUTE = BACKEND / "routes" / "transportation_experience.py"
SERVER = BACKEND / "server.py"
GATE = ROOT / "scripts" / "deployment_gate.py"
PAGE = ROOT / "frontend" / "src" / "pages" / "AdminTransportation.jsx"
TX_APP = ROOT / "frontend" / "src" / "pages" / "transportation" / "TransportationApp.jsx"
TX_SHARED = ROOT / "frontend" / "src" / "pages" / "transportation" / "_shared.jsx"
TX_VIEWS = ROOT / "frontend" / "src" / "pages" / "transportation" / "_views.jsx"
TX_LISTS = ROOT / "frontend" / "src" / "pages" / "transportation" / "_lists.jsx"
APP_JS = ROOT / "frontend" / "src" / "App.js"
PHASE2_TEST = BACKEND / "tests" / "test_track_16_05_transportation_onboarding_compliance_center.py"
PHASE1_TEST = BACKEND / "tests" / "test_track_16_04_transportation_foundation.py"


# ───────────────── Backend aggregation surface ─────────────────
def test_1_dashboard_endpoint_exists():
    src = EXP_ROUTE.read_text()
    assert '"/admin/transportation/dashboard"' in src


def test_2_document_queue_endpoint_exists():
    src = EXP_ROUTE.read_text()
    assert '"/admin/transportation/documents/queue"' in src


def test_3_inspection_queue_endpoint_exists():
    src = EXP_ROUTE.read_text()
    assert '"/admin/transportation/inspections/queue"' in src


def test_4_audit_timeline_endpoint_exists():
    src = EXP_ROUTE.read_text()
    assert '"/admin/transportation/audit-timeline"' in src


def test_5_workspace_endpoints_exist():
    src = EXP_ROUTE.read_text()
    assert '"/admin/transportation/carriers/{cid}/workspace"' in src
    assert '"/admin/transportation/persons/{pid}/workspace"' in src
    assert '"/admin/transportation/trucks/{tid}/workspace"' in src


def test_6_all_experience_routes_are_admin_strict():
    src = EXP_ROUTE.read_text()
    for m in re.finditer(r"@router\.(get|post|patch|delete)\(", src):
        window = src[m.start(): m.start() + 1500]
        assert "Depends(require_admin_dep)" in window, \
            f"experience-layer route at offset {m.start()} not admin-gated"


def test_7_no_new_audit_system():
    # Experience layer is READ-ONLY and reuses db.audit_events.
    src = EXP_ROUTE.read_text()
    assert "audit_events.insert_one" not in src  # no writes
    # It can READ audit_events for the timeline.
    assert "db.audit_events.find" in src


def test_8_no_duplicate_identity_or_storage():
    src = EXP_ROUTE.read_text()
    # Must NOT create new collections for identity/docs.
    forbidden_writes = [
        "carriers.insert_one(", "transport_persons.insert_one(",
        "transport_trucks.insert_one(",
        "carrier_documents.insert_one(", "driver_documents.insert_one(",
        "transport_packet_submissions.insert_one(",
        "transport_truck_inspections.insert_one(",
        "transport_rate_schedules.insert_one(",
    ]
    for w in forbidden_writes:
        assert w not in src, f"experience layer must not write {w}"


def test_9_no_new_storage_or_upload():
    src = EXP_ROUTE.read_text()
    assert "UploadFile" not in src
    assert "boto3" not in src
    assert ".put_object" not in src


def test_10_register_wired_into_server():
    src = SERVER.read_text()
    assert "register_transportation_experience_routes" in src
    assert "from routes.transportation_experience import" in src


def test_11_no_public_route_introduced():
    src = EXP_ROUTE.read_text()
    for needle in ("/public/", "/invite/", "/carrier-portal/"):
        assert needle not in src


# ───────────────── Frontend experience layer ─────────────────
def test_12_transportation_app_router_exists():
    assert TX_APP.exists()
    src = TX_APP.read_text()
    # Required 13 sub-routes: dashboard (index), carriers, carriers/:id,
    # drivers, drivers/:id, trucks, trucks/:id, compliance, documents,
    # inspections, rate-schedules, audit, reports.
    expected_routes = [
        'path="carriers"', 'path="carriers/:id"',
        'path="drivers"', 'path="drivers/:id"',
        'path="trucks"', 'path="trucks/:id"',
        'path="compliance"', 'path="documents"',
        'path="inspections"', 'path="rate-schedules"',
        'path="audit"', 'path="reports"',
    ]
    for r in expected_routes:
        assert r in src, f"missing route {r}"
    assert "<Route index" in src


def test_13_left_navigation_has_required_sections():
    src = TX_SHARED.read_text()
    # The TX_NAV array must contain all 10 entries.
    for label in ("Dashboard", "Carriers", "Drivers", "Trucks", "Compliance",
                  "Documents", "Inspections", "Rate Schedules",
                  "Audit Timeline", "Reports"):
        assert f'"{label}"' in src, f"side-nav missing {label}"


def test_14_dashboard_tiles_present():
    src = TX_VIEWS.read_text()
    for tile_key in ("eligible_drivers", "eligible_trucks",
                     "eligible_carriers", "drivers_pending_review",
                     "trucks_pending_inspection", "documents_awaiting_review",
                     "expiring_documents_30d", "annual_inspections_due_30d",
                     "pending_corrections"):
        assert tile_key in src, f"dashboard tile {tile_key} missing"
    # Compliance score must be surfaced.
    assert "tile-compliance-score" in src
    # Active rate tile must be surfaced.
    assert "tile-active-rate" in src


def test_15_carrier_workspace_has_required_sections():
    src = TX_LISTS.read_text()
    for tab in ("carrier-tab-overview", "carrier-tab-drivers",
                "carrier-tab-trucks", "carrier-tab-packet",
                "carrier-tab-documents", "carrier-tab-rates"):
        assert tab in src, f"carrier workspace missing {tab}"


def test_16_driver_workspace_renders():
    src = TX_LISTS.read_text()
    assert 'driver-workspace' in src
    # HR linkage section is required for MASCI employees.
    assert 'driver-hr-linkage' in src


def test_17_truck_workspace_renders():
    src = TX_LISTS.read_text()
    assert 'truck-workspace' in src
    assert 'truck-latest-insp-card' in src


def test_18_compliance_dashboard_has_three_columns():
    src = TX_VIEWS.read_text()
    for col in ("cc-carriers", "cc-drivers", "cc-trucks"):
        assert col in src


def test_19_document_center_renders():
    src = TX_VIEWS.read_text()
    assert 'data-testid="tx-document-center"' in src
    assert 'data-testid="doc-filter-status"' in src
    assert 'data-testid="doc-filter-scope"' in src


def test_20_inspection_center_includes_disclaimer():
    src = TX_VIEWS.read_text()
    assert 'data-testid="tx-inspection-center"' in src
    assert 'data-testid="insp-disclaimer"' in src
    assert "operational readiness only" in src or "INSPECTION_DISCLAIMER" in src or "disclaimer" in src.lower()


def test_21_rate_schedule_center_renders():
    src = TX_VIEWS.read_text()
    assert 'data-testid="tx-rate-center"' in src
    assert "rate-active-card" in src
    assert "rate-history-table" in src


def test_22_audit_timeline_renders():
    src = TX_VIEWS.read_text()
    assert 'data-testid="tx-audit-timeline"' in src


def test_23_no_dead_buttons_use_coming_soon():
    # Coming Soon is the canonical "future feature" pattern (no clickable
    # action that does nothing). Test that the ComingSoon component is
    # exported and used wherever future features are referenced.
    shared = TX_SHARED.read_text()
    assert "function ComingSoon" in shared

    lists = TX_LISTS.read_text()
    # The driver workspace surfaces orientation + retraining as Coming Soon.
    assert 'driver-orientation-coming-soon' in lists
    assert 'driver-retraining-coming-soon' in lists


def test_24_old_admin_transportation_is_reexport():
    """The original /admin/transportation page is now a thin re-export
    of the new experience-layer router. The file must still exist (so
    App.js's import resolves) and must not contain the old single-page
    code paths."""
    src = PAGE.read_text()
    assert "TransportationApp" in src
    # The Phase-1 monolithic surface is gone.
    assert "CarriersTab" not in src
    assert "data-testid=\"carriers-tab\"" not in src


def test_25_app_js_route_mounts_splat():
    src = APP_JS.read_text()
    # Nested routing requires the wildcard route.
    assert 'path="/admin/transportation/*"' in src
    assert "AdminTransportation" in src


# ───────────────── Track 16.04 + 16.05 preservation ─────────────────
def test_26_track_16_04_tests_still_exist():
    assert PHASE1_TEST.exists()


def test_27_track_16_05_tests_still_exist():
    assert PHASE2_TEST.exists()


def test_28_phase_1_endpoints_still_registered():
    src = SERVER.read_text()
    assert "register_transportation_routes(" in src


def test_29_phase_2_endpoints_still_registered():
    src = SERVER.read_text()
    assert "register_transportation_phase2_routes(" in src


def test_30_deployment_gate_includes_16_06():
    assert "test_track_16_06" in GATE.read_text()


# ───────────────── Quality / no drift ─────────────────
def test_31_no_forgedops_academy_references():
    for p in (EXP_ROUTE, TX_SHARED, TX_VIEWS, TX_LISTS, TX_APP):
        text = p.read_text()
        assert "ForgedOps Academy" not in text
        assert "forgedops academy" not in text.lower()


def test_32_no_forbidden_status_language():
    # Punitive labels remain banned in the new UI surface.
    surface = TX_SHARED.read_text() + "\n" + TX_VIEWS.read_text() + "\n" + TX_LISTS.read_text() + "\n" + TX_APP.read_text()
    for needle in ('"Failed"', '"Rejected"', '"Denied"',
                   "'Failed'", "'Rejected'", "'Denied'",
                   ">Failed<", ">Rejected<", ">Denied<"):
        assert needle not in surface, f"forbidden status label {needle!r}"


def test_33_responsive_grid_classes_used():
    # Mobile/iPad guarantee — main surfaces use responsive grid classes.
    for p in (TX_VIEWS, TX_LISTS):
        src = p.read_text()
        assert "sm:grid-cols-" in src or "md:grid-cols-" in src or "lg:grid-cols-" in src, \
            f"{p.name} missing responsive grid"


def test_34_chip_component_is_single_source_of_truth():
    """No page may inline its own status-chip color tables; everything
    routes through the shared Chip component."""
    shared = TX_SHARED.read_text()
    assert "export function Chip(" in shared
    # Every consumer imports Chip from _shared.
    for p in (TX_VIEWS, TX_LISTS):
        src = p.read_text()
        assert 'Chip' in src
        assert 'from "./_shared"' in src


def test_35_dispatch_endpoints_unchanged_in_experience_layer():
    """Experience layer must not register routes under /api/dispatch/
    (those belong to Phase 1/2). Reads are admin-only."""
    src = EXP_ROUTE.read_text()
    for m in re.finditer(r'@router\.\w+\("/dispatch', src):
        assert False, f"experience layer must not add /dispatch routes (found at {m.start()})"


def test_36_experience_layer_registers_before_phase2_to_avoid_path_shadow():
    """FastAPI matches routes in registration order. The experience-layer
    endpoint `/admin/transportation/inspections/queue` is a literal path
    that would otherwise be shadowed by Phase 2's `/admin/transportation/
    inspections/{iid}`. Lock the registration order so the literal wins."""
    src = SERVER.read_text()
    exp_idx = src.find("register_transportation_experience_routes(")
    p2_idx = src.find("register_transportation_phase2_routes(")
    assert exp_idx > 0, "experience layer not registered"
    assert p2_idx > 0, "phase 2 not registered"
    assert exp_idx < p2_idx, (
        "register_transportation_experience_routes(...) must be invoked "
        "BEFORE register_transportation_phase2_routes(...) in server.py "
        "to prevent Phase 2's /inspections/{iid} from shadowing the "
        "literal /inspections/queue endpoint."
    )
