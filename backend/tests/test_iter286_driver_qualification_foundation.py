"""
iter286 · Driver Qualification Foundation regression test.

Locks in the bounded operational scope from the iter284 audit (§8.2):
  - 7 new driver-qualification fields persisted (cdl_holder ·
    approved_company_driver · driver_status · cdl_license_number ·
    cdl_state · cdl_expiration_date · medical_card_expiration_date)
  - CDL Holder ≠ Approved Company Driver — the two flags are
    structurally independent (test: every combination of (cdl_holder,
    approved_company_driver) is acceptable; the dangerous combination
    is detectable but NOT auto-corrected)
  - driver_status enum validation
  - Date-format validation on the two new date fields
  - Coaching family `driver-qualification.*` carries canonical 4 on
    top family + EN/ES parity merged at load time
  - Scope locked to {hr, admin} — never field/dispatch on this surface
  - LMS-drift ban honored

iter286 does NOT touch:
  - endorsements (iter287)
  - dashboards (iter288)
  - Motive/MaintainX integration
  - dispatch assignment logic
  - auto-revocation of approved_company_driver on expiration
"""
import sys
import pathlib
import re

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import pytest

from routes.employee_lifecycle import (
    EmployeeCreate, EmployeePatch,
    ALLOWED_DRIVER_STATUSES, _DRIVER_QUALIFICATION_FIELDS,
)
from guidance.tips import all_tips


# ─── Taxonomy + field set unit tests ─────────────────────────────


def test_driver_status_enum_is_exactly_four_values():
    """The audit specified 4 driver statuses. No more, no less."""
    assert ALLOWED_DRIVER_STATUSES == {
        "active", "suspended", "restricted", "inactive",
    }


def test_driver_qualification_field_set_is_exactly_seven_fields():
    assert set(_DRIVER_QUALIFICATION_FIELDS) == {
        "cdl_holder",
        "approved_company_driver",
        "driver_status",
        "cdl_license_number",
        "cdl_state",
        "cdl_expiration_date",
        "medical_card_expiration_date",
    }


# ─── Schema acceptance tests ─────────────────────────────────────


def test_create_accepts_all_seven_driver_fields():
    body = EmployeeCreate(
        name="Test Driver",
        cdl_holder=True,
        approved_company_driver=True,
        driver_status="active",
        cdl_license_number="TX1234567",
        cdl_state="TX",
        cdl_expiration_date="2027-06-30",
        medical_card_expiration_date="2026-12-15",
    )
    assert body.cdl_holder is True
    assert body.approved_company_driver is True
    assert body.driver_status == "active"
    assert body.cdl_license_number == "TX1234567"
    assert body.cdl_state == "TX"


def test_patch_accepts_all_seven_driver_fields():
    p = EmployeePatch(
        cdl_holder=False,
        approved_company_driver=False,
        driver_status="inactive",
        cdl_license_number="CA9876543",
        cdl_state="CA",
        cdl_expiration_date="2025-01-01",
        medical_card_expiration_date="2024-08-20",
    )
    assert p.driver_status == "inactive"
    assert p.cdl_state == "CA"


# ─── CDL Holder vs Approved Company Driver independence ─────────


@pytest.mark.parametrize("cdl,approved", [
    (True,  True),   # CDL + approved → legitimate operator
    (True,  False),  # CDL + not approved → the operationally critical case
    (False, False),  # Neither → non-driver employee
    (False, True),   # No CDL + approved → structurally allowed but unusual
])
def test_cdl_and_approved_are_independent_flags(cdl, approved):
    """Every combination of (cdl_holder, approved_company_driver) must
    be acceptable. The audit's central distinction is that these are
    two INDEPENDENT decisions — the schema must reflect that.
    Conflating them into a single field would erase the protection."""
    body = EmployeeCreate(
        name=f"Test {cdl}/{approved}",
        cdl_holder=cdl,
        approved_company_driver=approved,
    )
    assert body.cdl_holder is cdl
    assert body.approved_company_driver is approved


# ─── Enum / date validators ──────────────────────────────────────


def test_driver_status_rejects_unknown_values():
    with pytest.raises(ValueError):
        EmployeePatch(driver_status="probation")  # not in enum
    with pytest.raises(ValueError):
        EmployeePatch(driver_status="terminated")  # employment status, not driver status
    # The four legitimate values pass
    for s in ALLOWED_DRIVER_STATUSES:
        EmployeePatch(driver_status=s)


def test_driver_status_empty_string_is_allowed():
    """Empty string clears the field — same convention as date fields."""
    p = EmployeePatch(driver_status="")
    assert p.driver_status == ""


def test_cdl_and_medical_card_dates_validate_format():
    with pytest.raises(ValueError):
        EmployeePatch(cdl_expiration_date="06/30/2027")
    with pytest.raises(ValueError):
        EmployeePatch(medical_card_expiration_date="not-a-date")
    # ISO format passes
    EmployeePatch(cdl_expiration_date="2027-06-30")
    EmployeePatch(medical_card_expiration_date="2026-12-15")


# ─── Coaching family parity ──────────────────────────────────────


def _dq_tips():
    return [
        t for t in all_tips()
        if (t.get("form_key") or "").startswith("driver-qualification")
    ]


def test_driver_qualification_top_family_has_canonical_four_kinds():
    top = {t["kind"] for t in _dq_tips() if t["form_key"] == "driver-qualification"}
    missing = {"why", "who", "next", "escalate"} - top
    assert not missing, f"Top family missing canonical kinds: {missing}"


def test_section_keys_present_with_expected_kinds():
    by_fk = {}
    for t in _dq_tips():
        by_fk.setdefault(t["form_key"], set()).add(t["kind"])
    assert by_fk.get("driver-qualification.cdl-vs-approved") == {"why", "mistake"}
    assert by_fk.get("driver-qualification.expirations") == {"why", "next", "escalate"}


def test_total_dq_tip_count_at_least_nine():
    """4 (top) + 2 (cdl-vs-approved) + 3 (expirations) = 9."""
    assert len(_dq_tips()) >= 9


def test_every_dq_tip_has_es_counterpart_merged():
    not_merged = []
    for t in _dq_tips():
        if not t.get("title_es") or not t.get("body_es"):
            not_merged.append((t["form_key"], t["kind"]))
    assert not not_merged, f"ES merge incomplete: {not_merged}"


def test_all_dq_tips_use_hr_or_admin_scope_only():
    """Surface is HR portal only. Dispatch and fleet will consume the
    data via read-only surfaces in iter288 — NOT here."""
    bad = []
    for t in _dq_tips():
        scopes = set(t.get("scopes") or [])
        if scopes - {"hr", "admin"}:
            bad.append((t["form_key"], t["kind"], scopes))
    assert not bad, f"DQ tips have non-HR scopes: {bad}"


def test_no_lms_drift_in_iter286_tips():
    banned = [
        re.compile(r"\bbest practices?\b", re.I),
        re.compile(r"\bempower\b", re.I),
        re.compile(r"\bleverage\b", re.I),
        re.compile(r"\bstakeholders?\b", re.I),
        re.compile(r"\bjourney\b", re.I),
        re.compile(r"\bculture of\b", re.I),
    ]
    hits = []
    for t in _dq_tips():
        for field in ("title", "body", "title_es", "body_es"):
            text = t.get(field, "") or ""
            for pat in banned:
                m = pat.search(text)
                if m:
                    hits.append((t["form_key"], t["kind"], field, m.group()))
    assert not hits, f"LMS drift in iter286 tips: {hits}"


def test_cdl_vs_approved_distinction_is_explicit_in_coaching():
    """The audit's central operational distinction must be coached
    explicitly somewhere in the family — the field is too important to
    rely on intuition. Verify the phrase appears in at least one tip
    in BOTH languages."""
    by_key = {(t["form_key"], t["kind"]): t for t in _dq_tips()}
    tip = by_key[("driver-qualification.cdl-vs-approved", "why")]
    en = (tip.get("body") or "")
    es = (tip.get("body_es") or "")
    # English explicitly says the two are not the same
    assert "two separate fields" in (tip.get("title") or "").lower() or \
        ("MASCI" in en and "decision" in en.lower())
    # Spanish equivalent — "decisión" + "campos separados"
    assert "decisión" in es.lower() and "separados" in es.lower()


def test_iter285_lifecycle_tests_still_pass_via_no_field_collision():
    """Sanity: iter286 added 7 fields to the same models that iter285
    extended. Make sure the field names don't collide with anything
    iter285 introduced."""
    iter285_fields = {
        "original_hire_date", "last_day_worked", "termination_date",
        "leave_start_date", "expected_return_date", "separation_type",
    }
    iter286_fields = set(_DRIVER_QUALIFICATION_FIELDS)
    assert not (iter285_fields & iter286_fields), \
        f"Field-name collision between iter285 and iter286: " \
        f"{iter285_fields & iter286_fields}"
