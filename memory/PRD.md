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
  - the Shared Operational Home route was explicitly reopened after executive review and recertified: the Home header now uses the governed `CanonicalHeader` home variant (logo-first, no repeated platform-name copy, no duplicate sign-in entry, compact language control, preserved navy/glass shell) and the hero hierarchy was deduplicated to restore the previously approved command-center feel
  - safety record detail convergence is now closed for the non-admin routes: `ViewSafetyForm.jsx` was rebuilt onto `PortalShell`/`AdminRouteShell`, `DetailPageHero`, and the canonical `DataTable`, eliminating local-header drift, duplicate title stacks, and legacy table treatment on issuance/training detail records
  - `PortalShell.jsx` now supports a governed `showPageHeader` switch so routes with their own canonical detail hero do not stack a second page-intro block above the content; `JhaPlansHub.jsx` now uses that switch and has tighter, operational coaching with verified mobile overflow fixes at `390` and `430`
  - admin safety aliases are now formally closed: `/admin/safety/issuance/:id` and `/admin/safety/training/:id` were visually certified on the governed `AdminRouteShell` + `DetailPageHero` detail architecture at `390`, `430`, `768`, `1024`, and `1440`
  - admin library convergence continued: `JhaPlansAdmin.jsx` was moved off `LegacyAdminModernShell`, duplicate title stacks were removed, and the admin JHA refetch loop was fixed by memoizing admin auth headers; `TrenchBoxesAdmin.jsx` was moved onto `AdminRouteShell` + `DetailPageHero` and its Add Box dialog now uses the governed navy/glass modal treatment with the canonical icon family
  - trench shell convergence is now underway on shared architecture, not one-off patches: `SafetyShell.jsx` and `PmShell.jsx` now support governed suppression of duplicate page headers / mission banners, `TrenchSafetyShell.jsx` now renders one canonical trench navigation surface across admin/safety/PM contexts, and portal-hop inconsistencies in `TrenchSafetyAssetsList.jsx` + `TrenchSafetyHub.jsx` were removed so trench links stay inside the active portal
  - `TrenchSafetyAssetDetail.jsx` now uses the canonical detail hero, governed route framing, and `DataTable` deployment history treatment; `/admin/trench-safety/assets/:assetId`, `/admin/trench-safety/reports`, and `/safety/trench-safety/reports` were visually certified after the trench shell convergence pass
  - the approved executive operations tool is now live at `/admin/wp17d-certification`, showing survivor counts by category, route-by-route certification status, screenshot / QA evidence summaries, blocker state, overall completion %, and GO / NO-GO readiness
  - Executive Amendment #2 is now active in implementation: the shared MASCI header system was rebuilt into a strict two-tier architecture (`CanonicalHeader.jsx`, `PortalShell.jsx`, `AdminRouteShell.jsx`, `SafetyShell.jsx`, `PmShell.jsx`, `PortalLoginShell.jsx`, `DetailPageHero.jsx`) so global controls stay in row one, workflow identity lives in row two, long titles remain readable at `390px`, and utility controls live below — not inside — the sticky header rows
  - operator-facing product language was cleaned immediately after the header rewrite: the former internal admin governance surface now renders as **Operations Readiness Center** at `/admin/platform-readiness`, and banned engineering terms no longer appear in the visible UI even when the legacy alias `/admin/wp17d-certification` is opened
  - the first Amendment #3 reopen batch is now closed through governed shared systems: `FormShell.jsx`, `FormSection.jsx`, `ProgressRail.jsx`, `SubmitReviewPanel.jsx`, and `JobPicker.jsx` were upgraded so DVIR, Equipment Pre-Op, Daily Report, and Meeting workflows share the same operator-first hierarchy, cleaner header language, normalized utility/progress placement, and stronger submit-action emphasis
  - `NewDailyReportV3.jsx` now uses a governed sticky submit footer while removing the duplicate inline submit CTA; form routes that previously said `MASCI Job` / `Pick a MASCI job` now use operator-safe wording (`Current Job`, `Pick a current job`)
  - `DevHub.jsx` remains **BLOCKED_CREDENTIALS** for authenticated visual certification in Preview: `GET /api/dev/check` returns `404`, `POST /api/dev/login` returns `404`, and backend fail-closed logic requires backend `DEV_PASSWORD` plus the dev endpoint gate to be enabled before the actual `/dev` surface can be opened and certified
  - Executive Direction lock is now reflected in implementation order: shared governed design primitives are the reference, Hub is the first full implementation, and route propagation follows only after the shared primitive layer is complete
  - shared design-system primitives were completed for the current visual-governance wave: canonical card architecture (`CanonicalCard.jsx` + `wp17.css`), canonical section headings (`SectionHeading.jsx`), canonical CTA/button treatment (`components/ui/button.jsx`), canonical badges/chips (`OperationalStatusBadge.jsx` + chip tokens), and canonical state surfaces (`components/ui/PortalStates.jsx`, `components/EmptyState.jsx`)
  - `CanonicalHeader.jsx` home-mode fallback was tightened so the Shared Operational Home now correctly shows **Operations Platform** instead of the generic **Operational workflow** label
  - Hub/home was rebuilt from the governed primitive layer instead of page-local card implementations: field-entry cards, leadership cards, workspace cards, new-hire entry card, welcome-back card, and reference cards now all render through one shared card language with unified accent logic, spacing, icon containers, typography, footer CTAs, and interaction states
  - Executive Constitution update batch is now landed for the Home experience and shared design-system hardening: the Home header now owns the single primary sign-in entry point through `CanonicalHeader.headerControlsSlot`, the bolted-on explanatory navy panel was removed, the hero now uses governed CTA buttons instead of decorative chips, the shared language selector was hardened for `390px`, and home copy now renders as **MASCI Operations Platform** instead of drifting into alternate “Hub” naming
  - shared card governance was hardened beyond the base card primitive: `CanonicalCard.jsx` now exposes governed families (`ModuleCard`, `WorkflowCard`, `ActionCard`, `InformationCard`, `ExternalPlatformCard`, `DetailCard`, `FormSectionCard`, `AlertCard`) so propagation can replace local card implementations with shared variants instead of forcing one generic card everywhere
  - anti-drift enforcement is now active for the constitutional Home lane through `/app/scripts/wp17d_constitution_guard.py`, with scoped checks for banned Home terminology, duplicate Home sign-in, explanatory-panel regressions, local-card regressions, language-control treatment, white-header drift, and UI emoji/icon shortcuts in the constitutional surfaces

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
  - Shared Operational Home header restoration verified by direct screenshot review at `390`, `430`, `768`, `1024`, and `1440`, authenticated Home screenshots at `390` and `1440`, Spanish toggle verification at `390`, logo-to-home behavior check, and focused `auto_frontend_testing_agent` pass with no remaining Home-route defects
  - focused frontend QA passed for `/jha`, `/safety/forms/equipment-issuance/:id`, and `/safety/forms/equipment-training/:id`; JHA mobile overflow was found at `390`, fixed, and re-verified at `390` and `430` with **100% pass**
  - responsive screenshot certification passed for `/admin/safety/issuance/:id`, `/admin/safety/training/:id`, `/admin/jha-plans`, and `/admin/trench-boxes` at `390`, `430`, `768`, `1024`, and `1440`
  - focused `auto_frontend_testing_agent` pass (**4/4 PASS**) confirmed the admin safety aliases, admin JHA surface, trench Add Box dialog, and DevHub disabled-environment handling with no remaining defects
  - responsive screenshot certification also passed for `/admin/trench-safety/reports`, `/safety/trench-safety/reports`, `/admin/trench-safety/assets/:assetId`, and `/admin/wp17d-certification` at `390`, `430`, `768`, `1024`, and `1440`
  - focused `auto_frontend_testing_agent` pass (**7/7 PASS**) confirmed trench shell portal consistency, admin trench detail alias routing, executive dashboard behavior, and console/network cleanliness with no remaining defects
  - shared-header QA pass (**4/4 PASS**) confirmed the new two-tier header, product-language cleanup, detail-header integration, and legacy-alias hygiene on `/admin/login`, `/admin/platform-readiness`, `/admin/trench-safety/assets/:assetId`, and `/admin/wp17d-certification`
  - shared field-form QA pass (**4/4 PASS**) confirmed the reopened DVIR, Equipment Pre-Op, Daily Report, and Meeting workflows with mobile-first header readability, zero duplicated MASCI wording in sticky header rows, corrected Daily Report sticky footer behavior, and zero overflow / console defects
  - responsive screenshot certification passed for the rebuilt Hub and shared primitive layer at `390`, `430`, `768`, `1024`, and `1440`, with zero horizontal overflow and governed-card consistency across all Hub sections
  - formal design-system + Hub certification passed in `/app/test_reports/iteration_99.json` with **100% frontend pass**, including canonical header validation, 15 governed card surfaces, Need Help dialog behavior, and zero console errors
  - final `auto_frontend_testing_agent` verification passed (**19/19 PASS**) on the public Hub route, confirming the two-tier header, unified card system, Company Info dialog trigger, responsive behavior, and console cleanliness
  - constitution-update Home certification passed in `/app/test_reports/iteration_100.json` with **100% frontend pass**, confirming header-owned sign-in, no duplicate sign-in below header, interactive EN/ES control at `390px`, no explanatory navy panel, governed card families, Need Help dialog continuity, and zero overflow / console errors at `390`, `430`, `768`, `1024`, and `1440`
  - scoped constitutional anti-drift guard now passes locally via `python /app/scripts/wp17d_constitution_guard.py`

## Constraints Still Honored
- No full-platform migration was started.
- No broad redesign outside the bounded representative set.
- White-label readiness preserved; MASCI identity was not hard-coded into the reusable foundation.

## Next Authorized Work
- Continue WP-17D in the locked order now set by executive direction: governed design system → Hub implementation → platform propagation.
- Treat the public Home correction as closed for this constitution wave and use it as the first verified implementation of the hardened design system — not as a separate product identity.
- Propagate the new shared card / button / badge / section-heading / state primitives across the platform in the approved rollout order: Field Operations → Transportation → Safety → QA/QC → Shop → Project Management → Human Resources → Administration.
- Start the next propagation wave with **Field Operations** and reopen every touched route against the complete-page rule, the no-duplicate-sign-in rule, and the product-language constitution before certifying it again.
- While propagating, replace legacy local card/tile implementations with the governed shared primitives instead of redesigning routes individually.
- Continue the icon-system sweep in every touched route so mixed icon families, stroke weights, containers, and spacing are eliminated alongside card migration.
- Expand anti-drift automation beyond the Home lane to cover banned visible terminology scans, unicode/emoji UI icon scans, local card implementation scans, direct-header scans, duplicate-title / duplicate-sign-in scans, and representative screenshot regression gates for each portal family.
- Reopen and certify remaining dialogs, overlays, tables, loading/empty/error/success/warning states, and motion under the same governed primitive system after the card rollout advances.
- Keep `DevHub.jsx` in **BLOCKED_CREDENTIALS** until backend Preview exposes `DEV_PASSWORD` plus the dev-endpoint gate; do not mark authenticated `/dev` certified before the environment is unblocked.
- Continue survivor-ledger reconciliation so platform counts move by eliminated mixed-generation primitives rather than ad-hoc route polish.
- Only after genuine full-platform convergence should WP-17E be considered.