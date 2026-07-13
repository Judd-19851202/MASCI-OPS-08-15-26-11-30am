"""TRACK 24.17 · Daily Report delivery health probe."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from lib.synthetic_dr_filter import apply_synthetic_dr_exclusion

from .registry import Operation, OperationCategory, RiskLevel


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _dr_health(payload: Dict[str, Any]) -> Dict[str, Any]:
    db = payload["_db"]
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    try:
        total_24h = await db.daily_reports.count_documents(
            apply_synthetic_dr_exclusion({"created_at": {"$gte": cutoff}}),
        )
        with_ai = await db.daily_reports.count_documents({
            **apply_synthetic_dr_exclusion({"created_at": {"$gte": cutoff}}),
            "ai_accepted_summary": {"$exists": True, "$nin": ["", None]},
        })
        with_manifest = await db.daily_reports.count_documents({
            **apply_synthetic_dr_exclusion({"created_at": {"$gte": cutoff}}),
            "evidence_manifest": {"$exists": True, "$ne": None},
        })
    except Exception as e:  # noqa: BLE001
        return {"status": "unavailable", "error": str(e)[:200]}
    warnings: List[str] = []
    state = "healthy"
    if total_24h > 0:
        ai_pct = round((with_ai / total_24h) * 100, 1)
        manifest_pct = round((with_manifest / total_24h) * 100, 1)
        if ai_pct < 60:
            state = "warning"
            warnings.append(
                f"Only {ai_pct}% of last 24 h daily reports carry an "
                "accepted AI summary — supervisors may be skipping the "
                "Operational Summary Assist step."
            )
    else:
        ai_pct = 0.0
        manifest_pct = 0.0
    return {
        "status": state,
        "summary": (
            f"{total_24h} daily report(s) in the last 24 h · "
            f"{with_ai} with accepted AI summary · "
            f"{with_manifest} with evidence manifest"
        ),
        "count_last_24h": total_24h,
        "with_ai_accepted_summary": with_ai,
        "with_evidence_manifest": with_manifest,
        "ai_coverage_percent": ai_pct,
        "manifest_coverage_percent": manifest_pct,
        "warnings": warnings,
        "generated_at": _now_iso(),
    }


def operations(_db) -> List[Operation]:
    return [
        Operation(
            id="daily_reports.health",
            title="Daily Report Health",
            description=(
                "Last-24-hour daily report submission count, accepted "
                "AI summary coverage, and evidence manifest coverage."
            ),
            category=OperationCategory.DAILY_REPORTS,
            risk=RiskLevel.INFO,
            status_fn=_dr_health,
            dry_run_fn=_dr_health,
            reads=["db.daily_reports (aggregate counts only)"],
            writes=[],
            never_touches=["individual daily reports"],
        ),
    ]
