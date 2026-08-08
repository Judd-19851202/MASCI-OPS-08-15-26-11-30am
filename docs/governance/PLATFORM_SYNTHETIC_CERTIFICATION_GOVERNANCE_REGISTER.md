# Platform Synthetic / Certification Data Governance Register

Last updated: 2026-08-08T21:00Z

Status: **OPEN / FAIL-CLOSED**

This register tracks platform-wide exposure to synthetic/test/certification/technical data contamination.
It is governed by the rule:

> Certification and technical records must never contaminate operator or executive business truth.

## Current governed scanner

Runtime scanner:

- Endpoint: `/api/admin/platform-truth-integrity/contamination`
- Library: `backend/lib/platform_truth_integrity.py`
- Release gate coverage: `backend/tests/test_prec10_platform_truth_integrity.py`

This scanner currently classifies material families using:

- explicit governed markers where available;
- heuristic-only legacy detection where explicit governance is still missing;
- certification-project scope checks for snapshot families;
- contradictory marker detection.

If a family still relies on heuristic-only exclusion for records that affect operator/executive truth, the family is **FAIL**.

## Current findings

### Explicitly governed and currently healthy in the scanner

| Family | Current state |
|---|---|
| Corrective Actions | PASS in current scanner. Explicit governed markers now control operator visibility and hostile tests prove no name-based hiding. |
| C7 Forecast Snapshots | Certification-scoped family currently tracked as governed project scope. |
| C8 Earned Value Snapshots | Certification-scoped family currently tracked as governed project scope. |
| C9 Portfolio Snapshots | Certification-scoped family currently tracked as governed project scope, but stale cache invalidation remains separately open. |

### Families still failing because they rely on heuristic-only exclusion instead of full explicit governance

| Family | Heuristic-only records currently detected | Explicit hidden rows already present | Current status | Why this remains open |
|---|---:|---:|---|---|
| Employees | 155 | 0 | FAIL | Test/certification-looking employee rows still rely on heuristic-only filtering; legitimate records could be excluded accidentally. |
| Daily Reports | 237 | 599 | FAIL | Explicit governance exists for many rows, but 237 rows still match legacy heuristic-only exclusion without explicit governed markers. |
| Field Leadership Records | 411 | 0 | FAIL | Role-scoped operator records still depend on heuristic-only exclusion patterns. |
| Incidents | 145 | 0 | FAIL | Safety event records still rely on heuristic-only exclusion in the absence of explicit governed markers. |
| Safety Meetings | 72 | 0 | FAIL | Meeting truth still depends on heuristic-only exclusion. |
| JHAs / JHPs | 15 | 0 | FAIL | Job-hazard analysis records still depend on heuristic-only exclusion. |
| Inspections | 107 | 0 | FAIL | Inspection truth still depends on heuristic-only exclusion. |
| Training / Qualifications | 1 | 0 | FAIL | At least one training row still depends on heuristic-only exclusion. |
| Safety Issuances | 44 | 0 | FAIL | PPE / issuance truth still depends on heuristic-only exclusion. |
| Dispatch Assignments | 81 | 0 | FAIL | Dispatch operator truth still depends on heuristic-only exclusion. |
| Equipment Inspections / DVIR | 47 | 0 | FAIL | Equipment inspection truth still depends on heuristic-only exclusion. |

## Interpretation

These FAIL rows do **not** prove that current live dashboards are wrong in every case.
They do prove that the platform still has governance gaps where exclusion logic depends on legacy heuristic identification instead of explicit governed metadata.

That is enough to block PRE-C10 GO.

## Required next actions per family

For every failing family:

1. define the canonical explicit classification values (`LIVE_OPERATIONAL`, `SYNTHETIC_TEST`, `CERTIFICATION`, `TECHNICAL`, `LEGACY_MIGRATION` or equivalent);
2. backfill explicit governed metadata onto legacy technical/certification rows;
3. ensure operator/executive consumers use the same governed exclusion contract;
4. add hostile tests proving legitimate live rows are not hidden by heuristic resemblance;
5. add consumer parity checks proving technical rows do not enter live aggregates.

## Release-health consequence

This register is now part of the platform truth-integrity gate.
If any material family remains FAIL here, PRE-C10 remains **OPEN / NO-GO**.