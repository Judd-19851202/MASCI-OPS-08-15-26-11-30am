# Track 13.6B · Operational Surface Conversion Plan

**Status:** ✅ Phase Complete — Ready For Operator Visual Review
**Date:** 2026-06-12 (UTC)
**Mode:** Preview-lane only · no portal swap · no live route change · no deploy.

> Master document for Track 13.6B. Plan + execution summary + verdict. Individual conversion details live in the PM, HR, Review-System, and Migration-Readiness companion reports.

---

## 1. Mission recap

Convert MASCI from a **collection of dashboards** into an **Operational Heavy-Civil OS** by enforcing five rules on the two active V2 preview lanes (PM, HR) and standing up an internal review system:

| Rule | Enforcement |
| --- | --- |
| #1 — No dead objects | Every visible item exists, has a destination, has a workflow. |
| #2 — Every KPI leads somewhere | Counts are queue sizes; clicking a count opens a real queue. |
| #3 — Actions over numbers | "What requires me today?" beats "how many?". |
| #4 — Operator review visibility | `/_internal/v2-index` hub + `/_internal/v2-compare/:portal` side-by-side view. |
| #5 — Before migrating any portal | Operator must visually approve the side-by-side comparison. |

---

## 2. Files created or rewritten

| File | Change | Purpose |
| --- | --- | --- |
| `/app/frontend/src/pages/PmV2Preview.jsx` | **Rewritten** (overwrite) | Action-queue PM V2. Every card opens a real PM queue. Vanity counts removed. |
| `/app/frontend/src/pages/HrV2Preview.jsx` | **Rewritten** (overwrite) | Action-queue HR V2. Vanity headcount removed. |
| `/app/frontend/src/pages/V2Index.jsx` | **New** | Operator review hub at `/_internal/v2-index`. |
| `/app/frontend/src/pages/V2Compare.jsx` | **New** | Side-by-side current-vs-V2 viewer at `/_internal/v2-compare/:portal`. |
| `/app/frontend/src/App.js` | **+3 lines** | Lazy imports + 2 new routes (`/v2-index`, `/v2-compare/:portal`). |

No operator-route file touched. No backend file touched. ESLint clean on all 4 new/rewritten frontend files.

---

## 3. New internal routes

| Route | Purpose | Linked from operator nav? |
| --- | --- | --- |
| `/_internal/pm-v2-preview` | PM V2 action-queue preview (updated) | No |
| `/_internal/hr-v2-preview` | HR V2 action-queue preview (updated) | No |
| `/_internal/v2-index` | Operator review hub | No |
| `/_internal/v2-compare/pm` | PM current vs V2 side-by-side | No |
| `/_internal/v2-compare/hr` | HR current vs V2 side-by-side | No |

All routes are deep-linkable but not advertised. Direct URL only.

---

## 4. Hard-rule verification (executed live)

### 4.1 No-dead-object verification — PM V2

Forbidden surfaces (no MASCI engine exists for any of these):

```
[data-testid="pm-v2-rfis-table"]        → 0   ✓
[data-testid="pm-v2-submittals-table"]  → 0   ✓
[data-testid="pm-v2-risks-table"]       → 0   ✓
[data-testid="pm-v2-photos-grid"]       → 0   ✓   (mock grid removed; live link to /pm/photos kept)
```

Required action-queue surfaces (all present at all 4 viewports):

```
[data-testid="pm-v2-queue-grid"]           → 1
[data-testid="pm-v2-projects-action-table"] → 1
[data-testid="pm-v2-verify-grid"]          → 1
[data-testid="pm-v2-capas-table"]          → 1
[data-testid="pm-v2-constraints-table"]    → 1
[data-testid="pm-v2-photos-card"]          → 1   (real link to /pm/photos)
[data-testid="pm-v2-daily-card"]           → 1   (real link to /pm/daily)
[data-testid="pm-v2-purpose-note"]         → 1
```

### 4.2 Required surfaces — HR V2

```
[data-testid="hr-v2-queue-grid"]           → 1
[data-testid="hr-v2-requests-table"]       → 1
[data-testid="hr-v2-driver-qual-table"]    → 1
[data-testid="hr-v2-training-table"]       → 1
[data-testid="hr-v2-payroll-table"]        → 1
[data-testid="hr-v2-accountability-table"] → 1
[data-testid="hr-v2-purpose-note"]         → 1
```

### 4.3 Required surfaces — V2 Index

```
[data-testid="v2-index-section-operational"] → 1
[data-testid="v2-index-section-planned"]     → 1
[data-testid="v2-index-row-pm-v2"]           → 1
[data-testid="v2-index-row-hr-v2"]           → 1
[data-testid="v2-index-pm-v2-compare"]       → 1
[data-testid="v2-index-hr-v2-compare"]       → 1
[data-testid="v2-index-rules-note"]          → 1
```

### 4.4 Required surfaces — V2 Compare

PM compare:
```
[data-testid="v2-compare-grid-pm"]            → 1
[data-testid="v2-compare-current-pm-iframe"]  → 1
[data-testid="v2-compare-v2-pm-iframe"]       → 1
[data-testid="v2-compare-rule-pm"]            → 1
```
HR compare:
```
[data-testid="v2-compare-grid-hr"]            → 1
[data-testid="v2-compare-current-hr-iframe"]  → 1
[data-testid="v2-compare-v2-hr-iframe"]       → 1
[data-testid="v2-compare-rule-hr"]            → 1
```

Unknown portal:
```
/_internal/v2-compare/xyz → [data-testid="v2-compare-unknown"] → 1 (calm EmptyState, back link)
```

---

## 5. Zero-drift verification

Identical sweep methodology from 13.6A re-run across the same 15 live operator routes:

```
hub                    | shell=0 chip=0 pm_v2=0 hr_v2=0 idx=0 cmp_pm=0 cmp_hr=0
admin_login            | shell=0 chip=0 pm_v2=0 hr_v2=0 idx=0 cmp_pm=0 cmp_hr=0
dispatch_login         | shell=0 chip=0 pm_v2=0 hr_v2=0 idx=0 cmp_pm=0 cmp_hr=0
pm_hub / command_center / jobs / daily / incidents / photos
                       | shell=0 chip=0 pm_v2=0 hr_v2=0 idx=0 cmp_pm=0 cmp_hr=0   (×6)
hr_hub                 | shell=0 chip=0 pm_v2=0 hr_v2=0 idx=0 cmp_pm=0 cmp_hr=0
safety                 | shell=0 chip=0 pm_v2=0 hr_v2=0 idx=0 cmp_pm=0 cmp_hr=0
shop_login             | shell=0 chip=0 pm_v2=0 hr_v2=0 idx=0 cmp_pm=0 cmp_hr=0
field_leadership       | shell=0 chip=0 pm_v2=0 hr_v2=0 idx=0 cmp_pm=0 cmp_hr=0
driver_login           | shell=0 chip=0 pm_v2=0 hr_v2=0 idx=0 cmp_pm=0 cmp_hr=0
public_trench          | shell=0 chip=0 pm_v2=0 hr_v2=0 idx=0 cmp_pm=0 cmp_hr=0
```

15 routes · 7 markers each · all zero · **zero design-system or V2 leakage**.

Dispatch visual guardrail re-executed (post-13.6B):

```
DISPATCH GUARDRAIL: {'box_w': 1084, 'box_h': 520,
                     'mean': 24.85, 'variance': 275.46, 'unique': 103}
DISPATCH GUARDRAIL PASS
```

Identical canvas signature to 13.4A / 13.5B / 13.6A baselines. **No map regression.**

---

## 6. Screenshot evidence

`/app/memory/screenshots/track_13_6b_recovery/` — **17 files**:

| Surface | Files |
| --- | --- |
| PM V2 (action-queue) | `pm-v2-preview_{desktop,ipad_landscape,ipad_portrait,phone}.jpg` |
| HR V2 (action-queue) | `hr-v2-preview_{desktop,ipad_landscape,ipad_portrait,phone}.jpg` |
| V2 Index | `v2-index_{desktop,ipad_portrait}.jpg` |
| V2 Compare · PM | `v2-compare-pm_desktop.jpg` |
| V2 Compare · HR | `v2-compare-hr_desktop.jpg` |

---

## 7. Final Verdict

> **Phase Complete — Ready For Operator Visual Review**

All 13.6B rules honored:
- PM V2 + HR V2 are now action-queue surfaces; every count is a queue size; every card opens a real queue.
- No dead objects. No vanity metrics. No fake buttons.
- Operator review hub live at `/_internal/v2-index`.
- Side-by-side compare live at `/_internal/v2-compare/pm` and `/_internal/v2-compare/hr`.
- Zero drift across 15 live operator routes.
- Dispatch map guardrail PASS.
- No deploy. No GitHub save. No merge.

Next gate: operator visual approval via the side-by-side comparison views, leading to Phase B3 pilot migration authorization. See `TRACK_13_6B_MIGRATION_READINESS_REPORT.md`.
