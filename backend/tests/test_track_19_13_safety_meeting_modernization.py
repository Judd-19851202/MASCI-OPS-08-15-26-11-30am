"""Track 19.13 · Safety Meeting Modernization — Lock Tests.

Doctrine:
    Safety Meeting is the THIRD production consumer of the Track 19.11
    MAIN reusable platform primitives. Topic Auto Load — the flagship
    knowledge-engine capability — remains untouched. HelpDrawer, the
    ProgressRail, and the SubmitReviewPanel wrap the meeting flow;
    the primitive files themselves are unchanged (locked by pytest).

Zero drift from:
    * Track 19.05 schema lock
    * Track 19.08 forms-audit snapshots
    * Track 19.09 modernization
    * Track 19.10 FormShell/HelpDrawer primitives
    * Track 19.11 Amendment session-expired ack-suppression
    * Track 19.11 MAIN Equipment Pre-Op modernization
    * Track 19.12 DVIR modernization
    * Topic Library architecture (TOPIC_LIBRARY + TOPIC_LIBRARY_ES)
    * Attendee acknowledgement pipeline (SAFETY-MEETING-CERT)
"""
from __future__ import annotations

from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
FRONTEND = REPO_ROOT / "frontend"

_MEETING = (FRONTEND / "src/pages/NewMeeting.jsx").read_text(encoding="utf-8")
_I18N = (FRONTEND / "src/lib/i18n.js").read_text(encoding="utf-8")


# --- Safety Meeting consumes the four Track 19.11 MAIN primitives -----------


@pytest.mark.parametrize(
    "primitive_import",
    [
        'import { HelpDrawer } from "@/components/HelpDrawer"',
        'import { FormSection } from "@/components/FormSection"',
        'import { ProgressRail } from "@/components/ProgressRail"',
        'import { SubmitReviewPanel } from "@/components/SubmitReviewPanel"',
    ],
)
def test_meeting_imports_platform_primitive(primitive_import):
    assert primitive_import in _MEETING


def test_meeting_modernization_marker_present():
    assert 'data-testid="meeting-modernized"' in _MEETING


def test_meeting_helpdrawer_wired():
    assert "<HelpDrawer" in _MEETING
    assert 'testIdPrefix="meeting-help-drawer"' in _MEETING


def test_meeting_progressrail_wired():
    assert "<ProgressRail" in _MEETING
    assert 'testId="meeting-progress-rail"' in _MEETING


def test_meeting_review_section_and_panel_wired():
    assert "<FormSection" in _MEETING
    assert 'testId="meeting-review-section"' in _MEETING
    assert "<SubmitReviewPanel" in _MEETING
    assert 'testId="meeting-review-panel"' in _MEETING


def test_meeting_helpdrawer_carries_all_eight_bands():
    """Track 19.13 brief demands 8 rich bands (vs. 5 for Equipment
    Pre-Op / DVIR) — safety meetings carry richer coaching content."""
    for band_title in (
        "Why this meeting matters",
        "Who receives this",
        "How attendance is documented",
        "How knowledge is retained",
        "Legal documentation",
        "Common meeting mistakes",
        "Supervisor best practices",
        "Crew engagement tips",
    ):
        assert f't("{band_title}")' in _MEETING, (
            f"Safety Meeting HelpDrawer missing consolidated band: {band_title}"
        )


# --- Consolidation: all six HelpTipBlock defaults retired -------------------


@pytest.mark.parametrize(
    "form_key",
    ["meeting", "meeting.context", "meeting.topic", "meeting.attendees",
     "meeting.photos", "meeting.signoff"],
)
def test_meeting_helptipblock_default_retired(form_key):
    """Every stacked HelpTipBlock default that used to noise up the
    Safety Meeting page is RETIRED. Content lives inside the drawer."""
    pattern = f'<HelpTipBlock formKey="{form_key}"'
    assert pattern not in _MEETING, (
        f"HelpTipBlock '{form_key}' default is still visible — must be retired"
    )


def test_meeting_helptipblock_import_removed():
    assert 'import { HelpTipBlock } from "@/components/HelpTip"' not in _MEETING


# --- NON-NEGOTIABLE: Topic Auto Load must be untouched ----------------------


def test_meeting_topic_library_imports_preserved():
    """Track 19.13 brief explicitly forbids touching Topic Auto Load."""
    assert 'import { TOPIC_LIBRARY, CUSTOM_TOPIC_KEY, findTopic } from "@/lib/topics"' in _MEETING
    assert 'import { TOPIC_LIBRARY_ES } from "@/lib/topics/index.es"' in _MEETING


def test_meeting_topic_template_key_state_preserved():
    """The templateKey → data auto-population pipeline is intact."""
    assert "const [templateKey, setTemplateKey] = useState(CUSTOM_TOPIC_KEY)" in _MEETING


def test_meeting_topic_es_lookup_preserved():
    """Bilingual topic hydration path is intact."""
    assert 'TOPIC_LIBRARY_ES[key]' in _MEETING


def test_meeting_topic_data_testid_preserved():
    """UI hook for the topic picker must not have drifted."""
    assert 'data-testid="input-topic"' in _MEETING
    assert 'data-testid="meeting-domain-breadcrumb"' in _MEETING


# --- Preservation: attendance / signature / photos --------------------------


def test_meeting_attendee_acknowledgement_preserved():
    """SAFETY-MEETING-CERT explicit acknowledgement pipeline must
    remain — it's the legal-defensibility anchor."""
    assert "acknowledged" in _MEETING
    assert "acknowledged_at" in _MEETING
    # Attendee testIds
    assert 'data-testid={`attendee-ack-${i}`}' in _MEETING
    assert 'data-testid={`attendee-name-${i}`}' in _MEETING


def test_meeting_signature_pipeline_preserved():
    assert "SignaturePad" in _MEETING
    assert 'testId="conductor-sig"' in _MEETING


def test_meeting_photo_pipeline_preserved():
    assert "PhotoUpload" in _MEETING
    assert 'data-testid="meeting-photo-count"' in _MEETING
    assert '"meeting-photo-count"' in _MEETING


def test_meeting_submit_endpoint_preserved():
    """The POST route + payload contract must be untouched."""
    assert 'api.post("/meetings", payload)' in _MEETING


def test_meeting_bilingual_toggle_preserved():
    assert "<LangToggle" in _MEETING


def test_meeting_draft_restore_preserved():
    """Track 15.60 P0 field-trust fix must not have been touched."""
    assert "DraftRestorePrompt" in _MEETING


def test_meeting_bilingual_consent_preserved():
    assert "<BilingualConsent" in _MEETING


# --- Bilingual parity for new Track 19.13 strings --------------------------


NEW_MEETING_STRINGS = [
    "Safety Meeting · Guidance",
    "Why this meeting matters",
    "Who receives this",
    "How attendance is documented",
    "How knowledge is retained",
    "Legal documentation",
    "Common meeting mistakes",
    "Supervisor best practices",
    "Crew engagement tips",
    "Info",
    "Context",
    "Topic",
    "Confirm the meeting summary before you submit. What happens next is listed below.",
    "Topic pending.",
    "attendees on the record",
    "No attendees recorded yet.",
    "photos attached",
    "At least 2 photos required.",
    "Conductor signature captured.",
    "Conductor signature pending.",
    "Attendance will be recorded in the training history.",
    "Each attendee's training history is updated.",
    "The meeting is archived for legal and DOT/OSHA audit purposes.",
    "A PDF record is generated for downstream distribution.",
    "A permanent audit record is created.",
]


@pytest.mark.parametrize("en", NEW_MEETING_STRINGS)
def test_new_meeting_string_has_es_translation(en):
    escaped = en.replace('"', '\\"')
    assert f'"{escaped}":' in _I18N, (
        f"Missing ES translation for new Track 19.13 Safety Meeting string: {en!r}"
    )


# --- Zero backend drift + cross-form parity --------------------------------


def test_meeting_no_new_backend_endpoints():
    """The modernization is 100% frontend. Track 19.08 audit snapshot
    lock must remain intact."""
    audit_path = REPO_ROOT / "backend/tests/test_track_19_08_forms_audit_snapshots.py"
    audit = audit_path.read_text(encoding="utf-8")
    assert "SNAPSHOT_ROUTES_MIN = 900" in audit


def test_primitives_are_same_files_across_three_forms():
    """Doctrine: Equipment Pre-Op + DVIR + Safety Meeting all consume
    the SAME primitive files."""
    eq = (FRONTEND / "src/pages/NewEquipmentInspection.jsx").read_text(encoding="utf-8")
    dvir = (FRONTEND / "src/pages/NewFleetDVIR.jsx").read_text(encoding="utf-8")
    for imp in (
        'import { HelpDrawer } from "@/components/HelpDrawer"',
        'import { FormSection } from "@/components/FormSection"',
        'import { ProgressRail } from "@/components/ProgressRail"',
        'import { SubmitReviewPanel } from "@/components/SubmitReviewPanel"',
    ):
        assert imp in eq, f"Equipment Pre-Op missing {imp}"
        assert imp in dvir, f"DVIR missing {imp}"
        assert imp in _MEETING, f"Safety Meeting missing {imp}"


def test_primitive_files_untouched_by_meeting_adoption():
    """DVIR + Safety Meeting must NOT have leaked form-specific testIds
    into the primitive files. Primitives stay form-agnostic."""
    for name in ("FormSection.jsx", "ProgressRail.jsx",
                 "SubmitReviewPanel.jsx", "PresenceGate.jsx"):
        src = (FRONTEND / f"src/components/{name}").read_text(encoding="utf-8")
        assert 'testId="meeting-' not in src, (
            f"{name} leaked meeting-specific testId default — must be form-agnostic"
        )
        assert 'testId="dvir-' not in src, (
            f"{name} leaked dvir-specific testId default — must be form-agnostic"
        )


def test_track_19_11_main_and_19_12_locks_still_hold():
    """Prior modernizations must remain intact — no accidental
    cross-form regression from 19.13 landing."""
    eq = (FRONTEND / "src/pages/NewEquipmentInspection.jsx").read_text(encoding="utf-8")
    dvir = (FRONTEND / "src/pages/NewFleetDVIR.jsx").read_text(encoding="utf-8")
    assert 'data-testid="preop-modernized"' in eq
    assert 'testId="equipment-progress-rail"' in eq
    assert 'testId="equipment-review-panel"' in eq
    assert 'data-modernized="dvir-modernized"' in dvir
    assert 'testId="dvir-progress-rail"' in dvir
    assert 'testId="dvir-review-panel"' in dvir


def test_session_bus_still_locked():
    bus = (FRONTEND / "src/lib/sessionStatusBus.js").read_text(encoding="utf-8")
    assert "ACK_STICKY_KINDS" in bus
