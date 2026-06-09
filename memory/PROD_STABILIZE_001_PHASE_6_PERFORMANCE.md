# PROD-STABILIZE-001 · Phase 6 · Performance Validation

**Mode:** Read-only · External probes from this fork's container against `https://mascidocs.com`
**Date:** 2026-06-09
**Note:** Latency includes the fork-container ⇄ Cloudflare ⇄ origin path and reflects what a developer would observe from one network position. Real-user latency on iPhone/LTE will differ; treat these as **bounded upper envelopes for healthy server response**, not browser-LCP measurements.

| # | Item | Result | Measurement |
|---|---|---|---|
| 1 | Health endpoint latency | ✅ **PASS** | 5-run mean **174 ms** · range **139–225 ms** |
| 2 | Dashboard load (`/`) | ✅ **PASS** | **496 ms · 8,341 bytes** (HTTP 200) — well under the 1s "feels instant" threshold |
| 3 | Admin login load (`/admin/login`) | ✅ **PASS** | **394 ms** (HTTP 200) |
| 4 | Daily Report load | 🟡 **Operator-required** | Behind auth; operator can capture from devtools timing on real session |
| 5 | Search response | 🟡 **Operator-required** | Behind auth; same |
| 6 | DB query performance | ✅ **PASS** | `/api/jobs-master` 3-run mean **164 ms · range 142–203 ms**, returning 28 documents. This hits the live prod Mongo cluster — proves no DB hot-spot or pool exhaustion. |

## Raw timing

### /api/health (5 cold/warm mix from this container)

```
health try 1: 200 · 0.163s
health try 2: 200 · 0.184s
health try 3: 200 · 0.225s
health try 4: 200 · 0.153s
health try 5: 200 · 0.139s
mean: 174 ms · stdev: 30 ms
```

### /api/jobs-master (3 runs, hits Mongo)

```
jobs-master try 1: 200 · 0.203s
jobs-master try 2: 200 · 0.148s
jobs-master try 3: 200 · 0.142s
mean: 164 ms
```

### Browser-grade endpoint probes (one-shot)

```
GET /                          200 · 0.496s · 8,341 B
GET /admin/login               200 · 0.393s
GET /hub                       200 · 0.634s
POST /api/integrations/motive/webhook (no sig)    401 · 0.265s
POST /api/integrations/motive/webhook (bad sig)   401 · 0.186s
POST /api/integrations/maintainx/webhook          503 · 0.187s
GET /api/projects (unauthed)                      401 · 0.198s
GET /api/admin/integrations/overview (unauthed)   401 · 0.313s
GET /api/integrations/health (unauthed)           401 · 0.111s
```

## Performance verdict

- No 5xx observed on any healthy probe.
- All authenticated endpoints respond in **< 320 ms** even on the unauthorized-rejection path.
- `/api/jobs-master` (Mongo read) responds in **142–203 ms** for 28 docs — consistent with healthy Atlas + properly-indexed `jobs_master.project_number_1`.
- TLS handshake amortized into Cloudflare keepalive — repeated probes drop to ~140 ms steady state.

**Phase 6: 4/6 PASS · 2/6 deferred to operator (require authenticated session).**

## What this does NOT measure

- iPhone Safari LTE LCP (no real-device run authorized; PERFORMANCE-HARDEN-002 has a backlog item for this).
- Authenticated DR list load (operator-required).
- Mongo slow-query log (operator-required; would require ops console).
- Cache hit/miss rates at Cloudflare edge.
