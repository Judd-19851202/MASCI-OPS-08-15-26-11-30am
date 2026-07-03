# TRACK 19.47 · Mobile / iPad Review

Every Cockpit surface was built against three target viewports.

## Layouts
| Surface | Desktop (>1200px) | iPad landscape (1024×768) | iPad portrait (768×1024) | Mobile (≤640px) |
|---|---|---|---|---|
| Top strip | 6-col grid | 6-col grid | 3-col grid via `md:grid-cols-6` collapse | 2-col grid via `grid-cols-2` |
| Product grid | 3-col via `xl:grid-cols-3` | 2-col via `md:grid-cols-2` | 2-col | 1-col |
| Drawer | 4xl (max ~896px) | Full-height slide-over | Full-height slide-over | Full-screen slide-over |
| History/Audit tables | Native table | Native table | Scroll horizontally within drawer | Scroll horizontally within drawer |
| Buttons | 32px height | 32px height (thumb-safe) | 32px height (thumb-safe) | 32px height (thumb-safe) |

## Overflow contract
- All drawers use `overflow-auto` on the body wrapper.
- Tables use `overflow-auto` on their container wrapper.
- Dedupe keys and long text render inside `<span class="font-mono text-[10px] break-all">` so they never blow out cells.
- The preview iframe uses `min-h-[70vh]` and inherits the drawer's own scroll axis.

## Iframe safety
The preview iframe uses `sandbox=""` (fully restricted) — no scripts,
no forms, no popup. Backend HTML is rendered as static text — safe on
any device.

## Six-Pillar audit (device dimension)
- **Beautiful** — the grid holds together at every breakpoint tested.
- **Trusted** — the sandboxed iframe never breaks the parent page.
- **Operational** — every action button is thumb-safe (min-height 32px)
  and Tailwind's default focus rings provide keyboard accessibility.

## Manual QA plan
1. Open Cockpit on iPad landscape → confirm all 11 cards visible in
   2-column layout without overflow.
2. Open a Preview drawer on iPad portrait → iframe scrolls internally,
   drawer close button reachable in thumb zone.
3. Open a History drawer on iPad landscape → table scrolls horizontally
   inside the drawer if long dedupe keys are present.
4. Load the page on a mobile-width viewport (Chrome DevTools 375×812)
   → confirm no horizontal page overflow and all cards stack in a
   single column.

## Explicit non-goals
This track does not ship a mobile-native shell (that is P3 on the
platform roadmap). The Cockpit is optimised for desktop and iPad; the
mobile view is "readable but not thumb-optimised" by design.
