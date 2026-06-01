# Customer #2 Blocker Matrix · OMEGA Pre-Build Validation

**Program:** OMEGA · Platform Completion Program · Phase 1A · Pre-Build Validation
**Mode:** READ-ONLY
**Companion:** `PHASE1A_PRIORITY_VALIDATION.md` · `CRITICAL_FINDING_RANKING.md` · `PHASE1A_SCOPE_CHALLENGE_REPORT.md`
**Date:** 2026-06-01

---

## 1 · Headline

**A second tenant cannot be onboarded today without inheriting 8 platform-wide operational dead-ends. 5 are addressed by current Phase 1A. 1 (OC-005 JHA) requires elevation. 2 (OC-010 + OC-014) follow in Phase 1B. The full Customer #2 blocker list is now mapped.**

---

## 2 · Customer #2 onboarding blocker matrix

| ID | Finding | Severity | C#2 blocker tier | In current Phase 1A? | Phase that resolves |
|---|---|---|---|---|---|
| OC-001 | Incident closure | 🔴 | T1 · Mission-critical | ✅ | 1A |
| OC-002 | Daily Report office review | 🔴 | T1 · Mission-critical | ✅ | 1A |
| OC-007 | Payroll Variance batch finalize | 🔴 | T1 · Mission-critical | ✅ | 1A |
| OC-005 | JHA acknowledgement ledger | 🔴 | T1 · Compliance-critical | ❌ | 🟡 **ELEVATE TO 1A** |
| OC-003 | QA/QC follow-up | 🔴 | T2 · Important | ✅ | 1A |
| OC-004 | Site Inspection follow-up | 🔴 | T2 · Important | ✅ | 1A |
| OC-010 | Status Vocabulary fragmentation | 🔴 | T2 · Cross-cutting | ❌ | 1B |
| OC-014 | Employee Offboarding multi-step | 🟡 | T3 · Workflow-friction | ❌ | 1B/3 |
| OC-008 | PPE Return | 🟡 | T3 · Workflow-friction | ❌ | 2 |
| OC-013 | Employee Onboarding multi-step | 🟡 | T4 · Operational | ❌ | 2 |
| OC-009 | Photo Janitor | 🟢 | T5 · Hygiene | ❌ | 2 |

11 of 22 findings have any Customer #2 readiness impact. Of those:
* **6 are Phase 1A** (post-elevation including OC-005)
* **2 are Phase 1B** (OC-010 + OC-014)
* **3 are Phase 2** (placeholders + onboarding)

---

## 3 · Tier definitions

| Tier | Definition | Resolution required before onboarding? |
|---|---|---|
| T1 · Mission-critical | Workflow cannot complete; affects daily ops | **YES** — second tenant cannot be onboarded |
| T2 · Important | Workflow partially complete; affects executive visibility | **YES — at 80 % completion minimum** |
| T3 · Workflow-friction | Multi-step flows missing intermediate steps | **NO — second tenant can operate with manual workarounds; deferred to first 60 days** |
| T4 · Operational | Single-flow improvements (e.g., onboarding checklist) | **NO** |
| T5 · Hygiene | Storage / janitor / cleanup | **NO** |

---

## 4 · Per-tenant operational expectation (post-Phase 1A)

If Phase 1A ships with the **recommended 6-workflow scope (including OC-005)**:

### Customer #2 onboarding day 1

| Capability | Status |
|---|---|
| File an incident | ✅ |
| Investigate an incident → close it | ✅ |
| File a daily report | ✅ |
| Review + approve a daily report | ✅ |
| Generate payroll variance from a CSV upload | ✅ |
| Decide every row + close the variance batch | ✅ |
| Submit a JHA + crew acknowledges | ✅ (with OC-005 elevation) |
| Audit JHA acknowledgements per crew | ✅ (with OC-005 elevation) |
| Submit QA/QC inspection + resolve deficiencies | ✅ |
| Submit Site Inspection + resolve findings | ✅ |
| Submit PO request → approve → close | ✅ (already complete) |
| Asset transfer through full lifecycle | ✅ (already complete) |
| Dispatch driver to job + reassign mid-shift | ✅ (already complete) |
| Shop fleet-defect lifecycle | ✅ (already complete) |
| Fire extinguisher monthly inspection | ✅ (already complete) |
| Tasks · Notifications · Time-Off · Documents · Backups · Recovery | ✅ (already complete) |

### Customer #2 onboarding day 1 · STILL BROKEN

| Capability | Phase that fixes |
|---|---|
| Status labels consistent across surfaces (executive sees same status everywhere) | 1B |
| Employee offboarding multi-step ceremony | 1B/3 |
| PPE return workflow | 2 |
| Multi-step onboarding checklist | 2 |
| Photo janitor for orphan rows | 2 |

**Customer #2 can operate normally on day 1 with manual workarounds for the 5 items above. Tier 1 + Tier 2 (mission-critical + important) blockers are all resolved.**

---

## 5 · Without OC-005 elevation (Option C from scope challenge)

If OC-005 is left in Phase 2 (the current sequencing per iter447):

* Customer #2 can operate but is exposed to OSHA general-duty rule for 8-12 weeks
* Crew JHA acknowledgement is verbal only · no platform record
* Audit risk: same as MASCI today, but inherited by Customer #2 from day 1

This is an unacceptable handover state for an "operations platform" pitch. **OC-005 elevation is recommended for Customer #2 readiness.**

---

## 6 · Without Phase 1B (OC-010 status vocab)

Even with Phase 1A complete (5 or 6 workflows), Customer #2 will see the residual 18-vocab fragmentation:

* Executive Command Center labels say "Open · unresolved"
* Accountability projection labels say "in_progress"
* Frontend filter says "Open / Investigating / Closed"
* Per-tenant override capability blocked by vocab fragmentation

This is **executive-confusing but not operationally blocking**. Customer #2 can operate; they will ask why the labels disagree.

**Phase 1B must follow Phase 1A within 1 sprint to fully unblock the executive-readability concern.**

---

## 7 · Without Phase 2 (PPE Return + Onboarding multi-step)

Customer #2 operates with manual workarounds:

* PPE return → tracked in spreadsheets temporarily
* Onboarding checklist → ad-hoc until Phase 2 ships
* Photo janitor → manual R2 cleanup by Admin

**Acceptable manual workaround state. Phase 2 can ship within 90 days of Customer #2 onboarding.**

---

## 8 · Recommendation for Customer #2 readiness criteria

| Phase | Required for Customer #2 onboarding? | Acceptable Customer #2 state on day 1 |
|---|---|---|
| **Phase 1A (6 workflows incl. OC-005)** | **YES — MUST SHIP** | All Tier 1 blockers resolved · all 6 dead-end workflows complete |
| **Phase 1B (OC-010 + OC-014)** | **YES — within 1 sprint of onboarding** | Executive labels canonicalized · offboarding ceremony complete |
| **Phase 2 (OC-008 + OC-009 + OC-013 + OC-016)** | **NO — within 90 days** | Workflow-friction items handled with manual workarounds initially |
| **Phase 3 onward** | **NO — opportunistic** | Cleanup over the platform's first year |

---

## 9 · Customer #2 sign-off checklist (informational · for future use)

When a future operator authorization claims "Customer #2 ready":

```
CUSTOMER #2 READINESS CERTIFICATION

Tier 1 · Mission-critical (4 items)
[ ] OC-001 Incident closure deployed + certified in production
[ ] OC-002 Daily Report review deployed + certified
[ ] OC-007 Payroll Variance finalize deployed + certified
[ ] OC-005 JHA Acknowledgement deployed + certified

Tier 2 · Important (3 items)
[ ] OC-003 QA/QC deployed + certified
[ ] OC-004 Site Inspection deployed + certified
[ ] OC-010 Vocabulary canonicalized for 13+ workflows

Operator sign-off:    _______________
Date:                 _______________
Customer #2 contract: _______________
Onboarding date:      _______________
```

---

## 10 · OMEGA discipline

🟢 Read-only · 11 of 22 findings classified by Customer #2 blocker tier · 6 of 11 in Phase 1A (post-elevation) · per-tenant operational expectation enumerated · zero code changes.

🛑 Continue to operator review of all 4 deliverables (`PHASE1A_PRIORITY_VALIDATION.md` · `CRITICAL_FINDING_RANKING.md` · `PHASE1A_SCOPE_CHALLENGE_REPORT.md` · `CUSTOMER2_BLOCKER_MATRIX.md`).
