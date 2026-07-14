# Draft, Autosave, and Restore Architecture Lock

Date: 2026-07-14
Track: DR-02

## Canonical lock

### Canonical draft identity
- base key: one shared Daily Report key family
- scope: `project_number + report_date`
- owner: actor-scoped persistence via `draftStore.savedByActor`

### Why not `report_number`
- `report_number` is generated after initial form work begins and therefore is not a stable work-context anchor.

Evidence:
- `frontend/src/lib/resiliency/dailyReportScope.js:10-18`
- `frontend/src/pages/NewDailyReport.jsx:742-747`

## Canonical autosave triggers
- debounced field changes
- lifecycle visibility/pagehide/beforeunload best-effort flush
- explicit submit success commit
- queued-submit commit on confirmed delivery

Evidence:
- `useFormDraft.js:174-276`
- `NewDailyReport.jsx:1170-1197`
- `NewDailyReportV3.jsx:586-590`

## Canonical restore order
1. pending same-report draft
2. archived same-report draft
3. local setup memory
4. server recent-context Smart Prefill

## Conflict behavior
- no silent overwrite of a new blank session
- operator must explicitly restore
- shell changes must never create a hidden alternate draft slot

## Cross-device behavior
- Repository proves local device storage only for drafts and crewMemory.
- Cross-device draft sync is **NOT IMPLEMENTED** in repo.
- Canonical decision: do not imply cross-device continuity; keep behavior honest.

## Recovery behaviors that must be supported
- browser close and reopen on same device
- page refresh
- offline queued submission with later reconnect
- draft recovery after queue exhaustion

## UNKNOWNs
- recovery after full device reboot depends on browser IndexedDB persistence behavior in production device/browser matrix; implementation should certify it but repo alone cannot prove it.
