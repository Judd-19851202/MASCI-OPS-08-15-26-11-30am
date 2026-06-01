# OMEGA · JHP_ACKNOWLEDGEMENT_GAP_REPORT.md

**Date:** 2026-06-01
**Trigger:** Operator OC-005 reality check. The prior fork's task list lists `iter454 OC-005 JHA Acknowledgement Ledger`. The operator's correction reframes the workflow as **JHP Acknowledgement Ledger** and clarifies that JHPs are **PDFs uploaded by the Safety department**, not crew-authored forms.
**Method:** Static code trace + live data query. No code changed.

---

## 1 · Headline gap

There is **no acknowledgement infrastructure of any kind** for JHPs in the platform today.

| Surface | Present? | Citation |
|---|---|---|
| Acknowledgement collection (any name) | ❌ NO | Live `db.list_collection_names()` returns no `jhp_*`, `jha_*`, `job_hazard_acknowledgements`, `jhp_signoffs`, `jha_signoffs`, `jhp_attestations`. Verified live. |
| Backend endpoint to record an acknowledgement | ❌ NO | `grep -rn "acknowledg" /app/backend/job_hazard_files.py /app/backend/routes/safety.py` returns ONLY `stop_work_acknowledged` (a string on the vestigial JHA form, not an ack record). |
| Frontend UI control to acknowledge | ❌ NO | `JhaPlansHub.jsx` (245 LOC) renders only `<a>` download links. No checkbox, no signature pad, no "I have read this" affordance. |
| Audit row written on view/download | ❌ NO | `server.py:2347-2381` streams the file without writing any audit row. The public download endpoint is anonymous. |
| Identity at the download point | ❌ NO | `GET /api/job-hazard-files/{file_id}/download` carries no `Depends` — anyone with the URL gets the PDF. |
| Acknowledgement requirement / gate | ❌ NO | No middleware blocks any other workflow on missing JHP ack. |
| Reporting / dashboard for Safety/PM | ❌ NO | No endpoint returns "who has acknowledged JHP X" or "which crew members are unacknowledged on project Y". |

The OC-005 ledger does not exist in any partial form. Building it requires a full vertical from data model through to reporting.

---

## 2 · What this means for the JHP workflow today

A crew member's JHP "acknowledgement" is currently **inferred and unprovable**. The presumed-but-unwritten contract is:

1. Safety uploads a JHP PDF → admin UI.
2. PMs / Foremen are expected to circulate the PDF to crews.
3. Crews are expected to read it.
4. If an incident occurs, the company has the upload row in `job_hazard_files` proving "we had a JHP" — but it has no proof "the involved crew member read it."

OSHA / contract / insurance ramifications of this gap are outside the scope of this audit, but the **technical fact** is: the platform does not currently support proving that an individual crew member acknowledged any specific JHP at any specific point in time.

---

## 3 · The two adjacent acknowledgement patterns the platform DOES carry (reusable evidence)

These are useful precedents for OC-005 design — they are NOT replacements.

### Pattern A · `training_hits` collection (HelpTip view tracking)
* **88 rows live.** Schema: tracks individual tooltip views, time-on-screen, user, page.
* Pattern: "user X interacted with content Y at time T". Closest existing primitive to "user X acknowledged JHP Y at time T".
* Limitation: HelpTip is read-only telemetry, not a signed attestation. Cannot satisfy "the employee actively confirmed comprehension."

### Pattern B · `safety_training_records` collection (formal training)
* 6 rows live. Schema typical of a credentialing system: `employee_id`, `training_type`, `completed_at`, `expires_at`, `instructor`, etc.
* Pattern: "employee X completed credentialed training Y, valid through date Z."
* Reusable design idiom for JHP acknowledgements (treat each ack as a one-shot credential pinned to a file version), but not directly extensible — the topic/credential schema is fixed.

### Pattern C · `field_submitter_bindings` collection (iter452.5)
* 0 rows live (recently introduced). Schema: ties a public-gate submission to an identity-resolved person + signed-token follow-up flow.
* **Most directly applicable pattern for OC-005.** A JHP ack is structurally identical to an FSI binding: "this person + this record + this timestamp + this consent text version + this signed-link audit."
* The whole iter452.5.1 5-tier identity ladder (FL → employee → per-submit → PM relay → dead-letter) is directly transferable: the supervisor reading the JHP on the field crew's behalf maps cleanly to tier-1 FL-token resolution.

### Pattern D · `BilingualConsent.jsx`
* Pre-built bilingual (EN/ES) consent affordance with checkbox + version-stamped consent text. Currently used on Daily Report and Incident public forms.
* Directly transferable to a JHP ack UI: replace the consent body with "I have read JHP DOC-ID for project X" + signature.

---

## 4 · The 8 capability gaps required to close OC-005

Anchored on the iter450 PRD's OC-005 short description and the operator's JHP framing. Listed in dependency order.

| # | Capability | Existing primitive to reuse | Net-new work |
|---|---|---|---|
| 1 | **Identity at the download point** | `X-FL-Token` (iter452.5.1) · `is_valid_fl_user_token_async` | Wrap `GET /api/job-hazard-files/{file_id}/download` with optional identity capture; emit an audit row whenever identity is present |
| 2 | **JHP version pinning** | `db.job_hazard_files` upsert pattern | Add `version_number` field auto-incremented per `(project_number, scope='jha')`; older rows get `is_current=False` on new upload |
| 3 | **Safety author identity** | `X-FL-Token` (iter452.5.1) | Capture `safety_author_id` from FL token at upload time (vs current free-text `uploaded_by`) |
| 4 | **Acknowledgement collection** | `field_submitter_bindings` schema as model | New `jhp_acknowledgements` collection: `{id, jhp_file_id, project_number, version_number_at_ack, employee_id, employee_name, employee_email, supervisor_token_id (if relay), signature_image (optional), ip, user_agent, locale, consent_text_version, acknowledged_at}` |
| 5 | **Acknowledgement POST endpoint** | `routes/field_revision.py` revision pattern · `lib/idempotency.py` | `POST /api/jhp/{file_id}/acknowledge` accepting employee_id + signature + locale; idempotent on `(file_id, employee_id, version_number)` |
| 6 | **Acknowledgement UI** | `BilingualConsent.jsx` · `SignaturePad.jsx` | Wire onto `JhaPlansHub.jsx` — "I have read this" affordance after download confirmation |
| 7 | **Audit chain integration** | `lib/workflow_state_events.py::write_state_event` (already pluralized for many workflows) | Emit `workflow="jhp"` `to_state="ACKNOWLEDGED"` rows so Phase 1B aggregator picks them up natively |
| 8 | **Reporting · "who hasn't acked"** | Existing `employees.project_numbers` array + `jobs_master` | `GET /api/admin/jhp-acknowledgements/coverage?project_number=&jhp_id=` returns ack matrix |

---

## 5 · OC-005 capability gap classification (operator-grade)

| Gap | Type | Closing-effort feel |
|---|---|---|
| 1 | Wire-up | Small — one route change + audit row |
| 2 | Schema | Small — additive field + nightly recompute job |
| 3 | Wire-up | Trivial — token capture mirrors iter452.5.1 P0 |
| 4 | Schema | Small — new collection · 3 indexes |
| 5 | Endpoint | Medium — POST handler · validation · idempotency wrap |
| 6 | UI | Medium — bilingual ack widget · signature pad · resilient-queue support for offline |
| 7 | Integration | Trivial — single `write_state_event` call |
| 8 | Reporting | Medium — admin query · CSV export · Command Center tile |

🟢 None of the eight gaps requires Tier-2 infrastructure (SMS, push, PWA install). All are buildable inside the OMEGA "Phase 1A workflow completeness" envelope.

---

## 6 · Adjacencies that must NOT be broken by OC-005

These existing capabilities are stable and must remain unchanged:

| Surface | Why it must not change |
|---|---|
| Public download endpoint `/api/job-hazard-files/{file_id}/download` | Crews currently scan QR codes from `JhaPlansPoster.jsx` to fetch PDFs without login. Adding hard auth would break offline access. Identity capture must be OPTIONAL on the download endpoint; the ack POST is where identity becomes mandatory. |
| Trench-box library piggyback (`scope="trench_box"`) | Six existing rows. Any change to the schema/collection must preserve `scope` semantics. |
| `JhaPlansAdmin.jsx` admin upload UI | Active. New version field + safety-author capture must be additive. |
| Existing JHA form-submission system (`/api/jhas`, `db.jhas`) | Operator explicitly stated MASCI does not use JHA forms — but the routes exist. OC-005 should not touch them in this batch (separate authorization conversation). |

---

## 7 · OC-005 scope-and-sequencing recommendation (NOT authorized — operator-visible options)

Three plausible build envelopes, each with effort estimates. Operator selects one (or rejects all and re-scopes).

### Option 1 — Minimum viable ledger (recommended)
* Capabilities 1, 3, 4, 5, 7 from §4.
* Defer 2 (versioning) by treating each `job_hazard_files` row as immutable and binding acks to `file_id`. Older rows on re-upload remain valid for prior acks (no `is_current` flag needed yet).
* Defer 6 (full bilingual ack UI) — initial UI is a single-language checkbox + button.
* Defer 8 (reporting matrix) to iter455.1 alongside Phase 1A integration certification.
* Estimated effort: **~4 realistic days / ~6 buffered.**

### Option 2 — Full Phase-1A-ready ledger
* All 8 capabilities from §4.
* Estimated effort: **~7 realistic days / ~10 buffered.**

### Option 3 — Rename + reframe pass first, then OC-005
* Sub-batch A: rename code-level `JHA` identifiers → `JHP` (one frontend route rename + alias retention for back-compat + Mongo collection alias). Estimated 1-2 days.
* Sub-batch B: Option 1 OR Option 2 above.
* Estimated effort: **3-4 days additional rename overhead** on top of the chosen ledger option.

---

## 8 · Discipline check

| Check | Status |
|---|---|
| Zero code changed | ✅ |
| Every gap claim citation-backed | ✅ |
| Existing reusable primitives enumerated | ✅ |
| Three operator-visible scope options presented | ✅ |
| No Tier-2 infrastructure proposed (per operator's standing freeze) | ✅ |
| Adjacencies that must not break enumerated | ✅ |

---

## 9 · Authorization status

🛑 **STOPPED.** All three reports delivered:
* `JHP_CODE_REALITY_AUDIT.md`
* `JHP_DATA_MODEL_AUDIT.md`
* `JHP_ACKNOWLEDGEMENT_GAP_REPORT.md` (this file)

Awaiting operator direction. Options on the table:
1. Authorize a code-level `JHA` → `JHP` rename batch (sub-batch A above) before continuing OC-005.
2. Authorize OC-005 build directly under Option 1 / 2 / 3.
3. Adjust scope based on findings in these reports.
4. Re-prioritize ahead of iter453 / iter452.5.2 (P1) sequencing.
5. Defer OC-005 until later in Phase 1A.

No code will be written until the operator selects.
