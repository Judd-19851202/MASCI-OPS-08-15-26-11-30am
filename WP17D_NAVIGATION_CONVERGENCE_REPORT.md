# WP-17D Navigation Convergence Report

## Current status
IN PROGRESS

## Current ledger counts
- total surfaces: `1190`
- implemented: `640`
- migrating: `453`
- redirected: `53`
- hidden: `44`

## Wave actions already applied
- `PortalShell` now defaults to the WP-17D canonical shell layer.
- Public entry links, Admin navigation, PM navigation, HR navigation, Safety navigation, and Transportation navigation are being converged onto one governed shell model.
- Transportation duplicate-nav pressure is being reduced by keeping sidebar as the primary navigation surface and relegating subnav to smaller-screen contextual use.

## Remaining work
- Sweep every portal/family against the `253` navigation-item denominator.
- Remove duplicate destinations, unreachable items, and legacy aliases that still leak into active navigation.
- Certify mobile/desktop active-state parity.
