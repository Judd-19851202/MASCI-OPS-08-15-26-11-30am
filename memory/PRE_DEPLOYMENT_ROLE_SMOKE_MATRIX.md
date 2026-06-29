PRE-DEPLOYMENT ROLE SMOKE MATRIX
================================

DATE: 2026-02-15
SCOPE: Per-role functional smoke checklist for the Track 18 release.
       Each row is a discrete test the operator (or testing agent) must
       confirm green BEFORE flipping the release. Status legend:
       PASS / WARN / FAIL.

────────────────────────────────────────────────────────────────────────────
PUBLIC / UNAUTHENTICATED
────────────────────────────────────────────────────────────────────────────
| # | Check                                                          | Expected                                                        | Status |
|---|----------------------------------------------------------------|-----------------------------------------------------------------|--------|
| 1 | Public home loads                                              | 200 OK, MASCI Operations Platform branding                       | PASS   |
| 2 | Platform name in hero                                          | "MASCI Operations Platform" (NOT "MASCI Hub" / "Portal")        | PASS   |
| 3 | Sign-in entry visible                                          | `/sign-in` and `/admin/login` reachable                          | PASS   |
| 4 | Public guidance accessible                                     | Operational Guidance Center anonymous links work                 | PASS   |
| 5 | No legacy "Office Portals" copy                                | Banned strings absent from rendered DOM                          | PASS   |
| 6 | No preview-only data entry                                     | No "Try Demo" / "Sandbox" CTA on production hero                 | PASS   |
| 7 | Driver magic-link route (`/transport-verify/:token`)           | Loads without TopBar bleed; minimal driver chrome only            | PASS   |

────────────────────────────────────────────────────────────────────────────
SUPER ADMIN (`jaymn.judd@mascigc.com`)
────────────────────────────────────────────────────────────────────────────
| # | Check                                                          | Status |
|---|----------------------------------------------------------------|--------|
| 1 | `/admin/login` multi-login succeeds                            | PASS   |
| 2 | Admin home renders                                             | PASS   |
| 3 | `/admin/transportation` Mission Control loads real data         | PASS   |
| 4 | `/admin/transportation/drivers` renders ~159 drivers            | PASS   |
| 5 | `/admin/transportation/carriers` renders ~200 carriers          | PASS   |
| 6 | `/admin/transportation/trucks` renders trucks                   | PASS   |
| 7 | `/admin/transportation/orientation` Dashboard renders            | PASS   |
| 8 | `/admin/transportation/intelligence` deep analytics accessible | PASS (slow cold-start — non-blocker) |
| 9 | `/admin/transportation/command-queue` Health visible            | PASS   |
| 10| `/admin/transportation/audit` Audit Timeline renders            | PASS   |
| 11| `/transportation-operations` same Mission Control works         | PASS   |
| 12| Administration nav GROUP visible                                | PASS   |
| 13| All sub-tabs visible (Email Pilot, Automation Health)           | PASS   |
| 14| PM portal accessible                                            | PASS   |
| 15| HR portal accessible                                            | PASS   |
| 16| Safety portal accessible                                        | PASS   |
| 17| Shop portal accessible                                          | PASS   |
| 18| Field Leadership accessible                                     | PASS   |
| 19| Operational Guidance Center accessible                          | PASS   |
| 20| Access management panels (IAM) accessible                       | PASS   |
| 21| No "Admin Console" copy where banned (governance linter green) | PASS   |

────────────────────────────────────────────────────────────────────────────
DISPATCH / TRANSPORTATION (`dispatch@mascigc.com`)
────────────────────────────────────────────────────────────────────────────
| # | Check                                                          | Status |
|---|----------------------------------------------------------------|--------|
| 1 | `/dispatch-portal/login` succeeds                              | PASS   |
| 2 | `/dispatch-portal` board renders                               | PASS   |
| 3 | Dispatch map renders                                           | PASS   |
| 4 | Haul ledger renders                                            | PASS   |
| 5 | Driver qualification view renders                              | PASS   |
| 6 | Fleet view renders                                             | PASS   |
| 7 | `/transportation-operations` loads Mission Control (real data) | PASS   |
| 8 | `/transportation-operations/drivers` → 171 rows real           | PASS   |
| 9 | `/transportation-operations/carriers` → 200 rows real          | PASS   |
| 10| `/transportation-operations/trucks` → 12 rows real             | PASS   |
| 11| `/transportation-operations/compliance` real summary           | PASS   |
| 12| `/transportation-operations/orientation` 4 sub-tabs real       | PASS   |
| 13| `/transportation-operations/command-queue` Morning Queue real  | PASS   |
| 14| 30-day Forecast real                                            | PASS   |
| 15| Cleanup real signals                                            | PASS   |
| 16| Email Pilot sub-tab HIDDEN                                      | PASS   |
| 17| Automation Health sub-tab HIDDEN                                | PASS   |
| 18| Intelligence nav HIDDEN                                         | PASS   |
| 19| Reports nav HIDDEN                                              | PASS   |
| 20| Administration nav GROUP HIDDEN                                 | PASS   |
| 21| Zero "Admin login required" text                                | PASS   |
| 22| Zero "Request failed with status code 401/403" text             | PASS   |
| 23| Zero React red runtime overlays                                 | PASS   |
| 24| Zero restricted banner on core operational workspace            | PASS   |

────────────────────────────────────────────────────────────────────────────
PROJECT MANAGEMENT
────────────────────────────────────────────────────────────────────────────
| # | Check                                                          | Status |
|---|----------------------------------------------------------------|--------|
| 1 | Login as PM user succeeds                                      | PASS   |
| 2 | PM dashboard loads                                              | PASS   |
| 3 | PO request flow accessible                                      | PASS   |
| 4 | Project workflows render                                        | PASS   |
| 5 | Naming = "Project Management" (NOT "PM Portal")                 | PASS   |
| 6 | Case style follows Track 18.07                                  | PASS   |

────────────────────────────────────────────────────────────────────────────
HUMAN RESOURCES
────────────────────────────────────────────────────────────────────────────
| # | Check                                                          | Status |
|---|----------------------------------------------------------------|--------|
| 1 | HR login                                                       | PASS   |
| 2 | HR dashboard                                                    | PASS   |
| 3 | Employee records accessible                                    | PASS   |
| 4 | Training / onboarding paths render                              | PASS   |
| 5 | No "HR Portal" drift                                            | PASS   |

────────────────────────────────────────────────────────────────────────────
SAFETY OPERATIONS
────────────────────────────────────────────────────────────────────────────
| # | Check                                                          | Status |
|---|----------------------------------------------------------------|--------|
| 1 | Safety login                                                   | PASS   |
| 2 | Safety dashboard                                                | PASS   |
| 3 | Audits / forms / records accessible                             | PASS   |
| 4 | Public safety forms still work                                  | PASS   |
| 5 | No "Safety Portal" drift                                        | PASS   |

────────────────────────────────────────────────────────────────────────────
SHOP OPERATIONS
────────────────────────────────────────────────────────────────────────────
| # | Check                                                          | Status |
|---|----------------------------------------------------------------|--------|
| 1 | Shop login                                                     | PASS   |
| 2 | Fleet / equipment views                                         | PASS   |
| 3 | Inspection / maintenance paths render                           | PASS   |
| 4 | No "Shop Portal" drift                                          | PASS   |

────────────────────────────────────────────────────────────────────────────
FIELD LEADERSHIP
────────────────────────────────────────────────────────────────────────────
| # | Check                                                          | Status |
|---|----------------------------------------------------------------|--------|
| 1 | Field Leadership login                                         | PASS   |
| 2 | Records / forms render                                          | PASS   |
| 3 | Daily report / JHP / field submissions render                   | PASS   |

────────────────────────────────────────────────────────────────────────────
DRIVER / MAGIC-LINK
────────────────────────────────────────────────────────────────────────────
| # | Check                                                          | Status |
|---|----------------------------------------------------------------|--------|
| 1 | `/transport-verify/:token` opens for tokenized link            | PASS   |
| 2 | Acknowledgement path completes                                  | PASS   |
| 3 | No Transportation TopBar bleed into driver chrome               | PASS   |
| 4 | Tokenized driver link not broken                                | PASS   |

────────────────────────────────────────────────────────────────────────────
OVERALL ROLE-SMOKE STATUS
────────────────────────────────────────────────────────────────────────────
PASS across every role · 100 % of checklists green · 1 non-blocking
warning (admin Intelligence cold-start slow). No FAIL items.
