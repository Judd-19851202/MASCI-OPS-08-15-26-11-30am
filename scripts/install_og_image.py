#!/usr/bin/env python3
"""
Generate the Open Graph + Twitter card image for MASCI Hub.

Layout (1200×630, brand colors):
    [ slate-900 background ]
    [ red M mark on the left | wordmark + tagline on the right ]
    [ red 4px bottom rule    ]

Produces:
    /app/frontend/public/og-image.png        (1200×630, ~PNG ≤ 200 KB)
    /app/frontend/public/og-image-square.png (1200×1200, for iMessage / WhatsApp
                                              which prefer square previews)
"""

from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

SRC_M = Path("/app/scripts/source/red_m_master.png")
OUT_DIR = Path("/app/frontend/public")
DARK_BG = (15, 23, 42)   # slate-900
RED = (196, 1, 13)       # MASCI red (sampled from new mark)
WHITE = (255, 255, 255)
MUTED = (148, 163, 184)  # slate-400

FONT_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"


def _load_red_m() -> Image.Image:
    """Same red-M extraction as install_icons.py (black → transparent, trim)."""
    im = Image.open(SRC_M).convert("RGBA")
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, _ = px[x, y]
            if r < 60 and g < 60 and b < 60:
                px[x, y] = (0, 0, 0, 0)
    return im.crop(im.getbbox())


def _build_card(width: int, height: int, square: bool) -> Image.Image:
    img = Image.new("RGB", (width, height), DARK_BG)
    draw = ImageDraw.Draw(img)
    mark = _load_red_m()

    # Left-side red M.
    if square:
        # Centered top, smaller text underneath
        m_target = int(height * 0.42)
        scale = m_target / max(mark.size)
        nw, nh = int(mark.size[0] * scale), int(mark.size[1] * scale)
        m_resized = mark.resize((nw, nh), Image.LANCZOS)
        m_x = (width - nw) // 2
        m_y = int(height * 0.10)
        img.paste(m_resized, (m_x, m_y), m_resized)
        text_anchor_y = m_y + nh + int(height * 0.06)
        text_align_x = width // 2
        align = "center"
    else:
        # Side-by-side: M on left, text right of it
        m_target = int(height * 0.55)
        scale = m_target / max(mark.size)
        nw, nh = int(mark.size[0] * scale), int(mark.size[1] * scale)
        m_resized = mark.resize((nw, nh), Image.LANCZOS)
        m_x = int(width * 0.06)
        m_y = (height - nh) // 2
        img.paste(m_resized, (m_x, m_y), m_resized)
        text_anchor_y = int(height * 0.32)
        text_align_x = m_x + nw + int(width * 0.04)
        align = "left"

    # Wordmark
    wordmark_size = int(height * 0.16) if not square else int(height * 0.10)
    wordmark = ImageFont.truetype(FONT_BOLD, wordmark_size)
    draw.text(
        (text_align_x, text_anchor_y),
        "MASCI HUB",
        fill=WHITE,
        font=wordmark,
        anchor="lt" if align == "left" else "mt",
    )

    # Tagline (red, bold)
    tag_size = int(height * 0.040) if not square else int(height * 0.030)
    tag_font = ImageFont.truetype(FONT_BOLD, tag_size)
    tag_y = text_anchor_y + wordmark_size + int(height * 0.04)
    draw.text(
        (text_align_x, tag_y),
        "NO GUESSWORK · NO MISSED STEPS · NO EXCUSES",
        fill=RED,
        font=tag_font,
        anchor="lt" if align == "left" else "mt",
    )

    # Subtitle
    sub_size = int(height * 0.045) if not square else int(height * 0.032)
    sub_font = ImageFont.truetype(FONT_REG, sub_size)
    sub_y = tag_y + tag_size + int(height * 0.03)
    draw.text(
        (text_align_x, sub_y),
        "Safety · Field · Projects · Admin",
        fill=MUTED,
        font=sub_font,
        anchor="lt" if align == "left" else "mt",
    )

    # Bottom 4px red rule (full-bleed accent)
    draw.rectangle([0, height - 4, width, height], fill=RED)

    return img


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    landscape = _build_card(1200, 630, square=False)
    p1 = OUT_DIR / "og-image.png"
    landscape.save(p1, "PNG", optimize=True)
    print(f"  wrote {p1.name:25s} 1200x630   {p1.stat().st_size} bytes")

    square = _build_card(1200, 1200, square=True)
    p2 = OUT_DIR / "og-image-square.png"
    square.save(p2, "PNG", optimize=True)
    print(f"  wrote {p2.name:25s} 1200x1200  {p2.stat().st_size} bytes")


if __name__ == "__main__":
    main()
