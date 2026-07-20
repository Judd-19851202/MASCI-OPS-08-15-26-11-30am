from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Query

from lib.runtime_reliability import INCIDENT_COLLECTION, INCIDENT_DIR, runtime_health_snapshot


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