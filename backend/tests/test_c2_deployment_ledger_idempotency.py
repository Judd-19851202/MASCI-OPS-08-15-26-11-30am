from __future__ import annotations

from datetime import datetime, timezone

import pytest

from routes.admin_deployment_ledger import write_snapshot_doc


class _FakeCollection:
    def __init__(self) -> None:
        self.docs = []

    async def create_index(self, *args, **kwargs):
        return None

    async def update_one(self, filter_doc, update_doc, upsert=False):
        verification_id = filter_doc.get("verification_id")
        for row in self.docs:
            if row.get("verification_id") == verification_id:
                return None
        if upsert:
            self.docs.append(dict(update_doc.get("$setOnInsert") or {}))
        return None

    async def insert_one(self, doc):
        self.docs.append(dict(doc))
        return None


class _FakeDb:
    def __init__(self) -> None:
        self._collections = {"deployment_decisions": _FakeCollection()}

    def __getitem__(self, key):
        return self._collections[key]


@pytest.mark.asyncio
async def test_write_snapshot_doc_is_idempotent_for_same_verification_id():
    db = _FakeDb()
    body = {
        "verification_id": "verify-1",
        "decision": "pass",
        "commit": "abc123",
        "backend_runtime_commit": "abc123",
        "frontend_build_commit": "abc123",
        "intended_release_commit": "abc123",
        "environment": "preview",
        "operator": "test",
        "trust_score": 50,
        "trust_band": "red",
        "parity_result": True,
        "health_ok": True,
        "go_no_go": "GO",
        "source_hash": "hash123",
        "build_timestamp": datetime.now(timezone.utc).isoformat(),
    }

    first = await write_snapshot_doc(db, body)
    second = await write_snapshot_doc(db, body)

    assert first["ok"] is True
    assert second["ok"] is True
    assert len(db["deployment_decisions"].docs) == 1
    assert db["deployment_decisions"].docs[0]["verification_id"] == "verify-1"