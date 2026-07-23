from __future__ import annotations

from datetime import datetime, timezone

import pytest

from services.photo_intelligence import pipeline


class _FakeCursor:
    def __init__(self, rows):
        self._rows = list(rows)

    async def to_list(self, _limit):
        return list(self._rows)


class _FakeCollection:
    def __init__(self, docs=None):
        self.docs = list(docs or [])

    def _match(self, doc, query):
        for k, v in query.items():
            if isinstance(v, dict) and "$in" in v:
                if doc.get(k) not in v["$in"]:
                    return False
            elif doc.get(k) != v:
                return False
        return True

    def _raw_find_one(self, query):
        for doc in self.docs:
            if self._match(doc, query):
                return doc
        return None

    async def find_one(self, query, projection=None):
        doc = self._raw_find_one(query)
        if doc is not None:
            return {k: vv for k, vv in doc.items() if k != "_id"}
        return None

    def find(self, query, projection=None):
        rows = []
        for doc in self.docs:
            if self._match(doc, query):
                rows.append({kk: vv for kk, vv in doc.items() if kk != "_id"})
        return _FakeCursor(rows)

    async def update_one(self, query, update, upsert=False):
        doc = self._raw_find_one(query)
        if doc is None:
            doc = dict(query)
            self.docs.append(doc)
        if "$set" in update:
            doc.update(update["$set"])
        if "$setOnInsert" in update:
            for k, v in update["$setOnInsert"].items():
                doc.setdefault(k, v)
        if "$inc" in update:
            for k, v in update["$inc"].items():
                doc[k] = int(doc.get(k) or 0) + int(v)


class _FakeDb:
    def __init__(self):
        self.daily_reports = _FakeCollection([
            {
                "doc_id": "DR-TEST-1",
                "id": "dr-test-1",
                "photos": ["photo://bucket/a.jpg", "photo://bucket/b.jpg"],
                "ai_accepted_summary_meta": {
                    "source": "ai",
                    "accepted_at": datetime.now(timezone.utc).isoformat(),
                    "photo_intelligence_status": "complete",
                    "photo_observations": [{"description": "stale"}],
                },
                "photo_intelligence_status": "complete",
                "photo_observations": [{"description": "stale"}],
            }
        ])
        self.dr_v1_photo_intel_jobs = _FakeCollection([
            {"report_id": "DR-TEST-1", "photo_id": "a", "status": "unavailable"},
            {"report_id": "DR-TEST-1", "photo_id": "b", "status": "unavailable"},
        ])
        self.dr_v2_photo_intelligence = _FakeCollection([
            {"report_id": "DR-TEST-1", "photo_id": "a", "analysis_status": "unavailable", "observations": []},
            {"report_id": "DR-TEST-1", "photo_id": "b", "analysis_status": "unavailable", "observations": []},
        ])

    def __getitem__(self, name):
        return getattr(self, name)


@pytest.mark.asyncio
async def test_process_report_syncs_canonical_photo_status(monkeypatch):
    db = _FakeDb()

    async def fake_enqueue(_db, _report):
        return {"ok": True, "enqueued": 0, "photos": 2}

    async def fake_claim(_db, **_kwargs):
        return True

    async def fake_analyze(_db, **_kwargs):
        return {"ok": True, "ai_available": False}

    async def fake_mark(_db, **kwargs):
        for doc in db.dr_v1_photo_intel_jobs.docs:
            if doc.get("report_id") == kwargs.get("report_id") and doc.get("photo_id") == kwargs.get("photo_id"):
                doc["status"] = kwargs.get("status")

    monkeypatch.setattr(pipeline, "enqueue_report", fake_enqueue)
    monkeypatch.setattr(pipeline, "_extract_photo_refs", lambda report: [
        {"photo_id": "a", "ref": "photo://bucket/a.jpg", "source": "photos"},
        {"photo_id": "b", "ref": "photo://bucket/b.jpg", "source": "photos"},
    ])
    monkeypatch.setattr(pipeline, "_claim_job", fake_claim)
    monkeypatch.setattr(pipeline, "_analyze_one", fake_analyze)
    monkeypatch.setattr(pipeline, "_mark_job", fake_mark)
    async def fake_list_report_intelligence(_db, *, report_id):
        return {
            "report_id": report_id,
            "status": "complete_with_some_failures",
            "observations": [],
        }
    monkeypatch.setattr(pipeline, "list_report_intelligence", fake_list_report_intelligence)

    result = await pipeline.process_report(db, {"doc_id": "DR-TEST-1", "project_number": "X", "report_date": "2026-07-23", "photos": ["photo://bucket/a.jpg", "photo://bucket/b.jpg"]})

    assert result["ok"] is True
    saved = await db.daily_reports.find_one({"doc_id": "DR-TEST-1"})
    assert saved["photo_intelligence_status"] == "complete_with_some_failures"
    assert saved["photo_observations"] == []
    assert saved["ai_accepted_summary_meta"]["photo_intelligence_status"] == "complete_with_some_failures"
    assert saved["ai_accepted_summary_meta"]["photo_observations"] == []