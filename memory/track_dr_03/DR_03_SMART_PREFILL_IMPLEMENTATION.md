# DR-03 Smart Prefill Implementation

## Canonical source
- `GET /api/jobs/{project_number}/recent-context`

## Implemented trigger behavior
- Initial remembered project state in V3 shell
- Project selection / change
- Report-date-aware request keying

## Implemented UX behavior
- Explicit Smart Prefill offer card in V3 shell
- Explicit Restore Setup / Start Fresh actions
- Truthful calm error state when no reusable context or request failure occurs

## Implemented restored fields
- crew identities
- employee IDs
- start / stop / lunch values
- crew hours
- equipment identities / notes / hours-used setup

## Implemented protections
- explicit overwrite confirmation if current setup rows are already non-empty
- stale request-key suppression

## Remaining open item
- Production-style project with actual prior-report data still needs end-to-end proof in preview/field acceptance
