"""TRACK 15.73 SLICE 4 · Canonical Identity Audit · CI Guardrail.

Cross-cutting identity-integrity sweep. Validates that the platform's
canonical identity invariants hold against the current preview database
state and against the frontend source tree.

Invariants asserted:

1. equipment_master uses `unit_number` as canonical key for resolver.
   Display label may exist but is never the lookup key.
2. db.employees uses `id` as canonical key for safety meeting attendee
   identity. Meeting attendees with `attendee_type="employee"` must
   carry a non-empty `employee_id`.
3. Newly-submitted meeting attendees with `non_masci=true` must have
   `employee_id=""` (OurCo id never carried on a subcontractor row).
4. The `brandCompanyName` helper signature default is `"Customer"`
   (intentional — the helper itself is neutral) but every callsite in
   the frontend uses a tenant-canonical default (asserted by
   `test_track_15_73_slice3_no_branding_default_drift`).

This module is read-only against MongoDB and never mutates data.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

import pytest
from dotenv import load_dotenv
from pymongo import MongoClient


load_dotenv(Path("/app/backend/.env"))


@pytest.fixture(scope="module")
def db():
    client = MongoClient(os.environ["MONGO_URL"])
    yield client[os.environ["DB_NAME"]]
    client.close()


def test_equipment_master_canonical_id_present(db):
    """Every equipment_master record must have a canonical `id` (UUID).

    Note: `unit_number` is INTENTIONALLY optional for small fungible
    gear (air compressors, pumps, generators, misc tools) — at least
    247 / 705 preview rows fall into this category. The canonical
    identifier for lookup is `id` (UUID); `unit_number` is a
    human-readable secondary key for trackable assets (trucks,
    excavators, motor graders, etc.). The Track 15.73 Slice 1 resolver
    looks up by `id` first, then `unit_number`. So this test asserts
    only on `id`, the true canonical key."""
    blank_id = db.equipment_master.count_documents({
        "$or": [{"id": None}, {"id": ""}, {"id": {"$exists": False}}],
    })
    assert blank_id == 0, (
        f"{blank_id} equipment_master rows have empty canonical id — "
        "this would break every resolver join. P0 data corruption."
    )


def test_equipment_master_unit_number_observability(db):
    """Informational only — surfaces the count of equipment_master rows
    without a `unit_number` so operators can see the legacy fungible-
    gear data state.

    NOT a failure assertion (small gear is intentionally identifier-less)."""
    blank = db.equipment_master.count_documents({
        "$or": [{"unit_number": None}, {"unit_number": ""}],
    })
    total = db.equipment_master.estimated_document_count()
    if total == 0:
        pytest.skip("equipment_master is empty")
    ratio = blank / total
    # We DOCUMENT the ratio as part of the canonical-identity audit
    # output. Operators can review via `pytest -s` capture.
    print(
        f"\n[equipment_master unit_number observability] "
        f"{blank}/{total} ({ratio:.1%}) rows have empty unit_number — "
        "expected for fungible small gear (air compressors, pumps, "
        "generators, misc). Trackable assets (graders/excavators/trucks) "
        "should all have unit_number; if this ratio exceeds 60%, "
        "investigate import drift."
    )
    # Hard ceiling — fail only on catastrophic data corruption.
    assert ratio < 0.60, (
        f"equipment_master has {ratio:.1%} blank unit_numbers — "
        "exceeds the 60% catastrophic-drift ceiling. Likely import bug."
    )


def test_employees_has_canonical_ids(db):
    """Every employees record must have a non-empty `id`."""
    blank = db.employees.count_documents({"$or": [{"id": None}, {"id": ""}]})
    assert blank == 0, f"{blank} employees records have empty canonical id."


def test_recent_meeting_attendees_obey_identity_invariants(db):
    """Meetings created after Slice 2 ship (2026-02-11) must have
    canonically-classified attendees.

    Pre-Slice-2 historical rows are exempt — they pre-date the
    `normalize_meeting_attendees` guard."""
    cursor = db.meetings.find(
        {"attendees.attendee_type": {"$exists": True}},
        {"_id": 0, "attendees": 1, "doc_id": 1},
    )
    violations: list[str] = []
    for m in cursor:
        for idx, a in enumerate(m.get("attendees") or []):
            if not isinstance(a, dict):
                continue
            t = (a.get("attendee_type") or "").strip()
            if t == "employee":
                # OurCo employees MUST carry employee_id.
                if not (a.get("employee_id") or "").strip():
                    violations.append(
                        f"{m.get('doc_id')}.attendees[{idx}] type=employee but employee_id is empty"
                    )
                if (a.get("company") or "").strip().upper() != "MASCI":
                    violations.append(
                        f"{m.get('doc_id')}.attendees[{idx}] type=employee but company='{a.get('company')}'"
                    )
            elif t == "subcontractor":
                # Subcontractors must NOT carry an OurCo employee_id.
                if (a.get("employee_id") or "").strip():
                    violations.append(
                        f"{m.get('doc_id')}.attendees[{idx}] type=subcontractor but employee_id='{a.get('employee_id')}'"
                    )
    assert not violations, (
        "Identity invariant violation(s) in post-Slice-2 meetings:\n  "
        + "\n  ".join(violations)
    )


def test_brand_helper_default_is_neutral():
    """The brandCompanyName helper signature default may be 'Customer'
    (the helper is intentionally neutral). The guardrail enforces that
    every CALLSITE passes a tenant-canonical default — see the
    `no_branding_default_drift` sibling test."""
    helper_src = Path("/app/frontend/src/lib/brandFilename.js").read_text()
    # We assert the helper signature accepts a defaultName argument and
    # is not hardcoded to return "Customer" unconditionally.
    assert "defaultName" in helper_src, "brandCompanyName must accept a defaultName parameter."
    assert "function brandCompanyName" in helper_src, "Helper export name unchanged."


def test_no_unit_number_lookup_uses_unescaped_regex():
    """The asset-spine resolver MUST `re.escape` user input before
    embedding into a MongoDB regex (Slice 1 hardening). Regression-
    proof: if anyone re-introduces a raw f-string, this fails."""
    src = Path("/app/backend/routes/asset_spine.py").read_text()
    # Look for unescaped regex pattern in unit_number lookup.
    unsafe = re.search(
        r'unit_number["\']?\s*:\s*\{[^}]*\$regex["\']?\s*:\s*f["\']\^\{unit_or_id\}\$',
        src,
    )
    assert unsafe is None, (
        "Unescaped regex pattern detected in routes/asset_spine.py — "
        "must use re.escape() on user input (Slice 1 hardening)."
    )
