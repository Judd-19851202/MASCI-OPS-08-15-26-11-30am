# Daily Posture Dashboard Certification

## Surface
Top of `/safety/trench-safety` (Hub) and `/admin/trench-safety` (Admin mirror). Renders **above** the existing KPI / breakdown / alerts sections — no scrolling required.

## Component
`DailyPosturePanel` in `TrenchSafetyOpsCenter.jsx`.

## Tiles (9 — per directive)
| Tile | Source | Filtered view on click |
|---|---|---|
| Open Safety Holds | `counts_by_status["Safety Hold"]` | `…/assets?status=Safety+Hold` |
| Open Inspection Holds | `counts_by_status["Inspection Hold"]` | `…/assets?status=Inspection+Hold` |
| Open Certification Holds | `counts_by_status["Certification Hold"]` | `…/assets?status=Certification+Hold` |
| Repairs Awaiting Verification | `alerts.repairs_awaiting_verification` | `…/repair-review?status=awaiting` |
| Critical Repairs | `alerts.critical_repairs` | `…/repair-review?severity=Critical` |
| Failed Inspections Last 7 Days | `alerts.failed_inspections_7d` | `…/assets?needs_review=yes` |
| Damage Reports Awaiting Review | `alerts.new_damage_reports_7d` | `…/field-reports` |
| Certifications Expiring 30 Days | `alerts.expiring_certifications_30d` | `…/assets?needs_review=yes` |
| Assets Out Of Service | `counts_by_status["Maintenance Hold"] + counts_by_status["Retired"]` | `…/assets` |

Every tile is a button. Click navigates to a filtered view.

## Data source
`GET /api/trench-safety/dashboard` (existing). No new endpoint.

## Severity coloring
- `danger` (red) — Open Safety Holds, Critical Repairs.
- `warn` (amber) — Inspection/Cert Holds, Awaiting Verification, Failed 7d, Damage Reports, Cert Exp 30d.
- `default` (slate) — Out Of Service.

Matches the existing MASCI severity palette used elsewhere in the platform.

## Verdict
🟢 PASS — Production-ready.
