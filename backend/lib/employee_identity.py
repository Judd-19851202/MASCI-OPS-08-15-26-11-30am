"""
lib/employee_identity.py — TRACK 23.5.

Single normalized contract for field-facing employee identity.

Employee Lifecycle (HR) writes to `db.employees` using the canonical
create/patch schema (see `routes/employee_lifecycle.py::EmployeeCreate`
/ `EmployeePatch`). The canonical keys are:

    name · preferred_name · employee_id · trade · role · crew ·
    department · supervisor · legal_first_name · legal_middle_name ·
    legal_last_name · is_active · lifecycle_status

Historical projections diverged between `/api/employees` and
`/api/hr/employee-roster`:

    * `/api/employees` projected `supervisor` + `division` (division
      is not written by HR — dead field), plus `crew`, `role`, `trade`,
      `department`.
    * `/api/hr/employee-roster` projected `supervisor_name` +
      `supervisor_id` (neither of which HR writes — dead fields), so
      supervisor was silently dropped for every field picker consuming
      that endpoint (Daily Report V3, EmployeeCombo, trench pickers).

TRACK 23.5 fix: both endpoints project the canonical write-keys AND
run every doc through :func:`normalize_employee_identity` which emits
the shared display contract:

    trade_role_display · trade_role_source
    crew_display · crew_source
    supervisor_display · supervisor_source
    display_identity   (preferred + legal composite)

Downstream (`daily_reports.masci_crews[]`, ODS `labor_fact`, PDF, email,
HR Time Verification, Payroll Variance, PM Intelligence) reads the
`*_display` keys directly and snapshots them without alias juggling.

Legacy raw keys are preserved so no downstream contract breaks.
"""
from __future__ import annotations

from typing import Any, Mapping, Optional


def _s(v: Any) -> str:
    if v is None:
        return ""
    return str(v).strip()


# Alias tables — the order encodes precedence.
_TRADE_ALIASES = (
    "trade",
    "role",
    "title",
    "position",
    "classification",
    "trade_role",
)
_CREW_ALIASES = (
    "crew",
    "division",
)
_SUPERVISOR_ALIASES = (
    "supervisor",
    "supervisor_name",
)
_DEPARTMENT_ALIASES = (
    "department",
    "division",
)


def _first_populated(obj: Mapping[str, Any], keys) -> tuple[str, str]:
    """Return (value, source_key) for the first alias with non-empty
    value. Returns ("", "") when every alias is blank / missing."""
    for k in keys:
        v = _s(obj.get(k))
        if v:
            return v, k
    return "", ""


def normalize_employee_identity(doc: Optional[Mapping[str, Any]]) -> dict:
    """Return the canonical field-facing employee identity contract.

    Guarantees:
      * All legacy raw keys pass through unchanged (`trade`, `role`,
        `crew`, `department`, `supervisor`, `preferred_name`,
        `employee_id`, `name`, `is_active`, `lifecycle_status`, `id`).
      * Adds the normalized display contract:
            trade_role_display · trade_role_source
            crew_display · crew_source
            supervisor_display · supervisor_source
            department_display · department_source
            display_identity   (preferred + legal composite)
      * When no value exists for a given category, the display key
        returns "" and the *_source key returns "". Downstream code
        can differentiate "not on employee record" honestly.

    Never fabricates data. Never renames writes. Purely additive.
    """
    if not doc:
        return {}
    out: dict = {}
    # Pass every original key through unchanged so backward-compatible
    # readers still work.
    for k, v in doc.items():
        if k == "_id":
            continue
        out[k] = v

    trade, trade_src = _first_populated(doc, _TRADE_ALIASES)
    crew, crew_src = _first_populated(doc, _CREW_ALIASES)
    sup, sup_src = _first_populated(doc, _SUPERVISOR_ALIASES)
    dept, dept_src = _first_populated(doc, _DEPARTMENT_ALIASES)

    # If department was consumed for something else, keep as fallback
    # for Crew (rare — some legacy imports used department for crew).
    if not crew:
        dept_val = _s(doc.get("department"))
        if dept_val and dept_val != trade:
            crew, crew_src = dept_val, "department"

    out["trade_role_display"] = trade
    out["trade_role_source"] = trade_src
    out["crew_display"] = crew
    out["crew_source"] = crew_src
    out["supervisor_display"] = sup
    out["supervisor_source"] = sup_src
    out["department_display"] = dept
    out["department_source"] = dept_src

    # display_identity — reuse masci.identity when available so PDF /
    # email / notifications land on the same label.
    try:
        from masci.identity import format_employee_identity  # noqa: PLC0415
        out["display_identity"] = format_employee_identity(doc)
    except Exception:
        # Defensive fallback — never break the projection because of
        # an identity helper import error.
        pref = _s(doc.get("preferred_name"))
        legal = _s(doc.get("name")) or _s(doc.get("display_name"))
        if pref and legal and pref.lower() != legal.lower():
            out["display_identity"] = f"{legal} ({pref})"
        else:
            out["display_identity"] = legal or pref

    return out


# ---------------------------------------------------------------------------
# Public projection — the fields any public roster endpoint should query
# from Mongo. Kept as a constant so both `/api/employees` and
# `/api/hr/employee-roster` project the same allow-list.
#
# No CDL, no medical, no email, no phone, no SSN, no DOB, no history.
# ---------------------------------------------------------------------------
PUBLIC_ROSTER_PROJECTION = {
    "_id": 0,
    "id": 1,
    "employee_id": 1,
    "name": 1,
    "preferred_name": 1,
    "legal_first_name": 1,
    "legal_middle_name": 1,
    "legal_last_name": 1,
    "trade": 1,
    "role": 1,
    "crew": 1,
    "department": 1,
    "supervisor": 1,
    "is_active": 1,
    "lifecycle_status": 1,
    "updated_at": 1,
}


__all__ = [
    "normalize_employee_identity",
    "PUBLIC_ROSTER_PROJECTION",
]
