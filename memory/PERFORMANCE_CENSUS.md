# Performance Census

## Mega files (identified · deferred per Track 20.9 doctrine)
- `backend/server.py` — 15,986 lines · Phase-2 split plan (Track 21.x).
- `frontend/src/App.js` — 1,283 lines · Phase-2 route-group extraction (Track 21.y).

## Bundle size
- CRA + craco build (Track 20.9 verified `yarn build` clean in 48s).
- Code-splitting via `React.lazy(() => import(...))` for every route in `App.js`.

## API calls
- 743 frontend api client call sites — spot-checked in Track 20.8 human walkthrough. No N+1 patterns identified.
- Trust-spine event fetches are indexed via `ts_desc_workflow_asc` (Track 15.76B lock).

## Pagination
- Job Photos, Historical Records, Employee Timeline, Incident List — all paginated server-side.

## Startup
- Preview backend cold start ~30s (scheduler init + index ensure + boot-self-heal). Verified post-restart in Track 20.6B execution.

## Classification
- **KEEP** — 100%.
- **FIX** — 0.
- **DEFER** — `server.py` + `App.js` mega-file splits (Track 21.x/21.y).
