# WP-18C8 EN / ES / Accessibility Certification

Date: 2026-08-07
Result: PASS

## English / Spanish

- New C8 PM and Executive surfaces were written through the existing `useT()` translation path for user-facing strings.
- A live ES toggle smoke check passed on the PM earned-value route after login.
- Language-neutral metric abbreviations (BAC, PV, EV, AC, CPI, SPI, ETC, EAC, TCPI) remain unchanged across languages by design.

## Accessibility checks

- Buttons, links, tabs, selectors, inputs, and critical tables expose explicit `data-testid` hooks and semantic HTML controls.
- Status is not color-only; every readiness / confidence / KPI state also renders text badges.
- First-load recovery removed the need for a hidden manual refresh workaround.
- The PM budget trust-link review lane uses native `<select>`, `<input>`, `<textarea>`, and `<button>` controls.

## Keyboard / focus

- Tabs, buttons, and form controls inherit existing shell keyboard behavior.
- No custom focus trap was added in C8.
- No blocking keyboard issue was reported by automated frontend verification.

## Limits / notes

- This package does not introduce a new PDF document or email body, so those channels were not part of keyboard/accessibility scope.
- The app inherits the broader MASCI shell contrast and focus styles; C8 did not override them.

## Final result

WP-18C8 passes EN/ES/accessibility certification for the implemented operator surfaces.