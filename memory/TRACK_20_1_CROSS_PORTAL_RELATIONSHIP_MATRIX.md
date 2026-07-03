# TRACK 20.1 · Cross-Portal Relationship Matrix

Every relationship an employee has, mapped to its owner and current
storage location.

| Relationship             | Owner portal   | Storage / endpoint (existing)                                 | Inferred vs stored | Recommendation                        |
|--------------------------|----------------|---------------------------------------------------------------|:------------------:|---------------------------------------|
| Supervisor               | HR             | Employee record `supervisor_id`                                | Stored             | KEEP — surface as graph node          |
| Projects (active)        | PM             | `daily_reports` / project assignments                          | Stored             | KEEP — surface as graph node          |
| Equipment / Vehicles     | Fleet / Shop   | Assignment / accountability endpoints                          | Stored             | KEEP                                  |
| Training                 | HR             | `/api/training/videos` + acknowledgements                      | Stored             | KEEP — visible in Timeline category   |
| Incidents                | Safety         | Incident engine (Track 12.x)                                   | Stored             | KEEP — visible in Timeline category   |
| Recognitions             | HR             | Timeline event (`category=Field Leadership` when applicable)   | Stored             | KEEP                                  |
| Corrective Actions       | Safety         | CAPA queue on Safety Hub                                       | Stored             | KEEP — reachable via deep-link        |
| Crews                    | Ops            | Ops crew assignment                                            | Stored             | KEEP                                  |
| Departments              | HR             | Employee record `department`                                   | Stored             | KEEP                                  |
| Shops                    | Shop           | Shop assignment record                                         | Stored             | KEEP                                  |
| Offices                  | HR             | Employee record `office`                                       | Stored             | KEEP                                  |
| Assignments (today)      | Dispatch / Ops | Dispatch assignment log                                        | Stored             | KEEP                                  |
| Driver-qualification     | Transportation | Timeline category `Driver Qualification`                        | Stored             | KEEP                                  |

## Duplication scan
- No relationship is stored twice.
- No portal maintains a parallel employee-relationship database.
- The Accountability endpoint's `events[]` acts as the union view; individual owner-portals stay authoritative for their own records.

## Universal Relationship Graph (Track 19.55) adoption
When the Employee Thread promotion happens (Track 19.56 scope), the
`RelationshipGraph` node visual should render:
- **subject** — the employee (kind: `operator` — Track 19.55 tone map).
- **supervisor** — kind: `foreman` or new `supervisor` (reuse existing tone).
- **current project** — kind: `project` · deep-link `/pm/command-center`.
- **crew** — kind: `other` · sublabel-only.
- **current unit** (if assigned) — kind: `unit` · deep-link `/fleet/unit/:unit_number` (Track 19.55 route).
- **shop** — kind: `shop`.

Every node deep-links to an existing route. Zero new routes required.

## Verdict
🟢 **No duplicate relationship storage exists.** Adoption of the
universal RelationshipGraph is a pure visual promotion.
