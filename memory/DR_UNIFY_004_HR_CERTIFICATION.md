# DR-UNIFY-004 · HR Certification

**Claim:** HR crew-time, employee IDs, payroll export, and time
verification behave identically to last week's production.

## Data path

- Source of truth: `masci_crews[]` on each `daily_reports` document.
- HR endpoints read `daily_reports.masci_crews`. Neither DR-CUTOVER-002
  summary endpoints nor AI-ADMIN-001 endpoints ever read or write
  this field.

## Regression evidence

- `test_accept_persists_summary_onto_daily_report_doc` — asserts
  `masci_crews` is byte-identical before and after a summary accept.
- `test_accept_never_writes_a_provider_key_or_token_field` — asserts
  adversarial `masci_crews` field on accept body is silently
  dropped (allow-list gate).
- Live V1 submit accepts full crew rows (CERT-8).

## Preserved HR surfaces

- `/api/hr/time-verification` — unchanged.
- HR CSV export — unchanged.
- Payroll integration — unchanged.
- HR Portal (Admin → HR) — unchanged.

## No new HR fields required

- The summary section adds no HR-relevant fields.
- The Admin AI Configuration page does not read or write HR data.

**Verdict:** HR subsystem certified.
