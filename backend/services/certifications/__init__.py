"""TRACK 23.10-B · Professional Qualifications Engine.

Foundation for the platform-wide professional qualifications system.
Competent Person is the pilot qualification type; the engine ships with
15+ types on day one and is extensible via config.

Single source of truth: `db.safety_training_records`.
No parallel registry. No manual list. Registry is a QUERY.
"""
from __future__ import annotations

from .qualification_types import (
    QUALIFICATION_TYPES,
    QUALIFICATION_ENGINE_TYPES,
    QUALIFICATION_STATUS,
    is_engine_type,
    validate_type_metadata,
)
from .qualification_registry import (
    list_active_qualifications,
    resolve_active_for_employee,
    get_qualification_snapshot,
    is_active,
    qualification_summary,
)
from .qualification_facts import (
    emit_qualification_certification_fact,
    emit_qualification_expiration_facts_daily,
)

__all__ = [
    "QUALIFICATION_TYPES",
    "QUALIFICATION_ENGINE_TYPES",
    "QUALIFICATION_STATUS",
    "is_engine_type",
    "validate_type_metadata",
    "list_active_qualifications",
    "resolve_active_for_employee",
    "get_qualification_snapshot",
    "is_active",
    "qualification_summary",
    "emit_qualification_certification_fact",
    "emit_qualification_expiration_facts_daily",
]
