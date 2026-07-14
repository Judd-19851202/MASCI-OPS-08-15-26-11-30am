# DR-03 Draft Scope and Identity Contract

## Implemented canonical base key
- `daily-report`

## Implemented canonical scope
- `actor::project::date::instance`

## Implemented actor identity source
- `getStableActorIdentity()` for Daily Report continuity context

## Implemented scope helper
- `frontend/src/lib/resiliency/dailyReportScope.js`

## Implemented consumers
- draft restore/autosave
- idempotency load/persist
- queue formKey
- scope tests

## Notes
- `report_instance` now defaults to `primary` in `buildDailyReportDefaults()`.
- Device-local draft storage still uses the existing device-scoped store key, while the draft form key itself now carries stable actor scope.

## Remaining open item
- Full multi-instance authoring workflow is not yet exposed through the UI, although the scope helper now supports instance separation.
