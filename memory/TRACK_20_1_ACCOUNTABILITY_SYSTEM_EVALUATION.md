# TRACK 20.1 · Accountability System Evaluation

## What Accountability already solves
- **Single source of truth** for an employee's operational readiness across HR, Safety, Transportation, and Driver-Qualification lenses.
- **Role-aware presentation** — HR + Safety + Admin all consume ONE endpoint (`/api/hr/employees/{id}/accountability/timeline`); the endpoint filters visibility server-side.
- **PDF export** — `/api/hr/employees/{id}/accountability/brief.pdf` produces a compliance brief.
- **Category-tagged timeline** — every event carries a `category` (Training / PPE & Equipment / Incidents / Field Leadership / HR Lifecycle / Driver Qualification), enabling tab filtering without new backend joins.
- **Current-state aggregation** — the endpoint returns a `current_state` object summarising readiness, holds, and lifecycle status.

## What it already answers per persona
| Persona            | Question                                                       | Answered by Accountability today? |
|--------------------|----------------------------------------------------------------|:---------------------------------:|
| HR                 | Is this employee employment-ready?                             | ✅ (`current_state.hr_lifecycle`)  |
| Safety             | Can this employee safely perform today's work?                 | ✅ (Incidents + PPE categories)    |
| Transportation     | Can this employee legally drive today?                         | ✅ (Driver-Qualification category) |
| Shop               | Can this employee operate this equipment?                      | ⚠️ Partial (via PPE + Training)    |
| PM                 | Can this employee work this project?                           | ⚠️ Partial (via Field Leadership)  |
| Superintendent     | What do I need to know before assigning this person today?     | ✅ (all categories on one page)    |
| Executive          | Is this employee operationally healthy?                        | ⚠️ Needs OI attention chip / trend |

## What should remain exactly as-is
- Backend endpoint contract.
- PDF brief export.
- Six-category tag system.
- HR + Safety + Admin auth gate.
- `HrEmployeeAccountability.jsx` tile home (as launcher).

## What should move
- Nothing needs to move. All content is in the right place.

## What should simply be surfaced differently
- Wrap `HrEmployeeAccountabilityTimeline.jsx` in the Track 19.55 `OperationalThreadPage` shell so the visual matches every other Thread page platform-wide.
- Add the OI Attention Strip (Track 19.52) consuming `hr_intelligence` + `training_intelligence` at the top.
- Add a `RelationshipGraph` (Track 19.55) node visual for supervisor / crew / current project / current unit — populated from fields already present in the payload.
- Add a Section 3 Guidance Card button so any attention item opens the universal Guidance Card modal.
- Adopt the universal `AttentionChip` + `TrendChip` chips.

## What should NOT be built
- No new "Employee Thread" backend.
- No new score model.
- No new AI classification.
- No new recommendation engine.
- No parallel employee page.

## Verdict
🟢 **Accountability IS the Employee Thread foundation.**
Promote it through the Universal Thread visual language.
