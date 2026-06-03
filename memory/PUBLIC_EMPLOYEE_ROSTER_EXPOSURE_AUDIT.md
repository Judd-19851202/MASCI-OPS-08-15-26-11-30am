# PUBLIC EMPLOYEE ROSTER EXPOSURE — DEPENDENCY AUDIT
## OMEGA Directive · Read-only · No code · No fixes · No deploy

**Date**: 2026-06-03
**Investigator**: Certification agent (read-only mode)
**Endpoint under audit**: `GET /api/employees`
**Status of this report**: Evidence + recommendation only. No code, data, auth, or deploys touched.

---

## EXECUTIVE SUMMARY

1. `/api/employees` is **intentionally public** and serves **6 PUBLIC form pages** + **3 ROLE-GATED pages** + **1 health probe** + indirectly a few shared components.
2. **All UI consumers only display**: `id` + `name` + (some combination of) `employee_id`, `trade`, `role`, `crew`, `email`.
3. **Every other field returned** (`phone`, `cdl_*`, `medical_card_expiration_date`, `status_history`, `approved_company_driver`, `driver_status`, `created_at`, `updated_at`, `is_active`) is **unused by the UI**. It is present in the network payload only.
4. A **narrow precedent already exists** in the codebase: `GET /api/master-lookup/employees` returns only `{id, name, first_name, last_name, employee_id, email, role, display_name, trade}` — the same auth-posture (public), but a tight projection. This is what the safety-forms suite already uses via `EmployeeRosterField.jsx`.
5. **Risk classification: 🟡 MEDIUM** — designed public, no auth bypass, no write capability, but field projection is overbroad relative to the use case. Mechanical fix available with low blast radius.

---

# PHASE 1 — BACKEND ROUTE EVIDENCE

## 1.1 · Route file / line numbers

| Item | Value |
|---|---|
| File | `/app/backend/server.py` |
| Route registration line | **3307** (`@api_router.get("/employees")`) |
| Function definition span | **3308–3316** |
| Header comment | 3303–3306 |
| Docstring | 3309 |

## 1.2 · Verbatim source (lines 3303-3316)

```python
# ---------------------------------------------------------------------------
# Employees / crew roster — used by Daily Report's "MASCI Crews on Site"
# section and any other employee dropdown across the platform.
# ---------------------------------------------------------------------------
@api_router.get("/employees")
async def list_employees():
    """Public — returns the full MASCI crew roster (sorted by name)."""
    await _purge_expired("employees")
    cursor = db.employees.find(
        {"$and": [ACTIVE_FILTER, {"is_active": {"$ne": False}}]},
        {"_id": 0},
    ).sort("name", 1)
    docs = await cursor.to_list(2000)
    return {"items": docs, "count": len(docs)}
```

## 1.3 · Current projection

`{"_id": 0}` — **excludes only Mongo `_id`. No allow-list. Every other field on the document is returned.**

## 1.4 · Current filter

`{"$and": [ACTIVE_FILTER, {"is_active": {"$ne": False}}]}` where
`ACTIVE_FILTER = {"deleted_at": {"$in": [None, ""]}}` (server.py:1235).

Effect: non-soft-deleted + `is_active != False`. **Pagination cap: 2000** (`to_list(2000)`).

## 1.5 · Current returned fields (per live response sample · 247 records observed)

```
id · name · employee_id · trade · role · crew · email · phone
is_active · created_at · updated_at
approved_company_driver
cdl_holder · cdl_expiration_date · cdl_state · cdl_endorsements · cdl_restrictions
driver_status · medical_card_expiration_date
status_history (array of {ts, actor, action, source})
```

## 1.6 · Auth middleware / lack of auth

- **NO route-level dependency.** No `Depends(require_admin)`, no `Depends(_require_hr_or_*)`, no portal-token check, no header validation.
- **NO router-level dependency.** `api_router = APIRouter(prefix="/api")` (server.py:42) declares no `dependencies=[...]`.
- **NO mount-level dependency.** `app.include_router(api_router)` (server.py:8853) attaches no gates.
- **Global middlewares** (CORS, session-timeout, usage-tracking, thumbnail-cache) do **not** enforce auth on anonymous requests.

For contrast, sibling endpoints **do** carry auth dependencies — proof the framework supports gating and this route opts out:
- `@api_router.get("/admin/employees/status")` → `Depends(_require_hr_or_admin_for_queue)` (server.py:3320)
- `@router.get("/api/hr/employees")` (employee_lifecycle.py:767) → HR portal token gate

## 1.7 · Docstring / comments

- **Docstring (line 3309)**: `"""Public — returns the full MASCI crew roster (sorted by name)."""`
- **Header comment (lines 3303–3306)**: *"Employees / crew roster — used by Daily Report's 'MASCI Crews on Site' section and any other employee dropdown across the platform."*

Intentional public read is documented at the source.

## 1.8 · Returns all employee fields except `_id`?

**YES.** Confirmed by code (`{"_id": 0}` is the entire projection) and by live anonymous probe (all 20 schema fields visible).

---

# PHASE 2 — FRONTEND CONSUMER MATRIX

For each known consumer of `GET /api/employees`:

| # | Consumer (file) | Page / Workflow | Public or auth? | Why called | When triggered | Display vs search-only | Fields actually read |
|---|---|---|---|---|---|---|---|
| 1 | `components/EmployeeCombo.jsx:43` | Shared dropdown (used everywhere below) | `loadRoster()` on mount of every form using it | Provide picker | Auto on mount; retries up to 2× on empty | Both (display + filter) | **Display**: `name`, `employee_id`, `trade`, `role`, `crew` (lines 295–305). **Filter haystack**: `name`, `employee_id`, `role`, `trade`, `crew`, `email` (lines 118–129). **Binding**: `id` (line 284). **Total used**: 7 fields. |
| 2 | `pages/NewDailyReport.jsx:148` | Daily Report — "MASCI Crews on Site" picker | **PUBLIC** (`/daily/new`, `/daily/submit`) | Pick crew names | Combo opens on mount of each row in crew table | dropdown only; selected `name` becomes string field; no `onPick` to read sensitive fields | only those displayed by EmployeeCombo |
| 3 | `pages/NewIncident.jsx:555, 566` | Incident — reporter + involved-employee pickers | **PUBLIC** (`/incidents/new`, `/incidents/submit`) | Pick reporter / involved | Combo on mount | dropdown only; `onChange` returns name string | only displayed |
| 4 | `pages/NewMeeting.jsx:750` | Safety Meeting — attendee picker | **PUBLIC** (`/meetings/new`, `/meetings/submit`) | Pick attendee | Combo on mount | dropdown only | only displayed |
| 5 | `pages/NewInspection.jsx:456, 467` | Site Inspection — inspector / responsible picker | **ROLE-GATED** (`/safety/inspections/new` uses `SF()` wrapper) | Pick inspector + owner | Combo on mount (after auth) | dropdown only | only displayed |
| 6 | `pages/NewEquipmentInspection.jsx:669` | Equipment Inspection — inspector picker | **PUBLIC** (`/equipment/new`, `/equipment/submit`) | Pick inspector | Combo on mount | dropdown only | only displayed |
| 7 | `pages/NewFleetDVIR.jsx:522` | Fleet DVIR / Weekly Lead / Weekly Emergency — driver picker | **PUBLIC** (`/fleet/dvir/new`, `/fleet/dvir/submit`, `/fleet/weekly-*`) | Pick driver | Combo on mount | dropdown only | only displayed |
| 8 | `pages/NewSafetyEquipmentIssuance.jsx:78` | Safety Equipment Issuance | **ROLE-GATED** (`isSafety() \|\| isAdmin() \|\| isSafetyForms()`; redirects to `/safety-portal/login` otherwise) | Preload roster for `EmployeeRosterField` and any picker | Auto on mount after auth | dropdown only | only displayed |
| 9 | `pages/NewSafetyEquipmentTraining.jsx:59` | Safety Equipment Training | **ROLE-GATED** (same gate as above) | Preload roster | Auto on mount after auth | dropdown only | only displayed |
| 10 | `pages/HrSafetyRecords.jsx:74` | HR ↔ Safety pivot view | **ROLE-GATED** (`H()` wrapper, HR-only) | Pivot list by employee | Auto on mount after HR auth | rendered list | `name`, `id` |
| 11 | `pages/SafetyTrainingRecords.jsx:90` | Safety Training Records | **ROLE-GATED** (`SF()` wrapper, safety-only) | Pivot list | Auto on mount after auth | rendered list | `name`, `id` |
| 12 | `pages/SafetyEmployeeProfiles.jsx:61` | Safety Employee Profiles | **ROLE-GATED** (`SF()` wrapper) | Profile selector | Auto on mount after auth | rendered selector | `name`, `id` (links to `/hr/employees/{id}/accountability`, `/admin/employees/{id}/history`) |
| 13 | `components/EmployeeMasterPanel.jsx:17` | Admin master-data CRUD panel (calls `MasterListPanel` with `listEndpoint="/employees"`) | **ROLE-GATED** (used inside admin shells) | Generic CRUD list | On panel mount | tabular list | varies per panel column; typically `name`, `employee_id`, `role` |
| 14 | `components/SystemHealthBadge.jsx:22` | Top-bar health badge (mounted on `PmShell`, `AdminShell`) | **ROLE-GATED** (only rendered inside admin/PM shells) | Health probe — checks endpoint reachability | Auto on interval | reads `count` field only (or HTTP status) | none of the row data |

**Note on `EmployeeRosterField.jsx`** — it does **NOT** call `/api/employees`. It calls `/api/master-lookup/employees?q=…` (already a narrow projection: `{id, first_name, last_name, name, email, employee_id, role, display_name, trade}`). It is used inside `NewIncident.jsx`, `NewQaqcInspection.jsx`, `SafetyCorrectiveActions.jsx`, `NewSafetyEquipmentIssuance.jsx`, `NewSafetyEquipmentTraining.jsx`. Some of those pages also import `EmployeeCombo` for separate fields, so the broad `/api/employees` is still hit on them.

---

# PHASE 3 — PUBLIC SURFACE MAP

| Route | Component | Classification | Why employee roster needed | Anon payload reachable in browser network tab? | Sensitive fields visible in UI? | Sensitive fields present in API response only? |
|---|---|---|---|:-:|:-:|:-:|
| `/daily/new`, `/daily/submit` | `NewDailyReport` | **PUBLIC** | Pick crew members for the day | YES — `/api/employees` is fetched on combo mount | NO | **YES** — cdl_*, medical_card_*, status_history.actor are in JSON only |
| `/incidents/new`, `/incidents/submit` | `NewIncident` | **PUBLIC** | Pick reporter + involved + witnesses | YES | NO | YES |
| `/meetings/new`, `/meetings/submit` | `NewMeeting` | **PUBLIC** | Pick attendees | YES | NO | YES |
| `/equipment/new`, `/equipment/submit` | `NewEquipmentInspection` | **PUBLIC** | Pick inspector | YES | NO | YES |
| `/fleet/dvir/new`, `/fleet/dvir/submit`, `/fleet/weekly-lead/new`, `/fleet/weekly-emergency/new` | `NewFleetDVIR` | **PUBLIC** | Pick driver | YES | NO | YES |
| `/safety/inspections/new` | `NewInspection` | ROLE-GATED (safety) | Pick inspector | only after auth | NO | YES |
| `/safety/forms/equipment-issuance/new`, `/safety/forms/equipment-training/new` | `NewSafetyEquipment*` | ROLE-GATED (safety/admin/safety_forms) | Pick recipient | only after auth | NO | YES |
| `/safety-portal/employees`, `/safety-portal/training` | `SafetyEmployeeProfiles`, `SafetyTrainingRecords` | ROLE-GATED (safety) | Profile selector | only after auth | NO | YES |
| `/hr/safety-records` | `HrSafetyRecords` | ROLE-GATED (HR) | Pivot | only after auth | NO | YES |
| (any admin / PM shell) | `SystemHealthBadge` | ROLE-GATED | Health probe | only after auth | NO (badge reads `count` only) | YES |
| Plain anonymous client (`curl` or scraping tool) | — | PUBLIC (the endpoint, not a page) | — | YES | — | **YES** — the full payload is anonymously downloadable regardless of UI |

**Critical observation**: The **5 public form pages** (DR, Incident, Meeting, Equipment Inspection, Fleet DVIR) cause the **anonymous** browser to make the network request to `/api/employees`, which exposes the full payload to anyone viewing those pages OR scraping the API directly.

---

# PHASE 4 — FIELD NECESSITY MATRIX

## 4.1 · Field-by-field classification

| Field | Class | UI consumers that read it | Justification |
|---|---|---|---|
| `id` | **REQUIRED FOR PUBLIC DROPDOWNS** | EmployeeCombo (key), all pages that bind selection | Stable identifier |
| `name` | **REQUIRED FOR PUBLIC DROPDOWNS** | All consumers (display + filter) | Primary label |
| `employee_id` | **REQUIRED** (display badge + filter) | EmployeeCombo display "#NNN" + filter haystack | UX disambiguation when two employees share a name |
| `crew` | **REQUIRED** (display sub-line + filter) | EmployeeCombo display + filter | Helps disambiguate crews |
| `role` | **REQUIRED** (display sub-line + filter) | EmployeeCombo display + filter | Helps disambiguate roles |
| `trade` | **REQUIRED** (display sub-line + filter) | EmployeeCombo display + filter | Helps disambiguate trades |
| `is_active` | **OPTIONAL BUT USEFUL** | (used server-side in the filter; not displayed) | Could be removed from response since filter is applied server-side |
| `email` | **OPTIONAL BUT USEFUL** (filter only) | EmployeeCombo filter haystack only — never displayed | Used so a foreman can type a partial email and find the person. **Sparsely populated** (2/247 in production). Marginal utility; removing it eliminates a PII vector. |
| `phone` | **UNUSED** | NONE | Never read by any consumer. Pure exposure. |
| `approved_company_driver` | **UNUSED** | NONE in public scope | Operational status; not surfaced in UI |
| `cdl_holder` | **SENSITIVE · UNUSED in public scope** | NONE in public scope | DOT-regulated PII |
| `cdl_expiration_date` | **SENSITIVE · UNUSED in public scope** | NONE in public scope | DOT-regulated PII |
| `cdl_state` | **SENSITIVE · UNUSED in public scope** | NONE in public scope | DOT PII |
| `cdl_endorsements` | **SENSITIVE · UNUSED in public scope** | NONE in public scope | DOT PII (tanker/hazmat/doubles flags) |
| `cdl_restrictions` | **SENSITIVE · UNUSED in public scope** | NONE in public scope | DOT PII |
| `driver_status` | **SENSITIVE · UNUSED in public scope** | NONE in public scope | Operational status |
| `medical_card_expiration_date` | **SENSITIVE · UNUSED in public scope** | NONE in public scope | DOT/medical PII |
| `status_history` | **SENSITIVE · UNUSED in public scope** | NONE in public scope | Contains `actor` emails of internal users + lifecycle events |
| `created_at` | **INTERNAL ONLY · UNUSED** | NONE in public scope | Bookkeeping |
| `updated_at` | **INTERNAL ONLY · UNUSED** | NONE in public scope | Bookkeeping |

## 4.2 · Summary

- **6 fields are required** for the public dropdown UX: `id`, `name`, `employee_id`, `crew`, `role`, `trade`.
- **1 field is optional-useful but PII-adjacent**: `email` (filter haystack only, sparsely populated). Recommend dropping.
- **1 field is server-only** (filter, not display): `is_active`. Already enforced by the server filter; doesn't need to be in the response.
- **12 fields are unnecessary** for the public consumer set: `phone`, `approved_company_driver`, `cdl_holder`, `cdl_expiration_date`, `cdl_state`, `cdl_endorsements`, `cdl_restrictions`, `driver_status`, `medical_card_expiration_date`, `status_history`, `created_at`, `updated_at`.

Of the 12 unnecessary, **7 are SENSITIVE** (`cdl_*`, `medical_card_*`, `driver_status`, `status_history`).

---

# PHASE 5 — PUBLIC INTENT ANALYSIS

| Workflow | Genuinely needs a public employee lookup? | Could use a reduced public roster? | Should use authenticated roster only? |
|---|---|---|---|
| Daily Report — Crews on Site (`/daily/new`, `/daily/submit`) | **YES** — `publicMode` exists by design (workers / foremen submit DRs from a QR poster without portal auth) | **YES** — only needs `id, name, employee_id, crew, role, trade` | NO — would break the QR / kiosk submission pattern |
| Incident — Reporter + involved (`/incidents/new`, `/incidents/submit`) | **YES** — public incident reporting is a deliberate feature | YES — same reduced set | NO |
| Safety Meeting — Attendance (`/meetings/new`, `/meetings/submit`) | **YES** — public meeting submissions allowed (especially for visiting crews) | YES | NO |
| Site Inspection — Responsible person (`/safety/inspections/new`) | NO — page is ROLE-GATED (safety) | YES if site-inspection is later opened to a wider audience | could be moved to authenticated roster |
| Fleet DVIR — Driver (`/fleet/dvir/new`, `/fleet/dvir/submit`) | **YES** — DVIR submission from a paper QR is part of the daily fleet flow | YES — same reduced set | NO |
| Safety Equipment Issuance / Training | NO — already ROLE-GATED behind `isSafety/isAdmin/isSafetyForms` | could go authenticated-only | **YES** — these are not truly public |
| Equipment Inspection (`/equipment/new`, `/equipment/submit`) | **YES** — same QR/kiosk pattern as DVIR | YES | NO |

**Summary**:
- 5 public-form workflows (DR, Incident, Meeting, Equipment Inspection, Fleet DVIR) genuinely need an anonymous roster lookup for their QR/kiosk submission UX. **All of them** could be served with a strictly narrower projection (id, name, employee_id, crew, role, trade).
- The remaining role-gated consumers could move to an authenticated endpoint without UX impact.

---

# PHASE 6 — RISK CLASSIFICATION

## 6.1 · Per-axis analysis

| Axis | Observation | Severity contribution |
|---|---|---|
| 1. Data visible in UI | UI only renders `name`, `employee_id`, `trade`, `role`, `crew` | LOW — already minimal |
| 2. Data present in network payload | Full payload (20 fields × 247 records) including CDL, medical card, status_history | **MEDIUM** — overbroad |
| 3. Data downloadable anonymously | `curl https://mascidocs.com/api/employees` returns full payload, no auth | **MEDIUM** — trivially scrapable |
| 4. Data sensitivity | CDL + medical-card + actor emails in status_history; sparsely-populated email/phone | **MEDIUM** (PII / DOT-regulated; not HIPAA / SSN / financial / credentials) |
| 5. Public workflow dependency | 5 public-form workflows depend on the roster lookup | NEUTRAL — design intent is real |
| 6. Write access exists publicly? | NO — `POST /api/employees/add` returns 410; mutations are HR/admin-gated | LOW |
| 7. Auth bypass exists? | NO — this is not a misconfigured gate; the endpoint is documented public by design | LOW |
| 8. Would projection reduction fully mitigate? | YES — narrowing the projection to `{id, name, employee_id, crew, role, trade}` removes 100% of the sensitive payload while preserving 100% of the documented UX | NEUTRAL — high-leverage fix available |

## 6.2 · Final risk class

# 🟡 MEDIUM

- Not FALSE POSITIVE — the exposure is live-verified on production.
- Not LOW — the field surface includes DOT-regulated PII and internal actor emails on 247 records.
- **MEDIUM** — designed public, no auth bypass, no write capability, no credentials/financial/SSN exposure, but the field projection is broader than necessary. Mitigation is mechanical.
- Not HIGH — no system-takeover risk, no write capability, no credential leakage.
- Not CRITICAL — no large-scale HIPAA/SSN-class breach risk.

---

# PHASE 7 — MITIGATION OPTIONS (NOT IMPLEMENTED)

Five options enumerated. Each has pros/cons, blast radius, consumer impact, security improvement, dev effort, regression risk, and recommended tests.

## Option A — Narrow existing `/api/employees` projection

**Change**: replace `{"_id": 0}` with `{"_id": 0, "id": 1, "name": 1, "employee_id": 1, "crew": 1, "role": 1, "trade": 1, "is_active": 1}`.

| Aspect | Notes |
|---|---|
| Pros | Minimal change (1 line). Preserves the route URL all 13 consumers + the health badge already use. No frontend touch needed. Fully eliminates CDL, medical-card, status_history, email/phone, timestamps from anonymous reach. |
| Cons | The `email` field used in the EmployeeCombo filter haystack (line 124) would no longer find a person by their email substring. Sparsely populated (2/247) so impact is minor; but if filter-by-email is operationally important, it's a tiny UX regression. |
| Blast radius | All 13 UI consumers + health badge re-evaluated. None use a sensitive field. |
| Consumer impact | NONE for display. Marginal for filter (email no longer searchable). |
| Security improvement | HIGH — eliminates 12 fields including 7 SENSITIVE ones. |
| Development effort | ~2 minutes of `search_replace`. |
| Regression risk | LOW. Optional re-check: confirm no admin page reads dropped fields. (`grep -rn "\.cdl_\|\.medical_card_\|\.status_history\|\.phone\|\.driver_status\|\.approved_company_driver" frontend/src/` against the consumer set.) |
| Recommended tests | (a) Existing pytest suite. (b) New `test_iter_employees_projection_safe.py` asserting anonymous payload contains only the allow-list keys. (c) Live curl smoke after deploy. (d) Frontend smoke on the 5 public form pages: combo opens, populates, filters by name. |

## Option B — Split into `/api/public/employees` (narrow) + auth-gated `/api/employees` (full)

**Change**: introduce new route `GET /api/public/employees` returning the 6-field narrow projection (no auth); change existing `/api/employees` to require HR/admin auth.

| Aspect | Notes |
|---|---|
| Pros | Clean separation of concerns. The "full roster" endpoint becomes properly gated. |
| Cons | Requires frontend changes across all 13 consumers (point them at `/api/public/employees`); requires care to ensure SystemHealthBadge still probes a public endpoint; new route surface to maintain; doubles the test footprint. |
| Blast radius | All 13 UI consumers must be edited. Both backend routes + frontend `EmployeeCombo` + `MasterListPanel` need touch. |
| Consumer impact | MEDIUM — every consumer is rewired. |
| Security improvement | HIGH — same as Option A, with the bonus that authenticated callers can still see full records via the new gated endpoint. |
| Development effort | ~2–3 hours (backend + frontend + tests). |
| Regression risk | MEDIUM — every form page must be re-smoke-tested. |
| Recommended tests | (a) Anon probe of new `/api/public/employees` returns the narrow payload only. (b) Anon probe of old `/api/employees` returns 401. (c) Authenticated probe of old `/api/employees` returns full payload. (d) Smoke on all 5 public form pages + all 7 role-gated pages. |

## Option C — Keep public endpoint but strip sensitive fields server-side (response shaping)

**Change**: keep the route public but project to the narrow set (functionally identical to Option A, but framed as "shape the response" rather than "narrow the query projection"). Optionally do it via a Pydantic response_model.

| Aspect | Notes |
|---|---|
| Pros | If a Pydantic `EmployeePublic` model is used, schema is enforced — future field additions are NOT auto-exposed. Strong forward defence. |
| Cons | Slightly more code than Option A (define the model). |
| Blast radius | Same as Option A. |
| Consumer impact | NONE for display; marginal for filter (email). |
| Security improvement | HIGH + forward-proof (schema-locked). |
| Development effort | ~10–15 minutes (add `class EmployeePublic(BaseModel)` + `response_model=EmployeePublic`). |
| Regression risk | LOW. |
| Recommended tests | Same as Option A + a model-shape test asserting unknown fields are stripped. |

## Option D — Gate `/api/employees` entirely; refactor public workflows to use a project-scoped crew preload

**Change**: require auth on `/api/employees`. Modify each public form to preload the crew for the specific project (e.g., from a project-scoped public endpoint like `/api/public/projects/{id}/crew`) instead of fetching the whole roster.

| Aspect | Notes |
|---|---|
| Pros | Strongest principle-of-least-privilege posture. A public submitter only sees the crew assigned to the project they're submitting against — not the whole company. |
| Cons | Requires a project-context binding at the point of public submission (the QR / kiosk must encode the project id). Some public forms today are project-agnostic until the user picks the job. Workflow rework. |
| Blast radius | HIGH — every public form page is rewired. Backend needs a new project-scoped public roster endpoint. |
| Consumer impact | HIGH. |
| Security improvement | HIGHEST. |
| Development effort | 1–3 days. |
| Regression risk | HIGH — touches all 5 public-form QR flows. |
| Recommended tests | End-to-end QR-based DR submission, Incident submission, DVIR submission, Equipment Inspection submission, Meeting submission. |

## Option E — Other: response_model + project-scoped variant + keep existing route

A hybrid combining Option C (lock the public shape) with an opt-in project-scoped variant for QR flows. Most defensive long-term posture; biggest scope.

---

# PHASE 8 — RECOMMENDATION

## Final recommendation

**🟢 Adopt Option C (or its slim equivalent Option A)** — narrow the response shape on `/api/employees` to the 6 fields that the entire frontend consumer set actually displays/filters: `id`, `name`, `employee_id`, `crew`, `role`, `trade`. Optionally retain `is_active` if any current consumer reads it (this audit found none, but the existing combo could be sensitive to it).

## Question-by-question answer

### 1. Should `/api/employees` remain public?

**YES** — by design, with a narrowed shape. The QR/kiosk submission UX on 5 public forms (DR, Incident, Meeting, Equipment Inspection, Fleet DVIR) genuinely requires a no-auth roster lookup. Removing the public read breaks that intentional design.

### 2. If yes, what fields should it return?

```
id           (required — selection binding)
name         (required — primary label)
employee_id  (required — disambiguator, badge display)
crew         (required — sub-line + filter)
role         (required — sub-line + filter)
trade        (required — sub-line + filter)
```

### 3. If no, what replacement endpoint is needed?

Not applicable. Public access is retained with a narrowed shape.

### 4. Which public workflows depend on it?

5 public form workflows (verified at App.js route table):
- `NewDailyReport` at `/daily/new`, `/daily/submit`
- `NewIncident` at `/incidents/new`, `/incidents/submit`
- `NewMeeting` at `/meetings/new`, `/meetings/submit`
- `NewEquipmentInspection` at `/equipment/new`, `/equipment/submit`
- `NewFleetDVIR` at `/fleet/dvir/new`, `/fleet/dvir/submit`, `/fleet/weekly-lead/new`, `/fleet/weekly-emergency/new`

### 5. Which sensitive fields should be removed immediately?

Seven SENSITIVE + five UNUSED. Remove:
- `phone`
- `cdl_holder`, `cdl_expiration_date`, `cdl_state`, `cdl_endorsements`, `cdl_restrictions`
- `driver_status`
- `medical_card_expiration_date`
- `status_history` (this is the highest-value removal — it contains internal actor emails)
- `approved_company_driver`
- `created_at`, `updated_at`
- `email` (sparsely populated; filter-by-email value is marginal)

### 6. What is the lowest-risk fix?

**Option A** (or equivalent Option C with a Pydantic response_model). A one-line projection narrowing in `backend/server.py:3311-3314` from `{"_id": 0}` to `{"_id": 0, "id": 1, "name": 1, "employee_id": 1, "crew": 1, "role": 1, "trade": 1, "is_active": 1}`. No frontend touch required. ~2 minutes of work. Blast radius: 0 UI changes.

### 7. What test coverage is required?

- Anonymous-probe regression test (assert the public payload contains ONLY the allow-listed fields).
- Anonymous-probe count test (assert `count` field still represents non-deleted active employees).
- EmployeeCombo open/filter/select smoke on each of the 5 public form pages.
- SystemHealthBadge keeps showing GREEN.
- Add a new `tests/test_employees_public_projection_safe.py` that asserts none of the SENSITIVE fields appear in the anonymous payload.

### 8. Is this deploy-blocking?

**NO.** The risk is MEDIUM and the exposure is pre-existing (pre-dates the recent OKCP scope-gating deploy). It can be scheduled as a focused follow-up patch.

### 9. Is rollback needed?

**NO.** Rollback of the current OKCP scope-gating deploy would NOT address this finding (it pre-dates) and would re-introduce the OKCP blocker.

### 10. Does this affect employee records?

**NO.** A projection narrowing is a **READ-side** change. Stored employee records are not modified. No data migration. No employee data loss. No HR workflow impact. No accountability timeline impact. No status_history change. The data continues to be available to authenticated HR/admin views via `/api/hr/employees` (employee_lifecycle.py:767) and `/api/admin/employees/...` (server.py:3319+).

---

## STOP

Audit only. Evidence only. No code modified. No data modified. No deploy initiated. No auth changes. No employee records touched.

**Awaiting operator decision on Options A / C / D / E.**
