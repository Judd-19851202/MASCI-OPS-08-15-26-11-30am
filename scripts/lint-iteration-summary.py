#!/usr/bin/env python3
"""scripts/lint-iteration-summary.py — iter439 · Item K.

Enforces the iter436 'Preview ≠ Production' discipline rule by scanning
the most recent iteration block in `/app/memory/PRD.md` for the
required environment-labelling markers.

A passing iteration block MUST contain either:
  - the literal string  "Preview verified"      (case-insensitive)
  - the literal string  "Production verified"   (case-insensitive)
  - the literal string  "STANDING OPERATOR ACTIONS"
    (re-stated when production is still outstanding)

When you call `finish`, run this script first.  Exit 0 = green to ship.
Exit 1 = the discipline marker is missing and you must add it.

Usage:
    python3 scripts/lint-iteration-summary.py
    python3 scripts/lint-iteration-summary.py --path /app/memory/PRD.md

This is a tiny defensive utility · NOT a build gate · NOT a CI step ·
just a guardrail the agent runs before claiming the iteration done.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


DEFAULT_PRD = "/app/memory/PRD.md"
RE_ITER_HEADER = re.compile(r"^##\s+\d{4}-\d{2}-\d{2}.*iter\d+", re.MULTILINE)
REQUIRED_MARKERS = {
    "preview_or_production_label": re.compile(
        r"(preview verified|production verified)", re.IGNORECASE,
    ),
    "standing_operator_block_referenced": re.compile(
        r"standing operator actions", re.IGNORECASE,
    ),
}


def latest_iteration_block(text: str) -> str | None:
    matches = list(RE_ITER_HEADER.finditer(text))
    if not matches:
        return None
    start = matches[0].start()
    end = matches[1].start() if len(matches) > 1 else len(text)
    return text[start:end]


def lint(path: str) -> int:
    p = Path(path)
    if not p.exists():
        print(f"❌ PRD file not found at {path}", file=sys.stderr)
        return 1
    body = p.read_text(encoding="utf-8")
    block = latest_iteration_block(body)
    if not block:
        print(
            "❌ No iteration block (## YYYY-MM-DD — iterNNN ...) found at top of PRD.md.",
            file=sys.stderr,
        )
        return 1
    missing: list[str] = []
    for name, pattern in REQUIRED_MARKERS.items():
        if not pattern.search(block):
            missing.append(name)
    if missing:
        print(
            "❌ Latest iteration block is missing the following discipline markers:",
            file=sys.stderr,
        )
        for m in missing:
            print(f"    - {m}", file=sys.stderr)
        print(
            "\nFix: add an explicit 'Preview verified ✅' (or 'Production verified ✅') "
            "label in the block, and a 🔴 STANDING OPERATOR ACTIONS section if any "
            "production-side action is still outstanding.",
            file=sys.stderr,
        )
        return 1
    print("✅ Latest iteration block passes the Preview ≠ Production discipline lint.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--path", default=DEFAULT_PRD,
                    help=f"Path to PRD.md (default: {DEFAULT_PRD})")
    args = ap.parse_args()
    return lint(args.path)


if __name__ == "__main__":
    sys.exit(main())
