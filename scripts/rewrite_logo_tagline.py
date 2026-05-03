"""Logo tagline rewriter — v2.

This rebuild produces a CLEAN, transparent-background MASCI lockup with
the new tagline baked in. The previous rewrite left a solid black HUB
rectangle that read as a "box behind the logo" on dark headers; this
version converts that black background to fully transparent so the
lockup floats naturally on any header color.

Pipeline:
  1. Start from the pristine artwork in
     /app/frontend/public/_pre_tagline_rebrand_backup/.
  2. Detect the HUB rectangle's solid-black fill and convert ONLY those
     pixels to transparent. The M-shield artwork (which contains its own
     black detailing) is preserved by limiting the detection to the
     right-side rectangle bounds (x >= ~530).
  3. Stamp the new tagline twice — once inside the HUB rectangle (where
     "ACCOUNTABILITY · DISCIPLINE · EXECUTION" used to live), once below
     the badge (where "EXCELLENCE · ADAPT · OVERCOME" used to live).
  4. Save back to /app/frontend/public/.

After this script runs the lockup is essentially:
  • M-shield medallion (intact, original colors)
  • Floating "MASCI" + "HUB" letters (intact, original red+gradient)
  • New tagline rendered in clean silver type
  • Everything else fully transparent — no boxy background
"""
from PIL import Image, ImageDraw, ImageFont
import numpy as np

INSIDE_BAND_Y = (414, 442)        # tagline band that lived inside the HUB rect
INSIDE_BAND_X = (640, 1240)
BELOW_BAND_Y = (478, 508)         # tagline band that lived below the badge
BELOW_BAND_X = (488, 1138)

# The HUB rectangle's solid-black fill spans roughly y=210-465 on the right
# half of the canvas. Anything to the LEFT of this is the M-shield (which
# has its own black detailing we must keep).
RECT_X_MIN = 540
RECT_Y_RANGE = (200, 470)

FONT_PATH = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
NEW_TAGLINE = "NO GUESSWORK · NO MISSED STEPS · NO EXCUSES"
TAGLINE_COLOR = (210, 210, 210, 255)

VARIANTS = [
    "/app/frontend/public/masci-full-lockup.png",
    "/app/frontend/public/masci-full-lockup-onblack.png",
    "/app/frontend/public/masci-full-lockup-onlight.png",
]

SOURCE_DIR = "/app/frontend/public/_pre_tagline_rebrand_backup"


def _strip_hub_black(arr: np.ndarray) -> np.ndarray:
    """Convert the HUB rectangle's solid-black background to transparent.

    Targets pixels where R<15, G<15, B<15, A>=200, located in the
    right-side rectangle area only. Pixels with even slight red or grey
    tint (i.e. non-pure-black artwork) are preserved.
    """
    h, w, _ = arr.shape
    y0, y1 = RECT_Y_RANGE
    sub = arr[y0:y1, RECT_X_MIN:, :]
    is_black = (
        (sub[..., 0] < 15) & (sub[..., 1] < 15) & (sub[..., 2] < 15) & (sub[..., 3] >= 200)
    )
    sub[is_black] = (0, 0, 0, 0)
    arr[y0:y1, RECT_X_MIN:, :] = sub
    return arr


def _clear_band(arr: np.ndarray, x_band, y_band) -> None:
    """Wipe every pixel inside the given rectangle to fully transparent.

    Used to remove the OLD gray tagline pixels before stamping the new
    one. Once the HUB-rectangle's black background is gone, the old
    silver tagline glyphs would otherwise still be visible.
    """
    x0, x1 = x_band
    y0, y1 = y_band
    arr[y0:y1, x0:x1, :] = (0, 0, 0, 0)


def _fit_font(text: str, max_w: int, max_h: int) -> ImageFont.FreeTypeFont:
    for size in range(max_h + 4, 8, -1):
        font = ImageFont.truetype(FONT_PATH, size=size)
        bbox = font.getbbox(text)
        if (bbox[2] - bbox[0]) <= max_w and (bbox[3] - bbox[1]) <= max_h:
            return font
    return ImageFont.truetype(FONT_PATH, size=12)


def _stamp(draw: ImageDraw.ImageDraw, x_band, y_band, text, color):
    x0, x1 = x_band
    y0, y1 = y_band
    band_w = x1 - x0
    band_h = y1 - y0
    font = _fit_font(text, band_w - 12, band_h - 4)
    bbox = font.getbbox(text)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    cx = x0 + (band_w - text_w) // 2 - bbox[0]
    cy = y0 + (band_h - text_h) // 2 - bbox[1]
    draw.text((cx, cy), text, font=font, fill=color)


def rewrite(dest_path: str) -> None:
    """Read pristine source, strip black background, stamp new tagline, write to dest."""
    src_path = dest_path.replace("/app/frontend/public/", f"{SOURCE_DIR}/")
    im = Image.open(src_path).convert("RGBA")
    arr = np.array(im, dtype=np.uint8)

    # The on-light variant intentionally KEEPS the dark HUB rectangle so
    # the lockup has contrast against white headers. Only strip the black
    # background on the dark/default variants where it clashes with the
    # navy header.
    is_onlight = dest_path.endswith("onlight.png")

    if not is_onlight:
        # Step 1: drop the HUB rectangle's black fill (dark variants only)
        arr = _strip_hub_black(arr)
    # Step 2: wipe both old-tagline pixel bands.
    #   - On dark variants: clear to transparent so the new tagline stamps
    #     onto the header color.
    #   - On the on-light variant: re-paint the band BLACK to match the
    #     HUB rectangle, so the new silver tagline reads cleanly.
    if is_onlight:
        arr[INSIDE_BAND_Y[0]:INSIDE_BAND_Y[1], INSIDE_BAND_X[0]:INSIDE_BAND_X[1], :] = (0, 0, 0, 255)
        # below-band sits on the WHITE outer background; clear to transparent
        # so the dark tagline reads on white.
        arr[BELOW_BAND_Y[0]:BELOW_BAND_Y[1], BELOW_BAND_X[0]:BELOW_BAND_X[1], :] = (0, 0, 0, 0)
    else:
        _clear_band(arr, INSIDE_BAND_X, INSIDE_BAND_Y)
        _clear_band(arr, BELOW_BAND_X, BELOW_BAND_Y)

    im = Image.fromarray(arr, mode="RGBA")

    # Step 3: stamp new tagline. Both bands now sit on the right surface.
    draw = ImageDraw.Draw(im)
    _stamp(draw, INSIDE_BAND_X, INSIDE_BAND_Y, NEW_TAGLINE, TAGLINE_COLOR)
    # Below-badge band has slightly different requirements per variant:
    #   - default + onblack: silver text on transparent → looks fine
    #   - onlight: silver text would disappear on white background, so darken
    if dest_path.endswith("onlight.png"):
        below_color = (60, 60, 60, 255)
    else:
        below_color = TAGLINE_COLOR
    _stamp(draw, BELOW_BAND_X, BELOW_BAND_Y, NEW_TAGLINE, below_color)

    im.save(dest_path, optimize=True)
    print(f"  ✔ rewrote {dest_path}")


if __name__ == "__main__":
    for v in VARIANTS:
        rewrite(v)
    print("done.")
