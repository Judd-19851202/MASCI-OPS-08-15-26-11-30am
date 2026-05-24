# SYSTEM_CONTINUITY_MATRIX.md
**Phase 17 · iter413 · 2026-05-24**

Single-page operational truth map. Reads top-down: **source data → assignment → lifecycle → cycle → downstream awareness**.

## Source-of-truth data layer
| Collection | Owner | Phase added |
|---|---|---|
| `employees` | HR | pre-Phase-12 |
| `equipment_master` | Shop / Fleet | pre-Phase-12 |
| `daily_reports` | Field / PM | pre-Phase-12 |
| `dispatch_assignments` | Dispatch | iter392 |
| `dispatch_state_events` | DLS (append-only) | iter392 |
| `haul_cycles` | DLS (materialized) | iter392 |
| `dispatch_driver_sessions` | DLS (magic-link) | iter393 |
| `governance_findings` | Governance (computed) | iter395 |

**Zero new collections added in Phase 17.** All convergence rides on the iter392-iter410 schema.

## Assignment fields → downstream consumer map
| Field on `dispatch_assignments` | Set by | Consumed by |
|---|---|---|
| `truck_id` | Dispatch drawer / driver self-start | Board · PM tile · Shop tile · Cycle · Health summary |
| `driver_id`, `driver_name` | Dispatch drawer / self-start | Board · driver session · Cycle |
| `project_number`, `project_name` | Dispatch drawer | PM tile (project scope) · Cycle |
| `material` | Dispatch drawer | Cycle · PM `top_materials` |
| `source_location`, `destination` | Dispatch drawer | Cycle · Operational memory (recents) |
| `haul_type` (iter408) | Dispatch drawer | PM split (material/eq move) · Health summary `haul_types_today` |
| `equipment_id`, `equipment_label` (iter408) | Dispatch drawer (Equipment Move) | Cycle · Shop visibility |
| `pickup_location`, `dropoff_location` (iter408) | Dispatch drawer (Equipment Move) | Cycle · Operational memory |
| `trailer_id`, `trailer_label`, `carrier` (iter408) | Dispatch drawer | Cycle · Operational memory |
| `liquid_product` (iter410) | Dispatch drawer (Tanker) | Cycle · Tanker continuity · Future plant continuity |
| `current_state`, `current_wait_reason` | Driver lifecycle taps | Board · Governance · PM waits · Shop breakdowns · Health summary |
| `state_history` (append-only) | DLS state machine | Audit trail · Governance · CSV exports |

## State transitions → downstream signals
| State change | Triggers |
|---|---|
| ASSIGNED → ENROUTE_TO_LOAD | Driver lifecycle event · board row updates |
| AT_LOAD → WAITING (with reason) | Governance long-wait detector · PM `waiting_on_plant/dump` · Health summary `waiting_count` |
| → BREAKDOWN | Shop iter396 BREAKDOWN signal · PM `breakdown_impacts` · Health summary `breakdown_count` · Governance finding |
| → COMPLETE | `haul_cycles` doc materialized · PM `loads_completed_today` increments · Health summary `completed_cycles_today` |

## Cross-portal tile mounting matrix
| Portal | Mounted tiles | Source data |
|---|---|---|
| `/dispatch-portal` (iter411) | Operational Attention (findings) · Issue Work (drawer launcher) · Live Flow (board link) · Follow-Through (transfers/holds) · Secondary (overview/utilization/idle/integrations) | findings · existing tabs |
| `/dispatch-portal/board` | Full DLS board · assignment drawer | dispatch_assignments + state_events |
| `/pm` | iter409 PmHaulActivityTile · iter396 DispatchLifecycleTile (scope=pm) | dispatch_assignments + haul_cycles (project-scoped) |
| `/shop` | iter396 DispatchLifecycleTile (scope=shop, BREAKDOWN signals) | dispatch_assignments (state=BREAKDOWN) |
| `/field-leadership` | iter319 + iter396 (scope=fl) | dispatch_assignments (read-only) |
| `/field` (public) | iter403/404 Trucking Operations lane → `/shift` link | n/a (gateway) |
| `/admin/dls/shift-qr` (iter406) | QR generator | n/a (client-side) |

## Cross-language continuity layer
- Storage key: `masci.lang` (NOT `localStorage.lang`)
- 3,526 EN→ES translation keys
- Wire fields store canonical English; UI translates display

## Operational memory feedback loop
Every assignment POST seeds future drawer dropdowns:
1. Dispatcher types `Pit 27` as a custom source
2. POST `/api/dispatch/assignments`
3. Next call to `/api/dispatch/driver/assignment-lookups` returns `Pit 27` tagged `source: "history"`
4. Future dispatchers see it in the dropdown without admin intervention

## Verdict
The platform is **one connected operational truth layer**. Every state change, every field, every tile is traceable to its source and its downstream consumer through the diagram above.
