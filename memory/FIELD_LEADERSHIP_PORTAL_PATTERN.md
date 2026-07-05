# Field Leadership Portal Pattern — Doctrine

**Locked**: TRACK 22.4a · 2026-07-05
**Status**: Reference model for future portal work.

The Track 22.4 Per-Portal Deep Reality Audit scored Field Leadership hub
**8.6 / 10** — the highest of any authenticated portal, and effectively
tied with Trench Safety (8.7) among all surfaces. This memo captures why,
so PM, Dispatch, Admin, Safety, HR, and Shop can steal from it deliberately
instead of accidentally.

## Ten Rules

1. **Single-purpose card set.** Each card does one role-native thing: coach
   a person, write them up, log attendance, recognize excellence, evaluate
   a new hire, evaluate a crew, recommend a promotion, log a training
   deficiency, capture supervisor notes. No card is a dashboard.

2. **No sidebar.** The hub is a *single view*. No hunting. No nested
   navigation. If a role needs three clicks to start work, the hub is
   wrong.

3. **No dashboard clutter.** Zero "KPI grid at the top." The role does not
   arrive to *look at numbers*; the role arrives to *do work*. Any KPI in
   the field-leadership space must earn its position by naming an action.

4. **No copied metrics.** Cards do not reflect PM cost data or HR
   compliance data or Safety CAPAs. Each portal owns its own truth. Cross-
   portal reads are labelled and scoped.

5. **Recent operational memory.** A single strip at the bottom of the hub
   shows the last few actions the role took, so the operator has continuity
   between sessions. Never longer than 5 rows.

6. **Primary actions visible without scroll.** On a phone, on an iPad, on
   a desktop — the first tap zone answers the mission.

7. **Calm empty states.** No spinners that never stop. No "loading OI
   signals" limbo. Empty means *empty* and says so in one sentence.

8. **Mobile-safe by construction.** Cards flow, stack, and remain
   tappable at 390 × 844. Text wraps. Icons scale. No horizontal
   overflow.

9. **Role-native language.** The tiles say "Verbal Coaching" and "New
   Employee Evaluation" — not "Interaction Type 3" and "Assessment Form
   B". Language matches how the field talks about the work.

10. **Zero drift.** No `V2`, no `Next Generation`, no experimental copy,
    no orphan routes. If a card exists, it belongs.

## Anti-Patterns to Avoid

- ❌ "Loading OI signals…" as first render on a role's home.
- ❌ Two contradictory attention counts on the same screen.
- ❌ Sidebars with 30+ items across 7+ collapsed sections.
- ❌ Cross-portal counts wired to the wrong source.
- ❌ Cards that lead outside the hub without breadcrumb.
- ❌ Buttons that do nothing (dead actions).
- ❌ Copy that promises live data when the underlying integration is
  UNREACHABLE.
- ❌ Desktop-only layouts leaking into 390px viewports.

## How to Apply to Other Portals

- **PM**: consolidate Overview + Command Center. Kill the sidebar
  duplication. Make Section A ("My Projects") the tap zone; hide
  everything else behind clearly-labelled tabs.
- **Dispatch**: one attention number. One map. One roll-off action.
  Fewer tabs on the primary route.
- **Admin**: default-collapsed sidebar sections. Promote favourites.
  Trust surface consolidated to Integration Truth as canonical.
- **Safety**: keep the queue-first layout, but wire Trench Safety count
  to canonical source.
- **HR**: preserve the compliance queue — it is already this pattern.
- **Shop**: preserve the "Pick up where the shop left off" strip — it
  is already this pattern.

## What Not to Do With This Pattern

- Do not force it onto every portal. Admin needs configuration surfaces
  the Field Leadership hub deliberately excludes.
- Do not delete rich portals (PM Command Center) just because Field
  Leadership is simpler. Different roles need different information
  densities.
- Do not use this memo as license to rebuild every portal now. Track
  22.4a's mission is *trust repair*, not *redesign*. Apply the pattern
  only where a P1 finding forces the touch.
