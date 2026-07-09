"""
routes/employee_lifecycle.py — Iter152 (Phase 2.5) · Phase C.

EMPLOYEE LIFECYCLE MANAGEMENT.

Uses existing db.employees as the single source of truth. Does NOT
create a duplicate employee collection.

Adds the `lifecycle_status` field on the existing employee documents:
  Pending Hire · Active · Inactive · Suspended · Terminated · Resigned
  · Retired · Seasonal · Leave of Absence

Active dropdown behavior:
  * Existing `is_active` boolean is kept in sync so legacy
    `/api/employees` dropdowns continue to filter Inactive folks
    out by default.
  * New `?show_inactive=true` query param exposes the full roster.

Offboarding Summary (read-only):
  Aggregates outstanding accountability for an employee:
    * Open tasks (Phase A — db.tasks)
    * Document expirations (Phase B — db.document_expirations)
    * Equipment issuances if tracked (best-effort via db.equipment)

Auto-Offboarding Playbook:
  When status transitions from {Active, Pending Hire, Seasonal, Leave of Absence}
  → {Terminated, Resigned, Retired}, the platform fan-outs a canned
  task checklist via task_service.create() (Phase A). HR can review +
  close those tasks; the platform does NOT auto-fire any operational
  changes (no auto-revoke, no auto-equipment-transfer).
"""
from __future__ import annotations

from lib.mongo_query import safe_regex

import logging
import re as _re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)

ALLOWED_LIFECYCLE_STATUSES = {
    "Pending Hire", "Active", "Inactive", "Suspended",
    "Terminated", "Resigned", "Retired", "Seasonal",
    "Leave of Absence",
}


# iter352 · CDL roster import apply payload. Defined at module scope
# so FastAPI's TypeAdapter can resolve the ForwardRef in the route
# handler signature.
class CdlImportApplyPayload(BaseModel):
    preview_token: str
    skip_rows: List[int] = Field(default_factory=list)
    create_unmatched: bool = False
    model_config = {"extra": "ignore"}

# Statuses that count as "actively employed" for dropdown filtering.
_ACTIVE_STATUSES = {"Active", "Pending Hire", "Seasonal", "Leave of Absence"}

# Statuses that trigger the offboarding playbook.
_OFFBOARDING_STATUSES = {"Terminated", "Resigned", "Retired"}

# iter285 · employment separation taxonomy.
ALLOWED_SEPARATION_TYPES = {"voluntary", "involuntary", "layoff"}

# iter316 · rehire eligibility taxonomy. Three explicit operational
# values — no free-text equivalents. `review_required` is the DEFAULT
# because the platform must NOT assume eligible when HR did not
# explicitly decide. This field belongs on the termination/offboarding
# record and travels with the employee across reactivation cycles.
ALLOWED_REHIRE_ELIGIBILITY = {"eligible", "not_eligible", "review_required"}
_REHIRE_ELIGIBILITY_REQUIRES_REASON = {"not_eligible", "review_required"}

# iter286 · driver qualification taxonomy. Only meaningful when the
# employee is flagged as an `approved_company_driver`. The semantic
# distinction below is the entire reason CDL Holder and Approved
# Company Driver are independent fields:
#   - cdl_holder = "this person legally holds a CDL"
#   - approved_company_driver = "MASCI has authorized this person
#     to operate company vehicles/equipment"
# A person may hold a CDL and NOT be approved internally (suspended,
# under restriction, never cleared) — and vice versa is operationally
# uncommon but structurally legal.
ALLOWED_DRIVER_STATUSES = {"active", "suspended", "restricted", "inactive"}

# iter287 · CDL endorsements & restrictions taxonomy. Structured codes
# only — no free-form notes. Codes follow FMCSA letter conventions so
# Dispatch / Fleet / future Motive linkage can consume the data without
# translation. MASCI-operational note: Tanker (N) is the endorsement
# most frequently surfaced for asphalt-oil tanker assignments.
#   N = Tanker
#   H = Hazardous Materials
#   X = Tanker + Hazmat (combined endorsement)
#   T = Doubles / Triples
#   P = Passenger
#   S = School Bus
# The schema does NOT auto-collapse {N,H} into {X} or vice-versa — the
# entry on the CDL is the source of truth; we record exactly what the
# license shows.
ALLOWED_CDL_ENDORSEMENTS = {"N", "H", "X", "T", "P", "S"}

# iter287 · Restrictions. Two operationally-relevant restrictions
# tracked structurally. Anything beyond these belongs on the CDL
# document scan, not in structured fields.
ALLOWED_CDL_RESTRICTIONS = {"air_brake", "manual_transmission"}

# iter286 · driver qualification field set used by validators + the
# document-expirations linkage helper below.
_DRIVER_QUALIFICATION_FIELDS = (
    "cdl_holder",
    "approved_company_driver",
    "driver_status",
    "cdl_license_number",
    "cdl_state",
    "cdl_expiration_date",
    "medical_card_expiration_date",
)

# iter287 · endorsements + restrictions field set. Kept separate from
# the iter286 foundation set because iter286 owns
# document_expirations mirroring and iter287 owns operational
# capability flags only.
_DRIVER_ENDORSEMENT_FIELDS = (
    "cdl_endorsements",
    "cdl_restrictions",
)

# iter285 · lifecycle date field names · used by write-once enforcement
# and status-transition auto-population helpers below.
_LIFECYCLE_DATE_FIELDS = (
    "original_hire_date",
    "last_day_worked",
    "termination_date",
    "leave_start_date",
    "expected_return_date",
    "rehire_date",  # iter316 · most-recent rehire/reactivation date
)
# Once `original_hire_date` is set to a non-empty string on an employee
# document, no subsequent PATCH may change it. Audit (iter284 · §2.2 +
# §6 risk #1) flagged unprotected hire-date overwrite as the highest
# structural risk in the employee schema.
_WRITE_ONCE_FIELDS = ("original_hire_date",)


def _is_date_string(v: Any) -> bool:
    """Light validation: ISO-style YYYY-MM-DD prefix.

    Mongo stores dates as ISO strings in this collection per existing
    convention. We don't enforce calendar correctness here — that's
    the frontend date picker's job; this just keeps obviously bad
    values out.
    """
    if v is None or v == "":
        return True  # empty / null is fine; caller decides if required
    if not isinstance(v, str):
        return False
    if len(v) < 10:
        return False
    head = v[:10]
    return head[4] == "-" and head[7] == "-" and head.replace("-", "").isdigit()


def _validate_code_list(
    value: Optional[List[str]], allowed: set, field_name: str
) -> Optional[List[str]]:
    """iter287 · structured-code list validator.

    Used for `cdl_endorsements` and `cdl_restrictions` — both are lists
    of letter codes / short tokens drawn from a fixed taxonomy. Each
    incoming list is:
      - normalized (stripped, deduped, preserves first-seen order)
      - rejected outright if any element is not in `allowed`
      - left as `None` if the caller omitted the field
      - accepted as `[]` to explicitly clear the field

    This is the same shape we use for enum scalars elsewhere — empty
    string / None / [] all valid "clear" signals — keeping the
    operator-facing semantics consistent.
    """
    if value is None:
        return None
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list of codes")
    seen: List[str] = []
    for raw in value:
        if not isinstance(raw, str):
            raise ValueError(f"{field_name} entries must be strings")
        code = raw.strip()
        if code == "":
            continue
        if code not in allowed:
            raise ValueError(
                f"{field_name} contains invalid code {code!r}; "
                f"allowed: {sorted(allowed)}"
            )
        if code not in seen:
            seen.append(code)
    return seen


def _tenure_days(employee: Dict[str, Any]) -> Optional[int]:
    """Derive tenure in days from `original_hire_date` (preferred) or
    legacy `hire_date`. Returns None when neither is set.

    Strictly read-time — NEVER stored. Single source of truth is the
    authoritative date field itself.
    """
    from datetime import datetime, date
    raw = (employee.get("original_hire_date") or employee.get("hire_date") or "").strip()
    if not raw or len(raw) < 10:
        return None
    try:
        hire = datetime.strptime(raw[:10], "%Y-%m-%d").date()
    except ValueError:
        return None
    # If terminated/resigned/retired, freeze tenure at termination date
    # when available, otherwise last_day_worked, otherwise today.
    end_raw = (
        employee.get("termination_date")
        or employee.get("last_day_worked")
        or ""
    ).strip()
    if end_raw and employee.get("lifecycle_status") in _OFFBOARDING_STATUSES:
        try:
            end = datetime.strptime(end_raw[:10], "%Y-%m-%d").date()
            return max(0, (end - hire).days)
        except ValueError:
            pass
    today = date.today()
    return max(0, (today - hire).days)


async def _mirror_driver_doc_expirations(
    db, employee_id: str, incoming: Dict[str, Any], existing: Dict[str, Any]
) -> None:
    """iter286 · keep `db.document_expirations` in sync with
    driver-qualification expiration dates on the employee record.

    Why: the platform already runs an expiration scanner over the
    `document_expirations` collection (routes/document_expirations.py
    iter225). Mirroring CDL + medical card expiration dates into that
    collection means the existing scanner picks up the work without a
    second expiration system being introduced. The employee record
    stays the structured source of truth; the doc-expiration row is a
    derived projection keyed by `(linked_employee_id, document_type)`.

    Behavior:
      - When `cdl_expiration_date` is non-empty in the incoming patch
        AND the value changed, upsert a row in `document_expirations`
        with `document_type='cdl_license'`, category 'safety'.
      - Same for `medical_card_expiration_date` (doc_type
        'medical_card').
      - Empty / null incoming values are NOT mirrored — clearing a
        date on the employee record does NOT delete the historical
        document_expirations row (the doc-expirations surface is the
        right place to manage / archive those rows).
    """
    mirror_map = (
        ("cdl_expiration_date", "cdl_license", "CDL license"),
        ("medical_card_expiration_date", "medical_card", "Medical card"),
    )
    for field, doc_type, title_hint in mirror_map:
        new_val = (incoming.get(field) or "").strip() if isinstance(incoming.get(field), str) else None
        if not new_val:
            continue
        old_val = (existing.get(field) or "").strip() if isinstance(existing.get(field), str) else None
        if new_val == old_val:
            continue
        # Upsert by (linked_employee_id, document_type) — one canonical
        # row per employee per qualification document type.
        now_iso = datetime.now(timezone.utc).isoformat()
        await db.document_expirations.update_one(
            {
                "linked_employee_id": employee_id,
                "document_type": doc_type,
            },
            {
                "$set": {
                    "expiration_date": new_val,
                    "updated_at": now_iso,
                    "category": "employee",
                    "title": title_hint,
                    "source": "employee.driver_qualification",
                },
                "$setOnInsert": {
                    "id": str(uuid.uuid4()),
                    "linked_employee_id": employee_id,
                    "document_type": doc_type,
                    "status": "Current",
                    "created_at": now_iso,
                    "deleted_at": None,
                },
            },
            upsert=True,
        )


# ──────────────────────────────────────────────────────────────────
# Canned offboarding task playbook
# ──────────────────────────────────────────────────────────────────
# Each row: (assignee_role, priority, title, description)
_OFFBOARDING_PLAYBOOK: List[Dict[str, str]] = [
    {
        "role": "hr",
        "priority": "High",
        "title": "Finalize last paycheck + benefits closeout",
        "desc": "Verify last timesheet hours, accrued PTO payout, and benefits / COBRA notice.",
    },
    {
        "role": "hr",
        "priority": "High",
        "title": "Collect company-issued documents and badges",
        "desc": "Pick up MASCI ID, site badges, OSHA wallet card, and any signed acknowledgments.",
    },
    {
        "role": "shop",
        "priority": "High",
        "title": "Recover company equipment / tools / PPE",
        "desc": "Confirm any small tools, fall protection, hard hats, PPE, fuel cards, and vehicle if applicable are returned.",
    },
    {
        "role": "shop",
        "priority": "Medium",
        "title": "Verify equipment hand-off for any active assignments",
        "desc": "Reassign or stage any equipment that was checked out to this employee.",
    },
    {
        "role": "admin",
        "priority": "High",
        "title": "Disable directory login + portal accounts",
        "desc": "Revoke admin/portal access if any directory session exists, and rotate shared credentials this person used.",
    },
    {
        "role": "admin",
        "priority": "Medium",
        "title": "Disable Motive driver profile (if applicable)",
        "desc": "Mark Motive driver Inactive so they no longer count toward fleet quotas.",
    },
    {
        "role": "safety",
        "priority": "Medium",
        "title": "Close any open safety items tied to this employee",
        "desc": "Review open incidents, corrective actions, training deficiencies, and re-assign or close.",
    },
    {
        "role": "pm",
        "priority": "Medium",
        "title": "Backfill open project assignments",
        "desc": "Identify active jobs this employee was staffed on and either reassign or note coverage plan.",
    },
]


# ──────────────────────────────────────────────────────────────────
# Pydantic
# ──────────────────────────────────────────────────────────────────
class EmployeeCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    trade: Optional[str] = Field(default="", max_length=80)
    role: Optional[str] = Field(default="", max_length=80)
    crew: Optional[str] = Field(default="", max_length=80)
    employee_id: Optional[str] = Field(default="", max_length=64)
    email: Optional[str] = Field(default="", max_length=160)
    phone: Optional[str] = Field(default="", max_length=40)
    supervisor: Optional[str] = Field(default="", max_length=120)
    department: Optional[str] = Field(default="", max_length=80)
    default_project_number: Optional[str] = Field(default="", max_length=64)
    lifecycle_status: str = Field(default="Active")
    hire_date: Optional[str] = None

    # iter285 · lifecycle date structure
    original_hire_date: Optional[str] = None
    last_day_worked: Optional[str] = None
    termination_date: Optional[str] = None
    leave_start_date: Optional[str] = None
    expected_return_date: Optional[str] = None
    separation_type: Optional[str] = None

    # iter316 · rehire eligibility + rehire-cycle date
    rehire_eligibility: Optional[str] = None
    rehire_eligibility_reason: Optional[str] = Field(default=None, max_length=500)
    rehire_date: Optional[str] = None

    # iter286 · driver qualification structure
    # CDL Holder ≠ Approved Company Driver. The two flags are
    # intentionally independent — see ALLOWED_DRIVER_STATUSES doc above.
    cdl_holder: Optional[bool] = None
    approved_company_driver: Optional[bool] = None
    driver_status: Optional[str] = None
    cdl_license_number: Optional[str] = Field(default=None, max_length=40)
    cdl_state: Optional[str] = Field(default=None, max_length=4)
    cdl_expiration_date: Optional[str] = None
    medical_card_expiration_date: Optional[str] = None

    # iter287 · CDL endorsements + restrictions (structured codes only)
    cdl_endorsements: Optional[List[str]] = None
    cdl_restrictions: Optional[List[str]] = None

    @field_validator("lifecycle_status")
    @classmethod
    def _v_status(cls, v: str) -> str:
        if v not in ALLOWED_LIFECYCLE_STATUSES:
            raise ValueError(f"lifecycle_status must be one of {sorted(ALLOWED_LIFECYCLE_STATUSES)}")
        return v

    @field_validator(
        "original_hire_date", "last_day_worked", "termination_date",
        "leave_start_date", "expected_return_date",
        "cdl_expiration_date", "medical_card_expiration_date",
        "rehire_date",
    )
    @classmethod
    def _v_date(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return v
        if not _is_date_string(v):
            raise ValueError("date must be YYYY-MM-DD")
        return v

    @field_validator("separation_type")
    @classmethod
    def _v_sep(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return v
        if v not in ALLOWED_SEPARATION_TYPES:
            raise ValueError(f"separation_type must be one of {sorted(ALLOWED_SEPARATION_TYPES)}")
        return v

    @field_validator("rehire_eligibility")
    @classmethod
    def _v_rehire(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return v
        if v not in ALLOWED_REHIRE_ELIGIBILITY:
            raise ValueError(
                f"rehire_eligibility must be one of {sorted(ALLOWED_REHIRE_ELIGIBILITY)}"
            )
        return v

    @field_validator("driver_status")
    @classmethod
    def _v_driver_status(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return v
        if v not in ALLOWED_DRIVER_STATUSES:
            raise ValueError(f"driver_status must be one of {sorted(ALLOWED_DRIVER_STATUSES)}")
        return v

    @field_validator("cdl_endorsements")
    @classmethod
    def _v_endorsements(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        return _validate_code_list(v, ALLOWED_CDL_ENDORSEMENTS, "cdl_endorsements")

    @field_validator("cdl_restrictions")
    @classmethod
    def _v_restrictions(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        return _validate_code_list(v, ALLOWED_CDL_RESTRICTIONS, "cdl_restrictions")


class EmployeePatch(BaseModel):
    name: Optional[str] = None
    preferred_name: Optional[str] = None  # HR-EMPLOYEE-002
    trade: Optional[str] = None
    role: Optional[str] = None
    crew: Optional[str] = None
    employee_id: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    supervisor: Optional[str] = None
    department: Optional[str] = None
    default_project_number: Optional[str] = None
    hire_date: Optional[str] = None

    # iter285 · lifecycle date structure (mirror of create-time fields)
    original_hire_date: Optional[str] = None
    last_day_worked: Optional[str] = None
    termination_date: Optional[str] = None
    leave_start_date: Optional[str] = None
    expected_return_date: Optional[str] = None
    separation_type: Optional[str] = None

    # iter316 · rehire eligibility + rehire date (mirror of create-time)
    rehire_eligibility: Optional[str] = None
    rehire_eligibility_reason: Optional[str] = Field(default=None, max_length=500)
    rehire_date: Optional[str] = None

    # iter286 · driver qualification (mirror of create-time fields)
    cdl_holder: Optional[bool] = None
    approved_company_driver: Optional[bool] = None
    driver_status: Optional[str] = None
    cdl_license_number: Optional[str] = Field(default=None, max_length=40)
    cdl_state: Optional[str] = Field(default=None, max_length=4)
    cdl_expiration_date: Optional[str] = None
    medical_card_expiration_date: Optional[str] = None

    # iter287 · CDL endorsements + restrictions (mirror of create-time)
    cdl_endorsements: Optional[List[str]] = None
    cdl_restrictions: Optional[List[str]] = None

    @field_validator(
        "original_hire_date", "last_day_worked", "termination_date",
        "leave_start_date", "expected_return_date",
        "cdl_expiration_date", "medical_card_expiration_date",
        "rehire_date",
    )
    @classmethod
    def _v_date(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return v
        if not _is_date_string(v):
            raise ValueError("date must be YYYY-MM-DD")
        return v

    @field_validator("separation_type")
    @classmethod
    def _v_sep(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return v
        if v not in ALLOWED_SEPARATION_TYPES:
            raise ValueError(f"separation_type must be one of {sorted(ALLOWED_SEPARATION_TYPES)}")
        return v

    @field_validator("rehire_eligibility")
    @classmethod
    def _v_rehire(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return v
        if v not in ALLOWED_REHIRE_ELIGIBILITY:
            raise ValueError(
                f"rehire_eligibility must be one of {sorted(ALLOWED_REHIRE_ELIGIBILITY)}"
            )
        return v

    @field_validator("driver_status")
    @classmethod
    def _v_driver_status(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return v
        if v not in ALLOWED_DRIVER_STATUSES:
            raise ValueError(f"driver_status must be one of {sorted(ALLOWED_DRIVER_STATUSES)}")
        return v

    @field_validator("cdl_endorsements")
    @classmethod
    def _v_endorsements(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        return _validate_code_list(v, ALLOWED_CDL_ENDORSEMENTS, "cdl_endorsements")

    @field_validator("cdl_restrictions")
    @classmethod
    def _v_restrictions(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        return _validate_code_list(v, ALLOWED_CDL_RESTRICTIONS, "cdl_restrictions")


class StatusChange(BaseModel):
    lifecycle_status: str
    reason: Optional[str] = Field(default=None, max_length=2000)

    # iter285 · dates that may accompany a status transition. The route
    # also accepts these via PATCH, but allowing them on the dedicated
    # status-change endpoint keeps the lifecycle event atomic.
    last_day_worked: Optional[str] = None
    termination_date: Optional[str] = None
    leave_start_date: Optional[str] = None
    expected_return_date: Optional[str] = None
    separation_type: Optional[str] = None

    # iter316 · rehire eligibility — required on any transition into
    # Terminated/Resigned/Retired unless the employee already carries
    # one from a prior offboarding cycle. Validation lives in the
    # route handler so reactivation cycles can carry the prior value.
    rehire_eligibility: Optional[str] = None
    rehire_eligibility_reason: Optional[str] = Field(default=None, max_length=500)

    @field_validator("lifecycle_status")
    @classmethod
    def _v_status(cls, v: str) -> str:
        if v not in ALLOWED_LIFECYCLE_STATUSES:
            raise ValueError("invalid status")
        return v

    @field_validator(
        "last_day_worked", "termination_date",
        "leave_start_date", "expected_return_date",
    )
    @classmethod
    def _v_date(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return v
        if not _is_date_string(v):
            raise ValueError("date must be YYYY-MM-DD")
        return v

    @field_validator("separation_type")
    @classmethod
    def _v_sep(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return v
        if v not in ALLOWED_SEPARATION_TYPES:
            raise ValueError(f"separation_type must be one of {sorted(ALLOWED_SEPARATION_TYPES)}")
        return v

    @field_validator("rehire_eligibility")
    @classmethod
    def _v_rehire(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return v
        if v not in ALLOWED_REHIRE_ELIGIBILITY:
            raise ValueError(
                f"rehire_eligibility must be one of {sorted(ALLOWED_REHIRE_ELIGIBILITY)}"
            )
        return v


# iter316 · Reactivation / rehire payload. Bounded: HR/Admin can flip
# a previously-inactive/terminated employee back to Active or Pending
# Hire without creating a duplicate. Original hire date is preserved.
class ReactivatePayload(BaseModel):
    lifecycle_status: str = "Active"  # Active or Pending Hire only
    rehire_date: Optional[str] = None
    reason: Optional[str] = Field(default=None, max_length=2000)

    @field_validator("lifecycle_status")
    @classmethod
    def _v_status(cls, v: str) -> str:
        if v not in {"Active", "Pending Hire"}:
            raise ValueError(
                "reactivation lifecycle_status must be 'Active' or 'Pending Hire'"
            )
        return v

    @field_validator("rehire_date")
    @classmethod
    def _v_date(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return v
        if not _is_date_string(v):
            raise ValueError("date must be YYYY-MM-DD")
        return v


# ──────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────
def _strip_id(d: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not d:
        return d
    d.pop("_id", None)
    return d


def _is_active_for_status(status: str) -> bool:
    return status in _ACTIVE_STATUSES


# iter316 · inactive/terminated duplicate-match candidate finder.
# Used by create_employee when `?force=false` to warn HR they may be
# duplicating a previously-inactive record. Returns a compact dict
# (id/name/email/lifecycle_status/last_day_worked/termination_date/
# rehire_eligibility) or None.
_INACTIVE_DUP_MATCH_STATUSES = {
    "Inactive", "Terminated", "Resigned", "Retired",
}


async def _find_inactive_match(
    db, name: str, email: Optional[str],
) -> Optional[Dict[str, Any]]:
    name_clean = (name or "").strip()
    email_clean = (email or "").strip().lower()
    if not name_clean and not email_clean:
        return None
    or_clauses: List[Dict[str, Any]] = []
    if name_clean:
        # Case-insensitive exact match on name.
        or_clauses.append({
            "name": {"$regex": f"^{_re.escape(name_clean)}$", "$options": "i"},
        })
    if email_clean:
        or_clauses.append({
            "email": {"$regex": f"^{_re.escape(email_clean)}$", "$options": "i"},
        })
    if not or_clauses:
        return None
    query = {
        "$and": [
            {"deleted_at": None},
            {"$or": or_clauses},
            {"lifecycle_status": {"$in": list(_INACTIVE_DUP_MATCH_STATUSES)}},
        ],
    }
    candidate = await db.employees.find_one(
        query,
        {"_id": 0, "id": 1, "name": 1, "email": 1, "employee_id": 1,
         "lifecycle_status": 1, "last_day_worked": 1,
         "termination_date": 1, "rehire_eligibility": 1},
    )
    return candidate


async def _resolve_offboarding_pm_targets(
    db, employee: Dict[str, Any],
) -> List[Dict[str, str]]:
    """Track 15.1 (2026-06-16) — Defect 1: PM notification leakage.

    For the offboarded employee, return one target per (project_number,
    pm_user_id) pair so we can create a per-PM "Backfill open project
    assignments" task instead of broadcasting to every PM in the system.

    Returns [] when the employee has no active project_team_assignments
    — in that case the caller should skip the PM playbook row entirely
    so PMs never receive offboarding noise for someone who wasn't on
    one of their projects.
    """
    emp_id = employee.get("id")
    emp_email = (employee.get("email") or "").strip().lower()
    if not (emp_id or emp_email):
        return []
    # 1. Active assignments tied to this employee.
    or_clauses: List[Dict[str, Any]] = []
    if emp_id:
        or_clauses.append({"employee_id": emp_id})
    if emp_email:
        or_clauses.append({"email": emp_email})
    project_numbers: set = set()
    try:
        cur = db.project_team_assignments.find(
            {
                "active": True,
                "$or": or_clauses,
            },
            {"_id": 0, "project_number": 1},
        )
        async for r in cur:
            pn = r.get("project_number")
            if pn:
                project_numbers.add(pn)
    except Exception:  # pragma: no cover
        return []
    if not project_numbers:
        return []
    # 2. For each project, find PMs (primary + co-PMs from jobs_master,
    #    plus assignment_role in ['pm','co_pm'] from staffing).
    targets: List[Dict[str, str]] = []
    seen_user_ids: set = set()
    for pn in project_numbers:
        pm_emails: set = set()
        try:
            job = await db.jobs_master.find_one(
                {"project_number": pn},
                {"_id": 0, "pm_email": 1, "co_pm_emails": 1},
            )
            if job:
                if job.get("pm_email"):
                    pm_emails.add(job["pm_email"].lower())
                for e in (job.get("co_pm_emails") or []):
                    if e:
                        pm_emails.add(e.lower())
            staff_cur = db.project_team_assignments.find(
                {
                    "project_number": pn,
                    "active": True,
                    "assignment_role": {"$in": ["pm", "co_pm"]},
                },
                {"_id": 0, "email": 1, "user_id": 1},
            )
            async for r in staff_cur:
                if r.get("email"):
                    pm_emails.add(r["email"].lower())
        except Exception:  # pragma: no cover
            continue
        # 3. Resolve PM emails to directory user_ids so we can scope
        #    the notification person-level.
        for em in pm_emails:
            try:
                u = await db.user_directory.find_one(
                    {"email": em},
                    {"_id": 0, "id": 1, "email": 1, "name": 1},
                )
            except Exception:  # pragma: no cover
                u = None
            if not u:
                continue
            uid = u.get("id")
            key = f"{uid}|{pn}"
            if not uid or key in seen_user_ids:
                continue
            seen_user_ids.add(key)
            targets.append({
                "user_id": uid,
                "email": u.get("email", ""),
                "name": u.get("name", ""),
                "project_number": pn,
            })
    return targets


async def _fan_out_offboarding_playbook(
    db, employee: Dict[str, Any], new_status: str, reason: Optional[str],
    actor: Dict[str, Any],
) -> List[str]:
    """Emit one task per playbook row via Phase A task_service.
    Returns the list of created task IDs."""
    from routes.tasks_notifications import task_service  # noqa: PLC0415
    created: List[str] = []
    label = f"Offboarding: {employee.get('name', '(unknown)')}"
    # Track 15.1 (2026-06-16) — Defect 1 fix: pre-resolve the
    # per-project PM targets so the PM playbook row scopes to only
    # the PMs of the employee's active projects, instead of
    # broadcasting to every PM in the directory.
    pm_targets: List[Dict[str, str]] = await _resolve_offboarding_pm_targets(db, employee)
    for row in _OFFBOARDING_PLAYBOOK:
        # PM row: scope to specific PMs per project (or skip entirely
        # when the employee has no active project assignments).
        if row["role"] == "pm":
            if not pm_targets:
                # No active project assignments → PMs need no task.
                # No broadcast notification is created either.
                continue
            for target in pm_targets:
                try:
                    task_id = await task_service.create(db, {
                        "title": (
                            f"{label} — {row['title']} "
                            f"({target['project_number']})"
                        ),
                        "description": (
                            f"Status: {new_status}. "
                            f"{('Reason: ' + reason) if reason else ''}\n\n"
                            f"Project: {target['project_number']}\n"
                            f"{row['desc']}"
                        ).strip(),
                        "source_module": "hr.offboarding",
                        "source_record_id": employee.get("id"),
                        "linked_employee_id": employee.get("id"),
                        "linked_project_number": target["project_number"],
                        "assignee_role": row["role"],
                        "assignee_user_id": target["user_id"],
                        "priority": row["priority"],
                        "created_by": {
                            "role": "hr",
                            "name": actor.get("name") or actor.get("email")
                                    or "HR Manager",
                        },
                    })
                    if task_id:
                        created.append(task_id)
                except Exception as e:  # pragma: no cover
                    logger.warning(
                        "offboarding playbook pm-task failed: %s", e,
                    )
            continue
        # Non-PM rows: existing role-broadcast behavior.
        try:
            task_id = await task_service.create(db, {
                "title": f"{label} — {row['title']}",
                "description": (
                    f"Status: {new_status}. "
                    f"{('Reason: ' + reason) if reason else ''}\n\n"
                    f"{row['desc']}"
                ).strip(),
                "source_module": "hr.offboarding",
                "source_record_id": employee.get("id"),
                "linked_employee_id": employee.get("id"),
                "assignee_role": row["role"],
                "priority": row["priority"],
                "created_by": {
                    "role": "hr",
                    "name": actor.get("name") or actor.get("email")
                            or "HR Manager",
                },
            })
            if task_id:
                created.append(task_id)
        except Exception as e:  # pragma: no cover
            logger.warning("offboarding playbook task failed: %s", e)
    # Iter160 · Operational signal — offboarding started.
    try:
        from lib.operational_signals import record_signal  # noqa: PLC0415
        await record_signal(
            db, signal="hr.offboarding_started", module="hr.offboarding",
            dims={"new_status": (new_status or "")[:24],
                  "tasks_created": len(created)},
        )
    except Exception:
        pass
    return created


# ──────────────────────────────────────────────────────────────────
# Router
# ──────────────────────────────────────────────────────────────────
def build_employee_lifecycle_router(db, require_hr, require_admin,
                                     require_any_portal_token):
    """Builds the HR-employee + offboarding-summary router.

    Authentication: write endpoints accept either HR or Admin tokens
    (via require_hr_or_admin); read endpoints accept any portal token.
    """
    router = APIRouter(tags=["employee-lifecycle"])

    async def require_hr_or_admin(actor: Dict[str, Any] = Depends(require_any_portal_token)) -> Dict[str, Any]:
        role = actor.get("_actor") or actor.get("role") or ""
        if role in ("hr", "admin"):
            return actor
        raise HTTPException(403, "HR or Admin only")

    # ── Shared HR roster query ────────────────────────────────────────
    # Track 15.21A · Single source of truth for the HR employee dataset.
    # Used by both `GET /api/hr/employees` (roster + print source) and
    # `GET /api/hr/employees/export.xlsx` (Excel export). Same filters,
    # same dataset, zero drift between screen / print / export.
    def _build_employee_query(
        show_inactive: bool,
        lifecycle_status: Optional[str],
        rehire_eligibility: Optional[str],
        q: Optional[str],
        *,
        bucket: Optional[str] = None,
        crew: Optional[str] = None,
        supervisor: Optional[str] = None,
        trade: Optional[str] = None,
    ) -> Dict[str, Any]:
        """TRACK 27.00 · canonical query builder.

        Rules HR can trust:
          - `bucket` is the primary employment filter. Values: any /
            active / pending / off_roll / terminated / retired.
            Sourced from `lib.employee_status.BUCKET_STATUSES`.
          - `lifecycle_status` is the secondary detailed filter. When
            combined with `bucket`, both must agree — picking
            "Terminated" while bucket=active would produce an empty
            intersection *by definition*, so we short-circuit that
            combination and let the caller present a warning instead
            of a mystery-zero result.
          - `show_inactive` remains for backward compat with older
            callers (Daily Report autofill etc.). When bucket is set,
            show_inactive is ignored (the bucket is the source of
            truth).
          - Crew / Supervisor / Trade filters compose with AND.
            Explicit sentinel "(unassigned)" matches blank + null.
        """
        from lib.employee_status import (  # noqa: PLC0415
            mongo_clause_for_bucket, status_belongs_to_bucket,
            validate_bucket,
        )
        clauses: List[Dict[str, Any]] = [{"deleted_at": None}]

        effective_bucket = validate_bucket(bucket) if bucket is not None else None

        if effective_bucket is not None:
            # Bucket-driven mode (Track 27.00). Ignore legacy
            # show_inactive when the caller has explicitly picked a
            # bucket — the bucket already carries that intent.
            bucket_clause = mongo_clause_for_bucket(effective_bucket)
            if bucket_clause is not None:
                clauses.append(bucket_clause)
            if lifecycle_status:
                # Guard the impossible intersection (e.g. bucket=active
                # + status=Terminated). Return an unmatchable clause so
                # the API responds honestly with 0 rows instead of
                # letting Mongo AND them and produce a mystery-zero
                # that HR can't explain.
                if not status_belongs_to_bucket(
                    lifecycle_status, effective_bucket,
                ):
                    clauses.append({"_impossible_intersection": True})
                else:
                    clauses.append({"lifecycle_status": lifecycle_status})
        else:
            # Legacy path — preserved verbatim so no existing caller
            # regresses. This is what /api/hr/employees looked like
            # pre-Track 27.00.
            if not show_inactive:
                clauses.append({"$or": [
                    {"lifecycle_status": {"$in": list(_ACTIVE_STATUSES)}},
                    {"lifecycle_status": {"$exists": False},
                     "is_active": {"$ne": False}},
                ]})
            if lifecycle_status:
                clauses.append({"lifecycle_status": lifecycle_status})

        # iter316 · rehire-eligibility filter
        if rehire_eligibility:
            if rehire_eligibility not in ALLOWED_REHIRE_ELIGIBILITY:
                raise HTTPException(
                    400,
                    f"rehire_eligibility must be one of "
                    f"{sorted(ALLOWED_REHIRE_ELIGIBILITY)}",
                )
            clauses.append({"rehire_eligibility": rehire_eligibility})

        # Track 27.00 · crew filter. "(unassigned)" surfaces blank + null.
        if crew:
            if crew == "(unassigned)":
                clauses.append({"$or": [
                    {"crew": {"$in": [None, ""]}},
                    {"crew": {"$exists": False}},
                ]})
            else:
                clauses.append({"crew": crew})

        # Track 27.00 · supervisor filter. Same unassigned semantics.
        if supervisor:
            if supervisor == "(unassigned)":
                clauses.append({"$or": [
                    {"supervisor": {"$in": [None, ""]}},
                    {"supervisor": {"$exists": False}},
                ]})
            else:
                clauses.append({"supervisor": supervisor})

        # Track 27.00 · trade filter.
        if trade:
            if trade == "(unassigned)":
                clauses.append({"$or": [
                    {"trade": {"$in": [None, ""]}},
                    {"trade": {"$exists": False}},
                ]})
            else:
                clauses.append({"trade": trade})

        if q:
            # Track 14.0-HR-IDENTITY · search resolves legal first /
            # middle / last, preferred name, denormalised `name`,
            # employee_id, and trade.
            # Track 27.00 · search now ALSO matches crew and supervisor
            # so "Jason" finds employees supervised by Jason, not just
            # employees named Jason.
            clauses.append({"$or": [
                {"name": safe_regex(q)},
                {"legal_first_name": safe_regex(q)},
                {"legal_middle_name": safe_regex(q)},
                {"legal_last_name": safe_regex(q)},
                {"preferred_name": safe_regex(q)},
                {"employee_id": safe_regex(q)},
                {"trade": safe_regex(q)},
                {"crew": safe_regex(q)},
                {"supervisor": safe_regex(q)},
            ]})
        return {"$and": clauses}

    # ── HR employee CRUD ──────────────────────────────────────────────
    @router.get("/api/hr/employees")
    async def list_employees(
        actor: Dict[str, Any] = Depends(require_hr_or_admin),
        show_inactive: bool = Query(default=False),
        lifecycle_status: Optional[str] = Query(default=None),
        rehire_eligibility: Optional[str] = Query(default=None),
        q: Optional[str] = Query(default=None, max_length=80),
        limit: int = Query(default=500, ge=1, le=2000),
        # Track 27.00 · new filter primitives.
        bucket: Optional[str] = Query(default=None),
        crew: Optional[str] = Query(default=None, max_length=120),
        supervisor: Optional[str] = Query(default=None, max_length=120),
        trade: Optional[str] = Query(default=None, max_length=120),
    ) -> Dict[str, Any]:
        try:
            final = _build_employee_query(
                show_inactive, lifecycle_status, rehire_eligibility, q,
                bucket=bucket, crew=crew, supervisor=supervisor, trade=trade,
            )
        except ValueError as e:
            raise HTTPException(400, str(e))
        # Track 27.00 · impossible bucket + status intersection —
        # respond honestly with 0 rows and a machine-readable hint.
        impossible = any(c.get("_impossible_intersection") for c in final.get("$and", []))
        if impossible:
            return {
                "items": [], "count": 0,
                "warning": {
                    "code": "impossible_intersection",
                    "message": (
                        f"lifecycle_status={lifecycle_status!r} is not in "
                        f"the {bucket!r} bucket. Pick a status inside "
                        f"the bucket, or clear the bucket filter."
                    ),
                },
            }
        # Ask Mongo for total match count (unlimited) so the UI can show
        # "Showing first 500 of 923" instead of silently truncating.
        total_matching = await db.employees.count_documents(final)
        cur = db.employees.find(final, {"_id": 0}).sort("name", 1).limit(limit)
        from masci.identity import format_employee_identity
        items = []
        async for d in cur:
            d = _strip_id(d) or {}
            d["tenure_days"] = _tenure_days(d)
            d["display_identity"] = format_employee_identity(d)
            items.append(d)
        return {
            "items": items,
            "count": len(items),
            "total_matching": total_matching,
            "truncated": total_matching > len(items),
        }

    # ── Track 15.21A · HR Roster Excel Export ─────────────────────────
    # Generates an .xlsx of the same dataset the HR roster page renders,
    # using the same filters. Audit doc: /app/memory/
    # TRACK_15_21_HR_EMPLOYEE_ROSTER_EXPORT_PRINT_AUDIT.md.
    #
    # Sensitive fields explicitly excluded (per operator directive):
    #   - cdl_license_number
    #   - rehire_eligibility_reason
    #   - status_history (free-text per-transition reasons)
    @router.get("/api/hr/employees/export.xlsx")
    async def export_hr_employees_xlsx(
        actor: Dict[str, Any] = Depends(require_hr_or_admin),
        show_inactive: bool = Query(default=False),
        lifecycle_status: Optional[str] = Query(default=None),
        rehire_eligibility: Optional[str] = Query(default=None),
        q: Optional[str] = Query(default=None, max_length=80),
        limit: int = Query(default=5000, ge=1, le=10000),
        bucket: Optional[str] = Query(default=None),
        crew: Optional[str] = Query(default=None, max_length=120),
        supervisor: Optional[str] = Query(default=None, max_length=120),
        trade: Optional[str] = Query(default=None, max_length=120),
    ):
        try:
            final = _build_employee_query(
                show_inactive, lifecycle_status, rehire_eligibility, q,
                bucket=bucket, crew=crew, supervisor=supervisor, trade=trade,
            )
        except ValueError as e:
            raise HTTPException(400, str(e))
        # Impossible bucket + status intersection → empty export, no rows.
        if any(c.get("_impossible_intersection") for c in final.get("$and", [])):
            docs = []
        else:
            docs = await db.employees.find(
                final, {"_id": 0}
            ).sort("name", 1).to_list(limit)
        # Column order matches Track 15.21A directive exactly.
        header = [
            "Employee Name", "Preferred Name", "Status", "Position",
            "Department", "Phone", "Email", "Hire Date", "Supervisor",
        ]
        rows = []
        for d in docs:
            legal_parts = [
                d.get("legal_first_name") or "",
                d.get("legal_last_name") or "",
            ]
            legal = " ".join(p for p in legal_parts if p).strip()
            rows.append([
                legal or (d.get("name") or ""),
                d.get("preferred_name") or "",
                d.get("lifecycle_status") or (
                    "Active" if d.get("is_active") is not False else "Inactive"
                ),
                d.get("role") or "",
                d.get("department") or "",
                d.get("phone") or "",
                d.get("email") or "",
                d.get("original_hire_date") or d.get("hire_date") or "",
                d.get("supervisor") or "",
            ])
        # Reuse the existing server.py helper — same code path used by
        # /admin/employees/export, /admin/suppliers/export, etc.
        from server import _xlsx_response, _today_stamp  # noqa: PLC0415
        return _xlsx_response(
            rows, header,
            f"MASCI_HR_Employee_Roster_{_today_stamp()}.xlsx",
            "Employees",
        )

    # ── TRACK 27.00 · Employee Facets (crew / supervisor / trade) ─────
    # Powers the HR filter bar's dynamic dropdowns. No hardcoded crew
    # lists, no hardcoded supervisor names — HR sees exactly the values
    # currently in their live data, with counts, so they can spot both
    # the healthy values ("Paving · 42") and the data-quality gaps
    # ("(unassigned) · 246"). Cached in-process for 60 s to keep the
    # filter bar snappy without hammering Mongo when HR is typing.
    _facet_cache: Dict[str, Any] = {"ts": 0.0, "payload": None}

    async def _facet_values(field: str, *, limit: int = 100) -> List[Dict[str, Any]]:
        pipeline = [
            {"$match": {"deleted_at": None}},
            {"$group": {
                "_id": {"$ifNull": [f"${field}", None]},
                "count": {"$sum": 1},
            }},
            {"$sort": {"count": -1, "_id": 1}},
            {"$limit": limit},
        ]
        assigned: List[Dict[str, Any]] = []
        unassigned_count = 0
        async for row in db.employees.aggregate(pipeline):
            raw = row.get("_id")
            # Coerce blank / null / missing into a single "(unassigned)"
            # sentinel so the frontend gets one honest label for that
            # bucket instead of three near-duplicates.
            if raw is None or (isinstance(raw, str) and not raw.strip()):
                unassigned_count += row["count"]
            else:
                assigned.append({"value": raw, "label": raw,
                                 "count": row["count"], "unassigned": False})
        # Move "(unassigned)" to the end so the healthiest values render
        # first in the dropdown; hide it entirely when the field is
        # 100% populated (no need to offer a filter that matches nobody).
        out = assigned
        if unassigned_count:
            out = assigned + [{
                "value": "(unassigned)", "label": "(unassigned)",
                "count": unassigned_count, "unassigned": True,
            }]
        return out

    @router.get("/api/hr/employees/facets")
    async def hr_employee_facets(
        actor: Dict[str, Any] = Depends(require_hr_or_admin),
    ) -> Dict[str, Any]:
        """Return distinct crew / supervisor / trade values with counts.

        This endpoint is the single source of truth for the HR filter
        bar's Crew / Supervisor / Trade dropdowns. Nothing hardcoded.
        """
        import time  # noqa: PLC0415
        now = time.time()
        cached = _facet_cache.get("payload")
        if cached and (now - _facet_cache["ts"] < 60.0):
            return cached
        from lib.employee_status import BUCKET_LABELS, BUCKET_ORDER  # noqa: PLC0415
        crews = await _facet_values("crew")
        supers = await _facet_values("supervisor")
        trades = await _facet_values("trade")
        payload = {
            "crews": crews,
            "supervisors": supers,
            "trades": trades,
            "buckets": [
                {"value": b, "label": BUCKET_LABELS[b]}
                for b in ["any", *BUCKET_ORDER]
            ],
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        _facet_cache["ts"] = now
        _facet_cache["payload"] = payload
        return payload


    # ── TRACK 23.6 · Employee record completeness (read-only) ─────────
    # Purpose: check-engine light for whether Employee Lifecycle
    # records carry the identity fields downstream systems (Daily
    # Report autofill, ODS labor_fact, HR Time Verification, Payroll
    # Variance, PM Intelligence) rely on.
    #
    # Uses the shared `lib.employee_identity.normalize_employee_identity`
    # from Track 23.5. Does NOT re-implement projection logic. Does
    # NOT edit employee records. Does NOT create duplicate fields.
    # Does NOT touch Daily Report. Does NOT fire alerts.
    async def _completeness_snapshot(
        include_inactive: bool = False,
    ) -> Dict[str, Any]:
        from datetime import datetime, timezone  # noqa: PLC0415
        from lib.employee_identity import (  # noqa: PLC0415
            PUBLIC_ROSTER_PROJECTION,
            normalize_employee_identity,
        )
        # Reuse the exact filter the HR roster and /api/employees use
        # so counts never drift.
        clauses: List[Dict[str, Any]] = [{"deleted_at": None}]
        if not include_inactive:
            clauses.append({"$or": [
                {"lifecycle_status": {"$in": list(_ACTIVE_STATUSES)}},
                {"lifecycle_status": {"$exists": False},
                 "is_active": {"$ne": False}},
                {"lifecycle_status": None, "is_active": {"$ne": False}},
            ]})
        cursor = db.employees.find(
            {"$and": clauses}, PUBLIC_ROSTER_PROJECTION,
        ).sort("name", 1)

        total = 0
        trade_role_complete = 0
        crew_complete = 0
        sup_complete = 0
        fully_complete = 0
        missing_records: List[Dict[str, Any]] = []
        async for raw in cursor:
            total += 1
            emp = normalize_employee_identity(raw)
            has_trade = bool((emp.get("trade_role_display") or "").strip())
            has_crew = bool((emp.get("crew_display") or "").strip())
            has_sup = bool((emp.get("supervisor_display") or "").strip())
            if has_trade:
                trade_role_complete += 1
            if has_crew:
                crew_complete += 1
            if has_sup:
                sup_complete += 1
            if has_trade and has_crew and has_sup:
                fully_complete += 1
                continue
            missing_fields: List[str] = []
            if not has_trade:
                missing_fields.append("trade_role")
            if not has_crew:
                missing_fields.append("crew")
            if not has_sup:
                missing_fields.append("supervisor")
            missing_records.append({
                "employee_id": emp.get("employee_id") or "",
                "id": emp.get("id") or "",
                "name": emp.get("name") or "",
                "preferred_name": emp.get("preferred_name") or "",
                "display_identity": emp.get("display_identity") or emp.get("name") or "",
                "trade_role_display": emp.get("trade_role_display") or "",
                "crew_display": emp.get("crew_display") or "",
                "supervisor_display": emp.get("supervisor_display") or "",
                "missing_fields": missing_fields,
                "lifecycle_status": emp.get("lifecycle_status") or (
                    "Active" if emp.get("is_active") is not False else "Inactive"
                ),
            })

        pct = (fully_complete / total * 100.0) if total else 100.0
        if pct >= 95.0:
            band = "green"
        elif pct >= 75.0:
            band = "amber"
        else:
            band = "red"
        return {
            "total_active": total,
            "complete_count": fully_complete,
            "trade_role_complete_count": trade_role_complete,
            "crew_complete_count": crew_complete,
            "supervisor_complete_count": sup_complete,
            "completion_percent": round(pct, 1),
            "status_band": band,
            "missing_records": missing_records,
            "include_inactive": include_inactive,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "contract_version": "23.6",
        }

    @router.get("/api/hr/employee-completeness")
    async def employee_completeness(
        actor: Dict[str, Any] = Depends(require_hr_or_admin),
        include_inactive: bool = Query(default=False),
        missing_only: Optional[str] = Query(
            default=None,
            description="Comma-separated: trade_role,crew,supervisor. Filters missing_records to rows lacking ANY of the named fields.",
        ),
    ) -> Dict[str, Any]:
        """Read-only Employee Record Completeness snapshot (TRACK 23.6).

        HR/Admin only. Never mutates. Never fires alerts. Never leaks
        private HR fields. Uses the shared normalized identity
        contract from Track 23.5.
        """
        snap = await _completeness_snapshot(include_inactive=include_inactive)
        if missing_only:
            wanted = {
                s.strip() for s in missing_only.split(",")
                if s.strip() in {"trade_role", "crew", "supervisor"}
            }
            if wanted:
                snap["missing_records"] = [
                    r for r in snap["missing_records"]
                    if wanted.intersection(r["missing_fields"])
                ]
        return snap

    @router.get("/api/hr/employee-completeness.csv")
    async def employee_completeness_csv(
        actor: Dict[str, Any] = Depends(require_hr_or_admin),
        include_inactive: bool = Query(default=False),
    ):
        """CSV export of missing-records list (HR/Admin only)."""
        from fastapi.responses import Response  # noqa: PLC0415
        import csv  # noqa: PLC0415
        from io import StringIO  # noqa: PLC0415
        snap = await _completeness_snapshot(include_inactive=include_inactive)
        buf = StringIO()
        writer = csv.writer(buf)
        writer.writerow([
            "employee_id", "legal_name", "preferred_name",
            "trade_role_display", "crew_display", "supervisor_display",
            "missing_fields", "lifecycle_status",
        ])
        for r in snap["missing_records"]:
            writer.writerow([
                r["employee_id"], r["name"], r["preferred_name"],
                r["trade_role_display"], r["crew_display"],
                r["supervisor_display"],
                ";".join(r["missing_fields"]),
                r["lifecycle_status"],
            ])
        return Response(
            content=buf.getvalue(),
            media_type="text/csv",
            headers={
                "Content-Disposition": 'attachment; filename="MASCI_Employee_Completeness.csv"',
                "X-Content-Type-Options": "nosniff",
            },
        )



    @router.post("/api/hr/employees")
    async def create_employee(
        body: EmployeeCreate,
        actor: Dict[str, Any] = Depends(require_hr_or_admin),
        force: bool = Query(default=False),
    ) -> Dict[str, Any]:
        name = body.name.strip()
        # iter316 · strict block ONLY for *active* exact-name collisions.
        # An inactive/terminated record with the same name should drop
        # to the informational reactivation warning below, not a hard
        # block — operators should reactivate, not get stonewalled.
        existing_active = await db.employees.find_one(
            {
                "name": {"$regex": f"^{_re.escape(name)}$", "$options": "i"},
                "deleted_at": None,
                "$or": [
                    {"lifecycle_status": {"$in": list(_ACTIVE_STATUSES)}},
                    {"lifecycle_status": {"$exists": False},
                     "is_active": {"$ne": False}},
                ],
            },
            {"_id": 0},
        )
        if existing_active:
            raise HTTPException(409, f"An employee named '{name}' already exists")

        # iter316 · duplicate prevention — informational warning when
        # the incoming name OR email matches an inactive/terminated
        # employee. HR can `?force=true` to bypass after acknowledging.
        if not force:
            inactive_match = await _find_inactive_match(db, name, body.email)
            if inactive_match:
                raise HTTPException(
                    409,
                    {
                        "error": "possible_existing_inactive",
                        "message": (
                            "Possible existing inactive/terminated employee "
                            "found. Reactivate existing employee instead of "
                            "creating a duplicate?"
                        ),
                        "candidate": inactive_match,
                    },
                )
        now = datetime.now(timezone.utc).isoformat()
        doc = {
            "id": str(uuid.uuid4()),
            "name": name,
            "trade": body.trade or "",
            "role": body.role or "",
            "crew": body.crew or "",
            "employee_id": body.employee_id or "",
            "email": body.email or "",
            "phone": body.phone or "",
            "supervisor": body.supervisor or "",
            "department": body.department or "",
            "default_project_number": body.default_project_number or "",
            "hire_date": body.hire_date or None,
            # iter285 · lifecycle date structure
            "original_hire_date": (body.original_hire_date or None),
            "last_day_worked": (body.last_day_worked or None),
            "termination_date": (body.termination_date or None),
            "leave_start_date": (body.leave_start_date or None),
            "expected_return_date": (body.expected_return_date or None),
            "separation_type": (body.separation_type or None),
            # iter316 · rehire eligibility + rehire-cycle date
            "rehire_eligibility": (body.rehire_eligibility or None),
            "rehire_eligibility_reason": (body.rehire_eligibility_reason or None),
            "rehire_date": (body.rehire_date or None),
            # iter286 · driver qualification structure
            "cdl_holder": (body.cdl_holder if body.cdl_holder is not None else False),
            "approved_company_driver": (
                body.approved_company_driver
                if body.approved_company_driver is not None else False
            ),
            "driver_status": (body.driver_status or None),
            "cdl_license_number": (body.cdl_license_number or None),
            "cdl_state": (body.cdl_state or None),
            "cdl_expiration_date": (body.cdl_expiration_date or None),
            "medical_card_expiration_date": (body.medical_card_expiration_date or None),
            # iter287 · CDL endorsements + restrictions (structured codes)
            "cdl_endorsements": (body.cdl_endorsements or []),
            "cdl_restrictions": (body.cdl_restrictions or []),
            "lifecycle_status": body.lifecycle_status,
            "is_active": _is_active_for_status(body.lifecycle_status),
            "added_via": "hr-portal",
            "created_at": now,
            "updated_at": now,
            "status_history": [{
                "at": now,
                "by": actor.get("name") or actor.get("email") or "hr",
                "to": body.lifecycle_status,
                "reason": None,
            }],
            "deleted_at": None,
        }
        await db.employees.insert_one(doc)

        # iter286 · mirror CDL + medical-card expirations on create too
        # (PATCH path also mirrors). Same scope discipline: only mirror
        # when a non-empty date was supplied. `existing` is empty so any
        # supplied value is treated as a change.
        await _mirror_driver_doc_expirations(db, doc["id"], doc, {})

        # TRACK 16.11 · HR-safe lifecycle hook. Transportation reads HR
        # and updates its own projection. HR write is already complete
        # at this point; sync failure CANNOT block the HR response.
        try:
            from lib.transport_hr_lifecycle import safe_sync_after_hr_write  # noqa: PLC0415
            await safe_sync_after_hr_write(
                db, doc.get("employee_id") or doc.get("id"),
                trigger="hr.employee_created",
                actor=(actor or {}).get("email") or (actor or {}).get("name"),
            )
        except Exception as _e:  # noqa: BLE001
            logger.warning("transport_hr_lifecycle hook (create) failed: %s", _e)

        out = _strip_id(doc) or {}
        out["tenure_days"] = _tenure_days(out)
        return out

    @router.patch("/api/hr/employees/{employee_id}")
    async def patch_employee(
        employee_id: str,
        body: EmployeePatch,
        actor: Dict[str, Any] = Depends(require_hr_or_admin),
    ) -> Dict[str, Any]:
        existing = await db.employees.find_one(
            {"id": employee_id, "deleted_at": None}, {"_id": 0})
        if not existing:
            raise HTTPException(404, "Employee not found")
        incoming = body.model_dump(exclude_none=True)

        # iter285 · write-once enforcement for original_hire_date (and
        # any future write-once fields enumerated in _WRITE_ONCE_FIELDS).
        # Audit iter284 §2.2 / §6 risk #1: hire-date overwrite was the
        # highest structural risk in the schema. Once persisted as a
        # non-empty value, the field cannot be re-set to a different
        # value via PATCH. Re-sending the same value is a no-op (so
        # idempotent UI re-saves don't error).
        for fname in _WRITE_ONCE_FIELDS:
            cur = (existing.get(fname) or "").strip() if isinstance(existing.get(fname), str) else existing.get(fname)
            incoming_v = (incoming.get(fname) or "").strip() if isinstance(incoming.get(fname), str) else incoming.get(fname)
            if cur and incoming_v and cur != incoming_v:
                raise HTTPException(
                    409,
                    f"{fname} is write-once and is already set to {cur!r}; "
                    f"refusing to overwrite with {incoming_v!r}. Rehire "
                    f"flows are not supported in this surface.",
                )

        update: Dict[str, Any] = {
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        for k, v in incoming.items():
            update[k] = v

        # HR-EMPLOYEE-001 · P0 · Name-change audit trail.
        # If the patch carries a `name` and the value actually changed,
        # write an employee_lifecycle_events row capturing old/new/actor
        # so the Accountability Timeline and audit_events surface the
        # correction. Historical records (DRs, meetings, etc.) are NOT
        # rewritten — they keep whatever name string was captured at
        # the time.
        old_name = (existing.get("name") or "").strip()
        new_name = (incoming.get("name") or "").strip() if "name" in incoming else None
        name_changed = bool(new_name) and new_name != old_name

        # HR-EMPLOYEE-002 · preferred-name audit
        old_pref = (existing.get("preferred_name") or "").strip()
        new_pref = (incoming.get("preferred_name") or "").strip() if "preferred_name" in incoming else None
        pref_changed = ("preferred_name" in incoming) and (new_pref != old_pref)

        await db.employees.update_one({"id": employee_id}, {"$set": update})

        if name_changed:
            try:
                actor_email = (actor or {}).get("email") or (actor or {}).get("actor_email") or "hr"
                actor_role = (actor or {}).get("role") or (actor or {}).get("actor_role") or "hr"
                await db.employee_lifecycle_events.insert_one({
                    "id": str(uuid.uuid4()),
                    "employee_id": employee_id,
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "kind": "name_changed",
                    "actor_email": actor_email,
                    "actor_role": actor_role,
                    "actor_label": (actor or {}).get("actor_label") or actor_email,
                    "old_value": old_name or None,
                    "new_value": new_name,
                    "from_status": None,
                    "to_status": None,
                })
            except Exception as e:  # noqa: BLE001
                logger.warning(f"[hr-employee-001] audit write failed: {e}")

        if pref_changed:
            try:
                actor_email = (actor or {}).get("email") or (actor or {}).get("actor_email") or "hr"
                actor_role = (actor or {}).get("role") or (actor or {}).get("actor_role") or "hr"
                await db.employee_lifecycle_events.insert_one({
                    "id": str(uuid.uuid4()),
                    "employee_id": employee_id,
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "kind": "preferred_name_changed",
                    "actor_email": actor_email,
                    "actor_role": actor_role,
                    "actor_label": (actor or {}).get("actor_label") or actor_email,
                    "old_value": old_pref or None,
                    "new_value": new_pref or None,
                    "from_status": None,
                    "to_status": None,
                })
            except Exception as e:  # noqa: BLE001
                logger.warning(f"[hr-employee-002] audit write failed: {e}")

        # iter286 · mirror CDL + medical-card expirations into the
        # existing `document_expirations` collection so the platform's
        # expiration scanner (routes/document_expirations.py) treats
        # driver-qualification expirations the same as every other
        # tracked document. NEVER create a second expiration system.
        await _mirror_driver_doc_expirations(db, employee_id, incoming, existing)

        # TRACK 16.11 · HR-safe lifecycle hook (PATCH). Fires AFTER
        # the HR write has been persisted. Never raises into the HR
        # response.
        try:
            from lib.transport_hr_lifecycle import safe_sync_after_hr_write  # noqa: PLC0415
            await safe_sync_after_hr_write(
                db, existing.get("employee_id") or employee_id,
                trigger="hr.employee_updated",
                actor=(actor or {}).get("email") or (actor or {}).get("name"),
            )
        except Exception as _e:  # noqa: BLE001
            logger.warning("transport_hr_lifecycle hook (patch) failed: %s", _e)

        doc = await db.employees.find_one(
            {"id": employee_id}, {"_id": 0})
        out = _strip_id(doc) or {}
        out["tenure_days"] = _tenure_days(out)
        return out

    @router.post("/api/hr/employees/{employee_id}/status")
    async def change_status(
        employee_id: str,
        body: StatusChange,
        actor: Dict[str, Any] = Depends(require_hr_or_admin),
    ) -> Dict[str, Any]:
        existing = await db.employees.find_one(
            {"id": employee_id, "deleted_at": None}, {"_id": 0})
        if not existing:
            raise HTTPException(404, "Employee not found")
        prev_status = existing.get("lifecycle_status") or (
            "Active" if existing.get("is_active") is not False else "Inactive"
        )
        if prev_status == body.lifecycle_status:
            return {"ok": True, "employee": existing, "tasks_created": 0,
                    "noop": True}

        # iter285 · status transitions that require / auto-populate
        # lifecycle dates. The route accepts these in the request body
        # (preferred) and back-fills sensible defaults from "today"
        # (date-only) when omitted. Separation type is REQUIRED for any
        # offboarding transition so the historical record can be
        # filtered/audited later without parsing free-text reasons.
        from datetime import date
        today_iso = date.today().isoformat()
        date_updates: Dict[str, Any] = {}
        is_offboarding = (
            body.lifecycle_status in _OFFBOARDING_STATUSES
            and prev_status not in _OFFBOARDING_STATUSES
        )
        is_going_on_leave = (
            body.lifecycle_status == "Leave of Absence"
            and prev_status != "Leave of Absence"
        )
        if is_offboarding:
            # Separation type is operationally required to keep
            # downstream reporting honest. Reject the transition
            # if the existing record + the request together don't
            # supply one. (Accept either the request body OR a
            # value already present on the employee.)
            existing_sep = (existing.get("separation_type") or "").strip()
            incoming_sep = (body.separation_type or "").strip()
            if not (existing_sep or incoming_sep):
                raise HTTPException(
                    400,
                    "separation_type is required when transitioning to "
                    f"{body.lifecycle_status} "
                    "(one of: voluntary, involuntary, layoff)",
                )
            if incoming_sep:
                date_updates["separation_type"] = incoming_sep

            # iter316 · rehire eligibility is required on every
            # transition into Terminated/Resigned/Retired so the
            # platform never silently assumes "eligible". Defaults
            # to review_required when neither the request nor the
            # existing record carries a value (mirror of operator
            # mandate · §"Default" — system must not assume eligible).
            existing_rehire = (existing.get("rehire_eligibility") or "").strip()
            incoming_rehire = (body.rehire_eligibility or "").strip()
            chosen_rehire = incoming_rehire or existing_rehire or "review_required"
            if chosen_rehire not in ALLOWED_REHIRE_ELIGIBILITY:
                raise HTTPException(
                    400,
                    "rehire_eligibility must be one of "
                    f"{sorted(ALLOWED_REHIRE_ELIGIBILITY)}",
                )
            # Reason is required for not_eligible and review_required.
            incoming_reason = (
                body.rehire_eligibility_reason
                if body.rehire_eligibility_reason is not None
                else existing.get("rehire_eligibility_reason")
            )
            incoming_reason_clean = (incoming_reason or "").strip()
            if (
                chosen_rehire in _REHIRE_ELIGIBILITY_REQUIRES_REASON
                and not incoming_reason_clean
            ):
                raise HTTPException(
                    400,
                    "rehire_eligibility_reason is required when "
                    f"rehire_eligibility is {chosen_rehire!r}",
                )
            date_updates["rehire_eligibility"] = chosen_rehire
            if incoming_reason_clean:
                date_updates["rehire_eligibility_reason"] = incoming_reason_clean
            elif chosen_rehire == "eligible":
                # Clean up any stale reason — operator chose Eligible
                # explicitly, no reason needs to ride along.
                date_updates["rehire_eligibility_reason"] = None

            # Termination date + last day worked default to today if
            # not provided. Both are stored so reporting can use
            # whichever makes sense; HR can edit either via PATCH
            # after the transition.
            date_updates["termination_date"] = (
                body.termination_date or existing.get("termination_date") or today_iso
            )
            date_updates["last_day_worked"] = (
                body.last_day_worked or existing.get("last_day_worked") or today_iso
            )
        if is_going_on_leave:
            # Leave of Absence without a leave_start_date is the
            # iter284 §6 risk #6 anti-pattern. Default to today;
            # accept an explicit value when provided. Expected
            # return is optional but kept structured when present.
            date_updates["leave_start_date"] = (
                body.leave_start_date or existing.get("leave_start_date") or today_iso
            )
            if body.expected_return_date:
                date_updates["expected_return_date"] = body.expected_return_date

        now = datetime.now(timezone.utc).isoformat()
        entry = {
            "at": now,
            "by": actor.get("name") or actor.get("email") or "hr",
            "from": prev_status,
            "to": body.lifecycle_status,
            "reason": body.reason,
        }
        set_block: Dict[str, Any] = {
            "lifecycle_status": body.lifecycle_status,
            "is_active": _is_active_for_status(body.lifecycle_status),
            "updated_at": now,
        }
        set_block.update(date_updates)
        await db.employees.update_one(
            {"id": employee_id},
            {
                "$set": set_block,
                "$push": {"status_history": entry},
            },
        )
        # Auto-offboarding playbook
        tasks_created: List[str] = []
        triggers_playbook = (
            body.lifecycle_status in _OFFBOARDING_STATUSES
            and prev_status not in _OFFBOARDING_STATUSES
        )
        if triggers_playbook:
            employee = await db.employees.find_one(
                {"id": employee_id}, {"_id": 0})
            tasks_created = await _fan_out_offboarding_playbook(
                db, employee or {}, body.lifecycle_status, body.reason, actor)

        # TRACK 16.11 · HR-safe lifecycle hook (status change). HR
        # transition is already persisted; this fires after.
        try:
            from lib.transport_hr_lifecycle import safe_sync_after_hr_write  # noqa: PLC0415
            await safe_sync_after_hr_write(
                db, existing.get("employee_id") or employee_id,
                trigger=f"hr.status_changed.{body.lifecycle_status}",
                actor=(actor or {}).get("email") or (actor or {}).get("name"),
            )
        except Exception as _e:  # noqa: BLE001
            logger.warning("transport_hr_lifecycle hook (status) failed: %s", _e)

        doc = await db.employees.find_one(
            {"id": employee_id}, {"_id": 0})
        out = _strip_id(doc) or {}
        out["tenure_days"] = _tenure_days(out)
        return {
            "ok": True,
            "employee": out,
            "tasks_created": len(tasks_created),
            "task_ids": tasks_created,
            "playbook_fired": triggers_playbook,
        }

    # ── iter316 · Reactivation / rehire ───────────────────────────────
    # Bounded action — HR/Admin only. Available when employee is
    # currently Inactive / Terminated / Resigned / Retired. Preserves
    # original_hire_date (write-once already enforces this), sets a
    # new rehire_date, flips lifecycle_status to Active or Pending
    # Hire, clears termination_date+last_day_worked for the new
    # cycle, and appends a `kind="reactivate"` event to status_history.
    # All previously-recorded offboarding events stay in the history;
    # this is purely additive.
    _REACTIVATABLE_STATUSES = {"Inactive", "Terminated", "Resigned", "Retired"}

    @router.post("/api/hr/employees/{employee_id}/reactivate")
    async def reactivate_employee(
        employee_id: str,
        body: ReactivatePayload,
        actor: Dict[str, Any] = Depends(require_hr_or_admin),
    ) -> Dict[str, Any]:
        existing = await db.employees.find_one(
            {"id": employee_id, "deleted_at": None}, {"_id": 0})
        if not existing:
            raise HTTPException(404, "Employee not found")
        prev_status = existing.get("lifecycle_status") or (
            "Active" if existing.get("is_active") is not False else "Inactive"
        )
        if prev_status not in _REACTIVATABLE_STATUSES:
            raise HTTPException(
                409,
                f"Cannot reactivate an employee whose current status is "
                f"{prev_status!r}; reactivation is only allowed from "
                f"{sorted(_REACTIVATABLE_STATUSES)}",
            )
        from datetime import date
        today_iso = date.today().isoformat()
        rehire_date = body.rehire_date or today_iso
        now = datetime.now(timezone.utc).isoformat()

        # Original hire date is preserved — _WRITE_ONCE_FIELDS guard
        # on PATCH protects against accidental overwrite. We do NOT
        # write original_hire_date here at all (already set).

        set_block: Dict[str, Any] = {
            "lifecycle_status": body.lifecycle_status,
            "is_active": _is_active_for_status(body.lifecycle_status),
            "rehire_date": rehire_date,
            # New employment cycle starts clean — termination dates
            # belong to the prior cycle. status_history retains the
            # full record (incl. the prior termination_date value).
            "termination_date": None,
            "last_day_worked": None,
            "updated_at": now,
        }
        entry = {
            "at": now,
            "by": actor.get("name") or actor.get("email") or "hr",
            "from": prev_status,
            "to": body.lifecycle_status,
            "reason": body.reason,
            "kind": "reactivate",
            "rehire_date": rehire_date,
            "preserved_original_hire_date": existing.get("original_hire_date"),
            "preserved_separation_type": existing.get("separation_type"),
            "preserved_termination_date": existing.get("termination_date"),
            "preserved_rehire_eligibility": existing.get("rehire_eligibility"),
        }
        await db.employees.update_one(
            {"id": employee_id},
            {
                "$set": set_block,
                "$push": {"status_history": entry},
            },
        )
        # Iter160-style signal (best-effort).
        try:
            from lib.operational_signals import record_signal  # noqa: PLC0415
            await record_signal(
                db, signal="hr.employee_reactivated",
                module="hr.lifecycle",
                dims={
                    "from_status": (prev_status or "")[:24],
                    "to_status": (body.lifecycle_status or "")[:24],
                },
            )
        except Exception:
            pass

        # TRACK 16.11 · HR-safe lifecycle hook (reactivate).
        try:
            from lib.transport_hr_lifecycle import safe_sync_after_hr_write  # noqa: PLC0415
            await safe_sync_after_hr_write(
                db, existing.get("employee_id") or employee_id,
                trigger="hr.employee_reactivated",
                actor=(actor or {}).get("email") or (actor or {}).get("name"),
            )
        except Exception as _e:  # noqa: BLE001
            logger.warning("transport_hr_lifecycle hook (reactivate) failed: %s", _e)

        doc = await db.employees.find_one(
            {"id": employee_id}, {"_id": 0})
        out = _strip_id(doc) or {}
        out["tenure_days"] = _tenure_days(out)
        return {"ok": True, "employee": out}

    @router.get("/api/hr/employees/{employee_id}/offboarding-summary")
    async def offboarding_summary(
        employee_id: str,
        actor: Dict[str, Any] = Depends(require_hr_or_admin),
    ) -> Dict[str, Any]:
        emp = await db.employees.find_one(
            {"id": employee_id, "deleted_at": None}, {"_id": 0})
        if not emp:
            raise HTTPException(404, "Employee not found")
        # Open tasks linked to this employee
        open_tasks_cur = db.tasks.find(
            {
                "linked_employee_id": employee_id,
                "status": {"$in": ["Open", "In Progress",
                                   "Pending Review", "Overdue"]},
            },
            {"_id": 0},
        ).sort("created_at", -1).limit(200)
        open_tasks = [d async for d in open_tasks_cur]

        # Document expirations linked to this employee
        docs_cur = db.document_expirations.find(
            {
                "linked_employee_id": employee_id,
                "status": {"$nin": ["Archived", "Not Applicable"]},
            },
            {"_id": 0},
        ).sort("expiration_date", 1).limit(200)
        # Coerce date-like fields to ISO strings for JSON safety.
        docs = []
        async for d in docs_cur:
            d.pop("_id", None)
            for k in ("issue_date", "expiration_date"):
                v = d.get(k)
                if hasattr(v, "isoformat") and not isinstance(v, str):
                    d[k] = v.isoformat()
            docs.append(d)

        # Equipment issuances — try a few common collection names.
        # Track 13.31B-D5 · enrich each row with canonical asset_class/type
        # so offboarding labels use one platform vocabulary.
        from services.asset_taxonomy import resolve_classification
        equipment_links: List[Dict[str, Any]] = []
        try:
            cur = db.equipment.find(
                {"assigned_to_id": employee_id},
                {"_id": 0, "id": 1, "name": 1, "unit_number": 1,
                 "asset_class": 1, "asset_type": 1, "category": 1, "type": 1,
                 "taxonomy_verified": 1, "taxonomy_source": 1},
            ).limit(50)
            async for d in cur:
                cls = resolve_classification(d)
                d["canonical_asset_class"] = cls["asset_class"]
                d["canonical_asset_type"] = cls["asset_type"]
                d["canonical_taxonomy_verified"] = cls["classification_verified"]
                d["classification_source"] = cls["classification_source"]
                equipment_links.append(d)
        except Exception:
            pass

        # Outstanding corrective actions / incidents counts (Phase A
        # already creates tasks for these, but we surface raw count too).
        try:
            ca_open = await db.corrective_actions.count_documents({
                "employee_master_id": employee_id,
                "status": {"$ne": "Closed"},
            })
        except Exception:
            ca_open = 0

        # Iter153 — Final PO Reconciliation: any open POs tied to this
        # employee. Closes the loop between HR + Field Leadership at
        # exactly the moment someone leaves the company.
        open_pos: List[Dict[str, Any]] = []
        try:
            cur_pos = db.po_requests.find(
                {
                    "$or": [
                        {"requested_by_employee_id": employee_id},
                        {"requested_by_user_id": employee_id},
                    ],
                    "status": {"$in": [
                        "Submitted", "Pending Approval", "Approved",
                        "Pending Receipt", "Clarification Needed",
                        "Overdue Receipt",
                    ]},
                },
                {"_id": 0, "id": 1, "po_number": 1, "vendor": 1,
                 "status": 1, "estimated_amount": 1, "approved_amount": 1,
                 "created_at": 1},
            ).sort("created_at", -1).limit(50)
            async for p in cur_pos:
                p.pop("_id", None)
                open_pos.append(p)
        except Exception:
            pass

        # Status history excerpt
        status_history = emp.get("status_history") or []
        last_status_change = status_history[-1] if status_history else None

        return {
            "employee": _strip_id(emp),
            "open_tasks": open_tasks,
            "open_tasks_count": len(open_tasks),
            "document_expirations": docs,
            "document_expirations_count": len(docs),
            "equipment_issuances": equipment_links,
            "equipment_issuances_count": len(equipment_links),
            "open_corrective_actions": ca_open,
            "open_pos": open_pos,
            "open_pos_count": len(open_pos),
            "last_status_change": last_status_change,
            "is_active": emp.get("is_active", True),
            "lifecycle_status": emp.get("lifecycle_status") or (
                "Active" if emp.get("is_active") is not False else "Inactive"
            ),
        }

    # ── iter288 · Driver Qualification operational dashboard ──────
    # Read-only visibility surface for HR/Admin. Filterable list +
    # tiny summary counts. NOT a compliance-management system. NOT
    # a dispatch-assignment tool. Just answers operational questions:
    #   - Who can legally drive?
    #   - Who is approved internally?
    #   - Who has restricted/suspended status?
    #   - What expires soon?
    #   - Who can haul tanker?
    @router.get("/api/hr/driver-qualification/dashboard")
    async def driver_qualification_dashboard(
        actor: Dict[str, Any] = Depends(require_hr_or_admin),
        cdl_holder: Optional[bool] = Query(default=None),
        approved: Optional[bool] = Query(default=None),
        driver_status: Optional[str] = Query(default=None),
        endorsement: Optional[str] = Query(default=None),
        expiring_cdl_30d: Optional[bool] = Query(default=None),
        expiring_medical_30d: Optional[bool] = Query(default=None),
        q: Optional[str] = Query(default=None, max_length=80),
        limit: int = Query(default=500, ge=1, le=2000),
    ) -> Dict[str, Any]:
        from datetime import date, timedelta
        today = date.today()
        cutoff_30d = (today + timedelta(days=30)).isoformat()
        today_iso = today.isoformat()

        # Base scope: non-deleted, employees who have any
        # driver-qualification signal at all (cdl_holder=True OR
        # approved=True OR any expiration date set). Avoids showing
        # the entire roster on the driver-visibility surface.
        base: Dict[str, Any] = {
            "deleted_at": None,
            "$or": [
                {"cdl_holder": True},
                {"approved_company_driver": True},
                # iter350 hardening: a stored value must be a real date
                # (truthy non-empty string), not None and not "". Before
                # this fix, an employee whose CDL date was cleared in the
                # HR roster (PATCH normalizes null → "") would stay
                # permanently visible on the dashboard with a blank
                # expiration column. The $nin clause excludes both.
                {"cdl_expiration_date":           {"$nin": [None, ""]}},
                {"medical_card_expiration_date":  {"$nin": [None, ""]}},
                # iter350 — also accept structured driver_status as a
                # qualification signal (an HR coordinator marking an
                # employee "active|restricted|suspended|inactive" is
                # explicitly tagging them as a driver).
                {"driver_status":                 {"$nin": [None, ""]}},
                # iter350 — and any CDL license number presence (HR
                # often records the number before they get the dates).
                {"cdl_license_number":            {"$nin": [None, ""]}},
            ],
        }

        clauses: List[Dict[str, Any]] = [base]
        if cdl_holder is not None:
            clauses.append({"cdl_holder": cdl_holder})
        if approved is not None:
            clauses.append({"approved_company_driver": approved})
        if driver_status:
            if driver_status not in ALLOWED_DRIVER_STATUSES:
                raise HTTPException(
                    400,
                    f"driver_status must be one of {sorted(ALLOWED_DRIVER_STATUSES)}",
                )
            clauses.append({"driver_status": driver_status})
        if endorsement:
            if endorsement not in ALLOWED_CDL_ENDORSEMENTS:
                raise HTTPException(
                    400,
                    f"endorsement must be one of {sorted(ALLOWED_CDL_ENDORSEMENTS)}",
                )
            clauses.append({"cdl_endorsements": endorsement})
        if expiring_cdl_30d:
            clauses.append({
                "cdl_expiration_date": {"$gte": today_iso, "$lte": cutoff_30d}
            })
        if expiring_medical_30d:
            clauses.append({
                "medical_card_expiration_date": {"$gte": today_iso, "$lte": cutoff_30d}
            })
        if q:
            clauses.append({"$or": [
                {"name": safe_regex(q)},
                {"employee_id": safe_regex(q)},
                {"cdl_license_number": safe_regex(q)},
            ]})

        # Projection trims the document to just what the dashboard
        # needs — keeps the response small and the surface read-only.
        projection = {
            "_id": 0,
            "id": 1, "name": 1, "employee_id": 1,
            "trade": 1, "supervisor": 1, "lifecycle_status": 1,
            "cdl_holder": 1, "approved_company_driver": 1,
            "driver_status": 1, "cdl_license_number": 1, "cdl_state": 1,
            "cdl_expiration_date": 1, "medical_card_expiration_date": 1,
            "cdl_endorsements": 1, "cdl_restrictions": 1,
        }

        final = {"$and": clauses}
        cur = db.employees.find(final, projection).sort("name", 1).limit(limit)
        items: List[Dict[str, Any]] = []
        async for d in cur:
            items.append(d)

        # Tiny summary cards — computed over the SAME base scope (NOT
        # over the filtered slice). The cards exist to give the
        # operational picture independent of whatever the user is
        # currently filtering on; if you filtered them, the counts
        # would just mirror the table length and add no value.
        async def _count(extra: Dict[str, Any]) -> int:
            return await db.employees.count_documents({"$and": [base, extra]})

        summary = {
            "cdl_expiring_30d": await _count({
                "cdl_expiration_date": {"$gte": today_iso, "$lte": cutoff_30d}
            }),
            "medical_card_expiring_30d": await _count({
                "medical_card_expiration_date": {"$gte": today_iso, "$lte": cutoff_30d}
            }),
            "restricted": await _count({"driver_status": "restricted"}),
            "suspended": await _count({"driver_status": "suspended"}),
            # MASCI-operational anchor: Tanker-capable means the
            # employee carries an N endorsement OR an X (combined)
            # endorsement on their CDL. Either one legally permits
            # tanker operation.
            "tanker_capable": await _count({
                "cdl_endorsements": {"$in": ["N", "X"]}
            }),
        }

        return {
            "items": items,
            "count": len(items),
            "summary": summary,
            "as_of": today_iso,
        }

    # ── iter312 · Driver Qualification CSV export ──────────────────
    # Bounded operational-visibility export. Reuses the EXACT same
    # filters as `/driver-qualification/dashboard` so the CSV
    # represents the same slice the user just saw on screen — no
    # second filter implementation, no new query path, no analytics
    # framework. HR/Dispatch can hand the CSV to FDOT, insurance
    # carriers, or attorneys without screen-scraping. Same auth gate
    # (`require_hr_or_admin`), same audit trail surface.
    @router.get("/api/hr/driver-qualification/dashboard.csv")
    async def driver_qualification_dashboard_csv(
        actor: Dict[str, Any] = Depends(require_hr_or_admin),
        cdl_holder: Optional[bool] = Query(default=None),
        approved: Optional[bool] = Query(default=None),
        driver_status: Optional[str] = Query(default=None),
        endorsement: Optional[str] = Query(default=None),
        expiring_cdl_30d: Optional[bool] = Query(default=None),
        expiring_medical_30d: Optional[bool] = Query(default=None),
        q: Optional[str] = Query(default=None, max_length=80),
        limit: int = Query(default=2000, ge=1, le=5000),
    ):
        import csv as _csv
        import io as _io
        from fastapi.responses import Response
        from datetime import date as _date

        # Reuse the dashboard handler verbatim. Same filters · same
        # auth · same projection · zero query drift.
        data = await driver_qualification_dashboard(
            actor=actor,
            cdl_holder=cdl_holder, approved=approved,
            driver_status=driver_status, endorsement=endorsement,
            expiring_cdl_30d=expiring_cdl_30d,
            expiring_medical_30d=expiring_medical_30d,
            q=q, limit=limit,
        )

        buf = _io.StringIO()
        w = _csv.writer(buf)
        # Header row matches the dashboard table columns one-for-one
        # (operational discipline: what HR sees on screen is what the
        # CSV ships — no extra fields, no hidden fields).
        # Track 14.0-HR-IDENTITY · explicit identity columns so legal
        # name, middle name, last name, and preferred name all survive
        # the export.
        w.writerow([
            "Display Name", "Legal First Name", "Legal Middle Name",
            "Legal Last Name", "Preferred Name",
            "Employee ID", "Trade", "Supervisor", "Lifecycle Status",
            "Approved Company Driver", "CDL Holder", "Driver Status",
            "CDL License #", "CDL State", "CDL Expiration",
            "Medical Card Expiration", "Endorsements", "Restrictions",
        ])

        def _yn(v: Any) -> str:
            if v is True:
                return "Yes"
            if v is False:
                return "No"
            return ""

        def _list(v: Any) -> str:
            if isinstance(v, list):
                return "; ".join(str(x) for x in v if x)
            return v or ""

        from masci.identity import format_employee_identity

        for r in data["items"]:
            w.writerow([
                format_employee_identity(r) or r.get("name") or "",
                r.get("legal_first_name") or "",
                r.get("legal_middle_name") or "",
                r.get("legal_last_name") or "",
                r.get("preferred_name") or "",
                r.get("employee_id") or "",
                r.get("trade") or "",
                r.get("supervisor") or "",
                r.get("lifecycle_status") or "",
                _yn(r.get("approved_company_driver")),
                _yn(r.get("cdl_holder")),
                r.get("driver_status") or "",
                r.get("cdl_license_number") or "",
                r.get("cdl_state") or "",
                r.get("cdl_expiration_date") or "",
                r.get("medical_card_expiration_date") or "",
                _list(r.get("cdl_endorsements")),
                _list(r.get("cdl_restrictions")),
            ])

        # Summary tail — same rollup numbers HR sees in the
        # summary-card row at the top of the dashboard. Keeps the
        # CSV self-contained for archival/audit purposes.
        s = data.get("summary") or {}
        w.writerow([])
        w.writerow(["SUMMARY (operational rollup)"])
        w.writerow(["Total drivers in scope", data.get("count", 0)])
        w.writerow(["CDL expiring within 30 days", s.get("cdl_expiring_30d", 0)])
        w.writerow(["Medical card expiring within 30 days", s.get("medical_card_expiring_30d", 0)])
        w.writerow(["Restricted", s.get("restricted", 0)])
        w.writerow(["Suspended", s.get("suspended", 0)])
        w.writerow(["Tanker-capable (N or X endorsement)", s.get("tanker_capable", 0)])
        w.writerow([])
        w.writerow(["AS OF", data.get("as_of", "")])
        w.writerow(["GENERATED FOR", actor.get("email") or actor.get("name") or "hr-user"])

        filename = f"MASCI_driver_qualification_{data.get('as_of', _date.today().isoformat())}.csv"
        return Response(
            content=buf.getvalue().encode("utf-8"),
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                # Cache-control: never let a browser/proxy keep a
                # qualification snapshot beyond the request — it's
                # personnel data.
                "Cache-Control": "no-store",
            },
        )

    # ─────────────────────────────────────────────────────────────────
    # CDL / DRIVER QUALIFICATION ROSTER IMPORTER · iter352
    # ─────────────────────────────────────────────────────────────────
    # Self-service replacement for the one-off iter351 loader script.
    # Allows HR + Admin to upload an XLSX or CSV roster, preview the
    # 7-tier match results, then apply the writes after explicit
    # confirmation. Every apply produces a durable audit record in
    # `driver_qualification_imports` AND individual field-level
    # admin_audit_log entries (one per touched field) so the existing
    # /admin/audit UI surfaces the changes alongside other HR edits.
    #
    # Endpoints:
    #   POST /api/hr/driver-qualification/import/preview   — multipart
    #   POST /api/hr/driver-qualification/import/apply     — JSON
    #   GET  /api/hr/driver-qualification/import/audit     — list
    #   GET  /api/hr/driver-qualification/import/audit/{id}— detail
    #
    # RBAC: HR or Admin tokens ONLY (require_hr_or_admin). PM / Safety /
    # Dispatch / Shop / FL / anonymous all return 403.
    from lib import cdl_importer  # noqa: PLC0415
    import uuid as _uuid  # noqa: PLC0415

    @router.post("/api/hr/driver-qualification/import/preview")
    async def cdl_import_preview(
        file: UploadFile = File(...),
        actor: Dict[str, Any] = Depends(require_hr_or_admin),
    ):
        """Parse + match the uploaded roster. NO database writes."""
        raw = await file.read()
        if not raw:
            raise HTTPException(400, "Empty file")
        if len(raw) > 5 * 1024 * 1024:
            raise HTTPException(400, "File too large (5 MB max)")
        fname = (file.filename or "").lower()
        try:
            if fname.endswith(".xlsx"):
                rows, source_columns = cdl_importer.parse_xlsx(raw)
            elif fname.endswith(".csv"):
                rows, source_columns = cdl_importer.parse_csv(raw)
            else:
                raise HTTPException(400, "Only .xlsx and .csv files are supported")
        except ValueError as e:
            raise HTTPException(400, str(e))
        except Exception as e:  # noqa: BLE001
            logger.exception("[cdl-import] parse failed: %s", e)
            raise HTTPException(400, "Could not read uploaded file")

        if not rows:
            return {
                "ok": True, "preview_token": None,
                "file_name": file.filename, "source_columns": source_columns,
                "row_count": 0, "preview": [], "warnings": ["File has no data rows."],
            }

        # Load roster once, build indexes.
        all_emps: List[Dict[str, Any]] = []
        async for e in db.employees.find({"deleted_at": None}, {"_id": 0}):
            all_emps.append(e)
        idx = cdl_importer.build_indexes(all_emps)

        preview: List[Dict[str, Any]] = []
        method_counts: Dict[str, int] = {}
        matched_n = 0
        ambiguous_n = 0
        unmatched_n = 0
        no_change_n = 0
        for r in rows:
            emp, method, conf = cdl_importer.match_row(r, idx)
            method_counts[method] = method_counts.get(method, 0) + 1
            entry: Dict[str, Any] = {
                "source_name": r.get("raw_name"),
                "source_employee_id": r.get("employee_id"),
                "source_email": r.get("email"),
                "match_method": method,
                "match_confidence": conf,
                "warnings": [],
            }
            if emp:
                matched_n += 1
                payload, diff = cdl_importer.build_payload(r, emp, source_columns)
                entry["employee_id"] = emp.get("id")
                entry["employee_name"] = emp.get("name")
                entry["employee_trade"] = emp.get("trade")
                entry["fields_to_update"] = payload
                entry["diff"] = diff
                if "ambiguous" in method:
                    ambiguous_n += 1
                    entry["warnings"].append("Multiple roster matches share this name — verify before applying.")
                if conf == "low" and "ambiguous" not in method:
                    entry["warnings"].append("Low-confidence match — verify before applying.")
                if not payload:
                    no_change_n += 1
                    entry["warnings"].append("All source fields already match the roster (no change).")
            else:
                unmatched_n += 1
                entry["employee_id"] = None
                entry["employee_name"] = None
                entry["fields_to_update"] = {}
                entry["diff"] = {}
                entry["warnings"].append("No matching employee found.")
            preview.append(entry)

        token = str(_uuid.uuid4())
        await db.driver_qualification_import_previews.insert_one({
            "id": token,
            "uploaded_by": actor.get("email") or actor.get("user_id"),
            "uploaded_by_role": actor.get("_actor") or actor.get("role"),
            "file_name": file.filename,
            "source_columns": source_columns,
            "preview": preview,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        return {
            "ok": True,
            "preview_token": token,
            "file_name": file.filename,
            "source_columns": source_columns,
            "row_count": len(rows),
            "summary": {
                "matched": matched_n,
                "unmatched": unmatched_n,
                "ambiguous": ambiguous_n,
                "no_change": no_change_n,
                "method_counts": method_counts,
            },
            "preview": preview,
        }

    @router.post("/api/hr/driver-qualification/import/apply")
    async def cdl_import_apply(
        body: CdlImportApplyPayload = Body(...),
        actor: Dict[str, Any] = Depends(require_hr_or_admin),
    ):
        """Apply the previously-previewed import. Writes:
          1. employees.* driver fields
          2. employees.status_history (one entry per touched employee)
          3. admin_audit_log (one entry per touched field)
          4. driver_qualification_imports (one audit record)
        """
        prev = await db.driver_qualification_import_previews.find_one(
            {"id": body.preview_token}, {"_id": 0}
        )
        if not prev:
            raise HTTPException(404, "Preview not found or expired")
        # Soft per-actor check — anyone with HR/Admin role can apply
        # any of their own previews; cross-actor apply is permitted
        # since both roles are trusted operational owners.

        skip = set(body.skip_rows)
        source_columns = prev.get("source_columns") or []
        now = datetime.now(timezone.utc).isoformat()
        actor_email = actor.get("email") or actor.get("user_id") or "unknown"
        actor_role = actor.get("_actor") or actor.get("role") or "hr"

        updated_n = 0
        created_n = 0
        skipped_n = 0
        no_change_n = 0
        errors: List[Dict[str, Any]] = []
        per_row_results: List[Dict[str, Any]] = []

        for i, entry in enumerate(prev.get("preview") or []):
            if i in skip:
                skipped_n += 1
                per_row_results.append({"row": i, "action": "skipped", "name": entry.get("source_name")})
                continue
            emp_id = entry.get("employee_id")
            payload = entry.get("fields_to_update") or {}

            # Handle create-unmatched opt-in
            if not emp_id:
                if not body.create_unmatched:
                    skipped_n += 1
                    per_row_results.append({"row": i, "action": "skipped_unmatched", "name": entry.get("source_name")})
                    continue
                new_id = str(_uuid.uuid4())
                new_emp = {
                    "id": new_id,
                    "name": entry.get("source_name"),
                    "is_active": True,
                    "lifecycle_status": "Active",
                    "created_at": now,
                    "created_by": actor_email,
                    "created_via": "driver_qualification_import",
                    "deleted_at": None,
                }
                # Apply payload to the new doc
                for k, v in payload.items():
                    new_emp[k] = v
                try:
                    await db.employees.insert_one(new_emp)
                    new_emp.pop("_id", None)
                    created_n += 1
                    per_row_results.append({
                        "row": i, "action": "created",
                        "employee_id": new_id, "name": entry.get("source_name"),
                        "fields": list(payload.keys()),
                    })
                except Exception as e:  # noqa: BLE001
                    errors.append({"row": i, "name": entry.get("source_name"), "error": str(e)})
                continue

            # Matched row — apply PATCH equivalent
            if not payload:
                no_change_n += 1
                per_row_results.append({"row": i, "action": "no_change", "employee_id": emp_id, "name": entry.get("employee_name")})
                continue
            try:
                # Fetch current snapshot for accurate before-values
                current = await db.employees.find_one({"id": emp_id}, {"_id": 0})
                if not current:
                    errors.append({"row": i, "employee_id": emp_id, "error": "employee not found (deleted between preview and apply)"})
                    continue
                # Build status_history entry — same calm-tone format
                # already used by other employee mutations.
                fields_changed = list(payload.keys())
                history_entry = {
                    "ts": now,
                    "actor": actor_email,
                    "actor_role": actor_role,
                    "kind": "driver_qualification_import",
                    "source_file": prev.get("file_name"),
                    "fields": fields_changed,
                    "diff": entry.get("diff") or {},
                }
                update_doc = {"$set": payload, "$push": {"status_history": history_entry}}
                await db.employees.update_one({"id": emp_id}, update_doc)
                updated_n += 1
                per_row_results.append({
                    "row": i, "action": "updated", "employee_id": emp_id,
                    "name": entry.get("employee_name"), "fields": fields_changed,
                })
                # Field-level admin_audit_log entries — one per field so
                # filtering by field type works in /admin/audit.
                for fname_, change in (entry.get("diff") or {}).items():
                    try:
                        await db.admin_audit_log.insert_one({
                            "id": str(_uuid.uuid4()),
                            "ts": now,
                            "actor": actor_email,
                            "actor_role": actor_role,
                            "action": "driver_qualification_field_update",
                            "kind": "employee.driver_qualification",
                            "target_kind": "employee",
                            "target_id": emp_id,
                            "target_name": entry.get("employee_name"),
                            "field": fname_,
                            "before": change.get("before"),
                            "after": change.get("after"),
                            "source": "import",
                            "source_file": prev.get("file_name"),
                        })
                    except Exception:  # pragma: no cover
                        pass  # best-effort audit; don't block the write
            except Exception as e:  # noqa: BLE001
                errors.append({"row": i, "employee_id": emp_id, "error": str(e)})

        audit_id = str(_uuid.uuid4())
        audit_doc = {
            "id": audit_id,
            "ts": now,
            "uploaded_by": actor_email,
            "uploaded_by_role": actor_role,
            "file_name": prev.get("file_name"),
            "source_columns": source_columns,
            "row_count": len(prev.get("preview") or []),
            "matched_count": sum(1 for e in (prev.get("preview") or []) if e.get("employee_id")),
            "unmatched_count": sum(1 for e in (prev.get("preview") or []) if not e.get("employee_id")),
            "updated_count": updated_n,
            "created_count": created_n,
            "skipped_count": skipped_n,
            "no_change_count": no_change_n,
            "errors_count": len(errors),
            "errors": errors,
            "per_row_results": per_row_results,
        }
        await db.driver_qualification_imports.insert_one(audit_doc)

        # Best-effort cleanup of the now-consumed preview.
        try:
            await db.driver_qualification_import_previews.delete_one({"id": body.preview_token})
        except Exception:  # pragma: no cover
            pass

        return {
            "ok": True,
            "audit_id": audit_id,
            "summary": {
                "updated": updated_n,
                "created": created_n,
                "skipped": skipped_n,
                "no_change": no_change_n,
                "errors": len(errors),
            },
            "errors": errors,
        }

    @router.get("/api/hr/driver-qualification/import/audit")
    async def cdl_import_audit_list(
        actor: Dict[str, Any] = Depends(require_hr_or_admin),
        limit: int = Query(default=50, ge=1, le=200),
    ):
        items: List[Dict[str, Any]] = []
        async for d in db.driver_qualification_imports.find({}, {"_id": 0, "per_row_results": 0}).sort("ts", -1).limit(limit):
            items.append(d)
        return {"ok": True, "items": items, "count": len(items)}

    @router.get("/api/hr/driver-qualification/import/audit/{audit_id}")
    async def cdl_import_audit_detail(
        audit_id: str,
        actor: Dict[str, Any] = Depends(require_hr_or_admin),
    ):
        d = await db.driver_qualification_imports.find_one({"id": audit_id}, {"_id": 0})
        if not d:
            raise HTTPException(404, "Audit record not found")
        return d

    # ── Lifecycle index bootstrap helper ─────────────────────────────
    return router


async def ensure_employee_lifecycle_indexes(db) -> None:
    try:
        await db.employees.create_index("lifecycle_status")
        await db.employees.create_index("supervisor")
        await db.employees.create_index("department")
        # iter316 · rehire-eligibility filter index.
        await db.employees.create_index("rehire_eligibility")
        # iter352 · CDL import audit + preview indexes.
        await db.driver_qualification_imports.create_index("ts")
        await db.driver_qualification_imports.create_index("uploaded_by")
        await db.driver_qualification_import_previews.create_index("id", unique=True)
        await db.driver_qualification_import_previews.create_index(
            "created_at", expireAfterSeconds=3600,  # 1h TTL
        )
    except Exception as e:  # pragma: no cover
        logger.warning("employee-lifecycle index bootstrap failed: %s", e)


__all__ = [
    "build_employee_lifecycle_router",
    "ensure_employee_lifecycle_indexes",
    "ALLOWED_LIFECYCLE_STATUSES",
    "ALLOWED_SEPARATION_TYPES",
    "ALLOWED_REHIRE_ELIGIBILITY",
    "ALLOWED_DRIVER_STATUSES",
    "ALLOWED_CDL_ENDORSEMENTS",
    "ALLOWED_CDL_RESTRICTIONS",
]
