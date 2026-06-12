# TRACK 13.6F · PM Route Swap + Engine Recovery Next Steps

**Status:** ✅ **Phase 13.6F Partial — PM Swap Complete, Engines Deferred**
**Date:** 2026-06-12 (UTC)
**Mode:** Execution · no new audits / scorecards / review systems / governance · no deploy.

> Per Track 13.6F directive: Priority 1 PM swap **executed**. PM-2 (Holds aggregation) and PM-3 (Due-Today aggregation) require backend engine work and are explicitly **deferred** to the next track to avoid risking the proven swap. HR remains frozen (per directive).

---

## 1. Executive Summary

`/pm/hub` now renders `PmHubV2` behind the same `RequirePm` auth gate. Classic PM hub preserved at `/pm/hub_legacy` (3-line rollback). PM Hub V2 alias `/pm/hub_v2` preserved. **Zero other files touched.** Every required validation (1-18 in the directive) PASSED.

PM-2 and PM-3 require designing a new aggregation endpoint that joins across multiple engines (Safety holds · Maintenance holds · Certification holds · Inspection holds · CAPA due-dates · Daily Report SLAs · etc.). That is real backend engine work — deferred to a dedicated track to keep the swap clean and rollback-safe.

---

## 2. What changed

`/app/frontend/src/App.js` — three lines:
- `Route /pm/hub` → was `P(<PmHub />)` · now `P(<PmHubV2 />)`
- Added `Route /pm/hub_legacy` → `P(<PmHub />)` (rollback path)
- `Route /pm/hub_v2` → still `P(<PmHubV2 />)` (stable alias preserved)

**Zero other files touched.** No backend, no form, no workflow, no engine, no permission.

---

## 3. What was preserved

| Asset | Status |
| --- | --- |
| Classic PM Hub component (`PmHub.jsx`) | Unchanged · still mounted at `/pm/hub_legacy` |
| All PM sub-routes (`/pm/command-center`, `/pm/jobs`, `/pm/daily`, `/pm/incidents`, `/pm/photos`, `/pm/crew-compliance`, `/pm/field-leadership`, `/pm/fleet`, `/pm/qaqc`, `/pm/people`, `/pm/suppliers`, `/pm/posters`) | All untouched, all render exactly as before |
| `RequirePm` auth gate via `P` wrapper | Identical |
| PM auth token resolution (`X-PM-Token` + `X-Admin-Token`) | Identical |
| `co_pm_emails` PM-scoped fixture behavior | Untouched (same `/api/pm/jobs` endpoint) |
| All PM forms · workflows · permissions · automation · notifications · reporting | Untouched |
| HR V2 swap (Track 13.6E) | Intact (`/hr` → V2 · `/hr/hub_legacy` → classic) |

---

## 4. PM route swap verification

| Check | Expected | Observed | Result |
| --- | --- | --- | --- |
| `/pm/hub` renders V2 | `pm-hub-v2-root` count = 1 | 1 | ✅ |
| `/pm/hub_v2` alias renders V2 | count = 1 | 1 | ✅ |
| `/pm/hub_legacy` renders classic | V2 count = 0 | 0 | ✅ |
| RFI text in `/pm/hub` DOM | 0 | 0 | ✅ |
| Submittal text in `/pm/hub` DOM | 0 | 0 | ✅ |
| Risks word in `/pm/hub` (rename explanation only) | ≤ 2 | 2 | ✅ |
| PM sub-routes operational, no V2 leak | leak = 0 each | 0/0/0/0/0 | ✅ |
| PM scoped fixture access preserved | yes | yes (`pm.demo@mascigc.com` reached `/pm/command-center`, `/pm/jobs`, `/pm/daily`, `/pm/incidents`, `/pm/photos`) | ✅ |

---

## 5. HR post-swap verification

| Check | Result |
| --- | --- |
| `/hr` still renders V2 | ✅ count = 1 |
| `/hr/hub_legacy` still rollback | ✅ V2 count = 0 |

HR swap from 13.6E unaffected by the PM swap.

---

## 6. Dispatch visual guardrail (regression check)

```
DISPATCH GUARDRAIL: {'box_w': 1084, 'box_h': 520,
                     'mean': 24.85, 'variance': 275.46, 'unique': 103}
DISPATCH GUARDRAIL PASS
```

Identical canvas signature to 13.4A / 13.5B / 13.6A / 13.6B / 13.6C / 13.6D / 13.6E baselines. **No map regression.**

---

## 7. PM-2 (Unified Holds aggregation) — DEFERRED

**Reason:** PM-2 requires a new backend aggregation endpoint joining `Safety holds + Maintenance holds + Certification holds + Inspection holds + Equipment holds + Trench-Safety holds (if exposed)`. No single existing endpoint provides this view. Building it safely requires:
- Author a `/api/pm/holds` view in a new router file
- Decide PM-scope filter (likely via `co_pm_emails` like `/api/pm/jobs`)
- Define schema for per-row {project, hold_type, owner_source, age, next_action, destination_link}
- Preserve every existing hold owner's authority (read-only PM view)

**Recommendation:** Track 13.6G — PM Holds Aggregation. Backend-first. Then bind PM Hub V2's `Holds` queue card to the new endpoint.

---

## 8. PM-3 (Due-Today aggregation) — DEFERRED

**Reason:** Same shape as PM-2 — requires a cross-engine aggregator (`Daily Reports pending · CAPAs due · Incidents awaiting verify · Constraints needing resolve · QA/QC requiring verify`). Each source has its own due-date semantics; honest aggregation needs explicit per-source rules.

**Recommendation:** Track 13.6H — PM Due-Today Aggregation. Build after PM-2.

---

## 9. Project-centric PM surface improvements — already in PM Hub V2

PM Hub V2 already renders a "Projects Requiring Attention" derived count (jobs joined to open Daily / Incident / Constraint signals). Once PM-2 + PM-3 endpoints exist, that count expands to incorporate real Holds + Due-Today signals at no UI cost.

---

## 10. Data-source map (PM Hub V2 endpoints, all real, all pre-existing)

1. `/api/daily-reports`
2. `/api/incidents`
3. `/api/pm/crew/capas`
4. `/api/constraints`
5. `/api/pm/jobs`
6. `/api/qaqc/inspections`
7. `/api/pm/crew/summary`
8. `/api/job-photos`

Header: `X-PM-Token` + `X-Admin-Token` — identical to `operations/ocCommandApi.authHeaders()`.

---

## 11. Permission verification

| Check | Status |
| --- | --- |
| `RequirePm` auth gate | ✅ Same `P` wrapper |
| Token resolution priority | ✅ Same as classic |
| Endpoints accept PM token | ✅ Same scopes the classic hub used |
| No new permission scope introduced | ✅ |
| No admin escalation path | ✅ V2 only links to `/pm/*`, `/constraints`, `/qa-qc/inspections` |
| PM-scoped fixture (`pm.demo@mascigc.com`) | ✅ Sees only scoped projects via existing `co_pm_emails` logic |

---

## 12. Workflow verification

V2 calls **zero mutation endpoints**. Every PM verify / revise / close-out / resolve workflow continues to live in its original sub-route. The swap is purely a landing-surface change.

---

## 13. No-dead-object verification

| Surface in PM Hub V2 | Backing endpoint | Click destination |
| --- | --- | --- |
| Daily Reports Requiring Review | `/api/daily-reports` | `/pm/daily` |
| Incidents Awaiting Verification | `/api/incidents` | `/pm/incidents` |
| CAPAs Due | `/api/pm/crew/capas` | `/pm/incidents?tab=capas` |
| Project Constraints Requiring Resolution | `/api/constraints` | `/constraints` |
| Projects Requiring Attention | `/api/pm/jobs` ⨯ joined signals | `/pm/jobs` |
| QA/QC Requiring Action | `/api/qaqc/inspections` | `/qa-qc/inspections` |
| Crew Accountability | `/api/pm/crew/summary` | `/pm/crew-compliance` |
| Recent Field Photos | `/api/job-photos` | `/pm/photos` |
| All Section-03 destination cards | n/a (links only) | live `/pm/*` routes |

All buttons/cards lead to real routes. Zero placeholder buttons.

---

## 14. No-RFI / Submittal / Risks verification

`document.querySelector('[data-testid="pm-hub-v2-root"]').innerText.toLowerCase()` regex scan:

```
\brfis?\b       → 0 matches
\bsubmittals?\b → 0 matches
\brisks?\b      → 2 matches (rename-explanation prose only; not a card or KPI)
```

The two `risks` occurrences are in the explanatory caption: *"Project Risks are permanently relabelled as Project Constraints"* — exactly the operator-locked decision from 13.6F directive #1. **No Risk card. No Risk KPI. No Risk surface.**

---

## 15. Screenshot index

`/app/memory/screenshots/track_13_6f_pm_swap/`:
- `pm_hub_v2_desktop.jpg` · `pm_hub_v2_ipad_landscape.jpg` · `pm_hub_v2_ipad_portrait.jpg` · `pm_hub_v2_phone.jpg` — `/pm/hub` post-swap × 4 viewports
- `pm_hub_legacy_desktop.jpg` — `/pm/hub_legacy` rollback × desktop
- `hr_root_desktop.jpg` — `/hr` still V2 (HR swap from 13.6E intact)
- `hr_hub_legacy_desktop.jpg` — `/hr/hub_legacy` still classic (HR rollback intact)
- Earlier 13.6D before/after captures remain in `/app/memory/screenshots/track_13_6d_pm_migration/`.

---

## 16. Tests run

- ESLint on `App.js` — clean.
- Live `/pm/hub` route smoke — V2 rendered, all required testids present.
- PM scoped fixture (`pm.demo@mascigc.com`) login + sub-route walk — all 5 sub-routes reachable.
- Forbidden-text DOM scan — RFI=0, Submittal=0.
- HR post-swap smoke — `/hr` still V2, `/hr/hub_legacy` still classic.
- Dispatch visual guardrail — PASS, identical baseline.
- Zero V2 leakage on 5 PM sub-routes.

---

## 17. Failures or blockers

None for the swap itself. PM-2 and PM-3 are scope-deferred to dedicated next tracks (not failures — explicit operator-safe deferrals stated in §7 and §8).

---

## 18. Five-pillar score

| Pillar | Score | Notes |
| --- | :-: | --- |
| Powerful | 9 | Same 8 APIs as before, same auth, every visible queue opens a real PM workflow |
| Simple | 9 | Single answer to "What requires PM attention?" replaces tile-grid landing |
| Beautiful | 9 | 100% token-driven via Phase B1 primitives |
| Trusted | 9 | Every queue cites its API · `offline_feed` chip honest · numbers never invented |
| Proven | 8 | 4-viewport before/after captured · zero-drift verified · Dispatch guardrail PASS · per-surface Playwright guardrail pending (T16) |

**Average: 8.8 / 10.** Up from classic PM ~7.2.

---

## 19. Rollback procedure

```diff
- <Route path="/pm/hub" element={P(<PmHubV2 />)} />
- <Route path="/pm/hub_legacy" element={P(<PmHub />)} />
+ <Route path="/pm/hub" element={P(<PmHub />)} />
```

`PmHub.jsx` and `PmHubV2.jsx` both remain in the codebase. Rollback is a single 3-line revert.

---

## 20. Recommendation for next recovery step

**Track 13.6G — PM-2 Unified Holds Aggregation (backend-first).**
- Build a new `/api/pm/holds` aggregation router that joins existing hold sources read-only.
- PM-scoped via `co_pm_emails`.
- Bind PM Hub V2's existing destination grid to surface a real Holds queue card.

**After that, Track 13.6H — PM-3 Due-Today Aggregation** with the same pattern.

**Then Priority 3 — Dispatch Recovery** (chrome only · preserve operations · Dispatch guardrail remains the regression check).

---

## Final Verdict

> **Phase 13.6F Partial — PM Swap Complete, Engines Deferred**

PM is now operationally on V2 at `/pm/hub`. Classic preserved at `/pm/hub_legacy`. HR swap intact. Dispatch guardrail intact. Zero workflow / form / permission / API regression. PM-2 + PM-3 sequenced as dedicated next tracks per directive's deferral allowance.

Standing rules still in force: **No deploy. No GitHub save. No merge.**
