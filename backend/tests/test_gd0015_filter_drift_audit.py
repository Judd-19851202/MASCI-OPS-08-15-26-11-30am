"""GD-0015 — Wave-4 FILTER-DRIFT AUDIT.

A canonical `total` computed from a broader/narrower query than the returned
`items` is another form of lying. This audit targets the items+total PAIRING only:
for every count_documents(X) on a collection handle H where the SAME function also
reads items via H.find(Y..), the population-total filter X MUST equal the items
filter Y. Standalone dashboard metric counts (functions with no matching H.find)
are a different contract and are out of scope. Explicitly-narrowed metrics
({**base, ...} or status:"active") are legitimate different scopes and are allowed.
"""
import re
from pathlib import Path

ROOT = Path("/app")

REPAIRED = [
    "backend/routes/field_leadership.py", "backend/routes/jha_acknowledgements.py",
    "backend/routes/field_revision.py", "backend/routes/promo_assets.py",
    "backend/routes/asset_spine.py", "backend/routes/job_photos.py",
    "backend/routes/enterprise_governance.py", "backend/routes/transportation_dispatch_gate.py",
    "backend/routes/transportation_orientation.py", "backend/routes/employee_records.py",
    "backend/routes/trench_safety/assets.py", "backend/routes/trench_safety/operations.py",
    "backend/routes/trench_safety/excavations.py", "backend/routes/trench_safety/report_distribution.py",
    "backend/routes/hr_portal.py", "backend/server.py", "backend/lib/transport_carrier_intelligence.py",
]

HANDLE = r"(db(?:\.[A-Za-z_]\w*|\[[^\]]+\]))"
# Only the population-total values I added in Wave-4: a return-dict key or a var
# named total / total_files / total_acknowledgements / current_count / history_count.
_TOTAL_KEYS = r'(?:total|total_files|total_acknowledgements|current_count|history_count)'
CD = re.compile(
    r'(?:["\']' + _TOTAL_KEYS + r'["\']\s*:\s*|(?:\b' + _TOTAL_KEYS + r')\s*=\s*)await\s+'
    + HANDLE + r"\.count_documents\(\s*(.+?)\s*\)", re.S)
FIND = re.compile(HANDLE + r"\.find\(\s*(.+?)\s*[,)]", re.S)


def _norm(s):
    return re.sub(r"\s+", " ", s or "").strip().rstrip(",")


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
        nested = [(ns, ne) for (ns, ne, ni) in spans if ns > s and ns < e and ni > ind]
        keep = [lines[ln] for ln in range(s, e) if not any(a <= ln < b for (a, b) in nested)]
        name = re.match(r"\s*(?:async\s+def|def)\s+([A-Za-z_]\w*)", lines[s])
        yield (name.group(1) if name else "?"), "\n".join(keep)


def test_repaired_totals_use_same_filter_as_items():
    drift = []
    for rel in REPAIRED:
        py = ROOT / rel
        lines = py.read_text(errors="ignore").splitlines()
        for fn, body in _funcs(lines):
            # find-filters per handle
            finds = {}
            for m in FIND.finditer(body):
                finds.setdefault(_norm(m.group(1)), set()).add(_norm(m.group(2)).split(", {")[0])
            for m in CD.finditer(body):
                h, x = _norm(m.group(1)), _norm(m.group(2))
                if h not in finds:
                    continue  # pure metric count on a collection not read for items here -> out of scope
                if x.startswith("{**") or '"status": "active"' in x or "'status': 'active'" in x:
                    continue  # explicitly narrowed/extended, different named metric
                yset = finds[h]
                ok = x in yset or any(x == y or (x and x in y) for y in yset)
                if not ok:
                    drift.append("%s :: %s [%s] total-filter '%s' != items-filter %s" % (
                        rel, fn, h, x[:70], sorted(yset)))
    assert not drift, "FILTER DRIFT (total vs items):\n" + "\n".join(sorted(set(drift)))
