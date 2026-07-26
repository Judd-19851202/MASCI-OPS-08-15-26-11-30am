# BCSS Release 2 · Program 2 · Wave 3 · Family 3D-1
# Asset Spine & Canonical Registry Authority — Phase A Discovery

## 1. Executive Summary
Repository evidence supports a **real, repository-backed Asset Spine candidate** centered on `/app/backend/routes/asset_spine.py`, `/app/backend/services/asset_spine.py`, and `equipment_master` as the canonical asset registry.

However, the repository does **not** show Asset Spine as the sole live owner of every adjacent asset responsibility. Canonical registry authority is strong; assignment authority, transfer workflow authority, operational status authority, and some direct registry mutation authority remain shared or adjacent.

**Phase A result:** **GO, but only for a narrowly bounded constitutional family defined as Canonical Asset Identity & Registry Authority with explicit Phase B constraints.**

## 2. Discovery Scope
This discovery was executed as a strict repository review focused on whether Asset Spine can stand as a constitutional family whose sole responsibility is canonical asset identity and registry authority.

Allowed action in this track:
- create this single artifact

Disallowed actions honored:
- no code mutation
- no refactor
- no optimization
- no PRD / ROADMAP / CHANGELOG mutation
- no adjacent family redesign

## 3. Discovery Method
Evidence was gathered from backend registry routes, backend service doctrine, adjacent asset/operations routes, frontend administrative consumers, and existing family-discovery context already produced in the same wave.

This document uses repository evidence only. It does not infer ownership from preference, aspiration, or proposed future cleanup.

## 4. Files Reviewed
Primary files reviewed for this narrowed discovery:
- `/app/backend/routes/asset_spine.py`
- `/app/backend/services/asset_spine.py`
- `/app/backend/routes/operations.py`
- `/app/backend/routes/asset_transfers.py`
- `/app/backend/routes/integrations/mappings.py`
- `/app/backend/server.py` (legacy `equipment_master` CRUD)
- `/app/frontend/src/pages/admin/AdminAssetAdmin.jsx`
- `/app/frontend/src/pages/admin/AssetProfile.jsx`
- `/app/frontend/src/pages/admin/AdminAssetSpineHealth.jsx`
- `/app/frontend/src/components/asset/AddAssetDialog.jsx`
- `/app/frontend/src/pages/AdminAssetThread.jsx`
- `/app/frontend/src/components/dispatch/command/FleetBoard.jsx`

## 5. Discovery Question
Does the repository support a constitutional family whose sole responsibility is **Canonical Asset Identity and Registry Authority**?

Sub-questions explicitly required:
- does Asset Spine own canonical asset registry?
- asset identity?
- asset lifecycle?
- identifier authority?
- registry status model?
- registry search?
- asset relationships?
- asset assignments?
- registry mutations?
- registry administration?

## 6. Candidate Constitutional Boundary
The narrowest repository-backed reading of Asset Spine is:

**Asset Spine = canonical asset identity, canonical registry record, canonical taxonomy, canonical registry search/resolution, and canonical registry administration over `equipment_master`.**

This reading is directly supported by:
- `services/asset_spine.py:4-12` — doctrine claims ForgedOps owns asset identity, ownership, classification, status, assignment, history, lifecycle and names `equipment_master` as the single source-of-truth collection
- `services/asset_spine.py:9-12` — explicit “NEVER creates a parallel asset collection”
- `routes/asset_spine.py:8-18` — dedicated route family for asset list/detail/profile/create/update/retire/activate/health
- `AdminAssetAdmin.jsx:157-160` — “single canonical taxonomy… no parallel maps, no duplicate spines”
- `AssetProfile.jsx:1003-1004` — “equipment_master · spine v… · one asset · one record”

## 7. Canonical Store Evidence
The strongest canonical registry store is `equipment_master`.

Repository evidence:
- `services/asset_spine.py:9-12` explicitly names `equipment_master` the single source-of-truth collection
- `routes/asset_spine.py` reads and writes `db.equipment_master` throughout list, detail, resolver, taxonomy, onboarding, and canonical mutations
- `routes/integrations/mappings.py:4-7` explicitly says mappings do **not** duplicate `equipment_master`
- `routes/asset_transfers.py:4-7,14-15` says `equipment_master` remains the single SOT and transfer rows are events, not duplicate ledger

This is the clearest repository-backed foundation for independent constitutional ownership.

## 8. Dedicated Family Surface Evidence
Asset Spine is not a stray helper. It already exists as a dedicated multi-surface subsystem:
- backend route family: `/api/asset-spine/*`
- backend service layer: `AssetSpine`
- dedicated admin UI: `AdminAssetAdmin.jsx`
- dedicated health UI: `AdminAssetSpineHealth.jsx`
- dedicated add-asset UI: `AddAssetDialog.jsx`
- canonical thread entry / resolver consumption: `AdminAssetThread.jsx`

This breadth is consistent with a family candidate rather than a minor capability hidden inside another family.

## 9. Canonical Registry Surface Inventory
Registry-facing Spine endpoints evidenced in `/app/backend/routes/asset_spine.py`:
- `GET /api/asset-spine/assets`
- `GET /api/asset-spine/assets/{asset_id}`
- `GET /api/asset-spine/assets/{asset_id}/profile`
- `GET /api/asset-spine/resolve`
- `POST /api/asset-spine/assets`
- `PATCH /api/asset-spine/assets/{asset_id}`
- `POST /api/asset-spine/assets/{asset_id}/retire`
- `POST /api/asset-spine/assets/{asset_id}/activate`
- `POST /api/asset-spine/assets/{asset_id}/transfer`
- `GET /api/asset-spine/assets/{asset_id}/transfers`
- `POST /api/asset-spine/assets/{asset_id}/onboarding/advance`
- `GET /api/asset-spine/assets/{asset_id}/onboarding`
- taxonomy and classification endpoints
- health endpoints

This is a substantial bounded surface for registry authority.

## 10. Consumer Surface Inventory
Frontend consumers confirm that Asset Spine is already treated as the central registry lane:
- `AdminAssetAdmin.jsx` — canonical taxonomy review and asset admin
- `AddAssetDialog.jsx` — canonical create flow via `/asset-spine/assets`
- `AssetProfile.jsx` admin tab — canonical admin edits via `/asset-spine/assets/{id}` and `/asset-spine/taxonomy`
- `AdminAssetSpineHealth.jsx` — registry health posture and scan history
- `AdminAssetThread.jsx` — starts with `/asset-spine/resolve` and `/asset-spine/assets/{id}/profile`
- `FleetBoard.jsx` — points rows either to mapping remediation or to Asset Spine profile

These consumers treat Asset Spine as the identity and registry destination even when other operational systems still exist.

## 11. Ownership Test — Canonical Asset Registry
**Determination: YES — strongest owner.**

Evidence:
- `services/asset_spine.py:4-12`
- `routes/asset_spine.py:176-349`
- `routes/asset_spine.py:457-735`
- frontend labels explicitly call this the canonical taxonomy / source-of-truth lane

No other reviewed route declares a different canonical asset registry. Adjacent systems either read `equipment_master`, enrich it, or use it as reference truth.

## 12. Ownership Test — Asset Identity
**Determination: YES, with legacy overlap risk.**

Evidence for ownership:
- `project_asset()` in `services/asset_spine.py:103-192` defines the canonical projected asset shape
- `/api/asset-spine/resolve` resolves canonical identity from `id`, `asset_id`, `unit_number`, `asset_number`, `serial_number`, and `vin`
- `/api/asset-spine/taxonomy/by-unit/{unit_or_id}` resolves a single canonical classification from `equipment_master`

Overlap risk:
- legacy `/admin/equipment-master` create/update/delete routes in `server.py:6748-6832` also mutate the same identity store directly

So Asset Spine is the strongest identity authority, but not yet the exclusive mutation gateway for identity rows.

## 13. Ownership Test — Asset Lifecycle
**Determination: PARTIAL / SHARED.**

Evidence inside Asset Spine:
- create/update/retire/activate/transfer/onboarding in `services/asset_spine.py`

Evidence of adjacent lifecycle engines:
- `routes/asset_transfers.py` implements a richer transfer state machine: `Requested → Approved → In Transit → Received → Closed`
- `routes/operations.py` implements `asset_assignments`, `asset_holds`, and `transfer_requests`, which drive operational lifecycle posture

Conclusion: Asset Spine owns important lifecycle mutations on the canonical row, but it does **not** solely own the full operational asset lifecycle across the platform.

## 14. Ownership Test — Identifier Authority
**Determination: YES for canonical identifiers; PARTIAL for external/provider identifiers.**

Canonical identifiers owned through Asset Spine:
- `asset_id`
- `id`
- `unit_number` / `asset_number`
- canonical resolver aliases

External/provider identifier posture is mixed:
- embedded IDs live on `equipment_master`
- provider-link records also live in `asset_mappings`
- `routes/integrations/mappings.py` owns provider mapping CRUD

So canonical identifier authority is strong; provider identifier authority is shared with mapping infrastructure.

## 15. Ownership Test — Registry Status Model
**Determination: PARTIAL / NOT SOLE OWNER.**

Asset Spine status evidence:
- `asset_status`
- `lifecycle_status`
- retirement/reactivation semantics in `services/asset_spine.py`

Competing operational status evidence:
- `routes/operations.py:358-407` derives current status from `asset_holds`, `asset_assignments`, and `transfer_requests`
- `AssetProfile.jsx` displays `current_status` from `/api/operations/assets/{asset_id}/profile`, not from `/api/asset-spine/assets/{id}/profile`

Therefore Asset Spine does not solely own the operator-facing status model.

## 16. Ownership Test — Registry Search
**Determination: YES — strongest owner.**

Evidence:
- `/api/asset-spine/assets?search=` searches `equipment_master`
- `/api/asset-spine/resolve` performs universal identifier resolution
- `/api/asset-spine/taxonomy/by-unit/{unit_or_id}` provides canonical unit/id classification lookup

This is a strong constitutional marker for registry authority.

## 17. Ownership Test — Asset Relationships
**Determination: PARTIAL / READ-AGGREGATED, NOT SOLE OWNER.**

Asset Spine profile reads relationships from:
- `asset_mappings`
- `equipment_inspections`
- `fleet_defects`
- `dispatch_assignments`
- `motive_events`
- `asset_transfers`
- `admin_audit_log`

Evidence: `services/asset_spine.py:259-358`

This means Asset Spine is an important **relationship aggregator**, but not the sole owner of all relationship records.

## 18. Ownership Test — Asset Assignments
**Determination: NO — not sole owner.**

Evidence against sole ownership:
- `services/asset_spine.py` reads `dispatch_assignments` history; it does not own assignment truth
- `routes/operations.py:773-838` owns `asset_assignments` mutation flows
- `routes/dispatch_command_center.py` and `dispatch_assignments` remain separate operational truth surfaces

Asset Spine exposes assignment-related fields and history, but assignment authority itself lives elsewhere.

## 19. Ownership Test — Registry Mutations
**Determination: PARTIAL / SHARED TODAY.**

Asset Spine mutation evidence:
- canonical create/update/retire/activate/transfer/onboarding

Overlapping mutation evidence:
- `server.py:6748-6832` legacy `/admin/equipment-master` CRUD writes `equipment_master` directly
- `routes/integrations/autolink.py` backfills Motive fields onto `equipment_master`
- trench-safety mirror helpers elsewhere in repository write mirror rows into `equipment_master`

Therefore Asset Spine is not yet the only mutation gateway into the registry.

## 20. Ownership Test — Registry Administration
**Determination: YES, but not exclusive.**

Strong Asset Spine administration evidence:
- `AdminAssetAdmin.jsx`
- `AddAssetDialog.jsx`
- `AssetProfile.jsx` admin section
- `AdminAssetSpineHealth.jsx`

Non-exclusive evidence:
- legacy `equipment_master` admin CRUD still exists in `server.py`

So the platform already has an Asset Spine administration surface, but constitutional exclusivity is not yet fully enforced.

## 21. Single Source of Truth Evidence
Direct repository claims supporting SSoT:
- `services/asset_spine.py:9-12` — `equipment_master` is the single source-of-truth collection
- `routes/asset_transfers.py:4-7,14-15` — transfer records are events; `equipment_master` remains SOT
- `routes/integrations/mappings.py:4-7` — mappings do not duplicate `equipment_master`
- `AdminAssetAdmin.jsx:157-160` — no parallel maps, no duplicate spines
- `AssetProfile.jsx:1003-1004` — one asset, one record

This is the strongest constitutional evidence in favor of independent family status.

## 22. Overlap and Drift Evidence
The same repository also shows live overlap that must be acknowledged:
- legacy direct `equipment_master` CRUD in `server.py`
- transfer workflow engine in `asset_transfers.py`
- operational assignment/hold/transfer status engine in `operations.py`
- provider mapping authority in `integrations/mappings.py`

This means Asset Spine is **real**, but not yet **perfectly exclusive**.

## 23. Legacy Admin Surface Assessment
Legacy `/admin/equipment-master` routes are the clearest evidence against already-clean constitutional exclusivity.

Evidence:
- `server.py:6748-6832` exposes create, update, delete directly against `equipment_master`
- these routes do not route through `AssetSpine`

Constitutional implication:
- the registry owner exists, but another mutation surface still touches the same canonical store

## 24. Transfer Workflow Boundary Assessment
`asset_transfers.py` is not a duplicate registry, but it is a separate lifecycle workflow engine.

Evidence:
- explicit event/lifecycle state machine in `routes/asset_transfers.py:4-33`
- transfer records are positioned as lifecycle events, not registry duplication
- it mutates `equipment_master` location only on receive

Boundary conclusion:
- transfer workflow should remain adjacent to, but not inside, the narrow constitutional registry family

## 25. Operations Aggregator Boundary Assessment
`operations.py` owns the read-only unified asset profile and operational status aggregation.

Evidence:
- module header: “Unified Asset Profile (read-only aggregator)”
- route `/api/operations/assets/{asset_id}/profile`
- `_compute_current_status()` derives statuses from holds, assignments, and transfer requests

Boundary conclusion:
- Asset Spine should not absorb the operational status engine just because the UI shows a unified asset page

## 26. External Mapping Boundary Assessment
`integrations/mappings.py` clearly owns provider-link CRUD, not canonical registry truth.

Evidence:
- mappings do not duplicate `equipment_master`
- create/update/delete endpoints act on `asset_mappings`
- provider identifiers are managed as mapping records

Boundary conclusion:
- the broad 3D split remains correct: mapping/reconciliation must stay separate from registry authority

## 27. Consumer Matrix
| Consumer | What it treats as authoritative | Implication |
|---|---|---|
| `AdminAssetAdmin.jsx` | Asset Spine taxonomy and canonical review queue | registry authority |
| `AddAssetDialog.jsx` | Asset Spine create endpoint | registry administration |
| `AssetProfile.jsx` admin tab | Asset Spine asset + taxonomy | registry administration |
| `AssetProfile.jsx` overview page | Operations unified profile route | operational aggregation is adjacent |
| `AdminAssetSpineHealth.jsx` | Asset Spine health + runs | registry quality / drift detection |
| `AdminAssetThread.jsx` | Asset Spine resolver and profile | identity authority |
| `FleetBoard.jsx` | Asset Spine profile destination vs mapping remediation | Spine is registry destination, not full ops owner |

## 28. Mutation Matrix
| Capability | Primary route/service | Store | Ownership reading |
|---|---|---|---|
| canonical create/update/retire/activate | `asset_spine.py` / `AssetSpine` | `equipment_master` | strong Spine evidence |
| legacy equipment admin create/update/delete | `server.py` | `equipment_master` | overlapping mutation owner |
| provider mapping CRUD | `integrations/mappings.py` | `asset_mappings` | separate mapping family |
| transfer workflow state machine | `asset_transfers.py` | `asset_transfers` + `equipment_master` | adjacent lifecycle engine |
| operational assignments/holds/transfers | `operations.py` | `asset_assignments`, `asset_holds`, `transfer_requests` | separate operational authority |

## 29. Canonical Owner Determination
**Canonical registry owner candidate:** Asset Spine

Reason:
- only reviewed subsystem that explicitly declares itself the canonical asset spine
- only reviewed subsystem with dedicated resolver, taxonomy, canonical projector, and canonical registry CRUD over `equipment_master`
- multiple frontend surfaces already recognize it as the registry lane

## 30. Unresolved or Competing Owner Candidates
Competing or overlapping live surfaces:
- legacy `server.py` `equipment_master` CRUD
- `asset_transfers.py` for rich transfer lifecycle
- `operations.py` for active assignment and current-status authority

These do not disprove the Asset Spine family candidate, but they do block an overly broad or overly exclusive claim.

## 31. Drift Protection Question
**Question:** If Asset Spine becomes a constitutional family, does doing so reduce the number of canonical owners in the platform—or increase them?

**Answer from repository evidence:**

- **Unconstrained recognition would increase or preserve overlap**, because the repository already contains multiple direct and adjacent owners touching asset registry/lifecycle surfaces.
- **Narrow constitutional recognition with explicit boundary constraints would reduce canonical-owner ambiguity**, because it would formalize Asset Spine as the sole canonical asset identity/registry authority while keeping transfers, assignments, and provider mappings outside its scope.

So the truthful evidence-based answer is:

**Asset Spine reduces canonical-owner drift only if Phase B explicitly constrains adjacent mutation surfaces; otherwise it risks naming another owner without removing overlap.**

## 32. Constitutional Necessity Test
**Required question:** Why does this capability deserve to exist as a constitutional family instead of remaining a capability within another family?

**Evidence-backed answer:**

Asset Spine deserves independent constitutional status because the repository already treats canonical asset identity and registry authority as a platform-level cross-cutting concern rather than as a sub-feature of dispatch, integrations, or admin tooling.

Evidence:
- it has a dedicated route namespace and service layer
- it defines canonical projection logic for the asset record itself
- it owns registry search and identifier resolution
- it owns taxonomy administration and review queues
- it is consumed by multiple independent operator surfaces
- adjacent systems explicitly position themselves as non-duplicating readers of `equipment_master`

This is materially different from a local capability inside Dispatch, Operations, or Integrations.

**However:** repository evidence justifies an independent family only for **canonical identity and registry authority**. It does **not** justify giving that family every adjacent asset workflow.

## 33. One Source of Truth Test
**Result: PASS for canonical registry, FAIL for exclusive mutation enforcement.**

Pass evidence:
- `equipment_master` is repeatedly named as SSoT

Fail/partial evidence:
- not all mutations currently funnel through Asset Spine
- direct legacy CRUD and adjacent writers still exist

This supports a family with Phase B boundary hardening, not a claim that the family is already perfectly closed.

## 34. Zero-Drift Test
**Result: CONDITIONAL PASS.**

Asset Spine strengthens zero drift when interpreted narrowly.

It violates zero-drift if Phase B tries to absorb:
- transfer workflow state machine
- operational assignment engine
- provider mapping CRUD
- operational status engine

## 35. Bounded Ownership Test
**Result: PASS only under a narrowed definition.**

Bounded family definition supported by the repository:
- canonical asset record authority
- canonical registry search and resolution
- canonical taxonomy and identifier normalization
- canonical registry administration

Responsibilities not cleanly owned by Spine alone today:
- assignments
- operational statuses
- full transfer workflow state machine
- provider reconciliation

## 36. Family Naming Assessment
Current candidate name “Asset Spine & Canonical Registry” is mostly correct, but the repository evidence is tighter than “all asset lifecycle authority.”

Best evidence-backed name:

**Canonical Asset Identity & Registry Authority (Asset Spine)**

That name matches what the repository most clearly proves.

## 37. What the Family Should Explicitly Own
Evidence-backed in-scope ownership for Phase B:
- canonical asset registry record in `equipment_master`
- canonical asset identity and canonical projection contract
- canonical registry search / resolver authority
- canonical taxonomy and verification authority
- canonical registry administration surfaces
- canonical health/drift detection over the registry

## 38. What the Family Should Explicitly Not Own
Evidence-backed out-of-scope ownership for this family:
- provider mapping CRUD (`asset_mappings`)
- external reconciliation engines
- dispatch assignment truth
- operational status engine derived from holds/assignments/transfers
- full transfer workflow state machine
- notification/task fanout attached to transfer processing

## 39. Highest Architectural Risks
1. **Legacy direct `equipment_master` CRUD weakens exclusive registry authority**
2. **Operational status is currently owned outside Spine, but may be mistaken for registry status**
3. **Transfer lifecycle exists both as simple Spine mutation and as dedicated transfer workflow engine**
4. **Provider identifiers live partly on canonical rows and partly in mapping records**
5. **Unconstrained family naming could accidentally pull adjacent owners into Spine**

## 40. Discovery Confidence
**Discovery confidence: High-Moderate.**

Why not low:
- primary route/service and consumer surfaces were directly reviewed
- overlapping routes were directly reviewed
- the family candidate is explicit in code comments, APIs, and UI labels

Why not absolute:
- repository still contains legacy and adjacent surfaces touching the same domain
- exclusivity is not fully enforced in the current implementation

## 41. Phase B Viability
**Phase B is viable only as a boundary-definition and constraint-setting exercise for the narrow family.**

It is **not** viable if Phase B assumes Asset Spine already owns:
- assignments
- all lifecycle workflows
- all status models
- all provider identity linkage

## 42. Final Recommendation
- **Constitutional Classification:** Independent constitutional family candidate, but only when narrowed to **Canonical Asset Identity & Registry Authority (Asset Spine)**
- **GO / NO-GO:** **GO — CONDITIONAL**
- **Discovery Confidence:** High-Moderate
- **Canonical Owner (or unresolved candidates):** Canonical owner candidate = Asset Spine; unresolved overlapping mutation surfaces = legacy `equipment_master` CRUD and adjacent lifecycle/status engines
- **Highest Architectural Risks:** direct legacy registry mutations, status-engine confusion, transfer-engine overlap, provider-ID split surfaces
- **Long-Term Roadmap Alignment:** **Conditionally aligned** (see §43)
- **Exact Recommended Next Action:** Authorize Phase B only to formalize the constitutional boundary as **registry/identity authority only**, explicitly demoting legacy `equipment_master` CRUD and all adjacent engines to non-owner or adjacent-owner status in the written architecture boundary

## 43. Long-Term Roadmap Alignment
Required verification against long-term architecture:

- **Preserves the original platform vision:** **Yes, conditionally.** Asset Spine already functions as the cross-platform canonical asset anchor used by admin, thread, health, and profile surfaces.
- **Reduces—not increases—architectural complexity:** **Conditionally.** It reduces complexity only if Phase B narrows the family to registry authority and refuses to absorb transfers, assignments, and mappings.
- **Does not introduce another canonical owner for responsibilities already owned elsewhere:** **Conditionally.** Without constraints it would. With constraints, it clarifies that Asset Spine owns registry truth while transfer/assignment/mapping engines remain adjacent.
- **Strengthens One Source of Truth:** **Yes.** The repository already points to `equipment_master` as SSoT; recognizing the Spine family makes that explicit.
- **Preserves Zero Drift:** **Conditionally.** Only if legacy direct registry writers are formally subordinated to the Spine boundary.
- **Preserves bounded ownership:** **Yes, if narrowed to identity/registry authority only.**
- **Does not create duplicate registries, identity systems, lifecycle engines, status engines, search systems, or business logic:** **Conditionally.** The repository already has adjacent engines; Phase B must avoid reclassifying them into the Spine family.
- **Keeps the platform converging toward fewer constitutional owners, not more:** **Conditionally.** Properly bounded, Spine reduces ambiguity. Unbounded, it increases named-owner overlap.

**Alignment statement:** **Conditionally aligned (required constraints identified).**

The repository supports recognizing Asset Spine as a constitutional family **only if the family is explicitly limited to canonical asset identity and registry authority**. Under that constraint, the move preserves the platform vision, strengthens One Source of Truth, and pushes the platform toward fewer true canonical owners. Without that constraint, it would introduce roadmap drift by overlapping with transfers, assignments, status engines, and mapping authorities already evidenced elsewhere in the repository.