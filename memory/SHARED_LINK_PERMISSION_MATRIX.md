# SHARED LINK · PERMISSION MATRIX

**Date**: 2026-06-02
**Companions**: `DAILY_REPORT_SHARE_FORENSIC_AUDIT.md`, `DAILY_REPORT_SHARE_SECURITY_REVIEW.md`, `DEPLOYMENT_IMPACT_ASSESSMENT.md`.
**Mode**: READ-ONLY.

This matrix consolidates the two email surfaces that touch Daily Reports and adjacent workflows. Both surfaces are documented because they share the recipient's inbox attack surface.

---

## A · Share Email Dialog (PDF-only — the feature the operator named)

### A.1 Endpoint metadata

| Property | Value |
|---|---|
| API endpoint | `POST /api/email-report` |
| Backend file | `backend/server.py:11522-11593` |
| Auth requirement | `Depends(require_admin)` — admin-or-PM token |
| Trigger | `EmailReportDialog` "Send PDF" button on view pages |
| Recipients | Operator-typed (1-20) |
| Delivery | Resend API · PDF attachment · static HTML body |
| URL in body | **NONE** (no `<a href>`) |
| URL in attachment | **NONE** |

### A.2 Permission matrix per recipient state

| Recipient state at email open | Reach record? | Read PDF? | Edit any field? | Vector |
|---|---|---|---|---|
| Logged in as Admin | Yes — via live app, NOT the email | Yes (PDF) | Yes — but only via `EditProjectDialog` on live page (project re-tag); their **session** authorises this, not the email | Session, not URL |
| Logged in as PM (assigned to the project) | Same as Admin (scope-filtered) | Yes (PDF) | Yes — project re-tag only | Session, not URL |
| Logged in as PM (NOT assigned) | NO — 404 on detail endpoint | Yes (PDF) | NO | n/a |
| Logged in as HR | NO — HR-side route is `/hr/daily-reports/{id}` (read-only HR view) | Yes (PDF) | NO | n/a |
| Logged in as Safety / Shop / Dispatch | NO — `/daily/{id}` redirects to PM login | Yes (PDF) | NO | n/a |
| Logged out | NO — gated by `RequireAdminOrPm` → `/pm/login` | Yes (PDF) | NO | n/a |
| Incognito browser | Same as Logged out | Yes (PDF) | NO | n/a |
| Different device (no session) | Same as Logged out | Yes (PDF) | NO | n/a |
| Email forwarded to a third party | Same as Logged out (third party has no session) | Yes (PDF — point-in-time snapshot) | NO | n/a |

**Conclusion**: the Share Email Dialog does not grant edit access to anyone. The recipient can read the snapshot; nothing more.

---

## B · Field Revision `/revise/{token}` email (adjacent, NOT triggered by sharing)

### B.1 Endpoint metadata

| Property | Value |
|---|---|
| API endpoints | `GET /api/revise/{token}` (resolve summary), `POST /api/revise/{token}` (save revision) |
| Backend file | `backend/routes/field_revision.py:71-177` |
| Auth requirement | **None — JWT signature is the auth.** |
| Trigger | Daily Report or Incident lifecycle transition `PENDING_REVIEW → OPEN` ("kickback") |
| Recipient resolution | 5-tier ladder: `fl_user_email → employee_email → submitter_email_at_submit → resolved_pm_email → dead_letter_email` |
| Delivery | `lib/fsi_email_sender.py::fsi_send_email` (Resend) |
| URL in body | `{PUBLIC_BASE_URL}/revise/{token}` — clickable `<a>` |
| Token expiry | 168 hours / 7 days default (`FIELD_REVISION_LINK_TTL_HOURS`) |
| Single-use? | NO — reusable within TTL |

### B.2 Permission matrix per recipient state

| Recipient state at email open | `GET /api/revise/{token}` | `POST /api/revise/{token}` (write revision) | Audit attribution |
|---|---|---|---|
| Logged in as report's original field submitter | ✅ 200 + summary | ✅ 200 — pushes into `field_submitter_revisions[]` | Binding's submitter_name + email · IP captured |
| Logged in as any other admin / PM / HR | ✅ 200 | ✅ 200 — same write | Same — binding's submitter, NOT actual session user |
| Logged in as Safety / Shop / Dispatch | ✅ 200 | ✅ 200 | Same |
| Logged out | ✅ 200 | ✅ 200 | Same |
| Incognito browser | ✅ 200 | ✅ 200 | Same |
| Different device (no session) | ✅ 200 | ✅ 200 | Same |
| Email forwarded to a third party | ✅ 200 | ✅ 200 (token is bearer) | Same — binding's submitter |
| Token expired (>168 h) | ❌ 400 `token_expired` | ❌ 400 `token_expired` | n/a |
| Token tampered | ❌ 400 `token_bad_signature` | ❌ 400 `token_bad_signature` | n/a |
| Binding deleted | ❌ 404 `binding_not_found` | ❌ 404 `binding_not_found` | n/a |
| Token's `bid` claim mutated | ❌ 400 `token_binding_mismatch` | ❌ 400 `token_binding_mismatch` | n/a |

### B.3 Write semantics

* **What writes**: a new dict appended to `field_submitter_revisions[]` array on the Daily Report or Incident document. Fields: `{at, binding_id, submitter, email, note, changes (free-form dict), ip}`.
* **What does NOT write**: canonical record fields (narrative, signatures, photos, weather, time, crew counts, project, audit envelope hash). The original submission remains the source of truth; the envelope SHA256 is NOT recomputed.
* **Chain event**: `revision_saved` row in `workflow_state_events` with `actor = {_actor: "field_submitter", name: binding.submitter_name, email: binding.submitter_email_at_submit}`.

---

## C · Workflow coverage matrix

| Workflow | Share Email Dialog wired? | `/revise/{token}` email wired? |
|---|---|---|
| Daily Reports | ✅ YES (`ViewDailyReport.jsx`) | ✅ YES (`daily_report_lifecycle.py` on PENDING_REVIEW → OPEN) |
| Incidents | ✅ YES (`ViewIncident.jsx`) | ✅ YES (`incident_lifecycle.py` on PENDING_REVIEW → OPEN) |
| Site Inspections (OC-004) | ✅ YES (`ViewInspection.jsx`) | ❌ NO |
| Safety Meetings | ✅ YES (`ViewMeeting.jsx`) | ❌ NO |
| Equipment Inspections | ✅ YES (`ViewEquipmentInspection.jsx`) | ❌ NO |
| QA/QC Inspections (OC-003) | ❌ NO | ❌ NO |
| JHP (Job Hazard Plans) | ❌ NO | ❌ NO |
| Time Verification | ❌ NO | ❌ NO |
| Payroll Variances | ❌ NO | ❌ NO |

The `field_revision.WORKFLOW_COLLECTION` whitelist (`incident, daily_report`) prevents tokens from being aimed at other workflows even with valid signatures.

---

## D · Token / URL property summary

| Property | Share Email Dialog | Revise URL |
|---|---|---|
| URL generated | NONE | `/revise/{token}` |
| Token format | n/a | HS256 JWT-like envelope `h.p.s` |
| Token TTL | n/a | 168 h (env-tunable) |
| Token single-use | n/a | NO (reusable within TTL) |
| Token bound to record | n/a | YES (`wf, rid, bid` claims) |
| Token bound to recipient identity | n/a | NO (bearer token) |
| Token revocable individually | n/a | NO (only secret rotation) |
| Anonymous access | n/a | YES (token IS auth) |
| Recipient session required | YES (admin/PM) to reach edit affordance on live app | NO |
| Edit capable from email | NO | YES (revision proposals) |
| Canonical fields editable | NO (only project re-tag via live `EditProjectDialog`) | NO (revisions land in append-only array) |
| Audit attribution | Live page session user | Binding's original submitter (+ IP) |

---

## E · Per-question answer table (operator's 9 objectives)

| # | Question | Answer |
|---|---|---|
| 1 | What URL is generated by the Daily Report Share Email function? | **NONE.** Email contains only a static PDF attachment + branded HTML shell. |
| 2 | Is the URL view-only / edit-capable / tokenized / authenticated / anonymous / expiring / non-expiring? | n/a — no URL. The ADJACENT `/revise/{token}` URL (separate feature) is: tokenized · anonymous (token-bearer) · expiring (168 h) · edit-capable for revision proposals. |
| 3 | Does the URL permit editing when logged in as owner / another user / logged out / incognito / different device? | Share URL: n/a. Revise URL: YES in ALL 5 scenarios (token IS auth). |
| 4 | Is report ownership validated? | Share Dialog: yes — Admin/PM session is gated at the route level. Revise URL: NO concept of "owner"; only signature + binding match. |
| 5 | Are permissions re-checked when opening from email? | Share: yes — the live app re-checks the session on every navigation. Revise: NO — only the JWT is checked. |
| 6 | Can email recipients edit reports they do not own? | Share: NO. Revise: technically YES if they possess the link, but writes land in a forensic-only append-only array (not the canonical record). |
| 7 | Do shared URLs expire? | Share: n/a (no URL). Revise: 168 h / 7 days default. |
| 8 | Does URL leakage create a workflow-integrity risk? | Share: NO. Revise: MEDIUM — leaked link permits revision proposals (but not canonical-field corruption) for up to 7 days. |
| 9 | Similar behaviour in QA/QC, Site Inspections, Incidents, JHP, Safety Meetings, Time Verification, Payroll Variances? | See §C. Share Dialog: 5/9 workflows. Revise URL: 2/9 workflows (Daily Reports, Incidents). |
