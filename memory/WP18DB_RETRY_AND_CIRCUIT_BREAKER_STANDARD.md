# WP-18DB Retry and Circuit Breaker Standard

## Governing principle

Retries are allowed only where they do not create duplicate governed records or hide failure truth.

## Current platform standard (certified in WP-18DB)

1. **Auth / admin paths**
   - fail closed
   - do not retry privileged writes invisibly

2. **Background / async provider calls**
   - bounded retries only
   - surface explicit operator truth when delivery is degraded

3. **PDF / AI / notification assistive paths**
   - degrade safely
   - do not block Tier-0 governed filing

4. **Backup / restore paths**
   - overlap guard remains active
   - runtime evidence must be current before release

## Evidence

- notification delivery certification suite → PASS
- PDF non-blocking suite → PASS
- AI gateway fallback suite → PASS
- admin strict fail-closed suite → PASS

## Executive conclusion

The platform’s current retry behavior is certified only where the canonical truth model remains intact and operator messaging stays explicit.