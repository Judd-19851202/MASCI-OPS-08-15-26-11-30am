"""Track 19.08 — Operational Forms Forensic Audit · Drift-detection Snapshots.

Audit-only lock tests. Snapshots the ecosystem's public surface — routes,
collections, notification / email / PDF hooks, form-shell primitives — so any
future drift fails the suite until `/app/memory/TRACK_19_08_AUDIT/*` is
refreshed to reflect the new reality.

**These tests do not modify any application behaviour.** They inspect source
files only.

Snapshot baselines are computed as *lower bounds*. That way:
* Adding a new route / collection / hook does NOT fail the suite (the ecosystem
  is expected to grow).
* REMOVING one of the audited surfaces DOES fail — because the audit doc has
  documented that surface as present.

Update procedure: when a legitimate deprecation removes a surface, update the
matching audit document AND bump the constant in this file.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND = REPO_ROOT / "backend"
FRONTEND = REPO_ROOT / "frontend"
MEMORY = REPO_ROOT / "memory"
AUDIT = MEMORY / "TRACK_19_08_AUDIT"


# --- Audit-document presence -------------------------------------------------


AUDIT_DOCS = [
    "00_EXECUTIVE_ARCHITECTURE_REPORT.md",
    "01_MASTER_FORM_INVENTORY.md",
    "02_MASTER_ROUTE_INVENTORY.md",
    "03_MASTER_FIELD_DICTIONARY.md",
    "04_UI_COMPONENT_ATLAS.md",
    "05_BUTTON_TRIGGER_ENCYCLOPEDIA.md",
    "06_INSPECTION_ENGINE_SPECIFICATION.md",
    "07_FAIL_CASCADE_ANALYSIS.md",
    "08_SHOP_PM_SAFETY_INTEGRATION_MAP.md",
    "09_NOTIFICATION_EMAIL_PDF_MATRIX.md",
    "10_DATA_FLOW_TRACE.md",
    "11_DUPLICATE_LOGIC_REPORT.md",
    "12_UX_FRICTION_AND_SAFETY_MEETING_FORENSICS.md",
    "13_INDUSTRY_COMPARISON.md",
    "14_REDESIGN_PROTECTION_MATRIX.md",
    "15_ROOT_CAUSE_ANALYSIS.md",
    "16_EXECUTIVE_RECOMMENDATIONS_AND_CONSISTENCY_AND_VALUE.md",
]


@pytest.mark.parametrize("doc", AUDIT_DOCS)
def test_audit_document_present(doc):
    p = AUDIT / doc
    assert p.exists(), f"Track 19.08 audit doc missing: {doc}"
    # Documents must have non-trivial content.
    assert p.stat().st_size > 800, f"Audit doc too small: {doc}"


# --- Backend surface snapshots ----------------------------------------------


def _all_backend_source():
    srcs = []
    srcs.append((BACKEND / "server.py").read_text(encoding="utf-8"))
    for p in sorted((BACKEND / "routes").glob("*.py")):
        srcs.append(p.read_text(encoding="utf-8"))
    return "\n".join(srcs)


BACKEND_SRC = _all_backend_source()


def _count_route_declarations():
    return len(re.findall(r"@(?:api_)?router\.[a-z]+\(\"[^\"]+\"", BACKEND_SRC))


def _unique_collections():
    return set(re.findall(r"db\.([a-z_][a-z0-9_]*)", BACKEND_SRC))


def _count_email_hooks():
    return len(re.findall(r"schedule_auto_email\(", BACKEND_SRC))


def _count_weasyprint_refs():
    return len(re.findall(r"weasyprint|WeasyPrint", BACKEND_SRC))


# ---- Snapshot lower bounds captured 2026-07-01 ------------------------------
# Ecosystem may GROW past these numbers freely; a DROP below fails the lock.

SNAPSHOT_ROUTES_MIN = 900
SNAPSHOT_COLLECTIONS_MIN = 140
SNAPSHOT_EMAIL_HOOKS_MIN = 10
SNAPSHOT_WEASYPRINT_REFS_MIN = 5


def test_route_declaration_count_did_not_regress():
    n = _count_route_declarations()
    assert n >= SNAPSHOT_ROUTES_MIN, (
        f"Backend route declarations regressed: {n} < {SNAPSHOT_ROUTES_MIN}. "
        f"If a deprecation removed a route, update TRACK_19_08_AUDIT/"
        f"02_MASTER_ROUTE_INVENTORY.md and lower SNAPSHOT_ROUTES_MIN."
    )


def test_mongo_collection_reference_count_did_not_regress():
    cols = _unique_collections()
    assert len(cols) >= SNAPSHOT_COLLECTIONS_MIN, (
        f"Mongo collection surface regressed: {len(cols)} < {SNAPSHOT_COLLECTIONS_MIN}"
    )


def test_email_hook_count_did_not_regress():
    n = _count_email_hooks()
    assert n >= SNAPSHOT_EMAIL_HOOKS_MIN, (
        f"schedule_auto_email hooks regressed: {n} < {SNAPSHOT_EMAIL_HOOKS_MIN}"
    )


def test_weasyprint_reference_count_did_not_regress():
    n = _count_weasyprint_refs()
    assert n >= SNAPSHOT_WEASYPRINT_REFS_MIN, (
        f"WeasyPrint references regressed: {n} < {SNAPSHOT_WEASYPRINT_REFS_MIN}"
    )


# --- Critical routes MUST still exist ----------------------------------------

# Each of these is documented in the audit as a live surface. Removing one
# without updating the audit would silently break a documented workflow.

CRITICAL_BACKEND_ROUTES = [
    # Daily Report family
    "/daily-reports",
    "/jobs/{project_number}/recent-context",
    "/hr/employee-roster",
    # Equipment
    "/equipment-inspections",
    # DVIR / Fleet
    "/fleet/inspections",
    "/fleet/defects/{defect_id}",
    "/shop/fleet/defects",
    "/shop/fleet/defects/{defect_id}/acknowledge",
    "/shop/fleet/defects/{defect_id}/assign",
    "/shop/fleet/defects/{defect_id}/start",
    "/shop/fleet/defects/{defect_id}/repair",
    "/dispatch/fleet/defects/{defect_id}/clear",
    "/dispatch/fleet/units/{unit_number}/oos",
    "/dispatch/fleet/status",
    "/fleet/units",
    # Meetings
    "/meetings",
    "/meetings/{meeting_id}",
    # Incidents
    "/incidents",
    "/incidents/{incident_id}",
    "/incidents/{incident_id}/lifecycle",
    "/incidents/{incident_id}/transition",
    "/incidents/{incident_id}/state-events",
    "/incidents.csv",
    # JHA
    "/jhas",
    "/jhas/{jha_id}",
    "/jha-acknowledgements",
    "/jha-acknowledgements/compliance",
    "/jha-acknowledgements/me",
    "/jha-acknowledgements/by-employee/{employee_id}",
    "/jha-acknowledgements/by-project/{project_number}",
    # Corrective actions
    "/corrective-actions",
    "/hr/corrective-actions",
    # Safety equipment
    "/equipment-issuances",
    "/equipment-issuances/{rec_id}",
    "/equipment-issuances/{rec_id}/return",
    "/equipment-issuances/{rec_id}/pdf",
    "/equipment-issuances/{rec_id}/return/pdf",
    "/equipment-trainings",
    "/equipment-trainings/{rec_id}",
]


@pytest.mark.parametrize("route", CRITICAL_BACKEND_ROUTES)
def test_critical_backend_route_still_present(route):
    assert route in BACKEND_SRC, (
        f"Documented critical route disappeared: {route}. "
        f"If intentional, update TRACK_19_08_AUDIT/02_MASTER_ROUTE_INVENTORY.md."
    )


# --- Critical collections MUST still be referenced ---------------------------

CRITICAL_COLLECTIONS = [
    "daily_reports",
    "incidents",
    "meetings",
    "equipment_inspections",
    "fleet_audit",
    "fleet_defects",
    "fleet_status",
    "jhas",
    "jha_acknowledgements",
    "corrective_actions",
    "trench_excavations",
    "employees",
    "equipment_master",
    "audit_events",
    "email_routes",
    "notifications",
    "inspections",
]


@pytest.mark.parametrize("collection", CRITICAL_COLLECTIONS)
def test_critical_collection_still_referenced(collection):
    assert f"db.{collection}" in BACKEND_SRC, (
        f"Documented critical Mongo collection dropped: {collection}"
    )


# --- Critical email workflow keys MUST still be fired ------------------------

CRITICAL_EMAIL_WORKFLOWS = [
    "daily-report",
    "dvir",
    "equipment-inspection",
    "meeting",
    "incident",
    # Fleet defect workflow keys use per-state names (defect_open,
    # defect_assigned, defect_cleared, …). One representative sample:
    "defect_open",
]


@pytest.mark.parametrize("wf", CRITICAL_EMAIL_WORKFLOWS)
def test_critical_email_workflow_still_fires(wf):
    # Match either quoted argument in schedule_auto_email("<wf>" ...) or
    # nearby template usage.
    quoted = f'"{wf}"'
    single = f"'{wf}'"
    assert quoted in BACKEND_SRC or single in BACKEND_SRC, (
        f"Documented email workflow key missing: {wf}"
    )


# --- Frontend form-shell primitives MUST still be mounted -------------------


FRONTEND_FORMS = [
    "NewDailyReport.jsx",
    "NewEquipmentInspection.jsx",
    "NewFleetDVIR.jsx",
    "NewMeeting.jsx",
    "NewIncident.jsx",
    "NewInspection.jsx",
    "NewQaqcInspection.jsx",
    "NewSafetyEquipmentIssuance.jsx",
    "NewSafetyEquipmentTraining.jsx",
]


@pytest.mark.parametrize("f", FRONTEND_FORMS)
def test_form_page_still_present(f):
    p = FRONTEND / "src/pages" / f
    assert p.exists(), f"Documented form page dropped: {f}"


APP_JS = (FRONTEND / "src/App.js").read_text(encoding="utf-8")


CRITICAL_FRONTEND_ROUTES = [
    "/daily/new",
    "/incidents/new",
    "/equipment/new",
    "/fleet/dvir/new",
    "/meetings/new",
    "/inspections/new",
    "/jha",
    "/qaqc",
    "/constraints",
    "/leadership",
    "/safety/forms/equipment-issuance/new",
    "/safety/forms/equipment-training/new",
    "/trench-safety",
]


@pytest.mark.parametrize("route", CRITICAL_FRONTEND_ROUTES)
def test_critical_frontend_route_still_mounted(route):
    assert f'path="{route}' in APP_JS, (
        f"Documented frontend route disappeared: {route}. "
        f"Update TRACK_19_08_AUDIT/02_MASTER_ROUTE_INVENTORY.md if intentional."
    )


# --- Historical immutability still enforced ---------------------------------


def test_daily_reports_delete_still_returns_410():
    routes_src = (BACKEND / "routes/daily_reports.py").read_text(encoding="utf-8")
    # Look for the 410 status_code on the DELETE route.
    assert "@api_router.delete(\"/daily-reports/{report_id}\"" in routes_src
    assert "410" in routes_src


def test_legacy_admin_login_still_returns_410():
    """Track 15.32 retired the shared-password admin login. It must still
    return 410 (documented in 02_MASTER_ROUTE_INVENTORY.md)."""
    # This endpoint lives in server.py or a dedicated file — check both.
    hit = "shared-password admin login was retired" in BACKEND_SRC
    assert hit, "Legacy /api/admin/login 410 retirement message drifted"


# --- Trust-spine primitive check --------------------------------------------


def test_audit_events_collection_still_referenced():
    """Every submit path emits audit_events with a correlation id.
    Removal of this collection reference would break Trust Spine."""
    assert BACKEND_SRC.count("db.audit_events") >= 5, (
        "Trust-Spine audit_events writes appear to have regressed."
    )


# --- HR canonical roster still present ---------------------------------------


def test_hr_canonical_roster_endpoint_still_present():
    """Track 19.03 established /api/hr/employee-roster as SoT for identity
    on every operational form. Removing it would break every EmployeeCombo."""
    assert "/hr/employee-roster" in BACKEND_SRC


# --- Excavation hard-gate still present -------------------------------------


def test_excavation_hard_gate_still_enforced():
    """Track 19.05 audit documented the excavation_record_required gate on
    the Daily Report submit path."""
    routes_src = (BACKEND / "routes/daily_reports.py").read_text(encoding="utf-8")
    assert "excavation_record_required" in routes_src, (
        "Excavation hard-gate removed from daily-reports submit."
    )


# --- Track 19.06 amendment primitive still lives (Smart Prefill + reset) -----


def test_amendment_reset_hours_still_present():
    """Track 19.06 amendment shipped the per-row Reset hours affordance
    powered by row._prefilled and the useList.patch primitive."""
    dr = (FRONTEND / "src/pages/NewDailyReport.jsx").read_text(encoding="utf-8")
    assert 'data-testid={`crew-reset-hours-${i}`}' in dr
    assert "row._prefilled &&" in dr
    assert "idx === i ? { ...row, ...partial } : row" in dr


# --- Meta assertion — snapshot summary ---------------------------------------


def test_snapshot_summary_records_current_bounds():
    """Sanity: print the current numbers so a failing run has context."""
    n_routes = _count_route_declarations()
    n_cols = len(_unique_collections())
    n_email = _count_email_hooks()
    n_weasy = _count_weasyprint_refs()
    # We assert each above; this test simply must not fail. Its output on
    # failure of another lock helps the human diagnose without re-running.
    assert (n_routes, n_cols, n_email, n_weasy) >= (
        SNAPSHOT_ROUTES_MIN, SNAPSHOT_COLLECTIONS_MIN,
        SNAPSHOT_EMAIL_HOOKS_MIN, SNAPSHOT_WEASYPRINT_REFS_MIN,
    ), (
        f"Ecosystem surface below documented snapshot: "
        f"routes={n_routes} cols={n_cols} email={n_email} weasy={n_weasy}"
    )
