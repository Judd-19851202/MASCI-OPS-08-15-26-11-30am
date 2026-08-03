# WP18 ECAP No-Rebuild Register

Date: 2026-08-03

## Register purpose

**Proof label:** `DOCUMENTED_ONLY`

Everything listed here is protected from rebuild unless a later critical defect is evidenced.

## Protected capabilities

| Capability | Proof label | Why preserve | Allowed extension | Approved reopening trigger |
|---|---|---|---|---|
| WP-17 governed design system | `DOCUMENTED_ONLY` | It is already validated cross-platform UI infrastructure. | additive components and governed variants only | proven structural inability to support an approved workflow |
| Canonical shells / portal structure | `DOCUMENTED_ONLY` | Multi-role portal architecture already works and supports discoverability. | new routes inside existing shells; governed navigation changes | evidenced shell-level failure to support an accepted operator role |
| Authentication architecture | `SOURCE_VERIFIED` | MFA, passkeys, and session continuity are already implemented. | bounded scope propagation and permission mapping only | security defect or compliance requirement evidenced in source/runtime |
| Permission / governance system | `SOURCE_VERIFIED` | This is a core trust-line asset, not a candidate for casual redesign. | additive policies/permissions/approval flows only | critical contradiction in authority enforcement |
| Form engine / schema-driven capture | `DOCUMENTED_ONLY` | High-value capture infrastructure already exists across domains. | additive forms and governed schema evolution only | source-verified inability to support required field workflows |
| Daily Report architecture | `SOURCE_VERIFIED` | It is the established field-entry spine and should remain the operational root. | governed additions to feed schedule/cost/EV | evidence that the architecture cannot support approved fact families |
| Safety workflows | `DOCUMENTED_ONLY` | Already validated operator infrastructure. | additive reporting/rollup integration only | evidence of trust-line failure or impossible required workflow |
| Transportation / dispatch workflows | `SOURCE_VERIFIED` | Existing dispatch and transportation operations are substantial and working. | bounded integrations and reporting alignment only | evidence that accepted WP18C scope cannot integrate cleanly |
| Shop workflows | `SOURCE_VERIFIED` | Shop operations already have dedicated validated architecture. | additive cost/controls binding only | evidence of unresolvable lifecycle defect |
| HR workflows | `SOURCE_VERIFIED` | HR role surfaces already provide validated operational value. | additive labor/qualification rollups only | source-verified inability to meet approved role requirements |
| PDF / email / report framework | `DOCUMENTED_ONLY` | Communications/report infrastructure is already widespread and valuable. | new templates and governed outputs only | inability to meet a required regulatory/operator output |
| Backup / recovery systems | `DOCUMENTED_ONLY` | Recovery posture is not in WP-18C scope and should remain stable. | none within WP-18C except documentation alignment | explicit recovery failure or executive recovery directive |
| Current governance ledgers / audit systems | `SOURCE_VERIFIED` | Critical to traceability and authority trust. | additive entries and mappings only | proven inability to audit required WP18C events |
| Validated APIs and current data models | `SOURCE_VERIFIED` | Core platform behavior and contracts already embody substantial validated work. | additive evolution and compatibility only | source-verified inability to meet an accepted ECAP requirement |

## Executive no-rebuild law

**Decision label:** `APPROVED_CONSTITUTIONAL_DECISION`  
**Proof label:** `DOCUMENTED_ONLY`

No WP-18C package may propose replacement of a protected capability unless the reopening trigger is evidenced and logged in `WP18_ECAP_CONTRADICTION_AND_CONFLICT_REGISTER.md`.