# WP16 Coverage Register

Date: 2026-07-29

## Phase 1 checkpoint
- Coverage reporting has been normalized from overlapping summary labels into one final route classification per discovered route.
- Exact route total remains **480** and reconciles 1:1 with `WP16_ROUTE_CENSUS_RAW.json` and the enriched Screen Registry.

## Exact route classification totals
| Classification | Exact total | Qualification |
| --- | ---: | --- |
| FULLY_EXERCISED | 13 | Opened, visually inspectable, and not materially limited by defects in the captured baseline state. |
| PARTIALLY_EXERCISED | 1 | Opened, but some meaningful sub-surface remained limited during inspection. |
| BLOCKED_API_FAILURE | 2 | Route opened, but API/data failures materially blocked full inspection. |
| ALIAS_ROUTE | 7 | Synthetic detail-route alias redirecting to a canonical route with carried-through identifier context. |
| REDIRECT_ONLY | 58 | Legacy or convenience route that immediately redirects and does not present its own distinct UI surface. |
| NOT_YET_EXERCISED | 399 | Route-backed surface still awaiting direct evidence. |

## Portal summary by final route classification

| Portal / experience section | Total routes | Fully exercised | Partially exercised | Blocked API failure | Alias routes | Redirect-only routes | Not yet exercised | Screenshot-backed |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Admin | 141 | 3 | 0 | 0 | 0 | 13 | 125 | 3 |
| PM | 47 | 2 | 0 | 0 | 0 | 0 | 45 | 2 |
| HR | 32 | 1 | 0 | 2 | 0 | 0 | 29 | 3 |
| Safety | 54 | 2 | 0 | 0 | 0 | 5 | 47 | 2 |
| Dispatch | 14 | 1 | 1 | 0 | 0 | 0 | 12 | 2 |
| Shop | 26 | 2 | 0 | 0 | 0 | 0 | 24 | 2 |
| Field Leadership | 12 | 0 | 0 | 0 | 0 | 1 | 11 | 0 |
| Training / Guidance | 8 | 0 | 0 | 0 | 0 | 1 | 7 | 0 |
| Transportation Ops wrapper | 3 | 0 | 0 | 0 | 0 | 0 | 3 | 0 |
| Transportation Ops child | 36 | 0 | 0 | 0 | 0 | 6 | 30 | 0 |
| Driver | 3 | 0 | 0 | 0 | 0 | 0 | 3 | 0 |
| Executive | 3 | 0 | 0 | 0 | 0 | 3 | 0 | 0 |
| Dev | 2 | 0 | 0 | 0 | 0 | 0 | 2 | 0 |
| Public / Shared | 99 | 2 | 0 | 0 | 7 | 29 | 61 | 2 |

## Reconciliation notes
- Earlier closeout numbers (`14 fully exercised`, `3 partially exercised`, `2 blocked`, `464 not yet exercised`) were **overlapping observational metrics**, not singular route classes.
- Phase 1 resolves that contradiction by assigning every route exactly one final classification.
- Transportation workspace child routes now reconcile cleanly because the registry stores their **exact raw child route pattern** plus mounted-context metadata, instead of embedding the mounted note inside the route string itself.

## Remaining evidence gap summary after Phase 1
- Screenshot-backed route-backed surfaces: **16**
- Desktop-backed surfaces: **16**
- Tablet-backed surfaces: **0**
- Mobile-backed surfaces: **0**
- Zero-evidence portal sections still pending Phase 2: **7** — Field Leadership, Training / Guidance, Transportation Ops wrapper, Transportation Ops child, Driver, Executive, Dev
