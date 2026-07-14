# DR-03 Offline Queue and Idempotency

## Implemented
- V3 now persists idempotency by canonical scoped form key
- V3 now queues canonical fields:
  - `url`
  - `body`
  - `idempotencyKey`
  - `formKey`
- Queue settle callback now listens on the canonical idempotency key
- Offline submit now emits canonical lifecycle telemetry and preserves draft until replay settles

## Remaining open items
- Full replay-path certification with real queued submit + reconnect still needed in broader regression matrix
- Cross-route canonical cleanup proof still pending
