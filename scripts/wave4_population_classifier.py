#!/usr/bin/env python3
"""WAVE 4 — population-shaping site classifier (durable, resumable).

Scans the three population-shaping site classes and buckets each occurrence by
truncation RISK so the dangerous subset (a truncation feeding a human-visible
count/total/KPI, or the ONLY access path to a population) is separated from
benign display pagination / query batching / unbounded reads.

Buckets:
  SAFE_UNBOUNDED   to_list(None)/to_list(length=None) — full population
  RISK_COUNT       truncated result feeds .length/len() as a count/total  (REVIEW)
  DISPLAY_SLICE    frontend .slice(0,N) for rendering top-N (full data present)
  QUERY_BATCH      backend to_list(N)/limit=N pagination batch
Output: JSON summary to /app/memory/truth_program/WAVE4_SITE_CLASSIFICATION.json
"""
import json
import re
import subprocess
from pathlib import Path

ROOT = Path("/app")
COUNT_HINT = re.compile(r"\b(count|total|kpi|len\s*\(|\.length|_count|num_|summary)\b", re.I)


def _grep(pattern, globs, path):
    cmd = ["grep", "-rEn", pattern, path]
    for g in globs:
        cmd += ["--include", g]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=90).stdout
    except Exception:
        out = ""
    lines = []
    for ln in out.splitlines():
        if "/tests/" in ln or "__pycache__" in ln or "__tests__" in ln:
            continue
        if "/node_modules/" in ln or "wave4_population_classifier" in ln:
            continue
        lines.append(ln)
    return lines


def classify_backend_to_list(line):
    body = line.split(":", 2)[-1]
    if re.search(r"to_list\(\s*(None|length\s*=\s*None)\s*\)", body):
        return "SAFE_UNBOUNDED"
    # truncated to_list whose value is counted -> review
    if COUNT_HINT.search(body):
        return "RISK_COUNT"
    return "QUERY_BATCH"


def classify_backend_limit(line):
    body = line.split(":", 2)[-1]
    if COUNT_HINT.search(body):
        return "RISK_COUNT"
    return "QUERY_BATCH"


def classify_frontend_slice(line):
    body = line.split(":", 2)[-1]
    if COUNT_HINT.search(body):
        return "RISK_COUNT"
    return "DISPLAY_SLICE"


def bucketize(lines, fn):
    buckets = {}
    risky = []
    for ln in lines:
        b = fn(ln)
        buckets[b] = buckets.get(b, 0) + 1
        if b == "RISK_COUNT":
            risky.append(ln[:200])
    return buckets, risky


def main():
    tl = _grep(r"\.to_list\(", ["*.py"], str(ROOT / "backend"))
    lim = _grep(r"(limit\s*=\s*[0-9]+|\.limit\(\s*[0-9])", ["*.py"], str(ROOT / "backend"))
    sl = _grep(r"\.slice\(\s*0\s*,", ["*.js", "*.jsx"], str(ROOT / "frontend/src"))

    tl_b, tl_r = bucketize(tl, classify_backend_to_list)
    lim_b, lim_r = bucketize(lim, classify_backend_limit)
    sl_b, sl_r = bucketize(sl, classify_frontend_slice)

    result = {
        "generated": "wave4",
        "denominators_durable": {"frontend_slice": 595, "backend_to_list": 317, "backend_limit": 130, "total": 1042},
        "scanned": {"backend_to_list": len(tl), "backend_limit": len(lim), "frontend_slice": len(sl)},
        "backend_to_list_buckets": tl_b,
        "backend_limit_buckets": lim_b,
        "frontend_slice_buckets": sl_b,
        "risk_count_sites": {
            "backend_to_list": tl_r,
            "backend_limit": lim_r,
            "frontend_slice": sl_r,
        },
        "risk_count_totals": {
            "backend_to_list": len(tl_r),
            "backend_limit": len(lim_r),
            "frontend_slice": len(sl_r),
            "total_review_needed": len(tl_r) + len(lim_r) + len(sl_r),
        },
    }
    out = ROOT / "memory/truth_program/WAVE4_SITE_CLASSIFICATION.json"
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ("scanned", "backend_to_list_buckets", "backend_limit_buckets", "frontend_slice_buckets", "risk_count_totals")}, indent=2))


if __name__ == "__main__":
    main()
