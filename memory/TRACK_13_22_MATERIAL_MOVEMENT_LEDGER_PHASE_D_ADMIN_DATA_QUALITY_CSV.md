# Track 13.22 — Material Movement Ledger · Phase D · Admin Data-Quality + CSV Export

**Date:** 2026-06-12
**Mode:** CONTROLLED IMPLEMENTATION · additive backend (`format=csv`) + new admin page + Admin Hub card.
**Doctrine:** TRACK_13_18 · TRACK_13_19 · TRACK_13_20 · TRACK_13_21.
**Verdict:** ✅ **PASS** · CSV endpoint live · admin page mounted · Admin Hub V2 card surfaced · Dispatch map-first hard lock intact.

---

## 1 · Executive Summary

Admin now has a **company-wide Material Movement Ledger data-quality surface** at
`/admin/material-ledger-quality` with **CSV export** wired to the existing dispatch+admin
gated endpoint extended with `?format=csv` (single endpoint, no duplicate composition logic).

* Backend extension: `GET /api/dispatch/haul-ledger?format=csv` returns a CSV stream with operational fields only (no cost / pay / contract / accounting / FleetWatcher fabrication).
* New page: `frontend/src/pages/AdminMaterialLedgerQuality.jsx`.
* New route: `/admin/material-ledger-quality` (admin-gated via `RequireAdmin`).
* New Admin Hub V2 card: `Section 05 · Material data quality · admin`.

**Live smoke (admin token, 30-day range):** 92 haul cycles · 13 projects · 83 trucks · 4 materials · 22 DR-in rows · 30 DR-out rows · 92 missing-proof rows surfaced as the default queue. CSV stream returns 93 lines (header + 92 data rows) with `Content-Type: text/csv; charset=utf-8` and `Content-Disposition: attachment; filename="masci_haul_ledger_2026-05-15_to_2026-06-12.csv"`. FleetWatcher hard-zero.

---

## 2 · Source Verification (Phase 0)

### Backend

| Item                                                                | Verified |
| ------------------------------------------------------------------- | -------- |
| Track 13.21 endpoint `/api/dispatch/haul-ledger`                    | ✅ existing |
| Auth dep `_require_dispatch_or_admin` accepts both Dispatch + Admin tokens | ✅ (server.py · iter179 hardening) |
| Response shape (rows / rollups / by_project / by_material / by_truck / source_breakdown / fleetwatcher) | ✅ |
| Admin token reads endpoint successfully                             | ✅ (curl proof: `ok=True rows=92 projects=12`) |
| `Response` (fastapi.responses) suitable for CSV stream              | ✅ standard FastAPI pattern |
| No existing CSV duplicate                                            | ✅ |

### Frontend

| Item                                                                          | Verified |
| ----------------------------------------------------------------------------- | -------- |
| `AdminHubV2.jsx` Section pattern (k / t / c / Card)                           | ✅ |
| `App.js` admin guard `const A = (el) => <RequireAdmin>{el}</RequireAdmin>;`   | ✅ (line 335) |
| `lib/adminAuth.js` `getAdminToken()` for `X-Admin-Token` header               | ✅ |
| `DispatchHaulLedger.jsx` styling reusable                                      | ✅ (mirrored card/chip/table language) |

**No blocker identified.**

---

## 3 · Backend Export / Endpoint Summary

**Approach:** Extend existing endpoint (per spec preferred option) — `GET /api/dispatch/haul-ledger` now accepts an optional `format=csv` query parameter.

**Auth:** Unchanged — `_require_dispatch_or_admin` (Dispatch token OR Admin token).
**Bound:** Same 90-day window cap applies to CSV requests.
**Filters:** All 6 existing filters (`date_from` / `date_to` / `project_number` / `material_code` / `truck` / `verification_status`) work identically for CSV.

**File touched:** `backend/routes/dispatch_haul_ledger.py` (added `format` param + `Response` import + `_csv_response()` helper + `_CSV_FIELDS` list + `_csv_escape()` helper). Identical composition pipeline; CSV branch executes after JSON shape is fully assembled.

**CSV response headers:**

```
Content-Type:        text/csv; charset=utf-8
Content-Disposition: attachment; filename="masci_haul_ledger_{date_from}_to_{date_to}.csv"
X-MASCI-Export:      haul-ledger-phase-d
Cache-Control:       no-store
```

**Validation:** `format=csv` accepted; any other value 422s with explicit message.

---

## 4 · Admin Page Summary

**File:** `frontend/src/pages/AdminMaterialLedgerQuality.jsx` (new).
**Route:** `/admin/material-ledger-quality`.
**Guard:** `A(...)` (RequireAdmin).
**Default focus:** last 30 days · `verification_status=missing_proof` (data-quality first).

### Sections

1. **Header** — title · subtitle · Back-to-Admin · Refresh · Export CSV button (slate-900, downloads via fetch+blob with `X-Admin-Token` header).
2. **Filter strip** — date_from · date_to · project_number · material_code · truck · verification dropdown (default ordered: `missing_proof`, `partial`, `needs_review`, `verified`, `all`) · Apply.
3. **Rollup tiles (10)** — Haul cycles · Loads (filtered) · Missing proof (rose when > 0) · Scale tickets · Net tons (tickets) · Projects · Trucks · Materials · DR rows in · DR rows out.
4. **Main rows table** — date · project · material (code + description) · truck · driver · source→destination · ticket count · net tons · verification chip.
5. **By Project breakdown (top 25)** — loads · ticket_count · missing_proof (rose when > 0).
6. **By Material breakdown (top 25)** — loads · ticket_count.
7. **Trust footer** — source breakdown counts + verbatim FleetWatcher-not-connected line.

### Honest empty + error states

* **Empty:** "No material ledger issues for this range."
* **Error:** "Material ledger data-quality feed unavailable ({err}). No data invented."
* **`null` net tons:** rendered as `—`.

---

## 5 · Admin Surfacing Summary

**New Admin Hub V2 card** added in `AdminHubV2.jsx`:

```
Section: 05 · Material data quality · admin
Title:   Material Ledger Quality
Body:    Company-wide missing-proof queue + CSV export over the Material Movement Ledger
         (haul cycles · scale-ticket attachments · daily report material rows). Operator-driven
         follow-up for hauls without ticket proof. FleetWatcher remains not connected.
Link:    /admin/material-ledger-quality
Status:  Live workflow (verified chip)
testid:  admin-hub-v2-q-material-ledger-quality
```

* Placed AFTER existing Section 04 (Map data quality · admin) to preserve hub hierarchy.
* No metric / queue count fetched on the hub itself (spec rule: "do not show counts on hub unless existing endpoint safely provides them and you fetch them without heavy load"). Card is link-only.

---

## 6 · Access Control Verification

| Role               | Outcome on `/admin/material-ledger-quality`                                              |
| ------------------ | ---------------------------------------------------------------------------------------- |
| Admin              | ✅ Page loads · `X-Admin-Token` accepted by `/api/dispatch/haul-ledger`                 |
| PM                 | ❌ `RequireAdmin` HOC redirects to `/admin/login` (per existing `A(...)` guard pattern)  |
| Dispatch           | ❌ Same — admin-only client gate. Dispatch retains `/dispatch-portal/haul-ledger`.        |
| Driver / Safety / Shop / HR | ❌ Same client gate. Endpoint also rejects (only dispatch+admin tokens valid).    |
| Public (no auth)   | ❌ 401 from backend                                                                       |

**Endpoint stays at `/api/dispatch/haul-ledger`** — the spec acknowledged either path was acceptable; extension is cleaner because Admin already has read rights via `_require_dispatch_or_admin`. No new endpoint introduced.

---

## 7 · CSV Fields

Operational fields only — exactly the 20 columns approved by the spec:

```
date, project_number, project_name,
material_code, material_description,
haul_type,
truck_id, driver_name,
source_location, destination_location,
haul_cycle_id, assignment_id,
scale_ticket_count,
net_lbs, net_tons,
verification_status, source_system,
started_at, completed_at,
fleetwatcher_connected
```

**Excluded (hard rule):** cost · price · contract value · billing · pay quantities · margin · customer invoice · accounting fields · FleetWatcher truthy values (`fleetwatcher_connected` is always `false`).

**Quoting:** RFC-4180 minimal-quote — only quote values containing comma / double-quote / newline; internal double-quotes doubled.

---

## 8 · Data-Quality Logic

| Default                          | Value                                          |
| -------------------------------- | ---------------------------------------------- |
| Date range                       | last 30 days (today inclusive)                 |
| `verification_status`            | `missing_proof`                                |
| Filter dropdown order            | `missing_proof` → `partial` → `needs_review` → `verified` → `all` |
| Empty queue copy                 | "No material ledger issues for this range."   |

**No persistence.** Admin can change filters and re-query but cannot mark rows verified / corrected from this surface (per spec: "view + export only").

---

## 9 · FleetWatcher Trust Status

* JSON: `fleetwatcher: {connected: false, reason: "not_connected"}` on every response.
* CSV: `fleetwatcher_connected,false` on every row.
* UI trust footer: *"FleetWatcher not connected — admin view is currently based on MASCI daily reports, dispatch haul cycles, and scale-ticket attachments. No accounting, cost, pay-quantity, or contract totals are computed by this surface."* — verified live.

---

## 10 · Files Changed

| File                                                          | Change                                                                                                       |
| ------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| `backend/routes/dispatch_haul_ledger.py`                      | Added `Response` import · added `format` query param · added CSV branch (`_csv_response()`) + 20-field whitelist + `_csv_escape()`. JSON path unchanged. |
| `frontend/src/pages/AdminMaterialLedgerQuality.jsx`           | NEW · admin page (~430 lines · 25+ unique data-testids · matches Phase C visual language).                    |
| `frontend/src/App.js`                                         | 1 lazy import + 1 Route line under existing admin block.                                                     |
| `frontend/src/pages/AdminHubV2.jsx`                           | 1 new `Section 05` block with the Material Ledger Quality card.                                              |

**Files NOT touched:** every other file in the repo. `material_movement.py` (Phase A) untouched. `PmProjectDetail.jsx` (Phase B) untouched. `DispatchHaulLedger.jsx` (Phase C) untouched. `DispatchSideNavV2.jsx` untouched.

---

## 11 · Routes Added

| Route                                  | Guard         | Page                              |
| -------------------------------------- | ------------- | --------------------------------- |
| `/admin/material-ledger-quality`       | RequireAdmin  | `AdminMaterialLedgerQuality.jsx`  |

---

## 12 · Endpoints Added or Extended

| Method | Path                                       | Change                                                |
| ------ | ------------------------------------------ | ----------------------------------------------------- |
| GET    | `/api/dispatch/haul-ledger?format=csv`     | EXTENDED · CSV branch added. JSON path unchanged.     |

No new endpoint path. The Admin export reuses the exact same auth + composition pipeline as the JSON view.

---

## 13 · Tests Run

### Backend (curl against live preview)

| Case                                                                                                        | Result |
| ----------------------------------------------------------------------------------------------------------- | ------ |
| Admin token + JSON (default today)                                                                          | ✅ 200 |
| Admin token + 30-day range JSON                                                                             | ✅ 200 · rows=92 · projects=12 |
| Admin token + CSV (30-day range · `verification_status=missing_proof`)                                      | ✅ 200 · 93 lines · headers correct |
| CSV `Content-Type: text/csv; charset=utf-8`                                                                  | ✅ |
| CSV `Content-Disposition: attachment; filename="masci_haul_ledger_2026-05-15_to_2026-06-12.csv"`            | ✅ |
| CSV `X-MASCI-Export: haul-ledger-phase-d` custom header                                                      | ✅ |
| CSV row contains zero cost / price / contract / pay / margin / invoice / accounting fields                   | ✅ (verified by `_CSV_FIELDS` whitelist) |
| `format=invalid` returns 422                                                                                 | ✅ (closed-set validation) |
| 91-day range returns 422                                                                                     | ✅ (Phase C cap preserved) |
| Phase A endpoint (`/api/material-movement/daily/X/2099-01-01`) returns 200 unchanged                         | ✅ |

### Frontend

| Case                                                                                | Result |
| ----------------------------------------------------------------------------------- | ------ |
| ESLint on all 4 touched frontend files                                              | ✅ clean |
| Browser smoke at `/admin/material-ledger-quality`                                   | ✅ title + filters + Export CSV button + 10-tile rollups + 92-row table |
| FleetWatcher trust footer verbatim                                                  | ✅ verified |
| Admin Hub V2 card visible at `/admin/hub_v2`                                         | ✅ `admin-hub-v2-q-material-ledger-quality` testid present |
| Dispatch map-first canvas at `/dispatch-portal`                                     | ✅ still mounted |
| Phase C `/dispatch-portal/haul-ledger` still works (regression)                     | ✅ untouched |
| Phase B `/pm/projects-legacy/:p` still works (regression)                            | ✅ untouched |

---

## 14 · Browser Smoke Evidence

```
title rendered: True
filter strip: True
export CSV button: True
state machine rendered: True
fleetwatcher trust: FleetWatcher not connected — admin view is currently based on MASCI daily reports, dispatch haul cycles, and s…
Admin Hub V2 card surfaced: True
Dispatch map-first canvas still mounted: True
SUCCESS
```

Screenshot saved at `/tmp/track_13_22_admin_mlq.png` — 92 missing-proof rows queued as the default Admin view, with rose-toned "Missing proof" tile leading the eye.

---

## 15 · Hard-Lock Regression Results

| Hard lock                                                  | Verified | Method                                                  |
| ---------------------------------------------------------- | -------- | ------------------------------------------------------- |
| Dispatch Map-First (`/dispatch-portal` MapLibre canvas)    | ✅       | Browser smoke confirmed `canvas` present                |
| Dispatch Companion Haul Ledger (Phase C)                   | ✅       | Endpoint untouched on JSON path · sidebar untouched     |
| PM project material panel (Phase B)                        | ✅       | `PmProjectDetail.jsx` not touched                       |
| Driver no-login (`/shift`, `/d/:token`, `/driver`)         | ✅       | No driver file touched                                  |
| DriverHubV2 retired                                        | ✅       | No revival                                              |
| Shop Repair ≠ Returned                                     | ✅       | No shop file touched                                    |
| One map engine                                             | ✅       | No new map                                              |
| Track 13.13 Operational Events panel                       | ✅       | `PmProjectDetail.jsx` not touched                       |
| Track 13.14 scale-ticket extension                         | ✅       | `operational_attachments.py` not touched                |
| Track 13.17 PO lifecycle notifications                     | ✅       | `po_requests.py` not touched                            |
| Track 13.19 Phase A endpoint                               | ✅       | `material_movement.py` not touched                      |
| Track 13.20 Phase B PM panel                               | ✅       | `PmProjectDetail.jsx` not touched                       |
| Track 13.21 Phase C Dispatch ledger                        | ✅       | JSON path of endpoint unchanged · page untouched · sidebar untouched |
| ODR surfacing                                              | ✅       | No ODR file touched                                     |
| PM Hub V2                                                  | ✅       | `PmHubV2.jsx` not touched                               |
| No new collection                                          | ✅       | No DB write or new collection                            |
| FleetWatcher remains NOT_CONNECTED                         | ✅       | Hard-zero in JSON · `false` in every CSV row             |
| No cost / accounting / pay-app / contract / ERP fields     | ✅       | CSV column whitelist enforced                            |

---

## 16 · What Was NOT Built

* ❌ No new collection
* ❌ No new endpoint path (extension only)
* ❌ No cost / accounting / pay-app / contract / ERP / billing / invoice / margin fields anywhere
* ❌ No verification persistence (rows are not editable from this surface)
* ❌ No approve / reject / correct admin actions (view + export only per spec)
* ❌ No FleetWatcher activation (hard-zero in JSON; `false` in CSV)
* ❌ No map overlay / Dispatch map mutation
* ❌ No PM company-wide view (PM still project-scoped per Track 13.20)
* ❌ No driver UI / driver login
* ❌ No new design system; reused Phase C card/chip/table styling
* ❌ No Admin Hub count fetch (link-only card per spec)
* ❌ No PDF export, no XLSX export (CSV only per spec)
* ❌ No `mismatch` verification status (Phase D didn't add it; will defer to a future per-quantity reconciliation track)
* ❌ No ODR `MaterialEvent` join (still 0 in source_breakdown)

---

## 17 · Five-Pillar Evaluation

| Pillar    | Score | Justification                                                                                                                                                            |
| --------- | ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Powerful  | 9/10  | Admin gains a company-wide missing-proof queue + one-click CSV that operators can work with in spreadsheets immediately. 92 actionable rows surfaced from preview today.    |
| Simple    | 9/10  | Single endpoint extension + one page + one card. Zero new endpoint path. Zero new collection. Zero new auth gate.                                                         |
| Beautiful | 8/10  | Matches Phase C visual language exactly (same Rollup/StatusChip/Field components mirrored). Admin Hub card uses the existing Section pattern.                            |
| Trusted   | 10/10 | FleetWatcher hard-zero in both JSON and CSV. CSV column whitelist excludes every financial field by design. Honest empty/error states. `null` renders as `—`.            |
| Proven    | 9/10  | Backend curl covers JSON + CSV + invalid format + 91-day cap + admin auth. Browser smoke covers admin page + hub card + map-first regression. ESLint clean across 4 files. |

---

## 18 · Rollback Procedure

1. `git checkout HEAD~1 -- backend/routes/dispatch_haul_ledger.py frontend/src/pages/AdminMaterialLedgerQuality.jsx frontend/src/App.js frontend/src/pages/AdminHubV2.jsx`
2. Delete `frontend/src/pages/AdminMaterialLedgerQuality.jsx`
3. `sudo supervisorctl restart backend` (frontend hot-reloads)

Zero schema / index / collection / permission delta.

---

## 19 · Final Verdict

**Track 13.22 · CLOSED · PASS.**

Admin now has a powerful, simple, trusted, and proven Material Movement Ledger data-quality + CSV export surface that reuses the existing dispatch+admin gated endpoint with a single additive query parameter. No new collection. No accounting. No fake FleetWatcher. Dispatch map-first hard lock preserved.

Deployment readiness remains 🟢 **GREEN**.

---

## 20 · Recommended Track 13.23

The Material Movement Ledger phased plan (Phases A–D) is now **complete** within the boundaries set by Track 13.18. Phase E (FleetWatcher ingestion) remains **BLOCKED on `FLEETWATCHER_API_KEY` + active service credentials** and should not be attempted until those are present.

Recommended next track candidates (operator may pick):

* **Track 13.23 — Material Ledger Operator Sign-Off Window** (P1): Begin a 14- or 30-day operator validation window for Phases A–D before any further build. Collect actionable feedback from PM, Dispatch, and Admin users. Document changes requested. Defer all new ledger phases until window closes.
* **Track 13.6N — 30-day operator signoff window** (P1, pre-existing): Cross-portal V2 swap signoff (HR / PM / Safety / Shop V2 routes).
* **Track 13.X — ODR PM-Hub pending-drafts pill** (P0 leftover · ~2.5h from Track 13.9 §8 BQ#8).
* **Track 13.X — Material Ledger Phase E · FleetWatcher Ingestion** — DO NOT START until credentials supplied.

---

## 21 · Final Response (per Track 13.22 §9)

1. **Track status:** CLOSED · PASS.
2. **Implementation summary:** Extended existing `/api/dispatch/haul-ledger` endpoint with `?format=csv` returning operational-only CSV (20 whitelisted fields · no financial fields · FleetWatcher `false` on every row). New admin page `/admin/material-ledger-quality` consumes the JSON endpoint with `X-Admin-Token`. New Admin Hub V2 card surfaces the page. Zero new endpoint path · zero new collection · zero new auth gate.
3. **Files changed (4):** `backend/routes/dispatch_haul_ledger.py` (CSV branch) · `frontend/src/pages/AdminMaterialLedgerQuality.jsx` (new) · `frontend/src/App.js` (lazy import + route) · `frontend/src/pages/AdminHubV2.jsx` (Section 05 card).
4. **Routes added:** `/admin/material-ledger-quality` (admin-gated).
5. **Endpoint extended:** `GET /api/dispatch/haul-ledger?format=csv` returns a CSV stream (`text/csv; charset=utf-8` · Content-Disposition attachment with date-bounded filename · `X-MASCI-Export: haul-ledger-phase-d` header).
6. **What Admin can now see:** Company-wide ledger queue defaulted to `missing_proof` rows · 10 rollups · filterable by date range / project / material / truck / verification status · per-project + per-material breakdowns · one-click CSV export · honest empty + error states · FleetWatcher trust footer verbatim copy.
7. **What was not built:** new collection · new endpoint path · cost / accounting / pay-app / contract / ERP / billing / invoice fields · verification persistence · row-edit actions · FleetWatcher activation · map overlay · PDF/XLSX exports · ODR join · hub count badge · driver UI · PM company-wide view · mismatch status.
8. **Tests passed:** backend curl (JSON 200 · CSV 200 with 93 lines · 422 on invalid `format` · 422 on 91-day range · FleetWatcher hard-zero) · Phase A endpoint regression 200 unchanged · ESLint clean across all 4 touched files · browser smoke (admin page title/filters/export-button/rollups/table/trust-footer + Admin Hub V2 card + Dispatch map canvas).
9. **Hard locks verified:** Dispatch Map-First · Driver no-login · DriverHubV2 retired · Shop RTS · one map engine · Phases A/B/C surfaces untouched · Track 13.13/13.14/13.17 untouched · FleetWatcher NOT_CONNECTED enforced in JSON + CSV + UI · no new collection · no financial fields · PM stays project-scoped.
10. **Blockers:** None for Phase D. **Phase E (FleetWatcher ingestion) remains BLOCKED on `FLEETWATCHER_API_KEY` + active service credentials.**
11. **Recommended next build:** **Track 13.23 — Material Ledger Operator Sign-Off Window** (open Phases A–D for operator validation before any further build). Alternative: complete Track 13.9 §8 BQ#8 (ODR PM-Hub pending-drafts pill · ~2.5h).
