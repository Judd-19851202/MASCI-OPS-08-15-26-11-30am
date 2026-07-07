"""TRACK 24.6 · JobPicker touch-select regression lock.

Guards the fix for the iOS Safari + cmdk selection race where tapping
a highlighted row failed to commit because the CommandInput blur closed
the popover before the click event landed on the CommandItem.

Contract:
  * Every user-selectable CommandItem in JobPicker.jsx must have an
    `onPointerDown` handler that commits the selection for non-mouse
    pointers, in addition to the standard cmdk `onSelect` for
    keyboard + desktop-click parity.

Failure of this test = mobile users cannot select a job on the live
Daily Report. Production blocker.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

JOB_PICKER = Path("/app/frontend/src/components/JobPicker.jsx")


def _extract_command_items(src: str):
    """Return every ``<CommandItem ...>...</CommandItem>`` block."""
    # Non-greedy so nested JSX doesn't confuse us — cmdk items in this
    # file don't nest other CommandItems.
    return re.findall(r"<CommandItem\b[^>]*?(?:/>|>.*?</CommandItem>)",
                      src, flags=re.DOTALL)


def test_job_picker_command_items_commit_on_pointerdown():
    src = JOB_PICKER.read_text(encoding="utf-8")
    items = _extract_command_items(src)
    assert items, "JobPicker.jsx does not contain any <CommandItem> — refactor detected. This test needs updating."
    for i, block in enumerate(items):
        assert "onPointerDown" in block, (
            f"[Track 24.6] JobPicker CommandItem #{i+1} is missing "
            f"`onPointerDown` — iOS Safari tap-to-select will regress "
            f"and mobile users will not be able to pick a job. Block:\n"
            f"{block[:300]}"
        )
        # Sanity-check the pointer-type guard is present so we don't
        # double-fire on desktop mouse (which already works via
        # onSelect click).
        assert 'pointerType' in block, (
            f"[Track 24.6] JobPicker CommandItem #{i+1} onPointerDown "
            f"handler is missing a pointerType guard — desktop mouse "
            f"clicks will double-fire selection."
        )
        # Selection commit must be inside the handler.
        assert 'onSelect(' in block, (
            f"[Track 24.6] JobPicker CommandItem #{i+1} does not appear "
            f"to invoke onSelect() — selection cannot commit."
        )


def test_job_picker_keeps_onSelect_for_keyboard_parity():
    """cmdk keyboard-Enter path still works via onSelect."""
    src = JOB_PICKER.read_text(encoding="utf-8")
    items = _extract_command_items(src)
    for i, block in enumerate(items):
        assert re.search(r"\bonSelect=\{", block), (
            f"[Track 24.6] JobPicker CommandItem #{i+1} dropped "
            f"onSelect — keyboard Enter navigation will regress."
        )


def test_job_picker_consumers_use_correct_prop_contract():
    """Every JobPicker consumer must wire the props JobPicker actually
    reads (`onSelect`, `projectNumber`, optionally `projectName`).

    Track 24.3 accidentally rewrote SectionProjectConditions.jsx to
    pass `value` / `onChange` — a silent contract break that made
    every selection commit throw `onSelect is not a function` on
    desktop, mobile, and keyboard alike. This lock keeps it from
    happening again.
    """
    consumers = list(Path("/app/frontend/src").rglob("*.jsx"))
    offenders = []
    for path in consumers:
        if path.name == "JobPicker.jsx":
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        # Find JSX blocks that mount <JobPicker ...>
        for m in re.finditer(r"<JobPicker\b[^/>]*(?:/>|>[^<]*</JobPicker>)",
                             text, flags=re.DOTALL):
            block = m.group(0)
            # Must NOT use `value=` or `onChange=` on JobPicker.
            if re.search(r"\bvalue=\{", block) or re.search(r"\bonChange=\{", block):
                # Compute an approximate line for reporting.
                line = text[:m.start()].count("\n") + 1
                offenders.append((path, line, block[:180].replace("\n", " ")))
    if offenders:
        msg = "\n".join(f"  {p.relative_to('/app')}:{ln}  {b}" for p, ln, b in offenders)
        raise AssertionError(
            "[Track 24.6] JobPicker consumers using wrong prop contract "
            "(should use projectNumber/projectName/onSelect, NOT "
            "value/onChange):\n" + msg
        )
