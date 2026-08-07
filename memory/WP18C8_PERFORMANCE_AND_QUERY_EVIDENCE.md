# WP-18C8 Performance and Query Evidence

Date: 2026-08-07
Result: PASS WITH NOTED FORCE-REFRESH COST

## Endpoint timing evidence

Measured locally against the live backend on 2026-08-07:

| Endpoint | Result |
|---|---|
| PM earned-value cached read | `200` in ~`5.7s` |
| PM earned-value force refresh | `200` in ~`28.2s` |
| Executive earned-value force refresh | `200` in ~`26.6s` |
| PM CSV export | `200` in ~`27.9s` |
| Executive CSV export | `200` in ~`27.1s` |

Interpretation:
- The operator-facing default route uses cached/current snapshots and returned in ~`5.7s` during closeout.
- Force-refresh and export remain heavier because they intentionally re-read the inherited schedule, budget, work-ledger, actual-candidate, and C7 forecast authorities before writing a fresh C8 version.
- No blocking timeout or crash remained after implementation.

## Index evidence

Verified indexes:
- `project_earned_value_snapshots.project_number` (unique)
- `project_earned_value_snapshots.generated_at`
- `project_earned_value_versions.(project_number, version_number)` (unique)
- `project_earned_value_versions.(project_number, fingerprint)`
- `project_budget_commitment_candidates.(project_number, source_po_id)` (unique)
- `project_budget_actual_cost_candidates.(project_number, source_kind, source_record_id)` (unique)

## Query-shape result

- C8 uses bounded project-scoped reads only.
- No new unbounded collection scan was reported by `deployment_agent`.
- No repeated duplicate writes occur on unchanged snapshots because versions are fingerprinted.
- Default page loads reuse the current snapshot instead of always forcing a full rebuild.

## Non-blocking note

Force-refresh/export latency is acceptable for the current governed certification path, but the route remains a valid future optimization target if more projects or denser schedule/work-ledger history are added.