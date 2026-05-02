"""Recolor the bottom tagline ("EXCELLENCE • ADAPT • OVERCOME") on the
masci-full-lockup.png from near-black to silver/grey so it reads on
the dark navy site header (and stays readable on light surfaces).

The dark tagline currently sits below the dark plate at y=478..504.
Inside that band, anti-aliased dark text pixels (low R/G/B, full alpha)
are replaced with silver #C8C8C8 — keeping the per-pixel alpha so
anti-aliasing is preserved. Red dash separators are left alone.

After recolouring the transparent variant we also write proper
on-light (white background) and on-black variants used by PDFs/print.
"""
from pathlib import Path
from PIL import Image

PUBLIC = Path("/app/frontend/public")
SRC = PUBLIC / "masci-full-lockup.png"
OUT_TRANSPARENT = PUBLIC / "masci-full-lockup.png"
OUT_ONLIGHT = PUBLIC / "masci-full-lockup-onlight.png"
OUT_ONBLACK = PUBLIC / "masci-full-lockup-onblack.png"

# y-band that contains "EXCELLENCE • ADAPT • OVERCOME"
TAG_Y_START = 478
TAG_Y_END = 506  # exclusive

SILVER = (200, 200, 200)  # ~#C8C8C8 — same family as the HUB silver

# Pixel is considered "dark text" (anti-aliased glyph) when fairly opaque
# AND its RGB is dark grey/black (low and roughly equal).
def is_dark_text(p):
    r, g, b, a = p
    if a < 30:
        return False
    if max(r, g, b) > 90:
        return False
    if max(r, g, b) - min(r, g, b) > 25:  # filters out reds
        return False
    return True


def recolor_tagline(img: Image.Image) -> Image.Image:
    img = img.convert("RGBA")
    px = img.load()
    w, h = img.size
    changed = 0
    for y in range(TAG_Y_START, min(TAG_Y_END, h)):
        for x in range(w):
            p = px[x, y]
            if is_dark_text(p):
                # Preserve alpha so anti-aliased edges stay smooth.
                # Blend silver with darkness ratio so darker pixels become
                # darker silver (deep edge) and full-black centers become
                # solid silver — looks like a real silver glyph.
                r, g, b, a = p
                # darkness 0..1 (0 = pure black/center, 1 = light edge)
                darkness = min(r, g, b) / 90.0
                # final colour = silver scaled by (1 - darkness*0.4)
                # so the glyph centre is full silver, edges fade slightly
                scale = 1.0 - darkness * 0.35
                nr = int(SILVER[0] * scale)
                ng = int(SILVER[1] * scale)
                nb = int(SILVER[2] * scale)
                px[x, y] = (nr, ng, nb, a)
                changed += 1
    print(f"recoloured {changed} pixels in y={TAG_Y_START}..{TAG_Y_END}")
    return img


def flatten(img: Image.Image, bg: tuple) -> Image.Image:
    """Composite RGBA image over a solid background colour."""
    bg_img = Image.new("RGBA", img.size, bg + (255,))
    bg_img.alpha_composite(img)
    return bg_img.convert("RGB")


def main():
    src = Image.open(SRC).convert("RGBA")
    fixed = recolor_tagline(src)

    # 1) transparent variant (overwrite the canonical lockup)
    fixed.save(OUT_TRANSPARENT, "PNG")
    print(f"saved {OUT_TRANSPARENT}")

    # 2) on-light (white background)
    flatten(fixed, (255, 255, 255)).save(OUT_ONLIGHT, "PNG")
    print(f"saved {OUT_ONLIGHT}")

    # 3) on-black (black background)
    flatten(fixed, (0, 0, 0)).save(OUT_ONBLACK, "PNG")
    print(f"saved {OUT_ONBLACK}")


if __name__ == "__main__":
    main()
