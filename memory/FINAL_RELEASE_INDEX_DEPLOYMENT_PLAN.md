# Final Release Index Deployment Plan

## New / changed index risk surfaces in workspace
- `backup_health_ok_ts_desc`
- `backup_health_mode_ts_desc`
- `drill_runs_state_started_desc`
- additional startup ensure-index activity already present in `server.py` and related authority services

## Proven behavior
- In preview, bounded explains improved:
  - `backup_health {ok:true}.sort(ts desc)` from `40.0:1` to `1.0:1`
  - `drill_runs {state:'done'}.sort(started_at desc)` from `19.8:1` to `1.0:1`

## Production audit conclusion
- Production app routes did **not** expose a full authoritative index inventory for all affected collections.
- Therefore full production index parity is not proven.

## Build / runtime impact assessment
- Recovery indexes appear additive and low-risk on append-heavy collections.
- Main unknown is total production collection size and exact build time at deploy.
- Startup-driven index creation means build impact would be discovered during live startup unless pre-created.

## Safe deployment recommendation
1. Pre-create any proven new indexes during a controlled maintenance window **before** app release when possible.
2. Record collection counts and index build completion times.
3. Do not rely on startup auto-ensure alone for first live creation on large collections.

## Current gate effect
- **Index plan alone does not block Save.**
- **Index parity uncertainty contributes to Deploy = NOT SAFE yet.**
