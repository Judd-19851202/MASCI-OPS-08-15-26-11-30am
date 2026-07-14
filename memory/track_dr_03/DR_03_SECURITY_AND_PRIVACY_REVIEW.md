# DR-03 Security and Privacy Review

## Implemented protections
- Stable actor identity now scopes crew memory and remembered project state
- Canonical draft scope now includes actor identity, reducing cross-user collision risk
- Shared-device cross-actor draft offering remains blocked by `useFormDraft()` contract
- No new telemetry fields include raw form contents

## Not changed
- No auth roles widened
- No database schema changed
- No secrets introduced into drafts or telemetry

## Remaining open item
- Full end-to-end security review across downstream search/viewer/export surfaces remains pending
