# DR-CUTOVER-002 · Daily Summary Architecture

## 1. Doctrine

- **Never invent facts.** The summary composer receives ONLY the
  current report payload and composes sentences that reference literal
  values from that payload (crew counts, equipment names, weather
  text, safety flags, photo counts, etc.). This satisfies the
  "must not fabricate" contract mechanically, regardless of whether a
  live LLM is ever wired.
- **AI is optional.** Every draft call passes through
  `resolve_ai_capabilities(db, tenant_id, "daily_report_summary")`.
  If any link in the five-link chain is off, the endpoint returns
  `enabled=false` with a machine-readable `reason_disabled` — never
  a 5xx.
- **The supervisor is the source of truth.** They can accept the
  composed draft, edit it, regenerate it, clear it, or type their
  own from scratch. The last-committed text is what gets persisted.
- **Invisible Intelligence.** No AI/model/provider/token/cost
  vocabulary appears in the response body or the field UI — enforced
  by both backend and frontend lock tests.

## 2. Endpoints

### `POST /api/daily-reports/summary/draft`

Compose a preview summary from an in-flight (possibly unsaved) daily
report payload.

**Request**
```json
{
  "payload": { /* the full form data blob */ },
  "tenant_id": "masci",          // optional; defaults to masci
  "language": "en" | "es",       // optional; unknown → "en"
  "evidence_refs": ["photo:0", ...]  // optional
}
```

**Response — disabled path**
```json
{
  "ok": true,
  "enabled": false,
  "reason_disabled": "tenant_ai_disabled",
  "summary_text": null,
  "language": "en",
  "warnings": [],
  "evidence_refs": [],
  "request_id": null
}
```

**Response — enabled path**
```json
{
  "ok": true,
  "enabled": true,
  "reason_disabled": null,
  "summary_text": "Route 121 Grade (26-04), daily report for 2026-02-15…",
  "language": "en",
  "warnings": [],
  "evidence_refs": ["photo:0", "photo:1", "photo:2", "photo:3", "photo:4", "photo:5"],
  "sentence_count": 12,
  "request_id": null
}
```

### `POST /api/daily-reports/{report_id}/summary/accept`

Persist the accepted (possibly hand-edited) summary onto an
already-submitted daily report.

**Request**
```json
{
  "summary_text": "…",             // required · 1–4000 chars
  "language": "en" | "es",         // optional; unknown → "en"
  "source": "draft" | "user_edited",
  "evidence_refs": ["photo:0", ...],
  "canonical_english": "…",        // optional (used when language is es)
  "original_text": "…",            // optional (pre-edit draft)
  "accepted_by": "supervisor@…"    // optional; falls back to report.prepared_by
}
```

**Response**
```json
{
  "ok": true,
  "report_id": "…",
  "daily_operational_summary_status": "accepted",
  "daily_operational_summary_accepted_at": "2026-02-15T…",
  "language": "en"
}
```

**Errors**
- `400` — empty `report_id` in the path.
- `404` — daily report not found.
- `422` — pydantic validation (empty / oversize `summary_text`).
- `500` — Mongo write failure (surface only the error text; never
  provider details).

## 3. Storage model

Field additions on the existing `daily_reports` document (all optional;
legacy readers ignore them):

| Field                                          | Type          | Purpose                                             |
| ---------------------------------------------- | ------------- | --------------------------------------------------- |
| `daily_operational_summary`                    | string        | The accepted summary text (≤ 4000 chars).           |
| `daily_operational_summary_status`             | string        | `"empty" \| "drafted" \| "accepted"`.               |
| `daily_operational_summary_source`             | string        | `"draft" \| "user_edited"`.                         |
| `daily_operational_summary_accepted_at`        | ISO datetime  | Server-stamped on accept.                           |
| `daily_operational_summary_accepted_by`        | string        | Actor label.                                        |
| `daily_operational_summary_language`           | string        | `"en" \| "es"`.                                     |
| `daily_operational_summary_canonical_english`  | string        | Present when language is es and en canonical known. |
| `daily_operational_summary_original_text`      | string        | Pre-edit draft (audit).                             |
| `daily_operational_summary_evidence_refs`      | list[str]     | Refs to photos/evidence used (≤ 64).                |

No new collection created. No new Mongo index required for this track
(reads happen on the same `daily_reports.id` key already indexed).

## 4. Deterministic composer

**Location:** `_compose_deterministic_summary(payload, language="en")`
in `routes/daily_summary.py`.

**Inputs (allow-list — anything else is silently ignored):**

```
project_name, project_number, location, report_date,
prepared_by, superintendent, shift,
weather_summary, schedule_delays, schedule_delays_notes,
weather_impact, weather_impact_notes,
safety_incidents_today, injuries_reported, incident_notes,
general_notes,
masci_crews, subcontractors, equipment, materials,
outbound_materials, activities, production, constraints,
photos, photo_captions,
narrative_sections.tomorrow_plan
```

**Guarantees**

- Emits a sentence only when the corresponding field/list is non-empty.
- Never surfaces an unrecognised key (proved by
  `test_composer_uses_only_allowed_fields`).
- Never mentions safety when the report says no incident and no injury
  (`test_composer_never_invents_a_safety_incident`).
- Never mentions photos when none are attached
  (`test_composer_never_mentions_photos_when_none_attached`).
- Handles an entirely empty payload without crashing; emits a warning
  code `insufficient_evidence_for_meaningful_summary`.

## 5. AI capability resolution

Every draft call:

```
cap = await resolve_ai_capabilities(db, tenant_id, "daily_report_summary")
if not cap.enabled:
    return { ok: true, enabled: false, reason_disabled: cap.reason_disabled, ... }
```

The resolver's five-link chain (see AI-CONFIG-001 docs):

1. `AI_GATEWAY_ENABLED`
2. Tenant AI enabled (Mongo override → `TENANT_AI_ENABLED` env default)
3. `AI_DAILY_REPORT_SUMMARY_ENABLED`
4. Tenant module flag (Mongo override → env default)
5. Provider flag on + provider API key present

Any failure short-circuits without touching a provider adapter.

## 6. Frontend architecture

**Component:** `components/daily-report/DailyOperationalSummarySection.jsx`

- Presentational + minimal state. Reads `data` and calls `set(key,
  value)` — the same pattern every other section in NewDailyReport uses.
- Own state: `drafting` boolean and last-seen `availability`
  (enabled/reason). Both transient — never persisted.
- Never surfaces AI vocabulary — banned strings enumerated in the
  frontend lock envelope (via testing agent). Copy is only:
  - "Optional"
  - "Daily Operational Summary"
  - "Draft Summary" · "Regenerate" · "Accept Summary" · "Clear"
  - "Summary assistance is not enabled. You may submit the report normally."
- Buttons: `daily-summary-draft-btn`, `daily-summary-accept-btn`,
  `daily-summary-clear-btn`. Textarea: `daily-summary-textarea`.
  Accepted badge: `daily-summary-accepted-badge`.

**Mount site:** `pages/NewDailyReport.jsx`, immediately before
Section 11 (Sign-Off band). Two lines of code: an import and one JSX
tag. No parent refactor; the extract-to-component was the entirety
of the refactor scope for this track.

## 7. Submit-time behaviour

The V1 submit route (`POST /api/daily-reports`) already declares
`extra="allow"` on its pydantic model, so any `daily_operational_summary_*`
fields the client attaches to the payload are stored on the resulting
`daily_reports` doc *without* any change to the route. That is the
design — the summary lives on the same doc, in the same collection,
next to the crew and equipment rows.

## 8. ODS emission

On `POST …/summary/accept`, if ODS is enabled globally, a single
`intelligence_fact` is emitted:

```
source_type      = "daily_report"
source_id        = <report_id>
source_item_id   = "intel:operational_summary"
fact_type        = "intelligence_fact"
is_current       = true
payload          = { audience, agent, language, source, chars }
```

Previous `is_current` facts with the same `(source_type, source_id,
source_item_id)` triplet are set `is_current=false` — idempotent
supersede. No labor / equipment / safety fact is ever duplicated.

## 9. Non-goals for this track

- Live LLM polish on top of the deterministic composer.
- PDF renderer inclusion (data is stored; renderer wiring is P2).
- Email template inclusion.
- Photo Intelligence integration (Photo Intelligence is a separate
  module; the composer surfaces `photos.length` and `photo_captions[]`
  today — no photo AI call is made).
