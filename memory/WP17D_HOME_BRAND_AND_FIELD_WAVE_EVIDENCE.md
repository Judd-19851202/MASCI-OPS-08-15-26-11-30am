# WP17D Home Brand Hierarchy + Field Operations Wave 01 Evidence

Last updated: 2026-08-01

## Scope
- Home brand-hierarchy correction
- First Field Operations propagation wave (`/field`)

## Implemented Corrections

### Home
- Permanent header identity now reads:
  - `MASCI` (governed red, stronger weight)
  - `Operations Platform` (subordinate neutral line)
- Duplicate hero product-name eyebrow removed
- Hero begins directly with `One System. Every Crew. Every Job.`
- Single visible `Sign in` remains header-owned
- MASCI logo keeps Home navigation behavior

### Field Operations Wave 01
- `/field` rebuilt from local tiles onto governed shared card families
- Shared `SectionHeading` adopted for numbered route sections
- Duplicate shell summary block removed

## Responsive Evidence
- Home verified at `390`, `430`, `768`, `1024`, `1440`
- Field verified at `390` and desktop smoke widths during implementation, then in formal QA coverage

## Formal QA Evidence
- `/app/test_reports/iteration_101.json`
  - Home header hierarchy verified
  - no duplicate hero identity
  - MASCI logo returns Home from `/field`
  - `/field` confirmed on governed shared cards / headings
  - zero horizontal overflow at `390`, `430`, `768`, `1024`, `1440`
  - zero console errors

## Final Browser Verification
- `auto_frontend_testing_agent` verified `/` and `/field`
- Result: executive requirements met; no fixes required

## Anti-Drift Protection
- Guard script: `/app/scripts/wp17d_constitution_guard.py`
- New protections include:
  - duplicate hero identity regression
  - Home brand block presence
  - Home hierarchy styling checks
  - logo Home behavior contract