"""GD-0015 — items/total filter-drift audit (thin wrapper over the canonical
guard in backend/lib/truth_population_guard.py — ONE guard owner).

A canonical `total` computed from a broader/narrower query than the returned
`items` is another form of lying. For the items+total pairing on a collection
handle, the population-total filter MUST equal the items filter. Explicitly
narrowed metrics ({**base}, status:"active") and governed different-scope sites
(EXCEPTIONS) are allowed.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path("/app/backend")))
from lib.truth_population_guard import (  # noqa: E402
    filter_drift_in, scan_filter_drift, served_backend_files,
)

BAD_DRIFT = '''
async def f(db):
    docs = await db.x.find({"active": True}).to_list(200)
    return {"items": docs, "count": len(docs), "total": await db.x.count_documents({})}
'''
GOOD_SAME = '''
async def f(db):
    q = {"active": True}
    docs = await db.x.find(q).to_list(200)
    return {"items": docs, "count": len(docs), "total": await db.x.count_documents(q)}
'''


def test_drift_helper_flags_broader_total():
    assert filter_drift_in(BAD_DRIFT), "must flag total filter {} != items filter {active:true}"


def test_drift_helper_passes_same_filter():
    assert filter_drift_in(GOOD_SAME) == [], "identical items/total filter must pass"


def test_no_filter_drift_in_served_code():
    violations = scan_filter_drift(served_backend_files(Path("/app")))
    assert not violations, "GD-0015 filter drift (align total filter to items, or add a governed EXCEPTIONS entry):\n" + \
        "\n".join(sorted(v.message() for v in violations))
