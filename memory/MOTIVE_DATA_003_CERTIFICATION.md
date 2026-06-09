# MOTIVE-DATA-003 · Operational Impact Command Card · Certification

**Sprint:** MOTIVE-DATA-003
**Status:** ✅ GREEN
**Date:** 2026-02-09
**Dependencies:** MOTIVE-DATA-002 ✅ (operational workspace) · VER-1 ✅ (trust derivation)
**Companion:** `MOTIVE_DATA_003_AUDIT.md`

---

## 1. Brief ↔ Build matrix

| Requirement | Status | Where |
|---|---|---|
| **R1** Operational Impact card at top of `/admin/asset-mapping` with 8 metrics | ✅ | `pages/admin/AdminAssetMapping.jsx` — card with `data-testid="am-operational-impact"`, 8 stat tiles: Current Trust · Potential Trust · HIGH Matches Waiting · Est. Dispatches Impacted · Est. Assets Confirmed · Coverage % · Mapped Assets · Unmapped Assets |
| **R2** "Review HIGH Confidence Matches" primary action button | ✅ | `am-review-high-btn` — sets local `bandFilter = "HIGH"` on the existing queue and smooth-scrolls to it. **No new endpoint** — reuses existing `/admin/asset-mapping/queue`. New chip row `am-queue-filter-{BAND}` lets operator pivot bands in-place. |
| **R3** Impact Preview Summary — current vs projected state | ✅ | `am-impact-preview` block renders Current State (Coverage / Trust / Mapped) next to Projected State (same fields, emerald-bordered) — derived from new endpoint's `current` + `potential` blocks. Reason line beneath surfaces `readiness_reason`. |
| **R4** Executive Readiness Banner (NOT READY / PARTIALLY READY / READY FOR ACTIVATION) | ✅ | `am-readiness-banner` pill in card header. Rules **exactly per directive**: `coverage ≥ 75% AND high == 0 → READY_FOR_ACTIVATION`; `coverage > 25% → PARTIALLY_READY`; else `NOT_READY`. Visibility only — no automation. |
| **R5** Day-1 Activation Shortcut → existing runbook | ✅ | `am-runbook-link` button. Reuses `/app/memory/MOTIVE_DAY1_ACTIVATION_RUNBOOK.md` (no new document generated). Toast surfaces the file path for operators on the pod. |

---

## 2. Endpoint added (1, read-only, admin-gated)

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/admin/asset-mapping/operational-impact` | Aggregate rollup for the Operational Impact card — current/potential trust & coverage, HIGH-waiting count, estimated dispatches impacted, readiness banner verdict. Pure derivation across `dispatch_assignments`, `asset_mappings`, `asset_mapping_proposals`, `operational_events`. |

**Zero new collections. Zero writes. Zero workflow changes.** Constitutional guard test (`test_no_httpx_no_motive_writes_in_router_source`) confirms the router still has no `httpx` and no `motive_service` imports.

---

## 3. Live verification (real preview backend)

```
$ curl /api/admin/asset-mapping/operational-impact
{
  "ok": true,
  "current":   { "trust_score_pct": 0.0, "coverage_pct": 0.0,
                 "mapped_assets": 0, "unmapped_assets": 219,
                 "total_dispatch_trucks": 219 },
  "potential": { "trust_score_pct": 79.3, "coverage_pct": 0.0,
                 "mapped_assets": 0, "unmapped_assets": 219 },
  "actions":   { "high_confidence_waiting": 0,
                 "estimated_dispatches_impacted": 0,
                 "estimated_assets_confirmed": 0 },
  "readiness": "NOT_READY",
  "readiness_reason": "Coverage 0.0% < 25% · 0 HIGH match(es) waiting · 219 unmapped truck(s)",
  "runbook_path": "/app/memory/MOTIVE_DAY1_ACTIVATION_RUNBOOK.md"
}
```

The banner correctly verdicts **NOT READY** because preview is a synthetic-dispatch env without `equipment_master` twins — no proposals score HIGH yet. Once the operator runs Day-1 scan in production, the same endpoint will tilt the banner.

---

## 4. Test results

```
$ pytest tests/test_motive_data_003.py -v
============== 9 passed in 72.90s ==============
```

| Test | Verifies |
|---|---|
| `test_endpoint_requires_admin_token` | 401/403 without `X-Admin-Token` |
| `test_operational_impact_shape` | All required keys present in current/potential/actions |
| `test_readiness_value_in_enum` | Enum-valid readiness |
| `test_readiness_logic_consistent_with_directive` | NOT_READY / PARTIALLY_READY / READY_FOR_ACTIVATION rules |
| `test_projected_state_monotonic` | Approving can only ↑ mapped/coverage, ↓ unmapped |
| `test_estimated_assets_confirmed_equals_high_waiting` | Action-count parity |
| `test_no_writes_on_repeated_get` | Queue counts unchanged after 2 GETs |
| `test_runbook_path_returned` | R5 shortcut path returned |
| `test_no_httpx_no_motive_writes_in_router_source` | Constitutional guard |

**Full Motive regression (80/80 green):**
- `test_motive_data_001.py` 15/15 ✅
- `test_motive_data_003.py` 9/9 ✅ (new)
- `test_ver1_verification.py` ✅
- `test_m2_event_router.py` ✅
- `test_m3_geocode_foundation.py` ✅
- `test_mdr1_equipment_detection.py` ✅

Lint: ✅ ruff clean · ✅ eslint clean (0 blocking).

---

## 5. UI verification

Smoke screenshot on `/admin/asset-mapping` (1920×1400, full page):

- ✅ `am-operational-impact` card renders at the very top (above existing 002 surfaces)
- ✅ `am-readiness-banner` shows **NOT READY** pill with red dot
- ✅ All 8 metric tiles render (`am-impact-current-trust`, `am-impact-potential-trust`, `am-impact-high-waiting`, `am-impact-dispatches`, `am-impact-assets-confirmed`, `am-impact-coverage`, `am-impact-mapped`, `am-impact-unmapped`)
- ✅ `am-impact-preview` block shows Current State vs Projected State side-by-side; projected card is emerald-bordered
- ✅ `am-review-high-btn` rendered (disabled because high_confidence_waiting=0)
- ✅ `am-runbook-link` rendered
- ✅ `am-queue-filter` chip row present with all 5 band filters
- ✅ Existing 002 surfaces (Top 10, queue, exec summary) still render below

---

## 6. Constitutional adherence

| Forbidden | Enforcement |
|---|---|
| ❌ Automation | Endpoint is GET-only · button only navigates · no auto-approve |
| ❌ New collection | None added |
| ❌ New workflow | Existing approve/reject + scan flows unchanged |
| ❌ Motive writes | Constitutional guard test passes |
| ❌ Dispatch writes | No `dispatch_assignments` mutation anywhere |
| ❌ FleetWatcher | Not touched |
| ❌ Material automation | Not touched |
| ❌ Auto approvals | Operator still clicks Approve on every proposal |
| ❌ Auto mappings | Not introduced |
| ❌ Push-to-Motive | No outbound HTTP to Motive |
| ❌ Driver analytics / scoring / route optimization | Not present in this router |

---

## 7. Pillar scorecard

| Pillar | Score | Why |
|---|---|---|
| Powerful | 🟢 | 4-question 30-second answer surface — readiness, blockers, top fix, projected impact |
| Simple | 🟢 | 1 new endpoint · 1 new card · 0 new collections · 0 new workflows |
| Beautiful | 🟢 | Readiness banner · projected-state emerald accent · single-glance hierarchy |
| Trusted | 🟢 | Honest live numbers · operator approves every action · pure derivation |
| Proven | 🟢 | 9/9 new tests + 71/71 prior regression = 80/80 across the Motive estate |

---

## 8. Success criterion

> An Operations Manager can open the page and determine within 30 seconds:
> * Are we ready?
> * What is blocking us?
> * What should be fixed first?
> * What will happen if we fix it?

**Met.** The Operational Impact card answers all 4 in a single screen above the fold:
- "Are we ready?" → readiness banner
- "What is blocking us?" → readiness_reason line + HIGH Matches Waiting / Unmapped counters
- "What should be fixed first?" → Review HIGH Confidence Matches button + existing Top-10 ROI table below
- "What will happen if we fix it?" → Projected State emerald card (Coverage / Trust / Mapped)

🛑 **STOP.** FleetWatcher / Dispatch automation / Material automation NOT initiated.
