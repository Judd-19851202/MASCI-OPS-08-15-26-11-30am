# TRAINING GAP REGISTER
## OCEP · Training Completion Program (TCP)

**Date**: 2026-06-03
**Authority**: OMEGA · TCP
**Mode**: READ-ONLY · page-level training gap register
**Purpose**: For each platform page involved in the 19 workflows, record whether a brand-new employee can answer "What is this? · Why do I use it? · What happens next?" within 30 seconds using ONLY the page itself (no external coaching, no Jaymn).

Methodology: source-direct page inspection against the 3-question test. Verdict = PASS / FLAG. Gap reason cites the missing affordance.

Pages audited: the 32 primary pages referenced in the 19 workflows. Sub-pages and read-only views excluded.

---

## 1 · 32-page register

| # | Page (route) | Source file | What is this? (≤ 30s) | Why do I use it? (≤ 30s) | What happens next? (≤ 30s) | Verdict | Gap reason |
|---|---|---|:-:|:-:|:-:|---|---|
| 1 | `/daily-reports/new` | `NewDailyReport.jsx` | ✅ (page title) | ✅ (`HelpTipBlock formKey="daily-report"`) | ✅ (post-iter453.7 sticky footer + status pill on success) | **PASS** | — |
| 2 | `/daily-reports` (list) | `DailyReports.jsx` | ✅ | 🟡 (status meaning of "Pending Office Review" not inline-explained) | 🟡 (kickback reason hidden in history drawer) | **FLAG** | Kickback reason not on tile preview (AR-0003) |
| 3 | `/jha` (public) | `JhaPlansHub.jsx` | ✅ | ✅ (`HelpTipBlock` + identity strip post-FOCP R2) | ✅ (modal copy explains attestation) | **PASS** | — |
| 4 | `/admin/jha-acknowledgements` | `AdminJhaAcknowledgements.jsx` | ✅ (page title) | 🟡 (no entry-point tip) | ✅ (drill-in / drill-by-employee labels) | **FLAG** | Brand-new surface (FOCP R2); no admin coaching primer (AR-0021) |
| 5 | `/incidents/new` | `NewIncident.jsx` | ✅ | ✅ | ✅ (post-iter453 + iter500 sticky footer) | **PASS** | — |
| 6 | Incident detail (lifecycle panel) | `IncidentLifecyclePanel.jsx` | ✅ | 🟡 (closure attestation flags have labels but no per-flag definition) | ✅ (history drawer + Undo button) | **FLAG** | AR-0016 attestation-flag definitions missing |
| 7 | `/meetings/new` | `NewMeeting.jsx` | ✅ | 🟡 (no `mistake` kind on `meeting` form_key) | 🟡 (post-submit destiny unclear without coaching) | **FLAG** | Phase 2 P1 `mistake` gap + post-submit guidance |
| 8 | `/meetings` (list) | `MeetingsDashboard.jsx` | ✅ | 🟡 | 🟡 | **FLAG** | Same as #7 |
| 9 | `/qaqc-inspections/new` | `NewQaqcInspection.jsx` | ✅ | ✅ | 🟡 (3-path closure not taught) | **FLAG** | Phase 2 P4 closure-path coaching missing |
| 10 | QA/QC detail (lifecycle panel) | `QaqcLifecyclePanel.jsx` | ✅ | 🟡 | 🟡 (3-path closure unclear which path applies) | **FLAG** | Phase 2 P4 |
| 11 | `/inspections/new` | `NewInspection.jsx` | ✅ | ✅ | 🟡 | **FLAG** | Same shape as QA/QC; `FINDINGS_RAISED` vs `DEFICIENCY_RAISED` vocab risk (AR-0007) |
| 12 | Site Inspection detail | `SiteInspectionLifecyclePanel.jsx` | ✅ | 🟡 | 🟡 | **FLAG** | Same as #10 |
| 13 | `/admin/dispatch` | `AdminDispatchBoard.jsx` | ✅ (page title) | 🟡 (no parent `dispatch` tip) | 🟡 (driver shift-start QR + Day-1 debrief flow not narrated at entry) | **FLAG** | Phase 2 §1.6 — dispatch parent tip absent (P5) |
| 14 | Driver shift-start (QR) | Driver pages | ✅ | ✅ | 🟡 | **FLAG** | Driver pages mostly action-only; new driver unclear what happens after scan |
| 15 | `/admin/fleet` (repair) | Fleet pages | ✅ | 🟡 | 🟡 | **FLAG** | Phase 2 §1.12 P3 — Shop/Fleet thinnest coverage; severity-tier model undocumented |
| 16 | `/admin/fleet` (RTS) | Fleet pages | ✅ | 🟡 | 🟡 | **FLAG** | Same as #15 |
| 17 | `/admin/equipment` (pre-shift) | Equipment pages | ✅ | 🟡 (no `mistake` kind) | 🟡 | **FLAG** | Phase 2 P1 |
| 18 | Equipment issuance | `equipment-issuance.*` form_keys | ✅ | ✅ | ✅ (acknowledgment has `mistake` kind) | **PASS** | — |
| 19 | Equipment training records | HR Training Records | ✅ | ✅ | ✅ | **PASS** | — |
| 20 | `/admin/hr` (HR Hub) | `HrHub.jsx` | ✅ | ✅ | ✅ (drill tiles labeled) | **PASS** | — |
| 21 | `/admin/hr/time-off` | `HrTimeOff.jsx` | ✅ (page title) | 🟡 | 🟡 (approval mechanism uncoached) | **FLAG** | Phase 2 §1.19 — Approvals-class FAIL |
| 22 | `/time-off` (public) | `PublicTimeOff.jsx` | ✅ | ✅ | ✅ (success state visible post-submit) | **PASS** | — |
| 23 | `/admin/hr/employees` | `HrEmployees.jsx` | ✅ | ✅ | ✅ (reactivate-vs-rehire tip PASS) | **PASS** | — |
| 24 | `/admin/hr/employee-requests` | `HrEmployeeRequestsQueue.jsx` | ✅ | 🟡 | 🟡 | **FLAG** | Phase 2 P2 — Approvals-class |
| 25 | `/admin/po-requests` | `PoRequests.jsx` | ✅ (page title) | 🟡 | 🟡 | **FLAG** | Phase 2 P2 — Approvals-class |
| 26 | `/asset-transfers` | `AssetTransfers.jsx` | ✅ | 🟡 | 🟡 | **FLAG** | Phase 2 P2 — Approvals-class |
| 27 | `/admin/hr/payroll-variance` | `HrPayrollVariance.jsx` | ✅ | ✅ | 🟡 (3-attestation gate has labels but no per-flag definition) | **FLAG** | AR-0004 — attestation easy to tick without understanding |
| 28 | Payroll Variance lifecycle | `PayrollVarianceLifecyclePanel.jsx` | ✅ | ✅ | ✅ (Undo + history drawer) | **PASS** | — |
| 29 | `/constraints/new` | `NewConstraint.jsx` | ✅ | ✅ | ✅ (chronology + status PATCH evident) | **PASS** | — |
| 30 | Constraint detail | `ConstraintDetail.jsx` | ✅ | ✅ | ✅ (no reopen — doctrine-exempt; this is correct, not a gap) | **PASS** | — |
| 31 | `/submittals` (NOT-IMPLEMENTED) | — | ❌ | ❌ | ❌ | **NOT-IMPLEMENTED** | Page does not exist; PMs run submittals outside the platform |
| 32 | `/admin/vendors` / `/admin/suppliers` | Vendor admin pages | ✅ | ✅ | 🟡 (no archive workflow — TR-0003) | **FLAG** | TR-0003 — Sub/Vendor archive workflow missing |
| 33 | `/pm` (Project Management hub) | `PmHub.jsx` | ✅ | ✅ | ✅ | **PASS** | — |
| 34 | `/admin/recovery-stream` | `AdminRecoveryStream.jsx` | ✅ (page title) | ✅ (subtitle on page) | ✅ (rows self-explain via labels) | **PASS-by-doctrine** | Admin-only; FOCP R2 § 8 declares English-canonical |

---

## 2 · Aggregate metrics

| Category | Count |
|---|---:|
| Pages audited | 33 (Submittals counted as NOT-IMPLEMENTED) |
| PASS | 12 |
| PASS-by-doctrine | 1 (Recovery Stream) |
| FLAG | 19 |
| NOT-IMPLEMENTED | 1 (Submittals) |

**Pass rate**: (12 + 1) / 33 = **39%**

---

## 3 · Gaps clustered by root cause

| Root cause | Pages affected | Phase 2 reference |
|---|---|---|
| `mistake` kind absent on parent form_key | #7, #8, #17, #21, #24, #25, #26 (7 pages) | P1 |
| Approvals-class has no coaching at all | #21, #24, #25, #26 (4 pages — overlap with P1) | P2 |
| QA/QC + Site Inspection 3-path closure unexplained | #9, #10, #11, #12 (4 pages) | P4 |
| Dispatch parent tip absent | #13, #14 (2 pages) | P5 |
| Fleet/Shop thin coverage | #15, #16, #17 (3 pages — partial overlap) | P3 |
| Kickback reason / status meaning hidden | #2 (1 page) | AR-0003 |
| Attestation-flag definitions missing | #6, #27 (2 pages) | AR-0004, AR-0016 |
| New post-FOCP-R2 surface lacks primer | #4 (1 page) | AR-0021 |
| Vendor archive workflow missing | #32 (1 page) | TR-0003 |
| Workflow not implemented | #31 (1 page) | Out-of-scope under FOCP |

---

## 4 · 30-second test fail probability (source-direct only)

For each FLAG page, the source-direct probability that a brand-new employee fails the 30-second test:

| Probability tier | Pages |
|---|---|
| HIGH (no inline coaching at all on the core question) | #7, #8, #21, #24, #25, #26 (6 pages) |
| MEDIUM (partial coaching but key term/path missing) | #2, #4, #9, #10, #11, #12, #13, #14, #15, #16, #17, #27, #32 (13 pages) |

This is source-direct probability, not observed behavior. Real interviews (`REALITY_VALIDATION_INTERVIEW_PLAYBOOK.md`) are the only mechanism that converts this to evidence.

---

## 5 · Truth Register classification

Per OMEGA TRUTH REGISTER RULE, this register adds the following classifications:

| Cluster | TR classification |
|---|---|
| `mistake` kind absent across 7+ pages | **ACTIVE** (Phase 2 P1) |
| Approvals-class coaching absent | **ACTIVE** (Phase 2 P2) |
| Fleet/Shop coverage thinness | **ACTIVE** (Phase 2 P3) |
| QA/QC + Site Inspection 3-path closure coaching | **ACTIVE** (Phase 2 P4) |
| Dispatch parent tip absent | **ACTIVE** (Phase 2 P5 new) |
| AR-0003 / AR-0004 / AR-0016 / AR-0021 | **ACTIVE** (already in `ADOPTION_RISK_REGISTER`) |
| Submittals (NOT-IMPLEMENTED) | **DEFERRED** (out-of-scope under FOCP Final Directive) |
| Vendor archive (TR-0003) | **ACTIVE** (already in TRUTH_REGISTER) |
| Constraint reopen | **DOCTRINE-EXEMPT** (TR-0007) |

No new engineering work authorized.

---

**End of TRAINING GAP REGISTER · TCP**
