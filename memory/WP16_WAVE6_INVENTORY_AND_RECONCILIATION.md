# WP16 Wave 6 — Inventory & Operational Reconciliation

Date: 2026-07-30
Authorization: `WP16-EA-006`

## Executive scope statement

- Authorized work package: **Wave 6 – Inventory & Operational Reconciliation**
- Authorized scope: **inventory and reconciliation only**
- Repairs made: **None**
- Production code changes made: **None**
- Runtime inspection performed in this wave: **None**
- Source of truth used: route declarations, guard contracts, backend router registrations, and existing captured route evidence already stored under WP16 memory artifacts

## Wave 6 domain determination

The next operational domain after Executive-locked Wave 5 is:

- **Wave 6 — Dispatch & Transportation**

This determination is evidence-backed by the remaining unaudited operational route family in the existing route census:

- Dispatch operational routes under `/dispatch-portal/*`
- Transportation operational wrapper and tokenized routes under `/transportation-operations/*`, `/transport-invite/:token`, and `/transport-verify/:cnum`

Adjacent routes that remain **outside** the Wave 6 denominator because they are already owned by prior waves:

- Wave 1: `/dispatch-portal/login`, `/dispatch-portal/forgot-password`, `/dispatch-portal/reset/:token`, `/dispatch-portal/change-password`
- Wave 2: `/dispatch-portal`, `/dispatch-portal/hub_legacy`, `/dispatch-portal/hub_v2`
- Wave 3: `/admin/dispatch`, `/admin/transportation/*`
- Wave 5: `/pm/fleet`, `/safety-portal/fleet`

## Final Wave 6 denominator

- **Canonical Wave 6 denominator:** `10` route-pattern experiences
- Canonical route ownership model:
  - `7` Dispatch operational routes
  - `1` Transportation operational wrapper route with embedded child-route family
  - `2` tokenized/public Transportation verification routes

## Canonical route census

| W6 ID | Route | Experience name | Evidence source | Notes |
|---|---|---|---|---|
| W6-001 | `/dispatch-portal/board` | Dispatch Board | `AppRoutes.jsx:1171`, `WP16_ROUTE_EXERCISE_REGISTER.md:322` | CSV export strip already evidenced |
| W6-002 | `/dispatch-portal/command` | Dispatch Command Center | `AppRoutes.jsx:1172`, `WP16_ROUTE_EXERCISE_REGISTER.md:323` | Seven-tab operational command surface |
| W6-003 | `/dispatch-portal/fleet` | Dispatch Fleet Visibility | `AppRoutes.jsx:1173`, `WP16_ROUTE_EXERCISE_REGISTER.md:324` | Inherited prior evidence references `WP16-DEF-011` degradation |
| W6-004 | `/dispatch-portal/map` | Dispatch Operations Map | `AppRoutes.jsx:1185`, `WP16_ROUTE_EXERCISE_REGISTER.md:325` | Wrapper around shared operations map |
| W6-005 | `/dispatch-portal/haul-ledger` | Dispatch Haul Ledger | `AppRoutes.jsx:1188`, `WP16_ROUTE_EXERCISE_REGISTER.md:326` | Read-only ledger with filters |
| W6-006 | `/dispatch-portal/driver-qualification` | Dispatch Driver Qualification | `AppRoutes.jsx:1190`, `WP16_ROUTE_EXERCISE_REGISTER.md:327` | Read-only qualification surface |
| W6-007 | `/dispatch-portal/driver/:driverKey` | Dispatch Driver Command Profile | `AppRoutes.jsx:1192`, `WP16_ROUTE_EXERCISE_REGISTER.md:328` | Hidden/detail route requiring live driver key |
| W6-008 | `/transportation-operations/*` | Transportation Operations Wrapper | `AppRoutes.jsx:540`, `AppRoutes.jsx:479`, `WP16_ROUTE_EXERCISE_REGISTER.md:395` | Mixed dispatch/admin shell with 20 child routes and redirect aliases |
| W6-009 | `/transport-invite/:token` | External Carrier Invite | `AppRoutes.jsx:591`, `WP16_ROUTE_EXERCISE_REGISTER.md:396` | Public/tokenized onboarding detail route |
| W6-010 | `/transport-verify/:cnum` | Transportation Certificate Verify | `AppRoutes.jsx:592`, `WP16_ROUTE_EXERCISE_REGISTER.md:397` | Public/tokenized certificate verification detail route |

## Experience matrix

| W6 ID | Parent domain | Hidden/Public | CRUD / workflow class | Downloads / exports / print | Primary frontend file | Primary API dependencies | Permission boundary | Operational criticality |
|---|---|---|---|---|---|---|---|---|
| W6-001 | Dispatch | Protected | Create / read / transition / cancel / reassign / acknowledge | CSV exports: assignments, state-events, haul-cycles | `frontend/src/pages/DispatchBoard.jsx` | `/api/dispatch/assignments*`, `/api/dispatch/assignments/board`, `/api/dispatch/state-events`, `/api/dispatch/exports/*`, `/api/dispatch/transportation/check`, `/api/dispatch/transportation/override`, `/api/operational-attachments/*`, `/api/dispatch/operational-moments/*` | `RequireDispatch`; backend mix of dispatch-or-admin write and any-portal read | A |
| W6-002 | Dispatch | Protected | Read / broadcast / cross-tab command workflows | SMS broadcast audit trail | `frontend/src/pages/DispatchCommandCenter.jsx` | `/api/dispatch/command/summary`, `/fleet`, `/drivers`, `/jobs`, `/haul`, `/broadcast-sms`, `/broadcasts`, `/api/operational-intelligence/summary`, `/api/dispatch/motive-posture` | `RequireDispatch`; reads via any-portal token, write via dispatch-or-admin | A |
| W6-003 | Dispatch | Protected | Read / expand / audit / repair handoff / RTS handoff | Export-style defect detail via linked unit thread | `frontend/src/pages/FleetVisibility.jsx` | `/api/fleet/visibility*`, `/api/fleet/defects/{id}/detail`, `/api/integrations/maintainx/defect-coverage`, `/api/operations/drivers/{driverKey}/profile` via thread links | `RequireDispatch`; mixed admin/dispatch headers in shared fleet component | A |
| W6-004 | Dispatch | Protected | Read-only situational awareness | Map timeline / asset-card exploration | `frontend/src/pages/DispatchOperationsMapPage.jsx` | Shared `OperationsMapPage` API family, `/api/operations-map*`, `/api/dispatch/motive-posture` | `RequireDispatch`; shared operations-map auth contract | A |
| W6-005 | Dispatch | Protected | Read / filter / refresh | No direct file export on this surface; companion to map + downstream CSV context | `frontend/src/pages/DispatchHaulLedger.jsx` | `/api/dispatch/haul-ledger` | `RequireDispatch`; dispatch header required | B |
| W6-006 | Dispatch | Protected | Read-only compliance view | None | `frontend/src/pages/DispatchDriverQualification.jsx` | `/api/dispatch/driver-qualification` | `RequireDispatch`; dispatch-or-admin backend gate | B |
| W6-007 | Dispatch | Hidden detail | Read-only driver operational profile | None | `frontend/src/pages/DispatchDriverProfile.jsx` | `/api/operations/drivers/{driverKey}/profile` | `RequireDispatch`; backend role-shaped payload | B |
| W6-008 | Dispatch & Transportation | Protected mixed shell | Mixed read / create / edit / review / compliance / intelligence / automation | Certificate PDFs, packet/docs upload flows, future reports placeholder, admin digest preview/send, operational downloads inside child workflows | `frontend/src/pages/transportation/TransportationApp.jsx` | Transportation API families across `transportation*.py`, `dispatch/transportation/*`, `/api/operations/transportation/readiness`, `/api/admin/transportation/search`, `/related/*` | `RequireTransportationPortal`; child routes use admin-only, dispatch-or-admin, or any-portal gates depending on sub-route | A |
| W6-009 | Transportation | Public tokenized detail | Read / submit / orientation acknowledgement / document upload | Orientation certificates list | `frontend/src/pages/transportation/ExternalCarrierInvite.jsx` | `/api/transportation/invite/{token}`, `/submit`, `/orientation/modules`, `/orientation/assignments*`, `/orientation/certificates` | Public tokenized invite boundary | B |
| W6-010 | Transportation | Public tokenized detail | Read-only verification | Certificate display / verify | `frontend/src/pages/transportation/CertificateVerify.jsx` | `/api/transportation/orientation/certificates/verify/{cnum}` | Public certificate-number boundary | B |

## Transportation wrapper child-route census (`W6-008`)

### Canonical child routes mounted in `TransportationApp.jsx`

`TransportationApp.jsx:61-124` mounts the following child routes inside the Wave 6 wrapper:

1. `(index)` → Mission Control
2. `dispatch`
3. `live-operations`
4. `trucks`
5. `trucks/:id`
6. `drivers`
7. `drivers/:id`
8. `carriers`
9. `carriers/:id`
10. `compliance`
11. `orientation/*`
12. `academy`
13. `academy/:moduleKey`
14. `intelligence/*`
15. `command-queue/*`
16. `reports`
17. `audit`
18. `documents`
19. `inspections`
20. `rate-schedules`

### Redirect / alias child routes

1. `compliance/documents` → `../documents`
2. `compliance/rate-schedules` → `../rate-schedules`
3. `fleet` → `../trucks`
4. `fleet/trucks` → `../../trucks`
5. `fleet/inspections` → `../../inspections`
6. `administration/audit` → `../audit`

### Nested visible child states already evidenced in prior route capture

Source: `WP16_ROUTE_EXERCISE_REGISTER.md:403-438`

- Dispatch bridge workspace
- Live operations workspace
- Trucks list + `trucks/:id` detail
- Drivers list + `drivers/:id` detail
- Carriers list + `carriers/:id` workspace tabs
- Compliance dashboard
- Orientation dashboard + modules + `modules/:mid` + assignments + certificates + emails
- Academy + `academy/:moduleKey`
- Intelligence executive + recommendations + predictions + learning + cleanup
- Command queue root + `health` + `forecast`
- Reports placeholder
- Audit timeline
- Documents center
- Inspections center + inspection wizard state
- Rate schedules + new-version dialog state

## Modal / drawer / wizard inventory

| Modal ID | Surface | Modal / drawer / wizard | File | Purpose |
|---|---|---|---|---|
| W6-M01 | W6-001 | AssignmentDrawer | `frontend/src/components/dispatch/AssignmentDrawer.jsx` | Assignment detail, state actions, magic-link issue, cancel, reassign, revoke |
| W6-M02 | W6-001 | AssignmentCreateDrawer | `frontend/src/components/dispatch/AssignmentCreateDrawer.jsx` | New dispatch assignment creation |
| W6-M03 | W6-001 | OverrideRequiredModal | `frontend/src/components/dispatch/TransportationGate.jsx` | Transportation gate override acknowledgement |
| W6-M04 | W6-001 | WhyDrawer | `frontend/src/components/dispatch/DispatchDecisionChip.jsx` | Dispatch recommendation rationale |
| W6-M05 | W6-003 | RepairDrawer | `frontend/src/components/FleetRepairDrawer.jsx` | Shop repair handoff from fleet visibility |
| W6-M06 | W6-003 | RtsDrawer | `frontend/src/components/FleetRepairDrawer.jsx` | Return-to-service handoff |
| W6-M07 | W6-008 | LinkHRDriverModal | `frontend/src/pages/transportation/_modals.jsx` | Link HR CDL driver into Transportation |
| W6-M08 | W6-008 | AddLeasedDriverModal | `frontend/src/pages/transportation/_modals.jsx` | Create leased driver |
| W6-M09 | W6-008 | AddCarrierModal | `frontend/src/pages/transportation/_modals.jsx` | Create carrier |
| W6-M10 | W6-008 | EditCarrierModal | `frontend/src/pages/transportation/_modals.jsx` | Edit carrier |
| W6-M11 | W6-008 | FleetBulkAdoptionModal | `frontend/src/pages/transportation/_lists.jsx` | Bulk adopt fleet equipment into Transportation |
| W6-M12 | W6-008 | FleetOverlayEditModal | `frontend/src/pages/transportation/_lists.jsx` | Edit truck overlay / metadata |
| W6-M13 | W6-008 | SignaturePad | `frontend/src/pages/transportation/_widgets.jsx` | Capture signature for packets / attestations |
| W6-M14 | W6-008 | RateCreateDialog | `frontend/src/pages/transportation/_widgets.jsx` | Create new rate schedule |
| W6-M15 | W6-008 | InspectionWizard | `frontend/src/pages/transportation/_widgets.jsx` | Truck inspection creation / completion |
| W6-M16 | W6-008 | AffectedDrawer | `frontend/src/pages/transportation/_intelligence.jsx` | Cleanup/intelligence affected-record detail |

## API matrix

### Dispatch auth + portal operations

Source: `backend/routes/dispatch_portal_auth.py`

- `POST /api/dispatch/login`
- `GET /api/dispatch/me`
- `POST /api/dispatch/change-password`
- `POST /api/dispatch/forgot-password`
- `POST /api/dispatch/reset-password`
- `GET /api/admin/dispatch-users`
- `POST /api/admin/dispatch-users`
- `PATCH /api/admin/dispatch-users/{user_id}`
- `POST /api/admin/dispatch-users/{user_id}/reset-password`
- `POST /api/admin/dispatch-users/{user_id}/impersonate`
- `DELETE /api/admin/dispatch-users/{user_id}`
- `GET /api/dispatch/driver-qualification`
- `GET /api/dispatch/daily-reports`

### Dispatch lifecycle + exports + driver + continuity

Sources: `dispatch_lifecycle.py`, `dispatch_exports.py`, `dispatch_driver.py`, `dispatch_continuity.py`, `dispatch_haul_ledger.py`, `dispatch_decision_surface.py`

- `POST /api/dispatch/assignments`
- `GET /api/dispatch/assignments/board`
- `GET /api/dispatch/assignments`
- `GET /api/dispatch/assignments/{assignment_id}`
- `POST /api/dispatch/assignments/{assignment_id}/transition`
- `POST /api/dispatch/assignments/{assignment_id}/cancel`
- `POST /api/dispatch/assignments/{assignment_id}/reassign`
- `POST /api/dispatch/assignments/{assignment_id}/acknowledge`
- `POST /api/dispatch/assignments/{assignment_id}/send-magic-sms`
- `POST /api/dispatch/assignments/{assignment_id}/revise`
- `GET /api/dispatch/state-events`
- `GET /api/dispatch/haul-cycles`
- `GET /api/dispatch/lifecycle/states`
- `GET /api/dispatch/haul-activity`
- `GET /api/admin/dls/health-summary`
- `GET /api/dispatch/exports/assignments.csv`
- `GET /api/dispatch/exports/state-events.csv`
- `GET /api/dispatch/exports/haul-cycles.csv`
- `POST /api/dispatch/driver/start-shift`
- `GET /api/dispatch/driver/shift-lookups`
- `GET /api/dispatch/driver/assignment-lookups`
- `POST /api/dispatch/driver/magic-link`
- `POST /api/dispatch/driver/session/exchange`
- `GET /api/dispatch/driver/me`
- `GET /api/dispatch/driver/my-assignment`
- `POST /api/dispatch/driver/assignments/{assignment_id}/transition`
- `POST /api/dispatch/driver/assignments/{assignment_id}/acknowledge`
- `GET /api/dispatch/driver/sessions`
- `POST /api/dispatch/driver/sessions/{session_id}/revoke`
- `POST /api/dispatch/driver/breakdown-proof/upload`
- `GET /api/dispatch/continuity-events/kinds`
- `POST /api/dispatch/continuity-events`
- `GET /api/dispatch/continuity-events/by-assignment/{assignment_id}`
- `GET /api/dispatch/continuity-events/recent`
- `GET /api/dispatch/recovery/states`
- `GET /api/dispatch/recovery/by-shop`
- `POST /api/dispatch/recovery/{assignment_id}/transition`
- `GET /api/dispatch/recovery/{assignment_id}`
- `GET /api/dispatch/operational-moments/by-assignment/{assignment_id}`
- `GET /api/dispatch/haul-ledger`
- `GET /api/dispatch/transportation/recommendation`
- `POST /api/dispatch/transportation/recommendation/audit`

### Dispatch command center

Source: `backend/routes/dispatch_command_center.py`

- `GET /api/dispatch/command/summary`
- `GET /api/dispatch/command/fleet`
- `GET /api/dispatch/command/drivers`
- `GET /api/dispatch/command/jobs`
- `GET /api/dispatch/command/haul`
- `POST /api/dispatch/command/broadcast-sms`
- `GET /api/dispatch/command/broadcasts`

### Transportation operations foundation + experience + phase 2

Sources: `transportation.py`, `transportation_experience.py`, `transportation_phase2.py`

- `GET /api/admin/transportation/carriers`
- `POST /api/admin/transportation/carriers`
- `GET /api/admin/transportation/carriers/{cid}`
- `PATCH /api/admin/transportation/carriers/{cid}`
- `GET /api/admin/transportation/persons`
- `POST /api/admin/transportation/persons`
- `GET /api/admin/transportation/persons/{pid}`
- `PATCH /api/admin/transportation/persons/{pid}`
- `GET /api/admin/transportation/eligible-hr-cdl-drivers`
- `POST /api/admin/transportation/persons/link-from-hr`
- `GET /api/admin/transportation/trucks`
- `POST /api/admin/transportation/trucks`
- `GET /api/admin/transportation/trucks/{tid}`
- `PATCH /api/admin/transportation/trucks/{tid}`
- `GET /api/admin/transportation/fleet/equipment`
- `GET /api/admin/transportation/fleet/adoption-preview`
- `POST /api/admin/transportation/fleet/adoption-bulk`
- `GET /api/admin/transportation/eligibility/{target_type}/{target_id}`
- `GET /api/dispatch/transportation/eligible-drivers`
- `GET /api/dispatch/transportation/eligible-trucks`
- `GET /api/dispatch/transportation/status/{target_type}/{target_id}`
- `GET /api/admin/transportation/dashboard`
- `GET /api/admin/transportation/documents/queue`
- `GET /api/admin/transportation/inspections/queue`
- `GET /api/admin/transportation/audit-timeline`
- `GET /api/admin/transportation/timeline/{entity_type}/{entity_id}`
- `GET /api/admin/transportation/carriers/{cid}/workspace`
- `GET /api/admin/transportation/persons/{pid}/workspace`
- `GET /api/admin/transportation/trucks/{tid}/workspace`
- `GET /api/admin/transportation/rate-schedules`
- `POST /api/admin/transportation/rate-schedules`
- `PATCH /api/admin/transportation/rate-schedules/{rid}`
- `POST /api/admin/transportation/rate-schedules/{rid}/activate`
- `GET /api/admin/transportation/carriers/{cid}/packet`
- `POST /api/admin/transportation/carriers/{cid}/packet`
- `PATCH /api/admin/transportation/packets/{pid}`
- `POST /api/admin/transportation/packets/{pid}/submit`
- `POST /api/admin/transportation/packets/{pid}/approve`
- `POST /api/admin/transportation/packets/{pid}/needs-correction`
- `GET /api/admin/transportation/carriers/{cid}/documents`
- `POST /api/admin/transportation/carriers/{cid}/documents`
- `PATCH /api/admin/transportation/documents/{doc_id}/review`
- `GET /api/admin/transportation/persons/{pid}/documents`
- `POST /api/admin/transportation/persons/{pid}/documents`
- `PATCH /api/admin/transportation/driver-documents/{doc_id}/review`
- `GET /api/admin/transportation/trucks/{tid}/inspections`
- `POST /api/admin/transportation/trucks/{tid}/inspections`
- `GET /api/admin/transportation/inspections/{iid}`
- `PATCH /api/admin/transportation/inspections/{iid}`
- `POST /api/admin/transportation/inspections/{iid}/complete`
- `GET /api/admin/transportation/eligibility/v2/{target_type}/{target_id}`
- `GET /api/dispatch/transportation/trucks/{tid}/readiness`
- `GET /api/dispatch/transportation/carriers/{cid}/packet-status`
- `GET /api/dispatch/transportation/readiness-summary`

### Transportation orientation + public token flows

Source: `backend/routes/transportation_orientation.py`

- `GET /api/admin/transportation/orientation/modules`
- `GET /api/admin/transportation/academy/modules`
- `POST /api/admin/transportation/orientation/modules`
- `PATCH /api/admin/transportation/orientation/modules/{mid}`
- `PATCH /api/admin/transportation/orientation/modules/{mid}/placeholder`
- `GET /api/admin/transportation/orientation/modules/{mid}/questions`
- `POST /api/admin/transportation/orientation/modules/{mid}/questions`
- `POST /api/admin/transportation/orientation/assignments`
- `GET /api/admin/transportation/orientation/assignments`
- `POST /api/admin/transportation/orientation/assignments/{aid}/heartbeat`
- `GET /api/admin/transportation/orientation/assignments/{aid}/quiz`
- `POST /api/admin/transportation/orientation/assignments/{aid}/quiz`
- `GET /api/admin/transportation/orientation/certificates/{cid}`
- `GET /api/transportation/orientation/certificates/verify/{cnum}`
- `POST /api/admin/transportation/invites`
- `GET /api/transportation/invite/{token}`
- `POST /api/transportation/invite/{token}/submit`
- `GET /api/admin/transportation/orientation/dashboard`
- `GET /api/admin/transportation/orientation/certificates`
- `GET /api/transportation/invite/{token}/orientation/modules`
- `POST /api/transportation/invite/{token}/orientation/assignments`
- `GET /api/transportation/invite/{token}/orientation/assignments/{aid}`
- `POST /api/transportation/invite/{token}/orientation/assignments/{aid}/heartbeat`
- `GET /api/transportation/invite/{token}/orientation/assignments/{aid}/quiz`
- `POST /api/transportation/invite/{token}/orientation/assignments/{aid}/quiz`
- `GET /api/transportation/invite/{token}/orientation/certificates`

### Transportation automation + intelligence + search + relationships + readiness

Sources: `transportation_automation.py`, `transportation_dispatch_gate.py`, `transportation_intelligence.py`, `transportation_search.py`, `transportation_relationships.py`, `operations_transportation_integration.py`

- `POST /api/admin/transportation/automation/run`
- `POST /api/admin/transportation/automation/dry-run`
- `GET /api/admin/transportation/automation/runs`
- `GET /api/admin/transportation/automation/health`
- `GET /api/admin/transportation/automation/actions`
- `PATCH /api/admin/transportation/automation/actions/{aid}`
- `GET /api/admin/transportation/automation/forecast`
- `GET /api/admin/transportation/automation/events`
- `GET /api/dispatch/transportation/visibility`
- `GET /api/admin/transportation/automation/digest/preview`
- `POST /api/admin/transportation/automation/digest/dry-run`
- `POST /api/admin/transportation/automation/digest/send-now`
- `GET /api/admin/transportation/automation/digest/runs`
- `GET /api/admin/transportation/hr-sync`
- `GET /api/admin/transportation/hr-sync/report`
- `GET /api/admin/hr/transportation-status`
- `GET /api/admin/hr/transportation-readiness`
- `POST /api/dispatch/transportation/check`
- `POST /api/dispatch/transportation/override`
- `GET /api/admin/transportation/dispatch-overrides`
- `POST /api/admin/transportation/dispatch-overrides/{oid}/revoke`
- `GET /api/admin/transportation/email-routes`
- `PATCH /api/admin/transportation/email-routes/{route_key}`
- `GET /api/admin/transportation/intelligence/drivers/{driver_id}`
- `GET /api/admin/transportation/intelligence/carriers/{carrier_id}`
- `GET /api/admin/transportation/intelligence/trucks/{truck_id}`
- `GET /api/admin/transportation/intelligence/dashboard`
- `GET /api/admin/transportation/intelligence/operational-health`
- `GET /api/admin/transportation/intelligence/recommendations`
- `GET /api/admin/transportation/intelligence/predictions`
- `GET /api/admin/transportation/intelligence/audit`
- `GET /api/admin/transportation/intelligence/dispatch-learning`
- `GET /api/admin/transportation/intelligence/cleanup-signals`
- `GET /api/admin/transportation/intelligence/cleanup-signals/{signal_key}`
- `POST /api/admin/transportation/intelligence/cleanup-signals/{signal_key}/materialize-actions`
- `GET /api/admin/transportation/search`
- `GET /api/admin/transportation/related/{entity_type}/{entity_id}`
- `GET /api/operations/transportation/readiness`

### API census summary

- Total reconciled endpoint patterns across Wave 6 domain: **184**
- Endpoint-bearing backend modules reconciled: **18**

## Permission matrix

| Surface / family | Frontend guard | Backend gate | Effective access posture |
|---|---|---|---|
| `/dispatch-portal/*` operational routes | `RequireDispatch` | `make_require_dispatch_token` or `make_require_dispatch_or_admin` depending on route | Dispatch primary; admin allowed on selected shared read/write endpoints |
| Dispatch board reads | `RequireDispatch` | `require_any_portal_token` for reads, `require_dispatch_or_admin` for writes | Read cross-portal; write dispatch/admin |
| Dispatch command center | `RequireDispatch` | reads via any-portal token, SMS broadcast via dispatch-or-admin | Mixed read/write split |
| Fleet visibility scope=`dispatch` | Shared fleet component | admin + dispatch headers | Shared component with dispatch-focused rendering |
| Driver command profile | `RequireDispatch` | backend role-shaped response from shared operations driver profile | Hidden detail, server-side redaction authoritative |
| `/transportation-operations/*` wrapper | `RequireTransportationPortal` | mixed admin-only / dispatch-or-admin / any-portal per child route | Shared shell, route-level capability varies |
| Transportation list/workspace reads | wrapper | many `/api/admin/transportation/*` endpoints now accept dispatch-or-admin through local gate | Shared admin/dispatch operations door |
| Orientation / academy admin authoring | wrapper | mostly admin-only | Dispatch can see allowed nav subset only |
| Intelligence deep analytics | wrapper | admin-only on most endpoints | Hidden from dispatch nav except allowed cleanup/ops surfaces |
| Public invite / verify routes | none | tokenized public endpoints | Public detail boundaries |
| Transportation search / relationships | wrapper | any-portal gate with actor-filtered results | Cross-portal trust dependency |

## Downloads / exports / print / PDF workflows

| Experience | Workflow |
|---|---|
| W6-001 Dispatch Board | CSV downloads for assignments, state events, and haul cycles via authenticated fetch |
| W6-003 Fleet Visibility | Deep-link out to fleet unit thread and detail/audit surfaces |
| W6-008 Transportation wrapper | carrier packet/signature flows, document uploads/review, inspection wizard, digest preview/send-now, certificate access, future reports placeholder |
| W6-009 External Carrier Invite | orientation certificate listing after invite progression |
| W6-010 Certificate Verify | public certificate verification display |

## Mobile-specific and tokenized experiences

- `W6-007` driver command profile detail is a hidden/detail route with role-shaped payloads
- `W6-009` external carrier invite is a public tokenized operational workflow intended for non-portal users
- `W6-010` certificate verification is a public tokenized detail route
- Transportation wrapper child workspaces include mobile-sensitive drawers/wizards, especially:
  - truck inspection wizard
  - rate create dialog
  - signature pad
  - carrier / driver / HR-link modals

## Trust dependencies and integrations

| Dependency | Where it appears | Why it matters |
|---|---|---|
| Dispatch portal token contract (`masci.dispatch.token`) | Dispatch routes and shared auth headers | Primary trust boundary for Wave 6 protected routes |
| Admin directory token contract | shared dispatch/admin and transportation admin routes | Secondary trust boundary for mixed read/write access |
| Shared `buildScopedPortalAuthHeaders()` | Dispatch and Transportation frontend consumers | Single-source auth-header generation for mixed-role surfaces |
| People & Access / directory portal grants | dispatch login fallback, dispatch/admin mixed access | Cross-portal entitlement trust |
| Twilio / SMS callback | dispatch lifecycle + command center | Magic-link and broadcast operational continuity |
| Motive posture / GPS map integrations | dispatch map, command center, fleet views | Live awareness and posture honesty |
| MaintainX defect coverage | Dispatch Fleet Visibility | Fleet defect readiness / inherited known degradation reference |
| HR sync / HR CDL link flows | Transportation driver linking and readiness | Cross-domain compliance trust |
| Transportation email routes / pilot send infrastructure | orientation and dispatch gate | Notification / invite delivery trust |
| Operations Transportation Readiness widgets | `live-operations` child route | Shared PM / operations / transportation awareness integration |

## Certification matrix

| W6 ID | Requires certification? | Why |
|---|---|---|
| W6-001 | Yes | Core dispatch lifecycle creation and state transitions |
| W6-002 | Yes | Broadcast communications and live command summary |
| W6-003 | Yes | Fleet availability, OOS visibility, repair trust |
| W6-004 | Yes | Live operations map awareness |
| W6-005 | Yes | Material movement ledger / proof visibility |
| W6-006 | Yes | Driver qualification and compliance readiness |
| W6-007 | Yes | Hidden driver operational profile / role-shaped data |
| W6-008 | Yes | Transportation operations shell with compliance, automation, and intelligence workflows |
| W6-009 | Yes | External carrier onboarding / attestation trust |
| W6-010 | Yes | Public certificate verification trust |

## Risk register

| Risk ID | Category | Description | Evidence / source | Impact on future inspection |
|---|---|---|---|---|
| W6-R01 | Prior known operational degradation | Dispatch Fleet Visibility inherited a prior evidence note referencing `WP16-DEF-011` fleet-GPS / intelligence degradation. This wave did not reproduce or repair it. | `WP16_ROUTE_EXERCISE_REGISTER.md:324`, `PRD.md:698` | Inspection must verify whether the degradation remains live before any PASS can be granted on W6-003 |
| W6-R02 | Fixture dependency | W6-007, W6-009, and W6-010 require live driver keys, invite tokens, or certificate numbers for full inspection. | `WP16_ROUTE_EXERCISE_REGISTER.md:328`, `396`, `397` | Inspection must obtain live fixtures or explicitly classify missing-data blockers |
| W6-R03 | Mixed-role auth complexity | Transportation wrapper child routes mix admin-only, dispatch-or-admin, and any-portal gates under one shell. | `transportation/_shared.jsx:27-36`, `366-400`; backend transportation route family | Gate 5 permission testing must be route-by-route, not shell-level only |
| W6-R04 | Shared-header trust dependency | Dispatch and Transportation rely heavily on shared auth-header generation and prefix-aware path helpers. | `buildScopedPortalAuthHeaders`, `txHeaders`, `visibleTxOpsNavGroups`, `useTxPathPrefix` | Hidden/detail-route authorization must be regression-tested carefully in inspection |
| W6-R05 | Export / notification dependency | CSV export, SMS broadcast, email route, digest preview/send, and public invite/certificate flows rely on external integrations and token continuity. | Dispatch exports, command center, transportation automation, orientation/invite routes | Inspection must verify network success and truthful fail states, not just UI render |

## Reconciliation findings

1. **Wave 6 domain established as Dispatch & Transportation.** Prior-wave auth/home/admin surfaces were separated from the next operational denominator.
2. **Canonical denominator is 10 route-pattern experiences.** This matches the remaining operational domain boundary without double-counting prior-wave auth or admin oversight routes.
3. **Transportation wrapper is the dominant complexity node.** One canonical route (`W6-008`) expands into 20 mounted child routes, 6 redirect aliases, and multiple nested visible states.
4. **No new defect was reproduced in this inventory-only phase.** Prior evidence references were preserved as risk input only.
5. **No production behavior was changed.** This package is documentation and reconciliation only.

## Recommended inspection plan

Inspect in exact canonical order:

1. `W6-001` Dispatch Board
2. `W6-002` Dispatch Command Center
3. `W6-003` Dispatch Fleet Visibility
4. `W6-004` Dispatch Operations Map
5. `W6-005` Dispatch Haul Ledger
6. `W6-006` Dispatch Driver Qualification
7. `W6-007` Dispatch Driver Command Profile
8. `W6-008` Transportation Operations Wrapper
9. `W6-009` External Carrier Invite
10. `W6-010` Transportation Certificate Verify

### W6-008 sub-plan

When inspection is authorized, break `W6-008` into these mandatory sub-groups:

- Mission Control / search rail
- Dispatch bridge
- Live operations
- Trucks list + truck detail + inspection wizard
- Drivers list + driver detail
- Carriers list + carrier workspace tabs
- Compliance + documents + inspections + rate schedules
- Orientation + academy + token-linked certificate flows
- Intelligence + command queue + cleanup / affected drawer
- Reports + audit + redirect alias behavior

### Gate emphasis for Wave 6

- **Gate 1 Routing:** hidden detail routes (`W6-007`, token routes, wrapper redirects)
- **Gate 4 API/Data:** CSV exports, gate preview/override, workspace detail APIs, invite/certificate verification
- **Gate 5 Permissions:** dispatch vs admin vs public token boundaries
- **Gate 7 Workflow:** assignment lifecycle, continuity events, packet/docs/inspection review, orientation invite lifecycle
- **Gate 8 Life Safety / Compliance:** fleet OOS truth, driver qualification, compliance packet review, certificate trust

## Evidence references

- `frontend/src/app/routing/AppRoutes.jsx:479, 540, 591, 592, 1171-1192`
- `frontend/src/pages/transportation/TransportationApp.jsx:61-124`
- `frontend/src/components/RequireDispatch.jsx:1-47`
- `frontend/src/components/RequireTransportationPortal.jsx:1-57`
- `frontend/src/pages/transportation/_shared.jsx:27-36, 96-173, 366-420`
- `WP16_ROUTE_EXERCISE_REGISTER.md:322-328, 395-438`
- `WP16_SCREEN_REGISTRY.md:323-329, 396-430`
- Backend route files listed in API matrix above

## Executive readiness statement

- Wave 6 canonical denominator established: **10**
- Child-route complexity documented: **20 mounted child routes + 6 redirects + nested modal/workflow inventory**
- API census documented: **184 endpoint patterns across 18 backend modules**
- Permissions and trust dependencies documented: **Yes**
- Production modifications made: **None**

**READY FOR WAVE 6 INSPECTION AUTHORIZATION**