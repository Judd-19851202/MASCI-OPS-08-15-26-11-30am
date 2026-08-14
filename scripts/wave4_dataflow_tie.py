#!/usr/bin/env python3
"""WAVE 4 Phase 1 — dataflow-tied D detection (precise).

For each truncated read (VAR = await <cursor>.to_list(N) / .limit(N)), tie the
truncated VARIABLE (and simple transforms VAR2=[.. for x in VAR]) to a
total/count field derivation, so we flag D only when len(THAT variable) is
presented as a canonical total/count (non-page-qualified) with a FIXED bound and
no count_documents in the function. Reduces 149 heuristic candidates to the
exact true-D subset. Does NOT repair.
"""
import json, re
from pathlib import Path

ROOT = Path("/app"); BACKEND = ROOT / "backend"
ASSIGN = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?:await\s+)?.*?\.(?:to_list\(\s*([^)]*)\)|limit\(\s*(\d+)\s*\))")
COUNT_DOCS = re.compile(r"count_documents|estimated_document_count|\.count\(\)|aggregate\(")
PAGEQ = re.compile(r"page|returned|batch|sample|window|shown|per_page|dedup|override|slice", re.I)


def enclosing(lines, i):
    ind=None; start=i
    for j in range(i,-1,-1):
        m=re.match(r"(\s*)(async\s+def|def)\s", lines[j])
        if m: start=j; ind=len(m.group(1)); break
    if ind is None: return max(0,i-15),min(len(lines),i+15)
    end=len(lines)
    for k in range(start+1,len(lines)):
        s=lines[k]
        if s.strip() and (len(s)-len(s.lstrip()))<=ind and re.match(r"\s*(async\s+def|def|class)\s",s):
            end=k; break
    return start,end


def derived_vars(body, base):
    vs={base}
    for _ in range(3):
        for m in re.finditer(r"([A-Za-z_][A-Za-z0-9_]*)\s*=\s*\[[^\]]*\bfor\b[^\]]*\bin\s+([A-Za-z_][A-Za-z0-9_]*)", body):
            if m.group(2) in vs: vs.add(m.group(1))
    return vs


def main():
    trueD=[]; total_sites=0
    for py in BACKEND.rglob("*.py"):
        if "/tests/" in str(py) or "__pycache__" in str(py): continue
        try: lines=py.read_text(errors="ignore").splitlines()
        except Exception: continue
        for i,l in enumerate(lines):
            m=ASSIGN.match(l)
            if not m: continue
            var=m.group(1); arg=(m.group(2) or "").strip(); litbound=m.group(3)
            # unbounded
            if m.group(2) is not None and re.match(r"\s*(None|length\s*=\s*None)\s*$", arg or ""): continue
            total_sites+=1
            # fixed numeric bound?
            fixed=None
            if litbound: fixed=int(litbound)
            else:
                nums=re.findall(r"\b(\d{2,7})\b", arg or "")
                if nums and not re.search(r"[a-zA-Z_]", arg or ""): fixed=int(nums[0])
            if fixed is None: continue  # variable/request-limit -> A_PAGE_ONLY (not D)
            s,e=enclosing(lines,i); body="\n".join(lines[s:e])
            if COUNT_DOCS.search(body): continue  # B_TRUE_TOTAL
            if re.search(r"len\(", arg or ""): continue  # C_BOUNDED_EXACT
            vs=derived_vars(body,var)
            hit=False
            for tm in re.finditer(r"[\"']([A-Za-z_]*(?:total|count)[A-Za-z_]*)[\"']\s*:\s*len\(\s*([A-Za-z_][A-Za-z0-9_]*)", body):
                key=tm.group(1); tvar=tm.group(2)
                if tvar in vs and not PAGEQ.search(key):
                    hit=True; break
            if hit:
                trueD.append({"file":str(py.relative_to(ROOT)),"line":i+1,"var":var,"bound":fixed,"snippet":l.strip()[:120]})
    p=ROOT/"memory/truth_program/WAVE4_SITE_CLASSIFICATION.json"
    d=json.load(open(p)); d["query_batch_contract"]["dataflow_tied_true_D"]={"count":len(trueD),"sites":trueD}
    json.dump(d,open(p,"w"),indent=2)
    print(json.dumps({"assigned_truncated_reads_scanned":total_sites,"dataflow_tied_true_D":len(trueD)},indent=2))
    for x in trueD: print("D:",x["file"],x["line"],"bound=",x["bound"],"|",x["snippet"])


if __name__=="__main__": main()
