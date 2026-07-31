# PRD

## Original Problem Statement
- Complete WP-17A production stabilization, release gating, and deployment validation.
- Then execute WP-17B as a full-platform audit of UX, IA, navigation, components, terminology, coaching, PDFs, emails, notifications, and white-label surfaces without redesigning the product yet.

## Current Architecture
- React frontend in `/app/frontend/src/`
- FastAPI backend in `/app/backend/`
- MongoDB runtime with environment-owned configuration
- Domain-segmented frontend routing through `AppRoutes.jsx`, sidebar/domain maps, hub shells, and nested Transportation routes

## What Is Implemented
- WP-17A is complete and production-validated.
- WP-17B blueprint lock is complete in documentation form.
- Authoritative WP-17B source-verified totals:
  - `1190` audited platform surfaces
  - `13` portal / route families
  - `481` routes
  - `113` hidden/detail surfaces
  - `66` forms
  - `15` PDF source surfaces
  - `14` email/template source surfaces
  - `253` navigation items
  - `64` reusable component families
  - `8` terminology conflict groups
  - `11` coaching/help findings

## Current Authoritative Documents
- `/app/WP17B_PLATFORM_MASTER_INVENTORY.md`
- `/app/WP17B_INFORMATION_ARCHITECTURE.md`
- `/app/WP17B_NAVIGATION_AUDIT.md`
- `/app/WP17B_DASHBOARD_AUDIT.md`
- `/app/WP17B_FORM_AUDIT.md`
- `/app/WP17B_WORKFLOW_AUDIT.md`
- `/app/WP17B_COMPONENT_AUDIT.md`
- `/app/WP17B_DESIGN_SYSTEM_STANDARD.md`
- `/app/WP17B_TERMINOLOGY_STANDARD.md`
- `/app/WP17B_COACHING_STANDARD.md`
- `/app/WP17B_ICON_AUDIT.md`
- `/app/WP17B_WHITE_LABEL_STANDARD.md`
- `/app/WP17B_EXECUTIVE_REPAIR_REGISTER.md`
- `/app/WP17B_IMPLEMENTATION_ROADMAP.md`

## WP-17B Constraints Honored
- No production changes
- No redesign implementation
- No component migration
- No WP-17C execution started

## Next Authorized Work
- Await executive authorization to begin WP-17C using the locked blueprint and repair register.