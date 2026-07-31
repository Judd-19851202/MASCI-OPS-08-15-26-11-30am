# WP-17C Canonical Shell Standard

## Purpose
One governed shell must support every authenticated portal without losing portal identity.

## Shell anatomy
1. **Global shell wrapper** — background, engineering grid, content width, safe-area behavior
2. **Global header** — portal identity, breadcrumbs/page context, search, notifications, language, session controls
3. **Sidebar** — domain-grouped canonical nav
4. **Page header** — title, subtitle, mission cue, primary/secondary actions, last activity
5. **Content rail** — main column with section rhythm and responsive behavior
6. **Footer/provider line** — low-noise attribution and platform identity
7. **Mobile navigation** — same IA, phone-safe interaction, no dead ends

## Canonical shell contract
- Header must always answer where the user is.
- Sidebar must always answer where the tools live.
- Page header must always answer what the page is for.
- Content must always have clear boundaries and not float in blank space.
- Mobile shell must stay scrollable and tappable without overlap.

## Allowed shell variants
- **Public entry shell** — no authenticated sidebar; public entry architecture only
- **Authenticated canonical shell** — shared header/sidebar/page anatomy
- **Portal accent variants** — admin, PM, and future portal accents through tokens/modifiers

## Responsive behavior
- Desktop: persistent sidebar + content rail
- Tablet: collapsible/overlay nav with the same grouping
- Phone: bottom/overlay nav plus task-safe page header and actions
- Detail routes retain shell framing at all sizes

## Representative WP-17C application
- Public sign-in and platform landing adopt the public foundation
- Admin OS adopts the canonical authenticated shell
- PM hub adopts the same shell with PM-specific emphasis and reduced noise

## Prohibited patterns
- Portal-specific shell reinvention without a documented functional reason
- Missing header or missing page title context
- Flat whitewashed pages with no portal identity
- Mobile navigation that cannot scroll or hides critical actions
