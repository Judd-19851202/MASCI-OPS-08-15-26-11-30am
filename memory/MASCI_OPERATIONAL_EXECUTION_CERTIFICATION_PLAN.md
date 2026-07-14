# MASCI Operational Execution Certification Plan

## 1. Certification Authority

This plan defines the permanent certification standard for every implementation track governed by the MASCI Operational Execution Constitution.

No operational implementation is complete until it has passed every certification gate applicable to its scope.

This plan operates in lockstep with:
- `MASCI_OPERATIONAL_EXECUTION_CONSTITUTION.md`
- `MASCI_OPERATIONAL_EXECUTION_REGISTER.md`
- `MASCI_OPERATIONAL_EXECUTION_ZERO_DRIFT_MATRIX.md`
- `MASCI_OPERATIONAL_EXECUTION_ROLE_AND_OWNERSHIP_MATRIX.md`
- `MASCI_OPERATIONAL_EXECUTION_CONSTITUTIONAL_APPENDIX.md`

## 2. Canonical Status Set

Only the following certification statuses are permitted:
- **VERIFIED** — executed and passed with evidence
- **FAILED** — executed and did not satisfy requirements
- **BLOCKED** — execution could not complete due to a proven blocker
- **STALE** — evidence exists but is outside the required freshness window
- **NOT_YET_EXERCISED** — required evidence has not yet been executed
- **NOT_APPLICABLE** — the requirement does not apply to the governed object, workflow, environment, role, or track; the reason must be explicit
- **UNKNOWN** — truth cannot currently be established, and neither execution absence nor a proven blocker adequately describes the condition; reason, owner, and resolution path must be recorded

No unexecuted test may be marked FAILED.
No unproven behavior may be marked VERIFIED.
No prose-only claim may substitute for evidence.
UNKNOWN may not be used as a convenience substitute for incomplete investigation.

## 2A. Five-Gate Release Governance

The permanent release-governance gates are:

1. `CONTRACT_LOCKED`
2. `LOCAL_ENGINEERING_VERIFIED`
3. `INDEPENDENT_ADVERSARIAL_CERTIFIED`
4. `IMMUTABLE_RELEASE_CANDIDATE_VERIFIED`
5. `DEPLOYED_OPERATIONAL_ACCEPTANCE_VERIFIED`

`DONE` is reserved for the state in which all five gates are VERIFIED.

The implementing builder may satisfy Gate 1 and local evidence for Gate
2, but may not self-assert Gate 3, may not self-assert Gate 5 without
deployed evidence, and may not self-declare `DONE`.

## 2B. Skipped-Test Classification Rule

Any required test, probe, walkthrough, or certification lane that is
skipped, deferred, or not exercised must carry all of the following:
- explicit reason
- explicit owner
- exact skipped step or lane
- `skip_classification`

Permitted `skip_classification` values are:
- `BLOCKING`
- `NON_BLOCKING`

No skipped required test may appear in evidence without
`skip_classification`.

## 3. Universal Evidence Standard

Every certification outcome must record:
- commit or build identity
- environment identity
- database / tenant / company identity where relevant
- tester or executing authority
- execution timestamp
- workflow or scope tested
- source evidence references
- screenshots or video where meaningful
- machine-verifiable outputs where applicable
- role acceptance lane where applicable
- blocker references where applicable
- reason for NOT_APPLICABLE or UNKNOWN where used
- owner and resolution path where UNKNOWN is used

## 4. Constitutional Certification Rule

Before code implementation begins, the governing artifacts themselves must be constitutionally complete.

For implementation tracks, certification must prove that the track remains constitutionally consistent with:
- ownership rules
- identifier rules
- schema rules
- API rules
- state-machine rules
- search rules
- ODS rules
- Trust Spine rules
- audit rules
- KPI rules
- AI rules
- UX rules
- security rules
- performance rules
- release rules
- manual GitHub/deployment boundary rules
- product identity and bilingual/accessibility rules

## 5. Engineering Certification

Required for every implementation track:
- changed-file review against the Constitution
- zero-drift review
- ownership review
- no-orphan-feature review
- schema/API consistency review
- static analysis or lint where applicable
- changed unit/contract tests
- no unrelated scope contamination
- no secret leakage
- no environment contamination
- touched-area quality review under the Eight Pillars

Engineering certification is VERIFIED only when all applicable engineering gates pass.

## 6. Schema Certification

Required whenever a track introduces or changes any data model.

Must verify:
- every new collection/table is declared
- every new field is declared
- field types and nullability are explicit
- indexes and uniqueness rules are explicit
- references/relationships are explicit
- retention and archival rules are explicit
- backward-compatibility rules are explicit
- migration path is explicit
- dashboard, brief, search, ODS, audit, and Trust Spine impacts are explicit

No schema change is certified without migration and backward-compatibility evidence where applicable.

## 7. API Contract Certification

Required whenever a track introduces or changes any API surface.

Must verify:
- route and method are correct
- request contract is explicit
- response contract is explicit
- permissions are explicit
- versioning rules are explicit
- idempotency behavior is explicit
- pagination, filtering, and sorting rules are explicit where relevant
- validation behavior is explicit
- error contract is explicit
- downstream consumers are identified and compatible

Frontend and backend must be proven contract-locked.

## 8. Security Certification

Required for every track touching runtime behavior, data visibility, publication, attachments, dashboards, search, ODS, AI, or exports.

Must verify:
- RBAC
- tenant/company isolation
- project-scope isolation
- authorization boundaries
- session handling assumptions
- attachment access control
- audit integrity
- privilege escalation prevention
- API abuse / rate-protection strategy where relevant
- export and search visibility boundaries
- AI input/output exposure boundaries

Security certification may not be deferred as future hardening when the track introduces the risk now.

## 9. Performance and Scale Certification

Required whenever affected workflows could operate over large data sets, many users, or heavy dashboard reads.

Must verify:
- no obvious N+1 query pattern
- no unbounded expensive aggregation without plan
- dashboard and briefing payload size is controlled
- mobile field payloads are controlled
- indexing strategy is sufficient for expected access patterns
- caching/materialization strategy is explicit where needed
- invalidation/freshness rules are explicit
- queue/background-job design is explicit where needed
- high-volume read/write behavior is acceptable for expected scale

Performance certification must assume growth to multi-year, high-volume, multi-company operations.

## 10. Concurrency, Caching, and Synchronization Certification

Required whenever a workflow supports repeated mutation, delayed sync, cached reads, background recompute, publish/review races, or offline continuity.

Must verify:
- stale-write handling is explicit
- duplicate-submit handling is explicit
- collision/conflict behavior is explicit
- cache ownership and invalidation are explicit
- stale-cache display behavior is explicit
- synchronization ownership is explicit
- reconnect and replay behavior are explicit
- local continuity artifacts do not masquerade as enterprise source truth

## 11. Offline and Mobile Continuity Certification

Required whenever a workflow is interruption-sensitive, mobile-first, or continuity-sensitive.

Must verify:
- local continuity scope is explicit
- server source-of-truth boundaries remain explicit
- reconnect and recovery behavior are explicit
- duplicate replay is prevented or safely resolved
- operator-visible degraded-state messaging is truthful
- mobile interruption handling remains usable under field conditions

## 12. Failure-Mode Certification

Required for every workflow creating, mutating, publishing, reconciling, projecting, or certifying operational truth.

Must verify the workflow’s behavior under:
- network interruption
- browser close / refresh / lock
- duplicate submit
- stale data or version conflict
- queue or worker failure
- AI failure
- notification/email failure
- background job interruption
- partial deployment or stale bundle
- database timeout or dependency outage

The workflow must preserve user-entered facts, avoid silent duplication, surface truthful status, and preserve audit lineage.

## 13. State-Machine Certification

Required whenever a governed object has lifecycle behavior.

Must verify:
- explicit allowed states
- explicit allowed transitions
- invalid transitions are rejected truthfully
- actor authority per transition is enforced
- rollback/correction behavior is explicit
- terminal states are explicit
- history retention works across transitions

This applies to work, schedule, Daily Report lifecycle where applicable, reconciliation, briefing, queue-visible artifacts, and any published AI artifact.

## 14. Workflow Dependency Certification

Required whenever a workflow creates, updates, or consumes data across domains.

Must verify:
- what creates the record
- what consumes the record
- what updates because of the record
- what dashboards display it
- what briefs consume it
- what search indexes it
- what ODS projections consume it
- what Trust Spine events prove it
- what notifications depend on it

If any dependency is undocumented or broken, certification fails.

## 15. Data Lineage Certification

Required for dashboards, reports, exports, executive briefs, AI-derived summaries, and KPI surfaces.

Must verify:
- every surfaced value traces to originating record classes
- calculation logic is explicit
- freshness is explicit
- confidence is explicit where derived
- dashboard and brief semantics are aligned
- AI narrative is separated from verified fact

No unverifiable dashboard or briefing value may be certified.

## 16. KPI Certification

Required whenever a track introduces or changes operational metrics.

Must verify:
- KPI name and meaning
- formula
- numerator and denominator
- exclusions
- source systems
- freshness expectation
- dashboard consumers
- brief consumers
- confidence/truth classification

No KPI may be certified if multiple competing formulas exist.

## 17. AI Governance Certification

Required whenever AI contributes to user-visible output, ranking, summaries, classifications, drafting, or recommendations.

Must verify:
- AI feature catalog entry exists
- inputs are explicit
- outputs are explicit
- human review requirement is explicit
- confidence or confidence-classification behavior is explicit
- AI output is labeled and separated from verified operational fact
- failure behavior is explicit
- audit/provenance behavior is explicit

AI certification fails if the user can mistake AI content for canonical fact.

## 18. UX and Mobile-First Certification

Required whenever a user-facing workflow or screen is introduced or changed.

Must verify:
- MASCI navigation consistency
- terminology consistency
- card/table/filter consistency
- permission and action consistency
- mobile-first field usability where applicable
- no bolted-on or visually foreign interactions
- interruption recovery for field-critical flows where applicable

For field-critical workflows, desktop-only success is insufficient.

## 19. Search Certification

Required whenever a new concept or artifact becomes discoverable in search.

Must verify:
- source authority remains clear
- read-scope safety is enforced
- labels are correct
- no sensitive payload leakage occurs
- stale or duplicate search results are handled truthfully

Search certification fails if search appears to own the record it merely indexes.

## 20. ODS Certification

Required whenever a concept is projected into ODS.

Must verify:
- source owner is retained
- source identifier is retained
- freshness metadata is retained
- projection is not writable as alternate truth
- cross-domain consumers remain consistent with source authority
- stale or failed projection states are visible where operator-visible outputs depend on them

## 21. Trust Spine Certification

Required for every workflow participating in the Trust Spine.

Must verify:
- expected lifecycle stages exist
- stage status truthfulness exists
- correlation identifiers propagate correctly
- failure visibility exists
- missing-stage behavior degrades certification truthfully

No fake green on missing or failed stages is permitted.

## 22. Audit Certification

Required whenever source records, ownership decisions, publications, overrides, approvals, or certifications occur.

Must verify:
- actor attribution
- timestamp
- source record identity
- workflow or module identity
- mutation/publication/certification type
- prior/new value or structured change summary
- correlation ID where applicable
- retention and historical readability

Audit certification fails if historical truth cannot be reconstructed.

## 22A. Lifecycle and Identifier Catalog Certification

Must verify:
- stable identifier catalog coverage is complete
- no governed concept relies on display label or fuzzy text as canonical identity
- lifecycle catalog covers every required governed object
- split/merge/revision lineage is preserved

## 23. Dashboard, Executive Reporting, and Notification Certification

Required whenever a track introduces or changes dashboards, executive reporting, brief-adjacent reporting, alerts, or notifications.

Must verify:
- dashboard source authority is explicit
- dashboard KPI authority is explicit
- dashboard freshness and stale-state behavior are explicit
- executive reporting semantics align with brief and KPI authority
- notification trigger authority is explicit
- notification deduplication and retry rules are explicit
- notifications do not become source or publication authority
- English and Spanish text coverage exists where user-facing
- existing notification ecosystem is reused

## 23A. Daily Company Operations Brief Certification

Must verify:
- brief identity contract exists
- reporting window and cutoff behavior are explicit
- preliminary / revised / final lifecycle is explicit
- late-data behavior is explicit
- source-coverage and missing-data behavior are explicit
- fact / derived / AI labeling is explicit
- one canonical snapshot powers role-specific views
- PDF/email/in-app delivery boundaries are explicit

## 23B. Product Identity, Bilingual, and Accessibility Certification

Must verify:
- MASCI shared shell, navigation, typography, spacing, cards, selectors, drill-down, and permission-aware navigation are reused
- English/Spanish parity exists for applicable user-facing surfaces
- no color-only status communication exists
- keyboard, screen-reader, focus, touch-target, semantic heading, and mobile/iPad responsiveness requirements are satisfied where applicable

## 23C. Manual GitHub and Deployment Boundary Certification

Must verify:
- local work is not misrepresented as GitHub work
- GitHub work is not misrepresented as deployed work
- preview is not misrepresented as production
- production is not misrepresented as field acceptance
- field acceptance is not misrepresented as executive acceptance
- only Jaymn is represented as the physical GitHub/deployment actor

## 24. Preview Verification

Preview verification is mandatory before production when the track affects runtime behavior.

Preview verification must prove:
- intended source/commit/build is deployed
- frontend and backend identities align
- no stale or mixed assets exist
- affected workflows run on the deployed preview source
- no console/runtime errors exist in tested scope
- visible behavior matches contracts and certification claims

## 25. Production Verification

Production verification is mandatory for deployment-bearing tracks.

Production verification must prove:
- deployed commit/build identity matches expectation
- correct environment and data boundaries are live
- no stale or mixed bundle/replica drift exists
- affected workflows operate truthfully on live production
- no unintended business mutation occurred
- no unintended notifications/emails/publications occurred

Preview does not overrule production truth.

## 26. Device and Field Acceptance

Device verification is mandatory for field-critical workflows.

Required when the workflow is:
- field-entered
- mobile/tablet primary
- continuity-sensitive
- interruption-sensitive
- offline/degraded-network sensitive

Field acceptance must verify:
- real operator usability
- save/restore truthfulness
- continuity under realistic interruption
- exact history fidelity where applicable
- duplicate-submit safety where applicable

If a physical-device run is required but not executed, the status is NOT_YET_EXERCISED, not VERIFIED.

## 27. Operator and Executive Acceptance

### 24.1 Operator Acceptance
Required when the track changes field, dispatch, PM, shop, fleet, safety, HR, QA/QC, or other operator-owned workflows.

Must include:
- role-specific walkthrough
- pass/fail against defined checkpoints
- screenshots or recordings where meaningful

### 24.2 Executive Acceptance
Required for:
- executive briefs
- executive operational decision surfaces
- major cross-domain summary logic

Executive acceptance verifies truthfulness and actionability, not aesthetics alone.

## 28. Release Sequencing Certification

Before each track begins, certification must revalidate that upstream dependency assumptions still hold.

Must verify:
- dependency list remains correct
- no accepted upstream track must be redesigned to support the new track
- schema assumptions remain valid
- API assumptions remain valid
- KPI assumptions remain valid
- event/dependency assumptions remain valid
- security/performance assumptions remain valid
- concurrency/caching assumptions remain valid
- offline/synchronization assumptions remain valid

If any dependency is invalid, the downstream track is BLOCKED until corrected.

## 29. Deployment Verification

Deployment verification must confirm:
- source lineage proven
- build identity proven
- environment identity proven
- required files are present in deployed source
- rollback criteria are recorded
- release communications and acceptance lanes are correct for scope

## 30. Rollback Criteria

A release must define rollback triggers, including but not limited to:
- source-lineage contradiction
- critical operator workflow failure
- continuity failure
- data mutation drift
- unauthorized visibility leakage
- trust or audit falsification
- broken schema/API contract on live runtime
- severe performance regression on core workflows
- security regression
- synchronization or replay corruption
- stale-cache / mixed-release truth contradiction on operator-visible surfaces

Rollback criteria must be explicit before production deployment.

## 31. No-Orphan Feature Certification Rule

No feature may be certified unless it can answer:
- Who creates it?
- Who owns it?
- Who consumes it?
- What updates because of it?
- What reports on it?
- What dashboard displays it?
- What audit trail records it?
- What Trust Spine events are emitted?
- What search indexes it?
- What certification validates it?

Any unanswered question blocks certification.

## 32. Release Readiness Standard

No track is release-ready until all applicable certification lanes are either:
- VERIFIED
- or NOT_YET_EXERCISED with explicit reason, explicit owner, and explicit `skip_classification=NON_BLOCKING`
- or NOT_APPLICABLE with explicit reason and scope statement

Any BLOCKED, FAILED, STALE, or UNKNOWN item affecting a core truth surface blocks release.

Release readiness for a candidate additionally requires Gates 1–4 of the
Five-Gate framework to be VERIFIED. `DONE` additionally requires Gate 5
to be VERIFIED.

## 33. Completion Evidence by Status

### VERIFIED
Requires executed evidence, matching expected results, and source/build/environment identity proof.

### FAILED
Requires executed evidence proving mismatch, defect, or unacceptable result.

### BLOCKED
Requires explicit blocker evidence and exact blocked step.

### STALE
Requires prior evidence plus proof that freshness is outside the accepted window.

### NOT_YET_EXERCISED
Requires explicit declaration that execution has not occurred, plus
reason, owner, and `skip_classification`.

### NOT_APPLICABLE
Requires explicit proof that the requirement does not apply to the governed object, workflow, environment, role, or track, plus the reason. If represented as a skipped lane in evidence, it must still record `skip_classification=NON_BLOCKING`.

### UNKNOWN
Requires explicit declaration that truth cannot currently be established, why BLOCKED or NOT_YET_EXERCISED do not adequately describe the condition, plus owner and resolution path.

## 34. Mandatory Certification Flow Per Implementation Track

1. Gate 1 — `CONTRACT_LOCKED`
   - constitutional dependency revalidation
   - governing-artifact consistency verification
2. Gate 2 — `LOCAL_ENGINEERING_VERIFIED`
   - engineering certification
   - schema/API/security/performance/concurrency/cache/sync/offline certification as applicable
   - state-machine, dependency, lineage, KPI, AI, dashboard/notification, search, ODS, trust, and audit certification as applicable
   - focused test certification
3. Gate 3 — `INDEPENDENT_ADVERSARIAL_CERTIFIED`
   - independent adversarial validation by a certifying authority other than the implementing builder
4. Gate 4 — `IMMUTABLE_RELEASE_CANDIDATE_VERIFIED`
   - preview verification where applicable
   - immutable source/build/environment identity verification
5. Gate 5 — `DEPLOYED_OPERATIONAL_ACCEPTANCE_VERIFIED`
   - production deployment verification when in scope
   - production sanity verification when in scope
   - device/field acceptance when required
   - operator and executive acceptance when required

Final constitutional status declaration may claim `DONE` only after all
five gates are VERIFIED.

## 35. Constitutional Appendix Cross-Reference

Where lifecycle catalogs, event maps, dashboard authorities, KPI authorities, notification authorities, offline authorities, or synchronization authorities are required for unambiguous certification, the normative appendix is part of the certification authority:
- `MASCI_OPERATIONAL_EXECUTION_CONSTITUTIONAL_APPENDIX.md`

## 36. No Fake PASS Rule

The MASCI OPS certification doctrine is absolute:
- screenshots and live behavior outrank prose
- production outranks preview for production truth
- operator/device evidence outrank static claims for field trust
- machine-verifiable lineage outranks narrative release notes
- certified schema/API/security/performance evidence outrank convenience assumptions

No implementation may claim success through narrative alone.