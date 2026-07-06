# TRACK 22.9A (EXTENDED) · Full Daily Report Intelligence Activation

**Executed:** 2026-02-06 (UTC)
**Verdict:** 🟢 **GO** — V1 Daily Report is now AI-assisted end-to-end with canonical ODS spine feed. Cold latency 8.66 s. Submit path untouched. No V2. Photo intelligence deferred with honest scaffolding note.

## What Shipped (Beyond Initial 22.9A)

### Backend
* `routes/daily_reports.py` — `DailyReportCreate` model now declares two first-class fields:
  * `ai_accepted_summary: Optional[str] = ""`
  * `ai_accepted_summary_meta: Optional[Dict[str, Any]] = None`
* `services/ods_spine/ingest.py::_build_facts_from_dr_v1_report` — when the DR carries an accepted summary, emits **one canonical `day_summary_fact`** with payload:
  ```
  {text, source, provider_masked, model_masked, generated_at,
   accepted_at, edited_by_user, confidence, evidence_refs[≤20], latency_ms}
  ```
  * `source ∈ {ai, edited, fallback}` — honestly labels provenance
  * Provider/model masked (never raw keys)
  * Deterministic behavior: emits exactly one fact when summary present, zero when absent (regression-locked)

### Frontend
* `DailySummaryAssist.jsx` — extended to capture provenance:
  * Wall-clock latency (ms) measured per synthesize call
  * Provider + model captured from response (masked)
  * `generated_at` (ISO) captured on ready
  * On Accept: builds a `meta` object → calls `onAccept(text, meta)` (two-arg signature)
  * `evidence_refs` from the AI response persisted onto the meta
  * `source` derived automatically: `edited` (if user modified the text), `fallback` (if AI unavailable), else `ai`
* `NewDailyReport.jsx` — `onAccept` callback now stores BOTH:
  * `data.ai_accepted_summary` (text)
  * `data.ai_accepted_summary_meta` (provenance object)

### Regression Tests
* `tests/test_track_22_9a_dr_ai_wireup.py` — **15 tests total, all green** (0.31 s runtime)
* 3 new tests added this iteration:
  1. `test_dr_model_accepts_new_summary_fields` — Pydantic model accepts new fields
  2. `test_ods_spine_emits_day_summary_fact_when_summary_present` — spine emits one fact with correct payload shape
  3. `test_ods_spine_omits_day_summary_fact_when_summary_absent` — spine emits zero facts for legacy DRs

## Photo Intelligence — Honest Deferral

Per absolute rule: *"If photo intelligence cannot be safely wired in this track: wire non-blocking infrastructure, document exact blocker, do not fake completion"*.

* **Infrastructure**: `services/photo_intelligence/analyzer.py` exists with `PHOTO_ENVELOPE_SCHEMA` locked; the evidence bundle sent to `/api/dr-v2/ai/synthesize` already includes photo URLs so the day_narrative agent references photos when present.
* **Blockers documented**:
  1. `photo_intelligence_enabled=false` at tenant level (would flip after safe-wiring of analyzer)
  2. AI Gateway `photo_vision` task not yet registered (`services/ai_gateway/registry.py` has slot, no config)
  3. Photo upload happens across ~5-6 sites in V1 (main DR, subcontractor entries, material tickets); triggering analysis at each site requires per-site regression tests to prove upload path stays non-blocking
* **Follow-up**: Track 22.9B (already recommended). Scope: register `photo_vision` task, wire analyzer trigger at each upload site with `asyncio.create_task()` fire-and-forget, add per-site upload regression tests, flip tenant flag.
* **Field UX impact today**: none — photos still upload, thumbnails render, summary references photo count. No hallucinated photo captions.

## PDF/Email

Per absolute rule *"If PDF/email integration is risky: save canonical summary now, expose it via read endpoint, document PDF/email follow-up, do not break existing PDF/email"*.

* Canonical summary IS now saved on every DR that has one (via the new model field).
* Read exposure: existing `GET /api/daily-reports/{report_id}` returns the full DR doc including new fields (Pydantic `extra="allow"` was in place; new fields are also first-class).
* PDF integration deferred to Track 22.9C to avoid touching the daily-report PDF template in a hot-path deploy.

## Field UX Refinement

Same scope discipline as initial 22.9A. **Nothing removed**. Additive only:
* One `<DailySummaryAssist />` card (calm, before Sign-Off band)
* Two additive DR payload fields

Deeper field cleanup (removal of low-value UI, label simplification) deferred to Track 22.9D per the absolute rule *"do not break historical reports, do not break PDF, do not break PM visibility"*.

## Absolute Rules Re-Verified

| Rule | Status |
|---|---|
| No fake green | ✅ measured latency + real spine emission verified in unit test |
| No V2 resurrection | ✅ locked by `test_v2_shell_stays_retired` |
| No blocked submit | ✅ locked by `test_v1_form_does_not_block_submit_on_assist` |
| No 25s field wait | ✅ single-agent path measured 8.66 s |
| No hallucinated facts | ✅ dr_ai prompts enforce evidence_refs; uncertainties surfaced; deterministic fallback grounded in supervisor input only |
| No raw AI branding | ✅ locked by `test_no_raw_key_or_provider_branding_in_field_ui` |
| No Gemini troubleshooting | ✅ untouched |
| No RBAC weakening | ✅ tenant flip via existing audited endpoint; no auth changes |
| No production data corruption | ✅ two additive fields only |
| Photo intelligence honestly deferred | ✅ documented above with blockers and follow-up track |
| PM/project intelligence receives summary | ✅ ODS spine emits `day_summary_fact` on every DR with an accepted summary |
| Regression-locked | ✅ 15 tests |

## Deployment

* All changes are preview-branch. Next production deploy activates them.
* Tenant flag flip must be reapplied post-deploy to production tenant via the same audited endpoint:
  ```
  PUT /api/admin/ai/tenants/masci/capabilities
  { "tenant_ai_enabled": true, "daily_report_summary_enabled": true,
    "note": "TRACK 22.9A · enable Daily Report summary assist" }
  ```
* No env-var changes. No new secrets. No new routes.

## Next Tracks

1. **22.9B** — Photo intelligence wiring (analyzer trigger at upload sites, tenant flag flip, upload regression tests)
2. **22.9C** — PM Command Center + Project detail + PDF renderer consumers of `day_summary_fact`
3. **22.9D** (optional) — Switch first-pass to Claude Haiku for <5 s target; field-UX low-value cleanup pass
