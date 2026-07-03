"""Track 19.33 · HR Compliance At Risk + Incident Engine Readiness Bridge · lock.

Frontend-only feature track. Backend endpoint reused (no new backend routes).
This lock enforces:
- widget component exists and is wired into HR portal home;
- widget consumes existing summary endpoint · never mutates;
- widget deep-links to Employee 360 · has empty/loading/error states;
- bilingual coverage via useT();
- 3 required Track 19.33 docs exist;
- closeout declares GO · Six Pillar Score · Zero-Drift Matrix · rollback path;
- Incident Engine Readiness Bridge documents field-vs-safety doctrine · 10 incident types;
- PRD + CHANGELOG updated.
"""
from pathlib import Path

APP = Path("/app")
FE = APP / "frontend/src"
MEM = APP / "memory"

WIDGET = FE / "components/hr/HrComplianceAtRiskWidget.jsx"
HR_HUB = FE / "pages/HrHubV2.jsx"
BACKEND_SUMMARY = APP / "backend/routes/sprint_a.py"


# --- Existence


def test_widget_component_exists():
    assert WIDGET.exists(), f"Missing {WIDGET}"


def test_backend_summary_endpoint_still_exists_unchanged():
    """Widget depends on this endpoint. If a future change breaks it, we want
    to fail loudly rather than silently ship a widget with no data."""
    text = BACKEND_SUMMARY.read_text(encoding="utf-8")
    assert '/operations/expirations/summary' in text
    assert 'require_actor' in text  # role gate preserved


# --- Widget contract


def test_widget_consumes_existing_endpoint_only():
    text = WIDGET.read_text(encoding="utf-8")
    assert '/api/operations/expirations/summary' in text, "Widget must call the existing summary endpoint"
    # No mutating verbs — read-only invariant
    for verb in ["method: 'POST'", "method: \"POST\"", "method: 'PATCH'", "method: 'DELETE'"]:
        assert verb not in text, f"Widget must not mutate ({verb} found)"


def test_widget_wraps_strings_in_useT():
    text = WIDGET.read_text(encoding="utf-8")
    assert 'useT' in text
    assert 't("Compliance At Risk")' in text
    assert 't("Attention")' in text or "t('Attention')" in text
    assert 't("No compliance risk right now.")' in text or "No compliance risk right now" in text


def test_widget_has_empty_loading_error_states():
    text = WIDGET.read_text(encoding="utf-8")
    assert 'hr-compliance-at-risk-empty' in text
    assert 'Loading live compliance signals' in text
    assert 'Unable to load' in text or 'offline_feed' in text


def test_widget_has_severity_classifications():
    text = WIDGET.read_text(encoding="utf-8")
    for level in ["Critical", "Warning", "Info"]:
        assert level in text, f"Widget missing severity band: {level}"


def test_widget_deep_links_to_employee_360():
    text = WIDGET.read_text(encoding="utf-8")
    assert '/hr/employees/' in text
    assert '/profile' in text


def test_widget_emits_expected_testids():
    text = WIDGET.read_text(encoding="utf-8")
    for tid in [
        'hr-compliance-at-risk-widget',
        'hr-compliance-at-risk-summary',
        'hr-compliance-at-risk-rows',
        'hr-compliance-at-risk-open-all',
    ]:
        assert tid in text, f"Widget missing testid: {tid}"


def test_widget_mounted_in_hr_hub_v2():
    text = HR_HUB.read_text(encoding="utf-8")
    assert 'HrComplianceAtRiskWidget' in text
    assert 'authHeaders={authHeaders}' in text or '<HrComplianceAtRiskWidget' in text


# --- Documentation


REQUIRED_DOCS = [
    "TRACK_19_33_HR_COMPLIANCE_AT_RISK.md",
    "TRACK_19_33_INCIDENT_ENGINE_READINESS_BRIDGE.md",
    "TRACK_19_33_QUALITY_GATE_CLOSEOUT.md",
    "TRACK_19_33_TEST_REPORT.md",
]


def test_all_track_19_33_docs_present():
    missing = [d for d in REQUIRED_DOCS if not (MEM / d).exists()]
    assert not missing, f"Missing Track 19.33 docs: {missing}"


def test_hr_widget_doc_lists_categories():
    text = (MEM / "TRACK_19_33_HR_COMPLIANCE_AT_RISK.md").read_text(encoding="utf-8")
    for cat in [
        "Expired documents",
        "expiring",
        "CDL",
        "Medical",
        "OSHA",
        "TWIC",
        "Safety training",
    ]:
        assert cat in text, f"HR compliance doc missing category: {cat}"


def test_hr_widget_doc_documents_future_categories():
    text = (MEM / "TRACK_19_33_HR_COMPLIANCE_AT_RISK.md").read_text(encoding="utf-8")
    # Future categories that cannot be supported without schema changes
    for cat in [
        "Driver qualification",
        "Missing emergency contact",
        "Open CAPA",
    ]:
        assert cat in text, f"HR compliance doc must document future category: {cat}"


def test_hr_widget_doc_documents_empty_state():
    text = (MEM / "TRACK_19_33_HR_COMPLIANCE_AT_RISK.md").read_text(encoding="utf-8")
    assert "empty state" in text.lower() or "No compliance risk" in text


def test_hr_widget_doc_documents_rollback():
    text = (MEM / "TRACK_19_33_HR_COMPLIANCE_AT_RISK.md").read_text(encoding="utf-8")
    assert "Rollback" in text or "rollback" in text
    assert "delete `HrComplianceAtRiskWidget" in text or "revert" in text.lower()


def test_hr_widget_doc_confirms_no_mutation():
    text = (MEM / "TRACK_19_33_HR_COMPLIANCE_AT_RISK.md").read_text(encoding="utf-8")
    assert "no mutation" in text.lower() or "Read-only" in text or "read-only" in text


def test_hr_widget_doc_confirms_permission_gating():
    text = (MEM / "TRACK_19_33_HR_COMPLIANCE_AT_RISK.md").read_text(encoding="utf-8")
    assert "HR" in text and "Admin" in text
    assert "RequireHr" in text or "role-gated" in text.lower() or "lane" in text.lower()


def test_hr_widget_doc_confirms_bilingual():
    text = (MEM / "TRACK_19_33_HR_COMPLIANCE_AT_RISK.md").read_text(encoding="utf-8")
    assert "useT" in text or "EN" in text or "Spanish" in text or "bilingual" in text.lower()


# --- Incident Engine Readiness Bridge


INCIDENT_TYPES = [
    "Utility Strike",
    "Employee Injury",
    "Vehicle Accident",
    "Equipment Accident",
    "Property Damage",
    "Near Miss",
    "Environmental Spill",
    "Workplace Violence",
    "Theft",
    "Other",
]


def test_incident_bridge_covers_all_10_types():
    text = (MEM / "TRACK_19_33_INCIDENT_ENGINE_READINESS_BRIDGE.md").read_text(encoding="utf-8")
    missing = [t for t in INCIDENT_TYPES if t not in text]
    assert not missing, f"Incident bridge missing types: {missing}"


def test_incident_bridge_includes_field_vs_safety_doctrine():
    text = (MEM / "TRACK_19_33_INCIDENT_ENGINE_READINESS_BRIDGE.md").read_text(encoding="utf-8")
    assert "Field" in text and "Safety" in text
    assert "facts" in text.lower()
    assert "investigation" in text.lower() or "investigate" in text.lower()
    assert "OSHA" in text  # field must NOT answer this


def test_incident_bridge_defines_track_split():
    text = (MEM / "TRACK_19_33_INCIDENT_ENGINE_READINESS_BRIDGE.md").read_text(encoding="utf-8")
    for tid in ["19.34", "19.35", "19.36"]:
        assert tid in text


# --- Closeout


def test_closeout_declares_go():
    text = (MEM / "TRACK_19_33_QUALITY_GATE_CLOSEOUT.md").read_text(encoding="utf-8")
    assert "🟢 GO" in text or "🟢 **GO" in text


def test_closeout_includes_six_pillar_score():
    text = (MEM / "TRACK_19_33_QUALITY_GATE_CLOSEOUT.md").read_text(encoding="utf-8")
    for pillar in ["Powerful", "Simple", "Beautiful", "Trusted", "Proven", "Operational"]:
        assert pillar in text
    assert "/ 60" in text or "/60" in text


def test_closeout_includes_zero_drift_matrix():
    text = (MEM / "TRACK_19_33_QUALITY_GATE_CLOSEOUT.md").read_text(encoding="utf-8")
    assert "ZERO-DRIFT MATRIX" in text
    for cat in ["Schemas", "Backend routes", "Permissions", "Rollback"]:
        assert cat in text


def test_closeout_includes_rollback_path():
    text = (MEM / "TRACK_19_33_QUALITY_GATE_CLOSEOUT.md").read_text(encoding="utf-8")
    assert "Rollback" in text
    assert "delete" in text.lower() or "revert" in text.lower() or "feature flag" in text.lower()


# --- PRD + CHANGELOG


def test_prd_updated_for_19_33():
    prd = (MEM / "PRD.md").read_text(encoding="utf-8")
    assert "TRACK 19.33" in prd


def test_changelog_updated_for_19_33():
    changelog = (MEM / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "TRACK 19.33" in changelog
