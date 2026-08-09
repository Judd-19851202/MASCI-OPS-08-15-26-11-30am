# PRE-C10 Cross-Entity Exception Reconciliation

Generated: 2026-08-09T21:02:33Z

## Scope

This reconciliation explains the active non-blocking cross-entity exception population after the cross-entity gate reached **GREEN**.

The governing rule remains:

- an exception is **non-blocking** only when source evidence is preserved;
- deterministic backfill would require guessing or would create materially false current operational truth;
- the unresolved condition remains visible in the governed Admin-only exception state / CSV export;
- materially relevant current operational misclassification count must remain `0`.

## Headline result

- **Total active exceptions:** `9,800`
- **Cross-entity blocking exceptions:** `0`
- **Materially misclassified exceptions:** `0`

## Counts by source family

| Source family | Count |
|---|---:|
| daily_report_project_and_submitter_lineage | 5,486 |
| dispatch_driver_truck_project_linkage | 2,717 |
| equipment_preop_asset_and_operator_lineage | 1,120 |
| incident_project_and_submitter_lineage | 355 |
| meeting_attendee_identity_normalization | 122 |

## Counts by relationship type

| Relationship type | Count |
|---|---:|
| submitter_lineage | 3,581 |
| project_lineage | 3,025 |
| operator_lineage | 1,061 |
| truck_lineage | 706 |
| active_scope | 435 |
| driver_lineage | 435 |
| equipment_lineage | 435 |
| employee_attendee | 122 |

## Counts by status

| Status | Count |
|---|---:|
| excluded_non_operational | 7,032 |
| accepted_historical_gap | 2,768 |

## Counts by age / time period

| Age band | Count |
|---|---:|
| 0-30 days | 374 |
| 31-90 days | 5,444 |
| 91-180 days | 32 |
| 181-365 days | 1,210 |
| 366+ days | 154 |
| Unknown | 2,586 |

## Active-entity involvement

| Dimension | Count |
|---|---:|
| Involving currently active employees | 15 |
| Involving currently active projects | 900 |
| Involving currently active equipment | 77 |
| Involving currently active vehicles | 0 |

## Current/live operational vs historical/legacy

| Classification | Count |
|---|---:|
| Current/live operational records | 169 |
| Historical/legacy records | 9,631 |
| Hidden or fixture-backed source records | 5,432 |

### Current/live non-blocking exception breakdown

#### By source family

| Source family | Count |
|---|---:|
| equipment_preop_asset_and_operator_lineage | 74 |
| daily_report_project_and_submitter_lineage | 72 |
| meeting_attendee_identity_normalization | 23 |

#### By reason code

| Reason code | Count |
|---|---:|
| legacy_submitter_without_deterministic_employee_match | 59 |
| legacy_operator_without_deterministic_employee_match | 51 |
| legacy_project_without_canonical_jobs_master_match | 36 |
| meeting_attendee_requires_documented_review | 23 |

#### By relationship type

| Relationship type | Count |
|---|---:|
| submitter_lineage | 59 |
| operator_lineage | 51 |
| project_lineage | 36 |
| employee_attendee | 23 |

## Cause reconciliation

| Cause | Count |
|---|---:|
| Missing canonical IDs | 2,768 |
| Ambiguous identity | 98 |
| Missing source evidence | 0 |
| Deterministic backfill would require guessing | 2,768 |

## Downstream relevance counts

These counts answer the question: “how many exceptions could still affect a governed consumer or materially relevant evidence chain?”

| Downstream relevance | Count |
|---|---:|
| Operator-facing history / profile | 9,800 |
| KPI / derived-state | 5,841 |
| Workflow | 9,323 |
| Qualification | 0 |
| Safety decision | 1,597 |
| Assignment | 2,717 |
| Downstream engine / export | 9,800 |
| Any material downstream relevance | 9,800 |

## Reason-code reconciliation

| Reason code | Count |
|---|---:|
| fixture_record_with_verified_test_provenance | 4,857 |
| non_masci_tenant_fixture | 2,175 |
| legacy_submitter_without_deterministic_employee_match | 1,575 |
| legacy_operator_without_deterministic_employee_match | 567 |
| legacy_project_without_canonical_jobs_master_match | 528 |
| meeting_attendee_requires_documented_review | 98 |

## Reclassification work completed in this batch

- Added a missing governed fixture-evidence rule for `backend/tests/test_iter417_operational_attachments.py` (`truck_id=T-IT417`, `driver_name=Test Driver`, `project_number=9999`).
- Normalized the cross-entity exception state against governed fixture evidence and hidden-source metadata.
- Result:
  - `30` previously visible dispatch fixture rows were explicitly hidden from live operations.
  - `4,857` exception rows were reclassified to `fixture_record_with_verified_test_provenance`.
  - `0` materially misclassified exceptions remain.

## Why GREEN still holds after reconciliation

- The `7,032` excluded non-operational exceptions are backed by deterministic fixture evidence or existing governed hidden markers, so they are outside live operator truth by rule.
- The remaining `2,768` accepted historical-gap exceptions still preserve their source evidence and remain visible in the governed Admin-only exception state/export.
- The remaining current/live non-blocking set (`169`) is limited to unresolved meeting attendee identity, daily-report submitter/project lineage, and equipment operator/project lineage where deterministic backfill would require guessing. These rows remain visible as unresolved evidence conditions and do **not** create materially false current dispatch / assignment truth.

## Methodology

- **Current/live operational**:
  - Dispatch = `current_state` in `ASSIGNED`, `EN_ROUTE`, `IN_TRANSIT`
  - Meetings / incidents / daily reports / equipment inspections = source event date within the last `30` days and the source row is not hidden from live operations
- **Active entities**:
  - Employees use `is_active` / status
  - Projects use `jobs_master.active` / status
  - Equipment uses `is_active` / status not retired
  - Vehicles use `transport_trucks.status in {active, pending_review}`
- **Non-blocking rule**:
  - source evidence must remain preserved;
  - deterministic backfill cannot require guessing;
  - unresolved conditions remain visible in governed exception state;
  - no materially false current operational truth may result.