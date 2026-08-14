#!/usr/bin/env python3
"""WAVE 5 — Human-visible TRUTH SURFACE per-surface enumeration + governed-class tie-out.

Component/element-level (NOT line-noise) enumeration of human-visible truth surfaces
that display a KPI, a count/total, or a health/status/band, and deterministic mapping
of each to a PROVEN governed class:

  KPI_CONCEPT          -> a reconciled canonical calculator (Wave-5): percent_complete,
                          expiring_rate, utilization, variance, efficiency, health/trust,
                          compliance, eligibility, avg_days, ownership.
  POPULATION_COUNT     -> Wave-4 count/total population truth (735/735 PROVEN, GD-0013/14/15).
  STATUS_BAND          -> Wave-2 status vocabulary (TC-0002 OCC/trust health bands).
  EXCLUDED_NON_KPI     -> proven non-KPI (on_time SectionTimeline false-match class).

A surface is only auto-dispositioned when its rendered token maps to one of the above
PROVEN governed owners. Anything else is OPEN_NEEDS_PROOF (never fabricated).

Read-only. Emits memory/truth_program/TRUTH_SURFACE_ENUMERATION.csv + summary JSON.
"""
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path("/app")
FRONTEND = ROOT / "frontend/src"

# Element-level surface markers: a rendered metric element.
SURFACE_MARKERS = [
    re.compile(r"<Stat\b"),
    re.compile(r"<KV\b"),
    re.compile(r"<Pct\b"),
    re.compile(r"<ScoreRing\b"),
    re.compile(r'data-testid="[^"]*(kpi|count|total|percent|pct|score|rate|util|variance|efficiency|health|status|band|complete|expiring|compliance|eligib|avg|days)[^"]*"'),
]

# concept keyword -> governed class + owner  (order = specificity)
CLASS_RULES = [
    ("percent_complete|completion_percent|pct_complete|progress_percent|onboarding", "KPI_CONCEPT", "percent_complete", "lib.kpi_percent_complete"),
    ("expiring|expired|days_until|expiry|at_risk", "KPI_CONCEPT", "expiring_rate", "lib.kpi_expiry"),
    ("utilization|util_pct|utili[sz]ation", "KPI_CONCEPT", "utilization", "kpi_percent_complete.utilization_percent/storage_capacity_truth"),
    ("variance_percent|variance_pct|variance", "KPI_CONCEPT", "variance_percent", "lib.kpi_variance"),
    ("efficiency", "KPI_CONCEPT", "efficiency_percent", "lib.kpi_efficiency"),
    ("trust_score|health_score|readiness_score|score_band|scoreband|ScoreRing", "KPI_CONCEPT", "health_score", "lib.trust_score(+distinct)"),
    ("compliance", "KPI_CONCEPT", "compliance_rate", "kpi_percent_complete.compliance_rate"),
    ("eligib|pct_eligible|qualified", "KPI_CONCEPT", "eligibility_rate", "transport_carrier_intelligence"),
    ("avg_days|days_open|days_to_close|average_days", "KPI_CONCEPT", "avg_days", "operational_intelligence.products"),
    ("ownership_score|attribution_score", "KPI_CONCEPT", "ownership_score", "r2_lifecycle(SO-07)"),
    ("on_time|ontime", "EXCLUDED_NON_KPI", "on_time_rate", "excluded (SectionTimeline false-match)"),
    ("count|total|count_documents", "POPULATION_COUNT", "population", "Wave-4 count/total (GD-0013/14/15)"),
    ("status|band|pill|overall_status|health_label", "STATUS_BAND", "status", "Wave-2 status vocab (TC-0002)"),
]

RECONCILED_OWNERS = {"percent_complete", "expiring_rate", "utilization", "variance_percent",
                     "efficiency_percent", "health_score", "compliance_rate", "eligibility_rate",
                     "avg_days", "ownership_score"}


def classify_token(text):
    for pat, klass, concept, owner in CLASS_RULES:
        if re.search(pat, text, re.I):
            return klass, concept, owner
    return "OPEN_NEEDS_PROOF", "unknown", ""


def route_of(path):
    # best-effort route/page from filename
    name = path.stem
    return name


def main():
    rows = []
    seen = set()
    for p in sorted(FRONTEND.rglob("*.jsx")) + sorted(FRONTEND.rglob("*.tsx")):
        s = str(p)
        if any(x in s for x in ("__tests__", ".test.", "node_modules")):
            continue
        try:
            lines = p.read_text(errors="ignore").splitlines()
        except Exception:
            continue
        rel = str(p.relative_to(ROOT))
        for i, l in enumerate(lines):
            if not any(m.search(l) for m in SURFACE_MARKERS):
                continue
            # extract a stable label token (testid or nearest metric word)
            m = re.search(r'data-testid="([^"]+)"', l)
            label = m.group(1) if m else l.strip()[:60]
            klass, concept, owner = classify_token(l)
            key = (rel, label)
            if key in seen:
                continue
            seen.add(key)
            disp = ("RECONCILED_KPI" if concept in RECONCILED_OWNERS
                    else "EXCLUDED_NON_KPI" if klass == "EXCLUDED_NON_KPI"
                    else "GOVERNED_POPULATION" if klass == "POPULATION_COUNT"
                    else "GOVERNED_STATUS" if klass == "STATUS_BAND"
                    else "OPEN_NEEDS_PROOF")
            rows.append({
                "loc": "%s:%d" % (rel, i + 1),
                "route": route_of(p),
                "label": label,
                "class": klass,
                "concept": concept,
                "owner": owner,
                "disposition": disp,
            })

    by_disp = defaultdict(int)
    for r in rows:
        by_disp[r["disposition"]] += 1

    # write CSV
    import csv
    out_csv = ROOT / "memory/truth_program/TRUTH_SURFACE_ENUMERATION.csv"
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["loc", "route", "label", "class", "concept", "owner", "disposition"])
        w.writeheader()
        for r in rows:
            w.writerow(r)

    summary = {
        "generated": "wave5_surface_enumeration",
        "total_human_visible_surfaces": len(rows),
        "by_disposition": dict(by_disp),
        "open_needs_proof": [r["loc"] for r in rows if r["disposition"] == "OPEN_NEEDS_PROOF"][:50],
    }
    (ROOT / "memory/truth_program/TRUTH_SURFACE_ENUMERATION.json").write_text(json.dumps(summary, indent=2))
    print("HUMAN-VISIBLE TRUTH SURFACES ENUMERATED:", len(rows))
    for k, v in sorted(by_disp.items(), key=lambda kv: -kv[1]):
        print("  %-22s %d" % (k, v))


if __name__ == "__main__":
    main()
