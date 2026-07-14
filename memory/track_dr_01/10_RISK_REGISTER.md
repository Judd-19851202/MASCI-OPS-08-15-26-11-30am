# Risk Register

Date: 2026-07-14
Track: DR-01

| ID | Risk | Evidence | Impact | Likelihood | Mitigation direction |
|---|---|---|---|---|---|
| R1 | Routed shell mismatch causes different continuity behavior for the same URL | `DailyReportRouter.jsx:14-29` | P0 trust loss | High | choose one field contract before repair |
| R2 | Draft key changes mid-session because scope includes `report_number` | `dailyReportScope.js:10-18`; `NewDailyReport.jsx:742-747` | P0 autosave loss | High | stabilize scope contract |
| R3 | V1 drafts are invisible to V3 and vice versa | `dailyReportScope.js:3`; `NewDailyReportV3.jsx:59-63` | P0 recovery failure | High | unify base key |
| R4 | V3 queued Daily Reports bypass canonical repair branch | `resiliencyQueue.js:152-167`; `NewDailyReportV3.jsx:579-585` | P0 offline trust loss | Medium-High | align queue form key |
| R5 | Smart Prefill absent in V3 | absence in `NewDailyReportV3.jsx`; present in V1 | P0 productivity regression | High | port or suppress shell until parity |
| R6 | Two Smart Prefill apply paths inside V1 create inconsistent operator outcomes | `NewDailyReport.jsx:1403-1429`, `1451-1491`, `680-729` | P1 confusion / hidden bugs | High | collapse to one apply path |
| R7 | Local setup memory and server Smart Prefill are conflated in UI | `CrewSetupRestorePrompt.jsx`; V1 server-offer reuse | P1 trust / UX confusion | Medium | separate semantics |
| R8 | V2 backend subsystem continues to shape architecture decisions invisibly | `dr_v2.py`, `daily_report_collections.py` | P1 permanent drift | Medium | explicitly isolate legacy boundary |
| R9 | Lifecycle flush may not complete during page teardown on mobile browsers | `useFormDraft.js` async flush vs synchronous comment | P1 mobile loss | Medium | runtime verification + repair |
| R10 | Production flag state and affected shell distribution are unknown | not derivable from repo | P0 certification blocker | Unknown | gather runtime evidence |

## Highest-risk cluster

The highest-risk cluster is **identity drift across routed shells**. That cluster affects autosave, restore, queue retry, and Smart Prefill at the same time.
