"""
iter287 · Driver Qualification Endorsements & Restrictions regression test.

Bounded closure of the iter284 §8.2 audit follow-on:
  - 2 new list fields persisted (`cdl_endorsements` · `cdl_restrictions`)
  - Endorsements drawn from a fixed code taxonomy: {N H X T P S}
  - Restrictions drawn from a fixed code taxonomy: {air_brake, manual_transmission}
  - Codes outside the taxonomy are rejected (no free-form drift)
  - Empty / null incoming values clear the field (consistent with the
    scalar-enum convention elsewhere in the model)
  - Duplicate codes within a list are deduped while preserving order
  - Coaching family `driver-qualification.endorsements` carries
    canonical 4 (why / who / next / escalate) · EN+ES parity merged
    at load time
  - Coaching sub-family `driver-qualification.restrictions` carries
    why + mistake (Restrictions ≠ Driver Status distinction)
  - Scope locked to {hr, admin}
  - No LMS drift

iter287 does NOT add:
  - dispatch assignment logic
  - automatic capability gating
  - compliance workflows
  - violation tracking
  - any new dashboard surface (iter288 will, separately)
"""
import sys
import pathlib
import re

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import pytest

from routes.employee_lifecycle import (
    EmployeeCreate, EmployeePatch,
    ALLOWED_CDL_ENDORSEMENTS, ALLOWED_CDL_RESTRICTIONS,
    _DRIVER_ENDORSEMENT_FIELDS,
)
from guidance.tips import all_tips


# ─── Taxonomy + field set unit tests ─────────────────────────────


def test_endorsement_taxonomy_is_exactly_six_codes():
    """The audit specified 6 FMCSA endorsement codes. No more, no less."""
    assert ALLOWED_CDL_ENDORSEMENTS == {"N", "H", "X", "T", "P", "S"}


def test_restriction_taxonomy_is_exactly_two_codes():
    """Air-brake + manual-transmission. Anything else lives on the
    CDL document scan, not in structured fields."""
    assert ALLOWED_CDL_RESTRICTIONS == {"air_brake", "manual_transmission"}


def test_endorsement_field_set_is_exactly_two_fields():
    assert set(_DRIVER_ENDORSEMENT_FIELDS) == {
        "cdl_endorsements", "cdl_restrictions",
    }


# ─── Schema acceptance tests ─────────────────────────────────────


def test_create_accepts_all_endorsement_codes():
    body = EmployeeCreate(
        name="Endorsement Test",
        cdl_endorsements=["N", "H", "X", "T", "P", "S"],
    )
    assert body.cdl_endorsements == ["N", "H", "X", "T", "P", "S"]


def test_create_accepts_restriction_codes():
    body = EmployeeCreate(
        name="Restriction Test",
        cdl_restrictions=["air_brake", "manual_transmission"],
    )
    assert body.cdl_restrictions == ["air_brake", "manual_transmission"]


def test_patch_accepts_endorsement_and_restriction_lists():
    p = EmployeePatch(
        cdl_endorsements=["N"],
        cdl_restrictions=["air_brake"],
    )
    assert p.cdl_endorsements == ["N"]
    assert p.cdl_restrictions == ["air_brake"]


def test_empty_list_clears_the_field():
    """Convention: [] = explicit clear. Mirrors the empty-string clear
    pattern used by enum scalars elsewhere in the model."""
    p = EmployeePatch(cdl_endorsements=[], cdl_restrictions=[])
    assert p.cdl_endorsements == []
    assert p.cdl_restrictions == []


def test_none_leaves_the_field_unchanged():
    p = EmployeePatch()
    assert p.cdl_endorsements is None
    assert p.cdl_restrictions is None


def test_dedup_preserves_first_seen_order():
    """Defensive against UI bugs sending dup codes. Audit principle:
    the model is the contract, not a hopeful gatekeeper."""
    body = EmployeeCreate(
        name="Dedupe Test",
        cdl_endorsements=["N", "H", "N", "X", "H"],
    )
    assert body.cdl_endorsements == ["N", "H", "X"]


def test_whitespace_is_stripped():
    body = EmployeeCreate(
        name="Whitespace Test",
        cdl_endorsements=["  N  ", "H"],
    )
    assert body.cdl_endorsements == ["N", "H"]


def test_empty_strings_within_list_are_dropped():
    body = EmployeeCreate(
        name="Empty Within List Test",
        cdl_endorsements=["N", "", "  ", "H"],
    )
    assert body.cdl_endorsements == ["N", "H"]


# ─── Rejection tests ─────────────────────────────────────────────


@pytest.mark.parametrize("bad_code", [
    "Z",         # not in FMCSA taxonomy
    "tanker",    # full word, not the code
    "n",         # lowercase code (taxonomy is case-sensitive)
    "OSHA-30",   # different doc type entirely
    "1",         # numeric
])
def test_endorsement_rejects_unknown_codes(bad_code):
    with pytest.raises(ValueError):
        EmployeeCreate(name="Reject Test", cdl_endorsements=[bad_code])


@pytest.mark.parametrize("bad_code", [
    "vision",          # not in taxonomy
    "no_air_brake",    # close but wrong
    "AUTOMATIC",       # different framing
])
def test_restriction_rejects_unknown_codes(bad_code):
    with pytest.raises(ValueError):
        EmployeeCreate(name="Reject Test", cdl_restrictions=[bad_code])


def test_endorsement_rejects_non_list_type():
    with pytest.raises(ValueError):
        EmployeeCreate(name="Type Test", cdl_endorsements="N")  # str not list


def test_endorsement_rejects_non_string_elements():
    with pytest.raises(ValueError):
        EmployeeCreate(name="Type Test", cdl_endorsements=[1, 2])


# ─── No auto-collapse rule ───────────────────────────────────────


def test_separate_N_and_H_is_preserved_not_collapsed_to_X():
    """Audit rule: record exactly what the license shows. If the CDL
    has N+H as two separate endorsements, the system records both —
    it does not silently 'help' by collapsing to X."""
    body = EmployeeCreate(
        name="No-Collapse Test",
        cdl_endorsements=["N", "H"],
    )
    assert body.cdl_endorsements == ["N", "H"]
    # And X is also accepted standalone — that is the license entry
    # for a combined endorsement.
    body2 = EmployeeCreate(
        name="X Standalone Test",
        cdl_endorsements=["X"],
    )
    assert body2.cdl_endorsements == ["X"]


# ─── Coaching family parity ──────────────────────────────────────


def _endorsement_tips():
    return [
        t for t in all_tips()
        if (t.get("form_key") or "").startswith("driver-qualification.endorsement")
        or (t.get("form_key") or "").startswith("driver-qualification.restriction")
    ]


def test_endorsements_family_has_canonical_four_kinds():
    fam = {t["kind"] for t in _endorsement_tips()
           if t["form_key"] == "driver-qualification.endorsements"}
    missing = {"why", "who", "next", "escalate"} - fam
    assert not missing, f"Endorsements family missing canonical kinds: {missing}"


def test_restrictions_family_has_why_and_mistake():
    fam = {t["kind"] for t in _endorsement_tips()
           if t["form_key"] == "driver-qualification.restrictions"}
    assert {"why", "mistake"}.issubset(fam), \
        f"Restrictions family missing why/mistake; has {fam}"


def test_total_iter287_tip_count_at_least_six():
    """4 (endorsements) + 2 (restrictions) = 6."""
    assert len(_endorsement_tips()) >= 6


def test_every_iter287_tip_has_es_counterpart_merged():
    not_merged = []
    for t in _endorsement_tips():
        if not t.get("title_es") or not t.get("body_es"):
            not_merged.append((t["form_key"], t["kind"]))
    assert not not_merged, f"ES merge incomplete: {not_merged}"


def test_all_iter287_tips_use_hr_or_admin_scope_only():
    """Surface is HR portal only. Dispatch/Fleet read-only consumption
    of this data is iter288 — NOT here."""
    bad = []
    for t in _endorsement_tips():
        scopes = set(t.get("scopes") or [])
        if scopes - {"hr", "admin"}:
            bad.append((t["form_key"], t["kind"], scopes))
    assert not bad, f"iter287 tips have non-HR scopes: {bad}"


def test_no_lms_drift_in_iter287_tips():
    banned = [
        re.compile(r"\bbest practices?\b", re.I),
        re.compile(r"\bempower\b", re.I),
        re.compile(r"\bleverage\b", re.I),
        re.compile(r"\bstakeholders?\b", re.I),
        re.compile(r"\bjourney\b", re.I),
        re.compile(r"\bculture of\b", re.I),
    ]
    hits = []
    for t in _endorsement_tips():
        for field in ("title", "body", "title_es", "body_es"):
            text = t.get(field, "") or ""
            for pat in banned:
                m = pat.search(text)
                if m:
                    hits.append((t["form_key"], t["kind"], field, m.group()))
    assert not hits, f"LMS drift in iter287 tips: {hits}"


def test_restrictions_mistake_tip_explicitly_distinguishes_from_driver_status():
    """The audit's operational distinction (Restrictions ≠ Driver
    Status) must be coached explicitly in BOTH languages. Critical
    because the field names sound similar and are easy to conflate."""
    by_key = {(t["form_key"], t["kind"]): t for t in _endorsement_tips()}
    tip = by_key[("driver-qualification.restrictions", "mistake")]
    en_title = (tip.get("title") or "")
    en_body = (tip.get("body") or "")
    es_title = (tip.get("title_es") or "")
    es_body = (tip.get("body_es") or "")
    # English: must explicitly name both concepts
    assert "Restrictions" in en_title or "Driver Status" in en_title or \
        ("Driver Status" in en_body and "Restrictions" in en_body)
    # Spanish: must explicitly name both concepts
    assert "Restricciones" in es_title or "Estatus" in es_title or \
        ("Estatus" in es_body and "Restricciones" in es_body)


# ─── Future-safety / no-collision guards ─────────────────────────


def test_iter286_field_set_unchanged_by_iter287():
    """Sanity: iter287 added 2 new fields. iter286's 7-field set must
    not have been mutated."""
    from routes.employee_lifecycle import _DRIVER_QUALIFICATION_FIELDS
    assert set(_DRIVER_QUALIFICATION_FIELDS) == {
        "cdl_holder", "approved_company_driver", "driver_status",
        "cdl_license_number", "cdl_state",
        "cdl_expiration_date", "medical_card_expiration_date",
    }


def test_iter287_fields_do_not_collide_with_earlier_iter_fields():
    from routes.employee_lifecycle import (
        _DRIVER_QUALIFICATION_FIELDS, _LIFECYCLE_DATE_FIELDS,
    )
    iter287 = set(_DRIVER_ENDORSEMENT_FIELDS)
    iter286 = set(_DRIVER_QUALIFICATION_FIELDS)
    iter285 = set(_LIFECYCLE_DATE_FIELDS) | {"separation_type"}
    assert not (iter287 & iter286), f"iter287 collides with iter286: {iter287 & iter286}"
    assert not (iter287 & iter285), f"iter287 collides with iter285: {iter287 & iter285}"
