"""ForgedOps · Incident Intelligence Engine · Phase A

Domain package for the new Incident Intelligence Engine.

Zero-Drift Doctrine:
    * Legacy ``db.incidents`` collection is NEVER touched.
    * Legacy ``/api/incidents`` routes are NEVER touched.
    * Every new artifact lives in a NEW collection and a NEW route
      namespace (`/api/incident-cases`).
    * Legacy incidents surface as read-only ``LegacyIncidentCase`` view
      models via the ``legacy_adapter`` module.

Ownership boundaries are absolute:
    Field  owns immediate facts (time / place / people / observed).
    Safety owns investigation (recordability / root cause / CAPA).
    Management owns oversight (metrics / approvals / escalation).

Constitutional pillars (Powerful · Simple · Beautiful · Trusted ·
Proven · Operational) are asserted by the lock test suite in
``backend/tests/test_track_19_16_incident_engine_phase_a.py``.
"""

from .constants import (
    INCIDENT_TYPES,
    CASE_STATES,
    CASE_DEFAULT_STATE,
    CASE_TRANSITIONS,
    EVIDENCE_TYPES,
    ACTION_CLASSES,
    EVENT_TYPES,
    ROLE_MATRIX,
    CROSS_LINK_KINDS,
    IMMUTABLE_AFTER_STATES,
)

__all__ = [
    "INCIDENT_TYPES",
    "CASE_STATES",
    "CASE_DEFAULT_STATE",
    "CASE_TRANSITIONS",
    "EVIDENCE_TYPES",
    "ACTION_CLASSES",
    "EVENT_TYPES",
    "ROLE_MATRIX",
    "CROSS_LINK_KINDS",
    "IMMUTABLE_AFTER_STATES",
]
