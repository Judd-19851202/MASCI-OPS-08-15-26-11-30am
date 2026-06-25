"""TRACK 15.76B · Categorized Trust Score.

Replaces the flat-penalty score with a **7-category breakdown** so
the operator can see *which* subsystem is hurting the score. Pure,
deterministic — same inputs produce the same numbers. Every
deduction names the evidence (workflow/finding/category) so the
``"Why isn't this 100?"`` panel can render the operator's
remediation list with zero magic.

Categories (each starts at 100, dropped by category-specific evidence):

  - workflow_health        — Trust Spine workflow band rollup
  - notification_delivery  — Resend/email queue + provider acceptance
  - routing_integrity      — PM/Co-PM resolvability, critical routes
  - master_data            — Employees / Equipment / Vendors integrity
  - infrastructure         — Backup age, scheduler health, DB indexes
  - security               — Auth + session integrity (placeholder for now)
  - audit_integrity        — Unknown audit status, missing audit rows

The overall ``trust_score`` is the **weighted minimum** of these
categories so a single failing category cannot be hidden by
high scores elsewhere. Weights mirror operational impact.
"""
from __future__ import annotations

from typing import Any, Dict, List


CATEGORY_WEIGHTS: Dict[str, int] = {
    "workflow_health":      25,
    "routing_integrity":    20,
    "notification_delivery": 15,
    "master_data":          10,
    "audit_integrity":      10,
    "infrastructure":       10,
    "security":             10,
}


def _band_from_score(score: int) -> str:
    if score >= 85:
        return "green"
    if score >= 60:
        return "amber"
    return "red"


def compute_categorized_score(
    *,
    workflows: List[Dict[str, Any]],
    master_data_findings: List[Dict[str, Any]] | None = None,
    unknown_audit_count_24h: int = 0,
    silent_failure_count_24h: int = 0,
    missing_critical_routes: int = 0,
    notification_failed_24h: int = 0,
    notification_total_24h: int = 0,
    backup_age_hours: float | None = None,
    scheduler_healthy: bool = True,
    auth_healthy: bool = True,
) -> Dict[str, Any]:
    """Return ``{trust_score, score_band, categories: {...}, score_inputs}``."""
    master_data_findings = master_data_findings or []
    categories: Dict[str, Dict[str, Any]] = {}

    # ── 1 · Workflow Health ──────────────────────────────────────
    red = [w for w in workflows if w.get("band") == "red"]
    amber = [w for w in workflows if w.get("band") == "amber"]
    idle = [w for w in workflows if w.get("band") == "amber-no-activity"]
    wh = 100
    wh_inputs: List[Dict[str, Any]] = []
    if red:
        pen = 25 * len(red)
        wh -= pen
        wh_inputs.append({
            "penalty": pen,
            "label": (
                f"{len(red)} workflow(s) failing: "
                + ", ".join(
                    (w.get("workflow") or "unknown") for w in red[:4]
                )
            ),
            "evidence": [w.get("workflow") for w in red],
        })
    if amber:
        pen = 8 * len(amber)
        wh -= pen
        wh_inputs.append({
            "penalty": pen,
            "label": (
                f"{len(amber)} workflow(s) missing expected stages: "
                + ", ".join(
                    (w.get("workflow") or "unknown") for w in amber[:4]
                )
            ),
            "evidence": [w.get("workflow") for w in amber],
        })
    if idle:
        pen = min(20, 2 * len(idle))
        wh -= pen
        wh_inputs.append({
            "penalty": pen,
            "label": (
                f"{len(idle)} workflow(s) idle in last 24h — "
                "confidence reduced (not a failure)"
            ),
            "evidence": [w.get("workflow") for w in idle],
        })
    # TRACK 15.77 · Gate 6 — any RED workflow forces workflow_health
    # into the RED band regardless of the residual numeric score. The
    # alternative (relying on the numeric drop) allowed a single
    # failing workflow to leak through as GREEN.
    wh_cat = _cat(wh, wh_inputs)
    if red:
        wh_cat["band"] = "red"
        if wh_cat["score"] > 59:
            wh_cat["score"] = 59
    categories["workflow_health"] = wh_cat

    # ── 2 · Routing Integrity ────────────────────────────────────
    ri = 100
    ri_inputs: List[Dict[str, Any]] = []
    pm_findings = [
        f for f in master_data_findings if f.get("code") == "pm_missing_route"
    ]
    if pm_findings:
        cnt = sum(f.get("count", 0) for f in pm_findings)
        pen = min(70, 15 * cnt)
        ri -= pen
        ri_inputs.append({
            "penalty": pen,
            "label": (
                f"{cnt} active project(s) have no resolvable PM/Co-PM "
                "email — every notification on these projects will "
                "dead-letter."
            ),
            "evidence": pm_findings[0].get("samples", []),
        })
    if missing_critical_routes:
        pen = 20 * missing_critical_routes
        ri -= pen
        ri_inputs.append({
            "penalty": pen,
            "label": (
                f"{missing_critical_routes} critical email route(s) "
                "missing — failures cannot be routed safely"
            ),
            "evidence": [],
        })
    categories["routing_integrity"] = _cat(ri, ri_inputs)

    # ── 3 · Notification Delivery ────────────────────────────────
    nd = 100
    nd_inputs: List[Dict[str, Any]] = []
    if notification_failed_24h:
        rate = (
            notification_failed_24h / max(1, notification_total_24h)
        )
        pen = min(60, int(rate * 100) + 10 * notification_failed_24h)
        nd -= pen
        nd_inputs.append({
            "penalty": pen,
            "label": (
                f"{notification_failed_24h} provider failure(s) on "
                f"{notification_total_24h} attempts in last 24h"
            ),
            "evidence": [],
        })
    categories["notification_delivery"] = _cat(nd, nd_inputs)

    # ── 4 · Master Data ──────────────────────────────────────────
    md = 100
    md_inputs: List[Dict[str, Any]] = []
    md_red = [
        f for f in master_data_findings
        if f.get("band") == "red" and f.get("code") != "pm_missing_route"
    ]
    md_amber = [f for f in master_data_findings if f.get("band") == "amber"]
    if md_red:
        pen = 25 * len(md_red)
        md -= pen
        md_inputs.append({
            "penalty": pen,
            "label": "; ".join(f["summary"] for f in md_red[:3]),
            "evidence": [f.get("code") for f in md_red],
        })
    for f in md_amber:
        pen = 5
        md -= pen
        md_inputs.append({
            "penalty": pen,
            "label": f.get("summary", ""),
            "evidence": f.get("samples", [])[:3],
        })
    categories["master_data"] = _cat(md, md_inputs)

    # ── 5 · Infrastructure ───────────────────────────────────────
    inf = 100
    inf_inputs: List[Dict[str, Any]] = []
    if backup_age_hours is not None and backup_age_hours > 36:
        pen = min(50, int((backup_age_hours - 36) // 6) * 10 + 10)
        inf -= pen
        inf_inputs.append({
            "penalty": pen,
            "label": (
                f"last successful backup is {int(backup_age_hours)}h "
                "old (target ≤ 36h)"
            ),
            "evidence": [],
        })
    if not scheduler_healthy:
        inf -= 30
        inf_inputs.append({
            "penalty": 30,
            "label": "background scheduler is not healthy",
            "evidence": [],
        })
    categories["infrastructure"] = _cat(inf, inf_inputs)

    # ── 6 · Security ─────────────────────────────────────────────
    sec = 100
    sec_inputs: List[Dict[str, Any]] = []
    if not auth_healthy:
        sec -= 50
        sec_inputs.append({
            "penalty": 50,
            "label": "authentication subsystem is reporting degraded",
            "evidence": [],
        })
    categories["security"] = _cat(sec, sec_inputs)

    # ── 7 · Audit Integrity ──────────────────────────────────────
    ai = 100
    ai_inputs: List[Dict[str, Any]] = []
    if unknown_audit_count_24h:
        pen = min(50, 5 * unknown_audit_count_24h)
        ai -= pen
        ai_inputs.append({
            "penalty": pen,
            "label": (
                f"{unknown_audit_count_24h} audit row(s) with unknown "
                "status in last 24h"
            ),
            "evidence": [],
        })
    if silent_failure_count_24h:
        pen = 10 * silent_failure_count_24h
        ai -= pen
        ai_inputs.append({
            "penalty": pen,
            "label": (
                f"{silent_failure_count_24h} silent failure(s) "
                "(failed events with no remediation hint)"
            ),
            "evidence": [],
        })
    categories["audit_integrity"] = _cat(ai, ai_inputs)

    # ── Roll-up ──────────────────────────────────────────────────
    # Weighted average + hard cap: overall score cannot exceed the
    # lowest category by more than 10 points. This implements the
    # "single failing category cannot be hidden" rule.
    weighted = 0
    total_w = 0
    for k, w in CATEGORY_WEIGHTS.items():
        weighted += categories[k]["score"] * w
        total_w += w
    overall = round(weighted / total_w) if total_w else 0
    min_cat_score = min(c["score"] for c in categories.values())
    overall = min(overall, min_cat_score + 10)
    overall = max(0, min(100, overall))
    band = _band_from_score(overall)

    # Flatten the top 5 score_inputs for the headline panel.
    flat_inputs: List[Dict[str, Any]] = []
    for key in CATEGORY_WEIGHTS.keys():
        for inp in categories[key]["inputs"]:
            flat_inputs.append({
                "category": key,
                "penalty": inp["penalty"],
                "reason": inp["label"],
                "evidence": inp["evidence"],
            })
    flat_inputs.sort(key=lambda i: i["penalty"], reverse=True)

    if any(c["band"] == "red" for c in categories.values()) and overall >= 60:
        overall = 59
        band = "red"
    if any(c["band"] == "amber" for c in categories.values()) and overall == 100:
        overall = 99
        band = "amber"

    return {
        "trust_score": overall,
        "score_band": band,
        "score_band_label": {
            "green": "Trusted",
            "amber": "Missing evidence",
            "red": "Failing",
        }[band],
        "score_reason": (
            flat_inputs[0]["reason"] if flat_inputs
            else "all monitored subsystems healthy"
        ),
        "categories": categories,
        "score_inputs": flat_inputs[:8],
    }


def _cat(score: int, inputs: List[Dict[str, Any]]) -> Dict[str, Any]:
    score = max(0, min(100, score))
    return {
        "score": score,
        "band": _band_from_score(score),
        "inputs": inputs,
    }
