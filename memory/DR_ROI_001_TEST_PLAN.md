# DR-ROI-001 · Test Plan

**Scope:** All 7 subtracks. Each subtrack extends the harness; nothing regresses.

## This session (Track A + expanded B)

### Frontend
- V2 route mounts at `/daily-report/v2` behind feature flag
- Feature flag default OFF (V1 is default)
- V2 shell renders all 10 sections + 4 panels
- Activity Card add/edit/delete works client-side
- Constraint Chip opens follow-up card
- Photo min 6 enforced in V2 shell
- Placeholder panels render clean "Coming in Track C/D/E" states
- Zero interference with V1 route (`/new-daily-report` untouched)

### Backend
- **Lock test:** `backend/tests/test_dr_roi_001a_b_shell.py`
  - Docs exist + non-empty
  - V2 route registered in `AppRoutes.jsx`
  - `NewDailyReport.jsx` line count = 3,021 (V1 untouched)
  - `dailyReportSchema.js` line count = 112 (V1 untouched)
  - `backend/routes/daily_reports.py` line count = 665 (V1 untouched)
  - `PRD.md` + `CHANGELOG.md` mention DR-ROI-001A + 001B
  - Backend routes = 1,441 (no drift)
  - Track 22.* lock envelope still 268/268

## Track C (AI wiring)
- New AI fields formalized as optional in schema
- All existing DR tests still pass
- No live email dispatch during AI wiring
- Evidence-trace required for every AI-generated sentence
- Confidence gate < 0.70 drops sentence or emits question
- Supervisor approval blocks submit until acted on

## Track D (Photo Vision)
- Vision agent output feeds Ops/Safety/Quality (evidence only, never final narrative)
- Rate limit: ≤ 1 vision call per report
- Cache: SHA-256 evidence-hash skips duplicates
- Fail-open: vision unavailable → photos remain, panel shows banner

## Track E (PM KPI)
- Submit writes `daily_report_kpis` row synchronously (fail-open)
- Regeneration endpoint restores KPIs from source report
- PM dashboard tiles consume KPI collection
- Indexes present as specified

## Track F (PDF V2)
- V1 PDF still byte-wise identical
- V2 PDF renders correctly with V2 fields
- Cutover flag `PDF_V2_ENABLED` toggles output

## Track G (regression + deployment)
- Full Track 22.* lock envelope (currently 268/268) — must remain green
- Existing DR tests: `test_daily_reports.py` + 4 Track 19.* tests — must remain green
- Playwright: V1 submit · V2 submit · HR reads · Safety escalation · Excavation gate
- No live emails
- Testing agent independent verification

*Details in `DR_ROI_001_CONSOLIDATED_PLANS.md § 6`.*
