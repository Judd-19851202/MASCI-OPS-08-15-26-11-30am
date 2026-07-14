# Certification Plan

Date: 2026-07-14
Track: DR-01

## Certification goal

Prove that Daily Report continuity and Smart Prefill are trustworthy again before any broad rollout.

## Stage 1 · Repository certification

Required proof:
- one approved canonical field contract
- no conflicting draft base keys across active shells
- no conflicting scope formulas across active shells
- one Smart Prefill source and one apply path in the active shell

## Stage 2 · Preview behavior certification

Required flows:
1. Start a report, type, refresh, restore draft
2. Start a report, switch project/date, verify scope stays truthful
3. Start a report, go offline, queue submit, recover when online
4. Pick a project with recent context, verify Smart Prefill offer appears
5. Apply Smart Prefill, verify review affordances and edited values persist
6. Discard draft, recover archived draft when applicable

## Stage 3 · Cross-shell certification

Only required if two shells remain routable.

Required proof:
- no draft loss when router moves operator between shells
- Smart Prefill behavior identical on every routable shell

## Stage 4 · Device/browser certification

Priority device matrix:
- iPad Safari
- iPhone Safari
- Chrome desktop
- Chrome/Android if field population uses it

Priority scenarios:
- home-button / tab background / lock-screen return
- poor network / offline queue
- pagehide during active typing

## Stage 5 · Production observability certification

Required evidence:
- `draft_telemetry` shows healthy write volume for the canonical Daily Report form key
- `draft.write.fail` and `quota.warning` trend downward after repair
- `draft.restore.offered` / `draft.restore.action` ratios are explainable
- no active shell emits a foreign/non-canonical Daily Report form key

## Unknowns blocking final certification today

The repository cannot prove:
- which shell production users are currently hitting
- which browser/device cohorts are affected most
- whether pagehide failures are dominant in the field

Therefore final certification requires runtime evidence after implementation.
