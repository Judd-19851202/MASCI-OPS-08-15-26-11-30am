# TRACK 15.50 · Requalification Workflow (Phase 4) + Amendment Compliance

**Status:** ✅ DELIVERED · single workflow · no portal, no dashboard, no V2.

## The mandated event flow · post-15.50
```
Incident Created
  ↓
classifications field evaluated (Track 15.47 G1)
  ↓
WV/PI trigger detected → backend safety.py fan-out fires
  ↓
  • 9 Track 15.47 notifications (Safety + PM + Super + Ops + Exec + HR + WV review CAPA)
  • Track 15.49 aftercare tasks: 24h welfare · 72h witness · 7d investigator
  • Track 15.50 NEW aftercare task: 14d training requalification
  ↓
Safety delivers the named topics to affected employees
  ↓
Safety records completion via POST /api/safety/training-records with
  source_incident_id=<id> + topic_keys=[...] + status="Completed"/"Verified"
  ↓
Training record bound to incident
  ↓
PDF (single artifact) renders "Recurrence Prevention · Training Requalification" block
  ↓
Executive Overview safety tile reflects:
  training_required / training_completed / training_overdue
  ↓
Overdue retraining → forces verdict RED + adds verdict_reasons bullet
```

## Trigger criteria · mapped to the amendment
| Amendment trigger | Implemented via |
|---|---|
| Workplace Violence | `classifications` contains "Workplace Violence" |
| Public Interaction | `classifications` contains "Public Interaction" |
| Physical Confrontation | `physical_contact=true` OR `classifications` contains "Physical Contact" |
| Physical Assault | `physical_assault=true` OR `classifications` contains "Physical Assault" |
| Threat | `threat_made=true` OR `classifications` contains "Threat" |
| Harassment | `classifications` contains "Harassment" |
| Weapon Displayed | `weapon_displayed=true` |
| Weapon Used | `weapon_used=true` |
| Safety Manager manually marks retraining required | Safety can manually `POST /api/tasks` with `task_key=incident.aftercare.training_14d` |

Excluded: ankle-twist-from-truck (no WV/PI classification) → no auto-retraining. ✅ As mandated.

## Required topics by classification
| Trigger | Minimum topics |
|---|---|
| Any WV/PI | `angry_public_de_escalation` + `stop_work_authority` |
| + Verbal Threat / Harassment | `+ verbal_threats_harassment` |
| + Physical Confrontation | `+ physical_confrontations` |
| + Recording / Social Media | `+ recording_employees_social_media` |
| + Trespass | `+ trespassing_into_work_zones` |
| + Children present | `+ public_near_children` |

These are mandated in the auto-task description. The Safety assignee delivers them and records completion with the `topic_keys` array on the training record.

## Status model · per amendment
Implemented on `safety_training_records.status`:
- Required · Assigned · In Progress · Completed · Verified · Overdue · Waived

Waiver fields enforced: `waived_by` · `waived_at` · `waiver_reason` (all required if status="Waived" — operational discipline; not enforced at schema level for backward compat).

## Audit trail · per amendment
| Field | Source |
|---|---|
| created_by | `created_by` + `created_by_name` + `created_by_role` (iter353a) |
| created_at | `created_at` |
| trigger incident | `source_incident_id` + `source_incident_doc_id` (NEW 15.50) |
| trigger classification | `trigger_classification` (NEW 15.50 · array) |
| assigned employee | `employee_id` + `employee_name` |
| assigned topic | `topic_keys[]` (NEW 15.50) |
| due date | `due_date` (NEW 15.50) |
| completed_at | `completed_date` |
| verified_by / verified_at | NEW 15.50 fields |
| waiver details | NEW 15.50 fields |

## Required surfaces · all met without new portals
| Surface | How |
|---|---|
| Incident Record | PDF "Recurrence Prevention · Training Requalification" block (NEW 15.50). The training records bound by `source_incident_id` appear automatically. |
| Employee Record | HR portal already lists `safety_training_records` filtered by employee — unchanged. The `source_incident_id` field is rendered as a reference. |
| Safety View | Existing `safety_training_records` list endpoint + Tasks list filtered by `task_key=incident.aftercare.training_14d`. |
| Executive Overview | NEW counts on safety tile: training_required / training_completed / training_overdue. Foundation v15.50.1. |

## Sign-off
GREEN. The amendment's mandated architecture is in place. No V2 portal, no separate dashboard, no manual workaround. The incident is the trigger; the platform drives everything else.
