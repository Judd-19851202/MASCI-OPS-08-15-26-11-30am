# DR-03 Autosave and Recovery Implementation

## Implemented
- Canonical shell uses `useFormDraft()` with canonical `daily-report` base key + canonical scope
- Draft status pill remains visible in the shell header
- Restore prompt remains explicit (never silent overwrite)
- Archive recovery slot added to V3 shell
- Legacy recovery slot added for pre-DR-03 candidates

## Truthful status behavior verified locally
- Draft
- Saved just now
- Autosave on / ready states from existing status pill contract

## Remaining open items
- Full explicit save-failure retry affordance copy is not yet expanded in the shell
- Full verified migration write-readback-retire flow for all legacy keys is not yet complete
