"""
Generate 10 iOS PWA splash screens by COMPOSING (not generating) the
master M-mark icon + wordmark + tagline + caution-stripe onto each
required iPhone/iPad portrait resolution.

Output: /app/frontend/public/splash-{w}x{h}.png + an HTML snippet for
index.html with the proper apple-touch-startup-image link tags.
"""
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path("/app/frontend/public")
MASTER = Path("/app/assets/source/icon_master_1024.png")
SLATE_900 = (15, 23, 42)
RED_700 = (185, 28, 28)
WHITE = (255, 255, 255)
SLATE_300 = (203, 213, 225)
SLATE_700 = (51, 65, 85)

FONT_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"

# 10 modern iPhone/iPad portrait sizes — covers ~95 % of installed iOS PWAs.
# Format: (width, height, device_label, css_w, css_h, pixel_ratio)
SPLASH = [
    (1290, 2796, "iPhone 15 Pro Max / 14 Pro Max",        430, 932, 3),
    (1179, 2556, "iPhone 15 Pro / 14 Pro",                393, 852, 3),
    (1170, 2532, "iPhone 13 / 14 / 15",                   390, 844, 3),
    (1284, 2778, "iPhone 12 Pro Max / 13 Pro Max",        428, 926, 3),
    (1125, 2436, "iPhone X / XS / 11 Pro",                375, 812, 3),
    (1080, 2340, "iPhone 13 mini",                        360, 780, 3),
    (828,  1792, "iPhone XR / 11",                        414, 896, 2),
    (750,  1334, "iPhone 8 / SE 2nd-gen",                 375, 667, 2),
    (2048, 2732, "iPad Pro 12.9\"",                      1024, 1366, 2),
    (1668, 2388, "iPad Pro 11\" / iPad Air",              834, 1194, 2),
]


def draw_caution_stripe(img: Image.Image, y: int, height: int):
    """Diagonal red/black stripe band — like construction warning tape."""
    w, _ = img.size
    draw = ImageDraw.Draw(img)
    stripe_w = max(24, height)
    # The stripes go at a 45° angle. We tile two-color diagonals across
    # a clip band that's `height` tall.
    band = Image.new("RGB", (w, height), SLATE_900)
    band_draw = ImageDraw.Draw(band)
    # alternating stripes
    for x in range(-height, w + height, stripe_w):
        # red parallelogram
        band_draw.polygon([
            (x, height), (x + stripe_w // 2, height),
            (x + stripe_w // 2 + height, 0), (x + height, 0),
        ], fill=RED_700)
    img.paste(band, (0, y))


def compose(w: int, h: int, label: str) -> Image.Image:
    canvas = Image.new("RGB", (w, h), SLATE_900)
    draw = ImageDraw.Draw(canvas)

    # M-mark — 30 % of the shortest side
    side = min(w, h)
    m_size = int(side * 0.30)
    master = Image.open(MASTER).convert("RGBA").resize(
        (m_size, m_size), Image.LANCZOS
    )
    # we drew the master with the slate background already, so paste flat
    mx = (w - m_size) // 2
    my = int(h * 0.30)
    canvas.paste(master, (mx, my), master)

    # Wordmark — sized to fit comfortably under the M
    wm_size = max(28, int(side * 0.035))
    try:
        wm_font = ImageFont.truetype(FONT_BOLD, wm_size)
    except OSError:
        wm_font = ImageFont.load_default()
    wm = "MASCI OPERATIONS PLATFORM"
    bbox = draw.textbbox((0, 0), wm, font=wm_font)
    wm_w = bbox[2] - bbox[0]
    wm_h = bbox[3] - bbox[1]
    draw.text(
        ((w - wm_w) // 2, my + m_size + int(side * 0.04)),
        wm, fill=WHITE, font=wm_font,
    )

    # Tagline — slightly smaller, slate-300
    tag_size = max(18, int(side * 0.022))
    try:
        tag_font = ImageFont.truetype(FONT_REG, tag_size)
    except OSError:
        tag_font = ImageFont.load_default()
    tagline = "Run every job. Control every detail. Protect everything."
    tbbox = draw.textbbox((0, 0), tagline, font=tag_font)
    t_w = tbbox[2] - tbbox[0]
    draw.text(
        ((w - t_w) // 2, my + m_size + int(side * 0.04) + wm_h + int(side * 0.025)),
        tagline, fill=SLATE_300, font=tag_font,
    )

    # Subtle "ForgedOps" attribution at bottom
    foot_size = max(14, int(side * 0.014))
    try:
        foot_font = ImageFont.truetype(FONT_BOLD, foot_size)
    except OSError:
        foot_font = ImageFont.load_default()
    foot = "POWERED BY FORGEDOPS\u2122"
    fbbox = draw.textbbox((0, 0), foot, font=foot_font)
    f_w = fbbox[2] - fbbox[0]
    draw.text(
        ((w - f_w) // 2, h - int(side * 0.08) - foot_size),
        foot, fill=SLATE_700, font=foot_font,
    )

    # Caution stripe along very bottom (24px-ish)
    stripe_h = max(20, int(side * 0.015))
    draw_caution_stripe(canvas, h - stripe_h, stripe_h)

    return canvas


def main():
    if not MASTER.exists():
        print(f"FAIL — master icon not found at {MASTER}")
        return

    snippets = []
    for w, h, label, css_w, css_h, ratio in SPLASH:
        img = compose(w, h, label)
        out = OUT / f"splash-{w}x{h}.png"
        img.save(out, format="PNG", optimize=True)
        size = out.stat().st_size
        print(f"  → {out.name:<22} {w}x{h:<5}  {size:>7,} bytes   ({label})")

        # Generate the <link> tag for this device
        media = (
            f"(device-width: {css_w}px) and "
            f"(device-height: {css_h}px) and "
            f"(-webkit-device-pixel-ratio: {ratio}) and "
            f"(orientation: portrait)"
        )
        snippets.append(
            f'<link rel="apple-touch-startup-image" '
            f'media="{media}" '
            f'href="/splash-{w}x{h}.png" />'
        )

    snippet_file = Path("/app/assets/source/splash_links.html")
    snippet_file.parent.mkdir(parents=True, exist_ok=True)
    snippet_file.write_text("\n".join(snippets) + "\n")
    print(f"\nWrote {snippet_file} ({len(snippets)} link tags)")


if __name__ == "__main__":
    main()
