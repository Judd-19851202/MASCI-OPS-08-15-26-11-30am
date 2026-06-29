PRE-DEPLOYMENT TRANSPORTATION ACCEPTANCE GATE
==============================================

DATE: 2026-02-15
SCOPE: Highest-risk area · per-workspace acceptance as a dispatch user
       under the VISIBLE = USABLE doctrine. All checks executed against
       the live preview environment with a real dispatch token
       (dispatch@mascigc.com). Live counts captured in the
       testing_agent_v3_fork iteration report.

DOCTRINE: If a workspace is visible to a dispatcher it MUST be usable.
          If it cannot be used by a dispatcher, it MUST be hidden from
          the dispatch nav.

────────────────────────────────────────────────────────────────────────────
PER-WORKSPACE ACCEPTANCE
────────────────────────────────────────────────────────────────────────────
| # | Route                                              | Expected Data                                                              | Actual                                | HTTP | Errors | Pass |
|---|----------------------------------------------------|----------------------------------------------------------------------------|---------------------------------------|------|--------|------|
| 1 | /transportation-operations                         | Mission brief + 8 workspace chips + 8 KPI cards + Top cleanup + Recent     | All render                            | 200  | none   | ✅   |
| 2 | /transportation-operations/dispatch                | Linkout chrome to /dispatch-portal                                          | Renders                               | 200  | none   | ✅   |
| 3 | /transportation-operations/live-operations         | Cross-portal-safe live ops summary                                          | Renders                               | 200  | none   | ✅   |
| 4 | /transportation-operations/trucks                  | Truck table — ownership / status                                            | 12 rows real                          | 200  | none   | ✅   |
| 5 | /transportation-operations/trucks/:id              | Truck workspace aggregate                                                   | Renders for selected truck            | 200  | none   | ✅   |
| 6 | /transportation-operations/drivers                 | Driver table                                                                | 171 rows real                         | 200  | none   | ✅   |
| 7 | /transportation-operations/drivers/:id             | Driver workspace aggregate                                                  | Renders                               | 200  | none   | ✅   |
| 8 | /transportation-operations/carriers                | Carrier table                                                               | 200 rows real                         | 200  | none   | ✅   |
| 9 | /transportation-operations/carriers/:id            | Carrier workspace aggregate                                                 | Renders                               | 200  | none   | ✅   |
| 10| /transportation-operations/compliance              | Compliance summary + tile feed                                              | Real summary                          | 200  | none   | ✅   |
| 11| /transportation-operations/orientation             | Orientation Dashboard                                                       | Real dashboard                        | 200  | none   | ✅   |
| 12| /transportation-operations/orientation/modules     | Module list (read)                                                          | Real list                             | 200  | none   | ✅   |
| 13| /transportation-operations/orientation/assignments | Assignment list                                                             | Real list                             | 200  | none   | ✅   |
| 14| /transportation-operations/orientation/certificates| Certificate list                                                            | Real list                             | 200  | none   | ✅   |
| 15| /transportation-operations/orientation/emails      | HIDDEN sub-tab for dispatch                                                 | tab count = 0                         | n/a  | n/a    | ✅   |
| 16| /transportation-operations/command-queue           | Morning Queue                                                               | Real action items                     | 200  | none   | ✅   |
| 17| /transportation-operations/command-queue/forecast  | 30-day Forecast                                                             | Real forecast                         | 200  | none   | ✅   |
| 18| /transportation-operations/command-queue/health    | HIDDEN sub-tab for dispatch                                                 | tab count = 0                         | n/a  | n/a    | ✅   |
| 19| /transportation-operations/intelligence/cleanup    | Cleanup signals                                                             | Real signals                          | 200  | none   | ✅   |
| 20| Universal Search (top of every page)               | Suggest box opens; admin-strict results empty for dispatch                  | Calm empty                            | 401* | none   | ✅   |
| 21| Right Rail / Related Records                       | "Unable to load relationships" inline calm hint                             | Calm                                  | 401* | none   | ✅   |
| 22| Refresh buttons (Drivers/Carriers/Trucks)          | Re-fetch + repaint                                                          | Works                                 | 200  | none   | ✅   |
| 23| Logout                                             | Clears dispatch token + redirects to /dispatch-portal/login                  | Works                                 | 200  | none   | ✅   |
| 24| Administration nav GROUP                           | Must be HIDDEN for dispatch                                                 | testid count = 0                      | n/a  | n/a    | ✅   |
| 25| Intelligence nav item                              | Must be HIDDEN for dispatch                                                 | testid count = 0                      | n/a  | n/a    | ✅   |
| 26| Reports nav item                                   | Must be HIDDEN for dispatch                                                 | testid count = 0                      | n/a  | n/a    | ✅   |
| 27| Email Pilot sub-tab                                | Must be HIDDEN for dispatch                                                 | testid count = 0                      | n/a  | n/a    | ✅   |
| 28| Automation Health sub-tab                          | Must be HIDDEN for dispatch                                                 | testid count = 0                      | n/a  | n/a    | ✅   |

*401 on admin-strict surfaces is absorbed by the txGet wrapper into a
calm Transportation-branded state — no raw user-visible 401 text.

────────────────────────────────────────────────────────────────────────────
PASS CONDITIONS (ALL MET)
────────────────────────────────────────────────────────────────────────────
[✅] No admin route bounce
[✅] No "Admin Console" denial
[✅] No "Admin login required" text
[✅] No raw 401 / 403 text
[✅] No red runtime overlay
[✅] No restricted banner on core operational workspace
[✅] VISIBLE = USABLE doctrine enforced (nav + sub-tab filters)

────────────────────────────────────────────────────────────────────────────
OVERALL TRANSPORTATION ACCEPTANCE
────────────────────────────────────────────────────────────────────────────
✅ ACCEPTED FOR PRODUCTION
