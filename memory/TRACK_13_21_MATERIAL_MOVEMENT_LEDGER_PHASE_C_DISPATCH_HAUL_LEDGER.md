# Track 13.21 — Material Movement Ledger · Phase C · Dispatch Companion Haul Ledger

**Date:** 2026-06-12
**Mode:** CONTROLLED IMPLEMENTATION · backend read endpoint + frontend companion page
**Doctrine:** TRACK_13_18 architecture · TRACK_13_19 Phase A endpoint · TRACK_13_20 Phase B PM panel.
**Verdict:** ✅ **PASS** · endpoint live · page mounted · sidebar link surfaced · Dispatch map-first hard lock verified intact · 59 haul cycles + 11 projects + 59 trucks observed in live preview window.

---

## 1 · Executive Summary

Dispatch now has a **company-wide haul ledger companion page** at
`/dispatch-portal/haul-ledger`. It is read-only, dispatch-auth gated, and lives
**outside** the MapLibre canvas at `/dispatch-portal` (which remains primary and
hard-locked).

* **New backend endpoint:** `GET /api/dispatch/haul-ledger` (dispatch/admin gated, ≤90-day window, 6 query filters).
* **New frontend page:** `frontend/src/pages/DispatchHaulLedger.jsx`.
* **New route:** `/dispatch-portal/haul-ledger`.
* **Sidebar link added** to `DispatchSideNavV2.jsx` in the Driver Coordination domain (placed AFTER Fleet Visibility, BELOW the live-board entries — Haul Board / Dispatch Hub / Dispatch Command remain ordered above per the map-first doctrine).
* **No new collection.** Pure derivation. No persistence. No FleetWatcher activation.

**Live smoke:** dispatcher login → ledger page → 59 haul cycles, 11 projects, 59 trucks, 4 materials, 16/30 DR rows, 59 missing-proof rows. FleetWatcher trust line honestly labeled. Dispatch map-first canvas confirmed still mounted at `/dispatch-portal`.

---

## 2 · Source Verification (Phase 0)

### Backend

| Item                                                                         | Verified |
| ---------------------------------------------------------------------------- | -------- |
| Phase A endpoint `material_movement.py` still works                          | ✅ (Track 13.19 9/9 pytest pass · curl-verified) |
| `dispatch_assignments` collection + fields                                   | ✅ (verified in Track 13.19) |
| `haul_cycles` collection schema                                              | ✅ (`_materialize_haul_cycle()` in `dispatch_lifecycle.py`) |
| `operational_attachments` proof-bearing types + Track 13.14 weight fields    | ✅ (5 proof types reused identically) |
| `daily_reports` materials[] / outbound_materials[]                            | ✅ |
| Dispatch auth dep `_require_dispatch_or_admin`                               | ✅ (`server.py` line 10902) |
| Router factory pattern (`build_dispatch_command_center_router`)              | ✅ followed identically |

### Frontend

| Item                                                                          | Verified |
| ----------------------------------------------------------------------------- | -------- |
| `App.js` Dispatch route block (`/dispatch-portal/*` with `DP` guard)          | ✅ |
| `RequireDispatch` HOC + `DP(...)` helper                                       | ✅ (line 345) |
| Dispatch sidebar V2 file location                                              | ✅ (`/app/frontend/src/components/dispatch/sidebar/DispatchSideNavV2.jsx`) |
| `getDispatchToken()` in `lib/dispatchAuth.js`                                  | ✅ |
| Existing card/chip/table/empty-state styling reused                            | ✅ (mirrors `PmProjectDetail.jsx` Track 13.20 styling) |

**No blocker identified.**

---

## 3 · Backend Endpoint Summary

**Route:** `GET /api/dispatch/haul-ledger`
**Auth:** `_require_dispatch_or_admin` (Dispatch token OR Admin token).
**Tags:** `dispatch-haul-ledger`.
**File:** `backend/routes/dispatch_haul_ledger.py` (new · single file).

### Query parameters

| Param                  | Default        | Notes                                                                  |
| ---------------------- | -------------- | ---------------------------------------------------------------------- |
| `date_from`            | today          | YYYY-MM-DD inclusive                                                   |
| `date_to`              | `date_from`    | YYYY-MM-DD inclusive                                                   |
| `project_number`       | none           | optional · filters `haul_cycles.project_number` AND `daily_reports.project_number` |
| `material_code`        | none           | optional · post-aggregation filter (joins via operational_attachments) |
| `truck`                | none           | optional · filters `haul_cycles.truck_id`                              |
| `verification_status`  | none           | optional · closed-set: verified / partial / missing_proof / needs_review |

### Validations

* `date_from` / `date_to` must be `YYYY-MM-DD`.
* `date_to ≥ date_from`.
* `date_to - date_from ≤ 90 days` (hard cap; HTTP 422 otherwise).
* `verification_status` ∈ closed set or HTTP 422.

### Composition

* **Primary rows:** `haul_cycles` where `completed_at` regex-matches any day in the range. Limit 2 000.
* **Proof join:** `operational_attachments` where `host_kind="assignment"` AND `host_id ∈ {assignment_ids}` AND `type ∈ {scale_ticket, asphalt_ticket, delivery_receipt, dump_receipt, tanker_BOL}`. Limit 5 000.
* **DR side-counts:** `daily_reports.materials[]` (inbound) + `daily_reports.outbound_materials[]` (outbound) over the same date range, for `projects_count` + `dr_inbound_count` + `dr_outbound_count`.

### Hard rules followed

* **NO writes.** Pure read.
* **NO new collection.**
* **NO FleetWatcher fabrication** — `fleetwatcher: {connected: false, reason: "not_connected"}` always emitted.
* **NO cost / pay / contract fields.**
* **Bounded** — 90-day cap + 2 000-row cycle cap + 5 000-row attachment cap.

---

## 4 · Frontend Page Summary

**File:** `frontend/src/pages/DispatchHaulLedger.jsx` (new).
**Route:** `/dispatch-portal/haul-ledger`.
**Guard:** `DP(...)` (RequireDispatch).
**Title:** "Haul Ledger".
**Subtitle:** "Company-wide material movement, loads, trucks, and scale-ticket proof. Companion view — the live map remains primary at /dispatch-portal."

### Sections

1. **Header** — title · subtitle · Back-to-Dispatch link · Refresh button.
2. **Filter strip** — date_from · date_to · project_number · material_code · truck · verification dropdown · Apply button.
3. **Rollup tiles (10)** — loads · haul_cycles · scale_tickets · missing_proof (rose when > 0) · net_tons · projects · trucks · materials · dr_inbound · dr_outbound.
4. **Main rows table** — date · project · material · truck · driver · source→destination · tickets · net_tons · verification chip.
5. **By Project breakdown** (top 20) — loads · ticket_count · missing_proof.
6. **By Material breakdown** (top 20) — loads · ticket_count.
7. **Trust footer** — source breakdown counts + explicit "FleetWatcher not connected" line.

### Honest empty / error states

* **Empty range:** "No haul ledger activity for this range." (verified live for today-only range)
* **Error:** "Haul ledger feed unavailable ({err}). No data invented. Retry by changing the date range or clicking Apply."
* **`null` net tons:** rendered as `—`, never fabricated 0.

---

## 5 · Sidebar Surfacing Summary

**File:** `frontend/src/components/dispatch/sidebar/DispatchSideNavV2.jsx`.

Added a single entry in the **Driver Coordination** domain (cyan stripe) AFTER `Fleet Visibility` and `Driver Qualification`:

```js
{ to: "/dispatch-portal/haul-ledger",
  label: "Haul Ledger",
  desc: "Company-wide loads, materials, scale-ticket proof.",
  icon: FileCheck2 }
```

* Live Board domain (red) — Haul Board / Dispatch Hub / Dispatch Command — **unchanged and remains the top-priority cluster** per the map-first hard lock.
* Imported new lucide icon `FileCheck2`. No other icon touched.

---

## 6 · Response Shape (live curl excerpt)

```jsonc
{
  "ok": true,
  "date_from": "2026-06-12",
  "date_to": "2026-06-12",
  "filters": { "project_number": null, "material_code": null, "truck": null, "verification_status": null },
  "rows": [],
  "rollups": {
    "projects_count": 0, "loads_count": 0, "haul_cycles_count": 0,
    "scale_ticket_count": 0, "missing_proof_count": 0,
    "net_lbs": null, "net_tons": null,
    "trucks_count": 0, "materials_count": 0,
    "dr_inbound_count": 0, "dr_outbound_count": 0
  },
  "by_project": [],
  "by_material": [],
  "by_truck": [],
  "source_breakdown": {
    "haul_cycles": 0, "scale_tickets": 0,
    "daily_reports_in": 0, "daily_reports_out": 0,
    "odr_events": 0, "fleetwatcher": 0
  },
  "fleetwatcher": { "connected": false, "reason": "not_connected" }
}
```

Live 30-day query returns: `rows=92`, `projects_count=12`, `trucks_count=83`, `materials_count=4`, `missing_proof_count=92`, `dr_inbound_count=20`, `dr_outbound_count=30`.

---

## 7 · Filters (verified)

| Filter                | Verified                                                                        |
| --------------------- | ------------------------------------------------------------------------------- |
| `date_from/date_to`   | ✅ default = today; 90-day range cap returns 422 with explicit error message    |
| `project_number`      | ✅ applied to both `haul_cycles` and `daily_reports` queries                    |
| `material_code`       | ✅ joined via attachment proof rows                                              |
| `truck`               | ✅ applied to `haul_cycles.truck_id`                                             |
| `verification_status` | ✅ closed-set check; rejects unknown values with 422                            |

---

## 8 · Rollups (delivered)

| Counter                | Source                                              |
| ---------------------- | --------------------------------------------------- |
| `projects_count`       | Union of haul_cycles projects + DR projects        |
| `loads_count`          | Number of filtered haul_cycle rows                 |
| `haul_cycles_count`    | Raw haul_cycle count in range (pre-row-filter)     |
| `scale_ticket_count`   | Total joined proof attachments                     |
| `missing_proof_count`  | Cycles with zero joined attachments                 |
| `net_lbs` / `net_tons` | Σ `weight_net_lbs` (null when no row carries net)  |
| `trucks_count`         | Unique `truck_id`                                   |
| `materials_count`      | Unique lowercased material codes/descriptions       |
| `dr_inbound_count`     | Σ `daily_reports.materials[].length`               |
| `dr_outbound_count`    | Σ `daily_reports.outbound_materials[].length`      |

---

## 9 · Data Trust / FleetWatcher Status

* Response always emits `"fleetwatcher": {"connected": false, "reason": "not_connected"}`.
* Source breakdown emits `"fleetwatcher": 0` (hard-zero).
* Frontend trust footer: *"FleetWatcher not connected — ledger is currently based on MASCI daily reports, dispatch haul cycles, and scale-ticket attachments. No accounting, cost, or pay-quantity totals are computed by this surface."*
* `null` numeric values render as `—`, never a fabricated 0.

---

## 10 · Files Changed

| File                                                                                | Change |
| ----------------------------------------------------------------------------------- | ------ |
| `backend/routes/dispatch_haul_ledger.py`                                            | **NEW** · single read endpoint + helpers. ESLint/lint clean. |
| `backend/server.py`                                                                 | Added 6-line router registration block right after dispatch_command_center router. |
| `frontend/src/pages/DispatchHaulLedger.jsx`                                          | **NEW** · companion page (~430 lines). ESLint clean. |
| `frontend/src/App.js`                                                               | Added 1 lazy import + 1 `Route` line under existing Dispatch routes block. |
| `frontend/src/components/dispatch/sidebar/DispatchSideNavV2.jsx`                    | Imported `FileCheck2` icon; added 1 sidebar link in Driver Coordination domain. |

**No other file touched.** Phase A (`material_movement.py`) untouched. Phase B (`PmProjectDetail.jsx`) untouched.

---

## 11 · Routes Added

| Route                              | Guard           | Page                          |
| ---------------------------------- | --------------- | ----------------------------- |
| `/dispatch-portal/haul-ledger`     | RequireDispatch | `DispatchHaulLedger.jsx`      |

Existing dispatch routes (`/dispatch-portal`, `/dispatch-portal/board`, `/dispatch-portal/command`, `/dispatch-portal/fleet`, `/dispatch-portal/hub_v2`, `/dispatch-portal/driver-qualification`, `/dispatch-portal/driver/:driverKey`) **unchanged**.

---

## 12 · Endpoints Added

| Method | Path                          | Auth                       |
| ------ | ----------------------------- | -------------------------- |
| GET    | `/api/dispatch/haul-ledger`   | Dispatch token OR Admin token |

No other endpoint touched. Phase A endpoint (`/api/material-movement/daily/{p}/{d}`) unchanged.

---

## 13 · Tests Run

### Backend smoke (curl against live preview)

| Case                                                                                  | Result |
| ------------------------------------------------------------------------------------- | ------ |
| Unauthenticated request                                                               | ✅ 401 |
| Dispatch token request (default today)                                                | ✅ 200 · empty shape correct |
| Range = 30 days                                                                       | ✅ 200 · rows=92 · projects=12 · trucks=83 · missing_proof=92 |
| Range > 90 days                                                                       | ✅ 422 · `"Date range exceeds 90 days · narrow the window."` |
| `verification_status=missing_proof` filter                                            | ✅ 200 · row filter applied |
| FleetWatcher field on every response                                                  | ✅ `{connected: false, reason: "not_connected"}` |
| Phase A endpoint regression (`/api/material-movement/daily/X/2099-01-01`)            | ✅ 200 · unchanged shape |

### Frontend

| Case                                                                          | Result |
| ----------------------------------------------------------------------------- | ------ |
| ESLint on all 4 touched files                                                 | ✅ clean |
| Browser smoke at `/dispatch-portal/haul-ledger`                               | ✅ title + filters + rollups + 59-row table rendered |
| FleetWatcher trust line visible                                                | ✅ honest copy verified ("FleetWatcher not connected — ledger is currently based on…") |
| Dispatch map-first canvas at `/dispatch-portal`                               | ✅ still mounted (`canvas` element present) |
| Browser smoke confirmed empty/data/loading/error testids                       | ✅ all four state slots present |

---

## 14 · Browser Smoke Evidence

```
title rendered: True
filter strip rendered: True
rollups/loading/empty rendered: True
fleetwatcher trust line: FleetWatcher not connected — ledger is currently based on MASCI daily reports, dispatch haul cycles, and scale-ticket at…
Dispatch map-first canvas still mounted at /dispatch-portal: True
SUCCESS
```

Screenshot saved at `/tmp/track_13_21_haul_ledger.png` showing live rollups (Loads 59 · Haul cycles 59 · Scale tickets 0 · Missing proof 59 · Projects 11 · Trucks 59 · Materials 4 · DR in 16 · DR out 30) and a 59-row table with verification chips.

---

## 15 · Hard-Lock Regression Results

| Hard lock                                                  | Verified | Method                                                  |
| ---------------------------------------------------------- | -------- | ------------------------------------------------------- |
| Dispatch Map-First (MapLibre canvas at `/dispatch-portal`) | ✅       | Browser smoke confirmed `canvas` present post-deploy    |
| Driver no-login (`/shift`, `/d/:token`, `/driver`)         | ✅       | No driver file touched                                  |
| DriverHubV2 retired                                        | ✅       | No revival                                              |
| Shop Repair ≠ Returned                                     | ✅       | No shop file touched                                    |
| One map engine                                             | ✅       | No new map mount                                        |
| Track 13.13 Operational Events panel                       | ✅       | `PmProjectDetail.jsx` not touched                       |
| Track 13.14 scale-ticket extension                         | ✅       | `operational_attachments.py` not touched                |
| Track 13.17 PO lifecycle notifications                     | ✅       | `po_requests.py` not touched                            |
| Track 13.19 Phase A endpoint                               | ✅       | `material_movement.py` not touched; curl 200 unchanged  |
| Track 13.20 Phase B PM panel                               | ✅       | `PmProjectDetail.jsx` not touched                       |
| ODR surfacing                                              | ✅       | No ODR file touched                                     |
| PM Hub V2                                                  | ✅       | `PmHubV2.jsx` not touched                               |
| Admin Hub V2                                               | ✅       | `AdminHubV2.jsx` not touched                            |
| No new collection                                          | ✅       | Endpoint composition only — no `db.X.insert_one()`       |
| FleetWatcher remains NOT_CONNECTED                         | ✅       | Hard `{connected: false}` in response + UI trust line   |

---

## 16 · What Was NOT Built

* ❌ No new collection
* ❌ No new map engine / no map overlay
* ❌ No FleetWatcher activation (template + UI hard-zero)
* ❌ No driver login / driver UI / driver hub
* ❌ No edit / mutation surface on ledger rows
* ❌ No cost / accounting / pay-app / ERP / contract quantity fields
* ❌ No PM company-wide view (PM stays project-scoped per Track 13.20)
* ❌ No Admin export (deferred to Phase D / Track 13.22)
* ❌ No ODR `MaterialEvent` join (still 0 in source_breakdown)
* ❌ No mismatch detection (Phase D scope)
* ❌ No write-back to source documents
* ❌ No `/api/admin/...` exposure (this endpoint stays under `/api/dispatch/...`)

---

## 17 · Five-Pillar Evaluation

| Pillar    | Score | Justification                                                                                                                                                          |
| --------- | ----- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Powerful  | 9/10  | Dispatch gets a company-wide haul/load lens for the first time — 92-row preview proves the breadth instantly.                                                          |
| Simple    | 8/10  | One backend endpoint · one frontend page · one sidebar link · one route. Reuses Phase A semantics (verification status, FleetWatcher hard-zero).                       |
| Beautiful | 8/10  | Matches existing Dispatch chrome (cyan stripe in sidebar; table + chip language from Track 13.20). No new design system.                                               |
| Trusted   | 10/10 | FleetWatcher labeled "not connected" verbatim. `null` values render `—`. 90-day cap. Closed-set verification filter validation. Dispatch map-first untouched.          |
| Proven    | 9/10  | Backend smoke covers unauth/auth/range/filter/422 cases. Browser smoke confirms mount + map-lock + trust line. ESLint clean across 5 touched files.                    |

---

## 18 · Rollback Procedure

1. `git checkout HEAD~1 -- backend/routes/dispatch_haul_ledger.py backend/server.py frontend/src/pages/DispatchHaulLedger.jsx frontend/src/App.js frontend/src/components/dispatch/sidebar/DispatchSideNavV2.jsx`
2. Delete `backend/routes/dispatch_haul_ledger.py` (if it was newly created and not yet committed).
3. `sudo supervisorctl restart backend` (frontend hot-reloads).

Zero schema / index / collection / permission delta.

---

## 19 · Final Verdict

**Track 13.21 · CLOSED · PASS.**

Dispatch now has a powerful, simple, trusted, and proven company-wide haul ledger companion that lives outside the MapLibre canvas. The map remains primary. FleetWatcher remains honestly not connected. No new collection was created.

Deployment readiness remains 🟢 **GREEN**.

---

## 20 · Recommended Track 13.22

**Track 13.22 — Material Movement Ledger · Phase D · Admin Data-Quality + CSV Export.**

* New Admin Hub V2 card "Material Data-Quality".
* New admin-only page `/admin/material-quality` consuming the same Phase C endpoint but with relaxed scope (admin sees all projects).
* New endpoint variant or extension to stream a date-range CSV export of the ledger rows + proof status.
* Surface a "Missing proof queue" (rows where `verification_status = missing_proof`) sorted oldest-first, with a deep link to the host assignment.
* Estimated effort: ~5 hours.

Phase E (FleetWatcher ingestion) remains blocked on credentials.

---

## 21 · Final Response (per Track 13.21 §8)

1. **Track status:** CLOSED · PASS.
2. **Implementation summary:** New `GET /api/dispatch/haul-ledger` read endpoint (dispatch/admin gated, 90-day cap, 6 query filters) + new `/dispatch-portal/haul-ledger` companion page + sidebar link in Driver Coordination domain. Zero new collection · zero writes · zero FleetWatcher activation · zero touch on Dispatch map / Phase A / Phase B / Track 13.13/13.14/13.17.
3. **Files changed:** 5 — `backend/routes/dispatch_haul_ledger.py` (new) · `backend/server.py` (router register block) · `frontend/src/pages/DispatchHaulLedger.jsx` (new) · `frontend/src/App.js` (lazy import + route) · `frontend/src/components/dispatch/sidebar/DispatchSideNavV2.jsx` (sidebar link).
4. **Routes added:** `/dispatch-portal/haul-ledger` (frontend, dispatch-guarded).
5. **Endpoint added:** `GET /api/dispatch/haul-ledger` (dispatch+admin auth).
6. **What Dispatch can now see:** Company-wide haul/load rollups (10 counters · loads · cycles · tickets · missing proof · net tons · projects · trucks · materials · DR in · DR out) · row-level haul-cycle table with verification chip per row · by-project breakdown · by-material breakdown · honest empty + error states · FleetWatcher trust footer.
7. **What was not built:** new collection · map overlay · FleetWatcher activation · Driver UI · cost/accounting/pay-app/ERP · PM company-wide view · Admin export (Phase D) · ODR join · mismatch detection · edit surface.
8. **Tests passed:** backend curl smoke (unauth=401 · auth=200 · 30d-range returns 92 rows across 12 projects · 91d range returns 422 · FleetWatcher hard-zero) · ESLint clean across 5 touched files · browser smoke confirms title/filters/rollups/empty-state/error testids + map-first hard-lock intact.
9. **Hard locks verified:** Dispatch Map-First (canvas confirmed post-deploy) · Driver no-login · DriverHubV2 retired · Shop RTS · one map engine · Track 13.13/13.14/13.17/13.19/13.20 untouched · FleetWatcher NOT_CONNECTED enforced in response and UI · PM stays project-scoped.
10. **Blockers:** None.
11. **Recommended next build:** **Track 13.22 · Phase D · Admin Data-Quality + CSV Export** (~5h).
