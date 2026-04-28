"""One-off logo generator — edits each MASCI lockup variant to say HUB instead of SAFETY.

Usage:
    cd /app/backend && python scripts/generate_hub_logos.py

Produces:
    /app/frontend/public/masci-full-lockup.png          (dark variant, rebranded)
    /app/frontend/public/masci-full-lockup-onblack.png
    /app/frontend/public/masci-full-lockup-onlight.png

Originals are copied to /app/frontend/public/_old_safety_lockups/ first so we
never lose the source art.
"""
import asyncio
import base64
import os
import shutil
import sys
import uuid
from pathlib import Path

from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent

load_dotenv()

PUBLIC_DIR = Path("/app/frontend/public")
BACKUP_DIR = PUBLIC_DIR / "_old_safety_lockups"
MODEL = "gemini-3.1-flash-image-preview"

VARIANTS = [
    "masci-full-lockup.png",
    "masci-full-lockup-onblack.png",
    "masci-full-lockup-onlight.png",
]

PROMPT = (
    "Take this logo image and make ONE precise change: replace the word "
    "\"SAFETY\" with the word \"HUB\" wherever it appears. Do NOT change "
    "anything else. Keep the exact same: the circular compass icon with "
    "the red M and white checkmark, the red \"MASCI\" wordmark above, the "
    "font/weight/letter-spacing of the replaced word (HUB must be styled "
    "identically to how SAFETY was styled — same font, same size, same "
    "white color, same letter spacing), the horizontal gray divider lines, "
    "the \"ACCOUNTABILITY | DISCIPLINE | EXECUTION\" subtext, the tagline "
    "\"NO SHORTCUTS · NO EXCEPTIONS.\" at the bottom with the short red "
    "horizontal lines flanking it, and the background color. The overall "
    "composition, padding, and proportions must match the original exactly."
)


async def edit_variant(src_path: Path, dst_path: Path) -> None:
    with open(src_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")

    api_key = os.getenv("EMERGENT_LLM_KEY")
    if not api_key:
        print("ERROR: EMERGENT_LLM_KEY missing", file=sys.stderr)
        sys.exit(1)

    chat = LlmChat(
        api_key=api_key,
        session_id=f"masci-logo-{uuid.uuid4()}",
        system_message="You are an expert brand designer. Make surgical edits to logos.",
    )
    chat.with_model("gemini", MODEL).with_params(modalities=["image", "text"])

    msg = UserMessage(text=PROMPT, file_contents=[ImageContent(b64)])
    text, images = await chat.send_message_multimodal_response(msg)
    print(f"[{src_path.name}] model text: {(text or '').strip()[:120]}")

    if not images:
        print(f"[{src_path.name}] ERROR: no images returned", file=sys.stderr)
        return
    img = images[0]
    out_bytes = base64.b64decode(img["data"])
    dst_path.write_bytes(out_bytes)
    print(f"[{src_path.name}] wrote {dst_path} ({len(out_bytes)/1024:.1f} KB)")


async def main():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    # Back up originals once
    for name in VARIANTS:
        src = PUBLIC_DIR / name
        bak = BACKUP_DIR / name
        if src.exists() and not bak.exists():
            shutil.copy2(src, bak)
            print(f"backed up {src.name} -> {bak}")

    for name in VARIANTS:
        src = BACKUP_DIR / name  # always edit from the original
        dst = PUBLIC_DIR / name
        if not src.exists():
            print(f"WARN: missing source {src}")
            continue
        await edit_variant(src, dst)


if __name__ == "__main__":
    asyncio.run(main())
