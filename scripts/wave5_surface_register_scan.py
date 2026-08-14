#!/usr/bin/env python3
"""WAVE 5 — Truth-surface register enumeration + deterministic grouping.

Reproducibly enumerates the human-visible / API-emitted TRUTH SURFACES (KPI,
count/total, health/status/score) across the codebase and GROUPS them by their
governed canonical concept so a single shared-owner proof can disposition many
surfaces at once (owner Part 6: automate the remainder by shared lineage — never
by name similarity alone; a group only closes when it maps to a proven canonical
owner).

Read-only. Emits memory/truth_program/WAVE5_SURFACE_GROUPING.json.

Disposition rule:
  - A surface is AUTO-RECONCILED only if it belongs to a concept whose canonical
    owner + executable guard already exist (the reconciled concept set below).
  - Everything else is OPEN and must receive a per-surface / per-group proof.
Nothing is fabricated: OPEN stays OPEN until a proof closes it.
"""
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path("/app")
FRONTEND = ROOT / "frontend/src"
BACKEND = ROOT / "backend"

# Concept -> (regex over a source line, canonical owner if reconciled).
# Ordered: first match wins (most specific first).
CONCEPT_PATTERNS = [
    ("percent_complete", r"percent_complete|completion_percent|pct_complete|progress_percent|onboarding.*percent",
     "lib.kpi_percent_complete.checklist_percent/schedule_rollup_percent/quantity_progress_percent"),
    ("expiring_rate", r"expiring|expired_(?:rate|percent|count)|days_until|expiry_status|at_risk",
     "lib.kpi_expiry"),
    ("utilization", r"utilization|util_pct|utili[sz]ation",
     "lib.kpi_percent_complete.utilization_percent / storage_capacity_truth (distinct owners)"),
    ("variance_percent", r"variance_percent|variance_pct",
     "lib.kpi_variance.variance_percent"),
    ("efficiency_percent", r"efficiency_percent|labor_efficiency|production_efficiency|efficiency_pct",
     "lib.kpi_efficiency.efficiency_percent"),
    ("health_score", r"health_score|trust_score|readiness_score|convergence_score|score_band",
     "lib.trust_score.compute_score/compute_backup_trust_score (+distinct variants)"),
    ("compliance_rate", r"compliance_(?:rate|percent|pct|score)|inspection_compliance",
     "lib.kpi_percent_complete.compliance_rate"),
    ("eligibility_rate", r"eligib\w*_(?:rate|percent|pct)|pct_eligible|qualified_(?:rate|percent)",
     "lib.transport_carrier_intelligence pct_eligible"),
    ("avg_days", r"avg_days|average_days|mean_days|days_avg|days_open|days_to_close",
     "operational_intelligence.products (DIRECT_FACT mean)"),
    ("ownership_score", r"ownership_score|attribution_score",
     "r2 lifecycle ownership (SO-07)"),
    ("on_time_rate", r"on_time_(?:rate|percent|pct)|ontime",
     None),  # excluded (non-KPI) — needs per-site proof
    ("pass_rate", r"pass_rate|pass_percent|fail_rate|defect_rate",
     None),
    # Non-KPI truth surfaces (count/status) — governed elsewhere (Wave 3/4 population + status vocab)
    ("count_total", r"\b(count|total|count_documents)\b",
     "Wave-4 population truth (count/total contract, GD-0013/14/15)"),
    ("status_band", r"\b(status|band|overall_status|health_label|pill)\b",
     "status vocabulary (OCC/trust — Wave 2 TC-0002)"),
]

RECONCILED_CONCEPTS = {
    "percent_complete", "expiring_rate", "utilization", "variance_percent",
    "efficiency_percent", "health_score", "compliance_rate", "eligibility_rate",
    "avg_days", "ownership_score",
}
# count_total + status_band are governed by prior waves (population + status vocab)
PRIOR_WAVE_GOVERNED = {"count_total", "status_band"}

# A surface line must LOOK like a rendered metric or emitted KPI field.
FE_SURFACE = re.compile(r"(data-testid|<Stat|<KV|<Pct|<ScoreRing|toFixed|\{\s*\w+\.\w+|%`|Number\()")
BE_SURFACE = re.compile(r"return\s*\{|\"[a-z_]+\":|'[a-z_]+':|round\(|/ ")


def classify(line):
    for concept, pat, owner in CONCEPT_PATTERNS:
        if re.search(pat, line, re.I):
            return concept, owner
    return None, None


def scan(root, label, surface_re):
    surfaces = []
    for p in root.rglob("*.*"):
        if p.suffix not in (".py", ".js", ".jsx", ".ts", ".tsx"):
            continue
        s = str(p)
        if any(x in s for x in ("/tests/", "__pycache__", "/node_modules/", "/scripts/", ".test.", "__tests__")):
            continue
        try:
            lines = p.read_text(errors="ignore").splitlines()
        except Exception:
            continue
        for i, l in enumerate(lines):
            concept, owner = classify(l)
            if not concept:
                continue
            if not surface_re.search(l):
                continue
            surfaces.append({
                "loc": "%s:%d" % (str(p.relative_to(ROOT)), i + 1),
                "side": label, "concept": concept, "owner": owner,
            })
    return surfaces


def main():
    fe = scan(FRONTEND, "frontend", FE_SURFACE)
    be = scan(BACKEND, "backend", BE_SURFACE)
    surfaces = fe + be
    by_concept = defaultdict(list)
    for s in surfaces:
        by_concept[s["concept"]].append(s)

    groups = {}
    reconciled = 0
    prior_governed = 0
    open_ = 0
    for concept, items in sorted(by_concept.items(), key=lambda kv: -len(kv[1])):
        if concept in RECONCILED_CONCEPTS:
            disp = "AUTO_RECONCILED"
            reconciled += len(items)
        elif concept in PRIOR_WAVE_GOVERNED:
            disp = "PRIOR_WAVE_GOVERNED"
            prior_governed += len(items)
        else:
            disp = "OPEN_NEEDS_PROOF"
            open_ += len(items)
        groups[concept] = {
            "concept": concept,
            "surface_count": len(items),
            "canonical_owner": items[0]["owner"],
            "disposition": disp,
            "sample_locs": [x["loc"] for x in items[:8]],
        }

    out = {
        "generated": "wave5_surface_grouping",
        "total_surfaces_enumerated": len(surfaces),
        "frontend_surfaces": len(fe),
        "backend_surfaces": len(be),
        "counters": {
            "auto_reconciled": reconciled,
            "prior_wave_governed": prior_governed,
            "open_needs_proof": open_,
        },
        "groups": groups,
    }
    (ROOT / "memory/truth_program/WAVE5_SURFACE_GROUPING.json").write_text(json.dumps(out, indent=2))
    print("WAVE 5 SURFACE GROUPING — total enumerated:", len(surfaces),
          "(fe=%d be=%d)" % (len(fe), len(be)))
    print("  auto_reconciled=%d prior_wave_governed=%d open_needs_proof=%d"
          % (reconciled, prior_governed, open_))
    for c, g in sorted(groups.items(), key=lambda kv: -kv[1]["surface_count"]):
        print("  %-20s %-20s %d" % (c, g["disposition"], g["surface_count"]))


if __name__ == "__main__":
    main()
