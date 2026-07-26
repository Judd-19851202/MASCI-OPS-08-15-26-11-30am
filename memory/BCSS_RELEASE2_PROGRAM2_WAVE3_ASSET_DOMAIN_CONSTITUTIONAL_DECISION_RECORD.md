# BCSS RELEASE 2 · PROGRAM 2 · WAVE 3
# ASSET DOMAIN CONSTITUTIONAL DECISION RECORD
# FINAL ADOPTION · CONSTITUTIONAL FREEZE

## 1. Purpose
This document is the permanent constitutional decision record for the Asset Domain.

It reconciles the completed discovery set only:
- Broad Family 3D Discovery
- Family 3D-1 Phase A Discovery
- Family 3D-2 Phase A Discovery

No new discovery was performed here. No implementation was performed here. This document freezes only repository-backed ownership and preserves unresolved areas as unresolved.

## 2. Governing Inputs Preserved
The following completed discoveries are treated as authoritative inputs:
- `/app/memory/BCSS_RELEASE2_PROGRAM2_WAVE3_FAMILY3D_ASSET_MAPPING_RECONCILIATION_PHASEA_DISCOVERY.md`
- `/app/memory/BCSS_RELEASE2_PROGRAM2_WAVE3_FAMILY3D1_ASSET_SPINE_CANONICAL_REGISTRY_PHASEA_DISCOVERY.md`
- `/app/memory/BCSS_RELEASE2_PROGRAM2_WAVE3_FAMILY3D2_EXTERNAL_ASSET_MAPPING_RECONCILIATION_PHASEA_DISCOVERY.md`

## 3. Reconciliation Standard
This decision record applies the conservative freeze posture required by governance:
- if ownership is explicit and repository-backed, freeze it
- if ownership is implied but not explicit, record it as unresolved
- never resolve ambiguity by assumption
- preserve every previously adopted constitutional boundary exactly as adopted
- do not broaden Asset Spine beyond the repository-backed scope established in 3D-1
- do not resurrect standalone 3D-2 after its completed NO-GO discovery result

## 4. Core Reconciliation Outcome
The completed discovery set supports the following permanent constitutional reading:

1. **Asset Spine is adopted as the Canonical Asset Identity & Registry Authority.**
2. **Standalone Family 3D-2 is rejected.**
3. **Provider Integrations retain provider transport, provider synchronization, provider-specific mapping, and provider-specific reconciliation ownership.**
4. **Previously established adjacent family boundaries remain preserved:**
   - Family 3A = Core Admin Operations / generic admin visibility boundary
   - Family 3B = Operations Actions
   - Family 3C = Operational Events

## 5. Final Constitutional Answers to the Required Questions
1. **What is the canonical Asset Registry?**
   - `equipment_master`, constitutionally anchored to Asset Spine.

2. **Who owns canonical asset identity?**
   - Asset Spine.

3. **Who owns registry mutations?**
   - Asset Spine is the constitutional owner of canonical registry mutations; legacy `/admin/equipment-master` mutation remains a live repository overlap, not a second adopted constitutional owner.

4. **Who owns canonical lifecycle?**
   - Asset Spine owns canonical registry lifecycle on the canonical asset row only. Full operational lifecycle is not frozen here as an Asset Spine responsibility.

5. **Who owns provider integrations?**
   - Provider Integrations.

6. **Who owns provider synchronization?**
   - Provider Integrations.

7. **Who owns provider mappings?**
   - Provider Integrations through the `asset_mappings` lane. Standalone 3D-2 is not adopted.

8. **Who owns reconciliation?**
   - Provider Integrations own provider-specific reconciliation. No standalone 3D-2 owner is adopted.

9. **Who owns provider transport?**
   - Provider Integrations.

10. **Who owns source normalization?**
   - Split by proven boundary:
     - canonical registry taxonomy / identifier normalization = Asset Spine
     - provider payload/source normalization = Provider Integrations
     - no additional single Asset Domain owner is frozen beyond those two proven lanes

11. **Who owns operational status?**
   - **UNRESOLVED / ADJACENT OPERATIONS AUTHORITY.** Discovery proved this is not solely owned by Asset Spine and did not prove a replacement Asset Domain constitutional owner.

12. **Who owns assignments?**
   - **UNRESOLVED / ADJACENT OPERATIONS AUTHORITY.** Discovery proved assignment truth is not owned by Asset Spine and did not prove a separate Wave 3 Asset family owner.

13. **Who owns external identifiers?**
   - **UNRESOLVED / SPLIT IN REPOSITORY.** Discovery proved external/provider identifiers live both in `asset_mappings` and embedded on canonical asset rows in `equipment_master`; no singular owner is frozen.

14. **Who owns canonical identifiers?**
   - Asset Spine.

15. **Who owns audit?**
   - Split by proven boundary:
     - canonical asset mutation audit = Asset Spine
     - provider mapping audit = not proven as one unified constitutional owner and therefore not frozen here as singular ownership

16. **Who owns Trust participation?**
   - No independent Asset Domain Trust owner is adopted here. Asset surfaces may participate only as bounded consumers/projections where separately evidenced.

17. **Who owns notifications?**
   - **UNRESOLVED / NOT EVIDENCED** as an Asset Domain constitutional owner in the completed discoveries.

18. **Who owns Operations Actions?**
   - Family 3B.

19. **Who owns Operational Events?**
   - Family 3C.

20. **Who owns Admin visibility?**
   - Family 3A owns generic read-only admin visibility. Family-specific admin screens remain consumers of their owning family, not a separate visibility owner.

## 6. Formal Adoption — Asset Spine
Asset Spine is hereby adopted as:

**Canonical Asset Identity & Registry Authority**

This adoption is intentionally narrow and preserves the exact 3D-1 discovery boundary:
- canonical asset registry
- canonical asset identity
- canonical identifiers
- canonical registry search / resolution
- canonical registry administration
- canonical registry taxonomy / registry-side normalization
- canonical registry lifecycle on the canonical row

This adoption does **not** broaden Asset Spine into provider transport, provider synchronization, provider-specific mapping, provider-specific reconciliation, operational status, assignments, notifications, Trust engine ownership, Operations Actions, or Operational Events.

## 7. Formal Rejection — Standalone Family 3D-2
Standalone Family 3D-2 is hereby rejected.

Completed discovery already concluded **NO-GO** for standalone 3D-2 because repository evidence did **not** prove:
- one clean cross-provider owner
- one exclusive external-identifier persistence model
- one clear mutation owner
- one clear overwrite authority
- one tenant-safe isolation model
- one clean boundary from Asset Spine

Completed discovery also proved material ambiguity around:
- `equipment_master` versus `asset_mappings`
- external overwrite authority
- tenant isolation
- provider symmetry

This record does not reopen that decision.

## 8. Required Rejection Statement — Provider Ownership Retained
Provider Integrations retain ownership of:
- provider transport
- provider synchronization
- provider-specific mapping
- provider-specific reconciliation

This remains the constitutional rule unless future repository evidence proves otherwise.

## 9. Permanent Owner Matrix
| Capability | Constitutional Owner | Repository Owner | Future Phase |
|---|---|---|---|
| Canonical asset registry | Asset Spine | `routes/asset_spine.py` + `services/asset_spine.py` + `equipment_master` | 3D-1 Phase B only |
| Canonical asset identity | Asset Spine | `AssetSpine.project_asset()` + resolver + canonical reads over `equipment_master` | 3D-1 Phase B only |
| Canonical identifiers | Asset Spine | `equipment_master.id` / `asset_id` / `unit_number` resolver surfaces | 3D-1 Phase B only |
| Canonical registry search / resolution | Asset Spine | `/api/asset-spine/assets`, `/api/asset-spine/resolve`, taxonomy-by-unit resolver | 3D-1 Phase B only |
| Canonical registry administration | Asset Spine | Asset Spine admin routes and direct consumers | 3D-1 Phase B only |
| Canonical registry taxonomy / registry-side normalization | Asset Spine | Asset Spine taxonomy + canonical registry normalization surfaces | 3D-1 Phase B only |
| Canonical registry mutation authority | Asset Spine | Asset Spine create/update/retire/activate flows over `equipment_master` | 3D-1 Phase B only |
| Legacy direct equipment row mutation overlap | NON-CONSTITUTIONAL OVERLAP — DO NOT FREEZE AS OWNER | `/admin/equipment-master` in `server.py` | 3D-1 Phase B demotion/containment only |
| Canonical registry lifecycle on the canonical row | Asset Spine | canonical asset create/update/retire/activate/onboarding/transfer row-side behavior | 3D-1 Phase B only |
| Provider integrations | Provider Integrations | integration routers and services | Outside 3D-1 / no standalone 3D-2 |
| Provider transport | Provider Integrations | provider connector / integration lanes evidenced in integration discovery | Outside 3D-1 / no standalone 3D-2 |
| Provider synchronization | Provider Integrations | integration sync/dry-run lanes | Outside 3D-1 / no standalone 3D-2 |
| Provider mappings | Provider Integrations | `routes/integrations/mappings.py` over `asset_mappings` | No standalone 3D-2 |
| Provider-specific reconciliation | Provider Integrations | `asset_mapping_recon.py` + `maintainx_asset_sync.py` as provider-specific reconciliation surfaces | No standalone 3D-2 |
| Reconciliation proposal queue | Provider Integrations | `asset_mapping_proposals` + `asset_mapping_recon.py` | No standalone 3D-2 |
| MaintainX dry-run reconciliation diagnostics | Provider Integrations | `maintainx_asset_sync.py` + `maintainx_p0.py` + `maintainx_dryrun_reports` | No standalone 3D-2 |
| External identifiers | UNRESOLVED — split in repository | split across `asset_mappings` and embedded `equipment_master` fields | No freeze beyond current record |
| Source normalization — provider payloads | Provider Integrations | MaintainX dry-run and provider mapping/recon flows | No standalone 3D-2 |
| Source normalization — canonical registry taxonomy/identifier lane | Asset Spine | registry taxonomy / canonical normalization surfaces | 3D-1 Phase B only |
| Operational status | UNRESOLVED — adjacent operations authority | `routes/operations.py` per completed discovery evidence | Out of Asset Domain freeze scope |
| Assignments | UNRESOLVED — adjacent operations authority | `asset_assignments`, `dispatch_assignments`, operations/dispatch surfaces per completed discovery evidence | Out of Asset Domain freeze scope |
| Canonical asset mutation audit | Asset Spine | `admin_audit_log` + `audit_events` for canonical asset mutations | 3D-1 Phase B only |
| Provider mapping audit | UNRESOLVED / PROVIDER-LOCAL ONLY | partial row notes, sync logs, dry-run reports; no singular constitutional owner proven | No standalone 3D-2 |
| Trust participation | UNRESOLVED / PARTICIPATION ONLY | bounded projections only; no independent asset-owned Trust engine evidenced | Out of Asset Domain freeze scope |
| Notifications | UNRESOLVED / NOT EVIDENCED | documentation/readiness hints only in completed discovery | Out of Asset Domain freeze scope |
| Operations Actions | Family 3B | `operations_actions` family per previously adopted boundary | Separate family |
| Operational Events | Family 3C | `operational_events` family per previously adopted boundary | Separate family |
| Generic admin visibility | Family 3A | core admin visibility / read-only admin operations boundary | Separate family |

## 10. Prohibited Ownership Matrix
| Family / Constitutional Boundary | May NEVER Own |
|---|---|
| Asset Spine (Family 3D-1) | provider transport; provider authentication; provider synchronization; provider-specific mapping CRUD; provider-specific reconciliation queues; Operations Actions; Operational Events; notification engine; Trust engine; generic admin visibility ownership |
| Provider Integrations | canonical asset identity; canonical asset registry truth; canonical identifiers; canonical registry search authority; canonical registry administration; generic admin visibility ownership |
| Family 3B Operations Actions | canonical asset registry; canonical asset identity; provider transport; provider synchronization; Operational Events ownership; notification engine ownership by implication |
| Family 3C Operational Events | canonical asset identity; canonical asset registry; provider mapping ownership; provider transport ownership; Operations Actions ownership |
| Family 3A Core Admin Operations | canonical asset identity; canonical asset registry truth; provider mapping ownership; provider synchronization; Operations Actions ownership; Operational Events ownership |
| Rejected Standalone 3D-2 Hypothesis | any constitutional ownership whatsoever as an independent family unless future repository evidence proves this record incorrect |

## 11. Permanent Boundary Statements
### Family 3D-1 owns…
Family 3D-1 owns canonical asset identity, canonical asset registry authority, canonical identifiers, canonical registry search/resolution, canonical registry administration, canonical registry taxonomy/identifier normalization, and canonical registry lifecycle on the canonical asset row only.

### Provider Integrations own…
Provider Integrations own provider transport, provider synchronization, provider-specific mapping, provider-specific reconciliation, proposal-queue style provider cleanup/reconciliation, and provider read-first diagnostics.

### Family 3B owns…
Family 3B owns Operations Actions and remains the canonical command boundary. No Asset family or provider integration surface may absorb that ownership by implication.

### Family 3C owns…
Family 3C owns Operational Events and remains the canonical normalized event boundary. Asset mapping, asset registry, and provider integrations may consume or enrich against those events but do not own them.

### Family 3A owns…
Family 3A owns generic read-only admin visibility and core admin operations visibility boundaries. Asset-specific admin pages remain consumers of their owning family and do not convert visibility into ownership.

### Unresolved boundaries remain unresolved…
Operational status, assignments, external identifiers as a singular owner, unified provider mapping audit ownership, Trust participation ownership, and notification ownership are not broadened or reclassified by this record because the completed discoveries did not prove singular constitutional ownership.

## 12. Implementation Guardrails
Future Phase B and later implementation must:
- never duplicate registry
- never duplicate mapping
- never duplicate reconciliation
- never duplicate identity
- never duplicate status
- never duplicate audit
- never duplicate Trust
- never duplicate notifications
- never broaden Asset Spine beyond canonical asset identity & registry authority
- never resurrect standalone 3D-2 without new repository evidence
- always treat this record as the authority that implementation follows

## 13. Constitutional Freeze
The Asset Domain constitutional architecture is now frozen under this record.

Future implementation must conform to this record.

Future discoveries may not redefine these boundaries unless repository evidence proves this document incorrect.

Feature requests shall not modify constitutional ownership.

Only repository evidence may reopen this document.

## 14. Remaining Asset Work
| Bucket | Remaining Asset Work | Constraint |
|---|---|---|
| Phase B | Authorize only the bounded 3D-1 Phase B track for constitutional boundary formalization around Asset Spine registry/identity authority | Must not broaden beyond 3D-1 discovery scope |
| Implementation | Implement only repository-backed 3D-1 boundary hardening and legacy overlap demotion if explicitly authorized later | Must not create standalone 3D-2 |
| Verification | Verify any later 3D-1 implementation against this record, especially no absorption of mappings, reconciliation, assignments, operational status, Trust, or notifications | Must use this record as acceptance authority |
| Formal Adoption | After any authorized 3D-1 Phase B is verified, issue the bounded formal adoption artifact for 3D-1 only | 3D-2 remains rejected unless new repository evidence exists |

## 15. Wave 3 Status
**Wave 3 Asset Domain constitutional architecture status: CONDITIONALLY COMPLETE.**

Support from the completed discovery set:
- the broad 3D hypothesis has been reconciled and split
- 3D-1 has a repository-backed narrow constitutional adoption path
- 3D-2 has a repository-backed standalone NO-GO result
- adjacent family boundaries 3A / 3B / 3C are preserved
- unresolved ownerships have been explicitly preserved as unresolved instead of guessed

This is conditionally complete because the constitutional record is now frozen, but the only remaining authorized implementation path is the bounded 3D-1 Phase B track.

## 16. Exactly One Recommended Next Action
**A. Authorize 3D-1 Phase B**

## 17. Final Conclusion
**The Asset Domain constitutional architecture is hereby adopted and frozen.**