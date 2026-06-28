# Role Workday Analysis — Where each Transportation role spends 95% of their day

**Constitutional rule (Track 18.09C):** If a Transportation operational role spends meaningful time in Administration, that is an architectural defect.

## Role-by-role analysis

| Role | Primary workspace | Secondary | Administration time | Defect? |
|---|---|---|:---:|:---:|
| Dispatcher | `/dispatch-portal/*` (board, command, map, ledger) | `/transportation-operations/*` (drivers, carriers, trucks for context) | 0% | ❌ none |
| Transportation Manager | `/transportation-operations/*` (mission control, lists, intelligence) | `/dispatch-portal/*` (oversight) | 0% | ❌ none |
| Fleet Manager | `/transportation-operations/trucks` (lists, workspace, inspections) | `/transportation-operations/compliance` | 0% | ❌ none |
| Carrier Coordinator | `/transportation-operations/carriers` | `/transportation-operations/compliance` | 0% | ❌ none |
| Driver Coordinator | `/transportation-operations/drivers` | `/transportation-operations/orientation` | 0% | ❌ none |
| Orientation Coordinator | `/transportation-operations/orientation` | `/transportation-operations/drivers` | 0% | ❌ none |
| Compliance Coordinator | `/transportation-operations/compliance` | `/transportation-operations/documents` | 0% | ❌ none |
| Transportation Director | `/transportation-operations/intelligence` + Mission Control | `/transportation-operations/reports` | 0% | ❌ none |
| Operations Executive | `/admin/executive-overview` (read-only) + Mission Control | Cross-portal scan | ~15% (read-only governance) | ❌ none — executives **should** consume governance dashboards |
| Super Admin | `/admin/*` | Cross-portal oversight | 95% | ❌ none — this is the role's intended workday |

## Findings

* **Eight Transportation operational roles spend 0% of their day in Administration.** ✅
* **Operations Executive uses Administration's executive-overview surface.** That is governance consumption, not operational execution — which is exactly what the constitutional rule prescribes.
* **Super Admin lives in Administration by design.** No defect.

## Pre-18.09C anti-pattern (now closed)

* A dispatch-authenticated user (Dispatcher / Transportation Manager / Fleet Manager / Carrier Coordinator / Driver Coordinator / Orientation Coordinator / Compliance Coordinator) hitting any of these six legacy URLs:
  * `/transportation-operations/compliance/documents`
  * `/transportation-operations/compliance/rate-schedules`
  * `/transportation-operations/fleet`
  * `/transportation-operations/fleet/trucks`
  * `/transportation-operations/fleet/inspections`
  * `/transportation-operations/administration/audit`
* …was silently redirected into the **admin shell** at `/admin/transportation/...`, where the admin token requirement would deny entry.
* **This is now closed.** Redirects are path-relative (`relative="path"`) so an operational user stays in the operational shell.

## Verdict

🟢 **Every Transportation operational role spends ~100% of their workday inside Transportation Operations + Dispatch portal.** Administration is never a required stop.
