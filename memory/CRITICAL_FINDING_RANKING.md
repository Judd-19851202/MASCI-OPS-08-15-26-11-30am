# Critical Finding Ranking · OMEGA Pre-Build Validation

**Program:** OMEGA · Platform Completion Program · Phase 1A · Pre-Build Validation
**Mode:** READ-ONLY · priority validation only · no new feature discovery
**Source:** `OPERATIONAL_COMPLETENESS_REGISTER.md` (22 findings · OC-001..OC-022) · `USER_TASK_COMPLETION_AUDIT.md` · `CLOSURE_PATH_AUDIT.md` · `STATUS_VOCABULARY_AUDIT.md` · `ROLE_ACTIONABILITY_MATRIX.md`
**Date:** 2026-06-01

---

## 1 · Method

Each of the 22 register findings is re-scored on 13 impact axes (compliance · safety · payroll · financial · customer · operational · accountability · CC · WL · C#2 · frequency · severity · 90-day damage if ignored). The scores roll up to a single Priority verdict:

* **P0** = Must be in Phase 1A (mission-critical dead-end OR top-tier compliance gap OR daily payroll blocker)
* **P1** = Must be Phase 1B (status canonicalization or cross-cutting refactor)
* **P2** = Phase 2 (placeholder elimination or multi-step lifecycle)
* **P3** = Future (cosmetic / low-frequency / safe to defer)

Scoring rubric per axis: 0 = no impact · 1 = minor · 2 = important · 3 = critical. Composite priority weighted toward: compliance(×2) · payroll(×2) · safety(×2) · operational frequency(×1.5) · 90-day damage(×1.5) · others ×1.

---

## 2 · Per-finding rescoring (22 rows)

### Legend
* OC-### = finding ID from the Operational Completeness Register
* Total = weighted sum (max ~50 for highest possible severity)

| ID | Workflow | Comp | Safe | Pay | Fin | Cust | Op | Acc | CC | WL | C#2 | Freq | Sev | 90d | Total | Priority |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| OC-001 | Incident closure | 3 | 3 | 0 | 1 | 1 | 2 | 3 | 3 | 3 | 3 | 1 | 3 | 3 | **39.5** | **P0** |
| OC-002 | Daily Report office review | 1 | 1 | 3 | 2 | 1 | 3 | 1 | 1 | 2 | 3 | 3 | 2 | 3 | **34.0** | **P0** |
| OC-003 | QA/QC deficiency follow-up | 1 | 2 | 0 | 2 | 2 | 2 | 1 | 1 | 1 | 2 | 1 | 2 | 2 | **25.0** | **P0** |
| OC-004 | Site Inspection follow-up | 2 | 3 | 0 | 1 | 1 | 2 | 1 | 1 | 1 | 2 | 1 | 2 | 2 | **26.5** | **P0** |
| OC-005 | JHA acknowledgement ledger | 3 | 3 | 0 | 1 | 1 | 1 | 1 | 1 | 2 | 3 | 3 | 3 | 2 | **31.5** | **P1**¹ |
| OC-006 | Safety Meeting amend | 1 | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 1 | 1 | 1 | 1 | 1 | **10.0** | **P3** |
| OC-007 | Payroll Variance batch finalize | 1 | 0 | 3 | 3 | 1 | 3 | 1 | 1 | 1 | 2 | 3 | 3 | 3 | **34.0** | **P0** |
| OC-008 | PPE Return | 2 | 1 | 0 | 1 | 0 | 1 | 0 | 0 | 1 | 1 | 1 | 2 | 1 | **14.5** | **P2** |
| OC-009 | Photo Janitor / orphan cleanup | 0 | 0 | 0 | 1 | 0 | 1 | 0 | 0 | 1 | 1 | 1 | 1 | 1 | **9.0** | **P2** |
| OC-010 | Status Vocabulary fragmentation | 1 | 1 | 1 | 1 | 1 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 2 | **31.0** | **P1**² |
| OC-011 | FL Forms post-submit edit | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 1 | 1 | 1 | **7.5** | **P3** |
| OC-012 | Safety Training renewal linkage | 2 | 2 | 0 | 0 | 0 | 1 | 1 | 1 | 1 | 1 | 2 | 1 | 2 | **17.0** | **P2** |
| OC-013 | Employee Onboarding multi-step | 1 | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 1 | 2 | 2 | 1 | 1 | **15.0** | **P2** |
| OC-014 | Employee Offboarding multi-step | 2 | 1 | 2 | 2 | 1 | 1 | 1 | 0 | 1 | 2 | 1 | 2 | 2 | **22.0** | **P1**³ |
| OC-015 | Time Verification dispute/resolve | 0 | 0 | 2 | 1 | 0 | 1 | 1 | 0 | 1 | 1 | 2 | 1 | 1 | **15.0** | **P2** |
| OC-016 | Continuity Events edit/close | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 1 | 1 | **5.5** | **P3** |
| OC-017 | Safety digest fire surface friction | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | **1.5** | **P3** |
| OC-018 | Audit-trail flag-only gaps (11 workflows) | 1 | 1 | 0 | 1 | 1 | 1 | 2 | 1 | 2 | 2 | 1 | 1 | 1 | **17.5** | **P2** |
| OC-019 | Casing inconsistency | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 1 | 1 | 1 | 0 | 0 | 0 | **5.0** | **P3** |
| OC-020 | Incidents list filter bug (Open everywhere) | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 0 | 0 | 1 | 1 | 1 | **6.0** | bundled w/ **P0** OC-001 |
| OC-021 | Project Health unbounded count | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 0 | 0 | 1 | 1 | 1 | **6.0** | bundled w/ **P0** OC-001 |
| OC-022 | Reopen action gap (17 workflows) | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 1 | 1 | 1 | 1 | **8.5** | bundled w/ **P0** Phase 1A (reopen included by design) |

¹ OC-005 (JHA acknowledgement) scores 31.5 — within striking distance of the top-tier P0 finds. See §3.2 for the case to elevate vs. defer.
² OC-010 (vocab fragmentation) scores 31.0 — cross-cutting refactor. Best-handled as Phase 1B because Phase 1A is its dress rehearsal.
³ OC-014 (offboarding) scores 22.0 — important but the PPE Return + access-deactivation pieces require Phase 2 placeholder eliminations to be built first.

---

## 3 · Top 10 ranking

| Rank | ID | Workflow | Total | Initial Phase 1A? | Final priority |
|---|---|---|---|---|---|
| 1 | OC-001 | Incident closure | 39.5 | ✅ | **P0 · Phase 1A** |
| 2 | OC-002 | Daily Report office review | 34.0 | ✅ | **P0 · Phase 1A** |
| 3 | OC-007 | Payroll Variance batch finalize | 34.0 | ✅ | **P0 · Phase 1A** |
| 4 | OC-005 | JHA acknowledgement ledger | 31.5 | ❌ (currently P2) | 🟡 **CONSIDER elevation** — see §3.2 |
| 5 | OC-010 | Status Vocabulary fragmentation | 31.0 | ❌ (Phase 1B by directive) | **P1 · Phase 1B (correctly placed)** |
| 6 | OC-004 | Site Inspection follow-up | 26.5 | ✅ | **P0 · Phase 1A** |
| 7 | OC-003 | QA/QC deficiency follow-up | 25.0 | ✅ | **P0 · Phase 1A** |
| 8 | OC-014 | Employee Offboarding multi-step | 22.0 | ❌ | **P1 · Phase 1B (after PPE Return in Phase 2)** |
| 9 | OC-018 | Audit-trail flag-only gaps | 17.5 | ❌ | **P2 · Phase 4** |
| 10 | OC-012 | Safety Training renewal linkage | 17.0 | ❌ | **P2 · Phase 3** |

The current Phase 1A scope (OC-001, OC-002, OC-007, OC-004, OC-003) holds 5 of the top 7 spots. The two top-7 contenders NOT in current Phase 1A are OC-005 (JHA acknowledgement) and OC-010 (vocab fragmentation).

---

## 3.1 · Case for OC-010 in Phase 1B (NOT Phase 1A)

OC-010 (vocab fragmentation) scores 31.0 but is correctly placed in Phase 1B because:

1. **Phase 1A IS the dress rehearsal for OC-010.** The 5-state canonical vocab (`OPEN · IN_PROGRESS · PENDING_REVIEW · PENDING_CLOSURE · CLOSED`) introduced in Phase 1A is the schema Phase 1B will roll out to the remaining 13 workflows.
2. **Elevating OC-010 into Phase 1A would multiply scope.** Five workflow lifecycles + thirteen status canonicalizations = unbuildable in one batch.
3. **Phase 1A's `workflow_state_events` collection is the chassis** Phase 1B inherits. Building Phase 1A first establishes the audit pattern.

Verdict: **OC-010 stays Phase 1B. Confirmed correctly sequenced.**

## 3.2 · Case for OC-005 (JHA acknowledgement)

OC-005 scores 31.5 — within ~3 % of OC-002 and OC-007. Detailed examination:

| Dimension | Detail |
|---|---|
| Compliance impact | OSHA 1926.21(b)(2) requires employer to "instruct each employee in the recognition and avoidance of unsafe conditions" — JHA acknowledgement is the documentation of that instruction. **HIGH.** |
| Safety impact | Daily JHA acknowledgement by crew is a leading indicator. Missing acknowledgement ledger doesn't stop work but eliminates audit evidence. **HIGH.** |
| Frequency | 1-2 per project per day · ~500 acknowledgements/week at MASCI's current pace. **HIGH.** |
| 90-day damage if ignored | Continued OSHA exposure. Audit trail missing for crew-level acknowledgement. **HIGH.** |
| Operational coupling | JHA library already exists. Acknowledgement is purely additive · doesn't require lifecycle state machine. **MODERATE.** |
| Build complexity vs Phase 1A scope | New collection `jha_acknowledgements` + signed acknowledgement endpoint + FL Hub surface. ~3 engineer-days. **LOW relative to OC-001/2/3/4/7.** |

**Two paths emerge:**

* **PATH A:** Add OC-005 to Phase 1A. Phase 1A scope grows from 5 → 6 workflows. Build effort 8-12 days → 11-15 days. Operator must accept longer Phase 1A duration.
* **PATH B:** Keep Phase 1A at 5 workflows. Add JHA acknowledgement as **Phase 1A.5** — a parallel/sequential sprint immediately after Phase 1A · before Phase 1B. Phase 1B's vocab canonicalization includes JHA, but acknowledgement workflow is separate.

**See `PHASE1A_SCOPE_CHALLENGE_REPORT.md` for a defensible recommendation.**

---

## 4 · Compliance/payroll/safety/customer impact heatmap

The findings that rank in the top quartile on the **operational / compliance / payroll** axes simultaneously:

| ID | Compliance | Safety | Payroll | Frequency | All-three? |
|---|---|---|---|---|---|
| OC-001 | 3 | 3 | 0 | 1 | partial (compliance + safety) |
| OC-002 | 1 | 1 | 3 | 3 | partial (payroll + frequency) |
| OC-005 | 3 | 3 | 0 | 3 | partial (compliance + safety + frequency) |
| OC-007 | 1 | 0 | 3 | 3 | partial (payroll + frequency) |
| OC-010 | 1 | 1 | 1 | 3 | partial (cross-cutting) |
| OC-014 | 2 | 1 | 2 | 1 | partial |

No single finding scores 3 on all three of compliance + safety + payroll. **OC-005 (JHA) is the closest to that profile (3+3+0).**

---

## 5 · Frequency-of-use ranking

Workflows by per-week operational interaction (estimate from `CLOSURE_PATH_AUDIT.md` §4):

| Rank | Workflow | Per-week | Records since 2026-01 |
|---|---|---|---|
| 1 | Daily Reports (OC-002) | 150 | ~3000 |
| 2 | Safety Meetings (OC-006) | 200 (multi-crew) | ~2000 |
| 3 | JHAs (OC-005) | ~500 (multi-crew) | ~500 distinct |
| 4 | Time Off Requests | 5-10 | ~150 |
| 5 | Site Inspections (OC-004) | 5-10 | ~150 |
| 6 | FL Forms (OC-011) | 5-10 | ~150 |
| 7 | QA/QC (OC-003) | 3-5 | ~100 |
| 8 | Payroll Variance batches (OC-007) | 1 | ~24 batches |
| 9 | Incidents (OC-001) | 1-3 | ~30 |
| 10 | PPE Issuance (OC-008) | 2-5 | ~80 |

**Highest-frequency operational dead-ends:** Daily Reports (#1 per week) + JHAs (acknowledgement gap, #3 by volume).

---

## 6 · 90-day damage-if-ignored ranking

Scenario: which finding causes the most operational damage if NOT fixed for 90 days?

| Rank | Finding | 90-day damage |
|---|---|---|
| 1 | OC-001 Incidents | ~10 incidents close-pending forever · OSHA closeout audit exposure for any recordable injury occurring in window |
| 2 | OC-007 Payroll Variance | 13 weekly batches accumulate "open" · Sandy reconciliation backlog · CFO visibility eroded |
| 3 | OC-002 Daily Reports | ~1,950 DRs unverified · Time Verification + Payroll Variance build atop unverified data · cumulative payroll trust erosion |
| 4 | OC-005 JHAs | ~6,500 JHA submissions without acknowledgement audit trail · OSHA general-duty exposure if injury occurs |
| 5 | OC-010 Vocab fragmentation | Continued executive confusion · 4 displayed statuses per incident · Customer #2 onboarding blocker grows |

OC-001 + OC-002 + OC-007 (current Phase 1A top 3) lead the 90-day damage ranking. OC-005 (JHA) is #4.

---

## 7 · Customer #2 onboarding blockers (priority view)

| ID | Blocks Customer #2 onboarding? | Reason |
|---|---|---|
| OC-001 | 🔴 YES | second tenant inherits "incidents stuck open" |
| OC-002 | 🔴 YES | second tenant cannot verify DRs |
| OC-007 | 🔴 YES | second tenant payroll workflow incomplete |
| OC-003/4 | 🟡 PARTIAL | follow-up surfaces missing |
| OC-005 | 🔴 YES | OSHA compliance ledger gap |
| OC-010 | 🔴 YES | vocab fragmentation breaks per-tenant overrides |
| OC-014 | 🟡 PARTIAL | offboarding multi-step missing |
| Others | 🟢 | not blockers |

**Customer #2 blockers list: OC-001, OC-002, OC-007, OC-005, OC-010.**

Phase 1A addresses OC-001, OC-002, OC-007. Phase 1B addresses OC-010. **OC-005 (JHA) is the missing piece for Customer #2 readiness.**

---

## 8 · OMEGA discipline

🟢 Read-only · 22 findings rescored on 13 axes · top-10 ranking finalized · OC-005 elevation case documented · zero code changes.

🛑 Continue to `PHASE1A_PRIORITY_VALIDATION.md` for the 15-question answer set.
