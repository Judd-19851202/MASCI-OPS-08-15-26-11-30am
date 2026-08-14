"""Canonical Truth-Program population-truth guards (ONE guard owner).

GD-0014 — population/truncation contract sentinel.
GD-0015 — items/total filter-drift audit.

Both the pytest guards (test_gd0014_*, test_gd0015_*) AND the pre-Save release
gate (backend/scripts/verify_release_identity.py) import from THIS module so
there is exactly one implementation, one contract, one result.

Public API:
  offenders_in(body)                      -> GD-0014 ties in a function body
  filter_drift_in(body)                   -> GD-0015 (handle, total_filter, item_filters) drift tuples
  scan_population_contract(files)         -> [Violation]   (files: iterable of (label, source_text))
  scan_filter_drift(files)                -> [Violation]
  served_backend_files(repo_root)         -> iterable of (relpath, source_text)
  gate_violations(repo_root)              -> [str]         (formatted GD-0014/GD-0015 messages)
  EXCEPTIONS                              -> machine-readable governed exception registry
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, List, Tuple

# ── shared contract vocabulary ───────────────────────────────────────────────
PAGEQ = re.compile(r"page|returned|batch|sample|window|shown|per_page|dedup|override|slice|display|preview|recent|\btop\b|shard|chunk|scan|_win\b", re.I)
TOTALISH = re.compile(r"total|count|size|\bnum\b|tally|\bsum\b|headcount|fleet|roster|population|records|entries|active_|open_", re.I)
CANON_TOTAL = re.compile(r"count_documents|estimated_document_count|\$count|to_list\(\s*length\s*=\s*None\s*\)|to_list\(\s*None\s*\)")
_ARG = r"(?:length\s*=\s*)?([^\n]*?)"
FIXED_LIMIT = re.compile(r"\.(?:to_list\(\s*" + _ARG + r"\s*\)|limit\(\s*" + _ARG + r"\s*\))")

# ── GD-0015 pairing detection ────────────────────────────────────────────────
HANDLE = r"(db(?:\.[A-Za-z_]\w*|\[[^\]]+\]))"
_TOTAL_KEYS = r'(?:total|total_files|total_acknowledgements|current_count|history_count)'
CD = re.compile(
    r'(?:["\']' + _TOTAL_KEYS + r'["\']\s*:\s*|(?:\b' + _TOTAL_KEYS + r')\s*=\s*)await\s+'
    + HANDLE + r"\.count_documents\(\s*(.+?)\s*\)", re.S)
FIND = re.compile(HANDLE + r"\.find\(\s*(.+?)\s*[,)]", re.S)

# ── machine-readable governed exceptions (GD-0014). class ∈ {A,B,C,D}. ───────
EXCEPTIONS = {
    "backend/routes/operations_actions/api.py::list": {
        "class": "A", "reason": "already exposes canonical total via $count aggregate ('total': total)."},
    "backend/routes/trench_safety/reports.py::open_repairs": {
        "class": "A", "reason": "open_repairs is itself count_documents(...), not len() of a capped read."},
    "backend/routes/governance.py::match_count": {
        "class": "C", "reason": "match_count = per-name ambiguity cardinality (len of a small name_index bucket), not a population total."},
    "backend/services/operations_control/control_plane.py::capture_count": {
        "class": "C", "reason": "capture_count = size of an intentional recent-10 evidence bundle window (sibling reads use explicit limit 3/10/20)."},
    "backend/services/cost_codes/oppc_execution.py::report_count": {
        "class": "B", "reason": "report_count bounded structurally by a single project + single ISO week query window; streamed (to_list(length=None))."},
    # GD-0015 governed different-scope: 'total' is the full-collection backfill denominator
    # (count_documents({})); the find() is the needing-backfill working subset, NOT a returned
    # items+count population list. total / attached / unresolved are distinct named metrics.
    "backend/routes/master_lookup.py::backfill_equipment": {
        "class": "A", "reason": "'total' = full-collection backfill denominator; find() is the needing-backfill working subset, not a returned items+count list. Distinct named metrics."},
    "backend/routes/master_lookup.py::backfill_employees": {
        "class": "A", "reason": "'total' = full-collection backfill denominator; find() is the needing-backfill working subset, not a returned items+count list. Distinct named metrics."},
}


class Violation:
    def __init__(self, guard: str, label: str, fn: str, reason: str):
        self.guard = guard
        self.label = label
        self.fn = fn
        self.reason = reason

    def message(self) -> str:
        if self.guard == "GD-0014":
            return f"GD-0014 POPULATION CONTRACT VIOLATION: {self.label}::{self.fn} — {self.reason}"
        return f"GD-0015 TOTAL FILTER DRIFT: {self.label}::{self.fn} — {self.reason}"


# ── shared AST-ish helpers ───────────────────────────────────────────────────
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


def funcs(lines):
    """Yield (name, shallow_body) with nested def bodies excluded (no closure collisions)."""
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


def offenders_in(body: str) -> List[Tuple[str, str]]:
    """GD-0014: fixed-cap population total := len(bounded read) with NO canonical total."""
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


def _norm(s):
    return re.sub(r"\s+", " ", s or "").strip().rstrip(",")


def filter_drift_in(body: str) -> List[Tuple[str, str, list]]:
    """GD-0015: population total (count_documents) computed from a filter that differs
    from the items find() filter on the same collection handle."""
    finds = {}
    for m in FIND.finditer(body):
        finds.setdefault(_norm(m.group(1)), set()).add(_norm(m.group(2)).split(", {")[0])
    drift = []
    for m in CD.finditer(body):
        h, x = _norm(m.group(1)), _norm(m.group(2))
        if h not in finds:
            continue  # standalone metric count, not an items+total pairing on this handle
        if x.startswith("{**") or '"status": "active"' in x or "'status': 'active'" in x:
            continue  # explicitly narrowed metric = legitimately different scope
        yset = finds[h]
        ok = x in yset or any(x == y or (x and x in y) for y in yset)
        if not ok:
            drift.append((h, x, sorted(yset)))
    return drift


def _allowed(label: str, fn: str, key: str) -> bool:
    exc_key = "%s::%s" % (label, fn)
    if exc_key in EXCEPTIONS:
        return True
    return any(k.startswith(label + "::") and (k.endswith("::" + fn) or k.endswith("::" + key))
               for k in EXCEPTIONS)


def scan_population_contract(files: Iterable[Tuple[str, str]]) -> List[Violation]:
    out = []
    for label, text in files:
        lines = text.splitlines()
        for fn, body in funcs(lines):
            for key, var in offenders_in(body):
                if not _allowed(label, fn, key):
                    out.append(Violation("GD-0014", label, fn,
                                         "fixed-cap read with population '%s':=len(%s) and no canonical total (add count_documents on the same filter, or classify via a governed EXCEPTIONS entry)" % (key, var)))
    return out


def scan_filter_drift(files: Iterable[Tuple[str, str]]) -> List[Violation]:
    out = []
    for label, text in files:
        lines = text.splitlines()
        for fn, body in funcs(lines):
            if "count_documents(" not in body:
                continue
            if _allowed(label, fn, "total"):
                continue  # governed different-scope (see EXCEPTIONS)
            for h, x, yset in filter_drift_in(body):
                out.append(Violation("GD-0015", label, fn,
                                     "total filter on %s '%s' != items filter %s" % (h, x[:70], yset)))
    return out


def served_backend_files(repo_root: Path) -> List[Tuple[str, str]]:
    be = repo_root / "backend"
    files = []
    for py in be.rglob("*.py"):
        s = str(py)
        if "/tests/" in s or "__pycache__" in s or "/scripts/" in s:
            continue
        files.append((str(py.relative_to(repo_root)), py.read_text(errors="ignore")))
    return files


def gate_violations(repo_root: Path) -> List[str]:
    """Canonical pre-Save enforcement: returns formatted fail-closed messages (empty == clean)."""
    files = served_backend_files(repo_root)
    msgs = [v.message() for v in scan_population_contract(files)]
    msgs += [v.message() for v in scan_filter_drift(files)]
    return msgs
