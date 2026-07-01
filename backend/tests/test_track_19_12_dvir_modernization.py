"""Track 19.12 · DVIR Modernization — Lock Tests.

Doctrine:
    DVIR is the SECOND production consumer of the four Track 19.11
    MAIN reusable platform primitives (FormSection, ProgressRail,
    PresenceGate, SubmitReviewPanel) + HelpDrawer + FormShell. Its
    modernization proves the primitives generalize; the primitives
    themselves DO NOT change between Equipment Pre-Op and DVIR.

Zero drift from:
    * Track 19.05 schema lock
    * Track 19.08 forms-audit snapshots
    * Track 19.09 camera obstruction gate (DVIR variant)
    * Track 19.10 FormShell / HelpDrawer primitives
    * Track 19.11 Amendment session-expired ack-suppression
    * Track 19.11 Part A session language state
    * Track 19.11 MAIN Equipment Pre-Op modernization primitives
"""
from __future__ import annotations

from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
FRONTEND = REPO_ROOT / "frontend"

_DVIR = (FRONTEND / "src/pages/NewFleetDVIR.jsx").read_text(encoding="utf-8")
_I18N = (FRONTEND / "src/lib/i18n.js").read_text(encoding="utf-8")


# --- DVIR consumes the four Track 19.11 MAIN primitives --------------------


@pytest.mark.parametrize(
    "primitive_import",
    [
        'import { HelpDrawer } from "@/components/HelpDrawer"',
        'import { FormSection } from "@/components/FormSection"',
        'import { ProgressRail } from "@/components/ProgressRail"',
        'import { SubmitReviewPanel } from "@/components/SubmitReviewPanel"',
    ],
)
def test_dvir_imports_platform_primitive(primitive_import):
    assert primitive_import in _DVIR


def test_dvir_modernization_marker_present():
    """The `data-modernized` marker + the pre-existing
    `data-testid="fleet-dvir-form"` both remain — the marker signals
    that the Track 19.12 pass has landed; the testid preserves the
    Track 19.09 lock contract."""
    assert 'data-testid="fleet-dvir-form"' in _DVIR
    assert 'data-modernized="dvir-modernized"' in _DVIR


def test_dvir_helpdrawer_wired():
    assert "<HelpDrawer" in _DVIR
    assert 'testIdPrefix="dvir-help-drawer"' in _DVIR


def test_dvir_progressrail_wired():
    assert "<ProgressRail" in _DVIR
    assert 'testId="dvir-progress-rail"' in _DVIR
    assert "progressSteps" in _DVIR
    assert "progressCurrentIndex" in _DVIR


def test_dvir_review_section_and_panel_wired():
    assert "<FormSection" in _DVIR
    assert 'testId="dvir-review-section"' in _DVIR
    assert "<SubmitReviewPanel" in _DVIR
    assert 'testId="dvir-review-panel"' in _DVIR


def test_dvir_helpdrawer_carries_all_five_bands():
    for band_title in (
        "Why this DVIR matters",
        "Who sees this",
        "What happens after you submit",
        "When to stop and call",
        "Common DVIR mistakes",
    ):
        assert f't("{band_title}")' in _DVIR, (
            f"DVIR HelpDrawer missing consolidated band: {band_title}"
        )


# --- Consolidation: noisy default coaching retired --------------------------


def test_dvir_helptipblock_default_retired():
    """The noisy top-level `<HelpTipBlock formKey={formCopy.helpFormKey}>`
    that stacked contextual coaching above every DVIR section is
    RETIRED. Its content is now consolidated inside the HelpDrawer.
    Main screen = action; drawer = explanation."""
    assert "HelpTipBlock formKey={formCopy.helpFormKey}" not in _DVIR


# --- Preservation: every Track 19.09 protection intact ---------------------


def test_dvir_camera_gate_preserved_track_19_09():
    assert 'data-testid="dvir-camera-gate"' in _DVIR
    assert "Clear the obstruction before operating" in _DVIR


def test_dvir_block_reason_preserved():
    """DVIR submit-blocker (defect-details / severity / signature)
    logic must remain intact — the modernization is UX only."""
    assert "blockReason" in _DVIR
    assert 'data-testid="dvir-block-reason"' in _DVIR
    assert 'data-testid="dvir-submit"' in _DVIR


def test_dvir_signature_preserved():
    assert "SignaturePad" in _DVIR
    assert 'testId="dvir-signature"' in _DVIR


def test_dvir_defect_details_pipeline_preserved():
    """The DVIR-specific defect-details capture pipeline (per-FAIL
    photo + description + severity) must remain."""
    assert "defect_details" in _DVIR
    assert "SeverityRationale" in _DVIR


def test_dvir_camera_state_and_payload_keys_preserved():
    """Track 19.09 payload keys must not drift."""
    for key in ("cameraSystemPresent", "cameraClear", "cameraObstructionNote"):
        assert key in _DVIR


def test_dvir_severity_table_version_marker_preserved():
    assert 'data-testid="dvir-severity-version"' in _DVIR


def test_dvir_bilingual_toggle_preserved():
    """LangToggle mounted in header."""
    assert "<LangToggle" in _DVIR


# --- Bilingual parity for new Track 19.12 strings --------------------------


NEW_DVIR_STRINGS = [
    "Driver",
    "DVIR · Guidance",
    "Why this DVIR matters",
    "Shop, Dispatch, Fleet, and the PM review every FAIL. Historical records are kept for DOT audits.",
    "If anything is Out of Service, Shop is notified automatically and Dispatch will reassign. Monitor items go to the shop queue for repair scheduling. A permanent historical record is created.",
    "If a critical defect appears or the camera view is obstructed, do not drive the truck. Tag it, call Shop, and get with your supervisor.",
    "Common DVIR mistakes",
    "Marking N/A when it should be FAIL, skipping the description on a FAIL, and not attaching a photo. Every FAIL needs a clear description Shop can act on.",
    "Confirm the DVIR summary before you submit. What happens next is listed below.",
    "Lead inspector signature captured.",
    "Inspector signature captured.",
    "Driver signature captured.",
    "Signature pending.",
]


@pytest.mark.parametrize("en", NEW_DVIR_STRINGS)
def test_new_dvir_string_has_es_translation(en):
    escaped = en.replace('"', '\\"')
    assert f'"{escaped}":' in _I18N, (
        f"Missing ES translation for new Track 19.12 DVIR string: {en!r}"
    )


# --- Zero backend drift ----------------------------------------------------


def test_dvir_no_new_backend_endpoints():
    """The modernization is 100% frontend. No new API endpoints, no
    schema changes, no route additions. Backend snapshot lock (Track
    19.08) still holds."""
    audit_path = REPO_ROOT / "backend/tests/test_track_19_08_forms_audit_snapshots.py"
    audit = audit_path.read_text(encoding="utf-8")
    assert "SNAPSHOT_ROUTES_MIN = 900" in audit
    assert "SNAPSHOT_COLLECTIONS_MIN = 140" in audit


# --- Cross-form consistency: DVIR primitives === Equipment Pre-Op ----------


def test_primitives_are_same_files_across_forms():
    """The Track 19.11 MAIN promise: DVIR (19.12) consumes the SAME
    primitive files as Equipment Pre-Op. No competing forks."""
    eq = (FRONTEND / "src/pages/NewEquipmentInspection.jsx").read_text(encoding="utf-8")
    for imp in (
        'import { HelpDrawer } from "@/components/HelpDrawer"',
        'import { FormSection } from "@/components/FormSection"',
        'import { ProgressRail } from "@/components/ProgressRail"',
        'import { SubmitReviewPanel } from "@/components/SubmitReviewPanel"',
    ):
        assert imp in eq, f"Equipment Pre-Op missing {imp}"
        assert imp in _DVIR, f"DVIR missing {imp}"


def test_primitive_files_untouched_by_dvir_adoption():
    """A key doctrine: DVIR configures the primitives, DVIR does NOT
    modify the primitives. The four primitives must remain
    form-agnostic — no DVIR-specific JSX / props / testId defaults."""
    fs = (FRONTEND / "src/components/FormSection.jsx").read_text(encoding="utf-8")
    pr = (FRONTEND / "src/components/ProgressRail.jsx").read_text(encoding="utf-8")
    srp = (FRONTEND / "src/components/SubmitReviewPanel.jsx").read_text(encoding="utf-8")
    pg = (FRONTEND / "src/components/PresenceGate.jsx").read_text(encoding="utf-8")
    for src in (fs, pr, srp, pg):
        # No DVIR-specific testId default leaked into the primitive.
        # (Comments mentioning DVIR as a future consumer are allowed —
        # we grep only for DVIR-specific testId / prop / route names.)
        assert 'testId="dvir-' not in src, (
            "A primitive shipped a DVIR-specific testId default — must be "
            "form-agnostic (configuration, not reinvention)."
        )
        assert '"/fleet-dvirs"' not in src
        # Still stateless.
        assert "fetch(" not in src
        assert "axios" not in src


def test_track_19_11_main_locks_still_hold():
    """The Equipment Pre-Op modernization must remain locked GREEN
    after DVIR adoption. We do this by asserting the modernization
    marker + primitives adoption are still in place on Equipment
    Pre-Op (no accidental cross-form regression)."""
    eq = (FRONTEND / "src/pages/NewEquipmentInspection.jsx").read_text(encoding="utf-8")
    assert 'data-testid="preop-modernized"' in eq
    assert 'testId="equipment-progress-rail"' in eq
    assert 'testId="equipment-review-panel"' in eq


def test_track_19_11_amendment_session_bus_untouched():
    bus = (FRONTEND / "src/lib/sessionStatusBus.js").read_text(encoding="utf-8")
    assert "ACK_STICKY_KINDS" in bus
    assert "export function resetSessionAck" in bus
