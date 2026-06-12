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
- **13.9 · FINAL DISPOSITION CERTIFICATION (this fork)** — definitive matrix of 173 systems · 8-item ruthless build queue · 34 hours total

## Backlog (P0/P1/P2)
### P0 — Immediate Build Queue (from Track 13.9 §8)
1. ODR sidebar link surfacing in PM + FL + Safety + Admin V2 hubs (3h)
2. PO Requests action-queue card in PM + FL Hub V2 (5h)
3. Operations Actions hub link in PM + Shop + Safety + FL (4h)
4. Operational Events project-day panel on PmProjectDetail (5h)
5. Scale Ticket 4-field extension on `operational_attachments.scale_ticket` (8h)
6. PO missing-receipts → tasks_notifications wire-up (5h)
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
