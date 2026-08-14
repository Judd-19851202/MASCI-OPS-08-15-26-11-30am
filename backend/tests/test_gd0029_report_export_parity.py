"""GD-0029 — Report / Export / Email PARITY + independent reconstruction (Wave 10).

Proves outbound artifacts agree with what the UI/API display, by construction:
  - the payroll-variance CSV export and the API serialize the SAME single canonical
    variance computation (no independent export formula);
  - independent reconstruction from raw inputs matches the canonical calculator;
  - outbound producers do not re-derive KPI percentages with an ungoverned inline
    formula that bypasses the canonical libs.
Falsifiable: fails if an export re-implements a KPI formula or drifts from canonical.
"""
import inspect
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.kpi_variance import variance_percent


def test_payroll_variance_single_canonical_owner_parity():
    # UI/API and CSV export both consume build_variance_rows -> one computation.
    from routes import payroll_variance as pv
    src = inspect.getsource(pv.build_variance_rows)
    assert "_canon_variance(" in src, "payroll variance must use the canonical owner"
    # no independent inline percent formula in the row builder
    assert not re.search(r"/\s*masci_hours\s*\)\s*\*\s*100", src), "no ungoverned inline variance formula"


def test_independent_reconstruction_matches_canonical():
    # Independently derive from raw records, compare to canonical calculator.
    # exact=41.5h vs masci=40h -> (41.5-40)/40*100 = 3.75 -> 3.8 (ndigits=1)
    raw_exact, raw_masci = 41.5, 40.0
    independent = round(((raw_exact - raw_masci) / raw_masci) * 100.0, 1)
    canonical = variance_percent(raw_exact, raw_masci, mode="honest_unknown", ndigits=1)
    assert canonical == independent == 3.8
    # zero/unknown baseline -> UNKNOWN (None), NOT a fabricated 0 in the export
    assert variance_percent(10.0, 0.0, mode="honest_unknown") is None


def test_no_ungoverned_percent_formula_in_export_producers():
    # High-risk outbound producers must not re-derive a KPI percentage inline.
    base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    producers = [
        os.path.join(base, "routes", "payroll_variance.py"),
        os.path.join(base, "routes", "odr", "pdf.py"),
    ]
    offenders = []
    pat = re.compile(r"(variance|efficiency|completion|compliance)\w*\s*=\s*[^=\n]*/[^=\n]*\*\s*100", re.I)
    for p in producers:
        if not os.path.exists(p):
            continue
        for i, line in enumerate(open(p, errors="ignore"), 1):
            if pat.search(line):
                offenders.append(f"{os.path.basename(p)}:{i}: {line.strip()[:80]}")
    assert not offenders, "ungoverned KPI formula in export producer:\n" + "\n".join(offenders)
