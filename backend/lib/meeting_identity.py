"""TRACK 15.73 SLICE 2 · Employee Identity Restoration · Backend Guard.

Authoritative normalization of Safety Meeting attendee identity at submit
time. Even if the frontend sends inconsistent values, the backend derives
canonical identity flags from the trusted `employees` collection so that:

  * A roster-selected MASCI employee is ALWAYS stored as
    `attendee_type="employee" · source="employee_master" · company="MASCI"
    · is_masci_employee=true`.
  * A subcontractor is ALWAYS stored as
    `attendee_type="subcontractor" · is_subcontractor=true`, with
    `employee_id` cleared.
  * A manual entry (typed name with no roster match) is flagged
    `attendee_type="manual" · review_status="needs_review"` so the safety
    admin queue can resolve identity later.

Also performs in-meeting deduplication by `employee_id` to prevent the
same MASCI employee from being added twice via bulk-add + single-pick.

This module is read-side safe and idempotent. It does NOT mutate the
`employees` collection. It does NOT create new identities.

Track 15.73 Slice 2.
"""
from __future__ import annotations

from typing import Any, Iterable

# Canonical attendee_type vocabulary.
ATTENDEE_TYPE_EMPLOYEE = "employee"
ATTENDEE_TYPE_SUBCONTRACTOR = "subcontractor"
ATTENDEE_TYPE_MANUAL = "manual"

SOURCE_EMPLOYEE_MASTER = "employee_master"
SOURCE_SUBCONTRACTOR_DIRECTORY = "subcontractor_directory"
SOURCE_MANUAL = "manual"

REVIEW_STATUS_NEEDS_REVIEW = "needs_review"


async def normalize_meeting_attendees(
    db: Any,
    attendees: list[dict],
    *,
    tenant_company_name: str = "MASCI",
) -> list[dict]:
    """Return a new list of attendee dicts with canonical identity flags.

    Pure function — does not write to MongoDB, does not mutate inputs.

    Args:
        db: motor AsyncIO database handle (async client).
        attendees: list of attendee dicts (as accepted by `MeetingAttendee`).
        tenant_company_name: the tenant's canonical company name; used as
            the locked company for roster-resolved employees. Defaults to
            "MASCI" for the single-tenant deploy; will be resolved from
            tenant branding once multi-tenant Safety Meetings ship.

    Returns:
        A new list of attendee dicts with these guaranteed fields:
          * attendee_type      ∈ {employee, subcontractor, manual}
          * source             ∈ {employee_master, subcontractor_directory, manual}
          * is_masci_employee  bool
          * is_subcontractor   bool
          * is_manual          bool
          * review_status      "" | "needs_review"
        Plus normalized canonical:
          * company             (locked to tenant name for resolved employees)
          * employee_id         (cleared for non_masci / unmatched manual)
          * non_masci           (boolean, consistent with attendee_type)
    """
    if not attendees:
        return []

    # Single round-trip employee_master lookup
    candidate_ids = {
        (a.get("employee_id") or "").strip()
        for a in attendees
        if isinstance(a, dict) and (a.get("employee_id") or "").strip()
    }
    candidate_ids.discard("")

    valid_ids: dict[str, dict] = {}
    if candidate_ids:
        cursor = db.employees.find(
            {"id": {"$in": list(candidate_ids)}},
            {"_id": 0, "id": 1, "name": 1, "trade": 1, "role": 1, "position": 1, "is_active": 1},
        )
        async for emp in cursor:
            valid_ids[emp.get("id")] = emp

    seen_employee_ids: set[str] = set()
    seen_subcontractor_signatures: set[tuple[str, str]] = set()
    out: list[dict] = []

    for a in attendees:
        if not isinstance(a, dict):
            continue
        # Start from a shallow copy so callers' originals are untouched.
        row = dict(a)
        eid = (row.get("employee_id") or "").strip()
        non_masci = bool(row.get("non_masci"))
        emp = valid_ids.get(eid) if eid else None

        if emp and not non_masci:
            # ─── Roster-resolved MASCI employee ───────────────────────
            # In-meeting dedup: same employee picked twice (bulk + single)
            # collapses to one row.
            if eid in seen_employee_ids:
                continue
            seen_employee_ids.add(eid)
            row["employee_id"] = eid
            row["non_masci"] = False
            row["company"] = tenant_company_name
            row["attendee_type"] = ATTENDEE_TYPE_EMPLOYEE
            row["source"] = SOURCE_EMPLOYEE_MASTER
            row["is_masci_employee"] = True
            row["is_subcontractor"] = False
            row["is_manual"] = False
            row["review_status"] = ""
            # Backfill trade from canonical record when blank.
            if not (row.get("trade") or "").strip():
                row["trade"] = (
                    emp.get("trade") or emp.get("role") or emp.get("position") or ""
                )
        elif non_masci:
            # ─── Subcontractor / non-OurCo ───────────────────────────
            row["employee_id"] = ""  # NEVER carry an OurCo id on a subcontractor row.
            row["non_masci"] = True
            # company stays as user-entered (subcontractor's company).
            row["attendee_type"] = ATTENDEE_TYPE_SUBCONTRACTOR
            row["source"] = SOURCE_SUBCONTRACTOR_DIRECTORY
            row["is_masci_employee"] = False
            row["is_subcontractor"] = True
            row["is_manual"] = False
            row["review_status"] = ""
            # Dedup by (name, company) tuple within this meeting.
            sig = (
                (row.get("name") or "").strip().lower(),
                (row.get("company") or "").strip().lower(),
            )
            if sig in seen_subcontractor_signatures:
                continue
            seen_subcontractor_signatures.add(sig)
        else:
            # ─── Manual entry (typed name, no valid roster match) ────
            # This includes: (a) typed name with stale/invalid employee_id
            # (b) typed name with no employee_id at all.
            row["employee_id"] = ""   # invalid id is dropped — never silently retained.
            row["non_masci"] = False
            if not (row.get("company") or "").strip():
                # No company entered → flag for review rather than silently
                # mark MASCI. Caller will see this in the admin queue.
                row["company"] = ""
            row["attendee_type"] = ATTENDEE_TYPE_MANUAL
            row["source"] = SOURCE_MANUAL
            row["is_masci_employee"] = False
            row["is_subcontractor"] = False
            row["is_manual"] = True
            row["review_status"] = REVIEW_STATUS_NEEDS_REVIEW

        out.append(row)

    return out


def normalize_counts(attendees: Iterable[dict]) -> dict[str, int]:
    """Summary counts used by reporting + the admin meeting view header."""
    counts = {
        "total": 0,
        ATTENDEE_TYPE_EMPLOYEE: 0,
        ATTENDEE_TYPE_SUBCONTRACTOR: 0,
        ATTENDEE_TYPE_MANUAL: 0,
        "needs_review": 0,
    }
    for a in attendees:
        if not isinstance(a, dict):
            continue
        counts["total"] += 1
        t = (a.get("attendee_type") or "").strip()
        if t in (ATTENDEE_TYPE_EMPLOYEE, ATTENDEE_TYPE_SUBCONTRACTOR, ATTENDEE_TYPE_MANUAL):
            counts[t] += 1
        if (a.get("review_status") or "").strip() == REVIEW_STATUS_NEEDS_REVIEW:
            counts["needs_review"] += 1
    return counts
