# Sequenced Implementation Roadmap

Date: 2026-07-14
Track: DR-01
Mode: Planning only

## Sequence philosophy

Repair identity first, then parity, then polish. Do not chase UI tweaks while the same report instance can still live under multiple draft identities.

## Step 0 · Approve the canonical contracts

Approve in writing:
- active field shell strategy
- canonical draft base key
- canonical draft scope fields
- canonical Smart Prefill source and apply path
- legacy V2 containment boundary

## Step 1 · Stop active shell drift

### Goal
Ensure `/daily/new` and `/daily/submit` do not send operators into two different continuity contracts during recovery.

### Deliverable
One approved shell strategy for the repair window.

## Step 2 · Repair draft identity

### Goal
Unify:
- draft base key
- scope formula
- archive recovery key
- queue form key
- idempotency key
- telemetry form key

### Exit condition
The same report instance has one stable identity from first keystroke through final submit.

## Step 3 · Repair Smart Prefill

### Goal
Ensure the active shell consumes `/recent-context` and only one explicit apply path exists.

### Exit condition
Recent-context prefill works in the active shell and has one reviewable operator experience.

## Step 4 · Reconcile local setup memory

### Goal
Keep `crewMemory.js` as a separate local continuity layer and remove conceptual overlap with Smart Prefill.

### Exit condition
Operator can tell whether they are loading local device setup memory or project prior-report context.

## Step 5 · Reconcile V3 parity or contain it

### Goal
Either:
- bring V3 to full continuity/prefill parity
- or prevent V3 from routing live Daily Report traffic until parity is complete

### Exit condition
No routed shell is missing a P0 continuity feature.

## Step 6 · Contain legacy V2

### Goal
Document exactly which `dr_v2_*` services remain valid compatibility surfaces and which are retirement candidates.

### Exit condition
V2 no longer silently influences active field-entry architecture.

## Step 7 · Add regression locks

### Goal
Encode shell parity and draft identity as automated invariants.

### Exit condition
Future version drift becomes test-failing, not operator-discovered.

## Step 8 · Preview + field certification

### Goal
Certify on preview first, then on real field device/browser conditions.

### Exit condition
Observed operator behavior matches the approved contract.
