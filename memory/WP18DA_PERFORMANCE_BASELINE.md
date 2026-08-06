# WP-18DA Performance Baseline

Date: 2026-08-06

## Evidence classes

- **Source / workspace**
  - Frontend route inventory from `frontend/src/app/routing/AppRoutes.jsx`: `462` routes
  - Backend route decorators across `/app/backend/**/*.py`: `1850`
  - Singleton scheduler registrations from source: `18`
  - Production build duration: `50.53s`
  - Production build output: `55,126,489` bytes total (includes sourcemaps + static media)
- **Preview runtime**
  - Home navigation: `domContentLoaded 926ms`, `loadEventEnd 1682ms`, `responseEnd 117ms`
  - WARM public API browser fetches:
    - `/api/health` `49ms`
    - `/api/version` `51ms`
    - `/api/job-hazard-files/public/grouped` `141ms`
  - Restart warmup observation: public API paths returned 502 during backend restart window, then stabilized to `200` after ~`30s`
- **Deployed production runtime**
  - Home navigation: `domContentLoaded 1071ms`, `loadEventEnd 1075ms`, `responseEnd 300ms`
  - Public API browser fetches:
    - `/api/health` `85ms`
    - `/api/version` `90ms`
    - `/api/job-hazard-files/public/grouped` `132ms`

## High-level baseline conclusion

1. Preview shell performance is now faster than production on first paint / route shell load.
2. Public API latency is within sub-`210ms` on both preview and production for the measured public platform paths.
3. The meaningful preview instability was restart warmup, not steady-state latency.
