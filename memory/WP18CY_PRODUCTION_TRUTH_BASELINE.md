# WP18CY Production Truth Baseline

Date: 2026-08-04

## Truth Classes
| Class | Meaning | Used In This Work |
|---|---|---|
| SOURCE | Code-path evidence only | Root-cause tracing, index callsites, email-family inventory |
| PREVIEW_RUNTIME | Live preview API/browser execution | Daily Report submit + capture verification |
| PREVIEW_DB | Direct preview Mongo reads | capture rows, backup rows, drill runs, explain plans |
| PRODUCTION_DIRECT | Direct live production runtime evidence | **Unavailable** |
| UNAVAILABLE | Not safely reachable in this run | production email provider behavior, production Atlas metrics, production scheduler state |

## Immutable Before-State Captured
### Daily Report communication
- SOURCE: `routes/daily_reports.py` persisted the report, emitted an OPPC event, then marked `email_dispatch_suppressed=True` when OPPC communications existed.
- SOURCE: `services/operations_control/control_plane.py` email transport rendered a generic operational communication body.
- PREVIEW_DB (before repair pattern): communication message/title referenced `OPPC proof chain`, `registered control-plane policy`, and `Operations Control Plane`; attachment count was `0`.

### Backup
- PREVIEW_DB: latest `backup_health` row at capture time was `2026-08-04T02:04:07.837337+00:00`, mode `lite`, age `~797.7 min`, target `<=60 min`.
- PREVIEW_DB: latest successful `complete-r2` backup row was `2026-07-31T03:12:41.305671+00:00`.
- PREVIEW_DB: scheduled `complete-r2` jobs for `2026-08-01`, `2026-08-02`, `2026-08-03` ended `state=stale` at `stage=archive_construction` after heartbeat activity.

### MongoDB
- PREVIEW_DB bounded explain before repair:
  - `backup_health.find({ok:true}).sort(ts desc).limit(5)` → `docsExamined=200`, `nReturned=5`, `COLLSCAN+SORT`.
  - `drill_runs.find({state:"done"}).sort(started_at desc).limit(5)` → `docsExamined=99`, `nReturned=5`, `COLLSCAN+SORT`.

## Direct Production Proof
- Not available in this workspace.
- Therefore all production claims remain blocked.
