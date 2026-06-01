# User Task Completion Audit · OMEGA Completeness Audit

**Batch:** OMEGA · Operational Completeness Audit · Phase 9
**Mode:** READ-ONLY
**Date:** 2026-06-01

---

## 1 · Headline

Of the 9 most operationally-critical user tasks, **3 cannot be completed in-platform** today. The user lands on a page, expects to finish the operational task, but is forced to call/email/Slack/admin-DB instead.

---

## 2 · "Can the user finish?" matrix

| User task | Surface | Can they finish? | Where they get stuck |
|---|---|---|---|
| **Safety closes an incident** | Safety portal → `/safety-portal/incidents/:id` | ❌ NO | No close button. No close API. Sandy can't even mark it "investigating". |
| **HR closes a payroll variance batch** | HR → `/hr/payroll-variance` | ❌ NO | Sandy can decide every row; the batch itself never closes (no finalize endpoint) |
| **PM resolves a PO issue (clarification → approve → close)** | PM → `/po-requests/:id` | ✅ YES | All transitions wired |
| **Shop clears a Pre-Op defect** | Shop → `/shop` → Open Items | ✅ YES | Signoff endpoint working |
| **Field Leadership completes an assigned workflow** | `/leadership` | n/a — FL only files; transitions belong to others | n/a |
| **Admin sees why something is blocked (e.g. incident delete with linked CAPA)** | `/admin/incidents/:id` → 🗑️ | 🟡 PARTIAL | 409 with `linked_capa_count` is returned but UI shows a generic error toast in some surfaces |
| **PM approves an Asset Transfer (request → in-transit → receive → close)** | `/asset-transfers/:id` | ✅ YES | All transitions wired |
| **Safety officer marks JHA acknowledged by crew** | `/jha` | ❌ NO | Read-only library; no per-crew acknowledgement ledger |
| **Foreman files a QA/QC inspection deficiency and PM marks it resolved** | `/qa-qc/new` → admin review | ❌ NO | Create works · no resolve surface |
| **HR completes employee offboarding (return PPE, deactivate access, exit interview)** | `/hr/employees/:id/offboarding-summary` | 🟡 PARTIAL | Status mutator + summary exist; no checklist surface forcing the four steps |
| **Safety officer manages Fire Extinguisher monthly inspection** | `/safety/fire-extinguishers/:id` | ✅ YES | Full inspection + history + attachments |
| **Dispatcher reassigns a driver mid-shift** | `/dispatch-portal` | ✅ YES | Transition + reassign endpoints wired |
| **Anyone marks a Daily Report "reviewed" by office** | `/admin/daily/:id` | ❌ NO | No review/approve surface |
| **PM resolves a Site Inspection finding** | `/safety/inspections/:id` | ❌ NO | No follow-up surface |
| **Safety officer manually fires the Monday safety digest** | `/admin/digest-config` | ✅ YES (admin only) | Friction: lives in Admin portal, not Safety |
| **Operator sees last Monday's digest fire** | `/admin/scheduler-runs` (iter445) | ✅ YES (iter445) | Newly added |

**6 of 16 high-value user tasks are dead-ends as of 2026-06-01.** 4 of those 6 are Safety/HR-domain tasks.

---

## 3 · Dead-end inventory

### 3.1 · Incident closure

| Element | State | Detail |
|---|---|---|
| Land here | `/admin/incidents/:id` | `ViewIncident.jsx` |
| Expectation | "Mark Under Investigation / CAPA Required / Pending Closure / Closed" | per operator's directive |
| Reality | Banner says: *"Reported → Linked CAPA(s) → Verified → Closed. Closing without a verified CAPA is blocked."* | static copy; no buttons follow |
| Next-action signal | none | the user has no CTA |
| Documented in | `INCIDENT_LIFECYCLE_AUDIT.md` | already audited |

### 3.2 · Payroll Variance batch closure

| Element | State | Detail |
|---|---|---|
| Land here | `/hr/payroll-variance` | per-row decisions wired |
| Expectation | Mark batch "finalized" after every row decided | implied by status enum `open · pending_review · finalized` |
| Reality | No batch-level finalize endpoint | batches stack up indefinitely |
| Next-action signal | none | row counter shows 0 remaining but page can't transition |

### 3.3 · Daily Report office review

| Element | State | Detail |
|---|---|---|
| Land here | `/admin/daily/:id` | `ViewDailyReport.jsx` |
| Expectation | PM/Admin reviews and "approves" or flags follow-up | not part of original DR design |
| Reality | Read-only. Delete-only on errors. | no review state |
| Next-action signal | "Edit" button absent; "Delete" present (admin) |
| Impact | Time Verification + Payroll Variance built atop DRs cannot have a "verified DR" signal |

### 3.4 · QA/QC deficiency resolution

| Element | State | Detail |
|---|---|---|
| Land here | `/qa-qc/:id` | read-only |
| Expectation | "Mark deficiency resolved" / "Re-inspect" | absent |
| Reality | Read-only view of deficiencies array | no per-deficiency state |
| Next-action signal | none |

### 3.5 · Site Inspection follow-up

Same pattern as QA/QC.

### 3.6 · JHA acknowledgement (per crew per day)

| Element | State | Detail |
|---|---|---|
| Land here | `/jha` library | read-only |
| Expectation | Crew acknowledges JHA before high-risk work; supervisor sees who acknowledged | iter445 surfaced JHA in FL Hub but acknowledgement workflow still absent |
| Reality | Library only; no acknowledgement record | no `jha_acknowledgements` collection |

---

## 4 · Confirmation friction

The platform asks for confirmation in 4 ways:

| Pattern | Where | Quality |
|---|---|---|
| Toast on success | most mutating endpoints | 🟢 good |
| Confirmation modal (`confirm()`) before destructive | DELETE flows | 🟢 |
| Two-confirmation flow | Sprint 1C incident delete · admin password re-entry for destructive admin actions | 🟢 best |
| No confirmation | some legacy submissions; FL form submit ("Thank You" page only) | 🟡 |

**No "uncomplete-this-task" indicator exists.** Users don't see "you have 3 unfiled incidents" or "you have 7 variance rows undecided" on any landing page.

---

## 5 · "Why is this blocked?" feedback quality

| Surface | Feedback quality | Example |
|---|---|---|
| Incident delete blocked by CAPA | 🟢 GREEN | 409 response body includes `linked_capa_count` + preview of blocking CAPAs |
| HR clicks "delete incident" | 🟡 AMBER | Backend returns 401; UI shows generic "session expired" via `operationalError` — misleading. Documented in `REAL_USER_DISCOVERABILITY_AUDIT.md` § 3.3 |
| Out-of-scope PM accesses unscoped job | 🟢 GREEN | 404 (not 403) intentionally; UX is "not found" |
| Approve PO without auth | 🟢 GREEN | 401 with clear message |
| Submit DR with accident=Yes but no Incident Report | 🟢 GREEN | Frontend blocks submit; banner instructs user to file incident first |
| Submit Pre-Op with FAIL but no description | 🟢 GREEN | Frontend blocks |
| Photo lightbox unable to load | 🟡 AMBER → 🟢 (Sprint 1G fixed) | "Photo data unavailable or corrupt" was the prior generic banner; now properly displays the photo |

---

## 6 · "What's the next action?" quality

| Page | Has clear next action? | Example |
|---|---|---|
| Hub home | 🟢 yes (tile layout) | each tile leads somewhere |
| `/admin` | 🟢 mostly | Sprint 1G+ improvements |
| `/safety-portal` | 🟢 | tile hub |
| `/hr` | 🟢 (iter445 copy clarification) | tile hub |
| `/pm` | 🟢 | tile hub |
| `/leadership` | 🟢 (iter445 On-Site Reference) | tile hub |
| ViewIncident detail | 🔴 NO | banner says "closing is blocked" but no path to unblock |
| ViewDailyReport detail | 🔴 NO | no review/approve/edit |
| HrPayrollVariance batch | 🟡 partial | row decisions clear; batch closure absent |
| `/admin/scheduler-runs` (iter445) | 🟢 | read-only; intentional |

---

## 7 · Dead-end summary

| Severity | Count | Workflows |
|---|---|---|
| 🔴 Dead-end (cannot finish operational task) | 6 | Incident closure · DR office review · QA/QC follow-up · Site Inspection follow-up · Payroll Variance batch close · JHA acknowledgement |
| 🟡 Partial (can finish with friction) | 4 | Employee offboarding · HR incident-delete confusion · Safety manual digest fire (lives in Admin) · Continuity events (no edit/close) |
| 🟢 Smooth | 6 | PO Requests · Asset Transfers · Fleet Defects · Pre-Op signoff · Dispatch · Fire Extinguisher inspection |

---

## 8 · OMEGA discipline

🟢 Read-only · user-task analysis grounded in page code + API contracts · no remediation proposed.

🛑 Continue to `OPERATIONAL_COMPLETENESS_REGISTER.md`.
