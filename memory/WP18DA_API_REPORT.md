# WP-18DA API Report

## Preview runtime

- Browser-verified warmed public API latencies:
  - `/api/health` `49ms`
  - `/api/version` `51ms`
  - `/api/job-hazard-files/public/grouped` `141ms`
- Backend verification (`/app/wp18da_test_results.json`):
  - `/api/health` `195ms` on restart verification path, `PASS`
  - `/api/version` `133ms`, `PASS`
  - `/api/job-hazard-files/public/grouped` `142ms`, `PASS`

## Deployed production runtime

- Browser-verified public API latencies:
  - `/api/health` `85ms`
  - `/api/version` `90ms`
  - `/api/job-hazard-files/public/grouped` `132ms`

## Restart behavior

- Preview API routes may return `502` during the backend restart warmup window.
- Warmed steady state recovered automatically after ~`30s` with no manual intervention.

## Output-channel path timings

- Preview CSV export (`/api/po-requests/export.csv?vendor=WP18CZ2 Vendor`): `200`, `2022ms`
- Preview Field Leadership PDF (`/api/field-leadership/{id}/pdf`): `200`, `2248ms`

## Email / provider boundary

- Preview runtime is intentionally safe-captured:
  - `AUTO_EMAIL_REPORTS=false`
  - `EMAIL_SAFETY_MODE=strict`
- Result: application-side email workflows remain measurable at the dispatch boundary, but no live uncontrolled email leaves preview.
