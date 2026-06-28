TRANSPORTATION API AUTH MATRIX
==============================

DATE  : 2026-02-15
SCOPE : Every backend endpoint called by /transportation-operations/*.
        Tokens evaluated: admin, dispatch, hr, pm, safety, shop, fl,
        multi-login portal_tokens.*, anonymous.

Conventions:
  ✅ = accepts                 ❌ = rejects (401/403)
  ✓R = read-only (via cross-portal helper)
  —  = N/A
  ADMIN-STRICT means /api/admin/* requires X-Admin-Token; backend gate
  is `require_admin`. Some endpoints also tolerate a directory session
  token if the multi-login flow set X-Directory-Token.

| # | Endpoint                                                              | Frontend caller                       | admin | dispatch | hr | pm | safety | shop | fl | anon | Class | Notes |
|---|-----------------------------------------------------------------------|---------------------------------------|-------|----------|----|----|--------|------|----|------|-------|-------|
| 1 | GET  /api/operations/transportation/readiness                        | useTransportationReadiness            | ✅    | ✅       | ✅ | ✅ | ✅     | ✅   | ✅ | ❌   | A     | Cross-portal helper (Track 16.16). Foundation of Mission Control. Errors silenced at the api.js helper layer (operations namespace branch). |
| 2 | GET  /api/admin/transportation/audit-timeline                         | MissionControl::useRecentActivity, AuditTimeline | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | C | admin-strict. txGet absorbs 401. UI renders TxOpsRestrictedData. |
| 3 | GET  /api/admin/transportation/intelligence/cleanup-signals           | TopCleanupOpportunityCard, CleanupCompanion | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | C | |
| 4 | GET  /api/admin/transportation/intelligence/cleanup-signals/{key}     | CleanupCompanion::openDetail          | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | C | |
| 5 | POST /api/admin/transportation/intelligence/cleanup-signals/{key}/materialize-actions | CleanupCompanion::materialize | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | C | Admin-only write. Restricted users never see the button (page is restricted). |
| 6 | GET  /api/admin/transportation/intelligence/dashboard                 | ExecutiveDashboard                    | ✅    | ❌       | ❌ | ❌ | ❌     | ❌   | ❌ | ❌   | C     | |
| 7 | GET  /api/admin/transportation/intelligence/recommendations           | RecommendationsPanel                  | ✅    | ❌       | ❌ | ❌ | ❌     | ❌   | ❌ | ❌   | C     | |
| 8 | GET  /api/admin/transportation/intelligence/predictions               | PredictionsPanel                      | ✅    | ❌       | ❌ | ❌ | ❌     | ❌   | ❌ | ❌   | C     | |
| 9 | GET  /api/admin/transportation/intelligence/dispatch-learning         | LearningLoopPanel                     | ✅    | ❌       | ❌ | ❌ | ❌     | ❌   | ❌ | ❌   | C     | |
| 10| GET  /api/admin/transportation/dashboard                              | ComplianceDashboard                   | ✅    | ❌       | ❌ | ❌ | ❌     | ❌   | ❌ | ❌   | C     | |
| 11| GET  /api/admin/transportation/documents/queue                        | DocumentCenter                        | ✅    | ❌       | ❌ | ❌ | ❌     | ❌   | ❌ | ❌   | C     | |
| 12| PATCH /api/admin/transportation/documents/{id}/review                 | DocRow::review                        | ✅    | ❌       | ❌ | ❌ | ❌     | ❌   | ❌ | ❌   | C     | |
| 13| PATCH /api/admin/transportation/driver-documents/{id}/review          | DocRow::review                        | ✅    | ❌       | ❌ | ❌ | ❌     | ❌   | ❌ | ❌   | C     | |
| 14| GET  /api/admin/transportation/inspections/queue                      | InspectionCenter                      | ✅    | ❌       | ❌ | ❌ | ❌     | ❌   | ❌ | ❌   | C     | |
| 15| GET  /api/admin/transportation/rate-schedules                         | RateScheduleCenter                    | ✅    | ❌       | ❌ | ❌ | ❌     | ❌   | ❌ | ❌   | C     | |
| 16| POST /api/admin/transportation/rate-schedules                         | RateCreateDialog                      | ✅    | ❌       | ❌ | ❌ | ❌     | ❌   | ❌ | ❌   | C     | Admin write. |
| 17| GET  /api/admin/transportation/carriers                               | CarriersList                          | ✅    | ❌       | ❌ | ❌ | ❌     | ❌   | ❌ | ❌   | C     | UI renders TxOpsRestrictedData for non-admin. |
| 18| GET  /api/admin/transportation/carriers/{id}/workspace                | CarrierWorkspace                      | ✅    | ❌       | ❌ | ❌ | ❌     | ❌   | ❌ | ❌   | C     | |
| 19| GET  /api/admin/transportation/persons                                | DriversList                           | ✅    | ❌       | ❌ | ❌ | ❌     | ❌   | ❌ | ❌   | C     | |
| 20| GET  /api/admin/transportation/persons/{id}/workspace                 | DriverWorkspace                       | ✅    | ❌       | ❌ | ❌ | ❌     | ❌   | ❌ | ❌   | C     | |
| 21| GET  /api/admin/transportation/trucks                                 | TrucksList + InspectionCenter         | ✅    | ❌       | ❌ | ❌ | ❌     | ❌   | ❌ | ❌   | C     | |
| 22| GET  /api/admin/transportation/trucks/{id}/workspace                  | TruckWorkspace                        | ✅    | ❌       | ❌ | ❌ | ❌     | ❌   | ❌ | ❌   | C     | |
| 23| GET  /api/admin/transportation/orientation/dashboard                  | OrientationDashboard                  | ✅    | ❌       | ❌ | ❌ | ❌     | ❌   | ❌ | ❌   | C     | |
| 24| GET  /api/admin/transportation/orientation/modules                    | ModuleManager, ModuleDetail           | ✅    | ❌       | ❌ | ❌ | ❌     | ❌   | ❌ | ❌   | C     | |
| 25| GET  /api/admin/transportation/orientation/modules/{id}/questions     | ModuleDetail                          | ✅    | ❌       | ❌ | ❌ | ❌     | ❌   | ❌ | ❌   | C     | |
| 26| GET  /api/admin/transportation/orientation/assignments                | AssignmentsView                       | ✅    | ❌       | ❌ | ❌ | ❌     | ❌   | ❌ | ❌   | C     | |
| 27| GET  /api/admin/transportation/orientation/certificates               | CertificatesView                      | ✅    | ❌       | ❌ | ❌ | ❌     | ❌   | ❌ | ❌   | C     | |
| 28| GET  /api/admin/transportation/email-routes                           | EmailRoutesPanel                      | ✅    | ❌       | ❌ | ❌ | ❌     | ❌   | ❌ | ❌   | C     | |
| 29| GET  /api/admin/transportation/automation/actions                     | MorningQueue                          | ✅    | ❌       | ❌ | ❌ | ❌     | ❌   | ❌ | ❌   | C     | |
| 30| GET  /api/admin/transportation/automation/health                      | AutomationHealthCore                  | ✅    | ❌       | ❌ | ❌ | ❌     | ❌   | ❌ | ❌   | C     | |
| 31| GET  /api/admin/transportation/automation/forecast                    | ComplianceForecast                    | ✅    | ❌       | ❌ | ❌ | ❌     | ❌   | ❌ | ❌   | C     | |
| 32| GET  /api/admin/transportation/automation/digest/preview              | DigestCard                            | ✅    | ❌       | ❌ | ❌ | ❌     | ❌   | ❌ | ❌   | C     | |
| 33| GET  /api/admin/transportation/automation/digest/runs                 | DigestCard                            | ✅    | ❌       | ❌ | ❌ | ❌     | ❌   | ❌ | ❌   | C     | |
| 34| POST /api/admin/transportation/automation/digest/dry-run|send-now     | DigestCard                            | ✅    | ❌       | ❌ | ❌ | ❌     | ❌   | ❌ | ❌   | C     | |
| 35| GET  /api/admin/transportation/hr-sync                                | HrSyncHealthCard, HrHealthWidget      | ✅    | ❌       | ❌ | ❌ | ❌     | ❌   | ❌ | ❌   | C     | |
| 36| GET  /api/admin/transportation/hr-sync/report                         | HrSyncHealthCard::runScan             | ✅    | ❌       | ❌ | ❌ | ❌     | ❌   | ❌ | ❌   | C     | |
| 37| GET  /api/admin/transportation/related/{type}/{id}                    | TxOpsRightRail                        | ✅    | ❌       | ❌ | ❌ | ❌     | ❌   | ❌ | ❌   | B/C   | Right rail surfaces "Unable to load relationships" inline (calm hint). |
| 38| GET  /api/admin/transportation/timeline/{type}/{id}                   | ComplianceTimeline widget             | ✅    | ❌       | ❌ | ❌ | ❌     | ❌   | ❌ | ❌   | C     | |
| 39| GET  /api/admin/transportation/intelligence/drivers/{id}              | _lists::DriverWorkspace               | ✅    | ❌       | ❌ | ❌ | ❌     | ❌   | ❌ | ❌   | C     | |
| 40| GET  /api/admin/transportation/search/* (relationships, suggest)      | TransportationSearch                  | ✅    | ❌       | ❌ | ❌ | ❌     | ❌   | ❌ | ❌   | C     | |

Operational reading of the matrix
─────────────────────────────────
- Mission Control's *foundational* readiness call (#1) is the only
  endpoint that returns true cross-portal-safe data — every other
  inline data feed is admin-strict by design.
- Dispatchers ARE expected to do executional work in the dedicated
  Dispatch Portal (`/dispatch-portal/*`), not inside the admin
  transportation governance surfaces. The Mission Control hub gives
  them situational awareness via the cross-portal readiness endpoint;
  every governance workspace below shows a clean restricted state.
- No endpoint was relaxed under Track 18.12B. The fix is **frontend
  only** — UI must never present admin-only data with a 401 traceback,
  but the data boundary is unchanged.
