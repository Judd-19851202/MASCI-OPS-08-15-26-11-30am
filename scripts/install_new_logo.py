"""Install the new MASCI HUB logo, full pipeline.

What this script does (idempotent, re-runnable):

  1. Open the source PNG (1774×887, RGB, pure-black background).
  2. Flood-fill the four corners with transparent so the black perimeter
     becomes alpha=0 — preserves all dark pixels INSIDE the medallion
     (those are not connected to the corners).
  3. Crop above the gap that has dense content both sides — drops the
     bottom "RUN EVERY JOB. CONTROL EVERY DETAIL. PROTECT EVERYTHING."
     line so the logo lockup is just the medallion + MASCI HUB plate
     (which already includes "NO GUESSWORK · NO MISSED STEPS · NO EXCUSES"
     baked inside the metallic plate).
  4. Auto-crop to the tight bounding box of opaque pixels.
  5. Split into mark (M-shield only) and wordmark (MASCI HUB plate only).
  6. Generate **two distinct logo variants per piece**:
       • dark-background variant — original transparent metallic-on-dark
       • light-background variant — high-contrast version with bright
         metallic pixels darkened so the lockup pops on white paper.
         Strategy: any opaque pixel whose RGB sum > 540 (pale silver /
         off-white) gets pushed down a uniform amount in luminance
         (×0.45) and slightly toward charcoal-blue so it doesn't go
         flat-grey.  Red and dark-navy pixels are untouched so the M
         and the wordmark stay the brand colors.
  7. Resize to sane sizes (lockup max 1600 wide; mark max 600).
  8. Write 11 logo PNGs to /app/frontend/public + /app/backend/static.
  9. Generate **brand-correct favicons + PWA icons** by rendering the
     M-shield mark on a transparent canvas at every size needed by the
     manifest:
       • favicon-16/32/48
       • apple-touch-icon-120/152/167/180
       • icon-192/512
       • icon-maskable-192/512  (with 10 % safe-zone padding per Android
         maskable icon spec)
 10. Wipe obsolete asset directories (`_old_safety_lockups`, `_src`,
     `_pre_tagline_rebrand_backup`).

Source image is /tmp/new_masci_logo.png.  If you push a new version,
drop it at that path and re-run the script — every downstream PNG is
regenerated from this single source.
"""
from __future__ import annotations

import shutil
from pathlib import Path

from PIL import Image, ImageDraw

SRC = Path("/tmp/new_masci_logo.png")
SRC_LIGHT = Path("/tmp/new_masci_logo_light.png")
PUBLIC = Path("/app/frontend/public")
STATIC = Path("/app/backend/static")


# ───────────────────────── Helpers ─────────────────────────


def _flood_corners_transparent(im: Image.Image, thresh: int = 28) -> Image.Image:
    if im.mode != "RGBA":
        im = im.convert("RGBA")
    w, h = im.size
    for seed in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]:
        ImageDraw.floodfill(im, seed, value=(0, 0, 0, 0), thresh=thresh)
    return im


def _autocrop(im: Image.Image) -> Image.Image:
    alpha = im.split()[-1]
    bbox = alpha.point(lambda v: 255 if v > 8 else 0).getbbox()
    return im.crop(bbox) if bbox else im


def _crop_above_gap(im: Image.Image) -> Image.Image:
    """Drop the bottom 'RUN EVERY JOB...' line by finding the first
    sparse-row band that has dense content both above AND below it."""
    w, h = im.size
    alpha = im.split()[-1].load()
    counts = [sum(1 for x in range(w) if alpha[x, y] > 8) for y in range(h)]
    sparse_thresh = max(2, int(w * 0.01))
    runs = []
    y = 0
    while y < h:
        if counts[y] < sparse_thresh:
            start = y
            while y < h and counts[y] < sparse_thresh:
                y += 1
            runs.append((start, y - start))
        else:
            y += 1

    def has_dense_above(start_y: int) -> bool:
        return any(counts[k] >= sparse_thresh for k in range(0, start_y))

    def has_dense_below(end_y: int) -> bool:
        return any(counts[k] >= sparse_thresh for k in range(end_y, h))

    qualifying = [
        (s, length)
        for s, length in runs
        if length >= max(15, h // 35) and has_dense_above(s) and has_dense_below(s + length)
    ]
    if qualifying:
        return im.crop((0, 0, w, qualifying[0][0]))
    return im


def _find_split_column(im: Image.Image) -> int | None:
    w, h = im.size
    alpha = im.split()[-1].load()
    col_counts = [sum(1 for y in range(h) if alpha[x, y] > 8) for x in range(w)]
    gap_thresh = max(2, int(h * 0.01))
    start = int(w * 0.25)
    min_gap = max(8, int(w * 0.02))
    x = start
    while x < w - min_gap:
        if col_counts[x] < gap_thresh:
            run = 0
            xx = x
            while xx < w and col_counts[xx] < gap_thresh:
                run += 1
                xx += 1
            if run >= min_gap:
                return x + run // 2
            x = xx
        else:
            x += 1
    return None


def _extract_mark(im: Image.Image) -> Image.Image:
    x = _find_split_column(im)
    if x is not None:
        return _autocrop(im.crop((0, 0, x, im.height)))
    return _autocrop(im.crop((0, 0, int(im.width * 0.32), im.height)))


def _extract_wordmark(im: Image.Image) -> Image.Image:
    x = _find_split_column(im)
    if x is not None:
        return _autocrop(im.crop((x, 0, im.width, im.height)))
    return _autocrop(im.crop((int(im.width * 0.32), 0, im.width, im.height)))


def _load_light_source() -> Image.Image | None:
    """Load the user-supplied light-background logo source, if present.

    Prefers a real designed asset over algorithmic darkening — the
    designer-provided image will always read better on white than
    anything we can derive from the dark variant.
    """
    if not SRC_LIGHT.exists():
        return None
    im = Image.open(SRC_LIGHT).convert("RGBA")
    # The supplied file may already be transparent (most exports are);
    # if it has a hard-black perimeter, flood-fill it the same way as
    # the dark variant.
    px = im.getpixel((0, 0))
    if px[3] > 200 and sum(px[:3]) < 60:
        # Opaque black corner — flood out
        im = _flood_corners_transparent(im, thresh=30)
    return _autocrop(im)


def _to_onlight_algorithmic(im: Image.Image) -> Image.Image:
    """Fallback: derive a light-bg variant from the dark logo by adding
    a deep-navy outline + selective darkening of silver pixels.

    Only used when no user-supplied light source exists at SRC_LIGHT.
    """
    from PIL import ImageFilter, ImageChops

    if im.mode != "RGBA":
        im = im.convert("RGBA")
    w, h = im.size

    darkened = im.copy()
    px = darkened.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            chroma = max(r, g, b) - min(r, g, b)
            if r > 80 and r > g + b and chroma > 60:
                continue
            lum = r + g + b
            if lum > 600:
                f = 0.55
            elif lum > 450:
                f = 0.70
            elif lum > 300:
                f = 0.85
            else:
                continue
            px[x, y] = (int(r * f), int(g * f), int(b * f), a)

    alpha = darkened.split()[-1]
    hard_mask = alpha.point(lambda v: 255 if v > 32 else 0)
    dilated = hard_mask.filter(ImageFilter.MaxFilter(7))
    outline_mask = ImageChops.subtract(dilated, hard_mask)
    outline_layer = Image.new("RGBA", (w, h), (11, 18, 32, 0))
    outline_layer.putalpha(outline_mask)
    return Image.alpha_composite(outline_layer, darkened)


def _resize_max(im: Image.Image, max_w: int) -> Image.Image:
    if im.width <= max_w:
        return im
    ratio = max_w / im.width
    return im.resize((max_w, int(im.height * ratio)), Image.LANCZOS)


def _save(path: Path, im: Image.Image) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path, format="PNG", optimize=True)
    print(f"[install-logo] wrote {path}  ({path.stat().st_size:,} bytes)")


# ───────────────────────── Favicons / PWA icons ─────────────────────────


def _square_canvas_for_icon(mark: Image.Image, side: int, pad_pct: float = 0.0) -> Image.Image:
    """Center-place the mark on a square transparent canvas at `side`x`side`,
    with `pad_pct` margin so the mark doesn't touch the edges."""
    if mark.mode != "RGBA":
        mark = mark.convert("RGBA")
    target_inner = int(side * (1 - pad_pct * 2))
    src = _autocrop(mark)
    sw, sh = src.size
    scale = min(target_inner / sw, target_inner / sh)
    new_w = max(1, int(sw * scale))
    new_h = max(1, int(sh * scale))
    resized = src.resize((new_w, new_h), Image.LANCZOS)
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(resized, ((side - new_w) // 2, (side - new_h) // 2), resized)
    return canvas


def _generate_favicons(mark: Image.Image) -> None:
    favs = [16, 32, 48]
    for s in favs:
        _save(PUBLIC / f"favicon-{s}.png", _square_canvas_for_icon(mark, s, pad_pct=0.05))
    apples = [(120, "apple-touch-icon-120.png"), (152, "apple-touch-icon-152.png"),
              (167, "apple-touch-icon-167.png"), (180, "apple-touch-icon.png")]
    for s, name in apples:
        # Apple icons render on iOS home screens: must be SQUARE with full
        # opacity (no transparency — iOS blends transparent pixels with
        # white which looks washed-out).  Composite over near-white so the
        # rounded-square mask iOS adds wraps cleanly on the dark logo.
        canvas = _square_canvas_for_icon(mark, s, pad_pct=0.08)
        bg = Image.new("RGBA", (s, s), (255, 255, 255, 255))
        bg.alpha_composite(canvas)
        _save(PUBLIC / name, bg.convert("RGB").convert("RGBA"))
    pwas = [192, 512]
    for s in pwas:
        # Standard PWA icon: transparent edges, mark centered with small pad
        _save(PUBLIC / f"icon-{s}.png", _square_canvas_for_icon(mark, s, pad_pct=0.06))
    # Maskable icons: Android crops to ~80 % of canvas, so we need a 10 %
    # safe zone on EACH side.  Composite the mark on a deep-navy background
    # to match the brand header palette.
    for s in pwas:
        canvas = _square_canvas_for_icon(mark, s, pad_pct=0.18)
        bg = Image.new("RGBA", (s, s), (15, 23, 42, 255))  # slate-900
        bg.alpha_composite(canvas)
        _save(PUBLIC / f"icon-maskable-{s}.png", bg)


# ───────────────────────── Main ─────────────────────────


def main() -> None:
    print(f"[install-logo] reading {SRC}")
    src = Image.open(SRC).convert("RGBA")
    print(f"[install-logo] source size: {src.size}")

    transparent = _flood_corners_transparent(src.copy(), thresh=28)
    cropped_top = _crop_above_gap(transparent)
    print(f"[install-logo] after dropping RUN-EVERY-JOB line: {cropped_top.size}")
    lockup = _autocrop(cropped_top)
    print(f"[install-logo] tight lockup: {lockup.size}")

    mark = _extract_mark(lockup)
    wordmark = _extract_wordmark(lockup)

    lockup = _resize_max(lockup, 1600)
    mark = _resize_max(mark, 600)
    wordmark = _resize_max(wordmark, 1200)
    print(f"[install-logo] final sizes — lockup={lockup.size} mark={mark.size} wordmark={wordmark.size}")

    # Build the light-bg variants.  Prefer the user-supplied designed
    # asset (SRC_LIGHT); fall back to the algorithmic outline if no
    # designed file is available.
    designed_light = _load_light_source()
    if designed_light is not None:
        print(f"[install-logo] using user-supplied light source: {SRC_LIGHT} {designed_light.size}")
        # Resize to the SAME max width as the dark lockup so that
        # everywhere the lockup renders the size is consistent.
        lockup_light = _resize_max(designed_light, 1600)
        mark_light = _resize_max(_extract_mark(designed_light), 600)
        wordmark_light = _resize_max(_extract_wordmark(designed_light), 1200)
        print(f"[install-logo] light-bg sizes — lockup={lockup_light.size} mark={mark_light.size} wordmark={wordmark_light.size}")
    else:
        print("[install-logo] no SRC_LIGHT — falling back to algorithmic onlight derivation")
        lockup_light = _to_onlight_algorithmic(lockup.copy())
        mark_light = _to_onlight_algorithmic(mark.copy())
        wordmark_light = _to_onlight_algorithmic(wordmark.copy())

    # Write all logo variants
    targets = {
        # On-dark (original transparent, metallic colors intact)
        PUBLIC / "masci-full-lockup.png": lockup,
        PUBLIC / "masci-full-lockup-onblack.png": lockup,
        PUBLIC / "masci-mark.png": mark,
        PUBLIC / "masci-mark-onblack.png": mark,
        PUBLIC / "masci-wordmark.png": wordmark,
        PUBLIC / "masci-wordmark-onblack.png": wordmark,
        # On-light (darkened metallics, high contrast on white paper)
        PUBLIC / "masci-full-lockup-onlight.png": lockup_light,
        PUBLIC / "masci-mark-onlight.png": mark_light,
        PUBLIC / "masci-wordmark-onlight.png": wordmark_light,
        # Backend static — PDFs are white-paper output, use light variant.
        # Email — clients render on white by default, also use light variant.
        STATIC / "masci-logo.png": lockup_light,
        STATIC / "masci-logo-email.png": lockup_light,
    }
    for path, img in targets.items():
        _save(path, img)

    # Audit copy of original source
    audit = Path("/app/assets/source/logo_source_2026-05-03.png")
    audit.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SRC, audit)
    print(f"[install-logo] audit copy: {audit}")

    # Favicons + PWA icons (built from the M-shield mark)
    print("[install-logo] regenerating favicons + PWA icons from mark…")
    _generate_favicons(mark)

    # Cleanup obsolete dirs
    for stale in [
        PUBLIC / "_pre_tagline_rebrand_backup",
        PUBLIC / "_old_safety_lockups",
        PUBLIC / "_src",
    ]:
        if stale.exists():
            shutil.rmtree(stale)
            print(f"[install-logo] removed obsolete dir: {stale}")

    print("[install-logo] DONE")


if __name__ == "__main__":
    main()
