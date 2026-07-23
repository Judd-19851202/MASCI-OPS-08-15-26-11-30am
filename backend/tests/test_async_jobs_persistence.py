import pytest

from lib.runtime_cache import InMemoryRuntimeCache
import lib.async_jobs as async_jobs


class _FakeCollection:
    def __init__(self):
        self.docs = {}

    async def create_index(self, *args, **kwargs):
        return None

    async def replace_one(self, query, doc, upsert=False):
        self.docs[query["job_id"]] = dict(doc)

    async def find_one(self, query, projection=None):
        doc = self.docs.get(query["job_id"])
        if not doc:
            return None
        out = dict(doc)
        projection = projection or {}
        for key, value in projection.items():
          if value == 0:
            out.pop(key, None)
        return out


@pytest.mark.asyncio
async def test_async_job_meta_survives_cache_miss(monkeypatch):
    meta_coll = _FakeCollection()
    binary_coll = _FakeCollection()
    cache_a = InMemoryRuntimeCache()
    cache_b = InMemoryRuntimeCache()
    current_cache = {"value": cache_a}

    monkeypatch.setattr(async_jobs, "get_runtime_cache", lambda: current_cache["value"])

    async def fake_meta():
        return meta_coll

    async def fake_binary():
        return binary_coll

    monkeypatch.setattr(async_jobs, "_get_job_meta_collection", fake_meta)
    monkeypatch.setattr(async_jobs, "_get_job_binary_collection", fake_binary)

    created = await async_jobs.create_async_job("daily_summary_draft")
    job_id = str(created["job_id"])

    current_cache["value"] = cache_b
    loaded = await async_jobs.get_async_job(job_id)

    assert loaded is not None
    assert loaded["job_id"] == job_id
    assert loaded["status"] == "queued"


@pytest.mark.asyncio
async def test_async_job_binary_survives_memory_only_process(monkeypatch):
    meta_coll = _FakeCollection()
    binary_coll = _FakeCollection()
    cache = InMemoryRuntimeCache()

    monkeypatch.setattr(async_jobs, "get_runtime_cache", lambda: cache)

    async def fake_meta():
        return meta_coll

    async def fake_binary():
        return binary_coll

    monkeypatch.setattr(async_jobs, "_get_job_meta_collection", fake_meta)
    monkeypatch.setattr(async_jobs, "_get_job_binary_collection", fake_binary)

    created = await async_jobs.create_async_job("daily_report_pdf", result_type="binary")
    job_id = str(created["job_id"])
    await async_jobs.complete_async_job_binary(
        job_id,
        content=b"%PDF-test",
        media_type="application/pdf",
        filename="test.pdf",
        result_meta={"kind": "pdf"},
    )

    async with async_jobs._BINARY_LOCK:
        async_jobs._BINARY_RESULTS.pop(job_id, None)

    resolved = await async_jobs.get_async_job_binary_result(job_id, created["result_token"])

    assert resolved is not None
    meta, stored = resolved
    assert meta["status"] == "completed"
    assert stored["filename"] == "test.pdf"
    assert stored["content"] == b"%PDF-test"