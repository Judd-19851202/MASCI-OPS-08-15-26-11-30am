"""
iter282 · HR Payroll Variance coaching-family parity regression test.

Locks in the new coaching family for `payroll-variance` and its
section keys:
  - payroll-variance (top family · canonical 4: why/who/next/escalate)
  - payroll-variance.upload (why · mistake)
  - payroll-variance.batches (why · next)
  - payroll-variance.row-decision (why · next · escalate)
  - payroll-variance.dispute (why · escalate)

Scope discipline (per user directive · coaching-family parity closure
only): no variance logic changes · no CSV parser changes · no UI
restructure. Backend regression test mirrors the iter273/iter274/iter275
pattern.
"""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from guidance.tips import all_tips
from guidance.tips_es import TIPS_ES


PAYROLL_VARIANCE_FORM_KEYS = {
    "payroll-variance",
    "payroll-variance.upload",
    "payroll-variance.batches",
    "payroll-variance.row-decision",
    "payroll-variance.dispute",
}

CANONICAL_4 = {"why", "who", "next", "escalate"}


def _pv_tips():
    return [
        t for t in all_tips()
        if (t.get("form_key") or "").split(".")[0] == "payroll-variance"
        or t.get("form_key") == "payroll-variance"
    ]


def test_payroll_variance_family_exists():
    keys = {t["form_key"] for t in _pv_tips()}
    missing = PAYROLL_VARIANCE_FORM_KEYS - keys
    assert not missing, f"Missing payroll-variance form_keys: {missing}"


def test_top_family_has_canonical_four_kinds():
    top = {t["kind"] for t in _pv_tips() if t["form_key"] == "payroll-variance"}
    missing = CANONICAL_4 - top
    assert not missing, f"Top family missing canonical kinds: {missing}"


def test_total_tip_count_at_least_13():
    """Author-time count: 4 (top) + 2 (upload) + 2 (batches) + 3 (row-decision) + 2 (dispute) = 13."""
    pv = _pv_tips()
    assert len(pv) >= 13, f"Expected >=13 payroll-variance tips, got {len(pv)}"


def test_each_section_key_has_at_least_one_tip():
    by_fk = {}
    for t in _pv_tips():
        by_fk.setdefault(t["form_key"], []).append(t)
    for fk in PAYROLL_VARIANCE_FORM_KEYS:
        assert by_fk.get(fk), f"Form-key {fk!r} has no tips"


def test_all_pv_tips_have_hr_scope():
    """Surface is HR portal only; every tip must include 'hr' in its scopes."""
    bad = [
        (t["form_key"], t["kind"])
        for t in _pv_tips()
        if "hr" not in (t.get("scopes") or [])
    ]
    assert not bad, f"PV tips missing 'hr' scope: {bad}"


def test_every_pv_tip_has_es_counterpart():
    missing = []
    for t in _pv_tips():
        key = (t["form_key"], t["kind"])
        if key not in TIPS_ES:
            missing.append(key)
    assert not missing, f"PV tips missing ES counterpart: {missing}"


def test_es_merge_lands_on_tips_at_load_time():
    """guidance.tips._merge_es should have populated title_es/body_es on every PV tip."""
    not_merged = []
    for t in _pv_tips():
        if not t.get("title_es") or not t.get("body_es"):
            not_merged.append((t["form_key"], t["kind"]))
    assert not not_merged, f"PV tips missing merged ES content: {not_merged}"


def test_no_lms_drift_in_pv_tips():
    """Spot-check: the iter282 tone discipline forbids corporate/LMS phrasing."""
    import re
    banned = [
        re.compile(r"\bbest practices?\b", re.I),
        re.compile(r"\bempower(?:ing|s)?\b", re.I),
        re.compile(r"\bleverag(?:e|ing)\b", re.I),
        re.compile(r"\bstakeholders?\b", re.I),
        re.compile(r"\bjourney\b", re.I),
        re.compile(r"\bculture of\b", re.I),
        re.compile(r"\bsynergies\b", re.I),
    ]
    hits = []
    for t in _pv_tips():
        text = " ".join([
            t.get("title", "") or "",
            t.get("body", "") or "",
            t.get("title_es", "") or "",
            t.get("body_es", "") or "",
        ])
        for pat in banned:
            m = pat.search(text)
            if m:
                hits.append((t["form_key"], t["kind"], pat.pattern, m.group()))
    assert not hits, f"LMS drift in PV tips: {hits}"
