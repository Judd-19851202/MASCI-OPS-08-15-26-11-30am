"""Fix the `masci-full-lockup-onlight.png` so it renders properly on
white surfaces (cheat sheet, posters, light cards).

Issues from the prior pass:
  1. Background came back transparent (checker pattern visible on white card)
  2. "HUB" text was white on a white background (invisible)
  3. Icon shows M with a clean checkmark, not the user's M-with-swoosh

This script asks the model for an explicit WHITE solid background and
DARK NAVY filled "HUB" so it reads on light surfaces.  It also feeds the
user's M icon as the primary reference so the curved-swoosh shape is
preserved, not turned into a sharp checkmark.
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
ONBLACK = PUBLIC_DIR / "masci-full-lockup-onblack.png"  # composition reference
OUT = PUBLIC_DIR / "masci-full-lockup-onlight.png"

PROMPT = (
    "I am giving you TWO reference images.\n\n"
    "Image 1 = the MASCI 'M' icon. CRITICAL: study it carefully. The white "
    "shape inside the red M is a SMOOTH CURVED SWOOSH ARC, not a "
    "checkmark. The swoosh starts wide at the bottom-left of the M, "
    "curves upward and to the right, and tapers to a sharp point at the "
    "upper right. It is one continuous curved line. DO NOT draw it as a "
    "checkmark with two straight legs meeting at an angle. Replicate the "
    "smooth curved arc exactly.\n\n"
    "Image 2 = the existing MASCI HUB lockup on black. Use it ONLY for "
    "composition reference (icon position on left, wordmark on right, "
    "divider line, tagline row at bottom, rounded rectangle outline frame).\n\n"
    "Build a NEW lockup designed for WHITE backgrounds:\n"
    "• Solid pure WHITE background fill (#FFFFFF). NOT transparent. NOT "
    "  silver-gradient. Pure flat white inside the rounded rectangle frame.\n"
    "• Left side: target/crosshair ring (dark grey #475569 outer ring, "
    "  thin red inner ring) with the M-icon from Image 1 inside. Keep the "
    "  M as RED with the WHITE CURVED SWOOSH from Image 1.\n"
    "• Right side wordmark, two lines:\n"
    "    Line 1: 'MASCI' — bold red serif (same red as the M), large.\n"
    "    Line 2: 'HUB'   — bold dark navy #0f172a (slate-900). NOT white! "
    "                       NOT light grey! It must read clearly on white. "
    "                       Same font family as MASCI, slightly smaller, "
    "                       open letter spacing.\n"
    "• Single thin medium-grey horizontal divider beneath the wordmark.\n"
    "• Single tagline row beneath the divider:\n"
    "    'ACCOUNTABILITY | ADAPT | OVERCOME'\n"
    "  in DARK NAVY #0f172a all-caps, separated by thin red vertical bars.\n"
    "• A thin rounded-rectangle outline frame around the whole lockup, in "
    "  medium grey.\n"
    "• ABSOLUTELY NO 'NO SHORTCUTS' or 'NO EXCEPTIONS' or 'DISCIPLINE' or "
    "  'EXECUTION' text anywhere. Only the single ACCOUNTABILITY | ADAPT | "
    "  OVERCOME tagline.\n"
    "• Output a wide PNG roughly 2000x1000.\n"
    "• Spell-check the output: it must literally say 'MASCI HUB' and "
    "  'ACCOUNTABILITY | ADAPT | OVERCOME'."
)


async def main():
    api_key = os.getenv("EMERGENT_LLM_KEY")
    if not api_key:
        print("ERROR: EMERGENT_LLM_KEY missing", file=sys.stderr); sys.exit(1)
    for p in (M_ICON, ONBLACK):
        if not p.exists():
            print(f"missing {p}", file=sys.stderr); sys.exit(1)

    chat = LlmChat(
        api_key=api_key, session_id=f"onlight-{uuid.uuid4()}",
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
