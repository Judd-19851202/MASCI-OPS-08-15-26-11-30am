"""
TRACK 27.07A · PHASE 1 · Composite Storage Governance Policy · Regression Contract.

Locks the mission gates of the Phase 1 charter:

Pillar 1 · Powerful     — 7 independent dimensions.
Pillar 2 · Simple       — one canonical policy definition.
Pillar 3 · Beautiful    — every dimension reports reason + evidence + recommendation.
Pillar 4 · Trusted      — no invented statuses; missing evidence surfaces as UNKNOWN / POLICY_REQUIRED.
Pillar 5 · Proven       — deterministic pure functions, unit-testable.
Pillar 6 · Deployable   — zero schema/config/env changes.
Pillar 7 · Durable      — every threshold owns a PolicyRecord with provenance.
Pillar 8 · Ownership    — every UNKNOWN explains WHY.

These tests are permanent. Any future edit that regresses one of these
contracts MUST be treated as a Phase 1 charter breach.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from services.r2_lifecycle.policy import (
    CANONICAL_POLICY,
    R2_PROVIDER_TECHNICAL_CEILING_GB,
    R2_USD_PER_GB_MONTH,
    aggregate,
    evaluate_backup_footprint,
    evaluate_certified_waste,
    evaluate_evidence_freshness,
    evaluate_growth,
    evaluate_retention_compliance,
    evaluate_storage_cost,
    evaluate_technical_capacity,
    policy_manifest,
)


# ── Pillar 2 · The 50 GB heuristic is fully retired from canonical code ───
def test_50gb_heuristic_removed_from_health_module():
    src = Path("/app/backend/services/r2_lifecycle/health.py").read_text()
    # The retired constants must not appear as hardcoded literals bound
    # to warn_gb / alert_gb anywhere in the canonical health module.
    assert "warn_gb, alert_gb = 45.0, 50.0" not in src, (
        "TRACK 27.07A P1 regression: the retired 45/50 GB hardcoded pair "
        "must not reappear in services/r2_lifecycle/health.py."
    )
    assert not re.search(
        r"^\s*warn_gb\s*=\s*45(\.\d+)?\s*$",
        src, flags=re.MULTILINE,
    )
    assert not re.search(
        r"^\s*alert_gb\s*=\s*50(\.\d+)?\s*$",
        src, flags=re.MULTILINE,
    )


def test_recovery_dashboard_pill_no_longer_escalates_on_bucket_status():
    src = Path("/app/backend/routes/recovery_dashboard.py").read_text()
    # The obsolete bucket_usage_status → RED / AMBER escalation must
    # be retired from the pill computation.
    assert 'if bucket_usage_status == "RED":' not in src
    assert 'if bucket_usage_status == "AMBER":' not in src


def test_occ_recovery_snapshot_no_longer_emits_bucket_reason_codes():
    src = Path("/app/backend/routes/occ_health_aggregator.py").read_text()
    # bucket_over_alert / bucket_over_warn reason codes are retired
    # from the recovery-snapshot evaluator (they now live on the
    # storage_health card via the composite policy verdict).
    # We tolerate the strings appearing inside the retirement comment;
    # what matters is that no active branch assigns those reason codes.
    assert 'reason_code = "bucket_over_alert"' not in src
    assert 'reason_code = "bucket_over_warn"' not in src


# ── Pillar 7 · Every threshold owns a PolicyRecord ───────────────────
def test_canonical_policy_covers_all_seven_dimensions():
    expected = {
        "technical_capacity",
        "storage_cost",
        "growth",
        "certified_waste",
        "backup_footprint",
        "retention_compliance",
        "evidence_freshness",
    }
    assert set(CANONICAL_POLICY) == expected


def test_every_policy_record_documents_owner_and_purpose():
    for name, pr in CANONICAL_POLICY.items():
        assert pr.owner, f"{name} missing owner"
        assert pr.purpose, f"{name} missing purpose"
        assert pr.evidence, f"{name} missing evidence"
        assert pr.approval_status, f"{name} missing approval_status"
        assert pr.review_cadence_days > 0, f"{name} missing review cadence"


# ── Pillar 4 · Never invent a status ────────────────────────────────
def test_technical_capacity_healthy_below_provider_ceiling():
    ev = evaluate_technical_capacity(320.47)
    assert ev.status == "HEALTHY"
    assert "provider_ceiling_gb" in ev.evidence
    assert ev.evidence["provider_ceiling_gb"] == R2_PROVIDER_TECHNICAL_CEILING_GB


def test_technical_capacity_unknown_when_no_signal():
    ev = evaluate_technical_capacity(None)
    assert ev.status == "UNKNOWN"
    assert "bucket_usage_row_missing" in ev.unknowns


def test_technical_capacity_never_flips_red_on_arbitrary_gb():
    # Even at 2 TB (which was the audit's proposed operator-capacity
    # ceiling in Phase 0B), the *technical_capacity* dimension is still
    # HEALTHY because it compares only against the provider ceiling.
    # Cost pressure is a separate dimension.
    ev = evaluate_technical_capacity(2048.0)
    assert ev.status == "HEALTHY"


# ── Pillar 1 · Cost calculation correct (official-rate estimate) ───
def test_storage_cost_healthy_at_current_320gb():
    ev = evaluate_storage_cost(320.47)
    assert ev.status == "HEALTHY"
    assert ev.evidence["estimate_kind"] == "OFFICIAL_RATE_ESTIMATE"
    # Cost = 320.47 GB × $0.015 = ~$4.81/mo (well below $30/mo healthy line)
    assert ev.evidence["monthly_usd"] == pytest.approx(
        320.47 * R2_USD_PER_GB_MONTH, rel=1e-3,
    )


def test_storage_cost_escalates_by_dollars_not_gb():
    # 3 TB × $0.015 = $45/mo → ATTENTION
    ev_mid = evaluate_storage_cost(3000.0)
    assert ev_mid.status == "ATTENTION"
    # 10 TB × $0.015 = $150/mo → CRITICAL
    ev_high = evaluate_storage_cost(10_000.0)
    assert ev_high.status == "CRITICAL"


def test_verified_invoice_beats_estimate():
    ev = evaluate_storage_cost(500.0, verified_invoice_usd_per_month=6.0)
    assert ev.evidence["estimate_kind"] == "VERIFIED_INVOICE"
    assert "no_verified_invoice" not in ev.unknowns
    assert ev.status == "HEALTHY"


# ── Pillar 1 · Growth signal is evidence-based ─────────────────────
def test_growth_unknown_with_insufficient_samples():
    ev = evaluate_growth([1.0, 2.0])  # < min_samples_required
    assert ev.status == "UNKNOWN"
    assert "insufficient_samples" in ev.unknowns


def test_growth_healthy_on_stable_series():
    ev = evaluate_growth([2.1] * 30)
    assert ev.status == "HEALTHY"


def test_growth_attention_on_3x_ratio():
    baseline = [2.0] * 25
    recent = [7.0] * 7  # 3.5× baseline
    ev = evaluate_growth(baseline + recent)
    assert ev.status == "ATTENTION"


def test_growth_critical_on_10x_ratio():
    baseline = [1.0] * 25
    recent = [15.0] * 7  # 15× baseline
    ev = evaluate_growth(baseline + recent)
    assert ev.status == "CRITICAL"


# ── Pillar 4 · Certified waste is UNKNOWN when classifier is stale ─
def test_certified_waste_unknown_when_no_snapshot():
    ev = evaluate_certified_waste(None, None)
    assert ev.status == "UNKNOWN"


def test_certified_waste_unknown_when_snapshot_stale():
    ev = evaluate_certified_waste(orphan_pct=1.0, classifier_age_days=30.0)
    assert ev.status == "UNKNOWN"
    assert "classifier_stale" in ev.unknowns


def test_certified_waste_healthy_on_fresh_low_orphan_share():
    ev = evaluate_certified_waste(orphan_pct=0.5, classifier_age_days=1.0)
    assert ev.status == "HEALTHY"


def test_certified_waste_critical_at_high_orphan_share():
    ev = evaluate_certified_waste(orphan_pct=25.0, classifier_age_days=1.0)
    assert ev.status == "CRITICAL"


# ── Pillar 8 · POLICY_REQUIRED never becomes GREEN silently ────────
def test_retention_compliance_policy_required_when_windows_missing():
    ev = evaluate_retention_compliance({})
    assert ev.status == "POLICY_REQUIRED"
    assert ev.unknowns  # must name the missing items
    assert "osha_incident_records_retention_years" in ev.unknowns


def test_retention_compliance_healthy_once_all_windows_encoded():
    encoded = {
        item: True
        for item in CANONICAL_POLICY["retention_compliance"].values["required_policy_items"]
    }
    ev = evaluate_retention_compliance(encoded)
    assert ev.status == "HEALTHY"


# ── Pillar 8 · Every UNKNOWN explains WHY ──────────────────────────
def test_every_unknown_status_names_at_least_one_unknown_item():
    unknown_evals = [
        evaluate_technical_capacity(None),
        evaluate_storage_cost(None),
        evaluate_growth([1.0]),
        evaluate_certified_waste(None, None),
        evaluate_backup_footprint(None, None),
        evaluate_evidence_freshness(None, None),
    ]
    for ev in unknown_evals:
        if ev.status in ("UNKNOWN", "POLICY_REQUIRED"):
            assert ev.unknowns, (
                f"{ev.dimension} returned {ev.status} without naming any "
                "unknown items — violates Pillar 8."
            )


# ── Pillar 1 · Composite is evidence-driven, NOT max(severity) ─────
def test_composite_attention_when_only_one_critical():
    dims = [
        evaluate_technical_capacity(320.47),        # HEALTHY
        evaluate_storage_cost(320.47),               # HEALTHY (~$4.80)
        evaluate_growth([1.0] * 25 + [15.0] * 7),   # CRITICAL (15× baseline)
        evaluate_certified_waste(0.5, 1.0),          # HEALTHY
        evaluate_backup_footprint(30.0, True),       # HEALTHY
        evaluate_retention_compliance({}),           # POLICY_REQUIRED
        evaluate_evidence_freshness(1.0, 1.0),       # HEALTHY
    ]
    v = aggregate(dims)
    assert v.status == "ATTENTION", (
        f"Composite with 1 CRITICAL + 5 HEALTHY + 1 POLICY_REQUIRED "
        f"must be ATTENTION (not CRITICAL). Got {v.status!r}."
    )


def test_composite_critical_only_when_two_or_more_critical():
    dims = [
        evaluate_technical_capacity(20_000_000.0),  # CRITICAL (> provider)
        evaluate_storage_cost(20_000.0),             # CRITICAL ($300/mo)
        evaluate_growth([1.0] * 30),                 # HEALTHY
        evaluate_certified_waste(0.5, 1.0),          # HEALTHY
        evaluate_backup_footprint(30.0, True),       # HEALTHY
        evaluate_retention_compliance({}),           # POLICY_REQUIRED
        evaluate_evidence_freshness(1.0, 1.0),       # HEALTHY
    ]
    v = aggregate(dims)
    assert v.status == "CRITICAL"


def test_composite_healthy_when_all_healthy_or_policy_required():
    dims = [
        evaluate_technical_capacity(320.47),
        evaluate_storage_cost(320.47),
        evaluate_growth([2.1] * 30),
        evaluate_certified_waste(0.5, 1.0),
        evaluate_backup_footprint(30.0, True),
        evaluate_retention_compliance({}),  # POLICY_REQUIRED — not RED
        evaluate_evidence_freshness(1.0, 1.0),
    ]
    v = aggregate(dims)
    assert v.status == "HEALTHY"


def test_composite_unknown_when_all_dimensions_are_unknown_or_policy_required():
    dims = [
        evaluate_technical_capacity(None),
        evaluate_storage_cost(None),
        evaluate_growth([]),
        evaluate_certified_waste(None, None),
        evaluate_backup_footprint(None, None),
        evaluate_retention_compliance({}),
        evaluate_evidence_freshness(None, None),
    ]
    v = aggregate(dims)
    assert v.status == "UNKNOWN"


def test_composite_carries_all_dimension_details():
    dims = [
        evaluate_technical_capacity(320.47),
        evaluate_storage_cost(320.47),
        evaluate_growth([2.1] * 30),
        evaluate_certified_waste(0.5, 1.0),
        evaluate_backup_footprint(30.0, True),
        evaluate_retention_compliance({}),
        evaluate_evidence_freshness(1.0, 1.0),
    ]
    v = aggregate(dims)
    d = v.to_dict()
    assert len(d["dimensions"]) == 7
    for row in d["dimensions"]:
        assert row["dimension"]
        assert row["status"]
        assert "reason" in row
        assert "evidence" in row
        assert "recommendation" in row
        assert "unknowns" in row
        assert "policy" in row


# ── Pillar 3 · Policy manifest exposes provenance ──────────────────
def test_policy_manifest_shape():
    m = policy_manifest()
    assert m["version"] == "27.07A.P1"
    assert set(m["records"]) == set(CANONICAL_POLICY)
    assert "provider_facts" in m
    assert m["provider_facts"]["r2_usd_per_gb_month"] == R2_USD_PER_GB_MONTH
    assert m["governance_note"]


# ── Pillar 6 · Deployable — backward-compat envelope ──────────────
def test_health_response_still_carries_legacy_fields():
    # The compute_storage_health envelope must still expose
    # overall_score, band, capacity{gb}, objects{...}, and freshness{...}
    # so existing UI consumers do not KeyError while migrating to the
    # new policy_verdict field.
    from services.r2_lifecycle.health import compute_storage_health

    class _FakeCursor:
        def __init__(self, docs):
            self._docs = docs

        def sort(self, *_a, **_kw):
            return self

        def limit(self, *_a, **_kw):
            return self

        async def to_list(self, length=None):
            return list(self._docs)[: length or len(self._docs)]

    class _FakeAggregate:
        def __init__(self, docs):
            self._docs = docs

        async def to_list(self, n):
            return list(self._docs)[:n]

    class _FakeColl:
        def __init__(self, docs=(), aggregate_docs=()):
            self._docs = list(docs)
            self._agg = list(aggregate_docs)

        async def find_one(self, *_a, **_kw):
            return dict(self._docs[0]) if self._docs else None

        def find(self, *_a, **_kw):
            return _FakeCursor(self._docs)

        def aggregate(self, *_a, **_kw):
            return _FakeAggregate(self._agg)

    class _FakeDB:
        backup_health = _FakeColl(
            docs=[{"mode": "r2-usage-warn",
                   "size_bytes": int(320.47 * (1024 ** 3)),
                   "ts": "2026-07-11T14:00:00Z", "ok": True}],
            aggregate_docs=[],
        )
        r2_inventory = _FakeColl(aggregate_docs=[{"b": 0}])
        r2_lifecycle_runs = _FakeColl(docs=[])

    import asyncio
    payload = asyncio.get_event_loop().run_until_complete(
        compute_storage_health(_FakeDB())
    )
    assert "overall_score" in payload
    assert "band" in payload
    assert "sub_scores" in payload
    assert "capacity" in payload
    assert "gb" in payload["capacity"]
    assert "policy_verdict" in payload
    assert payload["policy_verdict"]["status"] in (
        "HEALTHY", "ATTENTION", "CRITICAL", "UNKNOWN", "POLICY_REQUIRED"
    )
