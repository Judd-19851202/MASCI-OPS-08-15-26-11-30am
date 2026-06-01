# Phase 1A · Scope Challenge Report

**Program:** OMEGA · Platform Completion Program · Phase 1A · Pre-Build Validation
**Mode:** READ-ONLY
**Companion:** `PHASE1A_PRIORITY_VALIDATION.md` · `CRITICAL_FINDING_RANKING.md`
**Date:** 2026-06-01

---

## 1 · Challenge stance

The operator's directive asked: *"Challenge the current Phase 1A selection. Attempt to prove it is wrong."*

This report mounts that challenge in good faith. Findings:

* **3 of 5 current Phase 1A workflows are unchallengeable** (OC-001, OC-002, OC-007 — top-3 weighted scores).
* **2 of 5 current Phase 1A workflows are challengeable** (OC-003, OC-004 — ranks 6-7) but they survive the challenge on architectural-reuse grounds.
* **1 workflow NOT in Phase 1A challenges the scope** (OC-005 JHA Acknowledgement Ledger — rank #4) and should be **ELEVATED**.

---

## 2 · "What critical workflow is NOT included?"

**Answer:** OC-005 JHA Acknowledgement Ledger.

### 2.1 · Evidence

| Axis | OC-005 score | Top Phase 1A score (OC-001) |
|---|---|---|
| Weighted total | 31.5 | 39.5 |
| Compliance | 3 (OSHA 1926.21(b)(2)) | 3 |
| Safety | 3 | 3 |
| Frequency | 3 (~500/wk) | 1 (~1-3/wk) |
| 90-day damage | 2 | 3 |
| Customer #2 blocker | YES | YES |

OC-005 carries the **same compliance score** as OC-001 and the **highest frequency score** of any Phase 1A candidate. It is the platform's largest unaudited safety touchpoint.

### 2.2 · Why it was previously placed in Phase 2

The Operational Completeness Audit (iter447) sequenced JHA Acknowledgement into Phase 2 ("multi-step lifecycles") on the assumption that **acknowledgement = lifecycle**. This audit re-examines that assumption and finds it incorrect:

* JHA acknowledgement does NOT require a state machine.
* It is a single-step audit ledger: crew member signs · timestamp + signature recorded · no transitions ever.
* Build complexity is **substantially lower** than the other Phase 2 candidates (PPE Return, Photo Janitor).
* It belongs **with the OSHA-touching workflows in Phase 1A** (incidents + JHA both feed OSHA documentation).

**Verdict: OC-005 was mis-sequenced in iter447. Correct phase is 1A.**

---

## 3 · "What user dead-end is worse?"

`USER_TASK_COMPLETION_AUDIT.md` lists 6 dead-ends:

| Dead-end | Phase 1A addresses? |
|---|---|
| Safety closes an incident | ✅ via OC-001 |
| HR closes a payroll variance batch | ✅ via OC-007 |
| Anyone marks a Daily Report reviewed | ✅ via OC-002 |
| PM resolves QA/QC deficiency | ✅ via OC-003 |
| Safety resolves Site Inspection finding | ✅ via OC-004 |
| Safety officer marks JHA acknowledged by crew | ❌ NOT addressed |

**5 of 6 dead-ends are addressed by current Phase 1A. The 6th (JHA acknowledgement) is the elevation candidate.** No other dead-end exists at this severity tier.

---

## 4 · "What compliance gap is worse?"

| Gap | Severity | In Phase 1A? |
|---|---|---|
| OSHA recordable incident closure | 🔴 HIGHEST | ✅ OC-001 |
| OSHA JHA acknowledgement (29 CFR 1926.21(b)(2)) | 🔴 HIGH | ❌ OC-005 not in scope |
| OSHA daily report verification | 🟡 MEDIUM | ✅ OC-002 |
| IRS payroll variance documentation | 🟡 MEDIUM | ✅ OC-007 |
| OSHA training record (already complete in canonical training records workflow) | 🟢 not a gap | n/a |

OSHA JHA acknowledgement is the only compliance gap NOT in current Phase 1A scope. **Confirms OC-005 elevation.**

---

## 5 · "What ownership gap is worse?"

`ROLE_ACTIONABILITY_MATRIX.md` enumerated per-role action availability:

* Current Phase 1A addresses ownership gaps for: Safety (incidents) · PM (DRs · QA/QC) · HR (Payroll) · Safety (Site Inspections).
* OC-005 would add ownership for: **Safety + FL (JHA acknowledgement)**.
* Other ownership gaps (Employee onboard/offboard) score lower and are sequenced later.

**No ownership gap worse than what Phase 1A + OC-005 addresses.**

---

## 6 · "What closure gap is worse?"

`CLOSURE_PATH_AUDIT.md` listed 9 workflows that cannot exit active list:

| Workflow | Phase 1A addresses? |
|---|---|
| Incidents | ✅ |
| Daily Reports | ✅ |
| Site Inspections | ✅ |
| QA/QC | ✅ |
| Payroll Variance batches | ✅ |
| JHA Forms | ❌ — but JHA Acknowledgement ledger (OC-005) is the closer for daily crew acknowledgement, not the JHA library itself |
| Safety Meetings | ❌ — low-frequency (OC-006 · score 10.0 · Phase 3) |
| FL Forms | ❌ — low-frequency (OC-011 · score 7.5 · Phase 3) |
| PPE Issuance | ❌ — closure via PPE Return in Phase 2 (OC-008) |

The 9 closure gaps map cleanly to: 5 in Phase 1A · 1 in Phase 1A (elevated · OC-005) · 1 in Phase 2 · 2 in Phase 3.

---

## 7 · "What status fragmentation is worse?"

`STATUS_VOCABULARY_AUDIT.md` documented 18 vocabularies. OC-010 (the cross-cutting refactor) is correctly Phase 1B. The single workflow with the worst fragmentation is **Incidents** (4-way vocab split documented in `INCIDENT_LIFECYCLE_AUDIT.md`) — which is OC-001, already in Phase 1A.

**No status fragmentation worse than what Phase 1A + Phase 1B addresses.**

---

## 8 · Challenge against OC-003 (QA/QC) and OC-004 (Site Inspections)

These two findings rank #6-7 by score. Why are they in Phase 1A and not Phase 2?

### 8.1 · Architectural-reuse defense

OC-003 and OC-004 are **the same architectural pattern** (inspection-level state + per-finding state with auto-transitions). Building them in the same batch shares ~60 % of code (state machine + audit collection + UI panel + role gates). Splitting them across phases doubles the effort.

### 8.2 · Domain-pairing defense

OC-001 (Safety domain) + OC-004 (Safety domain) pair naturally for Safety officer training. PM works with OC-002 (DR) + OC-003 (QA/QC). HR works with OC-007 (Payroll). One Phase 1A delivers a coherent operator training package: each role gets ≥1 closure surface they own.

### 8.3 · Verdict

**OC-003 and OC-004 SURVIVE the challenge.** They stay in Phase 1A on architectural-reuse + domain-pairing grounds, despite scoring below OC-005.

---

## 9 · Alternative scope options (operator decision matrix)

### Option A · ELEVATE OC-005 into Phase 1A (recommended)

| Pros | Cons |
|---|---|
| Closes the highest-frequency unaudited safety workflow | Phase 1A scope grows from 5 → 6 workflows |
| OSHA compliance loop closed in one batch | Build effort 8-12 days → 11-15 days |
| Customer #2 blocker resolved sooner | Slightly higher coordination overhead |
| Lower build complexity than other Phase 2 items | Operator must accept longer Phase 1A duration |

### Option B · Defer OC-005 to Phase 1A.5 (mini-sprint after Phase 1A)

| Pros | Cons |
|---|---|
| Phase 1A stays at 5 workflows (original scope) | 90-day OSHA exposure continues until mini-sprint ships |
| Phase 1A.5 can leverage Phase 1A's `workflow_state_events` (though OC-005 doesn't need it) | Adds a discrete sprint to the program timeline |
| Lower risk per sprint | Customer #2 readiness delayed by mini-sprint duration |

### Option C · Reject elevation (NOT recommended)

| Pros | Cons |
|---|---|
| Minimum scope change | OC-005 sits in Phase 2 for 8-12 more weeks |
| | OSHA general-duty exposure continues |
| | Customer #2 onboarding blocked longer |

### Option D · Swap OC-003 or OC-004 OUT, add OC-005 IN

| Pros | Cons |
|---|---|
| Scope unchanged (5 workflows) | Loses architectural-reuse between QA/QC + Site Inspections |
| | Demoted workflow drifts to Phase 2; later resurrection requires re-design |
| | Domain coverage for PM (OC-003) or Safety (OC-004) lost |

---

## 10 · Recommendation

**Adopt Option A.** Elevate OC-005 (JHA Acknowledgement Ledger) into Phase 1A. Phase 1A scope: 6 workflows. Estimated effort: ~12.5 engineer-days.

Justification:

1. OC-005 scores #4 of 22 — within Phase 1A's natural threshold
2. OC-005 is a Customer #2 blocker — directly aligned with the program objective
3. OC-005 has the highest frequency of any unaddressed safety workflow
4. OC-005's build cost is LOW (additive only; no state machine)
5. OC-005 pairs naturally with OC-001 (both OSHA-touching)
6. The 3-day scope increase is justified by closing the OSHA-evidence loop in one batch

---

## 11 · OMEGA discipline

🟢 Read-only · scope challenge mounted in good faith · 2 of 5 current Phase 1A items challenged and defended · 1 new item identified for elevation (OC-005) · 4 alternative scope options enumerated with pros/cons · single recommendation issued.

🛑 Operator decision required: A / B / C / D from §9. Continue to `CUSTOMER2_BLOCKER_MATRIX.md`.
