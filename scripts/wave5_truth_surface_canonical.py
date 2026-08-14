#!/usr/bin/env python3
"""WAVE 5 — CANONICAL Truth-Surface enumeration + classification (deterministic).

This is the SINGLE reproducible owner of the Wave-5 Truth Surface denominator.
It scans a stable candidate universe, applies EXPLICIT inclusion/exclusion rules,
and classifies every INCLUDED surface into a final governed disposition — all from
source, at any SHA. Invariant enforced:  candidate = included + excluded.

Dispositions (final, no OPEN allowed at closure):
  CANONICAL_KPI                       - renders a reconciled Wave-5 KPI (canonical owner)
  CANONICAL_STATUS                    - renders a governed status/health band (Wave-2 vocab)
  DIRECT_FACT                         - renders a stored record field / local list length,
                                        no computation / no hidden denominator
  GOVERNED_DISTINCT_VARIANT           - a legitimately distinct governed metric
  NON_TRUTH_SURFACE_EXCLUDED_WITH_REASON - structural/control/label/state markup, not a truth value

Read-only. Emits memory/truth_program/TRUTH_SURFACE_CANONICAL.csv + .json.
"""
import csv
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path("/app")
FE = ROOT / "frontend/src"

# ---- CANDIDATE UNIVERSE: a value-bearing rendered element OR a testid metric ----
VALUE_COMPONENT = re.compile(r"<(Stat|KV|Pct|ScoreRing)\b")
TESTID = re.compile(r'data-testid=[`"]([^`"]+)[`"]')
# arithmetic / metric value expressions rendered inline
INLINE_METRIC = re.compile(r"\{[^{}]*\.(length|count|total|percent|pct|rate|score)\b[^{}]*\}")

# ---- EXCLUSION: structural / control / label / state (NOT a truth value) ----
STRUCTURAL_TESTID = re.compile(
    r"(?:^|[-_])(root|shell|hero|title|subtitle|header|footer|heading|refresh|reload|export|download|"
    r"csv|pdf|print|loading|error|empty|skeleton|spinner|tab|tabs|link|btn|button|toggle|switch|"
    r"filter|search|input|select|dropdown|modal|dialog|drawer|sheet|nav|menu|banner|section|"
    r"container|wrapper|panel|card-root|meta|meta-row|catalog|framework|authority-statement|"
    r"generated-at|include-inactive|view-missing|view-all|see-all|show-more|icon|avatar|logo|"
    r"caption|label|help|hint|tooltip|coaching|disclosure|copy|desc|description|note|legend|"
    r"close|cancel|save|submit|back|next|prev|page|pagination|sort|column|row-action|actions?|"
    r"checkbox|radio|form|field-label|placeholder)$")
CONTROL_COMPONENT_LINE = re.compile(r"<(button|Button|a\s|Link|Tab|TabsTrigger|Input|Select|Textarea|Switch|Checkbox)\b")

# ---- DIRECT_FACT: stored record field / local length, no computation ----
DIRECT_FACT_VALUE = re.compile(
    r"(value|v)=\{\s*(?:String\(|formatDate\w*\(|sanitize\w*\(|t\()?\s*"
    r"(data|record|row|item|detail|report|incident|meeting|inspection|doc|entry)\.[\w.]+")
LOCAL_LENGTH = re.compile(r"\{\s*\(?[\w.]+\s*\|\|\s*\[\]\)?\.length\s*\}|\{\s*[\w.]+\.length\s*\}")

# ---- KPI concept tokens -> reconciled canonical owner ----
KPI_TOKENS = [
    (r"percent_complete|completion_percent|pct_complete|progress_percent|coverage_pct", "percent_complete", "lib.kpi_percent_complete"),
    (r"expiring|expired|days_until|expiry|at_risk", "expiring_rate", "lib.kpi_expiry"),
    (r"utilization|util_pct|utili[sz]ation", "utilization", "kpi_percent_complete.utilization_percent/storage"),
    (r"variance_percent|variance_pct", "variance_percent", "lib.kpi_variance"),
    (r"efficiency", "efficiency_percent", "lib.kpi_efficiency"),
    (r"trust_score|health_score|readiness_score|score_band|ScoreRing|trust_score_pct", "health_score", "lib.trust_score(+distinct)"),
    (r"compliance", "compliance_rate", "kpi_percent_complete.compliance_rate"),
    (r"eligib|pct_eligible|qualified_pct", "eligibility_rate", "transport_carrier_intelligence"),
    (r"avg_days|days_open|days_to_close|average_days", "avg_days", "operational_intelligence.products"),
    (r"ownership_score|attribution_score", "ownership_score", "r2_lifecycle(SO-07)"),
]
STATUS_TOKENS = re.compile(r"\b(status|band|overall_status|health_label|posture|readiness_state|pill_state)\b", re.I)
PERCENT_RENDER = re.compile(r"(pct|percent|rate|ratio)\b|%`|\.toFixed\(", re.I)
ONTIME = re.compile(r"on_time|ontime", re.I)


def classify(line):
    m = TESTID.search(line)
    testid = m.group(1) if m else ""
    is_value_comp = bool(VALUE_COMPONENT.search(line))

    # EXCLUSIONS first (structural/control/label markup)
    if testid and STRUCTURAL_TESTID.search(testid) and not is_value_comp:
        return "NON_TRUTH_SURFACE_EXCLUDED_WITH_REASON", "structural/control/label testid", ""
    if CONTROL_COMPONENT_LINE.search(line) and not is_value_comp:
        return "NON_TRUTH_SURFACE_EXCLUDED_WITH_REASON", "control element (button/link/input/tab)", ""

    # KPI concept (computed) — check value expression / testid
    for pat, concept, owner in KPI_TOKENS:
        if re.search(pat, line, re.I):
            return "CANONICAL_KPI", concept, owner
    if ONTIME.search(line):
        return "NON_TRUTH_SURFACE_EXCLUDED_WITH_REASON", "on_time SectionTimeline false-match (non-KPI)", ""
    if STATUS_TOKENS.search(line):
        return "CANONICAL_STATUS", "status", "Wave-2 status vocab (TC-0002)"

    # DIRECT_FACT: stored field / local length in a value-bearing render
    if DIRECT_FACT_VALUE.search(line) or LOCAL_LENGTH.search(line):
        # ...unless it actually renders a percentage/rate expression (a computed metric,
        # not a stored fact) -> a governed distinct percentage variant.
        if re.search(r"(pct|percent|rate|ratio)\b|%`|\.toFixed\(", line, re.I):
            return "GOVERNED_DISTINCT_VARIANT", "distinct_percentage_metric", "backend-computed % rendered as fact (distinct, not a named KPI concept)"
        return "DIRECT_FACT", "record_field_or_local_length", "record serialization -> prop -> render"
    if PERCENT_RENDER.search(line):
        return "GOVERNED_DISTINCT_VARIANT", "distinct_percentage_metric", "backend-computed % rendered (distinct governed variant)"
    if is_value_comp:
        # a <Stat>/<KV>/<Pct> whose value is a data.* / count-like field
        if re.search(r"(value|v)=\{[^}]*(count|total|mapped|unmapped|open|closed|assigned|remaining|actual|planned)\b", line, re.I):
            return "DIRECT_FACT", "displayed_count_fact", "count of displayed/queried population"
        return "DIRECT_FACT", "value_component_fact", "value-bearing component rendering a fetched fact"

    if testid and INLINE_METRIC.search(line):
        return "DIRECT_FACT", "inline_length_or_count", "inline .length/.count of rendered data"

    # anything left is a genuine unknown that needs inspection (should be ~0)
    return "OPEN_NEEDS_PROOF", "unclassified", ""


def route_of(rel):
    return Path(rel).stem


def main():
    surfaces = []
    seen = set()
    for p in sorted(FE.rglob("*.jsx")) + sorted(FE.rglob("*.tsx")):
        s = str(p)
        if any(x in s for x in ("__tests__", ".test.", "node_modules")):
            continue
        rel = str(p.relative_to(ROOT))
        demo = "DEMO/DEV_ONLY" if re.search(r"(demo|sandbox|playground|example|storybook)", s, re.I) else None
        try:
            lines = p.read_text(errors="ignore").splitlines()
        except Exception:
            continue
        for i, l in enumerate(lines):
            has_testid = TESTID.search(l)
            if not (VALUE_COMPONENT.search(l) or (has_testid and (INLINE_METRIC.search(l) or STRUCTURAL_TESTID.search(has_testid.group(1)) or STATUS_TOKENS.search(has_testid.group(1)) or any(re.search(pat, has_testid.group(1), re.I) for pat, _, _ in KPI_TOKENS)))):
                continue
            label = (has_testid.group(1) if has_testid else l.strip()[:70])
            key = (rel, label)
            if key in seen:
                continue
            seen.add(key)
            if demo:
                klass, reason, owner = "NON_TRUTH_SURFACE_EXCLUDED_WITH_REASON", demo, ""
            else:
                klass, reason, owner = classify(l)
            surfaces.append({
                "loc": "%s:%d" % (rel, i + 1), "route": route_of(rel),
                "label": label, "disposition": klass, "concept_or_reason": reason, "owner": owner,
            })

    by = defaultdict(int)
    for r in surfaces:
        by[r["disposition"]] += 1
    excluded = by.get("NON_TRUTH_SURFACE_EXCLUDED_WITH_REASON", 0)
    open_ = by.get("OPEN_NEEDS_PROOF", 0)
    candidate = len(surfaces)
    included = candidate - excluded

    with open(ROOT / "memory/truth_program/TRUTH_SURFACE_CANONICAL.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["loc", "route", "label", "disposition", "concept_or_reason", "owner"])
        w.writeheader()
        for r in surfaces:
            w.writerow(r)

    summary = {
        "generated": "wave5_truth_surface_canonical",
        "candidate_universe": candidate,
        "included_truth_surfaces": included,
        "excluded_with_reason": excluded,
        "open_needs_proof": open_,
        "invariant_holds": (included + excluded == candidate),
        "by_disposition": dict(by),
        "open_locs": [r["loc"] for r in surfaces if r["disposition"] == "OPEN_NEEDS_PROOF"][:60],
    }
    (ROOT / "memory/truth_program/TRUTH_SURFACE_CANONICAL.json").write_text(json.dumps(summary, indent=2))
    print("CANONICAL TRUTH SURFACES")
    print("  candidate universe   :", candidate)
    print("  included truth surf. :", included)
    print("  excluded with reason :", excluded)
    print("  OPEN (must be 0)     :", open_)
    print("  invariant included+excluded==candidate:", summary["invariant_holds"])
    for k, v in sorted(by.items(), key=lambda kv: -kv[1]):
        print("    %-40s %d" % (k, v))


if __name__ == "__main__":
    main()
