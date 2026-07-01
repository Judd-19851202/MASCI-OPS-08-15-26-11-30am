"""Track 19.16 · UX Hardening Batch 2 · LOCK TESTS.

Scope
-----
* Incident report schema wires the 3 pickers (employee/equipment/vehicle)
  into the correct branches.
* IncidentReport.jsx renders the three new picker field types.
* PersonnelListField + WitnessesField use EmployeeCombo for internal-employee rows.
* PhotoField exposes count / preview / reorder / a11y controls.
* Review page carries platform-selected + photo + witness counters.
* Backend engine, workspace, intelligence, reports files untouched.
* Legacy redirects still in place.
* Prior lock tests still pass (regression guarded elsewhere).
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path("/app")
FE_ROOT = REPO_ROOT / "frontend/src"


# ── Schema wiring ───────────────────────────────────────────────────
def test_schema_vehicle_step_uses_vehicle_and_employee_pickers():
    src = (FE_ROOT / "lib/incidentReportSchema.js").read_text(encoding="utf-8")
    idx = src.index('key: "vehicle"')
    window = src[idx: idx + 1500]
    assert 'key: "vehicle_ids", type: "vehicle_picker"' in window
    assert 'key: "drivers", type: "employee_picker"' in window
    # No lingering plain-text on the fleet fields.
    assert 'key: "vehicle_ids", type: "text"' not in src
    assert 'key: "drivers", type: "text"' not in src


def test_schema_equipment_step_uses_equipment_picker_and_operator_picker():
    src = (FE_ROOT / "lib/incidentReportSchema.js").read_text(encoding="utf-8")
    idx = src.index('key: "equipment"')
    window = src[idx: idx + 1500]
    assert 'key: "equipment_id", type: "equipment_picker"' in window
    assert 'key: "operator_name", type: "employee_picker"' in window


def test_schema_injury_step_uses_employee_picker():
    src = (FE_ROOT / "lib/incidentReportSchema.js").read_text(encoding="utf-8")
    assert 'key: "injured_employee", type: "employee_picker"' in src


# ── Field renderers ─────────────────────────────────────────────────
def test_incident_report_registers_three_new_picker_types():
    src = (FE_ROOT / "pages/IncidentReport.jsx").read_text(encoding="utf-8")
    for typ in ("employee_picker", "equipment_picker", "vehicle_picker"):
        assert f'field.type === "{typ}"' in src, f"missing wiring for {typ}"
    # And their renderer components.
    assert "EmployeePickerField" in src
    assert "EquipmentPickerField" in src


def test_incident_report_reuses_existing_combos():
    """Zero duplication: pickers must reuse EmployeeCombo + EquipmentCombo."""
    src = (FE_ROOT / "pages/IncidentReport.jsx").read_text(encoding="utf-8")
    assert 'from "@/components/EmployeeCombo"' in src
    assert 'from "@/components/EquipmentCombo"' in src


def test_vehicle_picker_filters_equipment_master_by_fleet_categories():
    src = (FE_ROOT / "pages/IncidentReport.jsx").read_text(encoding="utf-8")
    assert "VEHICLE_CATEGORIES" in src
    # All fleet-y equipment_master categories are named explicitly so
    # the vehicle picker filters correctly.
    for cat in ("Pickup Trucks", "Dump Trucks", "Flatbed Trucks",
                "Tractor Trailer Trucks"):
        assert f'"{cat}"' in src, f"missing fleet category {cat!r}"


# ── Personnel + Witnesses renderers hydrate the roster ─────────────
def test_personnel_list_uses_employee_combo():
    src = (FE_ROOT / "pages/IncidentReport.jsx").read_text(encoding="utf-8")
    idx = src.index("function PersonnelListField(")
    window = src[idx: idx + 2500]
    assert "EmployeeCombo" in window
    # Roster-selected badge appears on picked rows.
    assert 'data-testid={`${testId}-row-${i}-roster-hint`}' in window


def test_witnesses_uses_employee_combo_for_internal_employee_only():
    src = (FE_ROOT / "pages/IncidentReport.jsx").read_text(encoding="utf-8")
    idx = src.index("function WitnessesField(")
    window = src[idx: idx + 3500]
    assert 'r.kind === "internal_employee"' in window
    assert "EmployeeCombo" in window
    # Manual entry still available for contractor/visitor/public/police/etc.
    assert 'placeholder={t("Name")}' in window


# ── Photo UX polish ─────────────────────────────────────────────────
def test_photo_field_shows_count_preview_and_reorder_controls():
    src = (FE_ROOT / "pages/IncidentReport.jsx").read_text(encoding="utf-8")
    idx = src.index("function PhotoField(")
    window = src[idx: idx + 9000]
    assert 'data-testid={`${testId}-count`}' in window
    assert 'data-testid={`${testId}-strip`}' in window
    assert '-preview`' in window
    assert '-preview-modal`' in window
    assert '-preview-close`' in window
    assert 'Move photo earlier' in window
    assert 'Move photo later' in window
    # Order badge lives on every photo tile so field users can see the
    # sequence at a glance.
    assert '-order`' in window


def test_photo_field_a11y_labels_present():
    src = (FE_ROOT / "pages/IncidentReport.jsx").read_text(encoding="utf-8")
    idx = src.index("function PhotoField(")
    window = src[idx: idx + 9000]
    assert 'aria-label={t("Add photo")}' in window
    assert 'aria-label={t("Remove photo")}' in window
    assert 'aria-label={t("Preview photo")}' in window
    assert 'role="dialog"' in window


def test_witness_kind_buttons_expose_aria_pressed():
    src = (FE_ROOT / "pages/IncidentReport.jsx").read_text(encoding="utf-8")
    idx = src.index("function WitnessesField(")
    window = src[idx: idx + 3500]
    assert "aria-pressed" in window


# ── Review page counters ────────────────────────────────────────────
def test_review_page_shows_selector_photo_and_witness_counters():
    src = (FE_ROOT / "pages/IncidentReport.jsx").read_text(encoding="utf-8")
    for testid in (
        "incident-report-review-selected-count",
        "incident-report-review-photo-count",
        "incident-report-review-witness-count",
        "incident-report-review-selected-block",
    ):
        assert testid in src, f"missing review counter {testid}"


def test_review_page_lists_selected_metadata_per_field():
    src = (FE_ROOT / "pages/IncidentReport.jsx").read_text(encoding="utf-8")
    # Each selected field renders a badge with the roster/equipment
    # metadata that came off the combo.
    assert 'incident-report-review-selected-${k}' in src


# ── Zero-Drift ──────────────────────────────────────────────────────
def test_batch2_never_touched_backend_engine():
    """Batch 2 is frontend-only + reuses existing employee/equipment
    endpoints — no backend engine files should have been modified."""
    # Report engine untouched.
    reports_src = (REPO_ROOT / "backend/incident_engine/reports.py").read_text(encoding="utf-8")
    for needle in ("EmployeeCombo", "EquipmentCombo",
                   "VEHICLE_CATEGORIES", "vehicle_picker"):
        assert needle not in reports_src
    # Workspace / Intelligence / Case-service untouched.
    for f in ("workspace.py", "intelligence.py", "case_service.py"):
        src = (REPO_ROOT / f"backend/incident_engine/{f}").read_text(encoding="utf-8")
        assert "vehicle_picker" not in src
        assert "employee_picker" not in src


def test_legacy_redirects_and_deep_links_still_intact():
    txt = (FE_ROOT / "App.js").read_text(encoding="utf-8")
    assert '<Route path="/incidents/new" element={<Navigate to="/incidents/report" replace />}' in txt
    assert '<Route path="/incidents/submit" element={<Navigate to="/incidents/report" replace />}' in txt
    assert '<Route path="/incidents/report"' in txt
    assert '<Route path="/near-miss"' in txt
    assert '<Route path="/safety/executive-intelligence"' in txt
    assert '<Route path="/safety/cases/:caseId"' in txt


def test_selectors_never_mutate_backend_engine_source():
    """Sanity: the report engine + weather helper never grew a
    dependency on the pickers."""
    for f in ("reports.py", "report_render.py", "report_routes.py", "weather.py"):
        src = (REPO_ROOT / f"backend/incident_engine/{f}").read_text(encoding="utf-8")
        assert "EmployeeCombo" not in src
        assert "EquipmentCombo" not in src
