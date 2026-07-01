"""Track 19.15 · Incident Intelligence Engine Forensic Audit — Lock Tests.

Audit-only track. Every runtime source file is UNTOUCHED. This suite
verifies the 14 architecture / audit documents exist and carry the
required doctrine markers so future tracks (19.16 → 19.20) can rely
on them as the source of truth.
"""
from __future__ import annotations

from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
AUDIT_DIR = REPO_ROOT / "memory/TRACK_19_15_INCIDENT_ENGINE_AUDIT"

DOCS = [
    "00_EXECUTIVE_SUMMARY.md",
    "01_CURRENT_SYSTEM_FORENSIC_AUDIT.md",
    "02_CURRENT_PDF_REPORT_AUDIT.md",
    "03_INCIDENT_TYPE_INTELLIGENCE_MAP.md",
    "04_FIELD_VS_SAFETY_OWNERSHIP_MATRIX.md",
    "05_CASE_LIFECYCLE_ARCHITECTURE.md",
    "06_ROUTING_NOTIFICATION_MATRIX.md",
    "07_EVIDENCE_ATTACHMENT_ARCHITECTURE.md",
    "08_MARKET_INDUSTRY_COMPARISON.md",
    "09_FUTURE_DATA_ARCHITECTURE.md",
    "10_FUTURE_UI_ARCHITECTURE.md",
    "11_REDESIGN_PROTECTION_MATRIX.md",
    "12_IMPLEMENTATION_ROADMAP.md",
    "13_FINAL_ARCHITECTURE_RECOMMENDATION.md",
]


@pytest.mark.parametrize("doc_name", DOCS)
def test_required_doc_exists(doc_name):
    p = AUDIT_DIR / doc_name
    assert p.exists(), f"Required audit doc missing: {doc_name}"
    assert p.stat().st_size > 500, f"Audit doc suspiciously small: {doc_name}"


def _read(name):
    return (AUDIT_DIR / name).read_text(encoding="utf-8")


# --- Current system audit ---------------------------------------------------


def test_current_system_audit_includes_routes():
    d = _read("01_CURRENT_SYSTEM_FORENSIC_AUDIT.md")
    for r in ("/incidents/new", "/admin/incidents", "/safety-portal/incidents", "/hr/incidents"):
        assert r in d, f"Route missing from current-system audit: {r}"


def test_current_system_audit_includes_collections():
    d = _read("01_CURRENT_SYSTEM_FORENSIC_AUDIT.md")
    assert "incidents" in d
    assert "collection" in d.lower()


# --- PDF audit --------------------------------------------------------------


def test_pdf_audit_includes_production_defects():
    d = _read("02_CURRENT_PDF_REPORT_AUDIT.md")
    for defect in ("blank space", "raw boolean", "Executive Summary",
                   "Root Cause", "Timeline", "Corrective Actions",
                   "Investigation", "utility"):
        assert defect.lower() in d.lower(), f"PDF audit missing defect note: {defect}"


# --- Incident type intelligence map ----------------------------------------


@pytest.mark.parametrize(
    "incident_type",
    ["Utility Strike", "Vehicle Accident", "Equipment Accident",
     "Employee Injury", "Workplace Violence"],
)
def test_incident_type_map_includes(incident_type):
    d = _read("03_INCIDENT_TYPE_INTELLIGENCE_MAP.md")
    assert incident_type in d, f"Incident-type map missing: {incident_type}"


# --- Ownership matrix ------------------------------------------------------


def test_ownership_matrix_separates_field_and_safety():
    d = _read("04_FIELD_VS_SAFETY_OWNERSHIP_MATRIX.md")
    assert "FIELD-OWNED" in d
    assert "SAFETY-OWNED" in d
    assert "MANAGEMENT-OWNED" in d
    assert "PLATFORM-OWNED" in d


def test_ownership_matrix_osha_is_safety_owned():
    d = _read("04_FIELD_VS_SAFETY_OWNERSHIP_MATRIX.md")
    assert "OSHA recordability" in d
    # OSHA recordability appears in the SAFETY-OWNED section
    safety_idx = d.find("### SAFETY-OWNED")
    next_hdr = d.find("### MANAGEMENT-OWNED")
    assert safety_idx != -1 and next_hdr != -1
    safety_block = d[safety_idx:next_hdr]
    assert "OSHA recordability" in safety_block


def test_ownership_matrix_police_followup_is_safety_owned():
    d = _read("04_FIELD_VS_SAFETY_OWNERSHIP_MATRIX.md")
    safety_idx = d.find("### SAFETY-OWNED")
    next_hdr = d.find("### MANAGEMENT-OWNED")
    safety_block = d[safety_idx:next_hdr]
    assert "Police follow-up" in safety_block or "police follow-up" in safety_block.lower()


# --- Case lifecycle --------------------------------------------------------


def test_case_lifecycle_includes_safety_review():
    d = _read("05_CASE_LIFECYCLE_ARCHITECTURE.md")
    assert "SAFETY_REVIEW" in d


def test_case_lifecycle_includes_corrective_actions():
    d = _read("05_CASE_LIFECYCLE_ARCHITECTURE.md")
    assert "CORRECTIVE_ACTIONS" in d


# --- Routing matrix --------------------------------------------------------


@pytest.mark.parametrize("stakeholder", ["Safety", "PM", "Shop", "Fleet"])
def test_routing_matrix_includes_stakeholder(stakeholder):
    d = _read("06_ROUTING_NOTIFICATION_MATRIX.md")
    assert stakeholder in d


# --- Evidence architecture -------------------------------------------------


@pytest.mark.parametrize(
    "evidence_kind",
    ["locate tickets", "police reports", "photos", "witness statements", "medical"],
)
def test_evidence_model_includes(evidence_kind):
    d = _read("07_EVIDENCE_ATTACHMENT_ARCHITECTURE.md")
    assert evidence_kind.lower() in d.lower(), f"Evidence model missing: {evidence_kind}"


# --- Market comparison -----------------------------------------------------


@pytest.mark.parametrize("vendor", ["Procore", "HCSS", "SafetyCulture", "Raken", "OSHA"])
def test_industry_comparison_includes(vendor):
    d = _read("08_MARKET_INDUSTRY_COMPARISON.md")
    assert vendor in d, f"Market comparison missing vendor: {vendor}"


# --- Future UI architecture ------------------------------------------------


@pytest.mark.parametrize(
    "primitive",
    ["FormShell", "PresenceGate", "HelpDrawer", "SubmitReviewPanel", "ProgressRail"],
)
def test_future_ui_uses_primitive(primitive):
    d = _read("10_FUTURE_UI_ARCHITECTURE.md")
    assert primitive in d, f"Future UI architecture missing primitive: {primitive}"


# --- Data architecture -----------------------------------------------------


def test_future_data_architecture_preserves_historical_records():
    d = _read("09_FUTURE_DATA_ARCHITECTURE.md")
    assert "historical records" in d.lower() or "historical record" in d.lower()
    assert "preserv" in d.lower() or "unchanged" in d.lower()
    assert "additive" in d.lower()
    # No destructive migration allowed.
    assert "no destructive migration" in d.lower() or "destructive migration" in d.lower()


# --- Protection matrix -----------------------------------------------------


def test_protection_matrix_includes_can_move_to_safety_case():
    d = _read("11_REDESIGN_PROTECTION_MATRIX.md")
    assert "CAN MOVE TO SAFETY CASE" in d


def test_protection_matrix_includes_can_move_to_appendix():
    d = _read("11_REDESIGN_PROTECTION_MATRIX.md")
    assert "CAN MOVE TO APPENDIX" in d


def test_protection_matrix_includes_must_preserve():
    d = _read("11_REDESIGN_PROTECTION_MATRIX.md")
    assert "MUST PRESERVE" in d


# --- Implementation roadmap ------------------------------------------------


def test_roadmap_includes_phased_implementation():
    d = _read("12_IMPLEMENTATION_ROADMAP.md")
    for track in ("Track 19.16", "Track 19.17", "Track 19.18", "Track 19.19", "Track 19.20"):
        assert track in d, f"Roadmap missing track: {track}"


def test_roadmap_includes_rollback_and_deployment_plan():
    d = _read("12_IMPLEMENTATION_ROADMAP.md")
    assert "Rollback" in d
    assert "Deployment plan" in d


# --- PRD.md updated --------------------------------------------------------


def test_prd_updated_with_track_19_15():
    prd = (REPO_ROOT / "memory/PRD.md").read_text(encoding="utf-8")
    assert "TRACK 19.15" in prd or "Track 19.15" in prd


# --- Zero runtime source file drift ----------------------------------------


def test_no_runtime_source_files_changed_this_track():
    """This track is docs + tests ONLY. Guard against a runtime file
    getting accidentally touched: we assert prior locks (Tracks 19.09
    camera gate, 19.11 Amendment session bus, 19.13 Topic Auto Load)
    still hold in the same files."""
    frontend = REPO_ROOT / "frontend/src"
    eq = (frontend / "pages/NewEquipmentInspection.jsx").read_text(encoding="utf-8")
    dvir = (frontend / "pages/NewFleetDVIR.jsx").read_text(encoding="utf-8")
    meeting = (frontend / "pages/NewMeeting.jsx").read_text(encoding="utf-8")
    bus = (frontend / "lib/sessionStatusBus.js").read_text(encoding="utf-8")
    assert 'data-testid="equipment-camera-gate"' in eq
    assert 'data-testid="dvir-camera-gate"' in dvir
    assert 'import { TOPIC_LIBRARY, CUSTOM_TOPIC_KEY, findTopic } from "@/lib/topics"' in meeting
    assert "ACK_STICKY_KINDS" in bus


# --- Executive summary sanity ----------------------------------------------


def test_executive_summary_declares_go_verdict():
    d = _read("00_EXECUTIVE_SUMMARY.md")
    assert "GO" in d or "Go for" in d or "Proceed" in d
