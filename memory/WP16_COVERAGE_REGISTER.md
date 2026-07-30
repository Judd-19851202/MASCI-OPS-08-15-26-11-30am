# WP16 Coverage Register

Date: 2026-07-29

## Route-family coverage by portal label
| Portal label | Total routes | Fully exercised | Partial | Blocked (all blocked classes) | Alias | Redirect | Not yet exercised | Notes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |

| Admin | 141 | 18 | 0 | 4 | 0 | 13 | 106 | — |
| PM | 47 | 19 | 0 | 0 | 0 | 0 | 28 | — |
| HR | 32 | 10 | 0 | 10 | 0 | 0 | 12 | Known 403s retained; historical intake now logged as runtime-blocked |
| Safety | 54 | 6 | 0 | 11 | 0 | 5 | 32 | secondary workflow auth gates documented as blocked-auth routes |
| Dispatch | 14 | 11 | 0 | 3 | 0 | 0 | 0 | MaintainX 401 retained; driver detail placeholder logged as missing-data |
| Shop | 26 | 17 | 0 | 4 | 0 | 0 | 5 | manager queue blocked by authorization; asset-care/equipment/trench-repairs degraded |
| Field Leadership | 12 | 11 | 0 | 0 | 0 | 1 | 0 | — |
| Training / Guidance | 8 | 7 | 0 | 0 | 0 | 1 | 0 | — |
| Transportation Ops wrapper | 3 | 1 | 2 | 0 | 0 | 0 | 0 | — |
| Transportation Ops child | 36 | 30 | 0 | 0 | 0 | 6 | 0 | — |
| Driver | 3 | 3 | 0 | 0 | 0 | 0 | 0 | — |
| Executive | 3 | 0 | 0 | 0 | 0 | 3 | 0 | redirect-only inventory remains; concrete executive surfaces were captured under admin-labelled routes |
| Dev | 2 | 0 | 2 | 0 | 0 | 0 | 0 | preview-config block retained from Phase 2 |
| Public / Shared | 99 | 2 | 0 | 0 | 7 | 29 | 61 | Phase 3 public capture started, but most inventory rows remain unreconciled |
