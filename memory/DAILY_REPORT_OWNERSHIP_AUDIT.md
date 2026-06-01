# OMEGA · Daily Report (OC-002) Ownership Audit

**Date:** 2026-06-01
**Mode:** Forensic, evidence-only. No code. No fixes. No design.
**Verdict:** 🟡 **YELLOW — ownership chain EXISTS but contains gaps that block reliable revision delivery to the original submitter.**

---

## 1 · Public-gate confirmation

Confirmed: Daily Reports are public-gated.

* React route declaration · `/app/frontend/src/App.js:351-352`
  ```
  <Route path="/daily/new"    element={<NewDailyReport />} />
  <Route path="/daily/submit" element={<NewDailyReport publicMode />} />
  ```
  Both routes are mounted OUTSIDE any authentication wrapper.

* Backend route guard · `/app/backend/routes/daily_reports.py:170-173`
  ```python
  @api_router.post(
      "/daily-reports", response_model=DailyReport,
      dependencies=[Depends(rate_limit_public_post)],
  )
  ```
  The only protective dependency is `rate_limit_public_post`. There is **no** auth-token requirement on submission.

**Operator's correction is validated by the code.** A Daily Report may be submitted with NO authenticated portal user attached.

---

## 2 · Stored fields — actual evidence

Direct probe of a live `daily_reports` document on the preview database (full key inventory):

```
Total keys: 29
  activities                  general_notes          report_date
  attachments                 id                     report_number
  audit_envelope_sha256       incident_notes         safety_contact_person
  constraints                 incident_report_filled safety_contact_time
  crews                       incident_report_time   safety_notified
  doc_id                      injuries_reported      safety_incidents_today
  general_notes               location               schedule_delays
  language                    materials              schedule_delays_notes
  prepared_by                 photos                 superintendent
  prepared_by_signature       prepared_by            superintendent_signature
  project_name                project_number         visitors
  subcontractors              weather_impact         weather_summary
  weather_impact_notes        equipment              weather_snapshots
                              created_at
```

Pydantic input model · `daily_reports.py:73-127`:
* Required string fields on submit: `project_name, project_number, location, report_date, prepared_by`
* `superintendent` is **optional** (`Optional[str] = ""`)
* `prepared_by_signature` is **optional**
* No email / phone / employee_id / portal_user_id fields anywhere in the input contract.

---

## 3 · Per-question answers

| # | Question | Evidence | Answer |
|---|---|---|---|
| 1 | What fields are stored when a Daily Report is submitted? | See §2 — 29 keys; identity-bearing keys are `prepared_by` (name string), `superintendent` (name string), `project_number`, `project_name`, `created_at`. | Captured above |
| 2 | Is `supervisor_name` stored? | `superintendent` (free-text name string) is the equivalent field. Optional. | 🟡 **Stored as free text only — not validated against any directory.** |
| 3 | Is `supervisor_email` stored? | Not in the Pydantic input model. Not in the live document. | 🔴 **NOT stored.** |
| 4 | Is `employee_id` stored? | Not in the Pydantic input model. Not in the live document. The 261 `employees` collection rows have an `employee_id` field but it is empty for the sampled row and there is no foreign-key link from `daily_reports` to `employees`. | 🔴 **NOT stored.** |
| 5 | Is `portal_user_id` stored? | Not in the Pydantic input model. Not in the live document. The public-gate has no portal session. | 🔴 **NOT stored.** |
| 6 | Is device information stored? | The platform has a device-local crew memory primitive (`/app/frontend/src/lib/crewMemory.js`) that lives entirely in `localStorage` and is **never synced to the server**. Lines 9-11 are explicit: "localStorage only. NO server sync. NO admin visibility." Server-side `audit_events` collection captures `ip` + `user_agent` per request, but the `daily_reports` row itself does NOT carry an `ip_address`, `user_agent`, or `device_id` field. | 🔴 **NOT stored on the DR document.** Audit-trail-only, and only for the original POST. |
| 7 | Is project information stored? | `project_number` + `project_name` are required input fields. | 🟢 **Yes — required.** |
| 8 | Can the system positively identify the original submitter? | `prepared_by` is a free-text string. There is no validation that it matches a real person, no email cross-reference, no `employee_id` link. The 261-row `employees` directory has only **1 row with a non-empty email** and **0 rows with a phone**. Two crews on the same job can have the same first name on different days and produce identical `prepared_by` strings. | 🔴 **NO — cannot positively identify.** |
| 9 | Can the system positively identify the responsible supervisor? | `superintendent` is a free-text name. Optional. Same problem as #8. No email/ID validation. | 🔴 **NO.** |
| 10 | Can the system positively identify the responsible PM? | Yes — but **NOT from the form submission**. PM resolution runs server-side via `pm_routing.resolve_pm_for_record_async()` which uses `project_number` to look up `jobs_master.pm_email` + `jobs_master.co_pm_emails`. Confirmed live: the sampled `jobs_master` row has `pm_email='chriswright@mascigc.com'`. | 🟢 **Yes — via project_number → jobs_master.pm_email.** |
| 11 | When a Daily Report is returned for correction, who receives notification and how? | iter452 `daily_report_lifecycle.py:135-160` fires `emit_notification` ONLY on `PENDING_REVIEW`, with three rows: `recipient_role` ∈ {admin, pm, safety}. **No notification is fired on PENDING_REVIEW → OPEN (the kickback path).** Probe of live `notifications` collection: `delivery = {internal: True, email: False, push: False, sms: False}` — i.e. **in-app only, no email, no push, no SMS** for this notification type today. | 🟡 **On kickback: NO notification fires at all.** The current state-machine writes the audit event but does not call `emit_notification` for the OPEN-bound transition. |
| 12 | Is the correction reason visible without opening History? | iter452 `LifecyclePanel.jsx` history-drawer pattern: the `reason` field on the `workflow_state_events` audit row is accessible only via the History button. The DR detail page does not render an inline "Returned to field — «reason»" banner. | 🔴 **No — audit-trail only, one extra click required.** |
| 13 | Can the submitter access the report again if they are not logged in? | The submitter received only the printed PDF / email confirmation (when `auto_email_enabled()` is true and the routing target list includes the submitter — which currently it does NOT, because routing is PM-only/PM-with-CC). There is **no submitter-bound URL with a token** in the codebase. The only ways to find a DR are: (a) the authenticated detail page `/admin/daily/:id` or `/pm/daily/:id`, or (b) the public submit form (`/daily/submit`) which is a NEW submission, not an edit. | 🔴 **No — a public-gate submitter cannot re-access their submission without portal credentials.** |
| 14 | Is there a secure revision path for public-gate submissions? | The Pydantic Update model exists (`DailyReportUpdate` · `daily_reports.py:139`) but the update endpoint requires admin/PM auth. There is no token-signed deep-link, magic-link, or signed-URL mechanism for the original submitter to amend their own submission. | 🔴 **No — no signed-revision path.** |
| 15 | What is the authoritative source of truth for Daily Report ownership? | The combination of (`prepared_by` free text · `superintendent` free text · `project_number` → `jobs_master.pm_email`). Only the last component is database-validated. | 🟡 **PM ownership is provable. Submitter / supervisor ownership is NOT.** |

---

## 4 · Ownership-chain proof

| Chain link | Provable? | How |
|---|---|---|
| Submitter identity | 🔴 NO | Free-text string only |
| Submitter contact | 🔴 NO | No email/phone/portal_user_id captured |
| Submitter device | 🔴 NO | Not persisted on the DR row |
| Supervisor identity | 🔴 NO | Free-text string only |
| Supervisor contact | 🔴 NO | Not captured |
| Project number | 🟢 YES | Required input |
| Primary PM email | 🟢 YES | `jobs_master.pm_email` lookup |
| Co-PM emails | 🟢 YES | `jobs_master.co_pm_emails` list |
| Office reviewer | 🟢 YES | Admin role (any admin can review) |
| Safety reviewer | 🟢 YES | Safety role (any safety user can review) |

---

## 5 · Critical findings

* **F1 (HIGH)** — A kicked-back Daily Report has no documented recipient. The lifecycle audit row records the reason, but no email, push, in-app, or SMS notification is dispatched to the field crew. The original submitter has no automatic awareness that their report was returned.
* **F2 (HIGH)** — Free-text `prepared_by` cannot be reliably resolved to a person. Two different employees with the same first name produce indistinguishable submitter strings.
* **F3 (HIGH)** — The 261-row `employees` directory has only 1 row with an email. Even if the form captured a directory selection, contacting the submitter would fail for ~260 / 261 of them.
* **F4 (MEDIUM)** — There is no public-gate revision URL. A submitter who realises they made an error after submit can only submit a new DR (creating a duplicate) or wait for the office to find them off-platform.
* **F5 (LOW)** — `audit_events` rows DO carry `ip` + `user_agent` for the original POST, but `daily_reports` itself does NOT, so cross-collection joining is required to correlate device data to a specific submission.

---

## 6 · Classification

🟡 **YELLOW — Ownership chain exists but contains gaps.**

* PM/office side of the chain is GREEN (project_number → pm_email → co_pm_emails → office/safety roles).
* Field side of the chain is RED (prepared_by + superintendent are free text; no email; no device binding; no revision path).
* Net result: corrective actions raised through the iter452 kickback path can reach the **office** reliably but **cannot reach the field submitter** through the platform. Office staff must contact field crews via off-platform channels (phone call / text / radio).

**This does not meet the operator's Phase 1A "Definition of DONE":** *"corrective actions cannot reliably reach the responsible party."*

→ Recommend operator authorize a follow-up batch to close the field side of the ownership chain. **No code in this audit.**
