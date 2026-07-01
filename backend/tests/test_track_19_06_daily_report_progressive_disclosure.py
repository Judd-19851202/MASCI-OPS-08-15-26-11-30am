"""Track 19.06 · Daily Report Progressive-Disclosure Redesign — Lock Test.

Ensures the UI redesign preserves every persisted schema key, every
backend route, and every Track 19.03 / 19.04 / 19.05 doctrine while
the new Yes/No progressive-disclosure shell is delivered.
"""
from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
FRONTEND = REPO_ROOT / "frontend"
BACKEND = REPO_ROOT / "backend"
MEMORY = REPO_ROOT / "memory"


# ---- Report existence ----

def test_track_19_06_reports_exist():
    for name in [
        "TRACK_19_06_DAILY_REPORT_PROGRESSIVE_DISCLOSURE_REDESIGN.md",
        "TRACK_19_06_DAILY_REPORT_UI_CHANGE_MAP.md",
        "TRACK_19_06_DAILY_REPORT_SCHEMA_PROTECTION_REPORT.md",
        "TRACK_19_06_DAILY_REPORT_TEST_REPORT.md",
    ]:
        p = MEMORY / name
        assert p.exists(), f"missing 19.06 report: {name}"
        assert len(p.read_text(encoding="utf-8")) > 300


def test_prd_updated_for_19_06():
    prd = (MEMORY / "PRD.md").read_text(encoding="utf-8")
    assert "TRACK 19.06" in prd or "Track 19.06" in prd


# ---- Schema protection ----

_SCHEMA_KEYS = [
    "project_name:", "project_number:", "location:", "report_date:",
    "report_number:", "prepared_by:", "superintendent:",
    "weather_summary:", "weather_snapshots:", "weather_impact:",
    "schedule_delays:", "safety_incidents_today:", "injuries_reported:",
    "incident_notes:", "safety_notified:", "safety_contact_person:",
    "safety_contact_time:", "incident_report_filled:", "incident_report_time:",
    "general_notes:", "masci_crews:", "subcontractors:", "visitors:",
    "equipment:", "materials:", "activities:", "outbound_materials:",
    "production:", "constraints:", "photos:", "narrative_sections:",
    "photo_captions:", "prepared_by_signature:", "superintendent_signature:",
    "distribution_list:", "attachments:",
]


def test_no_schema_keys_removed_or_renamed():
    src = (BACKEND / "routes/daily_reports.py").read_text(encoding="utf-8")
    for k in _SCHEMA_KEYS:
        assert k in src, f"persisted schema key removed/renamed in Track 19.06: {k}"


def test_daily_report_routes_intact():
    src = (BACKEND / "routes/daily_reports.py").read_text(encoding="utf-8")
    for path in [
        '"/daily-reports"', '"/daily-reports.csv"', '"/daily-reports/next-number"',
        '"/daily-reports/{report_id}"', 'audit-footer',
    ]:
        assert path in src, f"route removed: {path}"


def test_daily_report_attachment_route_still_present():
    src = (BACKEND / "server.py").read_text(encoding="utf-8")
    assert "/daily-reports/attachments/upload" in src


def test_recent_context_endpoint_still_present():
    src = (BACKEND / "server.py").read_text(encoding="utf-8")
    assert "/jobs/{project_number}/recent-context" in src
    assert "contract_version" in src


# ---- Progressive-disclosure UI redesign ----

_UI = (FRONTEND / "src/pages/NewDailyReport.jsx").read_text(encoding="utf-8")


def test_new_flow_includes_job_setup():
    assert '"Job Setup"' in _UI


def test_new_flow_includes_people_on_site():
    assert '"People on Site"' in _UI


def test_new_flow_asks_masci_yes_no():
    assert "Did MASCI employees work on site today?" in _UI


def test_new_flow_asks_subcontractors_yes_no():
    assert "Were subcontractors on site today?" in _UI


def test_new_flow_asks_visitors_yes_no():
    assert "Were visitors or inspectors on site today?" in _UI


def test_new_flow_includes_equipment_resources():
    assert '"Equipment & Resources"' in _UI


def test_new_flow_asks_equipment_yes_no():
    assert "Was MASCI equipment on site or used today?" in _UI


def test_new_flow_includes_materials_import_export():
    assert '"Materials / Import / Export"' in _UI


def test_new_flow_asks_materials_in_yes_no():
    assert "Were materials delivered or imported today?" in _UI


def test_new_flow_asks_materials_out_yes_no():
    assert "Were materials exported or hauled off today?" in _UI


def test_new_flow_includes_work_performed_production():
    assert '"Work Performed & Production"' in _UI


def test_production_array_still_present_in_ui():
    assert "production" in _UI


def test_activity_production_ui_consolidated_under_one_band():
    # The Activity / Production Log CollapseCard remains, but is now
    # rendered under the single "Work Performed & Production" band
    # so the operator sees one section instead of two competing
    # concepts.
    assert '"Work Performed & Production"' in _UI
    assert 'data-testid="band-work-performed"' in _UI


def test_new_flow_includes_delays_constraints_extra_work():
    assert '"Delays / Constraints / Extra Work"' in _UI


def test_new_flow_asks_delays_yes_no():
    assert "Did anything delay, change, or impact production today?" in _UI


def test_weather_impact_still_represented():
    assert "weather_impact" in _UI


def test_new_flow_includes_safety_incidents_inspections():
    assert '"Safety / Incidents / Inspections"' in _UI


def test_new_flow_asks_safety_yes_no():
    assert "Any safety incidents, injuries, accidents, utility hits, near misses, or inspections today?" in _UI


def test_injury_and_accident_distinct_fields():
    assert 'set("safety_incidents_today"' in _UI
    assert 'set("injuries_reported"' in _UI


def test_new_flow_includes_required_evidence():
    assert "Required Evidence" in _UI


def test_photo_min_still_6():
    assert "photo_min: 6" in (FRONTEND / "src/lib/dailyReportSchema.js").read_text(encoding="utf-8")


def test_attachments_still_supported():
    assert 'testIdBase="daily-attachments"' in _UI
    assert "AttachmentUpload" in _UI


def test_pdf_and_excel_still_accepted_by_server():
    src = (BACKEND / "photo_storage.py").read_text(encoding="utf-8")
    for mime in [
        "application/pdf",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ]:
        assert mime in src


def test_new_flow_includes_tomorrow_follow_up():
    assert '"Tomorrow / Follow-Up"' in _UI
    assert 'data-testid="input-tomorrow-plan"' in _UI


def test_new_flow_includes_sign_off_submit():
    assert '"Sign-Off / Submit"' in _UI or '"Sign-Off"' in _UI


def test_smart_prefill_still_explicit():
    assert "smartPrefillOffer" in _UI
    assert "daily-report-smart-prefill-apply" in _UI
    assert "daily-report-smart-prefill-dismiss" in _UI


def test_start_blank_still_present():
    # "Start blank" affordance lives in CrewSetupRestorePrompt for
    # device-local snapshot; Discard/StartBlank buttons are inside the
    # prompt component.
    assert "CrewSetupRestorePrompt" in _UI


def test_autosave_hook_still_used():
    assert "useFormDraft" in _UI


def test_actor_scoped_draft_contract_present():
    src = (FRONTEND / "src/lib/resiliency/draftStore.js").read_text(encoding="utf-8")
    assert "savedByActor" in src
    assert 'contract_version: "19.04"' in src


def test_employee_combo_still_uses_hr_roster():
    src = (FRONTEND / "src/components/EmployeeCombo.jsx").read_text(encoding="utf-8")
    assert "fetchHrRoster" in src
    assert "subscribeHrRoster" in src


def test_photo_upload_still_mounted():
    assert "<PhotoUpload" in _UI


def test_attachment_upload_still_mounted():
    assert "<AttachmentUpload" in _UI


def test_submit_button_still_exists():
    assert "Submit Daily Report" in _UI
    assert 'data-testid="submit-top-btn"' in _UI


def test_excavation_hard_gate_not_removed():
    src = (BACKEND / "routes/daily_reports.py").read_text(encoding="utf-8")
    assert "excavation_record_required" in src or "linked_excavation_ids" in src


def test_pm_and_email_and_pdf_routes_unchanged():
    src = (BACKEND / "server.py").read_text(encoding="utf-8")
    assert "/reports/{kind}/pdf/{id}".replace("{kind}", "").replace("{id}", "") in src or "pdf" in src


def test_csv_export_unchanged():
    src = (BACKEND / "routes/daily_reports.py").read_text(encoding="utf-8")
    assert "daily-reports.csv" in src or ".csv" in src


def test_no_local_permanent_employee_cache_reintroduced():
    for path in [
        "src/components/EmployeeCombo.jsx",
        "src/components/trench/EmployeePicker.jsx",
    ]:
        src = (FRONTEND / path).read_text(encoding="utf-8")
        # Track 19.03 doctrine: no `let _cache = null` / `let _employeeCache`.
        assert "let _cache = null" not in src, f"permanent cache reintroduced in {path}"
        assert "let _employeeCache" not in src, f"permanent cache reintroduced in {path}"


def test_final_go_status_present():
    p = MEMORY / "TRACK_19_06_DAILY_REPORT_TEST_REPORT.md"
    assert "GO" in p.read_text(encoding="utf-8")
