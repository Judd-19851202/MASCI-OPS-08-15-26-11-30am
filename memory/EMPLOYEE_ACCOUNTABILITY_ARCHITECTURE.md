# EMPLOYEE_ACCOUNTABILITY_ARCHITECTURE.md
**Initiative:** Platform Governance Convergence — Phase 1
**Iteration:** iter353 · Phase 1
**Generated:** 2026-05-23
**Status:** READ-ONLY · Architecture proposal · No collections will be migrated yet.

---

## 1 · The problem

Today, employee accountability data is **fragmented across 11+ collections**, each owned by a different portal, written through different routes, with different audit semantics. There is **no canonical per-employee timeline**.

When an operator asks: *"Show me everything about Andrew Hayes — onboarding, training, certs, incidents, PPE, CDL, attendance, current status, and his last 90 days of activity"*, the platform cannot answer that question in a single query. Each surface returns a slice; the operator must mentally stitch them together.

This was tolerable when each portal stood alone. With the iter352/iter353 policy shift to **shared HR + Safety accountability ownership**, fragmentation becomes a real operational hazard:
- 🔴 Compliance gaps go undetected (HR doesn't know Safety closed a CAPA; Safety doesn't know HR moved someone to Inactive).
- 🔴 Cross-portal contradictions persist (employee marked Active by HR but driver_status="suspended" by Safety).
- 🟡 Insurance / DOT exports require manual data-stitching.

---

## 2 · Current collections (sources of truth)

| Collection | Owner | What it stores | Linkage to employee | Audit attribution? |
|---|---|---|---|---|
| `employees` | HR | Master employee record (name, trade, supervisor, hire/separation, CDL fields, lifecycle status) | `id` (canonical) | partial (`created_by`, `status_history` since iter316) |
| `safety_training_records` | Safety | Training certifications (OSHA, CPR/AED, equipment) | `employee_id` + `employee_master_id` + `employee_name` | partial (`created_by_name`) |
| `safety_documents` | Safety | Document library (OSHA certs, fit-for-duty, qualification certs) | NONE (library is global, not per-employee) | partial |
| `safety_equipment_issuances` | Safety | PPE issued (boots, hard hats, vests, etc) | `employee_id` + `employee_name` | partial |
| `safety_equipment_trainings` | Safety | Use-and-care training acknowledgments | `employee_id` | partial |
| `training_track_records` | HR | HR-internal curriculums (Operational Guidance Center) | `employee_id` + `employee_master_id` + `employee_name` | partial |
| `incidents` | Safety | Injury/near-miss/incident records | `employee_id` (involved party) | partial |
| `corrective_actions` | Safety | CAPAs assigned to employees | `assigned_to_employee_id` | yes (iter? — chained from incidents) |
| `daily_reports` | PM | References employee work hours, crew membership | `crew[*].employee_id` (denormalized) | yes |
| `tasks` | All | Task assignments | `assigned_to_user_id` | yes |
| `field_leadership_records` | FL | Onboarding/separation forms, approved-driver forms, accountability forms | `employee_id` (or freeform) | yes (iter314) |
| `driver_qualification_imports` | HR | CDL roster import audit | (per-row employee_id) | **yes (iter352)** |
| `document_expirations` | Shared | Mirror of upcoming expirations from above collections | `employee_id` | mirror only |

**Plus:** `admin_audit_log` (HR/Admin field edits) and `employees.status_history` (calm-tone audit chain on the employee doc itself).

---

## 3 · Linkage Standard (iter350)

Cross-portal records resolve to the canonical `employees` row via the iter350 **Employee Linkage Standard**:

1. **Primary:** `employee_id` exact match (canonical roster ID)
2. **Fallback A:** `employee_master_id` exact match (alternate FK)
3. **Fallback B:** normalized `name` + `email` exact match
4. **Fallback C:** normalized `name` alone
5. **Final:** report `unlinked` (graceful None — never crash, never silently drop)

`/app/backend/lib/employee_linkage.py` exposes `resolve_employee()`, `attach_employee_link()`, `attach_employee_links()`. **This is the canonical resolver — use it everywhere.**

---

## 4 · Proposed unified timeline endpoint

### `GET /api/hr/employees/{id}/accountability/timeline`

**Auth:** `require_hr_or_admin` (matches existing accountability surfaces).

**Returns:** Single JSON payload with every accountability event tied to that employee, sorted by timestamp DESC.

```json
{
  "employee": { "id": "...", "name": "Andrew Hayes", "trade": "Transportation", "lifecycle_status": "Active", ... },
  "current_state": {
    "active": true,
    "cdl_status": "valid",
    "cdl_expiration_date": "2027-06-30",
    "medical_card_expiration_date": "2026-09-15",
    "open_capas": 0,
    "open_tasks": 2,
    "expiring_within_30d": [],
    "last_safety_training": "2026-04-10",
    "last_ppe_issuance": "2026-01-15",
    "last_daily_report": "2026-05-22"
  },
  "timeline": [
    {
      "ts": "2026-05-22T14:30:00Z",
      "kind": "daily_report",
      "actor": "pm@mascigc.com",
      "actor_role": "pm",
      "source_collection": "daily_reports",
      "summary": "Worked 9.5h on JOB-1042",
      "ref_id": "..."
    },
    {
      "ts": "2026-04-10T08:00:00Z",
      "kind": "safety_training",
      "actor": "safety@mascigc.com",
      "actor_role": "safety",
      "source_collection": "safety_training_records",
      "summary": "OSHA 10-hour completion · expires 2028-04-10",
      "ref_id": "..."
    },
    {
      "ts": "2026-01-15T13:00:00Z",
      "kind": "ppe_issuance",
      "actor": "safety@mascigc.com",
      "actor_role": "safety",
      "source_collection": "safety_equipment_issuances",
      "summary": "Issued: hard hat, safety glasses, hi-viz vest",
      "ref_id": "..."
    },
    {
      "ts": "2025-11-02T10:00:00Z",
      "kind": "incident",
      "actor": "safety@mascigc.com",
      "actor_role": "safety",
      "source_collection": "incidents",
      "severity": "minor",
      "summary": "Hand laceration · first aid only · CAPA closed",
      "ref_id": "..."
    },
    ...
  ],
  "counts": {
    "trainings": 5, "documents": 2, "ppe_issuances": 3,
    "incidents": 1, "capas": 0, "tasks": 12,
    "daily_reports": 87, "fl_records": 1
  }
}
```

**Implementation pattern:**
- Single endpoint, multiple find() calls in parallel (asyncio.gather).
- Each collection's row is mapped to a uniform `TimelineEvent` shape.
- Final merge + sort by `ts` DESC.
- Pagination via `before_ts` cursor (timeline can be long for tenured employees).
- Optional `?kind=` filter for type-specific drill-down.

---

## 5 · Proposed unified employee accountability page

**Frontend:** `/hr/employees/{id}/accountability` (new page).

**Sections:**
1. **Header card** — employee identity, lifecycle status pill, last-active timestamp.
2. **Current State Tiles** (6) — CDL status, Medical Card status, Open CAPAs, Open Tasks, Last Safety Training, Last Daily Report.
3. **Expirations Watch Strip** (only renders if anything expires within 90 days) — calm amber bar with click-through to the relevant editor.
4. **Tabbed timeline** — All / Trainings / Documents / PPE / Incidents / Tasks / Dailies / FL Records. Each tab uses the same `TimelineEvent` schema; tab counts come from `counts` object.
5. **Source Attribution column** — every row shows `actor_role` pill (HR / Safety / PM / FL / Dispatch / Shop) so the operator knows which portal wrote it.

**RBAC for the page:** `H` wrapper (`require_hr_user`) — same shell as HR Employee Detail. Admin via super-admin shell.

---

## 6 · Future-ready data model adjustments

To make the timeline endpoint efficient at scale:

### A · Add denormalized `employee_index` field everywhere
- New canonical field on all per-employee collections: `employee_index: {employee_id, employee_master_id, employee_name_norm, employee_email_norm, linked_at}`.
- Set on write via the `lib/employee_linkage.attach_employee_link()` helper.
- Indexed for fast `find({"employee_index.employee_id": X})`.

### B · Add canonical `actor_audit` object to every write
- Replace the inconsistent `created_by` / `created_by_name` / `created_by_role` zoo with `actor_audit: {ts, user_id, email, role, originating_portal, source_doc_id?, ip?}`.
- Backwards-compat: leave old fields in place during migration; new readers consult `actor_audit` first.

### C · Single document-expiration mirror
- Already exists (`document_expirations` mirror). Extend it to mirror ALL accountability collections (training expiration, medical-card expiration, qualification expiration, etc).
- One unified expiration-monitor cron consumes only this collection.

### D · Cross-portal contradiction detection
- New nightly job: for each employee, compute a "consistency check" — e.g. `employees.cdl_holder=true` but no `safety_training_records.training_name="CDL"` → flag for HR review.
- Surface flags as a dedicated tile on the HR Hub: "Cross-portal contradictions: N employees need review".

---

## 7 · Roll-out roadmap

| Iteration | Deliverable | Notes |
|---|---|---|
| iter353c (Phase 2 candidate) | `/api/hr/employees/{id}/accountability/timeline` endpoint + dedicated frontend page | Pure read; no schema changes. |
| iter354 | Denormalized `employee_index` written by `lib/employee_linkage` on every shared write path | Pure additive — backfill ALL existing records via one-time script. |
| iter355 | `actor_audit` object on all new writes | Same backfill pattern; legacy rows marked `actor_role: "legacy"`. |
| iter356 | Expanded `document_expirations` mirror (all accountability expirations) | iter286 already mirrors most; just need to add the missing ones. |
| iter357 | Cross-portal consistency-check cron + HR Hub tile | Nightly job. Findings go to a new `cross_portal_findings` collection. |
| iter358 | Insurance export packet (PDF or zipped XLSX) of full driver accountability roster | DOT compliance prep. |

---

## 8 · Risk: doing this badly

- 🔴 **Performance.** A naive timeline query could fan-out to 11 collections per request. Mitigation: parallel find()s, paginated tabs, lazy-load sub-tabs.
- 🔴 **Stale data.** If `employee_index` denorm gets out of sync after employee rename. Mitigation: rename triggers re-sync via existing `status_history` write path.
- 🟡 **Audit attribution gaps.** Legacy rows have no actor_role. Mitigation: explicit `legacy` marker; never silently fill in.
- 🟡 **Cross-portal contradiction noise.** First nightly run will find dozens of contradictions on day 1. Mitigation: surface gradually, allow batch-resolve.

---

## 9 · NOT in this initiative

Phase 1 is audit-only. The following are documented but **not built yet**:
- ❌ Unified timeline endpoint (Phase 2 candidate iter353c)
- ❌ Per-employee accountability page (Phase 2 candidate)
- ❌ Denormalized `employee_index` writes (Phase 2)
- ❌ `actor_audit` consolidation (Phase 2)
- ❌ Cross-portal contradiction detection (Phase 2)
- ❌ Schema migrations on existing collections (Phase 2 — strictly additive)

---

## 10 · See also
- `lib/employee_linkage.py` (iter350) — canonical resolver
- `PLATFORM_OWNERSHIP_MATRIX.md` § 1, § 3, § 4, § 7 — collection ownership
- `SHARED_GOVERNANCE_GAPS.md` GAP-014, GAP-015, GAP-017 — audit / expiration / fragmentation
