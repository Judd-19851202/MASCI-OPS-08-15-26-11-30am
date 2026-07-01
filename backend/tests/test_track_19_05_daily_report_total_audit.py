"""Track 19.05 · Daily Report Total Audit — Lock Test.

Verifies the audit artifacts exist and cover the required surface areas.
This is a documentation lock — NOT a behavioural test. No implementation
changes were made in Track 19.05.
"""
from __future__ import annotations

from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
MEMORY = REPO_ROOT / "memory"


REPORTS = {
    "route": "TRACK_19_05_DAILY_REPORT_ROUTE_INVENTORY.md",
    "frontend": "TRACK_19_05_DAILY_REPORT_FRONTEND_COMPONENT_MAP.md",
    "backend": "TRACK_19_05_DAILY_REPORT_BACKEND_MAP.md",
    "model": "TRACK_19_05_DAILY_REPORT_DATA_MODEL_MAP.md",
    "ui": "TRACK_19_05_DAILY_REPORT_UI_SECTION_AUDIT.md",
    "control": "TRACK_19_05_DAILY_REPORT_CONTROL_AUDIT.md",
    "trigger": "TRACK_19_05_DAILY_REPORT_TRIGGER_AUDIT.md",
    "validation": "TRACK_19_05_DAILY_REPORT_VALIDATION_AUDIT.md",
    "draft": "TRACK_19_05_DAILY_REPORT_DRAFT_PREFILL_AUDIT.md",
    "attach": "TRACK_19_05_DAILY_REPORT_ATTACHMENT_AUDIT.md",
    "email": "TRACK_19_05_DAILY_REPORT_EMAIL_ROUTING_AUDIT.md",
    "delivery": "TRACK_19_05_DAILY_REPORT_DELIVERY_SURFACE_AUDIT.md",
    "pdf": "TRACK_19_05_DAILY_REPORT_PDF_EXPORT_AUDIT.md",
    "quality": "TRACK_19_05_DAILY_REPORT_DATA_QUALITY_AUDIT.md",
    "industry": "TRACK_19_05_DAILY_REPORT_INDUSTRY_RESEARCH_MAP.md",
    "redundancy": "TRACK_19_05_DAILY_REPORT_REDUNDANCY_CONFUSION_AUDIT.md",
    "matrix": "TRACK_19_05_DAILY_REPORT_REDESIGN_PROTECTION_MATRIX.md",
    "clickthrough": "TRACK_19_05_DAILY_REPORT_LIVE_CLICKTHROUGH_REPORT.md",
    "readiness": "TRACK_19_05_DAILY_REPORT_REDESIGN_READINESS_REPORT.md",
}


def _read(name: str) -> str:
    p = MEMORY / name
    assert p.exists(), f"missing required 19.05 report: {name}"
    return p.read_text(encoding="utf-8")


# 1. All required reports exist
@pytest.mark.parametrize("name", list(REPORTS.values()))
def test_required_report_exists(name: str):
    txt = _read(name)
    assert len(txt) > 400, f"{name} looks too thin ({len(txt)} bytes)"


# 2. Route inventory includes frontend routes
def test_route_inventory_includes_frontend_routes():
    t = _read(REPORTS["route"])
    for r in ["/daily/new", "/daily/submit", "/admin/daily", "/pm/daily"]:
        assert r in t


# 3. Route inventory includes backend routes
def test_route_inventory_includes_backend_routes():
    t = _read(REPORTS["route"])
    for r in ["/api/daily-reports", "/api/daily-reports/next-number",
              "/api/daily-reports/attachments/upload", "/api/jobs/"]:
        assert r in t


# 4. Component map includes NewDailyReport
def test_frontend_map_includes_new_daily_report():
    assert "NewDailyReport" in _read(REPORTS["frontend"])
    assert "AttachmentUpload" in _read(REPORTS["frontend"])
    assert "PhotoUpload" in _read(REPORTS["frontend"])


# 5. Backend map includes daily report submit endpoint
def test_backend_map_includes_submit_and_helpers():
    t = _read(REPORTS["backend"])
    for k in ["create_daily_report", "_sanitize_inline_photos", "_compute_audit_envelope_sha256",
              "schedule_auto_email", "ensure_doc_id", "snapshot_team"]:
        assert k in t, f"backend map missing {k}"


# 6-12. Data model map includes required arrays
@pytest.mark.parametrize("field", [
    "masci_crews", "equipment", "production", "materials",
    "outbound_materials", "photos", "attachments",
    "subcontractors", "visitors", "constraints",
])
def test_data_model_lists_field(field: str):
    assert field in _read(REPORTS["model"])


# 13-15. Control audit includes key controls
@pytest.mark.parametrize("key", ["Submit", "Smart Prefill", "Start blank", "Discard", "Resume"])
def test_control_audit_includes_key_controls(key: str):
    assert key in _read(REPORTS["control"])


# 16-19. Trigger audit yes/no gates
@pytest.mark.parametrize("phrase", [
    "masci_crews", "subcontractors", "materials",
    "outbound", "Excavation Activity", "photo_min",
])
def test_trigger_audit_lists_phrase(phrase: str):
    assert phrase in _read(REPORTS["trigger"])


# 20. Validation audit includes required fields
def test_validation_audit_lists_required():
    t = _read(REPORTS["validation"])
    for f in ["project_name", "location", "report_date", "prepared_by", "photo_min", "422"]:
        assert f in t


# 21-22. Draft audit includes autosave + actor-scoped identity
def test_draft_audit_covers_autosave_and_actor():
    t = _read(REPORTS["draft"])
    for k in ["autosave", "savedByActor", "getAuthActorFingerprint", "IndexedDB", "Smart Prefill"]:
        assert k in t


# 23-24. Attachment audit includes PDF + Excel
def test_attachment_audit_includes_pdf_xlsx():
    t = _read(REPORTS["attach"])
    for k in ["PDF", "xlsx", "CSV", "photo_storage", "25 MiB"]:
        assert k in t


# 25. Email audit includes delivery path
def test_email_audit_lists_delivery_path():
    t = _read(REPORTS["email"])
    for k in ["PM", "Safety", "Distribution", "schedule_auto_email"]:
        assert k in t


# 26. Delivery audit includes PM
def test_delivery_audit_includes_pm_admin_safety():
    t = _read(REPORTS["delivery"])
    for k in ["/pm/daily", "/admin/daily", "Safety", "HrDailyReports"]:
        assert k in t


# 27. PDF audit includes export behavior
def test_pdf_audit_covers_render_and_csv():
    t = _read(REPORTS["pdf"])
    for k in ["WeasyPrint", "application/pdf", "CSV", "/pdf/"]:
        assert k in t


# 28. Data quality audit includes recent report sampling
def test_quality_audit_shows_sample():
    t = _read(REPORTS["quality"])
    for k in ["Sample", "1,118", "Completion rates", "adoption"]:
        assert k in t or k.replace(",", "") in t


# 29-30. Industry map includes HCSS + Procore
def test_industry_map_covers_competitors():
    t = _read(REPORTS["industry"])
    for k in ["HCSS", "HeavyJob", "Procore", "Raken"]:
        assert k in t


# 31-32. Redundancy audit includes activity vs production + injury vs accident
def test_redundancy_audit_covers_key_pairs():
    t = _read(REPORTS["redundancy"])
    for k in ["Activity Log vs Production", "Injury vs Accident",
              "Materials Delivered", "Materials Exported", "Attachments vs Photos"]:
        assert k in t


# 33-35. Protection matrix includes taxonomy
def test_protection_matrix_taxonomy():
    t = _read(REPORTS["matrix"])
    for k in ["MUST PRESERVE", "CAN MERGE", "CAN HIDE BEHIND YES/NO",
              "CAN SIMPLIFY", "CAN REMOVE", "NEEDS DECISION"]:
        assert k in t


# 36. Live clickthrough exists
def test_live_clickthrough_report_exists():
    t = _read(REPORTS["clickthrough"])
    for k in ["Testid presence", "REACT_OVERLAY", "daily-attachments"]:
        assert k in t


# 37. Redesign readiness exists + final verdict
def test_readiness_report_has_go_verdict():
    t = _read(REPORTS["readiness"])
    assert "Redesign readiness" in t
    assert "GO" in t


# 38. PRD updated
def test_prd_mentions_track_19_05():
    prd = (MEMORY / "PRD.md").read_text(encoding="utf-8")
    assert "TRACK 19.05" in prd or "Track 19.05" in prd


# 40. No implementation changes were made to Daily Report redesign yet.
#     We assert that the persisted Pydantic model still declares every
#     field the audit relied on — a redesign that renames a schema key
#     will fail this test and force the audit to be refreshed first.
def test_no_schema_drift_since_audit():
    src = (REPO_ROOT / "backend/routes/daily_reports.py").read_text(encoding="utf-8")
    for field in [
        "project_name:", "location:", "report_date:", "report_number:",
        "prepared_by:", "superintendent:",
        "weather_summary:", "weather_snapshots:",
        "schedule_delays:", "weather_impact:",
        "safety_incidents_today:", "injuries_reported:", "incident_notes:",
        "safety_notified:", "safety_contact_person:", "safety_contact_time:",
        "incident_report_filled:", "incident_report_time:",
        "general_notes:",
        "masci_crews:", "subcontractors:", "visitors:", "equipment:",
        "materials:", "activities:", "outbound_materials:",
        "production:", "constraints:",
        "photos:", "narrative_sections:", "photo_captions:",
        "prepared_by_signature:", "superintendent_signature:",
        "distribution_list:", "attachments:",
    ]:
        assert field in src, f"schema drift — field {field!r} no longer present"


# 39. Final GO/NO-GO status present in readiness report
def test_readiness_final_call_present():
    t = _read(REPORTS["readiness"])
    assert "GO" in t
