"""TRACK 15.83B · Canonical operator transfer-visibility helper.

Mirrors the frontend ``transferVisibility.js`` (Track 15.83) so the
backend can be the source of truth for which transfer records are
"operator-visible" (real dispatch work) vs. "audit residue" (deployment
validation, smoke tests, sample seeds, demo data).

Why this exists
---------------
Track 15.83 introduced a frontend filter to scrub production-facing
audit residue ("#71 in Masci Equip list → AUDIT-2") from the Dispatch
landing surface. That filter works today, but regex drift between
frontend / backend is a maintenance risk and any future native client
would have to re-implement the rules.

This module canonicalises the rules. Track 15.83B wires it into
``GET /api/asset-transfers?audience=operator`` so any client that asks
for the operator audience gets the same filter applied server-side,
plus a ``suppressed_count`` for the transparent trust signal.

Doctrine
--------
* Conservative-by-default: when uncertain, the record passes through.
* Multiple signals: project-number, reason text, source-system,
  explicit flags.
* No mutation: this module never deletes / never writes.
* Pure functions only.
"""
from __future__ import annotations

import re
from typing import Any, Iterable, List, Mapping, Tuple

# Project numbers that signal validation residue.
AUDIT_PROJECT_RX = re.compile(
    r"^(AUDIT|TEST|DEMO|VALIDATION|VAL|SMOKE|SAMPLE)[-_]?\d*$",
    re.IGNORECASE,
)

# Reason / decision-reason text that signals validation residue.
AUDIT_REASON_RX = re.compile(
    r"\b(audit|smoke[\s-]?test|deployment validation|"
    r"validation run|self[\s-]?test|test fixture|seed validation)\b",
    re.IGNORECASE,
)

# Source-system / created-by / record-type markers that signal residue.
AUDIT_SOURCE_RX = re.compile(
    r"\b(audit|seed|validator|fixture|smoke|cert)\b",
    re.IGNORECASE,
)


def _matches(rx: re.Pattern, value: Any) -> bool:
    if value is None:
        return False
    return bool(rx.search(str(value)))


def is_audit_project_marker(value: Any) -> bool:
    """True iff `value` looks like an AUDIT / TEST / DEMO / VALIDATION /
    SMOKE / SAMPLE project number. Used by both the operator transfer
    filter AND any other surface that needs to scrub validation residue.
    """
    if value is None:
        return False
    s = str(value).strip()
    return bool(AUDIT_PROJECT_RX.match(s))


def is_operator_visible_transfer(record: Mapping[str, Any]) -> bool:
    """Return True if `record` is a real operational transfer the
    dispatcher should see. Return False if it is obvious audit /
    validation / smoke-test residue.

    Mirrors ``frontend/src/lib/transferVisibility.js``.
    """
    if not isinstance(record, Mapping):
        return False

    # 1 · destination / source project markers — strongest signal.
    if is_audit_project_marker(record.get("to_project_number")):
        return False
    if is_audit_project_marker(record.get("from_project_number")):
        return False

    # 2 · reason text.
    if _matches(AUDIT_REASON_RX, record.get("reason")):
        return False
    if _matches(AUDIT_REASON_RX, record.get("decision_reason")):
        return False

    # 3 · source / created_by / record_type / audit_marker.
    for key in (
        "created_by", "requested_by", "source_system",
        "audit_marker", "record_type", "transfer_type",
    ):
        if _matches(AUDIT_SOURCE_RX, record.get(key)):
            return False

    # 4 · explicit flags some backends already set on validation rows.
    if record.get("is_audit") is True:
        return False
    if record.get("is_validation") is True:
        return False
    if record.get("is_test") is True:
        return False

    return True


def filter_operator_visible_transfers(
    records: Iterable[Mapping[str, Any]],
) -> Tuple[List[Mapping[str, Any]], int]:
    """Split `records` into (visible, suppressed_count).

    Operators see the `visible` list; the `suppressed_count` is exposed
    as a calm "N audit rows hidden" trust signal in the UI.
    """
    visible: List[Mapping[str, Any]] = []
    suppressed = 0
    for r in records:
        if is_operator_visible_transfer(r):
            visible.append(r)
        else:
            suppressed += 1
    return visible, suppressed


__all__ = [
    "is_audit_project_marker",
    "is_operator_visible_transfer",
    "filter_operator_visible_transfers",
    "AUDIT_PROJECT_RX",
    "AUDIT_REASON_RX",
    "AUDIT_SOURCE_RX",
]
