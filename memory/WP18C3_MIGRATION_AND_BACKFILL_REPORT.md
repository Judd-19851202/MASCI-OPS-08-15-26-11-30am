# WP18C3 Migration and Backfill Report

Date: 2026-08-03

## Scope of backfill

WP-18C3 backfill is additive and non-destructive. It does **not** rewrite source systems, infer original budgets, or synthesize accounting values.

## Implemented mechanism

- Service: `backend/services/project_budget_authority.py`
- Runtime method: `run_project_budget_backfill(db, force=True)`
- Admin route: `POST /api/admin/governance/project-controls/budget/backfill/run`

### Important repair made during C3

The first synchronous admin route approach was too heavy for an HTTP request path. It was changed to a **queued/non-blocking** route while the underlying service remains directly executable for bounded certification runs.

This preserves the constitutional rule from prior work: do not execute expensive migration/backfill work through a blocking request path.

## Certified execution evidence

### Direct service verification
- execution time: approximately `33.97s`
- result: completed successfully

### Most recent stored report
- `run_type`: `wp18c3_backfill`
- `run_id`: `wp18c3-backfill:20260803231717`
- `ran_at`: `2026-08-03T23:17:17.975521+00:00`
- `foundation_reviews_opened`: `0`
- `commitment_candidates_created`: `0`
- `actual_cost_candidates_created`: `0`
- `status`: `completed`

### Why later runs created zero rows

An earlier successful certification execution had already created the additive foundation rows:
- commitment candidates: `32`
- actual-cost candidates: `8`

The latest run demonstrated **idempotence** by creating `0` additional rows.

## What backfill does

1. Ensures additive indexes for C3 collections.
2. Scans governed projects / PO Request project references / project pay-item project references.
3. Opens a foundation review item only when governed pay-item authority exists but no budget version exists.
4. Preserves unresolved commitment candidates from approved/closed PO Requests.
5. Preserves unresolved actual-cost candidates from receipt evidence.

## What backfill does not do

- no deletion of source records
- no overwrite of existing budget versions
- no creation of fake original budgets
- no guessed budget-line linkage
- no GL/accounting transaction creation
