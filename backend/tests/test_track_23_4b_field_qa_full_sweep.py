"""TRACK 23.4B · Daily Report V3 · field QA + carrier + unit + full sweep.

Lock envelope covering:
  1. GPS handler writes STRING into `location` (never `[object Object]`).
  2. GPS coord fallback string when reverse-geocode fails.
  3. Weather refresh receives lat/lng AND date; graceful failure.
  4. Materials & Tickets · Inbound row → Carrier only (no duplicate
     Supplier/Vendor field). Unit uses UnitCombo picklist + custom entry.
  5. Materials · Outbound row → Carrier + UnitCombo + destination +
     manifest # + photos.
  6. Production rows → station_from / station_to / percent_complete +
     UnitCombo.
  7. Visitors block (name / company / time_in / time_out / purpose).
  8. Crew rows → employee `onPick` autofill of `trade` from HR roster.
  9. ODS labor_fact carries employee_id / person_name / start_time /
     stop_time / lunch_minutes / cost_code / verified_identity.
 10. ODS material_fact carries `flow` (inbound/outbound) + carrier +
     carrier_id + carrier_name_snapshot for both directions.
 11. ODS constraints → delay_fact emission per row.
 12. Card overflow-hidden safety on shared SectionShell.

If any of these regress, the operator regression class returns.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
FRONT = BACKEND.parent / "frontend" / "src"
V3_PAGE = FRONT / "pages" / "NewDailyReportV3.jsx"
V3_SECTIONS = FRONT / "components" / "daily-report-v3" / "sections.jsx"
V3_UNIT_COMBO = FRONT / "components" / "daily-report-v3" / "UnitCombo.jsx"
GEO = FRONT / "lib" / "geolocation.js"
INGEST = BACKEND / "services" / "ods_spine" / "ingest.py"


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


# ============================================================
# 1 · GPS handler NEVER writes an object into `location`
# ============================================================
def test_gps_handler_writes_string_location():
    src = _read(V3_PAGE)
    # Locate the useGps handler body.
    idx = src.find("const useGps = useCallback")
    assert idx > 0, "useGps handler missing."
    stop = src.find("const refreshWeather", idx)
    body = src[idx:stop]
    # MUST convert reverseGeocode result (object) to a string label.
    assert "typeof rev === \"string\"" in body or "rev?.display" in body, (
        "GPS handler must extract the string display label — never spread "
        "the reverseGeocode object into `location`."
    )
    # MUST NOT assign the raw object to location.
    assert "patch({ location: rev })" not in body, (
        "GPS handler must not push the reverse-geocode object directly."
    )
    # MUST provide a coord fallback string.
    assert "coordFallback" in body
    assert 'location: coordFallback' in body


def test_reverse_geocode_returns_object_contract():
    """Guard against silently reshaping the reverseGeocode return —
    V3 depends on the `.display` field for the string label."""
    src = _read(GEO)
    assert "display" in src
    assert "return {" in src, "reverseGeocode should return an object."


# ============================================================
# 2 · Weather refresh receives lat/lng AND date
# ============================================================
def test_weather_calls_pass_date():
    src = _read(V3_PAGE)
    # useGps + refreshWeather MUST both call fetchDailyWeather with 3 args.
    for label, call in [
        ("GPS-path", "fetchDailyWeather(\n          latitude,\n          longitude,\n          data.report_date"),
        ("refresh-path", "fetchDailyWeather(\n        data.gps_lat,\n        data.gps_lng,\n        data.report_date"),
    ]:
        assert call in src, f"Weather call ({label}) missing 3rd `dateStr` arg."


def test_weather_failure_is_graceful():
    src = _read(V3_PAGE)
    # No scary error toast on the auto-path (GPS click);
    # refresh path uses `toast("Weather unavailable — …")` (neutral).
    assert '"Weather refresh failed"' not in src, (
        "Legacy scary red toast must not return."
    )
    assert "Weather unavailable" in src


# ============================================================
# 3 · Materials · Inbound — carrier only, no duplicate supplier
# ============================================================
def test_inbound_material_row_carrier_only_no_supplier_field():
    src = _read(V3_SECTIONS)
    # The old inbound supplier SupplierCombo (`dr-v3-mat-supplier-<i>`)
    # MUST be removed. Only carrier remains.
    assert "dr-v3-mat-supplier-" not in src, (
        "TRACK 23.4B correction · duplicate Vendor/Supplier field on "
        "inbound materials rows must be removed. Only Carrier stays."
    )
    assert "dr-v3-mat-carrier-" in src


def test_inbound_uses_unit_combo():
    src = _read(V3_SECTIONS)
    assert 'import { UnitCombo }' in src
    # UnitCombo is rendered for material rows.
    assert 'testId={`dr-v3-mat-unit-${i}`}' in src


def test_unit_combo_component_shape():
    src = _read(V3_UNIT_COMBO)
    assert "DEFAULT_MATERIAL_UNITS" in src
    for label in ("Tons", "Cubic Yards", "Loads", "Each",
                  "Linear Feet", "Square Yards", "Gallons", "Truckloads"):
        assert label in src, f"Unit picklist missing `{label}`."
    # Must support custom entry (datalist backs it, input value passes through).
    assert '<datalist' in src
    assert "onChange?.(raw)" in src


# ============================================================
# 4 · Materials · Outbound — carrier + unit + manifest + photos
# ============================================================
def test_outbound_row_carrier_unit_manifest_photo():
    src = _read(V3_SECTIONS)
    for tid in (
        "dr-v3-out-mat-",
        "dr-v3-out-qty-",
        "dr-v3-out-unit-",
        "dr-v3-out-carrier-",
        "dr-v3-out-dest-",
        "dr-v3-out-ticket-",
        "dr-v3-out-photo-",
    ):
        assert f'`{tid}${{i}}`' in src or f'{tid}${{i}}' in src, (
            f"Outbound row missing testid `{tid}<i>`."
        )


# ============================================================
# 5 · Production rows — station_from / station_to / percent + UnitCombo
# ============================================================
def test_production_row_carries_station_and_percent():
    src = _read(V3_SECTIONS)
    for tid in (
        "dr-v3-prod-sta-from-",
        "dr-v3-prod-sta-to-",
        "dr-v3-prod-percent-",
        "dr-v3-prod-unit-",
    ):
        assert f'`{tid}${{i}}`' in src, (
            f"Production row missing testid `{tid}<i>`."
        )


# ============================================================
# 6 · Visitors sub-section
# ============================================================
def test_visitors_block_renders():
    src = _read(V3_SECTIONS)
    assert 'data-testid="dr-v3-visitors-block"' in src
    assert 'data-testid="dr-v3-visitor-add"' in src
    for tid in (
        "dr-v3-visitor-name-",
        "dr-v3-visitor-company-",
        "dr-v3-visitor-tin-",
        "dr-v3-visitor-tout-",
        "dr-v3-visitor-purpose-",
    ):
        assert f'`{tid}${{i}}`' in src, (
            f"Visitors row missing testid `{tid}<i>`."
        )


# ============================================================
# 7 · Crew employee-pick autofills trade from HR
# ============================================================
def test_employee_combo_onpick_autofills_trade():
    """Post-23.4C the trade-autofill logic moved into a shared
    `_applyHrPick(i, emp, currentRow)` helper so both the dropdown-pick
    path AND the typed-and-blur path (which fires on onChange) go
    through the same code. The lock now checks that helper."""
    src = _read(V3_SECTIONS)
    idx = src.find("_applyHrPick")
    assert idx > 0, "V3 must expose the shared _applyHrPick handler."
    body = src[idx:idx + 1500]
    assert "trade_autofilled" in body
    # The row-side EmployeeCombo must funnel BOTH paths through it.
    assert "onPick={(emp) => _applyHrPick" in src
    assert "resolveEmployeeByTypedName" in src


# ============================================================
# 8 · Section shell defensive overflow lock
# ============================================================
def test_section_shell_uses_overflow_hidden_and_min_w_0():
    src = _read(V3_SECTIONS)
    idx = src.find("function SectionShell(")
    assert idx > 0
    stop = src.find("\nexport function", idx)
    body = src[idx:stop]
    assert "overflow-hidden" in body
    assert "min-w-0" in body


# ============================================================
# 9 · ODS labor_fact carries HR + timing keys
# ============================================================
def _import_ingest():
    if str(BACKEND) not in sys.path:
        sys.path.insert(0, str(BACKEND))
    from services.ods_spine import ingest  # noqa: WPS433
    return ingest


def _emit(rec):
    """V1-shaped record → facts (uses the V1 fact builder directly)."""
    ingest = _import_ingest()
    return ingest._build_facts_from_dr_v1_report(rec)


def test_ods_labor_fact_carries_v3_hr_keys():
    ingest = _import_ingest()
    rec = {
        "id": "DR-2026-99999",
        "project_id": "20-07",
        "date": "2026-02-06",
        "report_date": "2026-02-06",
        "masci_crews": [
            {
                "name": "John Doe",
                "employee_id": "EMP-123",
                "trade": "Foreman",
                "start_time": "07:00",
                "stop_time": "17:00",
                "lunch_minutes": 30,
                "hours": 9.5,
                "cost_code": "PAV-100",
            }
        ],
    }
    facts = _emit(rec)
    labor = [f for f in facts if f["fact_type"] == "labor_fact"]
    assert labor, "No labor_fact emitted."
    p = labor[0]["payload"]
    assert p["employee_id"] == "EMP-123"
    assert p["person_name"] == "John Doe"
    assert p["role"] == "Foreman"
    assert p["start_time"] == "07:00"
    assert p["stop_time"] == "17:00"
    assert p["lunch_minutes"] == 30
    assert p["cost_code"] == "PAV-100"
    assert p["verified_identity"] is True
    assert labor[0]["source_status"] == "verified"


def test_ods_labor_fact_partial_when_no_employee_id():
    ingest = _import_ingest()
    rec = {
        "id": "DR-2026-99998",
        "project_id": "20-07",
        "date": "2026-02-06",
        "report_date": "2026-02-06",
        "masci_crews": [
            {"trade": "Laborer", "count": 4, "hours": 8, "foreman": "Foreman Bob"}
        ],
    }
    facts = _emit(rec)
    labor = [f for f in facts if f["fact_type"] == "labor_fact"]
    assert labor
    assert labor[0]["source_status"] == "partial"
    assert labor[0]["payload"]["verified_identity"] is False
    assert labor[0]["payload"]["labor_hours"] == 32  # 4 × 8


# ============================================================
# 10 · ODS material_fact carries flow + carrier for both directions
# ============================================================
def test_ods_material_fact_inbound_outbound_carrier():
    ingest = _import_ingest()
    rec = {
        "id": "DR-2026-99997",
        "project_id": "20-07",
        "date": "2026-02-06",
        "report_date": "2026-02-06",
        "materials": [
            {
                "description": "Lime rock",
                "quantity": 125,
                "unit": "Tons",
                "carrier": "Acme Hauling",
                "carrier_id": "SUP-77",
                "carrier_name_snapshot": "Acme Hauling",
                "ticket_number": "T-48372",
            }
        ],
        "outbound_materials": [
            {
                "material": "Demo debris",
                "quantity": 6,
                "unit": "Loads",
                "hauler": "Green Waste",
                "hauler_id": "SUP-88",
                "hauler_name_snapshot": "Green Waste",
                "destination": "Landfill A",
                "ticket_number": "M-77",
            }
        ],
    }
    facts = _emit(rec)
    mats = [f for f in facts if f["fact_type"] == "material_fact"]
    assert len(mats) == 2
    flows = {f["payload"]["flow"] for f in mats}
    assert flows == {"inbound", "outbound"}
    inbound = next(f for f in mats if f["payload"]["flow"] == "inbound")
    ip = inbound["payload"]
    assert ip["carrier"] == "Acme Hauling"
    assert ip["carrier_id"] == "SUP-77"
    assert ip["carrier_name_snapshot"] == "Acme Hauling"
    assert ip["ticket"] == "T-48372"
    outbound = next(f for f in mats if f["payload"]["flow"] == "outbound")
    op = outbound["payload"]
    assert op["carrier"] == "Green Waste"
    assert op["carrier_id"] == "SUP-88"
    assert op["destination"] == "Landfill A"
    assert op["ticket"] == "M-77"


# ============================================================
# 11 · V3 constraints[] emit delay_fact rows
# ============================================================
def test_ods_constraints_emit_delay_fact_rows():
    ingest = _import_ingest()
    rec = {
        "id": "DR-2026-99996",
        "project_id": "20-07",
        "date": "2026-02-06",
        "report_date": "2026-02-06",
        "impact_present": "Yes",
        "constraints": [
            {"constraint_type": "utility", "hours_impact": 6, "notes": "FPL delay"},
            {"constraint_type": "material", "hours_impact": 2, "notes": "Late stone"},
            {"constraint_type": "traffic_mot", "hours_impact": 0.5, "notes": ""},
        ],
    }
    facts = _emit(rec)
    delays = [f for f in facts if f["fact_type"] == "delay_fact"]
    cats = sorted(f["payload"]["delay_category"] for f in delays)
    assert cats == ["material", "traffic_mot", "utility"]
    # High severity when hours_impact >= 4.
    high = [f for f in delays if f["payload"]["delay_category"] == "utility"][0]
    assert high["payload"]["impact"] == "high"
    # Reason falls back to formatted category when notes blank.
    mot = [f for f in delays if f["payload"]["delay_category"] == "traffic_mot"][0]
    assert "Traffic Mot" in mot["payload"]["reason"]


def test_ods_non_summary_facts_do_not_leak_provider_meta():
    """The `day_summary_fact` internally carries masked meta by design
    (already locked by TRACK 22.9C so it never reaches PDF/email/PM
    surface). But NO OTHER fact type should carry provider or latency
    metadata."""
    rec = {
        "id": "DR-2026-99995",
        "project_id": "20-07",
        "date": "2026-02-06",
        "report_date": "2026-02-06",
        "ai_accepted_summary": "Poured curb.",
        "ai_accepted_summary_meta": {"provider": "openai", "model": "gpt-5.2", "latency_ms": 1234},
        "masci_crews": [{"name": "A", "employee_id": "E1", "hours": 8}],
        "materials": [{"description": "Rock", "quantity": 10, "unit": "TN", "carrier": "X"}],
    }
    facts = _emit(rec)
    other = [f for f in facts if f["fact_type"] != "day_summary_fact"]
    blob = repr(other).lower()
    for banned in ("openai", "gpt-5.2", "latency_ms", "provider_masked", "model_masked"):
        assert banned not in blob, (
            f"ODS non-summary fact leaked `{banned}` into a payload."
        )



# ============================================================
# 13 · Visual consistency · blueprint-bg engineering-grid parity
# ============================================================
def test_v3_uses_shared_blueprint_bg_and_caution_stripe():
    """V3 must render inside the same `blueprint-bg` + `caution-stripe`
    grammar used by QA/QC, Safety Audits, Field Safety, JHP,
    Excavation. Do not fall back to a plain `bg-slate-50` container —
    that reintroduces the visual drift the operator flagged."""
    src = _read(V3_PAGE)
    assert 'className="min-h-screen blueprint-bg"' in src, (
        "V3 root container must use the shared `blueprint-bg` class."
    )
    assert 'className="caution-stripe"' in src, (
        "V3 must render the `caution-stripe` accent (visual consistency)."
    )
    # Regression guard: the pre-fix plain container must not return.
    assert '<div className="min-h-screen bg-slate-50">' not in src


# ============================================================
# 14 · Anti-fall-back sweep against known operator regressions
# ============================================================
def test_v3_never_stores_object_object_string_anywhere():
    """The operator repeatedly caught `[object Object]` string leaking
    into text fields. Guard the entire page source against known
    footguns that produce that string."""
    src = _read(V3_PAGE)
    assert "${rev}" not in src, (
        "Do not interpolate the raw reverseGeocode object into strings."
    )
    assert "location: rev }" not in src


def test_track_23_4b_lockfile_present():
    assert INGEST.exists()
    assert V3_UNIT_COMBO.exists()


# ============================================================
# 15 · HR autofill · crew / supervisor / division snapshots
# ============================================================
def test_v3_crew_row_autofills_crew_and_supervisor_snapshots():
    """When a MASCI employee is picked, the row MUST persist snapshots
    of trade / crew / supervisor / division so downstream (HR Time
    Verification, Payroll Variance, PM manpower intelligence) can
    consume them without another lookup."""
    src = _read(V3_SECTIONS)
    for key in (
        "employee_name_snapshot",
        "trade_snapshot",
        "crew_snapshot",
        "division_snapshot",
        "supervisor_snapshot",
    ):
        assert key in src, (
            f"Crew row onPick must persist `{key}` from Employee Master."
        )
    # HR meta chip renders when crew or supervisor snapshot present.
    assert 'data-testid={`dr-v3-crew-hr-meta-${i}`}' in src


def test_public_employees_endpoint_returns_supervisor_and_division():
    """`/api/employees` MUST project `supervisor` and `division` so the
    frontend picker can hand them to the crew row for autofill."""
    src = (BACKEND / "server.py").read_text(encoding="utf-8")
    idx = src.find('@api_router.get("/employees")')
    assert idx > 0
    stop = src.find("@api_router.get(", idx + 20)
    body = src[idx:stop]
    assert '"supervisor": 1' in body
    assert '"division": 1' in body


def test_crew_memory_strip_drops_stale_trade_and_flags_hr_refresh():
    """Restore-yesterday must not carry yesterday's stale trade over —
    HR record may have changed (promotion / crew reassignment / new
    supervisor). Row must be tagged `_needs_hr_refresh: true` so the
    form re-hydrates from the fresh HR fetch."""
    src = (FRONT / "lib" / "crewMemory.js").read_text(encoding="utf-8")
    idx = src.find("function _stripCrewRow")
    stop = src.find("\nfunction ", idx + 1)
    body = src[idx:stop]
    # trade MUST NOT survive the strip.
    assert 'trade' not in body.split("return")[1].split("}")[0], (
        "Restore-yesterday strip must not preserve stale trade — HR is gospel."
    )
    assert "_needs_hr_refresh" in body


def test_refresh_crew_from_employee_master_helper_exists():
    src = (FRONT / "lib" / "crewMemory.js").read_text(encoding="utf-8")
    assert "export function refreshCrewFromEmployeeMaster" in src
    # Handles both employee_id-match and name-fallback.
    assert "byId" in src and "byName" in src


def test_ods_labor_fact_carries_hr_snapshots():
    """labor_fact payload MUST carry crew/supervisor snapshots so HR
    Time Verification and Payroll Variance downstream can consume."""
    rec = {
        "id": "DR-2026-99994",
        "project_id": "20-07",
        "date": "2026-02-06",
        "report_date": "2026-02-06",
        "masci_crews": [
            {
                "name": "Alec Perkins",
                "employee_id": "EMP-42",
                "trade": "Operator",
                "trade_snapshot": "Operator",
                "crew_snapshot": "Grade Crew A",
                "division_snapshot": "Grade Crew A",
                "supervisor_snapshot": "R. Diaz",
                "start_time": "06:30",
                "stop_time": "16:00",
                "lunch_minutes": 30,
                "hours": 9,
            }
        ],
    }
    facts = _emit(rec)
    labor = [f for f in facts if f["fact_type"] == "labor_fact"]
    assert labor, "No labor_fact emitted."
    p = labor[0]["payload"]
    assert p["employee_id"] == "EMP-42"
    assert p["person_name"] == "Alec Perkins"
    assert p["employee_name_snapshot"] == "Alec Perkins"
    assert p["role"] == "Operator"
    assert p["trade_snapshot"] == "Operator"
    assert p["crew_snapshot"] == "Grade Crew A"
    assert p["supervisor_snapshot"] == "R. Diaz"
    assert p["start_time"] == "06:30"
    assert p["stop_time"] == "16:00"
    assert p["lunch_minutes"] == 30
    assert p["labor_hours"] == 9  # crew_size=1 for named V3 rows


def test_v3_restore_calls_refresh_crew_from_hr():
    """The V3 page onUseCrewSetup handler MUST call
    refreshCrewFromEmployeeMaster after applying yesterday's snapshot."""
    src = _read(V3_PAGE)
    assert "refreshCrewFromEmployeeMaster" in src
    # Must fetch a fresh HR roster before rehydration.
    assert '/employees' in src
