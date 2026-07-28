import re

from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient

from routes.oppc_execution import register_oppc_execution_routes


class _Cursor:
    def __init__(self, rows):
        self.rows = list(rows)
        self._idx = 0

    def sort(self, *_args, **_kwargs):
        return self

    def limit(self, _count):
        return self

    async def to_list(self, _count):
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

    async def find_one(self, query, projection=None, sort=None):
        rows = list(self.rows)
        if sort:
            key, direction = sort[0]
            rows = sorted(rows, key=lambda row: row.get(key) or "", reverse=direction < 0)
        for row in rows:
            ok = True
            for key, value in query.items():
                if row.get(key) != value:
                    ok = False
                    break
            if ok:
                if projection:
                    positive_keys = [key for key, keep in projection.items() if keep and key != "_id"]
                    if not positive_keys:
                        return {k: v for k, v in row.items() if k != "_id"}
                    out = {}
                    for key, keep in projection.items():
                        if keep and key != "_id":
                            if "." in key:
                                root, sub = key.split(".", 1)
                                out.setdefault(root, {})
                                out[root][sub] = (row.get(root) or {}).get(sub)
                            else:
                                out[key] = row.get(key)
                    return out
                return dict(row)
        return None

    def find(self, query, projection=None):
        def _match_clause(doc, key, value):
            if key == "$or":
                return any(all(_match_clause(doc, sk, sv) for sk, sv in clause.items()) for clause in value)
            if key == "$and":
                return all(all(_match_clause(doc, sk, sv) for sk, sv in clause.items()) for clause in value)
            if isinstance(value, dict) and "$gte" in value:
                current = doc.get(key) or ""
                return value["$gte"] <= current <= value.get("$lte", current)
            if isinstance(value, dict) and "$in" in value:
                return doc.get(key) in value["$in"]
            if isinstance(value, dict) and "$regex" in value:
                return str(doc.get(key) or "").startswith(value["$regex"].replace("^", "").split(".*")[0])
            if isinstance(value, dict) and "$not" in value:
                regex = (((value.get("$not") or {}).get("$regex")) or "")
                options = (((value.get("$not") or {}).get("$options")) or "")
                flags = re.IGNORECASE if "i" in options.lower() else 0
                return re.search(regex, str(doc.get(key) or ""), flags) is None
            if isinstance(value, dict) and "$ne" in value:
                return doc.get(key) != value["$ne"]
            return doc.get(key) == value

        matched = []
        for row in self.rows:
            ok = True
            for key, value in query.items():
                ok = _match_clause(row, key, value)
                if not ok:
                    break
            if ok:
                if projection:
                    positive_keys = [key for key, keep in projection.items() if keep and key != "_id"]
                    if not positive_keys:
                        matched.append({k: v for k, v in row.items() if k != "_id"})
                    else:
                        matched.append({k: row.get(k) for k, keep in projection.items() if keep and k != "_id"})
                else:
                    matched.append(dict(row))
        return _Cursor(matched)

    async def update_one(self, query, update, upsert=False):
        for row in self.rows:
            if all(row.get(k) == v for k, v in query.items()):
                for key, value in (update or {}).get("$set", {}).items():
                    if "." in key:
                        root, sub = key.split(".", 1)
                        row.setdefault(root, {})
                        row[root][sub] = value
                    else:
                        row[key] = value
                return type("R", (), {"matched_count": 1})()
        if upsert:
            doc = dict(query)
            doc.update((update or {}).get("$set", {}))
            self.rows.append(doc)
            return type("R", (), {"matched_count": 1})()
        return type("R", (), {"matched_count": 0})()

    async def insert_one(self, doc):
        self.rows.append(dict(doc))
        return type("R", (), {"inserted_id": doc.get("id")})()


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
                        "planned_performer": "Crew A",
                        "target_man_hours": 40,
                        "planned_equipment_units": ["MILLER-1"],
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
                        "planned_performer": "Crew B",
                        "target_man_hours": 24,
                        "planned_equipment_units": ["PAVER-1"],
                    },
                ],
            }
        ])
        self.daily_reports = _Collection([
            {
                "project_number": "20-07",
                "report_date": "2026-07-17",
                "doc_id": "dr-1",
                "created_at": "2026-07-17T18:00:00+00:00",
                "masci_crews": [{"name": "Crew A", "hours": 10}],
                "equipment": [{"unit_number": "MILLER-1", "hours_used": 4}],
                "photos": ["photo://1"],
                "constraints": [{"constraint_type": "weather", "notes": "Rain delay"}],
                "cost_code_quantities": [{"cost_code": "MILL", "installed_quantity": 25}],
                "narrative_sections": {"tomorrow_plan": "Finish milling"},
                "subcontractors": [],
            },
            {
                "project_number": "20-07",
                "report_date": "2026-07-18",
                "doc_id": "dr-2",
                "created_at": "2026-07-18T18:00:00+00:00",
                "masci_crews": [{"name": "Crew B", "hours": 8}],
                "equipment": [{"unit_number": "PAVER-1", "hours_used": 3}],
                "photos": [],
                "constraints": [],
                "cost_code_quantities": [{"cost_code": "PAVE", "installed_quantity": 10}],
                "narrative_sections": {"tomorrow_plan": "Continue paving"},
                "subcontractors": [],
            },
        ])
        self.haul_cycles = _Collection([
            {"project_number": "20-07", "completed_at": "2026-07-17T14:00:00", "truck_id": "T-1", "truck_number": "TRUCK-1"}
        ])
        self.payroll_variance_batches = _Collection([
            {
                "id": "pv-1",
                "week_ending": "2026-07-19",
                "lifecycle_state": "FINALIZED",
                "rows": [
                    {"masci_jobs": ["20-07"], "exact_total": 18, "masci_total": 18, "diff_hours": 0, "flag": "ok"}
                ],
            }
        ])
        self.operational_variance_reviews = _Collection([])
        self.project_team_assignments = _Collection([
            {"project_number": "20-07", "assignment_role": "superintendent", "display_name": "Sup 1", "active": True},
            {"project_number": "20-07", "assignment_role": "foreman", "display_name": "Foreman 1", "active": True},
        ])
        self.dispatch_assignments = _Collection([
            {"project_number": "20-07", "truck_id": "TRUCK-1", "current_state": "assigned"},
            {"project_number": "20-08", "truck_id": "TRUCK-1", "current_state": "assigned"},
        ])
        self.equipment_master = _Collection([
            {"unit_number": "MILLER-1", "current_project_number": "20-07", "is_active": True},
            {"unit_number": "MILLER-1", "current_project_number": "20-08", "is_active": True},
        ])
        self.fleet_defects = _Collection([
            {"truck_unit_number": "TRUCK-1", "status": "open"},
        ])
        self.tasks = _Collection([])
        self.trust_spine_events = _Collection([])

    def __getitem__(self, name):
        return getattr(self, name)


def _client(actor):
    db = _DB()
    app = APIRouter(prefix="/api")

    async def _require_any_portal_token():
        return actor

    register_oppc_execution_routes(app, db, _require_any_portal_token)
    real = FastAPI()
    real.include_router(app)
    return TestClient(real), db


def test_execution_workspace_returns_monday_review_metrics():
    client, _ = _client({"role": "pm", "email": "pm@example.com", "id": "pm-1"})
    r = client.get("/api/oppc/projects/20-07/execution-workspace", params={"week_ending": "2026-07-19"})
    assert r.status_code == 200
    body = r.json()
    assert body["production_summary"]["actual_quantity"] == 35
    assert body["payroll_summary"]["complete"] is True
    assert len(body["monday_review"]["activities"]) == 2


def test_activity_review_creates_recovery_task_and_updates_workspace():
    client, db = _client({"role": "pm", "email": "pm@example.com", "id": "pm-1"})
    started = client.post("/api/oppc/projects/20-07/monday-review/start", json={"week_ending": "2026-07-19"})
    assert started.status_code == 200
    r = client.put(
        "/api/oppc/projects/20-07/monday-review/activities/MILL",
        json={
            "week_ending": "2026-07-19",
            "primary_cause": "weather",
            "contributing_causes": ["planning"],
            "controllability": "shared",
            "evidence": ["Daily report weather delay"],
            "recovery_strategy": "Add Saturday shift",
            "recovery_owner_role": "pm",
            "recovery_date": "2026-07-22",
            "forecast_impact": "No forecast slip after recovery",
            "critical_path_impact": "Monitor",
            "executive_escalation": False,
            "executive_actions": [],
            "notes": "Reviewed",
        },
    )
    assert r.status_code == 200
    body = r.json()
    mill = next(row for row in body["monday_review"]["activities"] if row["code"] == "MILL")
    assert mill["review"]["primary_cause"] == "weather"
    assert db.tasks.rows


def test_variance_intelligence_returns_canonical_variances():
    client, _ = _client({"role": "pm", "email": "pm@example.com", "id": "pm-1"})
    r = client.get("/api/oppc/projects/20-07/variance-intelligence", params={"week_ending": "2026-07-19"})
    assert r.status_code == 200
    body = r.json()
    assert body["summary"]["total_variances"] >= 4
    assert any(row["variance_type"] == "schedule" for row in body["variances"])
    assert any(row["variance_type"] == "production" for row in body["variances"])


def test_variance_review_creates_canonical_recovery_task():
    client, db = _client({"role": "pm", "email": "pm@example.com", "id": "pm-1"})
    intelligence = client.get("/api/oppc/projects/20-07/variance-intelligence", params={"week_ending": "2026-07-19"})
    variance_key = next(row["variance_key"] for row in intelligence.json()["variances"] if row["variance_type"] == "schedule")
    r = client.put(
        f"/api/oppc/projects/20-07/variances/{variance_key}",
        json={
            "status": "recovery_required",
            "primary_cause": "weather",
            "contributing_causes": ["planning"],
            "controllability": "not_preventable",
            "cause_notes": "Rain impacted paving window",
            "recovery_strategy": "weekend_work",
            "recovery_priority": "high",
            "recovery_owner_role": "pm",
            "recovery_due_date": "2026-07-22",
            "requires_executive_review": True,
            "executive_notes": ["Review sequencing with leadership"],
            "recovery_plan": {"planning_cycle": "2026-07-19", "strategy": "weekend_work", "estimated_schedule_gain": 1.5},
        },
    )
    assert r.status_code == 200
    assert db.operational_variance_reviews.rows
    assert db.tasks.rows


def test_enterprise_resource_coordination_returns_conflicts_for_admin():
    client, _ = _client(True)
    r = client.get("/api/oppc/enterprise/resource-coordination", params={"week_ending": "2026-07-19"})
    assert r.status_code == 200
    body = r.json()
    assert body["summary"]["resource_conflicts"] >= 1
    assert any(row["conflict_type"] in {"truck_conflict", "equipment_conflict"} for row in body["conflicts"])


def test_executive_operations_center_returns_summary_for_admin():
    client, db = _client(True)
    db.operational_variance_reviews.rows.append(
        {
            "variance_key": "20-07:2026-07-19:schedule:MILL",
            "project_number": "20-07",
            "status": "recovery_required",
            "requires_executive_review": True,
            "recovery_priority": "critical",
            "recovery_task_id": "task-1",
            "recovery_status": "Open",
        }
    )
    r = client.get("/api/oppc/enterprise/executive-operations-center", params={"week_ending": "2026-07-19"})
    assert r.status_code == 200
    body = r.json()
    assert body["summary"]["open_variances"] >= 1
    assert body["summary"]["leadership_projects"] >= 1
