from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Query

from lib.performance_budget_contract import read_performance_budget_contract
from lib.runtime_reliability import INCIDENT_COLLECTION, INCIDENT_DIR, redact_text, runtime_health_snapshot


MAX_INCIDENT_STRING = 1200
MAX_INCIDENT_LIST_ITEMS = 25
MAX_INCIDENT_DICT_KEYS = 60
MAX_INCIDENT_DEPTH = 5


def _bounded_incident_value(value: Any, *, depth: int = 0) -> Any:
    if depth >= MAX_INCIDENT_DEPTH:
        return "<trimmed-depth>"
    if isinstance(value, dict):
        out: Dict[str, Any] = {}
        items = list(value.items())
        for key, item in items[:MAX_INCIDENT_DICT_KEYS]:
            out[str(key)] = _bounded_incident_value(item, depth=depth + 1)
        if len(items) > MAX_INCIDENT_DICT_KEYS:
            out["_trimmed_keys"] = len(items) - MAX_INCIDENT_DICT_KEYS
        return out
    if isinstance(value, list):
        bounded = [_bounded_incident_value(item, depth=depth + 1) for item in value[:MAX_INCIDENT_LIST_ITEMS]]
        if len(value) > MAX_INCIDENT_LIST_ITEMS:
            bounded.append(f"<trimmed-items:{len(value) - MAX_INCIDENT_LIST_ITEMS}>")
        return bounded
    if isinstance(value, str):
        clean = redact_text(value)
        if len(clean) <= MAX_INCIDENT_STRING:
            return clean
        return f"{clean[:MAX_INCIDENT_STRING]}<trimmed:{len(clean) - MAX_INCIDENT_STRING}>"
    return value


def _sanitize_incident_row(row: Dict[str, Any]) -> Dict[str, Any]:
    try:
        payload = json.loads(redact_text(json.dumps(row, default=str)))
        return _bounded_incident_value(payload)
    except Exception:
        return {"redacted_payload": _bounded_incident_value(redact_text(str(row)))}


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
        return read_performance_budget_contract(Path("/app"))

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
        return {"count": len(rows), "rows": [_sanitize_incident_row(row) for row in rows]}

    return router


__all__ = ["build_runtime_reliability_router"]