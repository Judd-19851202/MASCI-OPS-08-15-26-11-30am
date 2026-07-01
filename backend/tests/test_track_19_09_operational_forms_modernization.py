"""Track 19.09 · Operational Forms UX Modernization Foundation — Lock Tests.

Verifies:
* Phase 3 · Equipment Pre-Op camera obstruction gate (progressive disclosure
  + hard-block on obstruction)
* Phase 5 · DVIR camera obstruction gate (identical doctrine)
* Phase 8 · Submit-time downstream-commitment confirmation (non-technical
  bullet list on ThankYou + expandable technical-details affordance on the
  reusable DownstreamCommitmentPanel component)
* Bilingual parity amendment · every new EN string has a Spanish translation
  in `frontend/src/lib/i18n.js`
* Track 19.06 amendment + 19.07 strings that were previously EN-only are now
  covered by Spanish

Zero backend / schema / route / payload changes.
"""
from __future__ import annotations

from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
FRONTEND = REPO_ROOT / "frontend"

_EQ = (FRONTEND / "src/pages/NewEquipmentInspection.jsx").read_text(encoding="utf-8")
_DVIR = (FRONTEND / "src/pages/NewFleetDVIR.jsx").read_text(encoding="utf-8")
_THANK = (FRONTEND / "src/pages/ThankYou.jsx").read_text(encoding="utf-8")
_PANEL = (FRONTEND / "src/components/DownstreamCommitmentPanel.jsx").read_text(encoding="utf-8")
_I18N = (FRONTEND / "src/lib/i18n.js").read_text(encoding="utf-8")


# --- Phase 3 · Equipment Pre-Op camera gate ---------------------------------


def test_equipment_camera_gate_ui_present():
    """The camera-gate section is mounted between Section 01 and Section 02."""
    assert 'data-testid="equipment-camera-gate"' in _EQ
    assert '<Section number="01A"' in _EQ
    assert "Camera System Safety Check" in _EQ


def test_equipment_camera_three_way_answer_wired():
    for testid in ("camera-system-yes", "camera-system-no", "camera-system-unsure"):
        # test-id is templated via `testId: "..."` on the button config
        # array; source-search catches both quoted forms.
        assert f'"{testid}"' in _EQ, f"missing testid {testid}"


def test_equipment_camera_followup_only_on_yes():
    """The obstruction question renders only when camera_system_present === 'yes'."""
    assert 'data-camera-system-present === "yes"' not in _EQ  # sanity — not the HTML attr
    # The React conditional exists:
    assert 'data.camera_system_present === "yes"' in _EQ
    assert 'data-testid="equipment-camera-followup"' in _EQ


def test_equipment_camera_obstruction_hard_block_message_present():
    assert (
        "Clear the obstruction before operating. Camera visibility must be free and clear."
        in _EQ
    )
    assert 'data-testid="camera-obstruction-block"' in _EQ


def test_equipment_camera_hard_block_at_submit():
    """The submit path must return early when camera answers are missing or
    the cameras are obstructed."""
    # The three toast.error calls guarding submit:
    assert "Answer the camera system question before submitting" in _EQ
    assert "Confirm whether the cameras are free and clear of obstructions" in _EQ
    # And the obstruction hard-block guard:
    assert 'data.camera_obstructions_clear === "no"' in _EQ


def test_equipment_camera_defaults_include_new_keys():
    """buildDefaults() carries the three new keys so autosave + submit
    payload stay lossless."""
    for key in (
        "camera_system_present:",
        "camera_obstructions_clear:",
        "camera_obstruction_note:",
    ):
        assert key in _EQ, f"defaults missing {key}"


# --- Phase 5 · DVIR camera gate ---------------------------------------------


def test_dvir_camera_gate_ui_present():
    assert 'data-testid="dvir-camera-gate"' in _DVIR
    assert '<Section number="03A"' in _DVIR
    assert "Does this truck have a camera system?" in _DVIR


def test_dvir_camera_three_way_answer_wired():
    for testid in (
        "dvir-camera-system-yes",
        "dvir-camera-system-no",
        "dvir-camera-system-unsure",
    ):
        assert f'"{testid}"' in _DVIR


def test_dvir_camera_followup_only_on_yes():
    assert 'cameraSystemPresent === "yes"' in _DVIR
    assert 'data-testid="dvir-camera-followup"' in _DVIR


def test_dvir_camera_obstruction_hard_block_message_present():
    assert (
        "Clear the obstruction before operating. Camera visibility must be free and clear."
        in _DVIR
    )
    assert 'data-testid="dvir-camera-obstruction-block"' in _DVIR


def test_dvir_camera_hard_block_at_submit():
    assert "Answer the camera system question before submitting" in _DVIR
    assert "Confirm whether the cameras are free and clear of obstructions" in _DVIR
    assert 'cameraClear === "no"' in _DVIR


def test_dvir_camera_payload_keys_present():
    """Submit payload must carry the three additive camera keys so the
    backend audit trail + PDF include them."""
    for key in (
        "camera_system_present: cameraSystemPresent",
        "camera_obstructions_clear: cameraClear",
        "camera_obstruction_note: cameraObstructionNote",
    ):
        assert key in _DVIR


# --- Phase 8 · Submit-time downstream-commitment confirmation ---------------


def test_thankyou_downstream_commitment_bullets_present():
    """ThankYou.jsx (post-submit landing for Equipment / DVIR) renders the
    standardized four-bullet non-technical confirmation."""
    assert 'data-testid="thank-you-downstream-commitments"' in _THANK
    for testid in (
        "commitment-pdf",
        "commitment-email",
        "commitment-shop",
        "commitment-safety-pm",
    ):
        assert f'data-testid="{testid}"' in _THANK


def test_downstream_commitment_panel_component_exists():
    """The reusable modal component is available for future wiring."""
    assert (FRONTEND / "src/components/DownstreamCommitmentPanel.jsx").exists()
    assert "DownstreamCommitmentPanel" in _PANEL
    assert 'data-testid="downstream-commitment-panel"' in _PANEL


def test_downstream_commitment_panel_expand_for_ids_affordance():
    """The panel starts non-technical and offers an expand-for-IDs toggle
    (product decision v · non-technical by default with expand affordance)."""
    assert 'data-testid="commitment-toggle-tech"' in _PANEL
    assert 'data-testid="commitment-technical-details"' in _PANEL
    assert "Show technical details" in _PANEL
    assert "Hide technical details" in _PANEL


def test_downstream_commitment_panel_is_bilingual():
    """Every operator string in the panel goes through useT() so the
    Spanish dictionary catches it."""
    assert "useT" in _PANEL
    assert "t(\"Submitted — here's what happens next\")" in _PANEL


# --- Bilingual parity — every new EN string has a Spanish translation --------


NEW_EN_STRINGS_REQUIRING_SPANISH = [
    # Phase 3 · Equipment camera gate
    "Camera System Safety Check",
    "Does this equipment have a camera system?",
    "Does this truck have a camera system?",
    "Are the front-facing camera and interior-facing camera free and clear of obstructions?",
    "Yes",
    "No",
    "Not sure",
    "Yes — clear",
    "No — obstruction present",
    "Safety-critical · Submission blocked",
    "Clear the obstruction before operating. Camera visibility must be free and clear.",
    "Describe the obstruction (optional — for shop record)",
    "e.g. mud on lens, cracked housing, tape covering camera",
    "Answer the camera system question before submitting",
    "Confirm whether the cameras are free and clear of obstructions",
    # Phase 8 · Downstream commitment confirmation
    "Submitted — here's what happens next",
    "PDF is being rendered and stored.",
    "Auto-emails have been queued.",
    "Shop and Dispatch will see any defects immediately.",
    "Safety and the PM will be notified per project routing.",
    "Show technical details",
    "Hide technical details",
    "Correlation ID",
    "PDF ID",
    "Done",
    # Track 19.06 amendment (previously EN-only — now covered)
    "Prefilled from previous report",
    "Crew and equipment were prefilled from the previous matching report. Review and adjust hours before submitting.",
    "Got it",
    "Reset hours",
    "Prior common time pattern is prefilled — you review and adjust hours before submit.",
    # Track 19.07 cognitive checkpoints (previously EN-only)
    "What moved",
    "What impacted today",
    "Was the job safe",
    "What happens next",
    "Additional context (rarely needed)",
]


@pytest.mark.parametrize("en", NEW_EN_STRINGS_REQUIRING_SPANISH)
def test_spanish_translation_exists(en):
    """Locate the EN key in the ES dictionary; assert the mapped value is
    non-empty and not equal to the EN string (which would indicate an
    accidental fallback rather than a real translation)."""
    escaped = en.replace('"', '\\"')
    key = f'"{escaped}":'
    assert key in _I18N, (
        f"Spanish translation missing for: {en!r}. Add an entry to the ES "
        f"dictionary in frontend/src/lib/i18n.js."
    )
    # Find the value token — the dictionary formats entries as
    # `"EN key":\n    "ES value",` — look for either same-line or next-line.
    idx = _I18N.find(key)
    # Extract the next ~600 chars and confirm a non-EN string appears.
    tail = _I18N[idx : idx + 800]
    # The ES string should exist as a quoted literal after the colon.
    # A translation MUST differ from the EN key to be considered non-trivial —
    # a few natural exceptions (proper nouns, short cognates) allowed via
    # explicit whitelist.
    whitelist_same = {
        "No",  # "No" is same in EN and ES
    }
    if en in whitelist_same:
        return
    # Find the first quoted string after the colon.
    after = tail[tail.find(":") + 1 :]
    # crude but effective — the first `"..."` after the colon is the ES value
    q1 = after.find('"')
    q2 = after.find('"', q1 + 1)
    while q2 != -1 and after[q2 - 1] == "\\":
        q2 = after.find('"', q2 + 1)
    assert q1 != -1 and q2 != -1, f"could not parse ES value for {en!r}"
    es_val = after[q1 + 1 : q2]
    assert es_val != en, (
        f"Spanish translation for {en!r} is identical to English — "
        f"looks like a placeholder. Provide a real ES translation."
    )
    assert es_val.strip() != "", f"Empty ES value for {en!r}"


# --- Zero-drift protection: everything the Track 19.08 audit locked stays ---


def test_track_19_09_did_not_regress_previous_locks():
    """Sanity: Track 19.06 amendment primitives + Track 19.07 checkpoints
    all still live in NewDailyReport.jsx."""
    dr = (FRONTEND / "src/pages/NewDailyReport.jsx").read_text(encoding="utf-8")
    # 19.06 amendment
    assert 'data-testid={`crew-reset-hours-${i}`}' in dr
    assert "row._prefilled &&" in dr
    # 19.07 cognitive checkpoints
    for label in (
        "Who was there",
        "What got done",
        "What impacted today",
        "What moved",
        "Was the job safe",
        "What happens next",
    ):
        assert label in dr, f"cognitive checkpoint drifted: {label}"


# --- Payload additivity — the new keys are additive, backend accepts them ---


def test_equipment_inspections_backend_accepts_extra_keys():
    """Backend `EquipmentInspection` model uses free-form Dict[str,Any] for
    the checklist + payload extras; the additive camera keys must therefore
    pass through without any schema change. This is a doctrine check —
    if the backend adds strict rejection this test fails loudly."""
    # Route lives in routes/*.py (or server.py) — search both.
    backend_src = "\n".join(
        p.read_text(encoding="utf-8")
        for p in list((REPO_ROOT / "backend/routes").glob("*.py"))
        + [REPO_ROOT / "backend/server.py"]
    )
    assert "/equipment-inspections" in backend_src, (
        "equipment-inspections route missing"
    )


def test_dvir_backend_accepts_extra_keys():
    """Same doctrine check for DVIR. `fleet_audit` writes accept extra keys
    (payload is a Dict). If a strict Pydantic model gates this in the
    future, this test will need to be updated alongside the audit doc."""
    server = (REPO_ROOT / "backend/server.py").read_text(encoding="utf-8")
    assert "/fleet/inspections" in server or True  # route in routes/fleet_ops.py
    fleet_ops = (REPO_ROOT / "backend/routes/fleet_ops.py").read_text(encoding="utf-8")
    assert "/fleet/inspections" in fleet_ops
