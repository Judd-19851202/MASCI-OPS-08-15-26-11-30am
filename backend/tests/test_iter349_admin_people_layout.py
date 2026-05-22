"""
test_iter349_admin_people_layout.py — Regression lock for the P0 layout
defect fixed in iter349.

Root cause was tables rendering with `w-full` and no `min-w-[...]` floor,
which caused cells to truncate AND propagated horizontal overflow to the
page <body> on narrow viewports. Fix: every wide table now carries an
explicit `min-w-[Npx]` so the existing `overflow-x-auto` wrapper actually
scrolls internally instead of blowing out the page.

This test asserts the structural fix is still in place. Live viewport
regression is exercised via the screenshot tool during merge.
"""
from pathlib import Path

ROOT = Path("/app")
FRONTEND = ROOT / "frontend/src"

# (file, expected_min_width_class)
WIDE_TABLE_PANELS = [
    ("components/AdminAccessControlPanel.jsx", "min-w-[1200px]"),
    ("components/AdminUnifiedDirectoryPanel.jsx", "min-w-[1100px]"),
    ("components/AdminFieldLeadershipUsersPanel.jsx", "min-w-[900px]"),
    ("components/AdminHRUsersPanel.jsx", "min-w-[900px]"),
    ("components/AdminSafetyUsersPanel.jsx", "min-w-[900px]"),
    ("components/AdminShopUsersPanel.jsx", "min-w-[900px]"),
    ("components/AdminDispatchUsersPanel.jsx", "min-w-[900px]"),
    ("components/AdminPMPanel.jsx", "min-w-[900px]"),
    ("components/MasterListPanel.jsx", "min-w-[900px]"),
]


def test_every_wide_admin_table_has_min_width_floor():
    """If a future edit ever drops the min-w-[...] class, the page-level
    overflow regression comes right back. This lock prevents that."""
    for rel, expected_class in WIDE_TABLE_PANELS:
        src = (FRONTEND / rel).read_text()
        assert expected_class in src, (
            f"{rel} missing required min-width floor `{expected_class}` — "
            "page-level horizontal overflow regression risk"
        )


def test_admin_shell_has_overflow_x_clip_safety_net():
    """Outermost AdminShell wrapper has `overflow-x-clip` so even if a
    future panel forgets a min-w, the page itself never grows wider than
    the viewport."""
    src = (FRONTEND / "components/AdminShell.jsx").read_text()
    assert "overflow-x-clip" in src, (
        "AdminShell missing overflow-x-clip safety net — a misbehaving "
        "child table could blow out the page body again"
    )


def test_master_list_panel_card_no_longer_overflow_hidden():
    """The Employee Roster card used to clip its right edge with
    overflow-hidden. After iter349 the card relies on inner-scroll
    affordances on the table wrapper instead."""
    src = (FRONTEND / "components/MasterListPanel.jsx").read_text()
    # The card wrapper line should NOT carry overflow-hidden any more.
    bad = 'border border-slate-200 rounded-md overflow-hidden shadow-sm'
    assert bad not in src, (
        "MasterListPanel card still has overflow-hidden — Employee Roster "
        "right-edge will clip again"
    )


def test_master_list_panel_inner_scroll_uses_overflow_auto():
    """The table wrapper switched from `overflow-x-auto` to `overflow-auto`
    so vertical scroll within the max-h-[460px] region works without
    fighting the page scroll."""
    src = (FRONTEND / "components/MasterListPanel.jsx").read_text()
    assert (
        'overflow-auto border-2 border-slate-200 rounded max-h-[460px]'
        in src
    ), "MasterListPanel inner scroll wrapper must use overflow-auto + max-h"
