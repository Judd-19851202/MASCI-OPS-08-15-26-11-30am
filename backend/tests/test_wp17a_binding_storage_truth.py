from __future__ import annotations

import asyncio
import sys

sys.path.insert(0, "/app/backend")

from routes.governance import _build_employee_link_review_queue  # noqa: E402
from routes.master_lookup import build_master_binding_audit  # noqa: E402
from services.operations_control import storage as storage_mod  # noqa: E402


class _FakeCollection:
    def __init__(self, docs=None):
        self.docs = list(docs or [])
        self.upserts = []

    async def count_documents(self, query):
        def _matches(doc, clause):
            for key, value in clause.items():
                if isinstance(value, dict):
                    cur = doc.get(key)
                    if "$exists" in value:
                        exists = key in doc
                        if exists != value["$exists"]:
                            return False
                    if "$ne" in value and cur == value["$ne"]:
                        return False
                elif doc.get(key) != value:
                    return False
            return True

        if "$or" in query:
            return sum(1 for doc in self.docs if any(_matches(doc, part) for part in query["$or"]))
        return sum(1 for doc in self.docs if _matches(doc, query))

    async def update_one(self, filt, update, upsert=False):
        self.upserts.append({"filter": filt, "update": update, "upsert": upsert})


class _FakeDB:
    def __init__(self):
        self.equipment_master = _FakeCollection([{"id": "eq-1"}, {"id": "eq-2"}])
        self.employees = _FakeCollection([{"id": "emp-1"}, {"id": "emp-2"}])
        self.incidents = _FakeCollection([
            {"id": "i1", "equipment_unit": "A1", "employee_name": "Jane Doe"},
            {"id": "i2", "equipment_master_id": "eq-1", "employee_master_id": "emp-1"},
            {"id": "i3", "employee_name": "Jane Doe"},
        ])
        self.corrective_actions = _FakeCollection([
            {"id": "c1", "equipment_unit": "A1"},
            {"id": "c2", "employee_name": "Jane Doe", "employee_master_id": "emp-1"},
        ])
        self.equipment_inspections = _FakeCollection([
            {"id": "e1", "equipment_unit": "Truck-1"},
            {"id": "e2", "equipment_master_id": "eq-2"},
        ])
        self.fire_extinguishers = _FakeCollection([])
        self.safety_training_records = _FakeCollection([
            {"id": "t1", "employee_name": "Jane Doe"},
        ])
        self.employee_link_review_queue = _FakeCollection([])

    def __getitem__(self, name):
        return getattr(self, name)


def test_master_binding_audit_uses_eligible_denominator_and_review_queue_endpoint():
    db = _FakeDB()
    out = asyncio.run(build_master_binding_audit(db))
    incident_emp = out["employee_coverage"]["incidents"]
    assert incident_emp["eligible_total"] == 3
    assert incident_emp["with_master_ref"] == 1
    assert incident_emp["pct"] == 33
    assert incident_emp["review_queue_endpoint"] == "/api/admin/compliance/employee-link-review-queue"


def test_employee_link_review_queue_materializes_ambiguous_findings(monkeypatch):
    db = _FakeDB()

    async def fake_findings(_db):
        return [{
            "rule_id": "EMP_LINK_UNRESOLVABLE",
            "entity_id": "ambiguous:jane-doe",
            "entity_name": "Jane Doe",
            "source": {
                "name_norm": "janedoe",
                "matched_employee_ids": ["emp-1", "emp-2"],
                "match_count": 2,
                "collections": {"incidents": 2},
                "record_count": 2,
            },
        }]

    monkeypatch.setattr("routes.governance._detect_employee_linkage", fake_findings)
    out = asyncio.run(_build_employee_link_review_queue(db, materialize=True))
    assert out["candidate_count"] == 1
    assert out["stored_count"] == 1
    assert db.employee_link_review_queue.upserts[0]["filter"]["queue_key"] == "ambiguous:jane-doe"


def test_storage_audit_reports_thresholds_cleanup_projection_and_retention(monkeypatch):
    monkeypatch.setattr(storage_mod, "_dir_stats", lambda p: {"path": str(p), "exists": True, "total_bytes": 1000, "human_total": "1000.0 B"})
    monkeypatch.setattr(storage_mod, "_disk_stats", lambda: {
        "total_bytes": 1000,
        "used_bytes": 800,
        "free_bytes": 200,
        "used_percent": 80.0,
        "human_total": "1000.0 B",
        "human_used": "800.0 B",
        "human_free": "200.0 B",
    })
    monkeypatch.setattr(storage_mod, "_log_stats", lambda: {"entries": [{"path": "/var/log/supervisor/backend.out.log", "bytes": 300, "human": "300.0 B"}]})
    monkeypatch.setattr(storage_mod, "_safe_cleanup_candidates", lambda: {"reclaimable_bytes": 120, "human_total": "120.0 B"})

    async def fake_last_cleanup(_payload):
        return {"generated_at": "2026-07-31T15:00:00+00:00", "reclaimed_human": "50.0 MB"}

    monkeypatch.setattr(storage_mod, "_latest_cleanup_history", fake_last_cleanup)
    out = asyncio.run(storage_mod._storage_audit_dry_run({}))
    assert out["status"] == "warning"
    assert out["thresholds"]["warning_percent"] == 75.0
    assert out["safe_cleanup_projection"]["used_percent"] == 68.0
    assert out["retention_classes"]["/app/backend/storage/project_docs"]["classification"] == "offloadable_to_r2"
    assert out["last_cleanup"]["reclaimed_human"] == "50.0 MB"