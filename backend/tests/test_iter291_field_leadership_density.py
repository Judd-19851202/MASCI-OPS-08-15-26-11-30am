"""
iter291 · Field-Leadership umbrella coaching density lift test.

Bounded closure of the FL coaching-thin matrix row. Pre-iter291:
  - 6 tips on `field-leadership.records` + `.review-tone` (umbrella)
  - 3 of 10 FL record kinds wired to coaching families
    (`checkout`/`writeup`/`crew_eval`)
  - 7 FL record kinds were coaching-orphan: verbal_coaching,
    attendance, recognition, new_employee_eval,
    promotion_recommendation, training_deficiency, supervisor_notes

iter291 closes those 7 orphans + adds one cross-cutting umbrella
sub-key (`field-leadership.records.follow-through`) without
restructuring the FL umbrella, without adding new UI components,
and without LMS / management-theory drift.

What this test locks:
  - All 7 previously-orphan FL kinds now have ≥2 operationally
    meaningful tips each
  - New `field-leadership.records.follow-through` sub-key has why+next
  - EN/ES parity on every new tip
  - Scope locked to {leadership, admin} (PM optionally for the
    umbrella sub-keys that PM reads)
  - No LMS / corporate-leadership / management-theory drift
  - Total FL-family tip count crossed the audit threshold of ≥10
  - All 10 FL record kinds are now either coached directly or
    explicitly wired through `FL_KIND_HELPTIP_FORMKEY`
"""
import sys
import pathlib
import re

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import pytest

from guidance.tips import all_tips


ITER291_KINDS = (
    "verbal_coaching",
    "attendance",
    "recognition",
    "new_employee_eval",
    "promotion_recommendation",
    "training_deficiency",
    "supervisor_notes",
)

# All 10 FL record kinds present in the FL workflow.
FL_RECORD_KINDS = (
    "equipment_checkout",   # → checkout
    "write_up",             # → writeup
    "crew_eval",
    "verbal_coaching",
    "attendance",
    "recognition",
    "new_employee_eval",
    "promotion_recommendation",
    "training_deficiency",
    "supervisor_notes",
)

# The 3 FL kinds wired before iter291 (they map to non-FL prefix keys).
PRE_ITER291_MAPPED_KEYS = {
    "equipment_checkout": "checkout",
    "write_up": "writeup",
    "crew_eval": "crew_eval",
}


def _tips_for(form_key):
    return [t for t in all_tips() if t.get("form_key") == form_key]


# ─── Per-kind coverage (iter291 closures) ────────────────────────


@pytest.mark.parametrize("kind", ITER291_KINDS)
def test_each_iter291_kind_has_at_least_two_tips(kind):
    tips = _tips_for(kind)
    assert len(tips) >= 2, \
        f"FL kind '{kind}' must have ≥2 operationally meaningful tips · has {len(tips)}"


@pytest.mark.parametrize("kind", ITER291_KINDS)
def test_each_iter291_kind_has_why_tip(kind):
    """Every closure includes a 'why' so the operator understands the
    operational anchor of the record kind."""
    kinds = {t["kind"] for t in _tips_for(kind)}
    assert "why" in kinds, f"FL kind '{kind}' missing 'why' tip"


@pytest.mark.parametrize("kind", ITER291_KINDS)
def test_each_iter291_kind_has_es_counterpart(kind):
    not_merged = []
    for t in _tips_for(kind):
        if not t.get("title_es") or not t.get("body_es"):
            not_merged.append(t["kind"])
    assert not not_merged, \
        f"FL kind '{kind}' has ES merge gaps on: {not_merged}"


@pytest.mark.parametrize("kind", ITER291_KINDS)
def test_each_iter291_kind_uses_leadership_or_admin_scope_only(kind):
    bad = []
    for t in _tips_for(kind):
        scopes = set(t.get("scopes") or [])
        if scopes - {"leadership", "admin", "pm"}:
            bad.append((t["kind"], scopes))
    assert not bad, f"FL kind '{kind}' has out-of-scope tips: {bad}"


# ─── Umbrella sub-key (follow-through) ───────────────────────────


def test_follow_through_sub_key_has_required_kinds():
    tips = _tips_for("field-leadership.records.follow-through")
    kinds = {t["kind"] for t in tips}
    assert {"why", "next"}.issubset(kinds), \
        f"follow-through sub-key missing why/next · has {kinds}"


def test_follow_through_sub_key_has_es_parity():
    tips = _tips_for("field-leadership.records.follow-through")
    for t in tips:
        assert t.get("title_es") and t.get("body_es"), \
            f"follow-through {t['kind']} missing ES"


# ─── Umbrella density (matrix threshold) ─────────────────────────


def test_total_field_leadership_namespace_tip_count_at_least_ten():
    """The matrix threshold for 'coaching parity' on the FL umbrella
    is ≥10 tips in the `field-leadership.*` namespace."""
    count = sum(1 for t in all_tips()
                if (t.get("form_key") or "").startswith("field-leadership"))
    assert count >= 10, f"FL umbrella tip count too low: {count}"


def test_total_fl_workflow_coverage_at_least_thirty():
    """Cross-check: counting `field-leadership.*` + the per-kind
    families (checkout, writeup, crew_eval, and the 7 iter291 closures)
    the workflow should now carry ≥30 tips total — comfortably above
    the audit threshold without inflation."""
    total = sum(1 for t in all_tips()
                if (t.get("form_key") or "").startswith("field-leadership")
                or t.get("form_key") in
                ("checkout", "writeup", "crew_eval")
                or (t.get("form_key") or "").startswith("checkout.")
                or (t.get("form_key") or "").startswith("writeup.")
                or (t.get("form_key") or "").startswith("crew_eval.")
                or t.get("form_key") in ITER291_KINDS)
    assert total >= 30, f"FL workflow total coverage too low: {total}"


# ─── Every FL kind is now reachable from the FormPage ────────────


def test_every_fl_kind_is_now_coached_or_mapped():
    """No orphan FL record kinds left after iter291. Each kind either
    has its own coaching family or maps to a non-FL-prefix family
    (the 3 pre-existing maps)."""
    for kind in FL_RECORD_KINDS:
        if kind in PRE_ITER291_MAPPED_KEYS:
            mapped = PRE_ITER291_MAPPED_KEYS[kind]
            assert _tips_for(mapped), \
                f"FL kind '{kind}' maps to '{mapped}' but that family is empty"
        else:
            assert _tips_for(kind), \
                f"FL kind '{kind}' has no coaching family (iter291 orphan)"


# ─── Tone discipline ─────────────────────────────────────────────


def test_no_lms_or_management_theory_drift_in_iter291():
    """iter291 is operational foreman/superintendent voice — never
    LMS / management-conference / culture-building rhetoric. This
    is the test that protects the umbrella from philosophy drift."""
    banned = [
        re.compile(r"\bempower\b", re.I),
        re.compile(r"\bleverage\b", re.I),
        re.compile(r"\bstakeholders?\b", re.I),
        re.compile(r"\bjourney\b", re.I),
        re.compile(r"\bculture of\b", re.I),
        re.compile(r"\bbest practices?\b", re.I),
        re.compile(r"\bsynerg", re.I),
        re.compile(r"\bcoaching culture\b", re.I),
        re.compile(r"\bleadership journey\b", re.I),
        re.compile(r"\bfield excellence\b", re.I),
        re.compile(r"\bperformance management\b", re.I),
        re.compile(r"\bgrowth mindset\b", re.I),
        # Spanish equivalents
        re.compile(r"\bempoderar\b", re.I),
        re.compile(r"\bsinergia\b", re.I),
        re.compile(r"\bcultura de liderazgo\b", re.I),
    ]
    iter291_form_keys = set(ITER291_KINDS) | {
        "field-leadership.records.follow-through",
    }
    hits = []
    for t in all_tips():
        if t.get("form_key") not in iter291_form_keys:
            continue
        for field in ("title", "body", "title_es", "body_es"):
            text = t.get(field, "") or ""
            for pat in banned:
                m = pat.search(text)
                if m:
                    hits.append((t["form_key"], t["kind"], field, m.group()))
    assert not hits, f"iter291 LMS / management-theory drift: {hits}"


# ─── No-collision guards ─────────────────────────────────────────


def test_iter291_kinds_do_not_collide_with_existing_form_keys():
    """The 7 new kinds use the kind name itself as the form_key (to
    match the established `crew_eval` / `writeup` / `checkout`
    pattern). Make sure none of them collide with an unrelated
    pre-existing family elsewhere in tips.py."""
    for kind in ITER291_KINDS:
        same_key_tips = _tips_for(kind)
        scopes_seen = set()
        for t in same_key_tips:
            scopes_seen.update(t.get("scopes") or [])
        # All tips for this form_key should share leadership/admin/pm scope
        assert scopes_seen <= {"leadership", "admin", "pm"}, \
            f"FL kind '{kind}' form_key collides with non-FL family: scopes={scopes_seen}"


# ─── Operational-anchor sanity checks ────────────────────────────


def test_attendance_why_tip_uses_pattern_framing():
    """Operational anchor for attendance: one day = data, three days
    = pattern, five days = problem. Verify the framing is locked in
    BOTH languages so future edits don't drift into 'absenteeism'
    policy language."""
    by = {(t["form_key"], t["kind"]): t for t in _tips_for("attendance")}
    why = by[("attendance", "why")]
    en = (why.get("body") or "").lower()
    es = (why.get("body_es") or "").lower()
    assert "pattern" in en or "data point" in en
    assert "patrón" in es or "dato" in es


def test_recognition_mistake_explicitly_calls_out_wallpaper():
    """Operational anchor: generic recognition is 'wallpaper'. Make
    sure the mistake tip names that anchor in BOTH languages."""
    by = {(t["form_key"], t["kind"]): t for t in _tips_for("recognition")}
    mistake = by[("recognition", "mistake")]
    en = (mistake.get("body") or "").lower()
    es = (mistake.get("body_es") or "").lower()
    assert "wallpaper" in en, f"EN mistake tip must call out wallpaper anchor: {en[:200]}"
    assert "papel tapiz" in es or "wallpaper" in es


def test_supervisor_notes_mistake_explicitly_bans_vent_file():
    """Operational anchor: supervisor_notes is not a vent file. Lock
    that boundary in BOTH languages — this is the single biggest
    misuse-risk on the FL umbrella."""
    by = {(t["form_key"], t["kind"]): t for t in _tips_for("supervisor_notes")}
    mistake = by[("supervisor_notes", "mistake")]
    en = (mistake.get("body") or "").lower()
    es = (mistake.get("body_es") or "").lower()
    assert "vent" in en, f"EN supervisor_notes mistake tip must ban vent-file: {en[:200]}"
    assert "queja" in es or "vent" in es
