"""TRACK 14.0-S2 · iPad Field Certification — CSS contract regression.

Verifies that the `index.css` field-mode rules and the shadcn primitive
contracts remain in place. These guarantees are the architectural floor
that prevents iPad field users from getting stuck on 36px buttons,
12px text, or 4:1-contrast slate-300 / slate-400 on white.

Run:
    cd /app/backend && python -m pytest tests/test_track14_s2_field_mode_css.py -v
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
INDEX_CSS = Path("/app/frontend/src/index.css")
BUTTON_JSX = Path("/app/frontend/src/components/ui/button.jsx")
INPUT_JSX = Path("/app/frontend/src/components/ui/input.jsx")
TEXTAREA_JSX = Path("/app/frontend/src/components/ui/textarea.jsx")


@pytest.fixture(scope="module")
def index_css() -> str:
    return INDEX_CSS.read_text(encoding="utf-8")


def test_field_tap_target_min_is_44px(index_css):
    """The CSS variable that drives every floor must be 44px."""
    assert "--field-tap-min: 44px" in index_css


def test_field_input_floor_is_16px(index_css):
    """iOS zoom-on-focus is defeated only when inputs are ≥16px."""
    assert "--field-input-min: 16px" in index_css


def test_coarse_pointer_media_query_present(index_css):
    """The media query is THE mechanism that protects iPad without
    breaking desktop layouts. If it disappears, the floor is gone."""
    assert "@media (pointer: coarse)" in index_css


def test_button_role_has_44px_floor(index_css):
    """Every button and role=button gets the 44px floor inside the
    coarse-pointer block."""
    coarse_block_match = re.search(
        r"@media \(pointer: coarse\) \{(.*?)\n\}\s*\n\s*/\* ─",
        index_css,
        flags=re.DOTALL,
    )
    assert coarse_block_match, "coarse-pointer block missing"
    block = coarse_block_match.group(1)
    assert 'button:not([data-field-exempt])' in block
    assert '[role="button"]' in block
    assert "min-height: var(--field-tap-min)" in block


def test_contrast_hardening_present(index_css):
    """text-slate-300 and text-slate-400 must be lifted on touch."""
    assert ".text-slate-300:not(" in index_css
    assert ".text-slate-400:not(" in index_css
    assert "var(--field-text-muted)" in index_css


def test_text_xs_lifted_on_touch(index_css):
    """12px (text-xs) is too small for an outdoor read. The floor
    must lift to ≈13.5px on coarse pointers."""
    assert ".text-xs:not(.text-xs-allow)" in index_css


def test_glance_anchor_helper_present(index_css):
    """Phase 2A · Glance Test helper must be available for adoption."""
    assert ".field-glance-anchor" in index_css


def test_busy_shimmer_helper_present(index_css):
    """Phase 6A · Speed Perception helper must be available."""
    assert ".field-busy" in index_css
    assert "field-busy-shimmer" in index_css


def test_portrait_grid_collapse_present(index_css):
    """Phase 7 · iPad portrait must collapse 3+ column grids."""
    assert "@media (pointer: coarse) and (max-width: 900px)" in index_css


# ── Shadcn primitive contracts ───────────────────────────────────


def test_button_default_size_unchanged_for_desktop():
    """Desktop visual scale preserved. CSS layer raises iPad to 44px."""
    src = BUTTON_JSX.read_text(encoding="utf-8")
    assert 'default: "h-9 px-4 py-2"' in src, (
        "shadcn Button default size should remain h-9 — desktop unchanged. "
        "iPad floor is enforced by the index.css coarse-pointer media query."
    )


def test_input_md_text_sm_removed():
    """`md:text-sm` shrinks the input font to 14px on iPad — REMOVED."""
    src = INPUT_JSX.read_text(encoding="utf-8")
    # Strip JS comments so any documentation about md:text-sm doesn't
    # count as live className content.
    stripped = re.sub(r"//[^\n]*\n", "\n", src)
    stripped = re.sub(r"/\*.*?\*/", "", stripped, flags=re.DOTALL)
    assert "md:text-sm" not in stripped, (
        "Input className still contains md:text-sm. This shrinks input "
        "font to 14px on iPad which triggers iOS focus-zoom — REMOVE it."
    )


def test_textarea_md_text_sm_removed():
    """Same defense for <Textarea>."""
    src = TEXTAREA_JSX.read_text(encoding="utf-8")
    stripped = re.sub(r"//[^\n]*\n", "\n", src)
    stripped = re.sub(r"/\*.*?\*/", "", stripped, flags=re.DOTALL)
    assert "md:text-sm" not in stripped


def test_input_size_default_remains_h9():
    """Desktop input height unchanged."""
    src = INPUT_JSX.read_text(encoding="utf-8")
    assert "h-9" in src, "Input lost its h-9 default"


# ── Cascade-defense audit (iteration_514 finding) ────────────────


def test_no_arbitrary_min_h_under_44px_in_components():
    """Ban Tailwind arbitrary `min-h-[Xpx]` classes below 44px in
    src/components AND src/pages. These win cascade specificity over
    the global coarse-pointer rule and recreate the LangToggle-class
    defect surfaced in iteration_514. Allowed exceptions: progress
    bars, skeleton placeholders (non-tap surfaces), and explicitly
    annotated `data-field-exempt` elements (caller assumes
    responsibility).
    """
    src_root = Path("/app/frontend/src")
    rx = re.compile(r"min-h-\[(\d+)px\]")
    offenders: list[tuple[str, int, str]] = []
    for base in ("components", "pages"):
        for p in (src_root / base).rglob("*.jsx"):
            text = p.read_text(encoding="utf-8")
            for m in rx.finditer(text):
                px = int(m.group(1))
                if px >= 44:
                    continue
                line_no = text.count("\n", 0, m.start()) + 1
                line = text.split("\n")[line_no - 1].strip()
                if any(
                    hint in line.lower()
                    for hint in ("progress", "skeleton", "data-field-exempt")
                ):
                    continue
                offenders.append((str(p.relative_to(src_root.parent)), line_no, line[:120]))
    assert not offenders, (
        "Tailwind arbitrary min-h classes below 44px found — these defeat "
        "the iPad field-mode floor. Bump them to min-h-[44px] or mark the "
        "element data-field-exempt with a comment justifying:\n"
        + "\n".join(f"  · {f}:{ln}  {snip}" for f, ln, snip in offenders)
    )
