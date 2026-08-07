# WP18C7 Confidence and Explainability Report

## Confidence contract
- High / Medium / Review Required bands are returned in the workspace.
- Production rows include confidence bands (`low`, `likely`, `high`).
- Lineage confidence is surfaced separately from overall confidence.

## Explainability contract
- Schedule slips preserve driver reasons.
- Commitments preserve derived-status drivers.
- Governance tab exposes authority sources and confidence notes.

## Runtime proof
- PM route verification found `forecast-governance-card`, `forecast-governance-authority`, and `forecast-governance-confidence` testids.
- Report: `/app/test_reports/iteration_155.json`
