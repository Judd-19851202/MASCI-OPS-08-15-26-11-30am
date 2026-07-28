"""TRACK 24.17 · Operations Control Center (OCC).

Single canonical entrypoint for platform maintenance operations.
The OCC lets a super-admin see platform health, run safe cleanup,
migrate storage, verify integrations, and inspect an immutable
audit trail from one screen — **without shell access**.

The subsystem is intentionally split into small modules so future
tracks can add operations without touching the shared machinery:

* ``registry.py``   – ``Operation`` dataclass + registry + risk enum
* ``audit.py``      – append-only Mongo audit log
* ``storage.py``    – disk audit + safe cleanup + project_docs → R2
* ``health.py``     – system / Mongo / disk / route heartbeat
* ``r2.py``         – Cloudflare R2 head-bucket + ref probes
* ``backups.py``    – backup posture read
* ``daily_reports.py`` – DR delivery + evidence forensics
* ``ai.py``         – AI provider posture + fallback rate
* ``email.py``      – provider posture + safety-mode + last 24 h
* ``security.py``   – env posture + dev-endpoint check + CORS
* ``deploy.py``     – (25.01 Phase C) deploy readiness + recovery playbook
* ``integrations.py`` – (25.01 Phase C) live probe of every provider
* ``queues.py``     – (25.01 Phase C) scheduler_runs history
"""
from __future__ import annotations

from .registry import (  # noqa: F401
    Operation,
    OperationCategory,
    OperationStatus,
    RiskLevel,
    build_operations_control_plane_registry,
    build_registry,
    operations_control_plane_registry_summary,
)

__all__ = [
    "Operation",
    "OperationCategory",
    "OperationStatus",
    "RiskLevel",
    "build_operations_control_plane_registry",
    "build_registry",
    "operations_control_plane_registry_summary",
]
