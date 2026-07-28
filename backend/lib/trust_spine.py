"""TRACK 15.76 · Platform Trust Spine — lifecycle event emitter.

Every workflow that participates in the Trust Spine emits a lifecycle
of stages. The dashboard reads from ``trust_spine_events`` and proves,
record-by-record, that the platform is doing what it claims.

Universal contract (minimum):

  record_created → validation_complete → routing_resolved →
  recipients_built → notification_queued → provider_accepted →
  audit_written → dashboard_updated → completed

A workflow MAY emit only a subset (e.g. an HR request has no
``provider_accepted`` because it does not send email) — the
dashboard treats absent stages as **AMBER**, never green.

Each emission writes one document to ``trust_spine_events``::

    {
      "ts": ISO-8601 UTC string,
      "workflow": "daily-report" | "meeting" | "incident" | ...,
      "stage":    "record_created" | "routing_resolved" | "audit_written" | ...,
      "correlation_id": uuid4 issued once per record lifecycle,
      "record_id": doc_id (canonical identifier),
      "project_number": "20-07" (when known),
      "module": "routes/daily_reports.py",
      "status": "ok" | "skipped" | "failed",
      "duration_ms": optional int,
      "failure_reason": optional str (≤ 240 chars),
      "remediation": optional str (≤ 240 chars, operator-readable hint),
    }

Design rules:
  - **Never raises** — all writes wrapped in try/except. A failed
    Trust Spine write must never break the actual workflow.
  - **Indexed** — Background ``ensure_indexes()`` covers ``(workflow, ts)``,
    ``(correlation_id)`` and ``(status, ts)`` for fast dashboard aggregation.
  - **No PII** — Only operational identifiers (doc_id, project_number,
    module). No recipient lists, no subjects, no payload bodies.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger("trust_spine")

# Canonical lifecycle stages.
STAGE_RECORD_CREATED = "record_created"
STAGE_VALIDATION_COMPLETE = "validation_complete"
STAGE_ROUTING_RESOLVED = "routing_resolved"
STAGE_RECIPIENTS_BUILT = "recipients_built"
STAGE_NOTIFICATION_QUEUED = "notification_queued"
STAGE_DELIVERY_CAPTURED_PREVIEW = "delivery_captured_preview"
STAGE_PROVIDER_ACCEPTED = "provider_accepted"
STAGE_AUDIT_WRITTEN = "audit_written"
STAGE_DASHBOARD_UPDATED = "dashboard_updated"
STAGE_COMPLETED = "completed"
STAGE_COMPLETED_FOR_ENVIRONMENT = "completed_for_environment"

ALLOWED_STAGES = {
    STAGE_RECORD_CREATED,
    STAGE_VALIDATION_COMPLETE,
    STAGE_ROUTING_RESOLVED,
    STAGE_RECIPIENTS_BUILT,
    STAGE_NOTIFICATION_QUEUED,
    STAGE_DELIVERY_CAPTURED_PREVIEW,
    STAGE_PROVIDER_ACCEPTED,
    STAGE_AUDIT_WRITTEN,
    STAGE_DASHBOARD_UPDATED,
    STAGE_COMPLETED,
    STAGE_COMPLETED_FOR_ENVIRONMENT,
}

ALLOWED_STATUSES = {"ok", "skipped", "failed"}

# Per-workflow ordered contract used by the dashboard to render
# missing-stage AMBER bands. A workflow's record is "fully verified"
# only when every stage in its expected list has at least one ok event.
WORKFLOW_EXPECTED_STAGES: Dict[str, list] = {
    "daily-report": [
        STAGE_RECORD_CREATED, STAGE_ROUTING_RESOLVED,
        STAGE_RECIPIENTS_BUILT, STAGE_NOTIFICATION_QUEUED,
        STAGE_AUDIT_WRITTEN, STAGE_COMPLETED,
        STAGE_COMPLETED_FOR_ENVIRONMENT,
    ],
    "meeting": [
        STAGE_RECORD_CREATED, STAGE_ROUTING_RESOLVED,
        STAGE_RECIPIENTS_BUILT, STAGE_NOTIFICATION_QUEUED,
        STAGE_PROVIDER_ACCEPTED, STAGE_AUDIT_WRITTEN,
        STAGE_COMPLETED,
    ],
    "inspection": [
        STAGE_RECORD_CREATED, STAGE_ROUTING_RESOLVED,
        STAGE_RECIPIENTS_BUILT, STAGE_NOTIFICATION_QUEUED,
        STAGE_PROVIDER_ACCEPTED, STAGE_AUDIT_WRITTEN,
        STAGE_COMPLETED,
    ],
    "incident": [
        STAGE_RECORD_CREATED, STAGE_ROUTING_RESOLVED,
        STAGE_RECIPIENTS_BUILT, STAGE_NOTIFICATION_QUEUED,
        STAGE_PROVIDER_ACCEPTED, STAGE_AUDIT_WRITTEN,
        STAGE_COMPLETED,
    ],
    "jha": [
        STAGE_RECORD_CREATED, STAGE_ROUTING_RESOLVED,
        STAGE_RECIPIENTS_BUILT, STAGE_NOTIFICATION_QUEUED,
        STAGE_PROVIDER_ACCEPTED, STAGE_AUDIT_WRITTEN,
        STAGE_COMPLETED,
    ],
    "qaqc": [
        STAGE_RECORD_CREATED, STAGE_ROUTING_RESOLVED,
        STAGE_RECIPIENTS_BUILT, STAGE_NOTIFICATION_QUEUED,
        STAGE_PROVIDER_ACCEPTED, STAGE_AUDIT_WRITTEN,
        STAGE_COMPLETED,
    ],
    "equipment-inspection": [
        STAGE_RECORD_CREATED, STAGE_ROUTING_RESOLVED,
        STAGE_RECIPIENTS_BUILT, STAGE_NOTIFICATION_QUEUED,
        STAGE_PROVIDER_ACCEPTED, STAGE_AUDIT_WRITTEN,
        STAGE_COMPLETED,
    ],
    "dvir": [
        STAGE_RECORD_CREATED, STAGE_ROUTING_RESOLVED,
        STAGE_RECIPIENTS_BUILT, STAGE_NOTIFICATION_QUEUED,
        STAGE_PROVIDER_ACCEPTED, STAGE_AUDIT_WRITTEN,
        STAGE_COMPLETED,
    ],
    "hr-request": [
        STAGE_RECORD_CREATED, STAGE_VALIDATION_COMPLETE,
        STAGE_ROUTING_RESOLVED, STAGE_DASHBOARD_UPDATED,
        STAGE_AUDIT_WRITTEN, STAGE_COMPLETED,
    ],
    "dispatch-assignment": [
        STAGE_RECORD_CREATED, STAGE_ROUTING_RESOLVED,
        STAGE_DASHBOARD_UPDATED, STAGE_AUDIT_WRITTEN,
        STAGE_COMPLETED,
    ],
    "operational-events-materialization": [
        STAGE_RECORD_CREATED, STAGE_VALIDATION_COMPLETE,
        STAGE_ROUTING_RESOLVED, STAGE_AUDIT_WRITTEN,
        STAGE_DASHBOARD_UPDATED, STAGE_COMPLETED,
    ],
    "shop-defect": [
        STAGE_RECORD_CREATED, STAGE_ROUTING_RESOLVED,
        STAGE_DASHBOARD_UPDATED, STAGE_AUDIT_WRITTEN,
        STAGE_COMPLETED,
    ],
    "oppc-cost-code-plan": [
        STAGE_RECORD_CREATED, STAGE_VALIDATION_COMPLETE,
        STAGE_AUDIT_WRITTEN, STAGE_DASHBOARD_UPDATED,
        STAGE_COMPLETED,
    ],
    "oppc-weekly-rollover": [
        STAGE_RECORD_CREATED, STAGE_VALIDATION_COMPLETE,
        STAGE_AUDIT_WRITTEN, STAGE_DASHBOARD_UPDATED,
        STAGE_COMPLETED,
    ],
    "oppc-daily-actuals": [
        STAGE_RECORD_CREATED, STAGE_VALIDATION_COMPLETE,
        STAGE_AUDIT_WRITTEN, STAGE_DASHBOARD_UPDATED,
        STAGE_COMPLETED,
    ],
    "oppc-payroll-reconciliation": [
        STAGE_RECORD_CREATED, STAGE_VALIDATION_COMPLETE,
        STAGE_AUDIT_WRITTEN, STAGE_DASHBOARD_UPDATED,
        STAGE_COMPLETED,
    ],
    "oppc-monday-look-behind": [
        STAGE_RECORD_CREATED, STAGE_VALIDATION_COMPLETE,
        STAGE_AUDIT_WRITTEN, STAGE_DASHBOARD_UPDATED,
        STAGE_COMPLETED,
    ],
    "oppc-variance-intelligence": [
        STAGE_RECORD_CREATED, STAGE_VALIDATION_COMPLETE,
        STAGE_AUDIT_WRITTEN, STAGE_DASHBOARD_UPDATED,
        STAGE_COMPLETED,
    ],
    "oppc-recovery-intelligence": [
        STAGE_RECORD_CREATED, STAGE_VALIDATION_COMPLETE,
        STAGE_AUDIT_WRITTEN, STAGE_DASHBOARD_UPDATED,
        STAGE_COMPLETED,
    ],
    "oppc-enterprise-resource-coordination": [
        STAGE_RECORD_CREATED, STAGE_VALIDATION_COMPLETE,
        STAGE_AUDIT_WRITTEN, STAGE_DASHBOARD_UPDATED,
        STAGE_COMPLETED,
    ],
    "oppc-forecasting": [
        STAGE_RECORD_CREATED, STAGE_VALIDATION_COMPLETE,
        STAGE_AUDIT_WRITTEN, STAGE_DASHBOARD_UPDATED,
        STAGE_COMPLETED,
    ],
    "oppc-monday-morning-briefing": [
        STAGE_RECORD_CREATED, STAGE_VALIDATION_COMPLETE,
        STAGE_AUDIT_WRITTEN, STAGE_DASHBOARD_UPDATED,
        STAGE_COMPLETED,
    ],
    "oppc-production-confidence": [
        STAGE_RECORD_CREATED, STAGE_VALIDATION_COMPLETE,
        STAGE_AUDIT_WRITTEN, STAGE_DASHBOARD_UPDATED,
        STAGE_COMPLETED,
    ],
}


def new_correlation_id() -> str:
    """Return a fresh correlation ID for one record's lifecycle.

    Issued at ``STAGE_RECORD_CREATED`` and propagated through every
    subsequent stage so the dashboard can trace a record end-to-end."""
    return f"cid-{uuid.uuid4().hex}"


def attach_correlation(record: dict) -> str:
    """Return the record's correlation_id, attaching a new one if missing.

    Stored on the record dict as ``_trust_cid`` so downstream
    dispatcher code can pick it up without round-tripping to Mongo.
    """
    if not isinstance(record, dict):
        return new_correlation_id()
    cid = record.get("_trust_cid")
    if not cid:
        cid = new_correlation_id()
        record["_trust_cid"] = cid
    return cid


def _ids_from_record(record: dict) -> Dict[str, str]:
    """Pull record_id + project_number from a workflow record dict."""
    if not isinstance(record, dict):
        return {"record_id": "", "project_number": ""}
    return {
        "record_id": str(
            record.get("doc_id")
            or record.get("id")
            or record.get("_id")
            or ""
        ),
        "project_number": str(record.get("project_number") or ""),
    }


async def emit_stage(
    db,
    *,
    workflow: str,
    stage: str,
    correlation_id: str,
    record_id: Optional[str] = None,
    project_number: Optional[str] = None,
    module: Optional[str] = None,
    status: str = "ok",
    duration_ms: Optional[int] = None,
    failure_reason: Optional[str] = None,
    remediation: Optional[str] = None,
    event_name: Optional[str] = None,
) -> None:
    """Write one Trust Spine lifecycle event.

    Best-effort: catches every exception. A Trust Spine write must
    never break the workflow that called it."""
    if stage not in ALLOWED_STAGES:
        logger.warning("[trust_spine] unknown stage=%r — refusing to emit", stage)
        return
    if status not in ALLOWED_STATUSES:
        logger.warning("[trust_spine] unknown status=%r — refusing to emit", status)
        return
    try:
        doc: Dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "workflow": workflow,
            "stage": stage,
            "correlation_id": correlation_id,
            "record_id": (record_id or "")[:128],
            "project_number": (project_number or "")[:64],
            "module": (module or "")[:96],
            "status": status,
            "duration_ms": int(duration_ms) if duration_ms is not None else None,
            "failure_reason": (failure_reason or "")[:240] or None,
        }
        if remediation:
            doc["remediation"] = remediation[:240]
        if event_name:
            doc["event_name"] = event_name[:120]
        await db.trust_spine_events.insert_one(doc)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "[trust_spine] emit failed workflow=%s stage=%s err=%s",
            workflow, stage, exc,
        )


# ───────────────────────────────────────────────────────────────────
# Record-aware helpers (keep workflow files clean).
# Each accepts a workflow record dict; pulls/attaches correlation_id
# and ids automatically. All best-effort — never raise.
# ───────────────────────────────────────────────────────────────────


async def emit_record_created(
    db, *, workflow: str, record: dict, module: str, event_name: Optional[str] = None
) -> str:
    """Open a record's lifecycle. Returns the correlation_id."""
    cid = attach_correlation(record)
    ids = _ids_from_record(record)
    await emit_stage(
        db, workflow=workflow, stage=STAGE_RECORD_CREATED,
        correlation_id=cid, module=module, status="ok", event_name=event_name, **ids,
    )
    return cid


async def emit_workflow_stage(
    db,
    *,
    workflow: str,
    stage: str,
    record: dict,
    module: str,
    status: str = "ok",
    failure_reason: Optional[str] = None,
    remediation: Optional[str] = None,
    event_name: Optional[str] = None,
) -> None:
    """Emit any subsequent stage for a record, using its threaded cid."""
    cid = attach_correlation(record)
    ids = _ids_from_record(record)
    await emit_stage(
        db, workflow=workflow, stage=stage, correlation_id=cid,
        module=module, status=status,
        failure_reason=failure_reason, remediation=remediation,
        event_name=event_name,
        **ids,
    )


async def ensure_indexes(db) -> None:
    """Idempotent index creation. Safe to call on startup."""
    try:
        await db.trust_spine_events.create_index([("workflow", 1), ("ts", -1)])
        await db.trust_spine_events.create_index([("correlation_id", 1)])
        await db.trust_spine_events.create_index([("status", 1), ("ts", -1)])
        await db.trust_spine_events.create_index([("workflow", 1), ("stage", 1), ("ts", -1)])
    except Exception as exc:  # noqa: BLE001
        logger.warning("[trust_spine] index creation failed: %s", exc)
