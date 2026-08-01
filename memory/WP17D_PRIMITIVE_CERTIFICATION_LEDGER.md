# WP-17D Primitive Certification Ledger

Last updated: 2026-08-01

## Scope
This ledger tracks shared design primitive families. A primitive family is not considered certified until:
- discovery is complete
- all consumers are known
- no local override breaks the primitive
- visual audit is complete
- functional behavior is complete where applicable
- EN/ES parity is complete where applicable
- responsive behavior is complete where applicable

## Primitive Families

| Primitive Family | Discovery Status | Consumer Reconciliation | Visual Audit | Functional Audit | EN/ES Audit | Responsive Audit | Local Override Audit | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Hero Family | IN_PROGRESS | IN_PROGRESS | IN_PROGRESS | N/A | IN_PROGRESS | IN_PROGRESS | IN_PROGRESS | SURVIVOR_OPEN | Governed hero sweep started across `OperationalPageFrame`, `OperationalOutcomeFrame`, `DetailPageHero`, and `wp17-mission-banner`. |
| Card Family | DISCOVERED | NOT_STARTED | NOT_STARTED | N/A | NOT_STARTED | NOT_STARTED | NOT_STARTED | SURVIVOR_OPEN | Needs platform-wide consumer mapping and local-drift audit. |
| Button Family | DISCOVERED | NOT_STARTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | SURVIVOR_OPEN | Must include hover, pressed, disabled, focus, sticky CTAs, and toolbar actions. |
| Form Controls | DISCOVERED | NOT_STARTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | SURVIVOR_OPEN | Inputs, selects, radios, toggles, date/time, textareas, signature, upload, GPS, camera. |
| Tables | DISCOVERED | NOT_STARTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | SURVIVOR_OPEN | Includes list shells, sticky headers, row actions, overflow menus, exports. |
| Dialogs / Modals / Drawers | DISCOVERED | NOT_STARTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | SURVIVOR_OPEN | Hidden-surface discovery and family mapping still open. |
| Navigation | DISCOVERED | IN_PROGRESS | NOT_STARTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | SURVIVOR_OPEN | Platform-wide route-to-entry-point ledger created; click-path proof still pending. |
| Icons | DISCOVERED | NOT_STARTED | NOT_STARTED | N/A | N/A | NOT_STARTED | NOT_STARTED | SURVIVOR_OPEN | Includes hero icons, card icons, nav icons, action icons, status icons. |
| Alerts / Banners | DISCOVERED | NOT_STARTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | NOT_STARTED | SURVIVOR_OPEN | Includes warnings, errors, success notices, blockers, coaching banners. |
| Empty States | DISCOVERED | NOT_STARTED | NOT_STARTED | N/A | NOT_STARTED | NOT_STARTED | NOT_STARTED | SURVIVOR_OPEN | Needs family-by-family visual and wording audit. |
| Success States | DISCOVERED | IN_PROGRESS | IN_PROGRESS | IN_PROGRESS | IN_PROGRESS | IN_PROGRESS | IN_PROGRESS | SURVIVOR_OPEN | `/thank-you` is under active repair and certification. |
| Loading States / Skeletons | DISCOVERED | NOT_STARTED | NOT_STARTED | N/A | NOT_STARTED | NOT_STARTED | NOT_STARTED | SURVIVOR_OPEN | Requires platform-wide discovery and consistency audit. |

## Immediate Next Actions
1. Finish the Hero consumer sweep and record every consumer route.
2. Reconcile dialog/modal/drawer inventory against the locked platform denominator.
3. Add consumer counts per primitive family.
4. Attach each primitive family to route-level certification only after local override review passes.