# WP16 Wave 5 — Authoritative Inventory & Operational Reconciliation

Date: 2026-07-30

## Executive scope statement

- Wave 5 scope: **Safety Certification**
- Phase authorized: **Inventory & Operational Reconciliation only**
- Production changes made: **None**
- Inspections performed: **None**
- Repairs performed: **None**
- Runtime testing performed: **None by executive instruction**

## Final denominator

- **Final Wave 5 denominator:** **52 Safety route-pattern experiences**
  - `40` route screens
  - `12` detail screens
- Denominator status: **authoritative pending Executive review**
- Identifier policy: **W5-001 … W5-052 assigned in this phase and treated as permanent**

## Sources reconciled

- `WP16_CERTIFICATION_REGISTER.csv` — authoritative route/register ledger synchronization
- `PRD.md` — executive dashboard synchronization
- `ROADMAP.md` — Wave 5 scope synchronization
- `WP16_PHASE_B_CONTROL.md` — supporting baseline and sequencing conflict evidence
- `frontend/src/app/routing/AppRoutes.jsx` — authoritative Safety route declarations and aliases
- `frontend/src/components/RequireSafety.jsx` — protected-route contract for `/safety-portal/*`
- `backend/routes/safety.py` — inspections / meetings / JHA / incidents CRUD family
- `backend/routes/safety_forms.py` — Safety forms API family
- `backend/routes/safety_exports.py` — Safety reports/export API family
- `backend/routes/safety_portal/*` — Safety portal operational API family
- `backend/routes/trench_safety/*` — Trench Safety operational API family
- `backend/routes/signatures.py` — shared signature capture API used by Safety workflows
- `backend/routes/incident_lifecycle.py` + `backend/incident_engine/*` — incident-case operational workflow APIs

## Taxonomy

- **Safety Forms & Equipment Accountability:** 8 experience(s)
- **Core Safety Reporting & Case Workflows:** 11 experience(s)
- **Trench Safety Public & Protected Operations:** 14 experience(s)
- **Safety Portal Operational Review:** 19 experience(s)

## Route hierarchy

### Safety Forms & Equipment Accountability
- `W5-001` · `/safety/forms/login` · Safety Forms Login · route_screen
- `W5-002` · `/safety/forms` · Safety Forms Hub · route_screen
- `W5-003` · `/safety/forms/equipment-issuance/new` · Equipment Issuance · route_screen
- `W5-004` · `/safety/forms/equipment-issuance/:id` · Equipment Issuance · detail_screen
- `W5-005` · `/safety/forms/equipment-issuance/:id/return` · Equipment Return · detail_screen
- `W5-006` · `/safety/forms/equipment-training/new` · Equipment Training · route_screen
- `W5-007` · `/safety/forms/equipment-training/:id` · Equipment Training · detail_screen
- `W5-008` · `/safety/cards` · Field Safety Cards · route_screen

### Core Safety Reporting & Case Workflows
- `W5-009` · `/safety/inspections/new` · Inspections · route_screen
- `W5-010` · `/meetings/new` · Safety Meetings · route_screen
- `W5-011` · `/meetings/submit` · Safety Meetings Public Submit · route_screen
- `W5-012` · `/jha` · JHA Plans · route_screen
- `W5-013` · `/incidents/report` · Incident Reporting · route_screen
- `W5-014` · `/near-miss` · Near Miss · route_screen
- `W5-015` · `/safety/cases/:caseId` · Safety Case Workspace · detail_screen
- `W5-016` · `/safety/incidents/:caseId/thread` · Incident Thread · detail_screen
- `W5-017` · `/safety/executive-intelligence` · Executive Intelligence · route_screen
- `W5-018` · `/safety/cases/:caseId/reports/:reportType` · Case Reports · detail_screen
- `W5-019` · `/safety/cases/:caseId/executive-report` · Executive Case Report · detail_screen

### Trench Safety Public & Protected Operations
- `W5-020` · `/trench-safety` · Public Trench Safety Dashboard · route_screen
- `W5-021` · `/trench-safety/tabulated-data` · Trench Tabulated Data · route_screen
- `W5-022` · `/trench-safety/references` · Trench References · route_screen
- `W5-023` · `/trench-safety/report` · Trench Report · route_screen
- `W5-024` · `/trench-safety/assets/:assetId` · Trench QR Asset · detail_screen
- `W5-025` · `/trench-safety/excavation/new` · Excavation Submission · route_screen
- `W5-026` · `/safety/trench-safety` · Safety Trench Hub · route_screen
- `W5-027` · `/safety/trench-safety/assets` · Trench Assets · route_screen
- `W5-028` · `/safety/trench-safety/assets/:assetId` · Trench Asset Detail · detail_screen
- `W5-029` · `/safety/trench-safety/tabulated-data` · Safety Trench Tabulated Data · route_screen
- `W5-030` · `/safety/trench-safety/reports` · Trench Reports · route_screen
- `W5-031` · `/safety/trench-safety/excavations` · Excavation Oversight · route_screen
- `W5-032` · `/safety/trench-safety/repair-review` · Repair Review · route_screen
- `W5-033` · `/safety/trench-safety/field-reports` · Field Reports · route_screen

### Safety Portal Operational Review
- `W5-034` · `/safety-portal/fleet` · Fleet Visibility · route_screen
- `W5-035` · `/safety-portal/corrective-actions` · Corrective Actions · route_screen
- `W5-036` · `/safety-portal/fire-extinguishers` · Fire Extinguishers · route_screen
- `W5-037` · `/safety-portal/fire-extinguishers/import` · Fire Extinguisher Import · route_screen
- `W5-038` · `/safety-portal/documents` · Safety Documents · route_screen
- `W5-039` · `/safety-portal/training` · Training Records · route_screen
- `W5-040` · `/safety-portal/incidents` · Safety Incidents · route_screen
- `W5-041` · `/safety-portal/incidents/:id` · Safety Incident Detail · detail_screen
- `W5-042` · `/safety-portal/meetings` · Safety Meetings · route_screen
- `W5-043` · `/safety-portal/meetings/:id` · Safety Meeting Detail · detail_screen
- `W5-044` · `/safety-portal/audits` · Safety Audits · route_screen
- `W5-045` · `/safety-portal/forms-records` · Forms Records · route_screen
- `W5-046` · `/safety-portal/reports` · Safety Reports · route_screen
- `W5-047` · `/safety-portal/library` · Topic Library · route_screen
- `W5-048` · `/safety-portal/employees` · Employee Safety Profiles · route_screen
- `W5-049` · `/safety-portal/digest` · Safety Digest · route_screen
- `W5-050` · `/safety-portal/inspections` · Safety Inspections · route_screen
- `W5-051` · `/safety-portal/inspections/:id` · Safety Inspection Detail · detail_screen
- `W5-052` · `/safety-portal/jha-plans` · JHA Plans · route_screen

## Complete inventory

| W5 ID | Route | Experience Name | Parent Domain | Hidden / Public | CRUD | API Dependencies | Permission Requirements | Criticality |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| W5-001 | `/safety/forms/login` | Safety Forms Login | Safety Forms & Equipment Accountability | Public | Create session | `/api/safety-forms/login`; `/api/safety-forms/check` | Public route; Safety Forms password gate via `X-Safety-Forms-Token` after login | B |
| W5-002 | `/safety/forms` | Safety Forms Hub | Safety Forms & Equipment Accountability | Public hub | Read / navigate | `/api/safety-forms/check`; `/api/safety-forms/equipment-issuances*`; `/api/safety-forms/equipment-trainings*` | Safety Forms password / token workflow | B |
| W5-003 | `/safety/forms/equipment-issuance/new` | Equipment Issuance | Safety Forms & Equipment Accountability | Public form | Create | `/api/safety-forms/equipment-issuances`; `/api/signatures` | Safety Forms password / token workflow | B |
| W5-004 | `/safety/forms/equipment-issuance/:id` | Equipment Issuance | Safety Forms & Equipment Accountability | Hidden detail | Read / print | `/api/safety-forms/equipment-issuances/{id}`; `/api/safety-forms/equipment-issuances/{id}/pdf` | Safety Forms password / token workflow; admin backend read also supported | B |
| W5-005 | `/safety/forms/equipment-issuance/:id/return` | Equipment Return | Safety Forms & Equipment Accountability | Hidden detail | Create return | `/api/safety-forms/equipment-issuances/{id}/return`; `/api/safety-forms/equipment-issuances/{id}/return/pdf`; `/api/signatures` | Safety Forms password / token workflow | B |
| W5-006 | `/safety/forms/equipment-training/new` | Equipment Training | Safety Forms & Equipment Accountability | Public form | Create | `/api/safety-forms/equipment-trainings`; `/api/signatures` | Safety Forms password / token workflow | B |
| W5-007 | `/safety/forms/equipment-training/:id` | Equipment Training | Safety Forms & Equipment Accountability | Hidden detail | Read / print | `/api/safety-forms/equipment-trainings/{id}`; `/api/safety-forms/equipment-trainings/{id}/pdf` | Safety Forms password / token workflow; admin backend read also supported | B |
| W5-008 | `/safety/cards` | Field Safety Cards | Safety Forms & Equipment Accountability | Public | Read / print | Static/public card assets | Public | B |
| W5-009 | `/safety/inspections/new` | Inspections | Core Safety Reporting & Case Workflows | Protected | Create | `/api/inspections`; `/api/signatures` | `RequireSafety`; `X-Safety-Token` or admin write gate backend-side | A |
| W5-010 | `/meetings/new` | Safety Meetings | Core Safety Reporting & Case Workflows | Public | Create | `/api/meetings`; `/api/signatures` | Public route; backend public submit with rate limit | B |
| W5-011 | `/meetings/submit` | Safety Meetings Public Submit | Core Safety Reporting & Case Workflows | Public | Create | `/api/meetings`; `/api/signatures` | Public route; backend public submit with rate limit | B |
| W5-012 | `/jha` | JHA Plans | Core Safety Reporting & Case Workflows | Public | Create / read | `/api/jhas`; JHA plan file helpers | Public route; backend public submit with rate limit | B |
| W5-013 | `/incidents/report` | Incident Reporting | Core Safety Reporting & Case Workflows | Public | Create | `/api/incidents`; `/api/signatures`; `/api/incident-cases/legacy/{incident_id}` bridge | Public route; backend public submit with rate limit | A |
| W5-014 | `/near-miss` | Near Miss | Core Safety Reporting & Case Workflows | Public | Create | `/api/incidents`; `/api/signatures` | Public route; backend public submit with rate limit | A |
| W5-015 | `/safety/cases/:caseId` | Safety Case Workspace | Core Safety Reporting & Case Workflows | Hidden detail | Read / update case workflow | `/api/incident-cases/*`; `/api/corrective-actions*`; `/api/incidents/{id}/lifecycle`; `/api/incidents/{id}/state-events` | No React guard on route; backend APIs require Safety/Admin/PM token | A |
| W5-016 | `/safety/incidents/:caseId/thread` | Incident Thread | Core Safety Reporting & Case Workflows | Hidden detail | Read / thread review | `/api/incident-cases/{id}/timeline`; `/api/incident-cases/{id}/audit`; `/api/incident-cases/{id}/communications` | No React guard on route; backend APIs require Safety/Admin/PM token | A |
| W5-017 | `/safety/executive-intelligence` | Executive Intelligence | Core Safety Reporting & Case Workflows | Hidden / linked | Read / review | `/api/incident-cases/{id}/executive-intelligence`; `/api/incident-intelligence/corrective-actions` | No React guard on route; backend APIs require Safety/Admin/PM token | B |
| W5-018 | `/safety/cases/:caseId/reports/:reportType` | Case Reports | Core Safety Reporting & Case Workflows | Hidden detail | Read / export | `/api/incident-cases/{id}/reports/{type}`; `/api/incident-cases/{id}/reports/{type}.pdf` | No React guard on route; backend APIs require Safety/Admin/PM token | B |
| W5-019 | `/safety/cases/:caseId/executive-report` | Executive Case Report | Core Safety Reporting & Case Workflows | Hidden detail | Read / export | `/api/incident-cases/{id}/executive-report.pdf`; `/api/incident-cases/{id}/presence-score` | No React guard on route; backend APIs require Safety/Admin/PM token | B |
| W5-020 | `/trench-safety` | Public Trench Safety Dashboard | Trench Safety Public & Protected Operations | Public | Read | `/api/trench-safety/public/overview`; `/api/trench-safety/alerts`; `/api/trench-boxes` | Public route | A |
| W5-021 | `/trench-safety/tabulated-data` | Trench Tabulated Data | Trench Safety Public & Protected Operations | Public | Read | `/api/trench-boxes`; `/api/trench-box-files`; `/api/trench-box-files/by-box/{box_id}` | Public route | A |
| W5-022 | `/trench-safety/references` | Trench References | Trench Safety Public & Protected Operations | Public | Read | Static/public trench reference content; tabulated-data references | Public route | B |
| W5-023 | `/trench-safety/report` | Trench Report | Trench Safety Public & Protected Operations | Public | Read / report view | `/api/trench-safety/reports/*`; `/api/trench-safety/reports/digest/*` | Public route | B |
| W5-024 | `/trench-safety/assets/:assetId` | Trench QR Asset | Trench Safety Public & Protected Operations | Hidden detail | Read / upload field photos | `/api/trench-safety/public/assets/{assetId}`; `/api/trench-safety/public/assets/{assetId}/photos` | Public route | A |
| W5-025 | `/trench-safety/excavation/new` | Excavation Submission | Trench Safety Public & Protected Operations | Public | Create | `/api/trench-safety/excavations/public/submit`; `/api/trench-safety/excavations/public/asset-roster` | Public route | A |
| W5-026 | `/safety/trench-safety` | Safety Trench Hub | Trench Safety Public & Protected Operations | Protected | Read / operate | `/api/trench-safety/dashboard`; `/api/trench-safety/alerts`; `/api/trench-safety/assets*` | `RequireSafety`; `X-Safety-Token` | A |
| W5-027 | `/safety/trench-safety/assets` | Trench Assets | Trench Safety Public & Protected Operations | Protected | Create / read / update | `/api/trench-safety/assets*`; `/api/trench-safety/assets/import*`; `/api/trench-safety/assets/{id}/audit` | `RequireSafety`; `X-Safety-Token` or admin | A |
| W5-028 | `/safety/trench-safety/assets/:assetId` | Trench Asset Detail | Trench Safety Public & Protected Operations | Hidden detail (protected) | Read / update status / media | `/api/trench-safety/assets/{id}`; `/api/trench-safety/assets/{id}/status`; `/api/trench-safety/assets/{id}/retire`; `/api/trench-safety/assets/{id}/photos`; QR label endpoints | `RequireSafety`; `X-Safety-Token` or admin | A |
| W5-029 | `/safety/trench-safety/tabulated-data` | Safety Trench Tabulated Data | Trench Safety Public & Protected Operations | Protected | Read / upload reference files | `/api/trench-boxes*`; `/api/trench-box-files*` | `RequireSafety`; `X-Safety-Token` or admin for writes | A |
| W5-030 | `/safety/trench-safety/reports` | Trench Reports | Trench Safety Public & Protected Operations | Protected | Read / export / distribute | `/api/trench-safety/reports/*`; `/api/trench-safety/reports/presets*`; `/api/trench-safety/reports/subscriptions*`; `/api/trench-safety/pulse*` | `RequireSafety`; `X-Safety-Token` or admin | B |
| W5-031 | `/safety/trench-safety/excavations` | Excavation Oversight | Trench Safety Public & Protected Operations | Protected | Read / review / transition | `/api/trench-safety/excavations*`; `/api/trench-safety/excavations/reinspection-queue`; `/api/trench-safety/excavations/reports/summary` | `RequireSafety`; `X-Safety-Token` or admin | A |
| W5-032 | `/safety/trench-safety/repair-review` | Repair Review | Trench Safety Public & Protected Operations | Protected | Read / verify repairs | `/api/trench-safety/repairs*`; `/api/trench-safety/shop/repairs` | `RequireSafety`; `X-Safety-Token` or admin | A |
| W5-033 | `/safety/trench-safety/field-reports` | Field Reports | Trench Safety Public & Protected Operations | Protected | Read / triage / follow up | `/api/trench-safety/inspections*`; `/api/trench-safety/deployments*`; `/api/trench-safety/holds*`; `/api/trench-safety/certifications*` | `RequireSafety`; `X-Safety-Token` or admin | A |
| W5-034 | `/safety-portal/fleet` | Fleet Visibility | Safety Portal Operational Review | Protected | Read | Fleet visibility APIs under shared fleet routes | `RequireSafety`; `X-Safety-Token` | C |
| W5-035 | `/safety-portal/corrective-actions` | Corrective Actions | Safety Portal Operational Review | Protected | Create / read / update / delete | `/api/safety/corrective-actions*`; `/api/corrective-actions*`; `/api/signatures` | `RequireSafety`; `X-Safety-Token` | B |
| W5-036 | `/safety-portal/fire-extinguishers` | Fire Extinguishers | Safety Portal Operational Review | Protected | Create / read / update / inspect / delete | `/api/safety/fire-extinguishers*`; attachment/history PDF endpoints | `RequireSafety`; `X-Safety-Token` | A |
| W5-037 | `/safety-portal/fire-extinguishers/import` | Fire Extinguisher Import | Safety Portal Operational Review | Protected | Import / create | `/api/safety/fire-extinguishers`; bulk import helper router | `RequireSafety`; `X-Safety-Token` | B |
| W5-038 | `/safety-portal/documents` | Safety Documents | Safety Portal Operational Review | Protected | Create / read / update / download / delete | `/api/safety/documents*`; `/api/safety/exports/documents` | `RequireSafety`; `X-Safety-Token`; HR/Admin read gate exists backend-side for some APIs | B |
| W5-039 | `/safety-portal/training` | Training Records | Safety Portal Operational Review | Protected | Create / read / update / delete | `/api/safety/training-records*`; `/api/safety/employee-profile/{employee_id}` | `RequireSafety`; `X-Safety-Token`; HR/Admin read gate exists backend-side for some APIs | B |
| W5-040 | `/safety-portal/incidents` | Safety Incidents | Safety Portal Operational Review | Protected | Read / filter / export | `/api/incidents`; `/api/incidents.csv`; `/api/incidents/{id}/lifecycle` | `RequireSafety`; `X-Safety-Token` (backend read gate also accepts Admin/PM) | A |
| W5-041 | `/safety-portal/incidents/:id` | Safety Incident Detail | Safety Portal Operational Review | Hidden detail (protected) | Read | `/api/incidents/{id}`; `/api/incidents/{id}/state-events`; `/api/incidents/{id}/lifecycle` | `RequireSafety`; `X-Safety-Token` | A |
| W5-042 | `/safety-portal/meetings` | Safety Meetings | Safety Portal Operational Review | Protected | Read / filter | `/api/meetings`; `/api/safety/exports/project-safety` | `RequireSafety`; `X-Safety-Token` (backend read gate also accepts Admin/PM) | B |
| W5-043 | `/safety-portal/meetings/:id` | Safety Meeting Detail | Safety Portal Operational Review | Hidden detail (protected) | Read | `/api/meetings/{id}` | `RequireSafety`; `X-Safety-Token` | B |
| W5-044 | `/safety-portal/audits` | Safety Audits | Safety Portal Operational Review | Protected | Read / filter | `/api/inspections`; `/api/safety/exports/inspections` | `RequireSafety`; `X-Safety-Token` | A |
| W5-045 | `/safety-portal/forms-records` | Forms Records | Safety Portal Operational Review | Protected | Read / filter | `/api/safety-forms/equipment-issuances`; `/api/safety-forms/equipment-trainings` | `RequireSafety`; page is Safety-guarded while backend records are Safety Forms token/admin scoped | B |
| W5-046 | `/safety-portal/reports` | Safety Reports | Safety Portal Operational Review | Protected | Read / export | `/api/safety/exports/*`; trench safety report/distribution APIs | `RequireSafety`; `X-Safety-Token` | C |
| W5-047 | `/safety-portal/library` | Topic Library | Safety Portal Operational Review | Protected | Read / generate pack | `/api/safety/library/pack` | `RequireSafety`; backend pack generation accepts Safety/Admin | B |
| W5-048 | `/safety-portal/employees` | Employee Safety Profiles | Safety Portal Operational Review | Protected | Read / filter / export | `/api/safety/employee-profile/{employee_id}`; `/api/safety/exports/employee-profiles`; `/api/safety/exports/training-records` | `RequireSafety`; `X-Safety-Token`; HR/Admin read gate exists backend-side for some APIs | B |
| W5-049 | `/safety-portal/digest` | Safety Digest | Safety Portal Operational Review | Protected | Read / send | `/api/safety/digest/preview`; `/api/safety/digest/send` | `RequireSafety`; `X-Safety-Token` | C |
| W5-050 | `/safety-portal/inspections` | Safety Inspections | Safety Portal Operational Review | Protected | Read / filter | `/api/inspections`; `/api/safety/exports/inspections` | `RequireSafety`; `X-Safety-Token` (backend read gate also accepts Admin/PM) | A |
| W5-051 | `/safety-portal/inspections/:id` | Safety Inspection Detail | Safety Portal Operational Review | Hidden detail (protected) | Read | `/api/inspections/{id}` | `RequireSafety`; `X-Safety-Token` | A |
| W5-052 | `/safety-portal/jha-plans` | JHA Plans | Safety Portal Operational Review | Protected | Read / filter | `/api/jhas`; JHA acknowledgement/file helpers | `RequireSafety`; `X-Safety-Token` (backend read gate also accepts Admin/PM) | B |

## Operational API inventory

| API Family | Endpoint patterns reconciled | Access posture | Primary workflow owner |
| --- | --- | --- | --- |
| Safety portal auth | `/api/safety/login`; `/api/safety/me`; `/api/safety/change-password`; `/api/safety/forgot-password`; `/api/safety/reset-password`; `/api/admin/safety-users*` | Public auth entry plus Safety/Admin management | Safety portal access & user administration |
| Safety portal overview | `/api/safety/overview`; `/api/admin/safety/overview` | Safety token / admin | Safety hub KPI roll-up |
| Safety portal corrective actions | `/api/safety/corrective-actions`; `/api/safety/corrective-actions/{id}`; `/links`; `/related-resolved`; delete | Safety token | CAPA management |
| Safety portal daily mirror | `/api/safety/daily-reports` | Safety token | Safety review of daily reports |
| Safety fire extinguishers | `/api/safety/fire-extinguishers*`; `/attachments*`; `/history.pdf` | Safety token | Extinguisher register / inspections |
| Safety documents | `/api/safety/documents*`; `/download` | Safety token; HR/Admin read on selected surfaces | Safety document library |
| Safety training | `/api/safety/training-records*`; `/api/safety/employee-profile/{employee_id}` | Safety token; HR/Admin read on selected surfaces | Training & employee safety profile |
| Safety digest | `/api/safety/digest/preview`; `/api/safety/digest/send` | Safety token | Safety digest generation |
| Safety exports | `/api/safety/exports/incidents`; `/corrective-actions`; `/inspections`; `/training-records`; `/training-expired`; `/fire-extinguishers`; `/employee-profiles`; `/documents`; `/project-safety`; `/executive` | Safety / HR / Admin read gate | Safety reports & exports |
| Safety forms | `/api/safety-forms/login`; `/check`; `/equipment-issuances*`; `/equipment-trainings*`; return and PDF variants | Safety Forms token; admin read support | Equipment issuance / return / training records |
| Core inspections CRUD | `/api/inspections`; `/api/inspections/{id}`; delete | Safety/Admin write; Safety/Admin/PM read | Site inspections |
| Core meetings CRUD | `/api/meetings`; `/api/meetings/{id}`; delete | Public submit; Safety/Admin/PM read | Safety meetings |
| Core JHA CRUD | `/api/jhas`; `/api/jhas/{id}`; delete | Public submit; Safety/Admin/PM read | JHA workflow |
| Core incidents CRUD | `/api/incidents`; `/api/incidents/{id}`; `/api/incidents.csv`; delete | Public submit; Safety/Admin/PM read; admin delete | Incident reporting |
| Incident lifecycle | `/api/incidents/{id}/transition`; `/state-events`; `/lifecycle` | Safety/Admin/PM read gate with role-specific transition enforcement | Incident state machine |
| Incident engine core | `/api/incident-cases/vocabulary`; `/api/incident-cases`; `/api/incident-cases/{id}`; field-block; safety-block; transitions; timeline; audit; evidence; cross-links; executive-review; `/api/corrective-actions*` | Safety/Admin/PM gate | Safety case workspace |
| Incident engine workspace | `/api/incident-cases/{id}/communications`; `/witnesses`; `/medical`; `/agency-contacts`; `/tasks`; `/health`; `/executive-snapshot` | Safety/Admin/PM gate | Incident case assembly |
| Incident intelligence / reports | `/api/incident-intelligence/corrective-actions`; `/api/incident-cases/{id}/presence-score`; `/reports/{type}`; `/reports/{type}.pdf`; `/executive-intelligence`; `/executive-report.pdf` | Safety/Admin/PM gate | Executive incident reporting |
| Legacy trench-box library | `/api/trench-boxes*`; `/api/trench-box-files*` | Public read; Safety/Admin write on mutable endpoints | Tabulated-data reference library |
| Trench safety assets | `/api/trench-safety/assets*`; `/assets/import*`; `/assets/{id}/audit`; QR label and photo endpoints | Any-portal read; Safety/Admin write; Shop/Admin on photo/repair-adjacent paths | Trench asset registry |
| Trench safety dashboard / operations | `/api/trench-safety/dashboard`; `/alerts`; `/by-project`; `/operations/picker` | Any-portal read | Trench operational overview |
| Trench safety inspections / deployments | `/api/trench-safety/inspections*`; `/api/trench-safety/deployments*` | Any-portal read; Safety/Admin workflow ownership | Field inspection & deployment chain |
| Trench safety repairs / holds / certifications | `/api/trench-safety/repairs*`; `/shop/repairs`; `/holds*`; `/certifications*` | Mixed Safety/Admin and Shop/Admin gates | Repair / hold / certification workflows |
| Trench safety excavations | `/api/trench-safety/excavations*`; `/public/asset-roster`; `/public/submit`; `/reports/summary` | Public submit plus Safety/Admin oversight | Excavation oversight |
| Trench safety reports / distribution / pulse | `/api/trench-safety/reports/*`; presets; subscriptions; digest; `/api/trench-safety/pulse*` | Safety/Admin write; any-portal read on selected rollups | Trench reporting and scheduled distribution |
| Competent persons | `/api/admin/employees/{employee_id}/cp-designation` | Admin / Safety-admin support path | Competent-person designation |
| Safety topic library | `/api/safety/library/pack` | Safety/Admin | Topic pack PDF generation |
| Shared signatures | `/api/signatures` GET/POST | Any portal token | Signature capture shared across Safety workflows |
| Safety trench intelligence | `/api/safety/company/trench-safety-kpis`; `/api/safety/company/trench-safety-cleanup`; `/api/safety/projects/{project_number}/trench-safety-kpis` | Safety/Admin company-wide; PM project-scoped | Safety trench intelligence |

## Completeness reconciliation findings

1. **Executive sequencing override documented.** `WP16_PHASE_B_CONTROL.md` still lists Safety as **Wave 6** with a planned denominator of `52`. Executive authorization for this checkpoint explicitly moved Safety inventory work into **Wave 5**. This package adopts the Executive instruction, preserves the `52`-experience denominator, and records the conflict without altering production code.
2. **Canonical Wave 5 denominator established at 52.** The final denominator intentionally counts Safety-owned canonical routes only and excludes duplicate aliases already covered by their canonical parents.
3. **Earlier-wave Safety entry surfaces were excluded, not lost.** The following active routes remain outside the Wave 5 denominator because they are already owned by prior waves: `/safety` (Wave 2), `/safety-portal/login` (Wave 1), `/safety-portal/forgot-password` (Wave 1), `/safety-portal/reset/:token` (Wave 1), `/safety-portal/change-password` (Wave 1), `/safety-portal` (Wave 2), `/safety-portal/hub_legacy` (Wave 2), `/safety-portal/hub_v2` (Wave 2).
4. **Canonical redirect aliases were documented but not double-counted.** Excluded alias-only routes: `/jha/submit`, `/jha/new`, `/trench-boxes`, `/incidents/new`, `/incidents/submit`, `/safety/jha`, `/safety/trench-boxes`, `/safety-portal/trench-safety`, `/safety-portal/trench-safety/assets`, `/safety-portal/trench-safety/tabulated-data`.
5. **Cross-wave mirror routes were reconciled and intentionally excluded from the Safety denominator.** Admin Safety mirrors (`/admin/incidents*`, `/admin/meetings*`, `/admin/jha-plans*`, `/admin/trench-safety*`, `/admin/safety/*`) remain owned by **Wave 3 — Admin**. PM Safety mirrors (`/pm/incidents*`, `/pm/meetings*`, `/pm/jha-plans`, `/pm/trench-safety*`) remain owned by the existing **Wave 5 — Project Management** ledger rows. They are dependencies, not duplicate Wave 5 Safety denominator items.
6. **Shared Driver Command Profile route remains adjacent, not absorbed.** `/safety-portal/driver/:driverKey` is a Safety-shell rendering of a shared driver profile workflow and is therefore documented as an external/shared dependency rather than counted as a Safety-owned denominator item.
7. **Protected-route mapping reconciled.** The Wave 5 denominator contains **28 React-guarded routes** (`RequireSafety`) and **24 public or runtime-authenticated routes**. Notably, the incident-case workspace family (`/safety/cases/*`, `/safety/incidents/*thread`, `/safety/executive-intelligence`) is not guarded at the React router level and instead relies on backend token enforcement.
8. **Operational API census complete.** All Safety API families referenced by this wave were reconciled across `routes/safety.py`, `routes/safety_forms.py`, `routes/safety_exports.py`, `routes/safety_portal/*`, `routes/trench_safety/*`, `routes/signatures.py`, and the incident engine / lifecycle modules.
9. **No production-code drift occurred.** This package records inventory truth only. No route, guard, component, or backend behavior was changed.

## Evidence

- `AppRoutes.jsx` lines `520–675` — Safety forms, public safety, trench safety, incident, and protected trench workflows
- `AppRoutes.jsx` lines `1103–1252` — Safety portal routes and protected operational review surfaces
- `RequireSafety.jsx` lines `1–49` — Safety portal route guard contract
- `safety.py` lines `434–1509` — inspections / meetings / JHA / incidents CRUD registration
- `safety_forms.py` lines `982–1452` — Safety forms API registration
- `safety_exports.py` lines `99–307` — Safety export/report endpoints
- `safety_portal/__init__.py` lines `36–86` — Safety portal router assembly
- `safety_portal/_deps.py` lines `14–235` — Safety token and cross-role read/write gates
- `trench_safety/__init__.py` lines `47–152` — Trench Safety router assembly
- `signatures.py` lines `158–205` — shared signature endpoints
- `incident_lifecycle.py` lines `57–273` — incident transition/state-event/lifecycle APIs
- `WP16_PHASE_B_CONTROL.md` lines `25–49` — supporting baseline and Wave 6 / 52-screen conflict evidence

## Wave 5 Executive Inventory Package

- Final denominator: **52**
- Total Safety experiences: **52**
- Reconciliation findings: **9** documented above
- Missing experiences: **0** within the adopted Safety-owned canonical denominator
- Duplicate experiences in denominator: **0**
- Recommended inspection scope: inspect all 52 Wave 5 Safety experiences, prioritizing (1) life-safety trench routes, (2) incident-case workspace / transition flows, (3) Safety Forms accountability flows, and (4) Safety portal corrective-action / extinguisher / document workflows
- Executive readiness assessment: denominator reconciled, IDs assigned, API families inventoried, register synchronized, PRD synchronized, ROADMAP synchronized, control-file sequencing conflict explicitly documented

**READY FOR WAVE 5 INSPECTION AUTHORIZATION**