# PLATFORM_DESTRUCTIVE_ACTION_SAFETY_STANDARD

Status: OPEN — PRE-C10 blocking standard

## Runtime rule

Destructive or recovery controls must be justified, clearly scoped, and visually subordinate to operational health.

## Required protections

- explicit role gate
- clear warning copy
- narrow scope description
- confirmation step
- audit trail
- no casual placement on primary operator screens

## Current open concerns

- Force Re-Seed must be proven necessary, hardened to emergency-only, or removed.
- Admin recovery controls must sit below operational health and diagnostics.
- no destructive production control may appear as a casual convenience action.