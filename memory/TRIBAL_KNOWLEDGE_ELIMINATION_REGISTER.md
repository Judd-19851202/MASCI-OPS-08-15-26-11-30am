# TRIBAL KNOWLEDGE ELIMINATION REGISTER
## OCEP Phase 5 · Operational Completion Evidence Program

**Date opened**: 2026-06-02
**Authority**: OMEGA · OCEP
**Mode**: READ-ONLY · evidence register
**Status**: Awaits operator-led classification per workflow
**Scope**: Determine whether a new employee can complete each workflow without anyone showing them

---

## 0 · Doctrine

"Tribal knowledge" is anything an employee must learn from another human to operate the platform successfully. Tribal knowledge is the enemy of 90-day operational independence and of Customer #2 readiness.

This register classifies every workflow on the platform as:

- **YES** — A new employee with the appropriate role token and zero prior platform exposure can complete this workflow start-to-end using only what the platform itself provides (tooltips, help blocks, inline guidance, labels, error messages).
- **PARTIAL** — Completable, but the employee must consult one external resource (Skywork video, SOP PDF, knowledge base, a peer).
- **NO** — Completable only with verbal hand-holding from an experienced operator (Jaymn, a senior PM, etc.).

`NO` is the explicit anti-pattern. Every `NO` is a 90-day independence risk and a Customer #2 onboarding landmine.

The AI agent CANNOT score this register. Only an operator-led observation of a new-employee dry run can produce a verdict. The AI agent provides the structure and the candidate workflow list (sourced from current source).

---

## 1 · Audit dimensions per workflow

For each workflow:

| Field | Definition |
|---|---|
| **Time-to-productivity (mins)** | Median time a new employee takes to complete this workflow correctly the first time (observed, not estimated) |
| **Support dependence** | Did the employee call / Slack / email someone during the attempt? 0 = none · 1+ = count |
| **Management dependence** | Did the employee require a manager to unblock? Y/N |
| **Jaymn dependence** | Did Jaymn's name come up as the unlock? Y/N |
| **Inline aid present** | Tooltip / Help block / coaching exists ON the surface? Y/N |
| **Error message clarity** | Did the error messages, if any, lead to the recovery path? Y/N/N-A |
| **Verdict** | YES / PARTIAL / NO |

---

## 2 · Workflow audit register (29 workflows + 5 universal verbs)

### 2.1 · Lifecycle workflows (with state machines)

| # | Workflow | Owner role | TTP (min) | Support? | Mgmt? | Jaymn? | Inline aid? | Verdict |
|---|---|---|---:|---:|---|---|---|---|
| 1 | Daily Report submission (OPEN → PENDING_REVIEW) | Foreman / PM |  |  |  |  |  |  |
| 2 | Daily Report office review (PENDING_REVIEW → REVIEWED → CLOSED) | Admin / Office |  |  |  |  |  |  |
| 3 | Daily Report return-to-field (PENDING_REVIEW → OPEN) | Admin |  |  |  |  |  |  |
| 4 | Incident submission (public) | Anyone |  |  |  |  |  |  |
| 5 | Incident investigation (OPEN → UNDER_INVESTIGATION) | Safety / Admin |  |  |  |  |  |  |
| 6 | Incident CAPA workflow | Safety / PM |  |  |  |  |  |  |
| 7 | Incident closure (PENDING_CLOSURE → CLOSED · 3 attestations + OSHA ack) | Safety / Admin |  |  |  |  |  |  |
| 8 | Incident reopen (CLOSED → UNDER_INVESTIGATION · reason required) | Safety / Admin |  |  |  |  |  |  |
| 9 | QA/QC deficiency intake | PM / Safety |  |  |  |  |  |  |
| 10 | QA/QC closure path A (re-inspection passed) | PM / Safety |  |  |  |  |  |  |
| 11 | QA/QC closure path B (corrective action ≥ 20 chars) | PM / Safety |  |  |  |  |  |  |
| 12 | QA/QC closure path C (exception with dual sign-off) | PM + Safety |  |  |  |  |  |  |
| 13 | Site Inspection finding closure | PM / Safety |  |  |  |  |  |  |
| 14 | Payroll Variance review (OPEN → UNDER_REVIEW) | HR |  |  |  |  |  |  |
| 15 | Payroll Variance approve (UNDER_REVIEW → APPROVED) | HR |  |  |  |  |  |  |
| 16 | Payroll Variance finalize (APPROVED → FINALIZED · 3 attestations) | Admin |  |  |  |  |  |  |
| 17 | Repair lifecycle | Shop |  |  |  |  |  |  |
| 18 | Dispatch lifecycle | Dispatch |  |  |  |  |  |  |
| 19 | Employee lifecycle (new hire) | HR |  |  |  |  |  |  |
| 20 | Employee reactivate vs rehire (write-once original_hire_date) | HR |  |  |  |  |  |  |

### 2.2 · Public-submission workflows

| # | Workflow | TTP | Support? | Mgmt? | Jaymn? | Inline aid? | Verdict |
|---|---|---:|---:|---|---|---|---|
| 21 | JHP acknowledgement (post-FOCP R2) |  |  |  |  |  |  |
| 22 | Time-off request submission |  |  |  |  |  |  |
| 23 | Employee request submission |  |  |  |  |  |  |
| 24 | Equipment pre-shift inspection |  |  |  |  |  |  |
| 25 | Driver shift-start QR |  |  |  |  |  |  |

### 2.3 · Admin / review workflows

| # | Workflow | TTP | Support? | Mgmt? | Jaymn? | Inline aid? | Verdict |
|---|---|---:|---:|---|---|---|---|
| 26 | PO Request approve / reject |  |  |  |  |  |  |
| 27 | Asset Transfer receive / reject |  |  |  |  |  |  |
| 28 | JHP supervisor visibility drill (post-FOCP R2) |  |  |  |  |  |  |
| 29 | Recovery Stream cross-workflow read (post-FOCP R2) |  |  |  |  |  |  |

### 2.4 · Universal verbs (cross-workflow, post-FOCP)

| # | Verb | TTP | Support? | Mgmt? | Jaymn? | Inline aid? | Verdict |
|---|---|---:|---:|---|---|---|---|
| 30 | Undo last status change (admin · 5 lifecycles) |  |  |  |  |  |  |
| 31 | Reopen any closed record (across all lifecycles) |  |  |  |  |  |  |
| 32 | Restore archived employee / supplier |  |  |  |  |  |  |
| 33 | Reactivate an offline equipment unit |  |  |  |  |  |  |
| 34 | Acknowledge a Job Hazard Plan version revision |  |  |  |  |  |  |

---

## 3 · Scoring composite

| Composite | Calculation |
|---|---|
| **% YES** | YES count / 34 |
| **% PARTIAL** | PARTIAL count / 34 |
| **% NO** | NO count / 34 |
| **Jaymn touch count** | Sum of Jaymn? = Y across all rows |
| **Median TTP** | Median time-to-productivity across all workflows |

### 3.1 · Thresholds for 90-day independence

| Composite | Target |
|---|---|
| % NO | 0 |
| % PARTIAL | ≤ 30 |
| % YES | ≥ 70 |
| Jaymn touch count | ≤ 2 (across the full 34-workflow set) |
| Median TTP | ≤ 5 minutes per workflow |

Any `NO` row blocks Final Operational Certification. Each `NO` must be:
1. Re-evaluated to see if existing inline aid is actually present but not discovered (Phase 2 audit cross-check)
2. Remediated through training (Priority 2) OR re-authorized as a build (Priority 3+, requires 7-test + 4-proof clearance)

---

## 4 · Common tribal-knowledge anti-patterns to watch for

When the operator runs the audit, the following observation signals likely indicate `NO`:

| Signal | Why it's tribal knowledge |
|---|---|
| Employee says "Jaymn told me to click here" | Verbal-only routing |
| Employee opens a notes app to look up something | Knowledge lives outside the platform |
| Employee texts a peer asking what the status field means | Status vocabulary is tribal |
| Employee guesses and clicks the wrong button | No inline aid prevented the mis-action |
| Employee abandons the workflow and uses paper | The platform doesn't carry them through |
| Employee asks "is this saved?" after clicking Save | Feedback / confirmation surface is invisible |
| Employee asks "did this go to the right person?" | Routing is not surfaced |
| Employee asks "can I undo this?" | Undo is not surfaced (FOCP R2 closed this for 5 workflows + JHP audit; verify) |

Each of these is a finding worth a register row even if the employee ultimately completes the workflow.

---

## 5 · Workflow-by-workflow remediation register (operator fills)

| # | Workflow | Verdict | Root cause | Recommended action | Authorization status |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

Recommended actions must be drawn from this menu (per FOCP Final Directive):

- **TRAIN** → Priority 2 training material refresh
- **TRANSLATE** → Priority 2 Spanish parity correction
- **COACH** → Add inline `HelpTip` or coaching block (build action, requires 7-test + 4-proof)
- **LABEL** → Status / button label change (build action, requires 7-test + 4-proof)
- **REORDER** → Step sequence change (build action, requires 7-test + 4-proof + state-machine review)
- **NOOP-WITH-REASON** → Workflow is fine; the observation was an operator-population issue, not a platform issue

---

## 6 · Refusal conditions

The AI agent MUST refuse to:
- Mark workflows as YES / PARTIAL / NO based on AI inference
- Backfill Jaymn dependence count without observed evidence
- Recommend a remediation action that is not in the menu in §5
- Advance Final Certification with any `NO` row open

---

**End of TRIBAL KNOWLEDGE ELIMINATION REGISTER · OCEP Phase 5**
