# BCSS Release 2 · Program 2 · Checkpoint 6
## Phase A — Discovery, Claim Inventory, and Bounded Adoption Proposal

Date: 2026-07-25

Status: PHASE A COMPLETE

This artifact derives constitutional authority from:
- `/app/memory/OTS_v1_0_CONSTITUTIONAL_REFERENCE_BASELINE.md`
- `/app/backend/lib/ots_truth.py`
- Checkpoint 4 surface and truth-subject inventories
- Checkpoint 5 starter adoption records

It establishes no new architecture.

---

## 1. Repository Discovery Summary

Repository discovery confirms that Checkpoint 5 adopted the following BCSS families into the canonical OTS pipeline:

1. `/api/platform/data-truth`
2. `/api/admin/recovery/snapshot`
3. `/api/admin/backup-verification/*`
4. `/api/admin/backup-trust-score`
5. `/api/admin/deployment-readiness/*`

Repository discovery also confirms a remaining cluster of BCSS admin trust, health, and operator-facing surfaces that still expose operational claims without a full canonical OTS truth-card projection.

### Confirmed remaining BCSS operator-facing / operator-consumed surfaces

#### Primary trust / validation / health routes
- `/api/admin/platform/status`
- `/api/admin/trust-spine`
- `/api/admin/operations-trust-center`
- `/api/admin/platform-trust/validate`
- `/api/admin/occ/health`
- `/api/admin/occ/trust-events`
- `/api/admin/system-health`
- `/api/admin/production-certification`
- `/api/admin/deploy-readiness`

#### Primary operator-visible consumers
- `frontend/src/components/PlatformTrustDashboard.jsx`
- `frontend/src/components/OperationsTrustCenter.jsx`
- `frontend/src/components/PlatformTrustValidator.jsx`
- `frontend/src/pages/admin/AdminGovernanceTrust.jsx`
- `frontend/src/pages/admin/AdminDiagnostics.jsx`
- `frontend/src/pages/admin/AdminIdentitySecurity.jsx`
- `frontend/src/pages/admin/SystemHealth.jsx`
- `frontend/src/pages/AdminDeployReadiness.jsx`
- `frontend/src/pages/admin/AdminEmail.jsx`

### Discovery conclusion

The repository does **not** support treating all remaining trust/health/admin surfaces as one implementation group.

The remaining surfaces split into at least five distinct constitutional families:

1. **Runtime attestation** — `/api/admin/platform/status`
2. **Workflow lifecycle truth** — `/api/admin/trust-spine` + `PlatformTrustDashboard`
3. **Platform validation** — `/api/admin/platform-trust/validate` + `PlatformTrustValidator`
4. **Derived operational trust** — `/api/admin/operations-trust-center` + `OperationsTrustCenter`
5. **Composite health / event aggregators** — `/api/admin/occ/health`, `/api/admin/occ/trust-events`, `/api/admin/system-health`, domain landing shells

These families do **not** share one Truth Subject, one evaluation path, and one projection path. Grouping them together would violate the bounded grouping rule.

---

## 2. Remaining Claim Inventory

### Unsupported-claim pattern observed in the repository

The remaining surfaces mostly expose one or more of the following without a full OTS truth-card contract:

- operator-facing red / amber / green or trusted / failing posture labels
- validation or certification language
- composite trust summaries
- route-level claims that are not yet bounded by explicit `ots_truth`, `compatibility`, and claim-ceiling disclosure

### Remaining unsupported-claim inventory

1. **`/api/admin/platform/status`**
   - canonical owner route exists
   - no route-level `ots_truth` projection currently exposed
   - risk: authoritative runtime truth remains implicit rather than claim-bounded

2. **`/api/admin/trust-spine`**
   - canonical owner route exists
   - exposes `platform_band`, `canonical_status`, workflow bands, reasons, remediation
   - currently has `truth_relationship` only
   - no `ots_truth` / no compatibility block

3. **`PlatformTrustDashboard.jsx`**
   - renders workflow lifecycle truth with strong operator language
   - no explicit OTS truth-card disclosure despite canonical-owner framing

4. **`/api/admin/platform-trust/validate`**
   - validator route exists
   - exposes final band and red/amber reasons
   - currently has `truth_relationship` only
   - no route-level `ots_truth` / no compatibility block

5. **`PlatformTrustValidator.jsx`**
   - renders “Trusted / Critical / Attention” outcomes
   - no explicit permitted-claim / claim-ceiling disclosure

6. **`/api/admin/operations-trust-center`**
   - derived consumer route exists
   - exposes trust score, score band, narrative, subsystem health, findings, actions
   - currently has `truth_relationship` only
   - no `ots_truth` / no compatibility block

7. **`OperationsTrustCenter.jsx`**
   - renders “Can I trust this platform to run operations today?”
   - strong derived trust wording remains operator-visible
   - no explicit OTS claim-ladder disclosure

8. **`/api/admin/occ/health`**
   - composite aggregator over many child endpoints
   - returns `truth_relationship` only
   - no route-level OTS truth-card projection

9. **`/api/admin/occ/trust-events`**
   - recent trust-events feed has no OTS mapping at all
   - composite event fan-in over audit, scheduler, deploy blockers, ops audit

10. **`/api/admin/system-health`**
    - operator-facing health card rollup
    - no OTS truth-card projection

11. **`/api/admin/production-certification`**
    - certification vocabulary exposed
    - no OTS truth-card projection

12. **`/api/admin/deploy-readiness`**
    - legacy readiness route still heavily consumed in UI
    - no OTS truth-card projection
    - overlaps with already-adopted `/api/admin/deployment-readiness`

---

## 3. Truth Subject Coverage Matrix

This matrix is the Phase A canonical planning artifact for Checkpoints 6–10.

| Surface | Truth Subject | Current Evaluation Path | Current Projection Path | Current Claim Ceiling | OTS Bound | Evidence Source | Duplicate Evaluation | Duplicate Projection | Operator Visible | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| `/api/admin/platform/status` | `bcss_runtime_state_authority` | `lib.platform_status.platform_status(app)` | direct route payload | `VERIFIED` (CP4 target) | Partial — registry only | runtime identity + DB authority + route inventory | No major duplicate owner | Used indirectly by validators / diagnostics | Indirect | Unadopted runtime owner surface |
| `/api/admin/trust-spine` | `workflow_lifecycle_truth` / canonical surface `trust_spine` | direct aggregation over `trust_spine_events` + `WORKFLOW_EXPECTED_STAGES` | direct route payload + drilldown payload | `VALIDATED` | Partial — `truth_relationship` only | `trust_spine_events` | Upstream for production certification and operations trust center | projected to dashboard + admin email embeds downstream | Yes | Highest-value remaining canonical owner |
| `PlatformTrustDashboard.jsx` | `workflow_lifecycle_truth` via `trust_spine` | consumes `/api/admin/trust-spine` | dashboard table + drilldown | inherited `VALIDATED` | Partial — owner panel only | route payload | No duplicate evaluation in UI | single dashboard projection | Yes | Unadopted UI consumer of canonical owner |
| `/api/admin/platform-trust/validate` | `platform_validation_truth` | defensive validation over system, routing, audit, workflow delivery, PM coverage, dead-letter | direct route payload | `VALIDATED` | Partial — `truth_relationship` only | admin-safe evidence blocks + `email_routing_audit_v2` | Some overlap with system-health and deploy-readiness conclusions | projected in email page | Yes | Clean bounded validator family |
| `PlatformTrustValidator.jsx` | `platform_validation_truth` | consumes validator route | card/grid projection | inherited `VALIDATED` | Partial — owner panel only | route payload | No duplicate evaluation in UI | single card projection | Yes | Unadopted validator consumer |
| `/api/admin/operations-trust-center` | `shared_operational_trust_score` | `compute_categorized_score()` over trust spine + master-data + audit counts | direct route payload | `CORRELATED` | Partial — `truth_relationship` only | trust spine payload + master-data findings + trend history | Duplicates trust scoring posture not source truth | projected in email page | Yes | Derived trust family |
| `OperationsTrustCenter.jsx` | `shared_operational_trust_score` | consumes OTC route | trust center dashboard | inherited `CORRELATED` | Partial — owner panel only | route payload | No duplicate evaluation in UI | single trust center projection | Yes | Unadopted derived consumer |
| `/api/admin/occ/health` | composite `shared_operational_posture` | fanout probe aggregator over child endpoints | section/card payload | `CORRELATED` | Partial — `truth_relationship` only | child endpoint probes | Yes — duplicates health rollups from system-health and domain shells | projected in diagnostics / OCC | Yes | Composite aggregator; larger scope |
| `/api/admin/occ/trust-events` | composite trust-events feed (no BCSS canonical OTS binding yet) | fanout over audit, scheduler, deploy-readiness, ops audit | event feed payload | Undefined in OTS terms | No | child endpoint/event fan-in | Yes — duplicates blocker / auth-failure summaries elsewhere | projected in governance + identity pages | Yes | Not ready for smallest-safe CP6 first adoption |
| `/api/admin/system-health` | composite operational health | `compute_system_health()` over runtime, db, backup, auth, integrations | health cards payload | likely `CORRELATED` if later bound | No | DB ping, lineage, integration storage, audit counts | Yes — overlaps OCC and validator conclusions | projected in SystemHealth + Diagnostics | Yes | Mixed-subject aggregator |
| `/api/admin/production-certification` | adjacent operational certification concept | `lib.production_certification.build_certification(db)` over trust spine terminal events | direct route payload | `VALIDATED` (CP4 matrix) | No | `trust_spine_events` terminal evidence | Yes — shares lifecycle evidence with trust spine | projected in governance / diagnostics / AI Ops | Yes | Separate certification family |
| `/api/admin/deploy-readiness` | legacy deploy readiness / certification-like posture | `routes/deploy_readiness.py` custom checks | direct route payload | functionally bounded readiness only | No | Mongo / indexes / R2 / integrations / seed / admin password checks | Yes — overlaps adopted `/api/admin/deployment-readiness` | projected in deploy page + governance + diagnostics + trust-events | Yes | Legacy duplicate family |

---

## 4. Evidence-Backed Priority Matrix

| Candidate family | Files changed if adopted | Unsupported claim reduction | Architectural risk | Boundary fit | Recommendation |
|---|---:|---|---|---|---|
| `trust_spine` API + dashboard | Low | High — canonical owner becomes explicitly claim-bound; downstream families gain anchored upstream truth | Low | Strong Wave 3 fit | **P0** |
| `platform_trust_validator` API + component | Low | Medium — one validator family bound | Low | Strong Wave 3 fit | P1 |
| `operations_trust_center` API + component | Low-medium | Medium — one derived trust family bound | Low | Strong Wave 3 fit | P1 |
| `platform_status` owner route | Low | Medium — runtime owner becomes explicit, but operator-facing reduction is smaller than trust spine | Low | Wave 3 fit | P1 |
| `occ/health` aggregator family | Medium-high | Medium | Medium-high — composite fanout and multiple imported subjects | Weak for smallest-safe first move | P2 |
| `occ/trust-events` family | Medium-high | Medium | High — no clean existing OTS subject binding in current repo | Weak | P2 |
| `system-health` family | Medium | Medium | High — mixed subjects, duplicate health semantics | Weak | P2 |
| `production-certification` family | Medium | Medium | Medium — certification vocabulary and cross-surface consumers | Outside smallest-safe first repair | P2 |
| legacy `/api/admin/deploy-readiness` family | Medium-high | High but scope-fragmenting | High — overlaps CP5-adopted canonical deployment-readiness family | Weak for CP6 first bounded group | P2 |

---

## 5. Duplicate Evaluation-Path Analysis

### Confirmed duplicate evaluation clusters

#### Cluster A — workflow lifecycle truth reuse
- `/api/admin/trust-spine`
- `/api/admin/operations-trust-center`
- `/api/admin/production-certification`

Repository evidence:
- `admin_operations_trust_center.py` imports and executes the trust-spine route internally
- `production_certification.py` separately evaluates `trust_spine_events`

Assessment:
- shared evidence source exists (`trust_spine_events`)
- but **not** one shared Truth Subject
- therefore these surfaces may not be grouped into one CP6 implementation set

#### Cluster B — deploy / certification posture duplication
- `/api/admin/deployment-readiness` (already OTS-adopted in CP5)
- `/api/admin/deploy-readiness` (legacy route, not adopted)
- `/api/admin/occ/trust-events` unresolved blocker summaries
- governance / diagnostics cards consuming legacy deploy-readiness

Assessment:
- this is real duplicate-evaluation pressure
- but it crosses into the certification boundary and the legacy route family
- not the smallest safe first repair for CP6

#### Cluster C — composite health aggregation duplication
- `/api/admin/system-health`
- `/api/admin/occ/health`
- `/api/admin/platform-trust/validate`

Assessment:
- all three summarize partially overlapping evidence
- but they do so for different operator purposes and different truth concepts
- grouping them would violate the bounded grouping rule

---

## 6. Duplicate Projection-Path Analysis

### Confirmed duplicate projection clusters

1. **Trust spine lifecycle projection**
   - direct dashboard: `PlatformTrustDashboard.jsx`
   - indirect trust consumers: `OperationsTrustCenter.jsx`, `production_certification.py`

2. **Validator projection**
   - `PlatformTrustValidator.jsx`
   - embedded inside `AdminEmail.jsx`

3. **Legacy deploy-readiness projection**
   - `AdminDeployReadiness.jsx`
   - `AdminGovernanceTrust.jsx`
   - `AdminDiagnostics.jsx`
   - `occ_trust_events.py`

4. **Trust-events projection**
   - `AdminGovernanceTrust.jsx`
   - `AdminIdentitySecurity.jsx`

5. **System-health projection**
   - `SystemHealth.jsx`
   - `AdminDiagnostics.jsx`

Assessment:
- the clearest low-risk projection family is still the **trust spine dashboard** because it is a single canonical owner route with one primary operator-visible dashboard.

---

## 7. Updated OTS Adoption Coverage Metrics

### Baseline from Checkpoint 5
- adopted surface families: **5**
- total API / UI / report / email consumers updated in CP5: **15**

### Updated Phase A coverage position
- Checkpoint 4 matrix entries inventoried: **24**
- families adopted in CP5: **5**
- matrix entries still outside explicit OTS route projection: **19**

### Remaining trust / health / operator-facing Phase A cluster
- primary remaining API routes discovered: **9**
- primary remaining operator-visible UI consumers discovered: **9**
- clean Wave 3 bounded candidates discovered: **4**
  - runtime attestation owner family
  - trust spine owner family
  - platform validator family
  - operations trust family

### Coverage interpretation

Checkpoint 5 closed the first 5 families.

Checkpoint 6 should now continue by binding the **smallest remaining canonical owner family** rather than jumping first into composite aggregators or legacy duplicate routes.

---

## 8. Smallest Safe Repair Recommendation

### Recommended bounded implementation group

**Group ID:** `CP6-G1-TRUST-SPINE-OWNER-FAMILY`

### Exact bounded group

1. `backend/routes/admin_trust_spine.py`
2. `frontend/src/components/PlatformTrustDashboard.jsx`

### Why this is the smallest safe repair

Repository evidence shows this group:

- consumes one truth subject family: workflow lifecycle truth via canonical surface `trust_spine`
- uses one evaluation path: expected-stage rollup over `trust_spine_events`
- uses one projection path: trust-spine route → trust dashboard
- is directly operator-visible
- is already registered as a canonical owner in `backend/lib/canonical_truth.py`
- already exposes `truth_relationship`, making additive OTS completion low-risk

### Why larger grouping is rejected

The repository does **not** support grouping `trust_spine`, `platform_trust_validator`, and `operations_trust_center` together because they differ in:

- Truth Subject
- evaluation logic
- projection contract

The repository also does **not** support choosing `occ/*`, `system-health`, or legacy `deploy-readiness` first because those are either:

- mixed-subject aggregators
- certification-adjacent overlaps
- or duplicate legacy paths with larger containment risk

---

## 9. Exact Expected Changed-File List for Phase B

### Runtime files
- `backend/routes/admin_trust_spine.py`
- `frontend/src/components/PlatformTrustDashboard.jsx`

### Focused verification files
- `backend/tests/test_bcss_checkpoint6_api_contracts.py`
- `backend/tests/test_bcss_checkpoint6_ots_claims.py`

### Documentation / adoption records
- `app/memory/BCSS_RELEASE2_PROGRAM2_CHECKPOINT6_PHASEA_DISCOVERY.md`
- `app/memory/BCSS_RELEASE2_PROGRAM2_CHECKPOINT6_IMPLEMENTATION_RECORD.md`
- `app/memory/PRD.md`

---

## 10. Expected Untouched-File List for Phase B

The following files are expected to remain untouched for the recommended bounded group:

- `backend/lib/ots_truth.py` unless a truly additive helper tweak is proven necessary
- `backend/routes/admin_platform_trust.py`
- `backend/routes/admin_operations_trust_center.py`
- `frontend/src/components/PlatformTrustValidator.jsx`
- `frontend/src/components/OperationsTrustCenter.jsx`
- `backend/routes/occ_health_aggregator.py`
- `backend/routes/occ_trust_events.py`
- `backend/routes/admin_ops.py`
- `backend/routes/admin_production_certification.py`
- `backend/routes/deploy_readiness.py`
- `frontend/src/pages/admin/AdminGovernanceTrust.jsx`
- `frontend/src/pages/admin/AdminDiagnostics.jsx`
- `frontend/src/pages/admin/AdminIdentitySecurity.jsx`
- `frontend/src/pages/admin/SystemHealth.jsx`
- `frontend/src/pages/AdminDeployReadiness.jsx`
- constitutional baseline documents

This untouched-file boundary preserves checkpoint containment.

---

## 11. Risk Assessment

### Implementation risk
**Low**

Reasons:
- additive route projection only
- canonical helper already exists
- no new architecture needed
- no DB schema change needed
- no new truth subject registration required

### Regression risk
**Low to medium**

Reasons:
- route contract changes are additive if legacy fields remain preserved
- dashboard UI changes should be disclosure-only and claim-boundary-only
- drilldown endpoint can remain untouched

### Boundary risk
**Low**

Reasons:
- stays within BCSS Domain 01
- stays within Wave 3 claim-binding convergence
- avoids R13 / R15 / new certification work
- avoids composite aggregator sprawl

---

## 12. Estimated Implementation Scope

- backend runtime route updates: **1 file**
- frontend operator-surface disclosure updates: **1 file**
- focused backend tests: **2 files**
- smoke + verification: backend + frontend

Estimated scope: **small / bounded / checkpoint-safe**

---

## 13. GO / NO-GO Recommendation

## GO

### GO basis

Repository evidence supports moving to Phase B **only** for:

**`CP6-G1-TRUST-SPINE-OWNER-FAMILY`**

Because this group:

- is repository-backed
- is already a canonical owner family
- eliminates unsupported operator claims at the source-owner layer
- creates no orphaned adoption
- introduces no new architecture
- does not cross checkpoint boundaries

### Explicit NO-GO for broader Phase B scope

Do **not** broaden Phase B to include, in the same implementation set:

- `admin_platform_trust.py`
- `admin_operations_trust_center.py`
- `occ_health_aggregator.py`
- `occ_trust_events.py`
- `admin_ops.py`
- `admin_production_certification.py`
- `deploy_readiness.py`

Those remain valid future bounded candidates, but repository evidence does not justify combining them into the first CP6 implementation group.

---

## 14. Constitutional Verdict

Phase A is complete.

The repository determines that the **smallest safe repair** for Checkpoint 6 is the **Trust Spine owner family**:

- `backend/routes/admin_trust_spine.py`
- `frontend/src/components/PlatformTrustDashboard.jsx`

This is the recommended first bounded implementation group for Phase B.