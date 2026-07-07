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
    """Every CommandItem must wire the shared touch handlers via
    commitHandlersFor(...) so scroll gestures do not commit
    selections. Track 24.8 replaced the naive Track 24.6 onPointerDown
    with a movement-threshold + pointerup pattern."""
    src = JOB_PICKER.read_text(encoding="utf-8")
    items = _extract_command_items(src)
    assert items, "JobPicker.jsx does not contain any <CommandItem> — refactor detected. This test needs updating."
    for i, block in enumerate(items):
        assert "commitHandlersFor(" in block, (
            f"[Track 24.8] JobPicker CommandItem #{i+1} is not using "
            f"the shared commitHandlersFor(...) touch handlers — "
            f"scroll gestures may incorrectly commit selections on "
            f"iOS. Block:\n{block[:300]}"
        )
        # Sanity-check onSelect is preserved for keyboard/desktop.
        assert 'onSelect(' in block, (
            f"[Track 24.8] JobPicker CommandItem #{i+1} does not "
            f"appear to invoke onSelect() — keyboard/desktop path broken."
        )


def test_job_picker_uses_movement_threshold_touch_pattern():
    """The JobPicker module must consume the Track 24.9 shared
    touch-guard hook (which contains the Track 24.8 scroll-cancel
    logic). The hook itself must contain the movement threshold,
    pointerup path, scroll-cancel ref, and cmdk-list attachment."""
    src = JOB_PICKER.read_text(encoding="utf-8")
    # JobPicker imports & consumes the hook.
    for marker in ["useCmdkTouchGuard", "commitHandlersFor"]:
        assert marker in src, (
            f"[Track 24.9] JobPicker.jsx missing `{marker}` — the "
            f"shared cmdk touch-guard hook is not wired. Users on "
            f"iOS will commit the row their finger first touched "
            f"when scrolling."
        )
    # Hook itself implements the full scroll-vs-tap disambiguation.
    hook_src = Path("/app/frontend/src/lib/useCmdkTouchGuard.js").read_text(encoding="utf-8")
    for marker in [
        "TOUCH_MOVE_CANCEL_PX",
        "onPointerUp",
        "scrolledRef",
        "cmdk-list",
    ]:
        assert marker in hook_src, (
            f"[Track 24.9] useCmdkTouchGuard.js missing `{marker}` — "
            f"the scroll-vs-tap disambiguation is not in place."
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
