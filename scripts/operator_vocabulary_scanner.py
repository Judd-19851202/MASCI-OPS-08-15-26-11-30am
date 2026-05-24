#!/usr/bin/env python3
"""
Operator Vocabulary Scanner · iter398 (Phase 12.5 · Lane E).

A lightweight audit guardrail that flags engineering / ERP / surveillance
vocabulary anywhere it might leak into operator-facing copy.

DOCTRINE
========
This is an *audit aid*, not an auto-rewriter. It deliberately
over-reports rather than under-reports. Every hit must be reviewed by a
human against the Phase 12.5 doctrine before any change is made. False
positives (canonical glossary terms, code comments that explain
behaviour) MUST be kept — they are not language drift.

USAGE
=====
    python3 /app/scripts/operator_vocabulary_scanner.py            # default scope
    python3 /app/scripts/operator_vocabulary_scanner.py --json     # machine-readable
    python3 /app/scripts/operator_vocabulary_scanner.py --strict   # strict mode (more hits)
    python3 /app/scripts/operator_vocabulary_scanner.py --paths a.jsx b.py
    python3 /app/scripts/operator_vocabulary_scanner.py --paths /app/frontend/src/pages/DispatchBoard.jsx

OUTPUT
======
Markdown-style report grouped by file: each hit shows line number, the
matching term, and the surrounding line so the operator can decide
whether the wording is honest or whether it is software-speak masquerading
as operational language.

NOTE
====
This tool never modifies files. It does not return a non-zero exit code,
so it can be safely added to a Makefile or CI without breaking builds —
it is *for awareness only*.
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
# Flagged vocabulary
# ─────────────────────────────────────────────────────────────────────
# Tier 1: ALWAYS suspicious in operator-facing copy. Even in code these
# leaking into a string is a strong drift signal.
TIER_1 = [
    r"\biter\d{2,4}\b",
    r"\bERP\b",
    r"\bsurveillance\b",
    r"\bproductivity scoring\b",
    r"\bdriver scoring\b",
    r"\bdriver score\b",
    r"\bmicromanagement\b",
    r"\bgamification\b",
    r"\bleaderboard\b",
]

# Tier 2: Often legitimate in code (comments, identifiers) but suspect
# inside operator-facing strings. Strict mode includes these.
TIER_2 = [
    r"\bendpoint\b",
    r"\bpayload\b",
    r"\bdashboard\b",
    r"\banalytics\b",
    r"\bKPI\b",
    r"\bmetric\b",
    r"\bscore\b",
    r"\bmodule\b",
    r"\bsubsystem\b",
    r"\bportal management\b",
    r"\bbackend\b",
    r"\bfrontend\b",
    r"\bAPI\b",
    r"\bcollection\b",
]

# ─────────────────────────────────────────────────────────────────────
# Default scope (iter398 · DLS + cross-portal mounts + governance + glossary)
# ─────────────────────────────────────────────────────────────────────
DEFAULT_SCOPE = [
    # DLS surfaces
    "frontend/src/pages/DispatchBoard.jsx",
    "frontend/src/components/dispatch/AssignmentDrawer.jsx",
    "frontend/src/components/dispatch/DispatchLifecycleTile.jsx",
    "frontend/src/pages/driver/DriverShift.jsx",
    "frontend/src/pages/driver/DriverMagicLanding.jsx",
    "frontend/src/pages/DispatchHub.jsx",
    # Cross-portal mount points (whole file — small, fast to scan)
    "frontend/src/pages/PmHub.jsx",
    "frontend/src/pages/ShopHub.jsx",
    # Governance + exports (backend strings end up in banner headlines / CSVs)
    "backend/routes/dispatch_governance.py",
    "backend/routes/dispatch_exports.py",
    # Glossary
    "frontend/src/pages/admin/AdminOperationalLanguage.jsx",
]

# Lines we deliberately skip — they're not operator-facing.
SKIP_PATTERNS = [
    re.compile(r"^\s*//"),                  # JS line comment
    re.compile(r"^\s*\*"),                  # JS block-comment body
    re.compile(r"^\s*#"),                   # Python comment
    re.compile(r"^\s*\"\"\""),              # Python docstring boundary
    re.compile(r"^\s*import\s"),
    re.compile(r"^\s*from\s+\S+\s+import"),
    re.compile(r"data-testid="),            # test ids are infrastructure
]


@dataclass
class Hit:
    path: str
    line_no: int
    term: str
    tier: int
    snippet: str

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "line": self.line_no,
            "term": self.term,
            "tier": self.tier,
            "snippet": self.snippet.strip(),
        }


def _line_is_skippable(line: str) -> bool:
    return any(p.search(line) for p in SKIP_PATTERNS)


def _compile_patterns(strict: bool) -> List[tuple[int, re.Pattern]]:
    out: List[tuple[int, re.Pattern]] = []
    for pat in TIER_1:
        out.append((1, re.compile(pat, re.IGNORECASE)))
    if strict:
        for pat in TIER_2:
            out.append((2, re.compile(pat, re.IGNORECASE)))
    return out


def scan_file(path: Path, patterns: List[tuple[int, re.Pattern]]) -> List[Hit]:
    if not path.exists():
        return []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    hits: List[Hit] = []
    for i, line in enumerate(text.splitlines(), start=1):
        if _line_is_skippable(line):
            continue
        for tier, pat in patterns:
            m = pat.search(line)
            if m:
                hits.append(Hit(
                    path=str(path.relative_to(ROOT)),
                    line_no=i,
                    term=m.group(0),
                    tier=tier,
                    snippet=line.strip()[:200],
                ))
                # one hit per line is enough; we want awareness, not noise
                break
    return hits


def scan(paths: Iterable[str], strict: bool) -> List[Hit]:
    patterns = _compile_patterns(strict)
    out: List[Hit] = []
    for rel in paths:
        full = (ROOT / rel) if not os.path.isabs(rel) else Path(rel)
        out.extend(scan_file(full, patterns))
    return out


def render_markdown(hits: List[Hit]) -> str:
    if not hits:
        return "# Operator Vocabulary Scan · clean\n\nNo flagged vocabulary in the scanned scope. ✅\n"
    lines = ["# Operator Vocabulary Scan · candidates", "",
             f"Found **{len(hits)}** candidate line(s) across "
             f"**{len(set(h.path for h in hits))}** file(s).",
             "",
             "_This is an audit aid only. Review each hit in context. "
             "False positives (canonical glossary terms, internal code comments) "
             "MUST stay — they are not language drift._",
             ""]
    by_file: dict[str, list[Hit]] = {}
    for h in hits:
        by_file.setdefault(h.path, []).append(h)
    for path in sorted(by_file):
        lines.append(f"## `{path}`")
        lines.append("")
        lines.append("| Line | Tier | Term | Context |")
        lines.append("|---:|:---:|:---|:---|")
        for h in sorted(by_file[path], key=lambda x: x.line_no):
            snippet = h.snippet.replace("|", "\\|")
            lines.append(f"| {h.line_no} | T{h.tier} | `{h.term}` | {snippet} |")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Phase 12.5 operator vocabulary scanner — audit aid.",
    )
    parser.add_argument(
        "--paths", nargs="*", default=None,
        help="Override scope with explicit file paths (relative to /app).",
    )
    parser.add_argument(
        "--strict", action="store_true",
        help="Include Tier-2 vocabulary (endpoint, payload, dashboard, …).",
    )
    parser.add_argument(
        "--json", dest="as_json", action="store_true",
        help="Output a JSON array instead of markdown.",
    )
    args = parser.parse_args()

    scope = args.paths if args.paths else DEFAULT_SCOPE
    hits = scan(scope, strict=args.strict)

    if args.as_json:
        sys.stdout.write(json.dumps([h.to_dict() for h in hits], indent=2))
        sys.stdout.write("\n")
    else:
        sys.stdout.write(render_markdown(hits))

    # always exit 0 — awareness tool, not a build break
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
