"""GD-0025 — Truth Surface Enumeration guard (permanent, reproducible denominator).

Regenerates the canonical Wave-5 Truth Surface denominator FROM SOURCE and fails if:
  - the candidate/included/excluded invariant breaks;
  - any surface is OPEN/unclassified (no fabricated closure);
  - the included truth-surface count drifts from the locked baseline without a
    governed reconciliation (a new truth-bearing surface appeared unregistered, or
    a registered surface disappeared). Drift -> update BASELINE + register with reason.

This guarantees the denominator can never again become non-reproducible.
"""
import json
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCANNER = os.path.join(REPO, "scripts", "wave5_truth_surface_canonical.py")
SUMMARY = os.path.join(REPO, "memory", "truth_program", "TRUTH_SURFACE_CANONICAL.json")

# LOCKED canonical baseline (governed reconciliation required to change).
BASELINE_INCLUDED = 396
BASELINE_TOLERANCE = 0  # exact; any drift must be reconciled + this bumped with reason


def _regenerate():
    subprocess.run([sys.executable, SCANNER], cwd=REPO, check=True,
                   capture_output=True, text=True)
    with open(SUMMARY) as f:
        return json.load(f)


def test_invariant_included_plus_excluded_equals_candidate():
    s = _regenerate()
    assert s["invariant_holds"] is True
    assert s["included_truth_surfaces"] + s["excluded_with_reason"] == s["candidate_universe"]


def test_no_open_or_unclassified_surfaces():
    s = _regenerate()
    assert s["open_needs_proof"] == 0, f"OPEN surfaces must be 0: {s.get('open_locs')}"
    # every included surface must have one of the final dispositions
    allowed = {"CANONICAL_KPI", "CANONICAL_STATUS", "DIRECT_FACT",
               "GOVERNED_DISTINCT_VARIANT", "NON_TRUTH_SURFACE_EXCLUDED_WITH_REASON"}
    assert set(s["by_disposition"]).issubset(allowed), s["by_disposition"]


def test_denominator_is_reproducible_and_locked():
    s = _regenerate()
    included = s["included_truth_surfaces"]
    delta = abs(included - BASELINE_INCLUDED)
    assert delta <= BASELINE_TOLERANCE, (
        f"Truth-surface denominator drift: baseline={BASELINE_INCLUDED} now={included}. "
        "A truth-bearing surface appeared/disappeared. Reconcile in the register and "
        "update BASELINE_INCLUDED with a governed reason.")
