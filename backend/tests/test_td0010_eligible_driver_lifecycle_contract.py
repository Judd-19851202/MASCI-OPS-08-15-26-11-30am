"""TD-0010 — eligible CDL driver lifecycle contract.

Live production (read-only): /api/admin/transportation/eligible-hr-cdl-drivers
returned 43 "eligible" drivers that INCLUDED 2 Resigned + 1 Inactive employees
because the filter omitted lifecycle status. An eligible driver must be actively
employable: exclude every non-active canonical status (off_roll / terminated /
retired / pending). None / missing lifecycle_status resolves to active (legacy
fallback) and is retained.
"""
from backend.lib.employee_status import BUCKET_STATUSES


def _ineligible_driver_statuses():
    return (
        BUCKET_STATUSES["off_roll"] + BUCKET_STATUSES["terminated"]
        + BUCKET_STATUSES["retired"] + BUCKET_STATUSES["pending"]
    )


def test_terminal_and_offroll_statuses_are_ineligible():
    ineligible = set(_ineligible_driver_statuses())
    for s in ("Resigned", "Terminated", "Inactive", "Suspended", "Retired", "Pending Hire"):
        assert s in ineligible, f"{s} must be excluded from eligible drivers"


def test_active_and_legacy_statuses_remain_eligible():
    ineligible = set(_ineligible_driver_statuses())
    # Active bucket + legacy None must NOT be excluded.
    for s in ("Active", "Seasonal", "Leave of Absence"):
        assert s not in ineligible
    # A $nin clause never excludes null/missing -> legacy active retained.
    nin = {"$nin": _ineligible_driver_statuses()}
    assert None not in nin["$nin"]


def test_contract_tracks_canonical_vocabulary():
    # Guard against drift: the ineligible set is exactly the non-active buckets.
    active = set(BUCKET_STATUSES["active"])
    ineligible = set(_ineligible_driver_statuses())
    assert active.isdisjoint(ineligible)
    all_known = {s for ss in BUCKET_STATUSES.values() for s in ss}
    assert ineligible == all_known - active
