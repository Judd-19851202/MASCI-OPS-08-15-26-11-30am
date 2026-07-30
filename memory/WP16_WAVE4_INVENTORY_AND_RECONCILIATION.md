# WP16 Wave 4 — Authoritative Inventory & Denominator Reconciliation

Date: 2026-07-30

## Executive scope statement

- Wave 4 scope: **HR Certification**
- Phase authorized: **Inventory & Completeness Reconciliation only**
- Production changes made: **None**
- Inspections performed: **None**
- Repairs performed: **None**

## Final denominator

- **Final Wave 4 denominator:** **26 HR experiences**
- Denominator status: **authoritative pending Executive review**
- Identifier policy: **W4-001 … W4-026 assigned and immutable after approval**

## Sources reconciled

- `WP16_PHASE_B_CONTROL.md` — planned Wave 4 allocation (`26` route-pattern screens)
- `WP16_CERTIFICATION_REGISTER.csv` — authoritative Wave assignment + source files
- `PRD.md` — executive dashboard synchronization
- `ROADMAP.md` — Wave 4 scope synchronization
- `frontend/src/app/routing/AppRoutes.jsx` — authoritative route registration, lazy loading, and route guards
- `frontend/src/components/hr/sidebar/HrSideNavV2.jsx` — active HR navigation + de facto HR domain registry
- `frontend/src/components/RequireHr.jsx` — protected-route rule
- `frontend/src/lib/permissions.js` — portal registration + HR home/login mapping
- `backend/routes/hr_portal.py` + `backend/routes/hr_portal_deps.py` — HR API family + canonical HR auth dependency
- Existing wave locks — exclusions validated against already-locked Wave 1 / Wave 2 artifacts and current certification register assignments

## Taxonomy

- **HR Access & Recovery:** 1 experience(s)
- **People Operations:** 11 experience(s)
- **Time & Payroll:** 3 experience(s)
- **Qualifications / Training:** 6 experience(s)
- **Compliance & Records:** 1 experience(s)
- **Historical Records:** 4 experience(s)

## Route hierarchy

### HR Access & Recovery
- `W4-001` · `/hr/forgot` · Forgot · route_screen

### People Operations
- `W4-002` · `/hr/field-leadership` · Field Leadership · route_screen
- `W4-003` · `/hr/field-leadership-users` · Field Leadership Users · route_screen
- `W4-004` · `/hr/employee-accountability` · Employee Accountability · route_screen
- `W4-012` · `/hr/daily-reports` · Daily Reports · route_screen
- `W4-013` · `/hr/daily-reports/:id` · Daily Reports · detail_screen
- `W4-017` · `/hr/employees` · Employees · route_screen
- `W4-018` · `/hr/employee-requests` · Employee Requests · route_screen
- `W4-019` · `/hr/employees/:id/accountability` · Employees · detail_screen
- `W4-020` · `/hr/employees/:id/thread` · Employees · detail_screen
- `W4-021` · `/hr/employees/:empId/profile` · Employees · detail_screen
- `W4-026` · `/hr/incidents` · Incidents · route_screen

### Time & Payroll
- `W4-005` · `/hr/time-verification` · Time Verification · route_screen
- `W4-006` · `/hr/time-off` · Time OFF · route_screen
- `W4-007` · `/hr/payroll-variance` · Payroll Variance · route_screen

### Qualifications / Training
- `W4-008` · `/hr/training-records` · Training Records · route_screen
- `W4-009` · `/hr/qualifications` · Qualifications · route_screen
- `W4-010` · `/hr/driver-qualification` · Driver Qualification · route_screen
- `W4-011` · `/hr/driver-qualification/import` · Driver Qualification · route_screen
- `W4-014` · `/hr/motive-drivers` · Motive Drivers · route_screen
- `W4-015` · `/hr/driver/:driverKey` · Driver · detail_screen

### Compliance & Records
- `W4-016` · `/hr/safety-records` · Safety Records · route_screen

### Historical Records
- `W4-022` · `/hr/historical-records/intake` · Historical Records · route_screen
- `W4-023` · `/hr/historical-records/queue` · Historical Records · route_screen
- `W4-024` · `/hr/historical-records/batches` · Historical Records · route_screen
- `W4-025` · `/hr/historical-records/batches/:batchId` · Historical Records · detail_screen

## Complete inventory

| W4 ID | Cert row | Route | Title | Domain | Parent Portal | Navigation Location | CRUD | API dependencies | Shared Components | Responsive Variants | Permission Requirements | Feature Flags | External Integrations | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| W4-001 | WP16-ROUTE-297 | `/hr/forgot` | Forgot | HR Access & Recovery | HR | Public auth route | Create (reset request trigger) | /api/auth/forgot-password (shared reset flow) | Page-local composition only | Public auth responsive login/redirect pattern | Public (no guard) | — | Password-reset email flow | RECONCILED_VERIFIED_NOT_CERTIFIED |
| W4-002 | WP16-ROUTE-303 | `/hr/field-leadership` | Field Leadership | People Operations | HR | Sidebar — People Operations | Read / filter / export PDF | /api/hr/field-leadership; /api/hr/field-leadership/:id/pdf | HrPageShell; HelpTipBlock | Shared HR responsive shell / mobile-safe layout | RequireHr guard; X-HR-Token; admin does not satisfy HR route guard | hrSidebarV2 (shared HR navigation chrome) | None documented | PRIOR_EVIDENCE_EXISTS_REVERIFY_REQUIRED |
| W4-003 | WP16-ROUTE-304 | `/hr/field-leadership-users` | Field Leadership Users | People Operations | HR | Sidebar — People Operations | Create / update / disable / reset password | /api/admin/field-leadership-users* (panel-backed admin/HR management surface) | HrSideNavV2; AdminFieldLeadershipUsersPanel; HelpTipBlock; IamUserDetailDrawerHost; PortalShell | Shared HR responsive shell / mobile-safe layout | RequireHr guard; X-HR-Token; admin does not satisfy HR route guard | hrSidebarV2 (shared HR navigation chrome) | None documented | BLOCKED_PRIOR_EVIDENCE |
| W4-004 | WP16-ROUTE-305 | `/hr/employee-accountability` | Employee Accountability | People Operations | HR | Sidebar — People Operations | Read / search / filter | /hr/employee-accountability | HrPageShell; HelpTipBlock | Shared HR responsive shell / mobile-safe layout | RequireHr guard; X-HR-Token; admin does not satisfy HR route guard | hrSidebarV2 (shared HR navigation chrome) | None documented | BLOCKED_PRIOR_EVIDENCE |
| W4-005 | WP16-ROUTE-306 | `/hr/time-verification` | Time Verification | Time & Payroll | HR | Sidebar — Time & Payroll | Read / filter / variance review | /api/hr/time-verification | HrPageShell; WhyItMattersPanel; HelpTipBlock; WeeklyHoursFlag; DailyHoursFlag | Shared HR responsive shell / mobile-safe layout | RequireHr guard; X-HR-Token; admin does not satisfy HR route guard | hrSidebarV2 (shared HR navigation chrome) | None documented | PRIOR_EVIDENCE_EXISTS_REVERIFY_REQUIRED |
| W4-006 | WP16-ROUTE-307 | `/hr/time-off` | Time OFF | Time & Payroll | HR | Sidebar — Time & Payroll | Read / approve / deny / request info / create public link | /api/field-leadership/time-off; /api/field-leadership/time-off/stats; /api/field-leadership/time-off/:id/decide; /api/field-leadership/time-off/public-link | HrSideNavV2; HelpTipBlock; PortalShell | Shared HR responsive shell / mobile-safe layout | RequireHr guard; X-HR-Token; admin does not satisfy HR route guard | hrSidebarV2 (shared HR navigation chrome) | None documented | BLOCKED_PRIOR_EVIDENCE |
| W4-007 | WP16-ROUTE-308 | `/hr/payroll-variance` | Payroll Variance | Time & Payroll | HR | Sidebar — Time & Payroll | Upload / compare / review | /api/hr/payroll-variance/recent; /api/hr/payroll-variance/upload; /api/hr/payroll-variance/:batchId.csv | PayrollVarianceLifecyclePanel; HrPageShell; HelpTipBlock | Shared HR responsive shell / mobile-safe layout | RequireHr guard; X-HR-Token; admin does not satisfy HR route guard | hrSidebarV2 (shared HR navigation chrome) | Exact payroll CSV import | PRIOR_EVIDENCE_EXISTS_REVERIFY_REQUIRED |
| W4-008 | WP16-ROUTE-309 | `/hr/training-records` | Training Records | Qualifications / Training | HR | Sidebar — Compliance & Records | Read / filter | /hr/training-records | HrPageShell | Shared HR responsive shell / mobile-safe layout | RequireHr guard; X-HR-Token; admin does not satisfy HR route guard | hrSidebarV2 (shared HR navigation chrome) | None documented | PRIOR_EVIDENCE_EXISTS_REVERIFY_REQUIRED |
| W4-009 | WP16-ROUTE-310 | `/hr/qualifications` | Qualifications | Qualifications / Training | HR | Sidebar — Compliance & Records | Read / search / expiration tracking | /api/employee-lifecycle/qualifications* (page-owned qualification reads) | HrPageShell | Shared HR responsive shell / mobile-safe layout | RequireHr guard; X-HR-Token; admin does not satisfy HR route guard | hrSidebarV2 (shared HR navigation chrome) | None documented | PRIOR_EVIDENCE_EXISTS_REVERIFY_REQUIRED |
| W4-010 | WP16-ROUTE-311 | `/hr/driver-qualification` | Driver Qualification | Qualifications / Training | HR | Sidebar — Compliance & Records | Read / filter / export | /hr/driver-qualification/dashboard; /hr/driver-qualification/dashboard.csv | HrPageShell; HelpTipBlock | Shared HR responsive shell / mobile-safe layout | RequireHr guard; X-HR-Token; admin does not satisfy HR route guard | hrSidebarV2 (shared HR navigation chrome) | Driver qualification / CDL document data | BLOCKED_PRIOR_EVIDENCE |
| W4-011 | WP16-ROUTE-312 | `/hr/driver-qualification/import` | Driver Qualification | Qualifications / Training | HR | Hidden/detail route (linked from parent experience) | Upload / preview / apply | /hr/driver-qualification/import/apply; /hr/driver-qualification/import/audit; /hr/driver-qualification/import/preview | HrPageShell | Shared HR responsive shell / mobile-safe layout | RequireHr guard; X-HR-Token; admin does not satisfy HR route guard | hrSidebarV2 (shared HR navigation chrome) | Driver qualification import payloads | BLOCKED_PRIOR_EVIDENCE |
| W4-012 | WP16-ROUTE-313 | `/hr/daily-reports` | Daily Reports | People Operations | HR | Sidebar — People Operations | Read / search / filter | /api/daily-reports* (shared daily report collection) | HrSideNavV2; RefKicker; PortalShell | Shared HR responsive shell / mobile-safe layout | RequireHr guard; X-HR-Token; admin does not satisfy HR route guard | hrSidebarV2 (shared HR navigation chrome) | None documented | PRIOR_EVIDENCE_EXISTS_REVERIFY_REQUIRED |
| W4-013 | WP16-ROUTE-314 | `/hr/daily-reports/:id` | Daily Reports | People Operations | HR | Hidden/detail route (linked from parent experience) | Read / print / media review | /api/daily-reports/:id | MasciLogo; RefKicker; useHubHome; MapThumbnail; PrintWatermark | Shared HR responsive shell / mobile-safe layout | RequireHr guard; X-HR-Token; admin does not satisfy HR route guard | — | None documented | NOT_YET_EXERCISED |
| W4-014 | WP16-ROUTE-315 | `/hr/motive-drivers` | Motive Drivers | Qualifications / Training | HR | Hidden/detail route (linked from parent experience) | Read / cleanup workflow | /api/hr/motive-drivers* / cleanup endpoints via page-owned mapping tab | HrSideNavV2; MappingCleanupTab; PortalShell | Shared HR responsive shell / mobile-safe layout | RequireHr guard; X-HR-Token; admin does not satisfy HR route guard | hrSidebarV2 (shared HR navigation chrome) | Motive data / mapping cleanup integration | BLOCKED_PRIOR_EVIDENCE |
| W4-015 | WP16-ROUTE-316 | `/hr/driver/:driverKey` | Driver | Qualifications / Training | HR | Hidden/detail route (linked from parent experience) | Read detail | /api/hr/driver/:driverKey (driver profile contract) | HrSideNavV2; DriverCommandProfile; PortalShell | Shared HR responsive shell / mobile-safe layout | RequireHr guard; X-HR-Token; admin does not satisfy HR route guard | hrSidebarV2 (shared HR navigation chrome) | None documented | NOT_YET_EXERCISED |
| W4-016 | WP16-ROUTE-349 | `/hr/safety-records` | Safety Records | Compliance & Records | HR | Sidebar — Compliance & Records | Read / filter / linked training actions | /api/hr/safety-records*; /api/training-records* | HrPageShell | Shared HR responsive shell / mobile-safe layout | RequireHr guard; X-HR-Token; admin does not satisfy HR route guard | hrSidebarV2 (shared HR navigation chrome) | None documented | PRIOR_EVIDENCE_EXISTS_REVERIFY_REQUIRED |
| W4-017 | WP16-ROUTE-392 | `/hr/employees` | Employees | People Operations | HR | Sidebar — People Operations | Create / update / lifecycle-status / reactivate / export | /api/hr/employees; /api/hr/employees/facets; /api/hr/employees/:id; /api/hr/employees/:id/status; /api/hr/employees/:id/reactivate; /api/hr/employees/export.xlsx | HrSideNavV2; NotificationBell; StatusBadge; EmptyState; GlobalSearch | Shared HR responsive shell / mobile-safe layout | RequireHr guard; X-HR-Token; admin does not satisfy HR route guard | hrSidebarV2 (shared HR navigation chrome) | None documented | BLOCKED_PRIOR_EVIDENCE |
| W4-018 | WP16-ROUTE-393 | `/hr/employee-requests` | Employee Requests | People Operations | HR | Hidden/detail route (linked from parent experience) | Read / approve / reject | /api/hr/employee-requests; /api/hr/employee-requests/:id/approve; /api/hr/employee-requests/:id/reject | Page-local composition only | Shared HR responsive shell / mobile-safe layout | RequireHr guard; X-HR-Token; admin does not satisfy HR route guard | — | None documented | BLOCKED_PRIOR_EVIDENCE |
| W4-019 | WP16-ROUTE-394 | `/hr/employees/:id/accountability` | Employees | People Operations | HR | Hidden/detail route (linked from parent experience) | Read timeline/detail | /api/hr/employees/:id/accountability* | HrSideNavV2; LifecycleGuide; PortalShell | Shared HR responsive shell / mobile-safe layout | RequireHr guard; X-HR-Token; admin does not satisfy HR route guard | hrSidebarV2 (shared HR navigation chrome) | None documented | NOT_YET_EXERCISED |
| W4-020 | WP16-ROUTE-395 | `/hr/employees/:id/thread` | Employees | People Operations | HR | Hidden/detail route (linked from parent experience) | Read / thread interaction | /api/hr/employees/:id/thread* | HrSideNavV2; OperationalThreadPage; PortalShell | Shared HR responsive shell / mobile-safe layout | RequireHr guard; X-HR-Token; admin does not satisfy HR route guard | hrSidebarV2 (shared HR navigation chrome) | None documented | NOT_YET_EXERCISED |
| W4-021 | WP16-ROUTE-396 | `/hr/employees/:empId/profile` | Employees | People Operations | HR | Hidden/detail route (linked from parent experience) | Read profile/detail | /api/hr/employees/:empId/profile* | Page-local composition only | Shared HR responsive shell / mobile-safe layout | RequireHr guard; X-HR-Token; admin does not satisfy HR route guard | — | None documented | NOT_YET_EXERCISED |
| W4-022 | WP16-ROUTE-397 | `/hr/historical-records/intake` | Historical Records | Historical Records | HR | Sidebar — Compliance & Records | Upload / stage / classify | /api/historical-records/intake* | EmployeeCombo | Shared HR responsive shell / mobile-safe layout | RequireHr guard; X-HR-Token; admin does not satisfy HR route guard | — | None documented | NOT_YET_EXERCISED |
| W4-023 | WP16-ROUTE-398 | `/hr/historical-records/queue` | Historical Records | Historical Records | HR | Sidebar — Compliance & Records | Read / review / approve / reject | /api/historical-records/queue* | EmployeeCombo | Shared HR responsive shell / mobile-safe layout | RequireHr guard; X-HR-Token; admin does not satisfy HR route guard | — | None documented | NOT_YET_EXERCISED |
| W4-024 | WP16-ROUTE-399 | `/hr/historical-records/batches` | Historical Records | Historical Records | HR | Sidebar — Compliance & Records | Read / filter / batch drill-in | /api/historical-records/batches* | Page-local composition only | Shared HR responsive shell / mobile-safe layout | RequireHr guard; X-HR-Token; admin does not satisfy HR route guard | — | None documented | NOT_YET_EXERCISED |
| W4-025 | WP16-ROUTE-400 | `/hr/historical-records/batches/:batchId` | Historical Records | Historical Records | HR | Hidden/detail route (linked from parent experience) | Read / batch action review | /api/historical-records/batches/:batchId* | EmployeeCombo | Shared HR responsive shell / mobile-safe layout | RequireHr guard; X-HR-Token; admin does not satisfy HR route guard | — | None documented | NOT_YET_EXERCISED |
| W4-026 | WP16-ROUTE-401 | `/hr/incidents` | Incidents | People Operations | HR | Sidebar — People Operations | Read / filter / export | /api/hr/incidents | HrSideNavV2; LifecycleGuide; PortalShell | Shared HR responsive shell / mobile-safe layout | RequireHr guard; X-HR-Token; admin does not satisfy HR route guard | hrSidebarV2 (shared HR navigation chrome) | None documented | NOT_YET_EXERCISED |

## Completeness reconciliation findings

1. **Wave allocation agreement confirmed.** `WP16_PHASE_B_CONTROL.md` assigns **26** route-pattern screens to Wave 4 HR, and `WP16_CERTIFICATION_REGISTER.csv` now contains **26** Wave 4 HR rows with permanent `W4-XXX` identifiers.
2. **AppRoutes reconciliation complete.** `AppRoutes.jsx` exposes **32** `/hr*` route-pattern screens plus **1** internal HR preview route. Of those, **26** belong to Wave 4, **6** are already allocated to locked earlier waves, and the internal preview remains allocated to Wave 16.
- `/hr/login` is outside the Wave 4 denominator because it is already allocated to **Wave 1 — Public Pages & Authentication** (`Login`) or reserved for a different wave.
- `/hr/reset/:token` is outside the Wave 4 denominator because it is already allocated to **Wave 1 — Public Pages & Authentication** (`Reset`) or reserved for a different wave.
- `/hr/change-password` is outside the Wave 4 denominator because it is already allocated to **Wave 1 — Public Pages & Authentication** (`Change Password`) or reserved for a different wave.
- `/hr` is outside the Wave 4 denominator because it is already allocated to **Wave 2 — Homepage / Dashboard** (`HR`) or reserved for a different wave.
- `/hr/hub_legacy` is outside the Wave 4 denominator because it is already allocated to **Wave 2 — Homepage / Dashboard** (`HUB Legacy`) or reserved for a different wave.
- `/hr/hub_v2` is outside the Wave 4 denominator because it is already allocated to **Wave 2 — Homepage / Dashboard** (`HUB V2`) or reserved for a different wave.
- `/_internal/hr-v2-preview` is outside the Wave 4 denominator because it is already allocated to **Wave 16 — Remaining Operational Modules** (`HR V2 Preview`) or reserved for a different wave.
3. **No Wave 4 route duplicates detected.** The Wave 4 denominator has `0` duplicate route entries across the certification register and `AppRoutes` declarations.
4. **No orphaned Wave 4 experiences detected.** After excluding prior-wave ownership and the internal preview route, missing-from-register Wave 4 routes = `0` and missing-from-AppRoutes Wave 4 rows = `0`.
5. **Protected route mapping reconciled.** Wave 4 includes **25** protected HR experiences behind `RequireHr` and **1** public HR auth-adjacent experience (`/hr/forgot`).
6. **Navigation ownership reconciled.** Wave 4 includes **16** sidebar-linked experiences and **9** hidden/detail routes that are reachable only from parent screens or deep links. These hidden/detail routes are documented, not orphaned.
7. **Cross-wave HR sidebar links documented, not absorbed into the denominator.** The HR sidebar also links to `/po-requests` (Wave 10), `/document-expirations` (Wave 16), `/guidance?from=hr` (Wave 12), and `/hr/change-password` (Wave 1). These remain external dependencies and do **not** expand the Wave 4 denominator.
8. **HR domain-registry discrepancy documented.** No standalone `domainMap` file exists for HR. The active domain registry is the grouped route taxonomy in `HrSideNavV2.jsx`, which is therefore treated as the authoritative HR domain-map source for this wave.
9. **Mission-category search reconciliation.** No authoritative route families were found for applicants, recruiting, candidate status, offer tracking, onboarding orientation dashboards, I-9, W-4, background checks, or drug-testing screens. These capabilities are therefore **not currently implemented as certifiable HR experiences** and were not added to the Wave 4 denominator.
10. **Auth-wave edge case preserved by documentation.** `/hr/forgot` remains in the Wave 4 denominator because the certification register already allocates it to Wave 4, even though other HR auth surfaces (`/hr/login`, `/hr/reset/:token`, `/hr/change-password`) are already owned by locked earlier waves. No renumbering or wave reallocation was performed in this inventory phase.

## Evidence

- `WP16_PHASE_B_CONTROL.md` line 47: Wave 4 planned allocation = `26`
- `WP16_CERTIFICATION_REGISTER.csv`: 26 rows tagged `Wave 4 — HR`, each now carrying a `wave_inventory_id` value
- `AppRoutes.jsx` lines 1039–1288: canonical HR route declarations
- `HrSideNavV2.jsx` lines 25–83: HR domain groups + nav routes
- `RequireHr.jsx` lines 11–52: HR protected-route contract
- `permissions.js` lines 27–57: canonical HR portal label, home, and login registration
- `hr_portal.py` header + route declarations: authoritative HR backend endpoint family

## Wave 4 Executive Inventory Package

- Final denominator: **26**
- Total HR experiences: **26**
- Reconciliation findings: **10** documented above
- Missing experiences: **0 hidden/orphaned authoritative HR routes**; mission-category gaps are documented as not-yet-implemented capabilities, not silent route omissions
- Duplicate experiences: **0**
- Recommended inspection scope: inspect all 26 Wave 4 HR experiences, prioritizing (1) blocked-prior-evidence screens, (2) hidden/detail screens with no direct navigation entry, and (3) cross-family compliance / historical-record workflows
- Executive readiness assessment: denominator reconciled, IDs assigned, source conflicts documented, certification register synchronized, PRD synchronized, ROADMAP synchronized

**READY FOR WAVE 4 INSPECTION AUTHORIZATION**
