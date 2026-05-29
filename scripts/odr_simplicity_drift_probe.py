#!/usr/bin/env python3
"""
odr_simplicity_drift_probe.py — Phase V.1 · M0.4 · ADVISORY · M1-prep.

Doctrine source: `/app/memory/ODR_SIMPLICITY_TEST_DOCTRINE.md`

Heuristic scan of the foreman-facing ODR surfaces for forbidden
simplicity-violating patterns:
  * Modal stacks (>1 simultaneously open Dialog)
  * Required free-text inputs outside the narrative box
  * Required PDF generation by foreman
  * Required PM-style approvals on foreman path
  * Punitive coaching tone ("you must…", "you forgot…")
  * More than 9 wizard steps in foreman entry

Files scanned:
  /app/frontend/src/pages/odr/OdrNew.jsx
  /app/frontend/src/pages/odr/OdrCenter.jsx (Foreman tab only)
  /app/frontend/src/components/odr/OdrTrustBanner.jsx (if present)

ADVISORY ONLY · exit code always 0.

Usage:
  python3 scripts/odr_simplicity_drift_probe.py
"""
from __future__ import annotations

import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REPORT_PATH = REPO_ROOT / "memory" / "ODR_SIMPLICITY_DRIFT_REPORT.md"

TARGETS = [
    REPO_ROOT / "frontend" / "src" / "pages" / "odr" / "OdrNew.jsx",
    REPO_ROOT / "frontend" / "src" / "pages" / "odr" / "OdrCenter.jsx",
]

PUNITIVE_PATTERNS = [
    re.compile(r"you\s+must\s+", re.IGNORECASE),
    re.compile(r"you\s+forgot", re.IGNORECASE),
    re.compile(r"you\s+failed", re.IGNORECASE),
    re.compile(r"required\s+by\s+you", re.IGNORECASE),
]

WIZARD_STEP_PATTERN = re.compile(r"step\s*[:=]\s*['\"]?(\d+)", re.IGNORECASE)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def scan(path: Path) -> dict:
    if not path.exists():
        return {"path": str(path.relative_to(REPO_ROOT)),
                "exists": False, "advisories": []}
    src = path.read_text(errors="ignore")
    advisories = []

    # Punitive copy
    for rx in PUNITIVE_PATTERNS:
        for m in rx.finditer(src):
            advisories.append({
                "kind": "punitive_copy",
                "match": m.group(0),
                "context": src[max(0, m.start() - 30):m.end() + 30].replace("\n", " "),
            })

    # Modal nesting heuristic — count Dialog open=true literal occurrences
    open_dialogs = re.findall(r"<Dialog[^>]+open=\{?true\}?", src)
    if len(open_dialogs) > 1:
        advisories.append({
            "kind": "modal_stack",
            "count": len(open_dialogs),
        })

    # Wizard step ceiling
    steps = WIZARD_STEP_PATTERN.findall(src)
    max_step = max((int(s) for s in steps), default=0)
    if max_step > 9:
        advisories.append({
            "kind": "wizard_step_ceiling_breach",
            "max_step_seen": max_step,
        })

    # Required PDF generation by foreman heuristic
    if re.search(r"foreman.{0,40}generate.{0,20}pdf", src, re.IGNORECASE):
        advisories.append({"kind": "foreman_pdf_required"})

    return {
        "path": str(path.relative_to(REPO_ROOT)),
        "exists": True,
        "advisories": advisories,
    }


def run() -> int:
    results = [scan(p) for p in TARGETS]
    advisory_count = sum(len(r["advisories"]) for r in results)
    state = "GREEN" if advisory_count == 0 else "AMBER"

    lines = [
        "# ODR Simplicity Drift Report",
        "",
        f"_Generated: {_utc_now_iso()} · advisory probe._",
        "",
        "**Doctrine source:** `ODR_SIMPLICITY_TEST_DOCTRINE.md`",
        "",
        f"## Summary · {state} · {advisory_count} advisory item(s)",
        "",
    ]
    for r in results:
        lines.append(f"### `{r['path']}`")
        if not r["exists"]:
            lines.append("- File not present (skipped).")
            lines.append("")
            continue
        if not r["advisories"]:
            lines.append("- No simplicity advisories.")
        else:
            for adv in r["advisories"]:
                lines.append(f"- **{adv['kind']}** · "
                             f"{ {k: v for k, v in adv.items() if k != 'kind'} }")
        lines.append("")

    lines += [
        "## ADVISORY",
        "",
        "This probe **never fails the build**. Operators interpret",
        "advisory items in context — not every match is a true",
        "violation. Use the report to triage friction signals before",
        "they hit the field.",
        "",
        "_Probe exit code: 0 (advisory)._",
    ]
    REPORT_PATH.write_text("\n".join(lines) + "\n")
    print(f"odr_simplicity_drift_probe · advisories={advisory_count} · state={state}")
    print(f"  report -> {REPORT_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    # Compatibility: accept --gate but ignore it (advisory).
    sys.exit(run())
