# TRACK 22.0 · Manifest Diff Report

| Metric | Pre-22.0 | Post-22.0 | Delta | Reason |
|---|---|---|---|---|
| Tracked files (git ls-files) | 6,982 (post-21.3) | +13 | +13 | 12 Track 22.0 memory docs + 1 lock test |
| Runtime FastAPI endpoints | 1,440 | 1,440 | 0 | No route additions |
| Frontend routes | 385 | 385 | 0 | No route additions |
| Frontend lazy imports | 180 | 180 | 0 | — |
| Pages | 309 | 309 | 0 | — |
| Components | 355 | 355 | 0 | — |
| Dialogs / forms / buttons / inputs / tables | unchanged | unchanged | 0 | — |
| Email dispatch sites | 29 | 29 | 0 | — |
| Upload endpoints | 23 | 23 | 0 | — |
| PDF modules | 24 | 24 | 0 | — |
| Scheduled tasks | 31 | 31 | 0 | — |
| Mongo collection refs | 328 | 328 | 0 | — |
| CORS allow_methods | explicit 7 | explicit 7 | 0 | — |
| CORS allow_headers | explicit 12 | explicit 12 | 0 | — |
| Lock tests | 133 | **145** | +12 | Track 22.0 permanent guardrail |
| Debt register open C entries | 4 | **4** (unchanged) | 0 | 2 new deferrals (TD-22.1, TD-22.2) balance 2 reclassifications |
| Non-`TEST_` payloads | 0 | 0 | 0 | Guardrail active |
| `EMAIL_SAFETY_MODE=strict` in preview | ✅ | ✅ | — | — |
| SDK monkey patch in `server.py` | ✅ | ✅ | — | — |

**Zero runtime behavior change.** Every delta is documentation or a test.
