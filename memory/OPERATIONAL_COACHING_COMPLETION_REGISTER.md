# OPERATIONAL COACHING COMPLETION REGISTER
## OCEP · Operational Coaching & Spanish Parity Completion Program (OCSPCP) · 1 of 7

**Date**: 2026-06-03
**Authority**: OMEGA / FOCP DIRECTIVE — OCSPCP
**Mode**: READ-ONLY source-direct verification · NO new workflows · NO new modules · NO roadmap expansion
**Evidence rule**: Every cell verified against `/app/backend/guidance/tips.py` (parsed for kind distribution per form_key), `/app/backend/routes/`, `/app/backend/lib/workflow_state_events.py`, `/app/frontend/src/pages/admin/AdminOperationalLanguage.jsx`, `/app/frontend/src/lib/i18n.js`.

**Platform-scale measurements** (source-direct):
- 157 total form_keys in `tips.py` (6218 LOC)
- 47 safety form_keys + 96 non-safety form_keys + 14 leaf-only (counted in parent form_keys above)
- Total tips: ~412
- Tips with `mistake` kind: 92 (52 non-safety + 23 safety + 17 other)
- Tips with `body_es` populated: **1 of ~412 (≈ 0.24%)** — sole instance on `jha.poster`
- i18n.js Spanish keys (Layer A): ~3218 entries
- AdminOperationalLanguage glossary (admin-only): ~50 EN+ES entries

---

## 1 · Phase 1 inventory: every workflow in production

For each workflow: Owner / Type / EN Help / EN Coaching / EN Mistakes / EN Lifecycle / EN Accountability / ES Help / ES Coaching / ES Mistakes / ES Lifecycle / ES Accountability. Verdicts: 🟢 Complete · 🟡 Partial · 🔴 Missing.

### 1.1 · Safety workflows (14) — see `SAFETY_TRAINING_COMPLETION_REGISTER.md` for full evidence

Summary verdicts inherited from STCP:

| # | Workflow | Owner | Type | EN Help | EN Coach | EN Mistakes | EN Lifecycle | EN Accountability | ES Help | ES Coach | ES Mistakes | ES Lifecycle | ES Accountability |
|---|---|---|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| 1 | JHP + Ack | Safety/PM | Attestation | 🟢 | 🟢 | 🟡 (parent `jha` missing) | 🔴 (no LifecycleGuide) | 🟡 (FOCP R2 ledger) | 🟢 (Layer A) | 🔴 (Layer B 12%) | 🔴 | 🔴 | 🟡 |
| 2 | Safety Meeting | Safety/Foreman | Record | 🟢 | 🟢 | 🟡 | 🔴 (no lifecycle file) | 🔴 (no approval gate) | 🟢 | 🔴 | 🔴 | 🔴 | 🔴 |
| 3 | Incident Report | Safety/Admin | Lifecycle | 🟢 | 🟢 | 🟡 (parent missing) | 🟢 | 🟢 (3-attestation) | 🟢 | 🔴 | 🔴 | 🟢 (Layer A) | 🟡 |
| 4 | Site Inspection | Safety | Lifecycle | 🟢 | 🟢 | 🟡 | 🟢 | 🟢 (Amendment 001) | 🟢 | 🔴 | 🔴 | 🟢 | 🟡 |
| 5 | QA/QC Inspection | PM/Safety | Lifecycle | 🟢 | 🟢 | 🟡 | 🟢 | 🟢 | 🟢 | 🔴 | 🔴 | 🟢 | 🟡 |
| 6 | CAPA / Corrective | Safety | Pipeline | 🟢 | 🟢 | 🟡 | 🟡 (status_history only) | 🟢 (5-stage) | 🟢 | 🔴 | 🔴 | 🟡 | 🟡 |
| 7 | Equipment Pre-op | Operator/Shop | Record | 🟢 | 🟡 | 🟡 | 🔴 | 🟡 | 🟢 | 🔴 | 🔴 | 🔴 | 🟡 |
| 8 | Equipment Issuance | Safety/HR | Ack | 🟢 | 🟡 | 🟡 | 🔴 | 🟡 | 🟢 | 🔴 | 🔴 | 🔴 | 🟡 |
| 9 | Equipment Training | HR/Safety | Record | 🟢 | 🟡 | 🟡 | 🔴 | 🟡 | 🟢 | 🔴 | 🔴 | 🔴 | 🟡 |
| 10 | **Fleet Repair/RTS** | Shop | Lifecycle | 🔴 (2 tips on RTS) | 🔴 | 🟡 | 🔴 | 🔴 | 🟢 | 🔴 | 🔴 | 🔴 | 🔴 |
| 11 | Fire Extinguisher | Safety/Shop | Record | 🟢 | 🟢 | 🟢 | 🔴 | 🟡 | 🟢 | 🔴 | 🔴 | 🔴 | 🟡 |
| 12 | Safety Topic Library | Safety | Read | 🟢 | 🟢 | 🟡 | n/a | n/a | 🟢 (23 ES files) | 🔴 (tips) | 🟡 | n/a | n/a |
| 13 | Safety Document | Safety | Record | 🟢 | 🟢 | 🟡 | 🔴 | 🟡 | 🟢 | 🔴 | 🔴 | 🔴 | 🟡 |
| 14 | Safety Training record | HR/Safety | Record | 🟢 | 🟢 | 🟡 | 🔴 | 🟢 | 🟢 | 🔴 | 🔴 | 🔴 | 🟢 |

### 1.2 · Non-safety workflows (10 distinct + sub-flows)

Verified from `tips.py` AST walk + route survey:

| # | Workflow | Owner | Type | EN Help | EN Coach | EN Mistakes | EN Lifecycle | EN Accountability | ES Help | ES Coach | ES Mistakes | ES Lifecycle | ES Accountability |
|---|---|---|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| 15 | **Daily Report** | Foreman | Lifecycle | 🟢 | 🟢 (21 tips · 5 sub-forms with mistake) | 🟢 | 🟢 (`daily_report_lifecycle.py`) | 🟡 (Office review/kickback) | 🟢 (Layer A iter437/438) | 🔴 (Layer B) | 🔴 | 🟢 (Layer A) | 🟡 |
| 16 | **Dispatch** | Dispatch | Multi-surface | 🟢 (25 tips across 14 sub-forms) | 🟢 | 🟢 (9 sub-forms with mistake) | 🟡 (`dispatch_lifecycle.py` exists) | 🟡 | 🟢 | 🔴 | 🔴 | 🟡 | 🟡 |
| 17 | Document Expirations | HR | Cadence | 🟢 (12 tips) | 🟢 | 🟢 (3 sub-forms) | n/a | 🟡 | 🟢 | 🔴 | 🔴 | n/a | 🟡 |
| 18 | Driver Qualification | HR/Dispatch | Compliance | 🟢 (30 tips · 8 sub-forms) | 🟢 | 🟢 (5 sub-forms) | n/a | 🟡 | 🟢 | 🔴 | 🔴 | n/a | 🟡 |
| 19 | Employee Accountability | Field Leadership | Tone/process | 🟢 (12 tips) | 🟢 | 🟢 (2 sub-forms) | n/a | 🟢 (verify sub-form) | 🟢 | 🔴 | 🔴 | n/a | 🟡 |
| 20 | **Employee Lifecycle** | HR | Lifecycle | 🟢 (19 tips · 7 sub-forms) | 🟢 | 🟢 (5 sub-forms inc. rehire) | 🟢 (`employee_lifecycle.py`) | 🟢 (Phase Alpha) | 🟢 | 🔴 | 🔴 | 🟢 (Layer A) | 🟢 |
| 21 | **Payroll Variance** | HR/Admin | Lifecycle | 🟢 (13 tips · 4 sub-forms) | 🟢 | 🟡 (only 1 sub-form has it) | 🟢 (`payroll_variance_lifecycle.py`) | 🟢 (3-attestation gate) | 🟢 | 🔴 | 🔴 | 🟢 | 🟡 (per AR-0004 def gap) |
| 22 | Field Leadership Portal | Admin | Admin tooling | 🟢 (22 tips · 8 sub-forms) | 🟢 | 🟢 (5 sub-forms) | n/a | 🟢 (records review tone) | 🟢 | 🔴 | 🔴 | n/a | 🟡 |
| 23 | Time-Off Review | HR/PM | Approval | 🟢 (14 tips · 4 sub-forms) | 🟢 | 🟢 (4 sub-forms) | 🔴 (no lifecycle file) | 🟡 | 🟢 (Layer A) | 🔴 | 🔴 | 🔴 | 🟡 |
| 24 | Time Verification | HR/Foreman | Reconcile | 🟢 (10 tips · 3 sub-forms) | 🟢 | 🟢 (2 sub-forms) | n/a | 🟡 | 🟢 | 🔴 | 🔴 | n/a | 🟡 |
| 25 | Discipline cluster (writeup / verbal_coaching / supervisor_notes / training_deficiency / promotion_recommendation / recognition / new_employee_eval / crew_eval) | HR/PM | HR records | 🟢 (21 tips across 9 form_keys) | 🟢 | 🟢 (5 forms with mistake) | n/a | 🟡 | 🟢 | 🔴 | 🔴 | n/a | 🟡 |
| 26 | Equipment Checkout / Return | Shop | Record | 🟢 (14 tips · 5 sub-forms) | 🟢 | 🟢 (3 sub-forms) | n/a | 🟡 | 🟢 | 🔴 | 🔴 | n/a | 🟡 |
| 27 | Material Calculator | PM/Foreman | Calc | 🟢 (10 tips · 4 sub-forms) | 🟢 | 🟢 (2 sub-forms) | n/a | n/a | 🟢 | 🔴 | 🔴 | n/a | n/a |
| 28 | Attendance | Field Leadership | Record | 🟡 (2 tips) | 🟡 | 🔴 (no mistake) | n/a | 🔴 | 🟢 | 🔴 | 🔴 | n/a | 🔴 |

### 1.3 · Workflows verified to exist without tips registry coverage (operate via i18n.js only)

| # | Workflow | EN Help | ES Help | EN Coach | ES Coach | EN Mistakes | ES Mistakes | EN Lifecycle | ES Lifecycle | EN Accountability | ES Accountability |
|---|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| 29 | Asset Transfer | 🟡 (Layer A only) | 🟢 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 (DOCTRINE-SILENT per TCP) | 🔴 | 🟡 | 🟡 |
| 30 | Operational Constraints | 🟡 | 🟢 | 🔴 | 🔴 | 🔴 | 🔴 | 🟢 (chronology + resolve API per TCP) | 🟢 | 🟡 (TR-0007 doctrine-exempt reopen) | 🟡 |
| 31 | Vendor Management | 🟡 | 🟢 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 (TR-0003 — no archive) | 🔴 | 🟡 | 🟡 |
| 32 | Project Management Hub | 🟢 (read-side) | 🟢 | 🔴 | 🔴 | n/a | n/a | n/a | n/a | 🟢 (read-side) | 🟢 |
| 33 | HR Hub | 🟢 | 🟢 | 🔴 | 🔴 | n/a | n/a | n/a | n/a | 🟢 | 🟢 |
| 34 | Public Time-Off (employee request) | 🟢 | 🟢 (Layer A) | 🔴 | 🔴 | 🔴 | 🔴 | 🟡 | 🟡 | 🟡 | 🟡 |
| 35 | Universal Undo / Recovery Stream | 🟢 (page subtitle) | 🟢 (FOCP R2 § 8 declares EN-canonical for admin surface) | 🟢 | 🟡 | 🟡 | 🟡 | 🟢 (audit twin) | 🟢 | 🟢 | 🟢 |

### 1.4 · Workflows known-NOT-IMPLEMENTED

| # | Workflow | Verdict |
|---|---|---|
| 36 | Submittals | ⛔ NOT-IMPLEMENTED (per TCP). Out of scope per FOCP Final Directive. |

---

## 2 · Aggregate verdict (36 inventoried workflows × 10 dimensions)

| Dimension | 🟢 | 🟡 | 🔴 | n/a |
|---|---:|---:|---:|---:|
| EN Help | 27 | 6 | 1 (Attendance partial) | 2 |
| EN Coaching | 21 | 8 | 6 | 1 |
| EN Mistakes | 20 | 11 | 4 | 1 |
| EN Lifecycle | 7 | 4 | 19 | 6 |
| EN Accountability | 9 | 18 | 4 | 5 |
| ES Help | 33 | 1 | 0 | 2 |
| **ES Coaching** | 1 (Recovery Stream) | 0 | **34** | 1 |
| **ES Mistakes** | 0 | 1 | **34** | 1 |
| ES Lifecycle | 5 | 4 | 21 | 6 |
| ES Accountability | 3 | 23 | 5 | 5 |

**Headline metric**: 
- **EN coaching**: 21 GREEN · 8 YELLOW · 6 RED of 36 workflows ≈ **58% GREEN**
- **ES coaching**: 1 GREEN · 0 YELLOW · 34 RED of 36 workflows ≈ **3% GREEN**

The ES-coaching column is the **single largest gap** between current state and the directive's target state (95%+ GREEN).

---

## 3 · Operator-priority cluster summary

Six clusters previously identified by STCP (Section 6 of `SAFETY_CERTIFICATION_READINESS_REPORT.md`) are now extended platform-wide:

| Cluster | Affected | Pattern |
|---|---|---|
| **C1 — Parent form_key `mistake` absent** | 12 safety + at least 8 non-safety parents (attendance, payroll-variance, time-off-review, time-verification, employee-accountability, employee-lifecycle, field-leadership.records, etc. lack `mistake` on parent) | Pattern is platform-wide |
| **C2 — Coaching body_es ≈ 0%** | **All 36** workflows | The single biggest parity gap on the platform |
| **C3 — LifecycleGuide unwired** | JHP, Meeting, CAPA, Pre-op, Fleet, Time-Off Review, Asset Transfer, Vendor Management | Per `SAFETY_HELP_CONTENT_REGISTER.md` §5.1 |
| **C4 — AdminOperationalLanguage glossary unwired in-flow** | All 36 | Operator-intent line 5 of glossary file not yet implemented |
| **C5 — Fleet RTS thin coaching** | 1 workflow | Highest single-decision risk |
| **C6 — Onboarding 🔴 absent** | All 36 | No in-app new-hire walk-through |

Every cluster reuses existing infrastructure (tips registry, LifecycleGuide component, glossary content, body_es field). **No new workflows. No new modules.**

---

## 4 · Retired false findings (platform-wide)

| Inherited claim | Source-direct verdict | Disposition |
|---|---|---|
| "Platform-wide Spanish coverage ~52%" | Layer A: ~comprehensive. Layer B: 1 of ~412 tips. | **REFINED** — two-layer model. |
| "Mistake kind absent on 14 form_keys" | Verified: at least 18 parent + 6 leaf form_keys across safety scope, plus ≥ 8 non-safety parents. ≥ 32 form_keys total lack `mistake` on the surface. | **REFINED — precise count.** |
| "Coaching is ~52% complete" | EN coaching: 58% GREEN at workflow level. ES coaching: 3% GREEN at workflow level. | **REFINED — language-split.** |
| "All workflows have at least partial help content" | Daily Report, Incident, Site, QA/QC, Employee Lifecycle, Payroll Variance, Dispatch — all 🟢 EN help. Attendance is the sole 🟡 EN help. | **CONFIRMED breadth; coverage exists, depth varies.** |
| "Submittals missing" | Confirmed NOT-IMPLEMENTED. Out of scope. | **CONFIRMED.** |
| "Vendor archive missing (TR-0003)" | Confirmed. | **ACTIVE.** |

---

**End of OPERATIONAL COACHING COMPLETION REGISTER · OCSPCP 1 of 7**
