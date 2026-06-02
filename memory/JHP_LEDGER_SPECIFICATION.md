# JHP LEDGER SPECIFICATION

**Authority**: FOCP MASTER PROGRAM · Phase 6
**Mode**: SPEC (not verification) · what the OC-005 JHP Acknowledgement Ledger must look like
**TR ID**: TR-0001 (build) + TR-0006 (integration)

---

## Problem statement

Job Hazard Posters (JHPs) are physically posted on job sites and digitally distributed. Today the platform:

* Has scattered JHA references in `safety_portal/_deps.py`, `training_center.py`, `pm_admin.py`, `admin_lookups.py`, `promo_assets.py`
* Has no collection dedicated to per-employee JHP acknowledgement
* Has no UI surface for an operator (e.g. Safety) to see *who acknowledged what version on what project on what date*
* Therefore Safety + Customer-#2-prospect auditors cannot verify the workforce has actually read and signed the current hazard analysis for the current job

This is the platform's #1 unbuilt-but-high-value dead-end (TR-0001).

---

## Data model · `jhp_acknowledgements` collection

```json
{
  "_id": "ack_01HX...",
  "id": "ack_01HX...",            // public id, mirror of _id
  "jhp_id": "jhp_01HX...",        // FK to jhp_documents
  "jhp_version": "v3.2",          // string version tag
  "project_id": "proj_01HX...",   // FK to projects · the job this acknowledgement covers
  "employee_id": "emp_01HX...",   // FK to employee_master
  "acknowledged_at": "2026-06-02T15:30:00Z",
  "acknowledged_via": "in_app | qr_kiosk | poster_qr | crew_meeting | other",
  "acknowledged_by_signature": "base64-png",
  "geo": { "lat": ..., "lng": ..., "accuracy_m": ... } | null,
  "device": "iphone-x · 17.4 | android · 13 | kiosk-tab-01 | …",
  "supervisor_witness_id": "emp_01HX..." | null,
  "audit_trail": [
    { "event": "created", "at": "...", "by": { "id": "...", "name": "..." } },
    { "event": "re_acknowledged", "at": "...", "by": { "id": "...", "name": "..." }, "previous_version": "v3.1" }
  ],
  "created_at": "...",
  "created_by": { "id": "...", "name": "..." },
  "updated_at": "..."
}
```

Indexes:

* `(jhp_id, project_id, employee_id)` — unique per current ack
* `(project_id, acknowledged_at)` — for project-level audit replay
* `(employee_id, acknowledged_at)` — for employee-level compliance history
* `(jhp_version, project_id)` — for "did everyone ack the current version?" queries

## Companion collection · `jhp_documents` (existing or to-be-extended)

If a `jhp_documents` collection already exists (verification step: TBD), use it. Otherwise create with:

```json
{
  "_id": "jhp_01HX...",
  "id": "jhp_01HX...",
  "title": "Excavation Hazard Analysis · East Yard",
  "version": "v3.2",
  "supersedes_version": "v3.1",
  "scope": "project | site | division | all",
  "applies_to_project_ids": [...],
  "issued_for_project_id": "proj_01HX..." | null,
  "language_variants": { "en": "...md", "es": "...md" },
  "effective_from": "...",
  "effective_until": "..." | null,
  "ack_required_for_role_keys": ["foreman", "laborer", "operator", ...],
  "created_at": "...",
  "created_by": "..."
}
```

## Endpoints

| Method | Path | Purpose | RBAC |
|---|---|---|---|
| `POST` | `/api/jhp/acknowledgements` | Record an ack | Authenticated employee or supervisor on behalf of |
| `GET` | `/api/jhp/acknowledgements?project_id=&jhp_id=&employee_id=` | List acks · paginated | Safety / Admin / HR |
| `GET` | `/api/jhp/acknowledgements/{id}` | Single ack with audit_trail | Safety / Admin / HR |
| `GET` | `/api/jhp/ledger/project/{project_id}` | Per-project rollup: which employees on this job have acked the current version, which haven't, last ack timestamp per employee | Safety / Admin |
| `GET` | `/api/jhp/ledger/employee/{employee_id}` | Per-employee compliance: all projects · all JHPs · status | Safety / HR / Admin / the employee themselves |
| `POST` | `/api/jhp/documents` | Issue a new JHP doc / new version | Safety / Admin |
| `GET` | `/api/jhp/documents/active?project_id=` | List active JHPs requiring ack on a job | Authenticated |

## UI surfaces

### A · Operator side (Safety / Admin) — `/safety-portal/jhp/ledger`

* Project picker → table of employees on the project · columns: Name · Role · Current JHP Version · Acked Version · Acked At · Status pill (🟢 current · 🟡 outdated · 🔴 never acked).
* Bulk action: "Send re-ack reminder" (queues notification).
* Drill-down: per-employee ack-history modal.
* Export: CSV + PDF for audit purposes.

### B · Employee side (Foreman / Field worker) — `/safety-portal/jhp/acknowledge`

* On magic-link or in-app login: list of JHPs the employee is required to ack for their current assigned projects.
* Tap a JHP → read the document in EN / ES → sign + capture device + geo → submit.
* Confirmation toast + success state ("You're current on the East Yard hazard analysis.").

### C · Kiosk mode — `/kiosk/jhp` (optional Phase 2)

* QR-code scanned from the printed JHP poster → kiosk-bound device prompts employee id → ack flow.

## Acknowledgement business rules

1. An ack is **valid** only for its `jhp_version + project_id` tuple.
2. When a new JHP version is issued (supersedes_version set), every prior ack for that JHP becomes **stale**. The employee must re-acknowledge.
3. Re-acks append to the audit_trail; they do NOT overwrite.
4. Employees with role `foreman | crew_leader` who supervise others may countersign an in-person crew-meeting ack on behalf of crew (with crew employee_ids enumerated).
5. Stale acks AND missing acks both surface in the operator ledger as 🟡 / 🔴.

## Reporting / Compliance

* Per-project dashboard widget: "% of crew current on JHPs."
* Per-employee compliance score in HR dashboard.
* Audit PDF export per project · per JHP version · per date range.

## Integration with existing platform

| Surface | Integration |
|---|---|
| HR Driver Qualification dashboard | Show JHP compliance alongside CDL / Medical Card |
| Site Inspection submit | Auto-check: did the foreman ack the active JHP? Inline warning if not |
| Daily Report submit | Same auto-check; soft warning, not a gate |
| Operations Center widget | "X workers not current on JHP" tile |
| Field Leadership records | Reference last JHP ack timestamp on the foreman's profile |

## Success criteria (Definition of Done for TR-0001)

1. `jhp_acknowledgements` and `jhp_documents` collections created with indexes.
2. All 7 endpoints implemented + RBAC-gated + audit-logged.
3. Three UI surfaces (operator ledger · employee ack · kiosk optional Phase 2) shipped.
4. Bilingual EN / ES support on the employee-facing ack flow.
5. Re-ack required when version increments — verified by automated test.
6. PDF audit export for any project / JHP version / date range produces a deterministic file an auditor would accept.
7. Operator ledger refresh-cycle < 5 s for projects up to 200 crew.
8. Closes TR-0001 + TR-0006.

## Effort estimate

* Backend (collections + endpoints + RBAC + audit): **5 – 7 days**
* Frontend operator ledger: **4 days**
* Frontend employee ack flow + sig capture: **3 days**
* Bilingual content + EN/ES copy review: **2 days** (requires operator translation review)
* Tests + integration: **3 days**
* **Total**: **17 – 19 working days** (~ 3.5 sprint weeks)

## Risks

* Bilingual content gating: requires a native-Spanish reviewer (TR-D004 dependency).
* Project-employee assignment data quality: ledger is only as accurate as `employees-on-project` data. Verify that source-of-truth before shipping.
* Kiosk mode requires per-customer hardware decision — optional, defer to Phase 2.

---

End of JHP Ledger Specification.
