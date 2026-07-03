# TRACK 19.36 · EXECUTIVE INTELLIGENCE LAYER

**Date:** 2026-07-03 · **Status:** 🟢 GO · **Six Pillar: 58/60 · Production Strong · Zero-Drift**
**Anchor:** `PRODUCTION_READINESS_QUALITY_GATE.md` · `TRACK_19_35_QUALITY_GATE_CLOSEOUT.md`

## Charter
Deliver ONE unified Executive Intelligence Model that powers every executive-grade surface (Executive Case Report page · Executive Report PDF · future consumers). Never duplicate logic. Never invent facts. Every value traceable to a certified source.

## What shipped

### New backend modules
| Module | Role |
|---|---|
| `backend/incident_engine/executive_intelligence.py` | Pure read-only **assembler** — `assemble_executive_intelligence(db, case_id)` returns the unified model |
| `backend/incident_engine/executive_report_render.py` | Boardroom-grade HTML template consumed by WeasyPrint |
| `backend/incident_engine/executive_report_routes.py` | 2 additive read-only routes |

### New API endpoints (additive)
| Method | Route | Payload |
|---|---|---|
| GET | `/api/incident-cases/{case_id}/executive-intelligence` | JSON — unified Executive Intelligence Model |
| GET | `/api/incident-cases/{case_id}/executive-report.pdf` | `application/pdf` — same model, boardroom template |

### New frontend surface
| File | Role |
|---|---|
| `frontend/src/pages/ExecutiveCaseReport.jsx` | Single-screen boardroom view of the model |
| Route `/safety/cases/:caseId/executive-report` | Additive, Safety-gated by existing auth stack |
| Header link in `SafetyCaseWorkspace.jsx` | 1-button navigation to the report page |

### Zero touches
- `/api/incident-cases/{id}/reports/{type}.pdf` (Phase E) — **untouched.**
- `/safety/executive-intelligence` dashboard (Phase D) — **untouched.**
- No collection schemas mutated.
- No permissions widened or narrowed.
- No emails, notifications, or audit events introduced.

## The Executive Intelligence Model

Top-level keys (in order):

```
model_version               "1.0.0"
generated_at                ISO timestamp of assembly
case_ref                    { case_id · case_number · state · incident_type · location · reporter · timestamps }
executive_summary           { headline · one_paragraph · severity_band · severity_rationale · root_cause_summary }
why_it_matters              { what_happened · why_leadership_should_care · current_risk_if_no_action ·
                              recommended_executive_decision · expected_outcome_if_implemented · source_note }
timeline                    [ { id · at · actor · event_type · summary · source } ]
evidence_chain              [ { id · type · label · added_by · added_at · withdrawn · custody_chain · source } ]
people                      { reporter · personnel_present · witnesses[] }
asset_buckets               { equipment_ids · vehicle_ids · unit_numbers · property · environmental · utility }
medical                     [ { kind · at · provider · subject · lost_days · restricted_days · notes · source } ]
agency                      [ { agency_name · officer · report_number · at · notes · source } ]
communications              [ { kind · at · subject · contact · body · source } ]
corrective_actions          { items[] · totals { total · open · verified · canceled } }
outstanding_tasks           { items[] · totals { total · open } }
regulatory_review           { osha_review · insurance_review · legal_review · executive_review }
readiness                   { overall_pct · band · sub_scores[6] each with num/den/pct/rationale }
decision_records            [ { at · decision · from_state · to_state · actor · reason · source } ]
operational_intelligence    { occurred_at · reported_at · safety_intake_at · first_capa_at · closed_at ·
                              time_to_intake_days · time_to_capa_days · time_to_closure_days · days_open ·
                              corrective_action_open · corrective_action_total }
sources                     { collection-per-domain mapping }
missing_fields              [ explicit list of fields the assembler could not populate ]
```

Every field is derived from one of these certified collections:

| Domain | Source collection |
|---|---|
| Case | `incident_cases` |
| Timeline | `incident_case_events` |
| Evidence chain | `incident_case_evidence` |
| CAPA | `corrective_actions` |
| Witnesses | `case_witnesses` |
| Medical | `case_medical` |
| Agency contacts | `case_agency_contacts` |
| Communications | `case_communications` |
| Tasks | `case_tasks` |

No new collections. No writes.

## Fact-based Why-It-Matters briefing

Every sentence is either:
- a direct value from `field_block` or `safety_block`, or
- a formatted count over one of the collections above, or
- a deterministic template selecting between two literal outcomes based on a boolean/numeric field.

When a required value is missing, the sentence explicitly says *"Not documented yet."* — never inferred, never fabricated. The renderer surfaces the same phrase in every gap.

The `source_note` inside the briefing spells out that every sentence is derived from the four certified source collections above.

## Consumers

- **Frontend page** `/safety/cases/:caseId/executive-report` — full model rendered as a single-screen boardroom view with PDF download.
- **PDF endpoint** `/api/incident-cases/{id}/executive-report.pdf` — same model, boardroom template.
- **Future consumers** (Track 19.37+) — read the same JSON. Consumers must never duplicate assembly logic.

## Rollback

- Runtime rollback: remove the 4-line `_register_ie_executive_report_routes(...)` block in `server.py` and the 2-line link in `SafetyCaseWorkspace.jsx`.
- File-level rollback: delete 3 backend files (`executive_intelligence.py` · `executive_report_render.py` · `executive_report_routes.py`) + 1 frontend file (`ExecutiveCaseReport.jsx`) + remove the App.js route entry.
- Rollback confidence: **HIGH.** Additive-only. No schema migrations. No permission changes.
