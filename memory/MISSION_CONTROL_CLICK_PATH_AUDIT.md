# Mission Control Click-Path Audit · Track 18.12

**Mission:** every visible clickable element under `/transportation-operations/*` must work for dispatch-authenticated users without bouncing into the admin shell.

## Files audited

| File | Role | Audit findings |
|---|---|---|
| `pages/transportation/MissionControl.jsx` | Mission Control cards (8) + workspace strip + recent activity card | All `actionHref` / `drillHref` previously hardcoded `/admin/transportation/...` — now use `${prefix}/...` |
| `pages/transportation/TransportationApp.jsx` | Mount router for both doorways | Routes defined: dispatch, drivers, carriers, trucks, compliance, orientation, intelligence/*, command-queue/*, reports, audit. Compat redirects already path-relative (Track 18.09C). |
| `pages/transportation/_shared.jsx` | `TransportationSubNav` (NavLink) + helpers | `NavLink to=` previously hardcoded `/admin/transportation/...` — now uses `${prefix}/${item.to}`. New `useTxPathPrefix()` hook exported. `useTxLocation()` now strips either prefix. |
| `pages/transportation/_views.jsx` | `TopCleanupOpportunityCard` `cleanupHref` | Previously hardcoded — now `${prefix}/intelligence/cleanup`. |
| `pages/transportation/_command_queue.jsx` | Command Queue sub-tabs | Previously hardcoded — now `${prefix}/command-queue/${t.to}`. |
| `pages/transportation/TransportationSearch.jsx` | Universal Search result router | `onPickResult` now rewrites backend-emitted `/admin/transportation/...` routes to the active prefix before navigating. |
| `pages/transportation/TransportationWorkspaceShell.jsx` | Right Rail (`RelatedRow`, `AuditRow`) | `to={row.route ...}` now passes through `_rewriteToPrefix()` which converts backend-emitted admin routes to the active prefix. |
| `components/transportation/TransportationOpsTopBar.jsx` | Workspace TopBar | Already used `/transportation-operations` — verified, no regression. |
| `components/transportation/TxOpsRestricted.jsx` | Transportation-branded restricted state | Already correct. Used inline (no admin redirect). |
| `pages/transportation/_widgets.jsx` | Backend API URL helpers (carrier/person document uploads) | These are **backend API URLs** (`${API}/api${url}`), legitimately preserve the `/admin/transportation` prefix. Not user-facing nav. |

## Click-path matrix

| # | Component / File | Visible label | Prev route (broken for dispatch) | Fixed route (active prefix) | Role visibility | Pre-fix dispatch behavior | Pre-fix admin behavior | Fix applied | Post-fix dispatch | Post-fix admin | Pass/Fail |
|---|---|---|---|---|---|---|---|---|---|---|:---:|
| 1 | `MissionControl.jsx` Card 1 | "Open Fleet" | `/admin/transportation/trucks` | `${prefix}/trucks` | all | admin denial | OK | prefix-aware | TX shell trucks workspace | admin shell trucks workspace | ✅ |
| 2 | `MissionControl.jsx` Card 1 drill | "View details →" | `/admin/transportation/inspections` | `${prefix}/inspections` | all | admin denial | OK | prefix-aware | TX inspection center | admin inspection center | ✅ |
| 3 | `MissionControl.jsx` Card 2 | "Open Drivers" | `/admin/transportation/drivers` | `${prefix}/drivers` | all | admin denial | OK | prefix-aware | TX drivers | admin drivers | ✅ |
| 4 | `MissionControl.jsx` Card 2 drill | "View details →" | `/admin/transportation/intelligence` | `${prefix}/intelligence` | all | admin denial | OK | prefix-aware | TX intelligence | admin intelligence | ✅ |
| 5 | `MissionControl.jsx` Card 3 | "Open Carriers" | `/admin/transportation/carriers` | `${prefix}/carriers` | all | admin denial | OK | prefix-aware | TX carriers | admin carriers | ✅ |
| 6 | `MissionControl.jsx` Card 3 drill | "View details →" | `/admin/transportation/compliance` | `${prefix}/compliance` | all | admin denial | OK | prefix-aware | TX compliance | admin compliance | ✅ |
| 7 | `MissionControl.jsx` Card 4 | "Open Dispatch" | `/admin/transportation/dispatch` | `${prefix}/dispatch` | all | admin denial | OK | prefix-aware | TX dispatch bridge | admin dispatch bridge | ✅ |
| 8 | `MissionControl.jsx` Card 4 drill | "View details →" | `/admin/transportation/live-operations` | `${prefix}/live-operations` | all | admin denial | OK | prefix-aware | TX live ops | admin live ops | ✅ |
| 9 | `MissionControl.jsx` Card 5 | "Open Live Operations" | `/admin/transportation/live-operations` | `${prefix}/live-operations` | all | admin denial | OK | prefix-aware | TX live ops | admin live ops | ✅ |
| 10 | `MissionControl.jsx` Card 5 drill | "View details →" | `/admin/transportation/intelligence/cleanup` | `${prefix}/intelligence/cleanup` | all | admin denial | OK | prefix-aware | TX cleanup | admin cleanup | ✅ |
| 11 | `MissionControl.jsx` Card 6 (RecentActivity) | "Open audit timeline" | `/admin/transportation/audit` | `${prefix}/audit` | all | admin denial | OK | prefix-aware | TX audit | admin audit | ✅ |
| 12 | `MissionControl.jsx` Card 7 | "Open Cleanup" | `/admin/transportation/intelligence/cleanup` | `${prefix}/intelligence/cleanup` | all | admin denial | OK | prefix-aware | TX cleanup | admin cleanup | ✅ |
| 13 | `MissionControl.jsx` Card 7 drill | "View details →" | `/admin/transportation/command-queue` | `${prefix}/command-queue` | all | admin denial | OK | prefix-aware | TX command queue | admin command queue | ✅ |
| 14 | `MissionControl.jsx` Card 8 | "Open the workflow" | one of 4 admin paths | `${prefix}/{path}` | all | admin denial | OK | prefix-aware | TX path | admin path | ✅ |
| 15 | `MissionControl.jsx` Workspace Strip · Dispatch | "Dispatch" | n/a (NEW) | `${prefix}/dispatch` | all | n/a | n/a | new in 18.12 | TX dispatch | admin dispatch | ✅ |
| 16 | `MissionControl.jsx` Workspace Strip · 7 more | Drivers/Carriers/Fleet/Orientation/Compliance/Live Operations/Cleanup | n/a (NEW) | `${prefix}/...` each | all | n/a | n/a | new in 18.12 | TX | admin | ✅ |
| 17 | `_shared.jsx` SubNav · Operations group | Dispatch / Live Operations / Trucks | `/admin/transportation/${item.to}` | `${prefix}/${item.to}` | all | admin denial | OK | prefix-aware | TX | admin | ✅ |
| 18 | `_shared.jsx` SubNav · People group | Drivers / Carriers | same | same | all | admin denial | OK | prefix-aware | TX | admin | ✅ |
| 19 | `_shared.jsx` SubNav · Compliance group | Compliance / Orientation | same | same | all | admin denial | OK | prefix-aware | TX | admin | ✅ |
| 20 | `_shared.jsx` SubNav · Intelligence group | Intelligence / Automation / Cleanup | same | same | all | admin denial | OK | prefix-aware | TX | admin | ✅ |
| 21 | `_shared.jsx` SubNav · Administration group | Reports / Administration | same | same | all | admin denial | OK | prefix-aware | TX | admin | ✅ |
| 22 | `_views.jsx` TopCleanupOpportunityCard | "Open in Cleanup" | `/admin/transportation/intelligence/cleanup` | `${prefix}/intelligence/cleanup` | all | admin denial | OK | prefix-aware | TX cleanup | admin cleanup | ✅ |
| 23 | `_command_queue.jsx` Sub-tabs | Morning Queue / Health / Forecast | `/admin/transportation/command-queue/${t.to}` | `${prefix}/command-queue/${t.to}` | all | admin denial | OK | prefix-aware | TX | admin | ✅ |
| 24 | `TransportationSearch.jsx` result click | (depends on result.route) | varies (admin) | rewritten to active prefix | all | admin denial if route was admin | OK | _rewriteToPrefix on navigate | TX | admin | ✅ |
| 25 | `TransportationWorkspaceShell.jsx` RelatedRow | (depends on row.route) | varies | rewritten | all | admin denial if admin | OK | `_rewriteToPrefix` | TX | admin | ✅ |
| 26 | `TransportationWorkspaceShell.jsx` AuditRow | (depends on row.route) | varies + fallback `/admin/transportation/administration/audit` | rewritten + fallback `${prefix}/administration/audit` | all | admin denial | OK | `_rewriteToPrefix` + prefix-aware fallback | TX | admin | ✅ |

## Result
**26 click paths audited and locked.** No remaining user-facing `/admin/transportation/...` hardcoded hrefs in any Transportation Operations chrome file.

## Preserved by design
- All **backend API calls** (`txGet("/admin/transportation/...")`) — these are API prefixes, not user-facing routes. Directive: "API prefixes such as `/api/admin/transportation/*` are preserved."
- `pages/transportation/_widgets.jsx` document-upload URLs (line 51-53) — backend API URLs prepended with `${API}/api`.
