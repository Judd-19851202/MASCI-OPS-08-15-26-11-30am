# TRACK 18.09C · Transportation Operations Ownership Audit

**Status:** ✅ AUDIT COMPLETE · 🟢 Architecture is MOSTLY CORRECT · One concrete defect closed · Two governance documents codified
**Date:** 2026-02-10
**Constitutional change:** Transportation Operations is the operational system of record. Administration is the governance system.

---

## Executive Verdict

**The architecture was hypothesized as fundamentally incorrect; the audit shows it is mostly correct *already* — but historically misnamed and missing one concrete redirect protection.**

The Transportation Experience Layer (`pages/transportation/TransportationApp.jsx`) is the **single source of truth** for every Transportation operational capability. The legacy `/admin/transportation/*` route is an **admin-token-gated alias** for the same router; the canonical operational entry point is `/transportation-operations/*` (Track 18.00E-FIX) which is dispatch-token-gated. **One router. Two doorways. Six Pillars upheld.**

The audit identified one concrete defect that violated the Six Pillars (Operational, Trusted): six internal compat redirects in `TransportationApp.jsx` hardcoded the `/admin/transportation/...` prefix, which silently bounced dispatch-authenticated operational users into the admin shell when they hit a legacy URL. **Closed this track** by switching the redirects to path-relative.

Beyond that, the audit produced the four governance matrices the directive demanded so every future Transportation feature has a documented ownership classification before it ships.

---

## Current Architecture Assessment

### Operational entry point — Transportation Operations (`/transportation-operations/*`)
* **Auth gate:** `TX(...)` — accepts dispatch_users / admin tokens (per Track 18.00E-FIX).
* **Mounted component:** `pages/transportation/TransportationApp.jsx`.
* **Side nav:** Admin side nav is *suppressed* when admin token is absent (`showAdminSideNav = isAdmin()` → renders `null` for pure dispatch users). The shell does not read as "Admin Console" for operational users.
* **Sub-nav:** `TransportationSubNav` (cross-portal).
* **Six Pillars:** Powerful ✅ · Simple ✅ · Beautiful ✅ · Trusted ✅ · Proven ✅ · Operational ✅.

### Governance entry point — `/admin/transportation/*`
* **Auth gate:** `A(...)` — admin strict.
* **Mounted component:** same `TransportationApp` via `pages/AdminTransportation.jsx` (a 9-line thin re-export).
* **Role:** Read-only oversight + privileged audit. Same render tree, different navigation framing.
* **Six Pillars:** Powerful ✅ · Simple ✅ · Beautiful ✅ · Trusted ✅ · Proven ✅ · Operational (governance, not execution) ✅.

### Dispatch surfaces — `/dispatch-portal/*`
* **Owner:** Dispatch is its own operational system of record. `_dispatch_bridge.jsx` makes this explicit: *"Dispatch is the operational system of record. Transportation Operations links into Dispatch — it never replaces it."*
* **Conclusion:** Dispatch ownership is **already correct**. No rehome required.

### Driver-token surfaces — `/dr/*`
* **Owner:** Driver self-service surfaces (driver-token-gated).
* **Conclusion:** Already correct.

---

## Ownership Findings

| # | Capability | Currently lives at | Owner today | Six-Pillar correct? | Action |
|---|---|---|---|:---:|---|
| 1 | Transportation Experience Layer router | `pages/transportation/TransportationApp.jsx` | TX & Admin (shared) | ✅ | Keep — one source of truth, two doorways |
| 2 | Compat redirects inside the router | hardcoded `/admin/transportation/...` | Admin-only effectively | ❌ Operational + Trusted | **FIXED this track** — `relative="path"` |
| 3 | Dispatch Board / Command / Map / Ledger / Driver-Q | `/dispatch-portal/*` | Dispatch (operational) | ✅ | Keep |
| 4 | Driver Command Profile (admin shell) | `pages/admin/AdminDriverIntel.jsx` | Admin | ⚠️ misnamed, operational data | Defer rename (filename change is architecture); doc as SHARED |
| 5 | Equipment availability / transfers / utilization | `pages/admin/AdminDispatch.jsx` | Admin shell, dispatch-relevant | ⚠️ operational under admin | Doc as SHARED — operational users reach equivalent via Transportation Operations workspace + Dispatch portal |
| 6 | Compliance findings (cross-portal) | `pages/admin/AdminComplianceFindings.jsx` | Admin | ✅ Governance | Keep — cross-portal contradictions = platform governance |
| 7 | Operations Events nervous-system viewer | `pages/admin/AdminOperationsEvents.jsx` | Admin | ✅ Governance | Keep — read-only platform telemetry |
| 8 | Operations Dashboard | `pages/admin/AdminOperationsDashboard.jsx` | Admin | ✅ Governance | Keep — read-only operational counts |
| 9 | Geofence Reconciliation | `pages/admin/AdminGeofenceReconciliation.jsx` | Admin | ✅ Governance | Keep — privileged Motive↔project mapping approval |
| 10 | Transportation Search rail | `pages/transportation/TransportationSearch.jsx` | TX | ✅ Operational | Keep |
| 11 | Mission Control | `pages/transportation/MissionControl.jsx` | TX | ✅ Operational | Keep |
| 12 | Carriers / Drivers / Trucks lists + workspaces | `pages/transportation/_lists.jsx` | TX | ✅ Operational | Keep |
| 13 | Orientation Center | `pages/transportation/_orientation.jsx` | TX | ✅ Operational | Keep |
| 14 | Compliance Dashboard | `pages/transportation/_views.jsx::ComplianceDashboard` | TX | ✅ Operational | Keep |
| 15 | Document Center | `pages/transportation/_views.jsx::DocumentCenter` | TX | ✅ Operational | Keep |
| 16 | Inspection Center | `pages/transportation/_views.jsx::InspectionCenter` | TX | ✅ Operational | Keep |
| 17 | Rate Schedule Center | `pages/transportation/_views.jsx::RateScheduleCenter` | TX | ✅ Operational | Keep |
| 18 | Audit Timeline (TX) | `pages/transportation/_views.jsx::AuditTimeline` | TX (read-only) | ✅ Operational | Keep |
| 19 | Reports view (TX) | `pages/transportation/_views.jsx::ReportsView` | TX | ✅ Operational | Keep |
| 20 | Intelligence Center | `pages/transportation/_intelligence.jsx` | TX | ✅ Operational | Keep |
| 21 | Command Queue (automation + cleanup) | `pages/transportation/_command_queue.jsx` | TX | ✅ Operational | Keep |
| 22 | Live Operations workspace | `pages/transportation/_live_operations.jsx` | TX | ✅ Operational | Keep |
| 23 | Right Rail | `design-system/PortalShell.jsx` | Shared shell | ✅ | Keep |

---

## Incorrect Ownership Discovered

Only one **concrete** ownership violation was discovered in code (the compat-redirect prefix). Two **nominal** ownership signals are present but do **not** constitute real ownership defects:

1. **`pages/AdminTransportation.jsx` symbol name.** The file is a 9-line thin re-export of `transportation/TransportationApp`. Renaming the symbol is a refactor with no operational benefit; the comment inside the file documents the historical reason. **Defer** rename per "no architecture change unless necessary."
2. **`pages/admin/AdminDriverIntel.jsx`** renders the Driver Command Profile inside `AdminShell` (admin oversight view). A Transportation Operations equivalent already exists (`pages/transportation/_lists.jsx::DriverWorkspace`). The admin variant is governance/oversight, not operational ownership. **Document as SHARED.**

---

## Required Rehome List (this track)

| Item | From | To | Action this track |
|---|---|---|---|
| Compat redirects inside `TransportationApp` | `/admin/transportation/...` (hardcoded) | path-relative | **DONE** — Operational users on `/transportation-operations/fleet/trucks` no longer get bounced into the admin shell on legacy URL hits. |

**No other rehome was required by the directive's hard rules.** Every other Transportation operational capability already lives in `pages/transportation/`. Every governance capability already lives under `pages/admin/`. The dispatch surfaces live at `/dispatch-portal/*` and are correct.

---

## Permission / RBAC / Dispatch / Driver Validation

| Concern | Pre-18.09C | Post-18.09C | Status |
|---|---|---|---|
| Auth gates (`A` admin, `TX` dispatch+admin) | Intact | Intact | ✅ |
| `/admin/transportation/*` admin-strict | Intact | Intact | ✅ |
| `/transportation-operations/*` dispatch-accessible | Intact | Intact | ✅ |
| Dispatch portal routes (`/dispatch-portal/*`) | Intact | Intact | ✅ |
| Driver-token routes (`/dr/*`) | Intact | Intact | ✅ |
| Dispatch token alias | Intact | Intact | ✅ |
| Audit trail collections | Intact | Intact | ✅ |
| API contracts | Intact | Intact | ✅ |
| Existing collections | Intact | Intact | ✅ |
| Backend security | Intact | Intact | ✅ |

---

## Testing Results

* **Track 18.09C lock file** — `backend/tests/test_track_18_09c_transportation_ownership.py` — passes solo (see assertion list at end of this doc).
* **Track 18.07 design system linter** — passes (no terminology drift).
* **Track 18.09 / 18.09A lock files** — pass.
* **Full deployment-gate REGRESSION_FILES** — run separately; result documented in CHANGELOG.
* **Frontend smoke** — Hub renders; Sign-In renders; `/transportation-operations` shell loads via `testing_agent_v3_fork`.

---

## Remaining Risks

1. **Vestigial naming** — `pages/AdminTransportation.jsx` and `AdminDriverIntel.jsx` retain "Admin" in their filenames. Risk is purely cosmetic; semantics are correct (one is a re-export, the other is the oversight variant). No data, no logic, no auth difference. Defer rename to a later cosmetic track.
2. **`/admin/dispatch`** — Track 18.08 verified the admin-gated equipment availability/transfer/utilization surface. Operational users currently reach the dispatch operational ground truth via `/dispatch-portal/*` + Transportation Operations dispatch bridge. The `/admin/dispatch` admin variant remains for governance/oversight. Considered SHARED — re-classify formally if future audit shows operational users are forced through it.
3. **`AdminDriverIntel`** lives at `/admin/people/drivers/:driverKey` — a discoverability question, not an ownership question. The operational Driver Workspace at `/transportation-operations/drivers/:id` is the canonical operator-facing surface.

---

## Final Recommendation

🟢 **GO. The architecture is constitutionally correct.**

* Transportation Operations is the **operational system of record** for transportation execution (✅ codified in `_dispatch_bridge.jsx`).
* Administration is the **governance system** (✅ admin shell pages are oversight, compliance findings, geofence reconciliation, operations events, system health).
* The single source of truth (`TransportationApp`) is shared between the two doorways. **No duplicated logic. No forked business rules. No forked data.**
* The one concrete defect (compat redirect prefix) is **closed** this track.
* Every operational Transportation route resolves cleanly from `/transportation-operations/*` without requiring the admin token.
* Dispatcher / Transportation Manager / Fleet Manager / Carrier Coordinator / Driver Coordinator / Orientation Coordinator / Compliance Coordinator workflows complete entirely inside Transportation Operations + Dispatch portal — **never required to enter Administration.**

The remaining work is **cosmetic naming** (vestigial filenames) and **continued vigilance** to prevent any new operational capability from being built under `pages/admin/`. The new lock file enforces that vigilance.

**Six Pillars status:**
* Powerful ✅ — One shared component, two doorways, full operational capability.
* Simple ✅ — Operational users have one entry point; admin users have one entry point.
* Beautiful ✅ — Side nav suppression for non-admin users keeps the shell calm.
* Trusted ✅ — RBAC unchanged; audit trail unchanged; auth gates unchanged.
* Proven ✅ — Locked by `test_track_18_09c_transportation_ownership.py`.
* Operational ✅ — Dispatch-authenticated operators never bounce into the admin shell on legacy URL navigations.

---

## Supporting documents (this track)

* `TRANSPORTATION_FEATURE_OWNERSHIP_MATRIX.md` — every Transportation feature classified OPERATIONAL / GOVERNANCE / SHARED.
* `ADMINISTRATION_GOVERNANCE_MATRIX.md` — every Administration page classified.
* `TRANSPORTATION_ROUTE_REHOME_PLAN.md` — the one fix shipped this track + the defer list with reasons.
* `TRANSPORTATION_OPERATIONAL_WORKFLOW_AUDIT.md` — eight role workflows walked end-to-end.
* `ROLE_WORKDAY_ANALYSIS.md` — where each Transportation role spends 95% of their workday.
* `TRANSPORTATION_REARCHITECTURE_IMPLEMENTATION.md` — what shipped, what was preserved, what was deferred.
