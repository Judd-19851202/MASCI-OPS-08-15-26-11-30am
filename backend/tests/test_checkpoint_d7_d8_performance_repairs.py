from __future__ import annotations

from typing import Any, Dict, List

import pytest

from pm_auth import PmScope
from services.safety_portal_trench.trench_kpi_lift import project_trench_safety_kpis


class _Cursor:
    def __init__(self, docs: List[Dict[str, Any]]):
        self._docs = list(docs)

    def sort(self, *args, **kwargs):
        return self

    def limit(self, n: int):
        self._docs = self._docs[:n]
        return self

    async def to_list(self, n: int):
        return list(self._docs)[:n]

    def __aiter__(self):
        self._i = 0
        return self

    async def __anext__(self):
        if self._i >= len(self._docs):
            raise StopAsyncIteration
        row = self._docs[self._i]
        self._i += 1
        return row


class _FactsCollection:
    def __init__(self, docs: List[Dict[str, Any]]):
        self.docs = list(docs)
        self.find_queries: List[Dict[str, Any]] = []
        self.count_queries: List[Dict[str, Any]] = []

    def _match(self, doc: Dict[str, Any], query: Dict[str, Any]) -> bool:
        for key, value in (query or {}).items():
            cur: Any = doc
            for part in key.split("."):
                if isinstance(cur, dict):
                    cur = cur.get(part)
                else:
                    cur = None
                    break
            if isinstance(value, dict):
                for op, opv in value.items():
                    if op == "$gte":
                        if cur is None or cur < opv:
                            return False
                    elif op == "$in":
                        if cur not in opv:
                            return False
                    else:
                        raise AssertionError(f"Unsupported operator in test double: {op}")
                continue
            if cur != value:
                return False
        return True

    def find(self, query=None, projection=None):
        query = query or {}
        self.find_queries.append(dict(query))
        return _Cursor([d for d in self.docs if self._match(d, query)])

    async def count_documents(self, query):
        self.count_queries.append(dict(query))
        return sum(1 for d in self.docs if self._match(d, query))


class _DB:
    def __init__(self, docs: List[Dict[str, Any]]):
        self.operational_facts = _FactsCollection(docs)

    def __getitem__(self, name: str):
        if name == "operational_facts":
            return self.operational_facts
        raise KeyError(name)


def _fact(project_id: str, fact_type: str, *, payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
    return {
        "tenant_id": "masci",
        "source_type": "trench_safety",
        "source_id": "trench_safety",
        "project_id": project_id,
        "fact_type": fact_type,
        "is_current": True,
        "date": "2026-07-19",
        "created_at": "2026-07-19T10:00:00+00:00",
        "payload": payload or {},
    }


def test_pm_scope_definitively_empty_only_for_non_admin_without_projects():
    assert PmScope(is_admin=False, project_numbers=[]).is_definitively_empty() is True
    assert PmScope(is_admin=False, project_numbers=["20-01"]).is_definitively_empty() is False
    assert PmScope(is_admin=True, project_numbers=[]).is_definitively_empty() is False


@pytest.mark.asyncio
async def test_project_trench_kpis_latest_fact_queries_are_project_bounded(monkeypatch):
    docs = [
        _fact("target-project", "excavation_day_fact", payload={"utilities_status": "ok"}),
        _fact("target-project", "competent_person_assignment_fact", payload={"cert_valid_at_report": True}),
        _fact("other-project", "excavation_day_fact", payload={"utilities_status": "damage_strike"}),
        _fact("other-project", "competent_person_assignment_fact", payload={"cert_valid_at_report": False}),
    ]
    db = _DB(docs)

    async def _fake_breakdown(_db, _project_number):
        return {"live": 1, "partial": 0, "ambiguous": 0, "missing": 0}

    monkeypatch.setattr(
        "services.safety_portal_trench.trench_kpi_lift._fact_link_breakdown_for_project",
        _fake_breakdown,
    )

    result = await project_trench_safety_kpis(db, "target-project")

    assert result["project_number"] == "target-project"
    latest_queries = [
        q for q in db.operational_facts.find_queries
        if q.get("fact_type") in {"excavation_day_fact", "competent_person_assignment_fact"}
    ]
    assert latest_queries, "expected fact reads to occur"
    assert all(q.get("project_id") == "target-project" for q in latest_queries)


def test_d7_d8_performance_docs_exist():
    required = [
        "/app/docs/performance/performance_baseline.json",
        "/app/docs/performance/PERFORMANCE_BASELINE.md",
        "/app/docs/performance/ATLAS_ALERT_EVIDENCE_REGISTER.md",
        "/app/docs/performance/query_inventory.json",
        "/app/docs/performance/INDEX_QUERY_RECOMMENDATION_REGISTER.md",
        "/app/docs/architecture/PERFORMANCE_EVENT_CONTRACT.md",
        "/app/docs/architecture/SAFE_SELF_HEALING_FOUNDATION.md",
    ]
    import os
    for path in required:
        assert os.path.exists(path), path


@pytest.mark.asyncio
async def test_qaqc_list_short_circuits_without_mongo_when_scope_empty(monkeypatch):
    from fastapi import APIRouter
    from routes.qaqc import register_qaqc_routes

    class _NoQueryCollection:
        def find(self, *args, **kwargs):
            raise AssertionError("Mongo should not be queried for definitively empty PM scope")

    class _DBQaqc:
        qaqc_inspections = _NoQueryCollection()

    async def _empty_scope(_db, _actor):
        return PmScope(is_admin=False, project_numbers=[])

    monkeypatch.setattr("routes.qaqc.compute_pm_scope", _empty_scope)

    router = APIRouter()
    register_qaqc_routes(router, _DBQaqc(), lambda: {"role": "pm"}, lambda: None, lambda *a, **k: None)
    endpoint = next(route.endpoint for route in router.routes if getattr(route, "path", "") == "/qaqc-inspections" and "GET" in getattr(route, "methods", set()))

    result = await endpoint(actor={"role": "pm"})
    assert result == []


@pytest.mark.asyncio
async def test_daily_report_csv_short_circuits_without_mongo_when_scope_empty(monkeypatch):
    from routes.daily_reports import _run_daily_reports_csv_export

    async def _empty_scope(_db, _actor):
        return PmScope(is_admin=False, project_numbers=[])

    monkeypatch.setattr("routes.daily_reports.compute_pm_scope", _empty_scope)

    result = await _run_daily_reports_csv_export(object(), actor={"role": "pm"})

    assert result["rows"] == 0
    assert result["filename"] == "daily_reports.csv"
    assert result["content"].decode("utf-8").startswith("report_number,")