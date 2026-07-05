"""DR-ROI-001D · Photo Intelligence service.

Turns Daily Report V2 photos into structured operational evidence via
the AI Gateway's `photo_vision` task. Never mutates source photos.
Never fabricates. Every observation is confidence-scored and marked
`requires_supervisor_confirmation=True` unless directly evidenced.
"""
from .flags import photo_vision_enabled
from .store import (
    COLL_PHOTO_INTEL, ensure_indexes, get_intel, upsert_intel,
    accept_link, dismiss_link, resolve_question,
)
from .analyzer import analyze_photo, PHOTO_ENVELOPE_SCHEMA, evidence_hash_for_photo
from .emitter import emit_photo_evidence_fact

__all__ = [
    "photo_vision_enabled",
    "COLL_PHOTO_INTEL", "ensure_indexes",
    "get_intel", "upsert_intel", "accept_link", "dismiss_link", "resolve_question",
    "analyze_photo", "PHOTO_ENVELOPE_SCHEMA", "evidence_hash_for_photo",
    "emit_photo_evidence_fact",
]
