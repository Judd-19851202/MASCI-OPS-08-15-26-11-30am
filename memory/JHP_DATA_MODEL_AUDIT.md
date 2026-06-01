# OMEGA · JHP_DATA_MODEL_AUDIT.md

**Date:** 2026-06-01
**Trigger:** Operator OC-005 reality check.
**Method:** Schema introspection (Pydantic models · doc-comments · live `db.list_collection_names()` + `find_one()`).

---

## 1 · Operative JHP storage model

### Collection: `db.job_hazard_files`

**Schema source of truth:** `backend/job_hazard_files.py:12-26` (doc-comment) + `upload_file()` at `:230-261`.

| Field | Type | Required | Source/derivation | Indexed? |
|---|---|---|---|---|
| `id` | `str (uuid4)` | ✅ | `uuid.uuid4()` server-side (`:190`) | No explicit index found |
| `scope` | `str` ∈ `{"jha", "trench_box"}` | ✅ (defaults `"jha"`) | Caller-supplied at upload (`:172, :179`) | No |
| `project_number` | `str` | ✅ | Form field, validated non-empty (`:176-178`) | No |
| `filename` | `str` (safe-sanitized) | ✅ | `_safe_filename()` strips path components (`:78-93`) | No |
| `content_type` | `str` (MIME) | ✅ | `file.content_type` from multipart, falls back to `application/octet-stream` (`:225-228`) | No |
| `file_size` | `int` (bytes) | ✅ | Computed during stream (`:204`) — max 250 MB (`:53`) | No |
| `storage` | `str` ∈ `{"inline", "disk"}` | ✅ | ≤ 8 MB → `"inline"`; > 8 MB → `"disk"` (`:50, :244-261`) | No |
| `file_data` | `str` (base64 data URL) | conditional (storage="inline" only) | `data:<mime>;base64,<…>` (`:250`) | No |
| `file_path` | `str` (relative to `STORAGE_ROOT`) | conditional (storage="disk" only) | Relative to `/app/backend/storage/jha_plans/` (`:258, :261`) | No |
| `notes` | `str` | optional (defaults `""`) | Caller-supplied free text (`:237`) | No |
| `uploaded_by` | `str` | optional (defaults `""`) | Caller-supplied free text (`:238`) | No |
| `uploaded_at` | `str` (ISO-UTC) | ✅ | `datetime.now(timezone.utc).isoformat()` (`:239, :74-75`) | No |

### Field NOT present (operator-relevant absences)

| Missing field | Implication |
|---|---|
| `version` / `revision_number` / `supersedes` | No formal versioning — repeat uploads for the same project accumulate as separate rows. There is no "latest pointer" enforced by the schema. |
| `effective_date` / `expiration_date` | No lifecycle window. A JHP cannot expire; an acknowledgement cannot be tied to "the JHP in force on date X". |
| `safety_author_id` / `safety_author_email` | `uploaded_by` is free-text. There is no link to the FL/Safety user record, no cryptographic identity binding, no audit row. |
| `acknowledgement_required` | No flag distinguishes "requires crew ack" from "informational reference". |
| `target_crew_ids[]` / `target_employee_ids[]` / `target_roles[]` | No targeting model — every JHP is implicitly "for everyone on that project". |
| `language` / `translations[]` | No bilingual companion model — a Spanish PDF would be a sibling row indistinguishable from the English original. |
| `status` (`draft` / `published` / `withdrawn`) | No lifecycle states. Every uploaded row is immediately public-downloadable. |
| `replaces_file_id` / `replaced_by_file_id` | No supersedes chain. Audit of "which version was current when employee X acknowledged" is impossible today. |

### Indexes (verified live)

`db.job_hazard_files` carries only the implicit `_id` index. No explicit indexes on `project_number`, `scope`, `uploaded_at` — for OC-005 acknowledgement listing (which must filter by `project_number` + `scope='jha'` + `uploaded_at` desc) a `(scope, project_number, uploaded_at -1)` index is the obvious add. Not built.

### Live row count

```
db.job_hazard_files.count():
  total: 6
  scope="jha":        0
  scope="trench_box": 6
```

All current rows belong to the trench-box piggyback library. **Zero JHP PDFs uploaded into the system today.**

---

## 2 · Legacy storage model (predecessor)

### Collection: `db.job_hazard_plans`

**Schema source:** Pydantic `JobHazardPlan` model at `server.py:2161-2170`.

| Field | Type | Notes |
|---|---|---|
| `id` | `str` | uuid |
| `project_number` | `str` | **Unique by upsert** (`server.py:2276-2280`) — one plan per project max |
| `project_name` | `str` (default `""`) | — |
| `location` | `str` (default `""`) | — |
| `filename` | `str` | — |
| `content_type` | `str` (default `"application/pdf"`) | — |
| `file_size` | `int` (default 0) | — |
| `notes` | `Optional[str]` | — |
| `uploaded_by` | `Optional[str]` | Free text |
| `uploaded_at` | `str` (ISO) | — |
| `file_data` | (in collection, excluded from response_model) | base64 data URL · max 25 MB (`server.py:2251-2255`) |

### Live row count

```
db.job_hazard_plans.count(): 0
```

**Effectively retired.** Routes still mounted (`server.py:2200-2295`) — admin can technically still POST to `/api/job-hazard-plans`, which would upsert into this collection. But the active admin UI (`JhaPlansAdmin.jsx`) uses the multi-file path exclusively.

---

## 3 · Vestigial form-submission model

### Collection: `db.jhas`

**Schema source:** Pydantic `JhaCreate` model at `routes/safety.py:159-178`, `Jha` at `:181-184`.

| Field | Type | Notes |
|---|---|---|
| `id` | `str` (uuid) | — |
| `doc_id` | `str` (`"JHA-YYYY-NNNNN"` pattern) | Generated by `doc_ids.ensure_doc_id` |
| `created_at` | `str` (ISO) | — |
| `project_name` | `str` | required |
| `project_number` | `Optional[str]` (default `""`) | **OPTIONAL** — orphan-corner pattern |
| `location` | `str` | required |
| `jha_date` | `str` | required |
| `job_title` | `str` | required |
| `job_description` | `Optional[str]` | — |
| `crew_lead` | `str` | required |
| `crew_members` | `Optional[str]` (free text, not relational) | — |
| `ppe_required` | `Dict[str, Any]` | Free shape |
| `permits_required` | `Dict[str, Any]` | Free shape |
| `tools_equipment` | `Optional[str]` (free text) | — |
| `task_steps` | `List[Dict[str, Any]]` (free shape) | — |
| `stop_work_acknowledged` | `Optional[str]` (default `"Yes"`) | **Single string. Not crew-level. Not auditable.** |
| `nearest_hospital` | `Optional[str]` | — |
| `emergency_contact` | `Optional[str]` | — |
| `crew_signoffs` | `List[Dict[str, Any]]` (free shape) | Signoffs on the FORM, NOT acks of an uploaded PDF |
| `foreman_signature` | `Optional[str]` (base64 signature image) | — |
| `photos` | `List[str]` (base64 / paths) | — |
| `model_config` | `extra="allow"` | Form is loose by design |

### Live row count

```
db.jhas.count(): 1
```

Almost certainly a test seed row. Not a workflow in operative use.

---

## 4 · Disk storage layout

`backend/job_hazard_files.py:45-46`: `STORAGE_ROOT = Path("/app/backend/storage/jha_plans").resolve()`

Live directory listing:
```
/app/backend/storage/jha_plans/
  _TEST_JHA_25-99/
  _TEST_JHA_25-MULTI/
  _TEST_JHA_DISK/
  _TEST_JHA_TYPES/
  general/
```

* Per-project sub-directories (named by `project_number`, file-system-safe).
* `general/` holds the trench-box "general" scope files.
* The `_TEST_*` directories are pytest fixture artifacts (test runs touch real disk).

---

## 5 · Cross-reference: existing identity-binding primitives that COULD power acknowledgements

These exist in the platform today and are not yet wired to JHP. Listed so OC-005 can reuse them rather than reinvent.

| Primitive | File:line | Reusability for OC-005 |
|---|---|---|
| `field_leadership_users` collection (24 supervisors, all with email) | `field_leadership_users.py:24-30` | Identifies supervisors who can attest on behalf of their crew |
| `X-FL-Token` header + `is_valid_fl_user_token_async` | `field_leadership_users.py:248-273` | Already in the request pipeline (iter452.5.1); could carry supervisor identity into a JHP-ack POST |
| `employees` collection (261 rows, all with email) | `db.employees` schema | Identifies individual crew members for per-employee ack |
| `workflow_state_events` collection (immutable audit trail) | `lib/workflow_state_events.py` | Could store `workflow="jhp"` `to_state="ACKNOWLEDGED"` rows — Phase 1B aggregator already mines this collection |
| `field_submitter_bindings` collection (FSI) | `lib/field_submitter_identity.py:34` | Pattern for "this person did this thing on this record at this time" — directly transferable to JHP acks |
| `lib/idempotency.py` (Idempotency-Key middleware) | `lib/idempotency.py` | Would prevent double-ack on flaky mobile networks |
| `BilingualConsent.jsx` + `@/lib/i18n` | `frontend/src/components/BilingualConsent.jsx` | Pre-built bilingual consent flow — ready for JHP ack copy |
| `SignaturePad.jsx` | `frontend/src/components/SignaturePad.jsx` | Already used by JHA form-submission system for `foreman_signature` |
| `pm_routing.py::recipients_for_record_async` | `pm_routing.py:?` | Could fan out non-ack alerts to PMs |
| `routes/field_revision.py::register_field_revision_routes` (iter452.5) | `routes/field_revision.py` | Pattern for signed-token public-gate flows; transferable to "supervisor receives email, clicks link, attests for crew" |

---

## 6 · Data-model gaps relative to OC-005 intent

Anchored on the operator's prior OC-005 description (JHA Acknowledgement Ledger), as adjusted to the JHP correction (PDF acknowledgement):

| Gap | Severity | Closing model (illustrative, not authorized) |
|---|---|---|
| No JHP version field | 🔴 RED — cannot pin acks to "which file was current" | Add `version_number: int` (auto-increment per project_number) + `is_current: bool` |
| No `safety_author_id` (FL/Safety user) on upload | 🟡 YELLOW — uploads orphaned from identity | Set `safety_author_id` from `X-FL-Token` at upload time (mirror iter452.5.1 P0) |
| No `acknowledgements` collection | 🔴 RED — no record of who has read what | New `jhp_acknowledgements` collection: `{id, jhp_file_id, project_number, employee_id, employee_name, employee_email, role_at_ack, signature_image, ip, user_agent, acknowledged_at, locale, consent_text_version}` |
| No "required ack" flag per PDF | 🟡 YELLOW — cannot differentiate mandatory from informational | Add `acknowledgement_required: bool` on `job_hazard_files` |
| No crew-roster targeting | 🟡 YELLOW — Safety cannot say "this crew must ack this JHP" | Use existing `employees.project_numbers` or introduce `jhp_assignments` collection |
| No expiration / re-ack policy | 🟡 YELLOW — when a JHP is replaced, old acks remain "valid" silently | `replaced_at` field + nightly job recomputes `is_current` |
| No status lifecycle (`draft`/`published`/`withdrawn`) | 🟡 YELLOW — every upload is immediately live | `status` field defaulting to `published` (back-compat) |
| No bilingual companion model | 🟡 YELLOW — Spanish copy would be an indistinguishable sibling row | `language: str` field + `translation_of: file_id` link |
| No `workflow_state_events` integration | 🟡 YELLOW — ack chain invisible to Phase 1B | Emit `workflow="jhp"` `to_state="ACKNOWLEDGED"` row on each ack |
| No indexes for ack reporting | 🟢 GREEN — easy add | `(scope, project_number, uploaded_at -1)` on `job_hazard_files` + `(project_number, employee_id)` unique on `jhp_acknowledgements` |
| Naming inconsistency `JHA` ↔ `JHP` in code identifiers | 🟢 GREEN cosmetic — does not affect functionality | Either alias new endpoints `/api/jhp/*` (keep `/api/job-hazard-files/*` for back-compat) OR a future rename batch |

---

## 7 · Data integrity findings

* **No referential integrity** between `job_hazard_files.project_number` and `jobs_master.project_number`. A JHP can be uploaded for a project_number that does not exist in `jobs_master` and the system will accept it without warning.
* **No FK from `uploaded_by` to any user collection** — purely a display string.
* **Soft delete is not modeled** — `DELETE /api/job-hazard-files/{id}` hard-deletes the row (`server.py:2385-2390`). When acks land on the row, this becomes an audit-integrity risk (acks of a deleted PDF would dangle).
* **No tombstone** — once deleted, a JHP cannot be recovered (no `archived_at`, no `restore` endpoint).

---

## 8 · Storage-engineering posture

The multi-file model carries operationally sound choices that are worth preserving in any OC-005 extension:

* ≤ 8 MB → inline base64 in Mongo for fast list/download (`backend/job_hazard_files.py:50, :244-256`).
* > 8 MB → streamed to disk with FileResponse on download (`server.py:2374-2380`).
* 1 MB chunk reads during upload (`backend/job_hazard_files.py:198-216`).
* Hard 250 MB cap per file (`:53, :205-215`) — enough for FDOT plan sets per doc-comment.
* Filename sanitization at `:78-93` (path-component stripping, charset whitelist).
* `X-Content-Type-Options: nosniff` on download responses (`server.py:2371`).
* No magic-byte validation on the multi-file path (doc-comment `:55-57` is explicit: "extension is informational only"). Legacy single-file path validates PDF magic bytes (`server.py:2250`). OC-005 should pick a posture.

---

## Discipline check

| Check | Status |
|---|---|
| Zero code changed | ✅ |
| Every schema field cited to source | ✅ |
| Operative collection identified · vestigial system disambiguated | ✅ |
| Reusable platform primitives enumerated for OC-005 | ✅ |
| Severity-graded gap inventory | ✅ |
