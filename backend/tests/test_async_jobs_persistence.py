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

    async def delete_one(self, query):
        self.docs.pop(query["job_id"], None)

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


@pytest.mark.asyncio
async def test_async_job_json_size_guard_fails_truthfully(monkeypatch):
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

    created = await async_jobs.create_async_job("daily_summary_draft")
    job_id = str(created["job_id"])
    huge = {"summary": "x" * (async_jobs.MAX_JSON_RESULT_BYTES + 1024)}

    meta = await async_jobs.complete_async_job_json(job_id, huge)

    assert meta is not None
    assert meta["status"] == "failed"
    assert meta["error"]["code"] == "result_too_large"


@pytest.mark.asyncio
async def test_async_job_binary_size_guard_fails_truthfully(monkeypatch):
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

    meta = await async_jobs.complete_async_job_binary(
        job_id,
        content=b"x" * (async_jobs.MAX_BINARY_RESULT_BYTES + 1),
        media_type="application/pdf",
        filename="too-big.pdf",
    )

    assert meta is not None
    assert meta["status"] == "failed"
    assert meta["error"]["code"] == "binary_result_too_large"


@pytest.mark.asyncio
async def test_terminal_completion_cannot_be_overwritten(monkeypatch):
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

    created = await async_jobs.create_async_job("daily_summary_draft")
    job_id = str(created["job_id"])
    first = await async_jobs.complete_async_job_json(job_id, {"summary": "newest"})
    second = await async_jobs.complete_async_job_json(job_id, {"summary": "older worker"})

    assert first is not None
    assert second is not None
    assert second["status"] == "completed"
    assert second["result"] == {"summary": "newest"}


@pytest.mark.asyncio
async def test_malformed_persisted_meta_is_rejected(monkeypatch):
    meta_coll = _FakeCollection()
    binary_coll = _FakeCollection()
    cache = InMemoryRuntimeCache()
    current_cache = {"value": cache}

    monkeypatch.setattr(async_jobs, "get_runtime_cache", lambda: current_cache["value"])
    async def fake_meta():
        return meta_coll
    async def fake_binary():
        return binary_coll
    monkeypatch.setattr(async_jobs, "_get_job_meta_collection", fake_meta)
    monkeypatch.setattr(async_jobs, "_get_job_binary_collection", fake_binary)

    job_id = "broken-job"
    meta_coll.docs[job_id] = {"job_id": job_id, "status": "completed", "result_type": "json", "result": object()}

    loaded = await async_jobs.get_async_job(job_id)

    assert loaded is None


@pytest.mark.asyncio
async def test_expired_job_is_not_returned(monkeypatch):
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

    created = await async_jobs.create_async_job("daily_summary_draft")
    job_id = str(created["job_id"])
    meta_coll.docs[job_id]["expires_at"] = "2000-01-01T00:00:00+00:00"
    await cache.delete(f"async-job:{job_id}:meta")

    loaded = await async_jobs.get_async_job(job_id)

    assert loaded is None