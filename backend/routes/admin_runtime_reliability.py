from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Query

from lib.runtime_reliability import INCIDENT_COLLECTION, INCIDENT_DIR, runtime_health_snapshot
from lib.release_gate_governance import load_release_gate_manifest


def build_runtime_reliability_router(*, app, db, require_admin_dep) -> APIRouter:
    router = APIRouter(prefix="/api/admin-strict/diag", tags=["admin-diag"])

    @router.get("/runtime-health")
    async def runtime_health(_admin: Any = Depends(require_admin_dep)) -> Dict[str, Any]:
        return runtime_health_snapshot(app)

    @router.get("/performance-baseline")
    async def performance_baseline(_admin: Any = Depends(require_admin_dep)) -> Dict[str, Any]:
        path = Path("/app/docs/performance/performance_baseline.json")
        payload: Dict[str, Any] = {"ok": False, "path": str(path), "exists": path.exists()}
        if path.exists():
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                payload["ok"] = True
            except Exception as exc:
                payload = {"ok": False, "path": str(path), "exists": True, "error": type(exc).__name__}
        return payload

    @router.get("/performance-budget-contract")
    async def performance_budget_contract(_admin: Any = Depends(require_admin_dep)) -> Dict[str, Any]:
        manifest = load_release_gate_manifest()
        perf = manifest.get("performance_prerequisites") or {}
        rel_path = str(perf.get("performance_budget_register") or "memory/WP18DA_PERFORMANCE_BUDGET_REGISTER.csv")
        path = Path("/app") / rel_path
        payload: Dict[str, Any] = {
            "ok": False,
            "path": str(path),
            "exists": path.exists(),
            "required_budget_keys": list(perf.get("required_budget_keys") or []),
        }
        if not path.exists():
            payload["summary"] = "Performance budget register is missing."
            return payload
        try:
            with path.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
        except Exception as exc:  # pragma: no cover
            return {
                **payload,
                "summary": "Performance budget register could not be parsed.",
                "error": type(exc).__name__,
            }

        required_keys = list(perf.get("required_budget_keys") or [])
        rows_by_key = {
            str((row or {}).get("budget_key") or "").strip(): row
            for row in rows
            if str((row or {}).get("budget_key") or "").strip()
        }
        missing_keys = [key for key in required_keys if key not in rows_by_key]
        failing_rows = []
        for key, row in rows_by_key.items():
            status = str((row or {}).get("status") or "").strip().upper()
            if status != "PASS":
                failing_rows.append(
                    {
                        "budget_key": key,
                        "status": status or "MISSING",
                        "measured": row.get("measured"),
                        "target": row.get("target"),
                    }
                )
        payload.update(
            {
                "ok": not missing_keys and not failing_rows,
                "row_count": len(rows),
                "pass_count": sum(1 for row in rows if str((row or {}).get("status") or "").strip().upper() == "PASS"),
                "missing_keys": missing_keys,
                "failing_rows": failing_rows,
                "summary": (
                    "Performance budget contract is currently satisfied."
                    if not missing_keys and not failing_rows
                    else "Performance budget contract is currently blocking release."
                ),
            }
        )
        return payload

    @router.get("/incident-forensics")
    async def incident_forensics(
        limit: int = Query(25, ge=1, le=100),
        _admin: Any = Depends(require_admin_dep),
    ) -> Dict[str, Any]:
        mongo_rows: List[Dict[str, Any]] = []
        try:
            async for row in db[INCIDENT_COLLECTION].find({}, {"_id": 0}).sort("captured_dt", -1).limit(limit):
                mongo_rows.append(row)
        except Exception:
            mongo_rows = []

        file_rows: List[Dict[str, Any]] = []
        for path in sorted(Path(INCIDENT_DIR).glob("*.json"), reverse=True)[:limit]:
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                payload["storage"] = payload.get("storage") or "file_fallback"
                file_rows.append(payload)
            except Exception:
                continue

        rows = sorted(
            mongo_rows + file_rows,
            key=lambda item: str(item.get("captured_at") or ""),
            reverse=True,
        )[:limit]
        return {"count": len(rows), "rows": rows}

    return router


__all__ = ["build_runtime_reliability_router"]