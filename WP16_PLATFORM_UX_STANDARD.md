# WP16 Platform UX Standard

## Scope
This document defines the canonical interaction model and information architecture for the MASCI operating system.

## Canonical interaction model
- One primary action per screen section.
- Secondary actions grouped together and visually de-emphasized.
- Search, notifications, and navigation always remain reachable from the shell.
- High-frequency actions must be reachable with one thumb on mobile and one glance on desktop.
- Destructive or irreversible actions must state consequence and evidence impact before confirmation.

## Canonical information architecture
- Every route must belong to one canonical home.
- Sidebars group destinations by operating-system meaning, not by engineering ownership.
- Detail pages are children of one parent section and must inherit the same shell.
- Breadcrumbs must always show the route back to the parent context.
- Dynamic routes must still be discoverable by global search or command palette.
- Cross-portal shared routes must still preserve operator context and an obvious path home.
- Namespace drift (`/admin`, `/safety`, `/safety-portal`, `/dispatch-portal`, shared root routes) must be normalized over the WP-16 remediation program.

## Shell requirements
- Sticky header with location, search, notifications, and exit paths.
- Canonical breadcrumb trail.
- Mobile navigation dock for core actions.
- Responsive navigation drawer for secondary destinations.
- Command palette shortcuts for desktop operators.

## Shared component inheritance
Every module must inherit these patterns:
- page headers
- action bars
- search and filter toolbars
- cards and panels
- tables and mobile record cards
- form fields and validation banners
- status chips
- toasts and confirmations
- empty, loading, success, and error states

## Forbidden UX behaviors
- orphaned routes with no obvious home
- multiple competing names for the same feature
- hidden-only mobile actions
- low-contrast helper text
- generic “something went wrong” messaging
- one-off layout inventions inside feature modules
- exempting legacy or secondary screens from the constitutional audit