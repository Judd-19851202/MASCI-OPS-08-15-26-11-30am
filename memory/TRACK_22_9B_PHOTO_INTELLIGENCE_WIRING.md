# TRACK 22.9B — DAILY REPORT PHOTO INTELLIGENCE WIRING

**Status:** 🟢 GO / CLOSED (2026-02-06)
**Testing:** 14 lock tests + 54 regression tests · **68 passed**
**Scope:** V1 Daily Report only. Zero V2 resurrection. Zero duplicate storage.

---

## What shipped

Wired the existing photo intelligence analyzer into the V1 Daily
Report submit workflow **asynchronously**, using the option-C strategy
(BackgroundTasks first-pass + reconciler loop for retries).

- **New module** `services/photo_intelligence/pipeline.py`
  - `enqueue_report(db, report)` — inserts one pending job per attached
    photo into `dr_v1_photo_intel_jobs`, guarded by a composite unique
    index `(report_id, photo_id)` so duplicate submits never spawn
    duplicate jobs.
  - `process_report(db, report)` — first-pass analysis; fires from
    FastAPI `BackgroundTasks` after `db.daily_reports.insert_one`.
  - `reconcile_once(db)` — one reconciler pass; reclaims stale
    `in_progress` claims, retries `failed` / `pending` jobs whose
    `next_attempt_at` has arrived, respects `JOB_MAX_ATTEMPTS=5`.
  - `reconciler_loop(db, interval_s=60)` — long-running loop; started
    via a `scheduler-nonemail` lifecycle step. Kill switch:
    `DR_V1_PHOTO_INTEL_RECONCILER_ENABLED=false`.
  - `list_report_intelligence(db, report_id)` — read aggregator used
    by the new HTTP endpoint AND by the ODS enrichment path.

- **V1 submit hook** (`routes/daily_reports.py`)
  - Endpoint signature now includes `BackgroundTasks`.
  - After `insert_one` and ODS emission: `await enqueue_v1_report(...)`
    (fast — only inserts pending job docs) then
    `background_tasks.add_task(process_v1_report, db, dict(doc))`.
  - The enqueue-before-schedule ordering is CI-locked; guarantees the
    reconciler owns the retry contract even if the request-scope
    BackgroundTask is dropped (pod recycle, worker crash).

- **Read endpoint**
  - `GET /api/daily-reports/{report_id}/photo-intelligence` → returns
    `{report_id, photo_count, analyzed, pending, observations,
    narrative, photos}`. Observations always preserve
    `requires_supervisor_confirmation=true` from the analyzer.

- **Lifecycle steps** (`server.py`)
  - `_ensure_dr_v1_photo_intel_indexes` — `index-ensure` group.
  - `_seed_tenant_photo_intelligence_flag` — `seed` group; idempotently
    upserts `tenant_ai_capabilities.masci.photo_intelligence_enabled=true`.
    Verified live on preview DB (`version=11`).
  - `_start_dr_v1_photo_intel_reconciler` — `scheduler-nonemail` group.

- **ODS enrichment** (`services/ods_spine/ingest.py`)
  - New helper `_enrich_photo_evidence_facts(db, src_id, facts)`.
  - Called by `ingest_dr_v1_report` after the pure builder, before
    write. Merges `ai_tags` + `ai_caption` + confidence from analyzed
    photos onto each matching `photo_evidence_fact`. Best-effort: any
    read error leaves the pre-22.9B payload shape unchanged.

- **Frontend** (`components/daily-report/DailySummaryAssist.jsx`)
  - Before synthesizing the Draft Summary, best-effort fetch from
    `/daily-reports/{reportNumber}/photo-intelligence`. Adds a
    `photo_observations[]` array into the evidence bundle passed to
    the AI backend. Fully guarded — network failure returns `[]`
    silently; never blocks summary generation.

- **Deployment flag** — `AI_PHOTO_VISION_ENABLED=true` in
  `/app/backend/.env` (was `false`). Together with the tenant flag
  seed and the existing `AI_GATEWAY_ENABLED=true`, this lights up the
  capability resolver for `photo_intelligence` module.

## Doctrine compliance

- ✅ **Never blocks submit** — enqueue is a fast index-hitting write;
  actual analysis happens after the HTTP response returns.
- ✅ **Never blocks upload / summary** — reads from the intel endpoint
  have their own timeout and empty fallback in `DailySummaryAssist`.
- ✅ **No duplicate storage system** — intel rows keep living in
  `dr_v2_photo_intelligence` (the existing V2 store). Only the job
  queue collection `dr_v1_photo_intel_jobs` is new.
- ✅ **No V2 shell resurrection** — every V2 route file was left
  untouched. Only the shared analyzer + store are reused.
- ✅ **Grounded only** — the analyzer's strict prompt is unchanged;
  every observation still carries `requires_supervisor_confirmation`.
- ✅ **Gemini direct key ignored** — task router still points
  `photo_vision` at `openai:gpt-5.2-vision`; the pipeline falls back
  through `has_key()` gates and, if no key is present, writes a
  placeholder intel row with `analysis_status="unavailable"` and
  closes the job as `unavailable` (never retried).
- ✅ **Failures logged, not surfaced** — every exception path in
  `pipeline.py` is wrapped; `process_report` cannot raise; the field
  UI never sees a photo-intel error.

## Regression envelope

`test_track_22_9b_photo_intel_wireup.py` — 14 new lock tests:

1. Module surface / exports.
2. Read endpoint registered.
3. BackgroundTasks scheduling (order: enqueue → add_task).
4. Server-side reconciler + seed step registration.
5. First-pass writes intel + closes jobs.
6. No-photo report is a no-op.
7. **Reconciler recovers lost BackgroundTasks** (the option-C mandate).
8. Idempotency: repeat calls create no new rows.
9. Enqueue never duplicates jobs.
10. AI disabled → placeholder + `unavailable` status.
11. Analyzer exception → job `failed`, no crash.
12. Read endpoint aggregates observations with confirmation guard.
13. Frontend evidence bundle wires `photo_observations` from the API.
14. Tenant seed step targets `tenant_id="masci"`.

Total: 68/68 across 22.9A + 22.9B + DR-CUTOVER-001 + DR-CUTOVER-002.

## Files touched

- **New:** `backend/services/photo_intelligence/pipeline.py`,
  `backend/tests/test_track_22_9b_photo_intel_wireup.py`.
- **Modified:** `backend/routes/daily_reports.py`,
  `backend/server.py`, `backend/services/photo_intelligence/__init__.py`,
  `backend/services/ods_spine/ingest.py`,
  `frontend/src/components/daily-report/DailySummaryAssist.jsx`,
  `backend/.env` (single flag flip).

## What's NOT in scope (deferred to 22.9C)

- PDF renderer + PM screen consuming `day_summary_fact` + photo intel
  observations directly. Reads are available via the new endpoint;
  wiring them into the emailed PDF template is Track 22.9C.
