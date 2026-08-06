# WP-18DB Observability and Alerting Report

## Verified observability surfaces

- Admin runtime health route
- Recovery snapshot route
- Backup trust score route
- Production certification route
- Supervisor backend logs
- Production public health/version routes

## WP-18DB evidence highlights

- Runtime health currently reports liveness and readiness as healthy.
- Recovery snapshot reflects the latest complete archive and latest successful restore drill.
- Backup trust score explains amber posture truthfully:
  - `hourly_disabled`
  - `failures_7d`
- Complete archive logs preserved inline-asset warning evidence without mislabeling the archive as failed.

## Alerting observations

- Health monitor emitted backup-related warnings during stale or amber windows.
- After the fresh archive and fresh restore drill, recovery truth advanced from the earlier stale/red posture to an amber posture with explicit reasons.

## Operator truth standard

- The platform now presents the current recovery point, restore-drill timestamp, and trust penalties through governed runtime surfaces.
- WP-18DB evidence relies on these runtime surfaces rather than config-only assumptions.

## Conclusion

Observability is sufficient to identify current backup posture, restore recency, runtime readiness, and public production reachability without destructive production actions.