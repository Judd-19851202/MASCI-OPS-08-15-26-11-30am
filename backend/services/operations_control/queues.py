"""TRACK 25.01 · Queues & scheduler runs probe for the OCC.

Phase C of the Admin Operating System consolidation: fold the
``/admin/scheduler-runs`` history page into OCC as ``queues.scheduler_runs``.
Read-only. Same collection, same normalization contract used by the
legacy admin page (`routes/scheduler_runs_admin.py`).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from .registry import Operation, OperationCategory, RiskLevel


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _iso(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:  # noqa: BLE001
            return None
    return value


async def _scheduler_runs_status(payload: Dict[str, Any]) -> Dict[str, Any]:
    db = payload.get("_db")
    if db is None:
        return {
            "status": "unavailable",
            "summary": "Scheduler runs probe requires an active database.",
            "generated_at": _now_iso(),
        }
    try:
        from lib.scheduler_runs import (  # noqa: PLC0415
            SCHEDULER_RUNS_COLLECTION,
        )
    except Exception as e:  # noqa: BLE001
        return {
            "status": "unavailable",
            "summary": "scheduler_runs helpers not importable.",
            "error": str(e)[:200],
            "generated_at": _now_iso(),
        }
    coll = db[SCHEDULER_RUNS_COLLECTION]
    try:
        total = await coll.count_documents({})
        failed = await coll.count_documents({"status": "failed"})
        dedup = await coll.count_documents({"dedup_attempts": {"$gt": 0}})
        latest_cursor = coll.find({}, {"_id": 0}).sort("started_at", -1).limit(5)
        latest: List[Dict[str, Any]] = []
        async for doc in latest_cursor:
            for k in ("started_at", "finished_at", "last_dedup_at", "ttl_at"):
                doc[k] = _iso(doc.get(k))
            latest.append(doc)
    except Exception as e:  # noqa: BLE001
        return {
            "status": "critical",
            "summary": f"scheduler_runs read failed: {str(e)[:160]}",
            "generated_at": _now_iso(),
        }

    warnings: List[str] = []
    state = "healthy"
    if failed and total:
        pct = (failed / total) * 100 if total else 0
        if pct >= 10:
            state = "critical"
            warnings.append(
                f"{failed}/{total} scheduler runs failed (≥10%) — "
                "review the failing scheduler."
            )
        elif pct >= 3:
            state = "warning"
            warnings.append(
                f"{failed}/{total} scheduler runs failed."
            )
    if dedup:
        # Dedup trips are informational — the guard is working.
        pass

    last_started = latest[0].get("started_at") if latest else None
    return {
        "status": state,
        "summary": (
            f"{total} scheduler runs recorded · {failed} failed · "
            f"{dedup} dedup trips · latest {last_started or 'never'}"
        ),
        "total_runs": total,
        "failed_runs": failed,
        "dedup_trips": dedup,
        "latest_runs": latest,
        "warnings": warnings,
        "canonical_source": "lib.scheduler_runs",
        "legacy_route": "/admin/scheduler-runs",
        "generated_at": _now_iso(),
    }


def operations(_db) -> List[Operation]:
    return [
        Operation(
            id="queues.scheduler_runs",
            title="Scheduler Runs & Digest History",
            description=(
                "Read-only history of every scheduled digest fire "
                "(PO digest · Safety digest · Operator digest). "
                "Shows total runs, failed runs, dedup trips, and the "
                "5 most recent executions with their status and "
                "recipient counts."
            ),
            category=OperationCategory.QUEUES,
            risk=RiskLevel.INFO,
            status_fn=_scheduler_runs_status,
            dry_run_fn=_scheduler_runs_status,
            reads=["scheduler_runs collection (count + latest 5)"],
            writes=[],
            never_touches=[
                "scheduler run history (append-only in the scheduler)",
                "digest recipients",
            ],
        ),
    ]
