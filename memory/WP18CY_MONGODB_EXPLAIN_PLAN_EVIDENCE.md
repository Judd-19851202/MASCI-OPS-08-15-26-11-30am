# WP18CY MongoDB Explain Plan Evidence

## Bounded Explain Policy
- Only narrow read-only explains were executed against preview data.
- No uncontrolled wide production profiler or unbounded production explain was executed.

## Before Repair
### backup_health latest success
- Query: `find({ok:true}).sort(ts desc).limit(5)`
- `docsExamined=200`, `keysExamined=0`, `nReturned=5`
- Winning plan: `SORT -> COLLSCAN`

### drill_runs latest done
- Query: `find({state:'done'}).sort(started_at desc).limit(5)`
- `docsExamined=99`, `keysExamined=0`, `nReturned=5`
- Winning plan: `SORT -> COLLSCAN`

## After Repair
### backup_health latest success
- `docsExamined=5`, `keysExamined=5`, `nReturned=5`
- Winning plan: `IXSCAN backup_health_ok_ts_desc`

### backup_health latest complete-r2 by mode
- `docsExamined=5`, `keysExamined=5`, `nReturned=5`
- Winning plan: `IXSCAN backup_health_mode_ts_desc`

### backup_health usage mode probe
- `docsExamined=5`, `keysExamined=5`, `nReturned=5`
- Winning plan: `SORT_MERGE` over `backup_health_mode_ts_desc` index scans

### drill_runs latest done
- `docsExamined=5`, `keysExamined=5`, `nReturned=5`
- Winning plan: `IXSCAN drill_runs_state_started_desc`

## Interpretation
- Recovery and health certification reads are now bounded to the requested subset.
- No evidence-backed production Atlas offender at the reported ~6200:1 ratio was directly reachable in this run.
