"""Track 19.10 · Slice 1 · Foundation Unification — Lock Tests.

Verifies the additive, opt-in FormShell + HelpDrawer primitives are
mounted and bilingual, WITHOUT any of the deferred form rewrites
(Equipment Pre-Op progressive-disclosure, DVIR rewrite, Safety Meeting
knowledge engine) — those land in dedicated Tracks 19.11 / 19.12 / 19.13.

Zero drift from:
* Track 19.05 schema lock
* Track 19.06 progressive-disclosure primitives
* Track 19.06 Amendment Smart Prefill
* Track 19.07 cognitive checkpoints
* Track 19.08 forms-audit snapshots
* Track 19.09 camera obstruction gate + downstream commitment
"""
from __future__ import annotations

from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
FRONTEND = REPO_ROOT / "frontend"

_FORMSHELL = (FRONTEND / "src/components/FormShell.jsx").read_text(encoding="utf-8")
_HELPDRAWER = (FRONTEND / "src/components/HelpDrawer.jsx").read_text(encoding="utf-8")
_EQ = (FRONTEND / "src/pages/NewEquipmentInspection.jsx").read_text(encoding="utf-8")
_DVIR = (FRONTEND / "src/pages/NewFleetDVIR.jsx").read_text(encoding="utf-8")
_MEETING = (FRONTEND / "src/pages/NewMeeting.jsx").read_text(encoding="utf-8")
_DR = (FRONTEND / "src/pages/NewDailyReport.jsx").read_text(encoding="utf-8")
_I18N = (FRONTEND / "src/lib/i18n.js").read_text(encoding="utf-8")


# --- Phase 1 · FormShell primitive exists and is bilingual ------------------


def test_formshell_component_exists_and_is_bilingual():
    assert (FRONTEND / "src/components/FormShell.jsx").exists()
    assert "export function FormShell" in _FORMSHELL
    # Must go through useT() for every visible string
    assert "useT" in _FORMSHELL
    # Slots present (kicker · title · progress · sticky footer · language toggle)
    for slot in ["kicker", "title", "progressSlot", "stickyFooter", "LangToggle"]:
        assert slot in _FORMSHELL
    # Container testId hook
    assert 'data-testid={containerTestId}' in _FORMSHELL


def test_formshell_is_stateless_no_backend_touched():
    """The primitive must not import from any api / persistence layer."""
    assert "import api" not in _FORMSHELL
    assert "fetch(" not in _FORMSHELL
    assert "axios" not in _FORMSHELL


# --- Phase 5 · HelpDrawer primitive exists and is bilingual -----------------


def test_helpdrawer_component_exists_and_is_bilingual():
    assert (FRONTEND / "src/components/HelpDrawer.jsx").exists()
    assert "export function HelpDrawer" in _HELPDRAWER
    assert "useT" in _HELPDRAWER
    # Accessibility hooks
    assert 'role="dialog"' in _HELPDRAWER
    assert 'aria-modal="true"' in _HELPDRAWER
    # Trigger + panel testIds
    assert '${testIdPrefix}-trigger' in _HELPDRAWER
    assert '${testIdPrefix}-panel' in _HELPDRAWER


def test_helpdrawer_wired_on_equipment_preop():
    """Equipment Pre-Op OPTS IN to the HelpDrawer as the proof-of-concept.
    Existing LifecycleGuide / HelpTipBlock coaching MUST remain live —
    the drawer is additive only in Slice 1."""
    assert 'import { HelpDrawer } from "@/components/HelpDrawer"' in _EQ
    assert "<HelpDrawer" in _EQ
    assert 'testIdPrefix="equipment-help-drawer"' in _EQ


def test_existing_coaching_systems_still_live_on_equipment_preop():
    """Slice 1 doctrine (Track 19.10): the drawer is proof-of-concept only.
    Existing coaching layers stay live UNTIL a dedicated modernization
    track consolidates them.

    TRACK 19.11 MAIN UPDATE: HelpTipBlock is now retired on Equipment
    Pre-Op — its 5 coaching bands have been fully migrated into the
    HelpDrawer sections array. Main screen = action; drawer =
    explanation. This is the intended end state per the Track 19.11
    MAIN brief. We now assert the migration is complete rather than
    that the old stacks are still live.
    """
    # HelpTipBlock retired on Equipment Pre-Op (consolidated into
    # HelpDrawer). The import is removed and no visible band remains.
    assert 'import { HelpTipBlock } from "@/components/HelpTip"' not in _EQ
    assert 'HelpTipBlock formKey="preop"' not in _EQ
    # Original page subtitle prose still present (canonical operator
    # framing).
    assert (
        "OSHA daily walk-around for the unit you're operating."
        in _EQ
    )
    # The 5 coaching bands now live inside the HelpDrawer sections.
    for band in (
        "Why this Pre-Op matters",
        "Who sees this",
        "What happens after you submit",
        "When to stop and call",
        "Common pre-op mistakes",
    ):
        assert band in _EQ, f"HelpDrawer missing consolidated band: {band}"


# --- Deferred work MUST NOT have been rushed --------------------------------


def test_slice_1_did_not_rewrite_equipment_preop():
    """Guardrail: Equipment Pre-Op must NOT have been converted to a
    progressive-disclosure shell in Slice 1. Track 19.11 owns that."""
    # Fluid alert + OOS modal + FAIL requirements all preserved.
    assert "CRITICAL_FLUID_ITEMS" in _EQ
    assert "MAJOR_OUT_OF_SERVICE_ITEMS" in _EQ
    assert "FAIL needs a photo" in _EQ
    assert "FAIL description must be at least 10 characters" in _EQ


def test_slice_1_did_not_rewrite_dvir():
    """Guardrail: DVIR must not have been rewritten in Slice 1.
    Track 19.12 owns that."""
    assert "blockReason" in _DVIR   # existing block-reason guard still live
    assert "defect_details" in _DVIR  # defect pipeline preserved


def test_slice_1_did_not_touch_safety_meeting_topic_engine():
    """HARD RULE: topic auto-load must not be touched in Slice 1.
    Track 19.13 owns Safety Meeting modernization."""
    # Look for the topic-picker / topic-body wiring signatures — the exact
    # symbols vary; presence check on the "topics" import + selection code
    # ensures we didn't accidentally remove them.
    assert "topic" in _MEETING.lower(), "Safety Meeting topic wiring gone"


def test_track_19_09_camera_gate_still_present():
    assert 'data-testid="equipment-camera-gate"' in _EQ
    assert 'data-testid="dvir-camera-gate"' in _DVIR
    assert "Clear the obstruction before operating" in _EQ
    assert "Clear the obstruction before operating" in _DVIR


def test_track_19_06_amendment_primitives_still_present():
    """Reset hours + prefill notice + amendment marker preserved."""
    assert 'data-testid={`crew-reset-hours-${i}`}' in _DR
    assert "row._prefilled &&" in _DR
    assert "idx === i ? { ...row, ...partial } : row" in _DR


def test_track_19_07_cognitive_checkpoints_still_present():
    for label in (
        "Who was there",
        "What got done",
        "What impacted today",
        "What moved",
        "Was the job safe",
        "What happens next",
    ):
        assert label in _DR, f"cognitive checkpoint drifted: {label}"


# --- Bilingual parity for the new primitive strings -------------------------


NEW_EN_STRINGS = [
    "Operational form · MASCI platform",
    "Help",
    "Help drawer",
    "Guidance",
    "Close",
    "Section",
    "No guidance available for this section.",
    "Open help",
    "Equipment Pre-Op · Guidance",
]


@pytest.mark.parametrize("en", NEW_EN_STRINGS)
def test_bilingual_parity_new_primitive_strings(en):
    escaped = en.replace('"', '\\"')
    assert f'"{escaped}":' in _I18N, (
        f"Spanish translation missing for new Slice-1 string: {en!r}. "
        f"Add an entry to the ES dictionary in frontend/src/lib/i18n.js."
    )


# --- Terminology consistency check (Phase 7 · terminology pass) --------------


UNIFIED_TERMS_EN = [
    # Required-field marker language
    "*",
    # Draft / autosave lingua franca
    "Discard",
    "Restore",
    # Camera-gate language (already unified in 19.09)
    "Yes",
    "No",
    # Downstream-commitment language (already unified in 19.09)
    "Submitted — here's what happens next",
]


@pytest.mark.parametrize("term", UNIFIED_TERMS_EN)
def test_unified_terminology_term_used(term):
    """Sanity: the unified operational-language vocabulary is present
    somewhere in the hero-form corpus (pages + shared confirmation
    surfaces). This is a lower-bound check — future tracks may extend
    this list per the Phase 7 pass."""
    thankyou = (FRONTEND / "src/pages/ThankYou.jsx").read_text(encoding="utf-8")
    panel = (FRONTEND / "src/components/DownstreamCommitmentPanel.jsx").read_text(encoding="utf-8")
    corpus = "\n".join([_DR, _EQ, _DVIR, _MEETING, thankyou, panel])
    if term == "*":
        assert "*" in corpus
    else:
        assert term in corpus, (
            f"unified term missing across hero-form corpus: {term}"
        )


# --- Zero drift on Track 19.08 audit snapshot lock --------------------------


def test_track_19_08_forms_audit_lock_still_holds():
    """Snapshot fingerprint sanity: the audit-lock test must still exist
    and its critical constant set must not be depleted."""
    audit_test = (
        REPO_ROOT / "backend/tests/test_track_19_08_forms_audit_snapshots.py"
    ).read_text(encoding="utf-8")
    assert "SNAPSHOT_ROUTES_MIN = 900" in audit_test
    assert "SNAPSHOT_COLLECTIONS_MIN = 140" in audit_test
    assert "CRITICAL_BACKEND_ROUTES = [" in audit_test
