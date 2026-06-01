# OMEGA · Public-Gate Workflow Accountability Report

**Date:** 2026-06-01
**Mode:** Forensic, evidence-only.
**Scope:** Cross-workflow rollup of public-gate ownership chains.
**Overall verdict:** 🟡 **YELLOW with one 🔴 RED systemic gap.**

---

## 1 · Public-gate inventory (confirmed against the live React router)

| Workflow | Public-gate route | Backend gate | Status |
|---|---|---|---|
| Daily Report | `/daily/new`, `/daily/submit` | `rate_limit_public_post` only | 🟡 Public |
| QA/QC Inspection | `/qaqc/:slug/new` | `rate_limit_public_post` only | 🟡 Public |
| JHA Plan submit | `/jha` (hub) → form | (see JHA module — also rate-limit-only on POST per the existing pattern) | 🟡 Public |
| Safety Meeting | `/safety-meeting/new` (public mode supported) | `rate_limit_public_post` only | 🟡 Public |
| Equipment Pre-Op Inspection | `/equipment/new` (public submit pattern) | `rate_limit_public_post` only | 🟡 Public |
| Incident Report | `/incidents/new` (public submit) | `rate_limit_public_post` only | 🟡 Public |

(Equipment Pre-Op auto-email override applies — operator directive, Shop Manager only.)

All public gates share the **same accountability pattern**:

1. Form accepts a free-text submitter name (varies by form — `prepared_by`, `inspector_name`, `attendee_name`, etc.)
2. Server-side PM resolution via `project_number → jobs_master.pm_email`
3. Auto-email fires to PM + co-PMs + ALWAYS_CC on submit
4. No email/phone/portal_user_id captured for the submitter
5. No revision URL bound to the submission

---

## 2 · Source-of-truth comparison

| Identity dimension | Source | Provable? | Notes |
|---|---|---|---|
| Submitter NAME | Form text field | 🟡 Yes (as a string) | Cannot be resolved to a unique person |
| Submitter EMAIL | — | 🔴 NO | Not captured on any public-gate form |
| Submitter PHONE | — | 🔴 NO | Not captured |
| Submitter EMPLOYEE_ID | — | 🔴 NO | No FK; directory linkage absent |
| Submitter PORTAL_USER_ID | — | 🔴 NO | Public-gate has no portal session |
| Submitter DEVICE_ID | localStorage only (`crewMemory.js`) | 🔴 NO server visibility | Device-local · never synced · 30-day TTL |
| Submitter IP / UA | `audit_events.ip, user_agent` | 🟢 YES for the POST request only | Not denormalized onto the workflow row |
| PROJECT_NUMBER | Form (required) | 🟢 YES | Required validation |
| PM EMAIL | `jobs_master.pm_email` lookup | 🟢 YES | DB-backed |
| Co-PM EMAILS | `jobs_master.co_pm_emails` | 🟢 YES | DB-backed |
| Subcontractor (QA/QC only) | Form (string) | 🟡 String only | Not validated against any vendor master |
| Department (CAPA only) | Form / dropdown | 🟡 String | Cannot route to a person |

---

## 3 · The structural finding

🔴 **SYSTEMIC GAP — there is one consistent accountability hole across every public-gate workflow:**

> The PM side of the ownership chain is GREEN. The FIELD side is RED.

The platform can always reach (a) the assigned PM, (b) co-PMs, and (c) office/safety/admin roles. It **cannot reach the field submitter** through any automated channel because the field submitter's contact information is not captured.

### What this means operationally

When a Daily Report is kicked back, a QA/QC deficiency requires re-walk, a JHA needs corrections, a Safety Meeting roster has missing signatures, or an Equipment Pre-Op flags a defect — **the office can know, but the field crew cannot be told by the platform.** Office staff must contact field crews off-platform (phone, text, radio, walk to the trailer).

This breaks the operator's Phase 1A "Definition of DONE":

> "corrective actions cannot reliably reach the responsible party"

---

## 4 · Notification delivery — actual evidence

Live `notifications` collection probe — schema fields:

```
id, type, title, message, severity, recipient_role, recipient_user_id,
linked_source_module, linked_source_record_id, linked_project_number,
linked_employee_id, linked_equipment_id, linked_task_id,
delivery, created_at, read_by, acknowledged_at, acknowledged_by, expires_at
```

Live `delivery` field on sampled row:

```
{ internal: True, email: False, push: False, sms: False }
```

**Every channel except `internal` is False today.** The schema is forward-compatible (email/push/sms keys exist) but no dispatcher writes `true` to any of them. Confirmation:

* `push_subscriptions` collection — **0 rows**
* `web_push_subs` collection — **0 rows**
* `devices` collection — **0 rows**
* `device_registrations` collection — **0 rows**
* No `VAPID_PUBLIC_KEY` / `VAPID_PRIVATE_KEY` in `backend/.env`
* No `TWILIO_*` / `FROM_NUMBER` / `SMS` in `backend/.env`
* Existing service worker (`/app/frontend/public/sw-thumbs.js`) is **scope-limited to photo thumbnails only** — never subscribes to push, never registers VAPID

### Implication

* In-app bell notifications work for **authenticated users** of the platform. The bell is wired but **no field crew sees it** because they are not logged in.
* PM auto-email works — but only on the original submission, never on kickback or correction events.
* Push notifications are not implemented at all.
* SMS is not implemented at all.

---

## 5 · Workflow-by-workflow classification

| Workflow | Submitter ID | Supervisor ID | PM resolvable | Closure can reach field? | Classification |
|---|---|---|---|---|---|
| Daily Report (OC-002) | 🔴 | 🔴 | 🟢 | 🔴 | 🟡 **YELLOW** |
| QA/QC Follow-Up (OC-003) | 🔴 | 🔴 | 🟢 | 🔴 | 🟡 **YELLOW** |
| Site Inspection Follow-Up (OC-004) | 🔴 expected | 🔴 expected | 🟢 expected | 🔴 expected | (not yet built — same gap will inherit) |
| JHA Acknowledgement Ledger (OC-005) | partial (employee directory mapping for crew sign-off) | n/a | 🟢 | 🟡 if directory has email | (iter454 scope) |
| Safety Meeting (similar pattern) | 🔴 expected | 🔴 expected | 🟢 expected | 🔴 expected | (not in Phase 1A) |
| Equipment Pre-Op (similar pattern) | 🔴 expected | 🔴 expected | 🟢 (shop mgr override) | 🔴 expected | (not in Phase 1A) |

---

## 6 · The 1-of-261 problem

Live probe:

```
employees with email   :   1 / 261
employees with phone   :   0 / 261
```

Even if every public-gate form captured `employee_id`, the employee directory carries no contact information for ~99.6% of the workforce. **Phase 1A cannot achieve "corrective actions reach the responsible party" until the employee directory is enriched** OR an alternative delivery channel is added (push subscription bound to device at submit time, SMS via a separately-captured field-crew phone, etc.).

---

## 7 · Recommendations (NO design proposals — operator decision required)

Three operator-decision branches:

* **Branch A — Tighten field identity at the public gate.** Add to every public-gate form: a required dropdown sourcing the employee directory, plus a per-submit contact field (email or phone). Backfill the employee directory.

* **Branch B — Add alternative delivery channels.** Implement Web Push (VAPID) bound to device at submit time, and/or SMS via Twilio. Capture the channel binding on the submission row.

* **Branch C — Accept the gap as out-of-Phase-1A scope.** Classify all 4 public-gate workflows currently in Phase 1A as YELLOW-with-deferred-closure and document that closure-loop notifications continue to flow through PMs (who phone the field).

A separate `PUSH_NOTIFICATION_FEASIBILITY_REPORT.md` (this batch) explores the technical viability of Branch B.

A separate `REVISION_DELIVERY_OPTIONS.md` (this batch) evaluates the secure-revision-link mechanics for either branch.

---

## 8 · Verdict

🟡 **YELLOW WITH A 🔴 RED SYSTEMIC SUB-FINDING.**

* PM side: GREEN — proven, robust, DB-backed.
* Field side: RED — submitter contact + revision path absent across the entire public-gate surface.

The Phase 1A workflows can transition state and audit those transitions (proven in iter451-452), **but the operator's Definition of DONE — "corrective actions reach the responsible party" — is not satisfied for any public-gate field submission today.**

**Recommendation:** classify the field-side gap as a **CRITICAL PHASE 1A GAP** and await operator authorization for one of Branches A / B / C above. No code. No design. Evidence on the table.
