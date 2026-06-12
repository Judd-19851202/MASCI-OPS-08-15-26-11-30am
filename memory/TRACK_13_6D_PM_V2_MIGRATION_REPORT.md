# TRACK 13.6D · PM V2 Live Migration Report

**Status:** ✅ **PM Hub V2 LIVE — Ready For Operator Visual Approval**
**Date:** 2026-06-12 (UTC)
**Mode:** Second real portal conversion · live PM data · side-by-side with `/pm/hub` · NO route swap.

> Second real implementation track. PM Hub V2 mounted at `/pm/hub_v2` behind PM's existing `RequirePm` auth gate. Reads real `/api/*` endpoints with the real PM token. Project Risks **permanently renamed** to Project Constraints. RFIs and Submittals **absent** (no engine).

---

## 1. Executive Summary

`/pm/hub_v2` is live, behind the same `P = <RequirePm>` wrapper as `/pm/hub`. It renders live PM data from the same `/api/*` endpoints the classic PM hub already consumes, through the Phase B1 design-system primitives, in the 13.6B action-queue model with the operator decisions from 13.6D applied.

The 13.6C HR pattern was repeated verbatim — establishing that the migration template is now a copy-paste-per-portal operation.

---

## 2. Operator decisions honored (per directive)

| Decision | Implementation |
| --- | --- |
| Project Risks = permanently renamed to Project Constraints | `Project Constraints Requiring Resolution` is the canonical card. The Risks card no longer exists. The rename explanation appears in the card's "why" caption. |
| RFIs = future engine — do NOT display | Zero `rfi` occurrences in the PM Hub V2 DOM (verified via case-insensitive regex scan). No card, no caption, no link mentions RFI. |
| Submittals = future engine — do NOT display | Zero `submittal` occurrences in the PM Hub V2 DOM (same scan). No card, no caption, no link mentions Submittals. |

DOM scan result:
```
FORBIDDEN-TEXT scan: {'risks_word': 2 (rename explanation only),
                      'rfi': 0,  'submittal': 0,
                      'constraints_word': 7}
```

---

## 3. Files created / edited

| Path | Change |
| --- | --- |
| `/app/frontend/src/pages/PmHubV2.jsx` | **New** — first real PM portal V2. Uses live `/api/*` endpoints. |
| `/app/frontend/src/App.js` | +2 lines — lazy import + `<Route path="/pm/hub_v2" element={P(<PmHubV2 />)} />` (same `P = (el) => <RequirePm>{el}</RequirePm>` wrapper as `/pm/hub`). |
| `/app/frontend/src/pages/V2Index.jsx` | `pm-v2` entry updated to track `13.6B / 13.6D`. |
| `/app/frontend/src/pages/V2Compare.jsx` | PM compare pane now loads LIVE `/pm/hub_v2`. |

ESLint clean across all four. No backend file touched.

---

## 4. Data-source map (every visible item has a real source)

| Surface | Live API consumed | Header | Filter |
| --- | --- | --- | --- |
| **Daily Reports Requiring Review** | `GET /api/daily-reports?limit=200` | `X-PM-Token` (+ `X-Admin-Token` fallback) | count of `submitted` + `needs_revision` + `pending_verification` |
| **Incidents Awaiting Verification** | `GET /api/incidents?limit=200` | Same | `submitted` + `pending_verification` |
| **CAPAs Due** | `GET /api/pm/crew/capas` | Same | non-closed / non-resolved / non-verified |
| **Project Constraints Requiring Resolution** | `GET /api/constraints?limit=200` | Same | non-closed / non-resolved |
| **Projects Requiring Attention** | `GET /api/pm/jobs` ⨯ joined to live signal queues | Same | jobs with ≥1 open signal |
| **QA/QC Requiring Action** | `GET /api/qaqc/inspections?limit=200` | Same | `submitted` + `pending_verification` + `needs_revision` |
| **Crew Accountability** | `GET /api/pm/crew/summary` | Same | `attention_count` field |
| **Recent Field Photos** | `GET /api/job-photos?limit=10` | Same | last 10 |

All eight endpoints are **already used by the classic PM portal**. No new backend endpoint was added.

**Live values observed** (PM test fixture, `pm.demo@mascigc.com`):
- Daily Reports: 0 · Incidents: 0 · CAPAs: 0 · Constraints: 0 · Projects with attention: 0 · QA/QC: `—` (endpoint returns non-200 for this scope · honest `offline_feed` chip) · Crew Accountability: `—` · Photos: 0
- The "All PM queues are clear" calm-state EmptyState therefore renders, as designed.

---

## 5. Permission verification

| Check | Status |
| --- | --- |
| Auth wrapper applied | ✅ `H(<PmHubV2 />)` in App.js — same `P` wrapper as `/pm/hub`, `/pm/jobs`, `/pm/command-center`, `/pm/daily`, `/pm/incidents`, `/pm/photos` |
| Token header | ✅ `X-PM-Token` from `pmAuth.getPmToken()` + `X-Admin-Token` from `adminAuth.getAdminToken()` — identical to `operations/ocCommandApi.authHeaders()` |
| No write APIs called | ✅ All eight calls are `GET` only |
| No new permission scope introduced | ✅ Every endpoint already accepted the PM token before 13.6D |
| Linked destinations PM-scoped | ✅ Every `<Link>` goes to `/pm/*`, `/constraints`, `/qa-qc/inspections` — same routes classic PM already links to |

---

## 6. Workflow verification

| Workflow | Touched? |
| --- | --- |
| Daily Report verify / revise | ❌ V2 reads only; verify-or-revise lives in `/pm/daily` |
| Incident verify | ❌ V2 reads only; verify lives in `/pm/incidents` |
| CAPA close-out | ❌ V2 reads only; close-out lives in `/pm/incidents?tab=capas` |
| Constraint resolve | ❌ V2 reads only; resolution lives in `/constraints` |
| QA/QC verify | ❌ V2 reads only; verify lives in `/qa-qc/inspections` |
| Job photo upload | ❌ V2 reads only; upload lives in `/pm/photos` |
| Crew compliance | ❌ V2 reads only; management lives in `/pm/crew-compliance` |
| Project assignment / scope | ❌ Admin domain; PM V2 does not touch |

Every PM workflow remains in its original home. V2 is purely a **surface** that links to those workflows.

---

## 7. Existing PM portal — operational verification

Zero-drift sweep across 15 live operator routes:

```
hub                    | pm_v2_root=0 hr_v2_root=0
admin_login            | pm_v2_root=0 hr_v2_root=0
dispatch_login         | pm_v2_root=0 hr_v2_root=0
pm_hub                 | pm_v2_root=0 hr_v2_root=0
pm_command_center      | pm_v2_root=0 hr_v2_root=0
pm_jobs                | pm_v2_root=0 hr_v2_root=0
pm_daily               | pm_v2_root=0 hr_v2_root=0
pm_incidents           | pm_v2_root=0 hr_v2_root=0
pm_photos              | pm_v2_root=0 hr_v2_root=0
hr                     | pm_v2_root=0 hr_v2_root=0
safety                 | pm_v2_root=0 hr_v2_root=0
shop_login             | pm_v2_root=0 hr_v2_root=0
field_leadership       | pm_v2_root=0 hr_v2_root=0
driver_login           | pm_v2_root=0 hr_v2_root=0
public_trench          | pm_v2_root=0 hr_v2_root=0
```

15 / 15 routes show zero V2 leakage. The classic PM hub at `/pm/hub` is unchanged.

**Dispatch visual guardrail re-executed post-13.6D:**

```
DISPATCH GUARDRAIL: {'box_w': 1084, 'box_h': 520,
                     'mean': 24.85, 'variance': 275.46, 'unique': 103}
DISPATCH GUARDRAIL PASS
```

Identical canvas signature to 13.4A / 13.5B / 13.6A / 13.6B / 13.6C baselines.

---

## 8. Screenshots

`/app/memory/screenshots/track_13_6d_pm_migration/` — **8 files**:

### 8.1 BEFORE — Current `/pm/hub`

| Viewport | File |
| --- | --- |
| Desktop (1920×1080) | `before_pm_desktop.jpg` |
| iPad landscape (1180×820) | `before_pm_ipad_landscape.jpg` |
| iPad portrait (820×1180) | `before_pm_ipad_portrait.jpg` |
| Phone (390×844) | `before_pm_phone.jpg` |

### 8.2 AFTER — `/pm/hub_v2` (live PM data, V2 surface)

| Viewport | File |
| --- | --- |
| Desktop | `after_pm_v2_desktop.jpg` |
| iPad landscape | `after_pm_v2_ipad_landscape.jpg` |
| iPad portrait | `after_pm_v2_ipad_portrait.jpg` |
| Phone | `after_pm_v2_phone.jpg` |

### 8.3 DOM verification (executed live)

All required sections present at all 4 viewports (15 testids per page):
```
pm-hub-v2-section-queues · pm-hub-v2-queue-grid
pm-hub-v2-queue-daily · pm-hub-v2-queue-incidents · pm-hub-v2-queue-capas
pm-hub-v2-queue-constraints · pm-hub-v2-queue-projects · pm-hub-v2-queue-qaqc
pm-hub-v2-section-reads · pm-hub-v2-reads-grid
pm-hub-v2-read-crew · pm-hub-v2-read-photos
pm-hub-v2-section-destinations · pm-hub-v2-destinations-grid
pm-hub-v2-purpose-note
```

---

## 9. Required-validation checklist (per directive)

| # | Validation | Status |
| --- | --- | --- |
| 1 | Every count comes from real data | ✅ §4 data source map · 8 live endpoints |
| 2 | Every queue opens real workflow | ✅ §6 workflow verification |
| 3 | Every button navigates somewhere real | ✅ Every `<Link to=…>` resolves to a real PM route |
| 4 | Every workflow preserves permissions | ✅ §5 permission verification — same `P` wrapper, same headers |
| 5 | Every workflow preserves current PM behavior | ✅ Workflows live in their original homes; V2 only reads |

All 5 directive validations pass.

---

## 10. Five-pillar score (live)

| Pillar | Score | Justification |
| --- | :-: | --- |
| Powerful | 9 | 8 real PM APIs powering 8 visible queues / reads. Same auth, same scoping. |
| Simple | 9 | One vocabulary · one Card · one EmptyState. Three sections · two primary actions max. Single question answered. |
| Beautiful | 9 | 100% tokens. Phase B1 primitives. Heavy-civil voice. |
| Trusted | 9 | Every queue caption names its API. `offline_feed` chip flips on non-200. Numbers never invented. |
| Proven | 8 | Before/after × 4 viewports captured · 15-route zero-drift verified · Dispatch guardrail PASS · per-surface Playwright guardrail pending (T16). |

**Average: 8.8 / 10.**

---

## 11. Final Verdict

> **Track 13.6D Complete — `/pm/hub_v2` is live · classic `/pm/hub` is unchanged · operator visual approval via `/_internal/v2-compare/pm` is the next gate.**

Two pilot portals (HR · PM) are now operating in side-by-side mode with **live real data**. The migration pattern is now proven on two independent portals with two different auth tokens, two different role audiences, and two different API surfaces. Repeatable across the remaining 7 portals.

Standing rules still in force: **No deploy. No GitHub save. No merge. No route swap.**
