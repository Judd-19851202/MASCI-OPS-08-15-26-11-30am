# BCSS Release 2 · Program 2 · Wave 3 · Family 3D-2
# External Asset Mapping & Reconciliation — Phase A Discovery

## 1. Executive Summary
Repository evidence confirms that external asset mapping and reconciliation behavior is real and active in the codebase, but it is **not proven as a clean standalone constitutional family**.

The strongest live evidence points to a **shared Integration Center mapping capability** centered on `asset_mappings`, `asset_mapping_proposals`, and admin reconciliation surfaces. However, the same repository also keeps external asset IDs directly on `equipment_master` via Asset Spine and legacy equipment-master mutation surfaces.

Under the stricter threshold, that ambiguity is disqualifying for a standalone Family 3D-2.

## 2. Discovery Scope
This Phase A review was executed under a strict read-only mandate to determine whether the repository proves a distinct constitutional family responsible for external source-system asset identities and reconciliation.

Allowed action:
- create this single artifact

Disallowed actions honored:
- no implementation
- no refactor
- no optimization
- no PRD / ROADMAP / CHANGELOG mutation
- no adjacent family redesign

## 3. Discovery Method
This document is based only on repository evidence from backend routes, backend services, frontend operator surfaces, and the previously completed 3D-1 discovery artifact.

No future-state assumptions, architectural preferences, or desired cleanup outcomes were treated as evidence.

## 4. Governing Decision Rule
The user-established decision posture is controlling:
- mixed evidence alone does not justify a new family
- merge into Asset Spine only if mapping/reconciliation is fundamentally subordinate to canonical identity authority
- merge into provider integrations when no genuine cross-provider owner exists
- reject when the candidate would only rename or layer existing behavior
- recommend standalone 3D-2 only if the repository proves a distinct cross-provider owner, lifecycle, persistence model, mutation authority, and clean boundary from Asset Spine
- any material ambiguity involving canonical identity, `equipment_master` versus `asset_mappings`, tenant isolation, or external overwrite authority must result in **NO-GO**

## 5. Files Reviewed
Primary evidence reviewed for this discovery:
- `/app/backend/routes/asset_mapping_recon.py`
- `/app/backend/routes/integrations/mappings.py`
- `/app/backend/routes/integrations/cleanup.py`
- `/app/backend/routes/integrations/maintainx_p0.py`
- `/app/backend/services/maintainx_asset_sync.py`
- `/app/backend/routes/asset_spine.py`
- `/app/backend/services/asset_spine.py`
- `/app/backend/server.py` (legacy `equipment_master` CRUD)
- `/app/frontend/src/pages/admin/AdminAssetMapping.jsx`
- `/app/frontend/src/pages/admin/IntegrationTruth.jsx`
- `/app/frontend/src/components/admin/MappingCleanupTab.jsx`
- `/app/frontend/src/components/admin/MaintainxP0Tab.jsx`
- `/app/memory/BCSS_RELEASE2_PROGRAM2_WAVE3_FAMILY3D1_ASSET_SPINE_CANONICAL_REGISTRY_PHASEA_DISCOVERY.md`

## 6. Discovery Question
Does the repository support a constitutional family whose responsibility is **external source-system asset identity mapping and reconciliation**, distinct from the canonical internal Asset Spine?

## 7. Candidate Constitutional Boundary
The narrowest candidate reading is:

**Family 3D-2 = external provider-to-canonical asset crosswalk ownership, reconciliation queueing, conflict handling, and operator-approved mapping persistence.**

## 8. Initial Candidate Strength
This candidate is not imaginary. The repository contains:
- dedicated reconciliation routes
- dedicated mapping CRUD routes
- dedicated cleanup/conflict routes
- a dedicated admin reconciliation page
- a shared `asset_mappings` collection
- a proposal collection `asset_mapping_proposals`

That is enough to justify serious evaluation.

## 9. Primary Persistence Stores
The discovery surfaced four relevant persistence areas:
- `asset_mappings`
- `asset_mapping_proposals`
- `maintainx_dryrun_reports`
- `equipment_master`

The first three are mapping/reconciliation-oriented. The fourth is the canonical asset registry and also carries embedded external IDs.

## 10. Route Surface Inventory
Backend route surfaces directly involved:
- `/api/admin/integrations/asset-mappings*`
- `/api/admin/asset-mapping/scan`
- `/api/admin/asset-mapping/queue`
- `/api/admin/asset-mapping/{id}/approve|reject|reassign`
- `/api/admin/asset-mapping/bulk-approve`
- `/api/admin/asset-mapping/coverage|audit|top-unmapped|impact-preview|operational-impact`
- `/api/admin/integrations/cleanup/*`
- `/api/admin/maintainx/p0/*`

## 11. Frontend Surface Inventory
Frontend operator surfaces directly involved:
- `AdminAssetMapping.jsx` — scan, approve, reject, coverage, operational impact, queue
- `MappingCleanupTab.jsx` — trust score, driver cleanup, asset cleanup, conflict handling
- `MaintainxP0Tab.jsx` — read-first MaintainX dry-run and saved report review

These are real operator-facing surfaces, not dormant scaffolding.

## 12. Provider Scope Inventory
Provider evidence is uneven:
- Motive has active reconciliation, cleanup, approval, trust score, and conflict flows
- MaintainX has read-first dry-run matching and report generation
- FleetWatcher appears only as an embedded external ID on Asset Spine surfaces, without a matching dedicated reconciliation lane in the reviewed files

So the cross-provider posture exists, but it is incomplete and asymmetrical.

## 13. Candidate Lifecycle Inventory
Lifecycle semantics are split across multiple states:
- proposal status: `Imported`, `Matched`, `Verified`, `Rejected` (`asset_mapping_recon.py:13-16, 218-236, 292-309`)
- mapping status: `Mapped` / `Unmapped` (`mappings.py:105-113, 153-159`)
- cleanup status: `ignored`, `former_employee`, `ignored_gateway`, `retired`, `resolved` (`cleanup.py:9-19, 55-58`)

This is a real lifecycle footprint, but it is fragmented rather than singular.

## 14. Candidate Mutation Inventory
Mutation authority is spread across multiple paths:
- `mappings.py` creates/updates/deletes `asset_mappings`
- `asset_mapping_recon.py` approves or reassigns proposals by updating `asset_mappings.masci_equipment_id`
- `cleanup.py` links, retires, ignores, or resolves conflicts on `asset_mappings`
- `asset_spine.py` and `asset_spine` service directly mutate embedded external IDs on `equipment_master`

This is strong evidence of non-exclusive mutation authority.

## 15. Read-Only Intelligence Inventory
There is also an intelligence/reporting layer:
- coverage
- audit
- top-unmapped
- impact preview
- operational impact
- executive summary
- MaintainX dry-run reports

These are valuable, but they do not by themselves prove constitutional ownership.

## 16. Relationship to Asset Spine
Asset Spine is the canonical internal registry family from 3D-1. It is important here because the mapping candidate is valid only if it is cleanly separated from canonical identity ownership.

## 17. Relationship to Provider Integrations
The mapping candidate also sits visibly inside the Integration Center structure:
- `routes/integrations/mappings.py`
- `routes/integrations/cleanup.py`
- `routes/integrations/maintainx_p0.py`

This is strong evidence that much of the candidate already behaves like an integration capability rather than a separate constitutional owner.

## 18. Relationship to MaintainX Dry-Run
`maintainx_asset_sync.py` is explicitly read-first and states it never writes to MaintainX, never writes to `equipment_master`, and only optionally writes to `maintainx_dryrun_reports` (`maintainx_asset_sync.py:5-7, 20-23, 308-312, 463-471`).

That makes MaintainX evidence useful for discovery, but weak as proof of a standalone mutation owner.

## 19. Relationship to Motive Cleanup
`cleanup.py` is substantial, but it is still explicitly framed as an Integration Center cleanup capability using existing `asset_mappings` and `employee_mappings` docs with no new collection (`cleanup.py:2-19`).

## 20. Ownership Test — Cross-Provider Identity Owner
**Determination: NOT PROVEN.**

Why:
- `asset_mappings` holds both Motive and MaintainX subdocuments (`mappings.py:91-118`)
- but active reconciliation depth is primarily Motive-specific (`asset_mapping_recon.py`, `cleanup.py`)
- MaintainX remains largely read-first dry-run logic (`maintainx_asset_sync.py`, `maintainx_p0.py`)
- FleetWatcher has only embedded ID fields in Asset Spine (`asset_spine.py:53-56, 96-99`; `asset_spine` service lines `143-146`, `439-442`, `506-507`)

The repository does not prove one coherent cross-provider owner with symmetric responsibilities.

## 21. Ownership Test — Canonical Internal Identity
**Determination: NO — not owned by 3D-2.**

Canonical internal identity remains anchored to Asset Spine / `equipment_master`, not to `asset_mappings`.

Evidence:
- 3D-1 discovery already established `equipment_master` as the canonical registry
- `mappings.py` explicitly says mappings do not duplicate `equipment_master` (`mappings.py:4-7`)

## 22. Ownership Test — External Identity Maintenance
**Determination: PARTIAL and SHARED.**

Evidence for mapping-layer ownership:
- `asset_mappings` stores `motive.vehicle_id`, `motive.asset_id`, `maintainx.asset_id`, and `masci_equipment_id` (`mappings.py:91-118`)

Evidence against exclusive ownership:
- Asset Spine also stores `motive_asset_id`, `motive_vehicle_id`, `fleetwatcher_asset_id`, and `maintainx_asset_id` directly on `equipment_master` (`asset_spine.py:53-56, 96-99`; `asset_spine` service `143-146`, `439-442`, `506-507`)

## 23. Ownership Test — Reconciliation Engine
**Determination: PARTIAL / PROVIDER-SPECIFIC.**

`asset_mapping_recon.py` is a real reconciliation engine, but it is narrowly focused on dispatch truck IDs, Motive mapping rows, and `equipment_master` heuristics (`asset_mapping_recon.py:5-16, 159-236`).

That is real capability, but not proof of a broad cross-provider reconciliation owner.

## 24. Ownership Test — Proposal Queue
**Determination: YES, but only for a Motive-oriented subflow.**

`asset_mapping_proposals` is a dedicated operator-approval queue (`asset_mapping_recon.py:13-16, 150-158, 244-271`).

This is strong functional evidence, but it is not broad enough to prove a full independent family by itself.

## 25. Ownership Test — Mapping CRUD
**Determination: YES inside Integration Center, not standalone family.**

`mappings.py` owns create/update/delete of `asset_mappings` and enforces 1:1 mapping per master record (`mappings.py:75-123, 124-170`).

This is the clearest owner surface for mapping persistence.

## 26. Ownership Test — Conflict Resolution
**Determination: YES as an integration cleanup capability.**

`cleanup.py` detects duplicates, proposal collisions, and resolves conflicts by modifying `asset_mappings` / `employee_mappings` (`cleanup.py:193-331, 653-768`).

Again, this proves active capability, but under Integration Center semantics.

## 27. Ownership Test — Drift / Coverage Metrics
**Determination: YES, but derivative.**

Coverage, audit, top-unmapped, impact, and trust-score surfaces exist (`asset_mapping_recon.py:363-688`; `cleanup.py:342-416`).

These are derivative measurements of mapping quality, not evidence of constitutional independence.

## 28. Ownership Test — Source-System Overwrite Authority
**Determination: AMBIGUOUS.**

The repository does not prove one single place that definitively owns external ID overwrite authority.

Competing evidence:
- `mappings.py` mutates `asset_mappings`
- `asset_mapping_recon.py` mutates `asset_mappings.masci_equipment_id`
- `cleanup.py` mutates `asset_mappings`
- Asset Spine mutates embedded external IDs on `equipment_master`

Under the required threshold, this ambiguity is disqualifying.

## 29. Ownership Test — Persistence Model
**Determination: REAL but SPLIT.**

The repository shows more than one persistence model:
- crosswalk records in `asset_mappings`
- approval queue records in `asset_mapping_proposals`
- dry-run audit reports in `maintainx_dryrun_reports`
- embedded external IDs in `equipment_master`

That is not a single clean persistence model.

## 30. Ownership Test — Lifecycle
**Determination: REAL but FRAGMENTED.**

There is no single lifecycle language. Proposal, mapping, and cleanup states coexist without a clearly unified owner model.

## 31. Ownership Test — Audit Trail
**Determination: PARTIAL.**

The mapping surfaces write sync logs and store notes/status fields (`cleanup.py:507-512, 533-537, 558-562, 602-607, 623-628, 644-649, 761-766`).

Useful evidence exists, but audit ownership is secondary to the mutation split.

## 32. Ownership Test — Tenant Isolation
**Determination: NOT PROVEN / MATERIALLY AMBIGUOUS.**

The reviewed mapping and reconciliation surfaces do not show explicit tenant scoping on `asset_mappings`, `asset_mapping_proposals`, or `maintainx_dryrun_reports`.

Given the platform’s broader tenant-aware architecture elsewhere, this silence is material.

Under the user’s threshold, tenant isolation ambiguity alone forces **NO-GO**.

## 33. Ownership Test — Provider Abstraction
**Determination: PARTIAL.**

`asset_mappings` contains both Motive and MaintainX fields, but the actual operational tooling is still uneven by provider. This is a shared schema, not a proven shared owner doctrine.

## 34. External-ID Duplication in Asset Spine
Asset Spine input models explicitly carry:
- `motive_asset_id`
- `motive_vehicle_id`
- `fleetwatcher_asset_id`
- `maintainx_asset_id`

Evidence:
- `asset_spine.py:53-56`
- `asset_spine.py:96-99`

This is direct evidence that external identity data is not isolated to the mapping family candidate.

## 35. Duplicate External Representation Risk
The repository keeps external identity in two places:
- as provider subdocuments in `asset_mappings`
- as embedded fields on `equipment_master`

That is the central constitutional problem for 3D-2.

## 36. `asset_mappings` Collection Evidence
`asset_mappings` is the strongest mapping-layer store.

Repository evidence:
- cross-provider subdocuments (`mappings.py:91-118`)
- 1:1 enforcement per `masci_equipment_id` (`mappings.py:88-90`)
- list and unmapped views (`mappings.py:58-74, 172-184`)
- cleanup actions and conflicts (`cleanup.py:116-190, 193-331, 565-768`)

## 37. `equipment_master` External-ID Evidence
`equipment_master` is also an external-ID store because Asset Spine create/update operations write provider IDs directly to the canonical row (`asset_spine.py` service `439-442`, `506-507`).

This weakens any claim that `asset_mappings` is the sole external identity owner.

## 38. `asset_mapping_proposals` Evidence
`asset_mapping_proposals` is a real queue with indexes, status, score, and operator approval (`asset_mapping_recon.py:13-16, 150-158, 200-236, 285-360`).

This is meaningful, but still narrower than a full constitutional family.

## 39. `maintainx_dryrun_reports` Evidence
`maintainx_dryrun_reports` is clearly an audit/report collection, not a mapping owner store (`maintainx_asset_sync.py:20-23, 463-471`; `maintainx_p0.py:15-19, 69-88`).

## 40. Mapping Status Semantics
`Mapped` / `Unmapped` are stored inside provider subdocuments (`mappings.py:105-113, 153-159`).

This is practical runtime metadata, but it does not answer canonical ownership.

## 41. Proposal Status Semantics
Proposal rows advance through `Imported`, `Matched`, `Verified`, `Rejected` (`asset_mapping_recon.py:13-16, 218-236, 294-309`).

This is a useful queue lifecycle, but only one part of the broader candidate.

## 42. Cleanup Status Semantics
Cleanup adds another independent state set: `ignored`, `former_employee`, `ignored_gateway`, `retired`, `resolved` (`cleanup.py:9-19, 55-58`).

This further proves fragmentation.

## 43. Consumer Matrix
| Consumer | What it treats as authoritative | Implication |
|---|---|---|
| `AdminAssetMapping.jsx` | proposal queue + coverage + approval flows | Motive-oriented reconciliation workspace |
| `MappingCleanupTab.jsx` | `asset_mappings` / `employee_mappings` cleanup state | Integration cleanup capability |
| `MaintainxP0Tab.jsx` | dry-run reports and read-first matching | advisory MaintainX reconciliation |
| Asset Spine profile | canonical asset plus some mapping-derived status | mapping output is consumed by Spine, not isolated from it |

## 44. Mutation Matrix
| Capability | Primary surface | Store | Reading |
|---|---|---|---|
| asset mapping create/update/delete | `mappings.py` | `asset_mappings` | strongest mapping persistence owner |
| reconciliation approval | `asset_mapping_recon.py` | `asset_mapping_proposals` + `asset_mappings` | operator queue subflow |
| cleanup/conflict resolution | `cleanup.py` | `asset_mappings` / `employee_mappings` | integration cleanup authority |
| embedded external ID mutation | Asset Spine | `equipment_master` | overlap with canonical row |
| legacy equipment row mutation | `server.py` | `equipment_master` | additional overlap risk |

## 45. Store Matrix
| Store | Role | Problem |
|---|---|---|
| `asset_mappings` | provider crosswalk | real owner candidate but not exclusive |
| `asset_mapping_proposals` | approval queue | subflow, not full family |
| `maintainx_dryrun_reports` | read-first audit output | advisory only |
| `equipment_master` | canonical asset row plus external IDs | breaks boundary purity |

## 46. Authority Matrix
| Question | Answer |
|---|---|
| Who owns canonical internal asset identity? | Asset Spine / `equipment_master` |
| Who owns provider crosswalk rows? | Integration Center mapping routes |
| Who owns proposal approval queue? | `asset_mapping_recon.py` |
| Who owns embedded provider IDs on canonical asset rows? | Asset Spine mutation surfaces |
| Is there one exclusive external-ID owner? | No |

## 47. Cross-Provider Cohesion Assessment
There is **schema-level cohesion** in `asset_mappings`, but not enough **owner-level cohesion** in runtime behavior.

That is not sufficient for standalone constitutional recognition.

## 48. Motive-Specific Overhang
Most of the strongest operator tooling is Motive-first:
- scan queue
- approve/reject/reassign
- cleanup center
- trust score
- conflict resolution

This makes the candidate look partly like a Motive operations family rather than a balanced cross-provider owner.

## 49. MaintainX-Specific Overhang
MaintainX evidence is mostly dry-run and advisory:
- connection test
- dry-run
- saved report review

That is materially weaker than the Motive lane and does not prove equal ownership footing.

## 50. FleetWatcher Overhang
FleetWatcher appears only as an external ID field inside Asset Spine in the reviewed evidence. No matching reconciliation workflow was surfaced.

That weakens the claim that 3D-2 is already a general external asset identity family.

## 51. Dispatch Linkage Assessment
`asset_mapping_recon.py` specifically closes the join gap between `dispatch_assignments.truck_id`, `asset_mappings.masci_equipment_id`, and Motive IDs (`asset_mapping_recon.py:5-16`).

This is important, but it is a dispatch/Motive reconciliation specialization, not proof of a full independent constitutional owner.

## 52. Canonical Subordination Test
**Result: FAIL for merge into Asset Spine as-is.**

Why:
- mapping/reconciliation carries its own queueing, conflict, cleanup, and provider-specific persistence semantics
- these are not merely passive canonical identity fields

So the candidate is **not fundamentally subordinate enough** to be simply absorbed by Asset Spine conceptually.

## 53. Provider-Integrations Merge Test
**Result: PASS.**

Why:
- strongest persistence owner is `routes/integrations/mappings.py`
- strongest cleanup/conflict owner is `routes/integrations/cleanup.py`
- MaintainX read-first surfaces are already mounted under integration routes
- operator understanding already treats much of this as Integration Center behavior

This is the cleanest repository-backed constitutional home.

## 54. Rename / Layering Rejection Test
**Result: FAIL for standalone 3D-2.**

A new standalone family would largely rename and layer behavior already spread across:
- Integration Center mapping CRUD
- Integration Center cleanup/conflict handling
- Motive reconciliation queue
- Asset Spine external-ID fields

Without eliminating duplication, it would add another named owner.

## 55. One Source of Truth Test
**Result: FAIL.**

Reason:
- canonical asset truth lives in `equipment_master`
- mapping crosswalk truth lives in `asset_mappings`
- external IDs also live on `equipment_master`

There is no one proven source of truth for external asset identities.

## 56. Zero-Drift Test
**Result: FAIL.**

The same external identity domain is represented in multiple places with multiple mutation paths.

## 57. Bounded Ownership Test
**Result: FAIL for standalone family.**

The candidate lacks a clean, exclusive boundary because canonical rows and integration rows both carry external identity data.

## 58. Clean Boundary Test
**Result: FAIL.**

Clean separation from Asset Spine is not proven.

## 59. External Overwrite Authority Ambiguity
Material ambiguity exists over whether the effective external identity authority is:
- `asset_mappings`
- proposal approval logic
- cleanup/conflict logic
- Asset Spine direct update of embedded fields

By user rule, this ambiguity forces **NO-GO**.

## 60. Tenant Isolation Ambiguity
The reviewed mapping and reconciliation surfaces do not demonstrate explicit tenant-scoped ownership rules.

By user rule, this ambiguity also forces **NO-GO**.

## 61. `equipment_master` vs `asset_mappings` Ambiguity
This is the most important ambiguity in the repository.

`asset_mappings` is treated as a provider crosswalk, but `equipment_master` also stores provider IDs directly and Asset Spine mutates them.

That means the codebase does not prove one authoritative external-identity persistence layer.

## 62. Long-Term Roadmap Alignment
Standalone 3D-2 is **not aligned** with the roadmap objective of fewer constitutional owners.

Recognizing it as-is would preserve or increase ownership overlap rather than reduce it.

## 63. Constitutional Necessity Test
Why might this capability deserve family status?

Evidence in favor:
- there is real mapping persistence
- there is real reconciliation queueing
- there are real operator workflows
- there are real conflict and trust metrics

Why that is still insufficient:
- the owner is not cleanly separated from Asset Spine
- the provider lanes are uneven
- mutation authority is fragmented
- tenant isolation is not proven

Therefore constitutional necessity is **not proven for a standalone family**.

## 64. Phase B Viability
**Phase B is not viable for a standalone 3D-2 family under current evidence.**

Any bounded Phase B that treated 3D-2 as already distinct would be building on unresolved constitutional ambiguity.

## 65. Highest Architectural Risks
1. Duplicate external-ID representation across `asset_mappings` and `equipment_master`
2. Split mutation authority across mapping routes, cleanup routes, reconciliation approval, and Asset Spine updates
3. Motive-heavy behavior masquerading as cross-provider ownership
4. Unproven tenant isolation for mapping stores and reconciliation flows
5. No clear external overwrite authority

## 66. Discovery Confidence
**Discovery confidence: High.**

Why high:
- primary mapping, cleanup, and MaintainX files were directly reviewed
- competing Asset Spine and legacy mutation surfaces were directly reviewed
- frontend consumers were directly reviewed
- the ambiguity is explicit in code, not speculative

## 67. Strict Constitutional Classification
**Classification: MERGE CANDIDATE — PROVIDER INTEGRATIONS, NOT STANDALONE FAMILY.**

More precisely:
- canonical internal asset identity remains with **Asset Spine**
- external provider crosswalk behavior is best classified as an **Integration Center / provider-integrations capability**
- standalone Family 3D-2 is **not repository-proven**

## 68. GO / NO-GO Recommendation
**GO / NO-GO: NO-GO for standalone Family 3D-2.**

This NO-GO is required by repository evidence because material ambiguity exists around:
- canonical identity versus external mapping authority
- `equipment_master` versus `asset_mappings`
- tenant isolation
- external overwrite authority

## 69. Exact Recommended Next Action
If the architecture wants a constitutional home for this behavior, treat it as a **provider-integrations mapping capability** anchored to `asset_mappings`, while keeping Asset Spine as the canonical internal asset authority.

Do **not** authorize Phase B for a standalone 3D-2 family unless later repository changes first prove:
- one exclusive external-ID persistence owner
- one clean mutation owner
- one clear overwrite authority
- tenant-safe boundaries
- a clean separation from Asset Spine

## 70. Closing Verdict
The repository proves that external asset mapping and reconciliation are important live capabilities.

It does **not** prove a distinct constitutional family cleanly separated from Asset Spine and provider integrations.

**Final verdict:** **MERGE INTO PROVIDER INTEGRATIONS · STANDALONE 3D-2 REJECTED FOR NOW · NO-GO.**