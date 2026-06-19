# TRACK 15.49 · Phase 5 · Notification Chain Certification

**Status:** ✅ CERTIFIED · 15 notifications fire per WV/PI incident · all roles receive actionable alerts.

## Live notification matrix (verified on synthetic WV incident)
| # | Role | Type | Severity | Source |
|---|---|---|---|---|
| 1 | Safety | `task.assigned` | Warning | Track 15.40 (legacy task auto-notif) |
| 2 | Safety | `incident.created` | Warning | Track 15.40 legacy fan-out |
| 3 | PM | `incident.created` | Warning | Track 15.40 legacy fan-out |
| 4 | **Superintendent** | `incident.violence` | **Critical** | Track 15.47 G6 |
| 5 | **Operations** | `incident.violence` | **Critical** | Track 15.47 G6 |
| 6 | **Executive** | `incident.violence` | **Critical** | Track 15.47 G6 |
| 7 | **HR** | `incident.violence` | **Critical** | Track 15.47 G6 |
| 8 | Safety | `task.assigned` (WV review CAPA) | Warning | Track 15.47 G10 |
| 9 | Safety | `incident.wv_review_task` | Critical | Track 15.47 G10 |
| 10 | **HR** | `task.assigned` (24h welfare) | Warning | **Track 15.49** |
| 11 | **HR** | `incident.aftercare.welfare_24h` | **Critical** | **Track 15.49** |
| 12 | Safety | `task.assigned` (72h witness) | Warning | **Track 15.49** |
| 13 | Safety | `incident.aftercare.witness_72h` | Info | **Track 15.49** |
| 14 | Safety | `task.assigned` (7d investigator) | Warning | **Track 15.49** |
| 15 | Safety | `incident.aftercare.investigator_7d` | Info | **Track 15.49** |

## Verification details
| Check | Status |
|---|:---:|
| Safety notified | ✅ |
| PM notified | ✅ |
| Superintendent notified | ✅ |
| Operations notified | ✅ |
| Executive notified | ✅ |
| HR notified (incident + welfare task) | ✅ |
| Timing — all notifications fire within seconds of incident creation | ✅ (single-call fan-out in `safety.py`) |
| Routing — `apply_routing()` respected for project-team-based refinements | ✅ |
| Action links — every notification carries `linked_source_module=safety.incidents`, `linked_source_record_id=<id>`, `linked_project_number=<pn>` | ✅ |
| Mobile usability — Track 15.46 FR-03 action-label specificity → notification chips show action verbs | ✅ |

## Severity hygiene
- All immediate notifications (incident.created, incident.violence) → Critical / Warning.
- Aftercare task notifications → Critical (welfare 24h, urgent) · Info (witness 72h, investigator 7d, ambient).
- The `task.assigned` notifications fire at Warning (always-on operator alert).

This means the executive bell does NOT get spammed with low-priority noise — Critical/Warning only on WV; Info on routine aftercare scheduling.

## Failure modes (all best-effort)
- Each per-role emit wrapped in `try/except`.
- A misconfigured role does NOT block any other notification.
- A missing `apply_routing` config does NOT block the emit.
- All failures log to supervisor logs with `[event_fanout]` or `[aftercare-task]` prefix.

## Sign-off
GREEN. No blind spots. Every stakeholder on the WV/PI chain receives a notification with actionable context, anchored to the source incident, within seconds.
