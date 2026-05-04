#!/usr/bin/env python3
"""
Regenerate browser / mobile icons from the new red-M artwork.

This script ONLY touches OS-level icon files. The full MASCI Hub
lockup, the MasciLogo component, masci-mark.png used in UI headers,
and all PDF logos are left untouched per the user's rule:

    "We are ONLY updating ICON USAGE."

Inputs:
    /app/scripts/source/red_m_master.png  — supplied 1254×1254 red M on black

Outputs (regenerated in /app/frontend/public):
    favicon.ico                 — multi-size 16/32/48/64
    favicon-16.png, favicon-32.png, favicon-48.png, favicon-64.png
    apple-touch-icon.png        (180×180)
    apple-touch-icon-120.png
    apple-touch-icon-152.png
    apple-touch-icon-167.png
    icon-192.png                (Android any)
    icon-512.png                (PWA high-res)
    icon-maskable-192.png       (Android maskable, ≥40% safe-zone padding)
    icon-maskable-512.png

    +light/-dark variants:
    favicon-light-16.png …       (red M on white — for prefers-color-scheme: dark
                                   browsers where the dark-bg variant disappears)
    apple-touch-icon-light.png   (180)
"""

from __future__ import annotations
from pathlib import Path
from PIL import Image

SRC = Path("/app/scripts/source/red_m_master.png")
OUT = Path("/app/frontend/public")

# Brand colours
DARK_BG = (15, 23, 42, 255)    # slate-900 — matches theme_color in manifest
LIGHT_BG = (255, 255, 255, 255)

# Padding ratio: how much of the canvas the M should occupy.
PADDING_RATIO_STANDARD = 0.78   # M fills 78% of the icon, 11% margin on each side
PADDING_RATIO_MASKABLE = 0.58   # ≥40% safe-zone for Android maskable


def isolate_red_m(src_path: Path) -> Image.Image:
    """Open source red-M-on-black image, replace the black background
    with transparency, then trim the result to its visible bounding box.
    Returns an RGBA PIL.Image of just the red M with no surrounding canvas."""
    im = Image.open(src_path).convert("RGBA")
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, _a = px[x, y]
            # Anything close to pure black → transparent. Red pixels stay.
            if r < 60 and g < 60 and b < 60:
                px[x, y] = (0, 0, 0, 0)
    return im.crop(im.getbbox())


def composite(mark: Image.Image, size: int, bg_rgba: tuple, fill_ratio: float) -> Image.Image:
    """Place the trimmed red-M mark centered on a `size`×`size` canvas
    of solid `bg_rgba`, occupying `fill_ratio` of the smaller dimension."""
    canvas = Image.new("RGBA", (size, size), bg_rgba)
    target = int(size * fill_ratio)
    # Letter shape is roughly square (slightly wider than tall in this art).
    mw, mh = mark.size
    scale = target / max(mw, mh)
    new_w, new_h = max(1, int(mw * scale)), max(1, int(mh * scale))
    resized = mark.resize((new_w, new_h), Image.LANCZOS)
    pos = ((size - new_w) // 2, (size - new_h) // 2)
    canvas.alpha_composite(resized, dest=pos)
    return canvas


def main() -> None:
    print(f"Loading source: {SRC} ({SRC.stat().st_size} bytes)")
    mark = isolate_red_m(SRC)
    print(f"Trimmed mark size: {mark.size}")

    OUT.mkdir(parents=True, exist_ok=True)

    # Build pairs of (filename, size, bg, fill_ratio)
    plan = [
        # Standard icons → DARK variant (red M on slate-900)
        ("favicon-16.png",            16,  DARK_BG, PADDING_RATIO_STANDARD),
        ("favicon-32.png",            32,  DARK_BG, PADDING_RATIO_STANDARD),
        ("favicon-48.png",            48,  DARK_BG, PADDING_RATIO_STANDARD),
        ("favicon-64.png",            64,  DARK_BG, PADDING_RATIO_STANDARD),
        ("apple-touch-icon.png",     180,  DARK_BG, PADDING_RATIO_STANDARD),
        ("apple-touch-icon-120.png", 120,  DARK_BG, PADDING_RATIO_STANDARD),
        ("apple-touch-icon-152.png", 152,  DARK_BG, PADDING_RATIO_STANDARD),
        ("apple-touch-icon-167.png", 167,  DARK_BG, PADDING_RATIO_STANDARD),
        ("icon-192.png",             192,  DARK_BG, PADDING_RATIO_STANDARD),
        ("icon-512.png",             512,  DARK_BG, PADDING_RATIO_STANDARD),
        # Maskable icons need an oversized safe-zone (Android crops to circle).
        ("icon-maskable-192.png",    192,  DARK_BG, PADDING_RATIO_MASKABLE),
        ("icon-maskable-512.png",    512,  DARK_BG, PADDING_RATIO_MASKABLE),
        # LIGHT variants for prefers-color-scheme: dark browsers
        ("favicon-light-16.png",      16, LIGHT_BG, PADDING_RATIO_STANDARD),
        ("favicon-light-32.png",      32, LIGHT_BG, PADDING_RATIO_STANDARD),
        ("favicon-light-48.png",      48, LIGHT_BG, PADDING_RATIO_STANDARD),
        ("apple-touch-icon-light.png", 180, LIGHT_BG, PADDING_RATIO_STANDARD),
    ]

    for name, size, bg, ratio in plan:
        img = composite(mark, size, bg, ratio)
        # Convert alpha → solid RGBA (no transparency) so iOS Springboard
        # doesn't fill it with default white/black.
        path = OUT / name
        img.save(path, "PNG", optimize=True)
        print(f"  wrote {path.name:30s} {size}×{size}  bg={bg[:3]}  fill={ratio:.0%}")

    # Multi-size favicon.ico (16/32/48/64 stacked in one .ico)
    ico_sizes = [(16, 16), (32, 32), (48, 48), (64, 64)]
    base = composite(mark, 64, DARK_BG, PADDING_RATIO_STANDARD)
    base.save(OUT / "favicon.ico", format="ICO", sizes=ico_sizes)
    print(f"  wrote {(OUT / 'favicon.ico').name:30s} multi-size {ico_sizes}")

    print("\nDone.")


if __name__ == "__main__":
    main()
