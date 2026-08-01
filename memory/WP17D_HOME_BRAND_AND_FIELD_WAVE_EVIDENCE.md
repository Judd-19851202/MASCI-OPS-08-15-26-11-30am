# WP17D Home Brand Hierarchy + Field Operations Wave 01 Evidence

Last updated: 2026-08-01

## Scope
- Home brand-hierarchy correction
- Shared shell identity propagation through applicable header wrappers
- First Field Operations propagation wave (`/field`, `/field/calculators`)

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

### Shared Shell Identity Propagation
- `CanonicalHeader.jsx` now renders the MASCI / Operations Platform brand block for shell-based routes, not just Home
- `PortalShell.jsx` now passes a secondary context label instead of letting portal labels replace the product identity
- `FormShell.jsx`, `PortalLoginShell.jsx`, `PublicShell.jsx`, and `OperationalPageFrame.jsx` now follow the same contract

### Field Operations Wave 02
- `/field/calculators` now inherits the shared global header identity
- duplicate shell subtitle strip removed
- summary migrated to governed `InformationCard`
- tab controls moved onto governed CTA styling
- all six calculator work areas wrapped in shared `Card` panels

### Field Operations Wave 03 · Executive Elite Polish
- `/admin/daily` polished onto governed summary-card, section-heading, shared button, and normalized metadata rhythm
- `/admin/equipment-inspections` polished onto governed summary-card, badge, and list-shell rhythm
- `/admin/equipment/:id` removed the custom dark local header and adopted governed content/action rhythm
- shared primitives refined: `PageHeader.jsx`, `wp17.css`, `BackLink.jsx`, `SubmitLangBadge.jsx`

## Responsive Evidence
- Home verified at `390`, `430`, `768`, `1024`, `1440`
- Field verified at `390`, `430`, `768`, `1024`, `1440`
- Material Calculators verified at `390`, `430`, `768`, `1024`, `1440`

## Formal QA Evidence
- `/app/test_reports/iteration_101.json`
  - Home header hierarchy verified
  - no duplicate hero identity
  - MASCI logo returns Home from `/field`
  - `/field` confirmed on governed shared cards / headings
  - zero horizontal overflow at `390`, `430`, `768`, `1024`, `1440`
  - zero console errors
- `/app/test_reports/iteration_102.json`
  - global MASCI brand hierarchy verified on `/`, `/field`, and `/field/calculators`
  - no portal-specific replacement identity on shared shell routes
  - calculators summary/tabs/panels verified after shared-component migration
  - zero horizontal overflow at `390`, `430`, `768`, `1024`, `1440`
  - zero console errors
- `/app/test_reports/iteration_103.json`
  - elite Field polish verified on `/`, `/field`, `/field/calculators`, `/admin/daily`, `/admin/equipment-inspections`, and `/admin/equipment/:id`
  - no emoji UI shortcuts, no local calculator button drift, no local daily-report CTA drift, no local equipment dark header
  - authenticated admin preview verification passed with Super Admin fixture
  - zero console errors

## Final Browser Verification
- `auto_frontend_testing_agent` verified `/`, `/field`, and `/field/calculators`
- Result: executive requirements met; no fixes required

## Anti-Drift Protection
- Guard script: `/app/scripts/wp17d_constitution_guard.py`
- New protections include:
  - duplicate hero identity regression
  - Home brand block presence
  - Home hierarchy styling checks
  - logo Home behavior contract
  - `PortalShell.jsx` shared brand propagation contract
  - `FormShell.jsx` shared brand propagation contract