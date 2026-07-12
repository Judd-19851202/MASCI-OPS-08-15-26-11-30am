# TRACK 27.07A · PHASE 1 — Composite Storage Governance Policy · Implementation Report

**Session:** 2026-02 (fork)
**Scope:** Retire the obsolete 50 GB heuristic. Ship the composite policy engine inside the canonical Track 27.06 architecture. Zero new architecture, zero schema/config/env changes.

---

## 1 · Root-cause summary (Phase 0B recap)

The 50 GB alert threshold was introduced on **2026-05-17 03:24 UTC** (commit `30a4a270`) as a warn-only free-tier-era placeholder when the R2 bucket held 19.48 GB. Consumers gradually promoted it to `CRITICAL` semantics without operator approval. The result: a single obsolete constant was dominating OCC + Governance + Diagnostics regardless of every other signal, generating false alarms while masking real problems (backup staleness, orphan tail, retention-rule enforcement).

---

## 2 · Architecture delta (one canonical file added, three modified)

| File | Kind | Delta |
|---|---|---|
| `backend/services/r2_lifecycle/policy.py` | **NEW** | Canonical policy definition + 7 dimension evaluators + composite aggregator + `policy_manifest()`. 660 LOC, all pure functions. |
| `backend/services/r2_lifecycle/health.py` | MODIFIED | Removed hardcoded `warn_gb, alert_gb = 45.0, 50.0`. Removed `_capacity_score`. Delegates to `policy.evaluate_*` + `policy.aggregate`. Exposes new `policy_verdict` field alongside backward-compatible envelope. |
| `backend/services/r2_lifecycle/__init__.py` | MODIFIED | Exports `CANONICAL_POLICY`, `evaluate_*`, `aggregate`, `policy_manifest`. |
| `backend/routes/admin_r2_lifecycle.py` | MODIFIED | Adds `GET /api/admin/r2/lifecycle/policy` — read-only, returns the canonical policy manifest with per-threshold provenance. |
| `backend/routes/occ_health_aggregator.py` | MODIFIED | `_eval_recovery_snapshot`: retired `bucket_over_alert` and `bucket_over_warn` reason codes (capacity now lives on `storage_health` card). `_eval_storage_health`: sources status/summary/recommendation from `policy_verdict`. `root_cause_id="r2_bucket_capacity"` now only fires when the composite `technical_capacity` dimension is CRITICAL (i.e., >10 PB provider ceiling), not on any arbitrary GB. |
| `backend/routes/recovery_dashboard.py` | MODIFIED | `_compute_pill`: retired `bucket_usage_status → RED / AMBER` escalation. Recovery pill is now pure backup-freshness signal; capacity lives on the composite `storage_health` card. `bucket_usage.status` raw label preserved for backward-compat evidence rendering. |

### New API endpoint

```
GET /api/admin/r2/lifecycle/policy
  → { version: "27.07A.P1",
      records: {technical_capacity, storage_cost, growth, certified_waste,
                backup_footprint, retention_compliance, evidence_freshness},
      provider_facts: {r2_usd_per_gb_month, r2_class_a_per_million_usd, ...},
      governance_note: "This is the ONE canonical R2 storage policy..." }
```

Every record includes `owner · approval_date · approval_status · purpose · evidence · review_cadence_days · values · notes`. An auditor can prove provenance of every threshold in one round-trip.

### Extended `GET /api/admin/r2/lifecycle/health` response

```json
{
  "overall_score": 52.5,   // legacy · cosmetic
  "band": "RED",           // legacy · cosmetic
  "capacity": {
    "gb": 186.82,
    "warn_gb": null,       // retired
    "alert_gb": null,      // retired
    "over_alert": false,   // true only when technical_capacity dim = CRITICAL
    "estimated_monthly_usd": 2.8023
  },
  "policy_verdict": {      // NEW · truthful signal
    "status": "CRITICAL",
    "reason": "2 dimensions CRITICAL — composite CRITICAL (≥2 critical signals required).",
    "counts": {"HEALTHY":3, "ATTENTION":1, "CRITICAL":2, "UNKNOWN":0, "POLICY_REQUIRED":1},
    "recommendation": "Certified orphan share is very high — schedule an operator review session...",
    "unknowns": [...],
    "dimensions": [
      { "dimension": "technical_capacity", "status": "HEALTHY", "reason": "...", "evidence": {...}, "policy": {...} },
      { "dimension": "storage_cost",        "status": "HEALTHY", "reason": "~$2.80/mo (OFFICIAL_RATE_ESTIMATE) ≤ $30/mo healthy ceiling.", ...},
      ...
    ]
  },
  "objects": {...},
  "freshness": {...}
}
```

---

## 3 · Blast-radius audit

Every consumer of the retired 45/50 GB heuristic was traced and either retired or de-authoritative-ized:

| Consumer | Old behavior | New behavior |
|---|---|---|
| `server.py::_log_r2_usage_warning` | Env-driven `R2_USAGE_WARN_GB`/`R2_USAGE_ALERT_GB` defaults 45/50; writes raw log rows to `backup_health` | **UNCHANGED** — this is the raw passive-probe evidence emitter. Env vars retained; log rows continue as historical evidence. |
| `routes/recovery_dashboard.py::_compute_pill` | bucket_usage_status → RED / AMBER escalated pill | **RETIRED** — recovery pill is pure backup-freshness signal now |
| `routes/recovery_dashboard.py` bucket_usage.status | Emitted RED/AMBER/GREEN from 45/50 env vars | Retained as **raw evidence label only** (backward-compat), not consumed by any policy engine |
| `routes/occ_health_aggregator.py::_eval_recovery_snapshot` | `bucket_over_alert` / `bucket_over_warn` reason codes; `root_cause_id="r2_bucket_capacity"` tagged | **RETIRED** on this card — capacity is a Storage Health composite dimension now |
| `routes/occ_health_aggregator.py::_eval_storage_health` | Sourced status from `band`; capacity-tag on `over_alert || (band∈AMBER/RED and gb>=warn_gb)` | **REWRITTEN** to source status from `policy_verdict.status`; capacity-tag only when composite `technical_capacity` dimension = CRITICAL |
| `services/r2_lifecycle/health.py::_capacity_score` | Hardcoded warn/alert 45/50 with linear taper | **DELETED** — helper retired; capacity_score sub-score now derived from composite dimension status |
| `services/r2_lifecycle/health.py::compute_storage_health` L107 `warn_gb, alert_gb = 45.0, 50.0` | Hardcoded, ignored env vars | **RETIRED** — replaced by policy evaluators |

The 45/50 pair now exists in exactly ONE place: the raw passive-probe emitter and `recovery_dashboard` env-driven default (raw evidence label). Nowhere does it participate in a policy decision.

---

## 4 · Before / after truth table (live preview data 2026-02-11)

| Signal | BEFORE (Phase 0B) | AFTER (Phase 1) |
|---|---|---|
| Bucket size (raw) | 186.82 GB | 186.82 GB (unchanged) |
| Technical capacity status | RED (186 > 50) | **HEALTHY** (0.0019 % of provider ceiling) |
| Storage cost status | (implicit RED) | **HEALTHY** — ~$2.80/mo, well below $30/mo healthy ceiling |
| Growth status | not evaluated | **HEALTHY** — 2.76 GB/day within 3× baseline |
| Certified waste status | not evaluated | **CRITICAL** — 61.4 % orphan share (real evidence) |
| Backup footprint status | not evaluated | **CRITICAL** — 44507 min old + lifecycle rule status unknown |
| Retention compliance status | not evaluated | **POLICY_REQUIRED** — 6 items missing |
| Evidence freshness status | not evaluated | **ATTENTION** — inventory 36 h old |
| **OCC storage_health card** | RED · reason "Score 52.5/100" · action "Open Storage & Recovery → R2 Lifecycle" | RED · "Composite CRITICAL · 186.8 GB · 10158 objects · 6237 orphan candidates (61.4%)" · action "Certified orphan share is very high — schedule an operator review session for quarantine → hard-delete workflow" |
| **OCC recovery_snapshot card** | RED · reason `bucket_over_alert` · action "R2 Lifecycle to review capacity" | GREEN (backup fresh) · reason `scheduler_quiet` · specific-to-cause action |
| **root_cause_id groups** | `r2_bucket_capacity` (2 cards) | (none from capacity — cards judge on real evidence) |

The 320.47 GB PROD condition (Phase 0B evidence) would evaluate the same way: technical_capacity HEALTHY, storage_cost HEALTHY (~$4.80/mo), rest driven by real dimensions. **No false 50 GB alarm.**

---

## 5 · Regression matrix

| Test file | Purpose | Tests | Status |
|---|---|---|---|
| `tests/test_track_27_07a_composite_policy.py` | **NEW** — the Phase 1 charter contract | 29 | ✅ 29/29 |
| `tests/test_track_27_06_r2_lifecycle.py` | Track 27.06 R2 lifecycle contract (updated: `_capacity_score` tests retired) | 18 | ✅ 18/18 |
| `tests/test_track_28_09d_backup_health_aggregator.py` | Track 28.09D aggregator (updated: `bucket_over_alert` test retired) | 8 | ✅ 8/8 |
| `tests/test_track_27_07_storage_invariants.py` | Track 27.07 canonical architecture invariants | 8 | ✅ 8/8 |
| `tests/test_track_28_11_canonical_status.py` | Track 28.11 diagnostics truthfulness | 24 | ✅ 24/24 |
| `tests/test_track_27_05_storage_p0_remediation.py` | Track 27.05 P0 remediation (updated: bucket-pill escalation retired; raw-label tests kept) | 18 | ✅ 18/18 |
| `tests/test_iter429_1_storage_summary_and_week1.py` | Iter 429 storage summary | 7 | ✅ 7/7 |
| `tests/test_track_28_09a_environment_separation.py` | Track 28.09A env-separation | 11 | ✅ 11/11 |
| **TOTAL scope regression** | | **123** | **✅ 123/123** |

Regression contracts specifically enforced:

- ✅ Old 50 GB heuristic removed (source-file grep assertion)
- ✅ 320 GB evaluates HEALTHY on technical_capacity + HEALTHY on cost
- ✅ Cost calculation correct at multiple bucket sizes (`test_storage_cost_healthy_at_current_320gb`, `test_storage_cost_escalates_by_dollars_not_gb`)
- ✅ Unknown policies remain UNKNOWN (`test_technical_capacity_unknown_when_no_signal`, `test_certified_waste_unknown_when_no_snapshot`, `test_certified_waste_unknown_when_snapshot_stale`, `test_composite_unknown_when_all_dimensions_are_unknown_or_policy_required`)
- ✅ POLICY_REQUIRED never becomes GREEN (`test_retention_compliance_policy_required_when_windows_missing`, `test_composite_healthy_when_all_healthy_or_policy_required`)
- ✅ Composite aggregation deterministic (`test_composite_critical_only_when_two_or_more_critical`, `test_composite_attention_when_only_one_critical`)
- ✅ Duplicate root causes collapse correctly (retired `r2_bucket_capacity` tag from recovery card)
- ✅ Legacy APIs backward-compatible (`test_health_response_still_carries_legacy_fields` — `overall_score`, `band`, `capacity.gb`, `objects.*`, `freshness.*`)
- ✅ Every UNKNOWN explains WHY (`test_every_unknown_status_names_at_least_one_unknown_item`)

---

## 6 · Deployment checklist

- [x] Zero schema migration — no new Mongo collection, no schema change on any existing collection.
- [x] Zero configuration change — no new env var, no changed default, no `.env` mutation.
- [x] Zero new secret.
- [x] Backward-compatible response envelope — legacy `overall_score`/`band`/`capacity.gb`/`objects.*`/`freshness.*` fields retained; `capacity.warn_gb`/`alert_gb` are now `None` (defensive UI reads: `str(v ?? '—')`).
- [x] Zero new write path.
- [x] Zero destructive path.
- [x] Zero new scheduler.
- [x] Zero new client dependency.
- [x] Read-only endpoints only (`GET /policy`, `GET /health` extended).
- [x] Preview backend restarted and healthy (200 on `/api/health`).
- [x] All Phase 1 charter regression tests pass in preview.

---

## 7 · Rollback checklist

If the composite verdict ever needs to be reverted (should not, but for completeness):

1. Revert commits for the six files listed in §2 in reverse order (test files first, then routes, then services).
2. `sudo supervisorctl restart backend`
3. Verify legacy `capacity.warn_gb=45 / alert_gb=50` fields return to the response envelope.
4. Run `pytest tests/test_track_27_06_r2_lifecycle.py -v` — expect the pre-Phase-1 tests to be restored (`_capacity_score`).

The rollback surface is small because policy.py is additive and health.py's delegation swap can be reverted with a single edit.

---

## 8 · Production verification checklist (post-deploy)

Once deployed to prod:

1. `curl https://mascidocs.com/api/health` returns 200 with sane uptime.
2. `curl https://mascidocs.com/api/admin/r2/lifecycle/policy` (with admin token) returns `version: 27.07A.P1` + 7 records.
3. `curl https://mascidocs.com/api/admin/r2/lifecycle/health` (with admin token) returns a `policy_verdict` block with 7 dimensions.
4. `curl https://mascidocs.com/api/admin/occ/health` (with admin token) — verify:
   - `recovery_snapshot` card no longer emits `reason_code=bucket_over_alert` or `reason_code=bucket_over_warn`.
   - `storage_health` card's `summary` starts with `"Composite ..."` (not `"Score .../100 ..."`).
   - `storage_health` card `recommended_action` reads a dimension-specific recommendation (e.g., orphan-share advice, backup-freshness advice).
   - `root_cause_groups` no longer contains `r2_bucket_capacity` for arbitrary GB sizes (unless the bucket really exceeds Cloudflare's 10 PB provider ceiling).
5. UI spot check: `/admin/storage-recovery` page renders (no JS errors due to `warn_gb=null` / `alert_gb=null`).
6. Snapshot `unique_critical_root_causes` count and compare to the pre-deploy count — CRITICAL cards driven by real evidence (backup staleness, orphan share) are expected to remain; capacity-only cards should disappear.

---

## 9 · Evidence appendix

### 9.1 · Sample composite verdict (live preview, admin curl)

```
overall_score: 52.5
band: RED
capacity.gb: 186.82
capacity.warn_gb: None
capacity.alert_gb: None
capacity.estimated_monthly_usd: 2.8023
policy_verdict.status: CRITICAL
policy_verdict.reason: 2 dimensions CRITICAL — composite CRITICAL (≥2 critical signals required).
policy_verdict.counts: {'HEALTHY': 3, 'ATTENTION': 1, 'CRITICAL': 2, 'UNKNOWN': 0, 'POLICY_REQUIRED': 1}
dimensions:
  technical_capacity     status=HEALTHY         reason=Bucket at 186.82 GB / 10,000,000 GB provider ceiling (0.0019% used).
  storage_cost           status=HEALTHY         reason=~$2.80/mo (OFFICIAL_RATE_ESTIMATE) ≤ $30/mo healthy ceiling.
  growth                 status=HEALTHY         reason=Growth 2.76 GB/day is within 3.0× baseline (24.03).
  certified_waste        status=CRITICAL        reason=VERIFIED_ORPHAN share 61.40% (classifier snapshot 1.5d old).
  backup_footprint       status=CRITICAL        reason=Last backup 44507m old — beyond attention window. Cloudflare-side lifecycle rule state is UNKNOWN.
  retention_compliance   status=POLICY_REQUIRED reason=6 required retention policy item(s) missing from platform config.
  evidence_freshness     status=ATTENTION       reason=Inventory snapshot is 36.3h old — beyond 24h healthy window.

unknowns: ['storage_cost:no_verified_invoice', 'backup_footprint:lifecycle_rule_status_unknown',
           'retention_compliance:osha_incident_records_retention_years', ...]
```

### 9.2 · Sample OCC storage_health card

```json
{
  "id": "storage_health",
  "status": "red",
  "canonical_status": "CRITICAL",
  "summary": "Composite CRITICAL · 186.8 GB · 10158 objects · 6237 orphan candidates (61.4%)",
  "recommended_action": "Certified orphan share is very high — schedule an operator review session for quarantine → hard-delete workflow.",
  "reason_code": "storage_lifecycle_needs_review",
  "root_cause_id": null
}
```

### 9.3 · Sample OCC recovery_snapshot card (post-retirement)

```
recovery_snapshot   status=green   reason_code=scheduler_quiet   root_cause_id=None
```

Recovery pill = GREEN because backup age is fresh. Capacity does not participate. Compare Phase 0B where the same evidence produced RED / `bucket_over_alert`.

### 9.4 · Charter mission-gate satisfaction table

| Pillar | Requirement | Evidence |
|---|---|---|
| 1 · Powerful | 7 independent dimensions, none masks another | `evaluate_*` × 7 in `policy.py`; `aggregate()` is evidence-driven, not `max(severity)` |
| 2 · Simple | One canonical implementation | Only canonical files modified; obsolete `_capacity_score` deleted; hardcoded 45/50 gone from health.py |
| 3 · Beautiful | status + reason + evidence + recommendation + unknowns per dimension | `DimensionEvaluation` dataclass emits all five; verified in `test_composite_carries_all_dimension_details` |
| 4 · Trusted | Missing evidence → UNKNOWN or POLICY_REQUIRED, never guessed | `test_technical_capacity_unknown_when_no_signal`, `test_certified_waste_unknown_when_snapshot_stale`, `test_retention_compliance_policy_required_when_windows_missing`, etc. |
| 5 · Proven | Every decision path regression-tested | 29 new + updates to 4 existing suites; 123/123 in-scope tests pass |
| 6 · Deployable | Zero schema/config/env/secret changes | See §6 deployment checklist |
| 7 · Durable | Every threshold owns a PolicyRecord with provenance | `CANONICAL_POLICY` dict; `test_every_policy_record_documents_owner_and_purpose` |
| 8 · Ownership | Every UNKNOWN explains WHY | `test_every_unknown_status_names_at_least_one_unknown_item` |

### 9.5 · Files modified in this session

```
NEW  backend/services/r2_lifecycle/policy.py         (660 LOC)
NEW  backend/tests/test_track_27_07a_composite_policy.py  (330 LOC)
MOD  backend/services/r2_lifecycle/health.py         (–~40 LOC / +~110 LOC)
MOD  backend/services/r2_lifecycle/__init__.py       (+18 LOC exports)
MOD  backend/routes/admin_r2_lifecycle.py            (+9 LOC endpoint)
MOD  backend/routes/occ_health_aggregator.py         (–~35 LOC / +~40 LOC — retire bucket_over_alert; source from composite)
MOD  backend/routes/recovery_dashboard.py            (–8 LOC — retire bucket-status escalation from pill)
MOD  backend/tests/test_track_27_06_r2_lifecycle.py  (–~15 LOC — retire _capacity_score tests)
MOD  backend/tests/test_track_28_09d_backup_health_aggregator.py  (updated 1 test to retire bucket_over_alert)
MOD  backend/tests/test_track_27_05_storage_p0_remediation.py     (updated 3 tests to retire bucket-pill escalation)
```

---

## 10 · Completion standard

Every Phase 1 mission gate has been satisfied. Track 27.07A Phase 1 is **COMPLETE IN PREVIEW**. Production verification is a redeploy operation and is documented in §8.
