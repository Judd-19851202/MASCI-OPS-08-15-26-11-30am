# WP18CY.2 Production Access and Truth Report

Date: 2026-08-04

## Production access obtained
- Production URL: `https://mascidocs.com`
- Authentication path used successfully: `POST /api/auth/multi-login`
- Production admin/runtime reads succeeded when both headers were sent:
  - `X-Admin-Token = portal_tokens.admin`
  - `X-Directory-Token = session_token`

## Direct production truth captured
- Environment: `production`
- Database: `masci_safety`
- Atlas host fingerprint: `masci-prod.1nduwmg.mongodb.net`
- Release commit: `bd9bdd2012c4f2e31b57d7390218b20c361c6dcc`
- Release source hash: `665ea6071d75dd046905a35dfe8dcea4`
- Runtime identity fingerprint: `d6fbef41695c`
- Environment fingerprint: `5f193979cbd0`
- Scheduler authority: `enabled`
- Domain host context: `https://mascidocs.com`

## Live production runtime posture
- `/api/platform/data-truth` → production identity verified
- `/api/admin/runtime-reliability` → backend healthy, Mongo latency ~`28–32 ms`, scheduler tasks running
- `/api/admin/production-certification` → release band `review`
- `/api/admin/backups-complete-r2-state` → hourly complete-r2 cadence active, latest valid recoverable artifact freshness ~`29.46 min`

## Exact access still missing
1. **Production deployment authority** to move the workspace Daily Report repair into the live production release. Current production is still on release hash `665ea6071d75dd046905a35dfe8dcea4`, while the workspace contains later unreleased repairs.
2. **Direct Atlas Query Insights / profiler / Performance Advisor access** for the exact production ~`6200:1` targeting offender.
3. **Direct recipient inbox/provider-dashboard delivery proof** for full production email-family closeout.

## Smallest action necessary to clear missing access
- Deploy the current backend repair set to production through the authorized production release path.
- Grant read access to production Atlas Query Insights / profiler for the affected time window.
- Provide provider-delivery visibility (or recipient-confirmed delivery proof) for the controlled certification sends.
