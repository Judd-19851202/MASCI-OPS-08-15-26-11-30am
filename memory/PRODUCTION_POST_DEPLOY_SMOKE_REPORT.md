PRODUCTION POST-DEPLOY SMOKE REPORT
====================================

DATE     : 2026-02-15
ENV      : Verified preview build (same code path that ships to production)
PROD URL : __________________ (operator fills after deploy)
SHA      : d5a8a4848ecbb3bf5e3eca1477fdee5929b7a84c

This smoke was executed against the verified preview build. The
production smoke must repeat these steps against the new production
URL after Step 6 of the deployment execution log.

────────────────────────────────────────────────────────────────────────────
PUBLIC / UNAUTHENTICATED
────────────────────────────────────────────────────────────────────────────
| Check                                                  | Status |
|--------------------------------------------------------|--------|
| Public home `/` loads                                  | ✅     |
| "MASCI Hub" string absent                              | ✅     |
| "Office Portals" string absent                         | ✅     |
| Sign-in entry reachable                                | ✅     |
| Canonical naming on hero (when not logged in)          | ✅     |

────────────────────────────────────────────────────────────────────────────
SUPER ADMIN (jaymn.judd@mascigc.com)
────────────────────────────────────────────────────────────────────────────
| Check                                                  | Status |
|--------------------------------------------------------|--------|
| /api/auth/multi-login → 200                            | ✅     |
| portal_tokens.admin issued                             | ✅     |
| /admin/transportation Mission Control strip renders    | ✅     |
| Administration nav GROUP visible                       | ✅     |
| No "Admin login required" text                         | ✅     |
| No React red runtime overlay                            | ✅     |

────────────────────────────────────────────────────────────────────────────
DISPATCH (dispatch@mascigc.com)
────────────────────────────────────────────────────────────────────────────
| Check                                                  | Result               |
|--------------------------------------------------------|----------------------|
| /api/dispatch/login → 200                              | ✅                   |
| dispatch token issued                                  | ✅                   |
| /transportation-operations/drivers tbody rows          | 171 (≥100) ✅         |
| tx-drivers-list-restricted testid absent               | ✅                   |
| /transportation-operations/carriers tbody rows         | 200 (≥100) ✅         |
| tx-carriers-list-restricted testid absent              | ✅                   |
| /transportation-operations/trucks tbody rows           | 12 (≥1) ✅            |
| tx-trucks-list-restricted testid absent                | ✅                   |
| No "Admin login required" on any of the above          | ✅                   |
| Mission Control real KPIs (fleet, drivers, carriers,   | ✅ (live screenshot)  |
|   dispatch, action items, risks, top opportunity)      |                       |

DISPATCH NAV VISIBILITY (VISIBLE = USABLE)
| Item                                                   | State    | Expected |
|--------------------------------------------------------|----------|----------|
| txops-nav-group-administration                         | hidden   | hidden ✅ |
| txops-nav-intelligence                                 | hidden   | hidden ✅ |
| txops-nav-reports                                      | hidden   | hidden ✅ |
| txops-nav-drivers                                      | visible  | visible ✅|
| txops-nav-carriers                                     | visible  | visible ✅|
| txops-nav-cleanup                                      | visible  | visible ✅|

────────────────────────────────────────────────────────────────────────────
GLOBAL OVERLAY / ERROR SCAN
────────────────────────────────────────────────────────────────────────────
| Check                                                  | Count    |
|--------------------------------------------------------|----------|
| React runtime overlay (div containing "runtime error") | 0        |
| "Admin Console" denial text inside TxOps               | 0        |
| Raw "Request failed with status code 401/403"          | 0        |
| Raw "Forbidden" / "Unauthorized" copy                  | 0        |

────────────────────────────────────────────────────────────────────────────
OTHER ROLES (verified in prior release-candidate smoke run at
/app/test_reports/iteration_track_18_production_cut_release_smoke.json)
────────────────────────────────────────────────────────────────────────────
| Role / Path                                            | Status |
|--------------------------------------------------------|--------|
| /pm (Project Management Center)                        | ✅ canonical naming |
| /hr                                                    | ✅ no overlay (denial copy now canonical) |
| /safety                                                | ✅ canonical naming |
| /shop                                                  | ✅ canonical naming |
| /leadership (Field Leadership)                          | ✅ canonical naming |
| /guidance (Operational Guidance Center)                 | ✅ canonical naming |
| /dispatch-portal                                       | ✅ board renders |
| /transport-verify/<token> (driver magic-link)           | ✅ no TopBar bleed |

────────────────────────────────────────────────────────────────────────────
DEPLOYMENT BLOCKER SCAN
────────────────────────────────────────────────────────────────────────────
✅ CLEAN — zero blockers detected on the verified build.

────────────────────────────────────────────────────────────────────────────
PRODUCTION POST-DEPLOY REPETITION (operator action)
────────────────────────────────────────────────────────────────────────────
After the operator flips the 4 env vars + triggers the production
deploy, repeat the above checks against the new production URL. The
smoke is GREEN only when every row above remains ✅ on production.
Populate the PROD URL header at the top of this file and append the
production timestamp.

────────────────────────────────────────────────────────────────────────────
OVERALL SMOKE VERDICT
────────────────────────────────────────────────────────────────────────────
✅ GO — every smoke check on the verified build is GREEN. Production
will inherit the same code path; assuming the env var flip is
performed correctly (Step 3 of the execution log), the production
smoke must reproduce these exact results.
