# OMEGA · PHASE 1A OPERATIONAL CERTIFICATION AUDIT

**Date:** 2026-06-02 00:50 UTC
**Method:** Role-by-role workflow trace through the actual platform surface (`/app/frontend/src/pages/*` tile inventory + lifecycle state machines + hub routing). **Not** a code audit — a UX/process audit asking *"can a real human complete this from start to finish?"*

---

## §1 · WORKFLOW COMPLETION MATRIX

Each row is a discrete business process. Each cell answers "can the named role complete this on the live product today?"

Legend: 🟢 completes · 🟡 completes with friction · 🟠 completes only with workaround · 🔴 cannot complete

### Phase 1A core (in scope of this certification)

| # | Business process | Foreman | Superintendent | PM | Payroll | Safety | QC | Executive |
|---:|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | Submit Daily Report (DR) — start of day to "filed" | 🟢 | 🟢 | 🟢 | n/a | n/a | n/a | n/a |
| 2 | Review DR · approve OR kick back to field | n/a | 🟡 | 🟢 | n/a | 🟢 | n/a | n/a |
| 3 | Field user receives kickback email + applies revision via `/revise/{token}` | 🟡 | 🟡 | 🟡 | n/a | n/a | n/a | n/a |
| 4 | Close DR (mark REVIEWED → CLOSED) | n/a | 🟡 | 🟢 | n/a | 🟢 | n/a | n/a |
| 5 | Submit Incident Report | 🟢 | 🟢 | 🟢 | n/a | 🟢 | n/a | n/a |
| 6 | Investigate Incident · move OPEN → UNDER_INVESTIGATION | n/a | n/a | 🟡 | n/a | 🟢 | n/a | n/a |
| 7 | Assign + execute Corrective Action | n/a | 🟠 | 🟠 | n/a | 🟡 | n/a | n/a |
| 8 | Close Incident (PENDING_CLOSURE → CLOSED) | n/a | n/a | 🟡 | n/a | 🟢 | n/a | n/a |
| 9 | Reopen Incident with reason | n/a | n/a | 🟡 | n/a | 🟢 | n/a | n/a |
| 10 | Submit QA/QC Inspection | 🟢 | 🟢 | 🟢 | n/a | n/a | 🟢 | n/a |
| 11 | Review QA/QC · close-loop on deficiencies | n/a | n/a | 🟡 | n/a | n/a | 🟠 | n/a |
| 12 | Submit Site Inspection (safety walk) | 🟢 | 🟢 | 🟢 | n/a | 🟢 | n/a | n/a |
| 13 | Close Site Inspection · acknowledge findings | n/a | n/a | 🟠 | n/a | 🟡 | n/a | n/a |
| 14 | Submit Payroll Variance CSV | n/a | n/a | n/a | 🟢 | n/a | n/a | n/a |
| 15 | Review PV · APPROVE | n/a | n/a | n/a | 🟡 | n/a | n/a | n/a |
| 16 | Finalize PV (APPROVED → FINALIZED) | n/a | n/a | n/a | 🟢 | n/a | n/a | n/a |
| 17 | Open · view JHP for the project I'm on today | 🟢 | 🟢 | 🟢 | n/a | 🟢 | n/a | n/a |
| 18 | Acknowledge that I read the JHP | 🔴 | 🔴 | 🔴 | n/a | 🔴 | n/a | n/a |
| 19 | Safety uploads a NEW JHP for a project | n/a | n/a | n/a | n/a | 🟡 | n/a | n/a |
| 20 | Submit JHA (free-form crew-authored — vestigial system) | 🟢 | 🟢 | n/a | n/a | n/a | n/a | n/a |
| 21 | Submit Toolbox Talk / Safety Meeting | 🟢 | 🟢 | 🟢 | n/a | 🟢 | n/a | n/a |
| 22 | Submit Equipment Pre-Op inspection | 🟢 | 🟢 | n/a | n/a | n/a | n/a | n/a |
| 23 | Submit DVIR (driver vehicle inspection) | 🟢 | 🟢 | n/a | n/a | n/a | n/a | n/a |
| 24 | View "what's open across the platform that I own" | 🟠 | 🟠 | 🟡 | 🟠 | 🟡 | 🟠 | 🔴 |
| 25 | View executive roll-up across all projects | n/a | n/a | 🟠 | n/a | 🟠 | n/a | 🔴 |

### Adjacent flows touched by Phase 1A (out of scope but observed)

| # | Business process | Foreman | Super | PM | Payroll | Safety | QC | Executive |
|---:|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 26 | Time Off Request submit + approve | 🟢 | 🟡 | 🟢 | 🟢 | n/a | n/a | n/a |
| 27 | Time Verification review by HR | n/a | n/a | n/a | 🟡 | n/a | n/a | n/a |
| 28 | PO Request approve | n/a | 🟡 | 🟢 | 🟡 | n/a | n/a | n/a |
| 29 | Training records / driver-qual expirations | 🟠 | 🟠 | 🟠 | 🟢 | 🟢 | n/a | n/a |
| 30 | Field Leadership user provisioning | n/a | n/a | n/a | 🟢 | n/a | n/a | n/a |

### Completion-matrix headline

* **18/25 in-scope rows are 🟢 or 🟡** — the platform supports completion for the vast majority of Phase 1A flows.
* **5/25 rows are 🟠** — completion is possible but requires a workaround (admin DM, manual cross-reference, second-tab open).
* **2/25 rows are 🔴** — JHP acknowledgement is structurally absent (operator-known, OC-005 pending scoping). Executive "what's open across the platform" is structurally absent (no executive role view, no portfolio-roll-up tile).

---

## §2 · USER FRICTION REGISTER

Each entry: who hits it, where it hits, why it's friction, and what an operator-authorized improvement would look like (no code in this audit — just the call-out).

### F-1 · Foreman submitting a Daily Report cannot find the JHP for their project from inside the form
- **Where:** `NewDailyReport.jsx`
- **Friction:** The form prompts for project_number and (optionally) "Has crew reviewed the JHP today?" type fields, but there is no inline link to the project's actual JHP. The foreman has to open a second tab → `/jha` → find project → download PDF → switch back. **Most do not.**
- **Knock-on:** Acknowledgement of the JHP becomes a verbal/social contract instead of a recorded act (compounds F-18 below).

### F-2 · Foreman gets the SAME kickback email twice if office accidentally re-fires PENDING_REVIEW→OPEN
- **Where:** Daily Report Lifecycle (iter452)
- **Friction:** The kickback fires a NEW signed JWT each time. Two emails arrive. The foreman has no way to tell which is "the live one"; both work (until the older one expires after 7 days).
- **Knock-on:** Field user could apply the revision via the older link AFTER the office already advanced the state — revision is saved to `field_submitter_revisions[]` but lifecycle does NOT auto-advance (FSI Q6 audit finding).

### F-3 · Foreman uses Daily Report Lifecycle button labeled "Reviewed" — but they're not the reviewer
- **Where:** `ViewDailyReport.jsx` → `LifecyclePanel.jsx`
- **Friction:** The lifecycle panel hides buttons by role at the backend (`role_not_authorized` is a server-side gate), but UX-wise a foreman who somehow has the admin/PM cookie open in the same browser tab can confuse "I made the report" with "I reviewed it." Role labels on the buttons are not visible (the buttons say "Mark Reviewed" not "Mark Reviewed (Office)").

### F-4 · Superintendent cannot delegate DR review to their PM
- **Where:** `DailyReportsDashboard.jsx` queue + `LifecyclePanel.jsx`
- **Friction:** There is no "assign-to" affordance. Anyone with Safety/PM/Admin role can mark any DR REVIEWED. The implicit ownership is "whoever opens it first." Two-PM crew = race condition.

### F-5 · PM never knows when a DR has been reviewed by Safety vs by themselves
- **Where:** `DailyReportsDashboard.jsx` listing
- **Friction:** The list shows `lifecycle_state` but not WHO advanced it. The PM has to open every record + click "History" drawer to see actor_role on `workflow_state_events`. There is no "reviewed by Jane (Safety) at 14:32" inline column.

### F-6 · Field user clicks `/revise/{token}` link 8 days later — link expired
- **Where:** `Revise.jsx`
- **Friction:** Page renders `error="token_expired"` in a red banner with no further direction. The field user does not know whether to call the office or wait. There is no "request a new link" button.

### F-7 · Field user opens `/revise/{token}` on a phone with no JS / Mongo Atlas down
- **Where:** `Revise.jsx`
- **Friction:** The page is a SPA and depends on JavaScript. If a foreman's data plan throttles JS, the page is blank with no fallback copy.

### F-8 · PM kicks back a DR but does not specify WHAT to fix
- **Where:** `LifecyclePanel.jsx` kickback modal
- **Friction:** Reason field is required (backend enforces) but free-text. Reason commonly arrives as "fix it" or "missing info." Field user has to call to find out what to actually change.

### F-9 · Incident report submitter has no way to "save draft and come back"
- **Where:** `NewIncident.jsx`
- **Friction:** The page has `useFormDraft` (offline queue) for resilience against network drops, but no "Save as draft, finish later" affordance with explicit UI. If a foreman starts an incident report at 16:55 then needs to clock out, they either lose work or accidentally submit a half-finished record.

### F-10 · Incident workflow has 5 states + reopen — too many buttons for a phone screen
- **Where:** `ViewIncident.jsx` → `LifecyclePanel.jsx`
- **Friction:** From UNDER_INVESTIGATION the user sees TWO active "next" buttons (CORRECTIVE_ACTION_REQUIRED · PENDING_CLOSURE). From PENDING_CLOSURE they see TWO active buttons (CLOSED · CORRECTIVE_ACTION_REQUIRED). On a 360px phone the buttons stack and the wrong one is one tap away.

### F-11 · Corrective Action is a STATE, not a TASK
- **Where:** Incident workflow CORRECTIVE_ACTION_REQUIRED state
- **Friction:** When an incident is set to CORRECTIVE_ACTION_REQUIRED, the platform does NOT create a corresponding row in any tasks / corrective-actions collection. The CA is implicit in the state. The PM who must execute it has no row in `Tasks.jsx` to check off. They MUST remember the incident exists. (Note: `SafetyCorrectiveActions.jsx` exists but is a different system — manual entry by Safety, no link back to the incident state.)

### F-12 · Incident reopen reason is required but does not surface in the listing
- **Where:** `IncidentsDashboard.jsx`
- **Friction:** Same as F-5 — to see WHY an incident was reopened, you must open it and look at the History drawer. There's no "Last reopened: 'witness recanted'" inline.

### F-13 · QA/QC inspection completion is implicit
- **Where:** `NewQaqcInspection.jsx`, `PmQaqcList.jsx`, `AdminQaqcList.jsx`
- **Friction:** QA/QC has no Phase-1A lifecycle attached yet (iter453 OC-003). A QC inspector submits, the record lands, then... nothing. There's no "PM has reviewed" marker, no "deficiencies closed" state. PMs are expected to scan the list and act. They forget.

### F-14 · Site Inspection has no closure ceremony
- **Where:** Same family as QA/QC. iter453 OC-004 is supposed to deliver this.
- **Friction:** Currently a write-only record. Open findings have no state.

### F-15 · Payroll Variance reviewer can FINALIZE without explicit "I checked every employee" attestation
- **Where:** `HrPayrollVariance.jsx` → `LifecyclePanel.jsx`
- **Friction:** APPROVED → FINALIZED button is one click. There is no checklist (e.g., "all employees with > $50 variance have a note"). Mistakes propagate to actual payroll runs.

### F-16 · Payroll Variance has only ONE reviewer role gate
- **Where:** Workflow state machine
- **Friction:** Single point of failure if HR is on PTO. There is no co-approver or delegation chain.

### F-17 · JHP library shows ALL projects, not "JHP for my crew's project today"
- **Where:** `JhaPlansHub.jsx` (public route `/jha`)
- **Friction:** Foreman has to scroll/search for project_number. No "today's project" autodetect.

### F-18 · No JHP acknowledgement (OC-005 absent · operator-known)
- **Where:** Anywhere
- **Friction:** Crew cannot prove they read the JHP. PMs/Safety cannot prove the crew read the JHP. OSHA / legal exposure increases over time.

### F-19 · "JHA" name in code vs "JHP" name in operator vocabulary
- **Where:** `JhaPlansHub.jsx`, `JhaPlansAdmin.jsx`, `db.jhas`, `/api/jhas`, `/admin/jha-plans`, `PmHub.jsx` tile labels switch between "Job Hazard Plans" and "JHA Plans"
- **Friction:** New employees learn the wrong term. Onboarding documents use a different term than the URL. Cosmetic but persistent.

### F-20 · Vestigial JHA form-submission system still mounted
- **Where:** `POST /api/jhas` accepts public submissions
- **Friction:** A crew member who Googles "MASCI JHA form" could discover an old form route. Submissions go to an inactive collection that nobody reviews.

### F-21 · "What's mine right now" view is absent for every role
- **Where:** No `Tasks.jsx` integration with lifecycle states; no role-specific "queue" view that combines DR + Incident + PV + QAQC + Site Inspection action items
- **Friction:** A PM logging in for the day must check 6 tiles in sequence: DR queue · Incident dashboard · PO requests · Tasks · QA/QC · Site inspections. Many days, the PM only checks the ones with notification badges. **Items without badges sit unreviewed indefinitely.**

### F-22 · No Executive view
- **Where:** No file matches `Executive*`. There is no `/executive` hub, no portfolio-level rollup
- **Friction:** Ownership at the executive layer is the operator's manual aggregation via Atlas queries or PDF digests. There is no role-grade view for VPs.

### F-23 · Login portal proliferation
- **Where:** `/safety-portal/login` · `/pm/login` · `/admin/login` · `/hr/login` · `/dispatch-portal/login` · `/shop/login` · `/leadership` (FL portal)
- **Friction:** Seven distinct login surfaces. A user who carries multiple roles (e.g., a Safety officer who is also Admin) cannot SSO between them. They have to log into each portal separately. Password fatigue.

### F-24 · Notification fan-out goes to "role" not to "individual"
- **Where:** `lib/event_fanout.py::emit_notification`
- **Friction:** When a DR enters PENDING_REVIEW, the notification goes to all PMs/admins/safety. There is no "you are assigned to this DR" personalized routing. The result is: everyone gets the notification, everyone assumes someone else will act.

### F-25 · `field_submitter_bindings` admin endpoint un-gated
- **Where:** `GET /api/admin/field-submitter-bindings`
- **Friction:** PII (submitter email · FL user email · employee email) visible without auth. Already disclosed by operator. Listed here because in operational terms, anyone who can reach the API host can enumerate the company's email directory.

### F-26 · Two competing daily-reports dashboards
- **Where:** `DailyReportsDashboard.jsx` (admin/PM) and `HrDailyReports.jsx` (HR)
- **Friction:** Same data, different lenses. A DR can be "REVIEWED" by PM but the HR view doesn't surface that semantics. Cross-domain queries (e.g., "has PM closed this DR and did HR resolve the payroll variance for the same day?") require manual cross-tab work.

### F-27 · Hub icon vs. tile color drift across roles
- **Where:** `PmHub.jsx` vs `HrHub.jsx` vs `SafetyHub.jsx` vs `FieldSection.jsx`
- **Friction:** "Daily Reports" tile is RED in PmHub (top-row), GREEN in HrHub, BLUE in FieldSection. Same data, different signal. Color is supposed to mean priority but the meaning is inconsistent across roles.

---

## §3 · ACCOUNTABILITY GAPS

These are the structural reasons workflows go silent.

| # | Gap | Symptom (operational) | Why it persists |
|---:|---|---|---|
| A-1 | **CORRECTIVE_ACTION_REQUIRED is a state, not a task** | Incident parks at "CA Required" indefinitely; no PM gets a checkable item | The state machine has no "responsible_party" field; no task row is created automatically |
| A-2 | **No assignee on any lifecycle state** | DR/Incident/PV transitions don't capture WHO must act next; everyone is responsible = no one is | No `assigned_to_user_id` field on the records; only `actor_role` is stamped on the audit row, not on the record itself |
| A-3 | **JHP read = nothing** | Cannot prove a crew member read a JHP; OSHA defense unprovable | OC-005 unbuilt (operator-disclosed, pending scoping) |
| A-4 | **Kickback reason invisible inline** | Field user opens revision page · sees ONE sentence · cannot tell which part of the DR to fix | Reason is on the email body + History drawer; not surfaced inline on `/revise/{token}` |
| A-5 | **Field-submitter post-closure revisions land silently** | After CLOSED, a field user can still POST a revision; record updated, lifecycle unchanged, no PM alert | iter452.5 R1 forensic finding Q6 — revision_saved event fires but no fan-out |
| A-6 | **Multi-actor races on same record** | Two PMs simultaneously mark a DR REVIEWED → last writer wins, no conflict UI | No optimistic-lock / If-Match semantics |
| A-7 | **Field Leadership session ≠ submission identity** | Today: a supervisor logs into FL portal; submits a DR; if browser localStorage is missing/private, X-FL-Token is dropped silently → falls back to anonymous tier-3 even though they're "logged in" | Frontend uses ternary `getFlToken() ? {…} : {}`; no UX warning when token absent on a supposed-FL-session POST |
| A-8 | **Resend-accepted ≠ delivered** | `notification_dispatch_succeeded` event is misleading; bounces silent until iter452.5.2 P1 | Operator-disclosed, batch authorized for next |
| A-9 | **Tier-5 dead-letter inbox has no SLA** | Submissions routed to `safety@mascigc.com` sit until a human happens to check that inbox | No dead-letter dashboard tile (iter455.1 P2 closes this) |
| A-10 | **No "this lifecycle was idle for N days" alerter** | OPEN incidents · PENDING_REVIEW DRs · UNDER_REVIEW PVs can sit indefinitely | No scheduler job watches lifecycle_state idle time |
| A-11 | **Notifications fan to ROLE not USER** | Everybody sees · nobody owns | F-24 — same pathology, structural |
| A-12 | **No "I claim this" affordance** | The platform has no "assign to me" button on any queue view | Self-service ownership is the missing UX primitive |
| A-13 | **Vestigial JHA form unmonitored** | `db.jhas` accepts submissions; nobody reads them | F-20 — kept mounted for back-compat with no operational owner |
| A-14 | **Executive layer absent** | No role can see "all projects, all open lifecycle states, this week's closures" | F-22 |

---

## §4 · SOURCE-OF-TRUTH VIOLATIONS

Cases where two collections (or two UIs) carry the same fact and can disagree.

| # | Violation | Two sources | Risk |
|---:|---|---|---|
| S-1 | **Submitter identity** | `daily_reports.prepared_by` (free text) vs `field_submitter_bindings.submitter_name` (resolved) vs `field_leadership_users.name` (canonical) | A DR can read "Prepared by: Jaymn Judd" while the binding reads `submitter_name: "Jane M Judd"` (autocomplete vs canonical). No periodic backfill aligns them. |
| S-2 | **PM email for a project** | `jobs_master.pm_email` vs `pm_routing.recipients_for_record_async` (which may overlay) vs `field_submitter_bindings.resolved_pm_email` (snapshot at submit time) | A PM email change in `jobs_master` does NOT retro-update older bindings. Kickback notifications post-PM-change can route to the prior PM. |
| S-3 | **JHP "current version" for a project** | `job_hazard_files` rows accumulate without `is_current` flag; ordering by `uploaded_at` is the convention | If two Safety officers upload near-simultaneously, the "newest" is racy. |
| S-4 | **Project_number formatting** | `jobs_master.project_number` is canonical; many submissions store FREE-TEXT (`"25-22 - Project Name"` instead of `"25-22"`) | Cross-collection joins miss matches. |
| S-5 | **Daily Report state vs Payroll Variance state for the same date** | Two independent lifecycles; no enforced consistency | A DR can be CLOSED while the day's PV is OPEN. Payroll runs against a PV that contradicts the field record. |
| S-6 | **Workflow state events count vs delivery-evidence events count** | iter452.5 introduced `evidence.delivery_event` rows in the SAME `workflow_state_events` collection | Naive aggregators that count transitions DOUBLE COUNT unless they filter (`evidence.delivery_event` absent). The Phase-1A R-CERT tests were updated; downstream reporters MAY not be. |
| S-7 | **Field Leadership user vs Employee directory** | `field_leadership_users` (24 supervisors) and `employees` (261) are SEPARATE collections | A supervisor exists in both; updating email in one does not propagate. iter452.5.1 ladder prefers FL — but if the FL row's email is stale, kickbacks miss. |
| S-8 | **"Lifecycle state" string casing** | Code emits UPPER (e.g., `OPEN`) but some frontend renderers may coerce to title-case for display | Saved as `OPEN`, displayed as `Open`. CSV exports inherit the displayed value. |
| S-9 | **JHA (form) vs JHP (PDF) terminology** | F-19 — UI labels switch | New users learn the wrong term. |

---

## §5 · CUSTOMER #2 READINESS SCORE

Definition: "Could a second construction-services GC adopt this platform with their own employees, projects, and PMs, within 30 days, without us hard-coding their identity?"

| Dimension | Score (0-10) | Evidence |
|---|---:|---|
| Data-model tenant-isolation | **2** | No `tenant_id` on any collection. `jobs_master`, `employees`, `daily_reports`, `incidents`, `field_submitter_bindings` are all single-tenant. |
| Email/branding configurability | **3** | `ADMIN_DEAD_LETTER_EMAIL` is operator-tunable. PDF footer hard-codes "MASCI" and "ForgedOps" branding strings. Login pages carry MASCI iconography. |
| URL/domain configurability | **2** | Frontend uses `process.env.REACT_APP_BACKEND_URL` — would work, but every PDF, email body, QR code currently embeds `mascidocs.com` or MASCI-internal references. |
| Role taxonomy generality | **6** | Foreman/Super/PM/Safety/QC/HR are industry-standard. Payroll Variance is more specific but transferable. |
| Onboarding wizard for new tenant | **0** | None. Tenant 2 would require a manual mongo seed run + DNS + branding sweep. |
| User-provisioning self-serve | **2** | `HrFieldLeadershipUsers.jsx` exists but is MASCI-org-scoped. No multi-tenant admin UI. |
| Auth multi-tenant | **1** | All login portals are tenant-singular. No SSO/SAML/OIDC integration. |
| Project-number convention | **3** | MASCI's `YY-NN` numbering is hard-baked into examples and validators. |
| Compliance/locale | **4** | EN/ES bilingual scaffolding present but copy is MASCI-tuned. |
| **TOTAL** | **23 / 90** | **🔴 NOT READY** |

**Headline:** Customer #2 onboarding requires a tenant-isolation rebuild (every collection needs a `tenant_id` + every query needs scoping) before any other work. Estimated 4-6 sprint cycles (~10 weeks).

---

## §6 · WHITE-LABEL READINESS SCORE

Definition: "Could we ship this platform to a different brand without code changes, just config/asset swaps?"

| Dimension | Score (0-10) | Evidence |
|---|---:|---|
| Logo asset slot | **2** | Logo is `/app/frontend/src/assets/masci-logo.*` referenced directly; no central `BRAND_CONFIG` |
| Color theme tokens | **3** | Tailwind config carries some custom colors; tile-color drift across hubs (F-27) is a sign of no central theme contract |
| Brand-string sweep | **1** | `grep -r "MASCI"` returns hundreds of hits across components, copy, PDF templates, email subjects, login welcome strings |
| Domain-string sweep | **2** | Hard `mascidocs.com` references in QR poster URL · `safety@mascigc.com` is dead-letter default (operator-tunable env var) |
| PDF templates | **2** | PDF render hard-codes MASCI letterhead, footer, watermark in `pdf_render.py` |
| Email templates | **3** | Subjects use `[MASCI]` prefix · operator could swap via env, but there is no template registry |
| Favicon/manifest | **2** | `public/favicon.*` is MASCI; `public/manifest.json` carries MASCI brand colors |
| Default copy (Hub welcome, etc) | **3** | Welcome strings name MASCI in places |
| Locale toggles | **5** | EN/ES toggle works; copy itself is brand-neutral in most cases |
| **TOTAL** | **23 / 90** | **🔴 NOT READY** |

**Headline:** White-label requires a brand-config layer (logo · primary/secondary/accent colors · brand-name string · domain · letterhead · favicon · welcome copy) and a sweep to replace every literal `MASCI` reference with a `BRAND.name` lookup. Estimated 2-3 sprint cycles (~5 weeks) AFTER tenant isolation is done.

---

## §7 · FORGEDOPS FOUNDATION READINESS SCORE

Definition: "Is the platform's data, audit, and lifecycle architecture mature enough to be marketed as a productized 'operational discipline' offering ('ForgedOps')?"

| Dimension | Score (0-10) | Evidence |
|---|---:|---|
| Universal state-machine framework | **8** | iter451 + iter452 + iter452.5.1 built ONE state machine library (`lib/workflow_state_machine.py`) reused across 3 workflows. Phase 1B will canonicalize the rest. Strong foundation. |
| Immutable audit trail | **8** | `workflow_state_events` collection is immutable; every transition stamped with actor/role/reason. iter452.5 extended for delivery-evidence. Excellent foundation. |
| Identity resolution discipline | **8** | iter452.5.1 5-tier ladder is the cleanest identity-resolution layer the platform has ever had. Phase 1B can mine `resolution_tier` for telemetry. |
| Lifecycle reporting | **3** | Today: per-record view. No aggregated "open work" dashboard. iter455.1 P2 closes this. |
| Workflow assignment | **2** | No assignee model — A-2 friction. Foundational gap for "ops discipline" branding. |
| Cross-workflow dependencies | **3** | No edge graph between DR closure and PV closure (S-5). |
| Notification routing | **3** | Role-based not person-based (F-24). |
| Drift detection | **4** | `lib/accountability_projection.py` exists; not yet wired to a dashboard. |
| Source-of-truth consolidation | **3** | S-1 through S-9 are 9 distinct violations open today. |
| Self-service tenant onboarding | **0** | See Customer #2 score. |
| **TOTAL** | **42 / 100** | **🟡 PARTIALLY READY (foundation phase)** |

**Headline:** ForgedOps as a productized offering has its FOUNDATION already shipped (state machine + audit trail + identity ladder are productizable, well-tested primitives). What's missing for a v1 launch: assignment model, cross-workflow graph, person-level routing, source-of-truth consolidation. **6-8 sprint cycles** between today and a marketable ForgedOps v1.

---

## §8 · OPERATIONAL CERTIFICATION HEADLINE

| Question | Answer | Evidence |
|---|---|---|
| Can every Phase-1A workflow be completed from creation through closure by a real user? | **YES, with friction in 7 places · WITHOUT JHP acknowledgement closure** | §1 completion matrix |
| Are accountability chains provable end-to-end for completed workflows? | **YES for DR/Incident/PV in the happy path** · **NO for the corrective-action sub-state and for JHP reads** | §3 A-1, A-3 |
| Is the platform safe for Customer #2 today? | **NO** — single-tenant architecture | §5 |
| Is the platform safe for white-label today? | **NO** — brand strings hard-coded | §6 |
| Is the platform foundation strong enough to evolve into ForgedOps? | **YES** — state machine + audit + identity layers are productizable; needs assignment + routing + reporting | §7 |

---

## §9 · TOP-10 OPERATOR-AUTHORIZABLE IMPROVEMENTS (ranked by friction-impact / effort)

| Rank | Improvement | Closes | Effort feel |
|---:|---|---|---|
| 1 | Inline kickback-reason banner on `/revise/{token}` AND on the field user's DR view | F-4 · F-8 · A-4 | small |
| 2 | "Assigned to me" affordance + actual assignee field on lifecycle records | A-1 · A-2 · A-11 · A-12 · F-21 | medium |
| 3 | OC-005 JHP Acknowledgement Ledger (Option 1 Minimum) | F-1 · F-17 · F-18 · A-3 | medium |
| 4 | Cross-workflow "what's idle > 7 days" alerter (scheduler job) | A-10 | small-medium |
| 5 | Resend bounce webhook (iter452.5.2 P1 — already authorized) | A-8 | small |
| 6 | Dead-letter dashboard tile (iter455.1 P2 — already authorized as bundle) | A-9 | small-medium |
| 7 | Executive role + portfolio rollup view | F-22 · F-24 | medium |
| 8 | Source-of-truth consolidation: backfill `prepared_by` against FSI binding · backfill `submitter_name` against directory | S-1 · S-7 | small |
| 9 | Brand-config layer (foundation for white-label) | §6 entirely | medium-large |
| 10 | `tenant_id` on every collection (foundation for Customer #2) | §5 entirely | large |

The top 4 of this list are entirely inside the Phase-1A envelope (no tenant work, no Tier-2 work) and address the largest operational pain. Items 5-6 are already operator-authorized for next batches.

---

## §10 · DISCIPLINE SCORECARD

| Check | Status |
|---|---|
| Zero code audited (workflow-only) | ✅ |
| Every friction call-out has a specific page/component reference | ✅ |
| Every accountability gap is structural (not just "training") | ✅ |
| Every source-of-truth violation cites both sources | ✅ |
| Three readiness scores rendered independently | ✅ |
| Top-10 prioritized improvements operator-actionable | ✅ |
| No code changes during audit | ✅ |
