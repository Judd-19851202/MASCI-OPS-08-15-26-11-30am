"""Track 19.34 · Incident Field Intake Modernization · lock test.

Frontend-only feature track. Backend contract preserved byte-for-byte.
This lock enforces:
- doctrine banner component exists · mounted in IncidentReport.jsx;
- 10 required incident types present in the schema;
- legacy incident routes still redirect (zero-drift on legacy URLs);
- forbidden field labels are NOT present in the field-facing schema
  or IncidentReport.jsx (the field-vs-safety protection invariant);
- banner is bilingual (useT());
- 6 required Track 19.34 documents exist;
- closeout declares GO · Six Pillar Score · Zero-Drift Matrix · Rollback;
- PRD + CHANGELOG updated.
"""
from pathlib import Path
import re

APP = Path("/app")
FE = APP / "frontend/src"
MEM = APP / "memory"

BANNER = FE / "components/incident/IncidentFieldDoctrineBanner.jsx"
INCIDENT_REPORT = FE / "pages/IncidentReport.jsx"
SCHEMA = FE / "lib/incidentReportSchema.js"
APP_JS = FE / "App.js"


# --- Component existence


def test_doctrine_banner_exists():
    assert BANNER.exists(), f"Missing {BANNER}"


def test_doctrine_banner_mounted_in_incident_report():
    text = INCIDENT_REPORT.read_text(encoding="utf-8")
    assert "IncidentFieldDoctrineBanner" in text
    assert "<IncidentFieldDoctrineBanner />" in text


def test_doctrine_banner_is_bilingual():
    text = BANNER.read_text(encoding="utf-8")
    assert "useT" in text
    assert 't("' in text or "t('" in text
    # Explicit doctrine sentence protects the wording lock
    assert "capturing facts" in text.lower()
    assert "safety will investigate" in text.lower()


# --- Required incident types


REQUIRED_TYPES = [
    "utility_strike",
    "employee_injury",
    "vehicle_accident",
    "equipment_accident",
    "property_damage",
    "near_miss",
    "environmental",
    "workplace_violence",
    "theft",
    "other",
]


def test_all_10_required_incident_types_present():
    text = SCHEMA.read_text(encoding="utf-8")
    missing = [t for t in REQUIRED_TYPES if f'"{t}"' not in text and f"'{t}'" not in text]
    assert not missing, f"INCIDENT_TYPE_ORDER missing required types: {missing}"


def test_legacy_incident_types_preserved():
    """Zero-drift: no legacy `incident_type` value may be removed."""
    text = SCHEMA.read_text(encoding="utf-8")
    for legacy in ["public_injury", "public_complaint", "fire", "hazard",
                   "threat", "vandalism", "security"]:
        assert legacy in text, f"Legacy incident type must not be removed: {legacy}"


# --- Legacy route redirects preserved


def test_legacy_incidents_new_still_redirects():
    text = APP_JS.read_text(encoding="utf-8")
    assert 'path="/incidents/new"' in text
    assert '<Navigate to="/incidents/report"' in text


def test_legacy_incidents_submit_still_redirects():
    text = APP_JS.read_text(encoding="utf-8")
    assert 'path="/incidents/submit"' in text


# --- Field-vs-Safety protection invariant (the doctrine enforcer)


FORBIDDEN_FIELDS = [
    ("osha_recordable", "OSHA recordable"),
    ("recordable_case", "OSHA recordable"),
    ("osha_reportable", "OSHA reportable"),
    ("root_cause", "Root cause is Safety-owned"),
    ("preventability", "Preventability is Safety-owned"),
    ("preventable_by", "Preventability is Safety-owned"),
    ("workers_comp", "Workers comp is Safety-owned"),
    ("insurance_liable", "Liability is Safety-owned"),
    ("liability_determination", "Liability is Safety-owned"),
    ("disciplinary_action", "Discipline is HR/Management-owned"),
    ("disciplinary_conclusion", "Discipline is HR/Management-owned"),
]


def test_field_intake_does_not_reference_forbidden_fields():
    """Grep-based invariant. Any future track that introduces one of these
    field labels into the field-facing incident schema fails loudly."""
    schema = SCHEMA.read_text(encoding="utf-8")
    report = INCIDENT_REPORT.read_text(encoding="utf-8")
    for field, reason in FORBIDDEN_FIELDS:
        assert field not in schema, f"Forbidden field {field!r} in {SCHEMA.name}: {reason}"
        assert field not in report, f"Forbidden field {field!r} in {INCIDENT_REPORT.name}: {reason}"


def test_no_osha_form_input_in_field_intake():
    """OSHA references may exist as doctrine comments only — never as form
    fields, labels, placeholders, or user prompts."""
    schema = SCHEMA.read_text(encoding="utf-8")
    # Allow doctrine comments (line comments starting with //)
    lines = schema.splitlines()
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("//") or stripped.startswith("*"):
            continue  # comment lines allowed
        # Any non-comment reference to OSHA is disallowed
        assert not re.search(r"\bOSHA\b|\bosha\b", line), (
            f"OSHA reference in non-comment line at {SCHEMA.name}:{i}: {line!r}"
        )


# --- Documentation


REQUIRED_DOCS = [
    "TRACK_19_34_INCIDENT_FIELD_INTAKE_MODERNIZATION.md",
    "TRACK_19_34_INCIDENT_TYPE_MAP.md",
    "TRACK_19_34_FIELD_VS_SAFETY_PROTECTION.md",
    "TRACK_19_34_ZERO_DRIFT_MATRIX.md",
    "TRACK_19_34_QUALITY_GATE_CLOSEOUT.md",
    "TRACK_19_34_TEST_REPORT.md",
]


def test_all_track_19_34_docs_present():
    missing = [d for d in REQUIRED_DOCS if not (MEM / d).exists()]
    assert not missing, f"Missing Track 19.34 docs: {missing}"


def test_type_map_covers_all_required_types():
    text = (MEM / "TRACK_19_34_INCIDENT_TYPE_MAP.md").read_text(encoding="utf-8")
    for t in REQUIRED_TYPES:
        assert t in text, f"Type map missing: {t}"


def test_field_vs_safety_doc_lists_forbidden_fields():
    text = (MEM / "TRACK_19_34_FIELD_VS_SAFETY_PROTECTION.md").read_text(encoding="utf-8")
    for label in ["OSHA recordable", "root cause", "preventability",
                  "discipline", "workers", "liability"]:
        assert label.lower() in text.lower(), f"Field-vs-Safety doc missing: {label}"


def test_zero_drift_matrix_covers_all_categories():
    text = (MEM / "TRACK_19_34_ZERO_DRIFT_MATRIX.md").read_text(encoding="utf-8")
    for cat in [
        "Schemas", "Backend routes", "Payloads", "PDFs", "Emails",
        "Notifications", "Permissions", "Trust Spine", "Audit events",
        "Rollback",
    ]:
        assert cat in text, f"Zero-drift matrix missing category: {cat}"


def test_closeout_declares_go():
    text = (MEM / "TRACK_19_34_QUALITY_GATE_CLOSEOUT.md").read_text(encoding="utf-8")
    assert "🟢 GO" in text or "🟢 **GO" in text


def test_closeout_includes_six_pillar_score():
    text = (MEM / "TRACK_19_34_QUALITY_GATE_CLOSEOUT.md").read_text(encoding="utf-8")
    for pillar in ["Powerful", "Simple", "Beautiful", "Trusted", "Proven", "Operational"]:
        assert pillar in text
    assert "/ 60" in text or "/60" in text


def test_closeout_includes_rollback_path():
    text = (MEM / "TRACK_19_34_QUALITY_GATE_CLOSEOUT.md").read_text(encoding="utf-8")
    assert "Rollback" in text
    assert "delete" in text.lower() or "revert" in text.lower()


def test_prd_updated_for_19_34():
    prd = (MEM / "PRD.md").read_text(encoding="utf-8")
    assert "TRACK 19.34" in prd


def test_changelog_updated_for_19_34():
    changelog = (MEM / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "TRACK 19.34" in changelog
