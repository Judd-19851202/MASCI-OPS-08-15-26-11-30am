# TRACK 14.0-PLATFORM-DISCOVERABILITY-CERTIFICATION — WAVE A INVENTORY

**Date:** 2026-02-15 (fork session)
**Scope:** Read-only audit of every portal navigation surface, hub tile,
sidebar entry, deep-link redirect, and global-search probe across the
MASCI Operations Platform. Two obvious-safe defects fixed inline.

## A. Portal Route Map (extracted from `/app/frontend/src/App.js`)

| Portal | Login Route | Hub Route | Auth Guard | Shell |
|--------|-------------|-----------|------------|-------|
| Public Hub | n/a | `/` | none | none (Hub.jsx) |
| Admin | `/admin/login` | `/admin` | `RequireAdmin` (A) | `AdminShell` |
| PM | `/pm/login` | `/pm` → `/pm/hub` | `RequirePm` (P) | `PmShell` |
| HR | `/hr/login`, `/sign-in` | `/hr` | `RequireHr` (H) | `HrPageShell` |
| Safety | `/safety-portal/login` | `/safety-portal` | `RequireSafety` (SF) | `SafetyShell` |
| Shop | `/shop/login` | `/shop` | `RequireShop` (S) | (shop pages) |
| Dispatch | `/dispatch-portal/login` | `/dispatch-portal` | `RequireDispatch` (DP) | (dispatch pages) |
| Field Leadership Portal | `/field-leadership/portal/login`, `/leadership/login` | `/field-leadership/portal/dashboard` | `RequireFl` (FL) | (FL pages) |
| Field Leadership (legacy doc gate) | `/leadership/legacy-login` | `/leadership` | shared-password gate | (legacy hub) |
| Dev | `/dev/login` | `/dev` | `RequireDev` (D) | (dev pages) |
| Cross-portal shared surfaces | n/a | `/tasks` `/po-requests` `/document-expirations` `/project-health` `/asset-transfers` `/constraints` `/operations-actions` `/operational-records` `/guidance` | mixed (page-scoped) | shared shells |

## B. Hub Tile / Sidebar Coverage Matrix

### Admin Console — `AdminShell.SECTIONS` (V1 default · 33 entries)
| Group | Workflow | Route | data-testid |
|-------|----------|-------|-------------|
| Operations | Overview | `/admin` | `admin-tile-overview` |
| Operations | Command Center | `/admin/command-center` | `admin-tile-command-center` |
| Operations | Operations Events | `/admin/operations-events` | `admin-tile-events` |
| Operations | Project Health | `/project-health` | `admin-tile-project-health` |
| Operations | Asset Transfers | `/asset-transfers` | `admin-tile-asset-transfers` |
| Operations | Dispatch | `/admin/dispatch` | `admin-tile-dispatch` |
| Workforce | People & Access | `/admin/people` | `admin-tile-people` |
| Workforce | Training & Forms | `/admin/training` | `admin-tile-training` |
| Workforce | Document Expirations | `/document-expirations` | `admin-tile-expirations` |
| Workforce | Sessions | `/admin/sessions` | `admin-tile-sessions` |
| Equipment | Jobs & Field | `/admin/jobs` | `admin-tile-jobs` |
| Equipment | Equipment & Suppliers | `/admin/equipment` | `admin-tile-equipment` |
| Equipment | Asset Administration | `/admin/asset-admin` | `admin-tile-asset-admin` |
| Equipment | Operational Inventory | `/admin/operational-inventory` | `admin-tile-operational-inventory` |
| Communications | Email & Routing | `/admin/email` | `admin-tile-email` |
| Communications | Weekly Digest | `/admin/digest-config` | `admin-tile-digest-config` |
| Compliance | Compliance & Audits | `/admin/compliance` | `admin-tile-compliance` |
| Compliance | Governance Health | `/admin/governance` | `admin-tile-governance` |
| Compliance | Operational Language | `/admin/operational-language` | `admin-tile-operational-language` |
| System | System & Backups | `/admin/system` | `admin-tile-system` |
| System | System Health | `/admin/system-health` | `admin-tile-system-health` |
| System | Database | `/admin/database` | `admin-tile-database` |
| System | Audit Log | `/admin/audit-log` | `admin-tile-audit-log` |
| System | Deploy Readiness | `/admin/deploy-readiness` | `admin-tile-deploy-readiness` |
| System | Deploy Recovery | `/admin/deploy-recovery` | `admin-tile-deploy-recovery` |
| System | Usage Analytics | `/admin/analytics` | `admin-tile-analytics` |
| System | Integrations | `/admin/integrations` | `admin-tile-integrations` |
| System | Promo Assets | `/admin/promo-assets` | `admin-tile-promo-assets` |
| Footer pinned | Tasks & Actions | `/tasks` | `admin-tile-tasks` |
| Footer pinned | PO Requests | `/po-requests` | `admin-tile-po` |
| Footer pinned | Guidance | `/guidance` | `admin-tile-operational-guidance` |
| Hub-only tile | Project Staffing | `/admin/project-staffing` | `admin-hub-v2-q-project-staffing` |
| Hub-only tile | Scheduler Runs | `/admin/scheduler-runs` | `admin-tile-scheduler-runs` |

### Admin Sidebar V2 — `domainMap.js` (feature-flagged OFF by default)
- Operations (8 entries), Workforce (4), Equipment & Fleet (2),
  Communications (2), Safety & Compliance (3), System & Governance (9),
  Footer pinned (3). Total ~31 — fewer than V1's 33.
- See **Defect Ledger D-A1** for the routes V2 omits.

### PM Console — `PmShell.SECTIONS` (7 entries)
| Workflow | Route | data-testid |
|----------|-------|-------------|
| Overview | `/pm` | `pm-shell-nav-overview` |
| Jobs | `/pm/jobs` | `pm-shell-nav-jobs` |
| Field Leadership | `/pm/field-leadership` | `pm-shell-nav-field-leadership` |
| Equipment Fleet | `/pm/fleet` | `pm-shell-nav-fleet` |
| People | `/pm/people` | `pm-shell-nav-people` |
| Suppliers | `/pm/suppliers` | `pm-shell-nav-suppliers` |
| Site Posters | `/pm/posters` | `pm-shell-nav-posters` |

### PM Hub V2 — full destination list (richer than sidebar)
- **Command Center** `/pm/command-center` · **Holds** `/pm/holds` · **Due Today** `/pm/due-today`
- **Daily** `/pm/daily` · **Incidents** `/pm/incidents` · **CAPAs** `/pm/incidents?tab=capas`
- **Constraints** `/constraints` · **Jobs** `/pm/jobs` · **QA/QC** `/pm/qaqc`
- **ODR Panel** `/pm/odr` · **Crew Compliance** `/pm/crew-compliance` · **Photos** `/pm/photos`
- **Project Staffing** `/pm/project-staffing` · **Fleet** `/pm/fleet` · **PO Requests** `/po-requests`

### HR Hub V2 — destination tiles
- Employees `/hr/employees` · Training `/hr/training-records` · Driver Qualification `/hr/driver-qualification`
- Payroll Variance `/hr/payroll-variance` · Time Verification `/hr/time-verification`
- FL Users `/hr/field-leadership-users` · Accountability `/hr/employee-accountability`
- Employee Requests `/hr/employee-requests` · Time Off `/hr/time-off`
- Daily Reports `/hr/daily-reports` · Incidents `/hr/incidents` · Field Leadership `/hr/field-leadership`
- Document Expirations `/safety-portal/document-expirations` (cross-portal link)

### Safety Hub V2 + Safety Sidebar V2 (14 entries)
| Group | Workflow | Route |
|-------|----------|-------|
| Primary action | Trench Safety | `/safety/trench-safety` |
| Active | Incidents & Near Misses | `/safety-portal/incidents` |
| Active | Corrective Actions | `/safety-portal/corrective-actions` |
| Active | Tasks & Actions | `/tasks` |
| Records | Training & Certifications | `/safety-portal/training` |
| Records | Safety Document Library | `/safety-portal/documents` |
| Records | Equipment & PPE Accountability | `/safety-portal/forms-records` |
| Records | Employee Safety Profiles | `/safety-portal/employees` |
| Tracking | Document Expirations | `/document-expirations` |
| Tracking | Fire Extinguishers | `/safety-portal/fire-extinguishers` |
| Tracking | Weekly Digest | `/safety-portal/digest` |
| Tracking | Reports & Exports | `/safety-portal/reports` |
| Reference | Audits & Inspections | `/safety-portal/audits` |
| Reference | Operational Daily Records | `/odr/center` |
| Reference | Topic Library | `/safety-portal/library` |
| Reference | Trucking · Fleet | `/safety-portal/fleet` |
| Reference | Training Center | `/guidance?from=safety` |

### Shop Hub V2 — destination tiles
- Manager Queue `/shop/manager/queue` · My Assignments `/shop/me` · Asset Care `/shop/asset-care`
- Pre-Ops `/shop/equipment` · Fleet `/shop/fleet` · Fuel/Lube `/shop/fuel-lube`
- Service Truck Reconciliation `/shop/service-truck-reconciliation` · Unit History `/shop/units/history`
- PM Dashboard `/shop/pm` · PM Templates `/shop/pm/templates` · PM Schedules `/shop/pm/schedules` · PM Work Orders `/shop/pm/work-orders`
- Trench Safety Repairs `/shop/trench-safety-repairs`

### Dispatch Hub V2 — destination tiles
- Command Map `/dispatch-portal/command` · Board `/dispatch-portal/board` (5 focus filters)
- Fleet `/dispatch-portal/fleet` (3 focus filters)
- Haul Ledger `/dispatch-portal/haul-ledger` · Driver Qualification `/dispatch-portal/driver-qualification`

### Field Leadership Portal — destinations
- Dashboard `/field-leadership/portal/dashboard` · Change Password · Driver Qualification (read-only)

### Field Leadership (legacy doc gate) — `/leadership`
- Records `/leadership/records` · Form launchers (`/leadership/:kind/new`) · Guidance `/guidance?from=leadership`

## C. Global Search Coverage (`routes/global_search.py`)

### Probed kinds (15 total)
`tasks · notifications · employees · equipment · projects · po_requests ·
incidents · corrective_actions · fire_extinguishers · safety_documents ·
safety_training · document_expirations · operations_events ·
field_leadership · staffing`

### Role visibility map
| Role | Kinds visible |
|------|--------------|
| admin | ALL 15 |
| safety | 10 (excludes projects, field_leadership, operations_events, po_requests, employees subset) |
| hr | 6 |
| pm | 9 (PM-scoped via `compute_pm_scope`) |
| shop | 5 |
| dispatch | 5 |
| leadership | 2 (po_requests, field_leadership) |

### Search fields (per probe — regex-matched, case-insensitive)
- **employees**: name, first_name, last_name, legal_first/middle/last_name, preferred_name, employee_id, email
- **equipment**: unit_number, make_model, vin, serial_number, type
- **projects**: project_number, name, location
- **incidents**: title, description, incident_type, project_number
- **staffing**: display_name, email, assignment_role, role_label, project_number
- **corrective_actions**: title, description, project_number, assigned_to_name
- (15 probes total — see source for full list)

## D. Deep Link Redirect Map (Phase 10 audit)

| Source URL | Destination | Audience | Status |
|------------|-------------|----------|--------|
| `/qa-qc` | `/qaqc` | all | ✅ |
| `/cheat-sheet` | `/cheatsheet` | all | ✅ |
| `/training-hub` | `/training` | all | ✅ |
| `/jha/submit`, `/jha/new` | `/jha` | all | ✅ |
| `/safety/jha` | `/jha` | all | ✅ |
| `/safety/trench-boxes` | `/trench-boxes` | all | ✅ |
| `/safety-portal/trench-safety*` | `/safety/trench-safety*` | safety | ✅ |
| `/admin/jha`, `/admin/jha/:id` | `/admin/jha-plans` | admin | ✅ |
| `/inspections`, `/inspect/:id`, `/inspections/:id` | `/admin/inspections` | admin | ✅ |
| `/meetings`, `/meetings/:id` | `/admin/meetings` | admin | ✅ |
| `/incidents`, `/incidents/:id` | `/admin/incidents` | admin | ✅ |
| `/daily`, `/daily/:id` | `/admin/daily` | admin | ✅ |
| `/reports/daily/new` | `/daily/new` | all | ✅ |
| `/trench-boxes` | `/trench-safety/tabulated-data` | all | ✅ |
| `/cheatsheet` legacy alias | active | all | ✅ |
| `/admin/audit` | `/admin/audit-log` | admin | ✅ |
| `/admin/health` | `/admin/system-health` | admin | ✅ |
| `/ops-training`, `/ops-training/:slug` | `/guidance` | all | ✅ |
| `/field-leadership` (root) | `/leadership` | all | ✅ |
| `/app/*` | `/` (Crew Hub removed) | all | ✅ |
| `/inspect/new`, `/submit`, `/inspections/submit`, `/inspections/new` | `/safety-portal/login?returnTo=/safety/inspections/new` | all | ✅ |
| **`/safety-portal/meetings`** | **`/safety-portal/meetings` (now SF-guarded list)** | **safety** | ✅ **FIXED** (was → /admin/meetings) |
| **`/admin/daily-reports`** | **`/admin/daily`** | **admin** | ✅ **FIXED** (was → /hr/daily-reports) |
| `/admin/trench-safety-assets` | `/safety/trench-safety/assets` | admin | ✅ |

## E. Public / Form-Password Gated Routes

| Workflow | Route | Gate | Output |
|----------|-------|------|--------|
| Excavation submit (public) | `/trench-safety/excavation/new` | `FormPasswordGate` | new excavation record |
| Trench Safety QR landing | `/trench-safety/assets/:assetId` | none | public mobile dashboard |
| Public Trench Safety dashboard | `/trench-safety` | none | tabulated data, references, report |
| Public Time-Off (manager link) | `/time-off/public/:token` | token | approve/deny |
| Public Daily submit | `/daily/submit` | password | public daily form |
| Public Incident submit | `/incidents/submit` | password | public incident |
| Public Meeting submit | `/meetings/submit` | password | public meeting |
| Public Equipment submit | `/equipment/submit` | password | public equipment inspection |
| Driver magic link | `/d/:token` | token | driver shift landing |
| Driver self-start | `/shift` | none (per-device) | shift start |

## F. Personas — Daily Workflow Findability (Phase 3 inventory)

| Persona | Most-used surface | Reachable in ≤ 10s? | Notes |
|---------|------------------|--------------------|----|
| Super Admin | `/admin` overview + sidebar | ✅ 33 entries | confidence high |
| Admin | `/admin` overview | ✅ | confidence high |
| PM | `/pm/hub` (Hub V2) | ✅ rich tile grid | confidence high after Track 14.0-PM-STAFFING |
| Superintendent / Foreman | `/leadership` (legacy gate) → submit forms | ✅ | confidence high · top-3 forms front-and-center |
| Safety Manager | `/safety-portal` Hub V2 | ✅ for top 6 workflows | **GAPS:** Site Inspections list, Meetings list, Daily Reports review, JHA Plans — see Defect Ledger |
| HR Manager | `/hr` Hub V2 | ✅ | confidence high |
| Shop Manager | `/shop` Hub V2 | ✅ rich queue | confidence high |
| Dispatcher | `/dispatch-portal` (map default) | ✅ | confidence high · map-dominant |
| FL portal user (per-user account) | `/field-leadership/portal/dashboard` | ✅ minimal but clear | low-feature portal · acceptable |

## G. Workflow-by-Persona Cross-Walk

| Workflow | Admin | PM | HR | Safety | Shop | Dispatch | FL | First-class entry |
|----------|-------|----|----|--------|------|----------|----|-------------------|
| Project Staffing | ✅ `/admin/project-staffing` | ✅ `/pm/project-staffing` | ➖ (read via HR Emp Drawer) | ➖ | ➖ | ➖ | ➖ | hub tile · sidebar |
| Daily Reports list | ✅ `/admin/daily` | ✅ `/pm/daily` | ✅ `/hr/daily-reports` | ⚠️ **gap** | ➖ | ➖ | ✅ submit | hub tile |
| Safety Meetings list | ✅ `/admin/meetings` | ✅ `/pm/meetings` | ➖ | ✅ `/safety-portal/meetings` *(newly added)* | ➖ | ➖ | ✅ submit | hub tile |
| Site Inspections list | ✅ `/admin/inspections` | ✅ `/pm/inspections` | ➖ | ⚠️ **gap** (hub tile missing) | ➖ | ➖ | ➖ | hub tile |
| Incidents list | ✅ | ✅ | ✅ `/hr/incidents` | ✅ Hub V2 tile | ➖ | ➖ | ➖ | hub tile |
| Corrective Actions | ✅ (via `/admin/incidents`) | ✅ `/pm/incidents?tab=capas` | ➖ | ✅ first-class | ➖ | ➖ | ➖ | hub tile |
| Equipment / Fleet | ✅ | ✅ `/pm/fleet` `/pm/equipment` | ➖ | ✅ `/safety-portal/fleet` | ✅ first-class | ✅ first-class | ➖ | hub tile · sidebar |
| Trench Safety | ✅ `/admin/trench-safety` | ➖ ⚠️ **gap** | ➖ | ✅ first-class | ➖ | ➖ | ➖ | hub primary action |
| JHA Plans | ✅ `/admin/jha-plans` | ✅ `/pm/jha-plans` | ➖ | ⚠️ **gap** (no hub tile) | ➖ | ➖ | ➖ | hub tile |
| QA/QC | ✅ `/admin/qaqc` | ✅ `/pm/qaqc` | ➖ | ➖ | ➖ | ➖ | ➖ | hub tile |
| Job Photos | ✅ `/admin/photos` | ✅ `/pm/photos` | ➖ | ➖ | ➖ | ➖ | ➖ | hub tile |
| HR Requests / Time Off | ➖ | ➖ | ✅ first-class | ➖ | ➖ | ➖ | ➖ | hub tile |
| Training Records | ✅ `/admin/training` | ➖ | ✅ `/hr/training-records` | ✅ `/safety-portal/training` | ➖ | ➖ | ➖ | hub tile |
| Tasks | ✅ pinned | ✅ (cross-portal `/tasks`) | ➖ | ✅ sidebar | ➖ | ➖ | ➖ | pinned |
| PO Requests | ✅ pinned | ✅ Hub V2 tile | ✅ Hub V2 tile | ➖ | ➖ | ➖ | ✅ Hub legacy tile | pinned |
| Project Health | ✅ sidebar V2 | ➖ ⚠️ | ➖ | ➖ | ➖ | ➖ | ➖ | sidebar |
| Asset Transfers | ✅ sidebar V2 | ➖ | ➖ | ➖ | ➖ | ➖ | ➖ | sidebar |
| Operations Center / Map | ✅ `/operations-center` | ➖ ⚠️ | ➖ | ➖ | ➖ | ➖ | ➖ | top-nav (admin-only) |
| Operational Records (unified) | ✅ pinned via `/operational-records` | ➖ | ➖ | ➖ | ➖ | ➖ | ➖ | sidebar |
| Operations Actions | ✅ sidebar V2 + Hub tile | ➖ | ➖ | ➖ | ➖ | ➖ | ➖ | tile (cross-portal entry exists via component) |
| Driver Profile (DCP-1) | ✅ `/admin/driver-intel/:k` | ➖ | ✅ `/hr/driver/:k` | ✅ `/safety-portal/driver/:k` | ➖ | ✅ `/dispatch-portal/driver/:k` | ➖ | cross-portal contract — strong |

## H. Mobile / iPad / Desktop Status (Phase 9 — spot-checked, not full re-cert)

- S2A iPad track previously certified iPad portrait + landscape for field workflows.
- Desktop 1366×768 and 1920×1080: AdminShell sidebar collapses to drawer on `<lg`; PmShell, HrPageShell, SafetyShell follow same pattern.
- **No new clipping / touch-target / horizontal-scroll regressions found** in audited routes.
- **Targeted iPad validation needed:** `/safety-portal/meetings` (new SF route) — captured in Phase 9 follow-up below.

## I. Label / Language Hygiene (Phase 11 sample audit)

✅ Operational language used throughout: "Project Staffing", "Add Team Member",
"Safety Meeting", "Incident Report", "Equipment Inspection", "Daily Report".

⚠️ Two abstractions flagged but defensible (operator vocabulary):
- "ODR" (Operational Daily Records) — internal jargon; documented in glossary
- "DCP" (Driver Command Profile) — internal naming; not user-facing in title bars

No "Registry", "Entity", "Workflow Node", or "Roster Mapping" violations found.

## J. Empty State Health (Phase 12 spot-check)

Sampled `JobTeamRosterPanel`, `IncidentsDashboard`, `MeetingsDashboard`,
`PmHoldsV2`, `PmDueTodayV2`, `SafetyHubV2`:
- `JobTeamRosterPanel` — "No team members assigned yet" + Add CTA ✅
- `IncidentsDashboard` — empty list shows filters helper ✅
- `MeetingsDashboard` — empty list shows "Submit Meeting" CTA ✅
- `SafetyHubV2` queue tiles — "Safety is all clear" calm state ✅
- `PmHoldsV2` / `PmDueTodayV2` — calm empty states ✅
- No "blank screen" failures observed in audited routes.

## K. Wave A — Summary of Inline Safe Fixes

| # | File | Defect | Fix | Risk |
|---|------|--------|-----|------|
| 1 | `/app/frontend/src/App.js:1000` | `/safety-portal/meetings` redirected to `/admin/meetings`, which is wrapped in `RequireAdminOrPm` and rejects Safety tokens → Safety users landed on AccessDenied. | Replaced redirect with real `SF(<MeetingsDashboard />)` route. Backend `/api/meetings` already accepts safety token (`_read_gate = require_safety_admin_or_pm or require_admin`). | None — additive, Safety can now list meetings in their portal shell. |
| 2 | `/app/frontend/src/App.js:1001` | `/admin/daily-reports` redirected to `/hr/daily-reports`, which is HR-only → Admin users typing the natural URL landed on AccessDenied. | Changed redirect target to `/admin/daily` (the canonical admin daily-reports list). | None — natural URL now resolves to the admin surface. HR's own canonical URL `/hr/daily-reports` is unchanged. |

Both fixes verified by `eslint` clean and visual review of `App.js`.
