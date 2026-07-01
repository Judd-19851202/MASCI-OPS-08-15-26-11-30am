# TRACK 19.08 · Shop / PM / Safety Integration Map

Downstream consumers of the operational forms ecosystem.

---

## 1 · Shop integration

### Inputs (writes flowing INTO Shop surfaces)

| Source form | Write path | Shop surface consuming |
| --- | --- | --- |
| DVIR (Fail) | `fleet_defects` insert · `fleet_status.oos` upsert | Shop Hub · Defects queue · Unit History |
| Equipment Pre-Op (Fail on fleet unit) | Same | Same |
| Direct defect report (backend-only endpoint) | `POST /api/fleet/defects` | Same |
| Motive/Samsara ingest (integration) | Same collections | Same |

### Shop actions (state transitions)

`open → acknowledged → assigned → in_progress → repaired → (manager_review) → cleared`

Each step:
* Emits audit event with correlation id
* Fires targeted email via `schedule_auto_email("fleet-defect-<state>", ...)`
* When last defect for a unit clears → `fleet_status` back to `available`

### Shop views (portal surfaces)

* `ShopHub.jsx` / `ShopHubV2.jsx` — top-level dashboard.
* `/shop/fleet/defects` — defect queue with filters (status · severity · unit · project).
* `pages/shop/UnitHistoryTimeline.jsx` — per-unit lifetime history (DVIRs + defects + repairs).
* `pages/shop/UnitHistoryLanding.jsx` — landing before unit selection.
* `ShopOpsIntelPanel.jsx` — dispatch-side snapshot of shop backlog.
* `ShopMaintainxReadinessTile.jsx` — integration status tile.

### Notification recipients (per defect)

Resolved from `email_routes` filtered by workflow key + severity + project scope. Typical: Shop foreman (home yard) · Dispatch on-shift · Safety Manager (CC on OOS) · Fleet Manager (CC on OOS) · Project PM.

---

## 2 · PM integration

### Inputs (what PM sees per form)

| Form | PM surface consuming |
| --- | --- |
| Daily Report | PM Board (`PmHub.jsx` · `components/pm/command/PmBoardShell.jsx`) · PM dashboard tiles · project-scoped DR list |
| Equipment Pre-Op | PM board (equipment status column) · unit history (read-only) |
| DVIR | PM board (fleet readiness tile) · unit history |
| Meeting | PM board (safety cadence tile) |
| Incident | PM board (safety-events tile) — severity ≥ medium surfaces prominently |
| JHA | PM board (JHA coverage tile) — % of crew acknowledged |
| Constraint | PM board (constraint queue) |
| Corrective Action | PM board (CA due-dates tile) |

### PM permissions

* Per-PM scoping via `pm_auth.compute_pm_scope(db, actor)` — returns `is_admin` OR `project_numbers` set.
* Non-admin PM sees only their project numbers.
* Shared PM tokens (legacy) bypass scoping — captured by `is_admin=True` in the legacy code path.

### PM notifications

* Digest emails (weekly via `safety_digest` cron when `SCHEDULER_ENABLED=true`).
* Per-event emails via `schedule_auto_email("daily-report", ...)` / `("dvir", ...)` etc. — routing tables in `email_routes` collection.

### PM PDF / Export

* All submitted forms produce a WeasyPrint PDF stored under R2, keyed on the doc id.
* Compliance export (CSV) available via `/daily-reports.csv` / `/incidents.csv` etc.
* Digest emails carry links to PDFs (never inline them).

---

## 3 · Safety integration

### Inputs (writes flowing INTO Safety)

| Source | Safety surface |
| --- | --- |
| Incident (any severity) | `SafetyIncidents.jsx` · `IncidentsDashboard.jsx` · Safety-portal digest |
| Meeting | `SafetyTrainingRecords.jsx` (attendance credit) · digest |
| JHA | `JhaPlansAdmin.jsx` (published) · acknowledgement compliance dashboard |
| Corrective Action | `SafetyCorrectiveActions.jsx` (queue + due dates) |
| DVIR/Equipment Fail (safety-critical only) | CC on OOS notifications; unit-history read-only |
| Excavation | Safety-portal trench-safety module |
| Fire Extinguisher | `SafetyFireExtinguishers.jsx` |

### Safety actions

* Transition incidents through lifecycle states (`reported → in_investigation → closed`).
* Create / edit corrective actions.
* Publish / revise JHAs → new revision spawns re-acknowledgement.
* Approve safety-training records.

### Safety notifications

* Every incident with `severity >= high` triggers immediate email to Safety + Executive + HR.
* Weekly safety digest via `safety_digest` cron.
* Corrective-action due-date reminders (weekly).

---

## 4 · HR integration

### Inputs

| Source | HR surface |
| --- | --- |
| Daily Report | `HrDailyReports.jsx` (accountability read) |
| Incident (injury) | `HrIncidents.jsx` — injuries auto-tagged to the employee's accountability timeline |
| Meeting | `HrTrainingRecords.jsx` — attendance credit |
| Corrective Action | `hr/corrective-actions` (HR-scoped view) |
| Equipment Issuance | HR-accountability (PPE issued) |
| Equipment Training | HR-accountability (competency verified) |
| Employee Request | `HrEmployeeRequestsQueue.jsx` |
| Payroll Variance | `HrPayrollVariance.jsx` (crew-hours anomalies) |

### HR-canon rule (Track 19.03)

* `/api/hr/employee-roster` is the single source of truth for employee identity on every form. All EmployeeCombos read from this endpoint.
* Inactive/terminated employees do not surface in pickers (Track 19.03 lock).
* Track 19.06 amendment: known-inactive employees are filtered from Smart Prefill offers on Daily Report.

---

## 5 · Executive / Compliance integration

* `ExecutiveOverview.jsx` — top-level KPI board fed by aggregations on daily_reports · incidents · meetings · fleet_audit · fleet_defects.
* `ComplianceExportPanel.jsx` — CSV / XLSX bundle export scoped per project or date range.
* `pdf_render.py` produces branded PDFs for every form family (see `09_NOTIFICATION_EMAIL_PDF_MATRIX.md`).

---

## 6 · Cross-portal integration surface

Every operational form fires an `audit_events` entry with a stable correlation id. That correlation id is the primary key of the **Trust Spine** — visible under Admin console. It lets any downstream consumer prove "I saw this event because of *that* operator action."

Loss of Trust Spine correlation is treated as P0 drift and is locked by `test_track_15_46_friction_reduction.py` and related regression tests.
