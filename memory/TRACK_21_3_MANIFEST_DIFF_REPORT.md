# TRACK 21.3 · Manifest Diff Report

**Date:** 2026-07-04

## Manifest before → after

| Metric | Pre-21.3 | Post-21.3 | Delta | Explanation |
|---|---|---|---|---|
| Tracked files (git ls-files) | 6,969 | +7 | +7 | 6 new Track 21.3 memory docs · 1 new lock test · 1 `.env.example` |
| Backend endpoints (runtime FastAPI) | 1,440 | 1,440 | 0 | No endpoints added/removed. |
| Frontend routes (App.js) | 385 | 385 | 0 | No route changes. |
| Frontend lazy imports | 180 | 180 | 0 | No lazy-import changes. |
| Pages | 309 | 309 | 0 | No page changes. |
| Components | 355 | 355 | 0 | Component collision plan documented; zero merges executed. |
| Dialogs | 98 | 98 | 0 | |
| Forms | 67 | 67 | 0 | |
| Buttons | 1,687 | 1,687 | 0 | |
| Inputs | 1,198 | 1,198 | 0 | |
| Tables | 198 | 198 | 0 | |
| Email dispatch sites | 29 | 29 | 0 | |
| Upload endpoints | 23 | 23 | 0 | |
| PDF modules | 24 | 24 | 0 | |
| Schedulers (`create_task`) | 31 | 31 | 0 | |
| Mongo collection refs | 328 | 328 | 0 | |
| CORS `allow_methods` | `["*"]` | 7 explicit | tightened | Class-C debt closed. |
| CORS `allow_headers` | `["*"]` | 12 explicit | tightened | Class-C debt closed. |
| CORS `expose_headers` | (none) | 4 explicit | added | Frontend reads Content-Disposition, ETag, etc. |
| Lock tests (Track 20.6B → present) | 120 | **132** | +12 | Track 21.3 permanent guardrail. |
| Debt register open Class-C entries | 8 | **4** | -4 | Closed: TD-21.2-C05 · TD-21.2E1-C01 (retire-with-plan) · TD-21.2-C04 (reclassified). CORS wildcard debt (was platform-level). |

## Verdict

**Zero runtime behavior drift.** Every delta is either documentation, a new lock test, or a strictly-narrower CORS allow-list that echoes the frontend's actual usage.
