"""GD-0013 — WAVE 4 population-count contract (scale-proof, shared patterns).

Proves the two shared Wave-4 repair patterns keep the canonical TOTAL truthful
regardless of the fixed page/read bound, for every representative population
size (below / at / above the old cap and a large future-scale population):

  Pattern A — capped list + count_documents total
    e.g. GET /trench-safety/assets: `count` = returned page/window length
    (bounded), `total` = count_documents(query) = TRUE population.

  Pattern B — streaming aggregation (no fixed cap)
    e.g. GET /trench-safety/public/overview: total_active_assets is computed by
    streaming the FULL cursor (async for), so it never truncates at a cap.

If a future population grows past the old bound, `total` (A) and the streamed
rollup (B) must still equal the real population — this is the fleet-units
(TD-0009) contract generalised across Wave 4.
"""
import asyncio
import pytest
from fastapi import APIRouter

from backend.routes.trench_safety.assets import register_asset_routes
from backend.routes.trench_safety.public import register_public_routes

OLD_ASSETS_BOUND = 2000
OLD_PUBLIC_BOUND = 5000


class _Cursor:
    def __init__(self, docs):
        self._docs = docs
        self._limit = None

    def sort(self, *a, **k):
        return self

    def limit(self, k):
        self._limit = k
        return self

    async def to_list(self, length=None):
        cap = length if length is not None else self._limit
        return self._docs[:cap] if cap else list(self._docs)

    def __aiter__(self):
        data = self._docs[: self._limit] if self._limit else self._docs

        async def _gen():
            for d in data:
                yield d

        return _gen()


class _Coll:
    def __init__(self, docs):
        self.docs = docs

    def find(self, query=None, projection=None):
        return _Cursor(self.docs)

    async def count_documents(self, query=None):
        return len(self.docs)


class _DB:
    def __init__(self, n):
        docs = [
            {"id": f"a{i}", "asset_id": f"TB-{i}", "is_active": True,
             "operational_status": "Available", "asset_type": "Trench Box"}
            for i in range(n)
        ]
        self.trench_safety_assets = _Coll(docs)


def _passthru(*a, **k):
    return None


def _asset_list_handler(db):
    router = APIRouter()
    register_asset_routes(
        router, db,
        require_admin=_passthru,
        require_safety_or_admin=_passthru,
        require_any_portal=_passthru,
    )
    return next(r.endpoint for r in router.routes
                if getattr(r, "path", "") == "/trench-safety/assets")


def _public_overview_handler(db):
    router = APIRouter()
    register_public_routes(router, db)
    return next(r.endpoint for r in router.routes
                if getattr(r, "path", "").endswith("/public/overview"))


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


@pytest.mark.parametrize("n", [0, 5, OLD_ASSETS_BOUND, OLD_ASSETS_BOUND + 1, 6000])
def test_pattern_a_capped_list_true_total(n):
    """count = bounded page length; total = true population (count_documents)."""
    handler = _asset_list_handler(_DB(n))
    out = _run(handler(asset_type=None, operational_status=None, condition=None,
                       project_id=None, needs_review=None, include_retired=False,
                       q=None, _actor=None))
    assert out["total"] == n, "total must equal the full population at every scale"
    assert out["count"] == min(n, OLD_ASSETS_BOUND), "count is the bounded window length"
    assert len(out["items"]) == min(n, OLD_ASSETS_BOUND)


@pytest.mark.parametrize("n", [0, 5, OLD_PUBLIC_BOUND, OLD_PUBLIC_BOUND + 1, 7000])
def test_pattern_b_streaming_aggregation_true_total(n):
    """Streamed rollup total_active_assets must equal the full population."""
    handler = _public_overview_handler(_DB(n))
    out = _run(handler())
    assert out["total_active_assets"] == n, "streamed total must not truncate at any cap"
    assert out["counts_by_status"]["Available"] == n, "streamed breakdown covers full population"
    assert out["counts_by_type"]["Trench Box"] == n
