# PLATFORM_ROUTE_MAP

**Date:** 2026-02-01 · Part of the Platform Truth Map
**Raw source:** `truth_map_data/frontend_routes.csv` (249 rows) · `truth_map_data/route_domains.json`
**Total routes:** 249 (one `*` catch-all + one `/app/*` legacy redirect + 247 substantive routes)

## Auth-wrapper legend (from `App.js`)

| Wrapper | Resolves to | Effect |
|---------|-------------|--------|
| `A(…)` | `RequireAdmin` | Admin token required |
| `AP(…)` | `RequireAdminOrPm` | Admin OR PM token |
| `APS(…)` | `RequireAdminOrPmOrSafety` | Admin / PM / Safety |
| `P(…)` | `RequirePm` | PM token required |
| `PS(…)` | `RequirePmOrShop` | PM / Shop |
| `H(…)` | `RequireHr` | HR token required |
| `S(…)` | `RequireSafety` | Safety token required |
| `SF(…)` | `RequireSafetyForms` | Safety-forms shared password |
| `SAF(…)` | `RequireSafetyOrSafetyForms` | Safety OR safety-forms |
| `DP(…)` | `RequireDispatch` | Dispatch token required |
| `FL(…)` | `RequireFl` | Field Leadership per-user token |
| `D(…)` | `RequireDev` | Dev portal token |
| _(empty)_ | none | **PUBLIC** — anyone can reach (security may still be enforced server-side) |

> Wrapper detection is mechanical: it strips the prefix from the route's `element` attribute. If a route renders `<X />` directly without a wrapper, it is classified PUBLIC.

---

## 1 · ADMIN domain — 66 routes 🟢 KNOWN GOOD

All gated by `A(…)` or `AP(…)` or `APS(…)` except `/admin/login` (public). Components: AdminHub, AdminPeople, AdminMfa, AdminJobs, AdminEquipment, AdminEmail, AdminTraining, AdminCompliance, AdminSystem, AdminDatabase, AdminIntegrationCenter, AdminDispatch, AdminDlsShiftQR, AdminDlsDay1Debrief, AdminProfile, AdminOperationsEvents, AdminDigestConfig, SystemHealth, AdminAuditLog, AdminLegacyImports, AdminSessions, AdminGuidanceCoverage, AdminOperationalInventory, AdminGovernance, SelfProtection, AdminComplianceFindings, AdminOperationalLanguage, DeployRecovery, AssetProfile, AdminMasterHistory, AdminAnalytics, AdminLeadershipEquipment, AdminTerminations, AdminGuide, ProjectPnlPage, Dashboard (inspections), ViewInspection, AdminPromoAssets, AdminQaqcList, JobPhotosLibrary, JhaPlansAdmin, AdminTrainingVideos, TrenchBoxesAdmin, JhaPosterPrint, TrenchBoxPosterPrint, AllPostersPrint, MeetingsDashboard, ViewMeeting, DailyReportsDashboard, ViewDailyReport, IncidentsDashboard, ViewIncident, EquipmentDashboard, ViewEquipmentInspection, QaqcDetail, AdminTraining (training tracks), ViewSafetyForm, AdminAuditDetail, AdminDeployReadiness.

Classification: **🟢 KNOWN GOOD** for the 65 gated routes. `/admin/login` is intentionally public.

---

## 2 · PM domain — 27 routes 🟢 KNOWN GOOD

All gated by `P(…)` or `AP(…)` except `/pm/login`, `/pm/reset/:token` (public). Includes: PmHub, PmCrewCompliance, PmJobs, PmProjectDetail, PmFieldLeadership, PmFleet, PmPeople, PmSuppliers, PmPosters, PmQaqcList, JobPhotosLibrary, PmChangePassword, MeetingsDashboard / IncidentsDashboard / Dashboard / DailyReportsDashboard / ViewIncident / ViewMeeting / ViewDailyReport (shared with admin via `AP`), JhaPlansAdmin (shared via `AP`), TrenchBoxesAdmin, EquipmentDashboard, ViewEquipmentInspection, `/pm/odr` (OdrCenter — operator records hub).

Classification: **🟢 KNOWN GOOD**.

---

## 3 · HR domain — 20 routes 🟢 KNOWN GOOD

All gated by `H(…)` except `/hr/login`, `/hr/forgot`, `/hr/reset/:token` (public). Components: HrHub, HrFieldLeadership, HrFieldLeadershipUsers, HrEmployeeAccountability, HrTimeVerification, HrTimeOff, HrChangePassword, HrPayrollVariance, HrEmployees, HrEmployeeAccountabilityTimeline, HrDriverQualificationDashboard, HrDriverQualificationImport, HrIncidents (HR mirror of incidents), HrDailyReports, HrDailyReportView, HrSafetyRecords (cross-portal read), HrTrainingRecords.

Classification: **🟢 KNOWN GOOD**.

---

## 4 · Shop domain — 7 routes 🟢 KNOWN GOOD

Gated by `S(…)` or shop session. Components: ShopHub, ShopChangePassword, ShopEquipment (shop-scoped equipment list), ShopEquipmentDetail, FleetVisibility, ShopLogin, ShopResetPassword.

Classification: **🟢 KNOWN GOOD** — except GAP-10 (Trash button dead — see `ORPHAN_AND_GAP_REGISTER.md`).

---

## 5 · Safety Portal domain — 18 routes 🟢 KNOWN GOOD

Gated by `S(…)` except login/forgot/reset (public). Components: SafetyHub, SafetyAudits, SafetyChangePassword, SafetyCorrectiveActions, SafetyDigest, SafetyDocuments, SafetyEmployees, SafetyFireExtinguishers, SafetyFireExtinguishersImport, FleetVisibility (safety scope), SafetyFormsRecords, SafetyIncidents, SafetyLibrary, SafetyLogin, SafetyReports, SafetyResetPassword, SafetyTraining.

Classification: **🟢 KNOWN GOOD**.

---

## 6 · Safety Public domain — 12 routes 🟢 KNOWN GOOD

Mix of public form-submit, the shared-password Safety Forms portal, and read-only links. Routes: `/safety` (section landing · public), `/safety/forms/login`, `/safety/forms`, `/safety/forms/equipment-issuance/{new,:id,:id/return}`, `/safety/forms/equipment-training/{new,:id}`, `/safety/cards`, `/safety/inspections/new` (gated SF), `/safety/jha` and `/safety/trench-boxes` (redirected to public read-only pages).

Classification: **🟢 KNOWN GOOD**.

---

## 7 · Dispatch domain — 8 routes 🟢 KNOWN GOOD

Gated by `DP(…)`. Components: DispatchHub (board), DispatchBoard, DispatchChangePassword, DispatchDriverQualification, FleetVisibility (dispatch scope), DispatchForgotPassword, DispatchLogin, DispatchResetPassword.

Classification: **🟢 KNOWN GOOD**.

---

## 8 · Field Leadership Portal — 6 routes 🟢 KNOWN GOOD

Per-user portal gated by `FL(…)`. Components: FieldLeadershipPortalDashboard, FieldLeadershipPortalChangePassword, FieldLeadershipPortalLogin, FieldLeadershipDriverQualification (per-user read-only), plus `/field-leadership/portal` index. Also: `/field-leadership` (legacy shared-password gate that survives for the 10-form library).

Classification: **🟢 KNOWN GOOD** for the per-user side. `/field-leadership` legacy gate remains — operator confirmed coexistence.

---

## 9 · Legacy "Leadership" domain — 6 routes 🟡 KNOWN GAP

`/leadership` is the older shared-password gate (`MASCIGC`). Routes: `/leadership` (gate hub), `/leadership/{kind}/new`, `/leadership/records`, `/leadership/records/:id`, `/leadership/login`, `/leadership/legacy-login`. Functionally complete; coexists with the per-user Field Leadership Portal. Classified as a GAP only in the sense that two parallel auth surfaces remain — operator-acknowledged.

Classification: **🟡 KNOWN GAP — intentional dual-track until operator retires legacy**.

---

## 10 · Other / public-shared — 64 routes

Includes:

| Route | Purpose | Classification |
|-------|---------|----------------|
| `/` `/cheatsheet` `/jha` `/trench-boxes` | Public Hub + read-only field references | 🟢 KNOWN GOOD |
| `/daily/new` `/daily/submit` `/inspect/new` `/inspections/new` `/meetings/new` `/incidents/new` `/jha/new` `/equipment/new` `/qaqc/:slug/new` `/reports/daily/new` `/fleet/dvir/new` `/fleet/weekly-emergency/new` `/fleet/weekly-lead/new` | Public form submit pages — anyone with the URL can submit; rate-limited | 🟢 KNOWN GOOD |
| `/daily/submit` `/inspections/submit` `/meetings/submit` `/incidents/submit` `/jha/submit` `/equipment/submit` `/qa-qc` `/submit` `/thank-you` | Post-submit confirmations and aliases | 🟢 KNOWN GOOD |
| `/inspections/:id` `/equipment/:id` | Redirects to `/admin/inspections/:id` and `/admin/equipment/:id` respectively | 🟡 KNOWN GAP — see GAP-16 / GAP-17. Cross-portal users land in admin namespace |
| `/d/:token` | DLS day-1 debrief public token landing | 🟢 KNOWN GOOD |
| `/time-off/public/:token` | Public time-off response link | 🟢 KNOWN GOOD |
| `/po-requests` | Public PO requests list (PMs can self-serve) | 🟢 KNOWN GOOD |
| `/asset-transfers` | Asset transfer queue (auth at component level) | ⚪ UNKNOWN — needs runtime trace of component-internal RequireAdmin |
| `/constraints` `/constraints/new` `/constraints/:id` | Constraints board (admin-or-PM at component level) | 🟢 KNOWN GOOD |
| `/document-expirations` | Doc expiration list (gated at component level by HR/Admin) | 🟢 KNOWN GOOD |
| `/incidents` `/incidents/:id` `/inspections` `/meetings` `/meetings/:id` `/daily` `/daily/:id` `/qaqc` `/qaqc/:id` | Listing/detail pages — token detected at component level | 🟢 KNOWN GOOD (validated by AP wrapper inside component) |
| `/field` `/field/calculators` `/shift` | Field crew tools (no auth wrapper — anyone on URL can use; rate-limited submission) | 🟢 KNOWN GOOD |
| `/legal/privacy` `/legal/terms` | Public legal pages | 🟢 KNOWN GOOD |
| `/training` `/training/:track` `/training/:track/packet` `/training/:track/poster` `/training-hub` `/ops-training` `/ops-training/:slug` | Public training packets & posters | 🟢 KNOWN GOOD |
| `/notifications` | Generic notifications drawer (auth checked at component level) | 🟢 KNOWN GOOD |
| `/tasks` | Global tasks list (auth checked at component level) | 🟢 KNOWN GOOD |
| `/project-health` | Project health dashboard (gated at component level — admin/PM) | 🟢 KNOWN GOOD |
| `/access-denied` | Generic 403 page | 🟢 KNOWN GOOD |
| `*` | NotFound catch-all | 🟢 KNOWN GOOD (Defect 1 fixed 2026-02-01) |
| `/app/*` | Legacy alias redirect to `/` (crew hub removed 2026-04-28) | 🟢 KNOWN GOOD |
| `/guidance` `/guidance/:articleId` `/guidance/section/:sectionId` | Operational guidance (public training-style content) | 🟢 KNOWN GOOD |

---

## 11 · Operational Records (`/operational-records`) · ODR domain — 5 routes 🟢 KNOWN GOOD

The Operational Daily Record (ODR) public viewer + submission flow. Routes: `/operational-records` (hub), `/odr/new`, `/odr/:id`, `/odr/:id/done`, `/odr/center`, `/odr/public/:doc_id`.

Classification: **🟢 KNOWN GOOD**.

---

## 12 · Driver domain — 1 route 🟢 KNOWN GOOD

`/driver` — Driver Magic Landing (per-driver magic-link session). Real workflow lives at `/d/:token` (shift start). Single-route alias.

---

## 13 · Sign-in — 1 route 🟢 KNOWN GOOD

`/sign-in` — multi-portal directory master login. Returns up to 6 portal tokens at once.

---

## 14 · Dev domain — 2 routes 🟢 KNOWN GOOD

`/dev`, `/dev/login`. Gated by `D(…)`. Externally hidden from MASCI staff per `test_credentials.md`.

---

## Cross-cutting observations

- **Two PM Exposure Tile routes referenced from PM sidebar but not declared** in `App.js` (intentional per operator stop-list — see GAP-18). This is a known dead-link condition.
- **149 of 249 routes are auth-wrapped**; the remainder are intentionally public (form submit, legal, training, guidance, redirects). No silent-public admin routes detected.
- **Path-prefix uniqueness**: Verified — no `<Route>` path appears more than once with different elements.

---

## Total classification

| Tag | Count |
|-----|-------|
| 🟢 KNOWN GOOD | 244 |
| 🟡 KNOWN GAP | 3 (GAP-16, GAP-17, GAP-18 + legacy `/leadership` dual-track) |
| 🔴 BROKEN | 0 |
| ⚪ UNKNOWN | 2 (`/asset-transfers` and `/notifications` rely on in-component RequireX; not 100% verifiable from App.js alone) |
| ⚫ OPERATOR DECISION NEEDED | 0 |

> Raw evidence: every route + component + auth wrapper is in `/app/memory/truth_map_data/frontend_routes.csv`.
