# WP17A Live Punch List

## Open blocker

1. Execute native production deployment of build `bd9bdd2012c4f2e31b57d7390218b20c361c6dcc` (`665ea6071d75dd046905a35dfe8dcea4`).
2. Re-run live production validation of `/api/admin/wp17a/*` governance routes.
3. Reconcile representative live KPI values source → API → UI after the new build is live.

## Closed in this gate

- Preview release package remains green.
- Final WP-17A backend suite remains green.
- Baseline production health smoke passes on the currently live build.
- Release-gate regressions repaired in preview codebase.