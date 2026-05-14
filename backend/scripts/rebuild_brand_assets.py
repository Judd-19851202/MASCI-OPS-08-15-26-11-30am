"""
Regenerate every icon/splash/OG asset from the AUTHENTIC `masci-mark.png`
file — no AI generation, pure PIL composition. This guarantees the
splash screens, favicons, app icons, and OG card all use the SAME M
the user has been using everywhere else.

Output:
    /app/frontend/public/favicon-{16,32,48,64}.png
    /app/frontend/public/apple-touch-icon-{120,152,167}.png
    /app/frontend/public/apple-touch-icon.png        (180)
    /app/frontend/public/icon-{192,512}.png
    /app/frontend/public/icon-maskable-{192,512}.png
    /app/frontend/public/favicon.ico                 (16/32/48)
    /app/frontend/public/og-image.png                (1200×630)
    /app/frontend/public/splash-*.png                (10 sizes)
"""
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path("/app/frontend/public")
SOURCE_M = OUT / "masci-mark.png"  # the user's authentic M
SLATE_900 = (15, 23, 42)
RED_700 = (185, 28, 28)
WHITE = (255, 255, 255)
SLATE_300 = (203, 213, 225)
SLATE_700 = (51, 65, 85)
FONT_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"


def load_m_on_slate(side: int) -> Image.Image:
    """Load the M, trim its background, place on slate-900 canvas at `side` px."""
    m = Image.open(SOURCE_M).convert("RGBA")
    # Trim transparent/near-black border so the M fills the frame
    bbox = m.getbbox()
    if bbox:
        m = m.crop(bbox)
    # Resize to 78 % of canvas (10% margin all around feels balanced)
    target = int(side * 0.78)
    # Maintain aspect ratio
    w, h = m.size
    scale = min(target / w, target / h)
    nw, nh = int(w * scale), int(h * scale)
    m_resized = m.resize((nw, nh), Image.LANCZOS)
    # Composite onto slate background
    canvas = Image.new("RGB", (side, side), SLATE_900)
    canvas.paste(m_resized, ((side - nw) // 2, (side - nh) // 2), m_resized)
    return canvas


def make_maskable(side: int) -> Image.Image:
    """Android safe-zone variant: M occupies inner 64% of canvas."""
    canvas = Image.new("RGB", (side, side), SLATE_900)
    inner_side = int(side * 0.64)
    m_inner = load_m_on_slate(inner_side)
    offset = (side - inner_side) // 2
    canvas.paste(m_inner, (offset, offset))
    return canvas


def draw_caution_stripe(img: Image.Image, y: int, height: int):
    w, _ = img.size
    band = Image.new("RGB", (w, height), SLATE_900)
    bd = ImageDraw.Draw(band)
    stripe_w = max(24, height)
    for x in range(-height, w + height, stripe_w):
        bd.polygon([
            (x, height), (x + stripe_w // 2, height),
            (x + stripe_w // 2 + height, 0), (x + height, 0),
        ], fill=RED_700)
    img.paste(band, (0, y))


def compose_og(w: int, h: int) -> Image.Image:
    canvas = Image.new("RGB", (w, h), SLATE_900)
    draw = ImageDraw.Draw(canvas)

    # Subtle blueprint grid (very low opacity)
    grid_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grid_layer)
    grid_color = (96, 165, 250, 18)  # blue-400 @ 7%
    step = max(40, h // 18)
    for x in range(0, w, step):
        gd.line([(x, 0), (x, h)], fill=grid_color, width=1)
    for y in range(0, h, step):
        gd.line([(0, y), (w, y)], fill=grid_color, width=1)
    canvas = Image.alpha_composite(canvas.convert("RGBA"), grid_layer).convert("RGB")
    draw = ImageDraw.Draw(canvas)

    # M-mark in the left third — height ≈ 70 % of canvas
    m_side = int(h * 0.78)
    m = load_m_on_slate(m_side)
    m_x = int(w * 0.08)
    m_y = (h - m_side) // 2
    canvas.paste(m, (m_x, m_y))

    # Wordmark + tagline in the right two-thirds
    text_x = m_x + m_side + int(w * 0.04)
    wm_size = int(h * 0.10)
    tag_size = int(h * 0.045)
    try:
        wm_font = ImageFont.truetype(FONT_BOLD, wm_size)
        tag_font = ImageFont.truetype(FONT_REG, tag_size)
    except OSError:
        wm_font = ImageFont.load_default()
        tag_font = ImageFont.load_default()

    line1 = "MASCI"
    line2 = "OPERATIONS PLATFORM"
    bbox1 = draw.textbbox((0, 0), line1, font=wm_font)
    bbox2 = draw.textbbox((0, 0), line2, font=wm_font)
    line1_h = bbox1[3] - bbox1[1]
    line2_h = bbox2[3] - bbox2[1]
    block_top = int(h * 0.28)
    draw.text((text_x, block_top), line1, fill=WHITE, font=wm_font)
    draw.text((text_x, block_top + line1_h + int(h * 0.01)),
              line2, fill=WHITE, font=wm_font)

    tagline = "Run every job. Control every detail. Protect everything."
    draw.text(
        (text_x, block_top + line1_h + line2_h + int(h * 0.05)),
        tagline, fill=SLATE_300, font=tag_font,
    )

    # Caution stripe along the bottom
    stripe_h = max(16, int(h * 0.03))
    draw_caution_stripe(canvas, h - stripe_h, stripe_h)
    return canvas


def compose_splash(w: int, h: int) -> Image.Image:
    """iPhone/iPad portrait splash — M centered, wordmark + tagline below."""
    canvas = Image.new("RGB", (w, h), SLATE_900)
    draw = ImageDraw.Draw(canvas)

    side = min(w, h)
    m_size = int(side * 0.30)
    m_img = load_m_on_slate(m_size)
    mx = (w - m_size) // 2
    my = int(h * 0.30)
    canvas.paste(m_img, (mx, my))

    wm_size = max(28, int(side * 0.04))
    tag_size = max(18, int(side * 0.024))
    foot_size = max(12, int(side * 0.013))
    try:
        wm_font = ImageFont.truetype(FONT_BOLD, wm_size)
        tag_font = ImageFont.truetype(FONT_REG, tag_size)
        foot_font = ImageFont.truetype(FONT_BOLD, foot_size)
    except OSError:
        wm_font = tag_font = foot_font = ImageFont.load_default()

    wm = "MASCI OPERATIONS PLATFORM"
    bbox = draw.textbbox((0, 0), wm, font=wm_font)
    wm_w = bbox[2] - bbox[0]
    wm_h = bbox[3] - bbox[1]
    wm_y = my + m_size + int(side * 0.05)
    draw.text(((w - wm_w) // 2, wm_y), wm, fill=WHITE, font=wm_font)

    tagline = "Run every job. Control every detail. Protect everything."
    tbbox = draw.textbbox((0, 0), tagline, font=tag_font)
    t_w = tbbox[2] - tbbox[0]
    draw.text(((w - t_w) // 2, wm_y + wm_h + int(side * 0.02)),
              tagline, fill=SLATE_300, font=tag_font)

    foot = "POWERED BY FORGEDOPS\u2122"
    fbbox = draw.textbbox((0, 0), foot, font=foot_font)
    f_w = fbbox[2] - fbbox[0]
    draw.text(((w - f_w) // 2, h - int(side * 0.08) - foot_size),
              foot, fill=SLATE_700, font=foot_font)

    stripe_h = max(18, int(side * 0.013))
    draw_caution_stripe(canvas, h - stripe_h, stripe_h)
    return canvas


# Sizes for icons / favicons / Apple touch / PWA
ICON_SIZES = [
    ("favicon-16.png", 16, False),
    ("favicon-32.png", 32, False),
    ("favicon-48.png", 48, False),
    ("favicon-64.png", 64, False),
    ("apple-touch-icon-120.png", 120, False),
    ("apple-touch-icon-152.png", 152, False),
    ("apple-touch-icon-167.png", 167, False),
    ("apple-touch-icon.png", 180, False),
    ("icon-192.png", 192, False),
    ("icon-512.png", 512, False),
    ("icon-maskable-192.png", 192, True),
    ("icon-maskable-512.png", 512, True),
]

# iOS portrait splash sizes (10 devices)
SPLASH_SIZES = [
    (1290, 2796), (1179, 2556), (1170, 2532), (1284, 2778),
    (1125, 2436), (1080, 2340), (828, 1792),  (750, 1334),
    (2048, 2732), (1668, 2388),
]


def main():
    if not SOURCE_M.exists():
        print(f"FAIL — {SOURCE_M} not found")
        return

    print(f"=== Master M source: {SOURCE_M} ({SOURCE_M.stat().st_size:,} bytes) ===\n")

    # Master 1024 icon (also saved for future use)
    master = load_m_on_slate(1024)
    master.save(OUT / "_icon_master_1024.png", format="PNG", optimize=True)
    print(f"  → _icon_master_1024.png  ({(OUT / '_icon_master_1024.png').stat().st_size:,} bytes)")

    # Icon set
    print("\n[icons]")
    for fname, size, maskable in ICON_SIZES:
        img = make_maskable(size) if maskable else load_m_on_slate(size)
        img.save(OUT / fname, format="PNG", optimize=True)
        print(f"  → {fname:<32} {size}x{size}  {(OUT / fname).stat().st_size:>7,} bytes  "
              f"{'maskable' if maskable else ''}")

    # favicon.ico
    ico_sizes = [(16, 16), (32, 32), (48, 48)]
    ico_imgs = [load_m_on_slate(s[0]) for s in ico_sizes]
    ico_imgs[0].save(
        OUT / "favicon.ico",
        format="ICO", sizes=ico_sizes, append_images=ico_imgs[1:],
    )
    print(f"  → favicon.ico (16,32,48)  {(OUT / 'favicon.ico').stat().st_size:,} bytes")

    # OG image
    print("\n[og-image]")
    og = compose_og(1200, 630)
    og.save(OUT / "og-image.png", format="PNG", optimize=True)
    print(f"  → og-image.png            1200x630  {(OUT / 'og-image.png').stat().st_size:>7,} bytes")

    # Splash screens
    print("\n[splash]")
    for w, h in SPLASH_SIZES:
        img = compose_splash(w, h)
        out = OUT / f"splash-{w}x{h}.png"
        img.save(out, format="PNG", optimize=True)
        print(f"  → {out.name:<22} {w}x{h:<5}  {out.stat().st_size:>7,} bytes")

    print("\nDone.")


if __name__ == "__main__":
    main()
