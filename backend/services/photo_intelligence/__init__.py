"""DR-ROI-001D · Photo Intelligence service.

Turns Daily Report V2 photos into structured operational evidence via
the AI Gateway's `photo_vision` task. Never mutates source photos.
Never fabricates. Every observation is confidence-scored and marked
`requires_supervisor_confirmation=True` unless directly evidenced.

Track 22.9B (2026-02) extended the module with a V1 pipeline
(pipeline.py) that wires the analyzer into the V1 Daily Report submit
workflow asynchronously — BackgroundTasks first-pass + a reconciler
loop for retries. Zero duplicate storage: intel rows live in the same
`dr_v2_photo_intelligence` collection, keyed by (report_id, photo_id).
"""
from .flags import photo_vision_enabled
from .store import (
    COLL_PHOTO_INTEL, ensure_indexes, get_intel, upsert_intel,
    accept_link, dismiss_link, resolve_question,
)
from .analyzer import analyze_photo, PHOTO_ENVELOPE_SCHEMA, evidence_hash_for_photo
from .emitter import emit_photo_evidence_fact
from .pipeline import (
    COLL_INTEL_JOBS,
    enqueue_report as enqueue_v1_report,
    process_report as process_v1_report,
    reconcile_once as reconcile_v1_once,
    reconciler_loop as v1_reconciler_loop,
    list_report_intelligence as list_v1_report_intelligence,
    ensure_indexes as ensure_v1_pipeline_indexes,
)

__all__ = [
    "photo_vision_enabled",
    "COLL_PHOTO_INTEL", "ensure_indexes",
    "get_intel", "upsert_intel", "accept_link", "dismiss_link", "resolve_question",
    "analyze_photo", "PHOTO_ENVELOPE_SCHEMA", "evidence_hash_for_photo",
    "emit_photo_evidence_fact",
    "COLL_INTEL_JOBS",
    "enqueue_v1_report", "process_v1_report",
    "reconcile_v1_once", "v1_reconciler_loop",
    "list_v1_report_intelligence", "ensure_v1_pipeline_indexes",
]
