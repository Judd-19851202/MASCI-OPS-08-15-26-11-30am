"""Aggregate every persona finding into a single refinement backlog.

Output: /app/walkthrough_reports/_backlog.json — a single sorted list
of findings across all persona walkthroughs, grouped by kind, ready
for the editorial workflow to consume.

Not telemetry, not analytics — an editorial artifact. Run it from
the command line after each walkthrough pass.
"""
import json
from collections import Counter
from pathlib import Path

REPORT_DIR = Path("/app/walkthrough_reports")

# Order matches the operator-stated priority sequence.
PRIORITY_ORDER = [
    "foreman", "superintendent", "operator", "dispatcher",
    "hr", "safety", "pm", "laborer",
]

# Kinds ranked by editorial-attention weight.
KIND_PRIORITY = [
    "no-escalation-path",
    "voice-drift",
    "missing-coaching",
    "weak-tip",
    "unclear-wording",
    "workflow-confusion",
    "discoverability-gap",
    "mobile-clipping",
    "friction",
    "positive-observation",
]


def collect() -> dict:
    aggregated: list[dict] = []
    per_persona: dict[str, dict] = {}
    for persona in PRIORITY_ORDER:
        path = REPORT_DIR / f"{persona}_findings.json"
        if not path.exists():
            continue
        report = json.loads(path.read_text())
        per_persona[persona] = {
            "step_count": report.get("step_count", 0),
            "finding_count": report.get("finding_count", 0),
            "finding_tally": report.get("finding_tally", {}),
            "device": report.get("device"),
            "finished_at": report.get("finished_at"),
        }
        aggregated.extend(report.get("findings", []))

    # Sort findings by kind-priority then persona-priority.
    def sort_key(f):
        kind_idx = KIND_PRIORITY.index(f["kind"]) if f["kind"] in KIND_PRIORITY else 99
        persona_idx = PRIORITY_ORDER.index(f["persona"]) if f["persona"] in PRIORITY_ORDER else 99
        return (kind_idx, persona_idx, f.get("step", ""))

    aggregated.sort(key=sort_key)

    # Group for easy editorial reading.
    by_kind: dict[str, list] = {}
    for f in aggregated:
        by_kind.setdefault(f["kind"], []).append(f)

    actionable = [f for f in aggregated if f["kind"] != "positive-observation"]
    tally_overall = Counter(f["kind"] for f in aggregated)
    return {
        "generated_for_personas": PRIORITY_ORDER,
        "persona_runs": per_persona,
        "overall_tally": dict(tally_overall),
        "total_findings": len(aggregated),
        "actionable_findings": len(actionable),
        "positive_observations": tally_overall.get("positive-observation", 0),
        "findings_by_kind": by_kind,
        "actionable_in_priority_order": actionable,
    }


def main() -> None:
    backlog = collect()
    out = REPORT_DIR / "_backlog.json"
    out.write_text(json.dumps(backlog, indent=2))
    print(f"[backlog] {backlog['total_findings']} findings · "
          f"{backlog['actionable_findings']} actionable · "
          f"{backlog['positive_observations']} positive")
    print(f"[backlog] tally: {backlog['overall_tally']}")
    print(f"[backlog] written: {out}")
    if backlog["actionable_findings"]:
        print("\nTOP-PRIORITY ACTIONABLE BACKLOG:")
        for f in backlog["actionable_in_priority_order"][:15]:
            print(f"  [{f['kind']:22s}] {f['persona']:15s} {f['step']:35s} :: {f['observation'][:80]}")


if __name__ == "__main__":
    main()
