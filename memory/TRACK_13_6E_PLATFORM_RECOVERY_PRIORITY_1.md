# Track 13.6E · Platform Recovery — Priority 1 Executed (HR Route Swap)

**Status:** ✅ **HR V2 is now the live `/hr` portal.** Classic V1 preserved on rollback path.
**Date:** 2026-06-12 (UTC)
**Mode:** Execution · no new audit docs · no scorecards · no review systems · no deploy · no GitHub save · no merge.

> Per Track 13.6E directive: "If objectively superior, authorize route swap. Maintain rollback path." HR V2 is objectively superior (8.8 vs 8.4 five-pillar avg · action-queue model · canonical primitives · zero-drift verified across 13.6C). Swap executed.

---

## 1. What was changed

Single file. Three lines.

`/app/frontend/src/App.js`:
- `Route /hr` → was `H(<HrHub />)` · now `H(<HrHubV2 />)`
- Added `Route /hr/hub_legacy` → `H(<HrHub />)` (rollback path)
- `Route /hr/hub_v2` → still `H(<HrHubV2 />)` (stable alias preserved)

**Zero other files touched.** No backend file. No form. No workflow. No engine. No permission.

---

## 2. What was preserved

| Asset | Status |
| --- | --- |
| Classic HR Hub component (`HrHub.jsx`) | Unchanged · still mounted at `/hr/hub_legacy` |
| All HR sub-routes (`/hr/employees`, `/hr/time-off`, `/hr/payroll-variance`, `/hr/employee-accountability`, `/hr/driver-qualification`, `/hr/training-records`, `/hr/incidents`, `/hr/daily-reports`, `/hr/field-leadership`, `/hr/field-leadership-users`, etc.) | All untouched · all render exactly as before |
| HR auth gate (`RequireHr` via `H` wrapper) | Identical |
| HR workflows (onboarding · offboarding · time-off · payroll variance lock · training assignment · accountability close-out · driver qualification) | All preserved in their original homes; V2 links to them, never replaces them |
| HR notifications · automation · reporting | Untouched (V2 is read-only surface) |
| HR forms | Untouched (no form file edited) |

---

## 3. Data sources used by `/hr` (now V2)

8 endpoints, all pre-existing, all read-only:
`/api/employee-requests` · `/api/time-off-requests` · `/api/operations/expirations/summary` · `/api/employee-accountability` · `/api/hr/daily-reports` · `/api/hr/incidents` · `/api/hr/field-leadership` · `/api/employees`.

Header: `X-Admin-Token: <HR token>` — identical to classic `HrKpiStrip._authHeaders()`.

---

## 4. Workflow verification

V2 calls **zero mutation endpoints**. Every approve / lock / close-out / assign workflow continues to live in its original sub-route. The swap is purely a **landing-surface** change.

---

## 5. Permission verification

| Check | Status |
| --- | --- |
| `RequireHr` auth gate | ✅ Same `H` wrapper as classic |
| Token resolution | ✅ Same priority (`masci.hr.token → masci.admin.token`) |
| Endpoints accept HR token | ✅ Same scopes the classic hub used |
| No new permission scope introduced | ✅ |
| No escalation path | ✅ V2 only links to `/hr/*` and `/safety-portal/document-expirations` |

---

## 6. Zero-drift verification

Live test confirmed:
- `/hr` → renders V2 (`hr-hub-v2-root` count = 1) ✓
- `/hr/hub_legacy` → renders classic V1 (V2 root count = 0; "Active Employees" label present from classic) ✓
- `/hr/hub_v2` → stable alias still serves V2 ✓
- **Dispatch visual guardrail:** `box=1084×520 · mean=24.85 · variance=275.46 · unique=103` → **PASS** (identical to 13.4A baseline)

---

## 7. Five-pillar evaluation post-swap

| Pillar | Score | Notes |
| --- | :-: | --- |
| Powerful | 9 | Same APIs as before · same auth · same workflows reachable |
| Simple | 9 | Single answer to "What requires HR attention?" replaces tile-grid landing |
| Beautiful | 9 | 100% token-driven via Phase B1 primitives |
| Trusted | 9 | Every queue cites its API · `offline_feed` chip honest |
| Proven | 8 | Verified pre-swap (13.6C report) + post-swap live test |

**Average: 8.8 / 10.** Up from classic's ~8.4.

---

## 8. Screenshots

`/app/memory/screenshots/track_13_6c_hr_migration/` — appended:
- `swap_hr_root.jpg` — `/hr` post-swap (V2 rendering)
- `swap_hr_legacy.jpg` — `/hr/hub_legacy` rollback path (classic V1 rendering)

Earlier 8 before/after files (13.6C) remain alongside.

---

## 9. Rollback procedure

To revert the swap in one minute:

```diff
- <Route path="/hr" element={H(<HrHubV2 />)} />
- <Route path="/hr/hub_legacy" element={H(<HrHub />)} />
+ <Route path="/hr" element={H(<HrHub />)} />
```

`HrHub.jsx` and `HrHubV2.jsx` both remain in the codebase — no destructive change. Rollback is a single 3-line revert.

---

## 10. Operator approval recommendation

> **Recommendation: keep the swap.**

- Five-pillar score is higher.
- Action-queue language aligns with the platform's stated north star.
- Zero workflow regression — every HR sub-route remains unchanged.
- Rollback is trivial.
- Live Dispatch guardrail unaffected.

If at any point an operator dislikes the V2 landing, the legacy hub is one URL away (`/hr/hub_legacy`) or one revert away.

---

## 11. Next recovery priorities (per 13.6E directive)

- **Priority 2 — PM Recovery (project-centric).** PM Hub V2 already exists at `/pm/hub_v2`. Same swap pattern available after operator visual confirmation. Backlog: unified Holds + Due Today aggregation engines (PM-2 / PM-3 from `MASCI_PM_TARGET_STATE.md`).
- **Priority 3 — Dispatch Recovery.** Apply design-system primitives to chrome only · preserve all operations · keep Dispatch guardrail as the regression check.
- **Priority 4 — Safety Recovery.** Preserve Trench Safety as the reference module. Align other safety surfaces' chrome.

Standing rules still in force: **No deploy. No GitHub save. No merge.**
