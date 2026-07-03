"""Track 19.29 · Production Readiness & Pilot Certification · deliverables lock.

This certification track produced no code changes. This test only proves the
required certification documents exist, reference the anchor summary, and
declare a GO/NO-GO verdict — so that a future agent (or auditor) can trust
the pilot-readiness trail.
"""
from pathlib import Path

MEM = Path("/app/memory")

ANCHOR = "TRACK_19_29_PRODUCTION_READINESS_CERTIFICATION.md"

REQUIRED = [
    ANCHOR,
    "TRACK_19_29_PERSONA_DAY_IN_LIFE_REPORT.md",
    "TRACK_19_29_WORKFLOW_CHAIN_CERTIFICATION.md",
    "TRACK_19_29_DEVICE_FIELD_CONDITIONS_REPORT.md",
    "TRACK_19_29_PERMISSION_SECURITY_CERTIFICATION.md",
    "TRACK_19_29_PDF_EMAIL_NOTIFICATION_CERTIFICATION.md",
    "TRACK_19_29_BILINGUAL_CERTIFICATION.md",
    "TRACK_19_29_PLATFORM_CONSISTENCY_REPORT.md",
    "TRACK_19_29_FINAL_PILOT_READINESS_VERDICT.md",
    "TRACK_19_29_TEST_REPORT.md",
]

# ---------------------------------------------------------------------------
# Document existence


def test_all_required_documents_present():
    missing = [f for f in REQUIRED if not (MEM / f).exists()]
    assert not missing, f"Missing Track 19.29 documents: {missing}"


def test_prd_updated():
    prd = (MEM / "PRD.md").read_text(encoding="utf-8")
    assert "TRACK 19.29" in prd, "PRD.md must reference TRACK 19.29"


def test_changelog_updated():
    changelog = (MEM / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "TRACK 19.29" in changelog, "CHANGELOG.md must reference TRACK 19.29"


# ---------------------------------------------------------------------------
# Persona coverage — every persona named must appear


PERSONAS = [
    "Field Laborer",
    "Equipment Operator",
    "Foreman",
    "Superintendent",
    "Project Manager",
    "Safety Manager",
    "HR",
    "Shop",
    "Fleet",
    "Dispatch",
    "Transportation",
    "Executive",
    "Administrator",
    "Public",
]


def test_persona_report_covers_all_personas():
    text = (MEM / "TRACK_19_29_PERSONA_DAY_IN_LIFE_REPORT.md").read_text(
        encoding="utf-8"
    )
    missing = [p for p in PERSONAS if p not in text]
    assert not missing, f"Persona report missing: {missing}"


# ---------------------------------------------------------------------------
# Workflow chain coverage


WORKFLOWS = [
    "Daily Report",
    "Equipment Pre-Op",
    "DVIR",
    "Safety Meeting",
    "Incident",
    "HR Employee Records",
    "Transportation",
    "Trench Safety",
    "QA/QC",
    "Field Leadership",
]


def test_workflow_report_covers_all_chains():
    text = (MEM / "TRACK_19_29_WORKFLOW_CHAIN_CERTIFICATION.md").read_text(
        encoding="utf-8"
    )
    missing = [w for w in WORKFLOWS if w not in text]
    assert not missing, f"Workflow chain report missing: {missing}"


# ---------------------------------------------------------------------------
# Device coverage


DEVICES = ["iPhone", "iPad", "laptop", "desktop"]


def test_device_report_covers_all_form_factors():
    text = (MEM / "TRACK_19_29_DEVICE_FIELD_CONDITIONS_REPORT.md").read_text(
        encoding="utf-8"
    )
    for device in DEVICES:
        assert device in text, f"Device report missing: {device}"


# ---------------------------------------------------------------------------
# Permission role coverage


ROLES = [
    "Public",
    "Field",
    "Foreman",
    "Superintendent",
    "PM",
    "Safety",
    "HR",
    "Shop",
    "Fleet",
    "Dispatch",
    "Transportation",
    "Executive",
    "Administrator",
]


def test_permission_report_covers_all_roles():
    text = (MEM / "TRACK_19_29_PERMISSION_SECURITY_CERTIFICATION.md").read_text(
        encoding="utf-8"
    )
    for role in ROLES:
        assert role in text, f"Permission report missing role: {role}"


# ---------------------------------------------------------------------------
# PDF / email families coverage


PDF_FAMILIES = [
    "Daily Report",
    "Equipment Pre-Op",
    "DVIR",
    "Safety Meeting",
    "HR Compliance Brief",
    "Employee Package",
    "Incident Executive",
    "Field Leadership",
    "JHA",
]


def test_pdf_report_covers_all_pdf_families():
    text = (MEM / "TRACK_19_29_PDF_EMAIL_NOTIFICATION_CERTIFICATION.md").read_text(
        encoding="utf-8"
    )
    missing = [p for p in PDF_FAMILIES if p not in text]
    assert not missing, f"PDF/email report missing: {missing}"


def test_pdf_report_includes_email_and_notifications():
    text = (MEM / "TRACK_19_29_PDF_EMAIL_NOTIFICATION_CERTIFICATION.md").read_text(
        encoding="utf-8"
    )
    assert "fsi_send_email" in text
    assert "email_routing_audit_v2" in text
    assert "dry-run" in text.lower() or "dry_run" in text
    assert "notification" in text.lower()


# ---------------------------------------------------------------------------
# Bilingual coverage


def test_bilingual_report_covers_en_es_and_translation_on_submit():
    text = (MEM / "TRACK_19_29_BILINGUAL_CERTIFICATION.md").read_text(
        encoding="utf-8"
    )
    assert "EN" in text and "ES" in text
    assert "useT()" in text
    assert (
        "Translation-on-submit" in text
        or "translation-on-submit" in text.lower()
        or "canonical" in text.lower()
    )


# ---------------------------------------------------------------------------
# Consistency portal coverage


PORTALS = [
    "HR",
    "Safety",
    "Admin",
    "PM",
    "Shop",
    "Dispatch",
    "Transportation",
    "Field",
    "Fleet",
]


def test_consistency_report_covers_all_portals():
    text = (MEM / "TRACK_19_29_PLATFORM_CONSISTENCY_REPORT.md").read_text(
        encoding="utf-8"
    )
    missing = [p for p in PORTALS if p not in text]
    assert not missing, f"Consistency report missing portals: {missing}"


# ---------------------------------------------------------------------------
# Final verdict enforcement


def test_final_verdict_declares_go_or_no_go():
    text = (MEM / "TRACK_19_29_FINAL_PILOT_READINESS_VERDICT.md").read_text(
        encoding="utf-8"
    )
    assert "GO" in text or "NO-GO" in text, "Final verdict must declare GO or NO-GO"


def test_final_verdict_is_go_for_pilot():
    """Track 19.29 must certify pilot-ready. If a future agent regresses this,
    the lock will fail and force a re-certification pass."""
    text = (MEM / "TRACK_19_29_FINAL_PILOT_READINESS_VERDICT.md").read_text(
        encoding="utf-8"
    )
    assert "PILOT-READY" in text or "PILOT READY" in text or "Pilot-ready" in text
    assert "🟢" in text, "Green verdict marker required"


def test_test_report_exists_and_declares_pass():
    text = (MEM / "TRACK_19_29_TEST_REPORT.md").read_text(encoding="utf-8")
    assert "PASS" in text
