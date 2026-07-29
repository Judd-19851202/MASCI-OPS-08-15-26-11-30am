# WP15 Certification Suite Modernization

Last updated: 2026-07-29
Status: Active

## Summary
The legacy broad certification sweep contained stale assumptions about:
- retired admin/FL login contracts
- stale multi-login response shapes
- stale data endpoint payload shapes
- stale target base URL fallback
- backend-served public routes no longer present in the canonical surface

## Actions Completed
- Modernized `backend/tests/test_full_cert_auth_sweep.py`
- Replaced stale fallback preview URL with current in-pod canonical backend target by default
- Updated login expectations to current canonical contracts
- Updated payload expectations to current envelope shapes (`items`, `count`, etc.)
- Explicitly treated retired/legacy login paths as retired compatibility behavior rather than active canonical behavior

## Current Result
- `pytest /app/backend/tests/test_full_cert_auth_sweep.py -q` → **40 passed**

## Remaining Work
- Expand certification coverage to emergency overrides, lockout/recovery, and broader session-expiry flows
- Add deeper governed-domain success/denial assertions beyond auth and surface checks