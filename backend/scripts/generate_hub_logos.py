"""Regenerate MASCI HUB logo lockups using the user-supplied M icon.

The user has asked for a new logo with:
  - The red M + white swoosh icon they uploaded (no more M+checkmark)
  - Kept inside the existing target/crosshair ring
  - "MASCI HUB" wordmark to the right
  - One tagline: "ACCOUNTABILITY · ADAPT · OVERCOME"
    (replacing the old "NO SHORTCUTS · NO EXCEPTIONS" AND the old
    ACCOUNTABILITY | DISCIPLINE | EXECUTION values row)
  - Transparent background so the dark navy site header shows through

Produces:
    masci-full-lockup.png         (transparent bg, for dark headers)
    masci-full-lockup-onblack.png (black bg, print/PDFs)
    masci-full-lockup-onlight.png (white bg, light surfaces)
    masci-mark.png                (just the target+M icon, transparent bg)
    masci-mark-onblack.png
    masci-mark-onlight.png
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
NEW_M_ICON = Path("/tmp/assets/new_m_icon.png")

MODEL = "gemini-3.1-flash-image-preview"

# ------ Build blocks ---------------------------------------------------------

def encode(p: Path) -> str:
    with open(p, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


async def gen(prompt: str, refs: list[Path], out_path: Path, session: str) -> None:
    api_key = os.getenv("EMERGENT_LLM_KEY")
    if not api_key:
        print("ERROR: EMERGENT_LLM_KEY missing", file=sys.stderr)
        sys.exit(1)
    chat = LlmChat(
        api_key=api_key, session_id=session,
        system_message="You are an expert brand designer producing clean, production-ready vector-style logos.",
    )
    chat.with_model("gemini", MODEL).with_params(modalities=["image", "text"])
    contents = [ImageContent(encode(p)) for p in refs]
    text, images = await chat.send_message_multimodal_response(
        UserMessage(text=prompt, file_contents=contents),
    )
    print(f"[{out_path.name}] text: {(text or '').strip()[:100]}")
    if not images:
        print(f"[{out_path.name}] ERROR: no image returned", file=sys.stderr)
        return
    out_path.write_bytes(base64.b64decode(images[0]["data"]))
    print(f"[{out_path.name}] saved ({len(images[0]['data'])//1024} KB b64)")


# ------ Main -----------------------------------------------------------------

async def main():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    if not NEW_M_ICON.exists():
        print(f"missing {NEW_M_ICON} — run the curl step first", file=sys.stderr)
        sys.exit(1)

    # Reference: the user's new M icon + the old lockup (for composition reference)
    old_lockup = BACKUP_DIR / "masci-full-lockup.png"
    if not old_lockup.exists():
        old_lockup = PUBLIC_DIR / "masci-full-lockup.png"

    # ---------- MARK (just icon: target ring with M inside) ----------
    mark_prompt = (
        "I am giving you two reference images. Image 1 is the MASCI 'M' icon "
        "(bold red serif M with a white dynamic swoosh cutting through it). "
        "Image 2 is a MASCI logo for visual style reference — look at the "
        "circular target/crosshair ring around the icon.\n\n"
        "Create ONE new logo MARK (icon only, no wordmark, no text):\n"
        "• Place the RED M WITH WHITE SWOOSH from Image 1 in the center.\n"
        "• Around it, draw the SAME grey/red target ring with four compass "
        "  crosshair points extending outward that you see in Image 2.\n"
        "• The ring should be the same outer circle style — grey outer ring "
        "  with a thin red inner ring.\n"
        "• Background must be pure TRANSPARENT (alpha channel) so the icon "
        "  sits cleanly on any background.\n"
        "• Output a square 1024x1024 PNG. High quality, crisp edges, no "
        "  jpeg artifacts.\n"
        "Do NOT include any wordmark, MASCI text, or tagline. Just the mark."
    )
    await gen(mark_prompt, [NEW_M_ICON, old_lockup], PUBLIC_DIR / "masci-mark.png", "masci-mark-transparent")
    # Variant with explicit light-bg padding (for admin hub on white)
    mark_light_prompt = mark_prompt.replace(
        "Background must be pure TRANSPARENT (alpha channel) so the icon sits cleanly on any background.",
        "Background must be pure WHITE so the icon reads on light surfaces.",
    )
    await gen(mark_light_prompt, [NEW_M_ICON, old_lockup], PUBLIC_DIR / "masci-mark-onlight.png", "masci-mark-light")
    mark_black_prompt = mark_prompt.replace(
        "Background must be pure TRANSPARENT (alpha channel) so the icon sits cleanly on any background.",
        "Background must be pure BLACK so the icon reads on dark surfaces.",
    )
    await gen(mark_black_prompt, [NEW_M_ICON, old_lockup], PUBLIC_DIR / "masci-mark-onblack.png", "masci-mark-black")

    # ---------- FULL LOCKUP ----------
    # Tagline REPLACES both old rows with a single "ACCOUNTABILITY · ADAPT · OVERCOME"
    lockup_prompt = (
        "I am giving you two reference images. Image 1 is the MASCI 'M' icon "
        "(bold red serif M with a white dynamic swoosh cutting through it). "
        "Image 2 is the previous MASCI SAFETY logo lockup — use it ONLY for "
        "layout/typography/composition reference. You will produce a new "
        "updated lockup.\n\n"
        "DESIGN SPECIFICATIONS for the new lockup:\n"
        "• LEFT SIDE — a circular target mark: the RED M WITH WHITE SWOOSH "
        "  from Image 1, surrounded by a grey target ring with a thin red "
        "  inner ring, and four short crosshair points extending N/S/E/W. "
        "  Match the ring style from Image 2's icon.\n"
        "• RIGHT SIDE — the wordmark in two lines:\n"
        "    Line 1:  MASCI    (bold red serif wordmark, all caps, LARGE, "
        "                       exactly the same font/size/weight as in Image 2)\n"
        "    Line 2:  HUB      (WHITE filled letters, all caps, bold, same "
        "                       typography family as MASCI, slightly smaller, "
        "                       with open letter spacing — matches how "
        "                       SAFETY appeared in Image 2)\n"
        "• UNDER the wordmark, a single thin grey horizontal divider line.\n"
        "• UNDER that divider, ONE tagline row (and only one):\n"
        "    ACCOUNTABILITY | ADAPT | OVERCOME\n"
        "  Styled with light grey/white all-caps text separated by thin red "
        "  vertical bars. The same visual treatment Image 2 used for its "
        "  'ACCOUNTABILITY | DISCIPLINE | EXECUTION' row.\n"
        "• DO NOT include the old 'NO SHORTCUTS · NO EXCEPTIONS' tagline. "
        "  DO NOT include the old 'DISCIPLINE | EXECUTION' values. Only the "
        "  single ACCOUNTABILITY | ADAPT | OVERCOME row appears.\n"
        "• A thin rounded rectangle outline frames the whole lockup like "
        "  Image 2.\n"
        "• Background must be pure TRANSPARENT (alpha channel) so the "
        "  lockup sits cleanly on the app's dark navy header.\n"
        "• The 'MASCI' red must be the exact same deep red as Image 1 / "
        "  Image 2. The white swoosh stays pure white.\n"
        "• Output a wide aspect ratio PNG (roughly 2:1 — about 2000x1000).\n"
        "• CRITICAL: the logo text must literally read 'MASCI HUB' with "
        "  HUB filled in WHITE (not outlined). Double-check spelling before "
        "  returning.\n"
    )
    await gen(lockup_prompt, [NEW_M_ICON, old_lockup], PUBLIC_DIR / "masci-full-lockup.png", "lockup-transparent")

    onblack_prompt = lockup_prompt.replace(
        "Background must be pure TRANSPARENT (alpha channel) so the lockup sits cleanly on the app's dark navy header.",
        "Background must be pure BLACK — the lockup will print on black collateral. Red MASCI and white HUB must pop against black.",
    )
    await gen(onblack_prompt, [NEW_M_ICON, old_lockup], PUBLIC_DIR / "masci-full-lockup-onblack.png", "lockup-onblack")

    onlight_prompt = lockup_prompt.replace(
        "Background must be pure TRANSPARENT (alpha channel) so the lockup sits cleanly on the app's dark navy header.",
        "Background must be pure WHITE — the lockup will print on light collateral. The word HUB must be dark navy blue filled (NOT white — swap to dark navy so it reads on white). MASCI stays red.",
    )
    await gen(onlight_prompt, [NEW_M_ICON, old_lockup], PUBLIC_DIR / "masci-full-lockup-onlight.png", "lockup-onlight")


if __name__ == "__main__":
    asyncio.run(main())
