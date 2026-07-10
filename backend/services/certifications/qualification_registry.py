"""TRACK 23.10-B · Qualification registry (read service).

The registry is a QUERY over `db.safety_training_records`, not a
stored list. Consumers (Daily Report V3, Trench Safety, Scheduling,
Safety Portal, PM Portal) call the endpoints in
`routes/qualifications.py` which delegate here.

Rules (Ref: `/app/memory/TRACK_23_10B_HANDOFF.md` §3):
  * Never returns pending / suspended / revoked / expired rows.
  * Joins to `db.employees` via the shared identity normaliser
    (`lib/employee_identity.py`) — never fabricates identity.
  * Read-only. Deterministic. Idempotent.
  * `is_active_for_selection` requires:
        verification_status == "active"
        AND today <= expiration_date (if present)
        AND suspended_at IS NULL
        AND revoked_at IS NULL
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Mapping, Optional

from lib.employee_identity import normalize_employee_identity

from .qualification_types import (
    QUALIFICATION_ENGINE_TYPES,
    is_engine_type,
)


COLL = "safety_training_records"


# ─── Date helpers ────────────────────────────────────────────────────
def _today_iso() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _to_date(v: Any) -> Optional[str]:
    """Coerce to YYYY-MM-DD; return None on failure or empty."""
    if not v:
        return None
    if isinstance(v, datetime):
        return v.date().isoformat()
    s = str(v)
    return s[:10] if len(s) >= 10 else None


def _days_between(from_iso: str, to_iso: str) -> int:
    """Whole days from `from_iso` to `to_iso` (both YYYY-MM-DD)."""
    a = datetime.fromisoformat(from_iso).date()
    b = datetime.fromisoformat(to_iso).date()
    return (b - a).days


# ─── Selectability rule (single source of truth) ─────────────────────
def is_active(row: Mapping[str, Any], today: Optional[str] = None) -> bool:
    """Return True iff the qualification is active-for-selection today.

    This is the single canonical rule — every consumer must derive
    active-selectability from this function or the equivalent server
    filter (§ list_active_qualifications), never from
    `verification_status` alone.
    """
    if not row:
        return False
    if row.get("verification_status") != "active":
        return False
    if row.get("suspended_at"):
        return False
    if row.get("revoked_at"):
        return False
    exp = _to_date(row.get("expiration_date"))
    if exp is None:
        # A qualification with no expiration is considered active as
        # long as verification_status is active. This mirrors the
        # legacy safety_training_records semantic (no expiry = valid).
        return True
    return exp >= (today or _today_iso())


# ─── Employee identity join ──────────────────────────────────────────
async def _load_employee_map(
    db, employee_ids: Iterable[str],
) -> Dict[str, Dict[str, Any]]:
    """Batch-load employees by `id` OR `employee_id`. Returns map keyed
    by both surface identifiers so join tolerates historical drift."""
    ids = [i for i in employee_ids if i]
    if not ids:
        return {}
    cursor = db.employees.find(
        {"$or": [{"id": {"$in": ids}}, {"employee_id": {"$in": ids}}]},
        {"_id": 0},
    )
    m: Dict[str, Dict[str, Any]] = {}
    async for e in cursor:
        norm = normalize_employee_identity(e)
        if e.get("id"):
            m[e["id"]] = norm
        if e.get("employee_id"):
            m[e["employee_id"]] = norm
    return m


def _project_row(
    row: Mapping[str, Any],
    emp: Optional[Mapping[str, Any]],
    today: str,
    warning_days: int,
) -> Dict[str, Any]:
    """Shape a `safety_training_records` row + employee doc into the
    canonical `QualificationRow` returned to consumers."""
    exp = _to_date(row.get("expiration_date"))
    expires_in = _days_between(today, exp) if exp else None
    warning = (
        expires_in is not None and 0 <= expires_in <= warning_days
    )
    qtype = row.get("qualification_type") or row.get("certification_type") or ""
    return {
        "qualification_id": row.get("id"),
        "qualification_type": qtype,
        "qualification_sub_code": (row.get("type_metadata") or {}).get("sub_code") or "",
        "employee_id": row.get("employee_id") or "",
        "employee_master_id": row.get("employee_master_id") or "",
        "employee_name": (emp or {}).get("display_identity")
            or (emp or {}).get("name")
            or row.get("employee_name")
            or "",
        "employee_trade": (emp or {}).get("trade_role_display") or "",
        "employee_crew": (emp or {}).get("crew_display") or "",
        "employee_supervisor": (emp or {}).get("supervisor_display") or "",
        "issuing_organization": row.get("issuing_organization")
            or row.get("issued_by") or "",
        "certificate_number": row.get("certificate_number") or "",
        "issued_at": _to_date(row.get("completed_date")) or "",
        "expires_at": exp or "",
        "expires_in_days": expires_in if expires_in is not None else -1,
        "warning": bool(warning),
        "verification_status": row.get("verification_status") or "active",
        "is_active_for_selection": True,
        "training_standard": row.get("training_standard") or "",
        "jurisdiction": row.get("jurisdiction") or "",
        "type_metadata": row.get("type_metadata") or {},
        "identity_source": "employees" if emp else "record",
    }


# ─── Public API ──────────────────────────────────────────────────────
async def list_active_qualifications(
    db,
    qualification_type: Optional[str] = None,
    warning_days: int = 30,
    employee_ids: Optional[Iterable[str]] = None,
) -> List[Dict[str, Any]]:
    """Return active-for-selection qualifications, joined to employees.

    Filters:
      * verification_status == "active" (server-side)
      * suspended_at IS NULL / revoked_at IS NULL (server-side)
      * expiration_date >= today (or missing = valid)
      * qualification_type filter when provided
      * employee_ids filter when provided
    """
    today = _today_iso()
    q: Dict[str, Any] = {
        "$and": [
            {"$or": [
                {"verification_status": "active"},
                # Legacy rows with no verification_status but a
                # non-expired completed_date behave as active. This
                # bridges the pre-23.10-B corpus without a hard cutover.
                {"verification_status": {"$exists": False}},
            ]},
            {"$or": [
                {"suspended_at": None},
                {"suspended_at": {"$exists": False}},
            ]},
            {"$or": [
                {"revoked_at": None},
                {"revoked_at": {"$exists": False}},
            ]},
            {"$or": [
                {"expiration_date": None},
                {"expiration_date": ""},
                {"expiration_date": {"$exists": False}},
                {"expiration_date": {"$gte": today}},
            ]},
        ],
    }
    if qualification_type:
        if not is_engine_type(qualification_type):
            return []
        q["$and"].append({"$or": [
            {"qualification_type": qualification_type},
            # Bridge: pre-23.10-B rows carried the value in
            # `certification_type` as free-text. If that free-text
            # equals the enum value literally (post-migration), we
            # accept it too. New writes ALWAYS set qualification_type.
            {"certification_type": qualification_type},
        ]})
    if employee_ids:
        q["$and"].append({"employee_id": {"$in": list(employee_ids)}})

    # TRACK 28.07 · exclude synthetic TEST_28_07_ / SYNTHETIC_ / ITER
    # test rows from every operator-facing qualification read path
    # (HR training tab, Safety credential registry, CP picker, public
    # QR verification, executive compliance rollup).
    from lib.synthetic_training_filter import apply_synthetic_qualification_exclusion  # noqa: PLC0415
    q = apply_synthetic_qualification_exclusion(q)

    rows = await db[COLL].find(q, {"_id": 0}).to_list(10_000)

    # Batch-load employees.
    ids = {r.get("employee_id") for r in rows if r.get("employee_id")}
    emp_map = await _load_employee_map(db, ids)

    out: List[Dict[str, Any]] = []
    for r in rows:
        # Defensive: even with server-side filter, apply canonical rule.
        # Fill in default verification_status for legacy rows.
        if not r.get("verification_status"):
            r = {**r, "verification_status": "active"}
        if not is_active(r, today=today):
            continue
        emp = emp_map.get(r.get("employee_id") or "")
        out.append(_project_row(r, emp, today, warning_days))

    # Sort: soonest-to-expire first, then employee_name.
    out.sort(key=lambda r: (
        r["expires_at"] or "9999-12-31",
        r["employee_name"].lower(),
    ))
    return out


async def resolve_active_for_employee(
    db,
    employee_id: str,
    qualification_type: str,
) -> Optional[Dict[str, Any]]:
    """Return the single most-current active qualification for the
    employee + type combo, or None."""
    if not employee_id or not qualification_type:
        return None
    rows = await list_active_qualifications(
        db,
        qualification_type=qualification_type,
        employee_ids=[employee_id],
    )
    if not rows:
        return None
    # `list_active_qualifications` sorts soonest-to-expire; the latest
    # issued (most-current) is best represented by the row with the
    # LATEST expiration date. Re-sort accordingly.
    rows.sort(key=lambda r: r["expires_at"] or "", reverse=True)
    return rows[0]


async def get_qualification_snapshot(
    db,
    qualification_id: str,
) -> Optional[Dict[str, Any]]:
    """Return a frozen shape suitable for historical embedding.

    Consumers embed this snapshot into their own row so later
    certification changes never rewrite historical facts.
    """
    if not qualification_id:
        return None
    row = await db[COLL].find_one({"id": qualification_id}, {"_id": 0})
    if not row:
        return None
    emp = None
    if row.get("employee_id"):
        m = await _load_employee_map(db, [row["employee_id"]])
        emp = m.get(row["employee_id"])
    today = _today_iso()
    exp = _to_date(row.get("expiration_date"))
    return {
        "qualification_id": row.get("id"),
        "qualification_type": row.get("qualification_type")
            or row.get("certification_type") or "",
        "verification_status_at_selection": row.get("verification_status")
            or "active",
        "expires_at_at_selection": exp or "",
        "is_active_at_selection": is_active(row, today=today),
        "employee_id": row.get("employee_id") or "",
        "employee_master_id": row.get("employee_master_id") or "",
        "person_name_snapshot": (emp or {}).get("display_identity")
            or row.get("employee_name") or "",
        "person_trade_snapshot": (emp or {}).get("trade_role_display") or "",
        "person_crew_snapshot": (emp or {}).get("crew_display") or "",
        "person_supervisor_snapshot": (emp or {}).get("supervisor_display") or "",
        "issuing_organization": row.get("issuing_organization")
            or row.get("issued_by") or "",
        "certificate_number": row.get("certificate_number") or "",
        "snapshot_at": datetime.now(timezone.utc).isoformat(),
    }


async def qualification_summary(
    db,
    qualification_type: Optional[str] = None,
    warning_days: int = 30,
) -> Dict[str, Any]:
    """Return per-type counts for Safety Portal / HR dashboards."""
    q: Dict[str, Any] = {}
    if qualification_type:
        if not is_engine_type(qualification_type):
            return {
                "qualification_type": qualification_type,
                "active_count": 0,
                "expiring_within_days": warning_days,
                "expiring_within_count": 0,
                "expired_count": 0,
                "pending_count": 0,
                "suspended_count": 0,
                "revoked_count": 0,
                "upcoming_renewals_by_month": [],
            }
        q["$or"] = [
            {"qualification_type": qualification_type},
            {"certification_type": qualification_type},
        ]
    rows = await db[COLL].find(q, {"_id": 0}).to_list(20_000)
    today = _today_iso()
    warn_cutoff = (
        datetime.fromisoformat(today).date() + timedelta(days=warning_days)
    ).isoformat()

    counters = {
        "active_count": 0, "expiring_within_count": 0,
        "expired_count": 0, "pending_count": 0,
        "suspended_count": 0, "revoked_count": 0,
    }
    upcoming: Dict[str, int] = {}
    for r in rows:
        if not r.get("verification_status"):
            r = {**r, "verification_status": "active"}
        st = r.get("verification_status")
        if st == "suspended":
            counters["suspended_count"] += 1
            continue
        if st == "revoked":
            counters["revoked_count"] += 1
            continue
        if st == "pending":
            counters["pending_count"] += 1
            continue
        exp = _to_date(r.get("expiration_date"))
        # No expiration = active (matches is_active rule).
        if exp is None:
            counters["active_count"] += 1
            continue
        if exp < today:
            counters["expired_count"] += 1
            continue
        counters["active_count"] += 1
        if today <= exp <= warn_cutoff:
            counters["expiring_within_count"] += 1
            month_key = exp[:7]
            upcoming[month_key] = upcoming.get(month_key, 0) + 1

    upcoming_sorted = sorted(
        [{"month": m, "count": c} for m, c in upcoming.items()],
        key=lambda x: x["month"],
    )
    return {
        "qualification_type": qualification_type or "ALL",
        "active_count": counters["active_count"],
        "expiring_within_days": warning_days,
        "expiring_within_count": counters["expiring_within_count"],
        "expired_count": counters["expired_count"],
        "pending_count": counters["pending_count"],
        "suspended_count": counters["suspended_count"],
        "revoked_count": counters["revoked_count"],
        "upcoming_renewals_by_month": upcoming_sorted,
    }


async def list_employee_qualifications(
    db,
    employee_id: str,
    include_history: bool = False,
    qualification_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Return every qualification row for an employee (all statuses).

    Used by the Employee Lifecycle Qualifications tab — HR needs to
    see active + expired + suspended + revoked + pending together.
    Never returned to field/consumer surfaces.
    """
    if not employee_id:
        return []
    q: Dict[str, Any] = {"employee_id": employee_id}
    if qualification_type:
        q["$or"] = [
            {"qualification_type": qualification_type},
            {"certification_type": qualification_type},
        ]
    rows = await db[COLL].find(q, {"_id": 0}).sort("completed_date", -1).to_list(2_000)
    today = _today_iso()
    for r in rows:
        if not r.get("verification_status"):
            r["verification_status"] = "active"
        # Derived active flag for UI convenience.
        r["is_active"] = is_active(r, today=today)
        # Days-to-expiry (negative if past).
        exp = _to_date(r.get("expiration_date"))
        r["expires_in_days"] = _days_between(today, exp) if exp else None
        if not include_history:
            r.pop("verification_status_history", None)
    return rows


__all__ = [
    "COLL",
    "is_active",
    "list_active_qualifications",
    "resolve_active_for_employee",
    "get_qualification_snapshot",
    "qualification_summary",
    "list_employee_qualifications",
]
