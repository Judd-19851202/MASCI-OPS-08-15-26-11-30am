# WP-17C Component Foundation

## Canonical shared components
- Page shell
- Page header
- Sidebar / mobile navigation
- Breadcrumbs
- Buttons / icon buttons
- Cards / KPI cards / queue cards
- Tables
- Search / filters
- Inputs / textareas / dropdowns / checkboxes / radios
- Date/time pickers
- Tabs / accordions
- Modals / drawers / sheets
- Alerts / toasts / status badges / progress indicators
- Empty / loading / error states
- Coaching/help panels
- Metadata panels

## Required definition per component
- variants
- usage rules
- accessibility behavior
- mobile behavior
- tenant-brand behavior
- error/loading behavior
- component API
- deprecated equivalents

## WP-17C foundation posture
- Build and certify the shared component layer.
- Do **not** mass-migrate every legacy page just because the canonical component exists.
- Use representative surfaces to prove the component contract.

## Deprecated-equivalent rule
If two existing components express the same job with different labels/styles, WP-17C defines the canonical version and records the older one as deprecated for WP-17D migration.

## Current WP-17C representative focus
- Canonical shell and page-header behavior
- Canonical dashboard cards / queue cards
- Canonical table shell
- Canonical detail hero
- Canonical form framing and draft-status rail
- Canonical notification drawer treatment
