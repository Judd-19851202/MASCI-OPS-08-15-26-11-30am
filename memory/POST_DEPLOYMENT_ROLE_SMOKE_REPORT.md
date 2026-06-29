POST-DEPLOYMENT ROLE SMOKE REPORT
==================================

RELEASE       : MASCI Operations Platform · Track 18 Production Cut
RELEASE SHA   : d5a8a4848ecbb3bf5e3eca1477fdee5929b7a84c
VERIFY DATE   : 2026-06-29 (UTC)
ENVIRONMENT   : verified preview build (same artefact that ships to prod)
PROD URL      : __________________ (operator-only)

Status legend:
  ✅  preview verified (same code path · same artefact)
  🔒  operator-only — must be re-run on live production URL
  ⚠   watch / minor non-blocker
  ❌  blocker

────────────────────────────────────────────────────────────────────────────
SUPER ADMIN — `jaymn.judd@mascigc.com`
────────────────────────────────────────────────────────────────────────────
| Check                                                    | Preview | Prod |
|----------------------------------------------------------|---------|------|
| /api/auth/multi-login → 200                              | ✅       | 🔒   |
| portal_tokens.admin issued                               | ✅       | 🔒   |
| Administration nav GROUP visible                         | ✅       | 🔒   |
| /admin/transportation Mission Control strip renders      | ✅       | 🔒   |
| Mission Control · Drivers · Carriers · Trucks            | ✅       | 🔒   |
| Orientation Dashboard · Modules · Assignments · Certs    | ✅       | 🔒   |
| Compliance loads                                         | ✅       | 🔒   |
| Intelligence loads (or documented cold-start)            | ✅ cold-start documented as non-blocker | 🔒 |
| Automation / Command Queue loads                         | ✅       | 🔒   |
| Audit Timeline loads                                     | ✅       | 🔒   |
| PM · HR · Safety · Shop · Field Leadership accessible    | ✅       | 🔒   |
| Guidance Center accessible                               | ✅       | 🔒   |
| No red overlays                                          | ✅       | 🔒   |
| No raw HTTP errors                                       | ✅       | 🔒   |

────────────────────────────────────────────────────────────────────────────
DISPATCH / TRANSPORTATION — `dispatch@mascigc.com` (or cert.dispatch@example.com)
────────────────────────────────────────────────────────────────────────────
HIGHEST PRIORITY ROLE (Track 18.12B + 18.12C "Visible = Usable" doctrine).

| Check                                                    | Preview | Prod |
|----------------------------------------------------------|---------|------|
| /api/dispatch/login → 200                                | ✅       | ❌ on prod — 401 in live smoke (missing seed); see ISSUES doc |
| dispatch token issued                                    | ✅       | 🔒   |
| /dispatch-portal (Dispatch Board / Map / Haul Ledger)    | ✅       | 🔒   |
| /transportation-operations (Mission Control)             | ✅       | 🔒   |
| /transportation-operations/drivers — real rows           | ✅ 171 rows | 🔒 |
| /transportation-operations/carriers — real rows          | ✅ 200 rows | 🔒 |
| /transportation-operations/trucks — real rows            | ✅ 12 rows  | 🔒 |
| Orientation Dashboard / Modules / Assignments / Certs    | ✅       | 🔒   |
| Automation / Morning Queue                               | ✅       | 🔒   |
| 30-day Forecast                                          | ✅       | 🔒   |
| Cleanup                                                  | ✅       | 🔒   |
| Search                                                   | ✅       | 🔒   |
| Right Rail / Related Records                             | ✅       | 🔒   |
| Refresh buttons                                          | ✅       | 🔒   |

Visible = Usable (per Track 18.12C):
| Sidebar item                                             | State    | Expected | Pass |
|----------------------------------------------------------|----------|----------|------|
| txops-nav-group-administration                           | hidden   | hidden   | ✅   |
| txops-nav-intelligence                                   | hidden   | hidden   | ✅   |
| txops-nav-reports                                        | hidden   | hidden   | ✅   |
| txops-nav-drivers                                        | visible  | visible  | ✅   |
| txops-nav-carriers                                       | visible  | visible  | ✅   |
| txops-nav-trucks                                         | visible  | visible  | ✅   |
| txops-nav-cleanup                                        | visible  | visible  | ✅   |
| Restricted banner on core operational workspaces         | absent   | absent   | ✅   |
| "Admin login required" copy                              | absent   | absent   | ✅   |
| Raw 401/403                                              | absent   | absent   | ✅   |
| Red React runtime overlay                                | absent   | absent   | ✅   |
| Bounce to /admin/transportation/*                        | absent   | absent   | ✅   |
| "Admin Console" denial inside TxOps                      | absent   | absent   | ✅   |

────────────────────────────────────────────────────────────────────────────
PROJECT MANAGEMENT — Project Workspace canonical
────────────────────────────────────────────────────────────────────────────
| Check                                                    | Preview | Prod |
|----------------------------------------------------------|---------|------|
| /pm login                                                | ✅       | 🔒   |
| Dashboard loads                                          | ✅       | 🔒   |
| Project list / load                                      | ✅       | 🔒   |
| Project detail                                           | ✅       | 🔒   |
| PM Command Center (where applicable)                     | ✅       | 🔒   |
| PO Requests                                              | ✅       | 🔒   |
| Daily project workflows render                           | ✅       | 🔒   |
| No "PM Portal" naming drift (user-facing)                | ✅       | 🔒   |
| Console errors                                           | 0       | 🔒   |

────────────────────────────────────────────────────────────────────────────
HUMAN RESOURCES — HR Workspace canonical
────────────────────────────────────────────────────────────────────────────
| Check                                                    | Preview | Prod |
|----------------------------------------------------------|---------|------|
| /hr login                                                | ✅       | 🔒   |
| Dashboard loads                                          | ✅       | 🔒   |
| Employee list                                            | ✅       | 🔒   |
| Employee detail                                          | ✅       | 🔒   |
| Driver-qualification sync visible (if exposed to HR)     | ✅       | 🔒   |
| Onboarding / training                                    | ✅       | 🔒   |
| No "HR Portal" naming drift (user-facing copy)           | ✅       | 🔒   |
| Canonical restricted copy where blocked                  | ✅       | 🔒   |
| Console errors                                           | 0       | 🔒   |

────────────────────────────────────────────────────────────────────────────
SAFETY OPERATIONS — Safety Workspace canonical
────────────────────────────────────────────────────────────────────────────
| Check                                                    | Preview | Prod |
|----------------------------------------------------------|---------|------|
| /safety-portal login                                     | ✅       | 🔒   |
| Dashboard loads                                          | ✅       | 🔒   |
| Audits · forms · records                                 | ✅       | 🔒   |
| Safety Meetings                                          | ✅       | 🔒   |
| JHP (if applicable)                                      | ✅       | 🔒   |
| Public safety submission routes                          | ✅       | 🔒   |
| No "Safety Portal" naming drift (user-facing copy)       | ✅       | 🔒   |
| Console errors                                           | 0       | 🔒   |

────────────────────────────────────────────────────────────────────────────
SHOP OPERATIONS — Shop Workspace canonical
────────────────────────────────────────────────────────────────────────────
| Check                                                    | Preview | Prod |
|----------------------------------------------------------|---------|------|
| /shop login                                              | ✅       | 🔒   |
| Dashboard loads                                          | ✅       | 🔒   |
| Equipment / fleet                                        | ✅       | 🔒   |
| Maintenance / inspection                                 | ✅       | 🔒   |
| Work orders (if applicable)                              | ✅       | 🔒   |
| No "Shop Portal" naming drift (user-facing copy)         | ✅       | 🔒   |
| Console errors                                           | 0       | 🔒   |

────────────────────────────────────────────────────────────────────────────
FIELD LEADERSHIP / PUBLIC FIELD FLOWS
────────────────────────────────────────────────────────────────────────────
| Check                                                    | Preview | Prod |
|----------------------------------------------------------|---------|------|
| /leadership route                                        | ✅       | 🔒   |
| FL records / forms                                       | ✅       | 🔒   |
| Public daily report flow                                 | ✅       | 🔒   |
| Public JHP / safety form                                 | ✅       | 🔒   |
| Photos / upload                                          | ✅       | 🔒   |
| Next daily-report-number endpoint                        | ✅       | 🔒   |
| Jobs list endpoint                                       | ✅       | 🔒   |
| FL roster endpoint                                       | ✅       | 🔒   |
| No "Crew Hub" user-facing drift                          | ✅       | 🔒   |

────────────────────────────────────────────────────────────────────────────
DRIVER MAGIC-LINK / DRIVER-FACING ROUTES
────────────────────────────────────────────────────────────────────────────
| Check                                                    | Preview | Prod |
|----------------------------------------------------------|---------|------|
| Magic-link route loads                                   | ✅       | 🔒   |
| Driver acknowledgement path                              | ✅       | 🔒   |
| Driver shift route                                       | ✅       | 🔒   |
| No Transportation TopBar bleed into minimal driver route | ✅       | 🔒   |
| No admin chrome                                          | ✅       | 🔒   |
| Token errors are user-friendly                           | ✅       | 🔒   |

────────────────────────────────────────────────────────────────────────────
GUIDANCE CENTER
────────────────────────────────────────────────────────────────────────────
| Check                                                    | Preview | Prod |
|----------------------------------------------------------|---------|------|
| Operational Guidance Center loads                        | ✅       | 🔒   |
| Canonical workspace names                                | ✅       | 🔒   |
| Transportation guidance present                          | ✅       | 🔒   |
| No "Hub" / "Portal" drift                                | ✅       | 🔒   |
| CTA hierarchy clean                                      | ✅       | 🔒   |
| Search / filter                                          | ✅       | 🔒   |
| Console errors                                           | 0       | 🔒   |

────────────────────────────────────────────────────────────────────────────
GLOBAL VERDICT
────────────────────────────────────────────────────────────────────────────
Preview-verified: ALL ROLES PASS.
Production-side verification of the per-role flows is operator-only.
Only ONE non-trivial item carries over to production: the missing
`dispatch@mascigc.com` seed (P1, operator-blocking, documented in
POST_DEPLOYMENT_ISSUES_AND_FIXES.md).
