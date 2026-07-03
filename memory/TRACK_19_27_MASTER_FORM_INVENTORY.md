# TRACK 19.27 · Master Form & Workflow Inventory

## Modernized public/field forms (Trust Spine, bilingual, mobile-first)
| Workflow | Route | Backend prefix | Portal destinations |
|---|---|---|---|
| Daily Report | `/daily/reports/new`, `/daily/*` | `/api/daily-reports/*` | PM · Admin · Safety (if triggered) |
| Job Photos | `/daily/photos` | `/api/job-photos/*` | PM · Admin |
| Equipment Pre-Op | `/inspect/pre-op` | `/api/pre-op/*` | Shop · Admin · PM (if OOS) |
| Equipment Post-Op | `/inspect/post-op` | `/api/post-op/*` | Shop · Admin |
| DVIR | `/inspect/dvir/pre`, `/inspect/dvir/post` | `/api/dvir/*` | Shop · Fleet · Dispatch (on defects) |
| Safety Meeting | `/meetings/safety/*` | `/api/safety-meetings/*` | Safety · Training history |
| Toolbox Talk | `/meetings/toolbox/*` | `/api/toolbox/*` | Safety · Training history |
| Incident Report | `/incidents/report` | `/api/incident-cases/*` | Safety · PM · Management (severity) |
| Near Miss kiosk | `/near-miss` | `/api/near-miss/*` | Safety |
| Trench Safety (excavation) | `/trench-safety/excavation/new` | `/api/trench-safety/*` | Safety · PM · Admin |
| JHA / JHP | `/jha/*` | `/api/jha/*` | Safety · PM · Admin |
| QA/QC | `/qa-qc/*`, `/qaqc/*` | `/api/qa-qc/*` | PM · Admin · QA/QC lead |

## Internal-review / lifecycle surfaces
| Workflow | Route | Backend | Portal owner |
|---|---|---|---|
| Historical Records Intake | `/hr/historical-records/intake` | `/api/employee-records/*` | HR (system owner) · Safety · Asset Admin (lane-scoped) |
| Historical Records Queue | `/hr/historical-records/queue` | `/api/employee-records/queues/{lane}` | HR / Safety / Asset Admin |
| Bulk Historical Intake | `/hr/historical-records/batches`, `/…/batches/:id` | `/api/employee-records/batches/*` | Same |
| Employee 360° | `/hr/employees/:id/profile` | `/api/hr/employees/:id/accountability/timeline`, `/api/employee-records/employees/:id/records` | HR |
| Safety Case Workspace | `/safety/cases/:caseId` | `/api/incident-cases/*` | Safety |
| Executive Intelligence | `/safety/executive-intelligence` | `/api/safety/executive/*` | Safety leadership + owner |
| Report Intelligence Engine | `/reports/*` | `/api/reports/*` | Admin · Safety · PM |
| Field Leadership Users | `/hr/field-leadership` | `/api/hr/field-leadership/*` | HR |
| Payroll Variance | `/hr/payroll-variance` | `/api/hr/payroll/*` | HR |
| Time Verification | `/hr/time-verification` | `/api/hr/time/*` | HR |
| Driver Qualification | `/hr/driver-qualification` | `/api/hr/driver-qualification/*` | HR + Transportation |
| PPE / Asset Issuance (Asset Admin) | via Shop Hub V2 tiles | `/api/employee-records/*` (asset lane) | Shop / Asset Admin |

## Admin / integration / ops
- User + permission management (Admin portal)
- Email Routing Center (Admin)
- System Health (Admin)
- Backup / Restore / R2 surfaces (Admin)
- Feature-flag registry (via env / query param)
- Integration surfaces: Motive · FleetWatcher · MaintainX read-only ingestion points (`/api/integrations/*`)

## Guidance / help surfaces
- `/guidance`, `/guidance/section/:sectionId`, `/guidance/:articleId` — active but content-only.
- `/cheat-sheet`, `/cheatsheet` — legacy quick reference (both routes still mounted for compatibility).
- `AdminGuide.jsx`, `OpsTrainingGuide.jsx` — inline training pages under Admin.

## Legacy / deprecated (kept mounted for URL compatibility)
- `/hr/employee-accountability` — superseded by `/hr/employees/:id/profile` (Track 19.21). Both mounted.
- `Hub.jsx` (unversioned) — superseded by `HubV2.jsx` variants across portals. Both mounted.
- `AdminHub` vs `AdminHubV2` (Sidebar V2 feature-flag `?adminSidebarV2=1`).

**No unreachable active workflows detected.** Every route in `App.js` either terminates in a page component or a documented redirect.
