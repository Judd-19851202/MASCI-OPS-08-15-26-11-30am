"""TRACK 23.10-C · Trench Safety services package.

Ships:
  * `project_linker.py`      — 6-rung resolution ladder that maps any
                               trench record → (project_number,
                               link_status, confidence).
  * `facts_emitter.py`       — 7 canonical ODS emitters, all idempotent
                               via `supersede_facts` on the natural key
                               `(source_type, source_id, source_item_id,
                               fact_type)`.
  * `derived_views.py`       — read-time derivations (deployment ·
                               asset utilisation · release · activity)
                               computed from the physical facts;
                               documented per user directive 2B.

Consumes but never duplicates:
  * TRACK 23.10-B Professional Qualifications Engine (Competent Person
    snapshots — always via `qualification_registry.get_qualification_snapshot`
    and `list_active_qualifications`).
  * ODS spine (`services/ods_spine/store.py` + `model.py`).
  * Track 23.5 employee identity normaliser.
"""
from __future__ import annotations

from .project_linker import (
    ProjectLinkage,
    LINK_STATUSES,
    LINK_CONFIDENCE,
    resolve_project,
    resolve_project_batch,
)
from .facts_emitter import (
    emit_excavation_day_fact,
    emit_trench_inspection_fact,
    emit_trench_hold_fact,
    emit_trench_repair_fact,
    emit_trench_verification_fact,
    emit_competent_person_assignment_fact,
    recompute_project_excavation_summary,
    SOURCE_TYPE_TRENCH,
    TRENCH_FACT_TYPES,
)

__all__ = [
    "ProjectLinkage",
    "LINK_STATUSES",
    "LINK_CONFIDENCE",
    "resolve_project",
    "resolve_project_batch",
    "emit_excavation_day_fact",
    "emit_trench_inspection_fact",
    "emit_trench_hold_fact",
    "emit_trench_repair_fact",
    "emit_trench_verification_fact",
    "emit_competent_person_assignment_fact",
    "recompute_project_excavation_summary",
    "SOURCE_TYPE_TRENCH",
    "TRENCH_FACT_TYPES",
]
