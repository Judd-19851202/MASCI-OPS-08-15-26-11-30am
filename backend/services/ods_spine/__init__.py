"""ODS-001 · Operational Data Spine service package.

Public surface — all writes to spine collections go through this module.

  services.ods_spine.model    — canonical fact type constants + validators
  services.ods_spine.store    — idempotent write + supersede primitives
  services.ods_spine.ingest   — source-specific ingestors (DR-V2 first)
  services.ods_spine.kpi      — snapshot builder
  services.ods_spine.query    — read helpers for PM/Admin
  services.ods_spine.flags    — env-driven ODS feature flags

Zero direct writes to `operational_*` collections from anywhere else.
"""
from .flags import ods_enabled, dr_v2_spine_emission_enabled
from .model import (
    FACT_TYPES, SOURCE_TYPES, FACT_ENVELOPE_FIELDS,
    validate_fact_envelope,
)
from .store import (
    write_facts, supersede_facts, record_ingestion_run,
    COLL_FACTS, COLL_RUNS, COLL_SNAPSHOTS, COLL_PROJECT_CFG, COLL_LINKS,
)
from .ingest import ingest_dr_v2_draft, ingest_dr_v2_approval
from .kpi import compute_kpi_snapshot, get_snapshot
from .query import list_facts, project_summary

__all__ = [
    "ods_enabled", "dr_v2_spine_emission_enabled",
    "FACT_TYPES", "SOURCE_TYPES", "FACT_ENVELOPE_FIELDS",
    "validate_fact_envelope",
    "write_facts", "supersede_facts", "record_ingestion_run",
    "COLL_FACTS", "COLL_RUNS", "COLL_SNAPSHOTS", "COLL_PROJECT_CFG", "COLL_LINKS",
    "ingest_dr_v2_draft", "ingest_dr_v2_approval",
    "compute_kpi_snapshot", "get_snapshot",
    "list_facts", "project_summary",
]
