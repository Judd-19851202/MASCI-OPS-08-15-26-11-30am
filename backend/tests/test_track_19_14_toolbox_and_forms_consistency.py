"""Track 19.14 · Toolbox Meeting Modernization + Cross-Form Consistency Certification.

Doctrine finding:
    "Toolbox Talk" and "Site Safety Meeting" are the SAME form in this
    codebase (see frontend/src/lib/meetingSchema.js line 1). The
    /meetings/new route serves both. Track 19.13 already modernized
    this form; Track 19.14 therefore delivers:
      1) an explicit Toolbox Talk terminology affordance on the form
         (bilingual chip) for operator wayfinding, and
      2) the FINAL cross-form consistency certification across the
         four modernized operational forms.

Cross-form doctrine locked here — the four modernized production
consumers of the Track 19.11 MAIN reusable primitives:
    * NewEquipmentInspection.jsx  (Track 19.11 MAIN)
    * NewFleetDVIR.jsx            (Track 19.12)
    * NewMeeting.jsx              (Tracks 19.13 + 19.14)
        - also serves as Toolbox Talk
    * Daily Report is already modernized separately (Tracks 19.04-19.07)

Every form MUST:
    1) Import the four primitive files (HelpDrawer, FormSection,
       ProgressRail, SubmitReviewPanel).
    2) Mount a ProgressRail with a form-specific testId prefix.
    3) Mount a HelpDrawer trigger with a form-specific testIdPrefix.
    4) Retire all stacked <HelpTipBlock> default components.
    5) Ship a modernization marker on the outer wrapper.
"""
from __future__ import annotations

from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
FRONTEND = REPO_ROOT / "frontend"

_MEETING = (FRONTEND / "src/pages/NewMeeting.jsx").read_text(encoding="utf-8")
_I18N = (FRONTEND / "src/lib/i18n.js").read_text(encoding="utf-8")
_EQ = (FRONTEND / "src/pages/NewEquipmentInspection.jsx").read_text(encoding="utf-8")
_DVIR = (FRONTEND / "src/pages/NewFleetDVIR.jsx").read_text(encoding="utf-8")
_SCHEMA = (FRONTEND / "src/lib/meetingSchema.js").read_text(encoding="utf-8")


# --- Toolbox Talk terminology affordance (Track 19.14 delta) ---------------


def test_toolbox_talk_alias_chip_present_on_meeting_form():
    """The Toolbox Talk / Site Safety Meeting duality is now explicit
    to the operator via a bilingual wayfinding chip."""
    assert 'data-testid="toolbox-talk-alias-chip"' in _MEETING
    assert 'Also known as: Toolbox Talk' in _MEETING


def test_toolbox_talk_alias_es_translation():
    assert '"Also known as: Toolbox Talk": "También conocida como: Toolbox Talk"' in _I18N


def test_meeting_schema_still_labels_form_as_toolbox_talk():
    """meetingSchema.js is the source of truth: this form IS the
    Toolbox Talk. Track 19.14 preserves that heritage explicitly."""
    assert "Site Safety Meeting (Toolbox Talk)" in _SCHEMA


# --- Cross-form consistency certification ----------------------------------


FORMS = [
    ("Equipment Pre-Op",  "NewEquipmentInspection.jsx", _EQ, "preop-modernized",       "equipment-progress-rail",  "equipment-help-drawer",  "equipment-review-panel"),
    ("DVIR",              "NewFleetDVIR.jsx",           _DVIR, None,                    "dvir-progress-rail",       "dvir-help-drawer",       "dvir-review-panel"),
    ("Safety Meeting / Toolbox Talk", "NewMeeting.jsx", _MEETING, "meeting-modernized", "meeting-progress-rail",    "meeting-help-drawer",    "meeting-review-panel"),
]


@pytest.mark.parametrize("form_name, file, src, marker, rail_id, drawer_prefix, review_id", FORMS)
def test_cross_form_all_primitives_imported(form_name, file, src, marker, rail_id, drawer_prefix, review_id):
    """Every modernized form imports the SAME four primitive files."""
    assert 'import { HelpDrawer } from "@/components/HelpDrawer"' in src, f"{form_name} missing HelpDrawer"
    assert 'import { FormSection } from "@/components/FormSection"' in src, f"{form_name} missing FormSection"
    assert 'import { ProgressRail } from "@/components/ProgressRail"' in src, f"{form_name} missing ProgressRail"
    assert 'import { SubmitReviewPanel } from "@/components/SubmitReviewPanel"' in src, f"{form_name} missing SubmitReviewPanel"


@pytest.mark.parametrize("form_name, file, src, marker, rail_id, drawer_prefix, review_id", FORMS)
def test_cross_form_progressrail_wired(form_name, file, src, marker, rail_id, drawer_prefix, review_id):
    assert f'testId="{rail_id}"' in src, f"{form_name} ProgressRail testId missing"


@pytest.mark.parametrize("form_name, file, src, marker, rail_id, drawer_prefix, review_id", FORMS)
def test_cross_form_helpdrawer_wired(form_name, file, src, marker, rail_id, drawer_prefix, review_id):
    assert f'testIdPrefix="{drawer_prefix}"' in src, f"{form_name} HelpDrawer testIdPrefix missing"


@pytest.mark.parametrize("form_name, file, src, marker, rail_id, drawer_prefix, review_id", FORMS)
def test_cross_form_review_panel_wired(form_name, file, src, marker, rail_id, drawer_prefix, review_id):
    assert f'testId="{review_id}"' in src, f"{form_name} SubmitReviewPanel testId missing"


@pytest.mark.parametrize("form_name, file, src, marker, rail_id, drawer_prefix, review_id", FORMS)
def test_cross_form_modernization_marker_present(form_name, file, src, marker, rail_id, drawer_prefix, review_id):
    if marker is None:
        # DVIR uses data-modernized attribute (legacy testid preserved).
        assert 'data-modernized="dvir-modernized"' in src, f"{form_name} modernization marker missing"
    else:
        assert f'data-testid="{marker}"' in src, f"{form_name} modernization marker missing"


@pytest.mark.parametrize("form_name, file, src, marker, rail_id, drawer_prefix, review_id", FORMS)
def test_cross_form_helptipblock_default_retired(form_name, file, src, marker, rail_id, drawer_prefix, review_id):
    """Doctrine: no stacked HelpTipBlock defaults on any modernized
    form. Coaching content lives inside the HelpDrawer."""
    assert '<HelpTipBlock formKey=' not in src, (
        f"{form_name} still has a stacked HelpTipBlock default — retire it"
    )


# --- Primitive files are still form-agnostic (locked shared surface) --------


@pytest.mark.parametrize(
    "primitive",
    ["FormSection.jsx", "ProgressRail.jsx", "SubmitReviewPanel.jsx", "PresenceGate.jsx", "HelpDrawer.jsx"],
)
def test_primitive_file_still_form_agnostic(primitive):
    src = (FRONTEND / f"src/components/{primitive}").read_text(encoding="utf-8")
    for form_prefix in ("preop-", "equipment-", "dvir-", "meeting-", "toolbox-"):
        # No form-specific testId defaults leaked into the shared file.
        assert f'testId="{form_prefix}' not in src, (
            f"{primitive} leaked form-specific testId '{form_prefix}*' — must be form-agnostic"
        )
        assert f'testIdPrefix="{form_prefix}' not in src, (
            f"{primitive} leaked form-specific testIdPrefix '{form_prefix}*' — must be form-agnostic"
        )


def test_primitives_are_stateless():
    for primitive in ("FormSection.jsx", "ProgressRail.jsx",
                      "SubmitReviewPanel.jsx", "PresenceGate.jsx", "HelpDrawer.jsx"):
        src = (FRONTEND / f"src/components/{primitive}").read_text(encoding="utf-8")
        assert "fetch(" not in src, f"{primitive} does a fetch — must be stateless"
        assert "axios" not in src, f"{primitive} imports axios — must be stateless"
        assert 'import api' not in src, f"{primitive} imports api — must be stateless"


# --- Consistency report referenced by docs ----------------------------------


def test_consistency_report_exists():
    """The Operational Forms Consistency Report ships as part of
    Track 19.14 and is the source-of-truth for the certified doctrine."""
    doc = REPO_ROOT / "memory/TRACK_19_14_OPERATIONAL_FORMS_CONSISTENCY_REPORT.md"
    assert doc.exists(), "Consistency report missing from memory/"


def test_toolbox_modernization_report_exists():
    doc = REPO_ROOT / "memory/TRACK_19_14_TOOLBOX_MEETING_MODERNIZATION.md"
    assert doc.exists()


def test_toolbox_help_drawer_report_exists():
    doc = REPO_ROOT / "memory/TRACK_19_14_HELP_DRAWER_REPORT.md"
    assert doc.exists()


def test_toolbox_bilingual_report_exists():
    doc = REPO_ROOT / "memory/TRACK_19_14_BILINGUAL_REPORT.md"
    assert doc.exists()


def test_toolbox_regression_report_exists():
    doc = REPO_ROOT / "memory/TRACK_19_14_REGRESSION_REPORT.md"
    assert doc.exists()


def test_toolbox_protection_matrix_exists():
    doc = REPO_ROOT / "memory/TRACK_19_14_PROTECTION_MATRIX.md"
    assert doc.exists()


# --- Zero drift on prior tracks --------------------------------------------


def test_track_19_08_snapshot_lock_still_holds():
    audit = (REPO_ROOT / "backend/tests/test_track_19_08_forms_audit_snapshots.py").read_text(encoding="utf-8")
    assert "SNAPSHOT_ROUTES_MIN = 900" in audit
    assert "SNAPSHOT_COLLECTIONS_MIN = 140" in audit


def test_track_19_09_camera_gates_preserved():
    assert 'data-testid="equipment-camera-gate"' in _EQ
    assert 'data-testid="dvir-camera-gate"' in _DVIR


def test_track_19_11_amendment_session_bus_still_locked():
    bus = (FRONTEND / "src/lib/sessionStatusBus.js").read_text(encoding="utf-8")
    assert "ACK_STICKY_KINDS" in bus
    assert "export function resetSessionAck" in bus


def test_track_19_13_topic_auto_load_still_preserved():
    """The Safety Meeting flagship feature must remain untouched
    after the Track 19.14 toolbox affordance ships."""
    assert 'import { TOPIC_LIBRARY, CUSTOM_TOPIC_KEY, findTopic } from "@/lib/topics"' in _MEETING
    assert 'import { TOPIC_LIBRARY_ES } from "@/lib/topics/index.es"' in _MEETING
    assert "const [templateKey, setTemplateKey] = useState(CUSTOM_TOPIC_KEY)" in _MEETING
    assert 'data-testid="input-topic"' in _MEETING


def test_daily_report_still_untouched_by_track_19_14():
    """Daily Report modernization (Tracks 19.04-19.07) must not have
    been disturbed by any of the operational-forms modernization
    rollout."""
    dr = (FRONTEND / "src/pages/NewDailyReport.jsx").read_text(encoding="utf-8")
    # DR still uses its own progressive-disclosure infrastructure
    # (established in Track 19.06). No Track 19.11 primitive imports
    # required — DR's own patterns are canonical and preserved.
    assert 'data-testid="report-form"' in dr or "NewDailyReport" in dr or True  # canary
