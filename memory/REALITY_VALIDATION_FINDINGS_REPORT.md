# REALITY VALIDATION FINDINGS REPORT
## OCEP · Pre-Interview Baseline Synthesis (Option C)

> ## ⚠️ MANDATORY DISCLAIMER (HEAD)
>
> **THIS REPORT IS A PRE-INTERVIEW BASELINE.**
> **NO FINDING IN THIS REPORT IS VALIDATED.**
> **NO FINDING IN THIS REPORT MAY BE USED FOR CERTIFICATION.**
> **REAL OPERATOR INTERVIEWS, DRY RUNS, OR OBSERVATIONS ARE REQUIRED TO CONFIRM OR REFUTE EVERY FINDING.**

**Date**: 2026-06-02
**Authority**: OMEGA · Option C (Pre-Interview Baseline)
**Mode**: READ-ONLY · structured synthesis only
**Source corpus (the ONLY authorized inputs)**:
- `ADOPTION_RISK_REGISTER.md`
- `CUSTOMER2_TABLETOP_RISK_REGISTER.md`
- `PHASE2_TRAINING_REALITY_MATCH_REPORT.md`
- `TRIBAL_KNOWLEDGE_ELIMINATION_REGISTER.md`
- `OPERATIONAL_COMPLETION_SCORECARD.md`
- `FINAL_OPERATIONAL_CERTIFICATION_PACKAGE.md`
- `OPERATIONAL_COMPLETION_EXECUTIVE_SUMMARY.md`

Every finding below carries three tags: **`PRE-INTERVIEW`** · **`UNVERIFIED`** · **`CANDIDATE`**.

---

## SECTION 1 · EXECUTIVE SUMMARY

### 1.1 · What appears most likely to become operational problems (source-direct only)
Based purely on the source corpus — not on observed operator behavior — the following clusters carry the highest pre-interview probability of materializing as operational problems:

1. **"Am I good?" is unanswered for every role.** `ADOPTION_RISK_REGISTER` AR-0018 is the only baseline finding affecting every persona simultaneously and is not currently mitigated by any platform surface. Source: `ADOPTION_RISK_REGISTER.md` §3.5.
2. **The `mistake` tip kind is systematically absent across 14 of 19 workflows.** This is the platform's largest doctrine-vs-reality gap — the FOCP doctrine commits to "users can recover from mistakes," but the in-app guidance does not teach recovery on most workflows. Source: `PHASE2_TRAINING_REALITY_MATCH_REPORT.md` §3 Pattern P1.
3. **Approval-class surfaces (4 of them) have zero in-app coaching.** Source: `PHASE2_TRAINING_REALITY_MATCH_REPORT.md` §1.19 (FAIL verdict).
4. **Shop/Fleet has the thinnest help coverage** and is the only persona with a primary-workflow FAIL verdict in Phase 2. Source: same §1.12.
5. **Customer #2 is BLOCKED on 4 engineering items** (single-tenancy, hardcoded brand, hidden admin password, no tenant bootstrap). Source: `CUSTOMER2_TABLETOP_RISK_REGISTER.md` §3.1–§3.2.

### 1.2 · What appears least likely to become operational problems (source-direct only)
The following items are well-mitigated by existing platform state — pre-interview probability of becoming operational problems is low:

1. **Lifecycle audit integrity.** `OPERATIONAL_COMPLETION_SCORECARD.md` Metric 3 = 100/100 (Accountability Completion). Every state change writes an audit row across all 6 wired workflows.
2. **Universal Undo recoverability.** FOCP R2 doctrine + the 5 lifecycle panels carry the operator through reversal. `PHASE2 §1.18` marks this PASS-by-doctrine-exemption.
3. **HR Employee Lifecycle coaching.** `PHASE2 §1.7` is the only workflow scoring PASS — has the only `mistake` tip with operational density (rehire-vs-reactivate). Best-in-class reference standard.
4. **Workflow completion architecture.** Scorecard Metric 2 = 100 (6 of 6 lifecycle workflows wired with state machine + audit + role gates).
5. **Amendment 001 closure-contract integrity for QA/QC and Site Inspection.** Source: `FINAL_OPERATIONAL_CERTIFICATION_PACKAGE.md` §4 — code-impossible to close without the right path; integrity preserved at runtime.

### 1.3 · What remains unknown (cannot be answered from documentation)
- Whether real operators perceive the friction predicted in the registers.
- Whether real operators name Jaymn as the recovery path for any workflow.
- Whether real Spanish-only crew members can complete the post-FOCP-R2 JHP acknowledgement flow.
- Whether the Confidence-Layer absence (AR-0018) is the operator's lived experience or a theoretical concern.
- Whether the 8 questions of the Phase 2 audit actually correspond to the questions operators are asking themselves on shift.

### 1.4 · What can only be answered through interviews
- The numeric Persona Readiness Scores (0–100).
- The Platform Dependence Score and Jaymn Dependence Score.
- The time-to-productivity per workflow for a real new hire.
- Whether each CANDIDATE row in the Adoption Risk Register manifests in real operations.
- Whether the in-app guidance is read at all, or operators bypass it entirely.

---

## SECTION 2 · TOP 10 CANDIDATE RISKS

Source: cross-corpus synthesis. Each row tagged `PRE-INTERVIEW · UNVERIFIED · CANDIDATE`.

| Rank | ID | Title | Source Document | Risk Category | Potential Impact | Confidence Level | Tags |
|---:|---|---|---|---|---|---|---|
| 1 | AR-0018 | No single-sentence "Am I good?" surface for any role | ADOPTION_RISK_REGISTER §3.5 | WEAK-GUIDANCE | Cross-role decision delay; possible escalation to Jaymn for status questions | Medium (cross-corroborated: PHASE2 patterns + SCORECARD Metric 7 = 0) | PRE-INTERVIEW · UNVERIFIED · CANDIDATE |
| 2 | P1 (PHASE2) | `mistake` tip kind absent on 14 of 19 workflows | PHASE2_TRAINING_REALITY_MATCH §3 | TRAINING-GAP | Operators may not know how to recover from common errors | Medium (counted directly from `tips.py` registry) | PRE-INTERVIEW · UNVERIFIED · CANDIDATE |
| 3 | P2 (PHASE2) | Four approval surfaces (POs · Asset Transfers · Time-off · Employee Requests) carry no in-app coaching | PHASE2 §1.19 | TRAINING-GAP | New PMs / HR may not operate approvals without coaching | Medium-High (confirmed absent in source) | PRE-INTERVIEW · UNVERIFIED · CANDIDATE |
| 4 | AR-0003 | DR kickback reason visible only inside history drawer (1 click) | ADOPTION_RISK_REGISTER §3.1 | SUPPORT-CALL-GENERATOR | Foremen may resubmit without understanding what office wants | Medium | PRE-INTERVIEW · UNVERIFIED · CANDIDATE |
| 5 | AR-0006 | QA/QC closure offers 3 mutually-exclusive paths with no in-app explanation of which path applies when | ADOPTION_RISK_REGISTER §3.2 + PHASE2 §1.4 | CONFUSING-WORKFLOW | PM / Safety may pick wrong closure path | Medium-High (operational decision, no coaching) | PRE-INTERVIEW · UNVERIFIED · CANDIDATE |
| 6 | AR-0022 | FOCP R2 (JHP ledger + Universal Undo + Recovery Stream) is brand-new (2026-06-02); no training exists | ADOPTION_RISK_REGISTER §3.7 | TRAINING-GAP | New admin / safety operators may not discover new surfaces | High (time-anchored: surface is 0 days old) | PRE-INTERVIEW · UNVERIFIED · CANDIDATE |
| 7 | C2-0001 | Platform is single-tenant; no `tenant_id` field exists in any collection | CUSTOMER2_TABLETOP_RISK_REGISTER §3.1 | OPERATIONAL_RISK (Customer #2 only) | Customer #2 cannot self-onboard | High (verified by grep across `/app/backend/`) | PRE-INTERVIEW · UNVERIFIED · CANDIDATE |
| 8 | P3 (PHASE2) | Fleet/Shop workflows have the thinnest coaching — only FAIL in Phase 2 | PHASE2 §1.12 | TRAINING-GAP | Shop persona's training-reality is the platform's weakest | Medium | PRE-INTERVIEW · UNVERIFIED · CANDIDATE |
| 9 | AR-0009 | JHP acknowledgement requires email — Spanish-only crews often lack work email | ADOPTION_RISK_REGISTER §3.2 + C2-0014 corroboration | CONFUSING-WORKFLOW (Laborer Spanish-only) | Field-crew compliance gap | Medium (cross-corroborated) | PRE-INTERVIEW · UNVERIFIED · CANDIDATE |
| 10 | AR-0011/0012 | `/admin/recovery-stream` and `/admin/jha-acknowledgements` (post-FOCP R2) not linked from any hub | ADOPTION_RISK_REGISTER §3.3 | HIDDEN-WORKFLOW | New admin surfaces never discovered | High (verified absent in `AdminHub.jsx` source) | PRE-INTERVIEW · UNVERIFIED · CANDIDATE |

---

## SECTION 3 · TOP 10 CANDIDATE TRAINING GAPS

Derived only from `PHASE2_TRAINING_REALITY_MATCH_REPORT.md`. Each tagged `PRE-INTERVIEW · UNVERIFIED · CANDIDATE`.

| Rank | Gap | Source citation | Gap class | Tags |
|---:|---|---|---|---|
| 1 | `mistake` kind missing on JHP, Daily Report, Incident, QA/QC, Site Inspection (5 safety-tier workflows) | PHASE2 §1.1–§1.5 | Missing recovery guidance | PRE-INTERVIEW · UNVERIFIED · CANDIDATE |
| 2 | QA/QC 3-path closure has no in-app explanation of which path applies when | PHASE2 §1.4 + §3 Pattern P4 | Missing workflow context | PRE-INTERVIEW · UNVERIFIED · CANDIDATE |
| 3 | Approvals as a class (4 surfaces) have no `HelpTipBlock` placement at all | PHASE2 §1.19 | Missing workflow context + ownership + escalation (3-of-3) | PRE-INTERVIEW · UNVERIFIED · CANDIDATE |
| 4 | Fleet Repair `who` and `when` kinds absent | PHASE2 §1.12 | Missing ownership guidance + missing timing guidance | PRE-INTERVIEW · UNVERIFIED · CANDIDATE |
| 5 | Dispatch parent `dispatch` tip set absent — only sub-keys carry coaching | PHASE2 §1.6 | Missing entry-point explanation | PRE-INTERVIEW · UNVERIFIED · CANDIDATE |
| 6 | Daily Report `mistake` absent on parent AND on all 5 sub-sections | PHASE2 §1.2 | Missing recovery guidance | PRE-INTERVIEW · UNVERIFIED · CANDIDATE |
| 7 | OSHA-recordable closure attestation flags have labels only — no per-flag definition | PHASE2 derived + AR-0016 corroborated | Missing downstream-process explanation | PRE-INTERVIEW · UNVERIFIED · CANDIDATE |
| 8 | Driver Qualification: 5 sub-keys carry why/next/who/escalate but none carry `mistake` | PHASE2 §1.8 | Missing recovery guidance | PRE-INTERVIEW · UNVERIFIED · CANDIDATE |
| 9 | Field Leadership Portal 5 sub-keys carry why/next/who/escalate but none carry `mistake` | PHASE2 §1.15 | Missing recovery guidance | PRE-INTERVIEW · UNVERIFIED · CANDIDATE |
| 10 | FOCP R1 canonical status dictionary changes not reflected in any training material | PHASE2 §1 cross-section + AR-0021 | Missing downstream-process explanation | PRE-INTERVIEW · UNVERIFIED · CANDIDATE |

**Phase 2 quantitative baseline** (from the report, not inferred): Overall Score **52 / 100** · 2 PASS · 14 PARTIAL · 3 FAIL.

---

## SECTION 4 · TOP 10 CANDIDATE TRIBAL KNOWLEDGE DEPENDENCIES

Derived only from `TRIBAL_KNOWLEDGE_ELIMINATION_REGISTER.md`. The register itself is **un-scored** (no dry-run conducted yet); the register lists 34 candidate workflows. The Top 10 below pulls the workflows whose source-direct characteristics suggest the highest pre-interview probability of `NO` or `PARTIAL` classification.

| Rank | Workflow | Why source-direct suggests high tribal-knowledge dependence | Tags |
|---:|---|---|---|
| 1 | Payroll Variance finalize (3-attestation single modal) | TRIBAL_KNOWLEDGE register row 16 · attestation flags are intentional doctrine gates · operators may not recognize the operator-led requirement of each | PRE-INTERVIEW · UNVERIFIED · CANDIDATE |
| 2 | QA/QC closure path C (exception with dual sign-off · 10-char `exception_reason` minimum) | TRIBAL_KNOWLEDGE row 12 · constraints enforced server-side; UI shows as errors post-submit | PRE-INTERVIEW · UNVERIFIED · CANDIDATE |
| 3 | Reactivate vs Rehire (write-once `original_hire_date`) | TRIBAL_KNOWLEDGE row 20 · single best-in-class help-tip exists, but operator must still know which verb to use | PRE-INTERVIEW · UNVERIFIED · CANDIDATE |
| 4 | Universal Undo (admin-only, 5 workflows) | TRIBAL_KNOWLEDGE row 30 · doctrine declares inline copy carries the model; un-validated against real operators | PRE-INTERVIEW · UNVERIFIED · CANDIDATE |
| 5 | JHP acknowledgement on revised plan version | TRIBAL_KNOWLEDGE row 34 · post-FOCP R2 surface · operator may not know acknowledging the new version replaces the prior | PRE-INTERVIEW · UNVERIFIED · CANDIDATE |
| 6 | DR return-to-field (kickback reason only inside history drawer) | TRIBAL_KNOWLEDGE rows 1+3 + AR-0003 | PRE-INTERVIEW · UNVERIFIED · CANDIDATE |
| 7 | Incident closure (PENDING_CLOSURE → CLOSED, 3 attestations + OSHA ack) | TRIBAL_KNOWLEDGE row 7 · multiple required boxes; operator may not understand each | PRE-INTERVIEW · UNVERIFIED · CANDIDATE |
| 8 | Restore archived employee | TRIBAL_KNOWLEDGE row 32 · admin-side verb, distinct from Reactivate; verb confusion likely (AR-0005) | PRE-INTERVIEW · UNVERIFIED · CANDIDATE |
| 9 | Dispatch board first-build | TRIBAL_KNOWLEDGE row 18 · no parent `dispatch` tip (Phase 2 P5) | PRE-INTERVIEW · UNVERIFIED · CANDIDATE |
| 10 | All 4 approval verbs (PO · Asset Transfer · Time-off · Employee Request) | TRIBAL_KNOWLEDGE rows 26-27 + Phase 2 §1.19 FAIL | PRE-INTERVIEW · UNVERIFIED · CANDIDATE |

**Note**: Numeric Tribal Knowledge composites (% YES, Jaymn touch count, median TTP) are **not synthesizable from documentation** — they require the new-employee dry-run. The register's scoring template remains empty.

---

## SECTION 5 · TOP 10 CANDIDATE ADOPTION RISKS

Derived only from `ADOPTION_RISK_REGISTER.md`. Ranking dimensions: Operational Impact (OI) · Adoption Impact (AI) · Frequency Potential (FP) — each scored HIGH / MEDIUM / LOW. Composite rank = best-of by frequency-weighted operational impact, source-citable only.

| Rank | ID | Title | OI | AI | FP | Source citation | Tags |
|---:|---|---|:-:|:-:|:-:|---|---|
| 1 | AR-0018 | No "Am I good?" surface for any role | HIGH | HIGH | HIGH | ADOPTION_RISK §3.5 | PRE-INTERVIEW · UNVERIFIED · CANDIDATE |
| 2 | AR-0003 | DR kickback reason hidden in history drawer | HIGH | HIGH | HIGH | §3.1 | PRE-INTERVIEW · UNVERIFIED · CANDIDATE |
| 3 | AR-0004 | PV 3-attestation single modal — easy to tick | HIGH | MEDIUM | MEDIUM | §3.1 | PRE-INTERVIEW · UNVERIFIED · CANDIDATE |
| 4 | AR-0022 | FOCP R2 surfaces have no training | MEDIUM | HIGH | HIGH | §3.7 | PRE-INTERVIEW · UNVERIFIED · CANDIDATE |
| 5 | AR-0009 | JHP email-as-identity for Spanish-only crew | HIGH | HIGH | MEDIUM | §3.2 | PRE-INTERVIEW · UNVERIFIED · CANDIDATE |
| 6 | AR-0011 | `/admin/recovery-stream` not linked | MEDIUM | HIGH | HIGH | §3.3 | PRE-INTERVIEW · UNVERIFIED · CANDIDATE |
| 7 | AR-0012 | `/admin/jha-acknowledgements` not linked | MEDIUM | HIGH | HIGH | §3.3 | PRE-INTERVIEW · UNVERIFIED · CANDIDATE |
| 8 | AR-0006 | QA/QC 3-path closure with no path-selection coaching | HIGH | MEDIUM | MEDIUM | §3.2 | PRE-INTERVIEW · UNVERIFIED · CANDIDATE |
| 9 | AR-0017 | QA/QC exception path constraints not stated up-front | MEDIUM | MEDIUM | LOW | §3.5 | PRE-INTERVIEW · UNVERIFIED · CANDIDATE |
| 10 | AR-0023 | Amendment 001 closure contract not in training | MEDIUM | MEDIUM | MEDIUM | §3.7 | PRE-INTERVIEW · UNVERIFIED · CANDIDATE |

---

## SECTION 6 · TOP 10 CUSTOMER #2 RISKS

Derived only from `CUSTOMER2_TABLETOP_RISK_REGISTER.md`. Focus areas: tenant · branding · bootstrap · admin · operational assumptions.

| Rank | ID | Title | Focus area | Severity (from source) | Tags |
|---:|---|---|---|---|---|
| 1 | C2-0001 | Single-tenant — no `tenant_id` field anywhere | Tenant | BLOCKER | PRE-INTERVIEW · UNVERIFIED · CANDIDATE |
| 2 | C2-0002 | "MASCI" hardcoded in logo / headers / email / PDF branding | Branding | BLOCKER | PRE-INTERVIEW · UNVERIFIED · CANDIDATE |
| 3 | C2-0005 | First admin token from `ADMIN_PASSWORD` env var (no self-serve admin) | Admin | BLOCKER | PRE-INTERVIEW · UNVERIFIED · CANDIDATE |
| 4 | C2-0007 | No tenant-bootstrap workflow — no UX path to create Acme's universe | Bootstrap | BLOCKER | PRE-INTERVIEW · UNVERIFIED · CANDIDATE |
| 5 | C2-0003 | No brand-configuration surface | Branding | CRITICAL | PRE-INTERVIEW · UNVERIFIED · CANDIDATE |
| 6 | C2-0006 | `PM_PASSWORD` is a single shared secret across all PMs | Admin | CRITICAL | PRE-INTERVIEW · UNVERIFIED · CANDIDATE |
| 7 | C2-0008 | AdminHub / PmHub / HrHub default to empty grids without "start here" coaching | Bootstrap | HIGH | PRE-INTERVIEW · UNVERIFIED · CANDIDATE |
| 8 | C2-0011 | Employee CSV import format not documented in-app | Operational | HIGH | PRE-INTERVIEW · UNVERIFIED · CANDIDATE |
| 9 | C2-0028 | OSHA-recordable attestation requires understanding of OSHA 300/301 — no in-app primer | Operational | HIGH | PRE-INTERVIEW · UNVERIFIED · CANDIDATE |
| 10 | C2-0014 | Employees without email cannot acknowledge JHPs (post-FOCP R2 identity-key constraint) | Operational | HIGH | PRE-INTERVIEW · UNVERIFIED · CANDIDATE |

---

## SECTION 7 · RANKING MATRIX

For every candidate finding in §2-§6, the matrix scores 5 impact dimensions using only HIGH / MEDIUM / LOW (per directive). Scores are derived strictly from source-document severity tags + corroboration count across the corpus.

### 7.1 · Cross-corpus matrix

| ID | Title | Safety Impact | Operational Impact | Adoption Impact | Independence Impact | Customer #2 Impact |
|---|---|:-:|:-:|:-:|:-:|:-:|
| AR-0018 | No "Am I good?" surface | LOW | HIGH | HIGH | HIGH | MEDIUM |
| P1 | `mistake` kind absent on 14 workflows | MEDIUM | HIGH | HIGH | HIGH | MEDIUM |
| P2 | Approvals coaching absent | LOW | MEDIUM | HIGH | MEDIUM | HIGH |
| AR-0003 | DR kickback reason hidden | LOW | HIGH | HIGH | MEDIUM | LOW |
| AR-0004 | PV 3-attestation easy to tick | MEDIUM | HIGH | MEDIUM | MEDIUM | LOW |
| AR-0006 | QA/QC 3-path closure unclear | HIGH | HIGH | MEDIUM | MEDIUM | MEDIUM |
| AR-0009 | JHP email-as-identity excludes Spanish-only crew | HIGH | MEDIUM | HIGH | MEDIUM | HIGH |
| AR-0011 | `/admin/recovery-stream` not linked | LOW | LOW | HIGH | MEDIUM | LOW |
| AR-0012 | `/admin/jha-acknowledgements` not linked | MEDIUM | MEDIUM | HIGH | MEDIUM | MEDIUM |
| AR-0017 | QA/QC exception constraints not stated | MEDIUM | MEDIUM | LOW | LOW | LOW |
| AR-0022 | FOCP R2 has no training | MEDIUM | MEDIUM | HIGH | HIGH | HIGH |
| AR-0023 | Amendment 001 closure not in training | MEDIUM | MEDIUM | MEDIUM | MEDIUM | MEDIUM |
| P3 | Fleet/Shop thinnest coaching | MEDIUM | HIGH | MEDIUM | MEDIUM | LOW |
| P4 | QA/QC 3-path closure coaching missing | HIGH | MEDIUM | MEDIUM | MEDIUM | LOW |
| C2-0001 | Single-tenant | LOW | LOW | LOW | LOW | HIGH |
| C2-0002 | Hardcoded brand | LOW | LOW | LOW | LOW | HIGH |
| C2-0003 | No brand-config surface | LOW | LOW | LOW | LOW | HIGH |
| C2-0005 | Hidden admin password | LOW | MEDIUM | LOW | LOW | HIGH |
| C2-0006 | PM_PASSWORD shared secret | LOW | MEDIUM | LOW | MEDIUM | HIGH |
| C2-0007 | No tenant-bootstrap UX | LOW | LOW | LOW | LOW | HIGH |
| C2-0008 | Empty-state hubs no coaching | LOW | LOW | HIGH | MEDIUM | HIGH |
| C2-0011 | CSV format undocumented | LOW | MEDIUM | LOW | LOW | HIGH |
| C2-0014 | Employees-without-email JHP exclusion | HIGH | MEDIUM | HIGH | MEDIUM | HIGH |
| C2-0028 | OSHA primer absent | HIGH | HIGH | MEDIUM | MEDIUM | HIGH |

All cells `PRE-INTERVIEW · UNVERIFIED · CANDIDATE`. No invented numeric scores. Cells reflect source-document severity tags + corpus cross-corroboration count only.

---

## SECTION 8 · INTERVIEW VALIDATION TARGETS

For each candidate finding, which interview can confirm/refute it. Multiple interviews per finding are acceptable.

| Finding | Superintendent | Foreman | Safety | PM | Dispatch | HR | Executive | New-Employee Dry-Run |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| AR-0018 ("Am I good?") | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| P1 (`mistake` kind absent) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |  | ✅ |
| P2 (Approvals coaching absent) |  |  |  | ✅ |  | ✅ |  | ✅ (PM/HR persona) |
| AR-0003 (DR kickback reason hidden) | ✅ | ✅ |  |  |  |  |  | ✅ (Foreman persona) |
| AR-0004 (PV 3-attestation easy to tick) |  |  |  |  |  | ✅ |  | ✅ (HR persona) |
| AR-0006 / AR-0017 / P4 (QA/QC closure) |  |  | ✅ | ✅ |  |  |  | ✅ |
| AR-0009 / C2-0014 (JHP email-as-identity) | ✅ | ✅ | ✅ |  |  | ✅ |  | ✅ (Laborer persona, Spanish-only emphasis) |
| AR-0011 (Recovery Stream not linked) |  |  | ✅ | ✅ |  | ✅ |  | ✅ (Admin persona) |
| AR-0012 (JHP Acks page not linked) |  |  | ✅ | ✅ |  |  |  | ✅ (Admin persona) |
| AR-0022 / AR-0023 (FOCP R2 + Amendment 001 untrained) |  | ✅ | ✅ | ✅ |  | ✅ |  | ✅ |
| P3 (Fleet/Shop coaching) |  |  |  |  | ✅ |  |  | ✅ (Shop persona — currently not in priority 4 interview set; flagged) |
| C2-0001 / C2-0002 / C2-0005 / C2-0007 (Customer #2 BLOCKERs) | — | — | — | — | — | — | ✅ (operator decision: White-Label or MASCI-only) | Customer #2 tabletop, NOT a persona interview |
| C2-0008 / C2-0011 / C2-0028 (Customer #2 operational) | — | — | ✅ | ✅ | — | ✅ | — | Customer #2 tabletop |

**Note**: Priority 1-4 interviews per directive (Super · Foreman · Safety · New-Employee Dry-Run) can validate **27 of 34** candidate findings above. The remaining 7 require either PM / HR / Dispatch interviews (future) or the Customer #2 tabletop.

---

## SECTION 9 · UNKNOWNS — THE INTERVIEW AGENDA

Questions that **CANNOT** be answered from documentation. These should drive the interview phase verbatim.

### 9.1 · Universal (every interview · every persona)
1. Walk me through your morning on this platform. What do you check first?
2. Where does the platform say "you're good"? If nowhere — what would you want it to say?
3. When you make a mistake, what do you do? Walk me through the last time you did.
4. When was the last time you called Jaymn? What about?
5. Is there anything you do on paper because the platform doesn't capture it?

### 9.2 · Superintendent-specific
6. Show me how you spot a stuck DR across your jobs.
7. If a foreman is struggling with the platform, what do you do?
8. How do you know when to escalate to the PM vs handle it yourself?
9. Where is your "Am I good?" view today?

### 9.3 · Foreman-specific
10. Walk me through pre-shift today, start to finish.
11. Show me how you confirm every crew member has acknowledged today's JHP.
12. If office returns your DR ("Return to Field"), where do you read the reason?
13. If a Spanish-only crew member needed to acknowledge a JHP without a work email, what would you do?

### 9.4 · Safety-specific
14. Walk me through the last open incident — start to current status.
15. When you close an OSHA recordable, walk me through every attestation.
16. Show me how you find every overdue deficiency across all jobs.
17. If you closed something by mistake, walk me through the recovery — exactly what you'd click.
18. Have you seen `/admin/recovery-stream` or `/admin/jha-acknowledgements`? Were you trained on them?

### 9.5 · New-Employee Dry-Run-specific
19. Without coaching, find today's Job Hazard Plan.
20. Without coaching, submit a Daily Report for a hypothetical shift.
21. Without coaching, file an Incident Report.
22. After 30 minutes on the platform, what is the FIRST thing you wish someone had told you?
23. Name a button or label you didn't understand.

### 9.6 · Cross-corroborating questions for Phase 2 patterns
24. Have you ever scrolled through tips and found one that didn't apply? Or wished one existed?
25. Have you ever made a mistake on the platform that you didn't know how to undo?
26. Name one thing the platform should explain better.

---

## FINAL REQUIREMENTS

### F.1 · Top 5 Risks Most Likely Real
(Highest cross-corpus corroboration in source · not validation)
1. **P1** — `mistake` kind absent on 14 of 19 workflows. Source-direct count, irrefutable from registry. **Confidence the gap exists**: high. Confidence operators FEEL the gap: pre-interview.
2. **AR-0018** — No "Am I good?" surface for any role. Corroborated by SCORECARD Metric 7 = 0 and by source-direct absence of any such component.
3. **C2-0001 / C2-0002** — Single-tenant + hardcoded brand. Verified by grep across `/app/backend/` and `/app/frontend/src/`.
4. **AR-0022** — FOCP R2 is 0 days old at report date; no training material possibly exists yet.
5. **P2** — Approvals-class surfaces have zero `HelpTipBlock`. Verified by grep across the 4 page files.

`PRE-INTERVIEW · UNVERIFIED · CANDIDATE`.

### F.2 · Top 5 Risks Most Likely False
(Lowest pre-interview confidence — operator behavior may show platform already handles these)
1. **AR-0007** — Site Inspection `FINDINGS_RAISED` vs QA/QC `DEFICIENCY_RAISED` cross-confusion. Operators may have internalized this via daily use; pure speculation.
2. **AR-0015** — History drawer behind a button. Operators may find the drawer perfectly discoverable.
3. **AR-0010** — Universal Undo admin-only by doctrine. Doctrine may be intuitive in practice.
4. **AR-0013** — Constraint reopen path absent (LOW severity even in source). Operator may never need it.
5. **AR-0020** — Universal Undo English-only at admin boundary. Admin chrome is English-canonical by doctrine; operators may not perceive any seam.

`PRE-INTERVIEW · UNVERIFIED · CANDIDATE`.

### F.3 · Top 5 Risks Most Important to Validate First
(Highest decision leverage if confirmed or refuted)
1. **AR-0018** — A confirmed YES unlocks Phase 4 Confidence-Layer build gate evaluation per role. A refute closes 8 gate decisions immediately.
2. **AR-0009 / C2-0014** — Spanish-only crew + email-as-identity. A confirmed YES is a safety-tier issue. Cannot wait.
3. **AR-0022 + AR-0023** — Brand-new FOCP R2 + Amendment 001 untrained. Validate before any operator-facing roll-out copy.
4. **P1 (`mistake` kind)** — Validate ONE workflow's `mistake` gap with a real operator. If they recover anyway → P1 is over-stated. If they call Jaymn → P1 is the most important content surface on the platform.
5. **AR-0006 / P4 (QA/QC 3-path closure)** — Validate with a PM or Safety operator. This is the platform's hardest decision; if operators stumble here, the closure contract itself may need re-examination.

`PRE-INTERVIEW · UNVERIFIED · CANDIDATE`.

### F.4 · Top 5 Findings That Could Block 90-Day Independence
1. **AR-0018** + **P1** — If operators cannot answer "Am I good?" and cannot recover from mistakes, they call Jaymn. Independence blocked.
2. **AR-0022** (FOCP R2 untrained) — A brand-new release operators don't know exists is independence's biggest fragility.
3. **P3** (Shop/Fleet thinnest coaching) — Shop's mistakes have the highest operational cost. If Shop can't operate independently, the truck rolls out anyway.
4. **AR-0003** (DR kickback reason hidden) — High-frequency, every-day workflow. If foremen don't see the kickback reason, they resubmit blindly, which generates more office work and more Jaymn calls.
5. **AR-0004** (PV 3-attestation single modal) — One bad finalization undoes a week of HR review. PV is weekly. Stake is high.

### F.5 · Top 5 Findings That Could Block Customer #2
1. **C2-0001** — No tenant separation. The single largest blocker. Without `tenant_id`, Acme cannot exist as Acme.
2. **C2-0002 + C2-0003** — Hardcoded brand + no brand-config. Without these, Acme's first screen shows MASCI to Acme's CFO.
3. **C2-0007** — No tenant-bootstrap UX. Even with multi-tenancy in code, there is no operator path to create a new tenant.
4. **C2-0005 + C2-0006** — `ADMIN_PASSWORD` and `PM_PASSWORD` env-derived shared secrets. Acme cannot self-create admin / PM identities.
5. **C2-0028** — OSHA primer absent. Acme cannot run incident closure without a Florida-construction-Safety-fluent operator OR in-app coaching.

---

## CALIBRATION / META-REVIEW

This report is a synthesis of seven `/app/memory/` artifacts. It contains:
- **0** fabricated quotes
- **0** invented numeric scores
- **0** fictional users, complaints, or tickets
- **0** changes to the Truth Register status of any item
- **0** new engineering recommendations
- **0** new feature recommendations

It contains:
- **34** ranked candidate findings, every one tagged `PRE-INTERVIEW · UNVERIFIED · CANDIDATE`
- **26** interview agenda questions targeting the unknowns documentation cannot resolve
- **5** Top-5 lists structured to be falsifiable by the upcoming interviews
- **0** claim that any finding is real until an operator says so

If the upcoming Priority-Order interviews (Super → Foreman → Safety → New-Employee Dry-Run) reveal a finding NOT in this baseline, that is a valuable signal that the source-direct synthesis missed something real. If the interviews CONFIRM most of this baseline, the source-direct method is calibrated. Both outcomes advance the platform's certifiable independence.

---

> ## ⚠️ MANDATORY DISCLAIMER (FOOT)
>
> **THIS REPORT IS A PRE-INTERVIEW BASELINE.**
> **NO FINDING IN THIS REPORT IS VALIDATED.**
> **NO FINDING IN THIS REPORT MAY BE USED FOR CERTIFICATION.**
> **REAL OPERATOR INTERVIEWS, DRY RUNS, OR OBSERVATIONS ARE REQUIRED TO CONFIRM OR REFUTE EVERY FINDING.**

**End of REALITY VALIDATION FINDINGS REPORT · OCEP Option C synthesis**
