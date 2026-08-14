#!/usr/bin/env python3
"""WAVE 4 — comprehensive bounded-len tie scan over ALL non-D backend functions.

For every backend function, identify bounded-collection variables:
  (a) VAR = ...to_list(FIXED) / ...limit(FIXED).to_list(...)
  (b) VAR = [ .. for .. in <limited cursor> ]
  (c) VAR = []  +  async for x in <...limit(FIXED)/to_list(FIXED)...>: VAR.append(..)
  (d) VAR2 derived from any bounded VAR (comprehension / reassignment)
Then flag any total-like, non-page `key: len(VAR)` / `key = len(VAR)` as a
future-scale count-truncation D. Prints file:line:key:var:bound.

Excludes already-repaired sites by checking for count_documents in the function.
Read-only.
"""
import re
from pathlib import Path

BACKEND = Path("/app/backend")
PAGEQ = re.compile(r"page|returned|batch|sample|window|shown|per_page|dedup|override|slice|display|preview|recent|top|limit|shard|chunk|scan|_win\b", re.I)
TOTALISH = re.compile(r"total|count|size|\bnum\b|tally|\bsum\b|headcount|fleet|roster|population|records|entries|active_|open_|len\b", re.I)
COUNT_DOCS = re.compile(r"count_documents|estimated_document_count")
# fixed-cap bound = numeric literal OR ternary-of-numerics (e.g. "200 if search else 5000"),
# but NOT request-driven paging (bare `limit`, `min(limit, N)`, `page_size`).
_ARG = r"(?:length\s*=\s*)?([^)]*?)"
FIXED_LIMIT = re.compile(r"\.(?:to_list\(\s*" + _ARG + r"\s*\)|limit\(\s*" + _ARG + r"\s*\))")


def _fixed_bound(arg):
    a = (arg or "").strip()
    if not a or a in ("None",):
        return None
    if re.search(r"\bmin\s*\(", a):  # min(limit, N) → request-capped page
        return None
    if re.search(r"\blen\s*\(", a):  # len(ids) → bounded-exact, not a cap
        return None
    nums = re.findall(r"\b(\d{1,9})\b", a)
    core = re.sub(r"\bif\b|\belse\b|\band\b|\bor\b", " ", a)
    has_ident = bool(re.search(r"[A-Za-z_]", core))
    if nums and not has_ident:
        return int(max(nums, key=int))
    if nums and re.search(r"\bif\b.*\belse\b", a):  # ternary of fixed caps
        return int(max(nums, key=int))
    return None  # request/variable-driven → page (A)


def funcs(lines):
    idxs = [i for i, l in enumerate(lines) if re.match(r"\s*(async\s+def|def)\s", l)]
    for n, s in enumerate(idxs):
        ind = len(lines[s]) - len(lines[s].lstrip())
        e = len(lines)
        for k in range(s + 1, len(lines)):
            ss = lines[k]
            if ss.strip() and (len(ss) - len(ss.lstrip())) <= ind and re.match(r"\s*(async\s+def|def|class)\s", ss):
                e = k; break
        yield s, e


def bounded_vars(body):
    """Return {var: bound} for fixed-cap bounded-collection vars in the function."""
    out = {}
    # (a) VAR = ... to_list(ARG) / limit(ARG)...
    for m in re.finditer(r"^\s*([A-Za-z_]\w*)\s*=\s*.*?" + FIXED_LIMIT.pattern, body, re.M):
        b = _fixed_bound(m.group(2) if m.group(2) is not None else m.group(3))
        if b is not None:
            out[m.group(1)] = b
    # (b) comprehension VAR = [.. for .. in <expr FIXED_LIMIT>]
    for m in re.finditer(r"([A-Za-z_]\w*)\s*=\s*\[[^\]]*?\bfor\b[^\]]*?" + FIXED_LIMIT.pattern + r"[^\]]*\]", body):
        b = _fixed_bound(m.group(2) if m.group(2) is not None else m.group(3))
        if b is not None:
            out[m.group(1)] = b
    # (c) async for x in <expr FIXED_LIMIT>: VAR.append(
    for m in re.finditer(r"async\s+for\s+\w+\s+in\s+[^\n]*?" + FIXED_LIMIT.pattern + r"[^\n]*:\s*\n(?:[^\n]*\n){0,40}", body):
        b = _fixed_bound(m.group(1) if m.group(1) is not None else m.group(2))
        block = m.group(0)
        for am in re.finditer(r"([A-Za-z_]\w*)\.append\(", block):
            if b is not None:
                out[am.group(1)] = b
    # (d) derive: VAR2 = <expr referencing bounded var>  (passes)
    for _ in range(3):
        for m in re.finditer(r"^\s*([A-Za-z_]\w*)\s*=\s*([^\n]+)$", body, re.M):
            lhs, rhs = m.group(1), m.group(2)
            if lhs in out:
                continue
            for v, b in list(out.items()):
                if re.search(r"\b%s\b" % re.escape(v), rhs) and not rhs.strip().startswith("len("):
                    out[lhs] = b; break
    return out


def main():
    flags = []
    for py in BACKEND.rglob("*.py"):
        sp = str(py)
        if "/tests/" in sp or "__pycache__" in sp or "/scripts/" in sp:
            continue
        lines = py.read_text(errors="ignore").splitlines()
        for s, e in funcs(lines):
            body = "\n".join(lines[s:e])
            if COUNT_DOCS.search(body):
                continue  # has a canonical total already
            bv = bounded_vars(body)
            if not bv:
                continue
            for m in re.finditer(r"[\"']([A-Za-z_]\w*)[\"']\s*:\s*len\(\s*([A-Za-z_]\w*)\s*\)", body):
                key, v = m.group(1), m.group(2)
                if v in bv and TOTALISH.search(key) and not PAGEQ.search(key):
                    flags.append((str(py.relative_to("/app")), key, v, bv[v]))
            for m in re.finditer(r"^\s*([A-Za-z_]\w*)\s*=\s*len\(\s*([A-Za-z_]\w*)\s*\)", body, re.M):
                key, v = m.group(1), m.group(2)
                if v in bv and TOTALISH.search(key) and not PAGEQ.search(key):
                    flags.append((str(py.relative_to("/app")), "var:" + key, v, bv[v]))
    # dedupe
    seen = set(); uniq = []
    for f in flags:
        if f not in seen:
            seen.add(f); uniq.append(f)
    print("TOTAL-LIKE bounded-len ties (post count_documents-exclusion):", len(uniq))
    for f in sorted(uniq):
        print(" D?", f[0], "key=", f[1], "var=", f[2], "bound=", f[3])


if __name__ == "__main__":
    main()
