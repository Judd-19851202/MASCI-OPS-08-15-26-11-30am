#!/usr/bin/env python3
"""iter437 / Phase IV-BETA.4A · Doctrine drift intelligence.

Diffs the working-tree `HUB_VISUAL_BASELINE.json` against the last
committed version and prints an operator-readable 5–10 line summary
of what shifted between deploys.

Each delta is classified:
  • expected             — within calibrated noise band
  • suspicious           — outside noise band, but no doctrine boundary crossed
  • doctrine violation   — crosses a doctrine boundary (loudness >75,
                           hierarchy-hash change, hue-family count jump
                           by >2, or badge-density doubled)

WARNING-ONLY: prints to stdout, exits 0. Intended to run as a
warning-only stage in `pre_deploy_check.sh` and as a manual
operator tool.

Usage:
    python3 scripts/diff_doctrine_baseline.py
    python3 scripts/diff_doctrine_baseline.py --against HEAD~1

If no committed baseline exists yet, exits 0 with "no prior baseline".
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BASELINE_PATH = REPO_ROOT / "memory" / "HUB_VISUAL_BASELINE.json"

LOUDNESS_VIOLATION_CEIL = 75.0      # >75 = doctrine violation
LOUDNESS_SUSPICIOUS_DELTA = 7.5     # delta beyond this = suspicious
HUE_VIOLATION_JUMP = 2              # hue family count jump >2 = violation
BADGE_VIOLATION_RATIO = 2.0         # badge density doubling = violation


def _committed(path: Path, ref: str) -> dict | None:
    """Return the JSON at the given git ref, or None if not present."""
    try:
        out = subprocess.check_output(
            ["git", "-C", str(REPO_ROOT), "show", f"{ref}:memory/{path.name}"],
            stderr=subprocess.DEVNULL,
        )
        return json.loads(out)
    except subprocess.CalledProcessError:
        return None
    except json.JSONDecodeError:
        return None


def _classify(metric: str, prev: float, curr: float) -> str:
    """Classify a numeric delta — return 'expected' | 'suspicious' | 'violation'."""
    if prev is None or curr is None:
        return "expected"
    if metric == "loudness_score":
        if curr > LOUDNESS_VIOLATION_CEIL:
            return "violation"
        if abs(curr - prev) > LOUDNESS_SUSPICIOUS_DELTA:
            return "suspicious"
        return "expected"
    if metric == "hue_family_count":
        if abs(curr - prev) > HUE_VIOLATION_JUMP:
            return "violation"
        if curr != prev:
            return "suspicious"
        return "expected"
    if metric == "badge_density":
        # avoid div-by-zero
        ratio = (curr + 0.5) / (prev + 0.5)
        if ratio >= BADGE_VIOLATION_RATIO or ratio <= (1.0 / BADGE_VIOLATION_RATIO):
            return "violation"
        if abs(curr - prev) > 5.0:
            return "suspicious"
        return "expected"
    if metric == "emphasis_score":
        if abs(curr - prev) > 5:
            return "suspicious"
        return "expected"
    return "expected"


CLASS_TAG = {
    "expected": "expected",
    "suspicious": "SUSPICIOUS",
    "violation": "DOCTRINE VIOLATION",
}


def _lines_for_portal(portal: str, prev_block: dict, curr_block: dict) -> list[str]:
    """One line per metric that materially shifted; calm wording."""
    lines: list[str] = []
    for viewport in ("desktop", "ipad", "mobile"):
        prev = (prev_block or {}).get(viewport) or {}
        curr = (curr_block or {}).get(viewport) or {}
        if not curr:
            continue
        # hierarchy hash — categorical, distinct callout
        if prev.get("hierarchy_hash") and prev["hierarchy_hash"] != curr.get("hierarchy_hash"):
            lines.append(
                f"  · {portal} {viewport} hierarchy hash changed "
                f"({prev['hierarchy_hash'][:8]} → {curr['hierarchy_hash'][:8]}) "
                f"· DOCTRINE VIOLATION"
            )
        # numeric metrics
        for metric, fmt in (
            ("loudness_score", "{:.1f}"),
            ("hue_family_count", "{:.0f}"),
            ("badge_density", "{:.1f}"),
            ("emphasis_score", "{:.0f}"),
        ):
            pv, cv = prev.get(metric), curr.get(metric)
            klass = _classify(metric, pv, cv)
            if klass == "expected":
                continue
            delta = "" if pv is None else f" ({fmt.format(pv)} → {fmt.format(cv)})"
            label = metric.replace("_", " ")
            lines.append(
                f"  · {portal} {viewport} {label}{delta} · {CLASS_TAG[klass]}"
            )
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description="Doctrine baseline drift summary")
    parser.add_argument("--against", default="HEAD", help="git ref to compare against")
    args = parser.parse_args()

    if not BASELINE_PATH.exists():
        print("doctrine drift: no working-tree baseline found — nothing to compare.")
        return 0

    curr = json.loads(BASELINE_PATH.read_text())
    prev = _committed(BASELINE_PATH, args.against)
    if prev is None:
        print("doctrine drift: no committed baseline at "
              f"`{args.against}:memory/{BASELINE_PATH.name}` — first run.")
        return 0

    curr_snaps = curr.get("snapshots", {})
    prev_snaps = prev.get("snapshots", {})

    summary: list[str] = []
    portals_with_change: list[str] = []
    for portal in sorted(set(curr_snaps) | set(prev_snaps)):
        portal_lines = _lines_for_portal(
            portal, prev_snaps.get(portal, {}), curr_snaps.get(portal, {})
        )
        if portal_lines:
            portals_with_change.append(portal)
            summary.extend(portal_lines)

    if not summary:
        print("doctrine drift: every governed metric stable across portals.")
        return 0

    # Calm operator-readable summary — cap at 10 lines per directive.
    print(f"doctrine drift summary · {len(portals_with_change)} portal(s) shifted")
    for line in summary[:10]:
        print(line)
    if len(summary) > 10:
        print(f"  · …and {len(summary) - 10} more metric shifts elided")
    return 0


if __name__ == "__main__":
    sys.exit(main())
