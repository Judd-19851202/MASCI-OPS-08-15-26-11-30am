# TRACK 19.43 · Fleet Intelligence Score Model

Uses `operational_intelligence.score_model.score_from_contributors(...)`.

## Positive contributors

| Key | Trigger | Impact | Rationale |
|---|---|---|---|
| `full_availability` | Total units > 0 · OOS = 0 | +12 | Fleet fully available |
| `clean_inspections` | Inspections 7d > 0 · open defects = 0 | +8 | Clean inspection pass |
| `no_holds` | Zero safety + zero maint/repair holds · total > 0 | +6 | No holds on any unit |
| `no_equip_incidents` | Zero equipment-damage incidents in period | +8 | Clean equipment-safety period |

## Negative contributors

| Key | Trigger | Impact | Rationale |
|---|---|---|---|
| `critical_defects` | CRITICAL defect count > 0 | `-min(35, count*12)` | Highest severity |
| `defect_backlog` | Open defects > 5 (when no critical) | `-min(20, count/2)` | Non-critical backlog |
| `oos_units` | OOS count > 0 | `-min(25, count*3)` | Availability drag |
| `safety_holds` | Safety hold count > 0 | `-min(25, count*6)` | Investigate immediately |
| `maint_holds` | Maint/repair hold count > 0 | `-min(15, count*2)` | Availability drag |
| `overdue_inspections` | Overdue count > 0 | `-min(15, count*3)` | Compliance + utilisation exposure |
| `equipment_incidents` | Equipment-damage incidents in period > 0 | `-min(25, count*10)` | Safety exposure |

## Confidence

- `insufficient_data` when no signals populated.
- `medium` when signals present but fleet total < 10.
- `high` when fleet total ≥ 10.

## Attention level

Derived from score (LOW ≥85 · MEDIUM ≥65 · HIGH ≥40 · CRITICAL <40).

## No-auto-decision

Fleet · Shop · Safety own investigation. Platform does NOT decide fault, root cause, mechanic responsibility, insurance liability, or return-to-service authorisation.
