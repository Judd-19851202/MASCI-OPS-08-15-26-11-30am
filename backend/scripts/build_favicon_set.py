"""Generate the favicon + iOS/Android home-screen icon set for MASCI Hub.

Source: `/app/frontend/public/masci-mark.png` (the M-in-target ring, the
brand mark only — no wordmark). We resize and pad as needed for each
platform's expected size.

Outputs into `/app/frontend/public/`:
    favicon.ico                 (16+32+48 multi-resolution)
    favicon-16.png
    favicon-32.png
    favicon-48.png
    apple-touch-icon.png        (180x180, no transparency, dark bg)
    icon-192.png                (Android Chrome)
    icon-512.png                (Android Chrome)
    site.webmanifest            (PWA manifest)
    safari-pinned-tab.svg       (mono icon for Safari pinned tabs — skipped, simple)

Then patches `/app/frontend/public/index.html` with the proper <link> tags.
"""
from pathlib import Path
from PIL import Image

PUBLIC = Path("/app/frontend/public")
# Use the user's clean M-on-black icon as the source — it has a solid black
# bg already which renders perfectly as a home-screen icon at any size.
SRC = Path("/tmp/assets/new_m_icon.png")
FALLBACK = PUBLIC / "masci-mark.png"

# Apple touch icons should not be transparent — pad onto navy bg
NAVY = (15, 23, 42, 255)  # slate-900
WHITE = (255, 255, 255, 255)

if not SRC.exists():
    SRC = FALLBACK
    print(f"WARN: user icon missing, falling back to {SRC.name}")
if not SRC.exists():
    print(f"ERROR: no source icon"); raise SystemExit(1)

src = Image.open(SRC).convert("RGBA")
print(f"source: {SRC} ({src.size}, mode={src.mode})")


def square_padded(img: Image.Image, target: int, bg=None) -> Image.Image:
    """Square-crop or pad the image to target x target."""
    w, h = img.size
    side = max(w, h)
    canvas = Image.new("RGBA", (side, side), bg or (0, 0, 0, 0))
    canvas.paste(img, ((side - w) // 2, (side - h) // 2), img)
    return canvas.resize((target, target), Image.LANCZOS)


def with_bg(img: Image.Image, bg) -> Image.Image:
    """Flatten alpha onto a solid background (apple-touch-icon must not have alpha)."""
    out = Image.new("RGB", img.size, bg[:3])
    out.paste(img, mask=img.split()[3] if img.mode == "RGBA" else None)
    return out


# ---- Favicon PNGs (transparent) ----
for size in (16, 32, 48):
    out = square_padded(src, size)
    p = PUBLIC / f"favicon-{size}.png"
    out.save(p, "PNG")
    print(f"  wrote {p.name}")

# ---- favicon.ico (multi-resolution) ----
ico_path = PUBLIC / "favicon.ico"
src_for_ico = square_padded(src, 256)
src_for_ico.save(ico_path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
print(f"  wrote {ico_path.name}")

# ---- Apple touch icon (180x180, no alpha, navy backplate so it pops on home screen) ----
apple = square_padded(src, 180)
apple_solid = with_bg(apple, NAVY)
apple_path = PUBLIC / "apple-touch-icon.png"
apple_solid.save(apple_path, "PNG")
print(f"  wrote {apple_path.name}")

# Apple expects a few legacy sizes too
for size in (152, 167, 120):
    out = with_bg(square_padded(src, size), NAVY)
    p = PUBLIC / f"apple-touch-icon-{size}.png"
    out.save(p, "PNG")
    print(f"  wrote {p.name}")

# ---- Android Chrome icons ----
for size in (192, 512):
    out = with_bg(square_padded(src, size), NAVY)
    p = PUBLIC / f"icon-{size}.png"
    out.save(p, "PNG")
    print(f"  wrote {p.name}")

# Maskable icon (Android) — needs ~10% safe-area padding around the mark
for size in (192, 512):
    side = size
    canvas = Image.new("RGB", (side, side), NAVY[:3])
    inner = int(side * 0.78)  # 11% padding on each side = safe zone
    inner_img = square_padded(src, inner)
    inner_solid = Image.new("RGBA", (inner, inner), (0, 0, 0, 0))
    inner_solid.paste(inner_img, (0, 0), inner_img)
    paste_xy = ((side - inner) // 2, (side - inner) // 2)
    canvas.paste(inner_solid.convert("RGB"), paste_xy, inner_solid.split()[3])
    p = PUBLIC / f"icon-maskable-{size}.png"
    canvas.save(p, "PNG")
    print(f"  wrote {p.name}")

# ---- PWA manifest ----
manifest = {
    "name": "MASCI Hub",
    "short_name": "MASCI",
    "description": "MASCI Hub — Safety, Field, Projects, Admin. One place for every MASCI job.",
    "start_url": "/",
    "scope": "/",
    "display": "standalone",
    "orientation": "portrait",
    "background_color": "#0f172a",
    "theme_color": "#0f172a",
    "icons": [
        {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
        {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
        {"src": "/icon-maskable-192.png", "sizes": "192x192", "type": "image/png", "purpose": "maskable"},
        {"src": "/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
    ],
}
import json as _json
manifest_path = PUBLIC / "site.webmanifest"
manifest_path.write_text(_json.dumps(manifest, indent=2))
print(f"  wrote {manifest_path.name}")

print("done.")
