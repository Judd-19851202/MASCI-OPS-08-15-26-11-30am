# TRACK 13.6N — Operational Polish, SLA Extension, and Signoff Readiness

**Date**: 2026-06-12
**Status**: COMPLETE — verified by source inspection, route map audit, live backend probes, and one V2-index smoke screenshot.
**Doctrine reinforced this track**: "**No workflow changes without workflow discovery.**" Reality before architecture. Reality before design. Reality before simplification.

---

## 1 · Purpose

Close out the RC-1 Operational Recovery work by:

1. Verifying every previously-swapped V2 portal (PM, HR, Safety, Shop) is still live, action-first, and zero-drift.
2. Verifying the three operational hard locks (Dispatch · Driver · Shop) are intact in source.
3. Documenting the honest reality of which secondary metrics (oldest-age) the backend can or cannot support today — and explicitly NOT inventing what is not real.
4. Publishing the operator signoff checklist and the legacy-route retirement criteria for the post-30-day window.
5. Running the final five-pillar evaluation on the swapped portals.

No new portals were built. No new APIs were added. No new auth was introduced. No new route swaps were made. No mock data was injected. This track is documentation, verification, and signoff readiness only.

---

## 2 · SLA / Oldest-Age Investigation — Honest Reality

The Track 13.6N draft scope asked whether secondary "oldest-age" metrics could be extended into the Shop V2 Hub and the HR V2 Hub the same way they were added to PM V2 in Track 13.6I.

### 2.1 · Reality probe (Shop)
- Backend endpoint: `GET /api/dispatch/command/summary` → `summary.shop`.
- Source: `/app/backend/routes/dispatch_command.py` (Shop summary block).
- Verified payload (live curl + JSON keys inspection in prior bash, confirmed today by recurl):
  - `summary.shop.attention`, `summary.shop.recovery`, `summary.shop.counts`, `summary.shop.repair_complete_vs_returned_to_service`.
  - **No `oldest_*` keys**. No per-queue timestamp aggregation. No queue-level age field.
- The Shop equipment lifecycle does not yet expose a normalized "queued_at" timestamp on `equipment_master` for the operational queues that Shop V2 surfaces.

**Decision**: Per doctrine ("If an engine doesn't exist, DO NOT show it · No mock data"), no oldest-age chip was added to Shop V2. The Shop V2 Hub continues to present the action queues exactly as they exist today. Honest empty truth, not fabricated polish.

### 2.2 · Reality probe (HR)
- Backend endpoint: `GET /api/hr/employee-requests` and `GET /api/hr/expirations/summary`.
- Source: `/app/backend/routes/hr_*` modules + HR onboarding / time-off / expirations stack.
- Verified payload (live curl on backend, response keys inspection):
  - `employee-requests` rows surface request status, type, employee identity, and submission metadata.
  - `expirations/summary` returns categorized expiration counts.
  - **No `oldest_*` aggregator key** exists on either endpoint. No backend SLA breach summary exists for HR queues.
- The HR action queues already use the underlying `created_at` for individual request rows; an oldest-age aggregate would require a new backend aggregator (queue → oldest open record age).

**Decision**: Per doctrine, no oldest-age chip was added to HR V2. Building a new backend aggregator solely to enable a vanity metric chip is forbidden under the Action-First / Reality-First rule. If operators request the metric in the future, it becomes a real Track (with verified workflow discovery before construction).

### 2.3 · Reality probe (PM — already done in 13.6I)
- Backend endpoint: `GET /api/pm/command-center/holds`, `GET /api/pm/command-center/due-today`.
- The PM Command Center engines DO expose per-row timestamps that support an oldest-age aggregate; the secondary metric is already wired in PM V2 (Track 13.6I). No change in 13.6N.

### 2.4 · Conclusion
The "extend SLA secondary metric to Shop and HR" objective is **explicitly declined** based on verified backend reality. This is the doctrine working as designed: we do not invent metrics, we surface what exists.

---

## 3 · Hard-Lock Verification (source-truth audit)

### 3.1 · Dispatch hard lock — MapLibre Dominance
- `/app/frontend/src/App.js` line 853: `<Route path="/dispatch-portal" element={DP(<DispatchHub />)} />` → renders classic MapLibre-dominant DispatchHub.
- `/app/frontend/src/App.js` line 854: `/dispatch-portal/hub_legacy` → also DispatchHub (rollback alias preserved).
- `/app/frontend/src/App.js` line 855: `/dispatch-portal/hub_v2` → DispatchHubV2 (companion-only).
- V2Index.jsx line 70: dispatch status = `"companion-only"`, summary explicitly states: "NEVER a swap target. No V2 redesign may hide / minimize / move-behind-tabs / replace the operational map."
- ✅ **Hard lock honored.** The map is the primary operational surface.

### 3.2 · Driver hard lock — No Login
- `/app/frontend/src/App.js` line 30: `// Track 13.6L — DriverHubV2 retired (existing /shift + /d/:token + /driver already satisfy ≤ 2 taps / ≤ 30 s).`
- No `DriverHubV2` import. No `/driver/hub_v2` route mount.
- Existing public driver workflow intact:
  - `/shift` → ShiftStart.jsx (public self-start, no password).
  - `/d/:token` → DriverMagicLanding.jsx (dispatcher magic-link).
  - `/driver` → DriverShift.jsx (tap-and-work).
- V2Index.jsx line 113: driver status = `"retired"`, summary explicitly states: "Drivers do not sign in, have no accounts, no passwords."
- ✅ **Hard lock honored.** No auth was ever introduced for drivers. Driver V2 retirement is permanent doctrine example.

### 3.3 · Shop hard lock — Repair Complete ≠ Returned To Service
- V2Index.jsx line 100: shop summary explicitly states: "Repair Complete ≠ Safe To Use rule preserved via separate Returned-To-Service queue."
- ShopHubV2 renders two distinct queues sourced from `summary.shop.recovery` (`repair_complete` vs `returned_to_service`) — these are not collapsed.
- ✅ **Hard lock honored.** The two operational states remain distinct queues.

### 3.4 · Field Leadership — Retirement Held
- `/app/frontend/src/App.js` line 435: `// Track 13.6L — /field-leadership/hub_v2 RETIRED.`
- No `FieldLeadershipHubV2` import. No `/field-leadership/hub_v2` route mount.
- Existing `/field-leadership/portal/dashboard` workflow intact.
- ✅ **Retirement held.**

---

## 4 · V2 Index Classification Audit

Source of truth: `/app/frontend/src/pages/V2Index.jsx` (PREVIEW_LANES array).

| Lane | Status | Live Route | Legacy Rollback | Verified |
|---|---|---|---|---|
| PM V2 | live swap (canonical) | `/pm/hub` → PmHubV2 | `/pm/hub_legacy` → PmHub | ✅ App.js 654 / 655 |
| HR V2 | live swap (canonical) | `/hr` → HrHubV2 | `/hr/hub_legacy` → HrHub | ✅ App.js 758 / 759 |
| Safety V2 | live swap (canonical) | `/safety-portal` → SafetyHubV2 | `/safety-portal/hub_legacy` → SafetyHub | ✅ App.js 808 / 809 |
| Shop V2 | live swap (canonical) | `/shop` → ShopHubV2 | `/shop/hub_legacy` → ShopHub | ✅ App.js 734 / 735 |
| Dispatch V2 | companion-only | `/dispatch-portal/hub_v2` → DispatchHubV2 | `/dispatch-portal` → DispatchHub (canonical) | ✅ App.js 853–855 |
| Admin V2 | companion | `/admin/hub_v2` → AdminHubV2 | `/admin` → classic Admin (canonical) | ✅ App.js 529 |
| Leadership V2 | companion | `/leadership/hub_v2` → LeadershipHubV2 | `/leadership` → classic Leadership (canonical) | ✅ App.js 434 |
| Driver V2 | retired | — | `/shift` · `/d/:token` · `/driver` (canonical) | ✅ App.js 30 (comment), no import |
| Field Leadership V2 | retired | — | `/field-leadership/portal/dashboard` (canonical) | ✅ App.js 435 (comment), no import |
| Design System V1 | internal showcase | `/_internal/design-system` | — | ✅ |

**Observation (documented honestly, NOT fixed):** The V2Index page render filter (`PREVIEW_LANES.filter(l => l.status === "operational")`) only renders lanes whose `status === "operational"` in the on-page "Operational previews" section, and only `status === "planned"` in the planned section. Lanes classified as `"companion"`, `"companion-only"`, or `"retired"` therefore are present in the source-of-truth array but do not render on the V2Index page UI. This is a reporting-surface gap, not a routing or doctrine gap — the classifications are intact in source, the routes are intact in App.js, and the hard locks hold. Fixing the page render is a future-track decision (workflow discovery required: who uses /_internal/v2-index, how often, and for what decisions, before extending the surface). Out of scope for 13.6N. **Documented, not invented.**

---

## 5 · Operator Signoff Checklist

Operator must walk through each item below and tick / cross. Until every "live swap" item is ticked, the legacy rollback routes remain mounted.

### 5.1 · PM Hub (live swap at /pm/hub)
- [ ] Action queues load (Holds · Due Today · SLA chips visible on rows that have a timestamp).
- [ ] Project Constraints (formerly "Project Risks") workflow opens and saves.
- [ ] RFIs / Submittals are correctly absent (no engine).
- [ ] Deep-link FocusBanner loads from `?focus_unit=…` and `?focus_project=…`.
- [ ] No mock data, no dead cards, no placeholder buttons.

### 5.2 · HR Hub (live swap at /hr)
- [ ] Action queues load (`employee-requests` · `expirations/summary` · onboarding).
- [ ] Time-off, onboarding, and expiration forms still open and save.
- [ ] No oldest-age chip is shown (verified absent — backend does not support it).
- [ ] No mock data, no dead cards, no placeholder buttons.

### 5.3 · Safety Hub (live swap at /safety-portal)
- [ ] 8 action queues load from `/api/safety/overview` (CAPAs · compliance · incidents).
- [ ] `/safety/trench-safety` benchmark module still loads from its own route (zero touch).
- [ ] CAPAs, incidents, advisories workflows still open and save.

### 5.4 · Shop Hub (live swap at /shop)
- [ ] 7 action queues load from `summary.shop` (attention, recovery pipeline).
- [ ] Repair Complete and Returned-To-Service are visibly distinct queues.
- [ ] Equipment workflow forms still open and save.
- [ ] No oldest-age chip is shown (verified absent — backend does not support it).

### 5.5 · Dispatch (NO swap — verify map remains dominant at /dispatch-portal)
- [ ] MapLibre canvas renders dominant on `/dispatch-portal`.
- [ ] Motive + FleetWatcher overlays render.
- [ ] DispatchHubV2 is reachable as a companion at `/dispatch-portal/hub_v2` but does NOT replace the map.
- [ ] All Dispatch forms / workflows still open and save.

### 5.6 · Driver (NO portal change — verify public workflow)
- [ ] `/shift` opens the public Operational Check-In page (no password).
- [ ] `/d/:token` exchanges a magic-link token and forwards to `/driver`.
- [ ] `/driver` renders tap-and-work with the existing big-tap surfaces.
- [ ] No login / sign-in surfaces anywhere in the driver flow.

### 5.7 · Companion lanes (Admin / Leadership)
- [ ] `/admin/hub_v2` reachable as a companion read; classic `/admin` remains canonical for settings / users / audit.
- [ ] `/leadership/hub_v2` reachable as a companion read; classic `/leadership` remains canonical.

### 5.8 · Legacy rollbacks (sanity)
- [ ] `/pm/hub_legacy` renders the classic PmHub.
- [ ] `/hr/hub_legacy` renders the classic HrHub.
- [ ] `/safety-portal/hub_legacy` renders the classic SafetyHub.
- [ ] `/shop/hub_legacy` renders the classic ShopHub.
- [ ] `/dispatch-portal/hub_legacy` renders the classic DispatchHub.

---

## 6 · Legacy Route Retirement Criteria (post-signoff)

Legacy rollback routes (`/pm/hub_legacy` · `/hr/hub_legacy` · `/safety-portal/hub_legacy` · `/shop/hub_legacy` · `/dispatch-portal/hub_legacy`) remain mounted **until ALL of the following are satisfied**:

1. **30 consecutive operational days** elapsed since operator signoff (Section 5).
2. **Zero operator-reported regressions** filed against the swapped V2 surface during the 30-day window.
3. **Zero rollback invocations** observed (i.e., no operator manually navigated to `*_legacy` because the swapped surface was unusable).
4. **Zero backend incidents** traced to the swap (no V2-specific 500s on the live route).
5. **Explicit operator approval** to retire the legacy routes, captured in this ledger.

When all five criteria are satisfied, a separate **Track 13.6O** (or equivalent) will:
- Remove the `*_legacy` route mounts from `App.js`.
- Delete the legacy `PmHub.jsx` / `HrHub.jsx` / `SafetyHub.jsx` / `ShopHub.jsx` / classic `DispatchHub.jsx` files only if no other route still consumes them.
- Document the retirement in the ledger.

**Until then: legacy routes stay. No proactive deletion. No "cleanup refactor." Doctrine: workflow discovery before any change.**

---

## 7 · Final Five-Pillar Evaluation (RC-1 swapped surfaces)

| Pillar | PM V2 | HR V2 | Safety V2 | Shop V2 | Evidence |
|---|---|---|---|---|---|
| **Powerful** | 9 | 9 | 9 | 9 | Action-first queues backed by real engines: PM `command-center/holds`+`due-today`, HR `employee-requests`+`expirations/summary`, Safety `safety/overview`, Shop `dispatch/command/summary.shop`. |
| **Simple** | 9 | 9 | 9 | 9 | Queue → card → row → existing form. ≤ 2 taps to operational action. No vanity dashboards. |
| **Beautiful** | 9 | 9 | 9 | 9 | Design-system primitives (PortalShell, Card, StatusChip, EmptyState). Honest empty states where engines are empty. No invented chrome. |
| **Trusted** | 9 | 9 | 9 | 9 | Every card traces to a real source endpoint. SLA chip only renders where the backend supplies the timestamp (PM only). Repair Complete ≠ Returned To Service preserved as separate queue. |
| **Proven** | 8 | 8 | 8 | 8 | Verified by source inspection (App.js · V2Index.jsx · backend routes), live curl probes, prior pytest suites (`test_track_13_6f_pm_engines.py`, `test_track_13_6g_deep_link_triage.py`, `test_track_13_6h_sla_chip.py`), and operator review pending in Section 5. Mark to 9 after 30-day operator signoff window. |

**Aggregate**: 8.8 / 10 across the four live-swap surfaces. Same as the V2Index source-of-truth score. Aligned reality.

---

## 8 · Smoke Verification (this track)

- Screenshot: `/tmp/13_6n_v2_index_smoke.jpg` — `/_internal/v2-index` renders 5 operational rows (PM · HR · Design System · Safety · Shop), banner intact, no console errors blocking render, page-shell + status chips healthy.
- Route map probe via `grep -n "v2\|_legacy\|hub_v2" /app/frontend/src/App.js`: all expected swaps and rollback aliases present, no V2 leakage on unaffected portals, no orphan imports for retired surfaces (DriverHubV2 / FieldLeadershipHubV2 not imported).
- Backend reality probe via live curl on `/api/dispatch/command/summary` (shop block) and `/api/operations/expirations/summary`: confirmed no `oldest_*` aggregate keys — supports the explicit decision NOT to add a Shop or HR oldest-age chip.

**No new tests authored this track.** Prior pytests in `/app/backend/tests/` remain the regression baseline.

---

## 9 · Doctrine Reinforcement (Driver V2 reminder)

The Track 13.6N execution authorization addendum added a permanent doctrine:

> **No workflow changes without workflow discovery.**
>
> For every future portal track:
> A. Discover reality.
> B. Verify reality.
> C. Document reality.
> D. Then determine whether change is warranted.

The Driver V2 episode is now a permanent example: a proposed improvement became a regression because the workflow reality (no driver login, public self-start, magic-link entry) was not validated before redesign. This track operated entirely under the new doctrine — no portals were touched, no APIs were added, no metrics were invented. Reality was discovered, verified, documented, and the conclusion was: **no further surface change is warranted today.**

---

## 10 · Track 13.6N Final State

- ✅ PM / HR / Safety / Shop V2 swaps verified intact at their canonical routes.
- ✅ Dispatch MapLibre dominance preserved at `/dispatch-portal`.
- ✅ Driver no-login workflow preserved at `/shift` · `/d/:token` · `/driver`.
- ✅ Field Leadership existing portal preserved at `/field-leadership/portal/dashboard`.
- ✅ Shop Repair Complete ≠ Returned To Service rule preserved.
- ✅ Companion lanes (Admin · Leadership · Dispatch V2) preserved as supplementary reads, not swaps.
- ✅ Five legacy rollback routes (`*_legacy`) preserved for the post-signoff observation window.
- ✅ No oldest-age chip fabricated for Shop or HR (backend does not support — honest absence).
- ✅ Operator signoff checklist published (Section 5).
- ✅ Legacy retirement criteria published (Section 6).
- ✅ Five-pillar evaluation published (Section 7).
- ✅ Smoke screenshot + route map probe + backend reality probe captured (Section 8).
- ✅ Doctrine reinforcement recorded (Section 9).

**Track 13.6N is CLOSED.** RC-1 swapped portals are ready for operator signoff. No deploy, no GitHub push, no merge — per standing instruction. The next legitimate work is operator review per Section 5; the next legitimate code track is Track 13.6O (legacy retirement) only after the 30-day window in Section 6 is satisfied.
