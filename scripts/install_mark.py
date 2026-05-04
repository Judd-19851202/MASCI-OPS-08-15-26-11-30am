#!/usr/bin/env python3
"""
Regenerate ONLY the small in-UI brand mark (`/masci-mark.png` and
`/masci-mark-onlight.png`) with the new bold red M.

Used by `<MasciLogo variant="mark">` — appears in mobile page headers,
the Pre-Op critical-fluid block, login forms, etc. Per the user
2026-05-04: the full lockup (`/masci-full-lockup{,-onlight}.png`) stays
untouched.

Both outputs are square PNGs with a transparent background and ~8%
padding so the mark sits comfortably inside whatever container it lands
in. Same red as the source mark, no recoloring.
"""

from __future__ import annotations
from pathlib import Path
from PIL import Image

SRC = Path("/app/scripts/source/red_m_master.png")
OUT_DIR = Path("/app/frontend/public")
SIZE = 512  # plenty of headroom; CSS scales it down
PADDING = 0.08   # 8% padding per side


def _load_red_m() -> Image.Image:
    """Black → transparent + trim-to-bbox."""
    im = Image.open(SRC).convert("RGBA")
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, _ = px[x, y]
            if r < 60 and g < 60 and b < 60:
                px[x, y] = (0, 0, 0, 0)
    return im.crop(im.getbbox())


def _build(size: int) -> Image.Image:
    """Square transparent canvas with the red M centered + 8% padding."""
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    mark = _load_red_m()
    target = int(size * (1 - 2 * PADDING))
    mw, mh = mark.size
    scale = target / max(mw, mh)
    nw, nh = int(mw * scale), int(mh * scale)
    resized = mark.resize((nw, nh), Image.LANCZOS)
    pos = ((size - nw) // 2, (size - nh) // 2)
    canvas.alpha_composite(resized, dest=pos)
    return canvas


def main() -> None:
    img = _build(SIZE)
    # Both files are byte-identical: transparent background means a single
    # asset reads correctly on both light and dark UI backgrounds. Keep
    # both filenames so the existing MasciLogo SRC dict stays unchanged.
    for name in ("masci-mark.png", "masci-mark-onlight.png"):
        path = OUT_DIR / name
        img.save(path, "PNG", optimize=True)
        print(f"  wrote {path.name:30s} {SIZE}x{SIZE}  {path.stat().st_size} bytes")


if __name__ == "__main__":
    main()
