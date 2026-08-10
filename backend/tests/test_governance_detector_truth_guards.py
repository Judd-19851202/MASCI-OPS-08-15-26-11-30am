from __future__ import annotations

import asyncio
import sys
from types import SimpleNamespace

sys.path.insert(0, "/app/backend")

from routes.governance import _detect_incident_lifecycle  # noqa: E402
from lib.synthetic_hr_filter import apply_synthetic_hr_exclusion, is_synthetic_hr  # noqa: E402


class _AsyncCursor:
    def __init__(self, rows):
        self.rows = list(rows)

    def limit(self, _n):
        return self

    async def __aiter__(self):
        for row in self.rows:
            yield row


class _Collection:
    def __init__(self, rows=None, count_map=None):
        self.rows = rows or []
        self.count_map = count_map or {}
        self.last_query = None

    def find(self, query=None, *_args, **_kwargs):
        self.last_query = query
        rows = list(self.rows)
        rendered = str(query or {})
        if "technical_record_classification" in rendered and "$nin" in rendered:
            rows = [
                row for row in rows
                if row.get("technical_record_classification") not in {"synthetic_test", "preview_certification", "technical", "legacy_migration"}
                and row.get("truth_visibility_scope") != "technical_audit_only"
            ]
        return _AsyncCursor(rows)

    async def count_documents(self, query):
        self.last_query = query
        return self.count_map.get("count", 0)


class _Db(SimpleNamespace):
    pass


def test_apply_synthetic_hr_exclusion_blocks_queue_and_canary_names() -> None:
    query = apply_synthetic_hr_exclusion({"deleted_at": None})
    rendered = str(query)
    assert "Queue New Hire" in rendered
    assert "G5UploadCanary" in rendered
    assert "Preview Dispatch Driver" in rendered
    assert "track_23_5_cert_seed" in rendered


def test_is_synthetic_hr_detects_queue_and_canary_literals() -> None:
    assert is_synthetic_hr({"name": "Queue New Hire abc-123"}) is True
    assert is_synthetic_hr({"name": "G5UploadCanary_1780403837"}) is True
    assert is_synthetic_hr({"name": "PYTEST bde2f3"}) is True
    assert is_synthetic_hr({"name": "Preview Dispatch Driver", "id": "driver-iter392"}) is True
    assert is_synthetic_hr({"name": "Allen Smathers", "track_23_5_cert_seed": True}) is True
    assert is_synthetic_hr({"name": "Alejandro Escobedo"}) is False


def test_incident_lifecycle_excludes_synthetic_incidents_from_capa_requirement() -> None:
    incidents = _Collection([
        {
            "id": "INC-1",
            "description": "Synthetic incident",
            "severity": "High",
            "osha_recordable": "Yes",
            "technical_record_classification": "synthetic_test",
            "truth_visibility_scope": "technical_audit_only",
        }
    ])
    corrective_actions = _Collection(count_map={"count": 0})
    db = _Db(incidents=incidents, corrective_actions=corrective_actions)

    out = asyncio.run(_detect_incident_lifecycle(db))

    assert out == []
    assert incidents.last_query is not None
    assert "technical_record_classification" in str(incidents.last_query)