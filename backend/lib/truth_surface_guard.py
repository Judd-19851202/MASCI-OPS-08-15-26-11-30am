"""Canonical Truth-Surface enumeration GATE (Wave 11 permanent enforcement).

ONE owner that wraps the single canonical enumeration scanner
(scripts/wave5_truth_surface_canonical.py) for the pre-Save/release-readiness path.
Returns a list of violation strings (empty = pass). No duplicate scanner is created;
this delegates to the canonical scanner and validates its output.

Violations:
  - scanner failed to run / no summary produced
  - invariant broken (included + excluded != candidate)
  - any OPEN/unclassified surface (no fabricated closure)
  - included truth-surface count drifted from the governed baseline (a truth-bearing
    surface appeared/disappeared without governed reconciliation)
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import List

# Governed baseline — change ONLY with a recorded reconciliation (WAVE5_DENOMINATOR_RECONCILIATION.md).
# 396 -> 397 (2026-06 repair cycle): TD-0014/TD-0015 repairs added ONE governed truth surface
# (equipment-master UNAVAILABLE error state / trench governed N/A cell). Invariant holds, OPEN=0.
BASELINE_INCLUDED = 397


def gate_violations(repo_root: Path) -> List[str]:
    repo_root = Path(repo_root)
    scanner = repo_root / "scripts" / "wave5_truth_surface_canonical.py"
    summary = repo_root / "memory" / "truth_program" / "TRUTH_SURFACE_CANONICAL.json"
    violations: List[str] = []
    if not scanner.exists():
        return ["GD-0025 truth-surface scanner missing: " + str(scanner)]
    try:
        subprocess.run([sys.executable, str(scanner)], cwd=str(repo_root),
                       check=True, capture_output=True, text=True, timeout=120)
    except Exception as exc:  # noqa: BLE001
        return [f"GD-0025 truth-surface scanner failed to run: {type(exc).__name__}: {exc}"]
    try:
        s = json.loads(summary.read_text())
    except Exception as exc:  # noqa: BLE001
        return [f"GD-0025 truth-surface summary unreadable: {type(exc).__name__}: {exc}"]

    if not s.get("invariant_holds"):
        violations.append(
            "GD-0025 invariant broken: included+excluded != candidate "
            f"({s.get('included_truth_surfaces')}+{s.get('excluded_with_reason')}!={s.get('candidate_universe')})")
    if s.get("open_needs_proof", 0) != 0:
        violations.append(f"GD-0025 OPEN/unclassified truth surfaces: {s.get('open_needs_proof')}")
    included = s.get("included_truth_surfaces")
    if included != BASELINE_INCLUDED:
        violations.append(
            f"GD-0025 truth-surface denominator drift: baseline={BASELINE_INCLUDED} now={included}. "
            "Reconcile in the register and update BASELINE_INCLUDED with a governed reason.")
    return violations


__all__ = ["gate_violations", "BASELINE_INCLUDED"]
