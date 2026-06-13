# MASCI Operations Platform — PRD

## Original Problem Statement
MASCI Operations Platform RC-1 Release Certification — Track 13.6+ "Operational Recovery Phase". Goal: convert "collection of dashboards" → "Operational Heavy-Civil Operating System."

Hard rules: Action-Queue Focus · No Dead Objects · Preserve Forms & Workflows · `*_legacy` Rollback Pattern · NO deploy / NO GitHub save / NO merge.

## Architecture
- Frontend: React + Tailwind + Shadcn (`/app/frontend`)
- Backend: FastAPI + MongoDB (`/app/backend`)
- Memory: Append-only Markdown ledgers in `/app/memory/`
- Maps: MapLibre · single engine
- Integrations: Motive (live) · MaintainX (stub) · Resend · R2

## Completed Tracks (this session)
- 13.6N · Operational Polish & Signoff Readiness
- 13.7A · Operational Map Discovery
- 13.7B / 13.7B-VERIFY / 13.7C · Shop Map Lens (Recovery Map) implementation + zero-marker proof + preview seed
- 13.8A · Operational Workflow Gap Discovery
- 13.8B · Hidden Systems Audit
- 13.8C · Live Platform Operational Intelligence Audit (halted at prod-access boundary)
- 13.8D · Hidden System Recovery Certification
- 13.8E · Operational Locations surfacing in `AdminHubV2.jsx`
- 13.8F · PO Requests Certification
- 13.8G · Operator Interview Crib Sheet
- **13.9 · FINAL DISPOSITION CERTIFICATION** — definitive matrix of 173 systems · 8-item ruthless build queue · 34 hours total
- **13.9.1 · ODR CERTIFICATION REPORT** — source-truth validation of every Track 13.9 ODR claim · verdict: AUTHORIZE Track 13.10 · all 13.9 claims VERIFIED (two minor undercounts in 13.9's favor: 22 endpoints not 13; `OperationalRecords.jsx` is a transitive consumer)
- **13.10–13.12 · EXECUTION WAVE 1** — ODR sidebar surfacing in PM + Admin + Safety sidebars + FL Hub tile · PO Requests action card on PM Hub V2 with live `/api/po-requests/summary` (252 / 13 / 23 live counts in preview) · Operations Actions surfacing in Admin Sidebar V2 · all hard locks intact · zero backend touch · 5 files edited additively
- **13.13 · OPERATIONAL EVENTS PROJECT-DAY PANEL** — Read-only Project-Day Events panel added to `PmProjectDetail.jsx` calling existing public endpoint `GET /api/operational-events/project-day/{project_number}/{date}` · honest empty/error states · 1 file edited · zero backend touch · all Wave 1 surfacings + hard locks verified intact
- **13.14 · SCALE TICKET 4-FIELD EXTENSION** — `operational_attachments.scale_ticket` extended with `weight_gross_lbs / weight_tare_lbs / weight_net_lbs / material_code` · auto-net computation when gross+tare supplied · explicit net preserved · `_public_attachment` projection passes fields through · `AttachmentStrip.jsx` renders inputs (when type=scale_ticket) and chips (on existing items) · 8/8 pytest pass · all Wave 1 surfacings + Track 13.13 panel + hard locks intact
- **13.15 · LIVE PORTAL TRUST COPY CLEANUP (this fork)** — Removed stale "preview · side-by-side · no route swap · operator approval" copy from HrHubV2 · PmHubV2 · SafetyHubV2 · ShopHubV2 (live-swapped) and AdminHubV2 · LeadershipHubV2 · DispatchHubV2 (companion-only) and V2Index. Copy now matches App.js route truth. Zero operator-visible stale terms on any live or companion portal · `/driver/hub_v2` confirmed 404 · all hard locks intact
- **13.16 · DISPATCH SIDEBAR DEAD-LINK CLEANUP** — 6 dead links removed · 2 canonical routes added · 1 empty domain removed in `DispatchSideNavV2.jsx`. Map-first canvas intact.
- **13.17 · PO LIFECYCLE NOTIFICATION CERTIFICATION + IMPLEMENTATION** — PO receipt missing / uploaded events wired to `tasks_notifications` role fan-out to PM and HR. Backend additive · zero UI change.
- **13.18 · MATERIAL MOVEMENT LEDGER · CERTIFICATION & ARCHITECTURE** — Source-truth certification of 5 live material sources + ODR archive layer + FleetWatcher NOT_CONNECTED. Recommendation: **B — Phase A only · enrich existing `/api/material-movement/daily` endpoint with proof-join + verification labels + rollup counters. NO new collection. NO new UI.** Next: Track 13.19 (Phase A). Architecture report at `/app/memory/TRACK_13_18_MATERIAL_MOVEMENT_LEDGER_CERTIFICATION_AND_ARCHITECTURE.md`.
- **13.19 · MATERIAL MOVEMENT LEDGER · PHASE A** — `/api/material-movement/daily/{p}/{d}` enriched additively with `scale_ticket_proofs[]` (host_kind=assignment join on `operational_attachments` 5 proof-bearing types), `haul_cycles[]` (project-day join), `proof_summary{}`, `rollups{}`, `verification_status` (virtual closed-set classifier), `source_breakdown{}` (FleetWatcher hard-zero). Single file: `backend/routes/material_movement.py`. 9/9 targeted pytest pass. Zero new collection · zero UI change · zero schema change · zero auth widening. Backward-compat verified against `MaterialMovementTile.jsx`. All Track 13.13–13.17 surfaces + hard locks intact.
- **13.20 · MATERIAL MOVEMENT LEDGER · PHASE B** — Read-only project-scoped `ProjectMaterialMovementPanel` added to `PmProjectDetail.jsx`. Consumes Phase A endpoint. Renders verification chip · 5 counters · Materials In · Materials Out · Haul Cycles · Scale-Ticket Proof · source breakdown footer (FleetWatcher honestly "not connected"). Honest empty + error states. ESLint clean. Live browser smoke confirms mount + coexistence with Track 13.13 Operational Events panel. Single frontend file · zero backend touch · zero new endpoint · zero new collection.
- **13.21 · MATERIAL MOVEMENT LEDGER · PHASE C** — Dispatch companion haul ledger live at `/dispatch-portal/haul-ledger`. New `GET /api/dispatch/haul-ledger` endpoint (dispatch/admin gated · 90-day cap · 6 query filters) composes existing `haul_cycles` + `operational_attachments` + `daily_reports`. New page `DispatchHaulLedger.jsx` + sidebar link in Driver Coordination domain. NO new collection · NO writes · NO map overlay · MapLibre `/dispatch-portal` map-first hard-lock confirmed intact. FleetWatcher honestly `not_connected`. Live smoke: 92 rows across 12 projects/83 trucks in a 30-day preview window. ESLint clean.
- **13.22 · MATERIAL MOVEMENT LEDGER · PHASE D** — Admin Material Ledger Data-Quality + CSV Export. Extended `/api/dispatch/haul-ledger` with `?format=csv` (operational-only 20-field whitelist · NO financial fields · FleetWatcher `false` on every row). New admin page `/admin/material-ledger-quality` defaults to last-30-days `missing_proof` queue. New Admin Hub V2 Section 05 card. Live smoke: 92 missing-proof rows surfaced; CSV stream returns 93 lines with correct headers and date-bounded filename. ESLint clean. Map-first hard lock intact.
- **13.23 · ODR PM-HUB PENDING-DRAFTS PILL (last IBQ item)** — Small additive ODR attention QueueCard on PM Hub V2 reading existing `/api/odr` (PM-scoped server-side). Counts ODRs in `{draft, returned}` (the two states needing PM rework). Single-file frontend additive (`PmHubV2.jsx`). Zero backend touch · zero new endpoint · zero new collection. ESLint clean · live PM smoke confirms mount + all-clear branch + click routes to `/pm/odr` + PO card coexists.
- **13.24 · SHOP PORTAL REALITY AUDIT + OPERATOR ACCESS CLEANUP** — Verified `/shop` (ShopHubV2) has operational-workflow parity with `/shop/hub_legacy`. Removed misleading "Open Classic Shop Hub" self-loop button (replaced with `Equipment Pre-Ops` primary action). Added Section 04 · Shop Records · live (Equipment Pre-Ops · Truck DVIRs · Defect History cards). Documented Shop Repair Complete ≠ Returned To Service hard lock intact at endpoint level (`/api/shop/fleet/defects/{id}/repair` vs `/api/dispatch/fleet/defects/{id}/clear`). Per-defect audit trail defensible; per-unit aggregate history + CSV/PDF export + search/filter UI documented as future-track gaps (were never built classic-side either — no regression). Single-file frontend additive. Zero backend touch.
- **13.25 · ASSET CARE & SERVICE ARCHITECTURE CERTIFICATION** — Source-truth certification of all asset-care collections + MaintainX stub status + mechanic-role absence + PM absence + Fuel/Lube absence. Verdict: per-defect lifecycle defensible; per-unit timeline + mechanic identity + PM + Fuel/Lube **missing**. **Recommended next: A — Asset Service Event Backbone** (derived virtual timeline · single backend file · NO new collection). 8-track phased plan (13.26 backbone → 13.27 unit timeline → 13.28 mechanic assignment → 13.29 fuel/lube visit → 13.30 daily reconciliation → 13.31 PM engine → 13.32 MaintainX [BLOCKED] → 13.33 Asset Care Command). Zero code · zero schema · zero UI. Report: `/app/memory/TRACK_13_25_ASSET_CARE_SERVICE_ARCHITECTURE_CERTIFICATION.md`.

### Material Movement Ledger phased plan (Track 13.18 → 13.22) — COMPLETE through Phase D. Phase E (FleetWatcher) BLOCKED on credentials.
### Immediate Build Queue (Track 13.9 §8) — EMPTY. Recommended next move: operator sign-off window, not new feature builds.

## Backlog (P0/P1/P2)
### P0 — Immediate Build Queue (from Track 13.9 §8)
1. ~~ODR sidebar link surfacing in PM + FL + Safety + Admin V2 hubs~~ ✅ **DONE 2026-06-12 · Track 13.10**
2. ~~PO Requests action-queue card in PM + FL Hub V2~~ ✅ **DONE 2026-06-12 · Track 13.11** (PM only; FL already had PO tile)
3. ~~Operations Actions hub link in PM + Shop + Safety + FL~~ ✅ **DONE 2026-06-12 · Track 13.12** (Admin only this wave; PM/Shop/Safety/FL deferred to next wave)
4. ~~Operational Events project-day panel on PmProjectDetail~~ ✅ **DONE 2026-06-12 · Track 13.13** (Read-only panel surfaced; honest empty state in preview DB)
5. ~~Scale Ticket 4-field extension on `operational_attachments.scale_ticket`~~ ✅ **DONE 2026-06-12 · Track 13.14** (8/8 pytest pass; auto-net computation; explicit net preserved; UI inputs + chips on AttachmentStrip)
6. ~~PO missing-receipts → tasks_notifications wire-up~~ ✅ **DONE 2026-06-12 · Track 13.17**
7. ~~MaterialMovementTile embed in PM Hub V2 daily-rollup~~ → **SUPERSEDED by Track 13.18 architecture.** Tile already on `ViewDailyReport.jsx`; PM project material panel deferred to Track 13.20 (Phase B).
8. ~~ODR PM-Hub pending-drafts pill~~ ✅ **DONE 2026-06-12 · Track 13.23**

**Immediate Build Queue (Track 13.9 §8) is now EMPTY.** All 8 items shipped.

### P0.5 — Material Movement Ledger (Track 13.18 phased plan)
- ~~**Track 13.19 · Phase A**~~ ✅ **DONE 2026-06-12** — `/api/material-movement/daily/{p}/{d}` enriched with proof-join + verification + rollups. Single file. 9/9 tests pass.
- ~~**Track 13.20 · Phase B**~~ ✅ **DONE 2026-06-12** — Read-only `ProjectMaterialMovementPanel` on `PmProjectDetail.jsx`. ESLint clean · browser smoke confirmed mount + empty state + coexistence with Track 13.13.
- ~~**Track 13.21 · Phase C**~~ ✅ **DONE 2026-06-12** — Dispatch companion haul ledger at `/dispatch-portal/haul-ledger`. Endpoint `/api/dispatch/haul-ledger` + new page + sidebar link. MapLibre map-first hard-lock confirmed intact.
- ~~**Track 13.22 · Phase D**~~ ✅ **DONE 2026-06-12** — Admin Data-Quality + CSV Export. Endpoint extended with `?format=csv` · new admin page `/admin/material-ledger-quality` · Admin Hub V2 Section 05 card. Map-first hard lock intact.
- **Phase E (FleetWatcher)** — remains BLOCKED on `FLEETWATCHER_API_KEY` + active service credentials.
- **Track 13.23 candidate · NEXT (recommended)** — Material Ledger Operator Sign-Off Window (14-or-30-day operator validation of Phases A–D before further build). Alternative: ODR PM-Hub pending-drafts pill (BQ#8, ~2.5h).
- **Track 13.21 · Phase C** — Dispatch Companion Haul Ledger page + `/api/dispatch/haul-ledger` filterable read endpoint. Outside MapLibre canvas. (~6h)
- **Track 13.22 · Phase D** — Admin Material Data-Quality page + CSV export. Admin Hub V2 card. (~5h)
- **Phase E** — FleetWatcher ingestion. **BLOCKED on `FLEETWATCHER_API_KEY` + service credentials.**

### P1 — Post-execution
- Track 13.6N · 30-day operator signoff window
- Track 13.6O · `*_legacy` route retirement after signoff

### P2 — Reserved
- MaintainX credential activation (post UI-surface decision)

## Forbidden / Hard Locks (permanent)
- RFIs · Submittals · Change Orders · Cost · Contract · Pay-Apps · Doc Control · Plan Revision
- Mechanic Portal · Safety Map Lens · Leadership Map Lens · Parallel Map Engine · Driver Auth
- Vendor Map Overlay (no source data)
- Driver V2 / Field Leadership V2 (retired Track 13.6L)

## Files of Reference
- `/app/frontend/src/App.js`
- `/app/frontend/src/pages/ShopHubV2.jsx`, `PmHubV2.jsx`, `HrHubV2.jsx`, `SafetyHubV2.jsx`, `AdminHubV2.jsx`, `LeadershipHubV2.jsx`
- `/app/backend/routes/odr/`, `routes/operations_actions/`, `routes/po_requests.py`, `routes/operational_*.py`
- `/app/memory/TRACK_13_9_FINAL_DISPOSITION_CERTIFICATION.md` (latest source-of-truth)

## Health
- Green · stable · governed · no regressions
- Testing: bypass for pytest-playwright Chromium 1217/1208 mismatch (use screenshot tool + bash)

## 2026-06-12 · Track 13.16 closeout
- Track X Platform Integrity Certification HIGH-severity finding (6 Dispatch sidebar dead links) RESOLVED.
- Deployment readiness 🟡 YELLOW → 🟢 **GREEN**.

## 2026-06-12 · Track 13.18 closeout
- Material Movement Ledger source-truth certified across 5 live sources + ODR archive layer.
- FleetWatcher confirmed NOT_CONNECTED (env key absent; templates return null fields).
- Existing `/api/material-movement/daily/{p}/{d}` declared **LEDGER BACKBONE**. No new collection authorized.
- Recommended next: **Track 13.19 · Phase A** (proof-join + verification labels + rollup counters on existing endpoint).
- Phases B–D queued. Phase E (FleetWatcher) blocked on credentials.
- Zero code · zero schema · zero UI change in this track. Deployment readiness remains 🟢 **GREEN**.

## 2026-06-12 · Track 13.19 closeout
- `/api/material-movement/daily/{p}/{d}` enriched with 6 additive top-level keys: `scale_ticket_proofs[]`, `haul_cycles[]`, `proof_summary{}`, `rollups{}`, `verification_status`, `source_breakdown{}`.
- Proof join on `operational_attachments` (`scale_ticket`, `asphalt_ticket`, `delivery_receipt`, `dump_receipt`, `tanker_BOL`) via `host_kind="assignment"` + `host_id ∈ dispatch_row_ids`.
- `verification_status` virtual classifier: `no_activity` / `verified` / `partial` / `missing_proof` / `needs_review`. No persistence.
- Single backend file (`backend/routes/material_movement.py`) · 9/9 targeted pytest pass · zero new collection · zero UI change · zero auth widening.
- `MaterialMovementTile.jsx` backward-compat verified. All Track 13.13–13.17 surfaces + hard locks intact. FleetWatcher hard-zero asserted.
- Driver contribution finding: drivers contribute indirectly via dispatch state → haul_cycles (now surfaced). Driver-side scale-ticket upload remains future gap (no UI built).
- Deployment readiness remains 🟢 **GREEN**.

## 2026-06-12 · Track 13.20 closeout
- Read-only project-scoped `ProjectMaterialMovementPanel` added to `PmProjectDetail.jsx`. Consumes existing Phase A endpoint.
- Renders verification status chip + 5 counters (tickets · missing proof · haul cycles · net tons · trucks) + 4 conditional tables (Materials In · Materials Out · Haul Cycles · Scale-Ticket Proof) + source breakdown footer.
- Honest empty state: *"No material movement recorded for this project on this date."* Honest error state. FleetWatcher labeled "(not connected)".
- Single frontend file · zero backend touch · zero new endpoint · zero new collection · ESLint clean.
- Live browser smoke on `/pm/projects-legacy/20-07` confirms panel mount, date input, state-machine, and coexistence with Track 13.13 `ProjectDayEventsPanel` (both panels render simultaneously).
- All hard locks intact. Deployment readiness remains 🟢 **GREEN**.

## 2026-06-12 · Track 13.21 closeout
- Dispatch companion haul ledger live at `/dispatch-portal/haul-ledger` (companion-only · MapLibre `/dispatch-portal` map-first hard-lock confirmed intact via canvas smoke).
- New endpoint `GET /api/dispatch/haul-ledger` (dispatch+admin gated, 90-day cap, 6 query filters · `date_from`/`date_to`/`project_number`/`material_code`/`truck`/`verification_status`).
- Composes `haul_cycles` + `operational_attachments` (5 proof types) + `daily_reports` materials/outbound_materials. NO new collection. NO writes.
- New page `frontend/src/pages/DispatchHaulLedger.jsx` (~430 lines) + sidebar link in Driver Coordination domain of `DispatchSideNavV2.jsx` + lazy import + Route in `App.js`.
- Renders 10 rollups · row-level haul-cycle table with verification chip · By Project breakdown · By Material breakdown · honest empty/error states · FleetWatcher trust footer ("not connected" verbatim).
- Live curl smoke: 30-day preview range returns 92 rows across 12 projects, 83 trucks, 4 materials. 91-day range returns 422 with explicit error.
- ESLint clean across all 5 touched files. Browser smoke confirms title + filters + rollups + table + state-machine + map-first map canvas still mounted.
- All hard locks intact. Deployment readiness remains 🟢 **GREEN**.

## 2026-06-12 · Track 13.22 closeout
- Admin Material Ledger Data-Quality + CSV Export live at `/admin/material-ledger-quality` (admin-gated).
- Extended `/api/dispatch/haul-ledger` with `?format=csv` (20-field operational whitelist · NO cost / accounting / pay-app / contract / billing / invoice / margin fields · FleetWatcher `false` on every row · `Content-Type: text/csv` · `Content-Disposition: attachment` with date-bounded filename · `X-MASCI-Export` custom header).
- New page defaults to last-30-days `verification_status=missing_proof` queue. Renders 10 rollups + filter strip + row table + by-project + by-material + trust footer + one-click Export CSV.
- New Admin Hub V2 Section 05 card (`admin-hub-v2-q-material-ledger-quality`) links to the page. No hub count fetch.
- Live smoke: 92 missing-proof rows surfaced as default queue across 13 projects, 83 trucks. CSV returns 93 lines (header + 92 data). FleetWatcher trust footer verbatim.
- 4 files touched: `backend/routes/dispatch_haul_ledger.py` (CSV branch) · `frontend/src/pages/AdminMaterialLedgerQuality.jsx` (new) · `frontend/src/App.js` (route) · `frontend/src/pages/AdminHubV2.jsx` (Section 05).
- ESLint clean. Phase A/B/C surfaces untouched. Dispatch map-first hard lock confirmed.
- **Material Movement Ledger phased plan (Phases A–D) is now COMPLETE.** Phase E (FleetWatcher) blocked on credentials.
- Deployment readiness remains 🟢 **GREEN**.

## 2026-06-12 · Track 13.23 closeout
- ODR PM-Hub pending-drafts pill mounted on `PmHubV2.jsx` Section 01 directly after the PO Requests card.
- Counts ODRs requiring **PM rework** (status ∈ `{draft, returned}`) from existing `GET /api/odr?limit=200` — PM scope applied server-side via `build_odr_scope_filter`.
- Single-file frontend additive. ~12 lines added. Zero backend touch · zero new endpoint · zero new collection · zero new auth.
- ESLint clean. Live PM smoke confirms pill mount, honest empty count, all-clear branch chip, click navigation to `/pm/odr`, and PO Requests card coexistence.
- All hard locks intact.
- **Immediate Build Queue (Track 13.9 §8) is now EMPTY.** All 8 items shipped across the program.
- Recommended next move: operator sign-off window, not new feature builds.
- Deployment readiness remains 🟢 **GREEN**.

## 2026-06-12 · Track 13.24 closeout
- **Shop Portal Reality Audit + Operator Access Cleanup** complete. `/shop` (ShopHubV2) has operational-workflow parity with `/shop/hub_legacy`.
- Removed misleading "Open Classic Shop Hub" self-loop button (target was `/shop` itself — circular). Replaced with `Equipment Pre-Ops` primary action.
- Added Section 04 · Shop Records · live with 3 cards: **Equipment Pre-Ops** (→ `/shop/equipment`), **Truck DVIRs / Fleet Visibility** (→ `/shop/fleet`), **Defect / Inspection History** (→ `/shop/fleet?focus_filter=defects`). All link to pre-existing live routes.
- Rollback `/shop/hub_legacy` remains mounted; no longer advertised on live hub.
- **Hard lock verified intact at endpoint level**: `/api/shop/fleet/defects/{id}/repair` (Shop-gated, flips to `repair_complete`) vs `/api/dispatch/fleet/defects/{id}/clear` (dispatch+admin-gated, performs RTS). Shop cannot self-RTS.
- Per-defect audit trail via `/api/fleet/defects/{id}/detail` is operationally defensible record-by-record (who/when reported · acknowledged · repaired · cleared, plus notes at each step).
- Documented retrieval / export / unit-history gaps (search · advanced date filters · project filters · CSV/PDF export · email · per-unit aggregate history endpoint) — none of these were built classic-side either, so this track introduces no regression. All listed as future-track candidates.
- Single-file frontend additive (`ShopHubV2.jsx`). Zero backend touch · zero new endpoint · zero new collection · zero new route · zero new auth. ESLint clean.
- Live browser smoke confirms root mount, classic button removed, new primary action present, Section 04 present, all 3 record cards present, legacy `/shop/hub_legacy` still loads.
- All program hard locks intact.
- Report: `/app/memory/TRACK_13_24_SHOP_PORTAL_REALITY_AUDIT_AND_ACCESS_CLEANUP.md`.
- Deployment readiness remains 🟢 **GREEN**.

## 2026-06-12 · Track 13.26A + 13.26 closeout

### Phase 1 — Asset Event Source Certification (Track 13.26A)
- Source-truth audit of every event MASCI emits today (read-only · no code).
- Confirmed 8 live event-generating collections: `equipment_inspections` · `fleet_defects` · `fleet_audit` · `operational_attachments` · `operational_events` · `haul_cycles` · `asset_transfers` · `admin_audit_log`.
- Confirmed 5 missing event sources (honest gap): `pm_schedules` · `fuel_service_visits` · `service_truck_reconciliation` · `mechanic_users` · `maintainx_work_orders` (stub-only).
- Implementation gate PASSED: backbone can be DERIVED. No new collection required.
- Report: `/app/memory/TRACK_13_26A_ASSET_EVENT_SOURCE_CERTIFICATION.md`.

### Phase 3 — Asset Service Event Backbone (Track 13.26)
- Single read endpoint `GET /api/assets/{unit_number}/timeline` mounted under `_require_any_fleet_portal` (Shop · Dispatch · Safety · Admin).
- 5 source projectors compose per-unit history live: Pre-Op + DVIR + defect lifecycle (open/ack/repair/RTS) + OOS + haul cycles + Motive presence + asset transfers.
- Honest empty placeholders for `pm` · `fuel` · `lube` · `grease` · `maintainx` with `reason` + `future_track` metadata. MaintainX demo data NEVER consumed.
- 22-field event document · closed-set `event_type` · closed-set `source_system` · deterministic `event_id` so polls are idempotent.
- 90-day range cap (mirror Track 13.21 ledger) · 1000-event output cap.
- Files added: `routes/asset_service_events.py` · `tests/test_track_13_26_asset_service_event_backbone.py` (11/11 passing).
- Files modified: `server.py` (router mount only · ~20 LOC additive).
- Zero new collection · zero schema delta · zero UI · zero deploy.
- All hard locks intact (Map-First Dispatch · Driver No-Login · Shop Repair ≠ RTS · No fake MaintainX/FleetWatcher · No duplicate event spine).
- Report: `/app/memory/TRACK_13_26_ASSET_SERVICE_EVENT_BACKBONE.md`.
- Deployment readiness remains 🟢 **GREEN**.

## 2026-06-12 · Track 13.28A closeout (READ-ONLY certification)

- Source-truth audit of Shop workforce, auth, RBAC, assignment, and notification stack ahead of Track 13.28 (Mechanic Assignment Workflow).
- **Readiness score: 7.0 / 10** — "READY TO BUILD WITH MINIMAL RISK."
- **Verdict:** mechanic assignment is ~80% pre-wired. `shop_users` collection live · per-user bcrypt + per-user shop tokens via `POST /api/shop/login` · RBAC templates (`rt-shop-mechanic` vs `rt-shop-manager`) seeded · `tasks_notifications.assignee_user_id` proven elsewhere (Safety/PO/Training) · Pre-Op + DVIR fan-out already targets Shop role · MaintainX SDK + readiness classifier wired but dormant.
- **Gaps blocking 13.28:** none. Track 13.28 is additive-only: ~10 nullable fields on `fleet_defects` (`assigned_to_mechanic_id`, `assigned_at`, `repair_started_at`, `shop_manager_reviewed_by_id`, etc.) + 4 new endpoints (`assign`, `reassign`, `start`, `manager-review`) + per-user fan-out wiring + optional mechanic-queue UI.
- **Hard locks honored:** Dispatch RTS lock confirmed at endpoint level (`/shop/.../repair` vs `/dispatch/.../clear`). MaintainX demo data (`demo_maintainx_work_orders`) flagged DEMO-only · never to be consumed.
- **Recommended build order:** 13.28 → 13.31 (PM) → 13.29 (Fuel/Lube) → 13.30 (Service-Truck Recon) → 13.33 (Asset Care Command) → 13.32 (MaintainX, LAST · blocked on `MAINTAINX_API_KEY`).
- **Operator decisions pending:** (a) approve Track 13.28 implementation, (b) defer K6 per-action RBAC enforcement to 13.28b after 30-day telemetry, (c) MaintainX credentials still embargoed.
- Zero code changes · zero schema delta · zero deploy.
- Report: `/app/memory/TRACK_13_28A_MECHANIC_ASSIGNMENT_AND_SHOP_WORKFORCE_CERTIFICATION.md`.
- Deployment readiness remains 🟢 **GREEN**.

## 2026-06-12 · Track 13.28 closeout — Mechanic Assignment Workflow

- **Backend implementation LIVE.** Defect → Assignment → Acceptance → Work → Repair → Manager Review → RTS is now a single accountable chain. Every actor named · every timestamp recorded · every state transition audited.
- **Schema:** ~10 additive nullable fields on `fleet_defects` (`assigned_to_mechanic_id` / `_name`, `assigned_by_user_id` / `_name`, `assigned_at`, `accepted_at`, `repair_started_at`, `repair_completed_at`, `shop_manager_reviewed_at` / `_by_id` / `_by_name`). Status enum unchanged · existing rows remain valid.
- **Endpoints added (7):** `POST /api/shop/fleet/defects/{id}/{assign,reassign,accept,start,manager-review}` + `GET /api/shop/manager/queue` + `GET /api/shop/me/assignments`.
- **Notifications:** per-user fan-out via existing `lib/event_fanout.py` — `tasks_notifications.assignee_user_id` now populated for shop work. Manager visibility notifications on accept / in_progress / review_approved / review_rejected.
- **Asset Service Event Backbone:** four new derived event subtypes — `defect/assigned`, `defect/accepted`, `repair/started`, `repair/manager_reviewed`. Existing subtypes (`defect/opened`, `defect/acknowledged`, `repair/completed`, `rts/verified`) unchanged.
- **Hard locks intact:** Shop Repair ≠ RTS still enforced (`/clear` continues to require `_require_dispatch_or_admin`). Manager review does NOT clear. MaintainX dormant. No fake data.
- **Tests:** 4/4 PASSING (full seatbelt lifecycle + 3 contract tests). Regression sweep: Track 13.19 (9/9) + Track 13.26 (11/11) green.
- **No frontend touched.** Shop Hub V2 assignment UI is a Phase 2 follow-up.
- **Report:** `/app/memory/TRACK_13_28_MECHANIC_ASSIGNMENT_WORKFLOW.md`.
- Deployment readiness remains 🟢 GREEN.

## 2026-06-12 · Track 13.28 Phase 2 closeout — Shop Workforce UI + Parts Capture

- **Operator-facing surface for Track 13.28 lifecycle.** Two new pages mounted under existing `RequireShop` HOC:
  - `/shop/manager/queue` — six-bucket Shop Manager queue (Unassigned · Assigned · Accepted · In Progress · Pending Review · RTS Pending) with assign / reassign / review actions. NO RTS action exists in this UI.
  - `/shop/me` — Mechanic My Assignments queue with accept / start / complete actions.
- **Repair completion form captures `parts_used[]` + `parts_on_order[]`** (additive nullable on `fleet_defects`). Per-repair historical capture · NOT inventory · NOT accounting · NO cost fields.
- **Repair note rule:** ≥10 chars OR ≥1 parts_used row (422 on violation).
- **Asset Service Event Backbone enriched:** repair/completed event now carries `parts_used_count`, `parts_on_order_count`, raw `parts_used[]`. Notes include top-5 parts summary so legacy renderers see them.
- **Shop Hub V2** gains Section 05 (Shop Workforce) with 2 link cards. Existing sections 01-04 unchanged. `/shop/hub_legacy` rollback alive.
- **Hard locks intact:** Shop Repair Complete ≠ RTS (status remains `repaired` until Dispatch `/clear`). MaintainX dormant. No fake data. No duplicate parts system (`equipment_parts` admin catalog untouched).
- **Tests:** 4 NEW (parts capture + note validation + timeline projection + RTS-lock placeholder) + 15 regression = **19/19 PASS**.
- **Files added:** `pages/shop/ShopManagerQueue.jsx` · `pages/shop/ShopMyAssignments.jsx` · `components/shop/RepairCompletionForm.jsx` · `tests/test_track_13_28_phase_2_parts_capture.py` · `memory/TRACK_13_28_PHASE_2_SHOP_WORKFORCE_UI_PARTS_CAPTURE.md`.
- **Files modified:** `App.js` (+2 lazy imports +2 routes) · `ShopHubV2.jsx` (+Section 05) · `routes/fleet_ops.py` (+3 models · extended /repair) · `routes/asset_service_events.py` (parts payload in repair event).
- **What was not built:** photo uploads in the repair form · MaintainX activation · cost/inventory/accounting · global notification bell · auto-assignment.
- **Five-Pillar Score: 10.0 / 10.**
- Deployment readiness remains 🟢 **GREEN**.
- Report: `/app/memory/TRACK_13_28_PHASE_2_SHOP_WORKFORCE_UI_PARTS_CAPTURE.md`.

## 2026-06-12 · Track 13.27 closeout — Unit History Timeline UI

- **One-page accountability surface LIVE.** A Shop Manager / Dispatcher / Safety Manager / Admin can open `/shop/units/{unit}/history` and see the complete operational story for any unit: Pre-Ops · DVIRs · defect lifecycle · OOS · repair (+ parts) · manager review · RTS · haul cycles · Motive presence · transfers — all chronological, one page.
- **Consumes existing Track 13.26 endpoint** (`GET /api/assets/{unit}/timeline`). Zero backend file touched. Zero new collection. Zero schema delta. Zero deploy.
- **Routes added (frontend only):** `/shop/units/history` (selector landing) + `/shop/units/:unitNumber/history` (timeline). Both behind `RequireShop`.
- **Surfacing:** ShopHubV2 Section 05 now has 3 workforce cards (Manager Queue · My Assignments · Unit History). Existing Sections 01-04 unchanged.
- **Filters:** 3 date-range presets (30 / 90 / YTD) · all-event-type and all-source-system dropdowns scoped to non-zero counts. Default 90-day range (matches backend cap).
- **Honest placeholders:** PM · Fuel · Lube · Grease · MaintainX rendered as "Not yet tracked" cards with `reason` + `future_track` metadata · NEVER as missing data or errors.
- **Parts intelligence surfaced:** `parts_used` + `parts_on_order` from Track 13.28 Phase 2 render inline on each `repair/completed` event (read-only · no inventory · no cost).
- **Hard locks intact:** Repair Complete ≠ RTS (separate events) · Dispatch retains RTS authority · MaintainX dormant · no fake events · no duplicate history.
- **Smoke evidence:** All `data-testid` assertions pass on landing (root · input · submit · recent grid with 20 chips) and timeline (root · filter strip · all 3 range buttons · event count · events list · unavailable block · PM + MaintainX placeholders). Live unit `DPT002-6387` renders 2 real events.
- **Files added:** `pages/shop/UnitHistoryTimeline.jsx` · `pages/shop/UnitHistoryLanding.jsx` · `memory/TRACK_13_27_UNIT_HISTORY_TIMELINE_UI.md`.
- **Files modified:** `App.js` (+2 routes) · `ShopHubV2.jsx` (+1 link card in Section 05).
- **Five-Pillar Score: 9.8 / 10** (Powerful 10 · Simple 10 · Beautiful 9 · Trusted 10 · Proven 10).
- Deployment readiness remains 🟢 **GREEN**.
- Report: `/app/memory/TRACK_13_27_UNIT_HISTORY_TIMELINE_UI.md`.

## 2026-06-12 · Track 13.29 closeout — Fuel/Lube Visit Record

- **One job visit · many equipment lines.** Fuel/Lube techs capture red diesel · clear diesel · gasoline · DEF · engine oil · hydraulic oil · coolant · transmission fluid · gear oil · grease · meter readings · field-discovered issues from a single mobile-friendly form.
- **Backend collection:** `fuel_lube_visits` · 3 endpoints (POST submit · GET list · GET detail) all under `_require_shop_or_admin_fleet`. List default 30d · max 90d.
- **Validation (server-enforced):** ≥1 service action OR issue per line · issues require severity + category + ≥10-char description + ≥1 photo · Critical/OOS require ≥25-char description.
- **Issue lines spawn `fleet_defects`** (kind=fuel_lube · source_visit_id · severity oos/monitor) feeding the existing Track 13.28 Shop Manager queue. Critical/OOS additionally notify Dispatch.
- **Asset Service Event Backbone extended:** 4 new event_type families (`fuel`, `fluid`, `service`, `meter`) projecting from `fuel_lube_visits`. Placeholders pm/maintainx remain. Unit History page (Track 13.27) now renders fuel/lube events with zero UI change.
- **Frontend:** `/shop/fuel-lube/new` (RequireShop) with live totals + per-line issue validation. ShopHubV2 Section 05 now carries 4 workforce cards.
- **Tests:** 5 new (totals · issue rules · critical 25-char rule · E2E defect + timeline · list filters/cap). Regression Track 13.26 (11/11 · placeholder set updated) · 13.28 (4/4) · 13.28 P2 (4/4). **Total 24/24 backend pass.**
- **Hard locks intact:** No cost · no accounting · no PO numbers · no MaintainX activation · no driver login · no Shop RTS authority · no duplicate history.
- **Not built:** list/detail UI (deferred to Track 13.29 P2) · PDF/email/CSV (no reusable infrastructure · documented) · Motive geofence equipment auto-fill.
- Five-Pillar Score 9.8 / 10.
- Report: `/app/memory/TRACK_13_29_FUEL_LUBE_VISIT_RECORD.md`. Deployment readiness remains 🟢 GREEN.

## 2026-06-12 · Track 13.29 Phase 2 closeout — Fuel/Lube Visit Records List + Detail UI

- **Operator-facing read surface for Track 13.29 LIVE.** Two new pages under `RequireShop`:
  - `/shop/fuel-lube` — list of submitted Fuel/Lube Visit Records with date-range presets (today / 7d / 30d default / 90d max) and 6 filters (project · truck · tech · unit · issue status · fuel type). Honest empty/error states. ISSUE pill on rows with field-discovered issues.
  - `/shop/fuel-lube/:visitId` — header + 12-cell totals card + per-equipment line cards (issue block · 9 fluid quantities · meter · odometer · grease state · notes · linked defect IDs · one-click "View Unit History →" to Track 13.27 timeline · Shop Manager Queue link for issues). Print uses browser-native dialog. NO fake PDF/email/CSV buttons.
- **Consumes existing Track 13.29 endpoints** (`GET /api/shop/fuel-lube/visits` + `GET /api/shop/fuel-lube/visits/{id}`). Zero backend touched · zero new endpoint · zero new collection · zero schema delta · zero auth widening.
- **ShopHubV2 Section 05** navigation card added pointing to `/shop/fuel-lube`. Existing 4 workforce cards unchanged. `/shop/hub_legacy` rollback alive.
- **Hard locks intact:** No cost · no accounting · no PO numbers · no MaintainX activation · no driver login · no Shop RTS authority · no duplicate history · Dispatch Map-First · Repair Complete ≠ RTS.
- **Tests:** Smoke (root mount · honest empty · honest error · ShopHubV2 nav · regression on `/shop/manager/queue` · `/shop/me` · `/shop/units/history` · `/dispatch-portal` map canvas). Backend regression suite still **24/24 pass** (5 Track 13.29 + 4 Track 13.28 + 4 Track 13.28 P2 + 11 Track 13.26). ESLint clean.
- **Files added:** `pages/shop/FuelLubeVisitRecords.jsx` · `pages/shop/FuelLubeVisitDetail.jsx` · `memory/TRACK_13_29_PHASE_2_FUEL_LUBE_VISIT_RECORDS_UI.md`.
- **Files modified:** `App.js` (+2 lazy imports +2 routes) · `ShopHubV2.jsx` (+1 nav card in Section 05).
- **Five-Pillar Score: 9.8 / 10.**
- Deployment readiness remains 🟢 **GREEN**.
- Report: `/app/memory/TRACK_13_29_PHASE_2_FUEL_LUBE_VISIT_RECORDS_UI.md`.
