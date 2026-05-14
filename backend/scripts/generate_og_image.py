"""
One-shot OG image generator for the MASCI Operations Platform.

Output: /app/frontend/public/og-image.png (1200×630)
Run:    python /app/backend/scripts/generate_og_image.py
"""
import asyncio
import os
import base64
from pathlib import Path

from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage

load_dotenv("/app/backend/.env")

PROMPT = (
    "Sharp, premium OpenGraph banner image for a heavy-civil construction "
    "operations platform called MASCI. CRITICAL: 1200x630 aspect ratio, "
    "landscape, designed for iMessage / Slack / LinkedIn link previews. "
    "\n\n"
    "Composition: dark slate-900 background color (#0f172a) covering the "
    "entire canvas. Faint blueprint grid pattern overlay in subtle blue "
    "lines, very low opacity (~8%), so it reads as 'engineering drawing' "
    "but doesn't compete with the foreground. "
    "\n\n"
    "Left third of the image: a large, bold geometric red letter M logo, "
    "centered vertically, painted in deep red (#b91c1c). The M should be "
    "industrial, angular, with sharp serifs at the top of the outer "
    "strokes — heavy-duty construction feel, NOT decorative. About 380px "
    "tall, takes up the left ~30% of the canvas. "
    "\n\n"
    "Center-right two-thirds: two stacked lines of text, left-aligned, "
    "vertically centered next to the M. "
    "Line 1 (large): 'MASCI OPERATIONS PLATFORM' in clean white industrial "
    "sans-serif, all caps, ~72pt, wide tracking, font weight 900. "
    "Line 2 (smaller, below): 'Run every job. Control every detail. "
    "Protect everything.' in slate-300 color (#cbd5e1), ~32pt, "
    "medium weight, sentence case. "
    "\n\n"
    "Bottom edge: a thin caution stripe band ~16px tall stretching full "
    "width — diagonal alternating red (#b91c1c) and black (#0f172a) bars "
    "at 45 degrees, like a construction warning tape. "
    "\n\n"
    "Style: looks like it belongs on a Bechtel or Kiewit landing page. "
    "Crisp, professional, no AI-slop pastel gradients, NO purple, NO "
    "abstract blobs, NO fake people. High contrast for small-thumbnail "
    "readability. Razor-sharp typography. Premium B2B SaaS aesthetic."
)


async def main():
    api_key = os.getenv("EMERGENT_LLM_KEY")
    assert api_key, "EMERGENT_LLM_KEY missing from /app/backend/.env"
    chat = (
        LlmChat(
            api_key=api_key,
            session_id="og-image-iter112",
            system_message=(
                "You are an expert graphic designer producing a single "
                "static OpenGraph banner. Output exactly ONE image, no "
                "commentary."
            ),
        )
        .with_model("gemini", "gemini-3.1-flash-image-preview")
        .with_params(modalities=["image", "text"])
    )

    msg = UserMessage(text=PROMPT)
    text, images = await chat.send_message_multimodal_response(msg)

    if not images:
        print(f"FAIL — no image returned. Text response: {text[:200]}")
        return

    out_path = Path("/app/frontend/public/og-image.png")
    image_bytes = base64.b64decode(images[0]["data"])
    out_path.write_bytes(image_bytes)
    print(f"OK — wrote {len(image_bytes):,} bytes → {out_path}")
    print(f"Model returned {len(images)} image(s); mime: {images[0]['mime_type']}")


if __name__ == "__main__":
    asyncio.run(main())
