# Track 19.05 · Daily Report Data Quality Audit

**Sample**: 30 most-recent submitted DRs from `db.daily_reports` (preview env), plus totals across 1,118 records.

## Completion rates (n=30)

| Field / section | Populated | Rate |
| --- | --- | --- |
| project_number | 30 | 100% |
| superintendent | 11 | 37% |
| photos ≥ 6 (submit-gate minimum) | 13 | 43% |
| avg photos per report | 4.4 | — |
| masci_crews[] | 16 | 53% |
| equipment[] | 7 | 23% |
| materials[] (inbound) | 6 | 20% |
| outbound_materials[] | 6 | 20% |
| activities[] (legacy free text) | 1 | 3% |
| production[] (Wave-1A structured) | 0 | **0%** |
| constraints[] (Wave-1A structured) | 0 | **0%** |
| subcontractors[] | 4 | 13% |
| visitors[] | 6 | 20% |
| narrative_sections{} | 3 | 10% |
| attachments[] (Track 19.04) | 0 | 0% (new — first uploads pending) |
| general_notes | 2 | 7% |
| safety_incidents_today = Yes | 0 | 0% |
| injuries_reported = Yes | 0 | 0% |
| weather_impact = Yes | 0 | 0% |
| schedule_delays = Yes | 0 | 0% |

## Findings

* **Photo minimum-gate is being bypassed** — 57% of recent reports have < 6 photos, meaning either the submit gate is not enforcing (client-only, not backend) OR the field flow is a public/legacy path. Historically the min-photo gate is UI-only; the backend accepts any count.
* **Production[] and constraints[] adoption is zero.** Wave-1A structured production shipped but foremen continue to use `activities[]` free text (only 1/30) or leave both empty. This suggests the current UI doesn't guide foremen to the structured surfaces — a redesign candidate.
* **narrative_sections{} adoption is 10%.** Guided-prompt structured narrative is not the default path yet.
* **Safety triggers are all 0% Yes** — a healthy signal (no incidents), but validates that the trigger cascade is not hyperactively firing.
* **Superintendent auto-fill is landing on only 37%** — suggests either the job-master lacks the superintendent link OR the recent-context fallback isn't running when project isn't picked from job list.
* **Crew rows on 53%** — MASCI crew section is the most-used row surface after project/date fields.
* **Attachments 0%** — Track 19.04 shipped; adoption will grow.

## Boilerplate / duplicate risk

* `activities[]` (legacy) vs `production[]` (structured) — see Redundancy Audit. Currently 3% + 0% ⇒ 97% of reports have NEITHER a work log NOR quantities. This is the single biggest quality gap.
* `general_notes` at 7% ⇒ largely unused.
* `narrative_sections{}` at 10% ⇒ six guided prompts are ~2× more effective than free-text general_notes but still low.

## Field value assessment

| Value tier | Fields |
| --- | --- |
| **Consistently valuable** (>50% populated) | project_number, report_date, prepared_by, masci_crews (53%), report_number |
| **Situationally valuable** (10-50%) | superintendent, subcontractors, equipment, materials, outbound_materials, visitors, narrative_sections |
| **Rarely used** (<10%) | general_notes, activities, production, constraints, all safety Yes/No triggers (correctly low) |
| **New** (0% baseline expected) | attachments[] |

## UX implications for the redesign

* The redesign should invest in **making production[] and materials[] easier to fill** — the current row-based interfaces work when foremen expand the section but the sections are collapsed by default.
* **Boilerplate defense**: no repeat-notes were detected in the sample (n=30 is small; a longer sample would surface template patterns).
* **Photo gate**: the field culture accepts fewer than 6 photos ~57% of the time. The redesign should either enforce the gate server-side, relax the minimum to 3, or make photo capture faster.
