# DASHBOARD_DESTINATION_MAP

**Date:** 2026-02-01 · Part of the Platform Truth Map
**Purpose:** For every record kind, document **where it lands** in the UI — which portal, which dashboard, which list, which stat card. This is the inverse of `WORKFLOW_LIFECYCLE_MAP.md`: that map answers "what happens after submit"; this map answers "where do I look to find it?".

---

## 1 · Public Hub (`/`)

- 7 tile entries linking to: `/inspect/new`, `/meetings/new`, `/incidents/new`, `/daily/new`, `/equipment/new`, `/qa-qc`, `/jha`.
- No record-listing surface — purely an entry point for field crews.

Classification: **🟢 KNOWN GOOD**.

---

## 2 · Admin Hub (`/admin`)

The global view. Every record kind has at least one Admin destination.

| Record | Destination | Notes |
|--------|-------------|-------|
| Inspections | `/admin/inspections`, `/admin/inspections/:id` | Sortable list + detail |
| Meetings | `/admin/meetings`, `/admin/meetings/:id` | |
| JHAs | `/admin/jha`, `/admin/jha/:id`, `/admin/jha-plans`, `/admin/jha-plans/poster` | Library + master plans |
| Incidents | `/admin/incidents`, `/admin/incidents/:id` | |
| Daily Reports | `/admin/daily`, `/admin/daily/:id` | |
| Equipment Pre-Op | `/admin/equipment`, `/admin/equipment/:id`, `/admin/equipment/:id/history`, `/admin/equipment-inspections` | Trend tables + per-unit history |
| QA/QC | `/admin/qaqc`, `/admin/qaqc/:id` | |
| Trench Boxes | `/admin/trench-boxes`, `/admin/trench-boxes/poster` | |
| Leadership records | `/admin/leadership/records/:id`, `/admin/leadership-equipment`, `/admin/terminations` | |
| Safety Forms | `/admin/safety/issuance/:id`, `/admin/safety/training/:id` | |
| Jobs Master | `/admin/jobs` | |
| Email routing | `/admin/email` | Routes auto-email recipients |
| Training | `/admin/training`, `/admin/training-videos` | |
| Compliance / Compliance Findings | `/admin/compliance`, `/admin/compliance-findings` | |
| Audit log | `/admin/audit`, `/admin/audit-log` | |
| Photos | `/admin/photos` | Job photo library |
| Operations Events | `/admin/operations-events` | Cross-portal `events` collection |
| System & Backups | `/admin/system`, `/admin/database` | Backup Health Panel · Cloud Archives · Restore |
| System Health | `/admin/system-health` | Cluster + integration health |
| Sessions | `/admin/sessions` | Active token sessions |
| People & Access | `/admin/people` | Multi-portal directory CRUD |
| MFA | `/admin/mfa` | TOTP enroll/disable |
| Profile | `/admin/profile` | Admin's own profile |
| Project P&L | `/admin/pnl` | Scoped P&L |
| Analytics | `/admin/analytics` | |
| Governance | `/admin/governance`, `/admin/governance/self-protection` | |
| Guidance | `/admin/guidance-coverage`, `/admin/guide` | Help-Search & guide content coverage |
| Operational Inventory | `/admin/operational-inventory` | Asset roster |
| Operational Language | `/admin/operational-language` | Doctrine tone |
| Deploy Readiness | `/admin/deploy-readiness` | Pre-deploy gate readout |
| Deploy Recovery | `/admin/deploy-recovery` | Roll-forward / rollback tools |
| Digest Config | `/admin/digest-config` | Per-portal digest cadence |
| Asset Profile | `/admin/assets/:assetId` | |
| Integrations | `/admin/integrations` | Health of each external service |
| DLS QR / debrief | `/admin/dls/shift-qr`, `/admin/dls/day-1-debrief`, `/admin/dls/week-1-debrief` | Daily Leadership Standup tools |
| Legacy imports | `/admin/legacy-imports` | One-off CDL/employee imports |
| Promo assets | `/admin/promo-assets` | |
| Poster print-all | `/admin/posters/print-all` | |
| Employee history (master) | `/admin/employees/:id/history` | |
| Equipment history (master) | `/admin/equipment/:id/history` | |
| Dispatch (admin view) | `/admin/dispatch` | |

Classification: **🟢 KNOWN GOOD** — Admin is the complete superset surface.

---

## 3 · PM Hub (`/pm`)

PM portal is scoped: PMs see only records tied to their assigned jobs (per `pm_auth.compute_pm_scope`).

| Record | Destination |
|--------|-------------|
| PM home | `/pm` (Overview, Operations Center, Crew Compliance teaser) |
| Crew Compliance | `/pm/crew-compliance` |
| Jobs (assigned) | `/pm/jobs` |
| Project detail | `/pm/projects/:projectNumber` |
| Field Leadership records (own crew) | `/pm/field-leadership` |
| Fleet (read-only) | `/pm/fleet` |
| People (PM directory view) | `/pm/people` |
| Suppliers (PM read) | `/pm/suppliers` |
| Posters | `/pm/posters` |
| QA/QC list | `/pm/qaqc` |
| Photos | `/pm/photos` |
| Daily Reports list & detail | `/pm/daily`, `/pm/daily/:id` |
| Incidents list & detail | `/pm/incidents`, `/pm/incidents/:id` |
| Meetings list & detail | `/pm/meetings`, `/pm/meetings/:id` |
| Inspections list & detail | `/pm/inspections`, `/pm/inspections/:id` |
| JHA library | `/pm/jha-plans` |
| Trench Boxes | `/pm/trench-boxes` |
| Equipment dashboard | `/pm/equipment`, `/pm/equipment/:id` |
| Operational Daily Records | `/pm/odr` |

Classification: **🟢 KNOWN GOOD**.

---

## 4 · HR Hub (`/hr`)

| Record | Destination |
|--------|-------------|
| Hub | `/hr` |
| Field Leadership records (cross-portal read) | `/hr/field-leadership` |
| Field Leadership users (admin panel mirror) | `/hr/field-leadership-users` |
| Employee Accountability | `/hr/employee-accountability`, `/hr/employees/:id/accountability` |
| Time Verification | `/hr/time-verification` |
| Payroll Variance | `/hr/payroll-variance` |
| Time-Off requests | `/hr/time-off` |
| Driver Qualification | `/hr/driver-qualification`, `/hr/driver-qualification/import` |
| Daily Reports (cross-portal read) | `/hr/daily-reports`, `/hr/daily-reports/:id` |
| Incidents (cross-portal read) | `/hr/incidents` |
| Employees | `/hr/employees` |
| Safety records (cross-portal read) | `/hr/safety-records` |
| Training records | `/hr/training-records` |

Classification: **🟢 KNOWN GOOD**.

---

## 5 · Shop Hub (`/shop`)

| Record | Destination |
|--------|-------------|
| Hub | `/shop` |
| Equipment list | `/shop/equipment` |
| Equipment detail | `/shop/equipment/:id` |
| Fleet visibility | `/shop/fleet` |

Classification: **🟢 KNOWN GOOD** (cosmetic: GAP-10 dead Trash button).

---

## 6 · Safety Portal (`/safety-portal`)

| Record | Destination |
|--------|-------------|
| Hub | `/safety-portal` |
| Audits | `/safety-portal/audits` |
| Corrective Actions | `/safety-portal/corrective-actions` |
| Digest | `/safety-portal/digest` |
| Documents | `/safety-portal/documents` |
| Employees (safety profile) | `/safety-portal/employees` |
| Fire Extinguishers | `/safety-portal/fire-extinguishers`, `/safety-portal/fire-extinguishers/import` |
| Fleet (safety read) | `/safety-portal/fleet` |
| Forms records | `/safety-portal/forms-records` |
| Incidents | `/safety-portal/incidents` |
| Library | `/safety-portal/library` |
| Reports | `/safety-portal/reports` |
| Training | `/safety-portal/training` |

Classification: **🟢 KNOWN GOOD**.

---

## 7 · Dispatch Portal (`/dispatch-portal`)

| Record | Destination |
|--------|-------------|
| Hub | `/dispatch-portal` |
| Board | `/dispatch-portal/board` |
| Fleet | `/dispatch-portal/fleet` |
| Driver Qualification | `/dispatch-portal/driver-qualification` |

Classification: **🟢 KNOWN GOOD**.

---

## 8 · Field Leadership Portal (`/field-leadership/portal`)

| Record | Destination |
|--------|-------------|
| Dashboard | `/field-leadership/portal/dashboard` |
| Driver Qualification (read-only proxy) | `/field-leadership/portal/driver-qualification` |
| Bounded read of own crew DR / Meetings / JHAs / Pre-Ops / Fleet / Dispatch (today+tomorrow) / Incidents | via dashboard tiles |

Classification: **🟢 KNOWN GOOD**.

---

## 9 · Legacy Field Leadership (`/leadership`)

| Record | Destination |
|--------|-------------|
| Shared-password hub | `/leadership` |
| 10 form kinds new submission | `/leadership/{kind}/new` |
| Records list | `/leadership/records` |
| Record detail | `/leadership/records/:id` |

Classification: **🟡 KNOWN GAP — intentional dual-track**.

---

## 10 · Public form-submit pages

These are stand-alone submit destinations. Nothing surfaces here after submit — submitter sees `/thank-you`.

| URL | Form |
|-----|------|
| `/inspect/new`, `/inspections/new`, `/inspections/submit` | Site Inspection |
| `/meetings/new`, `/meetings/submit` | Safety Meeting |
| `/incidents/new`, `/incidents/submit` | Incident |
| `/daily/new`, `/daily/submit`, `/reports/daily/new` | Daily Report |
| `/equipment/new`, `/equipment/submit` | Equipment Pre-Op |
| `/jha/new`, `/jha/submit` | JHA |
| `/qa-qc`, `/qaqc/:slug/new` | QA/QC |
| `/fleet/dvir/new`, `/fleet/dvir/submit`, `/fleet/dvir/submitted/:id`, `/fleet/weekly-emergency/new`, `/fleet/weekly-lead/new` | Fleet DVIR (ORPHAN-1 destination unclear) |

Classification: 🟢 KNOWN GOOD for the post-submit redirect. ⚫ OPERATOR DECISION NEEDED for Fleet DVIR downstream destination (ORPHAN-1).

---

## 11 · ODR / Operational Records

| URL | Surface |
|-----|---------|
| `/operational-records` | Hub |
| `/odr/center` | Center |
| `/odr/new` | New ODR |
| `/odr/:id` / `/odr/:id/done` | Detail / submitted-confirmation |
| `/odr/public/:doc_id` | Public viewer |

Classification: **🟢 KNOWN GOOD**.

---

## 12 · Notifications + Tasks

| URL | Surface |
|-----|---------|
| `/notifications` | Standalone notifications drawer |
| `/tasks` | Global task list |
| Bell on every portal chrome (`NotificationBell.jsx`) | Per-portal unread count + drawer |

Classification: **🟢 KNOWN GOOD**.

---

## 13 · Cross-portal record destinations

| Record kind | All destinations |
|-------------|------------------|
| Inspection | `/admin/inspections/:id` · `/pm/inspections/:id` · `/safety-portal/audits` · `/inspections/:id` (redirects to admin — GAP-16) |
| Meeting | `/admin/meetings/:id` · `/pm/meetings/:id` · Safety library · HR cross-portal viewer |
| JHA | `/admin/jha/:id` · `/pm/jha-plans` · `/safety/jha` · `/jha` (public read) |
| Incident | every portal incidents view (admin/pm/hr/safety) |
| Daily Report | `/admin/daily/:id` · `/pm/daily/:id` · `/hr/daily-reports/:id` · `/daily/:id` |
| Equipment Pre-Op | `/admin/equipment/:id` · `/pm/equipment/:id` · `/shop/equipment/:id` · `/equipment/:id` (redirects to admin — GAP-17) |
| QA/QC | `/admin/qaqc/:id` · `/pm/qaqc` |
| PO Request | `/po-requests` · admin queue · HR PO panel |
| Field Leadership form | `/admin/leadership/records/:id` · `/leadership/records/:id` · `/hr/field-leadership` · `/pm/field-leadership` · `/field-leadership/portal/dashboard` |
| Safety Form (issuance / training) | `/admin/safety/issuance/:id` · `/admin/safety/training/:id` · `/safety/forms/equipment-issuance/:id` · `/safety/forms/equipment-training/:id` · `/safety-portal/forms-records` |

Classification: **🟢 KNOWN GOOD** + 2 GAPs (16, 17).

---

## 14 · Count-only / aggregator dashboards (vs per-record action queues)

| Stat card | Type | Portal |
|-----------|------|--------|
| "Open Safety Forms" | count-only (SOFT-2) | Safety Hub |
| "Field Leadership Forms" | search-only (SOFT-1) | Admin · HR |
| "JHA submissions" | search-only (SOFT-3) | Admin · Safety |
| "Open Inspections" | actionable queue | Admin · Safety · PM |
| "Open Incidents" | actionable queue | Admin · Safety · PM · HR |
| "Pre-Op FAIL queue" | actionable queue | Shop |
| "PO Approvals" | actionable queue | Admin · approver |
| "Active Hauls" | live state | Dispatch |
| "Stuck > 30m" | live alert | Dispatch |
| "Document Expirations" | actionable queue | HR · Safety |
| "Backup Health" | live state (when scheduler alive) | Admin |
| "System Health" | live state | Admin |

Classification: SOFT-1/2/3 = 🟡 KNOWN GAP (per-record action card missing). All others 🟢 KNOWN GOOD.

---

## 15 · Total

- **Admin Hub destinations**: 35+ panels (the global view — superset of all record kinds)
- **PM destinations**: 19
- **HR destinations**: 13
- **Safety Portal destinations**: 13
- **Shop destinations**: 4
- **Dispatch destinations**: 4
- **Field Leadership Portal destinations**: 4
- **Public submit pages**: 16
- **Cross-portal records**: 10 record kinds with multi-portal landing

Classification rollup: 🟢 the destinations themselves exist for every record kind except Fleet DVIR (⚫ OPERATOR DECISION NEEDED). SOFT-1/2/3 are present-but-count-only.
