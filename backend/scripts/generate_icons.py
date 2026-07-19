"""
Generate the MASCI icon set (favicons + PWA + Apple touch icons) using
Nano Banana, then resample to every standard size.

Output: /app/frontend/public/*.png + favicon.ico
"""
import asyncio
import base64
import os
from io import BytesIO
from pathlib import Path

from PIL import Image
from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage

load_dotenv("/app/backend/.env")

OUT = Path("/app/frontend/public")
MASTER = Path("/app/assets/source/icon_master_1024.png")

PROMPT = (
    "Generate ONE square 1024x1024 app icon for a heavy-civil construction "
    "operations platform called MASCI. \n\n"
    "Composition: dark slate-900 (#0f172a) square background. "
    "Centered on the canvas is a large, bold, industrial red letter M "
    "logo (#b91c1c). The M occupies about 70% of the canvas — left and "
    "right strokes go nearly edge-to-edge with comfortable safe padding "
    "all around. The M has sharp angular serifs at the top of the outer "
    "strokes, like a heavy-duty construction stencil. Crisp, geometric, "
    "razor-sharp edges. \n\n"
    "Critical: NO text, NO words, NO additional graphics, NO gradient, "
    "NO blueprint grid, NO caution stripe — just the solid red M on the "
    "dark slate-900 square. This is for an iOS/Android app icon and "
    "browser favicon — it must remain instantly readable at 16x16 px so "
    "the M shape must be unmistakable and bold. Match the aesthetic of "
    "the existing MASCI Operations Platform OG banner."
)

SIZES = [
    # (filename, size, maskable?)
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


def make_maskable(im: Image.Image, target: int) -> Image.Image:
    """
    Android PWA maskable icons must have content fit within the inner
    safe-zone circle (radius = 0.4 * size). Shrink the actual artwork to
    80% of the canvas, keep the slate background bleeding to the edge.
    """
    inner = int(target * 0.8)
    shrunk = im.resize((inner, inner), Image.LANCZOS)
    canvas = Image.new("RGB", (target, target), (15, 23, 42))  # slate-900
    offset = (target - inner) // 2
    canvas.paste(shrunk, (offset, offset))
    return canvas


async def main():
    api_key = os.getenv("EMERGENT_LLM_KEY")
    assert api_key, "EMERGENT_LLM_KEY missing"

    chat = (
        LlmChat(
            api_key=api_key,
            session_id="favicon-iter114",
            system_message=(
                "You are an icon designer. Output exactly ONE square app "
                "icon, no commentary."
            ),
        )
        .with_model("gemini", "gemini-3.1-flash-image-preview")
        .with_params(modalities=["image", "text"])
    )

    text, images = await chat.send_message_multimodal_response(
        UserMessage(text=PROMPT)
    )
    if not images:
        print(f"FAIL — no image returned. Text: {text[:200]}")
        return

    image_bytes = base64.b64decode(images[0]["data"])
    im = Image.open(BytesIO(image_bytes)).convert("RGB")
    print(f"Generated master {im.size} ({len(image_bytes):,} bytes raw)")

    # Force square 1024x1024
    if im.size != (1024, 1024):
        im = im.resize((1024, 1024), Image.LANCZOS)
    im.save(MASTER, format="PNG", optimize=True)
    print(f"  → master saved: {MASTER}")

    # Generate each size
    for fname, size, maskable in SIZES:
        if maskable:
            out = make_maskable(im, size)
        else:
            out = im.resize((size, size), Image.LANCZOS)
        out.save(OUT / fname, format="PNG", optimize=True)
        bytes_ = (OUT / fname).stat().st_size
        print(f"  → {fname:<32} {size}x{size}  {bytes_:>7,} bytes  "
              f"{'maskable' if maskable else ''}")

    # Generate multi-resolution favicon.ico (16, 32, 48)
    ico_sizes = [(16, 16), (32, 32), (48, 48)]
    ico_imgs = [im.resize(s, Image.LANCZOS) for s in ico_sizes]
    ico_imgs[0].save(
        OUT / "favicon.ico",
        format="ICO",
        sizes=ico_sizes,
        append_images=ico_imgs[1:],
    )
    print(f"  → favicon.ico (16,32,48)  "
          f"{(OUT / 'favicon.ico').stat().st_size:,} bytes")

    print("\nDone.")


if __name__ == "__main__":
    asyncio.run(main())
