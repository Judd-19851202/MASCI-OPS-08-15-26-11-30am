# MASCI Operational Execution Certification Plan

## 1. Purpose

This plan defines the permanent certification standard for every implementation track governed by the MASCI Operational Execution Constitution.

No operational implementation is complete until it has passed the certification gates applicable to its scope.

## 2. Canonical Status Set

Only the following certification statuses are permitted:
- **VERIFIED** — executed and passed with evidence
- **FAILED** — executed and did not satisfy requirements
- **BLOCKED** — execution could not complete due to a proven blocker
- **STALE** — evidence exists but is outside the freshness window
- **NOT_YET_EXERCISED** — required evidence not yet executed
- **UNKNOWN** — system truth cannot currently be established

No unexecuted test may be marked FAILED.
No unproven behavior may be marked VERIFIED.

## 3. Evidence Standard

Every certification outcome must record:
- commit/build identity
- environment identity
- tester or executing authority
- execution timestamp
- workflow/scope tested
- source evidence references
- screenshots/logs where applicable
- machine-verifiable outputs where applicable

## 4. Engineering Certification

Required for every implementation track:
- source review against constitution
- ownership review
- zero-drift review
- changed-file lint/static analysis
- changed-unit or contract tests
- no unrelated scope contamination
- no secret leakage
- no environment-file contamination

Status evidence:
- VERIFIED only when all applicable engineering gates pass

## 5. Testing Certification

Every track must define and execute:
- focused regression tests for changed behavior
- source-of-truth contract tests
- cross-domain integration tests where affected
- negative-path tests
- historical integrity tests where history behavior is changed

## 6. Preview Verification

Preview verification is mandatory before production when the track affects runtime behavior.

Preview verification must prove:
- deployed commit/source hash matches intended release
- frontend and backend release identities align
- no stale/mixed assets
- affected workflows run on deployed preview source
- no console/runtime errors in tested scope

## 7. Production Verification

Production verification is mandatory when the track is deployment-bearing.

Production verification must prove:
- deployed commit/source hash matches intended release
- correct environment/database
- no stale/mixed bundle or replica drift
- affected workflows operate truthfully on live production
- no unexpected business mutation
- no unintended notifications/emails

## 8. Device Verification

Device verification is mandatory for field-critical workflows.

Required when the workflow is:
- field-entered
- tablet/mobile primary
- continuity-sensitive
- lock/background/offline-sensitive

If no physical device is available, status is **NOT_YET_EXERCISED**, not FAILED.

## 9. Field Acceptance

Field acceptance is required for workflows where operator trust is part of the core requirement.

Field acceptance must verify:
- real operator usability
- continuity through realistic device behavior
- truthful restore/save behavior
- exact history fidelity where applicable

## 10. Operator Acceptance

Operator acceptance is required when the workflow changes field, dispatch, PM, shop, HR, safety, or other operator-owned execution behavior.

Evidence must include:
- role-specific walkthrough
- pass/fail against defined checkpoints
- screenshots only where meaningful

## 11. Executive Acceptance

Executive acceptance is required for:
- Daily Company Operations Brief publication
- executive operational decision surfaces
- major cross-domain summary logic

Executive acceptance must verify truthfulness, not aesthetics alone.

## 12. Audit Verification

Audit verification is required whenever a source record, ownership decision, schedule publication, reconciliation publication, or briefing publication is created or changed.

Evidence must prove:
- actor attribution
- source record traceability
- mutation traceability
- publication/version traceability

## 13. Trust Verification

Trust verification is required for every workflow participating in the Trust Spine.

Must verify:
- expected lifecycle stages
- stage status truthfulness
- correlation ID continuity
- no fake green on missing stages

## 14. Search Verification

Search verification is required whenever a new operational concept is made discoverable.

Must verify:
- read-scope safety
- correct labels
- absence of unauthorized counters/results
- no sensitive payload leakage

## 15. ODS Verification

ODS verification is required whenever a concept is projected into cross-domain operational aggregation.

Must verify:
- source owner retained
- source record ID retained
- freshness metadata retained
- projection is not writable as alternate truth

## 16. Brief Verification

The Daily Company Operations Brief must verify:
- source fact traceability
- derived metric traceability
- AI narrative separation
- confidence classification
- operator and executive readability

## 17. Scheduling Verification

Schedule certification must verify:
- one canonical schedule authority
- correct work scoping
- ownership visibility
- constraint visibility
- commit/publication truth
- no overwrite across separate work instances
- no silent merge of distinct commitments

## 18. Reconciliation Verification

Reconciliation certification must verify:
- planned vs committed vs actual truth
- status classification correctness
- variance evidence
- root-cause attribution
- recovery action ownership
- history/version retention

## 19. Performance Verification

Required when affected workflows operate on large cross-domain reads or mobile field interactions.

Must verify:
- acceptable operator latency
- no pathological fan-out
- no accidental heavy payload projection
- acceptable resource usage for affected surfaces

## 20. Deployment Verification

Deployment verification must confirm:
- source lineage proven
- GitHub/release commit proven where applicable
- build identity proven
- environment identity proven
- rollback criteria recorded
- no untracked required file missing from deployed source

## 21. Rollback Criteria

A release must define rollback triggers, including but not limited to:
- source lineage contradiction
- critical operator workflow failure
- continuity failure
- data mutation drift
- unauthorized visibility leakage
- trust or audit falsification

Rollback criteria must be explicit before production deployment.

## 22. Release Readiness Standard

No track is release-ready until all applicable statuses are either:
- VERIFIED
- NOT_YET_EXERCISED with explicit reason and non-blocking classification

Any BLOCKED, FAILED, STALE, or UNKNOWN item that affects the track’s core truth surface blocks release.

## 23. Completion Evidence by Status

### VERIFIED
Requires executed evidence, matching expected results, and source/build identity.

### FAILED
Requires executed evidence proving mismatch or defect.

### BLOCKED
Requires explicit blocker evidence and exact blocked step.

### STALE
Requires prior evidence plus failed freshness requirement.

### NOT_YET_EXERCISED
Requires explicit declaration that execution has not occurred.

### UNKNOWN
Requires explicit declaration that truth cannot currently be established.

## 24. Mandatory Certification Flow Per Implementation Track

1. Engineering certification
2. Focused test certification
3. Preview verification
4. Production deployment verification when in scope
5. Production sanity verification when in scope
6. Device/field acceptance when required
7. Final constitutional status declaration

## 25. No Fake PASS Rule

The MASCI OPS constitutional certification doctrine is absolute:

- screenshots and live behavior outrank reports
- production outranks preview for production truth
- operator/device evidence outranks static claims for field trust
- machine-verifiable lineage outranks narrative release notes

No implementation may claim success through prose alone.
