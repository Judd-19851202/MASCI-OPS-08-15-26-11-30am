# OMEGA · QA/QC Follow-Up (OC-003) Ownership Audit

**Date:** 2026-06-01
**Mode:** Forensic, evidence-only. No code. No fixes. No design.
**Verdict:** 🟡 **YELLOW — ownership chain is partially provable but degrades when public-gate submissions lack inspector/sub-rep contact information.**

---

## 1 · Public-gate confirmation

Confirmed: QA/QC inspections are public-gated.

* Backend route guard · `/app/backend/routes/qaqc.py:149-156`
  ```python
  def register_qaqc_routes(api_router, db, require_admin,
                           rate_limit_public_post, schedule_auto_email):
      @api_router.post(
          "/qaqc-inspections", response_model=QAQCInspection,
          dependencies=[Depends(rate_limit_public_post)],
      )
  ```
  Only protective dep: `rate_limit_public_post`. No auth required.

* React route declaration · `/app/frontend/src/App.js:309-310`
  ```
  <Route path="/qaqc/:slug/new" element={<NewQaqcInspection />} />
  <Route path="/qaqc/:id"       element={<ViewQaqcInspection />} />
  ```
  Public — no auth wrapper.

The operator's correction is validated by the code.

---

## 2 · Stored fields — actual evidence

Direct probe of a live `qaqc_inspections` document (35 total keys):

```
all_keys: ['attachments', 'audit_envelope_sha256', 'completed_to_specs',
'completion_signature', 'compliant_codes_specs', 'concrete_compressive_strength',
'created_at', 'deficiencies', 'doc_id', 'engineer_review',
'engineer_review_concerns', 'enhanced_audit_status', 'engineer_review_required',
'id', 'inspection_kind', 'job_walk_signature', 'location', 'modifications_required',
'next_steps', 'overall_status', 'photos', 'project_name', 'project_number',
'restrictions_specs', 'safety_compliant', 'safety_remediation',
'specific_concerns', 'submission_envelope', 'specifications_followed',
'submission_payload_sha256', 'subcontractor', 'sub_rep_name', 'sub_rep_signature',
'work_area', 'yards_ordered']
```

Pydantic input model · `qaqc.py:55-118` (extracted):
* Required: `project_name, project_number, inspection_kind, location, sub_rep_name, subcontractor`
* Optional: `sub_rep_signature, completion_signature, job_walk_signature, deficiencies, photos`
* **NOT in the input model:** `inspector_name`, `inspector_email`, `responsible_party`, `assigned_to`, `subcontractor_email`, `sub_rep_email`, `submitter identity of any kind`.

---

## 3 · Per-question answers

| # | Question | Evidence | Answer |
|---|---|---|---|
| 1 | What fields are stored? | See §2 — 35 keys. Identity-bearing keys: `subcontractor` (company string), `sub_rep_name` (free text), `project_number`. | Captured above |
| 2 | Is QA/QC submitter identity stored? | There is no submitter field at all in the input model or the live document. The form does not ask "who is filling this out". | 🔴 **NOT stored.** |
| 3 | Is supervisor identity stored? | `sub_rep_name` (sub representative free text) is the closest analog — represents the *subcontractor* side, not a MASCI supervisor. No MASCI supervisor / superintendent / inspector field exists. | 🔴 **NOT stored.** |
| 4 | Is responsible party stored? | No `responsible_party` field. `deficiencies` is free-text (e.g. `"two fail items"` in the sampled row). When deficiencies fail, the existing corrective-actions module (`corrective_actions` collection) creates a row with `assigned_to_department` but **not** `assigned_to_employee_id` or `assigned_to_email`. | 🔴 **NOT stored at row level. Department-only at CAPA level.** |
| 5 | Is employee directory mapping used? | No FK to `employees` collection. Even if used, the directory has only 1 row with email (out of 261). | 🔴 **No directory mapping.** |
| 6 | Is PM mapping used? | Yes — server-side, via `project_number → jobs_master.pm_email` (same path as Daily Reports). Auto-email fan-out hits the PM + co-PMs + ALWAYS_CC (safety, jaymn.judd) per `pm_routing.recipients_for_record_async()`. Live `jobs_master` sample has `pm_email='chriswright@mascigc.com'`. | 🟢 **Yes — DB-resolved.** |
| 7 | When a deficiency requires correction: who owns it, how is ownership assigned, how is ownership tracked? | `qaqc.py:240-265` creates a `corrective_actions` row for each deficiency. The row's `assigned_to_department` is a string only. There is no `assigned_to_employee_id`, no `assigned_to_email`, no `assigned_to_phone`. Tracking is via `corrective_actions.status` ∈ {open, in_progress, resolved, verified}. | 🟡 **Owned by a department string. Cannot reliably reach a person.** |
| 8 | How is correction notification delivered? | `qaqc.py:249` calls `emit_notification` with `severity` derived from the deficiency. Live notification row shows `delivery = {internal: True, email: False, push: False, sms: False}`. The PM auto-email is fired ONCE on the original submission via `schedule_auto_email("inspection", record)`. **No automated email is fired specifically on deficiency-correction-required.** | 🟡 **In-app only. PM email on original submit only.** |
| 9 | How is closure notification delivered? | When a CAPA is verified, the existing flow updates `corrective_actions.status` but does NOT auto-notify the original submitter (because there is no submitter contact captured). iter453 lifecycle scope will add transition events on inspection close — but the **delivery channel** for those notifications is currently in-app only with no submitter target. | 🔴 **Closure notification does not reach the submitter / subcontractor.** |
| 10 | Authoritative source of truth for QA/QC ownership? | Same pattern as DR: project_number → jobs_master.pm_email (proven). Sub-rep name is free-text only (not proven). Inspector identity is absent. | 🟡 **PM ownership: GREEN. Inspector / sub-rep ownership: RED.** |

---

## 4 · Ownership-chain proof

| Chain link | Provable? |
|---|---|
| Inspector identity | 🔴 NO — no inspector field |
| Inspector contact | 🔴 NO |
| Sub-rep identity | 🔴 NO — free text only |
| Sub-rep contact | 🔴 NO — no email/phone field on row |
| Subcontractor company | 🟡 YES (string only — not validated against any vendor master) |
| Project number | 🟢 YES |
| Primary PM email | 🟢 YES (via jobs_master) |
| Co-PM emails | 🟢 YES |
| CAPA-assigned department | 🟡 YES (string, not person) |
| CAPA-assigned person | 🔴 NO |
| Verifier identity | 🟡 YES (captured at verify time on the CAPA row, via authenticated UI only) |

---

## 5 · Critical findings

* **F1 (HIGH)** — QA/QC inspections are submitted without any inspector identity field. The `sub_rep_name` field captures the *subcontractor's* side, not the MASCI-side inspector. The platform cannot identify who walked the area.
* **F2 (HIGH)** — Corrective actions raised from deficiencies are owned by a *department string*. Department membership is not modelled, so a CAPA assigned to "Concrete" cannot be reliably routed to a specific concrete foreman.
* **F3 (HIGH)** — Sub-rep contact (email, phone) is not captured anywhere. If a deficiency requires re-walk by the sub, the platform cannot reach them automatically; office staff must phone them.
* **F4 (MEDIUM)** — Public submission has no token-signed view URL for the sub-rep to return and verify their corrective work.
* **F5 (LOW)** — Inspector identity could in theory be inferred from `audit_events` (IP / user_agent for the POST), but this is not a sustainable owner channel.

---

## 6 · Classification

🟡 **YELLOW — Ownership chain is partially provable.**

* PM side: GREEN (same robust DB-backed pattern as DR).
* Sub-rep side: RED (free text + no contact).
* Inspector side: RED (field does not exist).
* CAPA-assignee side: RED at person level; YELLOW at department level.

**Definition of DONE risk:** corrective actions cannot reliably reach (a) the field inspector who walked the deficiency or (b) the subcontractor representative who needs to fix it. Office staff must close that loop manually off-platform.

→ **Operator decision required:** mark OC-003 as a CRITICAL PHASE 1A GAP until the field side of the chain is closed, OR scope iter453 work to address the gap as part of the QA/QC Follow-Up build.

No code in this audit.
