# WP18C9 Project Comparability Standard

Date: 2026-08-07  
Status: PASS

## Financial Comparability
- Included: BAC, PV, EV, AC, ETC, EAC.
- Derived only after aggregation: CPI, SPI.
- Explicitly forbidden: averaging project CPI or averaging project SPI.
- Preview result on 2026-08-07: 43 scoped executive projects, with 10 financially comparable project snapshots for the current portfolio totals.

## Schedule Comparability
- Allowed: count of projects with slips, count of projects past commitment, project-by-project likely-vs-committed finish delta.
- Forbidden: averaging finish dates into a fake portfolio finish.

## Production Comparability
- Allowed: roll up quantities only within the same unit bucket.
- Forbidden: adding unlike units together to make one headline number.

## Commitment and Constraint Comparability
- Allowed: counts of at-risk, missed, met commitments; counts of open constraints; cost exposure totals where the upstream forecast supplies money values.

## Confidence and Freshness
- `fresh`: project updates within the active freshness window.
- `watch`: project updates are aging and should be reviewed soon.
- `stale` or `missing`: project records stay visible but cannot be interpreted as healthy by default.

## Operator Interpretation Rule
Every portfolio value must answer five plain-language questions: what is shown, what it means, whether something is wrong, why it is wrong, and what should happen next.
