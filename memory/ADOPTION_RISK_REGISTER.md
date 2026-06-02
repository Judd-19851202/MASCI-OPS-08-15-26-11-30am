# ADOPTION RISK REGISTER
## OCEP Phase 6 · Operational Completion Evidence Program

**Date opened**: 2026-06-02
**Authority**: OMEGA · OCEP
**Mode**: READ-ONLY · evidence register
**Status**: Seeded with source-derived candidates · awaits operator confirmation
**Scope**: Identify every condition that reduces or threatens platform adoption

---

## 0 · Doctrine

Adoption fails one user at a time. A single confusing surface that 3 Foremen hit on the first Monday becomes 3 support calls, 3 paper workarounds, and a permanent reputational tax on the platform. This register is the catalog of those risks so they are visible, ranked, and individually attributable.

Risks below are CANDIDATES seeded from the AI agent's source-direct read of the current platform. **The operator confirms or refutes each.** AI-inferred risks have no standing without operator confirmation.

---

## 1 · Risk taxonomy

Each risk has:
- ID: `AR-NNNN`
- Category: SUPPORT-CALL-GENERATOR · CONFUSING-WORKFLOW · HIDDEN-WORKFLOW · POOR-DISCOVERABILITY · WEAK-GUIDANCE · TRANSLATION-RISK · TRAINING-GAP
- Severity: CRITICAL · HIGH · MEDIUM · LOW
- Affected personas: subset of {Laborer, Foreman, Super, PM, Safety, Dispatch, HR, Shop, Executive}
- Evidence: file path + line OR observed behavior + interview ID
- Status: CANDIDATE (AI-seeded) · CONFIRMED (operator-validated) · REFUTED (operator-rejected) · CLOSED (remediated)
- Recommended action: from the menu in `TRIBAL_KNOWLEDGE_ELIMINATION_REGISTER.md` §5 — or NOOP-WITH-REASON

---

## 2 · Severity rubric

| Severity | Definition | Action timeline |
|---|---|---|
| CRITICAL | A risk that could cause safety exposure, OSHA violation, payroll error, or workflow abandonment | Halt Phase 7 certification |
| HIGH | A risk that drives ≥ 1 support call per week or visible adoption regression | Remediate within 14 days |
| MEDIUM | A risk that drives occasional confusion but operators self-recover | Remediate within 60 days |
| LOW | A risk that creates friction but no failure | Backlog; no cert block |

---

## 3 · Source-seeded risk candidates (AI-derived · operator must confirm)

These are candidates the AI agent identified during the OMEGA program. Each is sourced from the current platform's verifiable state. Status: all CANDIDATE until operator confirms.

### 3.1 · SUPPORT-CALL-GENERATOR candidates

| ID | Risk | Severity | Personas | Evidence | Status |
|---|---|---|---|---|---|
| AR-0001 | Operators don't know whether a closed lifecycle record can be reopened or undone — both verbs exist but vocabulary differs across panels | MEDIUM | All write-side roles | Reopen modals (per-panel) + Undo button (post-FOCP R2, cross-panel · `UndoLastTransitionButton.jsx`). Buttons are adjacent but use different language. | CANDIDATE |
| AR-0002 | "Pending Review" (DR), "Pending Closure" (Incident), "Pending Re-Inspection" (QA/QC + Site Inspection) all read similarly to non-power users — confusable cross-workflow | MEDIUM | PM, Foreman | `statusBadges.js` STATE labels post-FOCP R1 disambiguate, but lifecycle panel headings re-introduce the ambiguity (per-workflow titles) | CANDIDATE |
| AR-0003 | DR returned-to-field (PENDING_REVIEW → OPEN) requires reason ≥ 5 chars — when Foreman receives it, the kickback reason is not visible in the Hub tile preview | HIGH | Foreman | `daily_report_lifecycle.py` requires reason; `LifecyclePanel.jsx` shows reason inside history drawer (1 click); Hub tile shows status only | CANDIDATE |
| AR-0004 | Payroll Variance attestation flags (`review_complete`, `approval_complete`, `variance_decisions_complete`) are 3 checkboxes in one modal — easy to tick without understanding | HIGH | HR / Admin | `workflow_state_machine.py:367` enforces all 3 but doctrine requires each be a separate operator-led decision | CANDIDATE |
| AR-0005 | "Restore" / "Reactivate" / "Reopen" / "Undo" are 4 different recovery verbs used across the platform — operators conflate them | MEDIUM | All admin roles | `/admin/employees/{id}/restore` (server.py:3310) · HR canonical Reactivate · per-workflow Reopen · FOCP R2 Undo | CANDIDATE |

### 3.2 · CONFUSING-WORKFLOW candidates

| ID | Risk | Severity | Personas | Evidence | Status |
|---|---|---|---|---|---|
| AR-0006 | QA/QC closure offers 3 mutually-exclusive paths (re-inspection / corrective-action / exception with dual sign-off) — operator must pick one | HIGH | PM, Safety | `workflow_state_machine.py:436-463` Amendment 001 REPLACE-5 | CANDIDATE |
| AR-0007 | Site Inspection closure is structurally symmetric to QA/QC but uses "FINDINGS_RAISED" instead of "DEFICIENCY_RAISED" — easy to confuse | MEDIUM | PM, Safety | `workflow_state_machine.py:526-540` | CANDIDATE |
| AR-0008 | Daily Report's office review (PENDING_REVIEW → REVIEWED → CLOSED) is currently admin-only — PM operators may expect to drive it | MEDIUM | PM | `workflow_state_machine.py:230-236` `_DR_ROLES` admin/super_admin only on review steps | CANDIDATE |
| AR-0009 | JHP acknowledgement uses email-as-identity-key (post-FOCP R2) — Spanish-only crew without work email may struggle | HIGH | Laborer (Spanish-only) | `routes/jha_acknowledgements.py:_resolve_employee` requires `email` or `employee_id` | CANDIDATE |
| AR-0010 | Universal Undo is admin-only by doctrine — Safety / PM operators may expect to undo and discover they can't | MEDIUM | Safety, PM | `routes/workflow_undo.py` `require_admin_dep=require_admin`; FOCP R2 TR-0002 bundle §5 declares the doctrine | CANDIDATE |

### 3.3 · HIDDEN-WORKFLOW candidates

| ID | Risk | Severity | Personas | Evidence | Status |
|---|---|---|---|---|---|
| AR-0011 | `/admin/recovery-stream` (post-FOCP R2) is a new admin page not linked from any hub | HIGH | Admin | `App.js:404` routes registered; `AdminHub.jsx` sections not updated | CANDIDATE |
| AR-0012 | `/admin/jha-acknowledgements` (post-FOCP R2) is a new admin page not linked from any hub | HIGH | Admin / Safety / PM | Same as AR-0011 | CANDIDATE |
| AR-0013 | Operational Constraints reopen path absent by doctrine (TR-0007) — operators may search for it and not find it | LOW | All admin write roles | TR-0007 ACTIVE-PRODUCT-DECISION | CANDIDATE |

### 3.4 · POOR-DISCOVERABILITY candidates

| ID | Risk | Severity | Personas | Evidence | Status |
|---|---|---|---|---|---|
| AR-0014 | Approval surfaces (Time-off, Employee Requests, PO Requests, Asset Transfers) live in different sub-hubs — no unified "approvals" queue | MEDIUM | PM, Safety, Admin | `HrTimeOff.jsx`, `HrEmployeeRequestsQueue.jsx`, `PoRequests.jsx`, `AssetTransfers.jsx` (4 surfaces, no roll-up) | CANDIDATE |
| AR-0015 | History drawer (lifecycle audit) is hidden behind a History button on each panel — operators expecting an always-visible timeline don't find it | LOW | Safety, Admin | All 5 lifecycle panels gate history behind a modal | CANDIDATE |

### 3.5 · WEAK-GUIDANCE candidates

| ID | Risk | Severity | Personas | Evidence | Status |
|---|---|---|---|---|---|
| AR-0016 | Closure attestation flags (Incident, DR, PV) have no per-flag definition — labels alone | MEDIUM | Safety, HR | `IncidentLifecyclePanel.jsx:282-296` labels-only checkboxes | CANDIDATE |
| AR-0017 | QA/QC exception path (closure path C) requires a 10-char minimum on `exception_reason` and dual sign-off but the UI doesn't explicitly state these constraints up-front | HIGH | PM, Safety | Constraints enforced server-side (`workflow_state_machine.py:454-462`) but UI surfaces them as errors only post-submit | CANDIDATE |
| AR-0018 | Operator Confidence — current platform has NO single answer to "Am I good?" for any role | HIGH | All | OCEP Phase 4 specification confirms this is not built | CANDIDATE |

### 3.6 · TRANSLATION-RISK candidates

| ID | Risk | Severity | Personas | Evidence | Status |
|---|---|---|---|---|---|
| AR-0019 | JHP acknowledgement modal (FOCP R2) was newly added with Spanish parity strings but has not been native-speaker reviewed | HIGH | Laborer (Spanish) | i18n.js post-FOCP R2 additions (~20 keys); reviewer not yet engaged | CANDIDATE |
| AR-0020 | Universal Undo button + admin Recovery Stream are English-only by FOCP R2 doctrine — confirmed correct for admin chrome but creates an English-Spanish boundary mid-app | LOW | None (admin-only) | FOCP_COMPLETION_RELEASE_2_TR0002_BUNDLE.md §8 | CANDIDATE |

### 3.7 · TRAINING-GAP candidates

| ID | Risk | Severity | Personas | Evidence | Status |
|---|---|---|---|---|---|
| AR-0021 | FOCP Release 1 (status canonicalization) introduced new status labels not yet reflected in any training material | MEDIUM | All write-side | `statusBadges.js` post-FOCP R1; training inventory empty (Phase 2) | CANDIDATE |
| AR-0022 | FOCP Release 2 (TR-0001 + TR-0002) is brand new (2026-06-02) — no training exists | HIGH | Admin, Safety, Laborer, Foreman | FOCP R2 bundles · same-day release | CANDIDATE |
| AR-0023 | Amendment 001 REPLACE-4/5 closure contract for QA/QC + Site Inspection adds operator decision points not in any training material | HIGH | PM, Safety | `workflow_state_machine.py:436-463` + Amendment 001 docs | CANDIDATE |

---

## 4 · Aggregate scoring

| Composite | Calculation | Threshold |
|---|---|---|
| **Critical risks open** | Count of CRITICAL with status CANDIDATE/CONFIRMED | Must be 0 to certify |
| **High risks open** | Count of HIGH not in CLOSED | Must be ≤ 3 |
| **Total adoption risks** | Total CANDIDATE + CONFIRMED | — |
| **Operator confirmation rate** | Count CONFIRMED / count CANDIDATE | Indicates audit completeness |

---

## 5 · Promotion / refutation protocol

When the operator works this register, each row moves:

- **CANDIDATE → CONFIRMED** when observed in real operator interviews (Phase 1) or hands-on dry-run (Phase 5)
- **CANDIDATE → REFUTED** when the operator confirms the risk does not manifest in real operations OR that the inline aid is sufficient
- **CONFIRMED → CLOSED** when the recommended action is executed AND verified by re-test
- **CONFIRMED → DEFERRED-WITH-REASON** when explicitly accepted as known-risk under specific conditions

The AI agent CANNOT move rows from CANDIDATE to CONFIRMED. Only the operator.

---

## 6 · Operator confirmation worksheet (paste-in template)

For each row above, the operator records:

```
ID: AR-NNNN
Confirmed by: <initials>
Evidence type: ☐ Interview · ☐ Dry-run · ☐ Support log · ☐ Other
Affected personas (actual): <subset>
Recommended action: <from menu>
Authorization status: ☐ Authorized · ☐ Backlog · ☐ NOOP-with-reason
Reason: ___________
```

---

## 7 · Refusal conditions

The AI agent MUST refuse to:
- Promote a row from CANDIDATE to CONFIRMED on its own
- Mark a row CLOSED without evidence of re-test
- Generate new risk candidates outside the source-direct method (AI-inferred risks are not admissible)
- Recommend an action that bypasses the 7-test + 4-proof clearance for any build-class remediation

---

**End of ADOPTION RISK REGISTER · OCEP Phase 6**
