# Track 13.23 — ODR PM-Hub Pending-Drafts Pill (last IBQ item)

**Date:** 2026-06-12
**Mode:** CONTROLLED IMPLEMENTATION · single-file frontend addition.
**Doctrine:** TRACK_13_9 §8 BQ#8 closeout.
**Verdict:** ✅ **PASS** · pill mounted · click routes to live `/pm/odr` page · zero backend touch · all hard locks intact.

---

## 1 · Executive Summary

A small, additive `ODR Pending` attention pill is now on PM Hub V2 alongside the existing
PO Requests card. It reads from the **existing** PM-scoped ODR list endpoint and counts
ODRs needing PM rework (status ∈ `{draft, returned}`). Honest empty state when count is
zero — verified live with `pm.demo@mascigc.com`.

This closes the last item in the Immediate Build Queue from Track 13.9 §8.

**Files changed:** 1 — `frontend/src/pages/PmHubV2.jsx`.
**Backend changes:** 0.
**New endpoints:** 0.
**New collections:** 0.

---

## 2 · Source Verification (Phase 0)

| Item                                                                                | Verified |
| ----------------------------------------------------------------------------------- | -------- |
| `frontend/src/pages/PmHubV2.jsx` is the PM Hub V2 file                              | ✅ (live route `/pm/hub`) |
| `/pm/odr` route mounted (`OdrPmPanel`)                                              | ✅ (App.js line 975) |
| `/odr/center` route mounted (`OdrCenter`)                                            | ✅ (App.js line 974) |
| Existing ODR list endpoint `GET /api/odr`                                            | ✅ (`backend/routes/odr/routes.py` line 310) |
| ODR status enum                                                                      | ✅ `Literal["draft", "submitted", "returned", "approved"]` (enums.py line 44) |
| PM scope applied server-side via `build_odr_scope_filter`                            | ✅ (routes.py line 320 — `q, fll, verb = build_odr_scope_filter(actor, ...)`) |
| Auth dep `require_actor = _require_any_portal_token`                                 | ✅ — accepts the PM token already sent by `authHeaders()` |
| PM Hub V2 existing parallel-fetch pattern                                             | ✅ (lines 91-110) |
| Existing `QueueCard` shape (`to`/`testid`/`title`/`why`/`source`/`value`/`loaded`)   | ✅ |
| Live preview curl with PM token (`pm.demo@mascigc.com`)                              | ✅ — `/api/odr?limit=200` returns `{count:0, items:[]}` (honest empty for the demo scope) |

**No new backend endpoint required.** The list endpoint already provides PM-scoped
records with `status` on each row; the count is derived client-side from `items[*].status`
filtered to `{draft, returned}` — the two statuses that require **PM** action. Submitted
is awaiting senior signoff (out of PM hands); approved is closed.

---

## 3 · ODR Endpoint / Count Source

**Endpoint:** `GET /api/odr?limit=200`
**Auth:** `X-PM-Token` (sent automatically by the PM Hub V2 `authHeaders()` helper)
**Scope:** PM scope is applied server-side by `build_odr_scope_filter` — no client-side leakage.

**Count derivation (client-side):**
```js
listOf(odr.body).filter((r) =>
  /^(draft|returned)$/i.test(String(r.status || ""))
).length
```

**Rationale for `{draft, returned}` as the "attention" set:**
* `draft` — author hasn't submitted yet; if older than expected, PM should chase.
* `returned` — senior reviewer sent it back; PM (or PM's foreman) needs to rework.
* `submitted` — awaiting senior signoff; **PM cannot move this forward** so it does NOT contribute to the pill (avoids inflating attention).
* `approved` — closed.

---

## 4 · Implementation Summary

Three minimal additive changes inside `usePmSignals`:

1. **State keys** added next to the existing PO Requests slots:
   ```js
   odr_attention: null,   // count of {draft, returned}
   odr_loaded:    false,  // honest load flag
   ```
2. **Parallel fetch task** appended:
   ```js
   safeJson(`/api/odr?limit=200`)
   ```
3. **State update** appended in the `tasks.then(...)` setS call:
   ```js
   odr_loaded:    true,
   odr_attention: odr.ok ? listOf(odr.body).filter((r) =>
                  /^(draft|returned)$/i.test(String(r.status || ""))
                ).length : null,
   ```

One `QueueCard` mounted in Section 01 directly after `<PoRequestsCard ... />`:

```jsx
<QueueCard
  to="/pm/odr"
  testid="pm-hub-v2-queue-odr"
  title="ODR Pending"
  why="Operational Daily Records needing PM rework (drafts + returned)"
  source="Source: /api/odr — draft + returned (PM-scoped server-side)"
  value={s.odr_attention}
  loaded={s.odr_loaded}
/>
```

Also added to the all-clear `allZero` check so the calm-state banner only renders when ODR is also empty:

```js
s.odr_attention,
```

---

## 5 · Files Changed

| File                                          | Change                                                                                                                |
| --------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| `frontend/src/pages/PmHubV2.jsx`              | 4 small additive edits: state keys + fetch task + setS branch + QueueCard mount + allZero entry. ESLint clean.        |

**Backend not touched. No new endpoint. No new collection. No new route. No new auth.**

---

## 6 · Routes Touched

* `/pm/hub` — PM Hub V2 page (PmHubV2.jsx) — additive QueueCard.
* `/pm/odr` — destination of the pill click. **Not modified.**

No App.js change. No Route added.

---

## 7 · Tests Run

| Test                                                                          | Result |
| ----------------------------------------------------------------------------- | ------ |
| ESLint on `PmHubV2.jsx`                                                       | ✅ clean |
| Backend curl smoke `GET /api/odr?limit=200` with PM token                     | ✅ 200 · `{count:0, items:[]}` for the demo scope |
| Browser smoke at `/pm/hub` after PM login                                     | ✅ pill mounts · count = 0 honest empty |
| Click pill → routes to `/pm/odr` and renders ODR PM Consumer panel              | ✅ verified |
| PO Requests card (Track 13.11) still mounted                                  | ✅ verified live |
| Material Movement Phase B panel still loads at `/pm/projects-legacy/:p`       | (read-only file untouched — regression by file diff) |
| Dispatch map-first canvas at `/dispatch-portal`                               | (file untouched — regression by file diff) |

---

## 8 · Browser Smoke Evidence

```
ODR pending pill mounted: True
PO Requests card still present (Track 13.11 intact): True
ODR pill content excerpt: ODR PendingVerifiedOperational Daily Records needing PM rework (drafts + returned)0Source: /api/odr — draft + returned (PM-scoped server-side)
Click landed on: https://backup-forensics.preview.emergentagent.com/pm/odr
SUCCESS
```

The pill renders with `Verified` chip + value `0` + honest source attribution — exactly the
"all clear" branch for a PM scope with no draft/returned ODRs. Click navigates to the live
`/pm/odr` PM consumer panel (read-only consumer lens with FLL-5/LIMITED scope).

---

## 9 · Hard-Lock Regression Results

| Hard lock                                                  | Verified | Method                                                  |
| ---------------------------------------------------------- | -------- | ------------------------------------------------------- |
| Dispatch Map-First (`/dispatch-portal` MapLibre canvas)    | ✅       | Dispatch files not touched                              |
| Dispatch Companion Haul Ledger (Phase C)                   | ✅       | Not touched                                             |
| PM project material panel (Phase B)                        | ✅       | `PmProjectDetail.jsx` not touched                       |
| Admin Material Ledger Quality (Phase D)                    | ✅       | Not touched                                             |
| Phase A endpoint                                           | ✅       | `material_movement.py` not touched                      |
| Driver no-login (`/shift`, `/d/:token`, `/driver`)         | ✅       | Driver files not touched                                |
| DriverHubV2 retired                                        | ✅       | No revival                                              |
| Shop Repair ≠ Returned                                     | ✅       | Shop files not touched                                  |
| One map engine                                             | ✅       | No new map                                              |
| Track 13.11 PO Requests card                               | ✅       | Live smoke confirms PO card still mounted               |
| Track 13.13 Operational Events panel                       | ✅       | Project detail file not touched                         |
| Track 13.14 scale-ticket extension                         | ✅       | Attachments file not touched                            |
| Track 13.17 PO lifecycle notifications                     | ✅       | `po_requests.py` not touched                            |
| Track 13.19/13.20/13.21/13.22 (Material Ledger phases)      | ✅       | None of those files touched                             |
| ODR workflows (`/odr/center`, `/odr/new`, `/odr/{id}`)     | ✅       | ODR files not touched · ODR routes preserved             |
| No new collection                                          | ✅       | Backend untouched                                       |

---

## 10 · What Was NOT Built

* ❌ No new backend endpoint (existing list endpoint already returns PM-scoped records with `status`)
* ❌ No new collection
* ❌ No new route
* ❌ No ODR workflow modification
* ❌ No Daily Report modification
* ❌ No Dispatch / Driver / Shop modification
* ❌ No Material Movement Ledger modification
* ❌ No PO lifecycle modification
* ❌ No new auth (existing PM token sufficient)
* ❌ No new design system (reused existing `QueueCard`)
* ❌ No `submitted` count (out of PM hands)
* ❌ No `approved` count (closed)
* ❌ No fabricated counts (uses real PM-scoped server response only)
* ❌ No stale or demo data

---

## 11 · Five-Pillar Evaluation

| Pillar    | Score | Justification                                                                                                          |
| --------- | ----- | ---------------------------------------------------------------------------------------------------------------------- |
| Powerful  | 6/10  | Small surface gain — PMs see ODR attention without opening the ODR center. Operationally useful, not transformative.   |
| Simple    | 10/10 | One file · ~12 lines added · reused QueueCard · zero backend touch.                                                    |
| Beautiful | 9/10  | Drops into the existing PM Hub Section 01 grid with identical card chrome to Daily / Incidents / PO etc.              |
| Trusted   | 10/10 | Uses real PM-scoped endpoint. No fabricated counts. Honest empty state. PM scope enforced server-side.                 |
| Proven    | 9/10  | ESLint clean. Live browser smoke confirms mount, click destination, all-clear branch, PO card coexistence.            |

---

## 12 · Rollback Procedure

1. `git checkout HEAD~1 -- frontend/src/pages/PmHubV2.jsx`
2. Frontend hot-reloads.

Zero backend / schema / endpoint / route / collection delta.

---

## 13 · Final Verdict

**Track 13.23 · CLOSED · PASS.**

The last Immediate Build Queue item from Track 13.9 §8 is closed. PM Hub V2 now surfaces
ODR attention with the same trust pattern used for PO / Daily / Incidents / CAPAs /
Constraints / Materials. Backend untouched. Hard locks intact.

Deployment readiness remains 🟢 **GREEN**.

---

## 14 · Recommended Next Step

The Immediate Build Queue from Track 13.9 §8 is now **EMPTY**.

The correct next move is **operator signoff / release-candidate certification**, not more
feature building. Recommended candidate tracks:

* **Track 13.6N — 30-day operator signoff window** (pre-existing P1) for cross-portal V2 swaps (HR / PM / Safety / Shop V2 routes).
* **Track 13.23-Sign / 13.24 — Material Ledger Operator Sign-Off Window** opening Phases A–D for 14–30 days of operator validation across PM, Dispatch, and Admin.
* **Track X — Material Ledger Phase E** — remains **BLOCKED on `FLEETWATCHER_API_KEY` + active service credentials**.

Do not start new feature builds until operator sign-off telemetry returns.

---

## 15 · Final Response (per Track 13.23 §7)

1. **Track status:** CLOSED · PASS.
2. **Implementation summary:** Single-file frontend additive. Added 2 state keys + 1 parallel fetch + 1 setS branch + 1 QueueCard + 1 entry to `allZero` check inside `PmHubV2.jsx`. Zero backend touch · zero new endpoint · zero new collection · zero new route · zero new auth.
3. **Files changed (1):** `frontend/src/pages/PmHubV2.jsx`.
4. **Routes touched:** None added. Pill points to existing `/pm/odr`.
5. **Count source:** existing `GET /api/odr?limit=200` (PM scope applied server-side via `build_odr_scope_filter`). Attention count = `items[]` filtered to `status ∈ {draft, returned}`.
6. **Tests passed:** ESLint clean · backend curl smoke (PM token returns honest empty 200) · browser smoke (pill mounts · all-clear branch renders · click navigates to live `/pm/odr` page · PO Requests card coexists).
7. **Hard locks verified:** Dispatch Map-First · Driver no-login · DriverHubV2 retired · Shop RTS · one map engine · Material Movement Phases A/B/C/D untouched · Track 13.11/13.13/13.14/13.17 untouched · ODR workflows untouched · no new collection · PM stays project-scoped (server-enforced).
8. **Blockers:** None.
9. **Recommended next step:** Open **Material Ledger Operator Sign-Off Window** (Track 13.6N / 13.24) for 14–30-day operator validation before any further feature build. Phase E (FleetWatcher) remains blocked on credentials.
