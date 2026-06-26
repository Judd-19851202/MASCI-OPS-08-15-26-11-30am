"""TRACK 15.82B · Dispatch Landing Page + Roll-Off Action Button.

Closes the visible-UI gap left by Track 15.82: Roll-Off was added to the
backend taxonomy, normalizer, map family classification, and marker
sprite logic, but the Dispatch Portal landing page Primary Actions card
still rendered only 4 buttons (Material · Equipment Move · Tanker ·
Support / Misc). Dispatchers had no visible way to issue a Roll-Off.

Track 15.82B
  * Adds ``Roll-Off`` to ``HAUL_TYPES`` in
    ``backend/dispatch_assignment_seeds.py`` so the assignment lookups
    endpoint exposes it.
  * Adds the daily ``haul_counts`` slot for ``Roll-Off`` in
    ``routes/dispatch_lifecycle.py`` so the dashboard counts Roll-Off
    volume as a first-class haul type.
  * Adds the 5th Issue Work tile on ``DispatchHub.jsx`` with the
    canonical label/sublabel/icon/testid expected by browser tests.
  * Updates ``AssignmentCreateDrawer.jsx`` so the drawer icon mapping
    + the fallback lookups list both recognize ``Roll-Off``.

Hard rules enforced:
  * Existing four actions remain present and wired to the same
    issueWork(...) calls.
  * Roll-Off is NOT buried under Support / Misc.
  * No Admin RBAC weakening.
"""
from __future__ import annotations

import re
from pathlib import Path


FRONTEND_SRC = Path("/app/frontend/src")
DISPATCH_HUB = FRONTEND_SRC / "pages/DispatchHub.jsx"
ASSIGNMENT_DRAWER = FRONTEND_SRC / "components/dispatch/AssignmentCreateDrawer.jsx"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ─── Backend · haul-type list / lookups / daily counts ─────────────


def test_haul_types_includes_roll_off():
    from dispatch_assignment_seeds import HAUL_TYPES
    assert "Roll-Off" in HAUL_TYPES, (
        f"Track 15.82B: HAUL_TYPES must include 'Roll-Off'. Got: {HAUL_TYPES}"
    )


def test_haul_types_preserves_existing_entries():
    """Existing dispatch haul types must remain present after Track 15.82B."""
    from dispatch_assignment_seeds import HAUL_TYPES
    for required in [
        "Material", "Equipment Move", "Tanker / Liquid Asphalt",
        "Spoils / Dump", "Support / Misc",
    ]:
        assert required in HAUL_TYPES, (
            f"Track 15.82B regression: '{required}' must remain in "
            f"HAUL_TYPES. Got: {HAUL_TYPES}"
        )


def test_dispatch_daily_haul_counts_seeds_roll_off_slot():
    """The today-volume rollup in dispatch_lifecycle.py declares a
    Roll-Off slot so the dashboard renders the value (zero-state still
    counted) without an extra branch."""
    src = (Path("/app/backend/routes/dispatch_lifecycle.py")
           .read_text(encoding="utf-8"))
    assert '"Roll-Off": 0' in src, (
        "Track 15.82B regression: dispatch_lifecycle.py haul_counts "
        "default must include the 'Roll-Off' slot."
    )


# ─── Frontend · Dispatch Hub Issue Work tiles ──────────────────────


def test_dispatch_hub_renders_roll_off_action_button():
    src = _read(DISPATCH_HUB)
    # Canonical testid for browser automation.
    assert 'testId="ds-issue-roll-off"' in src, (
        "Track 15.82B regression: DispatchHub must expose the Roll-Off "
        "Issue Work tile with testid `ds-issue-roll-off`."
    )
    # Click handler must issue work as 'Roll-Off' (matches HAUL_TYPES).
    assert 'issueWork("Roll-Off")' in src, (
        "Track 15.82B regression: DispatchHub Roll-Off tile must call "
        "issueWork(\"Roll-Off\") so the assignment drawer preselects the "
        "Roll-Off haul type."
    )
    # Visible label + sublabel.
    assert 't("Roll-Off Truck")' in src, (
        "Track 15.82B regression: Roll-Off tile title must read "
        "'Roll-Off Truck'."
    )
    assert 't("Container · Roll-Off · Haul")' in src, (
        "Track 15.82B regression: Roll-Off tile sublabel must read "
        "'Container · Roll-Off · Haul'."
    )
    # Container icon must be imported so the tile renders the right glyph.
    assert "Container," in src or "Container }" in src, (
        "Track 15.82B regression: Container icon must be imported on "
        "DispatchHub.jsx (lucide-react)."
    )


def test_dispatch_hub_issue_grid_widens_for_five_actions():
    src = _read(DISPATCH_HUB)
    assert "lg:grid-cols-5" in src, (
        "Track 15.82B regression: the Issue Work grid must widen to 5 "
        "columns on large screens so the new Roll-Off tile does not "
        "wrap awkwardly next to the existing four."
    )


def test_dispatch_hub_preserves_existing_actions():
    """All four pre-15.82B Issue Work tiles must remain."""
    src = _read(DISPATCH_HUB)
    for required_testid in (
        "ds-issue-material",
        "ds-issue-equipment-move",
        "ds-issue-tanker",
        "ds-issue-support",
    ):
        pattern = re.compile(rf'testId="{re.escape(required_testid)}"')
        assert pattern.search(src), (
            f"Track 15.82B regression: existing Issue Work tile "
            f"`{required_testid}` was removed."
        )
    # And the corresponding issueWork calls remain wired.
    for required_call in (
        'issueWork("Material")',
        'issueWork("Equipment Move")',
        'issueWork("Tanker / Liquid Asphalt")',
        'issueWork("Support / Misc")',
    ):
        assert required_call in src, (
            f"Track 15.82B regression: `{required_call}` is no longer "
            f"wired on a Dispatch Hub tile."
        )


# ─── Frontend · Assignment drawer wiring ───────────────────────────


def test_assignment_drawer_haul_type_picker_handles_roll_off():
    src = _read(ASSIGNMENT_DRAWER)
    assert 'h === "Roll-Off"' in src, (
        "Track 15.82B regression: HaulTypePicker.iconFor must branch on "
        "'Roll-Off' so the drawer renders the Container icon."
    )
    # Fallback list (when /api/dispatch/driver/assignment-lookups
    # returns no haul_types) must still surface Roll-Off so the picker
    # can preselect it.
    assert '"Roll-Off"' in src, (
        "Track 15.82B regression: AssignmentCreateDrawer fallback "
        "haul_types must include 'Roll-Off'."
    )
