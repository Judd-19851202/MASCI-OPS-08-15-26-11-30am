# WP18 ECAP Retirement and Deprecation Register

Date: 2026-08-03

## Register purpose

**Proof label:** `DOCUMENTED_ONLY`

This register lists the small set of architecture that ECAP explicitly allows to retire or deprecate.

## Retirement register

| Item | Proof label | Current status | Final disposition | Why retirement is approved | Retirement guardrail |
|---|---|---|---|---|---|
| Legacy operational intelligence digest | `SOURCE_VERIFIED` | parallel executive digest lane still exists | `RETIRE` | it duplicates newer executive/read-side surfaces and increases semantic drift | may retire only after final reporting hierarchy and KPI dictionary are active |
| Executive duplicate report paths that conflict with the final hierarchy | `DOCUMENTED_ONLY` | current overlaps are tolerated only until the hierarchy is implemented | `RETIRE` | one hierarchy must govern every visible executive number | no reader may retire until an authoritative replacement path and drill-down exists |

## Deprecation law

**Decision label:** `APPROVED_CONSTITUTIONAL_DECISION`  
**Proof label:** `DOCUMENTED_ONLY`

Retirement is allowed only where it reduces duplication **without** removing validated upstream truth or operator-critical capability.