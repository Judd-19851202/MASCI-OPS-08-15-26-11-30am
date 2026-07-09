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

Track 27.02
-----------
Added `mongo_clause_for_status()` — a canonical Detailed-Status
resolver that includes legacy fallback for `Active` / `Inactive` (the
two statuses that legacy rows resolve to via `is_active`). This
guarantees Detailed-Status = Active returns the SAME rows the bucket=active
filter would, not the smaller strict-match subset.

Added `normalize_facet_value()` — a canonical facet normalizer. All
three facet fields (crew / supervisor / trade) are trimmed and
whitespace-collapsed at both facet-generation time AND query-match
time, so the value in the dropdown always matches the value used to
filter the table.
"""
from __future__ import annotations

import re
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
    "active":     "Active",
    "pending":    "Pending / Onboarding",
    "off_roll":   "Off-roll / Inactive",
    "terminated": "Terminated / Separated",
    "retired":    "Retired",
    "any":        "All employees",
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


# ── Track 27.02 · Canonical Detailed-Status resolver ─────────────────
# Bug reported in prod (2026-02-08): Detailed Status = Active returned
# 27 rows while bucket=active returned 236. Root cause: raw strict
# `lifecycle_status: "Active"` matched only backfilled/newer rows,
# excluding legacy rows that resolve to Active via `is_active`. The
# canonical resolver below closes that gap so *both* Employment-Group
# and Detailed-Status paths return the same rowset for any status
# that legacy rows can display as.
#
# Semantics: "detailed status = X" means "employees whose DISPLAY
# status is X." For statuses that legacy rows might display as
# (Active/Inactive), we OR in the legacy fallback. For statuses that
# only exist on modern rows (Terminated / Resigned / Retired /
# Pending Hire / Seasonal / Leave of Absence / Suspended), a strict
# match is correct because no legacy row can ever display as those.
def mongo_clause_for_status(status: str) -> Dict[str, Any]:
    """Return a Mongo $or clause matching every row whose display
    status resolves to `status`. Semantics mirror `bucket_of()`.
    """
    branches: List[Dict[str, Any]] = [{"lifecycle_status": status}]
    if status == "Active":
        branches += [
            {"lifecycle_status": None, "is_active": {"$ne": False}},
            {"lifecycle_status": {"$exists": False}, "is_active": {"$ne": False}},
        ]
    elif status == "Inactive":
        branches += [
            {"lifecycle_status": None, "is_active": False},
            {"lifecycle_status": {"$exists": False}, "is_active": False},
        ]
    return {"$or": branches}


# ── Track 27.02 · Canonical facet normalizer ─────────────────────────
# Bug reported in prod (2026-02-08): Supervisor facet showed
# "LENNY WITKOWSKI · 3" but selecting it returned 0 rows. Root cause:
# raw stored values had trailing whitespace / different casings; the
# facet grouped one way, the strict-match query matched a different
# way. Canonical normalization at BOTH ends closes that.
#
# Rule: display value = whitespace-collapsed, trimmed, ORIGINAL case
# (HR wants "David Puma", not "david puma"). Match semantics =
# case-insensitive + whitespace-tolerant regex against the raw stored
# value.
_SENTINEL_UNASSIGNED = "(unassigned)"


def normalize_facet_value(value: Any) -> Optional[str]:
    """Return the canonical display form of a facet field value.

    None / '' / whitespace-only → None (blank; caller decides whether
    to bucket into '(unassigned)').
    Otherwise: strip + collapse internal whitespace, preserve case.
    """
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)
    v = re.sub(r"\s+", " ", value).strip()
    return v or None


def is_unassigned_sentinel(value: Optional[str]) -> bool:
    """True if the value is our '(unassigned)' filter sentinel."""
    return value == _SENTINEL_UNASSIGNED


def mongo_clause_for_facet(field: str, value: str) -> Dict[str, Any]:
    """Return a Mongo clause that matches employees whose `field`
    value normalizes to `value`. Case-insensitive, whitespace-tolerant.

    For the special sentinel '(unassigned)', matches null / missing /
    whitespace-only rows.
    """
    if is_unassigned_sentinel(value):
        # Match null, missing, empty string, or whitespace-only.
        return {"$or": [
            {field: {"$in": [None, ""]}},
            {field: {"$exists": False}},
            {field: {"$regex": r"^\s*$"}},
        ]}
    normalized = normalize_facet_value(value) or ""
    # Escape regex specials in the value; then allow any internal-
    # whitespace variant (single space vs multiple spaces vs tabs) by
    # replacing our normalized single spaces with `\s+` and anchoring
    # with `\s*` on both ends so trailing/leading whitespace matches.
    escaped = re.escape(normalized).replace(r"\ ", r"\s+")
    return {field: {"$regex": f"^\\s*{escaped}\\s*$", "$options": "i"}}
