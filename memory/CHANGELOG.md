# Change Log

## 2026-07-25 — Wave 3 Family 3A Core Admin Operations Phase B

- Recorded the repository-backed Family 3 split: `3A Core Admin Operations`, `3B Operations Actions`, `3C Operational Events`, `3D Asset Mapping & Reconciliation`.
- Limited active implementation authority to Family 3A only.
- Applied bounded Family 3A contract fixes in the core admin operations route and direct consumers/tests only.

## 2026-07-25 — Wave 3 Family 3B Operations Actions Phase B

- Unified the Family 3B authentication contract to the secure runtime model: one acting portal token plus the bound `X-Directory-Token`.
- Repaired Family 3B consumers to use a dedicated OA client with explicit portal scoping and directory-session forwarding.
- Added bounded Trust Spine emission, richer history context, duplicate-assignment suppression, query reductions, owner-search parallelization, and photo-path rollback cleanup inside Family 3B only.