# TRACK 20.3 · Universal Thread Fit Matrix

Mapping every Universal Thread section to an already-existing incident source.

| # | Universal Thread section    | Already exists? | Route / endpoint                                                        | Component today                   | Reusable unchanged? | Adapter needed?      | Extension needed? | Build needed? |
|---|-----------------------------|:---------------:|-------------------------------------------------------------------------|-----------------------------------|:-------------------:|:--------------------:|:----------------:|:-------------:|
| 1 | Mission Overview            | ✅ YES          | `GET /incident-cases/{id}` + `GET /incident-cases/{id}/executive-snapshot` | SafetyCaseWorkspace header + snapshot | Almost              | ✅ `missionAdapter`   | ❌                | ❌            |
| 2 | Attention                   | ✅ YES          | `GET /incident-cases/{id}/health` (blockers) + `/incident-intelligence/portfolio-attention` (severity/urgency) | `CaseHealth` component            | No                  | ✅ `attentionAdapter` | ❌                | ❌            |
| 3 | Operational Guidance        | ✅ YES          | `GET /incident-intelligence/brief` + `safety_morning_digest` product     | Guidance is text-only today       | No                  | ✅ `GuidanceCard` wrap| ❌                | ❌            |
| 4 | Timeline                    | ✅ YES          | `GET /incident-cases/{id}/timeline`                                     | `TimelinePanel`                   | Almost              | ✅ `timelineAdapter`  | ❌                | ❌            |
| 5 | Relationships               | ✅ YES          | `GET /incident-cases/{id}` cross-links · involved_employees · equipment_units | Rendered as list today            | No                  | ✅ `relationshipAdapter` → RelationshipGraph | ❌ | ❌            |
| 6 | Documents                   | ✅ YES          | `GET /incident-cases/{id}/evidence` + report package endpoints           | `EvidencePanel` + Executive PDF link | Almost           | ✅ `documentsAdapter` | ❌                | ❌            |
| 7 | Photos                      | ✅ YES          | `GET /incident-cases/{id}/evidence` filtered by `kind=image`             | `EvidencePanel` (mixed today)     | Almost              | ✅ `photosAdapter`    | ❌                | ❌            |
| 8 | Operational Intelligence    | ✅ YES          | `safety_morning_digest` OI product from `/operational-intelligence/summary` | Cockpit product row               | ✅ Yes              | ❌ (consumed via `guidanceProduct`) | ❌ | ❌            |
| 9 | History                     | ✅ YES          | `GET /operational-intelligence/history/safety_morning_digest` + case audit | OI history page                   | ✅ Yes              | ❌                    | ❌                | ❌            |
|10 | Audit                       | ✅ YES          | `GET /incident-cases/{id}/audit`                                        | Not surfaced in workspace today   | Almost              | ✅ `auditAdapter`     | ❌                | ❌            |

## Missing sections
**None.** Every Universal Thread section maps to a certified endpoint that already ships and is already permissioned. The promotion track is a pure adapter exercise.

## Universal Action Queue (max 5)
Composable from:
- `health.blockers[]` (field_block, safety_block, missing evidence, missing witness statement, missing medical, missing agency contact, missing CAPA)
- `tasks[]` open items (assigned, due)
- OI top attention label from `safety_morning_digest` product

The `OperationalThreadPage` shell auto-caps the queue at 5.

## Attention Chip / Trend Chip
- **Attention level** derives from `incident_cases.severity` combined with `health.readiness_level` (Track 19.15+ presence + block state).
- **Trend** derives from OI `safety_morning_digest.trend_direction` + `trend_percent`. No new score model.

## Guidance Card
- Guidance text comes from `/incident-intelligence/brief` (per-case) + `/safety_morning_digest.recommendations[]` (portfolio).
- No new recommendation engine.
