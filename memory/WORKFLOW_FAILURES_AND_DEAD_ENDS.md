# WORKFLOW FAILURES AND DEAD ENDS
**Audit date:** 2026-05-23
**Purpose:** Catalog of "technically works but operationally broken" failures — flows that succeed at the API level but break in the real operator's day.

---

## DE-1 · Accountability Timeline is preview-only
**Symptom:** HR Compliance Brief PDF — the "operational employee system of record" — is unreachable in production. `mascidocs.com/api/hr/employees/{id}/accountability/timeline` returns 404.
**Why it matters:** Every iter350+ improvement is invisible to real operators until the next deploy. Operator was told the platform IS the operational system of record; today it is the **preview** operational system of record.
**Fix:** Trigger a production redeploy. Single biggest unlock available right now.

## DE-2 · FL just gained DQ — but is blind to everything else about the same driver
**Symptom:** FL portal shows "Driver Available Right Now" with CDL + medical validity. Click into the same employee for training currency? FL gets 401. PPE issuance? 401. Recent incident history? 401. Open tasks/notifications? 401.
**Why it matters:** The "Drivers Available Right Now" tile answers *legally available*. It does NOT answer *operationally safe to assign*. A driver with a current CDL but expired OSHA-10 is "available_now=true" today.
**Fix:** Queued widget — "FL Employee Accountability Mini-Widget" — needs ALSO read-only access to training_records + equipment_issuances within FL's existing token scope.

## DE-3 · HR can read incidents only through a single employee's drill-down
**Symptom:** `/api/incidents` rejects HR. There is no `/hr/incidents` list. HR can see an incident only by knowing the employee involved and clicking through the timeline.
**Why it matters:** OSHA 300 / 301 / 300A preparation is fundamentally an aggregate query: *"every recordable incident in this calendar year"*. HR cannot answer it without escalating to Safety. This is operationally inverted — HR should own OSHA paperwork.
**Fix:** Add `/api/hr/incidents` read-only proxy.

## DE-4 · PM cannot verify crew readiness before assignment
**Symptom:** PM has scoped views on jobs / daily reports / inspections / QA-QC. PM has NO read on `safety/training-records` or `safety-forms/equipment-issuances`. PM cannot answer: *"can my crew legally and safely do this confined-space job?"*
**Why it matters:** PM is the closest accountability layer to the actual work. The compliance question lives in their workflow but the answer lives in another portal.
**Fix:** Scoped PM training + PPE read endpoint (limit to PM's job-assigned employees).

## DE-5 · Notifications fan out to Safety + PM but never to FL
**Symptom:** `recipient_role` enum observed in live preview: only `safety`, `pm`. Zero FL recipients.
**Why it matters:** Field leaders are the human escalation point in the field. When QA/QC fails on their job, the digital notification reaches Safety in Lake City and PM at the office. The foreman 50ft from the deficiency gets a phone call (maybe) hours later.
**Fix:** Extend recipient_role to include `fl` + fan-out logic on QA/QC fail, Pre-Op fail, daily-report missing, incident on FL's assigned project.

## DE-6 · Dispatch cannot reconcile yesterday's crew movement
**Symptom:** `GET /api/daily-reports` rejects Dispatch (401). Dispatch's only daily visibility is the FL `dispatch-today` proxy (today + tomorrow window).
**Why it matters:** When a fleet defect is reported, dispatch needs to ask "who drove that truck yesterday?" — the daily report has the answer. Today they escalate to admin.
**Fix:** Dispatch read-only proxy on daily-reports, 7-day window.

## DE-7 · Corrective Action endpoint is functionally hidden
**Symptom:** `GET /api/corrective-actions` returns 404 to Safety + HR + PM + FL tokens in this audit. Endpoint exists in `safety_exports.py` line 116.
**Why it matters:** The CAPA closeout chain is the operational follow-through on every incident. If the read endpoint isn't actually reachable to the people who CLOSE CAPAs, the closeout chain is broken.
**Fix:** Source-trace the `require_token` gate; align with `make_require_safety_or_admin` and add to live RBAC test matrix.

## DE-8 · Incident → CAPA → closeout has no enforced ladder
**Symptom:** Incidents POST works publicly. CAPAs exist in `corrective_actions`. There is no observed mechanism that **requires** an incident to have a linked CAPA before being marked closed, nor a CAPA to have a closeout signature before being marked complete.
**Why it matters:** Insurance + DOT + OSHA audits require demonstrable chain-of-custody on every recordable. Today: theoretically achievable, not enforced.
**Fix:** Schema constraint + UI gate: incident.status="closed" only when ≥1 linked CAPA exists AND every linked CAPA has `closed_at` + `closed_by` populated.

## DE-9 · Operator-employee linkage on Equipment Pre-Op is informal
**Symptom:** Pre-Op forms capture operator name as a string. There is no enforced `employee_id` linkage between the inspection record and the employee master.
**Why it matters:** When equipment fails, you cannot programmatically ask *"how many failed Pre-Ops did this operator submit this month?"*. The accountability link is human-eyeball-only.
**Fix:** Add `operator_employee_id` field; backfill via Employee Linkage Standard (`employee_id` → normalized name + email); surface on accountability timeline.

## DE-10 · Daily Report rediscoverability past 90 days
**Symptom:** `/api/daily-reports` lists current submissions. No archive UI surface, no date-range filter advertised on the list endpoint. Long-tail recall depends on knowing the report ID.
**Why it matters:** Payroll audits and lawsuits can request reports 2-3 years old. Today the recall is a Mongo query, not a UI flow.
**Fix:** Date-range filter + archive list with year/month/project grouping.

## DE-11 · Production drift hides every iter350+ improvement
**Symptom:** Production at `mascidocs.com` returns 404 on every iter350-and-later endpoint probed (CDL importer apply, Dispatch DQ, accountability timeline + PDF).
**Why it matters:** EVERY win in this audit window — bulk CDL load, importer, shared accountability, timeline, PDF, Dispatch DQ, FL DQ richening, Driver Availability tile — exists ONLY on preview. ~24 bounded iters · zero impact on real operators until redeploy.
**Fix:** Schedule production redeploy + smoke checklist for the 8 net-new endpoints.

## DE-12 · No global "platform health" tile for admin
**Symptom:** Operator must read PRD.md, run pytest, or inspect supervisor logs to know "is everything green?". There is no admin dashboard tile that says "X services up · Y open critical · Z drift items vs prod".
**Why it matters:** Governance Convergence Phase 1 surfaced GAPs. There is no living dashboard reflecting their close-state.
**Fix:** Queued — Governance Health Tile (Phase 2 follow-up).

---

## Severity ranking
| Severity | Items |
|---|---|
| 🔴 P0 — operational continuity broken | DE-1, DE-2, DE-11 |
| 🟡 P1 — major workflow inversion | DE-3, DE-4, DE-5, DE-8 |
| 🟢 P2 — recoverable / scoped | DE-6, DE-7, DE-9, DE-10, DE-12 |
