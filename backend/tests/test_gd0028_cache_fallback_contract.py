"""GD-0028 — Cache / Fallback / Derived truth invariants + failure injection (Wave 8).

Guards the canonical runtime cache (lib.runtime_cache) so derived/cached truth cannot
silently override canonical source:
  - a cache entry past its TTL is NOT served (stale-over-current = 0);
  - on miss/expiry the canonical builder runs and its value wins (fallback/cache is not
    canonical — the source is);
  - delete/invalidate forces a rebuild (recovery restores canonical truth);
  - distinct (principal-scoped) keys never collide (cross-principal leakage = 0 at the
    cache mechanism; callers MUST scope keys by principal).

Also contract-checks the frontend truthful-data-state owner keeps degraded states distinct
(unknown/stale/unavailable/no_access/error are NOT rendered as 0 — no unlabeled degraded truth).
"""
import asyncio
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.runtime_cache import InMemoryRuntimeCache, get_or_set_runtime_json, get_runtime_cache


@pytest.mark.asyncio
async def test_expired_entry_not_served_stale_over_current():
    c = InMemoryRuntimeCache()
    await c.set_json("k", {"v": 1}, ttl_seconds=1)
    assert await c.get_json("k") == {"v": 1}
    # force expiry (a past positive epoch; 0.0 means "no expiry" by contract)
    c._store["k"]["expires_at"] = 1.0
    assert await c.get_json("k") is None  # stale entry is dropped, never served


@pytest.mark.asyncio
async def test_builder_runs_on_miss_and_source_wins():
    c = get_runtime_cache()
    await c.delete("gd0028:test")
    calls = {"n": 0}

    async def builder():
        calls["n"] += 1
        return {"canonical": calls["n"]}

    first = await get_or_set_runtime_json("gd0028:test", ttl_seconds=60, builder=builder)
    assert first == {"canonical": 1} and calls["n"] == 1
    # second call served from cache (no rebuild) — but it is the SAME canonical value
    second = await get_or_set_runtime_json("gd0028:test", ttl_seconds=60, builder=builder)
    assert second == {"canonical": 1} and calls["n"] == 1
    await c.delete("gd0028:test")


@pytest.mark.asyncio
async def test_delete_forces_recovery_rebuild():
    c = get_runtime_cache()
    await c.delete("gd0028:recover")
    seq = {"n": 0}

    async def builder():
        seq["n"] += 1
        return seq["n"]

    assert await get_or_set_runtime_json("gd0028:recover", ttl_seconds=60, builder=builder) == 1
    await c.delete("gd0028:recover")  # invalidate
    # after invalidation the canonical builder runs again (recovery restores truth)
    assert await get_or_set_runtime_json("gd0028:recover", ttl_seconds=60, builder=builder) == 2
    await c.delete("gd0028:recover")


@pytest.mark.asyncio
async def test_distinct_principal_keys_do_not_collide():
    c = InMemoryRuntimeCache()
    await c.set_json("user:A:summary", {"owner": "A"}, ttl_seconds=60)
    await c.set_json("user:B:summary", {"owner": "B"}, ttl_seconds=60)
    assert (await c.get_json("user:A:summary"))["owner"] == "A"
    assert (await c.get_json("user:B:summary"))["owner"] == "B"  # no cross-principal leakage


def test_truthful_data_state_keeps_degraded_states_distinct():
    # Frontend owner must NOT collapse unknown/stale/unavailable into 0 or into a value.
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "..", "frontend", "src", "lib", "truthfulDataState.js")
    src = open(os.path.abspath(path)).read()
    for state in ("LOADING", "TRUE_ZERO", "EMPTY", "UNKNOWN", "UNAVAILABLE", "STALE", "NO_ACCESS", "ERROR"):
        assert state in src, f"missing governed state {state}"
    # degraded states render placeholder '—', not a fabricated 0
    assert re.search(r"STALE[\s\S]*?displayValue:\s*\"—\"", src)
    assert re.search(r"UNKNOWN[\s\S]*?displayValue:\s*\"—\"", src)
    # only TRUE_ZERO renders "0"
    assert re.search(r"TRUE_ZERO,\s*displayValue:\s*\"0\"", src)
