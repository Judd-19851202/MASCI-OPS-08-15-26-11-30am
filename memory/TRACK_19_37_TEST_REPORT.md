# TRACK 19.37 · TEST REPORT

**Date:** 2026-07-03 · **Anchor:** `PRODUCTION_READINESS_QUALITY_GATE.md`

## Scope
Regression + certification proof for Track 19.37 (Passive Incident-Presence Scoring).

## Backend build
- Lint (`ruff` on both new modules): ✅ clean.
- Backend supervisor restart: ✅ up · `/api/health` → 200.
- Runtime smoke against live DB (case `2026-00001`):
  - `EXECUTIVE_INTELLIGENCE_MODEL_VERSION = 1.1.0` (bumped from 1.0.0).
  - Executive Intelligence Model has 21 top-level keys (was 20).
  - `attention_signals` present · 11 signals returned · overall = 0 · level = low (case is clean).
  - Forbidden vocabulary check on the signals payload — **GREEN** (no `liability`, `discipline`, `fault`, `blame`, `osha_recordable`, `preventability`, `root_cause_conclusion` in signal keys/labels/rationales/source_fields/owners).
  - `no_auto_decision_notice` present and mentions "attention signal".
  - Every signal has `source_fields`, `rationale`, `recommended_review_owner`.

## Frontend build
- Hot-reload: ✅ clean.
- Lint on `ExecutiveCaseReport.jsx`: ✅ clean.

## Lock test (pytest · isolated)

**File:** `/app/backend/tests/test_track_19_37_presence_scoring.py`

Runs in isolation (Track 19.30 protocol · known asyncio bleed in global sweep).

### Assertion coverage

| # | Assertion | Purpose |
|---|---|---|
| 1 | Scorer module exists · imports cleanly | Module lock |
| 2 | Routes module exists · imports cleanly | Module lock |
| 3 | Scorer exports `compute_presence_score` and `PRESENCE_SCORE_MODEL_VERSION` | Public API lock |
| 4 | Scorer is read-only (grep · no writes) | Zero-write lock |
| 5 | Server wires `register_presence_score_routes` | Route registration lock |
| 6 | `EXECUTIVE_INTELLIGENCE_MODEL_VERSION` bumped ≥ 1.1.0, major = 1 | Additive-bump lock |
| 7 | Model contains `attention_signals` key | Integration lock |
| 8 | All 20 pre-19.37 model keys still present | Zero-drift lock on Track 19.36 |
| 9 | `attention_signals` object has `case_id`, `model_version`, `generated_at`, `overall_attention_score`, `attention_level`, `signals`, `missing_inputs`, `no_auto_decision_notice` | Shape lock |
| 10 | `attention_level` ∈ {low, medium, high} | Enum lock |
| 11 | Overall score ∈ [0, 100] | Range lock |
| 12 | 11 signals emitted with the required signal_key set | Signal-set lock |
| 13 | Every signal has `signal_key`, `label`, `score`, `confidence`, `rationale`, `source_fields`, `recommended_review_owner` | Per-signal shape lock |
| 14 | Every `score` ∈ [0, 1] float | Score-range lock |
| 15 | Every `confidence` ∈ {low, medium, high} | Enum lock |
| 16 | Every `recommended_review_owner` ∈ {safety, executive, pm} | Enum lock |
| 17 | `no_auto_decision_notice` mentions "attention signal only" AND "Safety owns investigation" | Doctrine notice lock |
| 18 | Forbidden vocabulary (`osha_recordable`, `liability`, `liable`, `discipline`, `disciplinary`, `fault`, `blame`, `preventability`, `root_cause_conclusion`, `at_fault`) absent from signal payload (excluding the notice) | Doctrine payload lock |
| 19 | Frontend panel exists in `ExecutiveCaseReport.jsx` with `data-testid="exec-report-section-attention"` | UI existence lock |
| 20 | Frontend panel uses neutral wording (`Attention Signals`, `Review Priority`, `Needs Safety Review`) | UI vocabulary lock |
| 21 | Frontend panel does NOT contain any forbidden label (`Liability`, `OSHA recordable`, `Root cause`, `Fault`, `Blame`, `Preventability`, `Discipline`) inside JSX literals | UI vocabulary ban lock |
| 22 | Frontend panel wraps at least 3 strings in `t(...)` | Bilingual lock |
| 23 | Deterministic: same inputs → same outputs (call twice, compare signals) | Determinism lock |
| 24 | Missing-inputs list is present and is a list | Shape lock |
| 25 | Scorer exposes `NO_AUTO_DECISION_NOTICE` constant | Public API lock |
| 26 | 7 required Track 19.37 docs present + PRD/CHANGELOG updated | Governance lock |
| 27 | Closeout doc declares 🟢 GO · Six Pillars · Rollback | Verdict lock |
| 28 | Zero-Drift Matrix covers required categories | Zero-drift completeness |
| 29 | Track 19.34 field-facing grep invariant still holds | Doctrine regression lock |

**Result:** all assertions PASS in isolation.

## Regression coverage on prior tracks

- Track 19.34 · Field intake modernization: field-facing schema/page still free of forbidden decision vocabulary — asserted directly in this suite.
- Track 19.35 · Safety Case Workspace: unchanged · lock test remains green.
- Track 19.36 · Executive Intelligence: model version test was **relaxed to accept any 1.x semver** (per Track 19.36 doctrine: additive bump for minor-version increments). All 36 assertions green post-relaxation.

## Known infra issue (unchanged from prior tracks)

Global pytest sweep fails due to asyncio event-loop bleed across suites (documented in the PRD backlog). Per Track 19.30 protocol, lock tests are validated in isolation. Track 19.37 conforms.

## Verdict

🟢 **PASS.** Zero regressions. All Track 19.37 assertions green.
