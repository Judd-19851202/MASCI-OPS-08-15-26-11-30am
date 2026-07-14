# Regression Locks

Date: 2026-07-14
Track: DR-02

## P0 locks
- Daily Report routes resolve one shell contract only
- one canonical draft base key across active Daily Report surfaces
- one canonical scope formula across active Daily Report surfaces
- `report_number` change must not change draft identity
- restore prompt appears for pending same-report draft
- archived-draft recovery works when applicable
- local setup memory and Smart Prefill never share the same UX semantics
- active shell always exposes Smart Prefill when recent-context returns meaningful data
- exactly one Smart Prefill apply path exists
- offline queue uses canonical Daily Report form key and repair path
- queued submit commits draft only after confirmed delivery
- duplicate submission prevention via idempotency holds across reconnect/retry

## P1 locks
- accepted summary contract is single and canonical
- PDF reads the canonical accepted summary field family
- ODS day_summary_fact derives from the canonical accepted summary field family
- PM/executive brief surfaces read Daily Report intelligence only through ODS
- notifications fire from lifecycle stages, not shell forks
- Trust Spine expected stages for `daily-report` are emitted consistently
- global search and doc-id search resolve the same report identity
- CSV export excludes synthetic/certification rows and reads canonical source

## Required named regressions from prompt
- Autosave
- Restore draft
- Restore yesterday
- Equipment carry-forward
- Crew carry-forward
- Hours carry-forward
- AI assistance
- Submission
- Offline recovery
- Synchronization
- Duplicate submission prevention
- Search
- Executive Brief
- Scheduling signal handling
- Reconciliation integrations that are actually verified
- Notifications
- Trust Spine
- PDFs
- Exports
