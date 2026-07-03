# TRACK 19.45B · Shop Intelligence Score Model

Universal 0-100 Operational Intelligence Score (Track 19.41).
Baseline 100 · positive contributors add · negative contributors
subtract · clamped 0..100.

## Positive contributors
| Key | Trigger | Impact |
|---|---|---|
| `full_availability` | fleet_total > 0 and oos_units == 0 | +10 |
| `no_safety_holds` | safety_holds == 0 and fleet_total > 0 | +10 |
| `no_critical_defects` | critical_defects == 0 with defect activity present | +8 |
| `closing_pace` | defects_closed_7d ≥ defects_opened_7d (with closures > 0) | +8 |
| `no_equipment_incidents` | equip_incidents_7d == 0 with fleet/wo present | +8 |

## Negative contributors
| Key | Trigger | Impact |
|---|---|---|
| `safety_holds` | safety_holds > 0 | -min(30, safety_holds × 8) |
| `aging_critical_defects` | aging_critical > 0 (>14d) | -min(35, aging × 10) |
| `critical_defects` | critical_defects > 0 (only if no aging) | -min(28, critical × 8) |
| `oos_units` | oos_units > 0 | -min(20, oos × 3) |
| `maint_holds` | maint_holds > 0 | -min(12, maint × 2) |
| `defect_backlog` | open_defects > 10 (only if no critical) | -min(15, open // 3) |
| `work_order_backlog` | work_orders_open > 15 | -min(15, wo // 5) |
| `overdue_inspections` | overdue_insp > 0 | -min(12, overdue × 3) |
| `dvir_open_defects` | dvir_open_defects > 0 | -min(15, dvir × 3) |
| `equipment_incidents` | equip_incidents_7d > 0 | -min(25, incidents × 10) |

## Attention level thresholds (universal)
- ≥85 → LOW
- 65–84 → MEDIUM
- 40–64 → HIGH
- <40 → CRITICAL

## Confidence
- `high` when fleet_total ≥ 10 AND (open_defects + work_orders_open) ≥ 5
- `medium` otherwise
- `insufficient_data` when every shop collection is empty

## Trend
Uses the universal engine trend model (Track 19.41). Trend engages
once history rows accumulate; until then trend_direction renders "→"
with `pct_change: None` (never faked).
