# TRACK 19.37 · NO-AUTO-DECISION DOCTRINE

**Date:** 2026-07-03 · **Anchor:** `TRACK_19_34_FIELD_VS_SAFETY_PROTECTION.md` · `TRACK_19_35_FIELD_FACTS_IMMUTABILITY.md`

## The doctrine
> **FIELD captures facts.**
> **SAFETY investigates.**
> **MANAGEMENT decides.**
> **PLATFORM routes, records, reports, protects, and surfaces risk signals.**

Track 19.37 introduces a **passive attention-scoring** layer. It **never**:

- decides OSHA recordability or reportability;
- decides root cause;
- decides liability;
- decides preventability;
- decides fault or blame;
- recommends discipline;
- classifies severity for legal purposes;
- makes any determination that binds insurance, agency, or attorney handling.

Every signal the layer surfaces is:
- **traceable** (source_fields cited),
- **explainable** (plain-language rationale),
- **presence-based** (no inference beyond documented field presence),
- **owned** (`recommended_review_owner` names who should review, not who is at fault).

## The required notice
Every presence-score object carries this literal string as `no_auto_decision_notice`:

> *"This score is an attention signal only. Safety owns investigation and classification. The platform routes, records, reports, protects, and surfaces risk signals — it never decides OSHA recordability, root cause, liability, fault, or discipline."*

The notice is:
- **required** at the top of the presence-score object;
- **surfaced verbatim** in the frontend Attention Signals panel;
- **locked** by the Track 19.37 pytest test (`test_notice_present` + `test_notice_names_forbidden_domains`).

## Forbidden vocabulary in signal payload
The following words / phrases must **not** appear inside any of these fields of a signal:
- `signal_key`
- `label`
- `rationale`
- `source_fields[]`
- `recommended_review_owner`

Forbidden set: `osha_recordable`, `liability`, `liable`, `discipline`, `disciplinary`, `fault`, `blame`, `preventability`, `root_cause_conclusion`, `at_fault`.

The `no_auto_decision_notice` field is **exempt** from this ban — that field explicitly declares what the platform does **not** decide, so it must be able to name those domains.

Enforcement: `test_signals_free_of_forbidden_decision_vocabulary` in the Track 19.37 lock test suite.

## Forbidden vocabulary in user-facing UI
The Attention Signals panel must **not** show any of these labels: `Liability` · `OSHA recordable` · `Root cause` · `Fault` · `Blame` · `Preventability` · `Discipline`.

Approved neutral wording: `Attention Signals` · `Review Priority` · `Needs Safety Review` · `Source fields` · `owner` · `confidence`.

Enforcement: `test_ui_panel_uses_neutral_wording_only` in the Track 19.37 lock test suite.

## Where decisions still live (unchanged)
| Determination | Owner | Surface |
|---|---|---|
| OSHA recordable / reportable | Safety | `incident_cases.safety_block.osha_recordable` via `PATCH /api/incident-cases/{id}` |
| Root cause | Safety | `incident_cases.safety_block.root_cause_summary` |
| Preventability | Safety | `incident_cases.safety_block.preventability` (extra field) |
| Liability | Safety + Admin | Communications tab · Executive review notes |
| Discipline | HR / Management | HR portal (out of Safety Case Workspace scope) |
| Final case closure | Safety | Executive header state transition |

Track 19.37 **does not touch** any of the above.

## Why this discipline matters
Automated risk classification, when misapplied, becomes:
- an OSHA compliance liability (a "recommendation" the platform generated could be used as evidence);
- an insurance dispute lever;
- an HR grievance point (perceived bias in disciplinary triage);
- a trust breaker with field reporters ("The machine decided I was at fault").

The Track 19.37 signals are **attention prioritization only**. A Safety Manager still opens the case, reviews the immutable field record (Track 19.35), and makes every judgement themselves. The platform surfaces "look here first" · nothing more.

## Rollback
The entire scoring layer is additive. To disable it: remove the assembler's `attention_signals` block, revert the model version, and delete the frontend panel. All investigation and classification surfaces continue to work unchanged.
