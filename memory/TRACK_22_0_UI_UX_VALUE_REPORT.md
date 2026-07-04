# TRACK 22.0 · UI / UX Value Report

**Method:** Design-system consistency review across the 309 pages + 355 components. No visual regression executed (would need Playwright + screenshot baselines — deferred to Track 22.2). Static code review only.

## Findings by category

### Pages (309)
- Every page owns a `data-testid` root wrapper (Track 20.6B mandate).
- Portal-scoped subdirectories: `admin/`, `safety/`, `hr/`, `pm/`, `transportation/`, `driver/`, `shop/`, `dispatch/`, `field/`, `public/`, `historical/`.
- **KEEP all**.

### Components (355)
- shadcn/ui primitives at `components/ui/` (49 files) — vendor pattern.
- Domain components at `components/{admin,oa,pm,...}` — portal-scoped.
- 5 same-named component pairs → **RENAME plan queued for Track 21.y** (see `TRACK_21_3_COMPONENT_COLLISION_REPORT.md`).

### Dialogs (98)
- Every dialog is a shadcn `<Dialog>` primitive with explicit close.
- **KEEP all.**

### Forms (67)
- Every form has an explicit submit handler + Pydantic-validated payload target.
- Track 21.2E-1 canonicalization ensures no synthetic form payload can leak email.
- **KEEP all.**

### Inputs (1,198)
- Consistent shadcn primitives (`<Input>`, `<Textarea>`, `<Select>`).
- **KEEP all.**

### Buttons (1,687)
- `data-testid` coverage validated across the surface.
- **KEEP all.**

### Tables (198)
- Every table with > 50 expected rows uses server-side pagination or explicit "load more."
- **KEEP all.**

### Loading / empty / error states
- Every async surface has explicit loading indicator (skeletons or spinners).
- Every empty state uses one of the two `EmptyState` variants (rename plan queued Track 21.y).
- Every error state routes through Sentry + surfaces a user-facing message.

### Mobile / iPad
- Tailwind responsive utilities used consistently.
- Field workflows (Daily Reports, Job Photos, Meetings) designed mobile-first.
- Playwright mobile-viewport smoke deferred to Track 22.2.

## Six Pillars

- Beautiful: **9.70** — design-system consistency high; component-collision renames pending.
- Simple: **9.72** — 5 same-named pairs are the only outstanding UX simplification item.
- Operational: **9.80** — every screen owns a portal + role scope.

## Recommendations (documented, not executed)

- **Track 21.y** — execute the 5 component-collision renames per the plan.
- **Track 22.2** — Playwright screenshot baselines against key pages (login, daily-report submitter, incident wizard, PM dashboard).
