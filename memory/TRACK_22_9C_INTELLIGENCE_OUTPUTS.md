# TRACK 22.9C · Daily Report Intelligence Outputs · 🟢 SHIPPED · CERTIFIED (2026-02-06)

## Mandate
Surface the V3 Daily Report supervisor-accepted `ai_accepted_summary` and grounded
photo observations onto the three PM-facing outputs that were still blind to them:

1. **PDF renderer** (`_render_daily` in `pdf_render.py`).
2. **Auto-email HTML body** (`render_email_html` — daily-report kind only).
3. **PM Command Center / project detail** (canonical ODS facts, not raw DR docs).

Do NOT rebuild the PDF or email templates from scratch. Do NOT change routing,
audit, or recipient logic. Do NOT expose AI provider names or raw metadata.
Historical reports and V1 fallbacks must render byte-identical to pre-22.9C.

## Delivered
### 1 · PDF
- Helper `_render_intelligence_section(d)` (already-defined from previous session)
  now wired inside `_render_daily`. Renders as `10a · Operational Intelligence
  Summary` between `10 · Photos` and `11 · Signature`. Returns `""` when no
  accepted summary AND no photo observations exist — section is fully skipped
  for legacy reports.
- Emits: source label (`Supervisor accepted` / `Supervisor edited` /
  `Fallback summary`), the accepted narrative, and up to 12 grounded photo
  observation tags + 4 captions with `requires supervisor confirmation` qualifier.
- Provider / model / `latency_ms` / `provider_masked` / `edited_by_user` /
  `deterministic` never appear in rendered output.

### 2 · Email
- `render_email_html(kind="daily-report", record)` injects a compact
  operational-intelligence excerpt block above the "The full … is attached as a
  PDF" line. Excerpt truncated at ~280 chars with `…` cue + `Full narrative in
  attached PDF` sub-line. Up to 6 unique tag chips.
- Non-daily-report kinds (`meeting`, `incident`, `equipment-inspection`,
  `qaqc`, `generic`) never sprout the block, even if the record incidentally
  carries the field.
- Legacy daily reports (no `ai_accepted_summary`, no `photo_intelligence`)
  render the email body byte-identical to pre-22.9C output.

### 3 · PM Surfaces
- **New endpoint** `GET /api/ods/pm/projects/{project_id}/operational-intelligence`
  reads canonical `operational_facts` — specifically `day_summary_fact` +
  `photo_evidence_fact` rows. Never scrapes raw `daily_reports`.
- Returns `{summaries[], photo_observation_tags[], photo_facts_scanned}` with
  ~280-char excerpt per summary, `meta_source` (`supervisor_accepted` /
  `supervisor_edited`) and case-insensitive de-duplicated tag counts. Provider /
  raw meta never emitted.
- **Attention-feed hint** — `_attention_items()` now surfaces an
  `operational_summary` bucket (one row per project, newest first, ~200-char
  excerpt) alongside safety/quality/delay/readiness. Read via existing
  `/api/ods/pm/attention` + `/api/ods/pm/projects/{id}/attention` +
  `/api/ods/admin/attention` — zero new route.
- **PM Command Center page** (`PmOperationalIntelligence.jsx`):
  - Horizon 3 grid renders a 5th `AttentionList` when
    `items.operational_summary` is non-empty
    (`testid=pm-attention-operational-summary`).
  - New `OperationalIntelligenceCard` component below Horizon 3 renders
    summaries + photo tags for the top-project (by labor hours). Card auto-hides
    when both arrays are empty.
- **Frontend API helper** `fetchPmProjectOperationalIntelligence()` in
  `lib/odsIntelligenceApi.js`.

## Backward compatibility (locked by pytest)
- `_render_intelligence_section({legacy})` → `""` (byte-parity for historical PDFs).
- Legacy daily-report email → no intel block; canonical "attached as a PDF" line intact.
- Non-daily-report kinds → never render the block.
- Rendered HTML never contains: `openai / anthropic / claude / gemini / gpt- /
  sonnet / opus / haiku / nano banana / llm / latency_ms / provider_masked /
  model_masked / deterministic / edited_by_user`.
- PM endpoint body contains `day_summary_fact` + `photo_evidence_fact` + `COLL_FACTS`
  but **never** `db["daily_reports"]` or `'daily_reports'`.

## Tests
- **17 new lock assertions** in
  `tests/test_track_22_9c_intel_outputs.py`:
  - PDF: helper exists, `_render_daily` calls it under a guard, legacy returns
    empty, positive render carries excerpt + tags, provider/meta never leak,
    supervisor-edited label, photos-only path renders block.
  - Email: excerpt present + tags + full-PDF cue; legacy omits block; non-daily
    kinds omit block; long summary truncates with `…`.
  - PM surface: endpoint registered, reads canonical facts only, attention
    bucket present without raw-meta keys; frontend helper + card component +
    page wiring present.
- **Regression 46/46 across 22.9A + 22.9B + 22.9C**.
- **Broader regression 111/111 across 22.9 + 23.1 + 23.3 + DR-CUTOVER**.
- **Live smoke**:
  - `GET /api/ods/pm/projects/20-07/operational-intelligence` → 200 with correct
    envelope shape.
  - `GET /api/ods/pm/attention` → returns 5 bucket keys including
    `operational_summary`.
  - Synthetic `render_record_pdf("daily-report", …)` with intel fields → 1.32 MB
    valid PDF (`%PDF` magic bytes); without intel → 1.32 MB parity PDF.
  - `render_email_html` with intel → excerpt + tags present, provider hidden;
    without intel → block absent.
- **UI smoke** at `/pm/operational-intelligence` (1440×900) → renders cleanly;
  card correctly self-hides when no V3-accepted summaries exist yet in preview.

## Files changed
- `backend/pdf_render.py` (2 additive blocks: `_render_daily` call, `render_email_html` excerpt).
- `backend/routes/ods_intelligence.py` (+ new PM endpoint, + `operational_summary`
  bucket in `_attention_items`).
- `frontend/src/lib/odsIntelligenceApi.js` (+ helper).
- `frontend/src/pages/PmOperationalIntelligence.jsx` (+ intel state, + card mount,
  + 5th AttentionList).
- **New** `frontend/src/components/ods/OperationalIntelligenceCard.jsx`.
- **New** `backend/tests/test_track_22_9c_intel_outputs.py` (17 assertions).

## Verdict
🟢 **GO** — Track 22.9C closes the highest-ROI gap surfaced by the Track 23.0
Constitutional Audit (`ai_accepted_summary` never reached PDF/email/PM screen).
V1 rollback / historical reports remain byte-parity. Next up:
🔵 **Track 23.2** — PDF/email field-layout alignment for V3-specific cost codes
and combined safety/delay gates (deferred per prior directive).
