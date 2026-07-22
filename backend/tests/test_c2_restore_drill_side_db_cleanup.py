from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from restore_drill import _restore_side_db


class _FakeCollection:
    def __init__(self) -> None:
        self.deleted_queries = []
        self.inserted_docs = []
        self.drop_called = False

    def delete_many(self, query):
        self.deleted_queries.append(query)

    def insert_many(self, docs, ordered=False):
        self.inserted_docs.append({"docs": list(docs), "ordered": ordered})

    def drop(self):
        self.drop_called = True
        raise AssertionError("drop() should not be used by restore drill")


class _FakeDatabase:
    def __init__(self) -> None:
        self.collections = {}

    def __getitem__(self, name: str):
        if name not in self.collections:
            self.collections[name] = _FakeCollection()
        return self.collections[name]


class _FakeClient:
    latest = None

    def __init__(self, *_args, **_kwargs) -> None:
        self.databases = {}
        _FakeClient.latest = self

    def __getitem__(self, name: str):
        if name not in self.databases:
            self.databases[name] = _FakeDatabase()
        return self.databases[name]

    def close(self):
        return None


def test_restore_side_db_uses_delete_many_instead_of_drop(monkeypatch, tmp_path: Path):
    coll_dir = tmp_path / "incident-case-public-submissions" / "json"
    coll_dir.mkdir(parents=True)
    (coll_dir / "row_000000.json").write_text(
        json.dumps({"id": "case-1", "summary": "restore proof"}),
        encoding="utf-8",
    )

    monkeypatch.setattr("pymongo.MongoClient", _FakeClient)

    counters = _restore_side_db(tmp_path, "mongodb://example.invalid", "masci_restore_drill_test", verbose=False)

    fake_client = _FakeClient.latest
    assert fake_client is not None
    fake_db = fake_client.databases["masci_restore_drill_test"]
    fake_coll = fake_db.collections["incident_case_public_submissions"]

    assert counters["incident_case_public_submissions"] == {
        "inserted": 1,
        "skipped_bad": 0,
        "files_seen": 1,
    }
    assert fake_coll.deleted_queries == [{}]
    assert fake_coll.drop_called is False
    assert fake_coll.inserted_docs == [
        {"docs": [{"id": "case-1", "summary": "restore proof"}], "ordered": False}
    ]