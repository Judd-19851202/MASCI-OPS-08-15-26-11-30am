# TRACK 19.37 · EXECUTIVE INTELLIGENCE INTEGRATION

**Date:** 2026-07-03 · **Anchor:** `TRACK_19_36_EXECUTIVE_INTELLIGENCE.md`

## Integration summary
Track 19.37 layers into the Track 19.36 Executive Intelligence Model **additively**. No key is renamed, no key is removed, no value is repurposed.

## Model version bump
- **Before Track 19.37:** `EXECUTIVE_INTELLIGENCE_MODEL_VERSION = "1.0.0"` (20 top-level keys).
- **After Track 19.37:** `EXECUTIVE_INTELLIGENCE_MODEL_VERSION = "1.1.0"` (21 top-level keys).

Semver-lite: **minor** bump for additive shape · **major** would signal a breaking change. Consumers keyed off major continue to work.

## Additive key
`attention_signals` — the full presence-score object as defined by `presence_score.compute_presence_score`. Contents documented in `TRACK_19_37_PASSIVE_INCIDENT_PRESENCE_SCORING.md`.

## Existing consumers — impact analysis
| Consumer | Reads which keys? | Impact |
|---|---|---|
| Executive Case Report page (`ExecutiveCaseReport.jsx`) | All 20 pre-19.37 keys + newly reads `attention_signals` | Additive panel · unchanged behavior on other sections |
| Executive Report PDF (`executive_report_render.render_executive_report_html`) | 20 pre-19.37 keys | No change · PDF renderer does not read `attention_signals` in v1.1.0 |
| Track 19.16 Phase D dashboard (`ExecutiveIntelligence.jsx`) | Reads `/api/incident-intelligence/*` · does NOT consume 19.36 model | **Not affected.** |
| Track 19.16 Phase E PDF (`/api/incident-cases/{id}/reports/{type}.pdf`) | Reads case document · does NOT consume 19.36 model | **Not affected.** |

## Executive PDF renderer — deferred integration
`executive_report_render.render_executive_report_html` was **not modified** in Track 19.37. The rendered PDF continues to show the 11 sections shipped in Track 19.36. Adding an Attention Signals section to the PDF is a future track — deferred to keep Track 19.37 scope tight and to observe attention signals in the UI before committing them to boardroom print output.

## Lock test coverage
- `test_executive_model_bumped_to_at_least_1_1_0`
- `test_executive_model_contains_attention_signals`
- `test_executive_model_all_pre_19_37_keys_preserved`
- `test_executive_model_attention_signals_has_notice`
- Re-run of the Track 19.36 lock test suite (36 assertions · **all green** after the model-version test was relaxed to accept any 1.x semver).

## Rollback
Setting `EXECUTIVE_INTELLIGENCE_MODEL_VERSION` back to `"1.0.0"` and deleting the assembler's `attention_signals` block reverts the model to Track 19.36 shape. Consumers that ignore `attention_signals` (i.e. the PDF renderer) require **no** code change.
