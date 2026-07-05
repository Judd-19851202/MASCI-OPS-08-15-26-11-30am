# ODS-001 · Operational Timeline Foundation

Every operational fact is naturally a timeline event. This document scopes the timeline **schema** so a future timeline UI can be built without any spine change.

## Event derivation (no new collection required)

Timeline events are **projections** of `operational_facts` filtered `is_current=true`. A timeline event is:

```
{ ts,               # coerced from date or created_at
  project_id,
  event_type,       # crew_started | activity_recorded | material_delivered
                    # delay_started | delay_ended | equipment_breakdown
                    # safety_event | quality_event | photo_uploaded
                    # report_submitted | intelligence_approved
                    # readiness_blocker_created
  fact_id,          # backing fact
  actor,            # submitted_by
  summary,          # 1-line UI label built from payload
  severity? }
```

## Mapping

| Fact type | event_type | severity source |
| --- | --- | --- |
| labor_fact | crew_started | — |
| production_fact | activity_recorded | — |
| material_fact | material_delivered | — |
| delay_fact | delay_started | payload.impact |
| equipment_fact where breakdown=true | equipment_breakdown | high |
| safety_fact | safety_event | payload.severity |
| quality_fact | quality_event | payload.status |
| photo_evidence_fact | photo_uploaded | — |
| readiness_fact where status!=ready | readiness_blocker_created | at_risk/blocker |
| intelligence_fact | intelligence_approved | — |

## Read (deferred)

`GET /api/ods/timeline/{project_id}?date_from=&date_to=&event_type=` will be built in the next track. Everything it needs is already indexed in `operational_facts`.
