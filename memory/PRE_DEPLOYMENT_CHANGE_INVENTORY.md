PRE-DEPLOYMENT CHANGE INVENTORY
===============================

DATE: 2026-02-15
SCOPE: Files touched across Tracks 18.00 → 18.12C. This inventory is
       organised by surface area. Risk level is LOW / MED / HIGH for
       deployment regression risk specifically (not security).

LEGEND
  LOW    — pure rename / language / lint / doc; broad test coverage.
  MED    — logic change behind existing tests + live smoke proof.
  HIGH   — auth/RBAC or data-layer touch — requires explicit smoke +
           regression sign-off.

────────────────────────────────────────────────────────────────────────────
FRONTEND PAGES
────────────────────────────────────────────────────────────────────────────
| Path                                                                   | Reason changed                                                          | User-facing impact                              | Risk | Smoke needed                          | Covered by tests |
|------------------------------------------------------------------------|-------------------------------------------------------------------------|-------------------------------------------------|------|---------------------------------------|------------------|
| frontend/src/pages/transportation/_shared.jsx                          | txGet 401/403 absorption + txHeaders + visibleTxOpsNavGroups            | Restricted-state UX + role-aware nav            | HIGH | Dispatch + Admin both                 | 18.12B + 18.12C lock |
| frontend/src/pages/transportation/_lists.jsx                           | Real data via OPS-GUARD + restricted fallback                           | Drivers/Carriers/Trucks lists                   | HIGH | Dispatch live smoke                   | 18.12C lock + live |
| frontend/src/pages/transportation/_orientation.jsx                     | Real data via OPS-GUARD; Email Pilot tab hidden for dispatch            | Orientation 5 sub-tabs                          | HIGH | Dispatch + Admin                      | 18.12C lock |
| frontend/src/pages/transportation/_intelligence.jsx                    | Restricted state for Class C analytics; Cleanup remains Class B         | Intelligence (admin-only)                       | MED  | Admin smoke                           | 18.12B + 18.12C  |
| frontend/src/pages/transportation/_command_queue.jsx                   | OPS-GUARD for Morning Queue + Forecast; Health tab hidden for dispatch  | Automation surface                              | HIGH | Dispatch + Admin                      | 18.12C lock |
| frontend/src/pages/transportation/_views.jsx                           | OPS-GUARD for compliance dashboard + doc center; restricted for audit   | Compliance / Documents / Audit Timeline         | MED  | Dispatch + Admin                      | 18.12C lock |
| frontend/src/pages/transportation/MissionControl.jsx                   | Layout repair + workspace strip (Track 18.12)                            | Mission Control                                 | MED  | Dispatch + Admin                      | 18.12 lock |
| frontend/src/pages/transportation/TransportationApp.jsx                | Routing prefix-aware (Track 18.12)                                       | Top-level shell                                 | MED  | Both                                  | 18.12 lock |
| frontend/src/pages/transportation/TransportationWorkspaceShell.jsx     | Shell composition                                                       | Shell chrome                                    | LOW  | Visual                                | 18.00 Phase A |
| frontend/src/pages/transportation/CertificateVerify.jsx                | Driver magic-link surface — no auth change                              | Public driver flow                              | LOW  | Magic-link smoke                      | 18.00G |
| frontend/src/pages/transportation/ExternalCarrierInvite.jsx            | Carrier invite — no auth change                                          | Carrier magic-link                              | LOW  | Magic-link smoke                      | 18.00G |
| frontend/src/pages/* (other portals: PM, HR, Safety, Shop, FL, Admin)  | Track 18.01–18.07 language + ODS migration                              | Portal naming + case style                      | LOW  | Per-role smoke                        | 18.01–18.07 |
| frontend/src/pages/PublicHome*.jsx + hub/homepage routes               | Track 18.06 hub/homepage language cleanup                               | Public copy                                     | LOW  | Anonymous smoke                       | 18.06 lock |

────────────────────────────────────────────────────────────────────────────
FRONTEND COMPONENTS
────────────────────────────────────────────────────────────────────────────
| Path                                                                   | Reason                                                                  | Impact                          | Risk | Smoke                | Tests |
|------------------------------------------------------------------------|-------------------------------------------------------------------------|---------------------------------|------|----------------------|-------|
| frontend/src/components/transportation/TxOpsRestricted.jsx             | Branded restricted-state component (18.12B)                             | Class-C deep-link UX            | LOW  | Visual              | 18.12B |
| frontend/src/components/operations_transportation_integration.jsx      | Cross-portal readiness helper (18.00F)                                  | Mission Control data feed       | MED  | Both                | 18.00F |
| frontend/src/components/PortalShell.jsx + topbar/footer                | Naming + ODS migration                                                  | Global chrome                   | LOW  | Visual              | 18.01–18.04 |

────────────────────────────────────────────────────────────────────────────
FRONTEND HOOKS / HELPERS
────────────────────────────────────────────────────────────────────────────
| Path                                                                   | Reason                                                                  | Impact                          | Risk | Smoke                | Tests |
|------------------------------------------------------------------------|-------------------------------------------------------------------------|---------------------------------|------|----------------------|-------|
| frontend/src/lib/api.js                                                | Cross-portal 401 absorption, session-status bus, skipSessionStatus flag | Global error UX                 | HIGH | Per-role smoke      | 18.00F + 18.12B |
| frontend/src/lib/adminAuth.js                                          | Untouched (token getter + isAdmin)                                       | Admin token storage             | —    | —                   | — |
| frontend/src/lib/dispatchAuth.js                                       | Untouched (dispatch token getter)                                        | Dispatch token storage          | —    | —                   | — |
| frontend/src/lib/directoryAuth.js                                      | Multi-login response → portal token writers                              | All portal tokens               | MED  | Multi-login smoke   | 18.01 IAM |

────────────────────────────────────────────────────────────────────────────
BACKEND ROUTES
────────────────────────────────────────────────────────────────────────────
| Path                                                                   | Reason                                                                  | Impact                          | Risk | Smoke                | Tests |
|------------------------------------------------------------------------|-------------------------------------------------------------------------|---------------------------------|------|----------------------|-------|
| backend/routes/transportation.py                                       | Carriers/Persons/Trucks list+read+workspace migrated to OPS-GUARD       | Dispatch reads real data        | HIGH | Live API + browser  | 18.12C lock |
| backend/routes/transportation_experience.py                            | Documents/Inspections queue + workspaces + entity timeline OPS-GUARD     | Dispatch compliance reads       | HIGH | Live API + browser  | 18.12C lock |
| backend/routes/transportation_orientation.py                           | Dashboard/modules/assignments/certificates OPS-GUARD                     | Dispatch orientation surface    | HIGH | Live API + browser  | 18.12C lock |
| backend/routes/transportation_automation.py                            | Morning Queue + Forecast OPS-GUARD                                       | Dispatch automation             | HIGH | Live API + browser  | 18.12C lock |
| backend/routes/transportation_intelligence.py                          | Cleanup-signals OPS-GUARD                                                | Dispatch cleanup card           | HIGH | Live API + browser  | 18.12C lock |
| backend/server.py                                                      | Wired dispatch deps into 3 register_* calls                              | Backend boot wiring             | HIGH | Backend supervisor   | 18.12C lock |

────────────────────────────────────────────────────────────────────────────
BACKEND TESTS (locks + regressions added)
────────────────────────────────────────────────────────────────────────────
| Path                                                                   | Reason                                                                  | Notes                                                |
|------------------------------------------------------------------------|-------------------------------------------------------------------------|------------------------------------------------------|
| tests/test_track_18_12c_transportation_role_permissions.py             | 43-test lock for 18.12C                                                  | NEW                                                  |
| tests/test_track_18_12b_transportation_dispatcher_functionality.py     | 47-test lock for 18.12B                                                  | NEW                                                  |
| tests/test_track_18_12_mission_control_access_layout.py                | Mission Control lock                                                     | Existing                                              |
| tests/test_track_18_11_r8_duplicate_cta_linter.py                      | CTA pattern lock                                                         | Existing                                              |
| tests/test_track_18_10_governance_boundary_linter.py                   | Admin/Operations boundary lock                                            | Existing                                              |
| tests/test_track_18_09c_transportation_ownership.py                    | Ownership audit lock                                                     | Existing                                              |
| tests/test_track_18_09a_true_completion_pass.py                        | Friction completion lock                                                 | Existing                                              |
| tests/test_track_18_00_phase_f_portal_aware_data_layer.py              | Updated test_25 to recognise ops_guard alias                             | Track 18.12C amendment                              |
| tests/test_track_18_00_phase_g_final_polish.py                         | Updated test_24 to recognise ops_guard alias                             | Track 18.12C amendment                              |
| tests/test_track_18_00_phase_a_universal_shell.py                      | Updated test_06 for visibleTxOpsNavGroups acceptance                     | Track 18.12B amendment                              |
| tests/test_track_16_06_transportation_experience_layer.py              | Updated test_6 for ops_guard alias                                        | Track 18.12C amendment                              |
| tests/test_track_16_07_transportation_workflow_activation.py           | Updated test_2 for ops_guard alias                                        | Track 18.12C amendment                              |
| tests/test_track_16_15_operational_cleanup_companion.py                | Updated test_21 to allow ops_guard read; POST still admin-strict          | Track 18.12C amendment                              |
| tests/test_track_16_15a_dashboard_cleanup_signal_mirror.py             | Updated test_11 — cleanup-signals now Class B (dispatch read)             | Track 18.12C amendment                              |
| tests/test_pre_deployment_release_safety.py                            | THIS RELEASE FREEZE                                                      | NEW                                                  |

────────────────────────────────────────────────────────────────────────────
DEPLOYMENT GATE
────────────────────────────────────────────────────────────────────────────
| Path                                  | Reason                                                                  |
|---------------------------------------|-------------------------------------------------------------------------|
| scripts/deployment_gate.py            | Added the 18.12B + 18.12C + this release-safety test to the gate list   |

────────────────────────────────────────────────────────────────────────────
DOCS / MEMORY
────────────────────────────────────────────────────────────────────────────
- /app/memory/PRD.md (updated)
- /app/memory/TRACK_18_12B_TRANSPORTATION_DISPATCHER_FUNCTIONALITY_RESTORE.md
- /app/memory/TRANSPORTATION_DISPATCHER_FUNCTIONALITY_AUDIT.md
- /app/memory/TRANSPORTATION_API_AUTH_MATRIX.md
- /app/memory/TRANSPORTATION_DISPATCHER_OPERATOR_WALKTHROUGH.md
- /app/memory/TRACK_18_12C_TRANSPORTATION_ROLE_PERMISSIONS_FIX.md
- /app/memory/TRANSPORTATION_ROLE_PERMISSION_MATRIX.md
- /app/memory/TRANSPORTATION_WORKSPACE_FUNCTIONALITY_AUDIT.md
- /app/memory/PRE_DEPLOYMENT_RELEASE_FREEZE.md (this set)
- /app/memory/PRE_DEPLOYMENT_CHANGE_INVENTORY.md (this set)
- /app/memory/PRE_DEPLOYMENT_ENVIRONMENT_CHECK.md (this set)
- /app/memory/PRE_DEPLOYMENT_DATA_SAFETY_CHECK.md (this set)
- /app/memory/PRE_DEPLOYMENT_ROLE_SMOKE_MATRIX.md (this set)
- /app/memory/PRE_DEPLOYMENT_TRANSPORTATION_ACCEPTANCE_GATE.md (this set)
- /app/memory/PRE_DEPLOYMENT_DESIGN_LANGUAGE_CHECK.md (this set)
- /app/memory/PRE_DEPLOYMENT_TEST_RESULTS.md (this set)
- /app/memory/PRODUCTION_DEPLOYMENT_CHECKLIST.md (this set)
- /app/memory/RELEASE_NOTES_TRACK_18_PRODUCTION_CUT.md (this set)

────────────────────────────────────────────────────────────────────────────
NOT TOUCHED (CONFIRMED SAFE)
────────────────────────────────────────────────────────────────────────────
- /app/backend/routes/dispatch_*.py  (dispatch portal preserved)
- driver magic-link / carrier invite workflows
- /app/backend/routes/safety_*, hr_*, pm_*, shop_*, fl_*  (no auth/RBAC drift)
- email templates (Track 18.05 was a one-touch terminology pass, locked)
- PDF generators (Track 18.05)
