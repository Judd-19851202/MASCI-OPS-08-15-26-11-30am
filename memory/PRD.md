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

## Backlog (P0/P1/P2)
### P0 — Immediate Build Queue (from Track 13.9 §8)
1. ~~ODR sidebar link surfacing in PM + FL + Safety + Admin V2 hubs~~ ✅ **DONE 2026-06-12 · Track 13.10**
2. ~~PO Requests action-queue card in PM + FL Hub V2~~ ✅ **DONE 2026-06-12 · Track 13.11** (PM only; FL already had PO tile)
3. ~~Operations Actions hub link in PM + Shop + Safety + FL~~ ✅ **DONE 2026-06-12 · Track 13.12** (Admin only this wave; PM/Shop/Safety/FL deferred to next wave)
4. ~~Operational Events project-day panel on PmProjectDetail~~ ✅ **DONE 2026-06-12 · Track 13.13** (Read-only panel surfaced; honest empty state in preview DB)
5. ~~Scale Ticket 4-field extension on `operational_attachments.scale_ticket`~~ ✅ **DONE 2026-06-12 · Track 13.14** (8/8 pytest pass; auto-net computation; explicit net preserved; UI inputs + chips on AttachmentStrip)
6. PO missing-receipts → tasks_notifications wire-up (5h · NEXT)
7. MaterialMovementTile embed in PM Hub V2 daily-rollup (1.5h)
8. ODR PM-Hub pending-drafts pill (2.5h)

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
