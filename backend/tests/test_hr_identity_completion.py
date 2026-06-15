"""
tests/test_hr_identity_completion.py — Track 14.0-HR-IDENTITY-COMPLETION-AND-CERTIFICATION.

Locks the HR identity display contract across the platform:
  * Backend canonical helper `masci.identity.format_employee_identity`
    returns "Legal First Last (Preferred)" when preferred is set,
    "Legal First Last" otherwise, and falls back to denormalised
    `name` when no legal parts are stored.
  * Frontend canonical helper `frontend/src/lib/identity.js` mirrors
    the same rule exactly.
  * Employee CSV exports carry the 4 identity fields explicitly so
    no data loss on import / export round-trips.
  * Search resolves any of: legal first / middle / last / preferred /
    legacy denormalised name.

Future developers cannot remove preferred_name display, break exports,
or weaken the search without these guards failing.
"""
from __future__ import annotations

import pytest
from pathlib import Path

from masci.identity import (
    format_employee_identity,
    format_legal_name,
    identity_search_blob,
)

REPO = Path("/app")


# ─────────────────────────────────────────────────────────────────────
# Backend canonical helper
# ─────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("doc,expected", [
    # Preferred name present → legal name + (preferred)
    (
        {"legal_first_name": "James", "legal_last_name": "Fisher",
         "preferred_name": "Jimmy"},
        "James Fisher (Jimmy)",
    ),
    # Preferred name absent → legal only
    (
        {"legal_first_name": "James", "legal_last_name": "Fisher"},
        "James Fisher",
    ),
    # Middle name present but no preferred → legal first + last only
    (
        {"legal_first_name": "James", "legal_middle_name": "Michael",
         "legal_last_name": "Fisher"},
        "James Fisher",
    ),
    # No legal name parts → fallback to denormalised `name`
    (
        {"name": "Jimmy Fisher"},
        "Jimmy Fisher",
    ),
    # Preferred-only employee (rare but valid)
    (
        {"preferred_name": "Doc"},
        "Doc",
    ),
    # Preferred identical to first-last → no redundant suffix
    (
        {"legal_first_name": "Sam", "legal_last_name": "Bell",
         "preferred_name": "sam bell"},
        "Sam Bell",
    ),
    # Empty record
    ({}, ""),
    (None, ""),
])
def test_format_employee_identity_contract(doc, expected):
    assert format_employee_identity(doc) == expected


@pytest.mark.parametrize("doc,expected", [
    ({"legal_first_name": "James", "legal_last_name": "Fisher",
      "preferred_name": "Jimmy"}, "James Fisher"),
    ({"name": "Jimmy Fisher"}, "Jimmy Fisher"),
    ({}, ""),
])
def test_format_legal_name_never_appends_preferred(doc, expected):
    """format_legal_name() drops the preferred suffix even when set."""
    assert format_legal_name(doc) == expected


def test_identity_search_blob_resolves_every_alias():
    """A single substring match against the blob must resolve
    "James", "Michael", "Fisher", "Jimmy", "James Fisher",
    "Jimmy Fisher", "James Michael Fisher" all to the same employee."""
    doc = {
        "legal_first_name": "James",
        "legal_middle_name": "Michael",
        "legal_last_name": "Fisher",
        "preferred_name": "Jimmy",
    }
    blob = identity_search_blob(doc)
    for q in ("james", "michael", "fisher", "jimmy",
              "james fisher", "jimmy fisher", "james michael fisher"):
        assert q in blob, f"{q!r} not findable in blob {blob!r}"


# ─────────────────────────────────────────────────────────────────────
# Frontend helper mirrors the backend rule exactly
# ─────────────────────────────────────────────────────────────────────


FRONTEND_IDENTITY = REPO / "frontend/src/lib/identity.js"


def test_frontend_identity_helper_exists():
    """Frontend has the canonical helper module."""
    assert FRONTEND_IDENTITY.is_file(), (
        "frontend/src/lib/identity.js is the canonical FE identity "
        "formatter — every employee-display surface must import it. "
        "Deleting it would force every consumer back to ad-hoc "
        "inline formatting and preferred_name would drift again."
    )


def test_frontend_identity_helper_exports_required_api():
    """The three required functions are exported."""
    src = FRONTEND_IDENTITY.read_text()
    for name in ("formatEmployeeIdentity", "formatLegalName",
                 "identitySearchBlob"):
        assert f"export function {name}(" in src, (
            f"identity.js no longer exports {name}. Callers across "
            "the platform import this — removing it breaks every "
            "employee-display surface."
        )


def test_frontend_identity_helper_obeys_display_rule():
    """The FE helper file documents and implements "Legal (Preferred)"
    in that order — never replace legal identity."""
    src = FRONTEND_IDENTITY.read_text()
    assert "James Fisher (Jimmy)" in src, (
        "Canonical example removed from identity.js docstring. The "
        "documented contract is the rule HR enforces — keep it."
    )
    assert "legal" in src.lower() and "preferred" in src.lower(), (
        "identity.js no longer references the legal/preferred contract."
    )


# ─────────────────────────────────────────────────────────────────────
# Display-surface usage guards
# ─────────────────────────────────────────────────────────────────────


HR_EMPLOYEES = REPO / "frontend/src/pages/HrEmployees.jsx"


def test_hr_employees_uses_canonical_identity_helper():
    """HR Directory + Drawer render through formatEmployeeIdentity()
    so future commits cannot silently revert to "first name only" or
    "preferred only"."""
    src = HR_EMPLOYEES.read_text()
    assert 'from "@/lib/identity"' in src, (
        "HrEmployees.jsx no longer imports the canonical identity "
        "formatter. Drawer + table will drift back to ad-hoc display."
    )
    assert "formatEmployeeIdentity(" in src, (
        "HrEmployees.jsx no longer calls formatEmployeeIdentity(). "
        "Ad-hoc identity rendering returns."
    )


# ─────────────────────────────────────────────────────────────────────
# Backend search + export coverage
# ─────────────────────────────────────────────────────────────────────


EMPLOYEE_LIFECYCLE = REPO / "backend/routes/employee_lifecycle.py"


def test_employee_list_search_covers_all_identity_fields():
    """Search must resolve legal_first / legal_middle / legal_last /
    preferred_name / legacy `name` / employee_id / trade. Anything
    less and HR cannot find an employee by their preferred name OR
    by their legal middle name."""
    src = EMPLOYEE_LIFECYCLE.read_text()
    for field in ("legal_first_name", "legal_middle_name",
                  "legal_last_name", "preferred_name"):
        assert f'"{field}": {{"$regex": q' in src, (
            f"Employee search no longer matches {field}. Searching "
            "by preferred name or middle name would silently fail."
        )


def test_driver_qualification_csv_carries_identity_columns():
    """The driver-qualification CSV export must carry the 4 identity
    columns explicitly so a round-trip through CSV cannot lose
    preferred_name or middle name."""
    src = EMPLOYEE_LIFECYCLE.read_text()
    for col in ("Legal First Name", "Legal Middle Name",
                "Legal Last Name", "Preferred Name"):
        assert f'"{col}"' in src, (
            f"Driver Qualification CSV no longer ships a {col!r} "
            "column. Identity round-trip is lossy — track stays open."
        )


def test_employees_response_includes_display_identity():
    """The /api/hr/employees response must carry a precomputed
    display_identity label so every consumer renders the same string
    without re-implementing the rule."""
    src = EMPLOYEE_LIFECYCLE.read_text()
    assert 'd["display_identity"] = format_employee_identity(d)' in src, (
        "/api/hr/employees no longer projects display_identity. "
        "Consumers will re-implement the formatting rule (and drift)."
    )


# ─────────────────────────────────────────────────────────────────────
# Track 14.0-UXS-11F · Display rollout regression
# ─────────────────────────────────────────────────────────────────────
#
# Every page that previously rendered a bare ``{x.employee_name}`` etc
# now routes through formatEmployeeIdentity(x) || x.employee_name so the
# preferred-name surfacing kicks in the moment HR populates the data.
# Future commits cannot silently revert these consumers.

UXS11F_DISPLAY_CONSUMERS = [
    "frontend/src/pages/ReturnEquipment.jsx",
    "frontend/src/pages/HrSafetyRecords.jsx",
    "frontend/src/pages/ShopHub.jsx",
    "frontend/src/pages/ViewEquipmentInspection.jsx",
    "frontend/src/pages/SafetyTrainingRecords.jsx",
    "frontend/src/pages/PmCrewCompliance.jsx",
    "frontend/src/pages/HrPayrollVariance.jsx",
    "frontend/src/pages/FieldLeadershipView.jsx",
    "frontend/src/pages/HrEmployeeRequestsQueue.jsx",
    "frontend/src/pages/HrTimeOff.jsx",
    "frontend/src/pages/HrTimeVerification.jsx",
    "frontend/src/pages/PublicTimeOff.jsx",
    "frontend/src/pages/admin/AdminJhaAcknowledgements.jsx",
    "frontend/src/pages/admin/AssetProfile.jsx",
    "frontend/src/components/AdminSafetyFormsPanel.jsx",
]


@pytest.mark.parametrize("relpath", UXS11F_DISPLAY_CONSUMERS)
def test_uxs11f_consumer_uses_canonical_helper(relpath):
    """Every display surface that renders an employee identity must
    import and use formatEmployeeIdentity. Adding new consumers is
    fine; removing the helper from any of these is not — the page
    would silently render legacy labels and preferred_name would
    drift back into invisibility."""
    src = (REPO / relpath).read_text()
    assert 'from "@/lib/identity"' in src, (
        f"{relpath} no longer imports the canonical identity helper."
    )
    assert "formatEmployeeIdentity(" in src, (
        f"{relpath} no longer calls formatEmployeeIdentity(). "
        "Preferred-name rendering broken on this surface."
    )


def test_uxs11f_no_bare_employee_name_in_locked_consumers():
    """Locked consumers must never reintroduce a bare
    ``{var.employee_name}`` JSX expression — every such render now
    has to go through the helper. This is a structural guarantee:
    you can add the helper around it, but you can't drop the helper
    and render the raw field."""
    import re
    bare_pat = re.compile(
        r"\{\s*[a-zA-Z_][a-zA-Z0-9_]*\.(employee_name|operator_name|driver_name|full_name|submitter_name|crew_member_name)\s*\}"
    )
    leaks: list[tuple[str, int, str]] = []
    for relpath in UXS11F_DISPLAY_CONSUMERS:
        text = (REPO / relpath).read_text()
        for i, line in enumerate(text.splitlines(), 1):
            if bare_pat.search(line) and "formatEmployeeIdentity" not in line:
                leaks.append((relpath, i, line.strip()[:120]))
    assert not leaks, (
        "Bare identity rendering detected on locked consumers — "
        "preferred-name surfacing will silently break:\n  "
        + "\n  ".join(f"{p}:{i}: {l}" for p, i, l in leaks)
    )


# ─────────────────────────────────────────────────────────────────────
# Track 14.0-UXS-11F · Global Search backend coverage
# ─────────────────────────────────────────────────────────────────────


GLOBAL_SEARCH = REPO / "backend/routes/global_search.py"


def test_global_search_imports_canonical_identity_helper():
    src = GLOBAL_SEARCH.read_text()
    assert "from masci.identity import format_employee_identity" in src, (
        "global_search no longer imports the canonical identity "
        "formatter. Search results would lose preferred-name display."
    )


def test_global_search_resolves_all_identity_aliases():
    """Global search must hit legal first / middle / last / preferred
    in addition to legacy ``name``."""
    src = GLOBAL_SEARCH.read_text()
    for field in ("legal_first_name", "legal_middle_name",
                  "legal_last_name", "preferred_name"):
        assert f'"{field}": rx' in src, (
            f"global_search no longer matches {field}. Searching by "
            "preferred or middle name would silently miss employees."
        )
