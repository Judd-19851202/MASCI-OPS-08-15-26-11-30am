# WP17C Canonical Design Standard

## Canonical Reference
The mature Safety Operations / Trench Safety shell is the reference pattern for:
- MASCI navy glass header
- frosted navigation treatment
- disciplined spacing and gutters
- executive-grade card depth
- restrained portal accents within one platform identity

## Canonical Shell Rules
- One platform shell: `PortalShell`
- One auth/public entry shell: `PortalLoginShell`
- One form shell: `FormShell`
- No portal-specific global header rebuilding
- No portal-specific logo resizing outside approved component props
- No route-local language selector patterns when a canonical toggle exists

## Canonical Header
- Sticky navy glass header
- Stable height driven by `--wp17-header-height`
- MASCI brand mark on the left/center responsive pattern only
- Portal identity via restrained role label, accent, and breadcrumbs
- No freeform header recoloring outside approved shell theme rules

## Canonical Typography
- Page title: `font-display` with shared shell hierarchy
- Body copy: `--wp17-body-size`
- Field label: `--wp17-label-size`, uppercase, mono, tracking tokenized
- No route-invented heading scales

## Canonical Surfaces
- Use `wp17-panel`, `wp17-form-frame`, `wp17-table-shell`, `wp17-mission-banner`
- Shared radius, border, shadow, and background tokens only
- No flat generic white SaaS treatment

## Canonical Responsive Rule
- Mobile, tablet, desktop layouts must be intentionally composed
- Sticky action bars belong to `FormShell`
- Portal navigation and top chrome belong to `PortalShell`
- Public/login flows belong to `PortalLoginShell`
