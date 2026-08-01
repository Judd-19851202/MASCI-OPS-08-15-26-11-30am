# WP17D Card Variant Register

Last updated: 2026-08-01

## Purpose
This register defines the governed card families that now form the shared MASCI Operations Platform card system. Routes should consume one of these families before adding any new local card styling.

## Shared Families

### ModuleCard
- Use for primary entry modules or major operational destinations
- Examples: Field, QA/QC, Safety on Home
- Design defaults: feature-size title scale, stronger presence, shared accent bar, shared icon tile, governed CTA footer

### WorkflowCard
- Use for restricted operational areas, workflow launchers, and medium-density destination cards
- Examples: operations workspace cards, Field Leadership
- Design defaults: default-size title scale, compact descriptive rhythm, governed lock/title suffix support

### ActionCard
- Use for single next-step cards, welcome-back cards, start-here cards, and promoted actions
- Examples: Home welcome-back, first-week start card
- Design defaults: compact rhythm, stronger action emphasis, minimal explanation

### InformationCard
- Use for support, help, guidance, and passive informational destinations with clear action follow-through
- Examples: Need Help, Guidance, Cheat Sheet
- Design defaults: compact informational tone with the same structural DNA as the rest of the family

### ExternalPlatformCard
- Use for governed external brand launches that preserve official logos inside a shared container architecture
- Examples: Basecamp, OnStation, ForgedOps Plans cluster
- Design defaults: shared card shell, governed launcher sub-architecture, consistent external-link treatment

### DetailCard
- Use for detailed operational summaries, read-only record overviews, or rich surface summaries when propagation requires a deeper card variant

### FormSectionCard
- Use for governed multi-section forms and grouped workflow data entry regions when a dedicated form-card wrapper is needed

### AlertCard
- Use for high-importance warning, blocked, or urgent attention surfaces where standard information or workflow cards are not sufficient

## Rules
- All families inherit the same core MASCI DNA: spacing scale, radius scale, border logic, elevation, typography family, icon alignment, focus state, hover state, and footer logic.
- No new route-local card styling should be introduced if one of these families can serve the need.
- If a new legitimate family is required, add it here first, then implement it in shared code.