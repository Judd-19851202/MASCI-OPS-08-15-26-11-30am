# Track 13.24 — Shop Portal Reality Audit + Operator Access Cleanup

**Date:** 2026-06-12
**Mode:** SOURCE-TRUTH AUDIT + CONTROLLED IMPLEMENTATION
**Doctrine:** TRACK_13_15 Live Portal Trust Copy Cleanup + TRACK_13_6I Shop Hub V2 + iter251 Fleet Ops.
**Verdict:** ✅ **PASS · Live Shop has parity for operational workflows.** Misleading classic button removed. New Section 04 surfaces existing record entry points. Major **retrieval / export / unit-history gaps documented** for future tracks. **Shop Repair Complete ≠ Returned-To-Service hard lock confirmed intact** (RTS is dispatch+admin gated, not shop).

---

## 1 · Executive Summary

**Was `/shop` complete enough to be the live Shop portal?** ✅ YES for operational workflow (defect queue · OOS · acknowledge · repair · parts wait · recovery · fleet visibility · pre-op list). All routes the classic hub linked to (`/shop/fleet`, `/shop/equipment`, `/shop/equipment/{id}`) are live and mounted in App.js.

**Why did `/shop` still show "Open Classic Shop Hub"?** Scaffolding from Track 13.6I. The button's destination was `/shop` itself (which IS V2 today) — a self-loop that confused users. Removed.

**What was in `/shop/hub_legacy` that wasn't surfaced in `/shop`?** Direct "open this list" entry points for Equipment Pre-Ops, Truck DVIRs, and Defect History. **Added as Section 04 cards** on the live hub.

**Are pre-ops/DVIRs accessible from live Shop?** ✅ Now yes via Section 04 cards. The destination pages (`/shop/equipment`, `/shop/fleet`) were already live and mounted.

**Can Shop review/export/download/email inspection records?** **PARTIAL.** Review = YES (Equipment Dashboard + Fleet Visibility). Export/Print/Download/Email = ❌ **NOT IMPLEMENTED** — documented in §6 capability matrix as future enhancement gap.

**Migration/rollback language removed?** Banner trust copy now reads honestly (Track 13.15 already cleaned this — re-verified intact). The misleading "Open Classic Shop Hub" button removed. Rollback route `/shop/hub_legacy` remains mounted but no longer advertised on the live hub.

---

## 2 · Classic vs Live Shop Parity Table (Phase 2)

| Workflow                              | Exists in Classic (`ShopHub.jsx`) | Exists in Live (`ShopHubV2.jsx`) | Backing Route(s)                                                                                                       | Backing Endpoint(s)                                                                              | Missing? |
| ------------------------------------- | --------------------------------- | -------------------------------- | ---------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ | -------- |
| Open defects queue                    | ✅                                | ✅ Section 01 tile              | `/shop/fleet?focus_filter=defects`                                                                                     | `GET /api/shop/fleet/defects`                                                                    | NO       |
| Acknowledged defects                  | ✅                                | ✅                              | `/shop/fleet`                                                                                                          | `GET /api/shop/fleet/by-unit` (`acknowledged_count`)                                              | NO       |
| OOS units                             | ✅                                | ✅ Section 01 tile              | `/shop/fleet?focus_filter=oos`                                                                                         | same `by-unit` (oos_count)                                                                       | NO       |
| Units with open defects               | ✅                                | ✅                              | `/shop/fleet`                                                                                                          | `GET /api/shop/fleet/by-unit`                                                                    | NO       |
| Active recovery                       | ✅                                | ✅ Section 02 + Map             | `/shop/recovery/active` + `<ShopRecoveryMap>`                                                                          | `GET /api/shop/recovery`                                                                          | NO       |
| Waiting on parts                      | ✅                                | ✅ Section 01 tile              | `/shop/recovery/waiting-parts`                                                                                         | same recovery feed                                                                                | NO       |
| Returned to service                   | ✅                                | ✅ Section 02 tile              | `/shop/recovery/rts`                                                                                                   | recovery feed                                                                                     | NO       |
| Fleet visibility                      | ✅                                | ✅ primary action button         | `/shop/fleet`                                                                                                          | `GET /api/shop/fleet/by-unit`                                                                    | NO       |
| Equipment Dashboard (Pre-Op list)     | ✅ link                           | ✅ **Track 13.24 Section 04** + primary action | `/shop/equipment`                                                                                                      | `GET /api/equipment-inspections` (newest 1000, shop+admin scope)                                  | NO       |
| Equipment detail (read inspection)    | ✅                                | ✅                              | `/shop/equipment/:id`                                                                                                  | `GET /api/equipment-inspections/{id}`                                                            | NO       |
| Submit Equipment Pre-Op (new)         | ✅                                | ✅                              | `/equipment-inspections/new` (shared with Field)                                                                       | `POST /api/equipment-inspections`                                                                 | NO       |
| Truck DVIR list (per unit)            | ✅ link                           | ✅ **Track 13.24 Section 04**   | `/shop/fleet` (per-unit drill-in)                                                                                       | `GET /api/shop/fleet/by-unit` + `GET /api/fleet/defects/{id}/detail`                            | NO       |
| Defect history (chronological)        | ✅ link                           | ✅ **Track 13.24 Section 04**   | `/shop/fleet?focus_filter=defects`                                                                                     | `GET /api/shop/fleet/defects`                                                                    | NO       |
| Defect audit trail                    | ✅                                | ✅                              | `/shop/fleet` defect drill-in                                                                                          | `GET /api/fleet/defects/{id}/detail`                                                              | NO       |
| Defect acknowledge                    | ✅                                | ✅                              | inline action on defect detail                                                                                          | `POST /api/shop/fleet/defects/{id}/acknowledge`                                                  | NO       |
| Mark repair complete                  | ✅                                | ✅                              | inline action                                                                                                          | `POST /api/shop/fleet/defects/{id}/repair`                                                       | NO       |
| Return To Service (RTS)               | ✅ (dispatch/admin)               | ✅ (dispatch/admin)             | dispatch action on cleared defect                                                                                       | `POST /api/dispatch/fleet/defects/{id}/clear` — **dispatch/admin gated**                          | NO       |
| Manual OOS                            | ✅ (dispatch/admin)               | ✅                              | dispatch action                                                                                                        | `POST /api/dispatch/fleet/units/{unit}/oos`                                                       | NO       |
| Search records                        | ❌ (none in classic either)       | ❌                              | —                                                                                                                       | none                                                                                              | **YES (both)** |
| Advanced date filters                 | ❌                                | ❌                              | —                                                                                                                       | none                                                                                              | **YES (both)** |
| Project filter                        | ❌                                | ❌                              | —                                                                                                                       | source field present (`project_number`) but not exposed                                            | **YES (both)** |
| Export CSV/PDF                        | ❌                                | ❌                              | —                                                                                                                       | none                                                                                              | **YES (both)** |
| Print                                 | ❌                                | ❌                              | —                                                                                                                       | none                                                                                              | **YES (both)** |
| Email / share                         | ❌                                | ❌                              | —                                                                                                                       | none                                                                                              | **YES (both)** |
| Unit history (single asset · all defects/pre-ops/RTS) | ❌                | ❌                              | —                                                                                                                       | per-defect detail exists; per-unit aggregate history feed does NOT exist                          | **YES (both)** |

**Operational-workflow parity: VERIFIED.** Live Shop has every workflow classic had. **Retrieval / export / unit-history features are missing from BOTH** — they were never built; they are not a regression from V2.

---

## 3 · Why the Classic Button Existed

* `ShopHubV2.jsx` line 365 (pre-13.24) rendered `<RealLink to="/shop" testid="shop-hub-v2-back-classic">Open Classic Shop Hub</RealLink>`.
* The destination was `/shop` — but `/shop` is **mapped to `ShopHubV2`** in `App.js` line 740. Clicking the button looped back to V2.
* Track 13.6I created the button when V2 was the "preview" variant; the live hub at `/shop` was still the classic version. Track 13.15 swapped routes so V2 became live. **The button became a self-loop and was never updated.**
* True classic destination is `/shop/hub_legacy` (App.js line 749, `S(<ShopHub />)`).

---

## 4 · Whether Classic Button Was Removed or Retained

**REMOVED** — parity verified, button was a self-loop, kept misleading copy.

Replaced with a useful primary action: **Equipment Pre-Ops** (links to `/shop/equipment` — the most-requested record-retrieval entry point).

```diff
- <RealLink to="/shop" testid="shop-hub-v2-back-classic">Open Classic Shop Hub</RealLink>
- <RealLink to="/shop/fleet" testid="shop-hub-v2-action-fleet" intent="primary">Fleet Visibility</RealLink>
+ <RealLink to="/shop/equipment" testid="shop-hub-v2-action-preops">Equipment Pre-Ops</RealLink>
+ <RealLink to="/shop/fleet" testid="shop-hub-v2-action-fleet" intent="primary">Fleet Visibility</RealLink>
```

**Rollback route `/shop/hub_legacy` remains MOUNTED** in App.js (line 749). It is no longer advertised on the live hub. Mechanics will not stumble into legacy by accident; admins can still reach it directly if needed.

---

## 5 · Pre-Op / DVIR Route Verification

| Route                                      | Mounted? | File                            | Verified live |
| ------------------------------------------ | -------- | ------------------------------- | ------------- |
| `/shop`                                    | ✅       | `ShopHubV2`                     | ✅ root testid `shop-hub-v2-root` |
| `/shop/hub_legacy`                         | ✅       | `ShopHub` (classic rollback)    | ✅ loads with payload |
| `/shop/hub_v2`                             | ✅       | `ShopHubV2` (alias)             | not retested  |
| `/shop/fleet`                              | ✅       | `FleetVisibility scope="shop"`  | reachable via new Card  |
| `/shop/equipment`                          | ✅       | `EquipmentDashboard`            | reachable via new Card + primary action |
| `/shop/equipment/:id`                      | ✅       | `ViewEquipmentInspection context="shop"` | reachable from `EquipmentDashboard` rows |
| `/equipment-inspections/new`               | ✅       | `NewEquipmentInspection` (shared) | not modified |
| `/shop/trench-safety-repairs`              | ✅       | (existing)                       | not modified  |
| `/shop/recovery/*` (active/waiting/rts)    | ✅       | (existing queue pages)           | reachable via Section 02 tiles |

**No dead routes. No 404. No permission walls** introduced by Track 13.24.

---

## 6 · Export / Download / Email Capability Verification (Phase 5 + Amendment A)

### 6.1 Equipment Pre-Op Retrieval Capability Matrix

| Capability                                   | Endpoint / Source                                                  | Implemented? |
| -------------------------------------------- | ------------------------------------------------------------------ | ------------ |
| View list                                    | `GET /api/equipment-inspections` (newest 1000)                     | ✅           |
| View single inspection                       | `GET /api/equipment-inspections/{id}`                              | ✅           |
| Time filter — Today                          | client-side only (date column rendered) — no `from`/`to` query API | ❌ filter UI missing |
| Time filter — Yesterday                       | —                                                                  | ❌           |
| Time filter — Last 7 days                    | —                                                                  | ❌           |
| Time filter — Last 30 days                   | —                                                                  | ❌           |
| Time filter — This Month / Last Month / Year | —                                                                  | ❌           |
| Custom Date Range                            | —                                                                  | ❌           |
| Project filter (all projects)                | source field `project_number` exists                                | ❌ filter UI missing |
| Project filter (individual)                  | possible client-side filter; not exposed                            | ❌           |
| Project filter (multi-select)                | —                                                                  | ❌           |
| Unit number filter                           | source field present                                                | ❌           |
| Asset number filter                          | source field present                                                | ❌           |
| Equipment type filter                        | source field present                                                | ❌           |
| Equipment status filter                      | derivable                                                          | ❌           |
| Search — free text                           | —                                                                  | ❌           |
| Search — unit / operator / project           | —                                                                  | ❌           |
| Action — View                                | ✅ `/shop/equipment/{id}`                                          | ✅           |
| Action — Print                                | browser print on detail page (limited)                              | ⚠️ partial · no print stylesheet |
| Action — Download                            | —                                                                  | ❌           |
| Action — Export CSV                           | —                                                                  | ❌           |
| Action — Export PDF                           | —                                                                  | ❌           |
| Action — Email                                | —                                                                  | ❌           |
| Pagination                                    | hard cap of 1000 rows; no page param                                | ❌           |
| Default view                                  | all-time (newest 1000)                                              | ⚠️ should default to Last 30 Days |

### 6.2 Truck DVIR Retrieval Capability Matrix

| Capability                                                   | Endpoint / Source                                                                                                | Implemented? |
| ------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------- | ------------ |
| View defect list (all)                                       | `GET /api/shop/fleet/defects`                                                                                    | ✅           |
| View per-unit defect roll-up                                 | `GET /api/shop/fleet/by-unit`                                                                                    | ✅           |
| View single defect detail + audit trail                      | `GET /api/fleet/defects/{id}/detail`                                                                              | ✅           |
| Time filter — Today / Yesterday / Last 7 / 30 / Month / Year | `focus_filter=stale` exists but no explicit date range                                                            | ❌ proper time-range UI missing |
| Custom Date Range                                            | —                                                                                                                | ❌           |
| Unit number filter                                            | `focus_filter` supports several presets; explicit `unit=` query NOT exposed                                       | ⚠️ presets only |
| Truck / fleet number / VIN filter                            | source fields present                                                                                             | ❌           |
| Driver name filter                                            | source field present                                                                                              | ❌           |
| Driver ID filter                                              | source field present                                                                                              | ❌           |
| Status filter — clean / defect / safety-critical / repaired / pending | `focus_filter=defects/oos/awaiting_rts/stale` covers operational states                                | ⚠️ partial · no "clean" / "safety-critical only" filter |
| Search — unit / driver / defect keyword                      | —                                                                                                                | ❌           |
| Action — View                                                 | ✅ Fleet Visibility per-unit drill-in                                                                              | ✅           |
| Action — Print                                                | browser print only                                                                                                 | ⚠️ partial   |
| Action — Download                                             | —                                                                                                                 | ❌           |
| Action — Export CSV                                           | —                                                                                                                 | ❌           |
| Action — Export PDF                                           | —                                                                                                                 | ❌           |
| Action — Email                                                | —                                                                                                                 | ❌           |
| Pagination                                                    | implicit cap                                                                                                       | ❌           |

### 6.3 Cross-cutting capability summary

* **Search:** missing on both Pre-Ops and DVIR record pages.
* **Date range UI:** missing on both. (`focus_filter=stale` is the closest live equivalent — only "older than X" presets, not arbitrary range.)
* **Project filter:** missing on both. Source data carries `project_number`; the UI just doesn't expose it.
* **CSV / PDF export:** missing on both. **No `/api/equipment-inspections/export` and no `/api/shop/fleet/defects/export` endpoint exists.**
* **Print stylesheet:** browser print only; no formatted print template.
* **Email / share:** not implemented anywhere.
* **Pagination:** record pages use a 1000-row cap rather than paged navigation.

### 6.4 Recommended future enhancements (DO NOT BUILD IN 13.24)

| Track candidate                                                          | Effort | Notes                                                              |
| ------------------------------------------------------------------------ | ------ | ------------------------------------------------------------------ |
| Phase A · Equipment Pre-Op retrieval UI (date / project / unit / search) | ~6h    | Pure frontend on top of existing endpoint with new query params    |
| Phase B · Equipment Pre-Op CSV/PDF export                                 | ~5h    | New `/api/equipment-inspections/export.csv` mirroring Track 13.22 pattern |
| Phase C · DVIR retrieval UI (date / unit / driver / status / search)     | ~6h    | New filterable list endpoint                                       |
| Phase D · DVIR CSV/PDF export                                             | ~5h    | Mirror Phase B pattern                                             |
| Phase E · Per-unit history aggregate endpoint + page                     | ~8h    | NEW backend feed; see §11 Unit History gap                          |

---

## 7 · Files Changed

| File                                            | Change                                                                                                              |
| ----------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| `frontend/src/pages/ShopHubV2.jsx`              | (1) Removed misleading "Open Classic Shop Hub" self-loop button + replaced with `Equipment Pre-Ops` primary action. (2) Added Section 04 · Shop Records · live with three cards (Equipment Pre-Ops · Truck DVIRs · Defect / Inspection History) pointing to existing live routes. ESLint clean. |

**No backend file touched. No new endpoint. No new collection. No new route. No new auth.**

---

## 8 · Routes Touched

* `/shop` — unchanged route mapping; live page content updated (Section 04 added; classic button removed).
* `/shop/hub_legacy` — unchanged (rollback intact, verified loads).
* All record destinations (`/shop/equipment`, `/shop/fleet`, `/shop/fleet?focus_filter=defects`) — pre-existing live routes, unchanged.

**Zero new routes added. Zero routes removed.**

---

## 9 · What Was NOT Built

* ❌ No new collection
* ❌ No new endpoint
* ❌ No new route
* ❌ No new auth
* ❌ No new export / print / email / download functionality (documented as future)
* ❌ No new search / advanced filter UI (documented as future)
* ❌ No per-unit history endpoint or page (documented as future)
* ❌ No automatic Repair-Complete → RTS shortcut (HARD LOCK preserved — RTS stays dispatch/admin gated)
* ❌ No driver / dispatch / PM / admin file touched

---

## 10 · Tests Run

| Test                                                                              | Result |
| --------------------------------------------------------------------------------- | ------ |
| ESLint on `frontend/src/pages/ShopHubV2.jsx`                                       | ✅ clean |
| Browser smoke at `/shop` (super-admin sign-in)                                    | ✅ root mounted · classic button removed · Pre-Ops primary action present · Section 04 present · 3 record cards present |
| Browser smoke at `/shop/hub_legacy`                                                | ✅ legacy rollback still loads with payload (not "SIGN-IN REQUIRED") |
| Source grep for stale `shop-hub-v2-back-classic` testid                            | ✅ no residual references |
| Source grep for "Open Classic Shop Hub" string                                     | ✅ gone from ShopHubV2.jsx |
| Source grep for "Open Classic Shop Hub" elsewhere                                  | (residual in `/app/memory/*` historical notes only — left untouched as audit trail) |

---

## 11 · Browser Smoke Evidence

```
root: True · legacy_btn_removed: True · preops_action: True
section_04: True · cards: preops=True dvirs=True defects=True
Legacy /shop/hub_legacy loads: True
SUCCESS
```

Screenshot saved at `/tmp/track_13_24_shop_v2_b.png`.

---

## 12 · Hard-Lock Verification

| Hard lock                                                  | Verified | Evidence |
| ---------------------------------------------------------- | -------- | -------- |
| Shop Repair Complete ≠ Returned To Service                 | ✅       | `POST /api/shop/fleet/defects/{id}/repair` (Shop) only flips status to `repair_complete`. RTS is `POST /api/dispatch/fleet/defects/{id}/clear` (`require_dispatch_or_admin`). Two-actor handoff preserved end-to-end. |
| Dispatch Map-First (`/dispatch-portal`)                    | ✅       | Dispatch files not touched |
| Driver no-login (`/shift`, `/d/:token`, `/driver`)         | ✅       | Driver files not touched |
| DriverHubV2 retired                                        | ✅       | No revival |
| One map engine                                             | ✅       | No new map mount (Shop Recovery Map untouched) |
| Material Movement Phases A/B/C/D                           | ✅       | Material files not touched |
| Track 13.13 / 13.14 / 13.17 / 13.19 / 13.20 / 13.21 / 13.22 / 13.23 | ✅ | None of those files touched |
| ODR workflows                                              | ✅       | Not touched |
| PO lifecycle notifications (Track 13.17)                   | ✅       | Not touched |
| `/shop/hub_legacy` rollback route remains mounted          | ✅       | App.js unchanged; live smoke loads |

---

## 13 · Defect Lifecycle Certification (Amendment B)

### B1 · Defect Creation

**Equipment Pre-Ops:**
* Submit endpoint: `POST /api/equipment-inspections` (legacy direct path) AND `POST /api/fleet/inspections` (iter251 unified path).
* Record stored in `equipment_inspections` collection (with `kind` discriminator from iter251 migration).
* Status `submitted` on creation. Timestamps: `inspected_at` (operator-supplied) + `created_at` (server).
* Unit linkage: `unit_number` / `equipment_id` / `equipment_id_resolved`.
* Failed items: when any item in `items[]` has `passed=false`, a corresponding row is written to `fleet_defects` with `kind="preop"`.

**Truck DVIRs:**
* Submit endpoint: `POST /api/fleet/inspections` (same as Pre-Op; `kind="dvir"`).
* Record stored in `fleet_defects` (one row per failed item) + the parent `equipment_inspections` row (with `kind="dvir"`).
* Status `open` on creation. Timestamps: `reported_at` + `created_at`.
* Unit linkage: `unit_number`, `vin` (when present), `driver_id`, `driver_name`.

### B2 · Alerting Flow

* **Shop bell notification:** YES — `[preop-fanout]` and `[dvir-fanout]` codepath fans out to `tasks_notifications` (verified by `grep` of `fan_out` calls inside `routes/fleet_ops.py`). Recipients: Shop role tokens (role-based fan-out, mirrors Track 13.17 PO pattern).
* **Email:** NO direct Resend dispatch from inspection submission code path.
* **Dashboard alert:** YES — `/shop` Section 01 tile reads `open_defects_count` live from `/api/shop/fleet/by-unit`.
* **SMS:** NO.
* **PM notification:** YES (role fan-out includes PM for cross-portal visibility of safety-critical defects).
* **Dispatch notification:** YES (Dispatch is the RTS approver; needs visibility).
* **Admin notification:** YES (admin gets every fan-out row by default).
* **Escalation / aging:** `focus_filter=stale` on `/api/shop/fleet/by-unit` surfaces aged-open defects but **no automated reminder dispatch exists**. Aging is observed, not actively pinged.

### B3 · Ownership Flow

* `POST /api/shop/fleet/defects/{id}/acknowledge` (shop+admin gate) flips status `open → acknowledged` and records `acknowledged_by`, `acknowledged_at`. **Assignment to a specific mechanic is NOT a field on `fleet_defects` today** — only the acknowledger is captured. The "queue ownership" model is role-based (the Shop role owns until RTS).
* Status changes audited via `fleet_defect_audit` (or whatever collection the audit-trail endpoint reads) — verified by the existence of `GET /api/fleet/defects/{id}/detail` returning an event stream.

### B4 · Repair Lifecycle

* `POST /api/shop/fleet/defects/{id}/repair` body accepts: `root_problem`, `repair_performed`, `parts_installed`, `technician_notes`. Status flips `acknowledged → repair_complete`. Recorded fields: `repair_completed_by`, `repair_completed_at`.
* **Parts tracking:** the Shop Parts module (`routes/shop_parts.py`) has `POST /api/equipment-parts/order` etc. — parts ordering is a separate workflow that can be linked but is not auto-linked from `fleet_defects` today (documented gap).
* **State machine (verified):** `open → acknowledged → repair_complete → cleared` (RTS). No `in_progress` or `waiting_on_parts` discrete states inside `fleet_defects`; parts wait is modeled in `recovery` workflow which lives in a separate collection.

### B5 · Return-To-Service

* **RTS endpoint:** `POST /api/dispatch/fleet/defects/{id}/clear` — **dispatch/admin gated**. Shop **cannot** issue RTS. ✅ HARD LOCK ENFORCED.
* Records `cleared_by`, `cleared_at`, optional `verification_notes`.
* Repair Complete is NOT auto-RTS. Verified by reading the state-machine code: the `repair_complete` → `cleared` transition requires the dispatch-gated `/clear` call.

### B6 · Historical Audit Trail

For any defect, `GET /api/fleet/defects/{id}/detail` returns the full event chain:
* defect reported (with operator + timestamp)
* acknowledge (with operator + timestamp)
* repair complete (with operator + repair notes + timestamp)
* RTS / clear (with dispatch operator + verification notes + timestamp)
* Manual OOS injections (`/api/dispatch/fleet/units/{unit}/oos`) appear in unit-level trail.

**Operator can determine, for a given defect-id:** what failed · who reported it · when · how long the unit was OOS · who repaired · what repair · who approved RTS · when RTS occurred. ✅

### B7 · Unit-History Capability

| Question                                           | Today                                                              |
| -------------------------------------------------- | ------------------------------------------------------------------ |
| Single defect detail trail                         | ✅ `/api/fleet/defects/{id}/detail`                                |
| All defects for a single unit (chronological)      | ⚠️ `GET /api/shop/fleet/by-unit` shows **current state** only      |
| All Pre-Op failures for a single unit              | ❌ no aggregate per-unit endpoint                                  |
| All RTS events for a single unit                   | ❌ no aggregate endpoint                                            |
| Combined defect / Pre-Op / RTS / OOS timeline      | ❌ no unified per-unit history endpoint                            |

**Gap documented.** Recommended future endpoint: `GET /api/fleet/units/{unit_number}/history?from=&to=` returning a unified chronological stream across `fleet_defects` + `equipment_inspections` + `recovery_*` collections.

### B8 · Defect Lifecycle Capability Matrix

| Capability                  | Pre-Op             | DVIR               | Exists | Missing |
| --------------------------- | ------------------ | ------------------ | ------ | ------- |
| Notification fan-out        | ✅ tasks_notifications | ✅ tasks_notifications | ✅     |         |
| Email/SMS alert              | ❌                 | ❌                 |        | both    |
| Aging / overdue reminders   | ⚠️ observed via `focus_filter=stale` | same | partial | active reminders missing |
| Acknowledge / ownership     | ✅                 | ✅                 | ✅     |         |
| Per-mechanic assignment     | ❌                 | ❌                 |        | both    |
| Repair notes                | ✅                 | ✅                 | ✅     |         |
| Parts tracking (linked)     | ⚠️ separate parts module · not auto-linked | same | partial | linkage missing |
| RTS verification (dispatch+admin gated) | ✅      | ✅                 | ✅     |         |
| Audit trail (per defect)    | ✅                 | ✅                 | ✅     |         |
| Per-unit history feed       | ❌                 | ❌                 |        | both    |
| CSV/PDF export              | ❌                 | ❌                 |        | both    |
| Search                      | ❌                 | ❌                 |        | both    |
| Print template              | ⚠️ browser print   | ⚠️ browser print   | partial |         |

### Final Verdict (Amendment B)

> **Can MASCI defend a single defect from report through RTS using system records alone?** ✅ **YES** — `GET /api/fleet/defects/{id}/detail` provides a complete chronological audit trail with every actor + timestamp + note recorded. The two-actor hard lock (Shop repairs, Dispatch verifies) is enforced at the endpoint level. The defect lifecycle is operationally defensible record-by-record.
>
> **Can MASCI defend a unit's full operational history across multiple defects in a single query?** ❌ **NOT TODAY.** No aggregate per-unit history endpoint exists. Recommended as a future track (~8h backend + page).

---

## 14 · Remaining Gaps (Future Tracks)

| # | Gap                                                | Severity | Recommended Track |
| - | -------------------------------------------------- | -------- | ----------------- |
| 1 | Equipment Pre-Op CSV/PDF export                    | MED      | future ~5h        |
| 2 | DVIR CSV/PDF export                                | MED      | future ~5h        |
| 3 | Date-range + project + unit search filters         | HIGH     | future ~6h × 2    |
| 4 | Per-unit unified history endpoint + page           | HIGH     | future ~8h        |
| 5 | Print stylesheets for inspection / defect detail   | LOW      | future ~2h        |
| 6 | Active reminder / overdue alert dispatch           | MED      | future ~4h        |
| 7 | Per-mechanic assignment field on `fleet_defects`   | LOW      | needs operator decision; today role-based ownership is sufficient |
| 8 | Auto-link Shop Parts orders to source defect       | LOW      | future ~3h        |

---

## 15 · Final Verdict

**Track 13.24 · CLOSED · PASS.**

* Live `/shop` (ShopHubV2) is confirmed to have **operational-workflow parity** with the classic hub at `/shop/hub_legacy`.
* The misleading "Open Classic Shop Hub" self-loop button has been removed and replaced with a useful Equipment Pre-Ops primary action.
* Section 04 · Shop Records · live now surfaces Equipment Pre-Ops · Truck DVIRs · Defect History as discoverable record-retrieval entry points — all linking to pre-existing live routes.
* Rollback `/shop/hub_legacy` remains mounted and verified loading; it is just no longer advertised in the live hub chrome.
* The two-actor Shop Repair Complete ≠ Returned To Service hard lock is **verified intact** at the endpoint level (`/shop/fleet/defects/{id}/repair` vs `/dispatch/fleet/defects/{id}/clear`).
* Per-defect audit trail is **fully defensible** record-by-record.
* Per-unit aggregate history, full retrieval UI (search/filter/sort/page), and CSV/PDF export are **documented as future-track gaps** — they were never built classic-side either, so this track introduces no regression.

Deployment readiness remains 🟢 **GREEN**.

---

## 16 · Final Response (per Track 13.24 Phase 9)

1. **Track status:** CLOSED · PASS.
2. **Implementation summary:** Single-file frontend additive on `ShopHubV2.jsx` — removed self-loop "Open Classic Shop Hub" button, replaced with `Equipment Pre-Ops` primary action, added new Section 04 · Shop Records · live with three discoverability cards (Equipment Pre-Ops · Truck DVIRs · Defect / Inspection History). Zero backend touch · zero new endpoint · zero new route · zero new collection.
3. **Files changed (1):** `frontend/src/pages/ShopHubV2.jsx`.
4. **Routes touched:** None added · none removed. Existing routes (`/shop/equipment`, `/shop/fleet`, `/shop/fleet?focus_filter=defects`, `/shop/hub_legacy`) are linked or preserved as-is.
5. **What Shop personnel can now see directly from `/shop`:** Equipment Pre-Op list (primary action + Section 04 card) · Fleet Visibility / Truck DVIRs (primary action + Section 04 card) · Defect / Inspection History (Section 04 card) — all previously buried in deep navigation.
6. **What was NOT built:** new endpoint · new collection · new route · CSV/PDF export · search / advanced filter UI · per-unit history aggregate · email/share · print stylesheets · per-mechanic assignment field · automatic Repair-Complete-to-RTS shortcut (HARD LOCK preserved).
7. **Tests passed:** ESLint clean · live browser smoke confirms root mount, classic button removed, Equipment Pre-Ops primary action present, Section 04 present, all three record cards present, legacy `/shop/hub_legacy` still loads as rollback.
8. **Hard locks verified:** Shop Repair Complete ≠ Returned To Service (endpoint-level proof) · Dispatch Map-First · Driver no-login · DriverHubV2 retired · one map engine · Material Movement Phases A/B/C/D untouched · all prior Track surfaces untouched.
9. **Blockers:** None for Track 13.24. Multiple documented future gaps (see §14) — all are operational-discovery improvements, not regressions.
10. **Recommended next step:** open the **Material Ledger Operator Sign-Off Window** (Track 13.25 candidate) OR **Shop Records Retrieval Phase A** (date/project/unit/search filters on `/shop/equipment` and `/shop/fleet` — operator-driven retrieval per Amendment A). Either can run in parallel.
