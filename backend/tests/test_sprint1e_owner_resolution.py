"""Sprint 1E · Command Center owner-resolution patch regression tests.

Authorized scope: prove that the Command Center JOBS-DR-MISSING owner
resolver now reads BOTH the new (`primary_pm_*`) and the legacy
(`project_manager`, `pm_email`) field names from `jobs_master`. The
production defect was that every job in `jobs_master` carries the
legacy field names (e.g., `project_manager = "David Jewett"` for job
24-06) but the resolver only read `primary_pm_*`, so every flagged job
fell through to the literal `"Unassigned PM"`.

The fix is surgical: extend the projection AND the fallback chain in
`routes/command_center.py:_build_jobs_card` so legacy rows resolve
correctly. No source-of-truth schema migration. No regression to other
resolvers. No new collection. No new route.
"""
from __future__ import annotations

import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from routes.command_center import (  # noqa: E402
    DEFAULT_THRESHOLDS,
    _build_jobs_card,
)
from tests.test_command_center_phase_a import _FakeDb, _FakeCollection  # noqa: E402


def _hours_ago(h: float) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=h)).isoformat()


def _run(coro):
    return asyncio.run(coro)


def _find_dr_item(card: Dict[str, Any], project_number: str) -> Dict[str, Any] | None:
    for it in (card.get("items") or []):
        if project_number in (it.get("what_wrong") or ""):
            return it
    return None


# ───────────────────────────────────────────────────────────────────────
# 1 · Legacy schema: jobs_master has `project_manager` (production state)
# ───────────────────────────────────────────────────────────────────────
def test_legacy_project_manager_field_resolves_to_real_pm_name():
    """Reproduces the production defect for job 24-06.

    Before the patch: owner = "Unassigned PM" even though
    project_manager = "David Jewett" is set on the jobs_master row.

    After the patch: owner = "David Jewett".
    """
    db = _FakeDb()
    # Legacy jobs_master row — only carries `project_manager` and `pm_email`,
    # exactly the shape currently in the production collection.
    db.jobs_master = _FakeCollection([
        {"id": "j24-06", "project_number": "24-06", "status": "Active",
         "project_manager": "David Jewett",
         "pm_email": "davidjewett@mascigc.com"},
    ])
    # No daily_reports for 24-06 → triggers JOBS-DR-MISSING.
    db.daily_reports = _FakeCollection([])

    card = _run(_build_jobs_card(db, DEFAULT_THRESHOLDS["rules"]))

    item = _find_dr_item(card, "24-06")
    assert item is not None, "Expected a JOBS-DR-MISSING item for project 24-06"
    assert item["owner"] == "David Jewett", (
        f"Expected owner 'David Jewett' (from legacy `project_manager` field), "
        f"got {item['owner']!r}. The resolver is still ignoring the legacy schema."
    )


# ───────────────────────────────────────────────────────────────────────
# 2 · New schema: `primary_pm_name` still takes precedence
# ───────────────────────────────────────────────────────────────────────
def test_new_primary_pm_name_still_takes_precedence_over_legacy():
    """Forward-compat: when BOTH `primary_pm_name` and `project_manager`
    are present, the new field wins. Ensures the patch does not flip
    the precedence on any job that has been migrated to the new schema.
    """
    db = _FakeDb()
    db.jobs_master = _FakeCollection([
        {"id": "j-mixed", "project_number": "MIXED-1", "status": "Active",
         "primary_pm_name": "Alice (new)",
         "project_manager": "Bob (legacy)"},
    ])
    db.daily_reports = _FakeCollection([])

    card = _run(_build_jobs_card(db, DEFAULT_THRESHOLDS["rules"]))
    item = _find_dr_item(card, "MIXED-1")
    assert item is not None
    assert item["owner"] == "Alice (new)", (
        f"Expected new-schema name 'Alice (new)' to win, got {item['owner']!r}"
    )


# ───────────────────────────────────────────────────────────────────────
# 3 · Email fallback chain · new email preferred over legacy email
# ───────────────────────────────────────────────────────────────────────
def test_email_fallback_chain_new_over_legacy():
    """When neither `primary_pm_name` nor `project_manager` is set but
    BOTH email fields are present, the new `primary_pm_email` wins.
    """
    db = _FakeDb()
    db.jobs_master = _FakeCollection([
        {"id": "j-email", "project_number": "EMAIL-1", "status": "Active",
         "primary_pm_email": "new@mascigc.com",
         "pm_email": "legacy@mascigc.com"},
    ])
    db.daily_reports = _FakeCollection([])

    card = _run(_build_jobs_card(db, DEFAULT_THRESHOLDS["rules"]))
    item = _find_dr_item(card, "EMAIL-1")
    assert item is not None
    assert item["owner"] == "new@mascigc.com"


# ───────────────────────────────────────────────────────────────────────
# 4 · Legacy email fallback when no names exist
# ───────────────────────────────────────────────────────────────────────
def test_legacy_pm_email_resolves_when_no_names():
    """The legacy `pm_email` is the next-to-last resort before
    `Unassigned PM`. Validates the complete fallback ladder:
    primary_pm_name → project_manager → primary_pm_email → pm_email.
    """
    db = _FakeDb()
    db.jobs_master = _FakeCollection([
        {"id": "j-lemail", "project_number": "LEMAIL-1", "status": "Active",
         "pm_email": "legacy-only@mascigc.com"},
    ])
    db.daily_reports = _FakeCollection([])

    card = _run(_build_jobs_card(db, DEFAULT_THRESHOLDS["rules"]))
    item = _find_dr_item(card, "LEMAIL-1")
    assert item is not None
    assert item["owner"] == "legacy-only@mascigc.com"


# ───────────────────────────────────────────────────────────────────────
# 5 · Genuine "Unassigned PM" path still fires
# ───────────────────────────────────────────────────────────────────────
def test_genuinely_unassigned_job_still_falls_through_to_label():
    """Jobs 20-07, 22-08, 24-08 on production have empty
    `project_manager` and empty `pm_email`. The resolver MUST still
    surface "Unassigned PM" for them so the operator can act on the
    real data-hygiene issue. The patch must not mask genuine gaps.
    """
    db = _FakeDb()
    db.jobs_master = _FakeCollection([
        {"id": "j-empty", "project_number": "EMPTY-1", "status": "Active",
         "project_manager": "", "pm_email": ""},
        {"id": "j-missing", "project_number": "MISSING-1", "status": "Active"},
    ])
    db.daily_reports = _FakeCollection([])

    card = _run(_build_jobs_card(db, DEFAULT_THRESHOLDS["rules"]))
    item_empty = _find_dr_item(card, "EMPTY-1")
    item_missing = _find_dr_item(card, "MISSING-1")
    assert item_empty is not None and item_empty["owner"] == "Unassigned PM"
    assert item_missing is not None and item_missing["owner"] == "Unassigned PM"


# ───────────────────────────────────────────────────────────────────────
# 6 · No regression on the GREEN path (job WITH a recent DR)
# ───────────────────────────────────────────────────────────────────────
def test_recent_dr_keeps_card_green_legacy_schema():
    """When a legacy-schema job DOES have a recent DR, it must NOT be
    flagged. Confirms the patch did not accidentally change the
    JOBS-DR-MISSING rule's selection logic.
    """
    db = _FakeDb()
    db.jobs_master = _FakeCollection([
        {"id": "j-green", "project_number": "GREEN-1", "status": "Active",
         "project_manager": "David Jewett", "pm_email": "davidjewett@mascigc.com"},
    ])
    db.daily_reports = _FakeCollection([
        {"id": "dr-1", "project_number": "GREEN-1", "created_at": _hours_ago(2)},
    ])

    card = _run(_build_jobs_card(db, DEFAULT_THRESHOLDS["rules"]))
    item = _find_dr_item(card, "GREEN-1")
    assert item is None, (
        f"Job GREEN-1 has a recent DR; should not appear in JOBS-DR-MISSING items. "
        f"Got: {item!r}"
    )
