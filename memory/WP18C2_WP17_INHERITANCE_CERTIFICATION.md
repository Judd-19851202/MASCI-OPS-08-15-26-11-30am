# WP18C2 · WP17 Inheritance Certification

## Certification Statement

WP-18C2 inherited the permanent WP-17 Product / Operator Experience Constitution on the newly added authority surfaces.

## New / Modified Surfaces Covered

- `/admin/governance/project-controls`
- `/pm/project-controls`
- Daily Report V3 work-block preview card
- Daily Report detail governed work-block section
- Admin / PM sidebar route additions

## Evidence of Inheritance

### Shared shells and navigation

- Admin surface uses existing admin shell patterns and side navigation.
- PM surface uses `PmShell` and existing PM project selector.
- New routes were added into existing sidebar domain maps rather than creating route-local navigation.

### Shared visual language

- Existing button, dialog, input, textarea, and table primitives were reused.
- No separate design system or noncanonical shell was introduced.

### Data-testid coverage

Critical interactive and informational elements were instrumented with `data-testid`, including:

- admin summary cards, review items, event cards, add-work-type dialog and fields
- PM summary cards, pay-item form, mapping form, lifecycle buttons, crew actions, work-ledger rows
- Daily Report work-block preview card and rows
- Daily Report governed work-block view section and rows

### Bilingual evidence

- EN/ES toggle remained functional.
- Testing agent report `iteration_111.json` recorded language toggle **PASS**.
- New strings were added through existing translation pathways and local bilingual handling on the new admin authority page.

### Responsive evidence

- Testing agent report `iteration_111.json` recorded responsive design **PASS**.
- Mobile viewport `390x844` verified on the new PM/admin flows.

### Workflow-state evidence

New flows provide visible empty / loaded / result states for:

- work types
- review queue
- event contracts
- pay items
- mappings
- lookahead
- lifecycle/archive
- crew intelligence
- work ledger

## Console / Network Note

Smoke capture on the public landing page showed aborted analytics / sentry / rum requests during navigation. No WP18C2 product-surface functional failure was attributed to those third-party browser events in testing.
