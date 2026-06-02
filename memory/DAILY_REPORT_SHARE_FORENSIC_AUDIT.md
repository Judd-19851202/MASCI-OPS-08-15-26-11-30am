# DAILY REPORT SHARE EMAIL · FORENSIC AUDIT

**Date**: 2026-06-02
**Authority**: P0 operator directive — read-only forensic audit.
**Mode**: READ-ONLY. No code, data, permission, or deploy changes performed.
**Companion docs**: `DAILY_REPORT_SHARE_SECURITY_REVIEW.md`, `SHARED_LINK_PERMISSION_MATRIX.md`, `DEPLOYMENT_IMPACT_ASSESSMENT.md`.

---

## 1 · Reported behaviour

A Superintendent reports:

> "After sharing a Daily Report to my email using the Daily Report Share Email feature, I can later edit the Daily Report from the received email."

This audit forensically reconstructs the code paths involved and classifies the behaviour.

---

## 2 · Surface inventory — what "Daily Report Share Email" actually is

The phrase "Daily Report Share Email" maps to exactly **one** UI entry point in the codebase:

* `frontend/src/components/EmailReportDialog.jsx` (242 LOC) — the dialog that opens from the **"Email"** button on `ViewDailyReport.jsx` (line 670).
* It calls `POST /api/email-report` (backend `server.py:11522`, gated by `Depends(require_admin)`).

A SECOND, OPERATIONALLY ADJACENT email path also exists and is the most likely source of the Superintendent's confusion:

* `backend/lib/field_submitter_identity.py::notify_field_submitter()` — sends a **signed tokenized `/revise/{token}` link** to the original field submitter (iter452.5 Tier 1).
* It is triggered ONLY by lifecycle transition `PENDING_REVIEW → OPEN` ("kicked back to field") on the Daily Report lifecycle (`backend/routes/daily_report_lifecycle.py:161-187`).
* It is NOT triggered by the share dialog. It is NOT triggered by report submission. It is NOT triggered by any user action labelled "share".

Both paths are audited in this document because they share the recipient's inbox surface and can be conflated by an end-user.

---

## 3 · Path A — Share Email Dialog (the feature the operator named)

### 3.1 What URL is generated?

**NONE.**

The HTML email body (`backend/pdf_render.py::render_email_html`, lines 1456-1528) is a static branded shell that contains:

* A base64-embedded MASCI logo (data URI, not a remote fetch).
* The record title, project name, date.
* The optional operator note (escaped).
* The literal sentence "The full Daily Job Report is attached as a PDF."
* The literal text "mascidocs.com" — **as plain text, not a hyperlink** (no `<a href>` anywhere in the function).

There is no `<a href>`, no embedded URL, no token, no record ID query string, and no deep-link parameter anywhere in the rendered body.

The PDF (`backend/pdf_render.py::render_record_pdf`) is rendered via WeasyPrint from static HTML; `grep -n "href\|<a "` against the entire `pdf_render.py` (1528 LOC) returns **zero** matches. The PDF is a point-in-time forensic snapshot — pure paper, no clickable navigation.

### 3.2 URL property matrix — Share Email Dialog

| Property | Value |
|---|---|
| Generated URL | **NONE** |
| View-only? | n/a (no URL) |
| Edit-capable? | **NO** (no URL to click) |
| Tokenized? | n/a |
| Authenticated? | n/a |
| Anonymous? | n/a |
| Expiring? | n/a |
| Non-expiring? | n/a |

### 3.3 Edit-capability matrix — Share Email Dialog

| Recipient state when opening the email | Can they reach `/daily/{id}`? | Can they edit anything? |
|---|---|---|
| Logged in as report owner (admin/PM/HR) | Yes — by navigating to the live app independently of the email | YES — but **only** the project re-tag via `EditProjectDialog` (PATCH `/api/admin/records/daily-reports/{id}/project` — see §3.5). Their existing session grants this access. The email did not. |
| Logged in as another admin / PM | Same as above | Same as above — admin/PM scope is global on this surface |
| Logged out | They cannot reach the record. `/daily/{id}` is gated by `RequireAdminOrPm` (`frontend/src/components/RequireAdminOrPm.jsx`) — redirects to `/pm/login`. | NO |
| Incognito browser | Same as "Logged out" | NO |
| Different device | Same as "Logged out" | NO |

### 3.4 Report-ownership validation

`ViewDailyReport.jsx` does not perform per-record ownership checks. The page-level guard is the role gate (Admin OR PM token). PMs are additionally scoped to their assigned `project_number` via `compute_pm_scope` on the **list** endpoint (`backend/routes/daily_reports.py:300`), and the detail endpoint enforces the same scope at `/daily-reports/{report_id}` (`daily_reports.py:496`). So:

* **Admin tokens** = global edit/view on every Daily Report (by design).
* **PM tokens** = edit/view only on reports tied to projects they're PMs of.
* There is no concept of "report owner = submitter"; the canonical authority is project assignment + role.

### 3.5 What can actually be edited from the live page?

Inspecting `frontend/src/pages/ViewDailyReport.jsx` for editable affordances:

* `<EditProjectDialog kind="daily-reports" recordId=… current=… />` — **the ONLY edit affordance on this page**.
* It edits **project_name · project_number · project_id · location** — and nothing else. It calls `PATCH /api/admin/records/daily-reports/{id}/project`.
* Narrative, signatures, photos, time entries, weather, crew counts, checklist, and the audit envelope hash are NOT mutable from this dialog.

There is **no PUT/PATCH endpoint** for full Daily Report records in `backend/routes/daily_reports.py` (only POST create, GET, GET-list, DELETE).

### 3.6 Classification — Share Email Dialog alone

🟢 **EXPECTED BEHAVIOUR.** The Share Email Dialog emits no URL, no token, and grants no edit capability. Any subsequent edit performed by the Superintendent is the result of his existing browser session on the live app — **not** the email content.

---

## 4 · Path B — Field Revision tokenized email (`/revise/{token}`)

This is a SEPARATE, NAMED feature shipped in **iter452.5** (`backend/routes/field_revision.py` · `backend/lib/field_submitter_identity.py`).

### 4.1 When is this email sent?

ONLY when an admin/HR/safety user transitions a Daily Report from `PENDING_REVIEW` → `OPEN` ("kick back to field") via `POST /api/daily-reports/{id}/transition` (`daily_report_lifecycle.py:161`). The same dispatch is wired for Incidents (`incident_lifecycle.py:157`).

It is NOT sent on:

* Initial report submission.
* The Share Email Dialog (Path A).
* Any user action labelled "share".

### 4.2 What URL is generated?

`{PUBLIC_BASE_URL}/revise/{token}` where `token` = compact JWT-like envelope `header.payload.signature` (HS256, in-house signer in `lib/field_submitter_identity.py::mint_revision_token`, lines 361-392).

Payload claims:

```
{
  "wf":  "daily_report" | "incident",
  "rid": <record uuid>,
  "bid": <binding uuid>,
  "iat": <issued epoch>,
  "exp": <issued + 168 hours epoch>,  ← default; env FIELD_REVISION_LINK_TTL_HOURS overrides
  "n":   <16 hex chars entropy>
}
```

Signing secret resolution order (`_jwt_secret()`, lines 83-93):

1. `FIELD_REVISION_JWT_SECRET`
2. `JWT_SECRET` ← what preview currently uses
3. `ADMIN_HMAC_SECRET`
4. **Dev-fallback string `"iter452_5_dev_only_secret_DO_NOT_USE_IN_PROD"`** if all 3 env vars are missing/empty.

### 4.3 URL property matrix — Revise URL

| Property | Value |
|---|---|
| Generated URL | `{PUBLIC_BASE_URL}/revise/{token}` |
| View-only? | NO — supports BOTH GET (resolve summary) and POST (save revision). |
| Edit-capable? | **YES** — POST appends `{at, binding_id, submitter, email, note, changes, ip}` into the record's `field_submitter_revisions[]` array AND stamps `field_submitter_last_revised_at`. The canonical record fields (narrative, signatures, photos, time) are NOT overwritten. |
| Tokenized? | YES — HS256 JWT-like envelope. |
| Authenticated? | **The token IS the auth.** No portal session is consulted. |
| Anonymous? | YES — recipient does not need to be logged in. |
| Expiring? | YES — default 168 hours (7 days). |
| Non-expiring? | NO. |
| Single-use? | **NO** — token is reusable for as many revision POSTs as the holder wants within the TTL window. Each POST emits a `revision_saved` chain event. |
| Bound to recipient? | NO — the token is bound to `(wf, rid, bid)`. ANY person in possession of the URL can submit. |

### 4.4 Edit-capability matrix — Revise URL

| Recipient state when opening the email | Can `POST /api/revise/{token}` succeed? | What gets written? |
|---|---|---|
| Logged in as report owner | YES | A new entry into `field_submitter_revisions[]`. The chain event records the BINDING's submitter, NOT the actual session user. |
| Logged in as another user | YES | Same as above. Session is ignored. |
| Logged out | YES | Same as above. |
| Incognito browser | YES | Same as above. |
| Different device | YES | Same as above. |

In ALL five scenarios, the platform's audit trail attributes the revision to the BINDING's `submitter_name` + `submitter_email_at_submit` (the original field submitter at submit time), plus the IP address of whoever made the POST. The actual person who possessed the link is NOT distinguished from the original submitter in the chain event's `actor` block (`backend/lib/field_submitter_identity.py:171-173`).

### 4.5 What does "edit" actually mean here?

Examining `backend/routes/field_revision.py:125-177`:

```python
revision_doc = {
    "at":         datetime.now(timezone.utc).isoformat(),
    "binding_id": binding.get("id") or "",
    "submitter":  binding.get("submitter_name") or "",
    "email":      binding.get("submitter_email_at_submit") or "",
    "note":       (body.note or "")[:2000],
    "changes":    body.changes or {},   ← arbitrary dict, no schema validation
    "ip":         <x-forwarded-for>,
}
await db[col].update_one(
    {"id": rid},
    {"$push": {"field_submitter_revisions": revision_doc},
     "$set":  {"field_submitter_last_revised_at": ...}},
)
```

* The CANONICAL record fields (narrative, signatures, photos, time, weather, crew counts, project, audit envelope hash) are **NOT overwritten**.
* Revisions land in an **append-only `field_submitter_revisions[]` array**. Forensic chain preserved.
* `changes` is a free-form `Dict[str, Any]` — no schema gate. An attacker could push arbitrary structured noise into the array (size-capped by Mongo's 16 MB doc limit but not pre-validated).
* The original record's `audit_envelope_sha256` is NOT recomputed when revisions are pushed — so the envelope hash remains the foreman's original submission, untouched.

This is by design (the source-of-truth IS the original submission), but the audit attribution glosses over WHO actually pushed the revision: the chain event records the BINDING's submitter as the actor, regardless of who held the link.

### 4.6 Classification — Revise URL alone

🟡 **GOVERNANCE CONCERN** — see `DAILY_REPORT_SHARE_SECURITY_REVIEW.md` §1 for the seven enumerated concerns.

---

## 5 · Probable root cause of the Superintendent's report

Highest-likelihood reconstruction:

1. The Superintendent opened the live `ViewDailyReport` page (logged in as Admin or PM in his browser).
2. He clicked **"Email"**, sent the PDF to his personal email via the Share Email Dialog (Path A).
3. He received the PDF email — there is **no clickable link inside it**.
4. He returned to the still-open browser tab on the live app, OR navigated back to it manually, and saw the **"Edit Project" (amber pencil icon) button** rendered by `EditProjectDialog` (line 203 of `ViewDailyReport.jsx`).
5. He clicked it and edited the project tag. He interpreted "I just emailed myself the report, and now I can edit it" as causation, when in fact the email had nothing to do with it — his **portal session** is what authorised the edit.

A secondary possibility: he received an `/revise/{token}` kickback email from a separate workflow event AND conflated it with the share email he sent. We were unable to reach into the recipient's inbox to disambiguate (READ-ONLY scope).

---

## 6 · Sister-workflow coverage

Cross-workflow inventory of BOTH email surfaces:

| Workflow | Share Email Dialog (PDF, no URL) | Revise URL email (tokenized, edit-capable) |
|---|---|---|
| Daily Reports | ✅ wired (`ViewDailyReport.jsx`) | ✅ wired (`daily_report_lifecycle.py`) |
| Incidents | ✅ wired (`ViewIncident.jsx`) | ✅ wired (`incident_lifecycle.py`) |
| Site Inspections | ✅ wired (`ViewInspection.jsx`) | ❌ NOT wired (despite ITER453 OC-004 lifecycle) |
| Safety Meetings | ✅ wired (`ViewMeeting.jsx`) | ❌ NOT wired |
| Equipment Inspections | ✅ wired (`ViewEquipmentInspection.jsx`) | ❌ NOT wired |
| QA/QC Inspections (OC-003) | ❌ NOT wired | ❌ NOT wired |
| JHP (Job Hazard Plans) | ❌ NOT wired | ❌ NOT wired |
| Time Verification | ❌ NOT wired | ❌ NOT wired |
| Payroll Variances | ❌ NOT wired | ❌ NOT wired |

The `WORKFLOW_COLLECTION` map in `field_revision.py:48-52` is explicitly limited to `{"incident", "daily_report"}` — an attacker cannot point a forged token at QA/QC, JHP, etc. even with a valid signature, because those workflows are not in the literal allow-list.

---

## 7 · Final forensic verdict

🟡 **GOVERNANCE CONCERN.**

* The **Share Email Dialog feature explicitly named by the operator is 🟢 EXPECTED BEHAVIOUR.** It emits no URL, no token, no edit affordance.
* The **adjacent Field Revision token feature is 🟡 GOVERNANCE CONCERN** — see Security Review for the 7 enumerated issues.
* The **most likely true root cause** of the Superintendent's report is **session-resident edit affordance** on the live `ViewDailyReport` page (the `EditProjectDialog` amber button), conflated with the email he himself sent. This is by-design but presents an operator-perception mismatch worth resolving.

No security defect was found. No workflow-integrity DEFECT was found that warrants 🔴 escalation. The pending items are best classified as governance hardening recommendations, not blockers.
