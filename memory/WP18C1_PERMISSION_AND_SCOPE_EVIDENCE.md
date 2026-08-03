# WP18C1 Permission and Scope Evidence

Date: 2026-08-03

## Scope foundation result

WP-18C1 preserved current permission enforcement and added hierarchy-aware scope foundations without changing live role behavior.

## What stayed unchanged

- authentication
- MFA
- passkeys
- session handling
- role and permission enforcement
- existing admin / PM / HR / field / safety / QA/QC / transportation / dispatch / shop workflow access

## What was added

- hierarchy-aware scope preview endpoint
- company / division / department / region / project scope foundations
- node-level inheritance fields for configuration, permissions, reporting scope, localization defaults, notification rules, assignment eligibility, and portfolio visibility

## Runtime evidence

- scope preview current identity count: `27`
- sample scope behavior verified for current admin identities:
  - company scope: `masci`
  - division scope: `division:operations`
  - project scope: preserved from current identity/project linkage where present

## Safety checks performed

- no privilege expansion detected on hierarchy APIs
- no privilege loss detected for existing admin governance access
- no cross-project leakage observed in current admin UI verification
- no cross-division leakage observed in current admin UI verification
- no confidential HR or financial visibility was expanded by WP-18C1

## Result

Permission safety remained intact while the hierarchy-aware scope foundation was successfully established for later WP-18C phases.