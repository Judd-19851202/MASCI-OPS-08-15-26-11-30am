import pytest

from routes.usage_analytics import ensure_usage_indexes
from services.photo_intelligence.analyzer import analyze_photo


class _UsageEventsCollection:
    def __init__(self):
        self.calls = []

    async def create_index(self, keys, **kwargs):
        self.calls.append((keys, kwargs))
        return "ok"


class _UsageDb:
    def __init__(self):
        self.usage_events = _UsageEventsCollection()


@pytest.mark.asyncio
async def test_usage_indexes_include_viewport_summary_index():
    db = _UsageDb()
    await ensure_usage_indexes(db)
    assert any(keys == [("viewport", 1), ("at", -1)] for keys, _ in db.usage_events.calls)


class _RetryGateway:
    def __init__(self):
        self.calls = 0

    async def dispatch_vision(self, **_kwargs):
        self.calls += 1
        if self.calls < 3:
            raise RuntimeError("transient")
        return {"ok": True}


@pytest.mark.asyncio
async def test_analyze_photo_retries_transient_vision_failures(monkeypatch):
    async def _fast_sleep(_seconds):
        return None

    monkeypatch.setattr("services.photo_intelligence.analyzer.asyncio.sleep", _fast_sleep)
    gw = _RetryGateway()
    env = await analyze_photo(
        gateway=gw,
        session_id="s1",
        photo_ref="p1",
        images=["abc"],
        draft_context={"project": "Demo"},
    )
    assert env == {"ok": True}
    assert gw.calls == 3