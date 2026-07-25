# MASCI OPS · Operational Truth Spine
## Release 2 · Program 2 · Wave 3 · Family 1
## OCC Health Aggregator
## Capability Verification & Repository Discovery

Date: 2026-07-25

Status: DISCOVERY COMPLETE · GO RECOMMENDED FOR A FUTURE BOUNDED PHASE B

---

## 1. Executive conclusion

Repository evidence proves the **OCC Health Aggregator already exists** and is **live**.

Repository-backed determination:

- capability status: **Present**
- backend runtime family exists
- frontend operator surface exists
- route is registered and active
- family is **not** a canonical owner
- family is an **AGGREGATOR**
- canonical owner relationship points to **`platform_attestation`**
- truth subject is **`shared_operational_posture`**

The family is not abandoned and not merely planned. It is an active aggregate posture surface over existing child endpoints.

However, repository evidence also proves that this family has **significant overlap** with:

- Trust Spine
- Operations Trust Center
- Admin Operations / System Health
- Production Certification
- Deploy Readiness

and therefore any future implementation must remain tightly bounded and must not attempt consolidation or cross-family redesign.

---

## 2. Repository evidence summary

Primary evidence proving existence and activity:

- `/app/backend/routes/occ_health_aggregator.py`
- `/app/backend/lib/canonical_truth.py`
- `/app/backend/server.py`
- `/app/frontend/src/pages/OperationsControlCenter.jsx`
- `/app/frontend/src/app/routing/AppRoutes.jsx`

Supporting evidence:

- `/app/backend/tests/test_track_25_sprint_2_occ_trust_layer.py`
- `/app/backend/tests/test_checkpoint_d2_runtime_truth_normalization.py`
- `/app/backend/tests/test_c2_checkpoint.py`
- `/app/backend/tests/test_track_28_09d_backup_health_aggregator.py`
- `/app/memory/BCSS_RELEASE2_PROGRAM2_CHECKPOINT4_SURFACE_CLAIM_MATRIX.md`
- `/app/memory/BCSS_RELEASE2_PROGRAM2_CHECKPOINT7_PHASEA_DISCOVERY.md`
- `/app/memory/BCSS_RELEASE1_PROGRAM1_CHECKPOINT3_TRUTH_SUBJECT_REGISTRY.md`

---

## 3. Capability classification

**Capability classification: Present**

Why:

- runtime route exists
- runtime route is registered
- canonical truth registry entry exists
- frontend operator surface exists
- tests exist
- documentation references exist
- route contract returns structured posture output now

This is not `Partial`, `External`, `Planned`, or `Not Applicable` by repository evidence.

---

## 4. Runtime inventory

### Primary backend runtime file
- `/app/backend/routes/occ_health_aggregator.py`

### Route registration
- `/app/backend/server.py:3875-3878`

### Route registration call
- `register_occ_health_routes(api_router, require_admin)`

### Route function
- `GET /api/admin/occ/health`

### Supporting runtime dependencies explicitly imported by the route
- `lib.canonical_truth.canonical_truth_surface`
- `lib.canonical_truth.derived_truth_payload`
- `lib.runtime_identity.runtime_identity_public_payload`
- `httpx`
- child endpoint fanout over internal backend base URL

### Additional adjacent runtime files directly connected by route behavior
- `/app/backend/routes/operations_control.py`
- `/app/backend/routes/occ_trust_events.py`

---

## 5. Frontend inventory

### Primary frontend surface
- `/app/frontend/src/pages/OperationsControlCenter.jsx`

### Route mount
- `/app/frontend/src/app/routing/AppRoutes.jsx`
- mounted route: `/admin/operations-control`

### OCC frontend truth-layer behavior
- calls `GET /api/admin/occ/health` through `fetchTrustLayer()`
- renders read-only health layer above maintenance console
- displays overall posture, counts, sections, cards, evidence drawers, refresh controls, and drill-down links

### Additional adjacent frontend references
- `/app/frontend/src/components/admin/trust/TrustPrimitives.jsx`
- `/app/frontend/src/pages/admin/AdminDiagnostics.jsx`
- `/app/frontend/src/pages/admin/AdminMaintenance.jsx`

### Frontend status
- live
- mounted
- operator-visible
- not abandoned

---

## 6. API inventory

### Primary family API
- `GET /api/admin/occ/health`

### Route contract fields proved in code
- `generated_at`
- `overall_status`
- `overall_canonical`
- `truth_surface`
- `truth_relationship`
- `runtime_identity`
- `counts`
- `canonical_counts`
- `root_cause_groups`
- `unique_critical_root_causes`
- `total_cards`
- `sections`

### Child APIs directly probed by this family
- `/api/health`
- `/api/version`
- `/api/admin/operations-control/overview`
- `/api/admin/recovery/snapshot`
- `/api/admin/r2/lifecycle/health`
- `/api/admin/backups-scheduler-state`
- `/api/admin/email-routing/v2/status`
- `/api/ai/gateway/status`
- `/api/admin/draft-health`
- `/api/admin/sessions/recent`
- `/api/admin/governance/summary`
- `/api/admin/production-certification`
- `/api/admin/integrations/health`

### API-family determination
This family is a **fanout aggregator API**, not a source-truth API.

---

## 7. Data inventory

The OCC aggregator itself does **not** directly query MongoDB collections inside `occ_health_aggregator.py`.

Instead, it fans out to child APIs that are backed by their own collections and runtime sources.

### Repository-proven data structures consumed indirectly through child endpoints
- runtime identity bundle
- operational registry overview payload
- recovery snapshot payload
- R2 lifecycle health payload
- scheduler state payload
- email routing v2 status payload
- AI gateway status payload
- draft health payload
- sessions payload
- governance summary payload
- production certification payload
- integrations health payload

### Database-support determination
Database structures support this family **indirectly**, not through direct route-local collection queries.

---

## 8. Truth Subject

Repository-proven Truth Subject:

- `shared_operational_posture`

Evidence:

- `/app/backend/lib/canonical_truth.py:216-245`

Interpretation:

- this is a shared operational posture summary
- it is not workflow lifecycle truth
- it is not operational trust score
- it is not deployment readiness truth
- it is not certification truth

---

## 9. Canonical owner

Repository-proven canonical owner relationship:

- `canonical_owner_id = platform_attestation`

Evidence:

- `/app/backend/lib/canonical_truth.py:216-245`

Additional upstream owners:

- `platform_attestation`
- `integration_truth`
- `shared_auth_session`

The primary canonical owner relationship for the aggregate surface is therefore repository-bound to **`platform_attestation`**, while multiple upstream owners also feed child truths.

---

## 10. Family classification

Repository-proven family classification:

- `AGGREGATOR`

Evidence:

- `/app/backend/lib/canonical_truth.py:216-245`
- `role=AGGREGATOR`
- `owner_type="derived"`
- route contract text explicitly says upstream canonical owners remain authoritative for their own subjects

This family is **not**:

- CANONICAL_OWNER
- DERIVED_CONSUMER
- VALIDATOR

---

## 11. Consumer relationships

### Direct consumer relationship
- `/app/frontend/src/pages/OperationsControlCenter.jsx` consumes `/api/admin/occ/health`

### Secondary repository consumers / adjacent readers
- Admin Diagnostics references OCC health
- Admin Maintenance references OCC overview paths
- trust primitives provide shared rendering for OCC cards

### Relationship type
- one aggregate API
- one primary operator dashboard
- several adjacent diagnostic or navigation references

---

## 12. Operator workflow supported

The operator workflow supported by this family is:

- open OCC
- refresh a live multi-domain health snapshot
- inspect overall posture
- inspect section-level cards
- open evidence drawers
- drill into source pages/endpoints
- move from trust layer to action layer in the maintenance console

This is a **read-only operational posture and triage workflow**, not a certification workflow and not a deployment workflow.

---

## 13. Evidence sources feeding the family

Repository-proven evidence sources include:

- child endpoint fanout
- runtime identity bundle
- per-card evaluator evidence
- auth passthrough to child admin routes

Card-level evidence sources explicitly include:

- API liveness
- runtime version / uptime
- maintenance operations registry
- recovery snapshot
- R2 lifecycle health
- backup scheduler loop
- email routing status
- AI gateway status
- draft health
- session inventory
- governance summary
- production certification status
- integration probes

This is a wide multi-source posture aggregator.

---

## 14. Unknown handling

Repository evidence proves explicit unknown handling exists.

Examples:

- route comments state: “Honest UNKNOWN over fake GREEN”
- child endpoint failures degrade the specific card
- route returns partial snapshot even when some probes fail
- missing / unreachable data becomes `UNVERIFIABLE` or `MISMATCH` depending on evaluator semantics
- source probe state is preserved as `probe_failure` vs `source_success`

Unknown handling is therefore **present and active**, though not yet normalized into full OTS claim-bound disclosures per aggregate and per card.

---

## 15. Contradiction handling

Repository evidence proves **partial contradiction handling** exists.

Examples:

- `truth_relationship.conflicts` is emitted when aggregate status differs from canonical summary
- `root_cause_groups` prevent double-counting certain shared causes
- probe-failure vs source-failure separation reduces false-positive health claims

However:

- there is no fully explicit first-class contradiction inventory for the aggregate family comparable to later OTS bounded patterns
- contradictions are handled operationally, but not yet as a full constitutional claim-bound surface

Determination:

- contradiction handling status: **Partial but present**

---

## 16. Duplicate analysis — Trust Spine overlap

Overlap with Trust Spine is **real but indirect**.

Trust Spine owns:
- `workflow_lifecycle_truth`

OCC Health Aggregator summarizes:
- shared operational posture
- including cards fed by certification/governance/runtime/recovery/integration signals

Overlap type:
- adjacent posture consumption
- not same truth subject
- not same owner

Risk:
- operators may read OCC aggregate posture as stronger than underlying lifecycle truth if claim boundaries remain loose

---

## 17. Duplicate analysis — Operations Trust Center overlap

Overlap with Operations Trust Center is **high**.

Operations Trust Center:
- truth subject: `shared_operational_trust_score`
- role: `DERIVED_CONSUMER`

OCC Health Aggregator:
- truth subject: `shared_operational_posture`
- role: `AGGREGATOR`

Overlap type:
- both summarize broad platform operations condition
- both are operator-facing
- both can be semantically over-read as stronger truth than they own

Risk:
- duplicate aggregate/operator-trust posture narratives

---

## 18. Duplicate analysis — Admin Operations overlap

Overlap with Admin Operations / system-health surfaces is **high**.

Evidence:

- OCC consumes operations-control overview
- diagnostics/admin ops pages reference OCC and overlapping health signals
- checkpoint artifacts already flag `admin_ops.py` as overlapping health surface

Risk:
- multiple health dashboards answering similar “is the platform okay?” questions

---

## 19. Duplicate analysis — Production Certification overlap

Overlap with Production Certification is **material**.

Evidence:

- OCC includes a production certification card
- production certification route is one of the probed sources
- OCC overall posture can therefore be read adjacent to certification posture

Risk:
- aggregate posture can be mistaken for certification authority

---

## 20. Duplicate analysis — Deploy Readiness overlap

Direct overlap with Deploy Readiness is **adjacent but not primary**.

Evidence:

- checkpoint artifacts classify deploy-readiness as overlapping family in the broader operational trust ecosystem
- OCC is used as trust center / operations center and is adjacent to readiness/diagnostics questions

Risk:
- operators may conflate aggregate posture with deploy gating even though the route does not own deploy-readiness truth

---

## 21. Duplicate health engines present?

**Yes.**

Repository evidence proves multiple health-style engines / surfaces exist:

- OCC Health Aggregator
- system-health / diagnostics surfaces
- Operations Trust Center posture/score
- Platform Trust Validator
- recovery snapshot posture surfaces

Determination:
- duplicate health engines: **present**

---

## 22. Duplicate scoring engines present?

**Yes, adjacent scoring/evaluation duplication exists.**

Examples:

- Operations Trust Center score model
- backup trust score model
- validator banding logic
- OCC worst-status aggregation logic

They are not identical engines, but repository evidence proves multiple overlapping status/scoring mechanisms exist.

Determination:
- duplicate scoring engines: **present**

---

## 23. Duplicate truth engines present?

**Not as canonical-owner duplication inside OCC itself, but duplicate truth-like aggregate layers are present.**

The registry still keeps ownership separate, which prevents a direct owner conflict.

However, there are multiple derived/aggregate/validator layers projecting operational truth-adjacent posture.

Determination:
- duplicate truth engines: **adjacent derived duplication present, direct canonical-owner duplication not proven**

---

## 24. Duplicate dashboards present?

**Yes.**

Repository evidence proves multiple dashboards/surfaces answer related operational-health or trust questions:

- `/admin/operations-control`
- `/admin/email`
- `/admin/diagnostics`
- `/admin/storage-recovery`
- `/admin/governance-trust`
- `/admin/system-health`

Determination:
- duplicate dashboards: **present**

---

## 25. Existing tests

Repository-proven relevant tests include:

- `/app/backend/tests/test_track_25_sprint_2_occ_trust_layer.py`
- `/app/backend/tests/test_checkpoint_d2_runtime_truth_normalization.py`
- `/app/backend/tests/test_c2_checkpoint.py`
- `/app/backend/tests/test_track_28_09d_backup_health_aggregator.py`
- `/app/backend/tests/test_track_25_00_occ_discoverability.py`
- `/app/backend/tests/test_track_25_01_occ_consolidation.py`

Test coverage areas proven by inspection include:

- required sections present
- card manifest consistency
- evaluator degradation honesty
- evaluator truth mapping
- worst-status ordering
- OCC endpoint structure
- truth-surface presence

---

## 26. Existing documentation

Repository-proven documentation references include:

- `/app/memory/BCSS_RELEASE2_PROGRAM2_CHECKPOINT4_IMPLEMENTATION_GAP_REGISTER.md`
- `/app/memory/BCSS_RELEASE2_PROGRAM2_CHECKPOINT4_SURFACE_CLAIM_MATRIX.md`
- `/app/memory/BCSS_RELEASE2_PROGRAM2_CHECKPOINT7_PHASEA_DISCOVERY.md`
- `/app/memory/BCSS_RELEASE2_PROGRAM2_CHECKPOINT8_PHASEA_DISCOVERY.md`
- `/app/memory/BCSS_RELEASE1_PROGRAM1_CHECKPOINT3_TRUTH_SUBJECT_REGISTRY.md`
- `/app/memory/platform_trust_inventory.json`

Documentation status:
- existing documentation is **present and substantial**

---

## 27. Repository risks

Primary repository risks proved by evidence:

1. **Aggregate overclaim risk**
   - OCC is an aggregator but can be read as stronger truth than its role supports.

2. **Cross-family semantic overlap**
   - strong overlap with OTC, validator, diagnostics, admin ops, certification, and recovery.

3. **Mixed-subject aggregation risk**
   - one aggregate surface covers runtime, recovery, AI, integrations, governance, sessions, daily reports, and certification signals.

4. **Bounded-claim ambiguity**
   - no explicit OTS-style claim ceiling disclosure in the route contract itself.

5. **Child-owner replacement risk**
   - if presented loosely, the aggregate can visually overshadow its child canonical owners.

---

## 28. Architectural conflicts

Repository-proven architectural conflicts / tensions:

- OCC is an active aggregate “trust center” while other adjacent families also answer trust/health questions.
- The route sets `canonical_owner_route` to `/api/admin/occ/health` in its `derived_truth_payload` call even though registry `canonical_owner_id` is `platform_attestation`; this is structurally live but semantically sensitive and must be bounded carefully in any future phase.
- The family spans many upstream subjects, making it a larger and riskier candidate than narrowly bounded two-file derived-consumer families.
- It is already identified in prior checkpoint artifacts as a duplicate/overlap family, not a next-smallest safe candidate.

---

## 29. Constitutional validity as currently implemented

**Yes, but only as an aggregate posture family.**

Repository evidence supports the following constitutional validity statement:

- valid as an **AGGREGATOR**
- valid as a **derived** operational posture surface
- valid as **non-owner** aggregate posture over child endpoints
- **not** valid as canonical source truth
- **not** valid as certification authority
- **not** valid as deployment-readiness authority

So the family is constitutionally valid **within its current aggregate role**, but not as a broader truth-authority surface.

---

## 30. Complete family status determination

### Does an OCC Health Aggregator already exist?
Yes.

### Where is it located?
- backend: `/app/backend/routes/occ_health_aggregator.py`
- frontend: `/app/frontend/src/pages/OperationsControlCenter.jsx`

### Is it complete, partial, legacy, duplicated, or abandoned?
Best repository-backed characterization:
- **Present, live, duplicated/overlapping, and active**
- not abandoned
- not merely legacy
- not merely partial

### What runtime files exist?
- `occ_health_aggregator.py`
- `server.py` registration

### What frontend surfaces exist?
- `OperationsControlCenter.jsx`
- route `/admin/operations-control`

### What APIs exist?
- `GET /api/admin/occ/health`
- plus many child probed APIs listed above

### What database structures support it?
Indirectly supported through child endpoints; no direct Mongo queries in the aggregator route itself.

---

## 31. GO / NO-GO recommendation for future Phase B

## NO-GO for immediate broad implementation

Repository evidence does **not** support this family as the next smallest safe bounded implementation candidate.

Why:

- it already exists and is active
- it is broad, multi-domain, and highly overlapping
- it is larger in scope than OTC or validator-style bounded families
- it has multiple duplicate health / truth-adjacent overlaps
- future work would need strong claim-boundary discipline and careful non-consolidation

## GO only for a future tightly bounded constitutional Phase B if separately authorized

That future Phase B would need to be explicitly limited to:

- claim-boundary corrections
- aggregate-role preservation
- child-owner non-override guarantees
- unknown / contradiction disclosure
- zero consolidation of adjacent families

Therefore the discovery recommendation is:

- **Immediate broad Phase B: NO-GO**
- **Future narrow bounded constitutional Phase B, if explicitly authorized: GO-possible**

---

## 32. Final recommendation

### Capability verdict
- **Present**

### Constitutional verdict
- **Valid as a live aggregate posture family**

### Implementation readiness verdict
- **Not the next-smallest-safe candidate for broad implementation work**

### Recommended future disposition
- preserve as active aggregate family
- do not redesign during discovery
- if a later Phase B is authorized, keep it tightly bounded to claim architecture and overlap control only

---

## 33. Roadmap Dependency Verification

Repository evidence indicates this family is **not completely independent** of survivability-adjacent domains.

Why:

- OCC directly probes `/api/admin/recovery/snapshot`
- OCC directly probes `/api/admin/r2/lifecycle/health`
- OCC directly probes `/api/admin/backups-scheduler-state`
- OCC includes storage & recovery posture as one of its core sections

Therefore:

- this family has **repository-backed dependency on backup/recovery state as an input surface**
- it is **not** a backup, recovery, disaster-recovery, business-continuity, rollback, or Wave 1 deployment-readiness program of its own
- but it is **not completely independent** from those future survivability concerns, because it aggregates their current signals into operational posture

Roadmap conclusion:

- OCC Health Aggregator is an **adjacent consumer of survivability-related signals**, not the survivability program itself
- future Platform Survivability Program remains a distinct mandatory roadmap milestone before production deployment
- OCC discovery must not be mistaken for completion of backup, recovery, DR, business continuity, rollback, or Wave 1 deployment readiness work
