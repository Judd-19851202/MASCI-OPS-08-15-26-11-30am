"""TRACK 28.05F · Regression lock — ShopManagerQueue mobile responsiveness.

Original defect (28-05-DW-001): horizontal overflow at mobile 390×844.

Root cause: `gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))"`
forced every card to be ≥ 360px wide. On 390px viewport, once the
platform shell + SideNavV3 rail consume their space, the card
grid overflows.

Fix (2026-07-11):
  * grid: `minmax(min(100%, 340px), 1fr)` — collapses to full width
    on narrow viewports.
  * ShopUserPicker: `minWidth: 0, maxWidth: 260, flex: "1 1 180px"`
    — collapses on mobile, expands to 260 on desktop.
  * AssignBar + review action row: `flexWrap: "wrap"` so buttons
    reflow instead of overflowing.
  * DefectRow header: `flexWrap: "wrap"` + `wordBreak: "break-word"`
    so long unit numbers / descriptions wrap.

This test asserts the fixed patterns remain in the source; it
prevents a silent regression if someone re-tightens the grid or
removes flex-wrap.
"""
from __future__ import annotations

from pathlib import Path

import pytest


COMPONENT = Path("/app/frontend/src/pages/shop/ShopManagerQueue.jsx")


@pytest.fixture(scope="module")
def source() -> str:
    assert COMPONENT.exists(), f"missing component: {COMPONENT}"
    return COMPONENT.read_text(encoding="utf-8")


def test_grid_collapses_on_narrow_viewport(source: str) -> None:
    """The card grid must not have a hard 360px minimum — it must
    use `min(100%, ...)` so a narrow viewport gets a single-column
    layout."""
    assert 'minmax(min(100%, 340px), 1fr)' in source, (
        "TRACK 28.05F regression: ShopManagerQueue card grid reverted "
        "to a hard-minimum column width. Restore "
        "`minmax(min(100%, 340px), 1fr)` so the grid collapses to full "
        "width on mobile viewports."
    )
    # Guard against re-introducing the buggy pattern
    assert 'minmax(360px' not in source, (
        "TRACK 28.05F regression: `minmax(360px, ...)` is the exact "
        "pattern that caused horizontal overflow at 390×844. Do not "
        "restore it."
    )


def test_shop_user_picker_collapses(source: str) -> None:
    """The mechanic picker must not have a hard `minWidth: 180` that
    forces horizontal overflow on mobile."""
    assert 'minWidth: 0, maxWidth: 260, flex: "1 1 180px"' in source, (
        "TRACK 28.05F regression: ShopUserPicker lost its collapsible "
        "sizing. Restore the responsive `minWidth: 0, maxWidth: 260, "
        "flex: \"1 1 180px\"` pattern."
    )
    # Guard against re-introducing the buggy pattern
    assert 'minWidth: 180 }}' not in source, (
        "TRACK 28.05F regression: `minWidth: 180` on the mechanic "
        "picker directly caused horizontal overflow at mobile widths."
    )


def test_assign_bar_wraps(source: str) -> None:
    """The AssignBar flex row (mechanic select + submit button) must
    wrap on narrow viewports."""
    # Search for the assign-bar container that includes flexWrap
    marker = 'manager-queue-assign-bar-${defect.id}'
    idx = source.find(marker)
    assert idx > 0, "ManagerQueue assign-bar test-id missing"
    window = source[idx: idx + 400]
    assert 'flexWrap' in window and 'wrap' in window, (
        "TRACK 28.05F regression: AssignBar must include "
        "`flexWrap: \"wrap\"` so the mechanic select + submit button "
        "reflow on mobile widths."
    )


def test_review_actions_wrap(source: str) -> None:
    """The review approve/reject/cancel button row must wrap on
    narrow viewports (3 buttons don't fit on mobile at 390px)."""
    marker = "manager-queue-review-approve-"
    idx = source.find(marker)
    assert idx > 0, "review-approve test-id missing"
    window = source[max(0, idx - 300): idx]
    assert 'flexWrap: "wrap"' in window, (
        "TRACK 28.05F regression: review action row must include "
        "`flexWrap: \"wrap\"` so approve/reject/cancel buttons reflow "
        "on mobile widths."
    )


def test_defect_row_header_wraps(source: str) -> None:
    """The DefectRow header (unit line + assign controls) must wrap
    and its text must break long words."""
    marker = "manager-queue-row-${defect.id}"
    idx = source.find(marker)
    assert idx > 0, "defect-row test-id missing"
    window = source[idx: idx + 400]
    assert 'flexWrap: "wrap"' in window, (
        "TRACK 28.05F regression: DefectRow header flex row must "
        "wrap on mobile widths."
    )
    assert 'wordBreak: "break-word"' in window, (
        "TRACK 28.05F regression: DefectRow body text must wrap long "
        "words (unit numbers, descriptions) to prevent horizontal "
        "overflow."
    )
