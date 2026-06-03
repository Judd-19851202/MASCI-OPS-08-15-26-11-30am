# LIVE PRODUCTION · WORKFLOW CERTIFICATION
## OMEGA Directive · Phase 3 of 10

**Date**: 2026-06-03
**Target**: https://mascidocs.com (production)
**Probe vector**: External anonymous probes ONLY. Authenticated workflow walkthrough requires operator-side execution.

---

## 🟡 PHASE 3 VERDICT — OPERATOR WALKTHROUGH REQUIRED

The certification agent cannot create or submit production workflows because production credentials are not available to the agent (Daily Report submission, Incident creation, QA/QC, Site Inspection, JHA acknowledgement, etc. all require authenticated sessions tied to real operator identities — the agent must NOT manufacture production accounts or pose as an operator).

What the agent **CAN** certify externally is reported below. The full workflow walkthrough is delegated to the operator using the structured checklist in §3.

---

## 1 · What the agent verified externally (proxies for workflow surface health)

| Surface probe | Result |
|---|:-:|
| Frontend SPA route loads for `/login`, `/hr-login`, `/admin`, `/fl-portal`, `/safety-portal`, `/dispatch-portal`, `/recovery` | 🟢 all 200 |
| Bundle parses (5.00 MB JS served via Cloudflare in 413 ms) | 🟢 |
| Auth-gated API endpoints return 401 to anon (correct gating) | 🟢 `/api/projects` 401, `/api/users` 401 |
| Guidance/coaching tips for each workflow respond | 🟢 daily-report=5, incident=5, jha=5, preop=5, inspection=5, qaqc=5 (Phase 2) |
| Public health endpoint | 🟢 200 |

These are necessary but not sufficient. The workflow data path (create → save → submit → persist → revisit) cannot be certified from outside.

---

## 2 · Probable cause of any future workflow defects (pre-arranged guidance for operator walkthrough)

If a workflow walkthrough surfaces issues, the diagnostic pre-list is:

1. **401 in browser** → session expired or wrong portal — re-login.
2. **500 on submit** → check `/api/version` `started_at` to confirm app stable; check Sentry for the stack trace.
3. **Persistence missing** → reopen the saved record; check the listing endpoint; check audit trail.
4. **Lifecycle event missing** → check `/api/<resource>/lifecycle` for the resource and the actor.

---

## 3 · Operator walkthrough checklist (required to complete Phase 3)

The operator must execute the following on https://mascidocs.com using their production credentials and record PASS/FAIL/NOTES for each step:

### 3.1 · Daily Report
- [ ] Log in to Field Leadership portal
- [ ] Create a Daily Report against a real project
- [ ] Fill: crew, hours, equipment, materials, photos, narrative
- [ ] Save as draft → verify the draft persists on page reload
- [ ] Submit → verify status transitions and confirmation
- [ ] Reopen the submitted DR → verify all fields persisted
- [ ] Confirm it appears in the project's Daily Reports list
- [ ] Confirm hours flow visible to HR (cross-portal handshake)

### 3.2 · Incident
- [ ] Open Incident form
- [ ] Create with severity, location, narrative, witnesses, photos
- [ ] Submit → confirm 3-attestation gate behaviour matches doctrine
- [ ] Reopen → confirm lifecycle events recorded
- [ ] Verify visibility from Safety portal

### 3.3 · QA/QC
- [ ] Open QA/QC form
- [ ] Submit with deficiency, owner, due date
- [ ] Test all three closure paths: (A) re-inspect, (B) corrective action, (C) exception with dual sign-off
- [ ] Confirm closure path enforces required evidence
- [ ] Reopen the record → confirm history visible

### 3.4 · Site Inspection
- [ ] Open Site Inspection form
- [ ] Submit with findings raised, owner, due date
- [ ] Re-inspect path → verify re-inspection evidence required
- [ ] Confirm FINDINGS_RAISED (Site) vs DEFICIENCY_RAISED (QA/QC) are tracked separately
- [ ] Reopen → confirm lifecycle events recorded

### 3.5 · JHA / JHP
- [ ] Open a posted JHA
- [ ] Acknowledge (signature)
- [ ] Verify the acknowledgement appears on the JHA record
- [ ] Sign out, sign back in, reopen → confirm acknowledgement persisted
- [ ] Verify the acknowledgement counts toward the project's JHA acknowledgement roster

### 3.6 · Acceptance criteria
- All flows complete end-to-end without 500s.
- All persistence checks return the expected payload.
- No data disappears between steps.
- All lifecycle events are visible in the resource's history view.

---

## 4 · Re-classification rule

After the operator walkthrough is complete:
- If every workflow passes → re-issue Phase 3 as 🟢 PRODUCTION WORKFLOW CERTIFIED.
- If any workflow fails persistence or lifecycle → classify per Phase 10 severity (HIGH / BLOCKER) and stop.

---

## 5 · Phase 3 outcome (current)

🟡 **OPERATOR WALKTHROUGH REQUIRED** — external probes confirm the workflow surface is reachable, but end-to-end workflow data-path certification requires operator-side execution. Checklist provided in §3.
