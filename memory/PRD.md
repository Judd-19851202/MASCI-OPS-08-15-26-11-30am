# PRD

## Original Problem Statement
- Complete WP-17A production stabilization, release gating, and deployment validation.
- Execute WP-17B as the authoritative platform audit across UX, IA, navigation, components, terminology, coaching, PDFs, emails, notifications, and white-label surfaces.
- Execute WP-17C as the shared experience foundation: build the reusable platform foundation, canonical IA/navigation, and a bounded representative implementation without beginning full-platform migration.

## Current Architecture
- React frontend in `/app/frontend/src/`
- FastAPI backend in `/app/backend/`
- MongoDB runtime with environment-owned configuration
- Domain-segmented frontend routing through `AppRoutes.jsx`, portal shells, sidebar/domain maps, and nested Transportation routing

## What Is Implemented
- WP-17A is complete and production-validated.
- WP-17B blueprint lock is complete in documentation form.
- WP-17C is now complete at the foundation scope:
  - `WP17C_IMPLEMENTATION_LEDGER.csv` created with `1190` reconciled surfaces
  - canonical mission, IA, navigation, token, shell, page anatomy, component, icon, regression, and closeout docs created
  - shared frontend foundation implemented in `frontend/src/design-system/wp17.css`, `PortalShell.jsx`, `MobileNavigation.jsx`, and representative wrappers/components
  - representative implementation completed on public sign-in, public landing, Admin landing, PM landing, list/detail/form/table/modal workflows, and tablet/phone views
- WP-17D is in active autonomous execution:
  - `WP17D_PLATFORM_CONVERGENCE_LEDGER.csv` created with the full `1190`-surface denominator
  - shared shell defaults widened so `PortalShell` surfaces converge on the WP-17D canonical shell automatically
  - portal wrappers converged for logins, HR, Safety, PM, and shared form flows
  - standalone authentication convergence completed for the current P0 wave: `AdminLogin.jsx`, `PmResetPassword.jsx`, `SafetyFormsLogin.jsx`, `HrChangePassword.jsx`, and `DispatchForgotPassword.jsx` now render through `PortalLoginShell`
  - `PortalLoginShell` was tightened to remove the duplicate shared-entry CTA so auth routes no longer show redundant sign-in actions
  - provisional Field Leadership surfaces were reopened under the executive visual audit and repaired: hub copy density was tightened, records dropped duplicate local navigation, the shared Field Leadership form moved onto `FormShell`, and record views were rewrapped into the canonical shell family
  - `FieldLeadershipView.jsx` admin mode no longer uses the prior admin-side wrapper; admin and non-admin record views now share the same canonical top-shell family with MASCI navy glass preserved
  - the next FormShell migration batch landed: `NewConstraint.jsx` and `NewQaqcInspection.jsx` now render through canonical `FormShell`
  - the QA/QC inspection route was decluttered by removing the duplicate top guidance band so the form no longer stacks repeated workflow tips before the body
  - survivor-register methodology is now active: `/app/memory/WP17D_SURVIVOR_REGISTER.md` tracks full-ledger denominator counts plus active-route code-scan counts so implementation is driven by remaining legacy survivors instead of migration percentages
  - additional auth/login survivor routes were converged onto `PortalLoginShell`: `SafetyForgotPassword.jsx`, `HrResetPassword.jsx`, `DispatchResetPassword.jsx`, `ShopResetPassword.jsx`, `SafetyChangePassword.jsx`, `DispatchChangePassword.jsx`, `ShopChangePassword.jsx`, `PmChangePassword.jsx`, and `DevLogin.jsx`
  - additional form-shell survivor routes were converged: `NewSafetyEquipmentIssuance.jsx`, `NewSafetyEquipmentTraining.jsx`, `NewEquipmentInspection.jsx`, and `NewFleetDVIR.jsx`
  - active section-route legacy wrappers were removed from `/field`, `/qaqc`, and `/safety`; these now render through canonical `PortalShell` without the nested legacy header/footer layer
  - Transportation first-wave repairs applied across shell, subnav, Mission Control cards, and external/public carrier verification/invite flows
  - portal-mission convergence expanded across HR, Safety, Dispatch, Shop, Transportation, Training, Executive, and Field Leadership landings
  - driver/public edge routes (`/shift`, `/driver`, `/revise/:token`) moved into the same public-family visual system
  - platform-wide convergence tightened again under the revised executive standard: canonical header declutter, one typography system, one color language, one form/table/control system, and login-experience convergence are now applied through shared primitives and shared CSS
  - Daily Report was reopened and moved onto the canonical `FormShell`
  - Transportation auth-scope drift was reduced further by fixing dispatch scope inference, directory compatibility for notifications, and dispatch-safe audit behavior
  - auth-wave visual certification confirmed: no duplicate shell CTA on migrated auth routes, no legacy Safety Forms notice, and Navy glass headers preserved across the migrated routes
  - shared-table survivor batch 01 is now closed: `AdminSchedulerRuns`, `AdminLeadershipEquipment`, `AdminTerminations`, `AdminGuide`, `ExecutiveOperationalIntelligence`, and `PmOperationalIntelligence` all render through the upgraded canonical `DataTable`
  - shared support fixes shipped with the table batch: `LastActivityLine` now guards missing portal values and Scheduler Runs no longer shows the obsolete legacy-moved banner
  - responsive screenshot certification was completed for the batch at `390`, `768`, `1024`, and `1440`, and the survivor ledgers were reconciled from `113` to `107` full-ledger table survivors and from `19` to `13` active-route table survivors
  - platform shell sub-batch 01 is now closed: `ViewDailyReport`, `ViewInspection`, `ViewMeeting`, and `ViewIncident` now share the canonical `DetailPageHero`, while `AdminRouteShell` can suppress duplicate shell headers/breadcrumbs on detail routes
  - shell support fixes shipped with the batch: stacked `PageHeader` mode for wide layouts and `ViewIncident` now gates linked CAPA fetches to Safety Portal routes so admin shell views stay clean
  - responsive screenshot certification was completed for `/admin/daily/:id`, `/pm/daily/:id`, `/admin/inspections/:id`, `/admin/meetings/:id`, and `/admin/incidents/:id` at `390`, `768`, `1024`, and `1440`, and the survivor ledgers were reconciled from `134` to `129` route/shell survivors and from `68` to `66` navigation survivors
  - public & off-shell convergence batch is now closed: `FieldSafetyCards`, trench-safety public routes, transportation invite/verify routes, `PublicExcavationForm`, public QA/QC detail, and the admin QA/QC alias were rebuilt onto the canonical shell family and visually certified together
  - shared shell support for the batch shipped through `OperationalPageFrame.jsx`, `OperationalStatusBadge.jsx`, and the rebuilt `PublicTrenchHeader.jsx`, while `ViewQaqcInspection.jsx` now shares the canonical `DetailPageHero` + `AdminRouteShell` suppression pattern
  - responsive screenshot certification was completed for the batch at `390`, `768`, `1024`, and `1440`, and the survivor ledgers were reconciled from `129` to `118` route/shell survivors and from `66` to `63` navigation survivors
  - highest-visibility platform experience batch is now closed: Hub/home, Guidance/help shells, `NearMissKiosk`, `ThankYou`, print/poster routes, and HR daily-report detail were converged and visually certified to the shared MASCI shell family
  - shared support for the batch shipped through `OperationalPrintPageFrame.jsx` and `OperationalOutcomeFrame.jsx`; `OperationalGuidanceCenter.jsx` now uses the shared operational topbar, while `ViewDailyReport.jsx` moved onto the canonical `DataTable` primitive for its repeated detail grids
  - responsive screenshot certification and QA were completed for `/`, `/guidance`, `/near-miss`, `/thank-you`, `/cheatsheet`, `/admin/trench-boxes/poster`, `/admin/jha-plans/poster`, `/admin/posters/print-all`, and `/hr/daily-reports/:id` at `390`, `768`, `1024`, and `1440`, and the survivor ledgers were reconciled from `118` to `107` route/shell survivors, `63` to `62` navigation survivors, `107` to `104` table survivors, and `39` to `38` form survivors
  - executive design correction applied: the platform-level header system is now locked back to the permanent MASCI navy/frosted operating shell through the shared `CanonicalHeader.jsx`, and shared public/portal/auth shells (`OperationalPageFrame`, `PortalShell`, `FormShell`, `PortalLoginShell`, `PublicShell`, `SignIn`, `Revise`, `FormPasswordGate`) now inherit that single header family instead of drifting toward white/flat variants
  - the canonical header keeps the MASCI “M” pinned in one location and one size, routes the logo to Shared Operational Home, keeps a single language selector treatment, and prevents portal accent colors from recoloring the shell itself

## Locked Totals Preserved
- `1190` audited platform surfaces
- `13` portal / family groupings
- `481` routes
- `113` hidden/detail surfaces
- `66` forms
- `15` PDF source surfaces
- `14` email/template source surfaces
- `253` navigation items
- `64` reusable component families
- `8` terminology conflict groups
- `11` coaching/help findings

## Key WP-17C Deliverables
- `/app/WP17C_IMPLEMENTATION_LEDGER.csv`
- `/app/WP17C_PORTAL_MISSION_AND_ENTRY_ARCHITECTURE.md`
- `/app/WP17C_INFORMATION_ARCHITECTURE_CANON.md`
- `/app/WP17C_NAVIGATION_CANON.md`
- `/app/WP17C_DESIGN_TOKEN_STANDARD.md`
- `/app/WP17C_CANONICAL_SHELL_STANDARD.md`
- `/app/WP17C_CANONICAL_PAGE_ANATOMY.md`
- `/app/WP17C_COMPONENT_FOUNDATION.md`
- `/app/WP17C_ICON_SYSTEM_STANDARD.md`
- `/app/WP17C_REPRESENTATIVE_IMPLEMENTATION_REPORT.md`
- `/app/WP17C_FOUNDATION_REGRESSION_REPORT.md`
- `/app/WP17C_EXECUTIVE_CLOSEOUT.md`

## Verification Status
- Testing agent report: `/app/test_reports/iteration_89.json`
- Smoke / spot verification completed for Hub, Daily Report form wrapper, and live Asset Profile detail route.
- Representative PM clarity, notification drawer, and responsive coverage verified in preview.
- WP-17D wave verification:
  - `/app/test_reports/iteration_90.json`
  - `/app/test_reports/iteration_91.json`
  - `/app/test_reports/iteration_92.json`
  - `/app/test_reports/iteration_93.json`
  - `/app/test_reports/iteration_94.json`
  - `/app/test_reports/iteration_95.json`
  - `/app/test_reports/iteration_96.json`
  - `/app/test_reports/iteration_97.json`
  - `/app/test_reports/iteration_98.json`
  - `auto_frontend_testing_agent`: **22/22 PASS** on the broader WP-17D convergence sweep
  - `auto_frontend_testing_agent`: **5/5 auth routes PASS** for the PortalLoginShell convergence wave
  - `auto_frontend_testing_agent`: **9/9 PASS after fix** on the Field Leadership visual-audit + FormShell migration wave
  - `auto_frontend_testing_agent`: **5/5 PASS** on the survivor-hunt wave covering `/equipment/new`, `/fleet/dvir/new`, `/field`, `/qaqc`, and `/safety`
  - dispatch direct-token hub verification passed
  - post-fix spot checks passed for Dispatch login shell, Admin canonical header, Daily Report canonical form shell, and Transportation dispatch route without 401 console noise
  - formal auth-wave certification passed for `/admin/login`, `/safety/forms/login`, `/dispatch-portal/forgot-password`, `/pm/reset/test-token`, and `/hr/change-password`
  - formal Field Leadership + FormShell certification passed for `/leadership`, `/leadership/records`, `/leadership/verbal_coaching/new`, `/leadership/records/:id`, `/admin/leadership/records/:id`, `/constraints/new`, and `/qaqc/concrete-form/new`
  - formal survivor-hunt certification passed for `/equipment/new`, `/fleet/dvir/new`, `/field`, `/qaqc`, and `/safety` in `/app/test_reports/iteration_94.json`
  - formal shared-table certification passed for `/admin/scheduler-runs`, `/admin/leadership-equipment`, `/admin/terminations`, `/admin/guide`, `/admin/executive-operational-intelligence`, and `/pm/operational-intelligence` in `/app/test_reports/iteration_95.json`
  - follow-up backend sanity check confirmed `/api/admin/scheduler-runs` and `/api/diag/last-activity?portal=admin` after the portal-fix patch
  - formal platform-shell sub-batch certification passed for `/admin/daily/:id`, `/pm/daily/:id`, `/admin/inspections/:id`, `/admin/meetings/:id`, and `/admin/incidents/:id` in `/app/test_reports/iteration_96.json`
  - focused frontend verification confirmed no duplicate shell headers and no background CAPA 401 on the admin incident route after the Safety Portal gate
  - formal public/off-shell convergence certification passed for `/safety/cards`, `/trench-safety`, `/trench-safety/references`, `/trench-safety/tabulated-data`, `/trench-safety/report`, `/trench-safety/assets/:assetId`, `/trench-safety/excavation/new`, `/transport-invite/:token`, `/transport-verify/:cnum`, `/qaqc/:id`, and `/admin/qaqc/:id` in `/app/test_reports/iteration_97.json`
  - auto frontend QA and formal certification passed for `/`, `/guidance`, `/near-miss`, `/thank-you`, `/cheatsheet`, `/admin/trench-boxes/poster`, `/admin/jha-plans/poster`, `/admin/posters/print-all`, and `/hr/daily-reports/:id` in `/app/test_reports/iteration_98.json`
  - canonical header correction verified across `/`, `/guidance`, `/sign-in`, `/revise/example-invalid-token`, and `/admin` with `auto_frontend_testing_agent`: same 65px navy/frosted header, same 32px logo, same language selector/control spacing, no white-header regressions, no console errors

## Constraints Still Honored
- No full-platform migration was started.
- No broad redesign outside the bounded representative set.
- White-label readiness preserved; MASCI identity was not hard-coded into the reusable foundation.

## Next Authorized Work
- Continue WP-17D portal-by-portal convergence until no active legacy or mixed-generation surface remains.
- Continue the Platform Shell Batch with the remaining highest-visibility routes first: `ViewSafetyForm` variants, `JhaPlansHub`, `DevHub`, remaining trench/detail aliases, and any remaining direct-header pages still not routed through `CanonicalHeader`.
- Continue shell-first convergence order: remaining legacy headers → navigation cleanup → typography/layout tightening → coaching/help reductions → information hierarchy and dead-space removal.
- Shared component batches still follow after shell completion: dialogs/overlays → detail tables/cards → remaining shared primitives.
- Continue the executive visual compliance audit on earlier WP-17D migrated surfaces to catch any remaining white/generic drift, duplicated controls, excess helper copy, icon inconsistency, or spacing regressions.
- Drive execution from `WP17D_SURVIVOR_REGISTER.md`: keep clearing active-route survivors through shared systems only, with the next shell batch centered on remaining form/table/coaching survivors (`ViewSafetyForm`, `JhaPlansHub`, `DevHub`, and portal-specific trench/detail aliases) plus icon convergence during every touched route.
- Reconcile survivor fixes back into `WP17D_PLATFORM_CONVERGENCE_LEDGER.csv` so platform-wide counts move toward zero by survivor category rather than percentage complete.
- Continue icon consolidation, card/table/dialog standardization, navigation cleanup, and responsive/mobile refinement until survivor counts reach zero or a documented exception exists.
- Only after genuine full-platform convergence should WP-17E be considered.