"""Track 19.11 · MAIN · Equipment Pre-Op Modernization — Lock Tests.

Doctrine:
    Track 19.11 MAIN modernizes Equipment Pre-Op UX using a set of
    reusable platform primitives that DVIR (19.12) and Safety Meeting
    (19.13) will consume unchanged — configuration, not reinvention.

Primitives locked:
    * FormSection.jsx     — active/completed/pending section wrapper
    * ProgressRail.jsx    — compact multi-step progress indicator
    * PresenceGate.jsx    — reusable Yes/No/Not-sure presence gate
    * SubmitReviewPanel.jsx — pre-submit review + downstream commit
    * HelpDrawer.jsx      — single coaching system (already existed)
    * FormShell.jsx       — shell primitive (already existed)

Zero drift from:
    * Track 19.05 schema lock
    * Track 19.06 progressive-disclosure primitives
    * Track 19.07 cognitive checkpoints
    * Track 19.08 forms-audit snapshots
    * Track 19.09 camera obstruction gate + fail-cascade + OOS modal
    * Track 19.10 FormShell/HelpDrawer primitives
    * Track 19.11 Amendment session-expired ack-suppression
    * Track 19.11 Part A session overlay language state
"""
from __future__ import annotations

from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
FRONTEND = REPO_ROOT / "frontend"

_EQ = (FRONTEND / "src/pages/NewEquipmentInspection.jsx").read_text(encoding="utf-8")
_I18N = (FRONTEND / "src/lib/i18n.js").read_text(encoding="utf-8")
_FORMSECTION = (FRONTEND / "src/components/FormSection.jsx").read_text(encoding="utf-8")
_PROGRESSRAIL = (FRONTEND / "src/components/ProgressRail.jsx").read_text(encoding="utf-8")
_PRESENCEGATE = (FRONTEND / "src/components/PresenceGate.jsx").read_text(encoding="utf-8")
_SUBMITREVIEW = (FRONTEND / "src/components/SubmitReviewPanel.jsx").read_text(encoding="utf-8")
_HELPDRAWER = (FRONTEND / "src/components/HelpDrawer.jsx").read_text(encoding="utf-8")
_FORMSHELL = (FRONTEND / "src/components/FormShell.jsx").read_text(encoding="utf-8")


# --- Reusable primitives exist, are stateless, and bilingual ----------------


@pytest.mark.parametrize(
    "path, symbol",
    [
        ("src/components/FormSection.jsx", "export function FormSection"),
        ("src/components/ProgressRail.jsx", "export function ProgressRail"),
        ("src/components/PresenceGate.jsx", "export function PresenceGate"),
        ("src/components/SubmitReviewPanel.jsx", "export function SubmitReviewPanel"),
    ],
)
def test_primitive_exists_and_is_exported(path, symbol):
    src = (FRONTEND / path).read_text(encoding="utf-8")
    assert symbol in src, f"{path} does not export the expected primitive"


@pytest.mark.parametrize(
    "src_name, src",
    [
        ("FormSection", _FORMSECTION),
        ("ProgressRail", _PROGRESSRAIL),
        ("PresenceGate", _PRESENCEGATE),
        ("SubmitReviewPanel", _SUBMITREVIEW),
    ],
)
def test_primitive_is_stateless(src_name, src):
    """Every new primitive must be pure visual scaffolding — no API
    calls, no persistence writes. All interactive state lives on the
    parent page. This preserves zero-drift on backend contracts."""
    assert "fetch(" not in src, f"{src_name} does a fetch — must be stateless"
    assert "axios" not in src, f"{src_name} imports axios — must be stateless"
    assert "import api" not in src, f"{src_name} imports api — must be stateless"
    assert "localStorage" not in src, f"{src_name} touches localStorage"


@pytest.mark.parametrize(
    "src_name, src",
    [
        ("FormSection", _FORMSECTION),
        ("ProgressRail", _PROGRESSRAIL),
        ("PresenceGate", _PRESENCEGATE),
        ("SubmitReviewPanel", _SUBMITREVIEW),
    ],
)
def test_primitive_is_bilingual(src_name, src):
    """Every operator-facing string must route through useT()."""
    assert 'import { useT } from "@/lib/i18n"' in src, f"{src_name} not wired to i18n"
    assert "useT()" in src


# --- Equipment Pre-Op consumes the new primitives ---------------------------


@pytest.mark.parametrize(
    "primitive_import",
    [
        'import { FormSection } from "@/components/FormSection"',
        'import { ProgressRail } from "@/components/ProgressRail"',
        'import { SubmitReviewPanel } from "@/components/SubmitReviewPanel"',
        'import { HelpDrawer } from "@/components/HelpDrawer"',
    ],
)
def test_equipment_preop_imports_primitive(primitive_import):
    assert primitive_import in _EQ


def test_equipment_preop_mounts_progressrail():
    assert "<ProgressRail" in _EQ
    assert 'testId="equipment-progress-rail"' in _EQ


def test_progressrail_steps_declared_and_derived_from_state():
    """Steps live inside a useMemo and are pure derivations of `data`.
    The primitive itself is stateless — the parent form owns state."""
    assert "const progressSteps = useMemo" in _EQ
    assert "const progressCurrentIndex = useMemo" in _EQ


def test_equipment_preop_uses_formsection_for_review():
    """The Review & Submit step is wrapped in a FormSection (the new
    primitive) — demonstrating the pattern the future full-refactor
    tracks (19.12 / 19.13) will apply across every section."""
    assert "<FormSection" in _EQ
    assert 'testId="equipment-review-section"' in _EQ


def test_equipment_preop_mounts_submit_review_panel():
    assert "<SubmitReviewPanel" in _EQ
    assert 'testId="equipment-review-panel"' in _EQ


def test_equipment_preop_marker_data_testid():
    """Modernization marker so live smoke can verify the new build
    reached the browser."""
    assert 'data-testid="preop-modernized"' in _EQ


# --- Consolidated HelpDrawer (single coaching system) ----------------------


def test_stacked_helptip_bands_retired_from_default_view():
    """HelpTipBlock components at the top of Equipment Pre-Op are
    RETIRED — they used to stack 3 separate coaching cards above the
    form. All 5 coaching bands now live inside the HelpDrawer.
    Doctrine: main screen = action; drawer = explanation."""
    assert "HelpTipBlock formKey=\"preop\"" not in _EQ
    assert "HelpTipBlock formKey=\"preop.defects\"" not in _EQ
    assert "HelpTipBlock formKey=\"preop.signoff\"" not in _EQ


def test_helptip_import_removed_from_equipment_preop():
    """No dead imports. The HelpTipBlock module is not referenced."""
    assert 'import { HelpTipBlock } from "@/components/HelpTip"' not in _EQ


def test_helpdrawer_carries_all_five_coaching_bands():
    """The 5 bands that used to stack above the form must all appear
    inside the drawer's sections array."""
    for title in [
        "Why this Pre-Op matters",
        "Who sees this",
        "What happens after you submit",
        "When to stop and call",
        "Common pre-op mistakes",
    ]:
        assert f't("{title}")' in _EQ, f"HelpDrawer missing consolidated band: {title}"


def test_helpdrawer_trigger_testid_stable():
    """The Playwright + operator-facing selector must not drift."""
    assert 'testIdPrefix="equipment-help-drawer"' in _EQ


# --- Preservation: every fail-cascade / gate / lock still in place ----------


def test_camera_obstruction_gate_preserved_track_19_09():
    """Track 19.09 hard-gate must remain untouched by 19.11 MAIN."""
    assert 'data-testid="equipment-camera-gate"' in _EQ
    # Camera Yes/No/Not-sure testIds are passed as opt.testId props.
    assert '"camera-system-yes"' in _EQ
    assert '"camera-system-no"' in _EQ
    assert '"camera-system-unsure"' in _EQ
    assert 'data-testid="camera-clear-yes"' in _EQ
    assert 'data-testid="camera-clear-no"' in _EQ
    assert 'data-testid="camera-obstruction-block"' in _EQ
    assert "Clear the obstruction before operating" in _EQ


def test_critical_fluid_alert_preserved():
    """OOS stop-work modal (fluid / major-safety) must remain."""
    assert "criticalFluidAlert" in _EQ
    assert 'data-testid="critical-fluid-modal"' in _EQ
    assert 'data-testid="critical-fluid-acknowledge"' in _EQ


def test_out_of_service_sets_preserved():
    """The two protected sets driving OOS classification MUST NOT
    be renamed or deleted."""
    assert "CRITICAL_FLUID_ITEMS" in _EQ
    assert "MAJOR_OUT_OF_SERVICE_ITEMS" in _EQ
    assert "const isOutOfServiceItem" in _EQ


def test_fail_photo_and_description_validation_preserved():
    """FAIL requires photo + 10-char description. This is a safety
    lock the pytest suite has enforced since Track 19.09."""
    assert "FAIL needs a photo" in _EQ
    assert "FAIL description must be at least 10 characters" in _EQ
    assert "FAIL needs a description" in _EQ


def test_submit_payload_route_unchanged():
    """Zero payload / route drift. The submit call must still target
    the exact endpoint that Track 19.08 snapshotted."""
    assert 'api.post("/equipment-inspections", payload)' in _EQ


def test_signature_capture_preserved():
    assert "SignaturePad" in _EQ
    assert 'testId="signature-operator"' in _EQ


def test_bilingual_translation_pipeline_preserved():
    """ES → EN translation before submit (canonical storage) must
    still fire when lang === 'es'. This is a Trust-Spine contract."""
    assert 'if (lang === "es")' in _EQ
    assert "translateUserInput" in _EQ
    assert "persistBilingualSidecar" in _EQ


def test_canonical_inspection_sections_preserved():
    assert "CanonicalInspectionSections" in _EQ
    assert "canonicalCapture" in _EQ
    assert "inspection_sections" in _EQ


def test_tally_bar_preserved():
    """Sticky tally bar (Track 19.06-era) must not have been removed
    by the modernization."""
    assert 'data-testid="equip-tally-bar"' in _EQ
    assert 'data-testid="tally-pass"' in _EQ
    assert 'data-testid="tally-fail"' in _EQ
    assert 'data-testid="tally-na"' in _EQ


# --- Bilingual parity for every new Track 19.11 MAIN string ----------------


NEW_STRINGS = [
    "Step",
    "Setup",
    "Cameras",
    "Inspection",
    "Notes",
    "Sign",
    "Review",
    "Who sees this",
    "Common pre-op mistakes",
    "Review & Submit",
    "Confirm the inspection summary before you submit. What happens next is listed below.",
    "PASS",
    "FAIL",
    "N/A",
    "What happens after you submit",
    "Inspection will be recorded in the operational history.",
    "Failed items may mark this unit OUT OF SERVICE until shop clears it.",
    "The shop team may be notified per project routing.",
    "Your supervisor and safety may be notified per project routing.",
    "Corrective action may be required before the unit is used again.",
    "A permanent historical record will be created for audits.",
    "Cameras present and clear of obstructions.",
    "This unit does not have a camera system.",
    "Camera presence marked as not sure — flagged for review.",
    "Camera obstruction present — submission blocked until cleared.",
    "Camera check not yet answered.",
    "Operator signature captured.",
    "Operator signature pending.",
    "Out of Service",
]


@pytest.mark.parametrize("en", NEW_STRINGS)
def test_new_string_has_es_translation(en):
    escaped = en.replace('"', '\\"')
    assert f'"{escaped}":' in _I18N, (
        f"Missing ES translation for new Track 19.11 MAIN string: {en!r}"
    )


# --- Zero backend drift ----------------------------------------------------


def test_backend_snapshot_lock_still_holds():
    audit_path = REPO_ROOT / "backend/tests/test_track_19_08_forms_audit_snapshots.py"
    audit = audit_path.read_text(encoding="utf-8")
    assert "SNAPSHOT_ROUTES_MIN = 900" in audit
    assert "SNAPSHOT_COLLECTIONS_MIN = 140" in audit
    assert "CRITICAL_BACKEND_ROUTES = [" in audit


def test_no_new_backend_files_touched():
    """The full modernization is frontend-only. No new backend
    endpoints, no schema changes, no route additions. Enforced by
    the audit-snapshot lock; this test asserts intent."""
    # Grep the equipment page for any new endpoint patterns beyond the
    # canonical POST + GET(equipment-types).
    lines = _EQ.splitlines()
    api_calls = [
        ln for ln in lines
        if "api.get(" in ln or "api.post(" in ln or "api.put(" in ln or "api.delete(" in ln
    ]
    # Only 2 authorized calls: GET /equipment-types + POST /equipment-inspections.
    joined = "\n".join(api_calls)
    assert 'api.get("/equipment-types")' in joined
    assert 'api.post("/equipment-inspections", payload)' in joined
    for ln in api_calls:
        # Must not have introduced any other endpoint.
        allowed = "/equipment-types" in ln or "/equipment-inspections" in ln
        assert allowed, f"UNAUTHORIZED backend call added: {ln}"


# --- Preservation of preceding tracks ---------------------------------------


def test_track_19_10_helpdrawer_still_wired():
    """HelpDrawer (Track 19.10) is still the only help-drawer path."""
    assert "<HelpDrawer" in _EQ
    assert 'testIdPrefix="equipment-help-drawer"' in _EQ


def test_track_19_11_amendment_session_bus_untouched():
    """Track 19.11 Amendment (session-expired ack-suppression) must
    remain intact — the modernization did not accidentally touch the
    session-status bus."""
    bus = (FRONTEND / "src/lib/sessionStatusBus.js").read_text(encoding="utf-8")
    assert "ACK_STICKY_KINDS" in bus
    assert "export function resetSessionAck" in bus
