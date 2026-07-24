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


def compute_backup_trust_score(
    *,
    hourly_disabled: bool,
    newest_r2_age_hours: float | None,
    restore_drill_age_days: float | None,
    restore_drill_ok: bool,
    integrity_ok: bool,
    overlap_blocked: bool,
    active_failures_7d: int,
    bucket_usage_status: str,
) -> Dict[str, Any]:
    inputs: List[Dict[str, Any]] = []
    score = 100

    if hourly_disabled:
        score -= 12
        inputs.append({"code": "hourly_disabled", "penalty": 12, "reason": "Hourly complete R2 remains disabled by safety lock"})
    if newest_r2_age_hours is None:
        score -= 30
        inputs.append({"code": "r2_missing", "penalty": 30, "reason": "No recent complete R2 archive evidence found"})
    elif newest_r2_age_hours > 36:
        score -= 25
        inputs.append({"code": "r2_stale", "penalty": 25, "reason": f"Newest complete R2 archive is stale ({newest_r2_age_hours:.1f}h)"})
    elif newest_r2_age_hours > 24:
        score -= 10
        inputs.append({"code": "r2_aging", "penalty": 10, "reason": f"Newest complete R2 archive is aging ({newest_r2_age_hours:.1f}h)"})
    if not integrity_ok:
        score -= 25
        inputs.append({"code": "integrity_missing", "penalty": 25, "reason": "Manifest or integrity evidence is missing"})
    if not restore_drill_ok:
        score -= 25
        inputs.append({"code": "restore_drill_failed", "penalty": 25, "reason": "Restore drill missing or failed"})
    elif restore_drill_age_days is not None and restore_drill_age_days > 14:
        score -= 12
        inputs.append({"code": "restore_drill_stale", "penalty": 12, "reason": f"Restore drill evidence is stale ({restore_drill_age_days:.1f}d)"})
    if overlap_blocked:
        score -= 8
        inputs.append({"code": "overlap_guard_triggered", "penalty": 8, "reason": "Backup/restore overlap guard was triggered"})
    if active_failures_7d:
        penalty = min(20, active_failures_7d * 5)
        score -= penalty
        inputs.append({"code": "failures_7d", "penalty": penalty, "reason": f"{active_failures_7d} backup failure event(s) in last 7d"})
    if bucket_usage_status == "AMBER":
        score -= 8
        inputs.append({"code": "bucket_usage_amber", "penalty": 8, "reason": "R2 usage above warning threshold"})
    elif bucket_usage_status == "RED":
        score -= 20
        inputs.append({"code": "bucket_usage_red", "penalty": 20, "reason": "R2 usage above alert threshold"})

    score = max(0, min(100, score))
    if score >= 85:
        band = "green"
        label = "Trusted"
    elif score >= 60:
        band = "amber"
        label = "Missing evidence"
    else:
        band = "red"
        label = "Not trusted"
    return {
        "trust_score": score,
        "score_band": band,
        "score_band_label": label,
        "score_reason": inputs[0]["reason"] if inputs else "All backup trust signals are healthy",
        "score_inputs": inputs,
    }
