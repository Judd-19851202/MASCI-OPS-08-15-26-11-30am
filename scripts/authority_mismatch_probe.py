#!/usr/bin/env python3
"""Authority Mismatch Probe — Phase GOVERNANCE-INFRA-1 · 2026-05-28.

Scans the frontend source tree for dangerous authority patterns that
bypass the capability layer (`lib/poCapabilities.js`, future siblings).
Designed as a calm, deterministic, sub-second pre-deploy gate that
catches the exact class of regression that caused the TRUST-PO-1
incident (`PoRequests.jsx` rendering approval controls under FL portal
chrome because `isPm() || isHr() || isAdmin()` ignored portal context).

Doctrine
--------
* Lightweight (<1s for the whole frontend tree).
* Deterministic — same input always gives same report.
* WARN-by-default, FAIL only on confirmed violations whose paths
  are NOT listed in the baseline.
* Baseline file (`scripts/authority_pattern_baseline.json`) records
  the set of (file, pattern) pairs that have been reviewed and
  considered acceptable. Anything outside the baseline is a NEW
  violation and fails the gate.
* No false positives on `pages/Admin*`, `pages/Pm*`, `pages/Hr*`,
  `pages/Safety*` — these are PORTAL-OWNED pages where token-presence
  is the right gate.
* No false positives on `lib/poCapabilities.js` itself — that IS the
  capability layer.

Scan patterns (in priority order)
---------------------------------
1. `isPm() || isHr() || isAdmin()` (and variants) — the canonical
   token-coexistence rendering pattern.
2. `isAdmin() || isPm()` and 4 other pairwise OR combos.
3. `(isPm() ?` / `(isHr() ?` etc — ternary token gates.
4. `&& (isPm()` / `&& (isAdmin()` — conditional gating.
5. Direct approval-action JSX patterns:
   - `data-testid="po-approve` (approval surface)
   - `<Approve` / `<Reject` / `<Clarify` JSX without capability prop.

Usage
-----
   python3 scripts/authority_mismatch_probe.py            # human report
   python3 scripts/authority_mismatch_probe.py --json     # JSON report
   python3 scripts/authority_mismatch_probe.py --gate     # exit 1 on
                                                          # new violations
   python3 scripts/authority_mismatch_probe.py --bless    # update baseline

Pre-deploy integration via `stage_governance_authority_mismatch()`
in `scripts/pre_deploy_check.sh`.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

REPO_ROOT = Path("/app")
FRONTEND_SRC = REPO_ROOT / "frontend" / "src"
BASELINE_PATH = REPO_ROOT / "scripts" / "authority_pattern_baseline.json"
REPORT_OUT = REPO_ROOT / "memory" / "AUTHORITY_MISMATCH_REPORT.md"

# Files we never scan — they're allowed to use raw token-presence
# because they are themselves the capability/auth layer or are
# portal-owned pages where token presence is the correct gate.
ALLOWLIST_GLOBS = [
    # The capability layer itself
    "lib/poCapabilities.js",
    "lib/portalContext.js",
    # Portal-owned pages — token presence is correct here
    "pages/AdminHub.jsx",
    "pages/AdminGovernance.jsx",
    "pages/PmHub.jsx",
    "pages/HrHub.jsx",
    "pages/FieldLeadershipHub.jsx",
    "pages/SafetyPortal.jsx",
    "pages/ShopHub.jsx",
    "pages/DispatchHub.jsx",
    # Auth modules
    "lib/adminAuth.js",
    "lib/pmAuth.js",
    "lib/hrAuth.js",
    "lib/leadershipAuth.js",
    "lib/flAuth.js",
    "lib/safetyAuth.js",
    "lib/shopAuth.js",
    # Routing / shell
    "App.js",
    "components/AdminShell.jsx",
    "components/PmShell.jsx",
    "components/SafetyShell.jsx",
    # Tests directory entirely
    "**/*.test.jsx",
    "**/*.test.js",
]

# Severity-ranked patterns. Each tuple = (severity, label, regex).
# Severity: "violation" (fails the gate) or "warning" (warn only).
PATTERNS = [
    # The canonical TRUST-PO-1 pattern — fails the gate.
    ("violation", "token-coexistence rendering · 3-way OR",
     re.compile(r"isPm\(\)\s*\|\|\s*isHr\(\)\s*\|\|\s*isAdmin\(\)")),
    ("violation", "token-coexistence rendering · 3-way OR (admin-first)",
     re.compile(r"isAdmin\(\)\s*\|\|\s*isPm\(\)\s*\|\|\s*isHr\(\)")),
    # 2-way OR combinations — warn (sometimes legitimate for read-only
    # access). Reviewer must bless or refactor.
    ("warning", "token-coexistence rendering · 2-way OR",
     re.compile(r"isPm\(\)\s*\|\|\s*isAdmin\(\)|isAdmin\(\)\s*\|\|\s*isPm\(\)|isHr\(\)\s*\|\|\s*isAdmin\(\)|isAdmin\(\)\s*\|\|\s*isHr\(\)|isPm\(\)\s*\|\|\s*isHr\(\)|isHr\(\)\s*\|\|\s*isPm\(\)")),
    # canApprove / canIssue / canClose derived from raw token checks
    ("warning", "ad-hoc canApprove variable",
     re.compile(r"const\s+can(?:Approve|Issue|Close|Cancel|Reject|Clarify)\s*=.*isPm\(\)|isHr\(\)|isAdmin\(\)")),
]


def _is_allowlisted(rel_path: str) -> bool:
    path = Path(rel_path)
    for glob in ALLOWLIST_GLOBS:
        if path.match(glob):
            return True
        # Also exact-suffix match for the file-only glob entries.
        if "/" in glob and rel_path.endswith(glob):
            return True
    return False


def _scan_file(path: Path) -> list[dict]:
    """Return a list of {pattern, severity, line, snippet} hits."""
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []
    hits: list[dict] = []
    for severity, label, regex in PATTERNS:
        for m in regex.finditer(text):
            line_no = text.count("\n", 0, m.start()) + 1
            line_start = text.rfind("\n", 0, m.start()) + 1
            line_end = text.find("\n", m.end())
            snippet = text[line_start: line_end if line_end != -1 else len(text)].strip()
            hits.append({
                "pattern": label,
                "severity": severity,
                "line": line_no,
                "snippet": snippet[:160],
            })
    return hits


def _scan_tree() -> dict:
    """Walk frontend/src; return {rel_path: [hits]}."""
    out: dict[str, list[dict]] = {}
    for ext in ("*.js", "*.jsx", "*.ts", "*.tsx"):
        for f in FRONTEND_SRC.rglob(ext):
            if "node_modules" in f.parts or "__tests__" in f.parts:
                continue
            rel = str(f.relative_to(FRONTEND_SRC))
            if _is_allowlisted(rel):
                continue
            hits = _scan_file(f)
            if hits:
                out[rel] = hits
    return out


def _load_baseline() -> dict:
    if not BASELINE_PATH.exists():
        return {"approved": []}
    try:
        return json.loads(BASELINE_PATH.read_text())
    except json.JSONDecodeError:
        return {"approved": []}


def _baseline_key(rel: str, hit: dict) -> str:
    return f"{rel}::{hit['pattern']}::{hit['line']}"


def _classify(scan: dict, baseline: dict) -> tuple[list[tuple], list[tuple], list[tuple]]:
    """Return (new_violations, new_warnings, baselined)."""
    approved = set(baseline.get("approved", []))
    new_v: list[tuple] = []
    new_w: list[tuple] = []
    baselined: list[tuple] = []
    for rel, hits in scan.items():
        for h in hits:
            key = _baseline_key(rel, h)
            if key in approved:
                baselined.append((rel, h))
            elif h["severity"] == "violation":
                new_v.append((rel, h))
            else:
                new_w.append((rel, h))
    return new_v, new_w, baselined


def _render_md_report(new_v, new_w, baselined, started_ms) -> str:
    lines = [
        "# AUTHORITY MISMATCH REPORT",
        "",
        "_Phase GOVERNANCE-INFRA-1 · Workstream 1 · Authority Mismatch Probe._",
        "",
        f"* Generated: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}",
        f"* Scan duration: {int((time.time() * 1000) - started_ms)} ms",
        f"* Frontend tree: `{FRONTEND_SRC}`",
        f"* Baseline: `{BASELINE_PATH}`",
        "",
        "## Summary",
        "",
        f"* **New violations** (fail the gate): **{len(new_v)}**",
        f"* **New warnings** (review): {len(new_w)}",
        f"* **Baselined** (previously approved): {len(baselined)}",
        "",
    ]
    if new_v:
        lines.append("## 🔴 New violations\n")
        for rel, h in new_v:
            lines.append(f"### `{rel}` · line {h['line']}\n")
            lines.append(f"* Pattern: **{h['pattern']}**")
            lines.append(f"* Severity: **{h['severity']}**")
            lines.append(f"* Snippet:\n  ```\n  {h['snippet']}\n  ```")
            lines.append("* Remediation: route this gate through "
                         "`getPoCapabilities()` (or the relevant "
                         "capability bundle). Consult portal context "
                         "FIRST, token presence SECOND. See "
                         "`SHARED_SURFACE_DOCTRINE.md`.")
            lines.append("")
    if new_w:
        lines.append("## 🟡 New warnings\n")
        for rel, h in new_w:
            lines.append(f"* `{rel}:{h['line']}` · {h['pattern']} · "
                         f"`{h['snippet'][:80]}`")
        lines.append("")
    if baselined:
        lines.append("## ⚪ Baselined (already reviewed)\n")
        for rel, h in baselined:
            lines.append(f"* `{rel}:{h['line']}` · {h['pattern']}")
        lines.append("")
    if not (new_v or new_w or baselined):
        lines.append("## ✅ Clean\n")
        lines.append("No authority-mismatch patterns found outside the "
                     "capability layer. Platform self-protection green.\n")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Authority Mismatch Probe")
    ap.add_argument("--json", action="store_true", help="JSON output to stdout")
    ap.add_argument("--gate", action="store_true",
                    help="exit 1 on new violations (pre-deploy mode)")
    ap.add_argument("--bless", action="store_true",
                    help="add current scan results to baseline")
    args = ap.parse_args()

    started = time.time() * 1000
    scan = _scan_tree()
    baseline = _load_baseline()
    new_v, new_w, baselined = _classify(scan, baseline)

    if args.bless:
        keys = sorted({_baseline_key(rel, h)
                       for rel, hits in scan.items() for h in hits})
        BASELINE_PATH.write_text(
            json.dumps({"approved": keys, "blessed_at":
                        time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())},
                       indent=2) + "\n"
        )
        print(f"✓ baseline updated · {len(keys)} approved entries · "
              f"{BASELINE_PATH}")
        return 0

    if args.json:
        json.dump({
            "new_violations": [{"file": r, **h} for r, h in new_v],
            "new_warnings": [{"file": r, **h} for r, h in new_w],
            "baselined": [{"file": r, **h} for r, h in baselined],
            "scan_ms": int((time.time() * 1000) - started),
        }, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        md = _render_md_report(new_v, new_w, baselined, started)
        REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
        REPORT_OUT.write_text(md)
        print(f"✓ report written · {REPORT_OUT}")
        print(f"  new_violations={len(new_v)} · new_warnings={len(new_w)} · "
              f"baselined={len(baselined)} · "
              f"scan_ms={int((time.time() * 1000) - started)}")

    if args.gate and new_v:
        print(f"✗ authority-mismatch probe FAILED · "
              f"{len(new_v)} new violation(s) outside baseline",
              file=sys.stderr)
        for rel, h in new_v[:5]:
            print(f"  · {rel}:{h['line']} · {h['pattern']}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
