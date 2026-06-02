# FINAL OPERATIONAL CERTIFICATION PACKAGE
## OCEP Operational Completion Sprint · Phase 6

**Date**: 2026-06-02
**Authority**: OMEGA · OPERATIONAL COMPLETION SPRINT
**Mode**: READ-ONLY · certification framework
**Status**: Framework complete · signatures pending evidence
**Purpose**: 10 role/scope certifications that together attest the platform is operationally complete

---

## 0 · How this package is used

Each of the 10 certifications below is a stand-alone attestation. A certification is "signed" only when:
1. Its **Pass Criteria** are met
2. Its **Evidence Requirements** are satisfied by referenced artifacts
3. Its **Failure Criteria** are all absent
4. The named **Verifier** signs and dates

The 10 certifications, when all signed, constitute the FORGEDOPS Operational Completion (FOC) certification. Until all 10 are signed, the platform is NOT operationally complete.

The AI agent CANNOT sign any of these. The operator (Jaymn or designee) is the Verifier for all certifications except Customer #2 (Verifier is the Customer #2 stand-in from the tabletop) and New Employee (Verifier is a real new hire on day 90).

---

## 1 · FOREMAN CERTIFICATION

```
Foreman Certification

Pass Criteria
─────────────
[ ] Foreman can submit a Daily Report start-to-end without consulting another human
[ ] Foreman can read kickback reasons in the lifecycle history drawer without coaching
[ ] Foreman can confirm crew JHP acknowledgement coverage for today's job
[ ] Foreman can report a first-on-scene incident in ≤ 5 minutes
[ ] Foreman can flag an equipment defect with severity classification

Evidence Requirements
─────────────────────
[ ] Phase 1 Foreman interview file: /app/memory/interviews/foreman_*.md exists
[ ] Foreman persona readiness score ≥ 70
[ ] Phase 5 Tribal Knowledge register has zero NO rows assigned to Foreman
[ ] Phase 2 Training Reality verdict for Daily Report ≥ PARTIAL (verified by remediation, not just verdict)
[ ] Phase 6 Adoption Risk Register: zero CRITICAL/HIGH rows confirmed for Foreman workflows

Failure Criteria (any one = certification FAILS)
─────────────────────────────────────────────────
[ ] Foreman names Jaymn as the recovery path for any workflow
[ ] Foreman maintains paper Daily Report alongside digital
[ ] Foreman submission TTP > 15 minutes for routine DR

Operator Signoff
────────────────
Verifier   : ___________________________
Date       : ___________________________
Signature  : ___________________________
Score      : ___ / 100   (composite from evidence)
Conditions : ___________________________
```

---

## 2 · SUPERINTENDENT CERTIFICATION

```
Superintendent Certification

Pass Criteria
─────────────
[ ] Super can see every stuck DR across their jobs from one screen
[ ] Super can see every open incident across their jobs from one screen
[ ] Super can reassign equipment cross-job with an audit trail
[ ] Super can answer "Am I good?" in ≤ 3 seconds on the device they use

Evidence Requirements
─────────────────────
[ ] Phase 1 Superintendent interview file exists; score ≥ 70
[ ] Phase 4 Confidence Layer status for Super = (gate G1-G6 evaluated; explicit decision: BUILD-AUTHORIZED or NO-LAYER-NEEDED)
[ ] Phase 5 Tribal Knowledge: zero NO rows for cross-job navigation workflows

Failure Criteria
────────────────
[ ] Super maintains parallel Excel for job tracking
[ ] Super calls Office for status that should be on-screen
[ ] Super uses platform only when prompted by email

Operator Signoff
────────────────
Verifier   : ___________________________
Date       : ___________________________
Signature  : ___________________________
Score      : ___ / 100
Conditions : ___________________________
```

---

## 3 · PROJECT MANAGER CERTIFICATION

```
PM Certification

Pass Criteria
─────────────
[ ] PM can see every overdue CAPA they own in one screen
[ ] PM can see JHP coverage per project on their portfolio
[ ] PM can approve/reject all 4 approval surfaces (Time-off · POs · Asset Transfers · Employee Requests) without coaching
[ ] PM can identify a stuck DR and unblock it (within their role authority)
[ ] PM can run the platform from a phone in the field

Evidence Requirements
─────────────────────
[ ] Phase 1 PM interview file exists; score ≥ 70
[ ] Phase 2 Approvals-class workflows have at minimum PARTIAL coaching (currently FAIL — must remediate to PARTIAL minimum before PM certification)
[ ] Phase 6 Adoption Risk Register: zero CRITICAL rows confirmed on PM-owned workflows
[ ] Phase 5 Tribal Knowledge: zero NO rows on PM workflows

Failure Criteria
────────────────
[ ] PM names Jaymn as the recovery path on any owned workflow
[ ] PM maintains parallel spreadsheets for CAPA tracking
[ ] PM's "Am I good?" answer requires > 4 clicks

Operator Signoff
────────────────
Verifier   : ___________________________
Date       : ___________________________
Signature  : ___________________________
Score      : ___ / 100
Conditions : ___________________________
```

---

## 4 · SAFETY CERTIFICATION

```
Safety Certification

Pass Criteria
─────────────
[ ] Safety can triage every open incident and route to investigation in ≤ 5 minutes
[ ] Safety can close an OSHA-recordable cleanly using the 3-attestation gate
[ ] Safety can reopen any closed record with audit-defensible reason
[ ] Safety can verify JHP acknowledgement compliance per project
[ ] Safety can use the Universal Undo when needed
[ ] Safety can run the Recovery Stream audit visibility surface

Evidence Requirements
─────────────────────
[ ] Phase 1 Safety Manager interview file exists; score ≥ 75 (safety threshold is one tier higher than other personas — Safety carries OSHA legal exposure)
[ ] Phase 3 Spanish Parity for safety-tier surfaces (Domains 1, 2, 3, 5, 6): zero CRITICAL findings
[ ] Amendment 001 closure contract enforced (code-verified · already true as of 2026-06-02)
[ ] FOCP R2 Universal Undo + Recovery Stream available to Safety (note: currently admin-only — TR-D003 doctrine point on whether Safety should have undo authority requires operator decision)

Failure Criteria
────────────────
[ ] Any unauthorized closure pattern detected (code-impossible post-Amendment 001; verify with one audit run)
[ ] Safety maintains parallel incident spreadsheet
[ ] Safety closes deficiencies without re-inspection (code-impossible post-Amendment 001)

Operator Signoff
────────────────
Verifier   : ___________________________
Date       : ___________________________
Signature  : ___________________________
Score      : ___ / 100
Conditions : ___________________________
```

---

## 5 · HR CERTIFICATION

```
HR Certification

Pass Criteria
─────────────
[ ] HR can onboard a new employee start-to-end without coaching
[ ] HR can distinguish reactivate vs rehire and preserve original_hire_date correctly
[ ] HR can run payroll variance review → approve → request finalize without losing rows
[ ] HR can confirm driver qualification expirations weekly
[ ] HR can approve Time-off / Employee Requests with full audit trail

Evidence Requirements
─────────────────────
[ ] Phase 1 HR interview file exists; score ≥ 70
[ ] Phase 2 Training Reality for Employee Lifecycle = PASS (currently true · the only workflow at PASS)
[ ] Phase 2 Training Reality for Approvals class ≥ PARTIAL (currently FAIL — remediation candidate)
[ ] Phase 6 Adoption Risk Register: zero CRITICAL on HR workflows

Failure Criteria
────────────────
[ ] HR maintains parallel HRIS / spreadsheet
[ ] HR edits records directly (bypasses lifecycle)
[ ] HR finalizes variances without operator-led review

Operator Signoff
────────────────
Verifier   : ___________________________
Date       : ___________________________
Signature  : ___________________________
Score      : ___ / 100
Conditions : ___________________________
```

---

## 6 · DISPATCH CERTIFICATION

```
Dispatch Certification

Pass Criteria
─────────────
[ ] Dispatch can build tomorrow's board independently
[ ] Dispatch can confirm all drivers qualified for tomorrow before EOD today
[ ] Dispatch can reassign mid-shift with audit trail
[ ] Dispatch can see Shop offline-events in real time

Evidence Requirements
─────────────────────
[ ] Phase 1 Dispatch interview file exists; score ≥ 70
[ ] Phase 2 dispatch parent tip set exists (currently absent · remediation candidate)
[ ] Phase 5 Tribal Knowledge: zero NO rows on dispatch workflows

Failure Criteria
────────────────
[ ] Dispatch maintains paper magnet board alongside digital
[ ] Dispatcher uses text messages to foremen instead of platform
[ ] Dispatcher cannot answer "is tomorrow's board complete?"

Operator Signoff
────────────────
Verifier   : ___________________________
Date       : ___________________________
Signature  : ___________________________
Score      : ___ / 100
Conditions : ___________________________
```

---

## 7 · EXECUTIVE CERTIFICATION

```
Executive Certification

Pass Criteria
─────────────
[ ] Executive can answer "Is everything good today?" in ≤ 3 seconds on phone
[ ] Executive trusts the operator_digest emailed Monday
[ ] Executive learns operational news from the platform BEFORE external sources

Evidence Requirements
─────────────────────
[ ] Phase 1 Executive interview file exists; score ≥ 75 (higher bar because Executive's role is "trust")
[ ] Phase 4 Confidence Layer Executive role: status = NO-LAYER-NEEDED (existing AdminCommandCenter + Recovery Dashboard + digest) OR BUILD-AUTHORIZED with all 6 gates passed

Failure Criteria
────────────────
[ ] Executive learns about operational events from outside the platform
[ ] Executive maintains parallel KPI spreadsheet
[ ] Executive's first question every morning is "is everything OK?" and the platform doesn't answer

Operator Signoff
────────────────
Verifier   : ___________________________
Date       : ___________________________
Signature  : ___________________________
Score      : ___ / 100
Conditions : ___________________________
```

---

## 8 · NEW EMPLOYEE CERTIFICATION

```
New Employee Certification  (Verifier: a real Day-90 new hire)

Pass Criteria
─────────────
[ ] New employee on Day 90 can perform all role-specific workflows without coaching
[ ] New employee never names Jaymn as the recovery path
[ ] New employee never opens paper / Excel / non-platform tools
[ ] New employee describes the platform as "operable" (not "complex / confusing")

Evidence Requirements
─────────────────────
[ ] A real new hire onboarded under MASCI's current onboarding process completes Day-90
[ ] Phase 5 Tribal Knowledge dry-run conducted with this new hire
[ ] Phase 5 % YES ≥ 70 for the workflows this employee owns
[ ] Phase 5 Jaymn touch count = 0 for this employee

Failure Criteria
────────────────
[ ] New employee asked Jaymn ≥ 3 questions about workflows
[ ] New employee resorted to paper for any required workflow
[ ] New employee abandoned the platform for any required workflow

Operator Signoff
────────────────
Verifier (new hire) : ___________________________
Verifier role       : ___________________________
Onboarded on        : ___________________________
Day-90 date         : ___________________________
Signature           : ___________________________
Score               : ___ / 100
Conditions          : ___________________________
```

---

## 9 · CUSTOMER #2 READINESS CERTIFICATION

```
Customer #2 Readiness Certification

Pass Criteria
─────────────
[ ] Customer #2 Tabletop conducted (all 12 steps)
[ ] CUSTOMER2_TABLETOP_RISK_REGISTER.md: zero BLOCKER open
[ ] CUSTOMER2_TABLETOP_RISK_REGISTER.md: ≤ 2 CRITICAL open
[ ] Customer #2 Readiness Score (formula in Risk Register §6) ≥ 70

Evidence Requirements
─────────────────────
[ ] /app/memory/customer_2_tabletop_*.md exists with all 12 steps documented
[ ] Recorder signature present
[ ] All BLOCKER candidates from §3 of the Risk Register are CONFIRMED-and-resolved OR REFUTED
[ ] The 4 BLOCKER candidates (single-tenancy + hardcoded brand + admin pw + tenant bootstrap) are resolved or explicitly accepted as "Customer #2 not supported · MASCI-only platform"

Failure Criteria
────────────────
[ ] Any BLOCKER row CONFIRMED and open
[ ] Customer #2 Readiness Score < 70
[ ] Operator (Jaymn) cannot identify how Acme would self-serve onboarding

Operator Signoff
────────────────
Verifier             : ___________________________
Tabletop facilitator : ___________________________
Tabletop date        : ___________________________
Signature            : ___________________________
Score                : ___ / 100
Conditions / scope-limit decision: ___________________________

If Conditions = "MASCI-only platform — White Label deferred", this Certification is signed but
the FORGEDOPS Operational Completion certification is marked "Single-Tenant Operational
Completion" rather than "White-Label Ready".
```

---

## 10 · 90-DAY INDEPENDENCE CERTIFICATION

```
90-Day Independence Certification  (the ultimate test)

Pass Criteria
─────────────
[ ] MASCI operates 90 consecutive days without Jaymn engineering / configuration / data intervention
[ ] No operator-blocking issue requires Emergent / developer intervention during the 90 days
[ ] All Phase 1 personas continue to operate at ≥ their interview scores throughout
[ ] No regression on Phase 2 Training Reality verdicts
[ ] No regression on Phase 3 Spanish Parity Score
[ ] No regression on Phase 5 Tribal Knowledge % YES
[ ] No new TR engineering item opened that would have blocked any of the prior 9 certifications

Evidence Requirements
─────────────────────
[ ] All 9 prior certifications (Foreman, Super, PM, Safety, HR, Dispatch, Executive, New Employee, Customer #2) signed
[ ] 90-day operational log captured in /app/memory/90_day_independence_log.md
[ ] No JIRA / developer ticket opened against the platform during the 90 days for operational reasons (engineering changes for new-business reasons are excluded)
[ ] Operator declares the 90 days passed without escalation to Jaymn for platform-recovery reasons

Failure Criteria (any one = certification FAILS)
─────────────────────────────────────────────────
[ ] Any operational workflow required Jaymn / Emergent / developer intervention
[ ] Any role's persona score dropped during the 90 days
[ ] Any tribal-knowledge NO row emerged that was previously YES
[ ] Customer #2 status regressed

Operator Signoff (the FOC certification itself)
─────────────────────────────────────────────────
Verifier (operator) : ___________________________
Date 90 days began  : ___________________________
Date 90 days ended  : ___________________________
Signature           : ___________________________
Final declaration   : ☐ FORGEDOPS Operational Completion certified
                     ☐ Single-Tenant Operational Completion certified
                     ☐ NOT certified · evidence required
Conditions / caveats: ___________________________
```

---

## 11 · Certification matrix (one-glance summary)

| # | Certification | Verifier | Threshold | Evidence Artifact | Status |
|---|---|---|---|---|---|
| 1 | Foreman | Operator | Score ≥ 70 | `/app/memory/interviews/foreman_*.md` | ⬜ Pending |
| 2 | Superintendent | Operator | Score ≥ 70 | `/app/memory/interviews/superintendent_*.md` | ⬜ Pending |
| 3 | PM | Operator | Score ≥ 70 | `/app/memory/interviews/pm_*.md` | ⬜ Pending |
| 4 | Safety | Operator | Score ≥ 75 | `/app/memory/interviews/safety_*.md` | ⬜ Pending |
| 5 | HR | Operator | Score ≥ 70 | `/app/memory/interviews/hr_*.md` | ⬜ Pending |
| 6 | Dispatch | Operator | Score ≥ 70 | `/app/memory/interviews/dispatch_*.md` | ⬜ Pending |
| 7 | Executive | Operator | Score ≥ 75 | `/app/memory/interviews/executive_*.md` | ⬜ Pending |
| 8 | New Employee | Real Day-90 hire | Score ≥ 75 · Jaymn-touch = 0 | Phase 5 dry-run | ⬜ Pending |
| 9 | Customer #2 Readiness | Tabletop facilitator | Risk Score ≥ 70 · 0 BLOCKER | `/app/memory/customer_2_tabletop_*.md` | ⬜ Pending |
| 10 | 90-Day Independence | Operator | All 9 above signed · 90 days passed without Jaymn | All of the above + log | ⬜ Pending |

---

## 12 · Refusal conditions

The AI agent MUST refuse to:
- Sign any of the 10 certifications on the operator's behalf
- Mark any threshold met without the named evidence artifact present
- Average / weight / smooth scores to make a certification pass
- Issue a "conditional" 90-Day Independence certification (the test is binary)
- Pre-fill score fields from inference

---

**End of FINAL OPERATIONAL CERTIFICATION PACKAGE · OCEP Phase 6**
