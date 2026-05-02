"""Recolour the bottom tagline ("EXCELLENCE • ADAPT • OVERCOME") on the
MASCI HUB lockup so it has the right contrast for the surface it sits on,
and bake a small "Powered by The Judd Group LLC" vendor credit into the
print-bound variants only (on-light, on-black). The transparent variant
that lives in the live app stays clean — no vendor credit baked in.

Each variant gets a tagline colour tuned for its target background:

    masci-full-lockup.png          (transparent → dark navy header)  → SILVER, no credit
    masci-full-lockup-onblack.png  (solid black PDFs)                → SILVER, credit
    masci-full-lockup-onlight.png  (white cheat sheets / posters)    → DARK NAVY, credit

Source-of-truth raster is `_src/masci-full-lockup.SOURCE.png` — the
original AI-generated lockup with the dark tagline still intact. We
read from this file every time so this script is idempotent and never
recolours an already-recoloured pixel.

The recolour band is y=478..506 (the row range that contains the
EXCELLENCE • ADAPT • OVERCOME line, just below the dark plate). Inside
the band, only "dark text" pixels (low/balanced RGB with non-trivial
alpha) are touched — red dash separators and any plate/border pixels
are left alone.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

PUBLIC = Path("/app/frontend/public")
SOURCE_DIR = PUBLIC / "_src"
SOURCE = SOURCE_DIR / "masci-full-lockup.SOURCE.png"

OUT_TRANSPARENT = PUBLIC / "masci-full-lockup.png"
OUT_ONLIGHT = PUBLIC / "masci-full-lockup-onlight.png"
OUT_ONBLACK = PUBLIC / "masci-full-lockup-onblack.png"

# y-band that contains "EXCELLENCE • ADAPT • OVERCOME"
TAG_Y_START = 478
TAG_Y_END = 506  # exclusive

SILVER = (200, 200, 200)        # ~#C8C8C8 — same family as the HUB silver
DARK_NAVY = (15, 23, 42)        # #0F172A — slate-900, app brand dark

# A pixel is treated as "dark glyph" (anti-aliased text) when reasonably
# opaque AND its RGB is dark-grey/black (low values, roughly equal channels).
def is_dark_text(p):
    r, g, b, a = p
    if a < 30:
        return False
    if max(r, g, b) > 90:
        return False
    if max(r, g, b) - min(r, g, b) > 25:  # filters out reds
        return False
    return True


def recolour(img: Image.Image, target: tuple) -> Image.Image:
    """Return a copy of img with the tagline glyphs recoloured to `target`,
    preserving each pixel's alpha and the per-pixel darkness ramp (so the
    glyph centre is full target colour, anti-aliased edges fade slightly).
    """
    img = img.convert("RGBA").copy()
    px = img.load()
    w, h = img.size
    changed = 0
    for y in range(TAG_Y_START, min(TAG_Y_END, h)):
        for x in range(w):
            p = px[x, y]
            if not is_dark_text(p):
                continue
            r, g, b, a = p
            # darkness ramp 0..1 (0 = pure black centre, 1 = light edge)
            darkness = min(r, g, b) / 90.0
            scale = 1.0 - darkness * 0.35
            nr = int(target[0] * scale + (255 - target[0]) * (1 - scale) * 0.0)
            ng = int(target[1] * scale + (255 - target[1]) * (1 - scale) * 0.0)
            nb = int(target[2] * scale + (255 - target[2]) * (1 - scale) * 0.0)
            px[x, y] = (max(0, min(255, nr)),
                        max(0, min(255, ng)),
                        max(0, min(255, nb)),
                        a)
            changed += 1
    print(f"  recoloured {changed} pixels → rgb{target}")
    return img


def flatten(img: Image.Image, bg: tuple) -> Image.Image:
    """Composite an RGBA image over a solid background colour, returning RGB."""
    bg_img = Image.new("RGBA", img.size, bg + (255,))
    bg_img.alpha_composite(img)
    return bg_img.convert("RGB")


# Vendor credit baked into print variants (on-light, on-black) — NOT the
# transparent variant. Plain text, no claim of sublicensing — just an
# attribution line for paperwork that leaves the building.
CREDIT_TEXT = "POWERED BY THE JUDD GROUP LLC"
CREDIT_FONT_PATH = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
CREDIT_FONT_SIZE = 22
CREDIT_Y = 552  # well below the EXCELLENCE row (which ends at y=506)


def add_credit(img: Image.Image, fill: tuple) -> Image.Image:
    """Draw the vendor credit centred horizontally below the lockup."""
    img = img.copy()
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(CREDIT_FONT_PATH, CREDIT_FONT_SIZE)
    except Exception:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), CREDIT_TEXT, font=font)
    text_w = bbox[2] - bbox[0]
    x = (img.size[0] - text_w) // 2
    # Subtle: lighter than the tagline so it reads as fine print, not headline.
    draw.text((x, CREDIT_Y), CREDIT_TEXT, font=font, fill=fill,
              spacing=2)
    return img


def main():
    SOURCE_DIR.mkdir(exist_ok=True)
    if not SOURCE.exists():
        raise SystemExit(
            f"source raster {SOURCE} missing — restore from git "
            f"(an earlier commit had the original dark-tagline lockup)."
        )
    src = Image.open(SOURCE).convert("RGBA")
    print(f"source: {SOURCE} ({src.size[0]}x{src.size[1]})")

    # 1) transparent variant — silver tagline (lives on dark navy header)
    print("[masci-full-lockup.png] transparent + silver tagline")
    silver = recolour(src, SILVER)
    silver.save(OUT_TRANSPARENT, "PNG")
    print(f"  saved {OUT_TRANSPARENT}")

    # 2) on-light variant — DARK NAVY tagline so it reads on white,
    #    + small "Powered by The Judd Group LLC" credit baked in.
    print("[masci-full-lockup-onlight.png] white-bg flatten + dark-navy tagline + credit")
    dark = recolour(src, DARK_NAVY)
    dark_with_credit = add_credit(dark, DARK_NAVY + (180,))  # 70% opacity slate-900
    flatten(dark_with_credit, (255, 255, 255)).save(OUT_ONLIGHT, "PNG")
    print(f"  saved {OUT_ONLIGHT}")

    # 3) on-black variant — silver tagline, flattened on black,
    #    + small silver credit.
    print("[masci-full-lockup-onblack.png] black-bg flatten + silver tagline + credit")
    silver_with_credit = add_credit(silver, SILVER + (180,))
    flatten(silver_with_credit, (0, 0, 0)).save(OUT_ONBLACK, "PNG")
    print(f"  saved {OUT_ONBLACK}")


if __name__ == "__main__":
    main()
