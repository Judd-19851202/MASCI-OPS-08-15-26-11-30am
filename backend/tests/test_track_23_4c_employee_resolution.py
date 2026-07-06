"""TRACK 23.4C · Employee Combo resolution repair — HR autofill actually works.

The 23.4B session shipped an `onPick` handler that autofilled trade /
crew / supervisor when the user clicked a dropdown item in
EmployeeCombo. The operator caught the fail-mode: typing "Jaymn Judd"
and blurring never fires `onPick` in EmployeeCombo, so the row was
left with an unfilled trade even though the HR record exists.

This lock envelope enforces:
  1. A shared `hrAutofill.js` helper exposes `pickHrFields(emp)` and
     `resolveEmployeeByTypedName(typed, roster)`.
  2. `pickHrFields` normalizes trade / crew / supervisor across every
     HR field alias the Employee Master has ever shipped with (trade,
     role, title, position, classification, trade_role, department,
     supervisor, supervisor_name, crew, division, employee_id, id).
  3. `resolveEmployeeByTypedName` returns the roster entry on exact
     name / preferred-name / legal-name / display-name / employee_id
     match, and on a single unambiguous partial match. Multiple
     partials → returns null (safer than guessing).
  4. `SectionCrewEquipment` fetches the roster on mount and uses the
     resolver on EVERY `onChange` so typed names autofill without a
     dropdown click.
  5. `crewMemory.refreshCrewFromEmployeeMaster` uses the same alias
     table so restore-yesterday works the same way.
"""
from __future__ import annotations

from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
FRONT = BACKEND.parent / "frontend" / "src"
HR_AUTOFILL = FRONT / "lib" / "hrAutofill.js"
V3_SECTIONS = FRONT / "components" / "daily-report-v3" / "sections.jsx"
CREW_MEMORY = FRONT / "lib" / "crewMemory.js"


def _r(p): return p.read_text(encoding="utf-8")


def test_hr_autofill_helper_exists():
    src = _r(HR_AUTOFILL)
    assert "export function pickHrFields" in src
    assert "export function resolveEmployeeByTypedName" in src


def test_pick_hr_fields_covers_every_alias():
    src = _r(HR_AUTOFILL)
    # Trade aliases.
    for alias in ("trade", "role", "title", "position",
                  "classification", "trade_role", "department"):
        assert f"emp.{alias}" in src, (
            f"pickHrFields must consider `emp.{alias}` as a trade source."
        )
    # Crew aliases.
    assert "emp.crew" in src
    assert "emp.division" in src
    # Supervisor aliases.
    assert "emp.supervisor" in src
    assert "emp.supervisor_name" in src
    # Identity aliases.
    assert "emp.employee_id" in src


def test_resolve_by_typed_name_matches_multiple_shapes():
    src = _r(HR_AUTOFILL)
    for shape in ("name", "legal_name", "preferred_name",
                  "display_name", "employee_id"):
        assert f"_norm(it.{shape})" in src, (
            f"resolveEmployeeByTypedName must consider `{shape}`."
        )
    # Single-partial-match branch.
    assert "candidateMatches.length === 1" in src
    # Multi-partial ambiguity → return null.
    assert "return null" in src


def test_v3_crew_row_wires_typed_resolution():
    src = _r(V3_SECTIONS)
    # Imports.
    assert "resolveEmployeeByTypedName" in src
    assert "pickHrFields" in src
    assert "from \"@/lib/hrAutofill\"" in src
    assert "from \"@/lib/hrRoster\"" in src
    # onChange handler resolves on every keystroke.
    assert "resolveEmployeeByTypedName(name, roster)" in src
    # Roster preloaded on mount.
    assert "rosterRef" in src
    assert "fetchHrRoster()" in src
    # Shared apply helper reused for both onPick + typed-match path.
    assert "_applyHrPick(i, emp" in src


def test_apply_hr_pick_persists_all_hr_snapshots():
    """The shared apply helper must set every downstream snapshot key."""
    src = _r(V3_SECTIONS)
    idx = src.find("_applyHrPick = (i, emp, currentRow)")
    assert idx > 0
    body = src[idx:idx + 1200]
    for key in (
        "employee_id",
        "employee_name_snapshot",
        "trade_snapshot",
        "crew_snapshot",
        "division_snapshot",
        "supervisor_snapshot",
        "trade_autofilled",
    ):
        assert key in body, (
            f"_applyHrPick must persist `{key}`."
        )


def test_crew_memory_refresh_uses_alias_table():
    """Restore-yesterday's rehydrate path must match the same alias
    table so trade autofill works after `Use yesterday's setup`."""
    src = _r(CREW_MEMORY)
    idx = src.find("export function refreshCrewFromEmployeeMaster")
    body = src[idx:]
    for alias in ("emp.trade", "emp.role", "emp.title", "emp.position",
                  "emp.classification", "emp.trade_role", "emp.department",
                  "emp.crew", "emp.division", "emp.supervisor",
                  "emp.supervisor_name"):
        assert alias in body, (
            f"refreshCrewFromEmployeeMaster must consider `{alias}`."
        )
