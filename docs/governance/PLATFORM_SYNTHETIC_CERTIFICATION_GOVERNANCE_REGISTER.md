# Platform Synthetic / Certification Data Governance Register

Last updated: 2026-08-11T09:50Z

Status: **PASS / DIRECT RUNTIME VERIFIED**

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

Current live runtime proof on 2026-08-11:

- Endpoint: `/api/admin/platform-truth-integrity/contamination` → `200`
- `overall_status=green`
- `release_gate_blocked=false`
- `backend/tests/test_prec10_platform_truth_integrity.py` = `1 / 1 PASS`

Interpretation rule now in force:

- **GREEN** = no heuristic-only exclusion, no fixture-only rows lacking explicit governed metadata, and no contradictory truth markers.
- **YELLOW** = certification-scoped rows exist in shared storage families and must remain isolated from operator/executive business truth, but this is a governed non-blocking condition, not contamination drift.
- **RED** = blocking contamination defect.

### Explicitly governed and currently healthy in the scanner

| Family | Current state |
|---|---|
| Corrective Actions | PASS in current scanner. Explicit governed markers now control operator visibility and hostile tests prove no name-based hiding. |
| C7 Forecast Snapshots | Certification-scoped family currently tracked as governed project scope. |
| C8 Earned Value Snapshots | Certification-scoped family currently tracked as governed project scope. |
| C9 Portfolio Snapshots | Certification-scoped family currently tracked as governed project scope; stale cache invalidation is now independently green in the stale-derived-state scanner. |

### Explicitly governed families that are now green

| Family | Heuristic-only records currently detected | Explicit hidden rows already present | Current status | Current disposition |
|---|---:|---:|---|---|
| Employees | 0 | 221 | PASS | Explicit governed metadata now controls technical/synthetic employee visibility. |
| Daily Reports | 0 | 1908 | PASS | Explicit governed metadata now controls technical/certification daily-report visibility. |
| Field Leadership Records | 0 | 430 | PASS | Explicit governed metadata now controls technical FL record visibility. |
| Incidents | 0 | 165 | PASS | Explicit governed metadata now controls technical incident visibility. |
| Safety Meetings | 0 | 135 | PASS | Explicit governed metadata now controls technical meeting visibility. |
| JHAs / JHPs | 0 | 15 | PASS | Explicit governed metadata now controls technical JHA/JHP visibility. |
| Inspections | 0 | 108 | PASS | Explicit governed metadata now controls technical inspection visibility. |
| Training / Qualifications | 0 | 1 | PASS | Explicit governed metadata now controls technical training visibility. |
| Safety Issuances | 0 | 49 | PASS | Explicit governed metadata now controls technical PPE issuance visibility. |
| Dispatch Assignments | 0 | 386 | PASS | Explicit governed metadata now controls technical dispatch assignment visibility. |
| Equipment Inspections / DVIR | 0 | 499 | PASS | Explicit governed metadata now controls technical DVIR visibility. |

### Governed non-blocking mixed-mode families

| Family | Certification-scoped rows present | Current status | Why this is not a blocker |
|---|---:|---|---|
| Projects | 1 | GOVERNED ADVISORY | Internal certification project exists in canonical storage and must remain isolated from operator/executive truth where applicable. |
| Project Members | 21 | GOVERNED ADVISORY | Certification-project assignments are explicitly scoped and not heuristic contamination. |
| Budget Actual Cost Candidates | 9 | GOVERNED ADVISORY | Certification/test cost-candidate rows are explicitly certification-scoped, not silent contamination. |
| C7 Forecast Snapshots | 983 | GOVERNED ADVISORY | Certification-project forecast snapshots are expected technical lineage, not operator contamination. |
| C8 Earned Value Snapshots | 1 | GOVERNED ADVISORY | Certification-project EV snapshot remains an explicit governed test asset. |
| C9 Portfolio Snapshots | governed scoped rows present | GOVERNED ADVISORY | Portfolio certification snapshots remain explicit governed lineage and are not heuristic contamination. |
| Backup / Recovery Certification | governed technical-only rows present | GOVERNED ADVISORY | Recovery certification artifacts are technical evidence and intentionally excluded from operator business truth. |

## Interpretation

The current scanner no longer reports any blocking contamination family.
Historical technical/certification rows still exist, but they are now explicitly governed and surfaced through the correct audit or technical lanes instead of contaminating operator/executive business truth.

## Release-health consequence

This register is now **PASS** for the current PRE-C10 denominator.
It remains part of the platform truth-integrity gate, and it should only reopen if current runtime evidence shows a new heuristic-only leak, fixture-only record without explicit metadata, or contradictory truth markers.