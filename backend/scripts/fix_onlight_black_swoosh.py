"""Regenerate `masci-full-lockup-onlight.png` so the swoosh through the M
is BLACK (not white). Per user feedback the white swoosh disappears against
the red M at small sizes, making the icon read as a solid red blob.
"""
import asyncio
import base64
import os
import sys
import uuid
from pathlib import Path

from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent

load_dotenv()

PUBLIC_DIR = Path("/app/frontend/public")
M_ICON = Path("/tmp/assets/new_m_icon.png")
ONBLACK = PUBLIC_DIR / "masci-full-lockup-onblack.png"
OUT = PUBLIC_DIR / "masci-full-lockup-onlight.png"

PROMPT = (
    "Build a NEW MASCI HUB lockup designed for WHITE backgrounds. Use "
    "Image 2 ONLY for composition (icon left, wordmark right, divider, "
    "tagline at bottom, rounded-rect frame).\n\n"
    "MOST IMPORTANT — the M icon:\n"
    "• Big bold red serif letter M (deep red, same red as Image 1).\n"
    "• A SMOOTH CURVED BLACK SWOOSH cuts through the M. The swoosh is "
    "  BLACK, not white, not red. It starts wider near the bottom-left "
    "  inside the M and tapers to a sharp point at the upper right. It is "
    "  one continuous curved line. NOT a checkmark with two straight "
    "  legs. The black swoosh creates strong visual contrast against the "
    "  red M so the shape reads clearly even at small sizes.\n"
    "• That M-with-black-swoosh sits inside a circular target/crosshair "
    "  ring (dark grey outer ring, thin red inner ring, four short "
    "  N/S/E/W crosshair points extending outward).\n\n"
    "Wordmark, two lines stacked to the right of the icon:\n"
    "  Line 1: 'MASCI' in big bold red serif (same red as the M).\n"
    "  Line 2: 'HUB' in big bold DARK NAVY #0f172a (so it reads on white).\n\n"
    "Below the wordmark: thin medium-grey horizontal divider line.\n"
    "Below the divider, ONE tagline row in dark navy #0f172a all-caps:\n"
    "  'ACCOUNTABILITY | ADAPT | OVERCOME'\n"
    "with thin red vertical bars between words.\n\n"
    "Rounded-rectangle outline frame in medium grey around the whole thing.\n"
    "Solid pure WHITE background fill (#FFFFFF) — NOT transparent.\n\n"
    "ABSOLUTELY NO 'NO SHORTCUTS', 'NO EXCEPTIONS', 'DISCIPLINE', or "
    "'EXECUTION' anywhere. Spell-check: must read 'MASCI HUB' and "
    "'ACCOUNTABILITY | ADAPT | OVERCOME'. Output a wide PNG ~2000x1000."
)


async def main():
    api_key = os.getenv("EMERGENT_LLM_KEY")
    if not api_key:
        print("ERROR: EMERGENT_LLM_KEY missing", file=sys.stderr); sys.exit(1)

    chat = LlmChat(
        api_key=api_key, session_id=f"black-swoosh-{uuid.uuid4()}",
        system_message="You are a precise brand designer. Follow specifications exactly.",
    )
    chat.with_model("gemini", "gemini-3.1-flash-image-preview").with_params(modalities=["image", "text"])

    refs = [
        ImageContent(base64.b64encode(M_ICON.read_bytes()).decode("utf-8")),
        ImageContent(base64.b64encode(ONBLACK.read_bytes()).decode("utf-8")),
    ]
    text, images = await chat.send_message_multimodal_response(
        UserMessage(text=PROMPT, file_contents=refs),
    )
    print(f"text: {(text or '').strip()[:120]}")
    if not images:
        print("no image returned", file=sys.stderr); sys.exit(1)
    OUT.write_bytes(base64.b64decode(images[0]["data"]))
    print(f"saved {OUT}")


if __name__ == "__main__":
    asyncio.run(main())
