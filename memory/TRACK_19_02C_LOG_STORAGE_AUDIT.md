# Track 19.02C · Log Storage Audit

## Logs on /app filesystem

None. The application does not write any log file to `/app/**`.
The only log-shaped files inside /app are inside `.git/` (git's own
operation log, platform-managed) and `node_modules/` (dependency
build logs, not application logs).

**Conclusion: /app filesystem disk pressure is NOT caused by logs.**

## Logs on the rootfs (informational only — NOT on /app)

`/var/log` totals 192 MB on the overlay rootfs (33% utilization,
70 GB free). No action needed but documented for completeness.

| File | Size | State | Action |
| --- | ---: | --- | --- |
| `/var/log/mongodb.out.log.2` | 51 M | rotated, stale | rotated by mongod; left alone |
| `/var/log/mongodb.out.log.1` | 51 M | rotated, stale | rotated by mongod; left alone |
| `/var/log/supervisor/` (dir) | 37 M | active supervisor logs | supervisor handles rotation |
| `/var/log/mongodb.out.log` | 23 M | active | mongod-managed |
| `/var/log/e1_agent.log.2` | 11 M | rotated | agent-managed |
| `/var/log/e1_agent.log.1` | 11 M | rotated | agent-managed |
| `/var/log/e1_agent.log` | 6.4 M | active | agent-managed |
| `/var/log/monitor.log` | 5.2 M | active | monitor-managed |

## Retention recommendation (for future hygiene)

* `mongod` rotation is currently retaining `.1` and `.2` — fine.
* `e1_agent` rotation retains `.1` and `.2` — fine.
* `supervisor` has no automatic rotation; if `/var/log` grows past
  60% rootfs utilization, consider adding `logrotate` config (out of
  scope for Track 19.02C since it's not on /app).

## Logs deleted by this track

**None.** No log file was deleted. Log retention is unchanged.
