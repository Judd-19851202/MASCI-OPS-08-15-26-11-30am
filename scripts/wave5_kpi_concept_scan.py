#!/usr/bin/env python3
"""WAVE 5 — canonical KPI concept discovery + blast-radius ranking.

Finds every place a KPI/derived metric is COMPUTED (percentage/rate/score/ratio),
groups them by concept, and ranks by blast radius (how many distinct files/sites
compute the same concept). Highest blast radius = reconcile first (same concept +
same scope must use one canonical calculation).

Read-only. Emits memory/truth_program/WAVE5_KPI_CONCEPTS.json
"""
import json, re
from collections import defaultdict
from pathlib import Path

ROOT = Path("/app")
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend/src"

# Concept -> patterns that indicate a COMPUTATION of that concept (not just a read).
CONCEPTS = {
    "percent_complete":        r"percent_complete|completion_percent|pct_complete|progress_percent",
    "utilization":             r"utilization|util_pct|utili[sz]ation_rate",
    "compliance_rate":         r"compliance_(?:rate|percent|pct|score)",
    "health_score":            r"health_score|convergence_score|readiness_score|trust_score",
    "on_time_rate":            r"on_time_(?:rate|percent|pct)|ontime",
    "efficiency_percent":      r"efficiency_percent|labor_efficiency|production_efficiency|efficiency_pct",
    "variance_percent":        r"variance_percent|variance_pct",
    "ownership_score":         r"ownership_score|attribution_score",
    "eligibility_rate":        r"eligib\w*_(?:rate|percent|pct)|qualified_(?:rate|percent)",
    "avg_days":                r"avg_days|average_days|mean_days|days_avg",
    "pass_rate":               r"pass_rate|pass_percent|fail_rate|defect_rate",
    "expiring_rate":           r"expiring|expired_(?:rate|percent|count)|at_risk_(?:rate|percent)",
}
# A site is a "computation" if a concept token co-occurs with a division / round / %
COMPUTE = re.compile(r"/|round\(|\*\s*100|100\s*\*|\bpct\b|percent")


def scan(root, label):
    hits = defaultdict(list)
    for p in root.rglob("*.*"):
        if p.suffix not in (".py", ".js", ".jsx", ".ts", ".tsx"):
            continue
        s = str(p)
        if "/tests/" in s or "__pycache__" in s or "/node_modules/" in s or "/scripts/" in s:
            continue
        try:
            lines = p.read_text(errors="ignore").splitlines()
        except Exception:
            continue
        for i, l in enumerate(lines):
            for concept, pat in CONCEPTS.items():
                if re.search(pat, l, re.I) and COMPUTE.search(l):
                    hits[concept].append({"loc": "%s:%d" % (str(p.relative_to(ROOT)), i + 1),
                                          "side": label, "code": l.strip()[:160]})
    return hits


def main():
    be = scan(BACKEND, "backend")
    fe = scan(FRONTEND, "frontend")
    concepts = {}
    for c in CONCEPTS:
        sites = be.get(c, []) + fe.get(c, [])
        files = sorted({h["loc"].split(":")[0] for h in sites})
        concepts[c] = {
            "concept_id": "KPI-" + c.upper().replace("_", "-"),
            "compute_site_count": len(sites),
            "distinct_files": len(files),
            "backend_sites": len(be.get(c, [])),
            "frontend_sites": len(fe.get(c, [])),
            "files": files,
            "sites": sites,
            "status": "PENDING_RECONCILE",
        }
    ranked = sorted(concepts.values(), key=lambda x: (-x["distinct_files"], -x["compute_site_count"]))
    out = {"generated": "wave5", "concepts": concepts,
           "blast_radius_ranking": [{"concept_id": c["concept_id"],
                                     "distinct_files": c["distinct_files"],
                                     "compute_sites": c["compute_site_count"],
                                     "backend": c["backend_sites"], "frontend": c["frontend_sites"]}
                                    for c in ranked]}
    (ROOT / "memory/truth_program/WAVE5_KPI_CONCEPTS.json").write_text(json.dumps(out, indent=2))
    print("WAVE 5 KPI concept blast-radius ranking (reconcile top-down):")
    for r in out["blast_radius_ranking"]:
        print("  %-22s files=%-3d sites=%-3d (be=%d fe=%d)" % (
            r["concept_id"], r["distinct_files"], r["compute_sites"], r["backend"], r["frontend"]))


if __name__ == "__main__":
    main()
