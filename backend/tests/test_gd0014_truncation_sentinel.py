"""GD-0014 — PERMANENT TRUNCATION SENTINEL (contract-aware, deterministic).

Truth contract (canonical): in a population-bearing read response,
  count = rows returned in THIS response/page
  total = complete canonical population under the SAME filters.

This guard walks served backend route/service source and flags any function that
returns a population-bearing `count/total := len(<fixed-cap bounded read>)` with
NO canonical total (count_documents / estimated_document_count / $count / full
stream) in the same function. That is the fleet-units (TD-0009) defect class.

Classification (contract-aware, not a dumb grep):
  A POPULATION/PAGINATED  -> must expose a truthful total (count_documents) OR stream full population.
  B EXACT BOUNDED SET     -> bound derived from len(ids)/known set -> cannot truncate.
  C PAGE-ONLY/NON-POP     -> request-controlled bound (page) — count means returned rows.
  D INTERNAL/NON-SERVED   -> backend/scripts/* (not user/API truth).
A site is an OFFENDER only when it is class-A-shaped (fixed cap + total-like len)
AND lacks a canonical total. Every allowed exception is explicit + justified below.
"""
import re
from pathlib import Path
import pytest

BACKEND = Path("/app/backend")
PAGEQ = re.compile(r"page|returned|batch|sample|window|shown|per_page|dedup|override|slice|display|preview|recent|\btop\b|shard|chunk|scan|_win\b", re.I)
TOTALISH = re.compile(r"total|count|size|\bnum\b|tally|\bsum\b|headcount|fleet|roster|population|records|entries|active_|open_", re.I)
CANON_TOTAL = re.compile(r"count_documents|estimated_document_count|\$count|to_list\(\s*length\s*=\s*None\s*\)|to_list\(\s*None\s*\)")
_ARG = r"(?:length\s*=\s*)?([^\n]*?)"
FIXED_LIMIT = re.compile(r"\.(?:to_list\(\s*" + _ARG + r"\s*\)|limit\(\s*" + _ARG + r"\s*\))")

# Machine-readable, justified exceptions. class ∈ {B,C,D}. Each is a proven non-D.
EXCEPTIONS = {
    "backend/routes/operations_actions/api.py::list": {
        "class": "A", "reason": "already exposes canonical total via $count aggregate (L558 'total': total)."},
    "backend/routes/trench_safety/reports.py::open_repairs": {
        "class": "A", "reason": "open_repairs is itself count_documents(...), not len() of a capped read."},
    "backend/routes/governance.py::match_count": {
        "class": "C", "reason": "match_count = per-name ambiguity cardinality (len of a small name_index bucket), not a population total."},
    "backend/services/operations_control/control_plane.py::capture_count": {
        "class": "C", "reason": "capture_count = size of an intentional recent-10 evidence bundle window (sibling reads use explicit limit 3/10/20)."},
    "backend/services/cost_codes/oppc_execution.py::report_count": {
        "class": "B", "reason": "report_count bounded structurally by a single project + single ISO week query window; now streamed (to_list(length=None))."},
}


def _fixed_bound(arg):
    a = (arg or "").strip()
    if not a or a == "None" or re.search(r"\bmin\s*\(", a) or re.search(r"\blen\s*\(", a):
        return None
    nums = re.findall(r"\b(\d{1,9})\b", a)
    core = re.sub(r"\bif\b|\belse\b|\band\b|\bor\b", " ", a)
    if nums and not re.search(r"[A-Za-z_]", core):
        return int(max(nums, key=int))
    if nums and re.search(r"\bif\b.*\belse\b", a):
        return int(max(nums, key=int))
    return None


def _funcs(lines):
    heads = [(i, len(lines[i]) - len(lines[i].lstrip()))
             for i, l in enumerate(lines) if re.match(r"\s*(async\s+def|def)\s", l)]
    spans = []
    for s, ind in heads:
        e = len(lines)
        for k in range(s + 1, len(lines)):
            ss = lines[k]
            if ss.strip() and (len(ss) - len(ss.lstrip())) <= ind and re.match(r"\s*(async\s+def|def|class)\s", ss):
                e = k; break
        spans.append((s, e, ind))
    for s, e, ind in spans:
        # SHALLOW body: exclude nested def blocks so a route-register closure does
        # not absorb its inner endpoints' variables (prevents cross-endpoint collisions).
        nested = [(ns, ne) for (ns, ne, ni) in spans if ns > s and ns < e and ni > ind]
        keep = []
        for ln in range(s, e):
            if any(a <= ln < b for (a, b) in nested):
                continue
            keep.append(lines[ln])
        name = re.match(r"\s*(?:async\s+def|def)\s+([A-Za-z_]\w*)", lines[s])
        yield (name.group(1) if name else "?"), "\n".join(keep)


def _bounded_vars(body):
    out = {}
    for m in re.finditer(r"^\s*([A-Za-z_]\w*)\s*=\s*.*?" + FIXED_LIMIT.pattern, body, re.M):
        b = _fixed_bound(m.group(2) if m.group(2) is not None else m.group(3))
        if b is not None:
            out[m.group(1)] = b
    for m in re.finditer(r"([A-Za-z_]\w*)\s*=\s*\[[^\]]*?\bfor\b[^\]]*?" + FIXED_LIMIT.pattern + r"[^\]]*\]", body):
        b = _fixed_bound(m.group(2) if m.group(2) is not None else m.group(3))
        if b is not None:
            out[m.group(1)] = b
    for m in re.finditer(r"async\s+for\s+\w+\s+in\s+[^\n]*?" + FIXED_LIMIT.pattern + r"[^\n]*:\s*\n(?:[^\n]*\n){0,40}", body):
        b = _fixed_bound(m.group(1) if m.group(1) is not None else m.group(2))
        for am in re.finditer(r"([A-Za-z_]\w*)\.append\(", m.group(0)):
            if b is not None:
                out[am.group(1)] = b
    for _ in range(3):
        for m in re.finditer(r"^\s*([A-Za-z_]\w*)\s*=\s*([^\n]+)$", body, re.M):
            lhs, rhs = m.group(1), m.group(2)
            if lhs in out:
                continue
            for v, b in list(out.items()):
                if re.search(r"\b%s\b" % re.escape(v), rhs) and not rhs.strip().startswith("len("):
                    out[lhs] = b; break
    return out


def _offenders_in(body):
    """Return list of (key, var) offending ties in a function body (no canonical total)."""
    if CANON_TOTAL.search(body):
        return []
    bv = _bounded_vars(body)
    if not bv:
        return []
    hits = []
    for m in re.finditer(r"[\"']([A-Za-z_]\w*)[\"']\s*:\s*len\(\s*([A-Za-z_]\w*)\s*\)", body):
        key, v = m.group(1), m.group(2)
        if v in bv and TOTALISH.search(key) and not PAGEQ.search(key):
            hits.append((key, v))
    for m in re.finditer(r"^\s*([A-Za-z_]\w*)\s*=\s*len\(\s*([A-Za-z_]\w*)\s*\)", body, re.M):
        key, v = m.group(1), m.group(2)
        if v in bv and TOTALISH.search(key) and not PAGEQ.search(key):
            hits.append((key, v))
    return hits


# ---------- fixtures proving the guard direction ----------
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
    assert _offenders_in(BAD), "sentinel MUST flag fixed-cap count:=len(read) with no canonical total"


@pytest.mark.parametrize("code", [GOOD_TOTAL, GOOD_EXACT, GOOD_PAGE, GOOD_STREAM])
def test_sentinel_passes_repaired_patterns(code):
    assert _offenders_in(code) == [], "sentinel must NOT flag count_documents/to_list(len)/request-page/streamed forms"


def test_no_unexplained_truncation_offenders_in_served_code():
    offenders = []
    for py in BACKEND.rglob("*.py"):
        s = str(py)
        if "/tests/" in s or "__pycache__" in s or "/scripts/" in s:
            continue
        rel = str(py.relative_to("/app"))
        lines = py.read_text(errors="ignore").splitlines()
        for fn, body in _funcs(lines):
            for key, var in _offenders_in(body):
                exc_key = "%s::%s" % (rel, fn)
                # allow by function name or by the total-like key alias
                allowed = exc_key in EXCEPTIONS or any(
                    k.startswith(rel + "::") and (k.endswith("::" + fn) or k.endswith("::" + key))
                    for k in EXCEPTIONS)
                if not allowed:
                    offenders.append("%s :: %s  ('%s' := len(%s))" % (rel, fn, key, var))
    assert not offenders, "Unexplained truncation-of-total offenders (add a justified EXCEPTIONS entry or repair):\n" + "\n".join(sorted(set(offenders)))
