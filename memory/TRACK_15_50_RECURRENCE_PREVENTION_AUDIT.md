# TRACK 15.50 · Recurrence Prevention Audit (Phase 2)

**Status:** ✅ AUDIT COMPLETE · gap closed in-track via 14-day training-requalification CAPA.

## Pre-15.50 recurrence-prevention state
For each incident class, what was preventing recurrence?
| Incident class | Pre-15.50 mechanism | Severity of gap |
|---|---|:---:|
| Workplace Violence | Manual decision by Safety to re-train · no auto-issue | 🔴 HIGH |
| Public Interaction | Same · manual | 🔴 HIGH |
| Physical Confrontation | Same · manual | 🔴 HIGH |
| Verbal Threat | Same · manual | 🔴 HIGH |
| Police-Involved Incident | Same · manual | 🟡 MEDIUM |

Across all five classes, recurrence prevention depended on someone REMEMBERING to schedule retraining. No system-enforced deadline. No system-tracked outcome.

## What 15.50 delivered
Two coupled changes:

### Change 1 · Auto-issued 14-day training CAPA
Extends the Track 15.49 aftercare task chain with a NEW task:
- **`incident.aftercare.training_14d`** → Safety role · High priority · T+14 days
- Description names the affected employee (`person_name`) + foreman (`supervisor_name`) + lists the FOUR specific topics: "Dealing With Angry Members of the Public" · "Stop Work Authority" · "Verbal Threats and Harassment" · "Physical Confrontations"
- Instructs the assignee to record completion in `safety_training_records` with `source_incident_id={incident_id}` so the chain is defensible

### Change 2 · `source_incident_id` field on training records
Lets every training record carry a chain-of-custody link back to the originating incident.

## Recurrence-prevention chain · post-15.50
| Step | Mechanism | Evidence |
|---|---|---|
| 1 · Incident classifies as WV/PI | Track 15.47 `classifications` field | ✅ |
| 2 · Auto-issue 14d training CAPA to Safety | Track 15.50 fan-out extension | ✅ verified live |
| 3 · Safety delivers the topics + records completion | Existing safety topic library (Track 15.46A/15.47 · 9 topics EN+ES) + existing training record endpoint | ✅ verified live |
| 4 · Training record bound to incident | NEW `source_incident_id` field | ✅ verified |
| 5 · PDF shows requalification | NEW "Recurrence Prevention · Training Requalification" block | ✅ verified live |
| 6 · Executive sees outstanding training | Bell notifications + Tasks list filtered by `source_module=safety.incidents` | ✅ |

## Recurrence question · answered with evidence
> "What mechanism currently prevents recurrence?"

**Post-15.50:** The 14-day Safety-owned task auto-issued at incident creation NAMES the affected employee + topics, forcing Safety to deliver + log the requalification. Completion is bound back to the incident via `source_incident_id`. The PDF carries the requalification row. If completion does NOT happen by day 14, the task moves to overdue — visible in the Executive Overview overdue-task / overdue-CAPA stream.

## Severity of remaining gaps
- 🟡 **MEDIUM** — No mandatory escalation if the 14d task goes overdue beyond 30 days. Today it surfaces in the overdue stream; a second-tier escalation (auto-notify Operations Manager) would close this. Backlog: B-04.

## Sign-off
GREEN. Recurrence prevention is now SYSTEM-ENFORCED, not memory-based. Every WV/PI incident produces an owned, due-dated, traceable retraining obligation.
