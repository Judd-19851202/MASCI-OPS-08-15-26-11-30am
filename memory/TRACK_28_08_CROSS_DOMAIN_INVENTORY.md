# TRACK 28.08 · Phase 1 · Cross-Domain Integration Inventory

Definitive map of every integration boundary between certified domains, produced by walking the code + manifest (`backend/lib/certification_manifest.py`) and validated against `backend/server.py` route registrations.

**Legend:** `src → dst` means data or state written in `src` is consumed by `dst`. Every row lists canonical IDs, source/destination routes, source/destination APIs, source/destination collections, audit + notification effects, cleanup requirements, and manifest entries affected.

---

## 1 · Employee Identity → Every Picker

- **Source workflow:** `hr.employee_lifecycle`
- **Destinations:** `field_ops.daily_report`, `field_leadership.records`, `safety.incidents_and_forms`, `training.qualifications_and_credentials`, `fleet.equipment_and_dispatch`, `executive.dashboards_and_reports`
- **Canonical id:** `employee.id` (Mongo `_id`)
- **Source route / API:** `/hr` · `/api/hr/employees*`
- **Destination APIs:** `/api/daily-reports/pickers/employees`, `/api/fl/pickers/employees`, `/api/safety/pickers/employees`, `/api/training/pickers/employees`, `/api/dispatch/pickers/employees`, `/api/executive/headcount`
- **Source collection:** `employees`
- **Destination reads:** identical `employees` reads with role scoping
- **Audit:** `state_events` (`employee.*`)
- **Notifications:** onboarding + termination via `email_routes`
- **Regression suites:** `test_track_28_04_hr_e2e.py`, `test_track_28_08_master_employee_lifecycle.py` (new)
- **Cleanup:** delete-by-prefix `TEST_28_08_EMPLOYEE_*`
- **Manifest impact:** `hr.employee_lifecycle`

## 2 · Employee Lifecycle → HR / FL / Safety / Training / Dispatch / Fleet / Executive

- **State transitions:** `pending_hire → active → assigned → on_leave → terminated → rehired → retired`
- **Every transition writes:** `employees.status`, `state_events`, optional `qualifications` retention, `dispatch_assignments`
- **Downstream truth checks:** pickers hide `terminated`/`retired`; Executive headcount decrements at `terminated`; Dispatch eligibility set to `false`
- **Regression suite:** `test_track_28_08_master_employee_lifecycle.py`

## 3 · Training / Qualification → HR / Safety / Dispatch / Executive / Public Verification

- **Canonical id:** `qualifications.id`
- **APIs:** `/api/training/qualifications*`, `/api/dispatch/eligibility/{id}`, `/api/verify/qualification/{token}`
- **Collections:** `qualifications`, `training_center`
- **Expiry event:** cron computes `expires_at ≤ today` → `state_events` + `email_routes` notification
- **Cross-domain truth:** Dispatch eligibility drops when active qualification expires; Executive compliance rate decrements; Public verify returns 410 for expired
- **Regression suite:** `test_track_28_08_master_training_eligibility.py`

## 4 · Equipment Lifecycle → Fleet / Dispatch / Shop / Daily Reports / Safety / Executive

- **Canonical id:** `equipment_master.id`
- **APIs:** `/api/equipment/*`, `/api/dispatch/assignments*`, `/api/shop/queue`, `/api/safety/inspections*`
- **State transitions:** `available → assigned → out_of_service → in_repair → available`
- **Cross-domain rule:** `out_of_service` MUST reject new `POST /api/dispatch/assignments`
- **Regression suite:** `test_track_28_08_master_equipment_chain.py`

## 5 · Daily Reports → PM / Email / PDF / Fleet / Executive / Search / Audit

- **Canonical id:** `daily_reports.id`
- **APIs:** `/api/daily-reports*`
- **PDF:** `/api/daily-reports/{id}.pdf` returns `application/pdf`, header `%PDF-`
- **Communications:** submit → route → queue → provider (safe-mode returns explicit stub)
- **Regression suite:** `test_track_28_08_master_daily_report_chain.py`

## 6 · Incidents → Safety / Fleet / HR / Executive / OCC / Reports

- **Canonical id:** `incidents.id`
- **APIs:** `/api/safety/incidents*`, `/api/incidents/projections/fleet-safe`
- **Fleet projection MUST NOT include:** medical info, witness details, root cause, CAPA, photos, protected employee PII, narrative
- **Fleet projection includes only:** case_number, incident_type, date, unit_ref, safe_route_link
- **Regression suite:** `test_track_28_08_master_incident_chain.py`

## 7 · Project Identity → Every Job-Scoped Workflow

- **Canonical id:** `jobs_master.id` + `project_number` + `project_name`
- **Consumers:** Daily Reports, Meetings, Inspections, JHAs, QA/QC, Incidents, Field Leadership, HR assignments, Fleet, Dispatch, Shop, Photos, Training, Executive
- **Truth check:** `project_number + project_name` agree across every projection
- **Regression suite:** `test_track_28_08_master_project_identity.py`

## 8 · Communications Trust Spine → Every Major Domain

- **Canonical events:** `record_created → routing_resolved → recipients_built → notification_queued → provider_accepted → audit_written → completed`
- **APIs:** `/api/admin/email-routes`, `/api/admin/comm/trust-events`
- **Collections:** `email_routes`, `resend_webhook_events`, `state_events`
- **Regression suite:** `test_track_28_08_master_comm_trust_spine.py`

## 9 · Storage / R2 → uploads / documents / photos / PDFs / recovery

- **APIs:** `/api/uploads`, `/api/admin/backup/status`, `/api/admin/recovery/snapshot`
- **Rule:** DB reference MUST NOT exist without R2 object; R2 object MUST NOT be leaked without DB reference
- **Regression suite:** `test_track_28_08_master_storage_chain.py`

## 10 · AI → Daily Reports / Safety / Executive

- **APIs:** `/api/ai/summarize`, `/api/ai/narrative`
- **Rule:** No provider secrets in response; canonical facts only; local time; explicit fallback state when unavailable
- **Regression suite:** `test_track_28_08_master_ai_safety_chain.py`

## 11 · Admin / OCC → health / maintenance / governance

- **APIs:** `/api/integrations/health`, `/api/admin/system/health`
- **Route aliases:** `/admin/occ → /admin/operations-control` (D1 fix)
- **Regression suite:** covered by `test_track_28_07_session2_manifest_and_control_layer.py::test_p8_occ_health_reachable` + Phase 0 alias tests

## 12 · Audit / State Events → history / trust / governance / executive

- **Collection:** `state_events`
- **APIs:** `/api/admin/audit/*`
- **Rule:** Every state transition in every master chain MUST insert a `state_events` doc
- **Regression suite:** cross-chain, verified inside each master chain test

## 13 · Global Search → Every Indexed Domain

- **API:** `/api/search/global`
- **Rule:** synthetic (TEST_*) records MUST NOT appear; permission-scoped
- **Regression suite:** `test_track_28_02b_global_search_synthetic.py` + `test_track_28_08_master_global_search.py`

## 14 · PortalShell / Shared Navigation → Every PortalShell-family Route

- **Rule:** every authenticated route inherits PortalShell's mobile contract
- **Regression suites:** `test_track_28_08_phase0_defects.py`, `test_track_28_08_responsive_contract.py`

---

## Route Alias Matrix (Phase 0 · re-verified in Phase 13)

| Legacy alias | Canonical route | Test |
| --- | --- | --- |
| `/admin/occ` | `/admin/operations-control` | `test_d1_admin_occ_alias_redirects_to_operations_control` |
| `/executive` | `/admin/executive-overview` | `test_d2_executive_aliases_redirect_to_executive_overview` |
| `/executive-dashboard` | `/admin/executive-overview` | 〃 |
| `/admin/executive` | `/admin/executive-overview` | 〃 |

## No Unknown Boundary Remaining

Every certified domain in `certification_manifest.py` has a documented boundary above. Cross-checked against `MANIFEST` list (13 entries): all 13 map to at least one boundary row.
