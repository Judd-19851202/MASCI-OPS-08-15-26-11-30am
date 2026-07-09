"""TRACK 27.00 · Canonical employee employment-status buckets.

One code path — the only one — that decides what "actively employed"
means, what "off-roll" means, what "retired" means, etc. Every consumer
(HR list query, HR export query, KPI card, filter dropdown, saved
views, reporting, Daily Report autofill, PM staffing) must call
`bucket_of()` or `mongo_clause_for_bucket()` instead of hardcoding
status sets.

Buckets
-------
  active      = Active, Seasonal, Leave of Absence
  pending     = Pending Hire        (onboarding — NOT counted as Active)
  off_roll    = Inactive, Suspended
  terminated  = Terminated, Resigned  (Layoff is a separation_type sub-flag)
  retired     = Retired               (Track 27.00 amendment — first-class)

The special `any` bucket returns everything not soft-deleted. It is not
a status; it is the "no employment filter" sentinel.

Legacy rows
-----------
Post-Phase-A backfill every row carries a `lifecycle_status`, but the
mongo clause STILL supports the legacy shape (`lifecycle_status`
missing + `is_active` truthy) so this module stays correct even if a
future migration ever writes a row without setting the field.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


# ── Canonical bucket → status-string mapping ─────────────────────────
BUCKET_STATUSES: Dict[str, List[str]] = {
    "active":     ["Active", "Seasonal", "Leave of Absence"],
    "pending":    ["Pending Hire"],
    "off_roll":   ["Inactive", "Suspended"],
    "terminated": ["Terminated", "Resigned"],
    "retired":    ["Retired"],
}

# All canonical lifecycle_status strings the system knows about.
ALL_LIFECYCLE_STATUSES: List[str] = [
    s for ss in BUCKET_STATUSES.values() for s in ss
]

# Public API for UI/consumers.
BUCKET_ORDER: List[str] = ["active", "pending", "off_roll", "terminated", "retired"]
BUCKET_LABELS: Dict[str, str] = {
    "active":     "Actively Employed",
    "pending":    "Pending / Onboarding",
    "off_roll":   "Off-roll / Inactive",
    "terminated": "Terminated / Separated",
    "retired":    "Retired",
    "any":        "Any (all employees)",
}


def bucket_of(employee: Dict[str, Any]) -> str:
    """Return the canonical bucket for one employee document.

    Legacy rows (missing `lifecycle_status`) fall back to `is_active`:
      - is_active is not False → active
      - is_active is False → off_roll (Inactive)

    Any status string not in the known map is treated as `off_roll`
    (fail-closed — never call an unknown status Active).
    """
    ls = employee.get("lifecycle_status")
    if ls is None:
        return "off_roll" if employee.get("is_active") is False else "active"
    for bucket, statuses in BUCKET_STATUSES.items():
        if ls in statuses:
            return bucket
    return "off_roll"


def mongo_clause_for_bucket(bucket: str) -> Optional[Dict[str, Any]]:
    """Return a Mongo $or clause that selects every row in the bucket.

    Returns None for `any` (no clause needed). Raises ValueError on
    unknown bucket to fail loudly at the API boundary — callers that
    already validate their input never hit this path.
    """
    if bucket == "any":
        return None
    if bucket not in BUCKET_STATUSES:
        raise ValueError(f"unknown employment bucket: {bucket!r}")
    statuses = BUCKET_STATUSES[bucket]
    branches: List[Dict[str, Any]] = [
        {"lifecycle_status": {"$in": statuses}},
    ]
    # Preserve legacy-shape support: rows without lifecycle_status still
    # resolve to `active` (if is_active truthy) or `off_roll` (if
    # is_active is False), matching bucket_of() above.
    if bucket == "active":
        branches.append({
            "lifecycle_status": {"$in": [None]},
            "is_active": {"$ne": False},
        })
        branches.append({
            "lifecycle_status": {"$exists": False},
            "is_active": {"$ne": False},
        })
    elif bucket == "off_roll":
        branches.append({
            "lifecycle_status": {"$in": [None]},
            "is_active": False,
        })
        branches.append({
            "lifecycle_status": {"$exists": False},
            "is_active": False,
        })
    return {"$or": branches}


def status_belongs_to_bucket(status: Optional[str], bucket: str) -> bool:
    """True if the (possibly-null) status resolves into the bucket."""
    if bucket == "any":
        return True
    if status is None:
        # Consistent with bucket_of() legacy fallback.
        return bucket == "active"
    return status in BUCKET_STATUSES.get(bucket, [])


def is_active_bucket(bucket: str) -> bool:
    """Convenience — Pending, Off-roll, Terminated, Retired are NOT active."""
    return bucket == "active"


def validate_bucket(bucket: Optional[str]) -> str:
    """Normalize a bucket string from the API. Missing → 'any'."""
    if not bucket:
        return "any"
    b = bucket.strip().lower()
    if b == "any":
        return "any"
    if b in BUCKET_STATUSES:
        return b
    raise ValueError(
        f"invalid employment bucket {bucket!r}; expected one of "
        f"{['any', *BUCKET_ORDER]}"
    )
