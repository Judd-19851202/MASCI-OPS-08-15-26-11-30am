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

## Backlog (P0/P1/P2)
### P0 — Immediate Build Queue (from Track 13.9 §8)
1. ~~ODR sidebar link surfacing in PM + FL + Safety + Admin V2 hubs~~ ✅ **DONE 2026-06-12 · Track 13.10**
2. ~~PO Requests action-queue card in PM + FL Hub V2~~ ✅ **DONE 2026-06-12 · Track 13.11** (PM only; FL already had PO tile)
3. ~~Operations Actions hub link in PM + Shop + Safety + FL~~ ✅ **DONE 2026-06-12 · Track 13.12** (Admin only this wave; PM/Shop/Safety/FL deferred to next wave)
4. ~~Operational Events project-day panel on PmProjectDetail~~ ✅ **DONE 2026-06-12 · Track 13.13** (Read-only panel surfaced; honest empty state in preview DB)
5. ~~Scale Ticket 4-field extension on `operational_attachments.scale_ticket`~~ ✅ **DONE 2026-06-12 · Track 13.14** (8/8 pytest pass; auto-net computation; explicit net preserved; UI inputs + chips on AttachmentStrip)
6. ~~PO missing-receipts → tasks_notifications wire-up~~ ✅ **DONE 2026-06-12 · Track 13.17**
7. ~~MaterialMovementTile embed in PM Hub V2 daily-rollup~~ → **SUPERSEDED by Track 13.18 architecture.** Tile already on `ViewDailyReport.jsx`; PM project material panel deferred to Track 13.20 (Phase B).
8. ODR PM-Hub pending-drafts pill (2.5h)

### P0.5 — Material Movement Ledger (Track 13.18 phased plan)
- ~~**Track 13.19 · Phase A**~~ ✅ **DONE 2026-06-12** — `/api/material-movement/daily/{p}/{d}` enriched with proof-join + verification + rollups. Single file. 9/9 tests pass.
- **Track 13.20 · Phase B · NEXT (recommended)** — Read-only Material Movement panel on `PmProjectDetail.jsx` (project-scoped). Consumes Phase A endpoint. Zero backend touch. (~2h)
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
