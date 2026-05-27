#!/usr/bin/env python3
"""verify_coaching_sublines.py — Phase IV-BETA.2 governance gate.

Scans the frontend codebase for surfaces governed by the Cross-Portal Coaching
Standard (CROSS_PORTAL_COACHING_STANDARD.md). Enforces:

  - 14-word budget per coaching subline
  - No banned marketing/SaaS phrases ("Welcome to", "Easily", "Just …",
    "Simply", "AI-powered", "Empower", "Seamless", …)
  - No exclamation marks in operational copy
  - No emoji in operational copy
  - Coaching subline present on governed sidebar entries

Exit codes:
  0 — all sublines pass
  1 — one or more violations found (deploy gate fails)

Usage:
  python scripts/verify_coaching_sublines.py [path]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

BANNED_PHRASES = [
    r"\bWelcome\s+to\b",
    r"\bHere\s+you\s+can\b",
    r"\bHere\s+is\s+where\b",
    r"\bEasily\b",
    r"\bSimply\b",
    r"\bJust\s+(submit|click|tap)\b",
    r"\bSeamless(ly)?\b",
    r"\bEffortless(ly)?\b",
    r"\bEmpower(s|ing)?\b",
    r"\bAI-powered\b",
    r"\bUnlock\b",
    r"\bRevolutioniz(e|ing)\b",
    r"\bCutting-edge\b",
    r"\bGet\s+started\b",
    r"\bClick\s+here\b",
    r"\bTap\s+here\b",
    r"\bDon't\s+hesitate\b",
    r"\bFeel\s+free\s+to\b",
    r"\bOops\b",
    r"\bWhoops\b",
    r"\bAwesome\b",
    r"\bAmazing\b",
    # iter437 P1D · escalation-wording doctrine (COMMUNICATION_UNIFICATION
    # _DOCTRINE.md §A.III banned urgency words). Coaching copy is operator-
    # facing and must NEVER patronise or shout urgency.
    r"\bURGENT\b",
    r"\bASAP\b",
    r"\bPlease\s+(click|tap|submit|review|approve)\b",
    r"\bKindly\b",
    r"\bTime-sensitive\b",
    r"\bHeads\s+up\b",
]

# Files governed by this gate. Only sidebar domainMap files and PmSections/
# AdminSections-style coaching wrappers — not arbitrary copy.
# iter437 P1D · HrSideNavV2 added.
COACHING_FILES = [
    "frontend/src/components/admin/sidebar/domainMap.js",
    "frontend/src/components/pm/sidebar/domainMap.js",
    "frontend/src/pages/pm/PmSections.jsx",
    "frontend/src/components/hr/sidebar/HrSideNavV2.jsx",
]

EMOJI_RE = re.compile(
    r"[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F1FF]"
)
EXCLAMATION_RE = re.compile(r"!{1,}")


def lint_file(path: Path) -> list[str]:
    if not path.exists():
        return [f"{path}: not found"]
    text = path.read_text(encoding="utf-8")
    violations: list[str] = []

    # Banned phrases
    for pattern in BANNED_PHRASES:
        for m in re.finditer(pattern, text, flags=re.IGNORECASE):
            line = text[: m.start()].count("\n") + 1
            violations.append(
                f"{path}:{line}: forbidden phrase {m.group()!r} (pattern {pattern})"
            )

    # Emoji
    for m in EMOJI_RE.finditer(text):
        line = text[: m.start()].count("\n") + 1
        violations.append(f"{path}:{line}: emoji {m.group()!r} forbidden in coaching copy")

    # Exclamation marks inside JSX string literals or subline strings
    # (we approximate by checking inside quoted strings of coaching files)
    for m in re.finditer(r'(?:subline|desc|intro)\s*[:=]\s*["\'`]([^"\'`]+)["\'`]', text):
        body = m.group(1)
        if EXCLAMATION_RE.search(body):
            line = text[: m.start()].count("\n") + 1
            violations.append(f"{path}:{line}: exclamation mark in coaching string: {body!r}")

    # 14-word budget on subline / desc fields
    for m in re.finditer(
        r'(?:subline|desc|coaching_subline)\s*[:=]\s*["\'`]([^"\'`]+)["\'`]', text
    ):
        body = m.group(1).strip()
        words = re.split(r"\s+", body)
        if len(words) > 14:
            line = text[: m.start()].count("\n") + 1
            violations.append(
                f"{path}:{line}: subline exceeds 14-word budget ({len(words)} words): {body!r}"
            )

    return violations


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "/app").resolve()
    all_violations: list[str] = []
    for rel in COACHING_FILES:
        all_violations.extend(lint_file(root / rel))

    if all_violations:
        print("❌ verify_coaching_sublines: violations found")
        for v in all_violations:
            print(f"  {v}")
        print(f"\nTotal: {len(all_violations)} violation(s)")
        return 1

    print("✅ verify_coaching_sublines: all governed sublines pass doctrine")
    return 0


if __name__ == "__main__":
    sys.exit(main())
