# DR-03 AI Summary Unification

## Current implemented authoring path
- Canonical shell continues to use the existing `DailySummaryAssist` path
- Accepted summary family remains the existing `ai_accepted_summary` contract used by the canonical authoring flow

## Continuation changes
- `daily_summary.py` accept path now writes canonical fields:
  - `ai_accepted_summary`
  - `ai_accepted_summary_meta`
- legacy `daily_operational_summary*` fields remain temporary compatibility mirrors only
- ODS intelligence fact emission from `daily_summary.py` now uses canonical Daily Report source family naming

## What is preserved
- AI-assisted summary remains optional
- Manual fallback path remains available through the existing component contract

## Remaining open items
- Full downstream parity certification (viewer/PDF/email/export/ODS/search/audit/Trust) against the canonical accepted summary still pending
