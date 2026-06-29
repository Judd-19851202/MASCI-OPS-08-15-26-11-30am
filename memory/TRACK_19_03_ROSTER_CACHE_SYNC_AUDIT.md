# Track 19.03 · Roster Cache & Sync Audit

## Verdict — **NO CACHE**

The canonical employee roster endpoints `/api/employees` and
`/api/hr/employee-roster` perform a **live read** of `db.employees`
on every request. There is no in-process TTL cache, no Redis cache,
no materialized projection.

## Why this is safe

* `db.employees` reaches at most ~5,000 rows in realistic MASCI scale.
* Indexed `name` sort + indexed soft-delete + small projection means
  the query completes in <100 ms server-side.
* MongoDB's own buffer pool is the only caching layer — and it is
  invalidated automatically by HR's write through the same connection
  pool.

## Why caching was considered and rejected

| Optimisation | Why we did NOT add it |
| --- | --- |
| In-process TTL cache (e.g. `lru_cache` with timer) | Would re-introduce the very drift Track 19.03 fixes. |
| Redis cached projection | Adds invalidation surface; HR Save would have to publish an invalidation event. Overhead far exceeds the cost of a 100 ms Mongo read. |
| Materialized view in Mongo | Same complexity as Redis with weaker guarantees. |
| `change_streams` / pub-sub | Useful for future at-scale projection, but unnecessary today. Documented in `/app/memory/TRACK_19_03_FORM_PICKER_AUDIT.md` as a Track 19.04 candidate. |

## HR Save → picker visibility timeline

```
T+0   ms   HR clicks Save in HR portal
T+~50 ms   /api/hr/employees PATCH/POST completes (Mongo write acked)
T+~50 ms   any subsequent GET /api/employees / /api/hr/employee-roster
           on the same Mongo session sees the new state
```

The user requirement "From an operational user's perspective: HR adds
employee → HR clicks Save → Superintendent opens a Daily Report →
Employee is already selectable" is met because the live read returns
the freshly-committed document on the next picker query.

## Test coverage

`test_track_19_03_hr_roster_source_of_truth.py::test_hr_save_active_employee_visible_immediately`
inserts a new HR row directly into Mongo and immediately fetches the
roster. The new row appears without restart, sync job, or wait.

`test_hr_save_terminated_employee_hidden_immediately` flips
`lifecycle_status` to Terminated and asserts the next read hides them.

`test_rehire_visible_immediately` re-activates them and asserts the
next read shows them again.

## Future evolution (Track 19.04 candidate, OUT OF SCOPE today)

If MASCI ever crosses ~50,000 active employees, a thin Redis or
Mongo `change_streams`-driven projection could be added — but only
with:
* explicit invalidation on every HR write path
* `cache_hit / cache_miss` metrics
* automatic fallback to live read if the cache is unhealthy
* version bump on the roster contract

For the current MASCI scale and operational tempo, live reads are
correct, fast enough, and architecturally simpler.
