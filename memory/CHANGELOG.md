# Change Log

## 2026-07-26 — Wave 3 Family 3C Operational Events Phase B

- Preserved bounded Family 3C ownership in `/app/backend/routes/operational_events.py` with `operational_events` as the canonical normalized store and no adjacent-family writes.
- Repaired the direct Family 3C admin auth contract to the current repository reality in tests and verification: admin routes require both `X-Admin-Token` and the bound `X-Directory-Token`.
- Added bounded Family 3C lifecycle evidence: materialization now writes append-only `audit_events` evidence with `kind=operational_events.materialize` and emits Trust Spine workflow `operational-events-materialization`.
- Hardened Family 3C query surfaces with explicit Mongo projections and a date-pushed dashboard aggregation while preserving public endpoint contracts.
- Verification evidence: local Family 3C suite passed `18/18`, independent verification passed in `/app/test_reports/iteration_43.json`, and direct PM Family 3C consumer smoke verification passed.

## 2026-07-25 — Wave 3 Family 3A Core Admin Operations Phase B

- Recorded the repository-backed Family 3 split: `3A Core Admin Operations`, `3B Operations Actions`, `3C Operational Events`, `3D Asset Mapping & Reconciliation`.
- Limited active implementation authority to Family 3A only.
- Applied bounded Family 3A contract fixes in the core admin operations route and direct consumers/tests only.

## 2026-07-25 — Wave 3 Family 3B Operations Actions Phase B

- Unified the Family 3B authentication contract to the secure runtime model: one acting portal token plus the bound `X-Directory-Token`.
- Repaired Family 3B consumers to use a dedicated OA client with explicit portal scoping and directory-session forwarding.
- Added bounded Trust Spine emission, richer history context, duplicate-assignment suppression, query reductions, owner-search parallelization, and photo-path rollback cleanup inside Family 3B only.
- Closed Phase B with bounded verification evidence: `42/42` Family 3B tests passed locally, independent verification passed in `/app/test_reports/iteration_42.json`, and final backend regression sweep passed `19/19`.
- Hardened the Family 3B auth gate further to reject multiple portal headers while preserving the required valid directory session pairing.
- Recorded Phase B latency evidence: list and owner-search improved in preview; summary remained shared-infrastructure dominated.