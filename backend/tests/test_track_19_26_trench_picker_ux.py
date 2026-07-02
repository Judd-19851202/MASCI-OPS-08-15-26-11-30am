"""Track 19.26 · Trench Safety Forensic UX Audit + Fix — lock tests.

Locks the field-UX fix: TrenchAssetPicker's results list now stays
collapsed until the operator focuses the search input or types, then
exposes a sticky "Done" affordance to dismiss on gloves-on iPad.

Zero drift: NO backend change, NO route change, NO payload change,
NO removal of any multi-select capability.
"""
from __future__ import annotations

from pathlib import Path


PICKER = Path("/app/frontend/src/components/trench/TrenchAssetPicker.jsx")
FORM = Path("/app/frontend/src/pages/trench_safety/PublicExcavationForm.jsx")


# ── Fix contract ────────────────────────────────────────────────────
def test_picker_defaults_to_collapsed():
    src = PICKER.read_text(encoding="utf-8")
    # A `useState(false)` open state must exist.
    assert "useState(false)" in src
    # Collapsed-hint button must be conditionally rendered.
    assert "show-registry" in src


def test_picker_opens_on_search_focus():
    src = PICKER.read_text(encoding="utf-8")
    assert "onFocus={() => setOpen(true)}" in src


def test_picker_has_done_button_to_dismiss():
    src = PICKER.read_text(encoding="utf-8")
    assert 'data-testid={`${testId}-done`}' in src
    assert 'onClick={() => setOpen(false)}' in src


def test_picker_lists_stay_capped_at_max_h_72():
    src = PICKER.read_text(encoding="utf-8")
    # Preserves the max-h-72 (288 px) cap when the list DOES open.
    assert "max-h-72" in src


def test_picker_click_outside_collapses_list():
    src = PICKER.read_text(encoding="utf-8")
    # Outside-click / touch listener must be present so the list
    # dismisses when the operator taps elsewhere on the form.
    assert 'document.addEventListener("mousedown"' in src
    assert 'document.addEventListener("touchstart"' in src


def test_picker_shows_selected_count_in_done_bar():
    src = PICKER.read_text(encoding="utf-8")
    assert 'selected-count' in src


# ── Zero-drift sentinels ────────────────────────────────────────────
def test_picker_still_forwards_all_data_testids():
    src = PICKER.read_text(encoding="utf-8")
    # Every existing test hook must survive (upstream regression protection).
    for tid_pattern in ("${testId}-selected", "${testId}-chip-${a.asset_id}",
                        "${testId}-chip-remove-${a.asset_id}", "${testId}-search",
                        "${testId}-list", "${testId}-row-${a.asset_id}"):
        assert tid_pattern in src, f"Missing test id pattern: {tid_pattern}"


def test_picker_still_calls_asset_roster_endpoint():
    src = PICKER.read_text(encoding="utf-8")
    # Do NOT change the backend contract for the roster.
    assert '"/trench-safety/excavations/public/asset-roster"' in src


def test_form_still_uses_the_picker_for_both_asset_and_road_plate_slots():
    src = FORM.read_text(encoding="utf-8")
    # Section 6 (assigned trench-safety assets)
    assert 'testId="exc-assets"' in src
    # Section 6b (road plates)
    assert 'testId="exc-road-plates"' in src
    assert 'assetType="Road Plate"' in src


def test_form_payload_keys_intact():
    src = FORM.read_text(encoding="utf-8")
    for key in ("assigned_asset_ids", "road_plate_ids",
                "rated_depth_acknowledged",
                "rated_depth_acknowledgement_reason",
                "rated_depth_tabulated_data_exception"):
        assert key in src, f"Payload key drift: {key}"
