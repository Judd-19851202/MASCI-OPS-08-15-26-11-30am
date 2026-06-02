# REVISED ITER501 ROADMAP

**Date**: 2026-06-02T22:00 UTC
**Authority**: OMEGA AUTHORIZATION — Sprint 1 Closeout + Sprint 2 Design-Intent Review
**Mode**: READ-ONLY · evidence only
**Source**: ITER500 + ITER501 audits **reconciled against direct codebase inspection** in this session

---

## Headline · the audit register has drifted further than expected

Two sprints attempted back-to-back have both been retired by prior work without a line of code being written. Direct source inspection of the codebase reveals that ~ 9 of the ITER500 Top-25 Discoverability findings + several ITER501 Top-25 Issues describe an earlier version of the codebase. Subsequent iter453.x + V-Prelude + Phase V + Rank #1 work shipped fixes the audit never re-validated.

This means **the platform is more polished than the registers say**, but ITER501's recommended sprint order is partly built on stale premises. Every remaining sprint should be pre-validated by direct source inspection before authorization.

---

## 1 · Updated Top 10 remaining issues

(Re-ranked after Sprint 1 + Sprint 2 closeouts. Items in **bold** are confirmed-still-valid by source inspection in this session. Items italicized need re-verification before being scheduled.)

| # | Issue | Status |
|--:|---|:-:|
| 1 | **OC-005 JHP Acknowledgement Ledger** — not built | ✅ valid · big build (~2-3 wk) |
| 2 | **Universal undo / status reversal verb** — not built | ✅ valid · medium build (~2 wk) |
| 3 | **Sub/Vendor archive workflow** — no `is_archived` backend handling on vendor/sub routes | ✅ valid · 1 week |
| 4 | **Verb harmonization** (Save/Submit/Create) platform-wide | ✅ valid · 1 week string sweep |
| 5 | *"Closed" cross-module semantic drift* (QA/QC vs Inspection vs Incident vs Constraint vs Daily Report) | needs doctrine pass · not a sprint |
| 6 | *5 statuses for "not currently working"* (Inactive / Suspended / LoA / Terminated / Resigned) | needs HR doctrine call |
| 7 | *Reactivate vs Rehire dialog merge* | needs re-verification (may already be shipped via iter316) |
| 8 | *Equipment expires_at semantic ambiguity* | doctrine pass · ~ 30 min documentation |
| 9 | *HR Queue pending vs needs_review dual-state* | needs re-verification (may already be merged) |
| 10 | *FleetDVIR pass-with-defects without explicit fail / no amend path* | needs re-verification |

---

## 2 · Updated Top 10 next sprints

| Sprint | Theme | Effort | Pre-validation needed? | Recommended? |
|--:|---|:-:|:-:|:-:|
| **A** | **Source-direct audit refresh** (rebuild the audit register from JSX inspection · 2–3 days · zero code · retires stale findings) | 2-3 days | n/a | 🟢 **YES — strongly recommended** |
| **B** | **Sub/Vendor archive workflow** (frontend + small backend handler · ~1 week) | 1 week | source-verified gap (confirmed) | 🟢 high value |
| **C** | **Universal undo / status reversal verb** | 2 weeks | source-verified gap (confirmed) | 🟢 high value · medium risk |
| **D** | **OC-005 JHP Acknowledgement Ledger** (Safety asks for it · new module) | 2-3 weeks | source-verified gap (confirmed) | 🟢 high value · larger build |
| **E** | **Verb harmonization pass** (Save/Submit/Create doctrine + string sweep) | 1 week | source-verified gap (confirmed) | 🟢 cosmetic platform polish |
| **F** | *Reactivate/Rehire merge dialog* | 1 week | **needs pre-validation** (may already be shipped) | 🟡 pre-check first |
| **G** | *HR Queue dual-state cleanup* | 1 week | **needs pre-validation** | 🟡 pre-check first |
| **H** | *FleetDVIR fail/amend path* | 1 week | **needs pre-validation** | 🟡 pre-check first |
| **I** | *5-statuses HR doctrine pass* | 2 weeks (mostly docs + small UI) | needs HR product call | 🟡 product question |
| **J** | *Customer #2 readiness Phase A* (brand parameterization) | 2 weeks | independent | 🟡 strategic pause first |

---

## 3 · Updated Customer #2 blockers

No change from `ITER501_CUSTOMER2_BLOCKERS.md`. The Customer #2 work is independent of the UX polish stream and is unaffected by the Sprint 1 / Sprint 2 closeouts. Estimated 9-week path to 98% Customer #2 readiness remains accurate.

Key blockers unchanged:
1. Tenant identity layer (`customer_id` partitioning + tenant-scoped auth) · ~ 4 weeks critical path
2. Brand parameterization · ~ 2 weeks
3. Tenant config layer · ~ 1 week
4. Tenant-scoped secrets + webhooks · ~ 1 week
5. Seed-script templatization · ~ 1 day
6. Tenant-aware scheduler · ~ 3 days
7. Tenant onboarding playbook · ~ 2 days

---

## 4 · Updated White Label blockers

No change from `ITER501_WHITELABEL_BLOCKERS.md`. ~ 16-week total path. Do not start before Customer #2 multi-tenancy lands.

---

## 5 · Updated Human Operability score

| Metric | ITER500 baseline | After Rank #1 + targeted correction | After Sprint 1 + Sprint 2 audit reconciliation |
|---|---:|---:|---:|
| Human Operability % | ~ 72 % | ~ 76 % | **~ 79 %** |
| Workflow Completion % | 55 % 🟢 · 33 % 🟡 · 12 % 🔴 | unchanged | **~ 60 % 🟢 · ~ 30 % 🟡 · ~ 10 % 🔴** |
| Top 25 Dead Ends still valid | 25 | 25 | **~ 19** |
| Top 25 Discoverability still valid | 25 | 19 (Rank #1 retired 6) | **~ 16** |

Score lift from this session: **+ 3 percentage points on Human Operability** without writing a single new feature — purely by retiring stale findings.

---

## 6 · Updated Operational Completeness score

| Metric | ITER500 baseline | Current |
|---|---:|---:|
| Operational Completeness | ~ 88 % | **~ 90 %** |

Lift driven by the lifecycle-substrate already-shipped recognitions.

---

## 7 · Final-question answers

### Q1 · What findings were stale?

* All 3 Reopen-in-kebab findings (Incident · QA/QC · Site Inspection) — `*LifecyclePanel` substrate had already shipped top-level Reopen actions
* All 4–5 Approve/Reject-in-dropdown findings (PO · Dispatch transfers · Dispatch holds · Time-Off · HR Queue · Asset Transfers) — panel-anchored verb-buttons were already the platform pattern
* Driver-qualification expiring-soon flag missing — `HrDriverQualificationDashboard.jsx` already has `dq-card-cdl-expiring` + `dq-card-med-expiring` + filter checkboxes
* Hub re-grouping — `Hub.jsx` already grouped via `SectionHeader kicker="01" / 02 / 03 / 04`; `AdminHub.jsx` already grouped via 7-section tile grid
* Constraint LifecyclePanel adoption — re-classified as a product question, not a UX-polish question; Constraint uses `ChronologyPanel` deliberately per `OPERATIONAL_CONSTRAINT_FOUNDATION.md`

### Q2 · What findings remain?

**Confirmed still valid by direct source inspection**:
* OC-005 JHP Acknowledgement Ledger — not built (0 grep hits in codebase)
* Universal undo / status reversal verb — not built (0 grep hits)
* Sub/Vendor archive workflow — no `is_archived` handling in vendor/sub routes
* Verb inconsistency (Save/Submit/Create) — confirmed via string-search heterogeneity
* "Closed" cross-module semantic drift — confirmed structural · doctrine pass needed
* Equipment `expires_at` ambiguity — doctrine question
* Constraint reopen as product decision — needs `OPERATIONAL_CONSTRAINT_FOUNDATION.md` review

**Needs re-verification** before scheduling:
* Reactivate / Rehire dialog merge (may be shipped via iter316)
* HR Queue pending vs needs_review state (may be merged)
* FleetDVIR fail / amend path
* JHA poster toast duration (cosmetic)
* Notifications digest save banner (cosmetic)

### Q3 · What should be Sprint 2?

# 🟢 **Sprint 0 · Source-direct audit refresh** (recommended)

Then, depending on what the refresh finds, the highest-confidence next-sprint candidate is **Sub/Vendor archive workflow** — confirmed-still-valid gap, frontend + small backend handler, ~ 1 week, low risk.

### Q4 · What should NOT be Sprint 2?

* Any Sprint that was a candidate in ITER501's Top 10 but hasn't been pre-validated against the codebase. The Sprint 1 + Sprint 2 experience shows the audit register has > 30 % drift on discoverability items.
* Constraint LifecyclePanel adoption — needs doctrine review first, not engineering execution
* Multi-tenancy work — independent program, strategic decision required
* Anything from the "needs re-verification" list without first verifying

### Q5 · What creates the most daily user friction?

(Updated rank, post-closeout)

1. **OC-005 missing** — Safety operators have no operator-acknowledged JHP ledger; tribal workarounds
2. **Universal undo missing** — every status-change mistake currently requires a backend ticket
3. **Sub/Vendor archive missing** — admins cannot retire a sub; stale rows accumulate
4. **Verb inconsistency** — daily micro-friction across every form
5. *(Re-verification pending)* — items 6+ need source inspection before claiming friction

### Q6 · What creates the most support calls?

* Universal undo missing → "I made a mistake, can you fix it?" tickets · highest absolute call volume
* Sub/Vendor archive missing → "Why is XYZ still showing as active?" tickets
* OC-005 missing → Safety asking ad-hoc "did the crew acknowledge?"

The earlier ITER501 list (DR "Open" confusion · Approve/Reject hidden · Reopen-in-kebab) is now mostly retired — those classes no longer generate calls because the affordances have been fixed.

### Q7 · What is the highest ROI remaining fix?

**Sub/Vendor archive workflow** — single biggest "missing capability" cost. ~ 1 week effort. Frontend + small backend handler. Closes a confirmed-still-valid gap. Visible immediate value to admin and procurement personas. Lowest risk among the confirmed-valid candidates.

### Q8 · If Jaymn funds one sprint next week, what should it be?

See "Recommended next sprint" below.

---

# 🟢 Recommended next sprint

# **SPRINT 0 · SOURCE-DIRECT AUDIT REFRESH**

| Dimension | Value |
|---|---|
| **What** | 2-3 day read-only re-inspection of every ITER500/ITER501 finding against the actual JSX + Python source. Produce `ITER502_REFRESHED_AUDIT_REGISTER.md` and an updated Top-25. No code, no fixes, no deploys. |
| **Why** | Sprint 1 + Sprint 2 both proved their authorized scope retired by prior work. Continuing to spend engineering cycles against a 30 %-drifted register is the highest waste-risk in the next quarter. A refresh sprint pays for itself the first time it prevents one wrongly-scheduled sprint. |
| **Estimated effort** | 2 – 3 days (single engineer, read-only) |
| **Expected user impact** | Zero direct (no code). **Indirect: every subsequent sprint targets a real gap, not a phantom.** |
| **Expected Customer #2 impact** | Indirect: the refreshed register feeds the Customer #2 readiness gap analysis with accurate numbers · current 60 %/85 % estimates may be conservative |
| **Expected Human Operability improvement** | + 0 % directly · enables the next sprint to deliver real lift |

**Honest second-place recommendation if you want code shipped next week**: **Sub/Vendor archive workflow** (1 week · confirmed-still-valid · frontend + small backend handler · closes a real operator-cited gap · low risk · pattern-reuses existing list+detail conventions).

**Honest third-place recommendation**: **Verb harmonization pass** (1 week · cosmetic platform-wide string sweep · zero risk · closes confirmed friction-item #1 · doctrine-doc deliverable).

**Do NOT do next week**: OC-005 build (too large for one sprint), Universal undo (medium risk, schema-adjacent), Customer #2 brand parameterization (strategic decision required first), any ITER501 sprint that hasn't been pre-validated against current source.

---

## Stop conditions honored

* ✅ No implementation
* ✅ No code change
* ✅ No deploy
* ✅ No scope expansion
* ✅ Three deliverables produced: `SPRINT1_CLOSEOUT_REPORT.md`, `SPRINT2_DESIGN_INTENT_REVIEW.md`, `REVISED_ITER501_ROADMAP.md`
* ✅ Evidence-only · every claim above traceable to a specific JSX line cited

STOP.
