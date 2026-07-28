from fastapi import APIRouter
from fastapi.testclient import TestClient

from routes.cost_codes import register_cost_code_routes


class _Cursor:
    def __init__(self, rows):
        self.rows = list(rows)
        self._idx = 0

    def sort(self, *_args, **_kwargs):
        return self

    async def to_list(self, _limit):
        return list(self.rows)

    def __aiter__(self):
        self._idx = 0
        return self

    async def __anext__(self):
        if self._idx >= len(self.rows):
            raise StopAsyncIteration
        row = self.rows[self._idx]
        self._idx += 1
        return row


class _Collection:
    def __init__(self, rows=None):
        self.rows = list(rows or [])

    async def create_index(self, *_args, **_kwargs):
        return None

    async def find_one(self, query, projection=None):
        for row in self.rows:
            if all(row.get(k) == v for k, v in query.items()):
                if projection:
                    return {k: row.get(k) for k, keep in projection.items() if keep and k != "_id"}
                return dict(row)
        return None

    def find(self, query, projection=None):
        matched = []
        for row in self.rows:
            ok = True
            for k, v in query.items():
                if k == "$or":
                    ok = any(all(row.get(subk) == subv for subk, subv in clause.items()) for clause in v)
                elif isinstance(v, dict) and "$in" in v:
                    ok = row.get(k) in v["$in"]
                elif isinstance(v, dict):
                    ok = True
                else:
                    ok = row.get(k) == v
                if not ok:
                    break
            if ok:
                if projection:
                    matched.append({k: row.get(k) for k, keep in projection.items() if keep and k != "_id"})
                else:
                    matched.append(dict(row))
        return _Cursor(matched)

    async def update_one(self, query, update, upsert=False):
        for row in self.rows:
            if all(row.get(k) == v for k, v in query.items()):
                row.update((update or {}).get("$set", {}))
                return type("R", (), {"matched_count": 1})()
        if upsert:
            doc = dict(query)
            doc.update((update or {}).get("$set", {}))
            self.rows.append(doc)
            return type("R", (), {"matched_count": 1})()
        return type("R", (), {"matched_count": 0})()


class _DB:
    def __init__(self):
        self.jobs_master = _Collection([
            {
                "project_number": "20-07",
                "pm_email": "pm@example.com",
                "deleted_at": "",
                "assigned_cost_codes": [
                    {
                        "id": "1",
                        "code": "MILL",
                        "item_name": "Milling",
                        "unit_of_measure": "TN",
                        "authorized_quantity": 100,
                        "forecast_quantity": 100,
                        "original_quantity": 100,
                        "schedule_start_date": "2026-07-10",
                        "duration_days": 4,
                        "predecessor_codes": [],
                        "schedule_phase": "Phase 1",
                        "planned_performer": "Paving Crew",
                    },
                    {
                        "id": "2",
                        "code": "PAVE",
                        "item_name": "Paving",
                        "unit_of_measure": "TN",
                        "authorized_quantity": 80,
                        "forecast_quantity": 80,
                        "original_quantity": 80,
                        "schedule_start_date": "2026-07-12",
                        "duration_days": 2,
                        "predecessor_codes": ["MILL"],
                        "schedule_phase": "Phase 2",
                        "planned_performer": "Asphalt Crew",
                    },
                ],
            }
        ])
        self.daily_reports = _Collection([
            {"project_number": "20-07", "report_date": "2026-07-17", "cost_code_quantities": [{"cost_code": "MILL", "installed_quantity": 25}]}
        ])
        self.cost_code_registry = _Collection([])

    def __getitem__(self, name):
        return getattr(self, name)


def _client(actor):
    app = APIRouter()
    db = _DB()

    async def _require_admin():
        return actor

    register_cost_code_routes(app, db, require_admin=_require_admin, require_admin_pm_or_hr_read=_require_admin)
    from fastapi import FastAPI
    real = FastAPI()
    real.include_router(app, prefix="/api")
    return TestClient(real), db


def test_pm_can_read_project_schedule():
    client, _ = _client({"_actor": "pm", "role": "pm", "email": "pm@example.com", "id": "pm-1"})
    r = client.get("/api/cost-codes/projects/20-07/schedule")
    assert r.status_code == 200
    body = r.json()
    assert body["project_number"] == "20-07"
    assert body["schedule"]["monday_look_behind_ready"] is True
    assert body["planning_readiness"]["status"] == "ready"
    assert body["planning_readiness"]["supports_weekly_rollover"] is True


def test_assignment_readiness_is_exposed_for_project_assignments():
    client, _ = _client({"_actor": "pm", "role": "pm", "email": "pm@example.com", "id": "pm-1"})
    r = client.get("/api/cost-codes/projects/20-07/assignments")
    assert r.status_code == 200
    body = r.json()
    assert body["planning_readiness"]["assignment_count"] == 2
    assert all(item.get("planning_readiness", {}).get("status") == "ready" for item in body["assignments"])


def test_publish_project_schedule_sets_lifecycle_status():
    client, db = _client({"_actor": "pm", "role": "pm", "email": "pm@example.com", "id": "pm-1"})
    r = client.post("/api/cost-codes/projects/20-07/planning-lifecycle/publish", json={"note": "Weekly publish"})
    assert r.status_code == 200
    body = r.json()
    assert body["planning_lifecycle"]["status"] == "published"
    assert body["planning_lifecycle"]["has_unpublished_changes"] is False
    assert db.jobs_master.rows[0]["oppc_planning_lifecycle"]["status"] == "published"


def test_pdf_export_returns_pdf_bytes_for_admin():
    client, _ = _client(True)
    r = client.get("/api/cost-codes/projects/20-07/schedule/dot-report.pdf")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content.startswith(b"%PDF")


def test_weekly_rollover_preview_and_apply():
    client, db = _client({"_actor": "pm", "role": "pm", "email": "pm@example.com", "id": "pm-1"})
    preview = client.get("/api/cost-codes/projects/20-07/weekly-rollover/preview")
    assert preview.status_code == 200
    preview_body = preview.json()
    assert preview_body["weekly_rollover"]["status"] in {"ready", "blocked"}
    assert "changed_count" in preview_body["weekly_rollover"]

    apply = client.post(
        "/api/cost-codes/projects/20-07/weekly-rollover/apply",
        json={"confirm": "APPLY_WEEKLY_ROLLOVER", "note": "Weekly rollover"},
    )
    assert apply.status_code == 200
    body = apply.json()
    assert body["weekly_rollover"]["status"] == "ready"
    assert body["planning_lifecycle"]["has_unpublished_changes"] is True
    assert "oppc_last_weekly_rollover" in db.jobs_master.rows[0]