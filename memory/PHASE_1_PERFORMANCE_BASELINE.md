# Phase 1 · Performance Baseline

**Date:** 2026-02-05
**Purpose:** Establish Phase 1 performance envelope for Phase 2 regression comparison.

## Backend

| Metric | Value | Method |
|---|---:|---|
| Boot time (cold import) | **7.29 s** | `time.time()` around `import server` (strict + schedulers off) |
| OpenAPI generation | **1.04 s** | `time.time()` around `app.openapi()` |
| Route count | 1,441 | `[r for r in app.routes if hasattr(r,'endpoint')]` |
| Method count | 1,445 | Sum of `len(r.methods)` |
| OpenAPI paths | 1,264 | `len(app.openapi()['paths'])` |
| Middleware count | 7 | `len(app.user_middleware)` |
| Bytecode fingerprints checked | 9 | `verify_locked_bytecode(app)` |
| Lifecycle steps | 51 | `platform_status.lifecycle.migration_progress` |
| Shutdown steps | 1 | `platform_status.lifecycle.migration_progress` |
| Backend Track 22.* test envelope | 254 tests · **31.55 s** | `pytest tests/test_track_22_*.py --timeout=90 -q` |
| `/api/admin/platform/status` (auth-gated) | HTTP 401 (< 1 s round-trip) | `curl` against preview URL |

## Frontend

| Metric | Value | Method |
|---|---:|---|
| Build tool | `craco build` (CRA 5 · webpack 5) |
| Build result | Compiled with 111 warnings (110 ESLint + 1 Tailwind) · 0 errors |
| Total build output | **48 MB** | `du -sh /app/frontend/build/` |
| JS chunk count | **193** | `ls build/static/js/*.js` |
| Main bundle (gzipped) | **1.14 MB** | `build/static/js/main.19f3be9e.js` |
| Second-largest chunk | **278 kB** | `2872.05051741.chunk.js` |
| Sentry chunk | **157 kB** | `sentry.088cd94a.chunk.js` (isolated) |
| Main CSS (gzipped) | 29.32 kB | `build/static/css/main.41b41ccd.css` |
| Public Home cold-render | UI visible in < 3s (Playwright observation) |

## Cold-load Playwright observations
| Route | Nav+DOM | Console errors | Notes |
|---|---:|---:|---|
| `/` | ~2.5 s | 0 | Preview banner + 3 portal cards fully rendered |
| `/sign-in` | ~2.5 s | 0 | Form + 7 workspace links rendered; 3 known-benign ERR_ABORTED (Class D) |
| `/signin` (404 fallback) | ~2.5 s | 0 | Custom 404 renders correctly |

## Baseline recommendations for Phase 2
- **Do not regress:** boot < 15 s · OpenAPI gen < 3 s · main bundle ≤ 1.14 MB gzipped · Track 22.* envelope < 45 s.
- **Investigate opportunistically (Class F):** Sentry lazy-init (save 157 kB from initial payload) · manual webpack chunk boundaries on the 278 kB chunk.
