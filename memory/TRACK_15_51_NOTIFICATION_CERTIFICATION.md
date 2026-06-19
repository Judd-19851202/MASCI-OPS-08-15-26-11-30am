# TRACK 15.51 · Notification Certification (Phase 7)

**Status:** ✅ CERTIFIED · all notification paths exercised against synthetic incident.

## Verified notification types (live · MongoDB recorded)
| Event class | Recipient roles | Type | Severity |
|---|---|---|---|
| Team assignment | Affected member | `project_team_assignment` | Warning |
| Incident · created | Safety + PM | `incident.created` | Warning |
| Incident · WV / Public-Interaction | Superintendent + Operations + Executive + HR | `incident.violence` / `incident.public_interaction` | Critical / Warning |
| WV review CAPA | Safety | `incident.wv_review_task` | Critical |
| Aftercare 24h welfare | HR | `incident.aftercare.welfare_24h` | Critical |
| Aftercare 72h witness | Safety | `incident.aftercare.witness_72h` | Info |
| Aftercare 7d investigator | Safety | `incident.aftercare.investigator_7d` | Info |
| Aftercare 14d training | Safety | `incident.aftercare.training_14d` | Info |
| Task · assigned (each aftercare task) | Per assignee | `task.assigned` | Warning |
| Daily Report pending | PM | `daily_report.pending_review` | Warning |
| CAPA · assigned | Owner | `task.assigned` | Warning |
| Trench safety hold / cert / damage | Safety + PM | various `trench_safety.*` | varies |
| Asset transfer flow | Dispatch + Shop + PM | `asset_transfer.*` | varies |
| Fleet defect OOS | Shop + Safety | `dvir.defect.oos` | Warning |

## Bell chip quality (Track 15.46 FR-03)
Every notification chip in `NotificationBell.jsx` shows an action verb (Review / Action / Acknowledge / Open / Submit / Verify / Renew / Schedule) instead of raw event type. Raw type preserved as hover-title.

## Routing
- `apply_routing(db, notif, project_number, event_key)` consulted on every emit.
- Project-team-based routing (Track 15.39A) refines per-project recipient lists.
- Default fan-out works when no routing config exists.

## Links
- Every notification carries `linked_source_module` + `linked_source_record_id` + `linked_project_number`.
- Frontend NotificationBell uses these to route the user into the correct portal (safety / pm / shop / dispatch / hr / fl).

## Failure modes
- Per-recipient emit wrapped in try/except (`backend/routes/safety.py:910-1015` for incident fan-out).
- Single role failure does NOT block the rest of the fan-out.
- Logs to supervisor with `[event_fanout]` / `[aftercare-task]` / `[incident-defense-fanout]` prefixes.

## Sign-off
GREEN. Notification chain proven live on synthetic incident (15 notifications · all expected roles · all action-labels rendering correctly).
