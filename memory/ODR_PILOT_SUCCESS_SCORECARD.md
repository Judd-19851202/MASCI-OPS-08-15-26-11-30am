# M0.35 · ODR Pilot Success Scorecard

_Phase V.1 · 2026-05-29 · pilot evaluation framework · aggregate-only._

This scorecard defines how we will judge the M1 pilot. Every metric
is **aggregate-only**. No individual employee is ever scored.

## Adoption (does the field actually use it?)

| Metric | Source | Target (pilot) |
|---|---|---|
| Completion rate | `submit_success / (session_start)` from `/api/odr/observation/summary` | ≥ 75% |
| Abandonment rate | `abandoned / session_start` | ≤ 25% |
| Average completion duration | `average_submit_duration_s` | ≤ 9 minutes (540s) |
| Mobile vs desktop split | `by_device.phone / total` | ≥ 70% phone |
| Bilingual usage | `by_language.es / total` | ≥ 15% (if Spanish-speaking foremen are in pilot) |
| Coaching engagement | `coaching_engagement_count / submit_success` | ≥ 30% (foremen open coaching at least 1 in 3 ODRs) |
| Draft resumption | `draft_resumed / session_start` | ≥ 5% (offline rescue works) |

## Quality (do the records carry real information?)

| Metric | Source | Target |
|---|---|---|
| Photo completeness | photos_added_count / submit_success | ≥ 3 photos per ODR avg |
| Production completeness | % of ODRs with at least 1 production_segment | ≥ 95% |
| Manpower completeness | % of ODRs with at least 1 manpower row | ≥ 95% |
| Tomorrow plan completeness | % of ODRs with `tomorrow.planned_work.text` non-empty | ≥ 90% |
| Amendment rate | `amendment_volume / submitted_count` | ≤ 0.10 (1 amendment per 10 ODRs) |
| Hard-stop block rate | `submit_blocked / (submit_blocked + submit_success)` | ≤ 0.05 |
| Readiness=ready at submit | % of submits with `readiness.score=ready` | ≥ 95% |

## Operational value (do consumers actually consume?)

| Metric | Source | Target |
|---|---|---|
| FL Center daily visits | `fl_inbox_opened` / pilot active days | ≥ 1 visit per active super per workday |
| FL record-deep-dive rate | `fl_record_opened / fl_inbox_opened` | ≥ 30% |
| PM panel daily visits | `pm_panel_opened` / pilot active days | ≥ 1 visit per PM per workday |
| Chronology usage | `chronology_opened / fl_inbox_opened` | ≥ 10% |
| PDF generation frequency | `pdf_render_count / submitted_count` | ≥ 1.0 (every ODR generates at least one PDF) |
| Public link usage (when CEI shares it) | `public_pdf_downloads / public_links_minted` | qualitative — operator review |
| Public viewer engagement | `public_viewer_opened / public_links_minted` | ≥ 0.5 (half of minted links are visited) |

## Sentiment (do operators trust the system?)

Sentiment is gathered through OPERATOR INTERVIEW, not telemetry.
The pilot operator runs a **structured 5-question survey** at week 2
and week 4 of pilot:

### Foreman survey (5 questions · 5-point scale)

1. The platform is faster than the old daily report.
2. The bilingual toggle helps me write what I need to write.
3. The coaching tips feel like a superintendent advising me, not a manager scoring me.
4. The trust banner makes me confident my report won't be edited behind my back.
5. I would rather use this than the legacy daily report.

### Superintendent survey (5 questions)

1. The FL ODR Center surfaces what I need to see, with no noise.
2. I can amend a report after 24h with the audit trail I expect.
3. Chronology gives me what happened, not just what was reported.
4. Readiness signals catch the right things without false alarms.
5. I would defend any of these PDFs to a CEI.

### PM survey (5 questions)

1. The PM panel answers "what risk exists today" within 30 seconds.
2. I can see contractual exposure (extra work, delays, safety) without drilling.
3. I never feel like I should be authoring or editing — only consuming.
4. The PDFs I send to CEI are clean.
5. The amendment authority matrix matches how my projects actually run.

## Evaluation cadence

| Week | Activity |
|---|---|
| Week 0 | Pilot starts · baseline telemetry capture |
| Week 1 | Daily aggregate review (no scoring · no per-foreman drill) |
| Week 2 | First survey · scorecard checkpoint 1 |
| Week 3 | Mid-pilot adjustment if any metric below threshold |
| Week 4 | Final survey · scorecard checkpoint 2 · M1 → general-availability decision |

## What this scorecard NEVER does

- ❌ Per-foreman ranking
- ❌ "Top 5 longest submit duration" surfacing
- ❌ Comparing one project's amendment rate against another publicly
- ❌ Naming individuals in any aggregate
- ❌ Coaching-acceptance correlated with later amendments per foreman

These are explicit doctrine violations per
`ODR_ADOPTION_OBSERVATION_PLAN.md`.

## Audience Projection alignment

Per the M0.35 audience projection doctrine, the scorecard's
aggregate metrics are **internal only** (Operations Leadership +
Admin). They never appear on:

- Public viewer
- External PDF
- PM panel (PM sees per-project metrics, not platform aggregates)
- Foreman entry surface

## Verdict

🟢 **PILOT SUCCESS SCORECARD DEFINED.** Adoption · Quality ·
Operational Value · Sentiment — measurable, aggregate, doctrine-
respecting. The pilot has a clear bar to clear.

_End of ODR_PILOT_SUCCESS_SCORECARD.md._
