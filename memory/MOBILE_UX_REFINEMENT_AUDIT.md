# Mobile UX Refinement Audit

_Phase V-Prelude · Priority #5 · audit + targeted polish list · 2026-05-28._

## Mission

The superintendent's mobile experience is sacred. This audit
inventories every operator-facing mobile surface and lists
targeted polish items — small, reversible, regression-protected.

**This is not a redesign.** This is the polish list.

## Audit method

For each of the 12 highest-traffic operator surfaces, we
evaluated 7 dimensions:
- Tap target ≥ 44 × 44 px
- No horizontal overflow at 390 × 844
- Drawer / sheet behavior calm
- Upload flow ≤ 3 taps from list view
- Keyboard does NOT obscure save pill
- Scan rhythm: H1 + body fits one mobile screen above the fold
- No frozen / clipped CTA

## Surfaces audited (12)

| # | Surface | Tap targets | Overflow | Drawer | Upload | KB | Rhythm | CTA | Verdict |
|---|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| 1 | `/admin/governance/self-protection` | ✓ | ✓ | n/a | n/a | n/a | ✓ | n/a | 🟢 |
| 2 | `/po-requests` (list + drawer) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 🟢 |
| 3 | `/daily-reports` | ✓ | ✓ | n/a | ✓ | ✓ | ✓ | ✓ | 🟢 |
| 4 | `/inspections/:id` | ✓ | ✓ | n/a | ✓ | ✓ | ✓ | ✓ | 🟢 |
| 5 | `/incidents/:id` | ✓ | ✓ | n/a | n/a | ✓ | ✓ | ✓ | 🟢 |
| 6 | `/meetings/:id` | ✓ | ✓ | n/a | n/a | ✓ | ✓ | ✓ | 🟢 |
| 7 | `/admin` console | ✓ | ✓ | ✓ | n/a | n/a | ✓ | n/a | 🟢 |
| 8 | HR Sign-In | ✓ | ✓ | n/a | n/a | ✓ | ✓ | ✓ | 🟢 |
| 9 | Admin Sign-In | ✓ | ✓ | n/a | n/a | ✓ | ✓ | ✓ | 🟢 |
| 10 | PM Hub | ✓ | ✓ | n/a | n/a | n/a | ✓ | ✓ | 🟢 |
| 11 | Safety Hub | ✓ | ✓ | n/a | n/a | n/a | ✓ | ✓ | 🟢 |
| 12 | Field Leadership intake | ✓ | ✓ | n/a | ✓ | ✓ | ✓ | ✓ | 🟢 |

🟢 **12 / 12 surfaces pass the 7-dimension audit at 390 × 844.**

## Targeted polish items (none deploy-blocking)

These are operator-quality wins that should land alongside
Priority #1 + #2 implementations. Each is < 50 LOC and reversible.

### P1 polish — operator-facing
1. **Save pill above the keyboard on iOS Safari.** The pill should
   `position: sticky` to the visual viewport, not the layout
   viewport. Some surfaces already do; audit confirms 2 surfaces
   that don't (`Constraints` form when it lands · `Field Note`
   form). Polish AT IMPLEMENTATION, not retroactively.
2. **Drawer dismiss via swipe-down.** Currently dismiss is X-button
   only. Adding swipe is ~ 30 LOC via a small `useSwipeDown` hook.
3. **Tap targets on the OPS-1 page status pills.** Currently each
   pill is text-only at 14 px height. Increase to 24 px wrapper
   with same visual density. Calm, no chart creep.
4. **`<input type="number" inputmode="decimal">` on every numeric
   field** (already on most — sweep the remaining 4 fields).

### P2 polish — calm correctness
5. **Search box auto-focus on overlay open.** Saves one tap.
6. **Photo thumbnail lazy-load** below the fold. Already does in
   most lists — sweep the inspection detail page.
7. **Loading skeleton calmness audit.** Replace the 3 skeleton
   bars-of-3-different-widths with a single 24-px row repeat. Less
   visual stutter on slow connections.
8. **Restore prompt button label.** Currently "Restore draft" /
   "Discard". Sweep to "Continue last draft" / "Start fresh" — same
   semantics, friendlier on a 4 a.m. jobsite.

### P3 polish — keyboard ergonomics
9. **Tab order** through long forms — verify ESC dismisses keyboard
   gracefully on every form.
10. **Submit on Cmd-Enter** for the markdown notes field
    (constraints + RFI later).

## What we DELIBERATELY did NOT touch

- ⛔ No new icons. The current Lucide set is sufficient.
- ⛔ No font-stack changes.
- ⛔ No color-palette additions.
- ⛔ No new animations. The platform stays calm.
- ⛔ No bottom-navigation bar experiment.

## Governance hooks

- All polish items individually testable.
- Each item shippable as a single small PR.
- Each item passes Authority + Timestamp probes (no auth /
  timestamp surface touched).
- OPS-1 stays GREEN throughout.

## Phase-V handoff

V.1 RFI MVP forms inherit P1.1 (save pill above keyboard) and
P1.2 (swipe-down dismiss) from day one.

## Stop condition

Audit-only deliverable. No code changes in this phase. Polish
items land alongside Priority #1 + #2 implementations as
side-improvements, not as separate sprints.
