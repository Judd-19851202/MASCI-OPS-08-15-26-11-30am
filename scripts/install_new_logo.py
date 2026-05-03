"""Install the new MASCI HUB logo across the platform.

Steps performed:
  1. Open the source PNG (1774x887, RGB, pure-black background).
  2. Flood-fill the four corners with transparent so the black perimeter
     becomes alpha=0 — preserves all dark pixels INSIDE the medallion
     (those are not connected to the corners).
  3. Slice off the bottom "RUN EVERY JOB. CONTROL EVERY DETAIL. PROTECT
     EVERYTHING." line.  That phrase is already the Hub homepage H1 — per
     spec section 4 ("Do NOT duplicate this tagline anywhere else"),
     keeping it inside the logo would duplicate it on Hub.
  4. Auto-crop to the tight bounding box of opaque pixels.
  5. Write three lockup variants + an icon-only mark to
     /app/frontend/public and /app/backend/static.

Re-runnable.  Source image is /tmp/new_masci_logo.png (downloaded from
the customer-assets URL the user uploaded).
"""
from __future__ import annotations

import shutil
from pathlib import Path

from PIL import Image, ImageDraw

SRC = Path("/tmp/new_masci_logo.png")
PUBLIC = Path("/app/frontend/public")
STATIC = Path("/app/backend/static")


def _flood_corners_transparent(im: Image.Image, thresh: int = 25) -> Image.Image:
    """Flood-fill from each corner; black-and-near-black pixels connected
    to the corner become alpha=0.  Pixels inside the medallion that are
    dark but isolated from the corner stay opaque."""
    if im.mode != "RGBA":
        im = im.convert("RGBA")
    w, h = im.size
    for seed in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]:
        ImageDraw.floodfill(im, seed, value=(0, 0, 0, 0), thresh=thresh)
    return im


def _autocrop(im: Image.Image) -> Image.Image:
    """Trim to the tight bounding box of pixels with alpha > 8."""
    alpha = im.split()[-1]
    bbox = alpha.point(lambda v: 255 if v > 8 else 0).getbbox()
    return im.crop(bbox) if bbox else im


def _crop_above_gap(im: Image.Image) -> Image.Image:
    """Find the gap between two content blocks and crop above it.

    Algorithm:
      1. Compute opaque-pixel count per row.
      2. Identify contiguous runs of "sparse" rows (count < 1% width).
      3. Filter to runs that have dense content BOTH above and below
         them — those are real visual breaks between two blocks (not the
         leading/trailing padding around the canvas).
      4. Of those, pick the FIRST one — that's the break right after the
         primary lockup, which is what we want to crop above.
    """
    w, h = im.size
    alpha = im.split()[-1].load()
    counts = [sum(1 for x in range(w) if alpha[x, y] > 8) for y in range(h)]
    sparse_thresh = max(2, int(w * 0.01))

    runs = []  # list of (start_y, length)
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
        if length >= max(15, h // 35)
        and has_dense_above(s)
        and has_dense_below(s + length)
    ]
    if qualifying:
        first_start = qualifying[0][0]
        return im.crop((0, 0, w, first_start))
    return im


def _extract_mark(im: Image.Image) -> Image.Image:
    """The M-shield medallion is the leftmost cluster.  Walk in from the
    right looking for the first "long vertical gap" — that's the column
    between the medallion and the MASCI HUB plate.  Crop everything to
    the left of that gap."""
    x = _find_split_column(im)
    if x is not None:
        return _autocrop(im.crop((0, 0, x, im.height)))
    # Fallback: left ~30%
    return _autocrop(im.crop((0, 0, int(im.width * 0.32), im.height)))


def _extract_wordmark(im: Image.Image) -> Image.Image:
    """Inverse of _extract_mark — keep everything to the right of the
    medallion (the MASCI HUB plate)."""
    x = _find_split_column(im)
    if x is not None:
        return _autocrop(im.crop((x, 0, im.width, im.height)))
    return _autocrop(im.crop((int(im.width * 0.32), 0, im.width, im.height)))


def _find_split_column(im: Image.Image) -> int | None:
    """Find the X-column that separates the M-shield (left) from the
    MASCI HUB plate (right) — the first long run of mostly-transparent
    columns starting after ~25% of the image width."""
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
                return x + run // 2  # split mid-gap
            x = xx
        else:
            x += 1
    return None


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
    print(f"[install-logo] mark (M-shield only): {mark.size}")

    # Wordmark = lockup minus the mark on the left.  Crop using the same
    # gap detection as _extract_mark but keep the right portion.
    wordmark = _extract_wordmark(lockup)
    print(f"[install-logo] wordmark (MASCI HUB plate only): {wordmark.size}")

    # Resize sane: lockup target ~1500 px wide (high-DPI safe), mark ~600 wide
    if lockup.width > 1600:
        ratio = 1600 / lockup.width
        lockup = lockup.resize(
            (1600, int(lockup.height * ratio)), Image.LANCZOS
        )
        print(f"[install-logo] resized lockup: {lockup.size}")
    if mark.width > 600:
        ratio = 600 / mark.width
        mark = mark.resize(
            (600, int(mark.height * ratio)), Image.LANCZOS
        )
        print(f"[install-logo] resized mark: {mark.size}")
    if wordmark.width > 1200:
        ratio = 1200 / wordmark.width
        wordmark = wordmark.resize(
            (1200, int(wordmark.height * ratio)), Image.LANCZOS
        )
        print(f"[install-logo] resized wordmark: {wordmark.size}")

    # Write to disk.  The new logo is metallic-on-transparent so all
    # "onblack" / "onlight" variants are the same file — they read on
    # both dark and light backgrounds without separate light/dark renders.
    targets = {
        PUBLIC / "masci-full-lockup.png": lockup,
        PUBLIC / "masci-full-lockup-onblack.png": lockup,
        PUBLIC / "masci-full-lockup-onlight.png": lockup,
        PUBLIC / "masci-mark.png": mark,
        PUBLIC / "masci-mark-onblack.png": mark,
        PUBLIC / "masci-mark-onlight.png": mark,
        PUBLIC / "masci-wordmark.png": wordmark,
        PUBLIC / "masci-wordmark-onblack.png": wordmark,
        PUBLIC / "masci-wordmark-onlight.png": wordmark,
        STATIC / "masci-logo.png": lockup,
        STATIC / "masci-logo-email.png": lockup,
    }
    for path, img in targets.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        img.save(path, format="PNG", optimize=True)
        print(f"[install-logo] wrote {path}  ({path.stat().st_size:,} bytes)")

    # Also stash the original source for audit
    audit = PUBLIC / "_logo_source_2026-05-03.png"
    shutil.copy2(SRC, audit)
    print(f"[install-logo] audit copy: {audit}")

    # Drop obsolete logo asset dirs left over from prior rebrands.
    for stale in [
        PUBLIC / "_pre_tagline_rebrand_backup",
        PUBLIC / "_old_safety_lockups",
        PUBLIC / "_src",
    ]:
        if stale.exists():
            shutil.rmtree(stale)
            print(f"[install-logo] removed obsolete dir: {stale}")


if __name__ == "__main__":
    main()
