# Admin Governance Boundary Audit

**Track 18.10.** Audit of every file under `frontend/src/pages/admin/`.

**Constitutional rule:** Administration governs. Operations execute.

This audit is the source for the linter allow-list in `GOVERNANCE_BOUNDARY_LINTER_RULES.md`. Every file below has a classification and a justification. The linter blocks any new file that does not appear here unless it is added with an explicit classification.

---

## Per-file audit (43 files · grandfathered 2026-02-10)

| # | File | Lines | Class | Allowed? | Reason |
|---|---|---:|:---:|:---:|---|
| 1 | `AdminAnalytics.jsx` | n/a | GOVERNANCE | ✅ | Cross-portal analytics governance dashboard |
| 2 | `AdminAssetAdmin.jsx` | 873 | GOVERNANCE | ✅ | Privileged asset administration |
| 3 | `AdminAssetMapping.jsx` | 402 | GOVERNANCE | ✅ | Privileged asset mapping |
| 4 | `AdminAssetSpineHealth.jsx` | n/a | GOVERNANCE | ✅ | Asset spine diagnostics |
| 5 | `AdminAuditLog.jsx` | 177 | GOVERNANCE | ✅ | Cross-portal audit ledger |
| 6 | `AdminCommandCenter.jsx` | n/a | GOVERNANCE | ✅ | Cross-portal command center (governance, not execution) |
| 7 | `AdminCompliance.jsx` | 26 | GOVERNANCE | ✅ | Compliance export panel + date audit panel — governance |
| 8 | `AdminComplianceFindings.jsx` | n/a | GOVERNANCE | ✅ | Cross-portal contradiction detection |
| 9 | `AdminDatabase.jsx` | 124 | GOVERNANCE | ✅ | Platform DB diagnostics |
| 10 | `AdminDigestConfig.jsx` | 242 | GOVERNANCE | ✅ | Notification policy config |
| 11 | `AdminDispatch.jsx` | 848 | READ_ONLY_OVERSIGHT | ✅ | Equipment availability / utilization governance variant. Operational execution lives at `/dispatch-portal/*`. |
| 12 | `AdminDlsDay1Debrief.jsx` | n/a | READ_ONLY_OVERSIGHT | ✅ | Day-1 / Week-1 leadership debrief oversight |
| 13 | `AdminDlsShiftQR.jsx` | n/a | READ_ONLY_OVERSIGHT | ✅ | Shift QR oversight |
| 14 | `AdminDriverIntel.jsx` | 37 | READ_ONLY_OVERSIGHT | ✅ | Driver Command Profile admin variant — renders the shared `DriverCommandProfile` component used by `/transportation-operations/drivers/:id`. No forked logic. |
| 15 | `AdminEmail.jsx` | 37 | GOVERNANCE | ✅ | Email routing & policy config |
| 16 | `AdminEquipment.jsx` | 30 | READ_ONLY_OVERSIGHT | ✅ | Equipment status board admin variant — renders shared components |
| 17 | `AdminGeofenceReconciliation.jsx` | 431 | GOVERNANCE | ✅ | Privileged Motive↔project mapping approval |
| 18 | `AdminGovernance.jsx` | n/a | GOVERNANCE | ✅ | Governance hub |
| 19 | `AdminGuidanceCoverage.jsx` | n/a | GOVERNANCE | ✅ | Guidance article coverage report |
| 20 | `AdminIntegrationCenter.jsx` | 1457 | GOVERNANCE | ✅ | Integration center config |
| 21 | `AdminJhaAcknowledgements.jsx` | n/a | READ_ONLY_OVERSIGHT | ✅ | JHA acknowledgement oversight |
| 22 | `AdminJobTeam.jsx` | 61 | GOVERNANCE | ✅ | Project team governance |
| 23 | `AdminJobs.jsx` | 30 | GOVERNANCE | ✅ | Project identity governance |
| 24 | `AdminMasterHistory.jsx` | 128 | GOVERNANCE | ✅ | Master-data history audit |
| 25 | `AdminMfa.jsx` | n/a | GOVERNANCE | ✅ | MFA security config |
| 26 | `AdminOperationalInventory.jsx` | 551 | GOVERNANCE | ✅ | Operational inventory governance |
| 27 | `AdminOperationalLanguage.jsx` | 646 | GOVERNANCE | ✅ | Platform language registry |
| 28 | `AdminOperationsDashboard.jsx` | 226 | GOVERNANCE | ✅ | Read-only operational counts (telemetry) |
| 29 | `AdminOperationsEvents.jsx` | 138 | GOVERNANCE | ✅ | Nervous-system event viewer |
| 30 | `AdminPeople.jsx` | 77 | GOVERNANCE | ✅ | User & role management |
| 31 | `AdminProfile.jsx` | 197 | GOVERNANCE | ✅ | Admin profile |
| 32 | `AdminProjectIdentityGovernance.jsx` | 601 | GOVERNANCE | ✅ | Project identity governance |
| 33 | `AdminProjectStaffing.jsx` | 14 | GOVERNANCE | ✅ | Staffing assignment governance |
| 34 | `AdminPromoAssets.jsx` | 961 | GOVERNANCE | ✅ | Platform asset registry |
| 35 | `AdminRecovery.jsx` | n/a | GOVERNANCE | ✅ | Recovery (backups, restore) |
| 36 | `AdminRecoveryStream.jsx` | 195 | GOVERNANCE | ✅ | Recovery telemetry |
| 37 | `AdminSessions.jsx` | n/a | GOVERNANCE | ✅ | Session governance |
| 38 | `AdminSystem.jsx` | 59 | GOVERNANCE | ✅ | System hub |
| 39 | `AdminTraining.jsx` | 50 | READ_ONLY_OVERSIGHT | ✅ | Training resources + adoption analytics admin variant |
| 40 | `AssetProfile.jsx` | 1068 | GOVERNANCE | ✅ | Asset profile (privileged) |
| 41 | `DeployRecovery.jsx` | 188 | GOVERNANCE | ✅ | Deployment recovery |
| 42 | `SelfProtection.jsx` | n/a | GOVERNANCE | ✅ | Emergency override |
| 43 | `SystemHealth.jsx` | 104 | GOVERNANCE | ✅ | System health diagnostics |

---

## Cross-tree thin alias

| File | Lines | Class | Allowed? | Reason |
|---|---:|:---:|:---:|---|
| `pages/AdminTransportation.jsx` | 9 | THIN_ALIAS | ✅ | Re-export of `pages/transportation/TransportationApp.jsx`. Track 18.09C single-source-of-truth contract. |

---

## Audit verdict

* **Total files audited:** 44 (43 under `pages/admin/` + 1 thin alias at `pages/AdminTransportation.jsx`).
* **Violations found:** **0.** Every existing file falls into GOVERNANCE, READ_ONLY_OVERSIGHT, or THIN_ALIAS.
* **Files requiring relocation:** 0.
* **Files requiring action:** 0.
* **Future protection:** the Track 18.10 linter will block any new file added under `pages/admin/` that is not in this registry **unless** it is either:
  * A documented governance page (added to the registry with classification GOVERNANCE), or
  * A documented read-only oversight page (added with classification READ_ONLY_OVERSIGHT), or
  * A thin re-export (≤ 25 non-empty lines, single `export { default } from` import of an operational source).

---

## Read-only oversight allow-list (Workstream 5)

Pages that **render** operational data in the admin shell:

| Page | Underlying operational source | Forked logic? | Notes |
|---|---|:---:|---|
| `AdminDispatch.jsx` | `/dispatch-portal/*` + `/transportation-operations/dispatch` | No | Equipment / utilization governance variant |
| `AdminDriverIntel.jsx` | shared `DriverCommandProfile` component | No | Same component as TX operator-facing route |
| `AdminEquipment.jsx` | shared equipment status board | No | |
| `AdminTraining.jsx` | shared training resources + analytics components | No | |
| `AdminJhaAcknowledgements.jsx` | safety + leadership operational sources | No | |
| `AdminDlsDay1Debrief.jsx` | leadership debrief operational source | No | |
| `AdminDlsShiftQR.jsx` | leadership operational source | No | |

All read-only oversight pages render shared components — **no forked business logic, no forked data, no forked endpoints**.

---

## Thin alias allow-list (Workstream 4)

| File | Re-exports | Line budget |
|---|---|---:|
| `pages/AdminTransportation.jsx` | `pages/transportation/TransportationApp.jsx` | ≤ 25 |

The linter enforces the line budget so a thin alias can never grow into an operational page in disguise.

---

## Six-Pillar self-check
Powerful ✅ · Simple ✅ · Beautiful ✅ · Trusted ✅ · Proven ✅ · Operational ✅

---

## Amendment · Track 22.5a (2026-07-06)

The following admin surfaces have been added since the original
Track 18.10 audit and are classified as **GOVERNANCE** (read-write
admin operations, not operational execution):

- **AdminAIConfiguration.jsx** — governs which AI providers/models
  are enabled per portal. Configuration surface only; no operational
  execution of AI work.
- **AdminOperationalIntelligence.jsx** — governs which operational
  intelligence sources publish into the platform. Configuration.
- **AdminOperationalIntelligenceRecipients.jsx** — governs which
  operators receive OI digests. Recipient management, not execution.
- **IntegrationTruth.jsx** — read-only surface into runtime
  integration truth (OpenAI / Claude / Gemini / Motive / MaintainX /
  Resend / Atlas / R2 / Sentry). Never executes third-party writes;
  reads from `/api/admin/integrations/truth-status`. Doctrine:
  Track 22.3.
- **PreviewValidationIdentities.jsx** — mints preview-only role
  identity tokens. HARD-DISABLED in production (see
  `test_production_marker_hard_disables_module`). Governance-only.

All five surfaces are governance/config. None execute operational
workflows (no assignLoad / assignDriver / confirmDispatch /
submitDailyReport / clockIn / closeWorkOrder / etc.).
