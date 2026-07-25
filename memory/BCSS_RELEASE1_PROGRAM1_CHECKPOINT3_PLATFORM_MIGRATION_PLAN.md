# BCSS Release 1 · Program 1 · Checkpoint 3
## Platform Migration Plan

This document derives its authority from BCSS_RELEASE1_PROGRAM1_CHECKPOINT3_MASTER_FOUNDATION.md and does not establish independent constitutional requirements.

Date: 2026-07-25

---

## 1. Purpose

### [Deferred implementation] Purpose
This artifact provides the approved wave-based migration philosophy for future BCSS adoption work. It is planning only and performs no migration in Checkpoint 3.

---

## 2. Wave Model

### [Constitutional (normative)] Migration philosophy
BCSS adoption shall be wave-based, not subsystem-based.

This preserves one platform-wide evidence language and reduces the risk that one module modernizes into a second evidence or truth architecture while other modules remain divergent.

---

## 3. Wave 1 — Evidence Vocabulary Convergence

### [Deferred implementation] Objective
Converge BCSS-facing evidence-bearing surfaces onto the constitutional Layer 1 / Layer 2 / Layer 3 vocabulary.

### [Deferred implementation] Likely repository areas
- `backend/lib/archive_lineage.py`
- `backend/routes/recovery_dashboard.py`
- `backend/backup_verification.py`
- `backend/server.py` backup trust surface
- `backend/routes/integration_truth.py`

### [Deferred implementation] Exit criteria
- BCSS-facing payloads and/or operator surfaces can disclose raw evidence class, evidence quality, and confidence where applicable
- no second vocabulary registry is introduced

### [Deferred implementation] No-go boundaries
- no forced rewrite of every domain-local status model in one pass
- no replacement of `canonical_status.py`

---

## 4. Wave 2 — Truth-Subject Registration Convergence

### [Deferred implementation] Objective
Converge BCSS-facing consumers to use the existing BCSS truth-subject registry consistently when rendering or validating claims.

### [Deferred implementation] Likely repository areas
- `backend/lib/canonical_truth.py` consumers
- recovery, trust, verification, dependency, and certification-facing routes

### [Deferred implementation] Exit criteria
- every BCSS-facing surface can be mapped cleanly to one truth subject boundary
- no owner ambiguity remains at the operator layer

### [Deferred implementation] No-go boundaries
- no new BCSS truth subjects unless a future amendment requires them
- no parallel registry

---

## 5. Wave 3 — Claim Binding

### [Deferred implementation] Objective
Bind every BCSS-facing surface to explicit `Observed`, `Verified`, or `Certified` claim ceilings and prohibited stronger claims.

### [Deferred implementation] Likely repository areas
- `backend/routes/recovery_dashboard.py`
- `backend/backup_verification.py`
- `backend/server.py` backup trust endpoint
- `backend/routes/admin_deployment_readiness.py`
- selected frontend BCSS operator surfaces

### [Deferred implementation] Exit criteria
- each surface maps its displayed claims to approved claim classes
- claim inflation paths are removed or labeled honestly

### [Deferred implementation] No-go boundaries
- no conflation of deployment certification with BCSS recovery certification
- no fake-green shortcuts

---

## 6. Wave 4 — Operator Surfaces

### [Deferred implementation] Objective
Expose the bound evidence and claim model to operators in the BCSS-facing UI and reports.

### [Deferred implementation] Likely repository areas
- Admin Recovery UI
- backup verification report/email
- dependency continuity views
- future BCSS-facing OCC drill-throughs

### [Deferred implementation] Exit criteria
- operators can see what kind of claim they are reading
- stale/preview/representative/full-platform boundaries are explicit

### [Deferred implementation] No-go boundaries
- no duplicate BCSS dashboard
- no UI-wide terminology rewrite unrelated to BCSS surfaces

---

## 7. Wave 5 — AI Consumption

### [Deferred implementation] Objective
Ensure AI-consuming or AI-generating BCSS-relevant flows consume the constitutional evidence language rather than domain-local assumptions.

### [Deferred implementation] Likely repository areas
- any future BCSS-aware AI summarization or recommendation path
- existing manifest-based precedent from `services/dr_evidence/manifest.py`

### [Deferred implementation] Exit criteria
- AI surfaces can identify claim basis rather than inferring unsupported certainty
- AI prompts/manifests do not overclaim beyond evidence class and claim ceiling

### [Deferred implementation] No-go boundaries
- no global AI rewrite in one wave
- no BCSS-specific AI engine creation if an existing canonical pattern suffices

---

## 8. Wave 6 — Certification Convergence

### [Deferred implementation] Objective
Adopt the shared recovery certification class model and converge BCSS certification rendering accordingly.

### [Deferred implementation] Primary dependency
- `BCSS-R13`

### [Deferred implementation] Likely repository areas
- recovery certification surfaces
- class-based operator labels
- certification evidence packaging

### [Deferred implementation] Exit criteria
- recovery claims are rendered against Classes 0–8 without unsupported inheritance
- certification freshness and scope are explicit

### [Deferred implementation] No-go boundaries
- no claim of full-platform, DR, BC, or production certification without the class-specific evidence required by the Constitution

---

## 9. Cross-Wave Guardrails

### [Constitutional (normative)] Guardrails
1. Reuse existing canonical architecture first.
2. Do not create a second evidence registry.
3. Do not create a second truth registry.
4. Do not let trust scores imply certification.
5. Do not let deployment certification imply recovery certification.
6. Do not let preview evidence imply production proof.
7. Do not migrate one subsystem into architectural drift while the platform language remains unconverged.

---

## 10. Suggested Future Execution Order

### [Deferred implementation] Order
1. Wave 1 — Evidence vocabulary convergence
2. Wave 2 — Truth-subject registration convergence
3. Wave 3 — Claim binding
4. Wave 4 — Operator surfaces
5. Wave 5 — AI consumption
6. Wave 6 — Certification convergence

### [Deferred implementation] Why this order is repository-first
The order follows the repository’s current strengths:
- ownership already exists
- lineage already exists
- operator surfaces already exist
- certification classes do not yet exist at runtime

So the platform should first converge the language, then bind the claims, then surface them, then move into class-model adoption.
