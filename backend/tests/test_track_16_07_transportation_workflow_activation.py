"""TRACK 16.07 · Transportation Workflow Activation regression.

Locks the activation contract:

* Inline Readiness Inspection Wizard component exists with required
  stages (setup → walkthrough → complete) and disclaimer.
* Document drag-and-drop dropzone component exists with multipart
  upload, camera capture, progress, and preview.
* Signature pad component captures printed_name, timestamp, user_agent,
  and timezone — the audit-evidence payload required by directive #4.
* Rate create dialog exists with create + immediate-activate flow.
* Compliance timeline component exists and consumes the new backend
  endpoint `/api/admin/transportation/timeline/{type}/{id}`.
* Backend timeline endpoint exists and is admin-strict.
* Carrier workspace replaces all ComingSoon placeholders for Packet
  + Documents with real widgets (PacketChecklist + DocumentDropzone).
* Driver workspace surfaces real document upload.
* Truck workspace surfaces the inline Inspection Wizard launcher.
* Inspection Center surfaces the inline wizard launcher.
* Rate Schedule Center surfaces inline "New Version" creation.
* Document Center surfaces inline Accept / Needs Correction review.
* Track 16.04 / 16.05 / 16.06 contracts preserved.
* deployment_gate includes Track 16.07.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path("/app")
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

EXP_ROUTE = BACKEND / "routes" / "transportation_experience.py"
GATE = ROOT / "scripts" / "deployment_gate.py"
WIDGETS = ROOT / "frontend" / "src" / "pages" / "transportation" / "_widgets.jsx"
LISTS = ROOT / "frontend" / "src" / "pages" / "transportation" / "_lists.jsx"
VIEWS = ROOT / "frontend" / "src" / "pages" / "transportation" / "_views.jsx"
SHARED = ROOT / "frontend" / "src" / "pages" / "transportation" / "_shared.jsx"


# ───────────── Backend timeline endpoint ─────────────
def test_1_timeline_endpoint_exists():
    src = EXP_ROUTE.read_text()
    assert '"/admin/transportation/timeline/{entity_type}/{entity_id}"' in src


def test_2_timeline_endpoint_is_admin_strict():
    src = EXP_ROUTE.read_text()
    # Find the timeline decorator and verify the next 1500 chars contain the admin gate.
    m = re.search(
        r'@router\.get\(\s*"/admin/transportation/timeline/\{entity_type\}/\{entity_id\}"',
        src,
    )
    assert m, "timeline decorator not found"
    window = src[m.start(): m.start() + 1600]
    assert "Depends(require_admin_dep)" in window


def test_3_timeline_validates_entity_type():
    src = EXP_ROUTE.read_text()
    assert "entity_type must be carrier|person|truck" in src


def test_4_timeline_returns_combined_direct_and_related_events():
    src = EXP_ROUTE.read_text()
    # Carrier timeline pulls related doc/packet/inspection events.
    assert 'carrier_documents.find' in src
    assert 'transport_packet_submissions.find' in src
    assert 'transport_trucks.find' in src
    assert 'transport_truck_inspections.find' in src
    # Truck timeline pulls related inspection events.
    assert 'transport_truck_inspections.find' in src
    # Driver timeline pulls related driver_documents events.
    assert 'driver_documents.find' in src


# ───────────── Inspection Wizard ─────────────
def test_5_inspection_wizard_component_exists():
    src = WIDGETS.read_text()
    assert "export function InspectionWizard(" in src


def test_6_inspection_wizard_three_stages():
    src = WIDGETS.read_text()
    for stage in ('"setup"', '"walkthrough"', '"done"'):
        assert stage in src, f"missing stage {stage}"
    for testid in ("insp-stage-setup", "insp-stage-walkthrough", "insp-stage-done"):
        assert testid in src


def test_7_inspection_wizard_includes_disclaimer_text():
    src = WIDGETS.read_text()
    assert "MASCI Hauler Truck Readiness Inspection is an operational readiness" in src
    assert "does not replace any DOT, FMCSA, CDL" in src
    assert "insp-disclaimer-setup" in src
    assert "insp-disclaimer-done" in src


def test_8_inspection_wizard_supports_all_required_triggers():
    src = WIDGETS.read_text()
    for trigger in ("initial_onboarding", "annual_recertification", "random",
                    "safety_concern", "customer_complaint", "incident_or_accident",
                    "vehicle_replacement", "major_modification",
                    "management_requested", "dispatch_requested", "safety_requested"):
        assert f'"{trigger}"' in src, f"missing trigger {trigger}"


def test_9_inspection_wizard_uses_existing_endpoints():
    src = WIDGETS.read_text()
    # Start uses POST trucks/{id}/inspections (Phase 2). Patch uses PATCH inspections/{id} (Phase 2).
    assert 'trucks/${truckId}/inspections' in src
    assert 'inspections/${inspection.id}' in src
    assert 'inspections/${inspection.id}/complete' in src


def test_10_inspection_wizard_marks_all_pass_button():
    src = WIDGETS.read_text()
    assert "insp-all-pass-btn" in src


def test_11_inspection_wizard_mobile_friendly_classes():
    src = WIDGETS.read_text()
    # Modal uses max-w-3xl + max-h-[90vh] + overflow-y-auto so the wizard
    # remains usable on iPad portrait without horizontal scroll.
    assert "max-w-3xl" in src
    assert "max-h-[90vh]" in src


# ───────────── Document Dropzone ─────────────
def test_12_document_dropzone_component_exists():
    src = WIDGETS.read_text()
    assert "export function DocumentDropzone(" in src


def test_13_dropzone_supports_drag_drop_browse_camera():
    src = WIDGETS.read_text()
    for testid in ("dropzone-area", "dropzone-browse-btn", "dropzone-camera-btn",
                   "dropzone-file-input", "dropzone-camera-input"):
        assert testid in src
    # Drag handlers.
    assert "onDragOver" in src and "onDrop" in src
    # Camera capture attribute (mobile camera).
    assert 'capture="environment"' in src


def test_14_dropzone_uses_multipart_form():
    src = WIDGETS.read_text()
    assert "new FormData()" in src
    assert 'form.append("document_type"' in src
    assert 'form.append("file"' in src


def test_15_dropzone_progress_indicator_present():
    src = WIDGETS.read_text()
    assert "xhr.upload.onprogress" in src
    # Progress shown via the shared Progress component.
    assert "<Progress" in src


def test_16_dropzone_uploads_to_existing_phase2_endpoints():
    src = WIDGETS.read_text()
    assert "carriers/${parentId}/documents" in src
    assert "persons/${parentId}/documents" in src


# ───────────── Signature Pad ─────────────
def test_17_signature_pad_component_exists():
    src = WIDGETS.read_text()
    assert "export function SignaturePad(" in src


def test_18_signature_captures_required_audit_fields():
    src = WIDGETS.read_text()
    # printed_name, timestamp, user_agent, timezone are required by the
    # MASCI digital-signature directive.
    assert "printed_name" in src
    assert "typed_signature" in src
    assert "acknowledged_at" in src
    assert "user_agent: navigator.userAgent" in src
    assert "timezone:" in src
    assert "signature-ack-checkbox" in src
    assert "signature-submit-btn" in src


def test_19_packet_signs_and_submits_via_existing_endpoint():
    src = WIDGETS.read_text()
    # The packet checklist's signature flow PATCHes the packet with
    # target_status=submitted + signature_payload (Phase 2 endpoint).
    assert "target_status" in src
    assert "signature_payload" in src
    assert "packets/${p.id}" in src


# ───────────── Rate Create Dialog ─────────────
def test_20_rate_create_dialog_exists():
    src = WIDGETS.read_text()
    assert "export function RateCreateDialog(" in src


def test_21_rate_dialog_uses_existing_endpoints():
    src = WIDGETS.read_text()
    assert "/admin/transportation/rate-schedules" in src
    assert "/activate" in src


def test_22_rate_dialog_default_85():
    src = WIDGETS.read_text()
    assert 'useState("85.00")' in src


def test_23_rate_dialog_preserves_historic_packets_note():
    src = WIDGETS.read_text()
    assert "historic packets keep their original locked rate" in src


# ───────────── Compliance Timeline ─────────────
def test_24_compliance_timeline_component_exists():
    src = WIDGETS.read_text()
    assert "export function ComplianceTimeline(" in src
    assert "/admin/transportation/timeline/" in src


def test_25_timeline_renders_audit_lineage_per_entity():
    src = WIDGETS.read_text()
    assert "timeline-list" in src
    assert "timeline-row-" in src


# ───────────── Packet Checklist ─────────────
def test_26_packet_checklist_component_exists():
    src = WIDGETS.read_text()
    assert "export function PacketChecklist(" in src


def test_27_packet_checklist_has_required_actions():
    src = WIDGETS.read_text()
    for testid in ("packet-create-btn", "packet-submit-btn",
                   "packet-approve-btn", "packet-return-btn",
                   "packet-status-chip"):
        assert testid in src


def test_28_packet_checklist_uses_signature_pad():
    src = WIDGETS.read_text()
    # Sign-and-Submit path uses the SignaturePad component.
    assert "packet-signature-pad" in src
    assert "<SignaturePad" in src


# ───────────── Workspace activations (no more dead buttons) ─────────────
def test_29_carrier_packet_pane_uses_packet_checklist():
    src = LISTS.read_text()
    assert "<PacketChecklist" in src
    # The Phase-1 placeholder was removed.
    assert "carrier-packet-checklist-coming-soon" not in src


def test_30_carrier_documents_pane_uses_dropzone():
    src = LISTS.read_text()
    assert 'kind="carrier"' in src
    assert "carrier-doc-dropzone" in src
    assert "carrier-doc-upload-coming-soon" not in src


def test_31_driver_documents_uses_dropzone():
    src = LISTS.read_text()
    assert 'kind="driver"' in src
    assert "driver-doc-dropzone" in src


def test_32_truck_workspace_has_inspection_wizard():
    src = LISTS.read_text()
    assert "truck-start-inspection-btn" in src
    assert 'data-testid="truck-inspection-wizard"' in src or "testid=\"truck-inspection-wizard\"" in src
    assert "<InspectionWizard" in src


def test_33_inspection_center_has_inline_launcher():
    src = VIEWS.read_text()
    assert "insp-launcher-truck-select" in src
    assert "insp-launcher-start-btn" in src
    assert "insp-center-wizard" in src


def test_34_rate_center_has_new_version_button():
    src = VIEWS.read_text()
    assert "rate-new-btn" in src
    assert "<RateCreateDialog" in src
    assert "rate-create-coming-soon" not in src


def test_35_document_center_has_inline_review_actions():
    src = VIEWS.read_text()
    assert "function DocRow" in src
    assert "doc-accept-${doc.id}" in src
    assert "doc-needs-correction-${doc.id}" in src
    assert "doc-review-coming-soon" not in src


def test_36_compliance_timeline_mounted_in_each_workspace():
    src = LISTS.read_text()
    assert 'entityType="carrier"' in src
    assert 'entityType="person"' in src
    assert 'entityType="truck"' in src
    for testid in ("carrier-ws-timeline", "driver-ws-timeline", "truck-ws-timeline"):
        assert testid in src


# ───────────── No drift on prior tracks ─────────────
def test_37_no_duplicate_audit_or_storage_in_widgets():
    src = WIDGETS.read_text()
    # Widgets only call existing Phase 1/2 endpoints. No new audit kinds,
    # no boto3, no Mongo collection writes.
    assert "audit_events" not in src
    assert "boto3" not in src
    assert "db.transport_" not in src  # no direct DB access from client


def test_38_no_forgedops_academy_or_punitive_language():
    full = WIDGETS.read_text() + "\n" + LISTS.read_text() + "\n" + VIEWS.read_text()
    assert "ForgedOps Academy" not in full
    for needle in ('"Failed"', '"Rejected"', '"Denied"',
                   "'Failed'", "'Rejected'", "'Denied'",
                   ">Failed<", ">Rejected<", ">Denied<"):
        assert needle not in full, f"forbidden status label {needle!r}"


def test_39_chip_remains_single_source_of_truth():
    # Widgets import Chip from _shared (don't define their own table).
    src = WIDGETS.read_text()
    assert "import { Chip, adminHeaders" in src or "import {\n  Chip" in src or 'Chip, adminHeaders' in src
    # No new STATE_BADGE table inside _widgets.jsx.
    assert "STATE_BADGE" not in src


def test_40_deployment_gate_includes_16_07():
    assert "test_track_16_07" in GATE.read_text()


# ───────────── Prior tracks still gated ─────────────
def test_41_prior_track_tests_still_referenced():
    gate = GATE.read_text()
    for t in ("test_track_16_04_transportation_foundation.py",
              "test_track_16_05_transportation_onboarding_compliance_center.py",
              "test_track_16_06_transportation_experience_layer.py"):
        assert t in gate
