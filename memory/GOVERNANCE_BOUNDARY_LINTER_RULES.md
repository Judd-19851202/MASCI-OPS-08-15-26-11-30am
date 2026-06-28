# Governance Boundary Linter — Rules Registry

**Constitutional rule (Track 18.10):** Administration governs. Operations execute.

**Build-time enforcement:** every file under `frontend/src/pages/admin/` must fall into one of the three classifications below. New files that do not are blocked by the linter at the deployment-gate.

---

## Classification

### GOVERNANCE
Files that **govern the platform**. Allowed in `pages/admin/` without further justification.
* Platform Settings · Users · Roles · Permissions · RBAC · Tenant Settings
* Feature Flags · Audit Logs · Security · System Health · Backups · Diagnostics
* Integrations · API Management · Deployment · Trust Center · Operational Health (read-only telemetry)
* Read-only enterprise oversight · Emergency override tools

### THIN_ALIAS
Files that re-export an operational source of truth so admin oversight bookmarks resolve.
Must satisfy:
* **≤ 25 non-empty lines.**
* No imports of operational business components (only one re-export line + the imported source).
* No local UI definitions, no state machines, no API calls, no business rules.
* Exists only for admin oversight / bookmark compatibility.

### READ_ONLY_OVERSIGHT
Files that render operational data in the admin shell for governance visibility.
Must satisfy:
* Renders operational data via the **same source-of-truth** components used by the operational workspace (no forked logic, no forked endpoints).
* Wraps the shared component in `AdminShell` only — no duplicate workflow surface.
* Documented in the read-only oversight allow-list.

### FORBIDDEN
Anything that performs operational execution. Examples (high-confidence indicators):
* Day-to-day dispatch assignment workflows that are not the dispatch portal source of truth.
* Driver onboarding execution forms under admin.
* Carrier onboarding execution forms under admin.
* Daily report submission under admin.
* Safety meeting creation under admin.
* JHA execution under admin.
* Field forms under admin.
* Equipment work-order execution under admin.

Any new file matching the FORBIDDEN signal must be relocated to the owning operational workspace.

---

## Allow-list — every current `pages/admin/` file (grandfathered 2026-02-10)

| File | Class | Reason |
|---|:---:|---|
| `AdminAnalytics.jsx` | GOVERNANCE | Cross-portal analytics governance dashboard |
| `AdminAssetAdmin.jsx` | GOVERNANCE | Privileged asset administration |
| `AdminAssetMapping.jsx` | GOVERNANCE | Privileged asset mapping |
| `AdminAssetSpineHealth.jsx` | GOVERNANCE | Asset spine diagnostics |
| `AdminAuditLog.jsx` | GOVERNANCE | Cross-portal audit ledger |
| `AdminCommandCenter.jsx` | GOVERNANCE | Cross-portal command center |
| `AdminCompliance.jsx` | GOVERNANCE | Cross-portal compliance overview |
| `AdminComplianceFindings.jsx` | GOVERNANCE | Cross-portal contradiction detection |
| `AdminDatabase.jsx` | GOVERNANCE | Platform DB diagnostics |
| `AdminDigestConfig.jsx` | GOVERNANCE | Notification policy config |
| `AdminDispatch.jsx` | READ_ONLY_OVERSIGHT | Equipment availability / utilization governance variant. Operational execution lives at `/dispatch-portal/*` and `/transportation-operations/dispatch`. The admin variant is privileged oversight. |
| `AdminDlsDay1Debrief.jsx` | READ_ONLY_OVERSIGHT | Day-1/Week-1 leadership debrief oversight |
| `AdminDlsShiftQR.jsx` | READ_ONLY_OVERSIGHT | Shift QR oversight |
| `AdminDriverIntel.jsx` | READ_ONLY_OVERSIGHT | Driver Command Profile admin variant — renders the **shared** `DriverCommandProfile` component used by `/transportation-operations/drivers/:id`. |
| `AdminEmail.jsx` | GOVERNANCE | Email routing & policy config |
| `AdminEquipment.jsx` | READ_ONLY_OVERSIGHT | Equipment status board admin variant — renders shared components |
| `AdminGeofenceReconciliation.jsx` | GOVERNANCE | Privileged Motive↔project mapping approval |
| `AdminGovernance.jsx` | GOVERNANCE | Governance hub |
| `AdminGuidanceCoverage.jsx` | GOVERNANCE | Guidance article coverage report |
| `AdminIntegrationCenter.jsx` | GOVERNANCE | Integration center config |
| `AdminJhaAcknowledgements.jsx` | READ_ONLY_OVERSIGHT | JHA acknowledgement oversight |
| `AdminJobTeam.jsx` | GOVERNANCE | Project team governance |
| `AdminJobs.jsx` | GOVERNANCE | Project identity governance |
| `AdminMasterHistory.jsx` | GOVERNANCE | Master-data history audit |
| `AdminMfa.jsx` | GOVERNANCE | MFA security config |
| `AdminOperationalInventory.jsx` | GOVERNANCE | Operational inventory governance |
| `AdminOperationalLanguage.jsx` | GOVERNANCE | Platform language registry |
| `AdminOperationsDashboard.jsx` | GOVERNANCE | Read-only operational counts (telemetry) |
| `AdminOperationsEvents.jsx` | GOVERNANCE | Nervous-system event viewer |
| `AdminPeople.jsx` | GOVERNANCE | User & role management |
| `AdminProfile.jsx` | GOVERNANCE | Admin profile |
| `AdminProjectIdentityGovernance.jsx` | GOVERNANCE | Project identity governance |
| `AdminProjectStaffing.jsx` | GOVERNANCE | Staffing assignment governance |
| `AdminPromoAssets.jsx` | GOVERNANCE | Platform asset registry |
| `AdminRecovery.jsx` | GOVERNANCE | Recovery (backups, restore) |
| `AdminRecoveryStream.jsx` | GOVERNANCE | Recovery telemetry |
| `AdminSessions.jsx` | GOVERNANCE | Session governance |
| `AdminSystem.jsx` | GOVERNANCE | System hub |
| `AdminTraining.jsx` | READ_ONLY_OVERSIGHT | Training resources + adoption analytics admin variant |
| `AssetProfile.jsx` | GOVERNANCE | Asset profile (privileged) |
| `DeployRecovery.jsx` | GOVERNANCE | Deployment recovery |
| `SelfProtection.jsx` | GOVERNANCE | Emergency override |
| `SystemHealth.jsx` | GOVERNANCE | System health diagnostics |

**Counts:** GOVERNANCE 36 · THIN_ALIAS 0 (the only thin alias `AdminTransportation.jsx` lives at `pages/AdminTransportation.jsx`, not under `pages/admin/`) · READ_ONLY_OVERSIGHT 7 · FORBIDDEN 0.

---

## Cross-tree thin alias allow-list

| File | Source of truth | Class |
|---|---|:---:|
| `pages/AdminTransportation.jsx` | `pages/transportation/TransportationApp.jsx` | THIN_ALIAS |

This alias must remain ≤ 25 non-empty lines and contain no operational logic.

---

## High-confidence operational-execution indicators

The linter applies **content** scans **only to NEW files** (not in the allow-list). New files trigger a FORBIDDEN classification if **two or more** of the following high-confidence signals appear in a single file:

| Signal | Pattern |
|---|---|
| Dispatch assignment | `assignLoad`, `assignDriver(`, `confirmDispatch(`, regex `\bdispatch_assignment\b` |
| Driver onboarding execution | `driverOnboarding(`, `onboardDriver(`, `submitDriverIntake(` |
| Carrier onboarding execution | `carrierOnboarding(`, `onboardCarrier(` |
| Truck readiness execution | `setTruckReady(`, `confirmTruckReady(` |
| Field-form submission | `submitDailyReport(`, `submitSafetyMeeting(`, `submitJHA(` |
| HR execution | `submitTimesheet(`, `clockIn(`, `clockOut(` |
| Shop execution | `closeWorkOrder(`, `confirmRepair(` |

Two-signal threshold prevents single-signal false positives (e.g., a governance dashboard that *displays* a dispatch metric but does not execute one).

---

## False-positive controls

1. **Allow-list-first.** Every existing file is grandfathered. The linter only fires on new files appearing under `pages/admin/`.
2. **Two-signal threshold** for content scan. One occurrence is not enough.
3. **Read-only oversight allow-list.** Pages that *render* operational data via shared components but don't execute are explicitly classified READ_ONLY_OVERSIGHT.
4. **Thin alias rule.** Re-export files ≤ 25 lines with a single `export { default } from` are auto-classified THIN_ALIAS.
5. **Allow-list is human-readable.** Any future maintainer can see the registry and either justify a new entry or relocate the file.

---

## Six-Pillar self-check

* **Powerful** — Operational pages live where operators work.
* **Simple** — Users are never forced into Administration to do day-to-day work.
* **Beautiful** — Workspace architecture stays intentional.
* **Trusted** — A route name predicts its ownership and permission expectations.
* **Proven** — Enforced by CI, not memory.
* **Operational** — Future drift fails the gate.
