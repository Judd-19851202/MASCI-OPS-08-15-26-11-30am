# OMEGA · JHP_CODE_REALITY_AUDIT.md

**Date:** 2026-06-01
**Trigger:** Operator correction — "MASCI does NOT use JHA as the workflow name. MASCI uses JHP — Job Hazard Plan. JHPs are built per job by the Safety department, then uploaded/placed in the JHP section as PDFs."
**Method:** Static code trace + live data query. No code changed.

---

## Headline — the codebase carries TWO DIFFERENT "JHA" systems, neither of which is canonically named JHP

The platform's internal vocabulary is **"JHA"** (Job Hazard Analysis) — visible in routes, collections, frontend file names, and admin pages. The operator-authoritative MASCI vocabulary is **"JHP"** (Job Hazard Plan). The two systems present in code:

| System | Identifier in code | What it does | Matches operator's JHP description? |
|---|---|---|---|
| **A · PDF-library system** | `db.job_hazard_files` + `db.job_hazard_plans` + `/api/job-hazard-files/*` + `/api/job-hazard-plans/*` + `pages/JhaPlansHub.jsx` + `pages/JhaPlansAdmin.jsx` | Admin uploads PDFs per project_number; crews browse + download | ✅ YES — this IS the JHP system |
| **B · Form-submission system** | `db.jhas` + `routes/safety.py::JhaCreate` + `POST /api/jhas` | Public-gate free-form JHA form (crew, task_steps, signoffs) | ❌ NO — this is a separate vestigial workflow, not the JHP PDF library |

System B is **orphaned legacy code that does not match how MASCI actually uses the platform.** Live data: only **1** row in `db.jhas` collection (likely test data); MASCI Safety does not author JHAs through this form per the operator correction. System A is the operative one.

---

## 1 · Where is the JHP section in frontend code?

### User-facing pages
| File | Route | Purpose | Evidence |
|---|---|---|---|
| `frontend/src/pages/JhaPlansHub.jsx` | `/jha` · also `/safety/jha` → redirect | **Public** crew-facing JHP library. Lists every project, expands to show every uploaded PDF, click to download | `App.js:344` mounts route · `JhaPlansHub.jsx:39` fetches `/job-hazard-files/public/grouped` |
| `frontend/src/pages/JhaPlansAdmin.jsx` | `/admin/jha-plans` · also `/pm/jha-plans` | **Admin** upload/delete UI for the multi-file library | `App.js:451, :533` · doc-comment `JhaPlansAdmin.jsx:31-45` enumerates the backend endpoints it uses |
| `frontend/src/pages/JhaPlansPoster.jsx` | `/admin/jha-plans/poster` | QR-code site-poster generator pointing at the public JHP page | `App.js:458` |
| `frontend/src/components/JhaPlansPosterCard.jsx` | — | Reusable card in poster section | — |

### Linkage from the Safety section
* `frontend/src/pages/SafetySection.jsx:142-148` — tile in the Safety module: `to="/jha"`, `title={t("Job Hazard Plans")}`, `testId="safety-tile-jha"`.

### Legacy redirects
* `/jha/submit` → `/jha` (App.js:345)
* `/jha/new` → `/jha` (App.js:346)
* `/safety/jha` → `/jha` (App.js:377)
* `/admin/jha` → `/admin/jha-plans` (App.js:452)

These redirects confirm a **prior** "submit/new JHA" UI existed and was deprecated in favor of the PDF-library model — supports the operator's correction that JHPs are admin-uploaded PDFs, not crew-authored forms.

---

## 2 · What backend routes serve JHP PDFs?

### Active route surface (PDF library — System A)

| Method | Path | Auth | Source | Purpose |
|---|---|---|---|---|
| GET | `/api/job-hazard-files` | `Depends(require_admin)` (`server.py:2304`) | `server.py:2303-2307` | Admin grouped listing |
| GET | `/api/job-hazard-files/public/grouped` | **PUBLIC** (no `Depends`) (`server.py:2311`) | `server.py:2310-2318` | Public crew-facing grouped listing |
| GET | `/api/job-hazard-files/by-project/{project_number}` | **PUBLIC** (`server.py:2322`) | `server.py:2321-2325` | Public per-project listing |
| POST | `/api/job-hazard-files` | `Depends(require_admin)` (`server.py:2334`) | `server.py:2328-2344` | Admin multipart upload |
| GET | `/api/job-hazard-files/{file_id}/download` | **PUBLIC** (`server.py:2348`) | `server.py:2347-2381` | Public stream/download |
| DELETE | `/api/job-hazard-files/{file_id}` | `Depends(require_admin)` (`server.py:2385`) | `server.py:2384-2390` | Admin delete |

### Legacy single-file route surface (`job_hazard_plans` — predecessor of `job_hazard_files`)

| Method | Path | Auth | Source | Purpose |
|---|---|---|---|---|
| GET | `/api/job-hazard-plans` | PUBLIC | `server.py:2200-2211` | List (excludes base64 payload) |
| GET | `/api/job-hazard-plans/{project_number}/file` | PUBLIC | `server.py:2214-2239` | Stream single PDF |
| POST | `/api/job-hazard-plans` | `Depends(require_admin)` | `server.py:2242-2284` | Admin upload (idempotent on project_number — upsert replaces) |
| DELETE | `/api/job-hazard-plans/{project_number}` | `Depends(require_admin)` | `server.py:2287-2295` | Admin delete |

This legacy collection (`db.job_hazard_plans`) holds ONE plan per project_number; it was superseded by the multi-file `db.job_hazard_files` model. **Live data: 0 rows** in `db.job_hazard_plans` (verified).

### Form-submission route surface (System B — vestigial, NOT the JHP PDF library)

| Method | Path | Auth | Source | Purpose |
|---|---|---|---|---|
| POST | `/api/jhas` | `Depends(rate_limit_public_post)` — **public-gate** | `routes/safety.py:544-545` | Free-form JHA submission |
| GET | `/api/jhas` | `Depends(_read_gate)` (Safety/Admin/PM) | `routes/safety.py:591-592` | List |
| GET | `/api/jhas/{jha_id}` | `Depends(_read_gate)` | `routes/safety.py:615-616` | Read one |
| DELETE | `/api/jhas/{jha_id}` | `Depends(require_admin)` | `routes/safety.py:625-626` | Delete |

---

## 3 · What collection stores JHP metadata?

Live data verification (`mongo` query):

```
collections present (jha-related):
  job_hazard_plans     (legacy single-file)     — 0 documents
  job_hazard_files     (current multi-file)     — 6 documents
  jhas                 (form submissions)       — 1 document (test data)
```

### `db.job_hazard_files` — the operative collection

Schema doc-comment from `backend/job_hazard_files.py:12-26`:

```
id              str (uuid)
scope           "jha" | "trench_box"   (defaults to "jha")
project_number  str (scope=jha)  OR trench_box_id (scope=trench_box)
                 OR "general" for shared educational docs
filename        str
content_type    str
file_size       int
storage         "inline" | "disk"
file_data       base64 data URL (inline only)
file_path       str (disk only, rel to STORAGE_ROOT)
notes           str
uploaded_by     str
uploaded_at     iso-utc
```

### CRITICAL data finding

Of the 6 rows currently in `db.job_hazard_files`:

```
scope="jha":        0  documents  (zero JHP PDFs uploaded today)
scope="trench_box": 6  documents  (all 6 are tabulated-data for the trench-box library
                                   piggybacking on the same collection)
```

Sample row (live):
```json
{
  "id": "50a72853-34c4-467c-a837-28d2e70c329a",
  "scope": "trench_box",
  "project_number": "general",
  "filename": "What_Is_Tabulated_Data_UnitedRentals.pdf",
  "content_type": "application/pdf",
  "file_size": 3529305,
  "notes": "United Rentals training presentation…",
  "uploaded_by": "MASCI Admin (auto-seed)",
  "uploaded_at": "2026-04-30T20:25:08.824289+00:00"
}
```

**Implication:** the JHP PDF library is wired end-to-end (frontend + backend + storage) but **has not yet had a single JHP uploaded into it.** The 6 rows present are trench-box educational PDFs sharing the same collection via the `scope` field.

### `db.jhas` — the vestigial form-submission collection

Schema (Pydantic `JhaCreate`, `safety.py:159-178`): `project_name`, `project_number`, `location`, `jha_date`, `job_title`, `job_description`, `crew_lead`, `crew_members`, `ppe_required`, `permits_required`, `tools_equipment`, `task_steps[]`, `stop_work_acknowledged`, `nearest_hospital`, `emergency_contact`, `crew_signoffs[]`, `foreman_signature`, `photos[]`.

**Live data: 1 row** (probable test seed). Not the operative JHP system.

---

## 4 · Are JHPs tied to job/project number?

✅ **YES, by primary key.**

* `job_hazard_files`: `project_number` is the grouping key. Public endpoint groups by it (`server.py:2310-2318`). The frontend hub lists every project from `JOB_LIBRARY` and expands to show files (`JhaPlansHub.jsx:52-58`).
* `job_hazard_plans`: `project_number` is the **unique** key (upsert on `project_number`, `server.py:2276-2280`). One plan per project max in the legacy model.
* Upload endpoint requires `project_number` and rejects with HTTP 400 if empty (`job_hazard_files.py:176-178`).

---

## 5 · Who uploads JHP PDFs?

Per route guards:

* `POST /api/job-hazard-files`: `Depends(require_admin)` — admin-only (and `require_admin` accepts Admin + PM by platform-wide policy, verified at `routes/safety.py:285-289` for the Safety module).
* `POST /api/job-hazard-plans`: `Depends(require_admin)` (legacy path).
* `DELETE` paths: same admin guard.
* Frontend `JhaPlansAdmin.jsx` is mounted under `/admin/jha-plans` and `/pm/jha-plans` (both admin-protected routes per `App.js:451, :533` using the `AP` admin wrapper).

**Reality:** the operator's statement — "JHPs are built per job by the Safety department, then uploaded/placed in the JHP section as PDFs" — maps EXACTLY to the `POST /api/job-hazard-files` flow exposed through `JhaPlansAdmin.jsx`. The persisted `uploaded_by` is a free-text string supplied by the uploader (it is NOT cryptographically tied to the Safety user; see GAP report for implications).

---

## 6 · Are JHP PDFs versioned?

❌ **NO formal versioning.**

* `job_hazard_files` schema (`backend/job_hazard_files.py:12-26`): no `version`, no `revision`, no `supersedes`, no `replaced_by` fields.
* `job_hazard_files.py:upload_file()` always creates a NEW row with a fresh `uuid` — multiple uploads for the same `project_number` accumulate as separate file rows. The "version" model is essentially: "each upload is its own file row; the latest by `uploaded_at` wins by convention." There is no `is_current` flag, no version pointer, no archive flag.
* `job_hazard_plans` (legacy): does the opposite — upsert by `project_number` REPLACES the file (`server.py:2276-2280`). Prior content is lost. No history kept.
* Acknowledgements (if they existed) could not currently be pinned to a specific PDF version.

---

## 7 · Is there any existing acknowledgement tracking?

❌ **NO.** Verified across the codebase + database:

* Collection sweep returned `[backup_health, safety_equipment_trainings, safety_training_records, training_guides, training_hits, training_videos]` as the only acknowledgement-adjacent collections. None are JHP-bound.
* Explicit existence checks (live mongo query) returned `False` for: `jhp_acknowledgements`, `jha_acknowledgements`, `job_hazard_acknowledgements`, `jhp_signoffs`, `jha_signoffs`, `jhp_attestations`.
* `job_hazard_files.py` (whole module, 325 LOC) does not import, reference, or write to any acknowledgement collection.
* `JhaPlansHub.jsx` (whole component, 245 LOC) renders only file-list UI — no acknowledgement controls, no "I have read this" affordance, no signature pad. The only download CTA is a plain `<a href={fileHref(f.id)}>` (`:208-217`).
* The vestigial `db.jhas` form-submission system has `crew_signoffs[]` and `foreman_signature` fields (`safety.py:176-177`) — these are signoffs on a crew-authored JHA FORM, NOT acknowledgements of an uploaded JHP PDF. They cannot satisfy the operator's OC-005 intent.

The only "acknowledgement-shaped" field anywhere in the JHA code surface is `stop_work_acknowledged: Optional[str] = "Yes"` (`safety.py:173`) — a single string on the form-submission JHA. Not crew-level, not per-PDF, not auditable.

---

## 8 · Is there any employee/crew acknowledgement requirement?

❌ **NO requirement enforced in code.**

* No middleware checks an "acknowledged_at" before serving a JHP PDF (`server.py:2347-2381` streams unconditionally).
* No frontend gate prevents progressing to other workflows (Daily Reports, Incidents, JHAs) before acknowledging a JHP.
* No notification, reminder, or expiration logic targets crew-by-crew JHP read receipts.
* `training_hits` (the closest existing pattern, 88 rows) tracks **HelpTip** views — unrelated to JHPs (`grep -rn "training_hits" /app/backend/` shows only the help-tip system).

---

## 9 · Is JHP currently public-gate, authenticated, or admin-upload-only?

| Action | Gate |
|---|---|
| **Read/list JHPs grouped** | PUBLIC (`/api/job-hazard-files/public/grouped` — no `Depends`, `server.py:2310-2318`) |
| **Read/list per project** | PUBLIC (`/api/job-hazard-files/by-project/{pn}`, `server.py:2321-2325`) |
| **Download a JHP** | PUBLIC (`/api/job-hazard-files/{file_id}/download`, `server.py:2347-2381`) |
| **Upload a JHP** | Admin/PM (`Depends(require_admin)`, `server.py:2334`) |
| **Delete a JHP** | Admin/PM (`Depends(require_admin)`, `server.py:2385`) |
| **Admin grouped list** | Admin/PM (`/api/job-hazard-files`, `server.py:2304`) |

**Hybrid model:** public READ, admin WRITE.

---

## 10 · What exact workflow exists today versus what is missing?

### What exists (verified live)

```
SAFETY DEPT (admin role)
   │
   │  POST /api/job-hazard-files   (multipart upload, per project_number)
   ▼
   db.job_hazard_files
   (storage: ≤8 MB inline base64 in Mongo · >8 MB on /app/backend/storage/jha_plans/)
   │
   │  /api/job-hazard-files/public/grouped
   ▼
CREW MEMBER (anonymous public)
   │
   │  Visits /jha
   │  Browses by project
   │  Clicks Download
   ▼
   GET /api/job-hazard-files/{file_id}/download
   (no token, no identity, no audit row written)
```

### What is missing (relative to OC-005 intent)

| Missing capability | Evidence of absence |
|---|---|
| Per-employee acknowledgement record (who read what JHP, when) | No collection · no endpoint · no UI control |
| Acknowledgement pinned to a specific JHP **version** | No version field on `job_hazard_files` |
| Required-acknowledgement rule (e.g., "before clocking in on this project") | No middleware · no gating |
| Expiration / re-acknowledgement after PDF replacement | No "supersedes" link · no expiration policy |
| PM/Safety visibility into who has NOT acknowledged | No reporting endpoint |
| Audit chain when an acknowledgement happens | No `workflow_state_events` rows for JHP |
| Crew identity binding (which crew member is reading?) | Download endpoint is anonymous public |
| Project-level enrollment ("crew X is assigned to project Y, must ack JHP Z") | No relation between crew membership and JHP |
| Bilingual / accessibility acknowledgement copy (English + Spanish) | The platform has bilingual capability (`@/lib/i18n`, `BilingualConsent.jsx`) but it is not wired to JHP |
| Print/poster handoff so non-mobile crews can sign on paper and an admin records it later | `JhaPlansPoster.jsx` exists but only generates the QR code, not the paper acknowledgement |

### Naming/terminology gap (orthogonal to OC-005 but operator-visible)

* Backend collection is `job_hazard_files`; route is `/job-hazard-files`; frontend page name is `JhaPlansHub`; tile label is `"Job Hazard Plans"`. Internal vocabulary cluster: `JHA`, `Jha`, `jha`.
* Operator-authoritative vocabulary: **`JHP`**.
* User-visible label `"Job Hazard Plans"` (`SafetySection.jsx:144`) is **already correct** at the UI surface.
* Code-level identifiers (`JhaPlansHub`, `db.jhas`, `/api/jhas`, `_TEST_JHA_*` storage dirs) carry the legacy `JHA` token. Operator may or may not want a rename batch — that is a separate authorization conversation (see GAP report).

---

## Discipline check

| Check | Status |
|---|---|
| Zero code changed | ✅ |
| Every claim citation-backed (`file:line` or live data) | ✅ |
| Two distinct "JHA" systems disambiguated | ✅ |
| Operator's correction (JHP = admin-uploaded PDFs) verified against live data + routes | ✅ |
| Acknowledgement gap quantified | ✅ (zero collection, zero route, zero UI control) |
