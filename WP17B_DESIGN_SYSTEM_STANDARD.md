# WP-17B Design System Standard

## What stays
- `PortalShell`, `Card`, `StatusChip`, `EmptyState`
- Existing KPI-help pattern
- Existing sidebar domain-group concept
- Existing operator-first tone (queue-first, evidence-first, no vanity metrics)

## What must standardize
1. One canonical shell per portal family
2. One sidebar grammar per portal family
3. One table density ladder
4. One form message system
5. One overlay decision tree (dialog vs drawer vs sheet)
6. One help/coaching placement rule
7. One white-label execution rule across web, email, and PDF

## Non-negotiable rules for implementation
- No route inventing during design cleanup
- No component replacement that breaks business logic ownership
- Canonical terminology must drive labels, empty states, and navigation
- Hidden/internal routes stay hidden unless explicitly reclassified in WP-17C

## Standard disposition summary
| Area | Disposition |
|---|---|
| Proven primitives | `KEEP` |
| Parallel shell/nav families | `MERGE` |
| Legacy layout chrome | `MODERNIZE` |
| Inconsistent overlays / tables / forms | `STANDARDIZE` |