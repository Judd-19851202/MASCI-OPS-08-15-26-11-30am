from fastapi import FastAPI
from fastapi.testclient import TestClient

from routes.project_health import build_project_health_router
from routes.ods_intelligence import register_ods_intelligence_routes


class _Cursor:
    def __init__(self, rows):
        self.rows = list(rows or [])

    def sort(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self

    async def to_list(self, limit):
        return list(self.rows)[:limit]

    def __aiter__(self):
        self._iter = iter(self.rows)
        return self

    async def __anext__(self):
        try:
            return next(self._iter)
        except StopIteration as exc:
            raise StopAsyncIteration from exc


class _Collection:
    def __init__(self, rows=None):
        self.rows = list(rows or [])

    async def find_one(self, query, projection=None):
        for row in self.rows:
            if all(row.get(k) == v for k, v in query.items()):
                if projection:
                    include_keys = [k for k, keep in projection.items() if keep and k != "_id"]
                    if include_keys:
                        return {k: row.get(k) for k in include_keys}
                    return {k: v for k, v in row.items() if k != "_id"}
                return dict(row)
        return None

    def find(self, query=None, projection=None):
        query = query or {}
        matched = []
        for row in self.rows:
            ok = True
            for key, value in query.items():
                if isinstance(value, dict) and "$in" in value:
                    if row.get(key) not in value["$in"]:
                        ok = False
                        break
                elif row.get(key) != value:
                    ok = False
                    break
            if ok:
                if projection:
                    include_keys = [k for k, keep in projection.items() if keep and k != "_id"]
                    if include_keys:
                        matched.append({k: row.get(k) for k in include_keys})
                    else:
                        matched.append({k: v for k, v in row.items() if k != "_id"})
                else:
                    matched.append(dict(row))
        return _Cursor(matched)

    async def update_one(self, query, update, upsert=False):
        for row in self.rows:
            if all(row.get(k) == v for k, v in query.items()):
                row.update((update or {}).get("$set", {}))
                return type("R", (), {"matched_count": 1})()
        return type("R", (), {"matched_count": 0})()

    def aggregate(self, pipeline):
        return _Cursor([])


class _Db:
    def __init__(self):
        self.jobs_master = _Collection([
            {
                "project_number": "20-07",
                "project_name": "Canal Expansion",
                "name": "Canal Expansion",
                "active": True,
                "assigned_cost_codes": [
                    {"code": "PIPE", "duration_days": 5, "authorized_quantity": 100, "schedule_start_date": "2026-07-01", "crew_size": 3, "unit": "LF", "production_rate": 20, "calendar": "5x8"}
                ],
                "oppc_variance_summary": {"open_variances": 1, "critical_variances": 0, "recovery_required": 0},
                "oppc_resource_coordination_summary": {"demand_foreman": 1, "supply_foreman": 1, "demand_superintendent": 1, "supply_superintendent": 1, "demand_drivers": 1, "supply_drivers": 1, "conflict_count": 0},
                "latest_payroll_finalized": True,
                "latest_payroll_hours": 24,
            }
        ])
        self.daily_reports = _Collection([
            {"project_number": "20-07", "report_date": "2026-07-28", "cost_code_quantities": [{"cost_code": "PIPE", "installed_quantity": 40, "reported_hours": 24}]}
        ])
        self.tasks = _Collection([])
        self.po_requests = _Collection([])
        self.document_expirations = _Collection([])
        self.incidents = _Collection([])
        self.corrective_actions = _Collection([])
        self.ods_snapshots = _Collection([])
        self.ods_operational_facts = _Collection([])

    def __getitem__(self, key):
        return getattr(self, key)


def _actor():
    return {"_actor": "admin", "role": "admin", "email": "admin@example.com"}


def _app():
    db = _Db()
    app = FastAPI()

    async def require_any_portal_token():
        return _actor()

    app.include_router(build_project_health_router(db, require_any_portal_token))
    router = FastAPI().router
    register_ods_intelligence_routes(router, db)
    app.include_router(router, prefix="/api")
    return TestClient(app), db


def test_project_health_returns_confidence_payload():
    client, _ = _app()
    r = client.get("/api/project-health")
    assert r.status_code == 200
    row = r.json()["rows"][0]
    assert row["production_confidence"]["governance"]["manual_forecast_fields_used"] is False
    assert row["production_confidence"]["score"] > 0


def test_project_confidence_snapshot_endpoint_persists_history():
    client, db = _app()
    r = client.post("/api/project-health/20-07/confidence/snapshots")
    assert r.status_code == 200
    assert db.jobs_master.rows[0]["oppc_confidence_history"][0]["truth_basis"] == "canonical_operational_data"


def test_executive_confidence_endpoint_rolls_up_projects():
    client, _ = _app()
    r = client.get("/api/ods/executive/confidence")
    assert r.status_code == 200
    body = r.json()
    assert body["summary"]["average_score"] > 0
    assert body["projects"][0]["production_confidence"]["components"]