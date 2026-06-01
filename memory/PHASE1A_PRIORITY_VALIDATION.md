# Phase 1A · Priority Validation

**Program:** OMEGA · Platform Completion Program · Phase 1A · Pre-Build Validation
**Mode:** READ-ONLY
**Companion:** `CRITICAL_FINDING_RANKING.md` · `PHASE1A_SCOPE_CHALLENGE_REPORT.md` · `CUSTOMER2_BLOCKER_MATRIX.md`
**Date:** 2026-06-01

---

## 1 · Answers to the 15 mandatory questions

### Q1 · Is Incident Lifecycle truly the #1 risk?

**YES.** Weighted score 39.5 — highest of all 22 findings. Compliance(3) + Safety(3) + Accountability(3) + CC(3) + WL(3) + C#2(3) + 90-day damage(3). OSHA recordable injuries that cannot be closed represent the most regulatorily exposed dead-end on the platform. Customer #2 cannot be onboarded with this defect present.

### Q2 · Is Daily Report Office Review truly Phase 1A?

**YES.** Score 34.0. Time Verification + Payroll Variance + accountability projections all build atop daily reports that have no "verified" signal. 150 DRs per week × 13 weeks = ~1,950 unverified records in a quarter. Sandy's payroll trust depends on this.

### Q3 · Is Payroll Variance Finalization truly Phase 1A?

**YES.** Score 34.0. The only platform workflow where the per-row decisions exist but the batch-level closure does NOT — a clear "starts but cannot finish" defect. Direct CFO visibility. 1 batch/week × 52 = 52/year accumulating in "open" state. P0.

### Q4 · Is QA/QC Follow-Up truly Phase 1A?

**YES (qualified).** Score 25.0. Lower frequency than OC-001/2/7 (3-5/wk) but the architectural pattern (inspection-level + per-item state) is shared with OC-004 Site Inspections. Building both in the same batch leverages design reuse. **Strong case for retention in Phase 1A.**

### Q5 · Is Site Inspection Follow-Up truly Phase 1A?

**YES.** Score 26.5. Same architectural family as QA/QC. Safety-domain. Already adjacent to OC-001 (Incidents). Logical grouping with QA/QC.

### Q6 · Should Employee Offboarding (OC-014) be elevated?

**NO.** Score 22.0 (rank #8). The offboarding multi-step checklist depends on **PPE Return** (OC-008, currently Phase 2) being built first — without PPE Return, the offboarding "return assets" checklist step has no surface to point at. Sequencing it Phase 1B / Phase 3 (after PPE Return ships in Phase 2) is correct. Elevating it now creates a dependency cycle.

### Q7 · Should JHA Acknowledgement Ledger (OC-005) be elevated?

**YES — RECOMMEND adding as Phase 1A.6.** Score 31.5 (rank #4). OSHA general-duty exposure. ~500 acknowledgements/wk (#3 frequency on platform). Build complexity is LOW (~3 engineer-days) because it's additive — no lifecycle state machine, just an acknowledgement ledger collection + signed endpoint + FL Hub surface. Including it in Phase 1A closes the OSHA-compliance loop alongside the OC-001 OSHA closure attestation. **Phase 1A scope grows from 5 → 6 workflows; build effort 8-12 days → 11-15 days.**

(See `PHASE1A_SCOPE_CHALLENGE_REPORT.md` §3 for the elevation rationale and §4 for the alternative "Phase 1A.5 dedicated mini-sprint" option.)

### Q8 · Should PPE Return (OC-008) be elevated?

**NO.** Score 14.5. PPE Return is operationally important but is a Phase 2 placeholder-elimination batch. PPE issuance happens at hiring; return happens at offboarding. Sequencing PPE Return with Employee Offboarding (Phase 3) keeps the natural workflow cohesive. The 90-day damage if ignored is bounded — PPE accountability gaps are recoverable; OSHA incident closure gaps are not.

### Q9 · Should Photo Janitor (OC-009) be elevated?

**NO.** Score 9.0 (rank #19). Cosmetic / storage hygiene. R2 has 92.38 GB and grows slowly. No operational dead-end. Phase 2 (placeholder elimination) is correct sequencing.

### Q10 · Should Status Vocabulary Canonicalization (OC-010) be elevated?

**NO — stays Phase 1B.** Score 31.0 but Phase 1A *is* the dress rehearsal for OC-010 (the 5-state canonical vocab is introduced in Phase 1A and rolled out to all 18 vocabs in Phase 1B). Elevating OC-010 into Phase 1A multiplies scope from 5 workflows to 18 workflows + 5 lifecycle remediations in one batch — unbuildable. **Confirmed correctly sequenced.**

### Q11 · Which finding causes greatest operational damage if ignored 90 days?

**Tier 1 — Direct operational damage (mission-impacting):**
1. **OC-001 Incidents** — OSHA closeout exposure for any recordable in window
2. **OC-007 Payroll Variance** — Sandy's reconciliation backlog · CFO visibility
3. **OC-002 Daily Reports** — ~1,950 unverified records cumulative

**Tier 2 — Cumulative damage (drifts but doesn't stop work):**
4. OC-005 JHAs — OSHA general-duty compliance ledger
5. OC-010 Vocab fragmentation — executive confusion + Customer #2 blocker

### Q12 · Which finding blocks Customer #2 readiness most?

**OC-001** — incident closure. Without it, a second tenant inherits a workflow that cannot complete. Followed by **OC-007** (payroll variance close) and **OC-005** (JHA OSHA ledger).

### Q13 · Which finding blocks White Label readiness most?

**OC-010** — vocab fragmentation. White Label requires deterministic workflow contracts per tenant. 18 vocabularies × N tenants = unmanageable. **OC-010 must be resolved before any White Label work** — and that's a Phase 1B blocker that gates the entire White Label initiative.

### Q14 · Which finding blocks ForgedOps Operations Center readiness most?

**OC-001, OC-002, OC-003, OC-004, OC-007 jointly.** The Ops Center will read workflow data; with these 5 workflows incomplete, it will display "stuck" or "missing data" cards as the dominant signal. Phase 1A unblocks this. Phase 1B (status canonicalization) further enables the Ops Center to display consistent labels.

### Q15 · If only FIVE findings could be fixed, which five and why?

In strict priority order:

1. **OC-001 Incident closure** — single highest-scoring finding (39.5); OSHA exposure; blocks Customer #2
2. **OC-007 Payroll Variance finalize** — Sandy's largest weekly friction; financial; weekly accumulation
3. **OC-002 Daily Report office review** — underpins #2 (Time Verification + Payroll Variance build atop DRs); 150/wk volume
4. **OC-005 JHA acknowledgement ledger** — OSHA general-duty compliance; highest-frequency safety acknowledgement; ~500/wk; build cost low
5. **OC-010 Vocab canonicalization** — blocks White Label and Customer #2; cross-cutting refactor; must follow Phase 1A's 5-state proof of concept

These 5 cover: 2 compliance (OC-001 + OC-005) · 2 payroll/financial (OC-002 + OC-007) · 1 cross-cutting (OC-010).

**OC-003 (QA/QC) and OC-004 (Site Inspections) are bumped out of the top 5** — they would be #6 and #7 in this constrained list. They remain in current Phase 1A scope but if forced to a 5-pick limit, the JHA + vocab elevations take priority.

---

## 2 · Final verdict

# 🟡 B · The current Phase 1A scope is INCOMPLETE.

The current 5-workflow Phase 1A scope is **correct in selecting OC-001, OC-002, OC-003, OC-004, OC-007**. **OC-005 (JHA Acknowledgement Ledger) should be elevated into Phase 1A** because:

* It scores **#4 of 22** on weighted impact (31.5)
* It is the **#1 frequency-of-use unaddressed safety workflow** (~500/week)
* It carries **direct OSHA general-duty exposure** (29 CFR 1926.21(b)(2))
* It is a **Customer #2 blocker** in parallel with OC-001
* Its build cost is **LOW relative to other Phase 1A items** (additive collection + endpoint + UI · no lifecycle state machine · ~3 engineer-days)
* It is **architecturally independent** of OC-010 vocab canonicalization
* It logically pairs with OC-001 (both are Safety-domain · both deal with OSHA evidence)

---

## 3 · Recommended Phase 1A scope (post-validation)

| Slot | Finding | Workflow | Effort | Rationale |
|---|---|---|---|---|
| 1 | OC-001 + OC-020 + OC-021 | Incident lifecycle (close + list filter + project health count) | 2.5 days | top-scoring finding · OSHA · Customer #2 blocker |
| 2 | OC-002 | Daily Report office review | 2 days | underpins Time Verification + Payroll · 150/wk |
| 3 | OC-007 | Payroll Variance batch finalize | 1.5 days | financial · weekly · Sandy's largest friction |
| 4 | OC-003 | QA/QC deficiency follow-up | 2 days | Phase 1A architectural family |
| 5 | OC-004 | Site Inspection follow-up | 1.5 days | Phase 1A architectural family · pair with OC-003 |
| 6 | **OC-005 (ELEVATED)** | JHA Acknowledgement Ledger | **3 days** | **OSHA general-duty · highest-frequency safety workflow · Customer #2 blocker · low build cost · this audit's elevation** |

**Total revised effort: ~12.5 engineer-days** (vs. original 8-12 days). 3-day delta is justified by closing the OSHA compliance loop in the same batch as OC-001's OSHA attestation gate.

**Total revised audit collection footprint:** 2 new collections — `workflow_state_events` (lifecycle audit) + `jha_acknowledgements` (acknowledgement ledger). Both ship with 7-year TTL aligned to OSHA + IRS retention.

---

## 4 · Phase 1B / Phase 2 / Phase 3 confirmed sequencing

| Phase | Findings | Rationale |
|---|---|---|
| **Phase 1B** | OC-010 (vocab) + OC-014 (offboarding multi-step) + OC-018 (audit-trail flag-only gaps) | After Phase 1A's 5-state vocab proves out · before Phase 2 placeholder work |
| **Phase 2** | OC-008 (PPE Return) + OC-009 (Photo Janitor) + OC-013 (onboarding multi-step) + OC-016 (continuity events) | Placeholders + multi-step lifecycles |
| **Phase 3** | OC-011 (FL Forms edit) + OC-012 (training renewal linkage) + OC-015 (time verification dispute) | Remaining 🟡 cleanup |
| **Phase 4** | OC-019 (casing normalization) + OC-022 (reopen support across additional workflows) + remaining 🟢 | Cosmetic / non-blocking |
| **NEVER (per directive)** | White Label · ForgedOps Operations Center · Escalation Framework | Frozen until 90% operational completeness |

---

## 5 · Operator decision required

Operator must choose ONE of:

* **DECISION A:** Accept revised Phase 1A scope (6 workflows incl. OC-005 JHA elevation). Build effort ~12.5 engineer-days. Recommended.
* **DECISION B:** Keep original Phase 1A scope (5 workflows). Add OC-005 JHA as immediate Phase 1A.5 mini-sprint after Phase 1A ships (3 engineer-days additional).
* **DECISION C:** Reject elevation. Keep original 5 workflows. Defer OC-005 JHA to Phase 2. (NOT recommended; OSHA exposure continues for 8-12 weeks.)
* **DECISION D:** Reduce scope. Drop OC-003 or OC-004 from Phase 1A and add OC-005 instead. (Loses architectural reuse between QA/QC and Site Inspections.)

---

## 6 · OMEGA discipline

🟢 Read-only · 15 mandatory questions answered with evidence · scope challenge issued · binary verdict reached (🟡 B · incomplete · elevate OC-005).

🛑 Continue to `PHASE1A_SCOPE_CHALLENGE_REPORT.md` for the formal challenge document and `CUSTOMER2_BLOCKER_MATRIX.md` for the second-customer impact view.
