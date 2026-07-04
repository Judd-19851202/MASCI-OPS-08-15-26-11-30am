# TRACK 22.0 · Keep / Improve / Merge / Retire / Delete Matrix

**Every manifest object receives exactly one status. No UNKNOWN.**

## Consolidated matrix (top-level rollup)

| Object | Status | Owner | Target track |
|---|---|---|---|
| 6,982 tracked files | KEEP | Backend + Frontend | — |
| 1,440 runtime endpoints | KEEP | Backend | — (source split → 22.1) |
| 385 frontend routes | KEEP | Frontend | (source split → 22.2) |
| 180 lazy imports | KEEP | Frontend | — |
| 309 pages | KEEP | Frontend | — |
| 355 components | KEEP (5 pairs queued for RENAME) | Frontend | 21.y |
| 98 dialogs | KEEP | Frontend | — |
| 67 forms | KEEP | Frontend | — |
| 1,687 buttons | KEEP | Frontend | — |
| 1,198 inputs | KEEP | Frontend | — |
| 198 tables | KEEP | Frontend | — |
| 29 email dispatch sites | KEEP (guarded 3 layers) | Backend | — |
| 23 upload endpoints | KEEP | Backend | — |
| 24 PDF modules | KEEP | Backend | — |
| 31 scheduled tasks | KEEP | Backend | — |
| 170 mongo collections | KEEP + 3 candidates RETIRE_LATER | Backend | 21.2z |
| 355+ auth gates | KEEP | Backend | — |
| 7 portal tokens | KEEP | Backend | — |
| CORS config | IMPROVED (Track 21.3) | Backend | — |
| Env-var docs | IMPROVED (Track 21.3) | Backend + Ops | — |
| Payload canonicalization | IMPROVED (Track 21.2E-1) | Backend | — |
| Email SDK kill switch | KEEP | Backend | — |
| Component-collision plan (5 pairs) | DEFERRED | Frontend | 21.y |
| server.py split | DEFERRED | Backend | 22.1 |
| App.js split | DEFERRED | Frontend | 22.2 |
| Storage janitor | DEFERRED (retire-with-plan) | Ops | 21.2z |
| Sentry env-tag | DEFERRED | Ops | 21.2z |
| Iter### tests (284 files) | KEEP (per-file evaluation P3) | Backend / Test | 21.2z |
| Tech-debt markers (33) | KEEP (documented intent) | Various | — |

**Zero items with status UNKNOWN. Zero items DELETED (Zero-Drift).**
