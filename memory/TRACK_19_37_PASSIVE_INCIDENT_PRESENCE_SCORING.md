# TRACK 19.37 · PASSIVE INCIDENT-PRESENCE SCORING

**Date:** 2026-07-03 · **Status:** 🟢 GO · **Six Pillar: 58/60 · Production Strong · Zero-Drift**
**Anchor:** `PRODUCTION_READINESS_QUALITY_GATE.md` · `TRACK_19_36_EXECUTIVE_INTELLIGENCE.md`

## Charter
Add a **read-only, deterministic, attention-only** signal layer that helps Safety identify cases needing review. Never a decision. Never a classification. Never OSHA / liability / root-cause / discipline automation. Every score explainable, every source cited.

Core doctrine: **Field captures facts · Safety investigates · Management decides · Platform routes, records, reports, protects, and surfaces risk signals.**

## What shipped

### New backend module
| Module | Role |
|---|---|
| `backend/incident_engine/presence_score.py` | Pure deterministic scorer · 11 signal rules · zero I/O |
| `backend/incident_engine/presence_score_routes.py` | Additive read-only endpoint |

### New API endpoint (additive)
| Method | Route |
|---|---|
| GET | `/api/incident-cases/{case_id}/presence-score` |

Same Safety/Admin/PM gate as every other `/api/incident-cases/*` route.

### Executive Intelligence integration
- `EXECUTIVE_INTELLIGENCE_MODEL_VERSION` bumped `1.0.0` → **`1.1.0`** (additive · no key removed).
- Added top-level key `attention_signals` (the full presence-score object).
- All 20 pre-19.37 model keys preserved · 21 top-level keys after the bump.

### Frontend
- **New panel** in `ExecutiveCaseReport.jsx`: "Attention Signals" section rendering the overall score, level chip, per-signal rationale + source_fields + owner, missing-inputs ledger, and the no-auto-decision notice.
- **Neutral wording** enforced by lock test: `Attention Signals` · `Review Priority` · `Needs Safety Review` · never "Liability" · "OSHA recordable" · "Root cause" · "Fault" · "Blame".
- **Bilingual** via `useT()` for every user-facing string.

## The Presence Score Object

```
case_id                       string
model_version                 "1.0.0" (presence-score model)
generated_at                  ISO timestamp
overall_attention_score       0–100 integer (mean of 11 signal scores * 100)
attention_level               "low" | "medium" | "high"
signals                       [ 11 signal objects ]
missing_inputs                [ field paths that could not be loaded ]
no_auto_decision_notice       required disclaimer string
```

Every signal object:
```
signal_key                    canonical id (see TRACK_19_37_SIGNAL_RULES.md)
label                         human-readable neutral label
score                         0.0–1.0 float (3 decimals)
confidence                    "low" | "medium" | "high"
rationale                     plain-language sentence(s) citing what triggered the score
source_fields                 list of dotted field paths (e.g. field_block.utility_type)
recommended_review_owner      "safety" | "executive" | "pm"
```

## Signal set (v1 · 11 signals)
1. `possible_injury_presence`
2. `possible_utility_involvement`
3. `possible_vehicle_equipment_involvement`
4. `possible_environmental_involvement`
5. `possible_property_damage`
6. `possible_public_exposure`
7. `possible_police_agency_involvement`
8. `possible_open_evidence_gap`
9. `possible_delayed_closeout`
10. `possible_overdue_capa`
11. `possible_executive_review_needed`

Full rules and source-field lists in `TRACK_19_37_SIGNAL_RULES.md`.

## Rollback

- Runtime rollback: revert 3 additive edits (server.py wiring · assembler `attention_signals` block · frontend panel) and delete the 2 new backend modules.
- Model version drop from 1.1.0 to 1.0.0 requires a matching 1-char edit in the assembler.
- **Rollback confidence:** HIGH. Additive-only. No collection touched, no permission changed, no email changed.
