# `/app/memory/` — Governance Doc Index

_30-second orientation map for future agents and forks · 2026-06-01 (last updated 2026-06-01 — OMEGA · iter452.5.1 P0 ORPHAN ELIMINATION SHIPPED · 🟢 5-tier identity ladder live · orphan corner architecturally impossible · 61/61 pytest green (52 + 9 new) · iter452.5.2 P1 authorized for next batch · Tier 2 frozen · iter453 BUILD inherits ladder natively)._

---

### 00 · OMEGA · iter452.5.1 P0 ORPHAN ELIMINATION SHIPPED (2026-06-01)

| File | Purpose | Status |
|---|---|---|
| `ITER452_5_1_CERTIFICATION_REPORT.md` | What shipped (4 backend edits + 1 new test + 2 frontend edits) · per-tier ladder citations · `resolution_tier` retention design · 9/9 new + 52/52 prior pytest green · Tier-2 freeze 8/8 confirmed · iter452.5.2 (P1) authorization captured for next batch | 🟢 |

🟢 **The orphan corner is architecturally impossible for new submissions.** Tier 5 (`ADMIN_DEAD_LETTER_EMAIL` → `safety@mascigc.com`) always populates `binding.primary_recipient_email`. The forensic-audit RED finding from FSI Question 8 is closed.

🟢 **5-tier ladder live:** `_resolve_fl_user_email` (Tier 1 · `X-FL-Token`) → `_find_employee` (Tier 2 · employees directory) → `submitter_email_at_submit` (Tier 3) → `pm_email` (Tier 4 · jobs_master) → `_dead_letter_email` (Tier 5). Selected tier persisted as `binding.resolution_tier` AND stamped on every delivery-evidence event for Phase 1B mining.

🟢 **Frontend:** `NewDailyReport.jsx` and `NewIncident.jsx` attach `X-FL-Token` header on `enqueueUpload` when a Field Leader is logged into the platform. Two-line additive changes.

🟢 **Index for P2:** `(resolution_tier, created_at -1)` pre-emptively created at startup so iter455.1 aggregation is O(log n).

🟢 **iter452.5.2 (P1 Resend bounce webhook) authorized to commence next batch.** iter455.1 (P2 Accountability Chain Projection) authorized as bundle with Phase 1A Integration Certification.

🛑 **Stopped.** Awaiting operator: (a) iter452.5.1 production-deploy click, AND/OR (b) "PROCEED WITH ITER452.5.2" to begin P1 Resend bounce webhook (~3 realistic days).

---

### 00 · OMEGA · iter452.5 Tier 1 BUILD SHIPPED · 3 deliverables (2026-06-01)

| File | Purpose | Status |
|---|---|---|
| `ITER452_5_BUILD_KICKOFF.md` | Build kickoff capturing 6 operator authorizations · delivery-evidence taxonomy addendum (3 → 6 event kinds) · R1..R5+R-CERT plan · Tier-2 exclusion inventory | 🟢 |
| `ITER452_5_TIER1_TIER2_SCOPING.md` | Pre-build scoping addendum to the Public-Gate Remediation Plan · Tier 1 vs Tier 2 split · iter453 safe-start matrix · final estimates | 🟢 reference |
| `ITER452_5_IMPLEMENTATION_REPORT.md` | What shipped · 6 new + 7 additive edits · 1 new collection · 14 new pytest (6 unit · 8 integration) · 52/52 cumulative green · Tier-2 frozen 8/8 · Day-9 gate cleared | 🟢 |

🟢 **Backend shipped:** `lib/field_submitter_identity.py` (core lib · resolve_identity · JWT mint/verify · 6-event chain) + `lib/fsi_email_sender.py` (Resend wrapper) + `routes/field_revision.py` (`/api/revise/{token}` · project team helper · admin bindings list).

🟢 **Frontend shipped:** `components/FieldSubmitterIdentityForm.jsx` (shared dropdown + email + consent block) + `pages/Revise.jsx` (passwordless `/revise/:token` page · uses axios to sidestep Sentry's fetch body-reader).

🟢 **Database:** new `field_submitter_bindings` collection with unique `(workflow, record_id)` index + employee + project indexes (idempotent at startup).

🟢 **Delivery-evidence taxonomy (operator directive #6):** `notification_dispatch_attempted` · `_succeeded` · `_failed` · `revision_link_issued` · `_consumed` · `revision_saved` — all written to existing `workflow_state_events` collection under `evidence.delivery_event`. Phase 1B can prove the chain closed end-to-end with a one-liner aggregation.

🟢 **Tier 2 discipline:** 8/8 components confirmed absent (no Twilio · no VAPID · no SW push · no phone field · no PWA install · no preference UI · no device-revocation · no per-employee channel prefs).

🟢 **Day-9 gate cleared:** R1+R2+R3 preview-ready → iter453 BUILD authorized to commence per operator directive #4.

🛑 **Stopped.** Awaiting operator's iter452.5 production-deploy authorization OR explicit "PROCEED WITH ITER453 BUILD" (OC-003 QA/QC + OC-004 Site Inspection Follow-Up · inherits Tier-1 service natively).

---

### 00 · OMEGA · iter452.5 Tier 1 / Tier 2 Scoping Addendum (2026-06-01)

| File | Purpose | Verdict |
|---|---|---|
| `ITER452_5_TIER1_TIER2_SCOPING.md` | Addendum to the Public-Gate Accountability Remediation Plan · operator's Tier 1 / Tier 2 split formalized · 8-field Tier-1 minimum (dropped phone, device_id, superintendent email from Tier-1) · 5 phases R1..R5 + R-CERT · Tier 1 realistic 13.75 d / buffered 18 d · Tier 2 additive realistic 20 d / buffered 26 d · combined realistic 33.75 d / buffered 44 d · earliest safe iter453 BUILD start = Day 9 of iter452.5 (after R1+R2+R3 preview-ready) · iter453 design may run in parallel from Day 1 · 5-item delta risk register, no HIGH unmitigated | 🟢 design only · awaiting GO/NO-GO |

🟢 **Tier 1 scope (required for Phase 1A continuation):** submitter identity resolution · employee directory mapping · project ownership resolution (reuse `pm_routing`) · email-based revision delivery (signed JWT + `/revise/<jwt>`) · audit trail integration · reusable workflow hooks. **Single hard rule:** `submitter_email_at_submit` required; non-email crews fall back to PM-relay (Option E).

🟡 **Tier 2 (deferred to Phase 1A.5 or Phase 2):** SMS (Twilio) · Web Push (VAPID + SW) · iOS PWA install flow · device-binding enhancements · per-employee channel preference UI.

🟢 **Sequencing:** iter452 deploy authorization → iter452.5 platform sprint (Week 1 R1 · Week 2 R2+R3 · Week 3 R4+R5+R-CERT) → iter452.5 deploy → iter453 BUILD (already started Day 9 in parallel) completes → iter453 deploy → iter454 (OC-005) → iter455 Phase 1A Integration Certification.

🛑 **Stopped.** Design decision delivered. Zero code. Awaiting operator's confirmation message authorizing Tier 1 only OR Tier 1 + Tier 2 OR deferral.

---

### 00 · OMEGA · Public-Gate Accountability Remediation Plan (2026-06-01)

| File | Purpose | Verdict |
|---|---|---|
| `PUBLIC_GATE_ACCOUNTABILITY_REMEDIATION_PLAN.md` | Single design-decision document answering all 8 operator questions · three-layer hybrid identity model (directory anchor + per-submit contact + resolved responsibility) · 10 minimum required fields per public-gate workflow · architecture · migration · ~14.5 day effort for Tier-1 · ~25.5 day effort for full Tier-1/2/3 stack · 6 workflows affected · 6 retrofit at ~2 hrs each · iter452.5 dedicated platform sprint recommended between iter452 deploy and iter453 BUILD | 🟢 solvable once · awaiting authorization |

🟢 **Recommended phase placement:** **iter452.5 dedicated platform sprint** (not iter453, not iter454, not iter455, not Phase 1B). Reasoning: cost compounds if retrofitted later; risk compounds with each iteration shipped at YELLOW; mental model aligns with OMEGA "build platform → build workflows" discipline.

🟢 **Open operator decisions:** authorize iter452.5 · sprint timing · Tier-1 channel choice (email-only recommended) · retention window (90d default) · consent wording · legacy backfill policy (none-with-flag recommended) · iOS PWA install messaging.

🛑 **Stopped.** Design decision delivered. Zero code. Awaiting operator authorization for iter452.5 platform sprint OR explicit deferral.

---

### 00 · OMEGA · Public-Gate Ownership Forensic Audit + Push Feasibility · 6 deliverables (2026-06-01)

| File | Purpose | Classification |
|---|---|---|
| `DAILY_REPORT_OWNERSHIP_AUDIT.md` | OC-002 evidence: 29 stored fields · `prepared_by` + `superintendent` free text only · NO email/phone/employee_id/portal_user_id/device_id captured · PM resolved via jobs_master · field-submitter unreachable | 🟡 YELLOW |
| `QAQC_OWNERSHIP_AUDIT.md` | OC-003 evidence: 35 stored fields · NO inspector field · sub-rep is free-text only · NO sub-rep contact · CAPA owned by department string · PM resolved via jobs_master | 🟡 YELLOW |
| `PUBLIC_GATE_WORKFLOW_ACCOUNTABILITY_REPORT.md` | Cross-workflow rollup · 6 public-gate workflows share the same accountability hole · 1/261 employees have email · 0/261 have phone · push/sms/email channels structurally unimplemented · PM-side GREEN, field-side RED | 🟡 YELLOW + 🔴 systemic |
| `PUSH_NOTIFICATION_FEASIBILITY_REPORT.md` | iOS Safari requires PWA-install + iOS 16.4+ for push · manifest already configured · 0 push subscriptions in DB · no VAPID config · ~5 weeks engineering for full push+fallback stack | 🟡 feasible-but-expensive |
| `PUBLIC_GATE_NOTIFICATION_ARCHITECTURE.md` | Target architecture: new `field_submitter_bindings` collection · dispatcher upgrade for delivery_log · 4-tier channel ladder · privacy/retention contract · ~20 backend + ~15 frontend files touched | 🟢 architecturally sound |
| `REVISION_DELIVERY_OPTIONS.md` | 7 options (A=email/B=SMS/C=push/D=QR/E=PM-relay/F=portal-account/G=unsafe) · recommended tiered stack A→B→C→E · signed-JWT contract · audit-event encoding | 🟢 multiple viable paths |

🔴 **CRITICAL PHASE 1A FINDING:** corrective actions raised through OC-001..OC-005 lifecycle workflows can reach the **office side** (PM/Admin/Safety via in-app bell + PM email) but **cannot reach the field submitter** through the platform. The platform does not capture submitter email/phone/device for any public-gate workflow.

🟡 **Operator decision required:** authorize one of —
- **Branch A:** Tighten field identity at the public gate (employee dropdown + per-submit contact + directory enrichment)
- **Branch B:** Add alternative delivery channels (Web Push + SMS + email-tier)
- **Branch C:** Accept the gap as out-of-Phase-1A and document deferred closure

🛑 **Stopped.** Zero code. Zero design proposals. Evidence and options on the table. Iter453 (OC-003 + OC-004) build authorization is independent of this finding but must factor in whether the operator wants the gap closed in-flight.

---

### 00 · OMEGA iter452 · Phase 1A BUILD · OC-002 + OC-007 · 4 deliverables (2026-06-01)

| File | Purpose | Status |
|---|---|---|
| `ITER452_IMPLEMENTATION_REPORT.md` | OC-002 (DR Office Review) + OC-007 (Payroll Variance Finalization) shipped · 6 new files · 6 additive edits · 1317 LOC · notification fan-out · server-side flagged-row decision safety net · NO AUTO FINALIZE | 🟢 |
| `ITER452_CERTIFICATION_REPORT.md` | 24/24 design gates green (12 per workflow) · 21/21 new pytest green · 38/38 cumulative (with iter451) · live curl walkthroughs proving every transition + every gate | 🟢 |
| `ITER452_REGRESSION_REPORT.md` | Surface-by-surface regression · 0 destructive changes · existing CRUD/CSV exports/legacy decision endpoint untouched · iter451 tests still green | 🟢 |
| `ITER452_RISK_REPORT.md` | 10-item risk register · 🟢 LOW overall · 3 🟡 backlogged · production-deploy assessment | 🟢 |

🟢 **OC-002 lifecycle:** OPEN → PENDING_REVIEW → REVIEWED → CLOSED · with kickback (PENDING_REVIEW → OPEN, reason required) and audited REOPEN. Notification fan-out on PENDING_REVIEW to PM/Safety/Admin.

🟢 **OC-007 lifecycle:** OPEN → UNDER_REVIEW → APPROVED → FINALIZED · with audited REOPEN. NO AUTO FINALIZE enforced by state graph + 3-flag attestation + server-side per-row decision safety net.

🟢 **Endpoints (additive):**
- `POST /api/daily-reports/{id}/transition` · `GET /state-events` · `GET /lifecycle`
- `POST /api/hr/payroll-variance/batches/{id}/transition` · `GET /state-events` · `GET /lifecycle`

🟢 **Frontend:** New `<LifecyclePanel/>` generic shell (config-driven) + per-workflow wrappers. Reused for iter451 incident pattern; ready for iter453-454.

🛑 **Stopped.** iter453 (OC-003 QA/QC Follow-Up + OC-004 Site Inspection Follow-Up), iter454 (OC-005 JHA Ledger), iter455 (Phase 1A Integration Certification) all FROZEN until operator authorization.

---

### 00 · OMEGA iter451 · Phase 1A BUILD · Pre-Deploy Operational Certification · 3 deliverables (2026-06-01)

| File | Purpose | Status |
|---|---|---|
| `ITER451_OPERATIONAL_CERTIFICATION.md` | 8-axis pre-deploy operational certification · 15 live transitions across non-OSHA + OSHA incidents · audit-trail integrity · OSHA & CAPA & closure & reopen handling proven · **VERDICT: GO TO DEPLOY** | 🟢 |
| `ITER451_ROLE_VALIDATION.md` | 3-role simulation (Safety Manager · Superintendent → PM-token analog · Super Admin) · 16/16 permission expectations met · defence-in-depth posture | 🟢 |
| `ITER451_USABILITY_REPORT.md` | Per-state UI walkthrough · modal-guard verification · history drawer audit-row parity · operator discoverability assessment · no HIGH/BLOCKING findings | 🟢 |
| `iter451_cert_evidence/` | Raw curl probe logs (01_role_probes · 02_lifecycle_walk · 03_osha_walk · 04_audit_trail). UI screenshots rendered inline to operator during the live session. | — |

🟢 **FINAL VERDICT: GO TO DEPLOY.** OC-001 Incident Lifecycle is operationally certified. All 8 operator-mandated verification axes (permissions · audit · OSHA · CAPA · closure · reopen · UI · discoverability) green. RECLOSE flow proven. Zero code changes this iteration — certification only.

🛑 **Stopped.** Awaiting operator's explicit production-deploy authorization OR iter452 BUILD authorization (OC-002 Daily Report Office Review + OC-007 Payroll Variance Finalization).

---

### 00 · OMEGA iter451 · Phase 1A BUILD · OC-001 Incident Lifecycle · 4 deliverables (2026-06-01)

| File | Purpose | Status |
|---|---|---|
| `ITER451_IMPLEMENTATION_REPORT.md` | Files shipped (5 new · 2 additive edits) · endpoint inventory · lifecycle-contract answers · 1238 LOC | 🟢 |
| `ITER451_CERTIFICATION_REPORT.md` | 12/12 design gates green · 17/17 pytest green · Definition-of-DONE proof matrix · live-curl evidence | 🟢 |
| `ITER451_REGRESSION_REPORT.md` | Surface-by-surface regression analysis · 0 destructive changes · auth gates preserved · existing test battery untouched | 🟢 |
| `ITER451_RISK_REPORT.md` | 10-item risk register · 🟢 LOW overall · production-deploy assessment · iter455 open items | 🟢 |

🟢 **Canonical 5-state lifecycle shipped (OC-001):** OPEN → UNDER_INVESTIGATION → CORRECTIVE_ACTION_REQUIRED → PENDING_CLOSURE → CLOSED · with audited REOPEN.

🟢 **Endpoints (additive):** `POST /api/incidents/{id}/transition` · `GET /api/incidents/{id}/state-events` · `GET /api/incidents/{id}/lifecycle`. Existing CRUD unchanged.

🟢 **Audit:** New `workflow_state_events` collection · append-only · 3 indexes · 7y TTL scheduled for iter455 deploy migration.

🟢 **Frontend:** `<IncidentLifecyclePanel/>` on `ViewIncident.jsx` · state pill · role-gated buttons · closure attestation modal (+OSHA ack) · reopen-with-reason modal · audit-trail history drawer · print-hidden.

🟢 **Tests:** `backend/tests/test_iter451_incident_lifecycle.py` · 9 unit + 8 live-HTTP integration tests.

🛑 **Stopped.** Iter452 (OC-002 Daily Report Office Review + OC-007 Payroll Variance Finalization), iter453, iter454, iter455 all FROZEN until operator BUILD authorization for the next sprint or production-deploy authorization for iter451.

---

### 00 · OMEGA iter450 · Platform Completion Program · Phase 1A FINAL BUILD PACKAGE · 10 deliverables (2026-06-01)

| File | Purpose | Status |
|---|---|---|
| `PHASE1A_FINAL_ARCHITECTURE.md` | Final architecture · canonical 5-state vocab (OPEN · IN_PROGRESS · PENDING_REVIEW · PENDING_CLOSURE · CLOSED) · per-workflow state maps · cross-workflow contracts · OC-005 JHA ledger model | 🟢 |
| `PHASE1A_DATABASE_IMPACT.md` | Schema additions per workflow · single canonical `workflow_state_events` audit collection · `jha_acknowledgements` ledger · indexes · TTL/retention (7y OSHA/IRS) | 🟢 |
| `PHASE1A_UI_IMPACT.md` | Per-workflow screen changes · new action buttons · status badges · attestation modals · accountability projection deltas | 🟢 |
| `PHASE1A_API_IMPACT.md` | New routes · payload contracts · idempotency keys · error envelope · backwards-compat guarantees | 🟢 |
| `PHASE1A_ROLE_PERMISSION_MATRIX.md` | 6 workflows × transitions × 9 roles · scoping rules · Super-Admin break-glass | 🟢 |
| `PHASE1A_BUILD_PLAN.md` | 5-sprint build sequence · LOC budget · risk register · checkpoints | 🟢 |
| `PHASE1A_TEST_PLAN.md` | ~30 test classes · unit/integration/regression/migration/perf · acceptance gates per workflow | 🟢 |
| `PHASE1A_DEPLOYMENT_PLAN.md` | Preview→Prod sequencing · feature flag plan · zero-downtime contract · migration order | 🟢 |
| `PHASE1A_ROLLBACK_PLAN.md` | Per-sprint rollback procedure · data preservation contract · forward-only schema discipline | 🟢 |
| `PHASE1A_GO_NO_GO.md` | Operator-facing decision matrix · 12 design gates · pre-build attestations · sign-off block | 🟢 |

🟢 **Certified Phase 1A scope (6 workflows · ~12.5 engineer-days · additive-only):** OC-001 Incident Lifecycle · OC-002 Daily Report Office Review · OC-003 QA/QC Follow-Up · OC-004 Site Inspection Follow-Up · OC-005 JHA Acknowledgement Ledger · OC-007 Payroll Variance Finalization.

🟢 **Certification statement #1:** "Phase 1A scope is complete."

🟢 **Certification statement #2:** "No additional workflow currently ranks above the approved Phase 1A scope based on all completed operational-completeness audits and scope-challenge reviews."

🛑 **Agent STOPPED.** Zero LOC written. NO build. NO deployment. **Awaiting operator's explicit BUILD authorization.** Phase 1B (status canonicalization · OC-010/014/018), Phase 2 (placeholders · OC-008/009/013/016), Phase 3 (employee lifecycle), Phase 4 (asset/equipment lifecycle), Phases 5–10, White Label, and ForgedOps Operations Center remain explicitly OUT-OF-SCOPE and FROZEN.

---

### 00 · OMEGA iter449 · Phase 1A Pre-Build Priority Validation · 4 deliverables (2026-06-01)

| File | Purpose | Status |
|---|---|---|
| `CRITICAL_FINDING_RANKING.md` | 22 register findings rescored on 13 impact axes · top-10 weighted ranking · 90-day damage analysis · OC-005 vs OC-010 elevation case | 🔴 |
| `PHASE1A_PRIORITY_VALIDATION.md` | 15 mandatory operator questions answered with evidence · binary verdict 🟡 B · revised Phase 1A scope · Phase 1B/2/3/4 sequencing confirmed | 🟡 |
| `PHASE1A_SCOPE_CHALLENGE_REPORT.md` | Formal challenge against 5 current workflows · OC-003/4 survive on architectural-reuse · OC-005 elevation argument · 4 alternative scope options A/B/C/D | 🟡 |
| `CUSTOMER2_BLOCKER_MATRIX.md` | 11 of 22 findings classified by Customer #2 blocker tier (T1..T5) · per-tenant day-1 operational expectation · sign-off checklist | 🔴 |

🟡 **Final verdict:** OPTION B — scope INCOMPLETE. Current 5-workflow Phase 1A scope is **correct in selecting OC-001, OC-002, OC-003, OC-004, OC-007** but **OC-005 (JHA Acknowledgement Ledger) must be elevated** because (1) it scores #4 of 22 weighted findings (31.5), (2) carries direct OSHA 1926.21(b)(2) general-duty exposure, (3) is the highest-frequency unaddressed safety workflow (~500/week), (4) is a Customer #2 blocker, (5) has the lowest build cost of any Phase 1A candidate (~3 engineer-days · additive only), (6) pairs naturally with OC-001 (both OSHA-touching).

🛑 **Recommended Phase 1A revised scope:** 6 workflows · ~12.5 engineer-days. Operator decision required (A/B/C/D from scope challenge §9).

🛑 **Confirmed-correct phase sequencing:** Phase 1B = OC-010 vocab canonicalization + OC-014 offboarding + OC-018 audit-trail. Phase 2 = OC-008 PPE Return + OC-009 Photo Janitor + OC-013 Onboarding + OC-016 Continuity Events. Phase 3+ = remaining cleanup. White Label and ForgedOps Operations Center remain FROZEN.

---

### 00 · OMEGA iter448 · Platform Completion Program · Phase 1A DESIGN · 4 deliverables (2026-06-01)

| File | Purpose | Status |
|---|---|---|
| `PHASE1A_WORKFLOW_DESIGN.md` | 10 design principles · 5 workflows (Incidents · DR · Payroll Variance · QA/QC · Site Inspection) · state maps · closure conditions · schema additions · UI changes · cross-workflow specs · 5 open questions for operator | 🟡 |
| `PHASE1A_STATE_MACHINE.md` | Canonical 5-state vocab (OPEN · IN_PROGRESS · PENDING_REVIEW · PENDING_CLOSURE · CLOSED) · per-workflow transition tables · guards · forbidden transitions · idempotency contract · Mermaid diagrams | 🟡 |
| `PHASE1A_ROLE_MATRIX.md` | 5 workflows × 11 transitions × 9 roles · 7 transition tables (Incident · DR · Payroll · QA/QC Inspection · QA/QC Deficiency · Site Inspection · Site Finding) · Super-Admin break-glass · scoping rules | 🟡 |
| `PHASE1A_CERTIFICATION_PLAN.md` | 3-gate certification (Design → Build → Preview → Prod) · 12 design gates · unit/integration/regression/migration/perf tests (~30 test classes) · rollback contract · 7 success metrics · operator sign-off block | 🟡 |

🟡 **Status: DESIGN COMPLETE · awaiting operator certification.** Per directive, no code will be written until operator answers 5 open questions in `PHASE1A_WORKFLOW_DESIGN.md` §9 and affirms 12 design gates in `PHASE1A_CERTIFICATION_PLAN.md` §1.

🎯 **Phase 1A goal**: 5 workflows transition from 🔴 INCOMPLETE → 🟢 COMPLETE. Operational Completeness rises from 56 % → ≥ 65 %. Zero regressions. Single canonical audit collection (`workflow_state_events`). 7-year TTL aligned with OSHA + IRS retention.

🛑 **Stopped.** No Build authorization issued. Phase 1B (status canonicalization across all 18 vocab) · Phase 2 (placeholders) · Phase 3 (employee lifecycle) · Phase 4 (asset/equipment lifecycle) · Phases 5-10 all explicitly out-of-scope until Phase 1A is certified, built, deployed, and operator-signed.

---

### 00 · OMEGA iter447 · Operational Completeness Audit · 11 deliverables (2026-06-01)

| File | Purpose | Status |
|---|---|---|
| `OPERATIONAL_COMPLETENESS_EXECUTIVE_SUMMARY.md` | **Start here.** Operator one-pager · scorecard · 22-finding register · Customer #2 / White Label / Ops Center readiness verdicts (all 🔴) | 🟡 |
| `OPERATIONAL_WORKFLOW_INVENTORY.md` | 55-workflow inventory (60-row table) with portal · routes · collections · owner roles · lifecycle classification | 🟡 |
| `OPERATIONAL_LIFECYCLE_MATRIX.md` | Per-action × per-workflow matrix (17 columns including Crt/Vw/Edt/Asn/Rsn/StC/Cls/Reo/Arc/Del/Aud/API/UI/Acc/CC/Prm/Fbk) | 🟡 |
| `STATUS_VOCABULARY_AUDIT.md` | 18 distinct status vocabularies catalogued · 11 pairwise incompatibilities · consolidation map | 🔴 |
| `SOURCE_OF_TRUTH_AUDIT.md` | 21 of 55 workflows show source-vs-consumer mismatch · 4 🔴 critical defects | 🔴 |
| `ROLE_ACTIONABILITY_MATRIX.md` | 9 roles × per-workflow · UI-vs-API gap inventory | 🟡 |
| `CLOSURE_PATH_AUDIT.md` | 24 of 41 workflows have closure path · 9 cannot exit active list · 11 flag-only · 1 placeholder | 🟡 |
| `AUDIT_TRAIL_COVERAGE_REPORT.md` | 13 workflows with dedicated audit · 21 flag-only · 7 zero | 🟡 |
| `COMMAND_CENTER_ACCOUNTABILITY_ALIGNMENT.md` | 9 producer-consumer pairs · 5 mismatches (status vocab + age math) | 🟡 |
| `USER_TASK_COMPLETION_AUDIT.md` | 6 of 16 user tasks are dead-ends today | 🟡 |
| `OPERATIONAL_COMPLETENESS_REGISTER.md` | **22 findings register** — OC-001..OC-022 · severity-assigned · phase-grouped (Phase 1A/1B/2/3/4) · Customer #2 / White Label / Ops Center impact per row | 🔴 |
| `completeness_evidence/` | Route inventory artifacts (260 backend routes · 252 frontend routes) | — |

🔴 **Top 10 operational gaps**: Incident closure · DR office review · QA/QC follow-up · Site Inspection follow-up · Payroll Variance batch finalize · PPE Return (placeholder) · Photo Janitor (placeholder) · JHA acknowledgement ledger · Employee Offboarding multi-step · Audit-trail gaps (11 workflows). Status vocabulary fragmentation (18 vocabs · 11 incompatible) is the cross-cutting blocker for White Label and ForgedOps Operations Center readiness.

🟢 **Strongest surfaces**: PO Requests · Asset Transfers · Dispatch Assignments · Fleet Defects · CAPA · Tasks · Fire Extinguishers · Document Expirations · Employees · Jobs · Suppliers · MFA · Backups · Recovery · Scheduler Runs (iter445). 24 of 41 lifecycle workflows have terminal closure paths.

🛑 **Operator status:** Stopped. Audit-only batch. Recommended remediation order per Executive Summary: Phase 1A (Incident/DR/Payroll closure + cosmetic alignment) → 1B (QA/QC + Inspection follow-up) → 2 (multi-step lifecycles) → 3 (vocab canonicalization) → 4 (audit-trail enrichments). Customer #2 onboarding and White Label and ForgedOps Operations Center should be gated on Phase 1A+1B completion.

---

### 00 · OMEGA iter446 · Production Deployment + Certification of iter445 · 3 deliverables (2026-06-01 · prod-time 2026-06-01T18:06:32Z)

| File | Purpose | Status |
|---|---|---|
| `ITER446_PRODUCTION_DEPLOY_REPORT.md` | Pre/post-deploy probe transition · source_hash byte-equivalence with preview · frontend bundle string scan · timeline | 🟢 |
| `ITER446_PRODUCTION_CERTIFICATION.md` | 5/5 certification gates (Ownership · Audit · Dedup · UX · Regression) · Executive Operator Summary · Evidence Summary table · 🟢 PRODUCTION CERTIFIED | 🟢 |
| `ITER446_POST_DEPLOY_VERIFICATION.md` | 20-probe verbatim battery · regression matrix · /api/version envelope · bundle string scan · outstanding passive observation note | 🟢 |
| `iter446_evidence/` | 13 raw probe logs (01_version.txt … 13_po_digest_preview.txt) | 🟢 |

🟢 **Headline**: iter445 deployment successful — backend `source_hash` transitioned `f506574f… → 269f9269cfbd6399d489cbd0a4e87f5e` (matches preview post-iter445 exactly · byte-equivalence). New pod boot 2026-06-01T18:06:32Z · `app_env=production` · `db_name=masci_safety`. The new admin endpoint `/api/admin/scheduler-runs` returns the iter445 envelope under admin auth (was 404 pre-deploy). All 11 required iter445 UX string markers present in production main.c23ae9cd.js (4.88 MB bundle) — Per-Day Detail · Scheduler Runs · admin-tile-scheduler-runs · hr-pv-perday-link · open_detail=daily · Spot-check one employee · Payroll Variance (CSV) · On-Site Reference · Job Hazard Plans · Asset Transfers. Photo Viewer raw endpoint still returns presigned R2 URL (Sprint 1G unaffected). PO digest preview still returns 8 active PMs (send path intact). 0 regressions across 14 probed surfaces. Only passive observation outstanding: first Monday fire 2026-06-08T14:00:00Z will populate first row in `scheduler_runs` collection.

---

### 00 · OMEGA iter445 · Sprint Scheduler Hardening + UX Phase 1 · 8 deliverables (2026-06-01)

| File | Purpose | Status |
|---|---|---|
| `SCHEDULER_HARDENING_REPORT.md` | Phase A · two-layer dedup (L1 orphan-cancel · L2 unique-index `scheduler_runs` claim_slot) · coverage matrix for all 5 schedulers | 🟢 |
| `SCHEDULER_CERTIFICATION_REPORT.md` | Phase A cert · 7/7 unit tests · admin endpoint healthy · zero regressions in adjacent surfaces | 🟢 |
| `DIGEST_DEDUP_VERIFICATION.md` | Per-layer defense proof · concurrent-claim stress test · per-scheduler coverage · admin endpoint envelope | 🟢 |
| `UX_PHASE1_IMPLEMENTATION_REPORT.md` | Phase B · F-001..F-005 closed (variance deep-link · HR Hub copy · in-app digest replay · JHA + Asset Transfers in FL Hub) · LOC table · bilingual coverage | 🟢 |
| `UX_PHASE1_CERTIFICATION_REPORT.md` | Phase B cert · per-friction acceptance evidence · adjacent-surface no-regression matrix | 🟢 |
| `USER_FRICTION_REDUCTION_REPORT.md` | Persona-level impact (Sandy · PMs · Supers · Admins · Executives) · friction-event closure table · call-pattern improvement forecast | 🟢 |
| `DEPLOYMENT_RISK_REPORT.md` | Change inventory · risk-by-failure-mode · pre-existing risk carry-forward · rollback runbook · deploy windows | 🟢 |
| `GO_NO_GO_DECISION.md` | **Operator one-pager · Executive Operator Summary + Evidence Summary table · final 🟢 GO recommendation** | 🟢 |

🟢 **Headline**: Closes the singleton-scheduler race that caused duplicate Monday PO/safety/operator digests, and closes the entire 🔴 High-friction bucket from the persona audit (5 UX items). Backend: ~445 LOC across 7 files · new `scheduler_runs` collection with unique compound index + TTL + history index · new `/api/admin/scheduler-runs` endpoint. Frontend: ~315 LOC across 7 files · new AdminSchedulerRuns page · variance row deep-link · HR Hub tile-copy rewrite · new "On-Site Reference" group on Field Leadership Hub with bilingual JHA + Asset Transfers tiles. 7/7 unit tests pass · backend source_hash changed on restart · frontend smoke clean. Zero 🔴 residual risk; one 🟡 cosmetic (backup schedulers L1-only · fuzzy slot · `backup_runs` already audits). Rollback wall-clock < 10 min · `scheduler_runs` collection TTL-prunes at 90 days · no schema migration · no env vars. Recommended deploy window: Tue–Wed daytime ET, ≥48 h before Monday 2026-06-08 14:00 UTC. **Awaiting operator deploy authorization.**

---

**Read this first.** Use the section headings to find the doctrine
domain you need, then open the file(s) under it. Do NOT grep blindly
across 500 docs — the platform has strict domain boundaries.

> **Status legend:** ✅ active · 📐 planning · 🟢 implemented ·
> 🟡 deferred · ⛔ read-before-touching · 🚫 ABANDONED/DO-NOT-IMPLEMENT

---



### 00 · OMEGA Sprint 1G · Photo Viewer Forensic + Remediation · 4 deliverables (2026-02-27 · prod probes 2026-06-01T17:36Z)

| File | Purpose | Status |
|---|---|---|
| `PHOTO_VIEWER_FORENSIC_REPORT.md` | End-to-end forensic narrative · 75-sample audit · operator's named target photo evidence · 10-axis storage check | 🟢 |
| `PHOTO_STORAGE_AUDIT.md` | R2 bucket architecture · URI scheme distribution (100 % `photo://`) · permission/expiration model · orphan record inventory | 🟢 |
| `PHOTO_ROOT_CAUSE_ANALYSIS.md` | Causal chain (post-iter64 R2 migration · /thumb updated · /raw not updated) · alternative-hypothesis elimination | 🟢 |
| `PHOTO_REMEDIATION_PLAN.md` | Fix manifest · pre/post diff · deployment recipe · rollback procedure (<60s wall-clock) | 🟢 |
| `sprint1g_photo_forensic_evidence/` | Raw curl probe logs (01_photo_inventory · 02_raw_endpoint_probe · 03_random_sample_audit) | 🟢 |

🟢 **Headline**: Production "Photo data unavailable or corrupt" was a 100 %-affected single-defect contract mismatch between backend (`get_photo_raw` returned raw `photo://` R2 pointer) and frontend (lightbox renderable check accepts only `data:image/`, `blob:`, or `http`). Thumbnails were unaffected because `_serve_thumb` already dereferences via `_load_photo_bytes`. The fix is surgical (+32/-2 LOC across 2 functions in 1 file) and matches the existing `photo_storage.presigned_get_url` helper's documented use case ("serving full-resolution photos to the gallery lightbox so we don't proxy the bytes through FastAPI"). Post-fix `data_url` is a 15-minute presigned HTTPS URL the browser fetches directly from R2. Live preview verified. 6/6 new regression tests pass. The 3 pre-existing `test_iter47_master_validation.py::TestPhotoPerformance` failures are environment-data flakiness (orphan job_photos rows) proven pre-existing via `git stash` revert + re-run — NOT a Sprint 1G regression. Awaiting operator deploy authorization.

### 00 · OMEGA Sprint 1F · Production Deployment & Certification · 3 deliverables (2026-02-27 · prod-time 2026-06-01T02:28Z)

| File | Purpose | Status |
|---|---|---|
| `SPRINT1F_PRODUCTION_DEPLOY_REPORT.md` | Pre-deploy gates 1-5 (source · 46/46 tests · preview behaviour · clean tree · no scope drift) | 🟢 |
| `SPRINT1F_PRODUCTION_CERTIFICATION.md` | Operator-facing final verdict · 15/15 gates GREEN · 🟢 PRODUCTION CERTIFIED | 🟢 |
| `SPRINT1F_POST_DEPLOY_VERIFICATION.md` | 10-point post-deploy battery against `mascidocs.com` + raw evidence | 🟢 |
| `sprint1f_postdeploy_evidence/` | Raw curl logs from production probes (2026-06-01T02:29–02:32Z) | 🟢 |

🟢 **Headline**: Sprint 1F Command Center Owner Resolution Patch is live, healthy, and certified on production. Operator's primary success criterion (Job 24-06 = David Jewett) and secondary criterion (Jobs 20-07/22-08/24-08 remain Unassigned PM) both verified post-deploy. Production runtime restarted at 2026-06-01T02:28:31Z (new pod). Scheduler self-healed within 30s of pod handoff (singleton-lock TTL working as designed). All 10 post-deploy axes pass: Command Center loads (2284 ms) · accountability healthy (sources 441 ms · snapshot 1185 ms) · backup cadence intact (last backup 27.4 min old · 24,163 records · ok=True) · 5 sibling DELETE auth gates consistent · cross-portal /me identical to pre-deploy · zero new warnings · zero regressions · zero auth issues. The 2 AMBER warnings observed (R2 bucket-usage 92.38 GB · transient scheduler-quiet at first probe) are both pre-existing or self-healed artifacts, not Sprint 1F-introduced. Known limitations carried forward: RTO AMBER on production (operator activation of `drill_runs` row deferred per `DR_DRILL_REPORT.md` §7), R2 bucket governance (3 reversible options per `R2_STORAGE_GOVERNANCE_REPORT.md`), and the accountability_projection.py PO-request resolver still uses the same `primary_pm_*` field pattern (out of OMEGA Sprint 1F scope; same defect class, deferred).

### 00 · OMEGA Sprint 1F · Production Maturity Patch · 6 deliverables (2026-02-27)

| File | Purpose | Status |
|---|---|---|
| `OWNER_RESOLUTION_PATCH_REPORT.md` | P0 · root cause + surgical patch +8/-2 LOC for the Command Center JOBS-DR-MISSING owner resolver (legacy `project_manager` field now read) + 6-case regression suite | 🟢 |
| `OWNER_RESOLUTION_CERTIFICATION.md` | P0 · GO/NO-GO cert · 46/46 pass · job 24-06 displays David Jewett · LOW × 4 risk · <60s rollback | 🟢 GO TO DEPLOY |
| `DR_DRILL_REPORT.md` | P1 · automated drill `6db3c618ce69` · 10/10 axes GREEN · 5.10 min · 24,152 records · 678 photos rehydrated | 🟢 |
| `RECOVERY_CERTIFICATION_UPDATE.md` | P1 · preview recovery dashboard RTO transitioned AMBER → GREEN · prod dashboard activation deferred to operator | 🟢 |
| `R2_STORAGE_GOVERNANCE_REPORT.md` | P2 · audit-only · 91.49 GB above 50 GB ALERT · cadence ~6.5× config · 3 recommended options (A: raise thresholds · B: rationalize cadence · C: class-tier migration) | 🟡 AMBER |
| `USAGE_EVENTS_FAILURE_ANALYSIS.md` | P3 · audit-only · May 25 failures closed by iter428 (sort removal) + iter441 (collection exclusion) · `allow_disk_use=True` recommendation OBSOLETE | 🟢 |
| `DRILL_6db3c618ce69_REPORT.md` | Auto-generated per-drill artifact (axes table + restore counters + cleanup) | 🟢 |

🟢 **Headline**: Production Maturity Patch closes the four highest-value findings from the Production Observation Audit. P0 owner-resolution defect surgically patched (8 LOC) and certified GO-TO-DEPLOY (preview-verified, job 24-06 now displays David Jewett; pre-existing 40 CC+owner-fidelity tests all pass alongside 6 new tests). P1 DR drill executed end-to-end against a production-origin R2 archive in 5.10 min (66 % under 15 min RTO target), all 10 verification axes green, drill DB cleanly dropped, drill_runs row written to preview Mongo (production-dashboard activation is the only outstanding operator-side step). P2 R2 governance: bucket at 91.49 GB explained by ~13/day cadence (6.5× the configured 2/day) — three reversible options offered for next batch authorization. P3 usage_events failure analysis: the May 25 failures are pre-iter441 historical artifacts; the platform already has the optimal fix (sort removal + collection exclusion); no code change required.

### 00 · OMEGA Production Observation Audit · 3 deliverables (2026-02-27 · prod-time 2026-06-01T01:14Z)

| File | Purpose | Status |
|---|---|---|
| `PRODUCTION_OBSERVATION_REPORT.md` | Top-level verdict 🟡 AMBER · top-10 issues · recommended-action plan (P1–P3) for future authorized batches | 🟢 |
| `PRODUCTION_DATA_HYGIENE_REPORT.md` | Per-collection contamination scan (412/414 clean) · categorization: Safe-to-delete=0 · Operator-review=1 (deactivated `fieldleader@mascigc.com`) · System=1 (false positive `safety@mascigc.com`) | 🟢 |
| `PRODUCTION_REGRESSION_AUDIT.md` | Sprint 1C/1D verification on production · 🟢 GREEN · 4/4 contract probes · HR Hub clean desktop+mobile · 0 console errors · 5/5 sibling DELETE routes consistent · no preview-banner leak | 🟢 |
| `prod_observation_evidence/` | 10 curl probe logs + 2 production HR Hub viewport screenshots (`hr_hub_prod_desktop_1920.png` · `hr_hub_prod_mobile_420.png`) | 🟢 |

🟡 **Headline**: Production is healthy and Sprint 1C/1D is live with zero regressions. Verdict is AMBER (not GREEN) because of **one Pillar 1A-3 ownership-projection defect** (job 24-06 has PM=David Jewett in `/api/jobs` but Command Center labels owner "Unassigned PM") and the **recovery pill is AMBER** (no DR drill recorded · R2 bucket usage 91.49 GB above ALERT threshold 50 GB · 2 transient `usage_events` backup failures from 2026-05-25 that have since recovered). Command Center pill RED is **operational** (4 daily-report-missing jobs + 3 incidents >7d without CAPA), not a technical defect. Production data hygiene is clean — 0 test-marker records across 6 incidents · 23 meetings · 86 daily reports · 245 employees · 8 PMs · all other user collections.

### 00 · OMEGA Sprint 1C/1D · Pre-Deployment Certification Gate · 3 deliverables (2026-02-27)

| File | Purpose | Status |
|---|---|---|
| `SPRINT1C1D_PRE_DEPLOY_CERTIFICATION.md` | 6-phase certification evidence (build integrity · test cert · incident-delete behaviour · UI hygiene rendering · platform health · risk classification) | 🟢 |
| `SPRINT1C1D_DEPLOYMENT_RISK_REPORT.md` | Risk × mitigation matrix + rollback procedure (`git revert` per file · < 3 min wall-clock) | 🟢 |
| `SPRINT1C1D_GO_NO_GO_DECISION.md` | Operator-facing sign-off bundle · 🟢 GO TO DEPLOY · post-deploy verification recipe | 🟢 |
| `sprint1c1d_cert_evidence/` | Pytest logs · curl probe logs · 3 HR Hub viewport screenshots (1920/900/420) | 🟢 |

🟢 **Headline**: Sprint 1C/1D passes pre-deployment gate with **186/186 tests** (7 Sprint-1C + 108 Accountability Pillar 1 + 71 Command Center+Incident bundle), **9/9 incident-delete behavioural checkpoints** (super-admin · UUID · doc_id · 409 CAPA block · 409 detail formatting · audit row · unknown-id 404 · safety-token 401 · no-token 401), **16/16 preview platform probes + 2/2 production health probes**, and **LOW × 4 risk classification** (incident workflow · UI · platform stability · rollback). End-to-end rollback wall-clock < 3 min (single `git revert` per file · no DB migration · no env var · no schema change). Production database **never connected** during the gate. Awaiting operator's explicit production-deploy authorization.

### 00 · OMEGA Critical Fix Sprint 1C/1D · Incident Delete + UI Hygiene · 4 deliverables (2026-02-27)

| File | Purpose | Status |
|---|---|---|
| `SPRINT1D_UI_HYGIENE_PATCH_REPORT.md` | Stage 1 · HR Sign Out button palette consistency + incident-delete error code surfacing in two frontend handlers | 🟢 |
| `SPRINT1C_INCIDENT_DELETE_PATCH_REPORT.md` | Stage 2 · Backend `DELETE /api/incidents/{id}` remediation: id-vs-doc_id resolution, CAPA-linked 409 block, audit_events row on success; require_admin gate preserved | 🟢 |
| `CRITICAL_FIX_SPRINT1C1D_CERTIFICATION.md` | Stage 3 · 7/7 pytest pass, 16/16 regression probes 🟢, 6/6 role-permission probes 🟢, lint clean, 0 prod writes | 🟢 |
| `SPRINT1C1D_PRODUCTION_DEPLOY_READINESS_REPORT.md` | Deploy gate · 🟢 GO TO DEPLOY · rollback plan · post-deploy verification recipe | 🟢 |

🟢 **Headline**: `DELETE /api/incidents/{id}` is now safe, observable, and integrity-preserving. The route accepts UUID or doc_id, returns HTTP 409 with structured detail when corrective_actions still cite the incident, and writes an `audit_events.kind=incident_deleted` audit row on success. Frontend toasts now expose the real backend HTTP code (401/404/409/5xx) and the 409 detail message instead of the legacy "Delete failed" swallow. HR Hub Sign Out button styled consistent with the adjacent Change Password button on the dark header. **7-case pytest suite at `tests/test_sprint1c_incident_delete.py` covers super-admin UUID + doc_id paths, Safety-token rejection, no-token rejection, unknown-id 404, CAPA-block 409, and audit-row verification — 7/7 PASS.** Sibling delete routes (inspections/meetings/jhas/daily-reports) unchanged. Accountability projection / Command Center / backups untouched. Zero production DB writes. Deploy is 4 reverts-per-file away from rollback at any time.

### 00 · OMEGA Critical Fix Sprint 1A · Forensic Sweep · 4 deliverables (2026-05-31)

| File | Purpose | Status |
|---|---|---|
| `FINAL_CONTAMINATION_SWEEP_REPORT.md` | Phase 1 · 141 collections × 17 terms × 35 fields scanned · 8 collections flagged · 4 TRUE contamination categories · 4 FALSE-POSITIVE categories filtered | 🟡 ⛔ |
| `PRODUCTION_HYGIENE_INVENTORY.md` | Full inventory · 2 duplicate doc_ids found (incidents · daily_reports) · 0 orphans · 0 referential gaps · 4 abandoned/test categories | 🟡 ⛔ |
| `REMEDIATION_CANDIDATE_LIST.md` | Per-record cleanup table · ~104 records across 10 collections · severity-classified | 🟡 ⛔ |
| `PRODUCTION_CLEANUP_EXECUTION_PLAN.md` | Phase 2 · P0/P1/P2/P3 categorized · DB sweep + ops actions + docs · rollback + verification gates per item · ~2-2.5 hr total effort | 🟡 ⛔ |

🟡 **Headline**: Exhaustive forensic sweep of all 141 production collections complete. **Total true contamination findings: 72 docs** (1 test FL user · 1 test incident with "John Smith" canary · 2 PREVIEW_POSTENV notifications · 68 test-FL session telemetry rows). **Total duplicate findings: 2** (`incidents.doc_id='INC-2026-00001'` × 2 · `daily_reports.doc_id='DR-2026-00007'` × 2). **Total orphan findings: 0** (referential integrity intact). **Total test/demo findings: ~13 docs in 4 categories** (1 FL user · 1 incident · 10 payroll batches · presumed 7 linked decisions). **Recommended cleanup**: DB-only sweep (~60 min) executing 4 P0 items + 3 P1 items touching ~44 records across 7 collections; rollback via 2026-05-31 16:02Z archive. **Production risk rating: 🟢 LOW** — no orphans · no broken workflows · cleanup is delete-or-update only on contamination/test data with backup-restore rollback paths. **Sprint 1 P0-B correction**: the prior Sprint 1 plan recommended promoting `d9626eeb` to keep `INC-2026-00001`; Sprint 1A discovered `d9626eeb` is TEST data (`reported_by="John Smith"`) — corrected action is to DELETE `d9626eeb` and let `566a38dd` retain `INC-2026-00001`. **OMEGA discipline preserved**: zero code · zero DB writes · zero deploys · zero features · awaiting operator authorization before any execution.

### 00 · OMEGA Critical Fix Sprint 1 · Forensic batch (2026-05-31)

| File | Purpose | Status |
|---|---|---|
| `CRITICAL_FIX_SPRINT1_MASTER_REPORT.md` | Master · 15 ranked actions (3 🔴 P0 · 5 🟡 P1 · 5 🟡 P2 · 2 🟢 P3) · execution order | 🟡 ⛔ |
| `TEST_ACCOUNT_AUDIT.md` | P0-1 · 48 prod users inventoried · 1 🔴 test FL user · 8 🟡 hygiene items | 🟡 ⛔ |
| `TEST_ACCOUNT_REMEDIATION_PLAN.md` | P0-1 · 5 remediation actions (3 options for FL test user · 5 audits) | 🟡 ⛔ |
| `INCIDENT_INTEGRITY_REPORT.md` | P0-2 · 7 incidents · 1 🔴 dup doc_id · 3 ID schemas · 7 🟡 null status · 0 orphans | 🟡 ⛔ |
| `INCIDENT_DELETE_ROOT_CAUSE.md` | P0-3 · DELETE route works · permission-gated · no cascade · no audit · frontend swallows error codes · live repro matrix | 🟡 ⛔ |
| `INCIDENT_DELETE_REMEDIATION_PLAN.md` | P0-3 · 8 actions (dedupe · soft-delete · cascade · permission · index · backfill · counter audit) | 🟡 ⛔ |
| `PAYROLL_VARIANCE_FORENSIC_REPORT.md` | P0-4 · 10 abandoned test batches by `hrmanager@mascigc.com` 2026-05-12/13 · "John Smith" canary confirmed | 🔴 ⛔ |
| `UI_HYGIENE_REMEDIATION_REPORT.md` | P0-5 · 12 HrHub header controls all wired · no empty button found by code scan · viewport repro needed | 🟡 ⛔ |

🟡 **Headline**: 5 P0 forensic dives complete. **3 🔴 P0 items remediable in ~2 hr of DB-only work** (deactivate FL test user · dedupe `doc_id='INC-2026-00001'` · delete 10 abandoned payroll-variance test batches). **5 🟡 P1 items** (soft-delete migration · frontend error surfacing · password audit · `user_directory.is_active` backfill · doc update) total 3-5 dev-days. Combined Sprint 1 effort: **3-5 dev-days + operator-coordination**. P0-3 incident-delete: route is NOT broken; it's permission-gated (Safety token returns 401) · identifier-strict on `id` (UUID) · lacks cascade to 6 surfaces (notifications · tasks · audit_events · admin_audit · corrective_actions · R2 photos) · frontend swallows HTTP codes. P0-4 payroll batches: confirmed test data with "John Smith" canary; prior phase-3 audit's "null status/uploaded_by/variances_count" was a schema misread — actual fields are `source`/`created_by`/`flagged_rows+matched_rows+total_rows`; the contamination finding STANDS. P0-5: no defect detected by exhaustive HrHub code inspection (12 header controls · all valid onClick + testid + icon + responsive label); operator viewport screenshot needed to reproduce. **OMEGA discipline preserved**: zero code · zero DB writes · zero deploys · zero features. Awaiting operator authorization to execute remediations.

### 00 · OMEGA Forensic Platform Certification · 9 deliverables (2026-05-31)

| File | Purpose | Status |
|---|---|---|
| `EXECUTIVE_SUMMARY.md` | One-page snapshot · 5 scores · top-5 findings · 9-deliverable index | 🟡 ⛔ |
| `EXECUTIVE_PLATFORM_CERTIFICATION.md` | Defect register · 25 🔴 + 25 🟡 + 25 🟢 = 75 evidence-backed findings | 🟡 ⛔ |
| `PLATFORM_MASTER_INVENTORY.md` | Phase 1 · 8 portals · 251 routes · 546 endpoints · 141 collections · 31 templates · 7 background jobs | 🟢 ⛔ |
| `UI_HYGIENE_AUDIT.md` | Phase 2 · sampled · operator-flagged items (HR header button · incident delete) investigated with structural evidence | 🟡 ⛔ |
| `PRODUCTION_DATA_HYGIENE_AUDIT.md` | Phase 3 · 6 contamination items · 44 docs across 5 collections · score 88/100 · 2 🔴 (test FL user · dup incident doc_id) | 🟡 ⛔ |
| `WORKFLOW_CERTIFICATION.md` | Phase 4 · 10 workflows × 6 verbs · 1 🔴 (incident delete) · all else 🟢/🟡 | 🟡 ⛔ |
| `ROLE_PERMISSION_MATRIX.md` | Phase 5 · 9 roles · 31 templates · no permission leaks · 1 🔴 (test FL user · same as 3-D-2) | 🟡 ⛔ |
| `WHITE_LABEL_BLOCKERS.md` | Phase 6 · 413 files · ~4,431 MASCI literals · 15-batch WL-0..WL-15 backlog · ~30-40 dev-days | 🔴 ⛔ |
| `FORGEDOPS_OPERATIONS_READINESS.md` | Phase 7 · 92-108 dev-day build needed · 7 capability areas · no support portal · no tickets · no tenancy | 🔴 ⛔ |

🟡 **Headline**: Read-only forensic audit complete. **Production health: 🟢 88/100** (Pillar 1 + Pillar 2 Phase A both live and healthy · scheduler ticking · auth + API spotless). **Production data cleanliness: 🟡 88/100** — six contamination items totaling 44 docs across 5 collections, with two 🔴 (test FL user `fieldleader@mascigc.com` live with documented password; duplicate `doc_id='INC-2026-00001'` on 2 incident rows). **White-label readiness: 🔴 15/100** (4,431 MASCI literals across 413 files · WL-0..WL-15 backlog ~30-40 dev-days). **Customer #2 readiness: 🔴 20/100** (architecturally supportable but no tenant_id propagation today). **ForgedOps support readiness: 🔴 5/100** (no support portal · no tickets · no tenancy · ~92-108 dev-day build needed). Master defect register: 25 🔴 + 25 🟡 + 25 🟢 = 75 evidence-backed findings, each with location · reproduction · evidence · root cause where proven · recommended remediation. **OMEGA discipline preserved**: zero code · zero DB writes · zero fixes · zero deployments. Awaiting operator authorization for any subsequent fix batch.

### 00 · Pillar 1 · Phase 1A-7 · PRODUCTION CERTIFIED 🟢 (2026-05-31)

| File | Purpose | Status |
|---|---|---|
| `PILLAR1_PRODUCTION_DEPLOY_REPORT.md` | Deploy mechanism · pre-deploy gates 7/7 GREEN · source_hash transition `54b8a402→2383567f` · operator-driven · files reaching prod · rollback posture | 🟢 ⛔ |
| `PILLAR1_PRODUCTION_CERTIFICATION.md` | All 12 cert requirements GREEN · 23-field projection verified live · escalation_level=0 invariant holds · scheduler healthy · auth/API spot-checks all green | 🟢 ⛔ |
| `PILLAR1_POST_DEPLOY_VERIFICATION.md` | Operational-safety verification matrix · backup-freeze respected · 25-record owner sample (0 mismatches) · pre-existing AMBER signals NOT regressions · final verdict | 🟢 ⛔ |

🟢 **Headline**: Pillar 1 (Accountability Engine — Phases 1A-2 · 1A-3 · 1A-4 · 1A-5) is **LIVE in production** at `https://mascidocs.com` (source_hash `2383567f4f9735cf936d90dce26bb267` · `started_at=2026-05-31T17:03:15Z`). **Authoritative deploy signal**: `/api/admin/accountability/sources` returns 200 with 6 sources (was 404 pre-deploy). All 12 post-deploy gates GREEN — `escalation_level=0` invariant holds across 9 sampled production projections · scheduler `alive=true · armed_at=17:06:47Z · ticking 50ms ago` · hourly cadence intact (last complete-r2 16:02Z · 335 MB · 24,002 records) · 7 portal `/me` endpoints all 200 · no API regressions. Pre-existing AMBER signals (R2 bucket usage · no recent drill · RPO 4.8-min slip) are unchanged from pre-deploy state. Deploy was operator-driven (Emergent Deploy button) per OMEGA Deploy Hold Directive; agent did not initiate. **Backup architecture frozen-inventory untouched.** Final verdict: 🟢 PRODUCTION CERTIFIED.

### 00 · Pillar 1 · Pre-Deployment Operational Certification 🟡 GO WITH KNOWN LIMITATIONS (2026-05-31)

| File | Purpose | Status |
|---|---|---|
| `PILLAR1_OPERATIONAL_CERTIFICATION_REPORT.md` | Master · Phase 1 (DQ) · Phase 2 (25-record ownership sample · 0 mismatches) · Phase 6 (Customer #2) · OMEGA scorecard | 🟡 ⛔ |
| `PILLAR1_DEPLOYMENT_RECOMMENDATION.md` | 🟡 verdict · 3 deployment paths · Path A recommended · pre-deploy checklist · rollback plan | 🟡 ⛔ |
| `PILLAR1_EXECUTIVE_USABILITY_REPORT.md` | Phase 3 · 6-AM walkthrough · 3 USEFUL / 3 MARGINAL / 0 NOISE cards | 🟡 ⛔ |
| `PILLAR1_SUPPORTABILITY_AUDIT.md` | Phase 4 · 5 ForgedOps support questions · 3 GREEN / 1 PARTIAL / 1 RED · runbook | 🟡 ⛔ |
| `PILLAR1_WHITE_LABEL_READINESS_REPORT.md` | Phase 5 · Pillar 1 modules white-label clean · platform 4,431 MASCI refs · 10-batch white-label backlog (WL-0..WL-10 · ~20-25 dev-days) | 🟡 ⛔ |
| `pillar1_certification_evidence/` (folder) | Live snapshot JSON · 25-record ownership probe · DQ aggregations | ✅ |

🟡 **Headline**: Pillar 1 itself is **🟢 CERTIFIED standalone** (128/128 pytests · 0 mismatches on 25-record owner sample · Pillar 1 modules carry 0 MASCI strings · architecture supports Customer #2 with ~3-4 dev-days of config work). The 🟡 verdict reflects **inherited Pillar 2 Phase A defects (D1, D2, D5) + JOBS-ISSUE-NO-OWNER predicate-vs-implementation mismatch + 6% TEST_iter preview pollution + supportability gap on "what changed" (Pillar 1B territory)** — none of which are addressable inside Pillar 1. **Path A recommended**: deploy Pillar 1 as-is, defer Pillar 2 D1/D2/D5 to its own authorized batch.

### 00 · Pillar 1 · Phase 1A-5 · Accountability Owner Fidelity CERTIFIED (2026-05-31)

| File | Purpose | Status |
|---|---|---|
| `ACCOUNTABILITY_OWNER_RESOLUTION_AUDIT.md` | Pre-implementation audit · placeholder inventory · authoritative routing source candidates per source · resolvable-vs-preserve decision · live preview baseline (0/10 PO link · 0/10 incident link) | 🟢 ⛔ |
| `ACCOUNTABILITY_OWNER_FIDELITY_REPORT.md` | Implementation report · 2 new async resolvers (`project_po_request_resolved` · `project_incident_resolved`) · 5-call-site Command Center wiring · resolved + fallback owner inventory · pytest evidence per resolver branch | 🟢 ⛔ |
| `PHASE_1A5_CERTIFICATION.md` | 10/10 cert requirements GREEN · 20 new + 128 combined pytests · canonical shape · 1B reservation · immutability · DB-fail fallback · frontend untouched · OMEGA scorecard | 🟢 ⛔ |

🟢 **Headline**: Two read-only async resolver helpers added to `lib/accountability_projection.py` (+119 LOC) and consumed by the Command Center on 4 rule paths + 2 drilldown call sites. POs with a `project_number` joined to `jobs_master.primary_pm_name` now surface as the named PM (`owner_role="pm"`). Incidents with a linked CA (preferring OPEN over closed, matching via `source_id` ∥ `incident_id`) now surface the CA's `assigned_to_name` (`owner_role="safety"` preserved). On preview today no owner string changes — the Audit empirically established 0/10 pending POs link to a project with a PM and 0/10 open incidents have a linked CA with an assignee, so the placeholders ARE the truth. The mechanism activates automatically as operator data accrues. **23-field canonical shape · escalation_level=0 · source-row immutability · DB-fail-fallback all verified by pytest. Source workflows, frontend (`AdminCommandCenter.jsx` md5 stable at `4cb825b4…`), service router, server.py, backup architecture untouched.**

### 00 · Pillar 1 · Phase 1A-4 · Executive Command Center CONSUMES Accountability (2026-05-31)

| File | Purpose | Status |
|---|---|---|
| `ACCOUNTABILITY_EXECUTIVE_INTEGRATION_REPORT.md` | What changed · 6 surgical edits in `command_center.py` · drilldown enrichment · backward-compat guarantee · live evidence | 🟢 ⛔ |
| `COMMAND_CENTER_ACCOUNTABILITY_CONSUMPTION_REPORT.md` | Per-card consumption map · dispatch logic · cache behavior · perf impact · frontend untouched | 🟢 ⛔ |
| `PHASE_1A4_CERTIFICATION.md` | 5/5 cert requirements GREEN · 16 new + 108 combined pytests · approver-not-requester verified live | 🟢 ⛔ |

🟢 **Headline**: 5/9 hardcoded Command Center owner strings replaced with Accountability projections. Approvals card stops misattributing the requester as owner (`owner='Pending Approver'` live on all 5 APP-AMBER items today). Drilldown endpoint enriched with additive `accountability` (23 canonical fields) + `timeline` (last 25 events) — legacy keys preserved byte-stable. **Frontend `AdminCommandCenter.jsx` untouched · md5 unchanged · zero visual change.** Pulse aggregate reconciliation intact · D1/D2/D5 Path B patches green · 108/108 pytests across Pillar suites pass · backup/recovery/scheduler unaffected. **Pillar 1B `escalation_level=0` reservation enforced across every surface.**

### 00 · Pillar 1 · Phase 1A-3 · Accountability Service CERTIFIED (2026-05-31)

| File | Purpose | Status |
|---|---|---|
| `ACCOUNTABILITY_INTEGRATION_REPORT.md` | What was built · 3 admin-strict endpoints · factory pattern · live preview probe | 🟢 ⛔ |
| `ACCOUNTABILITY_SERVICE_CERTIFICATION.md` | 7/7 cert requirements GREEN · 21 service pytests + 92 combined regression-free · per-source live-data evidence | 🟢 ⛔ |
| `ACCOUNTABILITY_PERFORMANCE_REPORT.md` | Cold ~1.5s @ per_source=100 (90% incidents async) · warm ~0.05s · ~7× cache speedup · scalability projection · NO tuning changes in this batch | 🟢 ⛔ |

🟢 **Headline**: Read-only Accountability service is live in preview. Three admin-strict endpoints (`/sources`, `/item`, `/snapshot`) expose the certified projection layer across all 6 sources (tasks · CA · PO · fleet_defects · incidents · virtual signals). 277 live projections at per_source=100. New module `/app/backend/routes/accountability_service.py` (215 LOC · md5 `0e879cf9…`) + 8-line `server.py` mount. Zero source workflow modified · zero new collection · zero Command Center integration · zero UI · zero deploy. Pillar 1B reservation invariant enforced on every live item (escalation_level=0 across 277 projections).

### 00 · Pillar 1 · Phase 1A-2 · Projection Layer CERTIFIED (2026-05-31)

| File | Purpose | Status |
|---|---|---|
| `ACCOUNTABILITY_PROJECTION_REPORT.md` | What was built · projection architecture · file locations · mapping logic · owner resolution logic | 🟢 ⛔ |
| `ACCOUNTABILITY_CANONICAL_MAPPING_REPORT.md` | Native→canonical evidence per source · status / owner / due-date / timeline mapping with pytest refs | 🟢 ⛔ |
| `ACCOUNTABILITY_PHASE_1A2_CERTIFICATION.md` | 7/7 cert requirements GREEN · 51/51 new pytests · 71/71 combined regression-free · OMEGA discipline scorecard | 🟢 ⛔ |

🟢 **Headline**: `/app/backend/lib/accountability_projection.py` (936 LOC · md5 `e8de1112…`) is the read-only pure-function contract that projects all 6 authorized sources (tasks · CA · PO · fleet_defects · incidents · virtual signals) into one 24-field canonical accountability shape. 51 pytests cover per-source status/owner/due-date/timeline + cross-source uniformity + source-row immutability + Pillar 1B reservation invariants. Zero source workflow modified · zero new collection · zero endpoint · zero UI · zero deploy. Library is **not yet imported by any route** — passive contract awaiting Phase 1A-3 authorization.

### 00 · Pillar 1 · Accountability Engine · SPECIFICATION (2026-05-31)

| File | Purpose | Status |
|---|---|---|
| `ACCOUNTABILITY_ENGINE_AUDIT.md` | Workflow-by-workflow inventory of ownership today · 9-row ambiguity register · 5 hardcoded Command Center owner strings | 🟢 ⛔ |
| `ACCOUNTABILITY_ENGINE_ARCHITECTURE.md` | Universal 9-question contract · canonical status set · single new collection proposal (`db.accountability_timeline`) gated behind operator authorization | 🟢 ⛔ |
| `ACCOUNTABILITY_LIFECYCLE_SPEC.md` | 6-state canonical machine + `overdue` overlay · allowed transitions · per-source native→canonical mapping · re-assignment & closure rules | 🟢 ⛔ |
| `ACCOUNTABILITY_TIMELINE_SPEC.md` | Append-only event shape · 10 event_kinds · idempotency rules · indexes · size estimate (~0.5 MB/day · ~180 MB/year) | 🟢 ⛔ |
| `EXECUTIVE_ACCOUNTABILITY_INTEGRATION.md` | Per-card plan to replace 5/9 hardcoded Command Center owner strings · additive drilldown payload · Accountability Dashboard surface (design only) | 🟢 ⛔ |
| `ACCOUNTABILITY_ENGINE_ROADMAP.md` | 7-phase ladder (1A-1..1A-7) · acceptance criteria · risk register · STOP condition · awaits `AUTHORIZE PHASE 1A-2` | 🟢 ⛔ |

🟢 **Headline**: Pillar 1 design batch complete. Engine reuses `tasks_notifications.py` as the foundation (already canonical-shaped: assignee_role/user_id/employee_id · status · priority · due_at · audit[]). Closes the executive-visibility-to-accountability gap: 5/9 Command Center owner strings will move from hardcoded literals (`"Safety"`, `"Shop"`, requester-misattributed approvers) to projection-derived values. Single new collection proposed (`db.accountability_timeline`); zero migration of existing audit/status_history arrays; zero new notifications/emails/SMS/cron; Pillar 1B escalation explicitly deferred. STOPPED awaiting operator `AUTHORIZE PHASE 1A-2`.

### 00 · Pillar 2 · Phase A · Path B PRODUCTION CERTIFIED (2026-05-31)

| File | Purpose | Status |
|---|---|---|
| `COMMAND_CENTER_PATH_B_PATCH_REPORT.md` | Code-level summary of D1/D2/D5 patches · file/line evidence · pytest 20/20 · OMEGA discipline check | 🟢 ⛔ |
| `COMMAND_CENTER_RECERTIFICATION_REPORT.md` | 12-gate re-certification on live preview · pulse aggregate reconciliation · D1/D2/D5 evidence inline | 🟢 ⛔ |
| `COMMAND_CENTER_DEPLOY_READINESS_REPORT.md` | 🟢 GO TO DEPLOY recommendation · 12/12 pre-deploy gates · risk register | 🟢 ⛔ |
| `COMMAND_CENTER_PRODUCTION_CERTIFICATION.md` | Post-deploy production certification · 9/9 verifications GREEN · prod source_hash=`54b8a402…` · pulse reconciles · backup/recovery/scheduler unchanged | 🟢 ⛔ |

🟢 **Headline**: Path B is LIVE in production (`https://mascidocs.com` · source_hash `54b8a402de538a17579cabc2e6aaac38`). D1/D2/D5 active; pulse reconciles exactly; backup scheduler, recovery dashboard, every existing portal endpoint unchanged. Production certification complete.

| File | Purpose | Status |
|---|---|---|
| `COMMAND_CENTER_PATH_B_PATCH_REPORT.md` | Code-level summary of D1/D2/D5 patches · file/line evidence · pytest 20/20 · OMEGA discipline check | 🟢 ⛔ |
| `COMMAND_CENTER_RECERTIFICATION_REPORT.md` | 12-gate re-certification on live preview · pulse aggregate reconciliation · D1/D2/D5 evidence inline | 🟢 ⛔ |
| `COMMAND_CENTER_DEPLOY_READINESS_REPORT.md` | 🟢 **GO TO DEPLOY** recommendation · 12/12 pre-deploy gates · risk register · operator-authorization required | 🟢 ⛔ |

🟢 **Headline**: D1 + D2 + D5 patched in `routes/command_center.py` (helpers + 4 query call-sites). Pytest expanded 14 → 20 · all green. Live preview snapshot now reconciles · Approvals card surfaces previously-invisible 139 aged POs (D5 evidence). Discipline preserved · zero frontend / collection / threshold / fan-out drift. Operator authorization required for production deploy.

### 00 · Pillar 2 · Phase A · Pre-Production CERTIFICATION (2026-05-31)

| File | Purpose | Status |
|---|---|---|
| `EXECUTIVE_COMMAND_CENTER_CERTIFICATION.md` | 9 certification gates · 7 PASS · 1 DEFECT (D5 noise/coherence) · 1 KNOWN (FP/FN inventory) · 7-defect inventory | 🟡 ⛔ |
| `EXECUTIVE_COMMAND_CENTER_DEPLOYMENT_RECOMMENDATION.md` | 🟡 **CONDITIONAL GO** · Path A (as-is) / Path B (~45 LOC patch · RECOMMENDED) / Path C (~100 LOC comprehensive) · post-patch readiness checklist | 🟡 ⛔ |
| `EXECUTIVE_COMMAND_CENTER_FALSE_POSITIVE_REVIEW.md` | 5 FP classes · per-rule mechanism · estimated 22% FP rate as-is → ~8% after Path B | 🟡 ⛔ |
| `EXECUTIVE_COMMAND_CENTER_FALSE_NEGATIVE_REVIEW.md` | 9 FN classes · FN-1 (D5) is MOST OPERATIONALLY DANGEROUS · zeros after Path B | 🟡 ⛔ |

🟡 **Headline**: Phase A is fit for purpose with documented limitations. **7 defects identified · 3 medium (D1/D2/D5) · 4 low/cosmetic (D3/D4/D6/D7).** Path B (D1+D2+D5 fix · ~45 LOC · zero scope drift) is the recommended pre-production patch. Without it: aged Safety incidents stay RED forever (trust erosion); Approvals card silently under-reports (operational miss). OMEGA discipline preserved throughout — zero code changes during certification. **Status: Path B PATCHED on preview 2026-05-31 (see Path B closeout block above).**



### 00 · Pillar 2 · Phase A · Executive Command Center SHIPPED (2026-05-31)

| File | Purpose | Status |
|---|---|---|
| `PHASE_A_EXECUTIVE_SUMMARY.md` | One-page operator-facing closeout · live preview numbers · OMEGA scorecard | 🟢 ⛔ |
| `PHASE_A_IMPLEMENTATION_REPORT.md` | What was built · drift check · 15/15 acceptance criteria | 🟢 ⛔ |
| `PHASE_A_ENDPOINT_INVENTORY.md` | 6 admin-strict endpoints · auth gate verified · MongoDB collections touched | 🟢 ⛔ |
| `PHASE_A_UI_CERTIFICATION.md` | testid map · render evidence (live preview) · accessibility checks | 🟢 ⛔ |
| `PHASE_A_ACCEPTANCE_TEST_REPORT.md` | Timed 5-second acceptance test · pytest 14/14 · auth gate · drift verification | 🟢 ⛔ |
| `EXECUTIVE_SCORING_CERTIFICATION.md` | 15 rules · evidence-backed thresholds · 5-question contract per rule | 🟢 ⛔ |

🟢 **Headline**: Executive Operations Command Center is LIVE in preview. `/admin/command-center`. Single-glass · 30-second readable · 5 cards (Jobs/Safety/Equipment/Accountability/Approvals) · drilldown modal answers what/why/who/being-done/ETA. 14/14 tests PASS. Zero drift. Backup architecture FROZEN. Pillars 1/3/4 untouched. Awaiting operator review and Phase B authorization decision.

**New endpoints (admin-strict)**: `/api/admin/command-center/snapshot · /thresholds · /calendar · /drilldown/{card}/{id}`.
**New frontend route**: `/admin/command-center` (RequireAdmin).
**New collections**: `command_center_thresholds` (config doc · operator-tunable RAG rules) · `command_center_calendar` (config doc · working-day awareness).



### 00 · Pillar 2 · Executive Command Center DESIGN REVIEW (2026-05-31)

| File | Purpose | Status |
|---|---|---|
| `EXECUTIVE_COMMAND_CENTER_DESIGN_REVIEW.md` | Per-card 5-question critique · KEEP/MODIFY/REMOVE verdicts · 5 cards survive Phase A (Jobs · Safety · Equipment · Accountability · Approvals) · 5 cards removed/deferred (PM Load · Supervisor Load · Projects-at-Risk · Bottlenecks · Recommender) | 📐 ⛔ |
| `EXECUTIVE_COMMAND_CENTER_RISK_ANALYSIS.md` | 8 missing exec questions cataloged · 6 duplicates → 0 · 6 low-value → 0 · 5 noise generators → 0 · 8 unreliable sources → 2 mitigated · 7 FP → 1 · 7 FN → 3 closed | 📐 ⛔ |
| `EXECUTIVE_COMMAND_CENTER_OPERATOR_CHALLENGE.md` | 19 operator questions · 11 hard-blocking · cannot start Phase A without answers or default acceptance | 📐 ⛔ |
| `FINAL_PHASE_A_RECOMMENDATION.md` | Slim Phase A contract · ~1,150 LOC · 5 cards · 3 endpoints · 2 pages · 2 config collections · acceptance criteria · stop conditions · OMEGA backup-freeze preserved | 📐 ⛔ |

🟢 **Headline**: Self-critique pass complete. The original 10-card blueprint becomes a slim 5-card Phase A grounded in real data quality, with all duplicates / noise generators removed and 11 hard-blocking operator questions surfaced. Implementation NOT authorized — agent stopped after documentation per operator directive.



### 00 · Pillar 2 · Executive Command Center BLUEPRINT (2026-05-31)

| File | Purpose | Status |
|---|---|---|
| `EXECUTIVE_COMMAND_CENTER_AUDIT.md` | Inventory existing exec-relevant surfaces · identify 10-domain gap matrix · raw data exists, synthesis missing | 📐 ⛔ |
| `EXECUTIVE_COMMAND_CENTER_SPEC.md` | 5-sec Pulse Strip → 60-sec Priority Stack → 5-min 10-card grid · single-glass design answering 10 operator questions | 📐 ⛔ |
| `EXECUTIVE_HEATMAP_SPEC.md` | GREEN/AMBER/RED scoring methodology · 30+ tunable rules · adopts proven `/admin/recovery/snapshot` `warnings[]` pattern | 📐 ⛔ |
| `EXECUTIVE_DATA_SOURCE_MAP.md` | Per-widget source collection / workflow / owner · 0 net-new collections beyond `command_center_thresholds` config doc | 📐 ⛔ |
| `EXECUTIVE_IMPLEMENTATION_ROADMAP.md` | Phase A (7 cards) → Phase B (Recommender · Projects) → Phase C (per-role lenses) · acceptance criteria · stop conditions · 8 deferred operator questions | 📐 ⛔ |

🟢 **Headline**: Spec-only batch complete. Blueprint demonstrates that the Executive Command Center is a synthesis-and-scoring layer over existing data — **no new workflows, no schema changes, ~1500 LOC for Phase A including tests**. Pattern is the production-proven `recovery/snapshot` RAG-with-warnings shape extended to 10 operational domains. **Implementation NOT authorized** — agent stopped after documentation per operator directive.



### 00 · Backup & Recoverability Epic CLOSEOUT + Pillar Pivot (2026-05-31)

| File | Purpose | Status |
|---|---|---|
| `BACKUP_RECOVERABILITY_EPIC_CLOSEOUT.md` | 🟢 **EPIC CLOSED · ARCHITECTURE FROZEN** · first hourly archive `MASCI_complete_backup_2026-05-31_024901Z.zip · 335 MB · 23,938 records` landed at 02:51:56Z · RPO 1.4 min GREEN · frozen-inventory list · forward focus pivots to 4 pillars | ✅ ⛔ |
| `POST_DEPLOY_HOURLY_ACTIVATION_VERIFICATION.md` | Hourly activation confirmed loaded after 02:40:59Z redeploy · `hourly_cadence_enabled=true` · scheduler alive · two prior warnings removed | ✅ ⛔ |
| `OMEGA_PRE_DEPLOYMENT_CERTIFICATION_REPORT.md` | Pre-deploy gate · 12/12 PASS · code-no-op redeploy (source_hash unchanged) | ✅ ⛔ |
| `HOURLY_BACKUP_ACTIVATION_REPORT.md` | PARTIAL → CLOSED · prior P0 (`BACKUP_R2_HOURLY` not loaded) is fully resolved | ✅ ⛔ |

🟢 **Headline**: Backup & Recoverability is DONE. Architecture FROZEN (defect-only). Forward focus on 4 pillars: Accountability Engine · Executive Visibility · Field Experience · Escalation Framework. Every new enhancement must declare business outcome · owner · notification path · escalation path · executive visibility path BEFORE implementation. No drift. No sprawl. No speculative features. Awaiting operator pillar authorization.



### 00 · OMEGA Pre-Deployment Certification Gate (2026-05-31)

| File | Purpose | Status |
|---|---|---|
| `OMEGA_PRE_DEPLOYMENT_CERTIFICATION_REPORT.md` | 🟢 **GO TO DEPLOY (Low Risk · Code-No-Op)** · 12/12 gates · preview & prod source_hash identical (`533c269640ae7153de97ac56a998089a`) · sole material effect of redeploy is env-var re-roll (load `BACKUP_R2_HOURLY=true` into running prod worker per prior `HOURLY_BACKUP_ACTIVATION_REPORT.md` §3.3) | ✅ ⛔ |
| `HOURLY_BACKUP_ACTIVATION_REPORT.md` | PARTIAL · scheduler alive, deployment healthy, but `BACKUP_R2_HOURLY=true` NOT loaded in running prod process (3 independent signals confirm) | ✅ ⛔ |

🟢 **Headline**: Code is byte-identical between preview and prod. All iter441/iter442/drill/dashboard primitives present. Operator pre-deploy checklist (verify prod env panel values for `BACKUP_R2_HOURLY`, `SCHEDULER_ENABLED`, `BACKUP_LITE_MODE_ONLY`, `AUTO_EMAIL_REPORTS`, `RATE_LIMITING`) documented in §9 of the certification report. Rollback is trivial (identical hash + env-var flip).



### 00 · Batch K + L · Notification Fan-out Wiring + Fleet DVIR Closure (2026-05-30)

| File | Purpose | Status |
|---|---|---|
| `BATCH_K_CERTIFICATION.md` | Batch K · 5 documented visibility gaps closed · 7 fan-out paths verified | 🟢 PASS ⛔ |
| `BATCH_K_FINAL_CERTIFICATION.md` | Batch K audit · 10 questions × 7 workflows · all evidence-backed | 🟢 PASS ⛔ |
| `SOFT_ORPHAN_CERTIFICATION.md` | Zero hard orphans · 1 soft visibility gap remaining (OMEGA-9 · Batch M) | 🟢 PASS ⛔ |
| `FLEET_DVIR_CERTIFICATION.md` | OMEGA-3 closed · 3 routing classes verified · NO Superintendent · DB returned to baseline | 🟢 PASS ⛔ |
| `OMEGA_STATUS_REPORT.md` | Post Batch K+L · 5 required questions answered · pillar scorecard 4🟢+1🟡 | ⛔ |

🟢 **Headline**: 6 OMEGA items closed (OMEGA-3 + OMEGA-5/6/7/8 + OMEGA-13). The last 🔴 (Fleet DVIR orphan) is resolved. Ownership pillar promoted CONDITIONAL → UNCONDITIONAL. Remaining work is all P1/P2/P3 (no UNACCEPTABLE items).


## 0 · 2026-05-30 fork — Latest pass index

### 00 · OMEGA · MASCI Operational Perfection Program (2026-05-30)

| File | Purpose | Status |
|---|---|---|
| `OMEGA_EXECUTIVE_SUMMARY.md` | 🟢 **OPERATIONALLY ELITE** · 5/5 pillars certified · 23 gaps registered · 3 P0 operator actions pending | ✅ ⛔ |
| `RECOVERABILITY_CERTIFICATION_v2.md` | Pillar 1 · 🟢 **PASS** · RTO < 30 min in all 4 disaster scenarios | ✅ ⛔ |
| `OWNERSHIP_CERTIFICATION.md` | Pillar 2 · 🟡 **CONDITIONAL PASS** · pending operator Fleet DVIR sign-off · NO Superintendent | ✅ ⛔ |
| `ACCOUNTABILITY_CERTIFICATION.md` | Pillar 3 · 🟢 **PASS WITH ASTERISKS** · 16 audit collections · zero silent completions | ✅ ⛔ |
| `PLATFORM_CERTIFICATION.md` | Pillar 4 · 🟢 **PASS** · 13 deltas logged · zero functional contradictions | ✅ ⛔ |
| `USER_EFFICIENCY_CERTIFICATION.md` | Pillar 5 · 🟡 **ACCEPTABLE** · 2 critical field-form items OUT of OMEGA scope | ✅ ⛔ |
| `OMEGA_GAP_REGISTER.md` | 23 gaps · severity-ranked · evidence-backed · 1 🔴 UNACCEPTABLE (Fleet DVIR orphan) | ✅ ⛔ |
| `OMEGA_IMPLEMENTATION_PLAN.md` | Sequenced: ITEM-0 → BATCH-K/L/M/N/O · ~21 h total · Phase 2 BATCH-P optional | ✅ ⛔ |

🟢 **Headline**: OPERATIONALLY ELITE. Platform survives loss of server / database / employee / PM / dispatcher / safety manager / internet · recovers within ~10–40 min · maintains accountability · preserves all records · routes every workflow to the correct owner. Single 🔴 = Fleet DVIR orphan (decision-ready). 3 operator-side P0 actions: photo migration, fresh prod deploy, DVIR sign-off.



### 00 · Batch J · Operational Reliability Closeout (2026-05-30)

| File | Purpose | Status |
|---|---|---|
| `BATCH_J_EXECUTIVE_SUMMARY.md` | 🟢 4/4 priorities resolved · prod scheduler PASS · prod alignment PARTIAL (photo migration outstanding) | ✅ ⛔ |
| `PRODUCTION_SCHEDULER_CERTIFICATION_REPORT.md` | 🟢 **PASS** · prod `scheduler.alive=true` · tick 43 sec ago · 3× complete-r2 in past 3 h · email path proven | ✅ ⛔ |
| `PRODUCTION_RECOVERABILITY_ALIGNMENT_REPORT.md` | 🟡 **PARTIAL** · scheduler+config+directory+restore aligned · photo migration NOT run on prod (DR-2026-00279 still inline base64) | ✅ ⛔ |
| `FLEET_DVIR_DECISION_PACKAGE.md` | 🟢 Decision-ready · 4 defect classes mapped (Normal/Defect/Safety/OOS/Repeat) · NO Superintendent · ~30 LOC implementation footprint when authorized | ✅ ⛔ |
| `NOTIFICATION_GAP_REMEDIATION_PLAN.md` | 🟢 Plan-ready · 8 gaps × (Current/Desired/Target/Effort) · suggested Batch K/L/M sequencing (~21 h total work) | ✅ ⛔ |
| `batch_j_evidence/` (folder) | `prod_probes_p0a.txt` · `prod_probes_p0b.txt` · `prod_probes_p0b2.txt` · `prod_probes_p0b3.txt` (17 live runtime probes) | ✅ |

🟢 **Headline**: Production scheduler CERTIFIED HEALTHY with live runtime evidence (`alive=true · last_tick=43sec · backups firing hourly · emails delivered`). Production recoverability PARTIALLY ALIGNED — photo migration is the only remaining 🔴. Fleet DVIR decision package and notification gap plan are ready for operator authorization on any future implementation batch.

### 0 · Batch I · Platform Operational Truth Map Finalization (2026-05-30)

| File | Purpose | Status |
|---|---|---|
| `BATCH_I_EXECUTIVE_SUMMARY.md` | 🟢 7/7 axes verified · 100% triangulated understanding · 6 deliverables · zero remediation | ✅ ⛔ |
| `PLATFORM_OPERATIONAL_TRUTH_MAP_v1.md` | Master map · 41 workflows · 25 notif events · 10 dashboard roles · 14 escalation triggers | ✅ ⛔ |
| `PLATFORM_TRUTH_DELTA_REPORT.md` | 13 Memory ↔ Code ↔ Runtime divergences logged | ✅ ⛔ |
| `PLATFORM_GAP_LEDGER_FINAL.md` | 19 deduplicated gaps · supersedes ORPHAN_AND_GAP_REGISTER + NOTIFICATION_GAP_REGISTER | ✅ ⛔ |
| `DISASTER_RECOVERY_VALIDATION_MATRIX.md` | 22 components × 4 DR pillars (backed up · restorable · tested · verified) | ✅ ⛔ |
| `PLATFORM_RECOVERABILITY_PROOF_REPORT.md` | Direct evidence for 4 "if X dies tomorrow" scenarios (all 🟢) | ✅ ⛔ |
| `batch_i_evidence/` (folder) | runtime_probes.txt · code_fanout_callsites.txt · db_collection_inventory.txt | ✅ |

🟢 **Headline**: Platform at 100% verified operational understanding. Fleet DVIR (ORPHAN-1) confirmed in code · backup scheduler verified dead in preview (preview-only — see Batch J for prod state). DR proven across all 4 scenarios.


### 00 · Batch H · Photo Architecture Hardening & Performance Certification (2026-05-30)

| File | Purpose | Status |
|---|---|---|
| `BATCH_H_EXECUTIVE_SUMMARY.md` | 🟢 PASS · 8/8 success criteria · Mongo fetch 5.1× faster · payload 99.8% smaller | ✅ ⛔ |
| `PHOTO_STORAGE_ARCHITECTURE_REPORT.md` | 3 storage modes mapped · write/read/cache/PDF paths · per-project distribution | ✅ ⛔ |
| `WRITE_PATH_PROTECTION_REPORT.md` | New `_sanitize_inline_photos()` in DR handler · live smoke-tested in preview | ✅ ⛔ |
| `PHOTO_PERFORMANCE_BENCHMARK_REPORT.md` | Mongo single-DR fetch: 140.8 ms → 27.7 ms · 11.33 MB → 25 KB | ✅ ⛔ |
| `PHOTO_RETRIEVAL_FLOW_MAP.md` | End-to-end retrieval flow + failure modes | ✅ ⛔ |
| `USER_EXPERIENCE_IMPACT_REPORT.md` | Zero UX regression · PM/Field/Safety workflow walkthroughs | ✅ ⛔ |
| `batch_h_evidence/` (folder) | `perf_benchmark_raw.txt` (live benchmark output) | ✅ |

🟢 **Headline**: 5.1× faster Mongo doc fetch · 99.8% payload reduction · zero UX regression · new DRs structurally immune to inline base64 bloat. Architecture answer to "18-month-old vs yesterday's project": photo retrieval is age-independent by design.

### 0a · Batch G · Full Recoverability Closeout (2026-05-30)

| File | Purpose | Status |
|---|---|---|
| `BATCH_G_EXECUTIVE_SUMMARY.md` | Operator-facing roll-up · 🟢 **FULLY RECOVERABLE** verdict · 4 GAPs closed | ✅ ⛔ |
| `PHOTO_BLOAT_REMEDIATION_REPORT.md` | GAP-1 · drill DB shrank 260.7 MB → 2.3 MB · `scripts/migrate_dr_photos.py` new artifact | ✅ ⛔ |
| `MULTI_LOGIN_RESEED_REPORT.md` | GAP-2 · all 7 directory users log in post-restore · server.py:7592 fix + restore_drill helper | ✅ ⛔ |
| `PHOTO_REHYDRATION_RECOVERY_REPORT.md` | GAP-4 · `--restore-photos` flag · idempotent R2 re-upload from archive | ✅ ⛔ |
| `FRONTEND_RESTORE_DRILL_REPORT.md` | GAP-6 · Playwright screenshot + compositional proof | ✅ ⛔ |
| `FULL_RECOVERABILITY_CLOSEOUT_REPORT.md` | Final cert · 12/12 axes 🟢 · supersedes Batch F cert | ✅ ⛔ |
| `batch_g_evidence/` (folder) | Drill backend boot log · Playwright screenshot + metadata · GAP-1 migration run output | ✅ |

🟢 **Headline: FULLY RECOVERABLE. RTO ~10 min (was 20-25). RTO with R2-loss ~20-40 min (was 2-8 hr). Archive size after operator migration: 442 MB → ~115 MB. OOM trajectory neutralized permanently.**

🔴 **Operator actions to realize in prod**: run `migrate_dr_photos.py` against prod · redeploy preview→prod (GAP-2 server.py) · optionally re-enable hourly cadence.

### 0a · Batch F · Platform Recoverability Completion (2026-05-30)

| File | Purpose | Status |
|---|---|---|
| `BATCH_F_EXECUTIVE_SUMMARY.md` | Operator-facing roll-up · verdict 🟢 **OPERATIONALLY RECOVERABLE** (upgrade from Batch E 🟡) | ✅ ⛔ |
| `APPLICATION_BOOT_DRILL_REPORT.md` | Phase 1 · drill backend on :8002 against restore DB · auth + 8 boot checks | ✅ ⛔ |
| `CRITICAL_WORKFLOW_RECOVERY_REPORT.md` | Phase 2 · 10 workflows · PDF rendering proven on DR/Incident/Meeting | ✅ ⛔ |
| `BACKUP_GROWTH_FORENSICS_REPORT.md` | Phase 3 · root cause is `daily_reports` (69% · 3.18 MB/DR) NOT telemetry · OOM in ~3 days at current rate | ✅ ⛔ |
| `COLLECTION_CLASSIFICATION_REPORT.md` | Phase 3 · 76 collections classified A–H · split/keep/exclude recommendations | ✅ ⛔ |
| `PLATFORM_RECOVERY_GAP_REPORT.md` | Phase 4 · 10-gap inventory with severity/effort/action | ✅ ⛔ |
| `PLATFORM_SAFEGUARD_AUDIT.md` | Phase 5 · 10-category safeguard audit + SPOF inventory | ✅ ⛔ |
| `FULL_RECOVERABILITY_CERTIFICATION.md` | Phase 5 · final cert (upgrade from Batch E) · per-axis breakdown · final RTO/RPO answers | ✅ ⛔ |
| `batch_f_evidence/` (folder) | Phase 1+2 probe JSON · growth forensics · R2 history · drill backend boot log | ✅ |

🔥 **Headline corrections from Batch E**:
- Backup-growth root cause is `daily_reports` inline base64 (NOT telemetry · validated by collStats)
- Multi-login is **universally broken** post-restore, not "portal logins survive" as Batch E said (validated by drill backend on 8002)
- Application boot + PDF rendering + 10 workflows now 🟢 PROVEN — converts ⚪ UNKNOWN from Batch E

🚨 **Operator IMMEDIATE action recommended**: `BACKUP_R2_HOURLY=false` + `BACKUP_R2_FULL_HOUR_UTC=4` (GAP-3 OOM trajectory · ~3 days).

### 0a · Batch E · Disaster Recovery Drill & Recoverability Certification (2026-05-30)

| File | Purpose | Status |
|---|---|---|
| `BATCH_E_EXECUTIVE_SUMMARY.md` | Operator-facing roll-up · final verdict 🟢 **PARTIALLY RECOVERABLE** (data layer 🟢 · master-login auth 🟡 · live-app boot ⚪) | ✅ ⛔ |
| `DISASTER_RECOVERY_DRILL_REPORT.md` | Phase 1+2 · 442 MB archive downloaded · 283 575 records restored · 0 corrupt · 10-step drill checklist | ✅ ⛔ |
| `RESTORE_VALIDATION_REPORT.md` | Phase 3 · 23/23 mandatory-target collection EXACT match · all portal-user bcrypt preserved · `user_directory` redacted by design | ✅ ⛔ |
| `RECOVERABILITY_CERTIFICATION.md` | Phase 4 · "Yes — ~10-20 min full app recovery, 60-min RPO (current) or 24-hr RPO (recommended)" | ✅ ⛔ |
| `BACKUP_POSTURE_RECOMMENDATION.md` | Phase 5 · Cadence analysis (hourly vs 4h vs 6h vs nightly) · **recommendation: nightly @ 04:00 UTC** (worker memory headroom shrinking; OOM trajectory ~14 days at current hourly cadence) | ✅ ⛔ |
| `batch_e_evidence/` (folder) | Raw R2 presigned URL listing · drill_run.log · prod source counts · drill-vs-prod comparison JSON | ✅ |

🟢 **Headline: drill DB `masci_restore_drill_2026_05_30` proves end-to-end restorability of the complete-R2 archive at the data layer.** Wall-clock drill: ~4 minutes. The principal UNKNOWN from Batch D is eliminated.

🟡 **Material findings**:
1. `user_directory.password_hash` redacted by design — master multi-login requires post-restore reseed (extension of `_seed_hash` logic at `server.py:7596` recommended)
2. `restore_drill.py` doesn't auto re-upload R2 photo bytes (bytes ARE in archive)
3. Live-application boot against restored DB not exercised — next logical Batch F candidate

🟡 **Backup posture recommendation**: set `BACKUP_R2_HOURLY=false` + `BACKUP_R2_FULL_HOUR_UTC=4`. Archive size grew 4.7× in 5 days; worker has 158 MB headroom under 600 MB OOM watermark; hourly cadence projects OOM within ~14 days at current growth.

### 0a · Batch D · Production Backup Scheduler Activation & Proof of Life (2026-05-30)

| File | Purpose | Status |
|---|---|---|
| `BATCH_D_EXECUTIVE_SUMMARY.md` | Operator-facing roll-up · 3 verdicts (🟢 SCHEDULER RESTORED · 🟢 LITE VERIFIED · 🟢 COMPLETE-R2 VERIFIED) · 1 critical operator-awareness finding | ✅ ⛔ |
| `SCHEDULER_STATUS_REPORT.md` | Phase 1+2 · T+0 Attempt-1 (inconclusive · rolling deploy) · T+0 Attempt-2 (PASS) · T+5 (PASS) · 10/10 mandatory proof checks | ✅ ⛔ |
| `BACKUP_SYSTEM_VERIFICATION_REPORT.md` | Phase 3 · 22-subsystem PASS/FAIL grid · RPO answer (≤ 60 min while `BACKUP_R2_HOURLY=true`) · restore paths still ⚪ UNKNOWN | ✅ ⛔ |
| `DOCUMENTATION_DRIFT_REPORT.md` | Phase 4 · 6 drift items (0 critical) · key drift: `BACKUP_LITE_MODE_ONLY` and `BACKUP_R2_HOURLY` are **independent** code paths | ✅ ⛔ |
| `RUNTIME_VS_CODE_COMPARISON_REPORT.md` | Phase 4 · 0 discrepancies on exercised subsystems · 9 subsystems documented as not-yet-exercised | ✅ ⛔ |
| `batch_d_evidence/` (folder) | Raw probe + version + R2 inventory + admin endpoints (JSON) | ✅ |

🟡 **Critical finding**: complete-R2 fired automatically on scheduler re-enable because `BACKUP_R2_HOURLY=true` was the pre-existing prod value. 464 MB archive succeeded with no OOM. Going forward: 24 complete-R2 archives/day while flag stays true. Operator decision required (no auto-action).

---

## 0 · 2026-02-01 fork — Prior pass index

> The 2026-02-01 fork session: (a) reverted an unauthorized design-system
> pivot · (b) built the complete Platform Truth Map · (c) verified it
> with code + runtime evidence · (d) executed operator-authorized
> Batch A (truth-map corrections, NEW-GAP-A, Fleet DVIR policy, prod
> scheduler probe + complete-backup verification, Phase 1+2 scheduler
> hardening) · (e) executed operator-authorized Batch B (prod hardening
> deploy + root-cause-ID of dead scheduler + complete-R2 disablement
> investigation). Read these files before doing ANY platform work
> going forward.

### 0a · Batch B · Prod Hardening Deploy + Root-Cause ID (2026-02-01)

| File | Purpose | Status |
|---|---|---|
| `BATCH_B_EXECUTIVE_SUMMARY.md` | Operator-facing roll-up · 4 deliverables · 6 future decisions surfaced | ✅ ⛔ |
| `PRODUCTION_SCHEDULER_INSTRUMENTATION_DEPLOY_REPORT.md` | Deploy mechanism + post-deploy field-shape verification | ✅ ⛔ |
| `POST_DEPLOY_SCHEDULER_PROBE_REPORT.md` | **ROOT CAUSE**: production has `SCHEDULER_ENABLED=false` (or other falsy value). Deterministic via `boot_step: None` + `boot_exception: None` + `singleton_scheduler.py:217` evidence | ✅ ⛔ |
| `COMPLETE_R2_DISABLEMENT_INVESTIGATION.md` | **DESIGN INTENT**: lite-only is deliberate safety constraint per `server.py:6341` docstring · 4+ code refs | ✅ ⛔ |
| `batch_b_evidence/` (folder) | 3 raw probe responses | ✅ |

### 0b · Batch A · Truth Map Corrections + Hardening (2026-02-01)

| File | Purpose | Status |
|---|---|---|
| `EXECUTIVE_BATCH_A_SUMMARY.md` | Operator-facing roll-up · 7 actions executed · 8 deliverables · 7 future decisions surfaced | ✅ ⛔ |
| `TRUTH_MAP_CORRECTIONS_CERTIFICATION.md` | 5 truth-map docs corrected (Workflows 2 3 4 5 10) | ✅ ⛔ |
| `GAP_REGISTER_UPDATE.md` | NEW-GAP-A added · 19 gaps + 1 orphan total | ✅ ⛔ |
| `FLEET_DVIR_POLICY_RECORD.md` | Routing matrix adopted (NO Superintendent) · severity source = `fleet_defect_severity` | ✅ ⛔ |
| `PRODUCTION_SCHEDULER_PROBE_REPORT.md` | 2026-05-30T03:13:55Z probe · scheduler still DEAD · 4-day complete-r2 drift | ✅ ⛔ |
| `COMPLETE_BACKUP_VERIFICATION_REPORT.md` | **CRITICAL**: `BACKUP_LITE_MODE_ONLY=true` silently overrides `lite=false`; manual lite verified working | ✅ ⛔ |
| `SCHEDULER_HARDENING_PHASE1_REPORT.md` | Instrumentation (`boot_step`/`boot_step_ts`/`boot_exception`) live in preview | ✅ ⛔ |
| `SCHEDULER_HARDENING_PHASE2_REPORT.md` | Defensive wrapper `_backup_scheduler_loop_with_capture` live in preview | ✅ ⛔ |
| `batch_a_evidence/` (folder) | Raw probe + run-now responses (JSON) | ✅ |

### 0c · Phase 2A · Truth Map Verification & Gap Triage (2026-02-01)

| File | Purpose | Status |
|---|---|---|
| `PHASE_2A_EXECUTIVE_SUMMARY.md` | Operator-facing roll-up · 7 decisions required | ✅ ⛔ |
| `TRUTH_MAP_VALIDATION_REPORT.md` | 10 workflows × evidence-backed verdicts (5 ✅ · 3 ⚠ · 2 ❌) | ✅ ⛔ |
| `GAP_REVALIDATION_REPORT.md` | 19 gaps re-confirmed + 1 new (NEW-GAP-A) · re-ranked P0/P1/P2/P3 | ✅ ⛔ |
| `FLEET_DVIR_INVESTIGATION_REPORT.md` | Partial-orphan confirmed · target-behaviour matrix recommended | ✅ ⛔ |
| `BACKUP_SCHEDULER_READINESS_REPORT.md` | Status proven (prod dead per 2026-05-29; preview noisy but harmless) · 5-phase hardening plan ready | ✅ ⛔ |

### 0d · Platform Truth Map Phase 1 (2026-02-01)

| File | Purpose | Status |
|---|---|---|
| `PLATFORM_TRUTH_MAP_README.md` | Master index + classification legend (🟢 / 🟡 / 🔴 / ⚪ / ⚫) | ✅ ⛔ |
| `PLATFORM_ROUTE_MAP.md` | 249 frontend routes · auth wrapper · classification | ✅ ⛔ |
| `API_DEPENDENCY_MAP.md` | 816 backend endpoints · auth gates · 143 collections · critical-path triggers | ✅ ⛔ |
| `WORKFLOW_LIFECYCLE_MAP.md` | 31 workflows × 16 required questions (full lifecycle) | ✅ ⛔ |
| `NOTIFICATION_DELIVERY_MAP.md` | Email routing rules · bell/task fan-out · cron · gap rollup | ✅ ⛔ |
| `DASHBOARD_DESTINATION_MAP.md` | Where every record kind lands per portal | ✅ ⛔ |
| `ORPHAN_AND_GAP_REGISTER.md` | 18 gaps + 1 confirmed orphan re-validated 2026-02-01 | ✅ ⛔ |
| `SYSTEM_TALK_MAP.md` | Inter-system feeds (DB → API → email → bell) + aspirational gaps | ✅ ⛔ |
| `truth_map_data/` (folder) | Raw machine-extracted CSV/JSON/TXT evidence | ✅ |
| `WORKFLOW_LIFECYCLE_MAP_2026-05-23_archived.md` | Prior dated version retained for audit history | 🟡 archived |

### 0e · Stabilization Pass 8 (2026-02-01)

| File | Purpose | Status |
|---|---|---|
| `MASTER_LAYOUT_DEFECT_LIST.md` | 18 surfaces × 4 viewports audited · 5 defects found and surgically fixed · before/after evidence + DOM probes · NO redesign, NO primitives, NO workflow changes | ✅ ⛔ |
| `DESIGN_FAMILY_CLASSIFICATION.md` | Pass 7 "design families" mockup spec — **REJECTED by operator 2026-02-01** | 🚫 ABANDONED |
| `DESIGN_SYSTEM_PRIMITIVES.md` | Pass 7 design-system primitives spec — **REJECTED by operator 2026-02-01** | 🚫 ABANDONED |

After-state screenshots: `/app/memory/audit_screenshots_2026-02-01/after/zoom/` (D1–D5).

---

## 1 · Platform Governance Core

The substrate that protects the platform from itself.

| File | Purpose | Status |
|---|---|---|
| `PRD.md` | Master product requirements + phase log (always read first) | ✅ |
| `FINAL_DEEP_PRE_DEPLOY_CERTIFICATION.md` | Last canonical pre-deploy gate · 15 dimensions | ✅ |
| `GLOBAL_FORM_LAYOUT_ROOT_CAUSE_REPORT.md` | **2026-02-01 EMERGENCY** · Real root cause for platform-wide form bleed · `sm:col-span-2` auto-column-expansion defect + `md:` breakpoint too narrow + 5-col filter bars unreadable below 1280px · 214 grid + 60 col-span replacements · DOM evidence · binding global standard | ✅ ⛔ |
| `HR_LAYOUT_REMAINING_DEFECTS_APPENDIX.md` | **Pass 3 · HR-only** · Surgical fix for residual HR defects after global Pass 2: `col-span-N` without breakpoint, dialog `grid-cols-2 gap-2` cramped on phone, iOS Safari date-input cell stretching · 7 edits across 5 HR files · `min-w-0` + `w-full` doctrine | ✅ ⛔ |
| `GLOBAL_GRID_PATTERN_AUDIT.md` | **Pass 4 · Static codebase audit** · 1,419 layout-pattern matches scanned · 0 NEEDS FIX after 2 Pass-4 surgical fixes · canonical doctrine table | ✅ ⛔ |
| `COL_SPAN_RESIDUAL_REGISTER.md` | **Pass 4** · 156 `col-span-*` usages cataloged · 0 implicit-column risks · verification rules | ✅ ⛔ |
| `FILTER_GRID_RESIDUAL_REGISTER.md` | **Pass 4** · 153 multi-col grids cataloged · `md:grid-cols-{4,5}` eliminated · category breakdown | ✅ ⛔ |
| `VIEWPORT_DOM_MEASUREMENT_REPORT.md` | **Pass 4 · Runtime sweep** · 15 surfaces × 9 viewports = 135 cells · 135 PASS · 0 FAIL · 0 ERROR | ✅ ⛔ |
| `LAYOUT_EXCEPTION_REGISTER.md` | **Pass 4** · 115 documented intentional exceptions across 7 categories (button clusters, KV display, 12-col bootstrap, admin diagnostic, thumbnails, Search-spans-2, arbitrary templates) | ✅ ⛔ |
| `GLOBAL_LAYOUT_COMPLETION_CERTIFICATION.md` | **Pass 4 · ⛔ REVOKED by operator on visual grounds** · Pass-4 rules were too permissive (150 px floor + 16 px gap allowed cramped 5-col filter bars) · superseded by Pass 5 | ⛔ |
| `VISUAL_LAYOUT_QUALITY_CORRECTION_REPORT.md` | **Pass 5 · Visual quality correction** · 240 px filter cell floor · 260 px form input floor · 24 px gap minimum on tablet+ · 2-col-max filter bars platform-wide · 58 files / 77 mechanical replacements · FilterBar.jsx 2-col doctrine | ✅ ⛔ |
| `PLATFORM_UX_QUALITY_AUDIT.md` | **Pass 6 · UX quality reset** · why DOM rules aren't enough · operator-cited UX failures (orphan buttons, empty stats, weak hierarchy, missing context chips) · approach + primitives + pattern roll-out plan | ✅ ⛔ |
| `FILTER_BAR_UX_STANDARD.md` | **Pass 6 binding contract** · filter bar required structure: 2-col input grid + dedicated action footer with context chip LEFT + actions RIGHT + border-t separator · color palette · anti-patterns | ✅ ⛔ |
| `FORM_COMPOSITION_STANDARD.md` | **Pass 6 binding contract** · form required structure: header + sections + footer · compact input rule (`max-w-[200px]`) · multi-line content rule · section grouping rule · anti-patterns | ✅ ⛔ |
| `DASHBOARD_VISUAL_QUALITY_STANDARD.md` | **Pass 6 binding contract** · stats strip = single Card with internal `sm:divide-x` grid (NOT N separate Cards) · tile dashboard contract · empty/loading/error states | ✅ ⛔ |
| `DEVICE_CLASS_VISUAL_REVIEW_REPORT.md` | **Pass 6** · per-device review of patched surfaces · operator's 10-question visual standard applied · pattern roll-out queue | ✅ ⛔ |
| `UX_QUALITY_FIX_CERTIFICATION.md` | **Pass 6 status: 🟡 awaiting operator verdict** · before/after summary · shared `<SectionCard>` + `<ActionFooter>` primitives · how-to-extend template | ✅ ⛔ |
| `DESIGN_SYSTEM_PRIMITIVES.md` | **Pass 7** · 8 primitive specs (SectionCard · ActionFooter · FilterBar · FormGrid · MetricStrip · FormSection · DrawerLayout · ModalLayout) · color accent tokens · anti-patterns | ✅ ⛔ |
| `DESIGN_FAMILY_CLASSIFICATION.md` | **Pass 7** · 4 workflow families (A Field Forms · B Approval Consoles · C Operational Status · D Configuration Consoles) · per-family doctrine + 22-surface mapping · Pass-8 rollout sequence · LIVE mockups at `/__design/family-{a,b,c,d}` | ✅ ⛔ |
| `PRE_DEPLOY_LIVE_DEFECT_VALIDATION_REPORT.md` | **Phase V.5 · 2026-02-01** · 5-viewport × 6-defect pre-redeploy gate · 🟢 SAFE TO REDEPLOY verdict · prototype for Phase 1C | ✅ ⛔ |
| `PHASE_1C_VIEWPORT_VALIDATION_GATE_SPEC.md` | **P1 Platform Quality Infrastructure** · 10-viewport × 11-target gate spec · binding deployment policy · APPROVED BACKLOG · implement AFTER prod validation + backup hardening | 📐 ⛔ |
| `POST_DEPLOY_LIVE_CERTIFICATION.md` | Last production verification · post-cutover | ✅ |
| `POST_DEPLOY_VERIFICATION_REPORT.md` | TRUST-TIME-1 + 1B post-deploy verification | ✅ |
| `AUTHORITY_MISMATCH_REPORT.md` | Authority Mismatch Probe last run | ✅ auto-gen |
| `TIMESTAMP_DOCTRINE_PROBE_REPORT.md` | Timestamp Doctrine Probe last run | ✅ auto-gen |
| `TIMESTAMP_UTILITY_STANDARD.md` | Store-UTC / transmit-tz-aware / render-local / label-UTC | ✅ ⛔ |
| `TRUST_TIME_1_CERTIFICATION.md` | +4h PO bug fix · 3-layer remediation | ✅ |
| `TIMESTAMP_DOCTRINE_SELF_PROTECTION_CERTIFICATION.md` | TRUST-TIME-1B self-protection probe | ✅ |
| `TRUST_SURFACES.md` / `.json` | Registry of every trust surface · 10 entries | ✅ |
| `TRUTHFUL_STATE_GOVERNANCE.md` / `.json` | 12 contracts of "what is displayed = what is true" | ✅ |
| `OPERATIONAL_TELEMETRY_DOCTRINE.md` / `.json` | Allowed telemetry events + PII rules | ✅ ⛔ |
| `CONTEXT_GOVERNANCE_STANDARD.md` | Cross-portal context inheritance doctrine | ✅ |
| `SHARED_SURFACE_CONTEXT_MATRIX.json` | Per-surface compliance matrix · 5 governed · 0 TBD | ✅ |
| `DEPLOYMENT_HISTORY.json` | OPS-1 deployment stanza · auto-tracked | ✅ |
| `GOVERNANCE_PRIMITIVES_STANDARD.md` | Capability-primitive doctrine | ✅ |

## 2 · Cross-Portal UX Governance

Visual + interaction discipline across Admin / PM / HR / Safety /
Dispatch / Shop / Field Leadership.

| File | Purpose | Status |
|---|---|---|
| `CROSS_PORTAL_OPERATOR_ATLAS.md` | Master map of every operator surface | ✅ |
| `FORM_SPACING_DOCTRINE.md` | **Phase V.5+ revised contract** · `lg:grid-cols-{2,3} gap-x-8` form rows · `sm:grid-cols-2 xl:grid-cols-{4,5}` filter bars · `lg:col-span-2` for full-width children · enforced by `<FormGrid>` + `<FilterBar>` primitives | ✅ ⛔ |
| `CROSS_PORTAL_CONSISTENCY_STANDARD.md` | UX consistency contract | ✅ |
| `CROSS_PORTAL_COACHING_STANDARD.md` | Coaching copy doctrine | ✅ ⛔ |
| `CROSS_PORTAL_VOCABULARY_GLOSSARY.md` | Canonical operator vocabulary | ✅ |
| `ADMIN_UX_GOVERNANCE.md` | Admin console rendering rules | ✅ |
| `ADMIN_INFORMATION_ARCHITECTURE.md` | Admin nav doctrine | ✅ |
| `ADMIN_DOMAIN_MAP.json` | Admin domain boundaries | ✅ |
| `PM_TRANSITION_INVENTORY.md` | PM portal scope | ✅ |
| `HR_PORTAL_GOVERNANCE.md` (if present) | HR portal rules | ✅ |
| `SAFETY_PORTAL_GOVERNANCE.md` (if present) | Safety portal rules | ✅ |
| `DISPATCH_INVENTORY.md` (if present) | Dispatch surface inventory | ✅ |
| `VISUAL_LOUDNESS_DOCTRINE.md` (or `CALM_OBSERVABILITY_UI.md`) | Calmness rules · single-red doctrine | ✅ ⛔ |
| `COACHING_AND_VERBIAGE_AUDIT.md` | Audit of operator-facing copy | ✅ |
| `COMMUNICATION_TONE_STANDARD.md` | Tone doctrine (calm · operational · non-corporate) | ✅ |
| `CONTEXTUAL_RETURN_PATH_AUDIT.md` | Back-link inheritance audit | ✅ |

## 3 · Operational Records / Phase V

Doctrine for the next major phase. NONE of these are implemented yet.

| File | Purpose | Status |
|---|---|---|
| `CONSTRAINT_BOARD_VISUAL_MODEL.md` | Constraint UI doctrine (V-Prelude Wave 1) | 📐 |
| `OPERATIONAL_CONSTRAINT_FOUNDATION.md` | Constraint schema + scope | 📐 |
| `OPERATIONAL_LINKING_RULES.md` | **Read before any cross-artifact link is built** | 📐 ⛔ |
| `OPERATIONAL_TIMELINE_FOUNDATION.md` | `operational_links` substrate doctrine | 📐 |
| `PHOTO_GOVERNANCE_STANDARD.md` | Photo-as-evidence doctrine | 📐 |
| `OPERATIONAL_SEARCH_ARCHITECTURE.md` | Field-first search doctrine | 📐 |
| `FIELD_MEMORY_FOUNDATION.md` | Deterministic recurring-pattern surface | 📐 |
| _(Future)_ `RFI_DOCTRINE.md` | Phase V.1+ · not yet drafted | 🟡 |
| _(Future)_ `RFI_LIFECYCLE.md` | Phase V.1+ · not yet drafted | 🟡 |
| _(Future)_ `SCHEDULE_DOCTRINE.md` | Phase V.3+ · not yet drafted | 🟡 |
| _(Future)_ `P6_IMPORT_ARCHITECTURE.md` | Phase V.4+ · not yet drafted | 🟡 |
| _(Future)_ `RFI_PDF_STANDARD.md` | Phase V.1+ · not yet drafted | 🟡 |
| _(Future)_ `DOT_FAA_TEMPLATES.md` | Phase V.1+ · not yet drafted | 🟡 |

## 4 · V-Prelude Planning (current phase)

All planning artifacts for the pre-RFI substrate work.

| File | Purpose | Status |
|---|---|---|
| `PHASE_V_PRELUDE_IMPLEMENTATION_PLAN.md` | 4-wave master sequence | 📐 ⛔ |
| `OPERATIONAL_CONSTRAINT_FOUNDATION.md` | Wave 1 substrate | 📐 |
| `PHOTO_GOVERNANCE_STANDARD.md` | Wave 1 substrate | 📐 |
| `OPERATIONAL_TIMELINE_FOUNDATION.md` | Wave 1 substrate | 📐 |
| `OPERATIONAL_LINKING_RULES.md` | Wave 1 substrate (this directive) | 📐 ⛔ |
| `OPERATIONAL_SEARCH_ARCHITECTURE.md` | Wave 2 | 📐 |
| `FIELD_MEMORY_FOUNDATION.md` | Wave 2 | 📐 |
| `OFFLINE_DRAFT_RESILIENCE_MODEL.md` | Wave 3 | 📐 |
| `MOBILE_UX_REFINEMENT_AUDIT.md` | Wave 3 | 📐 |
| `ROLE_AWARE_VISIBILITY_MODEL.md` | Wave 1-3 | 📐 |
| `GOVERNANCE_SELF_HEALING_ROADMAP.md` | Wave 4 | 📐 |
| `V_PRELUDE_WAVE_READINESS_CERTIFICATION.md` | Pre-Wave-1 gate | 🟢 |

### Wave 1 — Substrate (implemented 2026-05-28)

| File | Purpose | Status |
|---|---|---|
| `WAVE1_IMPLEMENTATION_SUMMARY.md` | Wave 1 master summary | 🟢 |
| `OPERATIONAL_CONSTRAINT_CERTIFICATION.md` | Wave 1 constraint cert | 🟢 |
| `OPERATIONAL_LINKS_CERTIFICATION.md` | Wave 1 links cert · §10 probes | 🟢 ⛔ |
| `OPERATIONAL_TIMELINE_CERTIFICATION.md` | Wave 1 timeline cert | 🟢 |
| `PHOTO_GOVERNANCE_CERTIFICATION.md` | Wave 1 photo governance cert | 🟢 |
| `WAVE1_OBSERVATION_GUIDE.md` | 24-hr observation window guide | 🟡 active |

### Wave 1.1 — Timeline Sidecar (implemented 2026-05-28)

| File | Purpose | Status |
|---|---|---|
| `WAVE1_1_TIMELINE_SIDECAR_SUMMARY.md` | Wave 1.1 master summary | 🟢 |
| `TIMELINE_CALMNESS_CERTIFICATION.md` | Visual calmness contract | 🟢 |
| `MOBILE_CHRONOLOGY_CERTIFICATION.md` | Mobile ergonomic contract | 🟢 |
| `TIMELINE_ROLE_VISIBILITY_CERTIFICATION.md` | Cross-portal role gate | 🟢 |
| `OPERATIONAL_TIMELINE_OBSERVATION_REPORT.md` | Observation window log | 🟡 active |

### Wave 1.1A — Calmness Telemetry (implemented 2026-05-28)

| File | Purpose | Status |
|---|---|---|
| `WAVE1_1A_CALMNESS_TELEMETRY_SUMMARY.md` | Wave 1.1A master summary | 🟢 |
| `TIMELINE_LOUDNESS_PROBE_CERTIFICATION.md` | Probe cert · heuristic targets | 🟢 |
| `CHRONOLOGY_DENSITY_HEURISTICS_REPORT.md` | Density / dup heuristics | 🟢 |
| `GOVERNANCE_TRENDLINE_EXTENSION.md` | Trendline doctrine + inventory | 🟢 |
| `OPERATIONAL_TIMELINE_STABILITY_REPORT.md` | End-of-pass stability picture | 🟡 active |
| `TIMELINE_LOUDNESS_TRENDLINE.json` | Append-only calmness trendline | 🟢 auto-gen |

### Wave 1.1B — Governance Memory Self-Protection (implemented 2026-05-28)

| File | Purpose | Status |
|---|---|---|
| `WAVE1_1B_GOVERNANCE_MEMORY_SUMMARY.md` | Wave 1.1B master summary | 🟢 |
| `TRENDLINE_SELF_PROTECTION_CERTIFICATION.md` | Probe cert · 8-axis matrix | 🟢 |
| `GOVERNANCE_MEMORY_INTEGRITY_REPORT.md` | Live snapshot state · guarantees | 🟢 |
| `APPEND_ONLY_MEMORY_CERTIFICATION.md` | Append-only doctrine | 🟢 |
| `OBSERVATION_FREEZE_HARDENING_REPORT.md` | 18 freeze triggers · pre-Wave-2 gate | 🟢 |
| `TIMELINE_LOUDNESS_TRENDLINE.snapshot.json` | Trendline integrity anchor | 🟢 auto-gen |
| `LOUDNESS_TRENDLINE.snapshot.json` | Portal-wide trendline anchor | 🟢 auto-gen |

### Wave 1 Observation Posture (open 2026-05-28)

| File | Purpose | Status |
|---|---|---|
| `WAVE1_OBSERVATION_STATUS.md` | Window status · 18 freeze trigger states · cleanup receipts | 🟡 active |
| `OPERATIONAL_TRUST_VALIDATION_REPORT.md` | Machine vs operator-verifiable trust signals · walkthrough capture template | 🟡 awaiting operator input |
| `CHRONOLOGY_BEHAVIOR_REPORT.md` | Substrate state · anti-patterns · canonical row shapes | 🟢 |
| `MOBILE_RHYTHM_REPORT.md` | Mobile contract · iPhone scenarios · stop-the-line conditions | 🟢 |
| `GOVERNANCE_STABILITY_REPORT.md` | 5/5 probes · 50/50 tests · reversibility ledger | 🟢 |

## 4.A · Phase V.1/V.2 · Operational Daily Record (ODR) + Daily Report Evolution (M0.0 → Wave-1C CLOSED · 2026-05-29)

ODR substrate is LIVE in preview through **M1 Option C**. M0.0–M0.4
shipped per their certifications. M0.35 added 2 permanent doctrine
locks. M1 shipped Option C: write freeze · unified projector ·
operational_links bridge · archive UI.

🔄 **Daily Report Evolution Pivot landed (2026-05-29):** ODR
substrate becomes the operational intelligence layer; the Daily
Report remains the field-facing experience.

**Wave-1A SHIPPED:** `POST /api/daily-reports` restored ·
`DELETE` stays frozen · structured `production[]` (7-unit closed
enum) · structured `constraints[]` (11-type closed enum) ·
`audit_envelope_sha256` at insert ·
`GET /api/daily-reports/{id}/audit-footer` endpoint · advisory
flags (RFI candidate · schedule impact · informational only ·
server-derived).

**Wave-1B SHIPPED:** Production UI · Constraint chip UI · PM
Exposure Tile · `GET /api/daily-reports/exposure-signals?days=14`.
Foreman 9-step contract preserved (both cards OPTIONAL ·
Doctrine Lock #1).

**Wave-1C SHIPPED:** DR PDF audit footer rendering
(WeasyPrint `@page @bottom-center` · universal across audiences) ·
offline / recovery baseline re-certified · Wave-2 strengthening
scoped + documented.

**89 / 89 cumulative ODR tests · 0 failures · ESLint clean ·
advisory governance probes green.**

**HALTED at end of Wave-1C pending Internal Superintendent
Validation Review. Pilot may NOT begin until operator authorizes
explicitly. RFI · Schedule · P6 remain out of scope.**

| File | Purpose | Status |
|---|---|---|
| `ODR_DATA_MODEL.md` | Pydantic schema · 16+2 sections · enums · indexes (+ Delta Integration Addendum D1–D8) | 📐 ⛔ |
| `ODR_UI_WIREFRAMES.md` | Mobile-first foreman entry · voice + dropdown + auto-fill (+ Addendum D1–D8) | 📐 |
| `ODR_ECOSYSTEM_INTEGRATION_MAP.md` | 12 consumer projectors · single-entry / multi-consumer (+ Addendum D1–D8) | 📐 ⛔ |
| `ODR_PDF_LAYOUT_DESIGN.md` | 5 pages + appendix · 5 audience variants · forensic envelope (+ Addendum D1–D8) | 📐 |
| `ODR_MIGRATION_PLAN.md` | 6-wave cutover M0–M5 · legacy → ODR field mapping (+ Addendum D1–D8) | 📐 |
| `ODR_GAP_AUDIT.md` | 7-requirement pre-lock audit · 8 deltas proposed | 🟢 |
| `ODR_DELTA_INTEGRATION_SUMMARY.md` | Master delta map · D1–D8 + O1–O10 doctrine | 🟢 |
| `ODR_SPEC_LOCK_READINESS_REVIEW.md` | Pre-lock certification · 9/9 confirmations · awaiting lock | 🟢 |
| `ODR_PUBLIC_LINK_DEVICE_CONTINUITY_ADDENDUM.md` | **Public-Link Device Continuity Doctrine** (O11–O20) · trust boundary · 7 signals · audit log spec | 🟢 |
| `ODR_FINAL_GOVERNANCE_ADDENDUM.md` | **Final Governance** (O21–O35) · Field Leadership ODR Center · Inbox · amendment / official record / signature / attachment doctrines | 🟢 |
| `ODR_SPEC_LOCK_CERTIFICATION.md` | **Final pre-lock certification** · 35/35 doctrines · 21/21 confirmations · 28/28 risks · STOP | 🟢 |
| `ODR_COACHING_GUIDANCE_ADDENDUM.md` | **Coaching · Training · Operational Guidance** (O36–O50) · 4 touchpoints · crew-specific · first-time onboarding · FL Training Center · PM coaching consumption | 🟢 |
| `ODR_COACHING_AND_GUIDANCE_CERTIFICATION.md` | **Coaching pre-lock certification** · 8/8 coaching certs · 50/50 doctrines · 29/29 confirmations | 🟢 |
| `M0_0_HYGIENE_CLOSURE_REPORT.md` | M0.0 W1/W2/W3 closure (precondition to substrate) | ✅ |
| `ODR_M0_1_SUBSTRATE_CERTIFICATION.md` | M0.1 substrate sealed · 8 collections · 25 indexes · 12 tests | ✅ 🟢 |
| `M0_2_CONTINUITY_ENGINE_CERTIFICATION.md` | M0.2 Public Link Continuity Engine LIVE | ✅ 🟢 |
| `M0_2_AMENDMENT_ENGINE_CERTIFICATION.md` | M0.2 Amendment Engine LIVE (24h window · Super+ post-window) | ✅ 🟢 |
| `M0_2_PDF_ENGINE_CERTIFICATION.md` | M0.2 PDF Engine LIVE · 5 audiences · SHA256 footer | ✅ 🟢 |
| `OGC_CATALOG_SEED_CERTIFICATION.md` | M0.2A OGC Catalog · 14 keys · ≥4 EN + ≥4 ES per key · 9 crew overlays | ✅ 🟢 |
| `CREW_TYPE_READINESS_MATRIX.md` | M0.2A · 21 crew types · Required / Recommended / Advanced | ✅ 🟢 |
| `GUIDANCE_INTELLIGENCE_FOUNDATION.md` | M0.2A · deterministic prompt resolver doctrine | ✅ 🟢 |
| `ODR_PUBLIC_LINK_CONTINUITY_PROBE_REPORT.md` | Probe auto-generated report (refreshed on every run) | ✅ auto-gen |
| `ODR_PUBLIC_LINK_CONTINUITY_PROBE_REPORT_DOCTRINE.md` | Operator playbook for the continuity probe | ✅ |
| `ODR_BILINGUAL_PROBE_REPORT.md` | Probe auto-generated report (refreshed on every run) | ✅ auto-gen |
| `ODR_BILINGUAL_PROBE_REPORT_DOCTRINE.md` | Operator playbook for the bilingual probe | ✅ |
| `M0_2A_OPERATOR_REVIEW_GUIDE.md` | **Pre-pilot review checklist · STOP point** | ✅ ⛔ |
| `M0_3_FOREMAN_ENTRY_CERTIFICATION.md` | M0.3 foreman entry surface (phone-first, bilingual, 9-step) | ✅ 🟢 |
| `M0_3_FL_CENTER_CERTIFICATION.md` | M0.3 FL ODR Command Center (7 calm tabs, role-aware) | ✅ 🟢 |
| `M0_3_PM_PANEL_CERTIFICATION.md` | M0.3 PM consumption panel (5-metric read-only lens) | ✅ 🟢 |
| `M0_3_PUBLIC_VIEWER_CERTIFICATION.md` | M0.3 public viewer (DOT/FAA/CEI-safe) | ✅ 🟢 |
| `ODR_TRUST_BANNER_DOCTRINE.md` | Calm "Operational Record · Audit history protected · Amendments tracked" line | ✅ 🟢 |
| `ODR_ADOPTION_OBSERVATION_PLAN.md` | Aggregate-only adoption telemetry doctrine (NEVER scoring) | ✅ 🟢 |
| `M0_3_OPERATOR_REVIEW_GUIDE.md` | **M0.3 review checklist · STOP point** | ✅ ⛔ |
| `ODR_AUDIENCE_PROJECTION_DOCTRINE.md` | M0.35 · "user picks audience · system picks projection" · 11 profiles → 5 projections | ✅ ⛔ |
| `ODR_REALITY_VALIDATION_REPORT.md` | M0.35 · 4 scenarios (Airport · Drainage · Asphalt · Concrete) · 4/4 clean · 0 leaks | ✅ 🟢 |
| `ODR_REALITY_GAP_AUDIT.md` | M0.35 · 8 gaps surfaced · 1 pilot blocker (G7 · photo embedding) | ✅ 🟢 |
| `OFFLINE_QUEUE_READINESS_ASSESSMENT.md` | M0.35 · 5-phase plan · 8.5–11.5 dev-day estimate | ✅ 🟢 |
| `ODR_PILOT_SUCCESS_SCORECARD.md` | M0.35 · adoption / quality / operational value / sentiment thresholds | ✅ 🟢 |
| `M0_35_OPERATOR_REVIEW_GUIDE.md` | **M0.35 review checklist · STOP point · M1 authorization gate** | ✅ ⛔ |
| `ODR_SIMPLICITY_TEST_DOCTRINE.md` | **M0.35 Doctrine Lock #1** · permanent foreman approval gate · field simplicity overrides architectural elegance | ✅ ⛔ |
| `ODR_PLATFORM_INHERITANCE_DOCTRINE.md` | **M0.35 Doctrine Lock #2** · ODR is a module of MASCI Ops, not a separate app · inheritance contract | ✅ ⛔ |
| `M0_4_PHOTO_PDF_CERTIFICATION.md` | **M0.4** · external PDF photo thumbnail embedding · 9/9 tests · audience projection + redaction + continuity preserved | ✅ 🟢 |
| `EXTERNAL_PDF_PHOTO_GOVERNANCE_REPORT.md` | **M0.4** · audience projection matrix · external threat model · 6/6 redactions confirmed · audit log enrichment | ✅ 🟢 |
| `UPDATED_OPERATOR_REVIEW_GUIDE.md` | **M0.4 supersedes M0.35 review guide** · M1 authorization gate · advisory probe inventory · approval items | ✅ ⛔ |
| `M1_PRE_AUTHORIZATION_REVIEW_LEGACY_DAILY_REPORT_STRATEGY.md` | **M1 review** · Option A/B/C analysis · 85-row mapping audit · recommendation: Option C · operator chose Option C | ✅ |
| `M1_OPTION_C_IMPLEMENTATION_PLAN.md` | **M1** · Option C closure · 6 authorized moves · zero-mutation evidence · reversibility plan | ✅ ⛔ |
| `LEGACY_RECORD_FREEZE_CERTIFICATION.md` | **M1** · POST/DELETE → 410 Gone · zero-mutation test green · response shape spec · reversibility | ✅ ⛔ |
| `UNIFIED_RECORDS_PROJECTOR_CERTIFICATION.md` | **M1** · `/api/operational-records` + resolver · read-only two-substrate projection · honest counts · 8 tests | ✅ ⛔ |
| `ARCHIVE_VISUAL_TREATMENT_STANDARD.md` | **M1** · single source of truth for archive UI · slate · uppercase · no alarm · forbidden phrases & colors · component contract | ✅ ⛔ |
| `OPERATIONAL_LINKS_BRIDGE_CERTIFICATION.md` | **M1** · `legacy_daily_report` target-only · validation gate · allowed link patterns · forward operations enabled | ✅ ⛔ |
| `M1_OPERATOR_REVIEW_GUIDE.md` | **M1 supersedes M0.4 review guide** · pilot authorization gate · spot-check checklist | ✅ ⛔ |
| `DAILY_REPORT_EVOLUTION_PLAN.md` | **Pivot master plan** · keep DR field-facing · retarget ODR as intelligence layer · 6 ADDs · M1 freeze collision flagged | ✅ ⛔ |
| `DAILY_REPORT_FIELD_SIMPLICITY_CERTIFICATION.md` | **Pivot** · Doctrine Lock #1 applied to every ADD · 9-step contract locked · PR approval block template | ✅ ⛔ |
| `DAILY_REPORT_PRODUCTION_TRACKING_DESIGN.md` | **Pivot design** · 7-unit closed enum · activity INFERRED | ✅ |
| `DAILY_REPORT_CONSTRAINT_TRACKING_DESIGN.md` | **Pivot design** · 11-type taxonomy · chip selector · advisory flags | ✅ |
| `DAILY_REPORT_OFFLINE_RECOVERY_PLAN.md` | **Pivot** · low/no signal contract · 7 acceptance criteria before pilot | ✅ ⛔ |
| `ODR_SUBSTRATE_REUSE_MAP.md` | **Pivot** · 16 ODR-era assets retargeted at DR | ✅ |
| `DAILY_REPORT_ELITE_UPGRADE_OPERATOR_REVIEW.md` | **Pivot** · implementation-readiness gate · wave-1 scope picks | ✅ ⛔ |
| `WAVE_1A_IMPLEMENTATION_REPORT.md` | **Wave-1A** · 14 moves shipped · POST restored · structured production+constraints · audit footer · advisory flags · 15/15 tests · 82/82 cumulative | ✅ ⛔ |
| `PRODUCTION_TRACKING_CERTIFICATION.md` | **Wave-1A** · 7-unit closed enum {LF,SY,CY,TON,EA,ACRE,OTHER} · ProductionRow · 3 tests | ✅ ⛔ |
| `CONSTRAINT_TRACKING_CERTIFICATION.md` | **Wave-1A** · 11-type closed enum · ConstraintRow + advisory derivation · 3 tests | ✅ ⛔ |
| `OFFLINE_HARDENING_CERTIFICATION.md` | **Wave-1A baseline** · existing offline contract baselined · Wave-1C strengthening scoped (~2.5 dev-days) · pilot gating | ✅ ⛔ |
| `DAILY_REPORT_AUDIT_FOOTER_CERTIFICATION.md` | **Wave-1A** · SHA256 envelope at insert · `GET /api/daily-reports/{id}/audit-footer` · 4 tests | ✅ ⛔ |
| `ADVISORY_FLAG_CERTIFICATION.md` | **Wave-1A** · operator-defined heuristic table · informational only · no actions triggered · 1 test | ✅ ⛔ |
| `WAVE_1A_OPERATOR_REVIEW_GUIDE.md` | **Wave-1A supersedes Daily Report Elite Upgrade review** · Wave-1B / 1C scope picks · 9-item spot-check | ✅ ⛔ |
| `WAVE_1B_IMPLEMENTATION_REPORT.md` | **Wave-1B** · Production UI · Constraint UI · PM Exposure Tile · 3 tests | ✅ ⛔ |
| `WAVE_1C_IMPLEMENTATION_REPORT.md` | **Wave-1C** · DR PDF audit footer rendering · offline baseline · 4 tests | ✅ ⛔ |
| `PRODUCTION_UI_CERTIFICATION.md` | **Wave-1B** · 7-field row · 7-unit closed-enum select · station from/to · doctrine compliance | ✅ ⛔ |
| `CONSTRAINT_UI_CERTIFICATION.md` | **Wave-1B** · 11-chip grid · one-tap insert · advisory derivation server-side · `signal_only` doctrine | ✅ ⛔ |
| `PM_EXPOSURE_TILE_CERTIFICATION.md` | **Wave-1B** · 5-row read-only signal panel · `GET /api/daily-reports/exposure-signals?days=14` | ✅ ⛔ |
| `OFFLINE_RECOVERY_CERTIFICATION.md` | **Wave-1C baseline** · existing offline contract baselined · Wave-2 strengthening scoped · pilot gating | ✅ ⛔ |
| `PDF_AUDIT_FOOTER_RENDER_CERTIFICATION.md` | **Wave-1C** · WeasyPrint `@page @bottom-center` · `Official Record · DR-NNN · sha256=<16> · rendered <UTC>` · universal across audiences | ✅ ⛔ |
| `PILOT_READINESS_ASSESSMENT.md` | **Wave-1B/1C** · pilot acceptance criteria · open risks · NOT yet a pilot authorization | ✅ ⛔ |
| `WAVE_1B_1C_OPERATOR_REVIEW_GUIDE.md` | **Wave-1B/1C supersedes Wave-1A review guide** · pilot is NOT next gate · Internal Superintendent Validation Review is | ✅ ⛔ |
| `WAVE_1B_1C_EXECUTIVE_SUMMARY.md` | **Wave-1B/1C closure brief** · WHAT CHANGED / WHAT DID NOT · current status · remaining risks · next gate (NOT pilot) | ✅ ⛔ |
| `SUPERINTENDENT_VALIDATION_REPORT.md` | **Post-refinement** · operational-review template · 3 scenarios (Airport · Utility/Drainage · Concrete/Sidewalk) · pilot gate checklist · field-language confirmation matrix | ✅ ⛔ |
| `DAILY_REPORT_FIELD_LOGIC_REFINEMENT_REPORT.md` | **Field-logic refinement closure** · 4 fixes shipped · backend untouched · 89/89 still green · stop-condition reinforced | ✅ ⛔ |
| `SUBCONTRACTOR_FOREMAN_FIELD_CERTIFICATION.md` | **Fix 1** · subcontractor foreman → plain text · no MASCI roster pollution · supplier-tied picker deferred | ✅ ⛔ |
| `REPORT_ROLE_PICKER_CERTIFICATION.md` | **Fix 2** · `FlUserCombo` + public `GET /api/field-leadership-roster` (name+role+active only · no PII) · Prepared By / Superintendent role-aware pickers with manual fallback | ✅ ⛔ |
| `DELAY_EXTRA_WORK_GATE_CERTIFICATION.md` | **Fix 3** · Section 03 relabel · submit-gate when YES + 0 rows · `attentionOpen` auto-expand · NO path preserved · still signal-only | ✅ ⛔ |
| `FIELD_LANGUAGE_CLEANUP_CERTIFICATION.md` | **Fix 4** · UI vocabulary matrix · "Hours Impact" → "Lost Hours" · anti-pattern audit (forbidden strings cleared) · chip labels held as-is per directive | ✅ ⛔ |
| `SECTION_03_CLEANUP_CERTIFICATION.md` | **Section 03** · legacy "Detail any Yes answers" box no longer fires on `schedule_delays === Yes` · weather/accidents/injuries still trigger · placeholder copy updated · `incident_notes` field preserved | ✅ ⛔ |
| `FL_ROLE_STANDARDIZATION_REPORT.md` | **FL Role · master closure** · 4 canonical roles · alias maps · resolver · picker + dashboard + permission foundation summary | ✅ ⛔ |
| `FL_ROLE_ENUM_CERTIFICATION.md` | **FL Role · enum spec** · `FL_CANONICAL_ROLES` + hard aliases + uncertain aliases + `_canonical_role()` resolver behavior matrix · public roster envelope | ✅ ⛔ |
| `DAILY_REPORT_ROLE_PICKER_ALIGNMENT.md` | **FL Role · DR picker doctrine** · Prepared By + Superintendent role lists · "Name — Role" em-dash display · uncertain `*` marker · auto-populate from FL user · manual fallback | ✅ ⛔ |
| `FL_DASHBOARD_VISIBILITY_PREP.md` | **FL Role · planning only** · per-role surface matrix (Leadman / Foreman / Super / Sr. Super / Admin) · forbidden combinations · NOT implemented today | 📐 |
| `APPROVAL_REJECTION_PERMISSION_FOUNDATION.md` | **FL Role · planning only** · permission matrix · audit contract · audit-hash continuity with Wave-1C footer · forbidden behaviors · NOT implemented today | 📐 |
| `LEGACY_ROLE_MAPPING_REVIEW.md` | **FL Role · operator review** · 4 uncertain aliases (`Field Supervisor`, `General Foreman`, `Truck Boss`, `Working Supervisor`) with proposed canonical defaults + counts + recommended actions | ✅ ⛔ |
| `WEATHER_IMPACT_CLEANUP_CERTIFICATION.md` | **Weather Impact** · YES now routes to the structured Delays / Extra Work card with a "row with cause = Weather" requirement · legacy detail box removed from weather path · merged-gate IIFE drives status pill + `attentionOpen` · 6-scenario behavior matrix verified | ✅ ⛔ |
| `AUTO_EXPAND_GUIDANCE_CERTIFICATION.md` | **Auto-Expand Guidance** · Weather YES or Delays YES auto-expands the Delays / Extra Work card · 1.6 s amber ring highlight · scroll-into-view · NEVER auto-creates rows / auto-fills / notifies · prohibited-behavior audit · iPad viewport validation | ✅ ⛔ |
| `OFFLINE_HARDENING_IMPLEMENTATION_REPORT.md` | **Wave-2 master** · iter440 engine inventory · audit findings (zero schema-bump gaps) · live verification summary · 8-deliverable index · stop condition | ✅ ⛔ |
| `OFFLINE_DRAFT_ENGINE_CERTIFICATION.md` | **Wave-2 · draft engine** · `useFormDraft` contract · 800 ms debounce + 10 s force + iOS lifecycle handlers · device-scoped IDB · production/constraints round-trip proof | ✅ ⛔ |
| `PHOTO_RESILIENCY_CERTIFICATION.md` | **Wave-2 · photos** · DR Path A (inline dataURL) vs PO/Incident Path B (`photoStaging`) · failure-mode coverage matrix · status surfaces | ✅ ⛔ |
| `OFFLINE_SUBMISSION_QUEUE_CERTIFICATION.md` | **Wave-2 · submit queue** · `enqueueUpload` · MAX_TRIES=5 · backoff `[1·2·4·8·16]s` · `online`/`focus` drain · `onQueueItemSettled` deferred-commit · 3-layer dedup | ✅ ⛔ |
| `SYNC_RECONCILIATION_CERTIFICATION.md` | **Wave-2 · sync** · single-author/single-device/append-only doctrine · device-A round-trip walk · cross-token banner · 24 h server dedup TTL | ✅ ⛔ |
| `RECOVERY_TELEMETRY_CERTIFICATION.md` | **Wave-2 · telemetry** · 7-event taxonomy mapped to operator's 5 mandated signals · `/api/draft-telemetry` ingestion · IDB-buffered offline send · aggregate-only | ✅ ⛔ |
| `FIELD_RELIABILITY_TEST_MATRIX.md` | **Wave-2 · 15-scenario matrix** · Tier-A Playwright scaffolding + Tier-B iPad operator checklist · acceptance criteria · pilot gate | ✅ ⛔ |
| `PILOT_READINESS_RELIABILITY_ASSESSMENT.md` | **Wave-2 · reliability-only pilot gate** · supersedes Wave-1B/1C assessment on the reliability axis · open risks · acceptance criteria · doctrine compliance · pilot scoping runway (not in scope today) | ✅ ⛔ |
| `FIELD_RELIABILITY_PLAYWRIGHT_SUITE_REPORT.md` | **Wave-2 Tier-A** · authored `backend/tests/pw_suite/test_dr_field_reliability.py` · 7 tests · 6 active · 1 skipped (auth-gated) · ≈40 s total · maps to 15 mandated assertions · regression guardrail value matrix | ✅ ⛔ |
| `DR_FIELD_RELIABILITY_AUTOMATION_CERTIFICATION.md` | **Wave-2 Tier-A** · per-assertion verification table (1–15) · stability features · maintenance contract · what the suite is NOT (not a Tier-B walk replacement) | ✅ ⛔ |
| `RELIABILITY_REGRESSION_GUARDRAIL_REPORT.md` | **Wave-2 Tier-A** · platform-wide tripwire inventory · what each suite protects · run cadence · maintenance contract · stop condition | ✅ ⛔ |
| `PLATFORM_FORM_LAYOUT_BLEED_AUDIT.md` | **V.5 P0-1** · iPad field-bleed investigation · 84 unsafe Tailwind occurrences mapped · root cause `sm:` breakpoint + `gap-3/4` · Pass 2 §7 covers filter / stats / hub multi-col grids | ✅ ⛔ |
| `PLATFORM_FORM_GRID_FIX_CERTIFICATION.md` | **V.5 P0-1** · 69 mechanical replacements (Pass 1) + ~146 dense-grid migrations (Pass 2) + new shared `FormGrid.jsx` · zero business-logic change · regression suite green | ✅ ⛔ |
| `IPAD_LAYOUT_VALIDATION_REPORT.md` | **V.5 P0-1** · Pass-2 visual evidence at 390 / 820 / 1180 px viewports · 15-surface coverage matrix · center-seam check table · DR / Meeting / Equipment / QA-QC / HR / PO bleed eliminated | ✅ ⛔ |
| `FORM_SPACING_DOCTRINE.md` | **V.5 P0-1 doctrine** · canonical `grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4` (sparse 2-3 col) + `grid grid-cols-2 md:grid-cols-{4,5} gap-x-4 gap-y-3` (dense 4-5 col) · binding on every form on the platform | ✅ ⛔ |
| `LIVE_PORTAL_WORKFLOW_DEFECT_AUDIT.md` | **V.5 P0-2/3** · PM bounce + delete button + Shop Pre-Op buried + PO receipt blank-tab investigation · root-cause chain · permission matrix · before/after | ✅ ⛔ |
| `PM_PREOP_ROUTING_FIX_CERTIFICATION.md` | **V.5 P0-2A** · namespace-aware 401 interceptor + EquipmentDashboard portal context + PM scope on list endpoint · 3-link bug chain documented · curl + Playwright evidence | ✅ ⛔ |
| `PM_PREOP_PERMISSION_CERTIFICATION.md` | **V.5 P0-2B** · PM read-only doctrine · every visible action audited · Trash/New/Share/File-First hidden in PM context · permission matrix | ✅ ⛔ |
| `SHOP_PREOP_WORKFLOW_CERTIFICATION.md` | **V.5 P0-2C** · new `/shop/equipment` route + enabled Recent Pre-Op link · failed pre-ops remain first-screen via `OpenItemsPanel` · live testmech verification | ✅ ⛔ |
| `PO_ATTACHMENT_OPEN_FIX_CERTIFICATION.md` | **V.5 P0-3** · new `GET /api/po-requests/{po_id}/receipt` streaming endpoint · iPad-Safari-friendly Blob URL frontend · data-URL + R2-URL storage modes handled · curl matrix | ✅ ⛔ |
| `LIVE_USER_FACING_P0_CLOSEOUT_REPORT.md` | **V.5 P0-2/3 closeout** · operator's 10-check validation matrix · regression evidence · stop conditions honored · awaiting review before backup scheduler hardening | ✅ ⛔ |
| `PLATFORM_ROUTING_PERMISSION_AUDIT.md` | **V.5 Trust Restoration** · 249 frontend routes · 739 backend endpoints · portal namespace map · routing defects inventory (P0/P1/P2/P3) | ✅ ⛔ |
| `VISIBLE_ACTION_MATRIX.md` | **V.5 Trust Restoration** · 2 200 testIds audited · per-action permission + destination + render-gate matrix · P0 surfaces certified | ✅ ⛔ |
| `PORTAL_BOUNDARY_CERTIFICATION.md` | **V.5 Trust Restoration** · 401 interceptor namespace policy · cross-portal access matrix · login-destination correctness | ✅ ⛔ |
| `BROKEN_ROUTE_FIX_PLAN.md` | **V.5 Trust Restoration · NO IMPL** · 4 P0 fixed in preview · 3 P1 + 3 P2 + 5 test-only defects documented · net-state verdict | ✅ ⛔ |
| `PLATFORM_FLOW_NOTIFICATION_AUDIT.md` | **V.5 Trust Restoration** · two notification pipelines (auto-email + emit_task_and_notification) · per-workflow matrix · routing-config keys | ✅ ⛔ |
| `WORKFLOW_OWNERSHIP_MATRIX.md` | **V.5 Trust Restoration** · creator·owner·viewers·editors·delete authority·closer·no-response path for 30+ workflows | ✅ ⛔ |
| `ALERTING_AND_DESTINATION_MATRIX.md` | **V.5 Trust Restoration** · email/bell/task/dashboard destinations per workflow · dashboard inventory per hub · alert-staleness recovery | ✅ ⛔ |
| `DASHBOARD_DESTINATION_CERTIFICATION.md` | **V.5 Trust Restoration** · every record's proactive vs search-only surface · orphan-candidate flags · recommended dashboard additions | ✅ ⛔ |
| `NOTIFICATION_GAP_REGISTER.md` | **V.5 Trust Restoration** · 18-gap inventory · P0/P1/P2/P3 classification · operator decision pending | ✅ ⛔ |
| `FLOW_FIX_RECOMMENDATION_PLAN.md` | **V.5 Trust Restoration · NO IMPL** · staged α/β/γ/δ remediation plan · effort estimates · held items list | ✅ ⛔ |
| `ORPHAN_WORKFLOW_REPORT.md` | **V.5 Trust Restoration** · 1 confirmed P0 orphan candidate (Fleet DVIR) · 4 soft orphans · 17 validated complete chains · no-response paths inventory | ✅ ⛔ |
| `PLATFORM_TRUST_RESTORATION_AUDIT.md` | **V.5 Trust Restoration · master synthesis · READ FIRST** · 5 trust pillars · solid 80% · patchy 20% · decision tree | ✅ ⛔ |
| `APPROVAL_REJECTION_ARCHITECTURE.md` | **V.4 architecture** · full Daily Report lifecycle · 7 canonical states · state-transition contract · append-only `daily_report_review_events` schema · planned API + UI surface · hash continuity · NOT implemented | 📐 |
| `REPORT_LIFECYCLE_DOCTRINE.md` | **V.4 doctrine** · per-state mutability · limited revision-edit surface · version semantics · multi-reviewer contention · legacy DR projection · NOT implemented | 📐 |
| `FL_ROLE_MAPPING_RESOLUTION_REPORT.md` | **V.4 governance · supersedes LEGACY_ROLE_MAPPING_REVIEW on the resolution axis** · operator review table for the 4 uncertain mappings · approval authority allowlist · project-scope contract · fail-closed defaults | ✅ ⛔ |
| `APPROVAL_PERMISSION_MATRIX.md` | **V.4 governance** · full action × role matrix · `can_approve(actor, dr)` primitive · `If-Match` concurrency · 403/409 surfaces · UI capability primitive spec · NOT implemented | 📐 |
| `REJECTION_WORKFLOW_CERTIFICATION.md` | **V.4 governance** · reason catalog · server-enforced ≥ 8-char reason · foreman recovery flow · forbidden behaviors · cycle handling · Review History PDF appendix · NOT implemented | 📐 |
| `LOCKED_RECORD_GOVERNANCE.md` | **V.4 governance** · LOCKED_RECORD contract · final hash stamp · amendment workflow (new record · never mutates original) · external-auditor experience · NOT implemented | 📐 |
| `PRE_DEPLOY_RELIABILITY_GATE_CERTIFICATION.md` | **V.4 reliability pillar** · `pre_deploy_verify.py` Phase 1B integration · verdict semantics · run cadence · the only V.4 code change | ✅ ⛔ |
| `scripts/odr_public_link_continuity_probe.py` | 8-invariant continuity probe · sub-second · wired into pre_deploy_check.sh | ✅ |
| `scripts/odr_bilingual_probe.py` | 7-invariant bilingual probe · sub-second · wired into pre_deploy_check.sh | ✅ |
| `scripts/odr_reality_validation.py` | M0.35 · 4-scenario field reality harness · run pre-pilot | ✅ |
| `scripts/odr_completion_time_drift_probe.py` | **M0.4 advisory** · foreman ODR completion-time drift · target/stretch/ceiling thresholds · exit 0 always | ✅ advisory |
| `scripts/odr_simplicity_drift_probe.py` | **M0.4 advisory** · scans foreman surfaces for forbidden patterns · exit 0 always | ✅ advisory |
| `scripts/odr_inheritance_drift_probe.py` | **M0.4 advisory** · scans ODR pages for off-palette colors / non-shared imports · exit 0 always | ✅ advisory |
| `scripts/cross_portal_consistency_drift_probe.py` | **M0.4 advisory** · cross-portal component inheritance · exit 0 always | ✅ advisory |
| _(Future)_ `odr_doctrine_probe.py` | shape + enum + audit-envelope probe (planned for M1+) | 🟡 |

## 5 · Route Decomposition / Backend Architecture

How `server.py` is being split into `routes/`.

| File | Purpose | Status |
|---|---|---|
| `ROUTE_DECOMPOSITION_*.md` (if present) | Per-route extraction notes | ✅ |
| `ARCHITECTURAL_RISK_REDUCTION.md` | High-risk zones to defer | ✅ |
| `AUTH_CONSOLIDATION_PROGRESS.md` | Auth route extraction status | ✅ |
| _(See)_ `backend/routes/` directory | Live extracted routes | ✅ |
| _(See)_ `server.py` | Remaining monolith — still primary surface | ✅ ⛔ |

## 6 · Field / Mobile Doctrine

Superintendent + foreman + iPad rules.

| File | Purpose | Status |
|---|---|---|
| `FIELD_WALK_CHECKLISTS/FL.md` | Foreman walk | ✅ |
| `FIELD_WALK_CHECKLISTS/PM.md` | PM walk | ✅ |
| `FIELD_WALK_CHECKLISTS/Safety.md` | Safety walk | ✅ |
| `FIELD_WALK_CHECKLISTS/HR.md` | HR walk | ✅ |
| `FIELD_WALK_CHECKLISTS/MobileSafari.md` | iOS Safari walk | ✅ |
| `DAILY_REPORT_FIELD_TRUST_REVIEW.md` | Daily-report field doctrine | ✅ |
| `DAILY_REPORT_DEVICE_MEMORY_MODEL.md` | Crew memory + preload doctrine | ✅ ⛔ |
| `DATA_SURVIVABILITY_AUDIT.md` | TRUST-1 doctrine root | ✅ ⛔ |
| `MOBILE_UX_REFINEMENT_AUDIT.md` | V-Prelude mobile polish list | 📐 |

## 7 · Legal / Audit / Retention

Locked snapshots, soft-delete, archive doctrine, audit defensibility.

| File | Purpose | Status |
|---|---|---|
| `AUDIT_GUARDRAILS.md` | Audit-trail discipline | ✅ ⛔ |
| `DATA_PORTABILITY.md` | Export + retention rules | ✅ |
| _(See)_ TRUST-1 archive-on-delete behavior in `idbDraft.js` + Mongo soft-delete | ✅ |
| _(Future)_ `RFI_RETENTION.md` | Phase V.1+ · not yet drafted | 🟡 |
| _(Future)_ `EXTERNAL_ACCESS_AUDIT.md` | Phase V.2+ · not yet drafted | 🟡 |
| _(Future)_ `PDF_SHA256_FOOTER_STANDARD.md` | Phase V.1+ · not yet drafted | 🟡 |

---

## Cross-cutting "read before touching" list

- ⛔ `TIMESTAMP_UTILITY_STANDARD.md` — every timestamp surface
- ⛔ `OPERATIONAL_LINKING_RULES.md` — every cross-artifact link
- ⛔ `OPERATIONAL_TELEMETRY_DOCTRINE.md` — every new client/server event
- ⛔ `DATA_SURVIVABILITY_AUDIT.md` — every draft / queue / IDB change
- ⛔ `AUDIT_GUARDRAILS.md` — every change to records that may be referenced legally
- ⛔ `CROSS_PORTAL_COACHING_STANDARD.md` — every operator-facing copy change
- ⛔ `VISUAL_LOUDNESS_DOCTRINE.md` (or `CALM_OBSERVABILITY_UI.md`) — every color / pill / badge addition

---

## Where to find the live state

- 🟢 Live OPS-1 status: `GET /api/admin/governance/self-protection`
- 🟢 Probe state: `python3 scripts/authority_mismatch_probe.py --gate`
- 🟢 Timestamp probe: `python3 scripts/timestamp_doctrine_probe.py --gate`
- 🟢 Pre-deploy gate: `bash scripts/pre_deploy_check.sh`

---

_If a doc you need is not listed here, grep `/app/memory/` for the
topic — but document its addition to this index when you next
touch it. Goal: 500 docs · 1 map · 30 seconds._
 copy change
- ⛔ `VISUAL_LOUDNESS_DOCTRINE.md` (or `CALM_OBSERVABILITY_UI.md`) — every color / pill / badge addition

---

## Where to find the live state

- 🟢 Live OPS-1 status: `GET /api/admin/governance/self-protection`
- 🟢 Probe state: `python3 scripts/authority_mismatch_probe.py --gate`
- 🟢 Timestamp probe: `python3 scripts/timestamp_doctrine_probe.py --gate`
- 🟢 Pre-deploy gate: `bash scripts/pre_deploy_check.sh`

---

_If a doc you need is not listed here, grep `/app/memory/` for the
topic — but document its addition to this index when you next
touch it. Goal: 500 docs · 1 map · 30 seconds._
