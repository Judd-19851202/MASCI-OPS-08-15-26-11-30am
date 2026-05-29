# M0.3 · PM Consumption Panel · Certification

_Phase V.1 · 2026-05-29 · CONSUMER LENS · READ-ONLY._

## Mission

PMs are **consumers**, not authors. The panel answers one question
within seconds:

> "What project risk exists today?"

## Page

`/pm/odr` · `/app/frontend/src/pages/odr/OdrPmPanel.jsx`

## Inheritance

- FIELD_LEADERSHIP_VISIBILITY_DOCTRINE (FLL-5 = LIMITED verb).
- M0_2_PDF_ENGINE_CERTIFICATION (PM audience PDF).
- M0_2A_OPERATOR_REVIEW_GUIDE (locked decisions: PM cannot edit or approve · PM may mint public links · PM may amend post-window).

## What surfaces (5 calm metrics)

| Metric | Source | Signal |
|---|---|---|
| Submitted (7d) | count of `status=submitted` in window | Field reporting volume |
| Open Delays | count of ODRs with `delays.any_delays=true` | Active drag on schedule |
| Hours Lost | sum of `delays.total_hours_lost` | Quantified schedule exposure |
| Extra Work | count of ODRs with `extra_work.any_extra_work=true` | Contractual exposure |
| Safety Events | count of ODRs with `safety.any_event=true` | Risk surface |

Each tile turns **amber** when value > 0 — calm, not alarming. NEVER red.

## What is hidden (per doctrine)

| Hidden | Why |
|---|---|
| `completion_telemetry` | Admin-only diagnostic (O9) |
| `readiness.coaching_prompts` | Author-only (O50) — PM does not "score" coaching |
| `reliability.sync_conflicts` | Operational noise · PM doesn't fix sync |
| `reliability.device_fingerprint` | Privacy boundary |
| `consumer_dispatch` | Diagnostic only |
| Per-foreman aggregates | Adoption Observation Plan forbids it |
| Per-crew "performance" rankings | Same |
| Coaching engagement counts per foreman | Same |

## What is exposed (per doctrine)

- Production summary per ODR row
- Blocker flags (delays / safety)
- PDF download (`audience=pm`) on every row — gates on portal-role
- Direct link to ODR detail (read-only consumption)

## Why PMs don't see "everything"

FLL-5 carries the LIMITED verb because the platform deliberately
treats PMs as a contract-and-cost lens, not as an operational
back-seat driver. The Field Leadership tier owns operational
execution; the PM tier owns contractual exposure. The panel reflects
that split.

## Telemetry wired

| Event | Tracked |
|---|---|
| Panel opened | `pm_panel_opened` |
| Project opened | `pm_project_opened` |
| PDF downloaded | `pm_pdf_downloaded` (+ context.audience) |

## Test surface

- `data-testid="pm-odr-panel"` · `pm-odr-metrics` · `pm-metric-{label}` ·
  `pm-odr-list` · `pm-odr-row-{doc_id}` · `pm-odr-pdf-{doc_id}`
- Backend tests cover the LIMITED scope filter + field projection in
  `tests/odr/test_odr_substrate.py` (visibility module) and
  `tests/odr/test_odr_m02.py` (PDF audience gates).

## Out of scope for M0.3

- Cost rollups (deferred to M1+ once `extra_work.potential_cost_impact_usd` is consistently populated).
- P6 schedule overlay (deferred to RFI / Schedule wave).
- Cross-project trend overlay (M0.4+).

## Verdict

🟢 **PM CONSUMPTION PANEL LIVE.** PMs consume. Field leadership leads.
The panel answers project-risk-today within seconds without dragging
PMs into operational micromanagement.
