# Transportation Feature Ownership Matrix

**Constitutional rule (Track 18.09C):** Transportation Operations owns Transportation. Administration oversees Transportation.

Each row classifies a Transportation capability as **OPERATIONAL** (execution lives in Transportation Operations), **GOVERNANCE** (oversight lives in Administration), or **SHARED** (operational execution in Transportation Operations + read-only oversight in Administration).

## Classification key
| Code | Meaning |
|---|---|
| OPERATIONAL | Lives in Transportation Operations workspace. Operational users do the work here. |
| GOVERNANCE | Lives in Administration. Admin / Trust Center observes; no operational execution. |
| SHARED | Operational execution in Transportation Operations; read-only oversight in Administration via the same source-of-truth component. |

## Full matrix

| # | Capability | Current location | Classification | Notes |
|---|---|---|:---:|---|
| 1 | Mission Control (Transportation Dashboard) | `pages/transportation/MissionControl.jsx` + `_views.jsx::TransportationDashboard` | OPERATIONAL | The operator's first surface of the day. |
| 2 | Dispatch Bridge | `pages/transportation/_dispatch_bridge.jsx` | OPERATIONAL | Launches into Dispatch portal; never replaces it. |
| 3 | Live Operations workspace | `pages/transportation/_live_operations.jsx` | OPERATIONAL | Read-only GPS / proximity awareness inside TX. |
| 4 | Dispatch Board | `/dispatch-portal/board` | OPERATIONAL | Lives in Dispatch portal (its own system of record). |
| 5 | Dispatch Command Center | `/dispatch-portal/command` | OPERATIONAL | Same. |
| 6 | Live Operations Map (Dispatch) | `/dispatch-portal/map` | OPERATIONAL | Same. |
| 7 | Haul Ledger | `/dispatch-portal/haul-ledger` | OPERATIONAL | Same. |
| 8 | Driver Qualification (Dispatcher view) | `/dispatch-portal/driver-qualification` | OPERATIONAL | Same. |
| 9 | Drivers List + Workspace | `pages/transportation/_lists.jsx::DriversList / DriverWorkspace` | OPERATIONAL | Canonical operator-facing driver surface. |
| 10 | Driver Command Profile (admin oversight view) | `pages/admin/AdminDriverIntel.jsx` | SHARED | Same `DriverCommandProfile` component rendered in admin shell for oversight. |
| 11 | Carriers List + Workspace | `_lists.jsx::CarriersList / CarrierWorkspace` | OPERATIONAL | |
| 12 | Trucks List + Workspace (Fleet) | `_lists.jsx::TrucksList / TruckWorkspace` | OPERATIONAL | |
| 13 | Fleet Readiness | `pages/transportation/_widgets.jsx` (readiness cards inside TX) | OPERATIONAL | |
| 14 | Carrier Readiness | same | OPERATIONAL | |
| 15 | Driver Readiness | same | OPERATIONAL | |
| 16 | Orientation Center | `_orientation.jsx` | OPERATIONAL | |
| 17 | Compliance Dashboard | `_views.jsx::ComplianceDashboard` | OPERATIONAL | |
| 18 | DOT Documents / Medical Cards / CDLs / Insurance / Authority | `_views.jsx::DocumentCenter` + workspace tabs | OPERATIONAL | |
| 19 | Vehicle Documents | same | OPERATIONAL | |
| 20 | Maintenance & Inspections | `_views.jsx::InspectionCenter` | OPERATIONAL | |
| 21 | Rate Schedules | `_views.jsx::RateScheduleCenter` | OPERATIONAL | |
| 22 | Transportation Intelligence | `_intelligence.jsx` | OPERATIONAL | |
| 23 | Automation Center | `_command_queue.jsx::CommandQueueCenter` | OPERATIONAL | |
| 24 | Cleanup Center | same | OPERATIONAL | |
| 25 | Transportation Reports | `_views.jsx::ReportsView` | OPERATIONAL | |
| 26 | Transportation Search | `pages/transportation/TransportationSearch.jsx` | OPERATIONAL | `/` keyboard shortcut focuses input. |
| 27 | Global Search (cross-workspace) | platform sidebar | SHARED | Existed before 18.09C; cross-workspace by nature. |
| 28 | Right Rail | `design-system/PortalShell.jsx` | OPERATIONAL | Composed inside the operational shell. |
| 29 | Notifications | shell composition | SHARED | |
| 30 | Audit Timeline (TX) | `_views.jsx::AuditTimeline` | OPERATIONAL | Read-only within TX. |
| 31 | Audit Log (cross-portal) | `pages/admin/AdminAuditLog.jsx` | GOVERNANCE | Cross-portal audit ledger — admin-only. |
| 32 | Operations Events nervous system | `pages/admin/AdminOperationsEvents.jsx` | GOVERNANCE | Platform-wide telemetry; read-only. |
| 33 | Operations Dashboard | `pages/admin/AdminOperationsDashboard.jsx` | GOVERNANCE | Read-only operational counts. |
| 34 | Compliance Findings (cross-portal) | `pages/admin/AdminComplianceFindings.jsx` | GOVERNANCE | Cross-portal contradiction detection. |
| 35 | Geofence Reconciliation | `pages/admin/AdminGeofenceReconciliation.jsx` | GOVERNANCE | Privileged Motive↔project mapping approval. |
| 36 | Operational Metrics widgets | `_widgets.jsx` | OPERATIONAL | |
| 37 | Alerts (TX shell) | composed in `PortalShell` | OPERATIONAL | |
| 38 | Quick Actions | TX shell | OPERATIONAL | |
| 39 | Drawer Actions | TX shell components | OPERATIONAL | |
| 40 | Card Actions | TX shell components | OPERATIONAL | |
| 41 | Breadcrumbs / Context Menus | TX shell | OPERATIONAL | |
| 42 | Transportation route prefixes | `/admin/transportation/*` (oversight) + `/transportation-operations/*` (operational) | SHARED | One router, two doorways. |

## Conclusion

Zero forks of business logic. Zero duplicated data. Zero forked auth contracts. The Transportation Experience Layer is owned by Transportation; Administration receives oversight via the admin-gated alias route.
