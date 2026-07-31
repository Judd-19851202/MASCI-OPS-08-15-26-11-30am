# WP-17C Design Token Standard

Source of truth: `frontend/src/design-system/wp16.css` and the WP-17C foundation layer introduced in `frontend/src/design-system/wp17.css`.

## Visual direction
- Preserve the light enterprise identity.
- Preserve navy as the structural brand direction.
- Use restrained frosted glass, not decorative glass.
- Keep the engineering grid subtle and navy-toned.
- Orange is an accent, not a theme.
- Never hard-code MASCI into the reusable framework.

## Canonical token groups
1. **Brand tokens** — tenant brand, navy shell hues, controlled accent hues
2. **Neutral tokens** — page, surface, panel, border, text, muted text
3. **Status tokens** — healthy, warning, critical, info, offline, pending
4. **Typography tokens** — display, body, mono, size hierarchy
5. **Spacing tokens** — shell gutters, panel padding, page rhythm, section gaps
6. **Radius tokens** — shell, panel, button, chip, modal
7. **Border/shadow/elevation tokens** — subtle enterprise depth only
8. **Glass tokens** — header glass, sidebar glass, panel glass readability
9. **Motion tokens** — duration, easing, stagger rhythm, hover/press behavior
10. **Focus/touch tokens** — visible focus, 44px minimum touch target
11. **Responsive tokens** — shell breakpoints, max widths, safe zones
12. **Z-index tokens** — sticky header, mobile nav, modal/drawer layering

## Token implementation rules
- Foundation tokens live as CSS custom properties.
- Portal-specific color accents are applied as opt-in modifiers, not hard-coded per page.
- Shell/page/component tokens are layered so old pages can coexist during WP-17D migration.
- Tenant branding may swap top-level brand tokens without changing layout or accessibility.

## Canonical semantic token families
- `--wp17-shell-*` → header/sidebar/background structure
- `--wp17-panel-*` → cards, tables, form sections, metadata blocks
- `--wp17-accent-*` → controlled CTA/emphasis treatment
- `--wp17-grid-*` → engineering-grid background line color/opacity
- `--wp17-focus-*` → keyboard focus ring consistency
- `--wp17-shadow-*` → restrained elevation

## Accessibility guardrails
- Text over glass must always pass readable contrast.
- Accent-only meaning is forbidden; status requires label + icon/chip treatment.
- Focus rings must remain visible against both white and navy surfaces.
- Motion must support reduced-motion preference.
