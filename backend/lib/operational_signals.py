"""
lib/operational_signals.py — Iter160 (Phase 2.5 · Operational Signal Density).

Passive, lightweight, infrastructure-level operational telemetry. Sibling
to `lib/event_fanout.py` but for OBSERVABILITY rather than fan-out.

Captures structured operational events at the same fan-out tap points that
already emit tasks/notifications — so we cannot miss an operational fact
once a workflow happens. Designed to feed `/admin/operational-signals`
rollups (incident throughput, CA cycle time, PO turnaround, equipment fail
frequency, doc threshold fires, training deficiencies, offboarding starts).

Design rules (strict — protect the workflow):
  * NEVER raise. Recording is best-effort. If Mongo is down, the
    originating write still succeeds.
  * Fire-and-forget. No await chains, no transactional dependency.
  * Reuse `db.usage_events` collection (Iter146 infrastructure — already
    TTL-90d indexed). Distinguish operational signals via
    `kind="operational_signal"` so existing usage analytics queries
    (which filter by `kind=="api_call"`) are unaffected.
  * No PII. No employee names, no project numbers, no free-text. Only
    a compact `signal` slug, optional `elapsed_ms` for cycle time,
    and a bounded `dims` dict (≤6 keys, all short strings/ints).
  * No new collection. No new schema. No duplicate audit point.

Signal vocabulary (closed set — extend deliberately):
    incident.created
    inspection.deficiency
    qaqc.deficiency
    equipment.fail
    fire_ext.pass
    fire_ext.fail
    ca.created
    ca.closed              (carries elapsed_ms = closed_at - created_at)
    po.submit
    po.approve             (carries elapsed_ms = approved_at - submitted_at)
    po.reject
    po.clarify
    po.receipt             (carries elapsed_ms = receipt_at - approved_at)
    po.close               (carries elapsed_ms = closed_at - submitted_at)
    po.cancel
    doc.threshold_fired
    training.deficiency
    hr.offboarding_started
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Closed signal vocabulary — explicit guard against scope creep.
ALLOWED_SIGNALS = {
    "incident.created",
    "inspection.deficiency",
    "qaqc.deficiency",
    "equipment.fail",
    "fire_ext.pass",
    "fire_ext.fail",
    "ca.created",
    "ca.closed",
    "po.submit",
    "po.approve",
    "po.reject",
    "po.clarify",
    "po.receipt",
    "po.close",
    "po.cancel",
    "doc.threshold_fired",
    "training.deficiency",
    "hr.offboarding_started",
}

# Hard cap on dims size — keeps the payload predictable.
_MAX_DIMS = 6
_MAX_DIM_KEY = 24
_MAX_DIM_VAL = 48


def _sanitize_dims(dims: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Bound dims to ≤6 short k/v pairs. Strings truncated, non-scalars
    coerced/dropped. Prevents accidental PII or free-text leakage."""
    if not dims or not isinstance(dims, dict):
        return {}
    out: Dict[str, Any] = {}
    for k, v in list(dims.items())[:_MAX_DIMS]:
        if not isinstance(k, str):
            continue
        key = k[:_MAX_DIM_KEY]
        if isinstance(v, bool):
            out[key] = v
        elif isinstance(v, (int, float)):
            out[key] = v
        elif isinstance(v, str):
            out[key] = v[:_MAX_DIM_VAL]
        # Drop everything else (lists, dicts, None) — keep schema tight.
    return out


async def record_signal(
    db,
    *,
    signal: str,
    module: str,
    elapsed_ms: Optional[int] = None,
    dims: Optional[Dict[str, Any]] = None,
) -> None:
    """Fire-and-forget. Persists ONE operational signal row to
    db.usage_events with kind='operational_signal'. Never raises.

    Args:
        signal: must be in ALLOWED_SIGNALS — unknown signals are silently
            dropped (defensive — protects schema integrity).
        module: source module slug (e.g., 'safety.incidents', 'po.requests').
        elapsed_ms: optional milliseconds for cycle-time signals
            (ca.closed, po.approve, po.receipt, po.close). Capped at 32-bit
            positive int.
        dims: optional bounded dimensions (≤6 short k/v pairs). PII-free.
    """
    if signal not in ALLOWED_SIGNALS:
        return
    try:
        doc: Dict[str, Any] = {
            "kind": "operational_signal",
            "signal": signal,
            "module": (module or "")[:64],
            "at": datetime.now(timezone.utc),
            "dims": _sanitize_dims(dims),
        }
        if elapsed_ms is not None:
            try:
                ems = int(elapsed_ms)
                if 0 <= ems <= 2_147_483_647:
                    doc["elapsed_ms"] = ems
            except (TypeError, ValueError):
                pass
        await db.usage_events.insert_one(doc)
    except Exception as e:  # noqa: BLE001
        # NEVER raise — telemetry must not block the originating workflow.
        logger.debug("[operational_signals] record_signal(%s) failed: %s",
                     signal, e)


def elapsed_ms_between(start, end=None) -> Optional[int]:
    """Compute elapsed milliseconds between two datetimes. Returns None if
    `start` is missing or unparseable. Used by tap points that have a
    submitted_at/created_at field and want to publish cycle time."""
    if start is None:
        return None
    end_dt = end if end is not None else datetime.now(timezone.utc)
    try:
        if isinstance(start, str):
            start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
        else:
            start_dt = start
        if isinstance(end_dt, str):
            end_dt = datetime.fromisoformat(end_dt.replace("Z", "+00:00"))
        # Normalize tz-naive to UTC
        if start_dt.tzinfo is None:
            start_dt = start_dt.replace(tzinfo=timezone.utc)
        if end_dt.tzinfo is None:
            end_dt = end_dt.replace(tzinfo=timezone.utc)
        delta = (end_dt - start_dt).total_seconds() * 1000.0
        if delta < 0:
            return 0
        return int(delta)
    except Exception:  # noqa: BLE001
        return None


__all__ = ["record_signal", "elapsed_ms_between", "ALLOWED_SIGNALS"]
