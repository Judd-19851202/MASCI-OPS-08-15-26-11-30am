"""
TRACK 27.07A · PHASE 1 · Composite Storage Governance Policy
============================================================

This module is the ONE canonical policy definition for R2 storage
governance.  It replaces the obsolete 50 GB heuristic that was
introduced 2026-05-17 as a warn-only free-tier-era placeholder and
gradually promoted to CRITICAL semantics without approval (see the
Track 27.07A Phase 0B audit at
`/app/memory/TRACK_27_07A_PHASE_0B_R2_CAPACITY_POLICY_AUDIT.md`).

Design goals (Phase 1 charter)
------------------------------
* Powerful  — 7 independent dimensions, none masks another.
* Simple    — one canonical implementation, no duplicate policy engine.
* Beautiful — every dimension reports status + reason + evidence +
              recommendation + unknowns.
* Trusted   — no invented statuses; missing evidence surfaces as
              `UNKNOWN` or `POLICY_REQUIRED`, never as a green.
* Proven    — every decision path unit-testable as a pure function.
* Deployable— zero schema/config/env/secret changes.
* Durable   — every threshold documents owner, approval date, purpose,
              evidence, and review cadence.
* Ownership — every UNKNOWN explains WHY; every POLICY_REQUIRED
              names the missing policy.

The seven dimensions
--------------------
1. `technical_capacity`     — bucket size vs documented provider limit.
2. `storage_cost`           — modeled monthly $ vs cost tiers.
3. `growth`                 — 7-day mean daily-delta vs baseline.
4. `certified_waste`        — orphan share from certified classifier.
5. `backup_footprint`       — backup freshness + retention enforcement.
6. `retention_compliance`   — documented retention windows encoded.
7. `evidence_freshness`     — how stale the inputs are.

Composite decision rule
-----------------------
`overall` is NEVER `max(severity)`.  Instead the rule is:

    critical_count = number of dimensions in CRITICAL
    attention_count = number in ATTENTION
    unknown_count   = number in UNKNOWN or POLICY_REQUIRED

    if unknown_count == 7                     → UNKNOWN
    if critical_count >= 2                    → CRITICAL
    if critical_count == 1 or attention_count → ATTENTION
    else                                       → HEALTHY

POLICY_REQUIRED and UNKNOWN never elevate.  They surface as advisory
banners on the operator UI.
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Literal, Optional


# ── Provider-published facts (Cloudflare R2, Feb 2026, US public rates)
# All values here are direct quotes from Cloudflare's public pricing.
# If Cloudflare updates its published pricing, update these constants
# and record the review date in the accompanying policy record below.
R2_USD_PER_GB_MONTH = 0.015
R2_CLASS_A_PER_MILLION_USD = 4.50   # PUT/POST/COPY/LIST/etc.
R2_CLASS_B_PER_MILLION_USD = 0.36   # GET/HEAD/etc.
R2_EGRESS_PER_GB_USD = 0.0
# Cloudflare R2's per-bucket practical soft ceiling.  Buckets larger
# than a few PB require Enterprise support; MASCI is nowhere near this.
# Documenting explicitly so `technical_capacity` never flips RED on
# absolute size until we approach a real provider constraint.
R2_PROVIDER_TECHNICAL_CEILING_GB = 10_000_000.0  # 10 PB soft ceiling


# ── Status vocabulary ────────────────────────────────────────────────
Status = Literal[
    "HEALTHY", "ATTENTION", "CRITICAL",
    "UNKNOWN", "POLICY_REQUIRED",
]

_SEVERITY_ORDER = {
    "HEALTHY": 0,
    "POLICY_REQUIRED": 1,
    "UNKNOWN": 2,
    "ATTENTION": 3,
    "CRITICAL": 4,
}


@dataclass(frozen=True)
class PolicyRecord:
    """Provenance envelope for every policy threshold in the file.

    Every threshold in this module MUST be attached to one of these
    records so that `GET /api/admin/r2/lifecycle/policy` can render the
    full evidence trail for an auditor.
    """
    dimension: str
    owner: str
    approval_date: str          # ISO 8601 date the value was approved
    approval_status: Literal[
        "OPERATOR_APPROVED",
        "PROVISIONAL_FROM_AUDIT",
        "PROVIDER_PUBLISHED",
        "POLICY_REQUIRED",
    ]
    purpose: str
    evidence: str
    review_cadence_days: int
    values: Dict[str, Any] = field(default_factory=dict)
    notes: str = ""


# ── Canonical policy definitions ─────────────────────────────────────
# ONE source of truth.  Every dimension evaluator below reads from this
# dictionary; no magic numbers appear anywhere in the evaluators.
CANONICAL_POLICY: Dict[str, PolicyRecord] = {
    # ─── 1 · Technical capacity ────────────────────────────────────
    "technical_capacity": PolicyRecord(
        dimension="technical_capacity",
        owner="Cloudflare R2 (public docs)",
        approval_date="2026-02-01",
        approval_status="PROVIDER_PUBLISHED",
        purpose=(
            "Compare bucket size against the provider's published "
            "soft ceiling. Bucket size below this ceiling is NEVER "
            "a technical failure — even if operators later prefer a "
            "smaller footprint for cost reasons, that concern lives "
            "in the storage_cost dimension, not here."
        ),
        evidence=(
            "Cloudflare R2 developer docs (Feb 2026): per-bucket "
            "soft ceiling ~10 PB; Enterprise contact required beyond."
        ),
        review_cadence_days=180,
        values={"provider_ceiling_gb": R2_PROVIDER_TECHNICAL_CEILING_GB},
    ),

    # ─── 2 · Storage cost ──────────────────────────────────────────
    "storage_cost": PolicyRecord(
        dimension="storage_cost",
        owner="Track 27.07A Phase 0B audit (provisional)",
        approval_date="2026-02",
        approval_status="PROVISIONAL_FROM_AUDIT",
        purpose=(
            "Escalate on monthly $ spend rather than raw GB. At a "
            "construction-ops platform's scale, R2 cost is trivial "
            "up to ~$30/mo; noticeable at ~$75/mo; likely to require "
            "budget approval above ~$150/mo."
        ),
        evidence=(
            "Track 27.07A Phase 0B §7 Option A. Reviewed against "
            "documented Cloudflare R2 official public list: storage "
            "$0.015 GB-mo, Class A $4.50/M, Class B $0.36/M, egress $0."
        ),
        review_cadence_days=90,
        values={
            "unit_price_usd_per_gb_month": R2_USD_PER_GB_MONTH,
            "class_a_per_million_usd": R2_CLASS_A_PER_MILLION_USD,
            "class_b_per_million_usd": R2_CLASS_B_PER_MILLION_USD,
            "healthy_max_usd_per_month": 30.0,
            "attention_max_usd_per_month": 75.0,
            "critical_min_usd_per_month": 150.0,
        },
        notes=(
            "Cost figures below the 'verified invoice' bar are labelled "
            "OFFICIAL_RATE_ESTIMATE. Operator drop of an invoice will "
            "promote them to VERIFIED_INVOICE."
        ),
    ),

    # ─── 3 · Growth behaviour ──────────────────────────────────────
    "growth": PolicyRecord(
        dimension="growth",
        owner="Track 27.07A Phase 0B audit (provisional)",
        approval_date="2026-02",
        approval_status="PROVISIONAL_FROM_AUDIT",
        purpose=(
            "Detect archive-inflation / runaway-cadence failure modes "
            "by comparing the rolling 7-day mean daily-delta against "
            "the historical baseline computed from the same series."
        ),
        evidence=(
            "PHASE31_3_STORAGE_GROWTH_ANALYSIS.md documents post-iter441 "
            "steady-state at ~2.1 GB/day; pre-iter441 pathological was "
            "~9.6 GB/day (~4.6× baseline)."
        ),
        review_cadence_days=90,
        values={
            "baseline_window_days": 30,
            "recent_window_days": 7,
            "attention_multiplier": 3.0,   # 3× baseline
            "critical_multiplier": 10.0,   # 10× baseline
            "min_samples_required": 5,
        },
    ),

    # ─── 4 · Certified waste ───────────────────────────────────────
    "certified_waste": PolicyRecord(
        dimension="certified_waste",
        owner="services/r2_lifecycle/classification.py",
        approval_date="2026-07-10",
        approval_status="OPERATOR_APPROVED",
        purpose=(
            "Report waste as certified `VERIFIED_ORPHAN` share only. "
            "Never infer orphan status from prefix guesses or file age."
        ),
        evidence=(
            "Track 27.06 classification contract: 10-state pure "
            "classifier backed by `r2_references` scan."
        ),
        review_cadence_days=180,
        values={
            "healthy_max_orphan_pct": 1.0,
            "attention_max_orphan_pct": 5.0,
            "critical_min_orphan_pct": 20.0,
            "classifier_max_age_days_for_confidence": 7,
        },
    ),

    # ─── 5 · Backup footprint ──────────────────────────────────────
    "backup_footprint": PolicyRecord(
        dimension="backup_footprint",
        owner="Track 15.28A tiered retention contract",
        approval_date="2026-05-31",
        approval_status="OPERATOR_APPROVED",
        purpose=(
            "Distinguish protected/expected backup mass from unexpected "
            "growth. HEALTHY when a recent backup succeeded AND the "
            "Cloudflare-side lifecycle rule (90-day auto-expire on "
            "`backups/auto-90d/`) is verified applied."
        ),
        evidence=(
            "backend/lib/r2_retention.py Tier 1/2/3/4 rule and "
            "R2_RETENTION_AUDIT.md 90-day lifecycle rule."
        ),
        review_cadence_days=90,
        values={
            "healthy_backup_max_age_minutes": 60 * 25,     # ≤ 25 h
            "attention_backup_max_age_minutes": 60 * 48,   # 25–48 h
            "expected_prefixes": ("backups/", "complete-backups/",
                                  "MASCI_complete_backup"),
        },
    ),

    # ─── 6 · Retention compliance ──────────────────────────────────
    "retention_compliance": PolicyRecord(
        dimension="retention_compliance",
        owner="OPERATOR (see Phase 0B §5)",
        approval_date="",
        approval_status="POLICY_REQUIRED",
        purpose=(
            "Encode legally-anchored retention windows (OSHA, insurance, "
            "state DOT, contract) so deletion / expiration decisions are "
            "defensible. Platform code does NOT currently encode any "
            "legal retention windows as constants."
        ),
        evidence=(
            "AMENDMENT001_EVIDENCE_HIERARCHY_MATRIX.md (OSHA 29 CFR 1904 "
            "is referenced but no numeric window is encoded); Phase 0B §5."
        ),
        review_cadence_days=180,
        values={
            "required_policy_items": [
                "osha_incident_records_retention_years",
                "contract_project_records_retention_years",
                "insurance_claim_records_retention_years",
                "state_dot_fleet_inspection_retention_years",
                "employee_pii_offboard_retention_years",
                "data_subject_erasure_protocol",
            ],
        },
        notes=(
            "This dimension NEVER goes GREEN until the operator supplies "
            "the missing policy items. It also NEVER goes RED — a "
            "missing policy is a data gap, not a failure."
        ),
    ),

    # ─── 7 · Evidence freshness ────────────────────────────────────
    "evidence_freshness": PolicyRecord(
        dimension="evidence_freshness",
        owner="services/r2_lifecycle/inventory.py",
        approval_date="2026-07-10",
        approval_status="OPERATOR_APPROVED",
        purpose=(
            "Any composite verdict depends on the evidence being fresh. "
            "Stale evidence LOWERS confidence; it never raises it."
        ),
        evidence=(
            "services/r2_lifecycle/inventory.py persists `completed_at` "
            "on every scan row; recovery_dashboard `bucket_usage.ts` is "
            "written after every complete-R2 backup."
        ),
        review_cadence_days=180,
        values={
            "healthy_max_inventory_age_hours": 24,
            "attention_max_inventory_age_hours": 24 * 7,
            "critical_min_inventory_age_hours": 24 * 30,
            "healthy_max_usage_signal_age_hours": 6,
        },
    ),
}


# ── Dimension evaluation ─────────────────────────────────────────────
@dataclass(frozen=True)
class DimensionEvaluation:
    dimension: str
    status: Status
    reason: str
    evidence: Dict[str, Any]
    recommendation: str
    unknowns: List[str]
    policy: Dict[str, Any]   # PolicyRecord serialised

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dimension": self.dimension,
            "status": self.status,
            "reason": self.reason,
            "evidence": self.evidence,
            "recommendation": self.recommendation,
            "unknowns": list(self.unknowns),
            "policy": dict(self.policy),
        }


def _pr_to_dict(pr: PolicyRecord) -> Dict[str, Any]:
    return {
        "dimension": pr.dimension,
        "owner": pr.owner,
        "approval_date": pr.approval_date,
        "approval_status": pr.approval_status,
        "purpose": pr.purpose,
        "evidence": pr.evidence,
        "review_cadence_days": pr.review_cadence_days,
        "values": dict(pr.values),
        "notes": pr.notes,
    }


# ── 1 · Technical capacity ───────────────────────────────────────────
def evaluate_technical_capacity(gb: Optional[float]) -> DimensionEvaluation:
    pr = CANONICAL_POLICY["technical_capacity"]
    ceiling = pr.values["provider_ceiling_gb"]
    if gb is None:
        return DimensionEvaluation(
            dimension=pr.dimension,
            status="UNKNOWN",
            reason="No bucket usage signal available.",
            evidence={"bucket_gb": None, "provider_ceiling_gb": ceiling},
            recommendation=(
                "Trigger a fresh R2 usage probe (e.g. next complete-R2 "
                "backup) so the passive bucket-size row lands in "
                "`backup_health`."
            ),
            unknowns=["bucket_usage_row_missing"],
            policy=_pr_to_dict(pr),
        )
    pct_used = (gb / ceiling) * 100.0 if ceiling else None
    status: Status = "HEALTHY" if gb <= ceiling else "CRITICAL"
    reason = (
        f"Bucket at {gb:.2f} GB / {ceiling:,.0f} GB provider ceiling "
        f"({pct_used:.4f}% used)."
        if pct_used is not None else
        f"Bucket at {gb:.2f} GB."
    )
    recommendation = (
        "" if status == "HEALTHY"
        else "Contact Cloudflare Enterprise support; per-bucket ceiling reached."
    )
    return DimensionEvaluation(
        dimension=pr.dimension,
        status=status,
        reason=reason,
        evidence={
            "bucket_gb": round(gb, 3),
            "provider_ceiling_gb": ceiling,
            "pct_used": round(pct_used, 6) if pct_used is not None else None,
        },
        recommendation=recommendation,
        unknowns=[],
        policy=_pr_to_dict(pr),
    )


# ── 2 · Storage cost ─────────────────────────────────────────────────
def evaluate_storage_cost(
    gb: Optional[float],
    *,
    verified_invoice_usd_per_month: Optional[float] = None,
    class_a_ops_per_month: Optional[int] = None,
    class_b_ops_per_month: Optional[int] = None,
) -> DimensionEvaluation:
    pr = CANONICAL_POLICY["storage_cost"]
    vals = pr.values
    if gb is None and verified_invoice_usd_per_month is None:
        return DimensionEvaluation(
            dimension=pr.dimension,
            status="UNKNOWN",
            reason="No bucket usage signal and no invoice available.",
            evidence={"estimate_kind": None},
            recommendation="Trigger a fresh R2 usage probe or provide an invoice.",
            unknowns=["bucket_usage_row_missing", "no_verified_invoice"],
            policy=_pr_to_dict(pr),
        )

    if verified_invoice_usd_per_month is not None:
        monthly = float(verified_invoice_usd_per_month)
        estimate_kind = "VERIFIED_INVOICE"
    else:
        storage = gb * vals["unit_price_usd_per_gb_month"]
        ops_a = ((class_a_ops_per_month or 0) / 1_000_000.0) * vals["class_a_per_million_usd"]
        ops_b = ((class_b_ops_per_month or 0) / 1_000_000.0) * vals["class_b_per_million_usd"]
        monthly = storage + ops_a + ops_b
        estimate_kind = "OFFICIAL_RATE_ESTIMATE"

    if monthly <= vals["healthy_max_usd_per_month"]:
        status: Status = "HEALTHY"
        reason = (
            f"~${monthly:.2f}/mo ({estimate_kind}) ≤ "
            f"${vals['healthy_max_usd_per_month']:.0f}/mo healthy ceiling."
        )
        rec = ""
    elif monthly <= vals["attention_max_usd_per_month"]:
        status = "ATTENTION"
        reason = (
            f"~${monthly:.2f}/mo ({estimate_kind}) between healthy "
            f"(${vals['healthy_max_usd_per_month']:.0f}) and attention "
            f"(${vals['attention_max_usd_per_month']:.0f}) budget lines."
        )
        rec = "Plan a retention-enforcement review; cost is noticeable but not urgent."
    elif monthly < vals["critical_min_usd_per_month"]:
        status = "ATTENTION"
        reason = (
            f"~${monthly:.2f}/mo ({estimate_kind}) above attention "
            f"(${vals['attention_max_usd_per_month']:.0f}) budget line."
        )
        rec = "Trigger a retention-enforcement pass; approach the critical budget line."
    else:
        status = "CRITICAL"
        reason = (
            f"~${monthly:.2f}/mo ({estimate_kind}) ≥ "
            f"${vals['critical_min_usd_per_month']:.0f}/mo critical budget line."
        )
        rec = "Escalate to budget approval; run retention enforcement immediately."

    unknowns: List[str] = []
    if estimate_kind == "OFFICIAL_RATE_ESTIMATE":
        unknowns.append("no_verified_invoice")

    return DimensionEvaluation(
        dimension=pr.dimension,
        status=status,
        reason=reason,
        evidence={
            "estimate_kind": estimate_kind,
            "monthly_usd": round(monthly, 4),
            "bucket_gb": (round(gb, 3) if gb is not None else None),
            "class_a_ops_per_month": class_a_ops_per_month,
            "class_b_ops_per_month": class_b_ops_per_month,
            "budget_lines": {
                "healthy_max_usd_per_month": vals["healthy_max_usd_per_month"],
                "attention_max_usd_per_month": vals["attention_max_usd_per_month"],
                "critical_min_usd_per_month": vals["critical_min_usd_per_month"],
            },
        },
        recommendation=rec,
        unknowns=unknowns,
        policy=_pr_to_dict(pr),
    )


# ── 3 · Growth behaviour ─────────────────────────────────────────────
def evaluate_growth(daily_deltas_gb: List[float]) -> DimensionEvaluation:
    """`daily_deltas_gb` — chronological list of daily bucket-size deltas
    in GB (positive = growth). Callers pass whatever they have; missing
    days are simply absent from the list."""
    pr = CANONICAL_POLICY["growth"]
    vals = pr.values
    min_samples = vals["min_samples_required"]
    if not daily_deltas_gb or len(daily_deltas_gb) < min_samples:
        return DimensionEvaluation(
            dimension=pr.dimension,
            status="UNKNOWN",
            reason=(
                f"Insufficient samples ({len(daily_deltas_gb)}) — need "
                f"≥ {min_samples} to derive a defensible trend."
            ),
            evidence={"samples": len(daily_deltas_gb)},
            recommendation=(
                "Wait until enough R2 usage rows accumulate in "
                "`backup_health` to derive a rolling baseline."
            ),
            unknowns=["insufficient_samples"],
            policy=_pr_to_dict(pr),
        )

    recent = daily_deltas_gb[-vals["recent_window_days"]:]
    baseline_pool = daily_deltas_gb[:-vals["recent_window_days"]] or daily_deltas_gb
    recent_mean = statistics.fmean(recent)
    baseline_mean = statistics.fmean(baseline_pool)
    # Avoid division by zero when baseline is flat.
    if baseline_mean <= 0.001:
        ratio = float("inf") if recent_mean > 0.001 else 1.0
    else:
        ratio = recent_mean / baseline_mean

    if ratio >= vals["critical_multiplier"]:
        status: Status = "CRITICAL"
        reason = f"Recent growth {recent_mean:.2f} GB/day is {ratio:.1f}× baseline."
        rec = (
            "Investigate archive-inflation cause (cadence surge, "
            "excluded-collection regression, or new large binary uploads)."
        )
    elif ratio >= vals["attention_multiplier"]:
        status = "ATTENTION"
        reason = f"Recent growth {recent_mean:.2f} GB/day is {ratio:.1f}× baseline."
        rec = "Confirm retention rule is enforcing on `backups/auto-90d/`."
    else:
        status = "HEALTHY"
        reason = (
            f"Growth {recent_mean:.2f} GB/day is within "
            f"{vals['attention_multiplier']}× baseline ({baseline_mean:.2f})."
        )
        rec = ""
    return DimensionEvaluation(
        dimension=pr.dimension,
        status=status,
        reason=reason,
        evidence={
            "recent_mean_gb_per_day": round(recent_mean, 3),
            "baseline_mean_gb_per_day": round(baseline_mean, 3),
            "ratio": (round(ratio, 3) if ratio != float("inf") else "inf"),
            "samples": len(daily_deltas_gb),
        },
        recommendation=rec,
        unknowns=[],
        policy=_pr_to_dict(pr),
    )


# ── 4 · Certified waste ──────────────────────────────────────────────
def evaluate_certified_waste(
    orphan_pct: Optional[float],
    classifier_age_days: Optional[float],
) -> DimensionEvaluation:
    pr = CANONICAL_POLICY["certified_waste"]
    vals = pr.values
    if orphan_pct is None or classifier_age_days is None:
        return DimensionEvaluation(
            dimension=pr.dimension,
            status="UNKNOWN",
            reason="Classifier has never produced a snapshot on this pod.",
            evidence={
                "orphan_pct": orphan_pct,
                "classifier_age_days": classifier_age_days,
            },
            recommendation="Run `POST /api/admin/r2/lifecycle/scan` to produce a classification snapshot.",
            unknowns=["no_classifier_snapshot"],
            policy=_pr_to_dict(pr),
        )
    if classifier_age_days > vals["classifier_max_age_days_for_confidence"]:
        return DimensionEvaluation(
            dimension=pr.dimension,
            status="UNKNOWN",
            reason=(
                f"Classifier snapshot is {classifier_age_days:.1f}d old — "
                f"older than the "
                f"{vals['classifier_max_age_days_for_confidence']}d confidence window."
            ),
            evidence={
                "orphan_pct": round(orphan_pct, 3),
                "classifier_age_days": round(classifier_age_days, 2),
            },
            recommendation="Re-run `POST /api/admin/r2/lifecycle/scan`.",
            unknowns=["classifier_stale"],
            policy=_pr_to_dict(pr),
        )

    if orphan_pct <= vals["healthy_max_orphan_pct"]:
        status: Status = "HEALTHY"
        rec = ""
    elif orphan_pct <= vals["attention_max_orphan_pct"]:
        status = "ATTENTION"
        rec = "Review orphan candidates in Storage & Recovery → R2 Lifecycle."
    elif orphan_pct < vals["critical_min_orphan_pct"]:
        status = "ATTENTION"
        rec = "Prepare a certified quarantine batch for operator approval."
    else:
        status = "CRITICAL"
        rec = (
            "Certified orphan share is very high — schedule an operator "
            "review session for quarantine → hard-delete workflow."
        )
    return DimensionEvaluation(
        dimension=pr.dimension,
        status=status,
        reason=(
            f"VERIFIED_ORPHAN share {orphan_pct:.2f}% "
            f"(classifier snapshot {classifier_age_days:.1f}d old)."
        ),
        evidence={
            "orphan_pct": round(orphan_pct, 3),
            "classifier_age_days": round(classifier_age_days, 2),
            "thresholds": {
                "healthy_max": vals["healthy_max_orphan_pct"],
                "attention_max": vals["attention_max_orphan_pct"],
                "critical_min": vals["critical_min_orphan_pct"],
            },
        },
        recommendation=rec,
        unknowns=[],
        policy=_pr_to_dict(pr),
    )


# ── 5 · Backup footprint ─────────────────────────────────────────────
def evaluate_backup_footprint(
    last_backup_age_minutes: Optional[float],
    lifecycle_rule_applied: Optional[bool],
) -> DimensionEvaluation:
    pr = CANONICAL_POLICY["backup_footprint"]
    vals = pr.values
    unknowns: List[str] = []
    if last_backup_age_minutes is None:
        return DimensionEvaluation(
            dimension=pr.dimension,
            status="UNKNOWN",
            reason="No backup age evidence.",
            evidence={"lifecycle_rule_applied": lifecycle_rule_applied},
            recommendation="Trigger a fresh complete-R2 backup.",
            unknowns=["no_backup_age"],
            policy=_pr_to_dict(pr),
        )

    if last_backup_age_minutes <= vals["healthy_backup_max_age_minutes"]:
        base_status: Status = "HEALTHY"
        reason = f"Last backup {last_backup_age_minutes:.0f}m old."
        rec = ""
    elif last_backup_age_minutes <= vals["attention_backup_max_age_minutes"]:
        base_status = "ATTENTION"
        reason = f"Last backup {last_backup_age_minutes:.0f}m old — beyond healthy window."
        rec = "Verify the next scheduled backup completes on cadence."
    else:
        base_status = "CRITICAL"
        reason = f"Last backup {last_backup_age_minutes:.0f}m old — beyond attention window."
        rec = "Trigger a fresh backup and verify the scheduler is running."

    # The lifecycle-rule signal DE-ESCALATES: a healthy backup with an
    # unverified lifecycle rule is ATTENTION (retention-enforcement gap).
    if lifecycle_rule_applied is False:
        base_status = "ATTENTION" if base_status == "HEALTHY" else base_status
        reason += " Cloudflare-side 90-day lifecycle rule reported NOT applied."
        rec = rec or "Rotate R2 API token to include `lifecycle:write`; apply the 90-day rule."
    elif lifecycle_rule_applied is None:
        unknowns.append("lifecycle_rule_status_unknown")
        base_status = "ATTENTION" if base_status == "HEALTHY" else base_status
        reason += " Cloudflare-side lifecycle rule state is UNKNOWN."
        rec = rec or (
            "Verify Cloudflare-side lifecycle rule is applied "
            "(`python3 /app/scripts/r2_lifecycle_apply.py --show`)."
        )

    return DimensionEvaluation(
        dimension=pr.dimension,
        status=base_status,
        reason=reason,
        evidence={
            "last_backup_age_minutes": (
                round(last_backup_age_minutes, 1)
                if last_backup_age_minutes is not None else None
            ),
            "lifecycle_rule_applied": lifecycle_rule_applied,
        },
        recommendation=rec,
        unknowns=unknowns,
        policy=_pr_to_dict(pr),
    )


# ── 6 · Retention compliance ─────────────────────────────────────────
def evaluate_retention_compliance(
    encoded_windows: Dict[str, Any],
) -> DimensionEvaluation:
    """`encoded_windows` is the set of retention windows the platform
    currently ENCODES as constants (not merely references)."""
    pr = CANONICAL_POLICY["retention_compliance"]
    required = pr.values["required_policy_items"]
    missing = [item for item in required if not encoded_windows.get(item)]
    if not missing:
        return DimensionEvaluation(
            dimension=pr.dimension,
            status="HEALTHY",
            reason="All required retention policies are encoded.",
            evidence={"encoded_windows": encoded_windows},
            recommendation="",
            unknowns=[],
            policy=_pr_to_dict(pr),
        )
    return DimensionEvaluation(
        dimension=pr.dimension,
        status="POLICY_REQUIRED",
        reason=(
            f"{len(missing)} required retention policy item(s) missing "
            f"from platform config."
        ),
        evidence={"encoded_windows": encoded_windows, "missing_items": missing},
        recommendation=(
            "Operator must supply retention windows for the missing items "
            "(see Phase 0B §5.2). Encode as constants in a follow-up track."
        ),
        unknowns=missing,
        policy=_pr_to_dict(pr),
    )


# ── 7 · Evidence freshness ───────────────────────────────────────────
def evaluate_evidence_freshness(
    inventory_age_hours: Optional[float],
    usage_signal_age_hours: Optional[float],
) -> DimensionEvaluation:
    pr = CANONICAL_POLICY["evidence_freshness"]
    vals = pr.values
    unknowns: List[str] = []
    if inventory_age_hours is None and usage_signal_age_hours is None:
        return DimensionEvaluation(
            dimension=pr.dimension,
            status="UNKNOWN",
            reason="No inventory scan and no usage signal recorded.",
            evidence={},
            recommendation="Run `POST /api/admin/r2/lifecycle/scan`.",
            unknowns=["no_evidence_timestamps"],
            policy=_pr_to_dict(pr),
        )

    if inventory_age_hours is None:
        unknowns.append("no_inventory_snapshot")
    if usage_signal_age_hours is None:
        unknowns.append("no_usage_signal")

    # Score against inventory age primarily; usage signal is a soft signal.
    inv = inventory_age_hours if inventory_age_hours is not None else 10**9
    use = usage_signal_age_hours if usage_signal_age_hours is not None else 10**9

    if inv >= vals["critical_min_inventory_age_hours"]:
        status: Status = "CRITICAL"
        reason = f"Inventory snapshot is {inv/24:.1f}d old — beyond critical window."
        rec = "Re-run `POST /api/admin/r2/lifecycle/scan` before trusting any waste/growth signals."
    elif inv >= vals["attention_max_inventory_age_hours"]:
        status = "ATTENTION"
        reason = f"Inventory snapshot is {inv/24:.1f}d old — beyond healthy window."
        rec = "Schedule a fresh lifecycle scan."
    elif inv >= vals["healthy_max_inventory_age_hours"]:
        status = "ATTENTION"
        reason = f"Inventory snapshot is {inv:.1f}h old — beyond 24h healthy window."
        rec = "Schedule a fresh lifecycle scan today."
    elif use >= vals["healthy_max_usage_signal_age_hours"]:
        status = "ATTENTION"
        reason = f"Bucket usage signal is {use:.1f}h old — beyond {vals['healthy_max_usage_signal_age_hours']}h freshness window."
        rec = "Trigger the next complete-R2 backup so the passive usage probe refires."
    else:
        status = "HEALTHY"
        reason = (
            f"Inventory {inv:.1f}h · usage-signal {use:.1f}h — within "
            f"freshness windows."
        )
        rec = ""

    return DimensionEvaluation(
        dimension=pr.dimension,
        status=status,
        reason=reason,
        evidence={
            "inventory_age_hours": (
                round(inv, 2) if inventory_age_hours is not None else None
            ),
            "usage_signal_age_hours": (
                round(use, 2) if usage_signal_age_hours is not None else None
            ),
        },
        recommendation=rec,
        unknowns=unknowns,
        policy=_pr_to_dict(pr),
    )


# ── Composite aggregator ─────────────────────────────────────────────
@dataclass(frozen=True)
class CompositeVerdict:
    status: Status
    reason: str
    dimensions: List[Dict[str, Any]]
    counts: Dict[str, int]
    recommendation: str
    unknowns: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "reason": self.reason,
            "dimensions": list(self.dimensions),
            "counts": dict(self.counts),
            "recommendation": self.recommendation,
            "unknowns": list(self.unknowns),
        }


def aggregate(dimensions: List[DimensionEvaluation]) -> CompositeVerdict:
    """Pure aggregator — evidence-driven, not max(severity).

    Rule
    ----
    * If ALL dimensions are UNKNOWN or POLICY_REQUIRED → UNKNOWN.
    * Elif ≥ 2 dimensions are CRITICAL → CRITICAL.
    * Elif ANY dimension is CRITICAL or ATTENTION → ATTENTION.
    * Elif ALL dimensions HEALTHY or POLICY_REQUIRED → HEALTHY.
    * POLICY_REQUIRED and UNKNOWN never elevate; they surface via
      `unknowns` on the returned verdict.
    """
    counts = {"HEALTHY": 0, "ATTENTION": 0, "CRITICAL": 0,
              "UNKNOWN": 0, "POLICY_REQUIRED": 0}
    for d in dimensions:
        counts[d.status] += 1

    critical = counts["CRITICAL"]
    attention = counts["ATTENTION"]
    healthy = counts["HEALTHY"]
    unknown = counts["UNKNOWN"] + counts["POLICY_REQUIRED"]

    if unknown == len(dimensions):
        status: Status = "UNKNOWN"
        reason = "All dimensions are UNKNOWN or POLICY_REQUIRED — cannot judge."
    elif critical >= 2:
        status = "CRITICAL"
        reason = (
            f"{critical} dimensions CRITICAL — composite CRITICAL "
            "(≥2 critical signals required)."
        )
    elif critical >= 1 or attention >= 1:
        status = "ATTENTION"
        reason = (
            f"{critical} CRITICAL, {attention} ATTENTION, {healthy} HEALTHY — "
            "composite ATTENTION."
        )
    else:
        status = "HEALTHY"
        reason = (
            f"{healthy} HEALTHY, {counts['POLICY_REQUIRED']} POLICY_REQUIRED — "
            "composite HEALTHY."
        )

    # Recommendation: first non-empty per-dimension recommendation
    # ordered by severity of that dimension.
    ordered = sorted(
        dimensions,
        key=lambda d: -_SEVERITY_ORDER.get(d.status, 0),
    )
    recommendation = next(
        (d.recommendation for d in ordered if d.recommendation),
        "",
    )

    unknowns: List[str] = []
    for d in dimensions:
        for u in d.unknowns:
            unknowns.append(f"{d.dimension}:{u}")

    return CompositeVerdict(
        status=status,
        reason=reason,
        dimensions=[d.to_dict() for d in dimensions],
        counts=counts,
        recommendation=recommendation,
        unknowns=unknowns,
    )


def policy_manifest() -> Dict[str, Any]:
    """Public representation of the canonical policy — exposed via
    `GET /api/admin/r2/lifecycle/policy` so an auditor can see the
    exact provenance of every threshold in use."""
    return {
        "version": "27.07A.P1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "records": {k: _pr_to_dict(v) for k, v in CANONICAL_POLICY.items()},
        "provider_facts": {
            "r2_usd_per_gb_month": R2_USD_PER_GB_MONTH,
            "r2_class_a_per_million_usd": R2_CLASS_A_PER_MILLION_USD,
            "r2_class_b_per_million_usd": R2_CLASS_B_PER_MILLION_USD,
            "r2_egress_per_gb_usd": R2_EGRESS_PER_GB_USD,
            "r2_provider_technical_ceiling_gb": R2_PROVIDER_TECHNICAL_CEILING_GB,
        },
        "governance_note": (
            "This is the ONE canonical R2 storage policy. Any additional "
            "storage policy engine, threshold constant, or evaluator "
            "outside this module is a duplicate and MUST be removed."
        ),
    }
