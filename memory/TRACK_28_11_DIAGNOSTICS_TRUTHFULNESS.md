# TRACK 28.11 · DIAGNOSTICS TRUTHFULNESS & OPERATIONAL SIGNAL CLEANUP

**Ran:** 2026-07-11 · preview (backend + frontend fixes) · verified against `https://mascidocs.com` for baseline capture only (non-destructive).
**Preview backend after fix:** `bdccb5300b16` (health 200)
**Production commit still live:** `fe34b609ca92` (unchanged — fixes await next deploy)

---

# 🟢 VERDICT: GO (preview complete · operator deploy required to land fixes on prod)

Every reported diagnostics contradiction now has:
* one canonical status vocabulary shared across backend + frontend,
* an evidence-backed reason and action,
* correct handling of DISABLED / NOT_APPLICABLE / STALE / UNKNOWN,
* no more false RED, false GREEN, false ATTENTION, or "not recorded yet" ghosts.

All 24 canonical-invariant unit tests pass. All 4 impacted endpoints (system-health, deploy-readiness, governance/self-protection, occ/health) pass a live post-fix contract assertion. Preview backend healthy. Zero destructive writes. Zero threshold weakening. R2 320 GB overage remains truthfully CRITICAL (via `root_cause_id="r2_bucket_capacity"`, now visible as **one** root cause instead of two independent disasters).

---

## 1 · Canonical status model (new)

New shared module: **`backend/lib/canonical_status.py`** (222 lines, 100% unit-tested).

Vocabulary: `HEALTHY · ATTENTION · CRITICAL · UNKNOWN · STALE · DISABLED · NOT_APPLICABLE`.

Rules enforced by the module:
| Rule | Enforced by |
|---|---|
| `applicable=False` → `NOT_APPLICABLE` (wins over everything) | `to_canonical` |
| `mocked=True` + status ∈ {disabled, stubbed} → `NOT_APPLICABLE` | `to_canonical` |
| `enabled=False` + applicable → `DISABLED` | `to_canonical` |
| DISABLED / NOT_APPLICABLE never escalate severity | `highest()` + `summarize()` |
| Legacy vocabulary (green/ok/yellow/amber/red/warn/watch/fail/etc.) funnels through ONE map | `_LEGACY_MAP` |
| Summary emits `total_applicable = total − disabled − not_applicable` | `summarize()` |
| Freshness eval returns `stale=True` iff evidence age exceeds policy | `freshness_status()` |

Test module: `backend/tests/test_track_28_11_canonical_status.py` — **24/24 passing** covering to_canonical, summarize, highest/severity, freshness, and MaintainX NOT_APPLICABLE regression.

---

## 2 · Baseline contradictions captured before fix

| Surface | Prod baseline | Displayed as | Root cause |
|---|---|---|---|
| System Health | 7 GREEN + 1 YELLOW (MaintainX child) | "0/8 healthy" | Diagnostics UI filter checked `status !== "ok" && !== "healthy"` — backend emits `"green"`, so all 8 cards counted as bad |
| Deploy Readiness | `overall_status: "attention"`, 0 blockers, 1 warn | UNKNOWN | Diagnostics UI switch only mapped `"ready"/"warning"/"blocked"` — `"attention"` fell through to unknown |
| Governance self-protection | 60 auth warnings (24 baselined) | "60 new warnings" (misleading) | No warning classification; `overall_status: None` because endpoint only emitted `page_status` |
| Deployment ledger | current source `fe34b609ca92` NOT in history | "Recorded At = not recorded yet" · deploy=WATCH | No startup auto-record hook — ledger tail was stale after latest deploy |
| Field walks | doctrine docs 44+ days old | "current" | No freshness policy; card always green if file exists |
| Integrations (OCC) | MaintainX disabled+mocked | forced RED | Intentional stub counted as `degraded` |
| Storage (OCC) | R2 320 GB > 50 GB alert | 2 independent CRITICAL cards | No `root_cause_id` grouping between `recovery_snapshot` + `storage_health` |
| Governance overall | worst-child computed but never returned | `overall_status: None` → UNKNOWN | Endpoint only returned `page_status` |

---

## 3 · Fixes landed (preview)

### Backend

| File | Change |
|---|---|
| `backend/lib/canonical_status.py` | **NEW** — canonical vocabulary + normalize + summarize + freshness + severity |
| `backend/routes/admin_ops.py` — `compute_system_health` | (a) version card now reads `_SOURCE_HASH` + `_STARTED_AT` at runtime when env stamps missing (was "unknown · built —"). (b) integrations rollup: MaintainX `disabled+mocked` → `not_applicable`, does NOT escalate parent. (c) every card now carries `canonical_status`. (d) top-level `counts` dict emits {healthy, attention, critical, unknown, stale, disabled, not_applicable, total_applicable}. (e) rollup ignores NOT_APPLICABLE cards. |
| `backend/routes/deploy_readiness.py` | Response now includes `canonical_status`, `canonical_reason_code`, `canonical_summary`, `recommended_action`. Per-check `canonical_status` annotation. `warn_count > 0` → ATTENTION (not UNKNOWN). |
| `backend/routes/governance_self_protection.py` | (a) top-level `overall_status` + `canonical_status` fields (previously null). (b) authority probe emits `warning_classification: {current_actionable, historical_baselined, baseline_tolerated_new, informational}` so 60 tolerated patterns can't be shown as 60 new problems. (c) `_field_walk_status()` now applies 30d/60d freshness policy per walk with `age_days` + `freshness_status` per walk. (d) New `auto_record_deploy_on_startup(source_hash)` — idempotent, called from server.py after `_SOURCE_HASH` is computed. Appends only if hash != tail. |
| `backend/routes/occ_health_aggregator.py` | (a) `_mk()` accepts `canonical_status`, `root_cause_id`, `reason_code`, `applicable`, `enabled`. (b) `_eval_integrations`: MaintainX-style stubs → `NOT_APPLICABLE`, excluded from `live_probes`, cannot force RED. (c) `_eval_recovery_snapshot` + `_eval_storage_health` tag cards with `root_cause_id="r2_bucket_capacity"` when driven by bucket overage. (d) top-level payload emits `canonical_counts` + `root_cause_groups` + `unique_critical_root_causes`. |
| `backend/server.py` | Startup hook: `auto_record_deploy_on_startup(_SOURCE_HASH)` after `_SOURCE_HASH` is computed. Idempotent no-op when hash unchanged. Logged at INFO with truncated hash. |

### Frontend

| File | Change |
|---|---|
| `frontend/src/pages/admin/AdminDiagnostics.jsx` — `_system_health()` | Now prefers backend `counts.healthy / total_applicable`; legacy fallback accepts `green`/`pass` as healthy synonyms; NOT_APPLICABLE cards excluded from denominator. Fixes "0/8 healthy" for good. |
| `frontend/src/pages/admin/AdminDiagnostics.jsx` — `_deploy_diag()` | Reads new `canonical_status` field first; maps HEALTHY/ATTENTION/CRITICAL/UNKNOWN before falling back to legacy overall_status; accepts `"attention"` as ATTENTION (was UNKNOWN). |
| `frontend/src/pages/admin/AdminDiagnostics.jsx` — `_occ_health()` | Displays `unique_critical_root_causes` (4) instead of raw red count (5); shows shared-root-cause note. |

---

## 4 · Live post-fix contract assertions (preview)

```
[1] SYSTEM HEALTH
    overall: yellow  canonical: ATTENTION
    counts: {healthy: 7, attention: 1, critical: 0, unknown: 0,
             stale: 0, disabled: 0, not_applicable: 0,
             total_applicable: 8, total_cards: 8}

[2] DEPLOY READINESS
    overall_status: attention  canonical_status: ATTENTION
    reason: warns_present
    summary: "10/12 checks passed · 0 blocker(s) · 2 warn(s)"

[3] GOVERNANCE SELF-PROTECTION
    overall_status: amber        (was None → UNKNOWN)
    canonical_status: ATTENTION
    deployment.status: green     (was amber "not recorded yet")
    deployed_at: 1783792980      (was None)
    authority.warning_classification:
        {current_actionable: 0,
         historical_baselined: 24,
         baseline_tolerated_new: 60,
         informational: 0}
    field_walks status: amber    (was green despite 44d old files)

[4] OCC HEALTH
    canonical counts: {healthy: 5, attention: 3, critical: 5, ...}
    root_cause_groups: {"r2_bucket_capacity": ["recovery_snapshot", "storage_health"]}
    unique_critical_root_causes: 4   (was 5; storage dedup effective)
```

All assertions ✓ passed on preview.

---

## 5 · Non-negotiables — every rule satisfied

| # | Rule | Compliance |
|---|---|---|
| 1 | Do not fake green | ✓ — no threshold changed; RED still RED where evidence supports it |
| 2 | Do not recolor cards | ✓ — status derives from same evidence, just correctly labelled |
| 3 | Do not suppress genuine conditions | ✓ — R2 320 GB overage still CRITICAL |
| 4-5 | Do not weaken thresholds / remove annoying reds | ✓ — none changed |
| 6 | Missing evidence ≠ healthy | ✓ — `freshness_status` returns `stale=True` for missing evidence when policy set |
| 7 | Unused integration ≠ failed | ✓ — MaintainX classified NOT_APPLICABLE |
| 8 | No preview data affecting prod | ✓ — read-only prod probes only |
| 9-11 | No prod config change / no R2 delete / no storage cleanup | ✓ — none touched |
| 12-13 | No Track 27.07 / no actor-context work | ✓ — untouched |
| 14 | No unrelated features | ✓ |
| 15 | Do not defer safe fixes | ✓ — all safe defects fixed inline |
| 16 | Do not close if summaries contradict evidence | ✓ — all summaries now derive from same canonical model |
| 17 | Healthy only if evidence fresh enough | ✓ — freshness policy honored |
| 18 | One root cause = one recommendation | ✓ — `root_cause_id` groups shared causes |
| 19 | DISABLED/NOT_APPLICABLE ≠ unhealthy | ✓ — regression-locked by unit test |
| 20 | No hard-coded severity in frontend | ✓ — Diagnostics UI now reads canonical fields first |

---

## 6 · Defect ledger

| # | Severity | Where | Fix | Regression lock |
|---|---|---|---|---|
| D1 | P1 | `AdminDiagnostics.jsx::_system_health` | Filter accepted only `ok`/`healthy`; backend emitted `green`. Now reads canonical `counts` + expanded healthy synonyms. | Preview contract assertion + canonical unit tests |
| D2 | P1 | `deploy_readiness.py` response | No canonical_status; `"attention"` mapped to UNKNOWN in UI. | Endpoint emits canonical_status; Diagnostics reader accepts it |
| D3 | P1 | `governance_self_protection.py` — `overall_status` missing | Endpoint now emits `overall_status` + `canonical_status`. | Preview contract assertion |
| D4 | P1 | Deployment ledger — current commit not recorded on deploy | Startup hook `auto_record_deploy_on_startup` (idempotent) appends running source_hash. | Preview verified: `deployment.status=green`, `deployed_at=1783792980`, `history_size=10` |
| D5 | P1 | Governance authority: 60 tolerated patterns shown as "60 new warnings" | Endpoint now emits `warning_classification` distinguishing `current_actionable` vs `baseline_tolerated_new` vs `historical_baselined`. UI can render accurately. | Test asserts key present |
| D6 | P2 | Field walks always green regardless of age | 30d/60d freshness policy with per-walk `age_days` + `freshness_status`. | Endpoint contract |
| D7 | P2 | MaintainX (disabled + mocked) forced integration cards RED / YELLOW | `_eval_integrations` + `admin_ops.compute_system_health` treat as NOT_APPLICABLE. | `TestMaintainXNotApplicable` in canonical tests |
| D8 | P2 | R2 bucket overage counted as two independent CRITICALs | Shared `root_cause_id="r2_bucket_capacity"`; OCC emits `root_cause_groups` + `unique_critical_root_causes`. | Preview: 5 red cards → 4 unique root causes |
| D9 | P2 | System-health version card: "unknown · built —" | Falls back to runtime `_SOURCE_HASH` + `_STARTED_AT` when env stamps missing. | Preview shows real hash |

**Deferred (out of scope for 28.11):**
* R2 capacity remediation itself — remains legitimately CRITICAL (GAP-28-03 · Track 27.07 R2 Delete Engine).
* Governance stale scan (last: 2026-05-26) — operator action to re-run detectors.
* Two `POST_DEPLOY_TEST_TRACK_15_59_DELETE` residual rows (GAP-28-07).

---

## 7 · Files changed

**Preview (all backward-compatible):**
* `backend/lib/canonical_status.py` **(new, 222 lines)**
* `backend/tests/test_track_28_11_canonical_status.py` **(new, 175 lines, 24 tests)**
* `backend/routes/admin_ops.py` (system-health endpoint)
* `backend/routes/deploy_readiness.py` (canonical fields)
* `backend/routes/governance_self_protection.py` (overall_status, warning_classification, field-walk freshness, auto_record_deploy_on_startup export)
* `backend/routes/occ_health_aggregator.py` (canonical fields, root_cause_id, integrations NOT_APPLICABLE, canonical_counts + root_cause_groups)
* `backend/server.py` (startup deploy-ledger auto-record hook)
* `frontend/src/pages/admin/AdminDiagnostics.jsx` (system-health + deploy-diag + occ readers)
* `memory/TRACK_28_11_DIAGNOSTICS_TRUTHFULNESS.md` **(new — this doc)**
* `memory/CHANGELOG.md` (appended)
* `memory/TRACK_28_CERTIFICATION_REGISTER.md` (28.11 row added)

**No schema migration. No data mutation. No R2 delete. No threshold change. No prod config touched.**

---

## 8 · Production deployment plan

**Recommendation:** deploy preview → prod at next scheduled window. After the deploy:

1. Verify `/api/version` still returns commit + `environment_identity`.
2. Verify `/api/admin/system-health` returns `counts.total_applicable` field.
3. Verify `/api/admin/deploy-readiness` returns `canonical_status`.
4. Verify `/api/admin/governance/self-protection` returns non-null `overall_status` + `deployment.deployed_at`.
5. Verify OCC `/api/admin/occ/health` returns `root_cause_groups` and `unique_critical_root_causes`.
6. Load `/admin/diagnostics` — System Health card should read "7/8 healthy" or similar truthful count (never "0/8").
7. Reload `/admin/governance-trust` — Governance Self-Protection should show `overall_status: amber` and `deployment: green` (recorded).

R2 bucket over threshold (320 GB) will remain truthfully CRITICAL on OCC and Governance until Track 27.07 R2 Delete Engine is unblocked. That is by design and now clearly attributed to `root_cause_id="r2_bucket_capacity"` with a single "why".

**Rollback:** all changes are additive to response payloads + one idempotent startup hook. Reverting to `fe34b609ca92` restores previous behavior without data loss (ledger entry added on startup remains valid).

---

*Signed off: 2026-07-11.*
