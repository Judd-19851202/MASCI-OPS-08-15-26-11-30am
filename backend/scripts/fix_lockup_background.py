"""Regenerate ONLY the main `masci-full-lockup.png` with a transparent/dark
background so it sits cleanly on the app's dark navy site header.

The Apr 28 first pass produced a silver gradient backplate that clashes with
the navy header. This fix asks the model for a transparent or fully dark-navy
backplate matching slate-900 (#0f172a).
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
OUT = PUBLIC_DIR / "masci-full-lockup.png"
REF = PUBLIC_DIR / "masci-full-lockup-onblack.png"  # the on-black variant we just made
M_REF = Path("/tmp/assets/new_m_icon.png")

PROMPT = (
    "Take this MASCI HUB logo (Image 1) and produce a new version with the "
    "background replaced. KEEP every element of the logo identical: the "
    "circular target/crosshair icon on the left with the red M and white "
    "swoosh inside, the bold red 'MASCI' wordmark, the bold white 'HUB' "
    "wordmark below, the thin grey divider line, the "
    "'ACCOUNTABILITY | ADAPT | OVERCOME' tagline row, the rounded rectangle "
    "outline frame, and ALL typography/colors/positions exactly the same.\n\n"
    "ONLY change the background fill: replace whatever gradient or backplate "
    "is currently behind the elements with a solid dark navy color matching "
    "hex #0f172a (slate-900). The whole lockup should look like it was "
    "designed natively for a dark navy header. The rounded rectangle outline "
    "frame stays. The grey ring around the M-icon stays. Just the inside "
    "fill of the lockup changes from silver/gradient to solid #0f172a.\n\n"
    "Output a wide PNG ~2000x1000."
)


async def main():
    api_key = os.getenv("EMERGENT_LLM_KEY")
    if not api_key:
        print("ERROR: EMERGENT_LLM_KEY missing", file=sys.stderr); sys.exit(1)
    if not REF.exists():
        print(f"missing {REF}", file=sys.stderr); sys.exit(1)

    chat = LlmChat(
        api_key=api_key, session_id=f"darkfix-{uuid.uuid4()}",
        system_message="You are an expert brand designer making minimal surgical edits to logos.",
    )
    chat.with_model("gemini", "gemini-3.1-flash-image-preview").with_params(modalities=["image", "text"])

    with open(REF, "rb") as f:
        ref_b64 = base64.b64encode(f.read()).decode("utf-8")

    msg = UserMessage(
        text=PROMPT,
        file_contents=[ImageContent(ref_b64)],
    )
    text, images = await chat.send_message_multimodal_response(msg)
    print(f"text: {(text or '').strip()[:120]}")
    if not images:
        print("no image returned", file=sys.stderr); sys.exit(1)
    OUT.write_bytes(base64.b64decode(images[0]["data"]))
    print(f"saved {OUT}")


if __name__ == "__main__":
    asyncio.run(main())
