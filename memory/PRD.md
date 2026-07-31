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
  - Transportation first-wave repairs applied across shell, subnav, Mission Control cards, and external/public carrier verification/invite flows
  - portal-mission convergence expanded across HR, Safety, Dispatch, Shop, Transportation, Training, Executive, and Field Leadership landings
  - driver/public edge routes (`/shift`, `/driver`, `/revise/:token`) moved into the same public-family visual system

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
  - `auto_frontend_testing_agent`: **22/22 PASS** on the broader WP-17D convergence sweep
  - dispatch direct-token hub verification passed

## Constraints Still Honored
- No full-platform migration was started.
- No broad redesign outside the bounded representative set.
- White-label readiness preserved; MASCI identity was not hard-coded into the reusable foundation.

## Next Authorized Work
- Continue WP-17D portal-by-portal convergence until no active legacy or mixed-generation surface remains.
- Finish migrating the remaining `MIGRATING` rows in `WP17D_PLATFORM_CONVERGENCE_LEDGER.csv`, then advance rows through functional / visual / responsive certification.
- Only after genuine full-platform convergence should WP-17E be considered.