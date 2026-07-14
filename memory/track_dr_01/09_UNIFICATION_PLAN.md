# Unification Plan

Date: 2026-07-14
Track: DR-01
Mode: Planning only

## Objective

Unify Daily Report behavior without widening scope beyond the existing repository architecture.

## Phase 0 · Recovery freeze
- freeze new Daily Report shell divergence until one canonical field contract is approved
- treat V3 as incomplete parity until Smart Prefill + continuity parity is proven
- treat V2 as legacy compatibility only

## Phase 1 · Contract declaration
- declare the canonical field-entry contract for:
  - draft base key
  - draft scope
  - queue/idempotency scoping
  - Smart Prefill source and apply path
  - local setup-memory boundaries

### Required outcome
One signed-off contract document before any code repair.

## Phase 2 · Draft identity unification
- remove drift between V1 and V3 draft base keys
- remove drift between V1 helper scope and intended project/date scope
- align idempotency, queue form key, archive recovery, prior usage, and telemetry on the same report-instance identity

### Why first
Autosave trust cannot recover while the same in-progress report can live under multiple keys.

## Phase 3 · Smart Prefill unification
- choose one explicit Smart Prefill UI path
- keep `/recent-context` as the single backend source
- separate server-backed Smart Prefill from local `crewMemory` restore
- ensure the currently routed shell consumes the 19.06.1 contract

### Why second
Smart Prefill is broken partly because the active field shell may not consume it at all.

## Phase 4 · Shell parity decision
- either:
  - promote one shell to canonical and port missing behavior into it
  - or keep router-based rollout only after contract parity is proven

### Repository-backed recommendation
Use the V1 continuity/prefill behavior contract as the baseline and only retain V3 elements that can prove parity against that contract.

Reason:
- V1 currently contains the richer recovery surface and the only active `/recent-context` integration.

## Phase 5 · Legacy V2 containment
- audit which `dr_v2_*` services are still required for AI/PDF/back-office workflows
- document them as compatibility surfaces
- remove any hidden assumption that V2 defines active field-entry behavior

## Phase 6 · Regression locks
- add contract tests for shared draft identity
- add route-shell parity tests
- add Smart Prefill availability tests for the active shell
- add queue-formKey parity tests

## Phase 7 · Certification
- preview certification
- device/browser certification
- production telemetry-based certification

## Out-of-scope until separately authorized
- rewriting the entire Daily Report domain from scratch
- deleting legacy V2 collections without a migration decision
- changing downstream PM/PDF/ODS contracts unrelated to continuity recovery
