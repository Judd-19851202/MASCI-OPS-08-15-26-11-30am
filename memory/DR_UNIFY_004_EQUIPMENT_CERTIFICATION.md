# DR-UNIFY-004 · Equipment Certification

**Claim:** Equipment lookup, DVIR, pre-op, hours, idle/run hours, maintenance, and shop integration behave identically.

## Preserved surfaces

- `equipment[]` rows on `daily_reports` — schema unchanged.
- Equipment lookup component — unchanged.
- DVIR and pre-op checklists — unchanged.
- Operator hours / idle hours / run hours — unchanged.
- Maintenance and shop-portal integrations — unchanged (no changes this session).

## Composer behaviour

- DR-CUTOVER-002 composer surfaces equipment names + operating hours
  in the summary when equipment rows are present. It never modifies
  equipment data.

## Regression evidence

- Lock test `test_enabled_path_returns_deterministic_composed_summary`
  asserts equipment names (e.g., "CAT 335F Excavator", "930M Loader")
  appear verbatim in the composed summary — proves the composer reads
  the correct fields without mutation.
- HR CSV export path (which shares crew + equipment context)
  unchanged.

**Verdict:** Equipment subsystem certified.
