# DR-CUTOVER-002 · Executive Summary

**Track:** DR-CUTOVER-002 · Daily Operational Summary inside the real Daily Report
**Date:** 2026-02
**Status:** ✅ Delivered — 22 new backend lock tests + full end-to-end regression, 100%/100% via testing agent.

---

## What shipped

One new **optional** section — *Daily Operational Summary* — mounted
inside the existing `NewDailyReport.jsx` at `/daily/submit`, immediately
before the sign-off band. It reuses the form's own state; nothing else
in the workflow changed.

Alongside the UI section, two additive backend endpoints:

- `POST /api/daily-reports/summary/draft` — composes a preview from
  the current (possibly unsaved) payload using **only** literal values
  from that payload. Never invents facts. Never makes a live LLM call.
  If AI capability is off for the tenant → returns
  `{ok:true, enabled:false, reason_disabled:"..."}` — never a 5xx.
- `POST /api/daily-reports/{report_id}/summary/accept` — patches a
  small set of `daily_operational_summary_*` fields onto the existing
  daily report doc. Emits a best-effort `intelligence_fact` via ODS
  (idempotent — supersedes the previous is_current fact).

## Zero drift on absolutely protected surfaces

- `POST /api/daily-reports` submit path — **untouched.**
  Regression lock: `test_daily_reports_route_still_ignorant_of_ai_summary`.
- HR crew time (`masci_crews[]`) — **untouched.** No summary code
  path reads or writes crew rows. Lock:
  `test_accept_persists_summary_onto_daily_report_doc` checks
  `masci_crews` is byte-identical after summary acceptance.
- Email pipeline — untouched; no change to `schedule_auto_email`
  callsite in `register_daily_reports_routes`.
- PDF renderer — untouched; the summary is stored on the report doc
  as `daily_operational_summary` for future renderer inclusion
  (documented in `DR_CUTOVER_002_HR_EMAIL_PDF_PROTECTION.md`).
- ODS ingestion (DR-CUTOVER-001) — untouched. Summary acceptance
  emits an *additional* `intelligence_fact`; it never duplicates the
  existing `labor_fact` / `photo_evidence_fact` emissions.
- Safety fields, incident gates, excavation gates — untouched.
- Photos, min-6 rule, upload flow — untouched.
- Signature, sign-off band — untouched.
- EN/ES language toggle — untouched; the summary section respects
  the form's `dr_language` state.
- V2 shell — **not exposed.** No `/daily-report/v2` nav entry.

## Field UX

The supervisor sees a compact, familiar section with:

- **Title:** "Daily Operational Summary" (mono/caps kicker: "Optional").
- **Helper copy:** "Optional. Draft a professional summary of today's
  work, then review and edit before submitting."
- **Textarea** — always usable; supervisor can type their own summary
  even when AI assistance is not enabled.
- **Three buttons:** Draft Summary · Accept Summary · Clear.
- **Accepted badge** appears once accepted; textarea remains editable
  so the supervisor can still refine before final submit.
- **No AI vocabulary** anywhere: no "AI", "agent", "model", "provider",
  "token", or "cost" language ever surfaces. Enforced by lock test
  `test_field_ui_wire_response_contains_no_ai_agent_language`.

## AI optionality — the six-link gate

Every draft call routes through `resolve_ai_capabilities(db, tenant_id,
"daily_report_summary")` — the same resolver AI-CONFIG-001 shipped.
Any failed link short-circuits with a machine-readable code:

- `ai_gateway_disabled_global`
- `tenant_ai_disabled` (default state today for MASCI in preview)
- `module_disabled_global:daily_report_summary`
- `module_disabled_tenant:daily_report_summary`
- `no_provider_available`

Each maps to a **non-alarming** toast message in the UI —
"Summary assistance is not enabled. You may submit the report
normally." — never surfaces the internal code, never blocks submit.

## Test evidence

- **22/22 backend lock tests pass** in
  `/app/backend/tests/test_dr_cutover_002_daily_summary.py`.
- **6/6 live HTTP integration checks** via testing agent v3
  (draft disabled path · accept-404 · accept-422 empty · V1 submit
  regression · admin GET after submit · zero regression on
  AI-ADMIN-001 page).
- **Full frontend flow** verified: section renders in the right place,
  buttons present, disabled-path toast, manual-type + accept flow,
  no AI vocabulary anywhere on the page HTML.
- **Success rate:** backend 100% · frontend 100% · retest_needed:false.

## Files delivered

Backend
- `routes/daily_summary.py` (new — 2 endpoints + deterministic composer)
- `server.py` (+7 lines · router registration)
- `tests/test_dr_cutover_002_daily_summary.py` (new · 22 tests)

Frontend
- `components/daily-report/DailyOperationalSummarySection.jsx` (new)
- `pages/NewDailyReport.jsx` (+2 lines · import + one JSX mount)

Memory
- `AI_CUTOVER_002_EXECUTIVE_SUMMARY.md` (this file)
- `DR_CUTOVER_002_DAILY_SUMMARY_ARCHITECTURE.md`
- `DR_CUTOVER_002_ZERO_DRIFT_MATRIX.md`
- `DR_CUTOVER_002_HR_EMAIL_PDF_PROTECTION.md`
- `DR_CUTOVER_002_TEST_REPORT.md`

## Follow-ups (P2 — non-blockers)

- **Live-LLM polish path.** The composer today is deterministic. When
  AI providers are enabled per tenant, a future track can layer LLM
  polish on top of the composed text (never replacing it — always
  editing sentences composed from real evidence). Reserved integration
  point: the `draft_summary` endpoint returns the composed text; a
  future middleware wrapper can hand it to an LLM for style pass with
  the strict rule "never introduce a new fact".
- **PDF renderer inclusion.** Store is live; renderer mapping is a
  small follow-up in `dr_v2_pdf.py` — documented in
  `DR_CUTOVER_002_HR_EMAIL_PDF_PROTECTION.md`.
- **Email inclusion.** Same as PDF — data is stored; email template
  wiring is the follow-up.
