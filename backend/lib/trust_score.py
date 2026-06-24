"""TRACK 15.76A · Platform Trust Score.

A **transparent, evidence-backed** scoring engine that converts the
Trust Spine + Master-Data + Audit signals into a single 0-100 trust
score for the operator. The score is **deterministic**: pass the same
inputs in and you get the same number out. No magic constants hidden
in code — every penalty is named in ``score_inputs`` so the operator
can read *why* the score is what it is.

Score model (max 100, lower is worse):

  Start at 100.
  - For each RED workflow band:               -25  (capped to drop to <60)
  - For each AMBER workflow with missing
    expected stages but recent activity:      -8
  - For each AMBER-NO-ACTIVITY workflow:      -2   (confidence reduction
                                                  only, not failure)
  - For each unknown-status audit row in 24h: -5
  - For each silent failure detected
    (failed event with no remediation):       -10
  - For each master-data RED finding:         -15
  - For each master-data AMBER finding:       -5
  - For each missing critical route:          -20

Bands:
  >=85   GREEN  "Trusted"
  >=60   AMBER  "Missing evidence"
  <60    RED    "Failing"

Hard rules:
  - A workflow in RED **caps** the score at 59 (cannot be green).
  - An unknown audit status **caps** at 79 (cannot be 100 / green).
  - All-green recent evidence with zero failures → 100.
"""
from __future__ import annotations

from typing import Any, Dict, List


def compute_score(
    *,
    workflows: List[Dict[str, Any]],
    master_data_findings: List[Dict[str, Any]] | None = None,
    unknown_audit_count_24h: int = 0,
    silent_failure_count_24h: int = 0,
    missing_critical_routes: List[str] | None = None,
) -> Dict[str, Any]:
    """Pure scoring function. Returns ``{trust_score, score_band,
    score_reason, score_inputs}``."""
    master_data_findings = master_data_findings or []
    missing_critical_routes = missing_critical_routes or []

    inputs: List[Dict[str, Any]] = []
    score = 100

    red_count = sum(1 for w in workflows if w.get("band") == "red")
    amber_evidence_count = sum(1 for w in workflows if w.get("band") == "amber")
    amber_idle_count = sum(
        1 for w in workflows if w.get("band") == "amber-no-activity"
    )
    green_count = sum(1 for w in workflows if w.get("band") == "green")

    if red_count:
        penalty = 25 * red_count
        score -= penalty
        inputs.append({
            "code": "workflow_red",
            "penalty": penalty,
            "reason": f"{red_count} workflow(s) in RED band",
        })
    if amber_evidence_count:
        penalty = 8 * amber_evidence_count
        score -= penalty
        inputs.append({
            "code": "workflow_amber",
            "penalty": penalty,
            "reason": (
                f"{amber_evidence_count} workflow(s) submitted records "
                "but missed expected lifecycle stages"
            ),
        })
    if amber_idle_count:
        penalty = 2 * amber_idle_count
        score -= penalty
        inputs.append({
            "code": "workflow_idle",
            "penalty": penalty,
            "reason": (
                f"{amber_idle_count} workflow(s) idle in last 24h — "
                "confidence reduced (not a failure)"
            ),
        })

    if unknown_audit_count_24h:
        penalty = 5 * unknown_audit_count_24h
        score -= penalty
        inputs.append({
            "code": "audit_unknown",
            "penalty": penalty,
            "reason": (
                f"{unknown_audit_count_24h} audit row(s) with unknown "
                "status in last 24h"
            ),
        })

    if silent_failure_count_24h:
        penalty = 10 * silent_failure_count_24h
        score -= penalty
        inputs.append({
            "code": "silent_failure",
            "penalty": penalty,
            "reason": (
                f"{silent_failure_count_24h} silent failure(s) "
                "(failed event with no remediation)"
            ),
        })

    md_red = sum(1 for f in master_data_findings if f.get("band") == "red")
    md_amber = sum(1 for f in master_data_findings if f.get("band") == "amber")
    if md_red:
        penalty = 15 * md_red
        score -= penalty
        inputs.append({
            "code": "master_data_red",
            "penalty": penalty,
            "reason": (
                f"{md_red} master-data finding(s) impacting active workflows"
            ),
        })
    if md_amber:
        penalty = 5 * md_amber
        score -= penalty
        inputs.append({
            "code": "master_data_amber",
            "penalty": penalty,
            "reason": f"{md_amber} master-data drift finding(s) (guarded)",
        })

    if missing_critical_routes:
        penalty = 20 * len(missing_critical_routes)
        score -= penalty
        inputs.append({
            "code": "missing_route",
            "penalty": penalty,
            "reason": (
                "missing critical route(s): "
                + ", ".join(missing_critical_routes[:5])
            ),
        })

    # Hard caps (no fake green).
    if red_count and score >= 60:
        score = 59
        inputs.append({
            "code": "cap_red",
            "penalty": 0,
            "reason": "score capped at 59 because a workflow is RED",
        })
    if unknown_audit_count_24h and score >= 80:
        score = 79
        inputs.append({
            "code": "cap_unknown_audit",
            "penalty": 0,
            "reason": "score capped at 79 because of unknown audit status",
        })

    # Clamp.
    if score < 0:
        score = 0
    if score > 100:
        score = 100

    if score >= 85:
        band = "green"
        band_label = "Trusted"
    elif score >= 60:
        band = "amber"
        band_label = "Missing evidence"
    else:
        band = "red"
        band_label = "Failing"

    if not inputs and green_count:
        reason = (
            f"all {green_count} active workflow(s) fully verified; no "
            "failures, no missing evidence"
        )
    elif inputs:
        reason = inputs[0]["reason"]
    else:
        reason = "no workflow activity yet in the last 24h"

    return {
        "trust_score": score,
        "score_band": band,
        "score_band_label": band_label,
        "score_reason": reason,
        "score_inputs": inputs,
    }
