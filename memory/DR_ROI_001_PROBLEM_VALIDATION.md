# DR-ROI-001 · Problem Validation

**Date:** 2026-02-05
**Method:** Structured pain-point verification against the audited current state.

## Verifying claims from the DR-ROI-001 directive

| # | Claim | Verification | Status |
|---:|---|---|---|
| 1 | "Current Daily Report captures data but does not convert enough into PM intelligence" | 15 downstream consumers read raw docs but only `executive_overview.py` and `material_movement.py` do any aggregation. No `daily_report_kpis` collection exists. PM dashboards render raw fields, not derived intelligence. | ✅ **VALIDATED** |
| 2 | "Current narrative/reporting sections are too duplicate" | Free-text surfaces: `general_notes`, `narrative_sections{}` (6 sub-prompts), `activities[].notes`, `constraints[].notes`, `schedule_delays_notes`, `weather_impact_notes`, `incident_notes`. Seven overlapping text surfaces. | ✅ **VALIDATED** |
| 3 | "Supervisors are asked to write too much freeform text" | `NewDailyReport.jsx` = 3,021 lines. Substantial portion is text inputs / textareas. Six narrative sub-prompts alone can produce 2,000+ chars of typing. | ✅ **VALIDATED** |
| 4 | "The dashboard shows counts more than insights" | `DailyReportsDashboard.jsx` = 243 lines, list-heavy. No delay-cause aggregation, no production-by-area trend, no equipment utilization trend, no readiness KPI. | ✅ **VALIDATED** |
| 5 | "Production/delay/equipment/manpower intelligence is underused" | `production[]` and `constraints[]` structures exist (V.2 Wave-1A/B) but no dashboard tile aggregates them across days. `equipment[].hours_used` present but never rolled up. | ✅ **VALIDATED** |
| 6 | "Photos are treated as attachments instead of evidence" | `photos: List[str]` — URLs only. Zero AI tagging. Zero activity-link. Zero material-link. Photos are opaque to downstream analysis. | ✅ **VALIDATED** |
| 7 | "PMs are not getting enough actionable KPI value" | Confirmed by (1) + (5). `pm_action_items` field does not exist. No "Today's PM Brief" screen. | ✅ **VALIDATED** |
| 8 | "The form is powerful but not simple enough" | Field-count audit of `dailyReportSchema.js` seed + downstream expansions ≈ 30+ top-level keys, many with nested repeating groups. Cognitive-UX track (19.07) was already an attempt at simplification. | ✅ **VALIDATED** |
| 9 | "The output PDF is not as executive/operationally useful as it should be" | PDF template maps 1:1 to raw fields (list of activities, list of constraints, big narrative text block). Zero KPIs on cover page. No Today's PM Brief section. | ✅ **VALIDATED** |

## Additional pain points surfaced by the audit

| # | Pain | Evidence |
|---:|---|---|
| 10 | **Photos have no source-of-work link** | A photo of "pipe going in" cannot be tied to the specific `activities[]` row that says "installed 40 LF of 12" HDPE"; downstream reviewers see photos out of context. |
| 11 | **`activities[]` shape is under-specified** | Free-form `activity, percent_complete, station_from, station_to, notes` — no crew, no equipment, no material, no quantity-unit, no photo links, no status enum, no continuation flag. |
| 12 | **`constraints[]` has minimal follow-up structure** | `constraint_type, hours_impact, notes` — no responsible party, no needed-by date, no cost-time-impact flag, no linked photos. |
| 13 | **No "tomorrow readiness" record** | No structured way to say "we need survey by 07:00 tomorrow or we're blocked". |
| 14 | **Narrative confidence + source trace absent** | The 6-prompt guided narrative has no per-sentence evidence trace, no confidence score, no audit-editable approval log. |
| 15 | **Delay categorization is soft** | Constraint taxonomy exists but the directive requires a MUCH deeper enum (weather · equipment · utility conflict · inspection delay · material delay · survey/model issue · subcontractor issue · owner/CEI decision · traffic control · manpower · extra work · safety stop · quality/rework · other). |

## What is NOT broken

- HR crew-time capture (`masci_crews[]`) — clean and consumed by 3 portals
- Safety escalation gate — 8 fields cover the required workflow
- Excavation/JHA gate — enforces backend 422 correctly
- Photo minimum (6) — enforced
- Signature requirement — enforced on both prepared-by and superintendent
- Backward compatibility contract — `ConfigDict(extra="allow")` means additive V2 fields are safe

## Success criteria for DR-ROI-001

1. Supervisor time per report drops from unmeasured-but-long to **5–8 minutes** on a normal day (per directive).
2. Every AI sentence traces to a supervisor-entered fact or a Vision-detected photo observation.
3. PM dashboard surfaces at least 22 named KPIs (production · delay · equipment · manpower · readiness · safety · quality · AI confidence · report completeness).
4. Zero broken submissions on existing V1 records.
5. Zero broken downstream consumers (15 endpoints audited).
6. Zero live emails during any test or preview run.
7. All existing tests (5 backend suites + frontend payload-repair) pass unchanged.

## Attestation

Every claim in the directive has been validated against the audited codebase. No claim was rejected. The problem is real; the redesign is warranted.
