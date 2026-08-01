# WP17D Anti-Drift Rules

Last updated: 2026-08-01

## Active Guardrails

### 1. Constitutional Home Guard
- Script: `/app/scripts/wp17d_constitution_guard.py`
- Current protected scope:
  - Home banned terminology regressions
  - duplicate Home sign-in regressions
  - Home local-card implementation regressions
  - explanatory-panel regressions
  - white-header regression on the canonical MASCI header
  - language-control treatment regressions
  - UI emoji / unicode-icon shortcuts inside the constitutional Home lane

## Expansion Plan
These checks must expand during propagation to cover:
- banned visible terminology scan across portal families
- banned UI emoji / unicode icon scan across user-facing source
- local card implementation scan across migrated routes
- direct-header survivor scan
- local icon-library import scan outside approved shared contexts
- duplicate title detection where feasible
- duplicate sign-in detection for representative public/auth flows
- white-header regression checks for shared shells
- logo/Home behavior checks
- mobile overflow checks
- representative screenshot regression for Home and one archetype per portal family

## Governance Rule
- A route does not pass because a script passes.
- Anti-drift automation is a gate, not a substitute for visual and functional certification.