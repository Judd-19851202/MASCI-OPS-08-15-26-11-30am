"""TD-0009 — /api/fleet/units population-count contract (scale-proof).

The endpoint returns `count` = returned PAGE length (backward-compatible) and
`total` = TRUE canonical fleet-unit population via count_documents. This proves
the fleet TOTAL stays correct regardless of response page size, so the KPI never
silently caps as the fleet grows past the page limit. Scale: 3 / 149 / limit+1 /
500+ / 6000.
"""
import asyncio
import pytest
from backend.routes.fleet_ops import build_router

FLEET_CATEGORY = "Dump Trucks"


class _Cursor:
    def __init__(self, docs):
        self._docs = docs
        self._limit = None

    def limit(self, k):
        self._limit = k
        return self

    def __aiter__(self):
        data = self._docs[: self._limit] if self._limit else self._docs

        async def _gen():
            for d in data:
                yield d

        return _gen()


class _Coll:
    def __init__(self, docs):
        self.docs = docs

    def find(self, query, projection=None):
        return _Cursor(self.docs)

    async def count_documents(self, query):
        return len(self.docs)


class _DB:
    def __init__(self, n):
        docs = [
            {"id": f"u{i}", "unit_number": f"T{i}", "category": FLEET_CATEGORY,
             "plate": f"P{i}", "vin_serial_number": f"V{i}", "make_model": "Mack",
             "year": 2020, "display_label": f"T{i}", "company": "MASCI"}
            for i in range(n)
        ]
        self.equipment_master = _Coll(docs)


def _passthru(*a, **k):
    return None


def _units_handler(db):
    router = build_router(db, _passthru, _passthru, _passthru, _passthru, _passthru)
    return next(r.endpoint for r in router.routes if getattr(r, "path", "") == "/api/fleet/units")


def _call(n, limit):
    handler = _units_handler(_DB(n))
    return asyncio.get_event_loop().run_until_complete(
        handler(q=None, unit_type=None, limit=limit, _actor=None)
    )


@pytest.mark.parametrize("n,limit", [(3, 200), (149, 200), (201, 200), (600, 500), (6000, 500)])
def test_total_is_true_population_regardless_of_page_size(n, limit):
    out = _call(n, limit)
    effective_limit = max(1, min(500, limit))
    assert out["total"] == n, "total must equal the full canonical population"
    assert out["count"] == min(n, effective_limit), "count is the returned page length"
    assert len(out["units"]) == min(n, effective_limit)
    assert out["page_size"] == len(out["units"])
    # The KPI (total) must never be capped by the page limit.
    if n > effective_limit:
        assert out["total"] > out["count"]
