# WP-18C8 Performance and Query Evidence

Date: 2026-08-07
Result: PASS

## Final hardening repair

Two narrow backend repairs were applied during final hardening:

- `backend/services/project_controls_authority.py`: `ensure_project_controls_foundation()` now caches one-time index / seed setup per DB.
- `backend/services/project_budget_authority.py`: `ensure_project_budget_foundation()` now caches one-time index / shared-foundation setup per DB.

This removed repeated startup-style foundation work from the PM Budget Review path and its supporting work-type / pay-item / review endpoints.

## Live endpoint timing evidence

Measured against the preview runtime after the cache repair using seeded project `ZZ-RUNTIME-CERT-2026`.

| Path | p50 | p95 | Notes |
|---|---:|---:|---|
| PM earned-value cached API | `1083.76 ms` | `2102.59 ms` | `200`, payload `196272` bytes |
| PM earned-value force refresh | `2028.49 ms` | `2096.20 ms` | `200`, payload `196328` bytes |
| Executive earned-value cached API | `491.63 ms` | `555.40 ms` | `200`, payload `196284` bytes |
| Executive earned-value force refresh | `1197.06 ms` | `1353.78 ms` | `200`, payload `196340` bytes |
| PM earned-value CSV export | `1138.60 ms` | `1155.77 ms` | `200`, `text/csv` |
| Executive earned-value CSV export | `438.46 ms` | `523.86 ms` | `200`, `text/csv` |
| PM budget overview | `1747.78 ms` | `3232.48 ms` | improved from prior ~`11.5s` warmed runtime |
| PM budget versions | `987.07 ms` | `1022.92 ms` | supporting Budget Review lane |
| PM budget review queue | `1028.85 ms` | `1066.92 ms` | supporting Budget Review lane |
| PM work types | `279.72 ms` | `297.48 ms` | supporting Budget Review lane |
| PM pay items | `983.13 ms` | `1035.18 ms` | supporting Budget Review lane |

## Earned-value backend profile evidence

Representative live runtime profile returned by the earned-value API after hardening:

- PM cached request profile:
  - `cache_lookup_ms`: `82.53`
  - `backend_total_ms`: `574.21`
  - `request_total_ms`: `82.56`
  - `budget_overview_ms`: `479.10`
  - `payload_bytes`: `100051`
- PM force-refresh profile:
  - `backend_calculation_ms`: `572.89`
  - `versioning_ms`: `64.09`
  - `snapshot_write_ms`: `38.25`
  - `request_total_ms`: `737.41`
  - `mongo_ms`: `1124.87`
- Executive cached request profile:
  - `request_total_ms`: `122.11`
  - `cache_lookup_ms`: `122.08`
- Executive force-refresh profile:
  - `backend_calculation_ms`: `574.27`
  - `snapshot_write_ms`: `40.63`
  - `request_total_ms`: `741.12`

## WP-18DA budget reconciliation

Locked WP-18DA rows were applied only where an exact budget class exists.

| C8 surface | Locked DA budget row | Threshold | Final evidence | Result |
|---|---|---:|---:|---|
| PM CSV export | `preview_output_channel_csv_export` | `<= 2500 ms` | `1138.60 ms` p50 | PASS |
| Executive CSV export | `preview_output_channel_csv_export` | `<= 2500 ms` | `438.46 ms` p50 | PASS |
| C8 snapshot query shape | `workspace_query_targeted_lookup` | `<= 5 docs examined`, no `COLLSCAN` | `1` doc / `1` key, `IXSCAN` | PASS |
| C8 commitment candidate query shape | `workspace_query_targeted_lookup` | `<= 5 docs examined`, no `COLLSCAN` | `1` doc / `1` key, `IXSCAN` | PASS |
| C8 actual-cost candidate query shape | `workspace_query_targeted_lookup` | `<= 5 docs examined`, no `COLLSCAN` | `1` doc / `1` key, `IXSCAN` | PASS |

Diagnostic note:

- PM/Admin earned-value JSON APIs and the PM Budget Review JSON APIs do **not** have a dedicated locked WP-18DA route-time row. They were still measured and reconciled here as truth-state diagnostics, but they are not counted as DA budget violations because no exact locked DA route threshold exists for those authenticated project-controls JSON reads.
- `jobs_master` PM-scope resolution still shows a small `COLLSCAN` over `43` documents in the current preview dataset. It did not create a runtime blocker after hardening and did not touch a locked targeted-query budget row for C8 truth queries.

## Query and index evidence

Verified query shape after hardening:

- `project_earned_value_snapshots.project_number` → `IXSCAN`, `1` doc examined, `1` key examined.
- `project_budget_commitment_candidates.(project_number, source_po_id)` → `IXSCAN`, `1` doc examined, `1` key examined.
- `project_budget_actual_cost_candidates.(project_number, source_kind, source_record_id)` → `IXSCAN`, `1` doc examined, `1` key examined.
- `project_team_assignments.(email, active)` PM-scope helper → `IXSCAN`, `1` doc examined, `1` key examined.

## Frontend/runtime certification linkage

- `testing_agent` report `/app/test_reports/iteration_158.json`: PASS
- `auto_frontend_testing_agent`: PASS on PM earned value, Executive earned value, and PM Budget Review at `390 / 430 / 768 / 1024 / 1440`
- `deep_testing_backend_v2`: PASS with PM force refresh `1.92s`, PM budget overview `1.75s`, and no remaining contradictions

## Final performance result

No locked WP-18DA performance-budget violation remained at C8 closeout. The material C8 outlier was the PM Budget Review foundation path, and that defect is now repaired, remeasured, and recertified.