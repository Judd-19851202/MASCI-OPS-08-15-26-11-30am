# BCSS Release 2 · Program 2 · Foundation · Checkpoint 4
## Operational Truth Spine

Date: 2026-07-25

This document is the only governing constitutional document for Checkpoint 4.

Checkpoint 2 remains formally adopted and closed.  
Checkpoint 3 remains complete and authoritative.  
This checkpoint is design / documentation only.

---

## 1. Constitutional Authority and Boundary

### [Constitutional (normative)] Authority rule
This document is the sole governing Checkpoint 4 document.

All companion documents derive authority from this document and establish no independent governance.

### [Constitutional (normative)] Boundary rule
Checkpoint 4 shall:
- transform the Checkpoint 3 constitutional foundation into a repository-backed adoption blueprint
- inventory active BCSS-facing operator surfaces
- map each surface to truth subjects, evidence, claim ceilings, wording boundaries, and migration waves

Checkpoint 4 shall not:
- implement runtime logic
- migrate systems
- redesign BCSS
- rewrite Checkpoint 3
- change API behavior
- change UI behavior
- deploy

### [Repository-backed current state (descriptive)] Checkpoint 4 execution boundary
Only `/app/memory/` artifacts and PRD tracking are changed in this checkpoint.

---

## 2. Governing Axioms

### [Constitutional (normative)] Platform axioms
Everything in the Operational Truth Spine shall obey:
- One Source of Truth
- One Canonical Architecture
- Zero Drift
- Repository Evidence First
- Reality Before Documentation
- Smallest Safe Repair
- Operator Experience Before Internal Complexity

### [Constitutional (normative)] Non-duplication rule
Nothing in this checkpoint may introduce:
- duplicate evidence engines
- duplicate truth engines
- duplicate claim engines
- duplicate certification systems
- duplicate trust vocabularies
- duplicate registries

---

## 3. Operational Truth Spine Definition

### [Constitutional (normative)] Single constitutional pipeline
Every operational statement in MASCI OPS shall trace through exactly one constitutional chain:

Reality  
↓  
Observation  
↓  
Evidence  
↓  
Evidence Quality  
↓  
Evidence Confidence  
↓  
Truth Subject  
↓  
Truth Evaluation  
↓  
Permitted Claim  
↓  
Operator Surface  
↓  
Automation Consumers  
↓  
AI Consumers  
↓  
Operational Decision  
↓  
Audit

### [Constitutional (normative)] Bypass prohibition
No surface may bypass this chain.  
No consumer may upgrade a claim.  
No AI may upgrade a claim.  
No certification may exist without constitutional evidence.

### [Constitutional (normative)] Required constitutional rule
"No operator-facing statement, dashboard, notification, API response, report, email, AI explanation, workflow status, export, or certification may assert a claim that exceeds the constitutional claim ceiling established by the Operational Truth Spine."

---

## 4. Repository Discovery Verdict

### [Repository-backed current state (descriptive)] High-level finding
The repository already contains the majority of the BCSS evidence and truth plumbing needed for adoption:
- canonical BCSS truth-subject registration in `backend/lib/canonical_truth.py`
- canonical archive-lineage truth in `backend/lib/archive_lineage.py`
- canonical recovery posture aggregation in `backend/routes/recovery_dashboard.py`
- bounded backup verification reporting in `backend/backup_verification.py`
- bounded deployment-readiness decision evidence in `backend/routes/admin_deployment_readiness.py`
- dependency continuity evidence in `backend/routes/integration_truth.py`
- multiple operator-facing admin surfaces already consuming these truths

### [Repository-backed current state (descriptive)] Main gap
The primary remaining gap is not absence of evidence. It is absence of a deterministic, surface-by-surface claim map that tells a future engineer:
- which truth subject a surface represents
- which evidence the surface may use
- which evidence the surface may not use
- which wording the surface may say
- which wording the surface may not say
- which wave owns the remaining adoption work

Checkpoint 4 closes that mapping gap.

---

## 5. Active Surface Corpus and Discovery Classification

### [Repository-backed current state (descriptive)] Active BCSS-facing operator surfaces inventoried
Checkpoint 4 inventories **24 active BCSS-facing operator surfaces** in the repository. They are detailed in the Surface Claim Matrix companion artifact.

### [Repository-backed current state (descriptive)] Additional discovered non-active surfaces

| Surface | Repository evidence | Classification | Reason |
|---|---|---|---|
| `/admin/operations-dashboard` | `frontend/src/app/routing/AppRoutes.jsx:694` | legacy | comment explicitly says it was consolidated into OCC |
| `/admin/platform-overview` | `frontend/src/pages/admin/AdminPlatformOverview.jsx:1-21` | duplicate | route is redirect-only to `/admin` |
| `PlatformTrustDashboard.jsx` | `frontend/src/components/PlatformTrustDashboard.jsx:1-555`; no active route usage found | unsupported | repository component exists but active operator reachability was not found in current route graph |

### [Constitutional (normative)] Surface classification rule
Only active, repository-backed BCSS-facing surfaces receive matrix entries. Legacy, duplicate, and unsupported discoveries remain documented but do not become new constitutional entry points.

---

## 6. Claim Ladder Reconciliation

### [Constitutional (normative)] Checkpoint 4 adoption ladder
For Operational Truth Spine adoption, the claim ladder shall be:

`UNKNOWN → OBSERVED → CORRELATED → VERIFIED → VALIDATED → CERTIFIED`

### [Constitutional (normative)] Reconciliation rule with Checkpoint 3
Checkpoint 3 remains authoritative for the constitutional BCSS claim classes `Observed`, `Verified`, and `Certified`.

Checkpoint 4 introduces `UNKNOWN`, `CORRELATED`, and `VALIDATED` as **Operational Truth Spine bridge levels** used to map current repository surfaces deterministically without creating a second claim engine.

They are:
- not a replacement certification system
- not a second truth architecture
- not a second evidence architecture

They are an adoption-map ladder for surface ceilings and truth evaluation only.

### [Constitutional (normative)] Claim ladder table

| Ladder level | Required evidence | Required confidence | Required verification | Permitted wording | Forbidden wording | Typical consumers |
|---|---|---|---|---|---|---|
| `UNKNOWN` | evidence absent, unreachable, or contradictory | `UNKNOWN` or unresolved | none | unknown, unavailable, not established | healthy, verified, validated, certified | health cards, safe UI fallbacks, smoke probes |
| `OBSERVED` | direct or durable observation exists | `LOW` to `MEDIUM` | capture only | observed, seen, present, recorded | verified, validated, certified | liveness endpoints, raw state surfaces |
| `CORRELATED` | multiple repository-backed signals align | `MEDIUM` | deterministic cross-check only | correlated, aligned, consistent across sources | verified, validated, certified | aggregators, posture surfaces, domain landings |
| `VERIFIED` | bounded truth established by authoritative owner evidence | `MEDIUM` to `HIGH` | owner-side validation or exercise exists | verified within scope, verified archive lineage, verified dependency posture | validated, certified | canonical owner APIs |
| `VALIDATED` | verified truth additionally checked by rule-bound validator or explicit validation surface | `HIGH` | validator / contract / independent review exists | validated against rules, validated by contract, validation passed | certified | validators, verification reports, production/operational validation surfaces |
| `CERTIFIED` | decision-recorded evidence under certification owner exists | `HIGH` | explicit approval / decision record exists | certified for stated scope, approved decision recorded | broader certification than evidence supports | deployment readiness, future BCSS recovery certification |

---

## 7. AI Governance

### [Constitutional (normative)] AI shall never
- create evidence
- upgrade evidence quality
- upgrade confidence
- upgrade claims
- create certifications
- override truth subjects
- suppress contradictory evidence

### [Constitutional (normative)] AI may
- summarize
- explain
- translate
- prioritize
- recommend
- predict

### [Deferred implementation] Current repository note
No repository-wide BCSS-specific AI claim-binding contract was found in current runtime surfaces. AI adoption remains future migration work.

---

## 8. Truth Subject Summary

### [Repository-backed current state (descriptive)] Canonical BCSS truth-subject registry
Checkpoint 4 preserves the 10 canonical BCSS truth subjects from Checkpoint 1 and Checkpoint 3:
- `bcss_runtime_state_authority`
- `bcss_backup_slot_execution`
- `bcss_backup_job_execution`
- `bcss_backup_archive_lineage`
- `bcss_restore_execution`
- `bcss_restore_drill_evidence`
- `bcss_recovery_posture`
- `bcss_recovery_trust`
- `bcss_recovery_certification`
- `bcss_external_dependency_continuity`

### [Repository-backed current state (descriptive)] Adjacent represented concepts
Checkpoint 4 also documents 6 adjacent represented truth concepts already visible in the repository without creating new BCSS truth-subject duplicates:
- platform availability
- backup integrity
- manifest integrity
- notification delivery
- recovery readiness
- operational health

The detailed inventory is in the companion truth-subject artifact.

---

## 9. Migration Wave Model

### [Constitutional (normative)] Approved waves
Only these waves are approved:
- Wave 0 — Discovery
- Wave 1 — Evidence Vocabulary
- Wave 2 — Truth Subject Registration
- Wave 3 — Claim Binding
- Wave 4 — Operator Surface Adoption
- Wave 5 — Automation Adoption
- Wave 6 — AI Adoption
- Wave 7 — Recovery Certification
- Wave 8 — Platform Convergence

### [Constitutional (normative)] Assignment rule
Every identified implementation gap shall belong to exactly one wave.

---

## 10. Operational Truth Coverage Report

### [Repository-backed current state (descriptive)] Coverage counts

| Coverage item | Count | Notes |
|---|---:|---|
| Active operator surfaces inventoried | 24 | detailed in the surface claim matrix |
| Canonical BCSS truth subjects | 10 | existing registered BCSS truth-subject entries |
| Adjacent represented truth concepts | 6 | mapped back to existing canonical owners |
| Legacy surfaces discovered | 1 | `/admin/operations-dashboard` |
| Duplicate surfaces discovered | 1 | `/admin/platform-overview` |
| Unsupported discovered surfaces | 1 | `PlatformTrustDashboard.jsx` active reachability not found |
| Missing BCSS-specific definitions | 4 | notification delivery surface, manifest integrity surface, recovery class runtime model, AI claim contract |
| Unsupported claim zones | 10 | current surfaces where wording can exceed explicit claim labeling if not bounded |
| Open repository unknowns | 4 | listed in Section 12 |
| Wave 1 items | 2 | vocabulary convergence gaps |
| Wave 2 items | 2 | truth-subject registration / adjacent concept mapping gaps |
| Wave 3 items | 4 | claim-binding gaps |
| Wave 4 items | 2 | operator-surface labeling gaps |
| Wave 5 items | 1 | automation-consumer adoption gap |
| Wave 6 items | 1 | AI adoption gap |
| Wave 7 items | 1 | recovery certification gap |
| Wave 8 items | 1 | platform convergence gap |

---

## 11. Repository Findings

### [Repository-backed current state (descriptive)] Strongest current repository strengths
1. `canonical_truth.py` already provides a canonical BCSS ownership backbone.
2. `archive_lineage.py` already provides the strongest repository-backed BCSS evidence-quality and confidence pattern.
3. `backup_verification.py` already demonstrates disciplined bounded claim wording.
4. `recovery_dashboard.py` already demonstrates deterministic recovery posture fan-in.
5. `integration_truth.py` already demonstrates separated configuration / connectivity / operational truth.

### [Repository-backed current state (descriptive)] Highest adoption risks
1. mixed surfaces can flatten multiple subclaims into one stronger umbrella claim
2. derived trust / score surfaces can be mistaken for verification or certification
3. deployment certification can be mistaken for BCSS recovery certification
4. health and version endpoints currently surface truth without explicit OTS claim labels

---

## 12. Open Repository Unknowns

### [Repository-backed current state (descriptive)] Unknowns that remain unknown
1. No distinct active BCSS-only notification-delivery operator surface was found beyond backup verification email/report and generic routing/trust surfaces.
2. No standalone BCSS manifest-integrity operator surface was found; manifest integrity is embedded inside archive lineage and restore validation paths.
3. No repository-backed BCSS recovery-class runtime surface was found; recovery certification remains registration-only and bounded by deployment readiness evidence.
4. No repository-wide AI claim-governance runtime contract was found for BCSS-facing summaries or recommendations.

Unknown remains unknown until repository evidence changes.

---

## 13. Exact Next Bounded Implementation Checkpoint

### [Deferred implementation] Next bounded checkpoint
**Checkpoint 5 — Wave 1 + Wave 3 starter adoption map for active BCSS surfaces**

Bounded scope:
- add evidence-vocabulary normalization plan for active BCSS APIs
- add explicit claim-ceiling / prohibited-wording mapping for recovery snapshot, backup verification, backup trust, dependency continuity, and deployment readiness surfaces
- no migrations
- no runtime behavior change beyond surface labeling only if separately authorized

---

## 14. Verdict

### [Repository-backed current state (descriptive)] Completion reading
Checkpoint 4 succeeds if a future engineer can select any inventoried BCSS operator surface and determine:
- what reality is represented
- what observations exist
- what evidence exists
- what evidence quality exists
- what confidence exists
- which truth subject owns it
- what truth is established
- what claim is constitutionally permitted
- what wording is prohibited
- which migration wave owns future implementation

without introducing duplicate architecture.

### [Constitutional (normative)] Verdict
`GO — the Operational Truth Spine adoption blueprint is repository-backed, deterministic, and bounded.`
