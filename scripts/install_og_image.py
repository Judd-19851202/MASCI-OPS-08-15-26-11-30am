#!/usr/bin/env python3
"""
Generate the Open Graph + Twitter card image for MASCI Hub.

Per user 2026-05-04: STRIP the card down to JUST the new red M on the
slate-900 brand background. No wordmark, no tagline, no subtitle, no
bottom rule. Clean, centered, single subject.

A single image (1200×630) is published — link previews on Slack, iMessage,
WhatsApp, LinkedIn, Twitter, etc. all accept the 1.91:1 landscape ratio.
The square variant is dropped to avoid iMessage stacking two previews on
top of each other.

Output:
    /app/frontend/public/og-image.png   (1200×630)
"""

from __future__ import annotations
from pathlib import Path
from PIL import Image

SRC_M = Path("/app/assets/source/red_m_master.png")
OUT_DIR = Path("/app/frontend/public")
DARK_BG = (15, 23, 42)   # slate-900 — matches index.html theme_color

# How much of the canvas height the M occupies. 0.62 leaves a clean
# breathing border (~19% top + bottom margin) so the M is unmistakably
# the focus and never crops into the link-preview UI chrome.
M_FILL_RATIO = 0.62


def _load_red_m() -> Image.Image:
    """Black → transparent + trim-to-bbox. Same pipeline as install_icons.py."""
    im = Image.open(SRC_M).convert("RGBA")
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, _ = px[x, y]
            if r < 60 and g < 60 and b < 60:
                px[x, y] = (0, 0, 0, 0)
    return im.crop(im.getbbox())


def _build_card(width: int, height: int) -> Image.Image:
    img = Image.new("RGB", (width, height), DARK_BG)
    mark = _load_red_m()
    target = int(height * M_FILL_RATIO)
    mw, mh = mark.size
    scale = target / max(mw, mh)
    new_w, new_h = int(mw * scale), int(mh * scale)
    resized = mark.resize((new_w, new_h), Image.LANCZOS)
    pos = ((width - new_w) // 2, (height - new_h) // 2)
    img.paste(resized, pos, resized)
    return img


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    landscape = _build_card(1200, 630)
    p1 = OUT_DIR / "og-image.png"
    landscape.save(p1, "PNG", optimize=True)
    print(f"  wrote {p1.name:25s} 1200x630   {p1.stat().st_size} bytes")

    # Remove the square variant if it exists from the previous run — having
    # two og:image declarations causes iMessage to stack both previews.
    sq = OUT_DIR / "og-image-square.png"
    if sq.exists():
        sq.unlink()
        print(f"  removed {sq.name} (single og:image policy)")


if __name__ == "__main__":
    main()
