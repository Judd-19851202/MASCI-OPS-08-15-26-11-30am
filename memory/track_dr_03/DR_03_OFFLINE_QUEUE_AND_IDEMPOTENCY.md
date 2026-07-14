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
- Queue entries now retain actor ownership metadata
- Queue exposes targeted cleanup by idempotency key

## Deterministic proof added
- frontend test: `resiliencyQueue.test.js`
  - canonical daily report queue entry preserves actor ownership and canonical form key
  - cleanup by idempotency removes only matching queue item

## Remaining open items
- Full replay-path certification with real queued submit + reconnect in browser automation still pending
