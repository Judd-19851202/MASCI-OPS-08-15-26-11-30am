# Final Release Worker / Scheduler Plan

## Production runtime observed
- Multiple background tasks and schedulers are live.
- Examples observed in production runtime reliability:
  - backup-verification-singleton
  - operator-digest-singleton
  - po-digest-singleton
  - runtime-reliability-monitor
  - job-photos-indexer
  - dispatch-reminder-scheduler

## Mixed-version safety assessment
- Exact fleet-wide code-hash parity was **not** provable for every worker process.
- Because the bundle changes backend routes, services, notification logic, startup indexes, and UI together, mixed-version overlap is a real deployment risk.

## Required restart/order plan
1. Confirm fresh verified backup exists.
2. Deploy backend code first only if worker/scheduler restarts are coordinated.
3. Restart or rotate all worker/scheduler processes that consume notification, PDF, backup, and OI logic.
4. Bring frontend artifact live after backend/worker parity is confirmed.
5. Immediately verify release identity, Daily Report submit, notification truth stages, and backup health.

## Duplicate-work protections
- Production backup cadence currently shows safety-guard ownership preventing duplicate complete-r2 jobs.
- This is positive, but deployment still requires worker coordination.

## Gate effect
- Save: allowed with documentation.
- Deploy: blocked until controlled restart order is owned and executed.
