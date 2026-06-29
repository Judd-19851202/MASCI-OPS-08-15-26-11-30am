POST-DEPLOYMENT TRANSPORTATION ACCEPTANCE
==========================================

RELEASE     : MASCI Operations Platform · Track 18 Production Cut
RELEASE SHA : d5a8a4848ecbb3bf5e3eca1477fdee5929b7a84c
DATE        : 2026-06-29 (UTC)
ROLE TESTED : Dispatch / Transportation Operations (highest priority)
ENV         : preview build (same artefact as production)
PROD URL    : __________________ (operator must re-run with prod creds)

────────────────────────────────────────────────────────────────────────────
ACCEPTANCE DOCTRINE
────────────────────────────────────────────────────────────────────────────
Track 18.12B + 18.12C established the binding doctrine:

  "Visible = Usable."

If a dispatcher sees a Transportation Operations workspace, that
workspace MUST load real role-safe data and accept role-safe writes.
Restricted banners on visible operational workspaces are a deployment
blocker. Items dispatchers cannot use are hidden from the sidebar,
not greyed-out behind a denial banner.

────────────────────────────────────────────────────────────────────────────
1 · WORKSPACE LANDING (Dispatch token)
────────────────────────────────────────────────────────────────────────────
| Route                                            | Status                                 |
|--------------------------------------------------|----------------------------------------|
| /dispatch-portal                                 | ✅ Dispatch Board renders               |
| /dispatch-portal/map                             | ✅ Map view renders                     |
| /dispatch-portal/haul-ledger                     | ✅ Ledger renders                       |
| /dispatch-portal/qualification                   | ✅ Driver Qualification renders         |
| /dispatch-portal/fleet                           | ✅ Dispatch Fleet renders               |
| /transportation-operations                        | ✅ Mission Control renders              |
| /transportation-operations/drivers               | ✅ 171 tbody rows                       |
| /transportation-operations/carriers              | ✅ 200 tbody rows                       |
| /transportation-operations/trucks                | ✅ 12 tbody rows                        |
| /transportation-operations/compliance            | ✅                                      |
| /transportation-operations/orientation           | ✅                                      |
| /transportation-operations/orientation/modules   | ✅                                      |
| /transportation-operations/orientation/assignments | ✅                                    |
| /transportation-operations/orientation/certificates | ✅                                   |
| /transportation-operations/automation            | ✅ Morning Queue                         |
| /transportation-operations/forecast              | ✅ 30-day Forecast                       |
| /transportation-operations/cleanup               | ✅                                      |
| /transportation-operations/search                | ✅                                      |

────────────────────────────────────────────────────────────────────────────
2 · WORKSPACE ACTIONS STRIP
────────────────────────────────────────────────────────────────────────────
Mission Control · Workspace Actions strip renders the role-safe CTA
set for dispatchers (no admin-only actions exposed). Real KPIs:
  · fleet
  · drivers
  · carriers
  · dispatch
  · action items
  · risks
  · top opportunity

All KPIs render real values from the preview Atlas data set.

────────────────────────────────────────────────────────────────────────────
3 · "VISIBLE = USABLE" SIDEBAR AUDIT (canonical lock from Track 18.12C)
────────────────────────────────────────────────────────────────────────────
| Sidebar item                                     | State on dispatch | Expected | Verdict |
|--------------------------------------------------|-------------------|----------|---------|
| txops-nav-mission-control                        | visible           | visible  | ✅       |
| txops-nav-drivers                                | visible           | visible  | ✅       |
| txops-nav-carriers                               | visible           | visible  | ✅       |
| txops-nav-trucks                                 | visible           | visible  | ✅       |
| txops-nav-compliance                             | visible           | visible  | ✅       |
| txops-nav-orientation                            | visible           | visible  | ✅       |
| txops-nav-automation                             | visible           | visible  | ✅       |
| txops-nav-forecast                               | visible           | visible  | ✅       |
| txops-nav-cleanup                                | visible           | visible  | ✅       |
| txops-nav-search                                 | visible           | visible  | ✅       |
| txops-nav-intelligence                           | hidden            | hidden   | ✅       |
| txops-nav-reports                                | hidden            | hidden   | ✅       |
| txops-nav-group-administration                   | hidden            | hidden   | ✅       |
| txops-nav-email-pilot                            | hidden            | hidden   | ✅       |
| txops-nav-automation-health                      | hidden            | hidden   | ✅       |

────────────────────────────────────────────────────────────────────────────
4 · RESTRICTED-STATE / RAW-ERROR SCAN
────────────────────────────────────────────────────────────────────────────
| Check                                            | Count    |
|--------------------------------------------------|----------|
| `tx-drivers-list-restricted` testid present      | 0        |
| `tx-carriers-list-restricted` testid present     | 0        |
| `tx-trucks-list-restricted` testid present       | 0        |
| "Admin login required" copy inside TxOps         | 0        |
| "Admin Console" denial inside TxOps              | 0        |
| Raw "401" / "403" inside visible TxOps pages     | 0        |
| Raw "Forbidden" / "Unauthorized" copy            | 0        |
| Bounce to /admin/transportation/*                | 0        |
| React red runtime overlay                        | 0        |
| Broken layout                                    | 0        |

────────────────────────────────────────────────────────────────────────────
5 · ROW COUNTS — VERIFIED REAL DATA
────────────────────────────────────────────────────────────────────────────
| Surface                          | Row Count | Pass Threshold | Pass |
|----------------------------------|-----------|----------------|------|
| Drivers list                     | 171       | ≥ 100          | ✅    |
| Carriers list                    | 200       | ≥ 100          | ✅    |
| Trucks list                      | 12        | ≥ 1            | ✅    |
| Orientation Modules              | populated | ≥ 1            | ✅    |
| Orientation Assignments          | populated | ≥ 1            | ✅    |
| Orientation Certificates         | populated | ≥ 1            | ✅    |
| Cleanup action signals           | populated | ≥ 0            | ✅    |

NOTE: Production-DB row counts may differ. Dispatch-side acceptance on
production requires the operator to log in as `dispatch@mascigc.com`
(or the seeded equivalent) and re-check the same testids and row counts
against the live URL.

────────────────────────────────────────────────────────────────────────────
6 · BACKEND ROUTE GUARD VERIFICATION (Track 18.12C)
────────────────────────────────────────────────────────────────────────────
The `_local_dispatch_or_admin` and `require_dispatch_or_admin`
FastAPI dependency injectors confirm:
  · `/api/admin/transportation/drivers`        accepts dispatch token  ✅
  · `/api/admin/transportation/carriers`       accepts dispatch token  ✅
  · `/api/admin/transportation/trucks`         accepts dispatch token  ✅
  · `/api/admin/transportation/orientation/*`  accepts dispatch token  ✅
  · `/api/admin/transportation/cleanup`        accepts dispatch token  ✅
  · `/api/admin/transportation/forecast`       accepts dispatch token  ✅

`/api/admin/transportation/intelligence` and reports endpoints
correctly reject dispatch tokens with canonical restricted copy
(not raw 401/403). These endpoints are also sidebar-hidden, per
the Visible = Usable doctrine.

────────────────────────────────────────────────────────────────────────────
7 · ACCEPTANCE VERDICT
────────────────────────────────────────────────────────────────────────────
TRANSPORTATION OPERATIONS · DISPATCH ROLE — ACCEPTED on preview build
(which is the artefact shipped to production via the Emergent deploy).

Production-side acceptance is gated on:
  (a) the operator seeding/sharing the `dispatch@mascigc.com` prod
      credentials so the live-URL smoke can be re-run, AND
  (b) the operator re-running the row-count and testid scans above
      against the live production URL.

No regressions versus Track 18.12C acceptance run.
No "Visible = Usable" violations.
No raw 401/403 leakage.
No banned-name drift inside the Transportation Operations shell.
