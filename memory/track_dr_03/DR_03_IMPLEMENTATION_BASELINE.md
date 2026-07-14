# DR-03 Implementation Baseline

Date: 2026-07-14
Status: In-progress implementation checkpoint

## Pre-change revalidation summary
- Active authoring routes before DR-03 changes: `/daily/new`, `/daily/submit` via `DailyReportRouter`
- Active shell fork before changes: `DailyReportRouter` could render `NewDailyReport` or `NewDailyReportV3`
- Active V2 authoring route status before changes: `/daily-report/v2` already redirected away from direct authoring
- Draft key drift before changes:
  - `daily-report-new` in canonical V1 helper
  - `daily-report` inline in V3
- Draft scope drift before changes:
  - V1: `project::date::report_number`
  - V3: `project::date`
- Smart Prefill drift before changes:
  - V1 consumed `/api/jobs/{project}/recent-context`
  - V3 omitted the contract entirely
- Queue/idempotency drift before changes:
  - V3 used unscoped idempotency and queued `endpoint/payload` instead of canonical queue fields

## DR-03 checkpoint implemented
- Shell fork removed from `DailyReportRouter`
- Canonical V3 authoring shell now serves both `/daily/new` and `/daily/submit`
- Canonical draft base key unified to `daily-report`
- Canonical draft scope unified to `actor::project::date::instance`
- Stable actor identity now scopes crew memory and remembered project state
- V3 now uses canonical scoped idempotency and queue formKey
- V3 now exposes restore, archive recovery slot, and Smart Prefill offer/error UI

## Not yet fully completed in this checkpoint
- Canonical single-route redirect convergence (two routes still point to one shell)
- Full destructive-proof legacy draft promotion / retirement workflow
- Full downstream zero-drift parity certification across ODS/PDF/email/export/search/audit/Trust Spine
- Full legacy backend containment for `dr_v2_*` and alternate summary endpoints
