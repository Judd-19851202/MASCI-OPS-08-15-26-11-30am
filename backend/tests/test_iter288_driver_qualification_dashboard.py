"""
iter288 · Driver Qualification Lightweight Operational Dashboard regression test.

Bounded closure of the iter284 §8.2 capstone iteration:
  - GET /api/hr/driver-qualification/dashboard endpoint exists
  - Returns shape: { items: [...], count: int, summary: {...}, as_of: str }
  - Summary includes the 5 operational counts:
      cdl_expiring_30d · medical_card_expiring_30d · restricted ·
      suspended · tanker_capable
  - Tanker-capable counts both N and X endorsements (MASCI asphalt-oil
    operational anchor)
  - Filters validate against the iter286/iter287 taxonomies (invalid
    driver_status or endorsement → 400)
  - The dashboard surface is HR/Admin scope only
  - Reuses existing document_expirations infrastructure (does not
    introduce a second expiration engine — the dashboard reads
    expiration dates straight from the employee record, same source
    of truth the mirror writes to document_expirations)
  - Coaching family `driver-qualification.dashboard` has canonical 4
    kinds (why / who / next / escalate) + mistake (the boundary tip)
  - Boundary discipline coached explicitly: dashboard is visibility,
    NOT a dispatch / compliance / FMCSA system
  - EN/ES parity for all dashboard tips
  - No LMS drift

iter288 does NOT add:
  - dispatch assignment logic
  - automatic capability gating at the moment of assignment
  - workflow orchestration
  - FMCSA compliance reporting
  - CSA scoring
  - audit pipelines
  - “smart assignment” systems
"""
import sys
import pathlib
import re

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import pytest

from routes.employee_lifecycle import (
    ALLOWED_DRIVER_STATUSES, ALLOWED_CDL_ENDORSEMENTS,
)
from guidance.tips import all_tips


# ─── Coaching family parity ──────────────────────────────────────


def _dashboard_tips():
    return [
        t for t in all_tips()
        if (t.get("form_key") or "") == "driver-qualification.dashboard"
    ]


def test_dashboard_family_has_canonical_four_kinds():
    fam = {t["kind"] for t in _dashboard_tips()}
    missing = {"why", "who", "next", "escalate"} - fam
    assert not missing, f"Dashboard family missing canonical kinds: {missing}"


def test_dashboard_family_has_boundary_mistake_tip():
    """The mistake tip is the boundary discipline — what this
    dashboard is NOT (a dispatch system / compliance platform /
    auto-revocation engine). Required."""
    kinds = {t["kind"] for t in _dashboard_tips()}
    assert "mistake" in kinds, \
        "Dashboard family must carry an explicit boundary 'mistake' tip"


def test_dashboard_tip_count_at_least_five():
    """4 canonical + 1 boundary = 5."""
    assert len(_dashboard_tips()) >= 5


def test_every_dashboard_tip_has_es_counterpart_merged():
    not_merged = []
    for t in _dashboard_tips():
        if not t.get("title_es") or not t.get("body_es"):
            not_merged.append((t["form_key"], t["kind"]))
    assert not not_merged, f"ES merge incomplete: {not_merged}"


def test_all_dashboard_tips_use_hr_or_admin_scope_only():
    bad = []
    for t in _dashboard_tips():
        scopes = set(t.get("scopes") or [])
        if scopes - {"hr", "admin"}:
            bad.append((t["form_key"], t["kind"], scopes))
    assert not bad, f"Dashboard tips have non-HR scopes: {bad}"


def test_no_lms_drift_in_iter288_tips():
    banned = [
        re.compile(r"\bbest practices?\b", re.I),
        re.compile(r"\bempower\b", re.I),
        re.compile(r"\bleverage\b", re.I),
        re.compile(r"\bstakeholders?\b", re.I),
        re.compile(r"\bjourney\b", re.I),
        re.compile(r"\bculture of\b", re.I),
    ]
    hits = []
    for t in _dashboard_tips():
        for field in ("title", "body", "title_es", "body_es"):
            text = t.get(field, "") or ""
            for pat in banned:
                m = pat.search(text)
                if m:
                    hits.append((t["form_key"], t["kind"], field, m.group()))
    assert not hits, f"LMS drift in iter288 tips: {hits}"


def test_boundary_tip_explicitly_names_what_dashboard_is_not():
    """The boundary tip exists specifically to PREVENT scope drift in
    future iterations. Verify it explicitly names at least one of:
    dispatch, compliance, assignment, FMCSA, auto-revoke."""
    by_key = {(t["form_key"], t["kind"]): t for t in _dashboard_tips()}
    tip = by_key[("driver-qualification.dashboard", "mistake")]
    en_body = (tip.get("body") or "").lower()
    es_body = (tip.get("body_es") or "").lower()
    en_boundary_words = ["dispatch", "compliance", "assign", "fmcsa", "auto-revoke", "revoke", "trucking"]
    es_boundary_words = ["despacho", "cumplimiento", "asign", "fmcsa", "revoca", "transporte"]
    assert any(w in en_body for w in en_boundary_words), \
        f"EN boundary tip body does not name the boundary: {en_body[:200]}"
    assert any(w in es_body for w in es_boundary_words), \
        f"ES boundary tip body does not name the boundary: {es_body[:200]}"


# ─── Endpoint contract (route registration via FastAPI app) ──────


def test_dashboard_route_is_registered_on_app():
    """Confirms the build_employee_lifecycle_router includes the new
    dashboard endpoint. Avoids hitting the live server (live API
    behavior is covered by main-agent smoke tests)."""
    from server import app
    paths = {r.path for r in app.routes if hasattr(r, "path")}
    assert "/api/hr/driver-qualification/dashboard" in paths, \
        "Dashboard route not registered on FastAPI app"


def test_dashboard_route_is_get_only():
    from server import app
    for r in app.routes:
        if getattr(r, "path", None) == "/api/hr/driver-qualification/dashboard":
            methods = set(r.methods or [])
            # FastAPI also reports HEAD on GET routes — that's fine.
            assert "POST" not in methods, "Dashboard must be read-only"
            assert "GET" in methods
            return
    pytest.fail("Dashboard route not found")


# ─── Reuse-existing-infrastructure guard ─────────────────────────


def test_iter288_does_not_introduce_a_second_expiration_collection():
    """The audit (and the iter286 mirror infrastructure) committed to a
    single canonical expiration system. iter288 (the read dashboard)
    must NOT add new Mongo collections.

    iter352 NOTE: the operator-approved CDL Roster Importer (also
    living in employee_lifecycle.py) DOES write
    `driver_qualification_imports` audit records + uses
    `driver_qualification_import_previews` for ephemeral preview
    tokens. Those are audit/orchestration collections — NOT a second
    expiration collection — and they are scoped to a different code
    block ("CDL / DRIVER QUALIFICATION ROSTER IMPORTER"). The lock
    below is intentionally scoped to the READ dashboard only."""
    import routes.employee_lifecycle as el
    src = pathlib.Path(el.__file__).read_text()
    # Sanity scan: no `db.<new_collection>.insert_*` calls introduced
    # for the dashboard. The dashboard endpoint only does .find /
    # .count_documents against existing collections.
    dashboard_block = src.split("Driver Qualification operational dashboard")[1]
    # End the slice at the next major operational section — either
    # the iter312 CSV export or the iter352 importer block, whichever
    # comes first. Before iter352 the next marker was always the
    # Lifecycle index bootstrap helper.
    cut_markers = [
        "CDL / DRIVER QUALIFICATION ROSTER IMPORTER",  # iter352
        "Lifecycle index bootstrap helper",
    ]
    for marker in cut_markers:
        if marker in dashboard_block:
            dashboard_block = dashboard_block.split(marker)[0]
            break
    # The dashboard handler should not insert / update / delete.
    forbidden = ["insert_one", "insert_many", "update_one", "update_many", "delete_one", "delete_many"]
    hits = [w for w in forbidden if w in dashboard_block]
    assert not hits, \
        f"iter288 dashboard endpoint must be read-only but contains: {hits}"


# ─── Taxonomy / no-collision guards ──────────────────────────────


def test_iter288_taxonomies_unchanged():
    """iter288 added a dashboard, NOT new codes. Driver statuses and
    endorsement taxonomies must be exactly what iter286 + iter287
    defined."""
    assert ALLOWED_DRIVER_STATUSES == {
        "active", "suspended", "restricted", "inactive",
    }
    assert ALLOWED_CDL_ENDORSEMENTS == {"N", "H", "X", "T", "P", "S"}


def test_tanker_capable_definition_matches_audit():
    """MASCI operational anchor: tanker-capable means N OR X
    endorsement. The dashboard summary card MUST count both. This
    test reads the dashboard handler source to verify the union is
    not accidentally narrowed to just N (which would silently miss
    every X-combined-endorsement driver)."""
    import routes.employee_lifecycle as el
    src = pathlib.Path(el.__file__).read_text()
    # The query in the handler must contain both 'N' and 'X' in a
    # $in clause on cdl_endorsements.
    pat = re.compile(
        r"cdl_endorsements.*?\$in.*?\[.*?[\"']N[\"'].*?[\"']X[\"']",
        re.S,
    )
    pat_rev = re.compile(
        r"cdl_endorsements.*?\$in.*?\[.*?[\"']X[\"'].*?[\"']N[\"']",
        re.S,
    )
    assert pat.search(src) or pat_rev.search(src), \
        "Tanker-capable summary must $in both 'N' and 'X' endorsements"


def test_dashboard_does_not_introduce_new_employee_fields():
    """iter288 is a visibility iteration. It must not add fields to
    the employee schema — those land in iter286 / iter287 / future
    bounded closures, never in a dashboard iteration."""
    from routes.employee_lifecycle import (
        _DRIVER_QUALIFICATION_FIELDS, _DRIVER_ENDORSEMENT_FIELDS,
        _LIFECYCLE_DATE_FIELDS,
    )
    iter286 = set(_DRIVER_QUALIFICATION_FIELDS)
    iter287 = set(_DRIVER_ENDORSEMENT_FIELDS)
    iter285 = set(_LIFECYCLE_DATE_FIELDS)
    assert iter286 == {
        "cdl_holder", "approved_company_driver", "driver_status",
        "cdl_license_number", "cdl_state",
        "cdl_expiration_date", "medical_card_expiration_date",
    }
    assert iter287 == {"cdl_endorsements", "cdl_restrictions"}
    # iter316 · added rehire_date to the lifecycle-date-fields set.
    # The dashboard iteration STILL does not introduce employee
    # fields — rehire_date came from the operator-mandated rehire
    # eligibility closure, not from any dashboard work.
    assert iter285 == {
        "original_hire_date", "last_day_worked", "termination_date",
        "leave_start_date", "expected_return_date", "rehire_date",
    }
