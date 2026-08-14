#!/usr/bin/env python3
"""Dump enclosing function bodies for all WAVE4_FINAL_PROOF D_PRECISE sites for manual trace."""
import json, re
from pathlib import Path
ROOT = Path("/app")
d = json.load(open(ROOT / "memory/truth_program/WAVE4_FINAL_PROOF.json"))
sites = [r for r in d["sites"] if r["final_class"] == "D_PRECISE"]
def enclosing(lines, i):
    ind=None; start=i
    for j in range(i,-1,-1):
        m=re.match(r"(\s*)(async\s+def|def)\s", lines[j])
        if m: start=j; ind=len(m.group(1)); break
    if ind is None: return max(0,i-15), min(len(lines),i+15)
    end=len(lines)
    for k in range(start+1,len(lines)):
        s=lines[k]
        if s.strip() and (len(s)-len(s.lstrip()))<=ind and re.match(r"\s*(async\s+def|def|class)\s",s):
            end=k; break
    return start,end
for r in sites:
    py=ROOT/r["file"]; lines=py.read_text(errors="ignore").splitlines()
    i=r["current_line"]-1
    s,e=enclosing(lines,i)
    print("\n"+"="*90)
    print(f"### {r['file']}::{r['function']}  L{r['current_line']}  bound={r['fixed_bound']} key={r['canonical_total_key']}")
    print("="*90)
    for n in range(s,e):
        print(f"{n+1:5d}| {lines[n]}")
