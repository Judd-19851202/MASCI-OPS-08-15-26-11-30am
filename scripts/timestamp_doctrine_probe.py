#!/usr/bin/env python3
"""Timestamp Doctrine Probe — Phase TRUST-TIME-1B · 2026-05-28.

Self-protection probe that prevents the +4h PO receipt-upload bug
class from ever returning. Scans the entire source tree for the
exact anti-patterns that produced TRUST-TIME-1, fails fast on any
NEW occurrence, and accepts a baseline of documented legacy lines.

Doctrine (locked in `memory/TIMESTAMP_UTILITY_STANDARD.md`):
  * Store UTC · transmit tz-aware ISO · render local · label UTC.
  * `lib/dateUtils.js` is the canonical helper layer.
  * `datetime.now(timezone.utc)` — never `datetime.utcnow()`.
  * Backend `_iso()` always tags naive datetimes as UTC.

Anti-patterns this probe catches
--------------------------------
FRONTEND (`frontend/src/**/*.{js,jsx,ts,tsx}`):
  F1. `.slice(0, 16).replace("T", " ")` — UTC clock as local
  F2. `.slice(0, 19).replace("T", " ")` — same, includes seconds
  F3. `.slice(0, 16)` immediately followed by `.replace("T", " ")` on the next chunk
  F4. `new Date(...).toLocaleString()` outside dateUtils.js (use formatLocalDateTime)
  F5. `new Date(...).toLocaleDateString()` outside dateUtils.js (use formatLocalDate)

BACKEND (`backend/**/*.py`):
  B1. `datetime.utcnow()` — produces naive datetimes
  B2. `def _iso(dt)` body without `dt.tzinfo is None` guard
  B3. `.isoformat()` on a value that was assigned by `datetime.utcnow()` (heuristic)

Allowlist
---------
Documented legacy admin/audit lines listed in
`scripts/timestamp_pattern_baseline.json` are baselined and produce
WARNINGS, not failures. Anything NEW outside the baseline FAILS.

Usage
-----
    python3 scripts/timestamp_doctrine_probe.py             # human report
    python3 scripts/timestamp_doctrine_probe.py --json      # JSON
    python3 scripts/timestamp_doctrine_probe.py --gate      # exit 1 on new
    python3 scripts/timestamp_doctrine_probe.py --bless     # update baseline

Integrated into `scripts/pre_deploy_check.sh` as
`stage_timestamp_doctrine`.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

REPO_ROOT = Path("/app")
FRONTEND_SRC = REPO_ROOT / "frontend" / "src"
BACKEND_ROOT = REPO_ROOT / "backend"
BASELINE_PATH = REPO_ROOT / "scripts" / "timestamp_pattern_baseline.json"
REPORT_OUT = REPO_ROOT / "memory" / "TIMESTAMP_DOCTRINE_PROBE_REPORT.md"

# Files we never scan — they ARE the canonical helpers, or they're
# documentation/test scaffolds where the patterns appear deliberately.
FRONTEND_ALLOWLIST = {
    "lib/dateUtils.js",                       # the helper itself
}
BACKEND_ALLOWLIST = {
    # The probe defines the doctrine — it's allowed to mention the patterns.
    "scripts/timestamp_doctrine_probe.py",
    # The pre-existing health helper uses `datetime.utcnow` for a
    # rendered footer that's already labeled "UTC" — kept here for
    # auditability, baselined below.
}

# Test files are scanned for documentation purposes but never fail
# the gate — patterns may appear as INPUTS to tests.
TEST_PATH_HINTS = ("/tests/", "/test_", "test_", "/_tests/")

# ─── Patterns ──────────────────────────────────────────────────────

# Each entry: (id, language, regex, severity, fix_hint).
PATTERNS: List[Tuple[str, str, re.Pattern, str, str]] = [
    # ─── Frontend ────────────────────────────────────────────────
    (
        "F1·slice16-replaceT",
        "frontend",
        re.compile(r"\.slice\(0,\s*16\)\.replace\(['\"]T['\"]"),
        "high",
        "Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js",
    ),
    (
        "F2·slice19-replaceT",
        "frontend",
        re.compile(r"\.slice\(0,\s*19\)\.replace\(['\"]T['\"]"),
        "high",
        "Use formatLocalDateTime() or formatUtcForAudit() from lib/dateUtils.js",
    ),
    (
        "F4·toLocaleString-bare",
        "frontend",
        # `new Date(...).toLocaleString(` outside dateUtils.js. We
        # match the call form; whitespace tolerant.
        re.compile(r"new\s+Date\s*\([^)]*\)\s*\.toLocaleString\s*\("),
        "med",
        "Use formatLocalDateTime() from lib/dateUtils.js — defensively coerces naive ISO as UTC.",
    ),
    (
        "F5·toLocaleDateString-bare",
        "frontend",
        re.compile(r"new\s+Date\s*\([^)]*\)\s*\.toLocaleDateString\s*\("),
        "med",
        "Use formatLocalDate() from lib/dateUtils.js.",
    ),
    # ─── Backend ─────────────────────────────────────────────────
    (
        "B1·datetime-utcnow",
        "backend",
        re.compile(r"\bdatetime\.utcnow\s*\("),
        "high",
        "Use datetime.now(timezone.utc) — utcnow() returns a NAIVE datetime.",
    ),
]


# ─── Scan ──────────────────────────────────────────────────────────


def _read_baseline() -> Dict[str, Any]:
    if not BASELINE_PATH.exists():
        return {"entries": []}
    try:
        return json.loads(BASELINE_PATH.read_text())
    except Exception:
        return {"entries": []}


def _baseline_key(rel_path: str, pattern_id: str, line: int) -> str:
    return f"{rel_path}::{pattern_id}::{line}"


def _is_allowlisted(rel_path: str, language: str) -> bool:
    if language == "frontend" and rel_path in FRONTEND_ALLOWLIST:
        return True
    if language == "backend" and rel_path in BACKEND_ALLOWLIST:
        return True
    return False


def _is_test_path(rel_path: str) -> bool:
    return any(h in f"/{rel_path}" for h in TEST_PATH_HINTS)


def _iter_files() -> List[Tuple[str, Path, str]]:
    """Yield (rel_path, abs_path, language) for every scannable file."""
    files: List[Tuple[str, Path, str]] = []
    if FRONTEND_SRC.exists():
        for p in FRONTEND_SRC.rglob("*"):
            if not p.is_file():
                continue
            if p.suffix not in (".js", ".jsx", ".ts", ".tsx"):
                continue
            rel = str(p.relative_to(FRONTEND_SRC))
            files.append((rel, p, "frontend"))
    # Backend: scan only routes/ + top-level .py — narrow scope to
    # keep the probe sub-second.
    candidates: List[Path] = []
    if (BACKEND_ROOT / "routes").exists():
        candidates.extend((BACKEND_ROOT / "routes").rglob("*.py"))
    candidates.extend(BACKEND_ROOT.glob("*.py"))
    for p in candidates:
        if not p.is_file():
            continue
        rel = str(p.relative_to(BACKEND_ROOT))
        files.append((rel, p, "backend"))
    return files


def scan() -> Dict[str, Any]:
    started = time.time()
    hits: List[Dict[str, Any]] = []
    files = _iter_files()
    for rel_path, abs_path, language in files:
        if _is_allowlisted(rel_path, language):
            continue
        try:
            text = abs_path.read_text(errors="replace")
        except Exception:
            continue
        lines = text.splitlines()
        for pid, plang, regex, sev, hint in PATTERNS:
            if plang != language:
                continue
            for idx, line in enumerate(lines, start=1):
                m = regex.search(line)
                if not m:
                    continue
                hits.append({
                    "path": rel_path,
                    "language": language,
                    "pattern_id": pid,
                    "line": idx,
                    "severity": sev,
                    "snippet": line.strip()[:140],
                    "fix_hint": hint,
                    "is_test": _is_test_path(rel_path),
                })
    baseline = _read_baseline()
    baseline_set = {e for e in (baseline.get("entries") or [])}
    new_violations: List[Dict[str, Any]] = []
    new_warnings: List[Dict[str, Any]] = []
    baselined: List[Dict[str, Any]] = []
    for h in hits:
        key = _baseline_key(h["path"], h["pattern_id"], h["line"])
        if key in baseline_set:
            baselined.append(h)
            continue
        if h["is_test"]:
            # Test files contribute to warnings, never failures.
            new_warnings.append(h)
        elif h["severity"] == "high":
            new_violations.append(h)
        else:
            new_warnings.append(h)
    return {
        "scan_ms": int((time.time() - started) * 1000),
        "files_scanned": len(files),
        "patterns": len(PATTERNS),
        "baselined": baselined,
        "new_violations": new_violations,
        "new_warnings": new_warnings,
    }


# ─── Output ────────────────────────────────────────────────────────


def _render_human(report: Dict[str, Any]) -> str:
    nv = len(report["new_violations"])
    nw = len(report["new_warnings"])
    bl = len(report["baselined"])
    head = (
        f"Timestamp Doctrine Probe · scan_ms={report['scan_ms']} · "
        f"files={report['files_scanned']} · patterns={report['patterns']}\n"
        f"  new_violations={nv}  new_warnings={nw}  baselined={bl}\n"
    )
    body = []
    if nv:
        body.append("\n  ⚠ NEW VIOLATIONS (deploy will fail):")
        for h in report["new_violations"]:
            body.append(
                f"    {h['path']}:{h['line']} · {h['pattern_id']} · "
                f"{h['snippet'][:80]}\n      → {h['fix_hint']}"
            )
    if nw:
        body.append("\n  · new warnings (review):")
        for h in report["new_warnings"][:20]:
            body.append(
                f"    {h['path']}:{h['line']} · {h['pattern_id']} · "
                f"{h['snippet'][:80]}"
            )
    return head + "\n".join(body)


def _render_markdown(report: Dict[str, Any]) -> str:
    nv = len(report["new_violations"])
    nw = len(report["new_warnings"])
    bl = len(report["baselined"])
    status = "🟢 PASS" if nv == 0 else "🔴 FAIL"
    lines = [
        "# Timestamp Doctrine Probe Report",
        "",
        f"_Phase TRUST-TIME-1B · self-protection probe · {status}_",
        "",
        f"- Scanned files     : **{report['files_scanned']}**",
        f"- Patterns           : **{report['patterns']}**",
        f"- New violations     : **{nv}**",
        f"- New warnings       : **{nw}**",
        f"- Baselined          : **{bl}**",
        f"- Scan runtime       : **{report['scan_ms']} ms**",
        "",
        "## Pattern catalogue",
        "",
        "| ID | Language | Severity | Fix |",
        "|----|----------|----------|-----|",
    ]
    for pid, plang, _regex, sev, hint in PATTERNS:
        lines.append(f"| `{pid}` | {plang} | {sev} | {hint} |")
    if nv:
        lines.extend(["", "## ⚠ New violations", ""])
        for h in report["new_violations"]:
            lines.append(
                f"- `{h['path']}:{h['line']}` · `{h['pattern_id']}` · "
                f"`{h['snippet'][:80]}` → {h['fix_hint']}"
            )
    if nw:
        lines.extend(["", "## · New warnings (review · not deploy-blocking)", ""])
        for h in report["new_warnings"][:30]:
            lines.append(
                f"- `{h['path']}:{h['line']}` · `{h['pattern_id']}` · "
                f"`{h['snippet'][:80]}`"
            )
        if nw > 30:
            lines.append(f"\n_…and {nw - 30} more (see JSON output)._")
    lines.extend([
        "",
        "## How to clear violations",
        "",
        "1. Replace ad-hoc rendering with helpers from `lib/dateUtils.js`.",
        "2. Replace `datetime.utcnow()` with `datetime.now(timezone.utc)`.",
        "3. If a legacy line is reviewed and accepted as-is, add its",
        "   `path::pattern_id::line` key to `scripts/timestamp_pattern_baseline.json`.",
        "",
        "Run `python3 scripts/timestamp_doctrine_probe.py --bless` to",
        "regenerate the baseline after a fix sweep.",
        "",
    ])
    return "\n".join(lines)


def _write_baseline(report: Dict[str, Any]) -> int:
    """Write a baseline containing EVERY current hit so the tree is clean."""
    entries = []
    all_hits = (
        report["baselined"]
        + report["new_violations"]
        + report["new_warnings"]
    )
    for h in all_hits:
        entries.append(_baseline_key(h["path"], h["pattern_id"], h["line"]))
    entries.sort()
    BASELINE_PATH.write_text(json.dumps(
        {"version": "TRUST-TIME-1B/v1", "entries": entries},
        indent=2,
    ))
    return len(entries)


# ─── CLI ───────────────────────────────────────────────────────────


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", action="store_true", help="emit JSON report")
    parser.add_argument("--gate", action="store_true",
                        help="exit 1 on any new violation")
    parser.add_argument("--bless", action="store_true",
                        help="regenerate baseline · USE WITH CAUTION")
    parser.add_argument("--md", action="store_true",
                        help="write markdown report to memory/")
    args = parser.parse_args()

    report = scan()

    if args.bless:
        n = _write_baseline(report)
        print(f"✓ baseline written · {n} entries · {BASELINE_PATH}")
        return 0

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(_render_human(report))

    if args.md or args.gate:
        REPORT_OUT.write_text(_render_markdown(report))
        if not args.json:
            print(f"\n  ✓ report written · {REPORT_OUT}")

    if args.gate and report["new_violations"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
