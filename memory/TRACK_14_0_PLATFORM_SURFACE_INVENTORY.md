# MASCI Platform · Surface Inventory (Track 14.0-PLATFORM-TRUTH-MAP)

**Audit date:** 2026-02-12 · **Mode:** READ-ONLY · **Scope:** every operator-facing surface (screens, lists, forms, reports, modals) grouped by portal, scored against `MASCI_DEFINITION_OF_DONE.md`.

Companion to:
- `TRACK_14_0_PLATFORM_TRUTH_MAP_ROUTE_NAV_SURFACE_INVENTORY.md` (executive truth map)
- `TRACK_14_0_PLATFORM_NAVIGATION_MATRIX.md` (navigation elements)
- `TRACK_14_0_PLATFORM_ROUTE_INVENTORY.json` (341 routes, machine-readable)

---

## Methodology

A **surface** = anything an operator can interact with: dashboard, list page, form, report, modal, drawer, detail page, settings screen, public form, review screen, approval screen, notification drawer, help/guidance screen.

Each surface gets a Definition-of-Done state per `MASCI_DEFINITION_OF_DONE.md`:

- **0 NOT STARTED** · no usable work
- **1 BUILT** · code exists, no visible navigation
- **2 WIRED** · route + visible link, workflow unproven
- **3 OPERATIONAL** · workflow proven end-to-end
- **4 DONE-DONE** · operational + tested + audited + notifications + leakage-clean + iPad/desktop proven

Evidence required to claim each level is in the canonical Definition document.

---

## Public surfaces (79 routes)

| Surface | Route | Primary role | State | Notes |
|---------|-------|---------------|:------:|-------|
| Public Hub | `/` | crew/visitor | 4 DONE-DONE | Landing page · stable |
| Multi-portal Sign In | `/sign-in` | any | 4 DONE-DONE | Phase 2B-2A verified |
| Daily Report (public) | `/daily/new` · `/daily/submit` | crew | 4 DONE-DONE | Phase 2B-2A embedded snapshot |
| Incident (public) | `/incidents/new` · `/incidents/submit` | crew | 4 DONE-DONE | Phase 2B-2A + 2B-2B wired |
| Site Inspection (public) | `/safety/inspections/new` · 3 legacy aliases | crew | 4 DONE-DONE | Phase 2B-2B wired |
| Safety Meeting (public) | `/meetings/new` · `/meetings/submit` | crew | 4 DONE-DONE | Phase 2B-2B wired |
| JHA (public) | `/jha` · `/jha/submit` · `/jha/new` | crew | 4 DONE-DONE | Phase 2B-2B wired |
| Equipment Pre-Op (public) | `/equipment/new` · `/equipment/submit` | operator | 4 DONE-DONE | Phase 2B-2B wired |
| Fleet DVIR (public) | `/fleet/dvir/new` · `/fleet/dvir/submit` · weekly-lead · weekly-emergency | driver | 3 OPERATIONAL | DVIR shares Pre-Op writer (Phase 2B-2B note) |
| Trench Safety dashboard (public) | `/trench-safety` | crew/super | 3 OPERATIONAL | Phase 2B-2A excavations wired |
| Trench Safety QR landing | `/trench-safety/assets/:assetId` | crew | 3 OPERATIONAL | Phase 2B-2B reinspection wired |
| Trench Tabulated Data / References / Report | `/trench-safety/tabulated-data` · `/references` · `/report` | crew/safety | 3 OPERATIONAL | — |
| Public Trench Excavation Form | `/trench-safety/excavation/new` | crew | 4 DONE-DONE | Phase 2B-2A embedded snapshot |
| QA/QC inspection (public) | `/qaqc` · `/qaqc/:slug/new` · `/qaqc/:id` | qaqc/super | 4 DONE-DONE | Phase 2B-2A + 2B-2B wired |
| Field Leadership Hub (public) | `/leadership` | super/foreman | 3 OPERATIONAL | Phase 2B-1 widget |
| Field Leadership form | `/leadership/:kind/new` | super/foreman | 3 OPERATIONAL | — |
| Field Safety Cards | `/safety/cards` | crew | 3 OPERATIONAL | — |
| Material Calculators | `/field/calculators` | crew | 3 OPERATIONAL | — |
| Constraints (public) | `/constraints` · `/constraints/new` · `/constraints/:id` | super | 2 WIRED | Workflow exists but discoverability ≤ 2 |
| Asset Transfers (semi-public) | `/asset-transfers` | dispatch/asset-admin | 2 WIRED | No PM card surfaces this |
| Document Expirations | `/document-expirations` | asset-admin | 2 WIRED | No card |
| Project Health | `/project-health` | PM/exec | 2 WIRED | No card |
| Operational Records | `/operational-records` | admin/QA | 1 BUILT | No visible nav |
| Operations Actions | `/operations-actions` · `/new` · `/:id` | admin | 1 BUILT | No visible nav |
| Operations Center Command | `/operations-center` | exec | 2 WIRED | Discoverable via admin sidebar (`/admin/operations-dashboard`) |
| Operations Map | `/operations-map` | exec | 2 WIRED | Same |
| PO Requests | `/po-requests` | super | 1 BUILT | No visible nav from any portal |
| Tasks | `/tasks` | any | 3 OPERATIONAL | Bell drawer → tasks |
| Notifications Digest | `/notifications` | any | 3 OPERATIONAL | Linked from bell |
| Operational Guidance Center | `/guidance` · `/guidance/section/:id` · `/guidance/:id` | any | 2 WIRED | No prominent card |
| Training Hub | `/training` · `/training/:track` · poster · packet | crew | 3 OPERATIONAL | Linked from public hub |
| ODR (Owner Daily Report) | `/odr/new` · `/odr/center` · `/odr/public/:id` · `/odr/:id` · `/odr/:id/done` · `/pm/odr` | PM/super | 2 WIRED | New flow; discoverability not yet certified |
| Driver Shift / Magic Landing | `/driver` · `/shift` · `/d/:token` | driver | 3 OPERATIONAL | Magic-link flow |
| Public Time-Off | `/time-off/public/:token` | employee | 3 OPERATIONAL | Magic-link flow |
| Cheat Sheet / Poster surfaces | `/cheatsheet` · `/admin/trench-boxes/poster` · `/admin/jha-plans/poster` · `/admin/posters/print-all` | super | 3 OPERATIONAL | — |
| Legal | `/legal/terms` · `/legal/privacy` | any | 4 DONE-DONE | Static |
| Access Denied | `/access-denied` | any | 4 DONE-DONE | Guard fallback |
| Thank You | `/thank-you` | any | 4 DONE-DONE | Post-submit landing |
| 404 NotFound | `*` | any | 4 DONE-DONE | Default route |

---

## Admin Portal surfaces (57+ routes guarded · 6 unguarded admin paths)

| Surface | Route | State | Notes |
|---------|-------|:------:|-------|
| Admin Hub (legacy) | `/admin` → `AdminHub` | 3 OPERATIONAL | — |
| Admin Hub V2 | `/admin/hub_v2` → `AdminHubV2` | 4 DONE-DONE | Baseline shell + sidebar |
| Admin Command Center | `/admin/command-center` | 3 OPERATIONAL | — |
| Admin People (users + temp pw) | `/admin/people` | 4 DONE-DONE | Canonical invite/temp-password flow |
| Admin Jobs (project master) | `/admin/jobs` | 4 DONE-DONE | Phase 1 audit trail |
| Admin Job Team Mgmt | `/admin/jobs/:projectNumber/team` | 4 DONE-DONE | Phase 1 + 2A · 13 roles |
| Admin Equipment | `/admin/equipment` · `/admin/equipment/:id/history` · `/admin/equipment-inspections` · `/admin/equipment/:id` | 4 DONE-DONE | Phase 2B-2B Pre-Op wired |
| Admin Daily | `/admin/daily` · `/admin/daily/:id` | 4 DONE-DONE | — |
| Admin Inspections | `/admin/inspections` · `/admin/inspections/:id` | 4 DONE-DONE | Phase 2B-2B wired |
| Admin Meetings | `/admin/meetings` · `/admin/meetings/:id` | 4 DONE-DONE | Phase 2B-2B wired |
| Admin Incidents | `/admin/incidents` · `/admin/incidents/:id` | 4 DONE-DONE | Phase 2B-2B wired |
| Admin QA/QC | `/admin/qaqc` · `/admin/qaqc/:id` | 4 DONE-DONE | Phase 2B-2B wired |
| Admin JHA Plans · Acks · Posters | `/admin/jha-plans` · `/admin/jha-acknowledgements` · `/admin/jha-plans/poster` | 4 DONE-DONE | — |
| Admin Trench Boxes / Trench Safety | `/admin/trench-boxes` · `/admin/trench-safety/*` (7 routes) | 4 DONE-DONE | — |
| Admin Operations Dashboard / Events | `/admin/operations-dashboard` · `/admin/operations-events` | 3 OPERATIONAL | — |
| Admin Dispatch (admin view) | `/admin/dispatch` | 3 OPERATIONAL | — |
| Admin Sessions · Audit Log | `/admin/sessions` · `/admin/audit-log` | 4 DONE-DONE | — |
| Admin System Health · Scheduler Runs · Recovery Stream | `/admin/system-health` · `/admin/scheduler-runs` · `/admin/recovery-stream` · `/admin/recovery` | 3 OPERATIONAL | — |
| Admin Integration Center · Email · MFA · Database | `/admin/integrations` · `/admin/email` · `/admin/mfa` · `/admin/database` | 3 OPERATIONAL | I1 banner work is downstream |
| Admin Compliance · Findings · Self-Protection | `/admin/compliance` · `/admin/compliance-findings` · `/admin/governance/self-protection` | 3 OPERATIONAL | — |
| Admin Driver Intel | `/admin/driver-intel/:driverKey` | 3 OPERATIONAL | — |
| Admin Asset Mapping · Spine · Profile · AssetAdmin | `/admin/asset-mapping` · `/admin/asset-spine` · `/admin/assets/:id` · `/admin/asset-admin` | 3 OPERATIONAL | — |
| Admin Geofence Reconciliation | `/admin/geofence-reconciliation` | 3 OPERATIONAL | — |
| Admin Legacy Imports · Promo Assets · DLS surfaces (Day-1, Week-1, Shift QR) | varies | 3 OPERATIONAL | — |
| Admin Project Identity / Governance / Operational Language | `/admin/project-identity` · `/admin/governance` · `/admin/operational-language` | 3 OPERATIONAL | — |
| Admin Guidance Coverage · Material Ledger Quality · Compliance Findings · Operational Inventory | varies | 3 OPERATIONAL | — |
| Admin Terminations · Field Leadership Equipment · Analytics · Guide | varies | 3 OPERATIONAL | — |
| Admin Training · Training Videos · Deploy Readiness · Deploy Recovery | varies | 3 OPERATIONAL | — |
| Admin Master History | `/admin/equipment/:id/history` · `/admin/employees/:id/history` | 3 OPERATIONAL | — |
| Admin Profile · Change Password · Login | varies | 4 DONE-DONE | — |
| Admin PnL | `/admin/pnl` | 3 OPERATIONAL | Guarded AP (admin+PM) |
| Admin Photos Library | `/admin/photos` | 3 OPERATIONAL | — |

---

## PM Portal surfaces (18 PM-guarded + ADMIN/PM-shared subset)

| Surface | Route | State | Notes |
|---------|-------|:------:|-------|
| PM Hub V2 (landing) | `/pm` → `/pm/hub` → `PmHubV2` | 3 OPERATIONAL | **No sidebar shell** — discoverability gap (RC1-NAV-001) |
| PM Hub legacy | `/pm/hub_legacy` → `PmHub` | 3 OPERATIONAL | Has PmShell sidebar |
| PM Command Center | `/pm/command-center` | 4 DONE-DONE (post-RC1-FIX-SWEEP) | Dispatch link removed; Project Roster fixed |
| PM Jobs | `/pm/jobs` | 4 DONE-DONE (post-RC1-FIX-SWEEP) | 28 jobs, per-row Team link |
| PM Job Team Management | `/pm/job/:projectNumber/team` | 4 DONE-DONE | Phase 1 + RC1 |
| PM Project detail | `/pm/projects/:projectNumber` → redirect · `/pm/projects-legacy/:projectNumber` | 3 OPERATIONAL | — |
| PM Holds | `/pm/holds` | 3 OPERATIONAL | — |
| PM Due Today | `/pm/due-today` | 3 OPERATIONAL | — |
| PM Crew Compliance | `/pm/crew-compliance` | 3 OPERATIONAL | Uses PmShell |
| PM Field Leadership | `/pm/field-leadership` | 3 OPERATIONAL | Uses PmShell |
| PM Fleet · People · Suppliers · Posters | `/pm/fleet` · `/pm/people` · `/pm/suppliers` · `/pm/posters` | 3 OPERATIONAL | — |
| PM QA/QC list | `/pm/qaqc` | 3 OPERATIONAL | — |
| PM Photos Library | `/pm/photos` | 3 OPERATIONAL | — |
| PM Daily · Daily detail | `/pm/daily` · `/pm/daily/:id` | 3 OPERATIONAL | AP-guarded |
| PM Incidents · Incident detail | `/pm/incidents` · `/pm/incidents/:id` | 3 OPERATIONAL | AP-guarded |
| PM Meetings · Meeting detail | `/pm/meetings` · `/pm/meetings/:id` | 3 OPERATIONAL | AP-guarded |
| PM Inspections · Inspection detail | `/pm/inspections` · `/pm/inspections/:id` | 3 OPERATIONAL | AP-guarded |
| PM JHA Plans · Trench Boxes · Equipment · Equipment detail | varies | 3 OPERATIONAL | AP-guarded |
| PM ODR Panel | `/pm/odr` | 2 WIRED | New flow |
| PM Profile · Change Password · Login · Reset | varies | 4 DONE-DONE | — |

---

## Shop Portal surfaces (24)

| Surface | Route | State |
|---------|-------|:------:|
| Shop Hub V2 | `/shop` → `ShopHubV2` | 3 OPERATIONAL |
| Shop Asset Care | `/shop/asset-care` | 4 DONE-DONE (D4 wired in Phase 2B-1) |
| Shop Manager Queue · My Assignments · Unit History | varies | 3 OPERATIONAL |
| Shop Fuel-Lube Visit form · records · detail | `/shop/fuel-lube/new` · `/shop/fuel-lube` · `/shop/fuel-lube/:id` | 4 DONE-DONE (Phase 2B-2A snapshot embedded) |
| Shop Service Truck Reconciliation form · records · detail | varies | 3 OPERATIONAL |
| Shop PM Templates · Schedules · Work Orders · WO detail | varies | 3 OPERATIONAL |
| Shop Trench Safety Repairs | `/shop/trench-safety-repairs` | 3 OPERATIONAL |
| Shop Fleet · Equipment · Equipment detail | varies | 3 OPERATIONAL |
| Shop Profile · Change Password · Login · Reset | varies | 4 DONE-DONE |

---

## HR Portal surfaces (20)

| Surface | Route | State |
|---------|-------|:------:|
| HR Hub V2 | `/hr` → `HrHubV2` | 3 OPERATIONAL |
| HR Field Leadership · Users · Employee Accountability · Timeline | varies | 3 OPERATIONAL |
| HR Time-Off · Time Verification · Payroll Variance | varies | 3 OPERATIONAL |
| HR Training Records | `/hr/training-records` | 3 OPERATIONAL |
| HR Driver Qualification (dashboard + import) | varies | 3 OPERATIONAL |
| HR Daily Reports · DR detail | varies | 3 OPERATIONAL |
| HR Motive Drivers · Driver Profile | varies | 3 OPERATIONAL |
| HR Employees · Employee Requests · Incidents · Safety Records | varies | 3 OPERATIONAL |
| HR Profile · Change Password · Login · Reset · Forgot | varies | 4 DONE-DONE |

---

## Safety Portal surfaces (27)

| Surface | Route | State |
|---------|-------|:------:|
| Safety Hub V2 | `/safety-portal` → `SafetyHubV2` | 3 OPERATIONAL |
| Safety Trench Hub | `/safety/trench-safety` · 6 sub-routes | 4 DONE-DONE |
| Safety Inspections (admin view) | `/admin/inspections` (AP-shared) | 4 DONE-DONE |
| Safety Forms (Equipment Issuance + Training) | `/safety/forms/*` · 6 sub-routes | 4 DONE-DONE (Phase 2B-2A snapshot) |
| Safety Corrective Actions · Fire Extinguishers · Documents · Training · Incidents · Audits · Forms-Records · Reports · Library · Employees · Digest · Driver Profile | varies | 3 OPERATIONAL |
| Safety Fleet | `/safety-portal/fleet` | 3 OPERATIONAL |
| Safety Profile · Change Password · Login · Reset · Forgot | varies | 4 DONE-DONE |

---

## Dispatch Portal surfaces (10)

| Surface | Route | State |
|---------|-------|:------:|
| Dispatch Hub | `/dispatch-portal` → `DispatchHub` (legacy) | 3 OPERATIONAL |
| Dispatch Hub V2 | `/dispatch-portal/hub_v2` → `DispatchHubV2` | 3 OPERATIONAL |
| Dispatch Board | `/dispatch-portal/board` | 4 DONE-DONE |
| Dispatch Command Center | `/dispatch-portal/command` | 3 OPERATIONAL |
| Dispatch Fleet · Haul Ledger · Driver Qualification · Driver Profile | varies | 3 OPERATIONAL |
| Dispatch Profile · Change Password · Login · Reset · Forgot | varies | 4 DONE-DONE |

---

## Field Leadership Portal surfaces (4)

| Surface | Route | State |
|---------|-------|:------:|
| FL Portal Dashboard | `/field-leadership/portal` · `/field-leadership/portal/dashboard` | 4 DONE-DONE (Phase 2B-1) |
| FL Driver Qualification | `/field-leadership/portal/driver-qualification` | 3 OPERATIONAL |
| FL Login · Change Password | varies | 4 DONE-DONE |

---

## Dev / Internal (6)

| Surface | Route | State |
|---------|-------|:------:|
| Dev Hub | `/dev` | gated · OPERATIONAL |
| Design System Demo | `/_internal/design-system` | dev-only · OPERATIONAL |
| V2 Preview surfaces (PM, HR, index, compare) | `/_internal/pm-v2-preview` · `/_internal/hr-v2-preview` · `/_internal/v2-index` · `/_internal/v2-compare/:portal` | dev-only · OPERATIONAL |

---

## Aggregate counts

| State | Approx count | %     |
|-------|--------------|-------|
| 4 DONE-DONE | ~70 surfaces | ~30% |
| 3 OPERATIONAL | ~125 surfaces | ~55% |
| 2 WIRED | ~25 surfaces | ~10% |
| 1 BUILT | ~12 surfaces | ~5% |
| 0 NOT STARTED | 0 | 0% |

**Total surfaces in scope:** ~232 (some routes share a surface; some routes are pure redirects). **Fully DONE-DONE share: ~30%** — concentrated on Admin, public crew forms, and the recently-wired safety/PM workflows. **Discoverability is the dominant gap** for the remaining 70% (most are OPERATIONAL but lack a visible card/sidebar link).
