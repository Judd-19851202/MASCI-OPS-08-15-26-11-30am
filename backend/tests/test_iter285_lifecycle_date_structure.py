"""
iter285 · Employment Lifecycle Date Structure regression test.

Locks in the bounded operational scope from the iter284 audit:
  - 5 new lifecycle date fields (plus separation_type enum) accepted on
    create + patch + status-change
  - `original_hire_date` write-once enforcement (audit §2.2 / §6 risk #1)
  - separation_type required on transitions into Terminated/Resigned/Retired
  - leave_start_date auto-populated on Leave of Absence transition
  - termination_date + last_day_worked auto-populated on offboarding
    transition when not supplied
  - Read-time derived `tenure_days` is present on every response (never
    stored on the document)
  - Date validators reject malformed strings
  - enum validators reject unknown separation types
  - Coaching family extension (employee-lifecycle.lifecycle-dates +
    .separation) has canonical EN+ES parity at load time

This iteration does NOT touch driver-qualification fields (iter286
scope), endorsements (iter287), or dashboards (iter288). Tests
that would belong to those iterations are deliberately absent.
"""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import pytest
from datetime import date, timedelta

from routes.employee_lifecycle import (
    EmployeeCreate, EmployeePatch, StatusChange,
    ALLOWED_LIFECYCLE_STATUSES, ALLOWED_SEPARATION_TYPES,
    _is_date_string, _tenure_days,
    _LIFECYCLE_DATE_FIELDS, _WRITE_ONCE_FIELDS,
)
from guidance.tips import all_tips


# ─── Schema / validator unit tests ───────────────────────────────


def test_separation_type_enum_is_exactly_three_values():
    assert ALLOWED_SEPARATION_TYPES == {"voluntary", "involuntary", "layoff"}


def test_lifecycle_date_fields_enumerate_the_five_required_fields():
    """Audit §2.1 listed exactly 5 missing date fields. iter285 added
    all 5; iter316 added the sixth (rehire_date) as part of the
    operator-mandated rehire eligibility + reactivation closure."""
    assert set(_LIFECYCLE_DATE_FIELDS) == {
        "original_hire_date",
        "last_day_worked",
        "termination_date",
        "leave_start_date",
        "expected_return_date",
        # iter316 · rehire-cycle date — protected by validators but
        # NOT write-once (unlike original_hire_date).
        "rehire_date",
    }


def test_original_hire_date_is_the_write_once_field():
    """The audit's highest structural risk (§6 risk #1) was hire-date
    overwrite. The protection lives on original_hire_date, NOT on the
    legacy hire_date field (which stays patchable for backward compat)."""
    assert "original_hire_date" in _WRITE_ONCE_FIELDS
    assert "hire_date" not in _WRITE_ONCE_FIELDS


def test_create_accepts_all_five_lifecycle_dates_and_separation_type():
    body = EmployeeCreate(
        name="Test Employee A",
        original_hire_date="2020-03-15",
        last_day_worked="2026-01-30",
        termination_date="2026-02-01",
        leave_start_date="",  # empty allowed
        expected_return_date=None,  # null allowed
        separation_type="voluntary",
    )
    assert body.original_hire_date == "2020-03-15"
    assert body.separation_type == "voluntary"


def test_patch_validates_date_format():
    with pytest.raises(ValueError):
        EmployeePatch(termination_date="01/30/2026")  # wrong format
    with pytest.raises(ValueError):
        EmployeePatch(leave_start_date="not-a-date")
    # Empty string is fine (means "clear")
    p = EmployeePatch(termination_date="")
    assert p.termination_date == ""


def test_patch_rejects_unknown_separation_type():
    with pytest.raises(ValueError):
        EmployeePatch(separation_type="fired")  # not in enum
    with pytest.raises(ValueError):
        EmployeePatch(separation_type="redundancy")
    # The three legitimate values pass
    for s in ("voluntary", "involuntary", "layoff"):
        EmployeePatch(separation_type=s)


def test_status_change_validates_dates_and_separation_type():
    sc = StatusChange(
        lifecycle_status="Terminated",
        separation_type="layoff",
        last_day_worked="2026-02-15",
    )
    assert sc.separation_type == "layoff"
    with pytest.raises(ValueError):
        StatusChange(lifecycle_status="Terminated", separation_type="quit")


# ─── _is_date_string unit tests ──────────────────────────────────


def test_is_date_string_accepts_iso_yyyy_mm_dd():
    assert _is_date_string("2026-05-20")
    assert _is_date_string("2026-05-20T14:30:00Z")  # prefix is enough
    assert _is_date_string("")  # empty allowed
    assert _is_date_string(None)  # null allowed


def test_is_date_string_rejects_bad_formats():
    assert not _is_date_string("05/20/2026")
    assert not _is_date_string("2026/05/20")
    assert not _is_date_string("2026-5-20")  # missing zero-pad
    assert not _is_date_string("hello")
    assert not _is_date_string(123)


# ─── _tenure_days derivation tests ───────────────────────────────


def test_tenure_days_returns_none_when_no_hire_date():
    assert _tenure_days({}) is None
    assert _tenure_days({"original_hire_date": ""}) is None


def test_tenure_days_prefers_original_hire_date():
    """If both legacy hire_date AND original_hire_date exist, the
    write-once original wins."""
    today = date.today()
    five_years_ago = (today - timedelta(days=5 * 365)).isoformat()
    one_year_ago = (today - timedelta(days=365)).isoformat()
    tenure = _tenure_days({
        "original_hire_date": five_years_ago,
        "hire_date": one_year_ago,
    })
    assert tenure is not None
    assert 5 * 365 - 1 <= tenure <= 5 * 365 + 1


def test_tenure_days_falls_back_to_legacy_hire_date():
    """When original_hire_date is unset, the function still derives
    from the legacy hire_date so iter285 doesn't regress employees who
    only have the legacy field populated."""
    today = date.today()
    two_years_ago = (today - timedelta(days=2 * 365)).isoformat()
    tenure = _tenure_days({"hire_date": two_years_ago})
    assert tenure is not None
    assert 2 * 365 - 1 <= tenure <= 2 * 365 + 1


def test_tenure_days_freezes_at_termination_for_offboarded_employees():
    """A terminated employee's tenure shouldn't keep counting up after
    their last day. Use termination_date (preferred) or last_day_worked."""
    tenure = _tenure_days({
        "original_hire_date": "2020-01-01",
        "termination_date": "2025-01-01",
        "lifecycle_status": "Terminated",
    })
    # 2020-01-01 → 2025-01-01 = ~5 years
    assert tenure is not None
    assert 5 * 365 - 5 <= tenure <= 5 * 365 + 5


def test_tenure_days_never_negative():
    """Future hire date (data-entry mistake) shouldn't return a negative."""
    future = (date.today() + timedelta(days=30)).isoformat()
    assert _tenure_days({"original_hire_date": future}) == 0


# ─── Coaching family parity tests ────────────────────────────────


def _elc_tips():
    return [
        t for t in all_tips()
        if (t.get("form_key") or "").startswith("employee-lifecycle")
    ]


def test_new_section_keys_present_with_expected_kinds():
    by_fk = {}
    for t in _elc_tips():
        by_fk.setdefault(t["form_key"], set()).add(t["kind"])
    assert by_fk.get("employee-lifecycle.lifecycle-dates") == {"why", "mistake", "next"}
    assert by_fk.get("employee-lifecycle.separation") == {"why", "mistake", "escalate"}


def test_every_new_tip_has_es_counterpart_merged():
    new_keys = (
        [("employee-lifecycle.lifecycle-dates", k) for k in ("why", "mistake", "next")]
        + [("employee-lifecycle.separation", k) for k in ("why", "mistake", "escalate")]
    )
    by_key = {(t["form_key"], t["kind"]): t for t in _elc_tips()}
    missing_es = []
    for key in new_keys:
        t = by_key.get(key)
        assert t is not None, f"missing tip {key}"
        if not t.get("title_es") or not t.get("body_es"):
            missing_es.append(key)
    assert not missing_es, f"ES merge incomplete on: {missing_es}"


def test_new_tips_use_hr_or_admin_scope_only():
    """Surface is HR portal; admin can view via shadow. Field/dispatch
    should NOT see these tips because the surface isn't on their portal."""
    bad = []
    for t in _elc_tips():
        if t["form_key"] not in (
            "employee-lifecycle.lifecycle-dates",
            "employee-lifecycle.separation",
        ):
            continue
        scopes = set(t.get("scopes") or [])
        if scopes - {"hr", "admin"}:
            bad.append((t["form_key"], t["kind"], scopes))
    assert not bad, f"new tips have wrong scopes: {bad}"


def test_no_lms_drift_in_iter285_tips():
    import re
    banned = [
        re.compile(r"\bbest practices?\b", re.I),
        re.compile(r"\bempower\b", re.I),
        re.compile(r"\bleverage\b", re.I),
        re.compile(r"\bstakeholders?\b", re.I),
        re.compile(r"\bjourney\b", re.I),
        re.compile(r"\bculture of\b", re.I),
    ]
    hits = []
    for t in _elc_tips():
        if t["form_key"] not in (
            "employee-lifecycle.lifecycle-dates",
            "employee-lifecycle.separation",
        ):
            continue
        for field in ("title", "body", "title_es", "body_es"):
            text = t.get(field, "") or ""
            for pat in banned:
                m = pat.search(text)
                if m:
                    hits.append((t["form_key"], t["kind"], field, m.group()))
    assert not hits, f"LMS drift in iter285 tips: {hits}"
