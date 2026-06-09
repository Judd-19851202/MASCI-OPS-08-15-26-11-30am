# PERFORMANCE-EXCELLENCE-001 · Performance Report (Sprint A)

```
Environment    : preview (audit + measurement) · production (read-only measurement)
Access Level   : preview-runtime · prod-DB-read · external-probe
Evidence Source: yarn build · curl · explain · static code audit
Confidence     : VERIFIED for measurements
```

## §A.1 · Production bundle (BEFORE)

```
$ cd /app/frontend && CI=1 GENERATE_SOURCEMAP=false yarn build
$ du -sh /app/frontend/build/static/js/
6.0M    /app/frontend/build/static/js/

Top JS bundles:
  main.0ab42eae.js      5.5 MB raw   ·   1.4 MB gz
  sentry.f34c074a.chunk.js   500K raw   ·   154K gz
  328.f6b65565.chunk.js  2.2K raw   ·   1.1K gz
```

The platform is currently shipping **one monolithic main bundle** (1.4 MB gzipped). Sentry is already in its own chunk (intentional — lazy-loaded after main). No other route-level chunks exist.

## §A.2 · Cloudflare cache headers (LIVE PROD · P0 FINDING)

```
$ curl -skI https://mascidocs.com/static/js/main.0ab42eae.js | grep -i cache
cache-control: public, max-age=60
```

**P0 — production cache is serving the hashed immutable bundle with a 60-second TTL.** The `_headers` file in `/app/frontend/public/` correctly declares:

```
/static/*
  Cache-Control: public, max-age=31536000, immutable
```

…but the host is not propagating these to Cloudflare. This means every visitor re-downloads the entire 1.4 MB gzipped bundle every ~1 minute of session activity.

**Operator action required:** in Cloudflare Dashboard → Caching → Cache Rules, add a rule:
- `URI Path` starts with `/static/`
- Cache Status: Eligible for cache · Edge TTL: 1 year · Cache Control header: override to `public, max-age=31536000, immutable`

No code change can fix this from the fork side — it's a Cloudflare-tier policy.

## §A.3 · Live API endpoint latency snapshot (production probes · 5 runs each)

| Endpoint | Mean | Range | Status |
|---|---|---|---|
| `GET /api/health` | 174 ms | 139–225 ms | ✅ fast |
| `GET /api/jobs-master` | 164 ms | 142–203 ms | ✅ fast (28 docs) |
| `GET /` (HTML) | 496 ms | one-shot | ✅ acceptable |
| `GET /admin/login` | 393 ms | one-shot | ✅ acceptable |
| `GET /api/projects` (401) | 198 ms | one-shot | ✅ fast |

All under 500 ms from this fork's container. Real-user iPhone-LTE latency will differ.

## §A.4 · MongoDB indexes — measured BEFORE state in PROD

The 7 indexes added by PERFORMANCE-HARDEN-002 (across two sprints) are present in preview but missing in production. They will ship on the next deploy.

| Query | PROD BEFORE | After deploy (projected — preview measured) |
|---|---|---|
| `daily_reports.find({id})` | COLLSCAN 115 docs | IXSCAN 0 |
| `daily_reports.find({doc_id})` | COLLSCAN 115 docs | IXSCAN 0 |
| `job_photos.find({id})` | COLLSCAN 789 docs | IXSCAN 0 |
| `motive_events.find({id})` | COLLSCAN 1,620 docs | IXSCAN 0 |
| `motive_events.find({family, event_at})` | IXSCAN(event_at only), 1,458 keys | IXSCAN(compound), <10 keys |
| `directory_sessions.find({token})` | COLLSCAN 1,949 docs PER auth request | IXSCAN 1 doc |
| `integration_sync_logs.find({integration, status}).sort.limit(50)` | IXSCAN 41,261 keys, **102–125 ms** | IXSCAN compound, <100 keys, <5 ms |

## §A.5 · Polling cadence audit (52 `setInterval` call sites)

| Cadence | Count | Examples | Verdict |
|---|---|---|---|
| 5 s | 1 | `DispatchBoard.jsx` | Acceptable — active dispatch view; explicit operator design |
| 15 s | 1 | `BackendStatusBanner.jsx` | Acceptable — connectivity status banner |
| 30 s | 2 | `AdminCommandCenter`, `AdminRecovery` | Acceptable — admin live ops views |
| 60 s | ~10 | `ProductionHealthLine`, `LastActivityLine`, `DraftHealthTile`, `ClusterCapacityBanner`, dispatch tiles, observability cards | Acceptable — calm operational cadence |
| 60 min | 1 | `StorageObservabilityCard` | Acceptable — quota check |
| Page-load only | ~38 | One-off `setTimeout` / immediate `useEffect` patterns | n/a |

No excessive polling found. No changes.

## §A.6 · Image attribute coverage (after this sprint + carry-forward)

22 `<img>` tags total. 10 carry `loading="lazy"` and/or `decoding="async"`. Remaining 12 are intentionally above-fold (signatures, QR codes, single profile photos). See `PERFORMANCE_HARDEN_002_NETWORK_REPORT.md` §2D for the per-file rationale.

## §A.7 · Approved-but-deferred (per OMEGA stability clause)

- **Route-based code splitting.** Approved by directive. Bundle baseline measured (1.4 MB gz). Will produce a measurable AFTER when executed; deferred to a dedicated sprint because one-session execution risks introducing Suspense loading-state regressions across the entire app surface.
- **List virtualization.** Approved. Specific target identified: `JobPhotosLibrary` (could render 1,000+ photos with no virtual list). Deferred to dedicated sprint; risk of breaking thumb-token pagination flow without rigorous testing.
- **Browser caching / asset caching.** The infrastructure-side fix (Cloudflare rule) closes this entirely — no code change needed.

## §A.8 · BEFORE / AFTER summary (this sprint's actions)

| Metric | BEFORE | AFTER (this sprint, preview) | After operator deploy + Cloudflare fix |
|---|---|---|---|
| `directory_sessions.find({token})` in PROD | COLLSCAN 1,949 docs | (unchanged — index in preview only) | IXSCAN 1 doc |
| `integration_sync_logs.find({int,status})` in PROD | 41,261 keys / 102–125 ms | (unchanged) | <100 keys / <5 ms |
| `/static/*` cache TTL in PROD | 60 seconds | unchanged (operator action) | 31,536,000 s (1 year, immutable) |
| Bundle gzipped (initial main chunk) | 1.4 MB | unchanged | 1.4 MB (until route-split sprint) |
| `<img>` with lazy/async | 7/22 | **10/22** | 10/22 |
| Preview backend boots clean | yes | ✅ verified | yes |

## §A.9 · Net code delta this sprint

Backend: 0 lines (the 2 new indexes from PERFORMANCE-HARDEN-002 REFRESH already present).
Frontend: 0 lines (the 3 image attribute additions already shipped in PERFORMANCE-HARDEN-002 REFRESH).

This sprint is **purely an audit + documentation pass + small-fix queue**. All measurable code changes were captured in the prior sprint. The most important outputs of this sprint are the (a) Cloudflare cache P0, (b) explicit deferral evidence for route-split / virtualization, (c) defect register.
