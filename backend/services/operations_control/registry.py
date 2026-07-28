"""TRACK 24.17 · Operation registry + shared vocabulary."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional


class OperationCategory(str, Enum):
    HEALTH = "health"
    STORAGE = "storage"
    R2 = "r2"
    BACKUPS = "backups"
    GOVERNANCE = "governance"
    DAILY_REPORTS = "daily_reports"
    AI = "ai"
    DOCUMENTS = "documents"
    PHOTOS = "photos"
    EMAIL = "email"
    DATA_INTEGRITY = "data_integrity"
    QUEUES = "queues"
    SECURITY = "security"


class RiskLevel(str, Enum):
    INFO = "info"
    SAFE_CLEANUP = "safe_cleanup"
    DATA_MIGRATION = "data_migration"
    DESTRUCTIVE = "destructive"
    EXTERNAL_PROVIDER = "external_provider"
    SECURITY_SENSITIVE = "security_sensitive"


class OperationStatus(str, Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNAVAILABLE = "unavailable"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    MANUAL_REQUIRED = "manual_required"
    DRY_RUN_READY = "dry_run_ready"
    APPLY_READY = "apply_ready"
    COMING_SOON = "coming_soon"


HandlerT = Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]


@dataclass
class Operation:
    """One safely-callable maintenance operation."""

    id: str
    title: str
    description: str
    category: OperationCategory
    risk: RiskLevel
    # Handlers. ``status_fn`` is a lightweight read-only probe for the
    # overview cards. ``dry_run_fn`` returns a preview envelope with a
    # server-issued ``dry_run_id``. ``apply_fn`` performs the actual
    # mutation and requires the ``dry_run_id`` if the operation is
    # destructive/data_migration.
    status_fn: Optional[HandlerT] = None
    dry_run_fn: Optional[HandlerT] = None
    apply_fn: Optional[HandlerT] = None
    # Human-readable declarations shown in the UI as truthful contracts.
    reads: List[str] = field(default_factory=list)
    writes: List[str] = field(default_factory=list)
    never_touches: List[str] = field(default_factory=list)
    # High-risk operations require this exact phrase in the payload.
    confirmation_phrase: Optional[str] = None
    # If true, ``apply_fn`` must be preceded by a valid recent dry-run.
    requires_dry_run: bool = False
    # Absent apply_fn means the OCC UI will render this as manual-required.
    manual_reason: Optional[str] = None

    def to_public_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category.value,
            "risk": self.risk.value,
            "reads": list(self.reads),
            "writes": list(self.writes),
            "never_touches": list(self.never_touches),
            "requires_dry_run": self.requires_dry_run,
            "requires_confirmation": bool(self.confirmation_phrase),
            "has_dry_run": self.dry_run_fn is not None,
            "has_apply": self.apply_fn is not None,
            "has_status": self.status_fn is not None,
            "manual_reason": self.manual_reason,
        }


def build_registry(db) -> Dict[str, Operation]:
    """Return the master registry, wiring each Operation to the DB.

    Split by module so future tracks can add operations without editing
    a single monolith.
    """
    from . import (  # noqa: PLC0415
        ai as ai_mod,
        backups as backups_mod,
        daily_reports as dr_mod,
        deploy as deploy_mod,
        email as email_mod,
        governance as governance_mod,
        health as health_mod,
        integrations as integrations_mod,
        queues as queues_mod,
        r2 as r2_mod,
        security as security_mod,
        storage as storage_mod,
    )

    ops: Dict[str, Operation] = {}

    def add(o: Operation) -> None:
        if o.id in ops:
            raise ValueError(f"duplicate operation id: {o.id}")
        ops[o.id] = o

    # Track 25.01 Phase C: ``deploy_mod``, ``integrations_mod`` and
    # ``queues_mod`` fold the scattered maintenance surfaces
    # (deploy-readiness · deploy-recovery · integration-truth ·
    # operations-dashboard · scheduler-runs) into OCC as first-class
    # read-only operations.
    for module in (
        health_mod, deploy_mod, integrations_mod, queues_mod,
        storage_mod, governance_mod, r2_mod, backups_mod, dr_mod,
        ai_mod, email_mod, security_mod,
    ):
        for op in module.operations(db):
            add(op)
    return ops
