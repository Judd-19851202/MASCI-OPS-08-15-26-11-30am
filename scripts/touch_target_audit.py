#!/usr/bin/env python3
"""
Touch-target Audit Helper · iter399 (Phase 12.6 · Lane B).

A lightweight doctrine guardrail that flags interactive elements
(buttons, links, anchors, click-bound elements) which do NOT carry an
explicit sizing class — the most common cause of undersized tap targets
in the field.

DOCTRINE
========
This is an *audit aid*, not an enforcement engine. It deliberately
over-reports rather than under-reports. Every hit must be reviewed by a
human against the Phase 12.6 mobile doctrine before any change is made:

  - one-thumb usage
  - sunlight readability
  - glove friendliness
  - low ambiguity
  - tap confidence
  - operational clarity

Targets that legitimately do not need explicit sizing (icon glyphs inside
larger parent buttons, links that wrap a sized child, modal scrim
overlays) MUST be kept — they are not friction.

USAGE
=====
    python3 /app/scripts/touch_target_audit.py            # default scope
    python3 /app/scripts/touch_target_audit.py --json     # machine-readable
    python3 /app/scripts/touch_target_audit.py --strict   # include all candidates
    python3 /app/scripts/touch_target_audit.py --paths a.jsx b.jsx

NOTE
====
Exit 0 always. Awareness tool, never breaks builds. Safe to wire into a
Makefile or CI without blocking. Follows the same philosophy as
`operator_vocabulary_scanner.py`.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

ROOT = Path("/app")

# ─────────────────────────────────────────────────────────────────────
# Default scope (iter399 · DLS mobile surfaces)
# ─────────────────────────────────────────────────────────────────────
DEFAULT_SCOPE = [
    "frontend/src/pages/DispatchBoard.jsx",
    "frontend/src/pages/driver/DriverShift.jsx",
    "frontend/src/pages/driver/DriverMagicLanding.jsx",
    "frontend/src/components/dispatch/AssignmentDrawer.jsx",
    "frontend/src/components/dispatch/DispatchLifecycleTile.jsx",
]

# Open-tag patterns we treat as "interactive" candidates.
# We intentionally include lowercase `button` and `a` because Tailwind
# patterns sometimes hand-roll them.
INTERACTIVE_OPEN_TAGS = re.compile(
    r"<(button|Button|a\s|Link\s|onClick=)",
)

# Tokens in className (or sized props) that count as "explicit sizing".
SIZE_HINTS = [
    r"\bh-\d+",         # h-9 h-10 h-11 …
    r"\bmin-h-\[",      # min-h-[80px]
    r"\bmin-h-\d",      # min-h-12
    r"\bpy-\d",         # py-2 py-3 …
    r"\bp-\d",          # p-3 p-4 …
    r"\bsize=\"",       # shadcn size="sm"/"lg"
    r"\bw-\d+\s+h-\d",  # square icon buttons w-10 h-10
    r"\bh-\[",          # h-[44px]
]
SIZE_HINT_RE = re.compile("|".join(SIZE_HINTS))

# Lines we deliberately skip.
SKIP_PATTERNS = [
    re.compile(r"^\s*//"),
    re.compile(r"^\s*\*"),
    re.compile(r"^\s*#"),
    re.compile(r"^\s*import\s"),
    re.compile(r"^\s*from\s+\S+\s+import"),
]


@dataclass
class Hit:
    path: str
    line_no: int
    snippet: str
    reason: str

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "line": self.line_no,
            "snippet": self.snippet.strip()[:200],
            "reason": self.reason,
        }


def _line_is_skippable(line: str) -> bool:
    return any(p.search(line) for p in SKIP_PATTERNS)


def _block_starting_at(lines: List[str], start: int, max_lines: int = 6) -> str:
    """Collapse a JSX opening block into a single string so we can
    inspect its className even if it wraps across lines."""
    end = min(start + max_lines, len(lines))
    return " ".join(lines[start:end])


def scan_file(path: Path, strict: bool) -> List[Hit]:
    if not path.exists():
        return []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    lines = text.splitlines()
    hits: List[Hit] = []
    for i, line in enumerate(lines):
        if _line_is_skippable(line):
            continue
        if not INTERACTIVE_OPEN_TAGS.search(line):
            continue
        block = _block_starting_at(lines, i, max_lines=6)
        # In non-strict mode, ignore lines that are clearly child wrappers
        # like <a href="…"><Truck/></a> — single-line links that wrap an
        # already-sized parent.
        if not SIZE_HINT_RE.search(block):
            # Heuristic: shadcn <Button> without an explicit `size=` and
            # without a sized className still renders default md ≈ 36 px.
            # That's below WCAG 44 px and the platform's 80 px driver
            # target, so we flag it.
            hits.append(Hit(
                path=str(path.relative_to(ROOT)),
                line_no=i + 1,
                snippet=line.strip()[:200],
                reason="no explicit h-/min-h-/py-/size= sizing on this interactive element",
            ))
            continue
        if strict:
            # In strict mode we additionally flag interactive elements
            # whose only sizing is `h-9` (36 px shadcn default) — under
            # WCAG 44 px.
            small = re.search(r"\bh-(\d+)\b", block)
            if small and int(small.group(1)) <= 9:
                hits.append(Hit(
                    path=str(path.relative_to(ROOT)),
                    line_no=i + 1,
                    snippet=line.strip()[:200],
                    reason=f"sizing h-{small.group(1)} below WCAG 44 px (≤ h-10)",
                ))
    return hits


def scan(paths: Iterable[str], strict: bool) -> List[Hit]:
    out: List[Hit] = []
    for rel in paths:
        full = (ROOT / rel) if not os.path.isabs(rel) else Path(rel)
        out.extend(scan_file(full, strict))
    return out


def render_markdown(hits: List[Hit]) -> str:
    if not hits:
        return ("# Touch-target Audit · clean\n\n"
                "No undersized interactive candidates in the scanned scope. ✅\n")
    files = sorted({h.path for h in hits})
    lines = [
        "# Touch-target Audit · candidates",
        "",
        f"Found **{len(hits)}** candidate interactive element(s) "
        f"across **{len(files)}** file(s).",
        "",
        "_This is an audit aid only. Review each hit in context. Children "
        "wrapped by sized parents, icon glyphs inside larger buttons, and "
        "modal scrim overlays are legitimate false positives — keep them._",
        "",
    ]
    by_file: dict[str, list[Hit]] = {}
    for h in hits:
        by_file.setdefault(h.path, []).append(h)
    for path in sorted(by_file):
        lines.append(f"## `{path}`")
        lines.append("")
        lines.append("| Line | Reason | Snippet |")
        lines.append("|---:|:---|:---|")
        for h in sorted(by_file[path], key=lambda x: x.line_no):
            snip = h.snippet.replace("|", "\\|")
            lines.append(f"| {h.line_no} | {h.reason} | `{snip}` |")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Phase 12.6 touch-target audit helper — "
            "doctrine guardrail, advisory only."
        ),
    )
    parser.add_argument("--paths", nargs="*", default=None,
                        help="Override scope with explicit file paths.")
    parser.add_argument("--strict", action="store_true",
                        help="Also flag h-9 (36 px) targets, below WCAG 44 px.")
    parser.add_argument("--json", dest="as_json", action="store_true",
                        help="Output JSON instead of markdown.")
    args = parser.parse_args()

    scope = args.paths if args.paths else DEFAULT_SCOPE
    hits = scan(scope, strict=args.strict)

    if args.as_json:
        sys.stdout.write(json.dumps([h.to_dict() for h in hits], indent=2))
        sys.stdout.write("\n")
    else:
        sys.stdout.write(render_markdown(hits))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
