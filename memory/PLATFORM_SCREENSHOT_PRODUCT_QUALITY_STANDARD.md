# PLATFORM_SCREENSHOT_PRODUCT_QUALITY_STANDARD

Status: OPEN — PRE-C10 blocking standard

## Acceptance question for every certified screen

Would this exact screen be acceptable as finished production software for MASCI without explaining away anything visible on it?

If NO → FAIL.

## Required product-quality checks

- correct truth
- correct role and project scope
- correct project identity
- correct status semantics
- correct nomenclature and acronym use
- no developer / migration / vendor leakage in operator UX
- no false zero
- no false green
- no stale-as-current
- no persistent blocking overlay
- no broken loading or infinite spinner
- responsive behavior at 390 / 430 / 768 / 1024 / 1440
- accessibility basics: focus, labels, status not color-only, touch targets, contrast

## Runtime gate status in this batch

- product-quality contract upgraded to `wp18db-product-quality-v3`.
- targeted rerun in progress for the previously failing executive portfolio surface after protected-route auth priming hardening.

## Permanent release-block rule

- screenshot product-quality ledger is a release blocker whenever any certified surface is FAIL.