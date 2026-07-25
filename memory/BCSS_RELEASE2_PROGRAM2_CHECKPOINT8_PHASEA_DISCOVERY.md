# MASCI OPS · Operational Truth Spine
## Release 2 · Program 2 · Checkpoint 8
## Phase A — Operations Trust Center Repository Discovery

Date: 2026-07-25

Status: PHASE A COMPLETE — GO RECOMMENDED

---

## 1. Executive conclusion

Repository discovery supports a **GO** recommendation for the Operations Trust Center family, but only with the repository-proven classification preserved exactly as implemented today:

- the candidate pair exists
- both surfaces are live
- both surfaces are already mounted and consumed
- the family is **not** a canonical owner family
- the family is a **derived consumer** family
- its primary upstream canonical owner is **`trust_spine`**
- its truth subject is **`shared_operational_trust_score`**

The smallest safe future implementation boundary is the exact candidate pair only:

- `/app/backend/routes/admin_operations_trust_center.py`
- `/app/frontend/src/components/OperationsTrustCenter.jsx`

Repository evidence does **not** support treating this family as a validator, canonical owner, certification family, OCC family, or deploy-readiness family.

---

## 2. Closed baseline carried forward

Checkpoint 7 remains formally verified, adopted, and closed.

This Phase A discovery did not reopen or alter:

- `platform_trust_validator`
- `trust_spine`
- OCC families
- production certification
- deploy readiness

No runtime code, tests, routes, schemas, navigation, configuration, or deployment artifacts were changed during this discovery track.

---

## 3. Constitutional authority and evidence standard

This discovery is governed by repository-backed authority only:

- `/app/backend/lib/canonical_truth.py`
- `/app/memory/BCSS_RELEASE2_PROGRAM2_CHECKPOINT4_SURFACE_CLAIM_MATRIX.md`
- `/app/memory/BCSS_RELEASE2_PROGRAM2_CHECKPOINT6_PHASEA_DISCOVERY.md`
- `/app/memory/BCSS_RELEASE2_PROGRAM2_CHECKPOINT7_PHASEA_DISCOVERY.md`
- live route registration and active UI mounting in the repository

Repository-first rule applied throughout:

- if earlier assumptions and repository evidence differ, the repository wins
- if a clean truth subject, owner, or bounded implementation group cannot be proven, GO is not allowed

---

## 4. Discovery scope

Primary candidate pair under evaluation:

- backend: `/app/backend/routes/admin_operations_trust_center.py`
- frontend: `/app/frontend/src/components/OperationsTrustCenter.jsx`

Supporting repository evidence inspected only to prove ownership, reachability, duplication, compatibility, and adoption boundaries:

- `/app/backend/lib/canonical_truth.py`
- `/app/backend/server.py`
- `/app/backend/routes/admin_trust_spine.py`
- `/app/frontend/src/pages/admin/AdminEmail.jsx`
- `/app/backend/tests/test_track_15_76a_operations_trust_center.py`
- `/app/backend/tests/test_track_15_76b_finalization.py`
- `/app/backend/tests/test_track_15_77_production_lock.py`
- `/app/frontend/src/components/__tests__/c2_closeout_trust_surfaces.test.jsx`
- `/app/frontend/src/components/__tests__/C2TruthOwnership.test.jsx`

---

## 5. Repository search methodology

Read-only methods used:

- glob discovery for exact candidate files
- repository-wide string search for route strings, imports, and surface identifiers
- direct inspection of backend route, frontend component, registry, host page, and tests
- comparison against previously adopted checkpoint discovery artifacts

No implementation assumptions were accepted without repository proof.

---

## 6. Initial candidate result

The candidate pair is valid and active.

### Backend candidate
- file exists: yes
- tracked in git: yes
- registered in runtime: yes
- route exposed: yes

### Frontend candidate
- file exists: yes
- tracked in git: yes
- mounted in a live admin page: yes
- consumed in runtime UI: yes

The pair is neither dead nor orphaned.

---

## 7. Primary discovery question 1 — Does the candidate pair exist exactly as hypothesized?

**Answer: Yes.**

Repository evidence:

- `/app/backend/routes/admin_operations_trust_center.py:297-505`
- `/app/frontend/src/components/OperationsTrustCenter.jsx:571-919`

The family is real, tracked, and currently live.

---

## 8. Primary discovery question 2 — What are the exact file paths and live route/page bindings?

### Exact candidate files
- `/app/backend/routes/admin_operations_trust_center.py`
- `/app/frontend/src/components/OperationsTrustCenter.jsx`

### Exact runtime route binding
- `GET /api/admin/operations-trust-center`
- auxiliary endpoint also exists in the same backend family: `POST /api/admin/operations-trust-center/test-alert`

### Exact UI host binding
- component is mounted by `/app/frontend/src/pages/admin/AdminEmail.jsx:31-34`
- live admin page route is `/admin/email`

### Exact backend registration
- `/app/backend/server.py:14938-14941`

---

## 9. Primary discovery question 3 — Is the backend route live and repository-registered?

**Answer: Yes.**

Repository evidence:

- `server.py` includes `_otc_make_router(db, require_admin)`
- candidate route function is declared at `/api/admin/operations-trust-center`
- tests directly resolve the route handler from the router object

The route is repository-proven live, not speculative.

---

## 10. Primary discovery question 4 — Is the frontend projection live and operator-visible?

**Answer: Yes.**

Repository evidence:

- `AdminEmail.jsx` imports `OperationsTrustCenter`
- `AdminEmail.jsx` renders `<OperationsTrustCenter />` before the validator panel
- the component exports a live default page-level projection and contains user-facing sections, buttons, tables, and operator actions

This is a live embedded operator surface, not an unused component.

---

## 11. Primary discovery question 5 — What is the repository-proven family classification?

**Answer: DERIVED_CONSUMER.**

Repository evidence:

- `/app/backend/lib/canonical_truth.py:246-276`
- `role=DERIVED_CONSUMER`
- `owner_type="derived"`
- component disposition metadata sets `data-trust-role="DERIVED_CONSUMER"`

The family is not a canonical owner, not a validator, and not an aggregator.

---

## 12. Primary discovery question 6 — What is the clean bounded Truth Subject?

**Answer: `shared_operational_trust_score`.**

Repository evidence:

- canonical registry entry for `operations_trust_center` sets `truth_subject="shared_operational_trust_score"`
- the route computes a categorized trust score, score band, score inputs, narrative, and operator actions
- the frontend projects score, band, narrative, trend, action panel, findings, and subsystem cards

This is one derived operational trust subject, not multiple independent owner subjects.

---

## 13. Primary discovery question 7 — Who is the canonical owner?

**Answer: the family itself is not a canonical owner; its primary upstream canonical owner is `trust_spine`.**

Repository evidence:

- canonical registry entry sets `canonical_owner_id="trust_spine"`
- route response uses `derived_truth_payload("operations_trust_center", canonical_owner_route="/api/admin/trust-spine", ...)`
- frontend hidden metadata sets `data-canonical-owner="trust_spine"`

Additional upstream dependency also exists in the registry:

- `upstream_owner_ids=["trust_spine", "platform_attestation"]`

But the repository-proven primary canonical owner relationship for this family is **trust_spine**.

---

## 14. Primary discovery question 8 — Is the family owner, consumer, validator, aggregate projection, or mixed-role?

**Answer: derived consumer family with a bounded projection; not mixed-role.**

Repository evidence supports one clean role:

- route contract explicitly says it is a derived consumer
- registry says derived consumer
- UI disposition metadata says derived consumer
- truth owner panel is rendered as a relationship disclosure, not as ownership assertion

The family projects a derived score, but that does not change the family role into canonical ownership.

---

## 15. Primary discovery question 9 — What exact evidence sources does the route consume?

**Answer: trust-spine payload, master-data findings, audit counts, notification counts, trend history, and red-alert state.**

Repository evidence from `/app/backend/routes/admin_operations_trust_center.py`:

- imports and invokes `routes.admin_trust_spine`
- consumes `collect_findings(db)` from master-data trust
- queries `email_routing_audit_v2`
- queries `trust_spine_events`
- computes categorized score via `compute_categorized_score`
- computes legacy score via `compute_score`
- writes and reads trend snapshots via `write_snapshot` and `read_trend`
- invokes `red_alert.maybe_send`

The route does not own raw truth creation for these inputs.

---

## 16. Primary discovery question 10 — What is the current evaluation path?

**Answer: one bounded derived evaluation path exists.**

Repository-proven path:

1. Trust Spine route is invoked and workflow rows are loaded.
2. Master-data findings are collected.
3. Audit/notification counts are queried from MongoDB.
4. Derived categorized score is computed.
5. Derived summary, operator actions, subsystem cards, and narrative are built.
6. Trend snapshot is persisted and trend window is read back.
7. Derived payload is returned with truth-surface and relationship metadata.

This is a local derived evaluation path, not a canonical owner evaluation path.

---

## 17. Primary discovery question 11 — What is the current projection path?

**Answer: one bounded projection path exists.**

Repository-proven path:

`/api/admin/operations-trust-center`
→ `api.get("/admin/operations-trust-center?trend_hours=...")`
→ `OperationsTrustCenter.jsx`
→ embedded render inside `AdminEmail.jsx`
→ live operator page `/admin/email`

The frontend does not compute a second trust score of its own; it consumes the route payload.

---

## 18. Primary discovery question 12 — What operator-visible claims does the family currently make?

**Answer: the family makes strong operator-facing trust claims.**

Material repository-visible claims include:

- “Can I trust this platform to run operations today?”
- band labels: `Trusted`, `Missing evidence`, `Failing`
- executive narrative status sentences
- “No operator action required” when actions are empty
- workflow rows such as “fully verified” and “every expected stage emitted ok evidence”
- subsystem health and trust trend framing

These claims are bounded by derived-consumer metadata, but some wording is stronger than the family role.

---

## 19. Primary discovery question 13 — What is the claim-ladder position supported by repository evidence?

**Answer: repository documentation supports a derived/correlated ceiling, while current runtime payload/wording projects stronger semantics.**

Repository evidence:

- Checkpoint 4 matrix classifies `/api/admin/operations-trust-center` with maximum constitutional claim `CORRELATED`
- Checkpoint 6 discovery also classifies the family as derived trust, not source truth
- current route maps score-band to `derived_status` values `VERIFIED`, `DEGRADED`, `MISMATCH`
- current UI projects `Trusted` and verification-style wording

Therefore the family has a **provable claim-boundary mismatch risk**, not an ownership ambiguity.

---

## 20. Primary discovery question 14 — Does the family duplicate another evaluator?

**Answer: yes, materially, but as a derived consumer rather than a competing owner.**

Repository-proven overlaps:

- `trust_spine` supplies upstream lifecycle truth
- `platform_trust_validator` evaluates platform trust from adjacent evidence
- `occ_health_aggregator` aggregates overlapping operational posture
- `admin_ops.py` system-health surfaces overlapping health claims
- `admin_production_certification.py` uses overlapping lifecycle evidence
- `deploy_readiness` and `admin_deployment_readiness` overlap on readiness/gating semantics

This is duplicate evaluation pressure, not duplicate canonical ownership.

---

## 21. Primary discovery question 15 — Does the family duplicate another projection?

**Answer: yes.**

Repository-proven overlapping operator projections include:

- `OperationsTrustCenter.jsx` on `/admin/email`
- `PlatformTrustValidator.jsx` on `/admin/email`
- OCC health surfaces
- system-health surfaces
- production-certification surfaces

The strongest direct duplication is page-level: `OperationsTrustCenter` and `PlatformTrustValidator` appear on the same `/admin/email` page.

---

## 22. Primary discovery question 16 — Is the family currently compatible and already relied upon by tests/consumers?

**Answer: yes.**

Repository evidence of current reliance:

- backend regression tests for 15.76A and 15.76B
- production-lock tests assert OTC invariants
- frontend closeout test asserts OTC disposition metadata
- host page `AdminEmail.jsx` consumes the component live

Current contract elements already relied upon include:

- `trust_score`
- `score_band`
- `score_band_label`
- `summary`
- `workflows`
- `master_data`
- `red_alert`
- new 15.76B sections such as `operator_actions`, `subsystems`, `trend`, and `executive_narrative`

---

## 23. Primary discovery question 17 — Are route mount, auth, and operator reachability already proven?

**Answer: yes.**

Repository evidence:

- backend route uses `Depends(require_admin_only_dep)`
- server registers the route under admin auth
- frontend host page is the admin email page
- production-lock regression explicitly checks anonymous access denial for `/api/admin/operations-trust-center`

There is no route-mount blocker and no auth-boundary ambiguity.

---

## 24. Primary discovery question 18 — Is there a clean bounded future implementation boundary?

**Answer: yes.**

Repository evidence supports one smallest safe group only:

- `/app/backend/routes/admin_operations_trust_center.py`
- `/app/frontend/src/components/OperationsTrustCenter.jsx`

Repository evidence does **not** require changes to:

- `/app/frontend/src/pages/admin/AdminEmail.jsx`
- `/app/frontend/src/app/routing/AppRoutes.jsx`
- `trust_spine`
- OCC routes
- certification routes
- deploy-readiness routes

The family is already live, so the bounded adoption group is proven.

---

## 25. Primary discovery question 19 — What is the smallest safe repair supported by the repository?

**Answer: bind the derived family more explicitly without changing ownership.**

Repository-supported future repair objective:

- preserve family role as `DERIVED_CONSUMER`
- preserve upstream canonical owner as `trust_spine`
- preserve route and UI compatibility
- tighten claim boundary so derived trust score does not read like canonical truth or certification

No repository evidence supports changing the owner, reclassifying the family, or broadening the scope to adjacent families.

---

## 26. Primary discovery question 20 — GO, NO-GO, or INCOMPLETE?

**Answer: GO.**

GO is supported because repository evidence proves all three required checkpoints:

1. clean bounded truth subject: `shared_operational_trust_score`
2. clean owner relationship: derived consumer under `trust_spine`
3. clean implementation boundary: backend route + frontend component only

The stop rule is not triggered.

---

## 27. Claim inventory

| Claim / implied claim | Repository surface | Evidence basis | Current role support | Risk |
|---|---|---|---|---|
| “Can I trust this platform to run operations today?” | component header contract | derived score + upstream evidence | partial only | high |
| `Trusted` | score-band label / badge | green derived score band | stronger than derived role | high |
| `Missing evidence` | score-band label / badge | amber derived score band | supported | medium |
| `Failing` | score-band label / badge | red derived score band | supported | medium |
| Executive narrative platform status sentence | route narrative builder | score band + red workflows + critical findings | partially supported | high |
| “No operator action required” | empty action panel state | no current derived actions | supported in derived scope | medium |
| workflow “fully verified” text | `_humanize_workflow_row` | upstream workflow evidence | bounded if read as workflow-level | medium |
| subsystem health cards | component cards | category scores | supported as derived projection | medium |
| trend and remediation ETA | route trend history + action sum | persisted snapshots + critical action totals | supported | low |

Primary claim risk: the family can be read as stronger operational truth than its derived-consumer role permits.

---

## 28. Claim ladder analysis

### Repository-backed support
- family role: `DERIVED_CONSUMER`
- truth subject: `shared_operational_trust_score`
- Checkpoint 4 ceiling: `CORRELATED`

### Current runtime projection
- route `truth_relationship.derived_status`: `VERIFIED | DEGRADED | MISMATCH`
- UI badge wording: `Trusted | Missing evidence | Failing`
- workflow helper text includes “fully verified”

### Determination

Repository evidence proves a **semantic claim-ceiling tension**:

- ownership is clean
- truth subject is clean
- implementation boundary is clean
- but current wording is stronger than the documented derived-family ceiling

That mismatch is a future bounded repair target, not a Phase A blocker.

---

## 29. Duplicate evaluation audit

| Evaluator | Question answered | Relationship to OTC | Disposition |
|---|---|---|---|
| `trust_spine` | what workflow lifecycle truth exists? | upstream canonical owner | supporting dependency |
| `platform_trust_validator` | does platform trust validate? | adjacent validator | duplicate evaluator |
| `occ_health_aggregator` | what is aggregate operational posture? | adjacent aggregator | duplicate evaluator |
| `admin_ops.py` system-health | what is system health? | overlapping health surface | duplicate evaluator |
| `admin_production_certification.py` | what workflows are proven end-to-end? | overlapping lifecycle-derived certification surface | duplicate evaluator |
| `deploy_readiness` / `admin_deployment_readiness` | is deployment/readiness blocked or clear? | adjacent gating/certification semantics | duplicate evaluator |

Conclusion: duplicate evaluation exists, but canonical ownership remains single because OTC is already registered as derived.

---

## 30. Duplicate projection audit

| Projection | Route/page | Overlap with OTC | Disposition |
|---|---|---|---|
| `OperationsTrustCenter.jsx` | `/admin/email` | in-scope candidate | candidate |
| `PlatformTrustValidator.jsx` | `/admin/email` | strongest direct page-level overlap | duplicate projection |
| OCC health UI | OCC pages | aggregate operational posture overlap | duplicate projection |
| system-health UI | diagnostics/system pages | health posture overlap | duplicate projection |
| production-certification UI | governance/diagnostic flows | proof/certification overlap | duplicate projection |

Conclusion: projection duplication is real, especially on `/admin/email`, but the OTC family boundary is still provable.

---

## 31. Truth Subject coverage matrix

| Surface | Classification | Truth Subject | Canonical Owner | Live | Operator Visible | Verdict |
|---|---|---|---|---|---|---|
| `admin_operations_trust_center.py` | DERIVED_CONSUMER | `shared_operational_trust_score` | `trust_spine` | yes | API-visible | in scope |
| `OperationsTrustCenter.jsx` | DERIVED_CONSUMER projection | `shared_operational_trust_score` | `trust_spine` | yes | yes | in scope |
| `admin_trust_spine.py` | CANONICAL_OWNER | `workflow_lifecycle_truth` | `trust_spine` | yes | yes | supporting dependency |
| `admin_platform_trust.py` | VALIDATOR | `platform_validation_truth` | `platform_attestation` | yes | yes | duplicate / out of scope |
| `occ_health_aggregator.py` | AGGREGATOR | `shared_operational_posture` | `platform_attestation` | yes | yes | duplicate / out of scope |
| `admin_production_certification.py` | adjacent certification surface | operational proof surface | separate boundary | yes | yes | out of scope |

---

## 32. Compatibility inventory

Current route contract already exposes both older and newer payload shapes.

### Existing preserved payload keys
- `trust_score`
- `score_band`
- `score_band_label`
- `score_reason`
- `score_inputs`
- `summary`
- `workflows`
- `master_data`
- `red_alert`
- `legacy_flat_score`

### 15.76B additive sections
- `categories`
- `category_weights`
- `critical_problems`
- `operational_warnings`
- `cleanup_opportunities`
- `operator_actions`
- `subsystems`
- `trend`
- `trend_hours`
- `executive_narrative`
- `estimated_remediation_seconds`

Compatibility is a real boundary and must be preserved in any future phase.

---

## 33. Current test inventory

### Direct backend tests
- `/app/backend/tests/test_track_15_76a_operations_trust_center.py`
- `/app/backend/tests/test_track_15_76b_finalization.py`

### Cross-family and lock tests
- `/app/backend/tests/test_track_15_77_production_lock.py`

### Direct frontend coverage
- `/app/frontend/src/components/__tests__/c2_closeout_trust_surfaces.test.jsx`
- `/app/frontend/src/components/__tests__/C2TruthOwnership.test.jsx`

### Test finding

Backend family coverage is strong.

Frontend OTC-specific constitutional wording coverage is comparatively light.

---

## 34. Required future test categories if Phase B is approved

Minimum required categories supported by repository reality:

### Backend
- explicit derived-claim ceiling tests
- conflict/contradiction disclosure tests when OTC band differs from trust-spine band
- compatibility preservation tests for existing keys

### Frontend
- derived-only wording tests
- operator-facing claim-boundary rendering tests
- conflict and relationship disclosure tests

### Integration/browser
- `/admin/email` render with OTC and validator together
- no semantic upgrade of OTC into canonical owner wording

---

## 35. Exact smallest safe repair recommendation

### Recommended bounded future group
- `/app/backend/routes/admin_operations_trust_center.py`
- `/app/frontend/src/components/OperationsTrustCenter.jsx`

### Why this is the smallest safe repair
- one truth subject
- one derived family role
- one upstream canonical owner
- one active backend route
- one active primary frontend projection
- no route-mount blocker
- no auth-boundary blocker
- no required schema or navigation changes proven by the repository

### Exact out-of-scope files for that future work
- `/app/frontend/src/pages/admin/AdminEmail.jsx`
- `/app/frontend/src/app/routing/AppRoutes.jsx`
- `/app/backend/routes/admin_trust_spine.py`
- `/app/backend/routes/admin_platform_trust.py`
- `/app/backend/routes/occ_health_aggregator.py`
- `/app/backend/routes/occ_trust_events.py`
- `/app/backend/routes/admin_ops.py`
- `/app/backend/routes/admin_production_certification.py`
- `/app/backend/routes/deploy_readiness.py`

---

## 36. Final Phase A verdict

Repository evidence proves the Operations Trust Center family is an active, bounded, derived-consumer family with a clean truth subject, a provable canonical owner relationship to `trust_spine`, and a clean future implementation boundary limited to the candidate route and component.

The family does have claim-ladder and duplication risks, but those risks are bounded and repairable without expanding into adjacent families.

**Verdict: PHASE A COMPLETE — GO RECOMMENDED**