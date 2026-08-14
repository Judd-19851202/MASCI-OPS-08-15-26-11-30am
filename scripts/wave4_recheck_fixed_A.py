#!/usr/bin/env python3
"""WAVE 4 — strict re-scan of the fixed-bound A_PAGE_ONLY candidates.

Broader, conservative tie detection to eliminate false-negatives:
  * derived vars: comprehension AND simple reassignment referencing the base var.
  * total-like keys: total|count|size|num|tally|sum|headcount|fleet (not only total/count).
  * ALSO catch bare `key: len(V)` / `key = len(V)` for V in the derived set.
Anything matching a NON-page-qualified total-like use of len(truncated var) is
escalated to D_RECHECK for manual confirmation. Over-flags on purpose.
"""
import json, re
from pathlib import Path

ROOT = Path("/app")
PROOF = json.load(open(ROOT / "memory/truth_program/WAVE4_FINAL_PROOF.json"))
PAGEQ = re.compile(r"page|returned|batch|sample|window|shown|per_page|dedup|override|slice|display|preview|recent|top|limit|shard|chunk|scan", re.I)
TOTALISH = re.compile(r"total|count|size|\bnum\b|tally|\bsum\b|headcount|fleet|roster|population|records|entries|rows_?count|n_?\w*", re.I)

TOLIST = re.compile(r"\.(?:to_list\(\s*([^)]*?)\s*\)|limit\(\s*([^)]*?)\s*\))")
ASSIGN_HEAD = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=")


def enclosing(lines, i):
    ind = None; start = i
    for j in range(i, -1, -1):
        m = re.match(r"(\s*)(async\s+def|def)\s", lines[j])
        if m:
            start = j; ind = len(m.group(1)); break
    if ind is None:
        return max(0, i - 20), min(len(lines), i + 20)
    end = len(lines)
    for k in range(start + 1, len(lines)):
        s = lines[k]
        if s.strip() and (len(s) - len(s.lstrip())) <= ind and re.match(r"\s*(async\s+def|def|class)\s", s):
            end = k; break
    return start, end


def derived_vars(body, base):
    vs = {base}
    for _ in range(4):
        # comprehension: X = [.. for .. in V]
        for m in re.finditer(r"([A-Za-z_][A-Za-z0-9_]*)\s*=\s*\[[^\]]*\bfor\b[^\]]*\bin\s+([A-Za-z_][A-Za-z0-9_]*)", body):
            if m.group(2) in vs:
                vs.add(m.group(1))
        # simple reassignment / slice / sorted(...): X = <expr with V>
        for m in re.finditer(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*([^\n]+)$", body, re.M):
            lhs, rhs = m.group(1), m.group(2)
            if any(re.search(r"\b%s\b" % re.escape(v), rhs) for v in vs) and "len(" not in rhs.split("=")[0]:
                vs.add(lhs)
    return vs


def main():
    fixed_A = [r for r in PROOF["sites"]
               if r["final_class"] == "A_PAGE_ONLY" and r["bound_semantics"] == "fixed"]
    rechecks = []
    for r in fixed_A:
        py = ROOT / r["file"]
        lines = py.read_text(errors="ignore").splitlines()
        idx = (r["current_line"] or 1) - 1
        mm = TOLIST.search(lines[idx]) if idx < len(lines) else None
        var = None
        for j in range(idx, max(-1, idx - 8), -1):
            am = ASSIGN_HEAD.match(lines[j])
            if am:
                var = am.group(1); break
        if not var:
            var = r.get("result_var") or "?"
        st, en = enclosing(lines, idx)
        body = "\n".join(lines[st:en])
        vs = derived_vars(body, var)
        hits = []
        # key: len(V)  or  key = len(V)
        for m in re.finditer(r"[\"']([A-Za-z_][A-Za-z0-9_]*)[\"']\s*:\s*len\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)", body):
            key, tv = m.group(1), m.group(2)
            if tv in vs and TOTALISH.search(key) and not PAGEQ.search(key):
                hits.append(("dict:%s" % key, tv))
        for m in re.finditer(r"([A-Za-z_][A-Za-z0-9_]*)\s*=\s*len\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)", body):
            key, tv = m.group(1), m.group(2)
            if tv in vs and TOTALISH.search(key) and not PAGEQ.search(key):
                hits.append(("var:%s" % key, tv))
        if hits:
            rechecks.append({"file": r["file"], "line": r["current_line"], "fn": r["function"],
                             "bound": r["fixed_bound"], "var": var, "hits": hits})
    print("fixed-bound A re-scanned:", len(fixed_A), " -> D_RECHECK:", len(rechecks))
    for x in rechecks:
        print("RECHECK:", x["file"], "L%s" % x["line"], x["fn"], "bound=", x["bound"], "var=", x["var"], "hits=", x["hits"])


if __name__ == "__main__":
    main()
