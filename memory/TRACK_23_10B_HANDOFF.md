# TRACK 23.10-B · COMPETENT PERSON CERTIFICATION FOUNDATION
## Execution Handoff for a Fresh Session · NO CODE CHANGES IN THIS FILE

> **Language rule for the executing agent**: respond in English only.
>
> **Prime directive**: Execute the approved design as written below and in
> `/app/memory/TRACK_23_10_TRENCH_PROJECT_JOIN_AUDIT.md` (Sections 10.1 – 10.9
> and Section 13 · sub-track 23.10-B). **Do not redesign. Do not reduce scope.
> Do not create temporary pickers. Do not create parallel registries. Do not
> fake green.** If a requirement is ambiguous, ask the user before deviating —
> never invent a lighter version.

---

## 0 · The single most important framing (READ FIRST)

**23.10-B is NOT a "Competent Person feature".** It is the foundation for a
**Professional Qualifications Engine** for the entire platform.

* **Competent Person** is the *first* mandatory qualification type shipped by
  this track — it is the pilot, not the product.
* The data model, service layer, API surface, ODS facts, permissions model,
  and UI must all be built so that adding the next qualification type is a
  **configuration change** (a new enum value + optional field metadata), not a
  redesign, not a new collection, not a new endpoint, not a new picker
  component.
* Every architectural decision in 23.10-B must pass this test:
  *"If I add OSHA 30 tomorrow, do I need to write any new plumbing?"*
  If yes → the design is wrong.

### 0.1 Qualification types the engine MUST accommodate on day one
(shipped in the enum, even if only Competent Person is wired to consumers in
this track)

```
COMPETENT_PERSON           ← the pilot in 23.10-B (fully wired end-to-end)
OSHA_10
OSHA_30
FIRST_AID_CPR
SIGNAL_PERSON
CONFINED_SPACE
RIGGING
CRANE_OPERATOR
EQUIPMENT_OPERATOR
TRAFFIC_CONTROL_FLAGGER
MSHA
HAZWOPER
DOT_MEDICAL
CDL_ENDORSEMENT          ← may carry a sub-code (A, B, H, N, P, S, T, X)
MANUFACTURER_CERT        ← carries manufacturer + product_model
COMPANY_SPECIFIC         ← carries company-specific program name
```

**Rule**: every qualification type shares the same base fields (issuer, dates,
verification lifecycle, attachments, audit history). Type-specific extras
(sub-code, product model, jurisdiction) live in a flexible `type_metadata`
blob on the same record — NOT in a new collection.

---

## 1 · Immutable architectural rules (violate any and the track is failed)

1. **`safety_training_records` is the single source of truth** for every
   qualification, including Competent Person. It is extended additively; it is
   never duplicated. There is no `competent_persons` collection. There is no
   `qualifications` collection. There is no `certifications_registry`
   collection. There is no `employee_certifications_view` materialised copy.
2. **Employee Lifecycle displays qualification status; it does not own it.**
   The Employee Lifecycle Certifications tab is a *read-through admin surface*
   that writes back to `safety_training_records`. It never caches, never
   snapshots, never mirrors.
3. **Trench Safety consumes the Competent Person registry; it does not own
   it.** No trench route, no trench collection, no trench UI creates,
   modifies, suspends, revokes, or renews a Competent Person cert. Read-only.
4. **Daily Report V3 consumes the Competent Person registry; it does not own
   it.** The DR V3 excavation picker (shipped in 23.10-E, NOT here) hits the
   registry endpoint. The DR never stores a cert; it stores a *snapshot* of
   the cert-at-report-time (id + status + validity flag).
5. **Scheduling consumes qualification readiness; it does not grant, revoke,
   or override qualifications.** Scheduling reads a boolean; it never writes.
6. **Only ACTIVE + non-expired qualifications are selectable as active.**
   Expired, suspended, revoked, and pending (draft, unverified) qualifications
   are **excluded server-side** from the "active" registry query. They are
   still visible in the admin view for audit and renewal, but never returned
   by `/api/employees/qualifications?active=true`.
7. **Historical records preserve the person + certification snapshot at the
   moment of selection.** When a DR / trench inspection / scheduling row
   references a qualification, it stores `qualification_id +
   qualification_type + verification_status_at_selection +
   expires_at_at_selection + person_name_snapshot + person_trade_snapshot +
   crew_snapshot`. Later cert changes NEVER rewrite historical rows.
8. **The registry is a QUERY, not a stored list.** No cron rebuilds it. No job
   materialises it. It is computed at read time from `safety_training_records`.
9. **HR / Training admin is the only writer.** Field roles, supervisor, PM,
   Safety officer, Trench Safety module: read-only. No self-certification.
   Every write logs actor + before/after into
   `verification_status_history[]` and `db.hr_audit`.
10. **B-04 style safety invariant for cert lifecycle**: a qualification is
    "active for selection" ONLY when
    `verification_status="active" AND today <= expiration_date AND
     suspended_at IS NULL AND revoked_at IS NULL`.
    "Completed training" ≠ "active qualification". Do not weaken this rule at
    the aggregator, endpoint, or UI layer.

---

## 2 · Data model (additive extension to `safety_training_records`)

Existing fields stay untouched. Add these fields (all optional at the schema
level, but *required* when `certification_type` is in the qualification-engine
enum from §0.1):

```
qualification_type            enum (from §0.1) · replaces free-text certification_type over time
qualification_sub_code        str (e.g. CDL "H", MANUFACTURER product model, COMPANY program id)
issuing_organization          str
instructor                    str
instructor_company            str
training_hours                float
training_standard             str  (e.g. "OSHA_29_CFR_1926_651", "custom")
jurisdiction                  str  (state / region / country)
certificate_number            str
attachments                   [file_ref]
digital_certificate           file_ref
wallet_credential             wallet_ref | null   (future — leave the column)
verification_status           enum {"active","expired","suspended","revoked","pending"}
verification_status_history   [{status, at, actor_id, actor_role, reason}]
suspended_at                  datetime | null
revoked_at                    datetime | null
type_metadata                 dict (free-shape, type-specific keys — validated per type)
active                        bool  (DERIVED, never stored on write)
```

**Migration**:
* Additive only. No column dropped. No existing enum value removed.
* Existing 13 rows: default `verification_status = "active"` iff `today <=
  expiration_date` else `"expired"`; leave all other new fields null; write
  one history entry `{status: "active"|"expired", at: now, actor_id:
  "system-migration", reason: "23.10-B additive backfill"}`.
* Legacy free-text `certification_type` remains readable. New writes MUST
  supply `qualification_type` from the enum.
* Migration is idempotent — re-running it is a no-op.

---

## 3 · Service layer (single canonical source)

**File**: `backend/services/certifications/qualification_registry.py`
(rename from `competent_person_registry.py` in the audit doc — the engine is
qualification-generic; Competent Person is one caller.)

Public API (pure functions, DB-injected, no globals):

```
list_active_qualifications(
    db,
    qualification_type: str | None = None,          # None = all types
    warning_days: int = 30,
    employee_ids: list[str] | None = None,
    project_number: str | None = None,              # future: cross-check assignment
) -> list[QualificationRow]

resolve_active_for_employee(
    db,
    employee_id: str,
    qualification_type: str,
) -> QualificationRow | None

get_qualification_snapshot(
    db,
    qualification_id: str,
) -> QualificationSnapshot        # for historical embedding

is_active(qualification_row) -> bool     # derived per Rule 10
```

`QualificationRow` shape (returned to consumers):

```
{
  "qualification_id":            str,
  "qualification_type":          str,
  "qualification_sub_code":      str | null,
  "employee_id":                 str,
  "employee_master_id":          str,
  "employee_name":               str,
  "employee_trade":              str,
  "employee_crew":               str,
  "issuing_organization":        str,
  "certificate_number":          str,
  "issued_at":                   iso,
  "expires_at":                  iso,
  "expires_in_days":             int,
  "warning":                     bool,        # expires_in_days <= warning_days
  "verification_status":         "active",
  "is_active_for_selection":     True,        # always True in this list
  "identity_source":             "employees"  # via Track 23.5 normaliser
}
```

**Rules the service must enforce**:
* Never returns pending / suspended / revoked / expired rows.
* Never invents identity — always joins to `employees` via the Track 23.5
  normaliser. If the employee row is missing → row is dropped from the result
  (and a warning is logged), never fabricated.
* Never writes. Read-only. Deterministic. Idempotent.
* `list_active_qualifications` is O(n) over `safety_training_records` filtered
  by `verification_status="active"` — no full-collection scans, uses the
  existing `certification_type` index (extended to cover `qualification_type`
  as a new index in the migration).

---

## 4 · API surface

### 4.1 Read (consumer-facing, read-only)

```
GET /api/employees/qualifications
    ?type=COMPETENT_PERSON               required (single type per call)
    &active=true                          default true; false is admin-only
    &warning_days=30                      default 30
    &project_number=…                     optional; passed through to service

GET /api/employees/{employee_id}/qualifications
    ?type=COMPETENT_PERSON               required
    &include_history=false               default false

GET /api/employees/qualifications/summary
    ?type=COMPETENT_PERSON               required
    → { active_count, expiring_within_30d_count, expired_count,
        pending_count, suspended_count, revoked_count,
        upcoming_renewals_by_month: [{month, count}] }
```

**Legacy alias** (Track 23.10-B is the qualification engine, but the audit doc
promised `/api/employees/competent-persons`). Provide it as a thin alias that
calls the generic endpoint with `type=COMPETENT_PERSON`. Both endpoints must
return byte-identical shapes. Deprecation note in the OpenAPI, keep working.

### 4.2 Write (HR / Training admin only)

```
POST   /api/hr/qualifications                       create
PATCH  /api/hr/qualifications/{id}                  update fields
POST   /api/hr/qualifications/{id}/suspend          { reason }
POST   /api/hr/qualifications/{id}/revoke           { reason }
POST   /api/hr/qualifications/{id}/reinstate        { reason }
POST   /api/hr/qualifications/{id}/renew            { new_expires_at, new_certificate_number, attachments }
```

**Every write**:
* Requires HR-role OR Training-admin JWT (via existing SSO / multi-portal
  session enrichment).
* Appends to `verification_status_history[]`.
* Writes to `db.hr_audit` with `{action, actor_id, actor_role, before, after,
  at}`.
* Emits `competent_person_certification_fact` (for `qualification_type ==
  COMPETENT_PERSON`); generalise via `qualification_certification_fact` with
  `qualification_type` in payload (see §6).
* Idempotent on `(qualification_id, verification_status, hash(before))`.

### 4.3 What must NOT exist

* No public write endpoint outside `/api/hr/*`.
* No endpoint that returns expired / suspended / revoked / pending rows unless
  explicitly gated by `active=false` AND HR/Training admin JWT.
* No endpoint that lets a DR / trench / scheduling caller create a
  qualification. Consumers are consumers.

---

## 5 · Employee Lifecycle UI (Certifications tab)

**File**: `frontend/src/pages/EmployeeLifecycleQualifications.jsx`
(preferred name; engine is qualification-generic — `EmployeeLifecycleCertifications.jsx`
from the audit doc is acceptable but the tab label and internal state must
speak "Qualifications", not "Competent Person").

* Renders as a tab on the existing Employee Lifecycle Detail page.
* Lists ALL qualifications for the employee (any type), with per-row:
  type · sub-code · issuer · issued · expires · verification_status · actions.
* Actions available only to HR / Training admin: Create · Edit · Suspend ·
  Revoke · Reinstate · Renew · Attach file.
* Type selector when creating a row is the full enum from §0.1.
* Type-specific extra fields (CDL sub-code, manufacturer product, company
  program) render conditionally, all persisted into `type_metadata`.
* NEVER shows a "Manual Competent Person" toggle. NEVER shows a "provisional
  cert" state. NEVER shows a hidden fallback text field.
* Empty state (employee has no qualifications): honest empty state, no
  fabricated placeholders.

**Nothing else in the Employee Lifecycle page changes in 23.10-B.**

---

## 6 · ODS certification facts (idempotent)

Facts emitted into `operational_facts` (existing collection).

| fact_type | Emitted on | Natural key |
|---|---|---|
| `qualification_certification_fact` | Any `safety_training_records` insert/update where `qualification_type` in the engine enum | `("safety_training_records", source_id, "certification")` |
| `qualification_expiration_fact` | Daily scheduler for rows with `expires_at - today ∈ [0, 30]` and `verification_status="active"` | `("safety_training_records", source_id, "expiration_daily", date(today))` |
| `qualification_assignment_fact` | When a consumer (DR V3 / trench inspection / scheduling assignment) references a qualification. Consumer emits it — engine does not. | `(consumer_collection, consumer_source_id, "qualification_assignment", qualification_id)` |

Payload always includes `qualification_type` so consumers filter cleanly
(e.g. `qualification_type=COMPETENT_PERSON` for Trench Safety KPI).

**Idempotency**: existing `is_current=True` upsert pattern per Track 22.4B.

**Backfill**: emit `qualification_certification_fact` for all 13 existing
rows once (part of the migration script). Safe to re-run.

---

## 7 · Consumers (INFORMATIONAL — do NOT touch in 23.10-B)

23.10-B ships ONLY the foundation. The following consumers are wired in later
sub-tracks — the executing agent must NOT edit them in this session, but must
verify the interfaces are compatible:

| Consumer | Sub-track | Reads |
|---|---|---|
| Daily Report V3 excavation section (`CompetentPersonCombo`) | 23.10-E | `GET /api/employees/qualifications?type=COMPETENT_PERSON&active=true` |
| Trench Safety module (all "competent person" free-text fields become the same picker) | 23.10-C follow-up | same endpoint |
| Scheduling readiness | 23.10-E backend | `resolve_active_for_employee(db, employee_id, "COMPETENT_PERSON")` |
| Safety Portal Operational KPI Card (`certifications` block) | 23.10-D | `/api/employees/qualifications/summary?type=COMPETENT_PERSON` |
| PM Portal (future) | later | same summary endpoint |

Anywhere today reads a free-text `competent_person_name`: leave it. Rewriting
historical rows is prohibited by Rule 7.

---

## 8 · Permissions & audit

* HR role OR Training-admin role: full write.
* All other roles: read-only.
* Enforcement lives at the route layer via the existing dependency
  (`require_hr_or_training_admin`); add it if missing.
* Every write appends to `verification_status_history[]` AND writes an entry
  to `db.hr_audit` with `{action, actor_id, actor_role, before, after, at,
  ip?}`.
* The audit collection is read via the existing HR audit surface — no new UI
  for audit in 23.10-B.

---

## 9 · Testing bar (all must pass before certification)

Create `/app/backend/tests/test_track_23_10_b_qualification_registry.py`
(pytest, uses the existing test DB fixture). Test cases — every one is
mandatory:

1. Extending `safety_training_records` with additive fields does not modify
   the existing 13 rows' payloads.
2. Migration is idempotent (run it twice → no diff on second run).
3. `list_active_qualifications` returns only `verification_status="active"
   AND expires_at > today`.
4. Expired row excluded.
5. Suspended row excluded.
6. Revoked row excluded.
7. Pending row excluded.
8. Warning flag correct at boundary (day 30, day 29, day 31).
9. `resolve_active_for_employee` returns the latest active cert when two
   overlap; returns None when the only cert is expired.
10. Employee identity fields on the returned row match the Track 23.5
    normaliser (trade_role_display, crew_display, supervisor_display).
11. Write endpoints require HR/Training admin token — 401/403 otherwise.
12. Every write appends exactly one `verification_status_history` entry.
13. Every write writes exactly one `db.hr_audit` row.
14. Suspend → row disappears from `active=true` immediately.
15. Reinstate → row reappears in `active=true` immediately.
16. Renew → new expiration set, history + fact emitted, `active=true`.
17. Revoke → row never reappears in `active=true`, even after new
    expiration is set (revoked is terminal until explicit reinstate).
18. `qualification_certification_fact` is idempotent under repeated writes.
19. `qualification_expiration_fact` emitted daily for rows in `[0, 30]` days
    to expiry — de-duped per day per row.
20. Legacy free-text `certification_type` rows still return via the legacy
    endpoints; they never pollute the new engine endpoint.
21. Enum from §0.1 is complete: writing each qualification_type value
    succeeds; writing an unknown value returns 400.
22. Type-specific `type_metadata` validated for CDL (requires sub-code),
    MANUFACTURER_CERT (requires product model), COMPANY_SPECIFIC (requires
    program id). Missing metadata returns 400.
23. Consumer read-only invariant: attempting to POST a qualification from a
    non-HR-role JWT (field, supervisor, PM, safety officer, trench module)
    returns 403.
24. Historical snapshot embedding: `get_qualification_snapshot` returns the
    frozen shape including person name + trade + crew + status + expiry —
    with a stable serialisation so a downstream DR row can store it verbatim.
25. All previous 150 regression tests (tracks 23.5 – 23.10-A) pass unchanged.

Additionally: run the full pytest suite (`pytest backend/tests -q`) and paste
the "N passed" line into the finish summary.

---

## 10 · Files created / modified in 23.10-B (definitive list)

**Backend**:
* NEW `backend/services/certifications/__init__.py`
* NEW `backend/services/certifications/qualification_registry.py`
* NEW `backend/services/certifications/qualification_facts.py`
  (fact emitters — one function per fact type)
* NEW `backend/services/certifications/qualification_types.py`
  (enum + type_metadata validators, one place for the full enum from §0.1)
* NEW `backend/routes/qualifications.py`
  (mounts `/api/employees/qualifications*` and `/api/hr/qualifications*`)
* Modify `backend/server.py` to register the new router.
* Modify `backend/models/safety_training_record.py` (or equivalent) to add
  the fields from §2 — **additive only**, no removals.
* NEW `backend/scripts/migrate_track_23_10_b_qualification_engine.py`
  (idempotent additive migration + backfill of 13 existing rows +
  initial fact backfill).
* NEW `backend/tests/test_track_23_10_b_qualification_registry.py`
  (all 25 tests from §9).

**Frontend**:
* NEW `frontend/src/pages/EmployeeLifecycleQualifications.jsx` (tab body).
* Modify the Employee Lifecycle Detail page to mount the new tab
  (single file edit — add `<TabsTrigger>` + `<TabsContent>`).
* NEW `frontend/src/lib/qualificationsApi.js` (thin fetch wrapper — never
  duplicated inside components).

**Docs**:
* This handoff doc.
* Update `/app/memory/PRD.md` on finish with the completed track.
* Update `/app/memory/test_credentials.md` if any new admin credentials are
  seeded.

**Explicitly NOT touched in 23.10-B**:
* Any Trench Safety route, collection, or component.
* Any Daily Report V3 component or route.
* Any Scheduling route or component.
* Any Safety Operational KPI aggregator field or Safety Portal card.
* Any PDF renderer or email template.

If a change is needed in any of those files, STOP and ask the user before
touching them — the design says they belong to sub-tracks 23.10-C / D / E.

---

## 11 · Definition of Done (23.10-B certification bar)

1. All 25 tests in §9 pass.
2. Full pytest suite green (no regressions in 23.5 – 23.10-A).
3. Migration ran idempotently on the preview DB; 13 legacy rows now have
   `verification_status` set correctly; no data loss.
4. `GET /api/employees/qualifications?type=COMPETENT_PERSON&active=true`
   returns a valid list (0 rows is acceptable — the empty state is honest).
5. Employee Lifecycle Qualifications tab renders on the detail page, can
   create · edit · suspend · revoke · reinstate · renew a qualification,
   validated end-to-end by the testing agent OR by a scripted browser proof.
6. HR / Training admin write gate proven by a 403 test from a non-HR JWT.
7. No new collections created. Verified by
   `db.list_collection_names()` diff before / after (delta = 0).
8. No manual registry UI. Verified by grep — no file contains a "Competent
   Person Registry" component that lists people from anywhere other than the
   engine endpoint.
9. No temporary picker component. Verified by grep — the only picker (to be
   built in 23.10-E) does not exist yet and NOTHING in 23.10-B added one.
10. `finish` summary includes: tests passed count · migration ran? · legacy
    row count preserved · new collections created (must be 0) · consumers
    touched (must be 0).

**Explicit anti-goals** (any of these = failed track):
* Creating a `competent_persons` collection.
* Creating a `qualifications` collection.
* Rewriting historical `competent_person_name` free-text values.
* Shipping a picker component in 23.10-B.
* Shipping a Trench / DR / Scheduling change in 23.10-B.
* Any endpoint that returns expired/suspended/revoked rows in the default
  active list.
* Any UI that allows a field user to self-certify.

---

## 12 · Non-negotiables (paraphrase of the user's instruction — verbatim
   intent)

> Execute from the approved design. Do not redesign. Do not reduce scope.
> Do not create temporary pickers. Do not fake green.

If the executing agent finds a genuine blocker in the approved design (e.g.,
a required index is missing, a permission dependency does not exist yet), the
correct action is: **stop and ask the user** — never invent a lighter path,
never insert a mock, never ship a partial surface. Ambiguity is escalated,
not resolved by degradation.

---

## 13 · Suggested execution order inside 23.10-B (single session)

1. Read this doc + `TRACK_23_10_TRENCH_PROJECT_JOIN_AUDIT.md` §10.
2. Confirm plan with user via `ask_human` (list the 25 tests, the file
   inventory, and the anti-goals). Only proceed on approval.
3. Write `qualification_types.py` (enum + validators). Lint.
4. Additive migration script + run it on preview DB. Verify 13 rows updated.
5. `qualification_registry.py` (pure read service). Unit-test in isolation.
6. `qualification_facts.py` emitters. Unit-test idempotency.
7. `routes/qualifications.py` (read + HR write endpoints). Register router.
8. Write the 25-test file. Green all tests.
9. `EmployeeLifecycleQualifications.jsx` + tab mount. One smoke screenshot.
10. Call `testing_agent_v3_fork` with the full test list from §9 and the
    consumer-invariant check from §11.
11. Fix any regressions surfaced. Re-test.
12. Finish with the tenpoint DoD checklist filled in.

---

## 14 · Reference material for the executing agent

* `/app/memory/TRACK_23_10_TRENCH_PROJECT_JOIN_AUDIT.md` (design source of
  truth — §10 is the canonical spec; this doc restates it and expands it into
  the Qualifications Engine.)
* `/app/memory/TRACK_23_10_TRENCH_FIELD_MATRIX.csv`
* `/app/memory/TRACK_23_10_TRENCH_SOURCE_CLASSIFICATION.csv`
* `/app/memory/TRACK_23_5_EMPLOYEE_IDENTITY_AUDIT.md` (the identity normaliser
  used to populate the person snapshot on registry rows).
* `/app/backend/lib/multi_portal_session_enrichment.py` (SSO — HR/Training
  admin identity flows through here).
* `/app/backend/services/operational_kpis/aggregator.py` (the KPI spine that
  a *future* sub-track will consume the certification summary from — do NOT
  edit in 23.10-B).
* Prior track tests in `/app/backend/tests/test_track_23_*` — must all remain
  green.

---

## 15 · Final rule

If any statement in this handoff contradicts the audit doc
`TRACK_23_10_TRENCH_PROJECT_JOIN_AUDIT.md`, the audit doc wins on architecture
and this handoff wins on scope, framing (Qualifications Engine), and the
qualification-type enum in §0.1. Escalate any real contradiction to the user.

**End of handoff.**
