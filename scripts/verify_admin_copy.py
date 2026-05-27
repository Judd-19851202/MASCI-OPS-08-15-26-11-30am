#!/usr/bin/env python3
"""verify_admin_copy.py — Phase IV-BETA.2 governance gate.

Scans frontend JSX/TS source for terminology and tone violations against
OPERATIONAL_VERBIAGE_DOCTRINE.md §IV (forbidden wording) and §VIII (state
canonicalization).

Does NOT scan:
  - Test files (they may quote forbidden phrases as test fixtures)
  - Backend code (server messages are governed elsewhere)
  - Markdown docs in /app/memory (this gate's own input)

Exit codes:
  0 — clean
  1 — violations found

Usage:
  python scripts/verify_admin_copy.py [path]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# Patterns that should NEVER appear in shipping UI copy. The full doctrine
# list lives in OPERATIONAL_VERBIAGE_DOCTRINE.md §IV; this is a focused
# starter set covering the highest-signal violators.
FORBIDDEN = {
    # Marketing slop
    r"\bSeamless(ly)?\b":          "marketing-slop · use a specific operational verb",
    r"\bEffortless(ly)?\b":        "marketing-slop · the platform does not promise ease",
    r"\bStreamlin(e|ed|ing)\b":    "marketing-slop · name the actual action",
    r"\bEmpower(s|ing|ed)?\b":     "marketing-slop · the platform is a tool, not motivation",
    r"\bUnlock\b":                 "marketing-slop · use 'enable' or specific verb",
    r"\bRevolutioniz(e|ing|ed)\b": "marketing-slop · forbidden anywhere",
    r"\bCutting-edge\b":           "marketing-slop · forbidden anywhere",
    r"\bAI-powered\b":             "vague brand claim · name the specific capability",
    # Robotic / AI-sounding
    r"\bI\s+can\s+help\s+you\b":   "AI-assistant tone · operational copy is not chat",
    r"\bFeel\s+free\s+to\b":       "AI-assistant tone",
    r"\bDon't\s+hesitate\b":       "AI-assistant tone",
    r"\bLet\s+me\s+know\s+if\b":   "AI-assistant tone",
    # Patronizing
    r"\bSimply\b":                 "patronizing adverb",
    r"\bEasily\b":                 "patronizing adverb",
    r"\bJust\s+(submit|click|tap|do)\b": "patronizing adverb · drop 'just'",
    # Casual
    r"\bOops\b":                   "casual error-tone · state the failure plainly",
    r"\bWhoops\b":                 "casual error-tone",
    r"\bUh\s*oh\b":                "casual error-tone",
    r"\bAwesome\b":                "casual celebratory tone",
    r"\bAmazing\b":                "casual celebratory tone",
    # Vague labels
    r'"Click\s+here"':             "vague CTA · name the noun",
    r'"Tap\s+here"':               "vague CTA · name the noun",
    r'"Manage\s+\w+"':             "vague verb · use Approve/Reject/Assign/Close/etc.",
    r'"More\s+info"':              "vague link · link to the doc with a noun",
    # State-name violations
    r'"In\s+Review"':              "non-canonical state · use 'Submitted' or 'In Progress' per domain",
}

INCLUDE_GLOBS = ["frontend/src/**/*.jsx", "frontend/src/**/*.js", "frontend/src/**/*.tsx"]
EXCLUDE_GLOBS = [
    "**/node_modules/**",
    "**/*.test.*",
    "**/__tests__/**",
    "**/storybook/**",
    # Don't grep the gate-input files (the doctrine itself names forbidden phrases)
    "frontend/src/components/admin/sidebar/domainMap.js",
    "frontend/src/components/pm/sidebar/domainMap.js",
]


def gather_files(root: Path) -> list[Path]:
    files: set[Path] = set()
    for pattern in INCLUDE_GLOBS:
        files.update(root.glob(pattern))
    out = []
    for f in sorted(files):
        rel = str(f.relative_to(root))
        if any(f.match(g) for g in EXCLUDE_GLOBS) or any(
            re.search(re.escape(g.replace("**/", "")), rel) for g in EXCLUDE_GLOBS
        ):
            continue
        out.append(f)
    return out


def lint_file(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, FileNotFoundError):
        return []
    violations: list[str] = []
    for pattern, why in FORBIDDEN.items():
        for m in re.finditer(pattern, text, flags=re.IGNORECASE):
            line = text[: m.start()].count("\n") + 1
            snippet = text[max(0, m.start() - 30): m.end() + 30].replace("\n", " ")
            violations.append(
                f"{path}:{line}: {m.group()!r} — {why}\n      … {snippet!r}"
            )
    return violations


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "/app").resolve()
    files = gather_files(root)
    print(f"verify_admin_copy: scanning {len(files)} files for terminology drift…")
    all_violations: list[str] = []
    for f in files:
        all_violations.extend(lint_file(f))

    if all_violations:
        print(f"\n❌ verify_admin_copy: {len(all_violations)} violation(s) found")
        for v in all_violations[:80]:
            print(f"  {v}")
        if len(all_violations) > 80:
            print(f"  … {len(all_violations) - 80} more violations omitted")
        return 1

    print("✅ verify_admin_copy: no terminology/tone violations found")
    return 0


if __name__ == "__main__":
    sys.exit(main())
