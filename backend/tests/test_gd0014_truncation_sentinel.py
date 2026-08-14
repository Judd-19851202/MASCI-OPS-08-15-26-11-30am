"""GD-0014 — population/truncation contract sentinel (thin wrapper over the
canonical guard in backend/lib/truth_population_guard.py — ONE guard owner).

count = rows returned in this response/page; total = complete canonical population
under the SAME filters. Flags any served function that returns a population
count/total := len(fixed-cap read) with NO canonical total. Contract-aware
(A population / B exact-bounded / C page-only / D internal). Exceptions are
explicit, machine-readable and justified in the canonical module's EXCEPTIONS.
"""
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path("/app/backend")))
from lib.truth_population_guard import (  # noqa: E402
    offenders_in, scan_population_contract, served_backend_files, EXCEPTIONS,
)

BAD = '''
async def list_things(db):
    docs = await db.things.find({"active": True}).to_list(200)
    return {"items": docs, "count": len(docs)}
'''
GOOD_TOTAL = '''
async def list_things(db):
    q = {"active": True}
    docs = await db.things.find(q).to_list(200)
    return {"items": docs, "count": len(docs), "total": await db.things.count_documents(q)}
'''
GOOD_EXACT = '''
async def by_ids(db, ids):
    docs = await db.things.find({"id": {"$in": ids}}).to_list(len(ids))
    return {"items": docs, "count": len(docs)}
'''
GOOD_PAGE = '''
async def list_things(db, limit: int = 50):
    docs = await db.things.find({}).limit(limit).to_list(limit)
    return {"items": docs, "count": len(docs)}
'''
GOOD_STREAM = '''
async def summary(db):
    total = 0
    async for d in db.things.find({}):
        total += 1
    return {"total": total}
'''


def test_sentinel_flags_old_defect_pattern():
    assert offenders_in(BAD), "sentinel MUST flag fixed-cap count:=len(read) with no canonical total"


@pytest.mark.parametrize("code", [GOOD_TOTAL, GOOD_EXACT, GOOD_PAGE, GOOD_STREAM])
def test_sentinel_passes_repaired_patterns(code):
    assert offenders_in(code) == [], "sentinel must NOT flag count_documents/to_list(len)/request-page/streamed forms"


def test_every_exception_is_fully_justified():
    for k, v in EXCEPTIONS.items():
        assert "::" in k, f"exception key must be source::site — {k}"
        assert v.get("class") in {"A", "B", "C", "D"}, f"exception {k} missing class"
        assert v.get("reason"), f"exception {k} missing justification"


def test_no_unexplained_truncation_offenders_in_served_code():
    violations = scan_population_contract(served_backend_files(Path("/app")))
    assert not violations, "GD-0014 offenders (repair or add a justified EXCEPTIONS entry):\n" + \
        "\n".join(sorted(v.message() for v in violations))
