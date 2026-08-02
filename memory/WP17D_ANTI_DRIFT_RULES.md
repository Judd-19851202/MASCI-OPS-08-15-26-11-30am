# WP17D Anti-Drift Rules

Last updated: 2026-08-01

## Active Guardrails

### 1. Constitutional Home Guard
- Script: `/app/scripts/wp17d_constitution_guard.py`
- Current protected scope:
  - Home banned terminology regressions
  - duplicate Home sign-in regressions
  - duplicate Home product-identity block above the hero
  - Home local-card implementation regressions
  - explanatory-panel regressions
  - white-header regression on the canonical MASCI header
  - language-control treatment regressions
  - Home brand-block presence in `CanonicalHeader.jsx`
  - MASCI red / stronger-than-product hierarchy styling in `wp17.css`
  - MASCI logo Home behavior contract in `MasciLogo.jsx`
  - `PortalShell.jsx` shared brand propagation contract
  - `FormShell.jsx` shared brand propagation contract
  - UI emoji / unicode-icon shortcuts inside the constitutional Home lane
  - no `Hub` fallback label in `BackLink.jsx`
  - no emoji UI shortcuts in the active Daily Reports list surface
  - no local calculator button styling drift in `MaterialCalculators.jsx`
  - no local daily-report CTA styling drift in `ViewDailyReport.jsx`
  - no local custom dark header in `ViewEquipmentInspection.jsx`
  - governed shared input/select/textarea/button/page-header primitive presence
  - no legacy DVIR toggle or textarea styling drift
  - no legacy daily-report prefill button drift
  - operator-language scan for high-risk operator surfaces (Operations Control, readiness boards, shared admin navigation, portal continuity labels)

## Expansion Plan
These checks must expand during propagation to cover:
- banned visible terminology scan across remaining portal families until the full platform is covered by the operator-language guard
- banned UI emoji / unicode icon scan across user-facing source
- local card implementation scan across migrated routes
- direct-header survivor scan
- local icon-library import scan outside approved shared contexts
- portal label replacement scan so portal names cannot replace the MASCI product identity in shared headers
- duplicate title detection where feasible
- duplicate sign-in detection for representative public/auth flows
- white-header regression checks for shared shells
- logo/Home behavior checks
- Home brand hierarchy screenshot regression
- mobile overflow checks
- representative screenshot regression for Home, Field, Material Calculators, and one archetype per remaining portal family
- local button / local shadow / local spacing / local typography scans should expand family-by-family as each portal wave is polished
- public form-auth edge cases should be documented so expected 401s on protected helper endpoints are not mistaken for visual regressions

## Governance Rule
- A route does not pass because a script passes.
- Anti-drift automation is a gate, not a substitute for visual and functional certification.
- Operator-facing UI must not expose internal engineering, QA, certification, debugging, or project-code language. See `OPERATOR_BANNED_LANGUAGE_REGISTER.md`.