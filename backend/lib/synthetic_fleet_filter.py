"""TRACK 28.05 · Synthetic Fleet / Dispatch exclusion filter.

Same doctrine as ``synthetic_dr_filter`` (28.02B), ``synthetic_flr_filter``
(28.03), ``synthetic_hr_filter`` (28.04). Certification / smoke-test
fixtures using ``TEST_28_05_``, ``SYNTHETIC_``, ``ITER[0-9]`` prefixes
on the identity fields of Fleet / Dispatch collections must never
surface on operator-facing screens.

Applies to reads on:
  * ``equipment_master``        — canonical fleet / equipment identity
  * ``dispatch_assignments``    — canonical dispatch assignment identity
  * ``fleet_defect_items``      — Shop / Fleet defect queue
  * ``equipment_inspections``   — Pre-Op / DVIR history

Sentinel fields matched (any → excluded):
  * ``synthetic_record: true``          — explicit opt-in
  * ``hidden_from_operations: true``    — explicit opt-in
  * ``unit_number`` / ``equipment_unit`` / ``truck_id`` / ``equipment_id``
    starts with TEST_ / TEST- / SYNTHETIC_ / ITER[0-9] / CERT_TEST_
  * ``driver_name`` / ``operator_name`` / ``vin_serial_number`` / ``doc_id``
    starts with same sentinel family
  * ``project_number`` matches sentinel family
"""
from __future__ import annotations

from typing import Any, Dict, List

from lib.governed_fixture_evidence import is_governed_fixture
from lib.governed_record_classification import (
    apply_governed_visibility_exclusion,
    governed_visibility_exclusion_clauses,
)


_TEST_SENTINEL_RE = (
    r"^("
    r"TEST[_\-]"
    r"|SMOKE[_\-]"
    r"|SYNTHETIC[_\-]"
    r"|CERT_TEST"
    r"|PARITY_"
    r"|ITER[0-9]"
    r")"
)

# Fields checked per collection. Each collection has its own natural
# identity surface, so we intentionally do NOT try to write a "one
# regex fits all" clause.
EQUIPMENT_MASTER_FIELDS = ("unit_number", "vin_serial_number", "display_label", "id")
INSPECTION_FIELDS = ("equipment_unit", "operator_name", "project_number", "doc_id")
DISPATCH_ASSIGNMENT_FIELDS = (
    "truck_id", "driver_id", "driver_name", "project_number",
    "material", "equipment_id", "equipment_label", "trailer_id",
)
FLEET_DEFECT_FIELDS = ("unit_number", "source_operator", "project_number")


def _field_regex_not_test(field: str) -> Dict[str, Any]:
    return {field: {"$not": {"$regex": _TEST_SENTINEL_RE, "$options": "i"}}}


def _exclusion_clauses(fields: tuple[str, ...]) -> List[Dict[str, Any]]:
    return governed_visibility_exclusion_clauses()


def apply_synthetic_equipment_exclusion(query: Dict[str, Any]) -> Dict[str, Any]:
    """Mix synthetic exclusion into a mongo query targeting ``equipment_master``."""
    return apply_governed_visibility_exclusion(query)


def apply_synthetic_inspection_exclusion(query: Dict[str, Any]) -> Dict[str, Any]:
    """Mix synthetic exclusion into a mongo query targeting
    ``equipment_inspections`` (Pre-Op / DVIR)."""
    return apply_governed_visibility_exclusion(query)


def apply_synthetic_dispatch_exclusion(query: Dict[str, Any]) -> Dict[str, Any]:
    """Mix synthetic exclusion into a mongo query targeting ``dispatch_assignments``."""
    return apply_governed_visibility_exclusion(query)


def apply_synthetic_fleet_defect_exclusion(query: Dict[str, Any]) -> Dict[str, Any]:
    """Mix synthetic exclusion into a mongo query targeting ``fleet_defect_items``."""
    return apply_governed_visibility_exclusion(query)


def is_synthetic_fleet_doc(doc: Dict[str, Any], fields: tuple[str, ...] = EQUIPMENT_MASTER_FIELDS) -> bool:
    """Python-side classifier used by cleanup + tests."""
    family = {
        INSPECTION_FIELDS: "equipment_inspections",
        DISPATCH_ASSIGNMENT_FIELDS: "dispatch_assignments",
    }.get(fields)
    if family:
        return is_governed_fixture(doc, family)
    return False


__all__ = [
    "apply_synthetic_equipment_exclusion",
    "apply_synthetic_inspection_exclusion",
    "apply_synthetic_dispatch_exclusion",
    "apply_synthetic_fleet_defect_exclusion",
    "is_synthetic_fleet_doc",
    "EQUIPMENT_MASTER_FIELDS",
    "INSPECTION_FIELDS",
    "DISPATCH_ASSIGNMENT_FIELDS",
    "FLEET_DEFECT_FIELDS",
]
