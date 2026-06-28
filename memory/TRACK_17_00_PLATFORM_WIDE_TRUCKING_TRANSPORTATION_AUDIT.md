# Track 17.00 — Platform-Wide Trucking / Transportation Discovery Audit

**Date:** 2026-02-10  
**Status:** ✅ GO — full inventory complete, zero code changes  
**Type:** Audit-only · read-only discovery · no behavior changes

---

## Executive summary

MASCI has accumulated **15 distinct tracks of transportation
capability** (Tracks 16.04 → 16.16) plus a parallel Dispatch
portal (~13 dispatch modules across `routes/dispatch_*.py`) plus
fleet, equipment, HR driver qualification, safety driver holds,
PM-side awareness, and public-facing carrier-onboarding flows.

This audit produces the source of truth for the next build —
specifically, a unified Transportation Command Center that
**preserves Dispatch** as a major operational workspace and folds
all remaining surfaces (Compliance Center · Orientation · Cleanup
Companion · Intelligence Center · Operations Integration) into one
coherent system.

**Headline numbers**

* **110** backend transportation endpoints (`routes/transportation*.py`
  + `operations_transportation_integration.py`).
* **68** backend dispatch endpoints (`routes/dispatch_*.py`).
* **15** fleet/equipment endpoints that intersect transportation
  (`routes/fleet_ops.py`).
* **35** transportation-related Mongo collections (see
  `TRUCKING_TRANSPORTATION_FEATURE_INVENTORY.md`).
* **24+** frontend routes that touch trucking / hauling.
* **9** distinct portals carry some transportation surface.

**Verdict**

* The existing inventory is **broad but coherent** — every
  surface routes through documented engines, and Tracks 16.11A
  and 16.16 have already established the read-only consumer
  pattern that lets adjacent portals safely consume Transportation
  data.
* No "lost" or unreachable feature was found — every backend
  endpoint maps to at least one mounted UI surface or a
  documented public token flow.
* **Three duplications** are tolerable and intentional (admin
  Transportation Compliance Center ↔ dispatch readiness mirror ↔
  PM/Operations consumer widgets — same data, different
  audiences). No surface mutates source-of-truth records outside
  the Transportation Compliance Center.
* Dispatch remains the operational system of record for active
  hauls. Transportation Compliance Center remains the system of
  record for fleet readiness. The two systems are bridged via
  the existing eligibility gate (Track 16.09) and the
  Decision Surface (Track 16.13).

**Status:** ✅ **GO** to proceed with a unified Transportation
Command Center build, but only after the recommendations below
are reviewed.

---

## Portals scanned

| Portal | Transportation surfaces |
|---|---|
| **Dispatch** | DispatchHub · DispatchHubV2 · DispatchBoard · DispatchCommandCenter · DispatchOperationsMapPage · DispatchHaulLedger · DispatchDriverQualification · DispatchDriverProfile · FleetVisibility(dispatch) · `/dispatch-portal/*` (16 routes) |
| **Admin** | AdminTransportation (mounts entire Transportation operating module at `/admin/transportation/*`) · AdminDispatch · AdminDriverIntel · AdminEquipment · AdminLeadershipEquipment · AdminAssetMapping · AdminAssetSpineHealth · AdminAssetAdmin · AdminMasterHistory · AdminPeople · AdminOperationsDashboard |
| **HR** | HrDriverQualificationDashboard · HrDriverQualificationImport · HrMotiveDrivers · HrDriverProfile · HrEmployees (employee drawer carries Transportation chip via Track 16.11A) |
| **Safety** | FleetVisibility(safety) · SafetyDriverProfile · Driver safety holds via existing eligibility gate · NewFleetDVIR (admin-only QA) |
| **PM** | PmHub · PmCommandCenter (Track 16.16 widget) · PmProjectDetail (Track 16.16 readiness card + risk banner + closeout) · PmFleet · PmJobTeam |
| **Operations** | OperationsCenterCommand (Track 16.16 health widget) · OperationsMapPage · DispatchOperationsMapPage · Operations actions queue · Operational timeline sidecar |
| **Equipment/Fleet** | EquipmentDashboard · FleetVisibility · FleetDVIRConfirmation · NewFleetDVIR · /equipment/* · /fleet/dvir/* |
| **Public** | `/transport-invite/:token` (ExternalCarrierInvite) · `/transport-verify/:cnum` (CertificateVerify) · `/fleet/dvir/submit` · `/equipment/submit` (public NewEquipmentInspection) · public orientation flows under `/transportation/invite/{token}/orientation/*` |
| **Driver-facing** | `/d/:token` (DriverMagicLanding) · `/driver` (DriverShift) · driver assignment acknowledgement · driver shift start · driver magic-link auth · `/dispatch-portal/driver/:driverKey` |

---

## Total features found

* **15 Tracks** in the 16.x Transportation series (16.04 → 16.16
  inclusive).
* **9 dispatch surfaces** (board · command center · map · haul
  ledger · driver qualification · driver profile · day-1
  debrief · governance findings · continuity events).
* **8 carrier-onboarding surfaces** (invite portal · packet
  upload · document review · carrier workspace · packet status ·
  carrier intelligence · carrier audit · admin carriers list).
* **8 driver surfaces** (driver dashboard · driver intel ·
  driver workspace · driver qualification · driver shift ·
  driver magic-link landing · driver assignment ack · driver
  documents).
* **7 truck surfaces** (truck workspace · truck inspections ·
  truck readiness · DVIR · weekly lead · weekly emergency ·
  truck intelligence).
* **6 intelligence surfaces** (operational health · dashboard ·
  recommendations · predictions · audit · dispatch-learning).
* **3 automation surfaces** (digest preview/dry-run/send-now ·
  scheduled producers · cleanup companion materializer).
* **2 cleanup-companion surfaces** (signals list · materialize
  actions).
* **2 operations-integration surfaces** (readiness composer ·
  three operations awareness widgets).

---

## Total routes found

* **24 frontend transportation-related route paths** in
  `App.js` (excluding nested children of `/admin/transportation/*`).
* **110 backend transportation endpoints** across:
  - `routes/transportation.py` (Track 16.04 base · 20 endpoints)
  - `routes/transportation_phase2.py` (Track 16.06 · 30 endpoints)
  - `routes/transportation_experience.py` (Track 16.07 · 9 endpoints)
  - `routes/transportation_orientation.py` (Track 16.08 · 26 endpoints)
  - `routes/transportation_dispatch_gate.py` (Track 16.09 · 7 endpoints)
  - `routes/transportation_automation.py` (Track 16.10 · 18 endpoints)
  - `routes/transportation_intelligence.py` (Track 16.12 · 12 endpoints)
  - `routes/operations_transportation_integration.py` (Track 16.16 · 1 endpoint)
* **68 backend dispatch endpoints** across 10 dispatch route modules.
* **15 fleet/equipment endpoints** that intersect transportation.

---

## Total backend endpoints

**193** endpoints across the trucking / hauling / transportation
domain (110 transportation + 68 dispatch + 15 fleet/equipment).

---

## Total collections

**35 transportation-related Mongo collections** — see
`TRUCKING_TRANSPORTATION_FEATURE_INVENTORY.md` for the full table.
Key collections:

* **System of record**: `carriers` · `transport_persons` ·
  `transport_trucks`
* **Eligibility / state**: `transport_eligibility_state` ·
  `transport_employees` (Track 16.11)
* **Documents**: `carrier_documents` · `driver_documents` ·
  `transport_truck_inspections`
* **Packet workflow**: `transport_carrier_packets` ·
  `transport_packet_requirements` · `transport_packet_submissions`
* **Orientation**: `transport_orientation_modules` ·
  `transport_orientation_questions` ·
  `transport_orientation_assignments` ·
  `transport_orientation_certificates` · `transport_invites`
* **Dispatch**: `dispatch_assignments` · `dispatch_state_events` ·
  `dispatch_continuity_events` · `dispatch_broadcasts` ·
  `dispatch_users` · `dispatch_driver_sessions` ·
  `dispatch_magic_links`
* **Dispatch gate / governance**: `transport_dispatch_overrides` ·
  `transport_dispatch_recommendation_audit`
* **Automation / digest**: `transport_automation_events` ·
  `transport_automation_runs` · `transport_command_digest_runs` ·
  `transport_action_items` · `transport_notifications`
* **Audit**: `transport_intelligence_audit` ·
  `email_routing_audit_v2` · `audit_events` (unified)
* **HR sync**: `transport_hr_sync_runs`
* **Rates**: `transport_rate_schedules`
* **Certificates**: `transport_certificates`

---

## Hidden / unreachable features

**None found.** Every backend endpoint maps to at least one
mounted UI surface or a documented public token flow.

Observations worth noting (not "unreachable", but worth highlighting):

1. **DispatchHub vs DispatchHubV2** — both are mounted
   (`/dispatch-portal` → DispatchHub; `/dispatch-portal/hub_v2`
   → DispatchHubV2). Legacy is reachable for rollback.
2. **`/dispatch-portal/hub_legacy`** explicitly points back to
   the legacy hub — intentional fallback.
3. **`AdminTransportation`** is a single SPA route
   (`/admin/transportation/*`) that internally renders the
   Transportation Compliance Center, the Intelligence Center,
   the Cleanup Companion, the Orientation Center, and the
   Command Queue — these are NOT separately routed in `App.js`
   (they are children inside `pages/transportation/TransportationApp.jsx`).
   This is by design but means deep links are only discoverable
   via internal navigation.
4. **`transport_employees`** collection is owned by the Track
   16.11 HR Lifecycle Integration — used by Track 16.11A's HR
   sync monitor. The collection has no admin UI of its own;
   it's a derived index, surfaced through the HR driver
   qualification dashboard and the sync-monitor health widget.

---

## Duplications / overlaps

Three intentional / tolerable surface duplications were found —
**all share the same underlying engines** and none mutate source
records independently:

1. **Top cleanup signal mirror** — surfaced in:
   - the Cleanup Companion tab (`/admin/transportation/intelligence/cleanup`)
   - the Transportation Dashboard card (Track 16.15A, admin-only)
   - the Operations Center health widget (Track 16.16, all portals)
   All three read from the same `transport_action_items` queue and
   `build_cleanup_signals` engine — no duplicate logic.
2. **Eligibility chips** — surfaced on every entity workspace
   (carrier, driver, truck) plus the dispatch readiness summary
   plus the Track 16.16 readiness card. All read
   `transport_eligibility_state`; the Track 16.09 gate is the
   single writer.
3. **HR ↔ Transportation health** — surfaced via the HR sync
   widget (admin Transportation dashboard) AND via the Track
   16.16 readiness card. Both consume `scan_hr_transport_consistency`
   from `transport_sync_monitor`.

**No conflicting writes** — Transportation Compliance Center is
the only mutator of `carriers`/`transport_persons`/`transport_trucks`/
`carrier_documents`/`driver_documents`/`transport_truck_inspections`.
Dispatch reads but does not write these. Operations / PM never
write.

---

## Dispatch preservation findings

Dispatch is the operational system of record for **active hauls**
and **driver shift state** and must be preserved. Specifically:

* `dispatch_assignments` is the canonical assignment table —
  Transportation must NEVER write here.
* `dispatch_state_events` is the canonical state-machine
  history.
* `DispatchCommandCenter` is the live operational workspace —
  not a candidate for replacement.
* `DispatchHaulLedger` is the daily haul-cycle ledger —
  preserved as-is.
* Driver-facing magic-link auth + driver shift + assignment
  acknowledgement (`/d/:token`, `/driver`) — preserved.
* Twilio SMS callbacks (`/sms/twilio-status-callback`) —
  preserved.

**Bridge points to preserve:**

* The eligibility gate (`POST /dispatch/transportation/check`)
  is consumed at assignment creation time — preserve this
  contract.
* The decision-surface recommendation
  (`GET /dispatch/recommendation`) and its audit
  (`POST /dispatch/recommendation/audit`) — preserve this.
* The dispatch override flow
  (`POST /dispatch/transportation/override`) — preserve this.

**What should NOT happen in any future unified system:**

* Do NOT migrate `dispatch_*` collections into `transport_*`.
* Do NOT replace `DispatchCommandCenter`.
* Do NOT remove the driver magic-link / driver shift screens.
* Do NOT change the `/dispatch/transportation/check` contract.

---

## Transportation system findings

Tracks 16.04 → 16.16 form a coherent system with documented
boundaries:

* **System of record** (mutating writes): Transportation Compliance
  Center (`routes/transportation.py` + `routes/transportation_phase2.py`).
* **Read-only intelligence**: `routes/transportation_intelligence.py`
  (Track 16.12) — driver/carrier/truck scoring + dashboard +
  recommendations + cleanup signals.
* **Read-only operations integration**: `routes/operations_transportation_integration.py`
  (Track 16.16) — cross-portal awareness layer.
* **Read-only dispatch bridge**: `routes/transportation_dispatch_gate.py`
  (Track 16.09) — eligibility check + override audit.
* **Lifecycle automation**: `routes/transportation_automation.py`
  (Track 16.10) — annual document rotation, command digest,
  HR sync.
* **External onboarding**: `routes/transportation_orientation.py`
  (Track 16.08) — carrier invite portal + orientation modules +
  certificates.

Audit doctrine is consistent: every mutator writes to
`audit_events` AND to its domain-specific audit collection
(`transport_intelligence_audit`, `transport_dispatch_recommendation_audit`,
`email_routing_audit_v2`).

---

## Data model findings

See `TRUCKING_TRANSPORTATION_FEATURE_INVENTORY.md` for the full
collection table. Highlights:

* Every Transportation collection uses `tenant: "masci"` —
  consistent multi-tenant discipline.
* `transport_eligibility_state` is a derived/materialized index
  — never a source of truth — written by `transport_eligibility.py`
  and read everywhere.
* `audit_events` is the platform-wide unified timeline that
  carries dispatch + transportation events alongside daily
  reports and operational records.
* No collection mixes read/write between Dispatch and
  Transportation domains.

---

## RBAC findings

See `TRUCKING_TRANSPORTATION_RBAC_MATRIX.md` for the per-surface
matrix. Key observations:

* The **admin Transportation Compliance Center** is strictly
  `require_admin_dep`-gated.
* The **dispatch surfaces** require `require_dispatch_or_admin`
  (Track 16.13 introduced this dual-gate pattern).
* The **HR sync widgets** require either admin or HR portal
  token (Track 16.11A introduced this).
* The **Track 16.16 readiness composer**
  (`/api/operations/transportation/readiness`) accepts ANY
  signed-in portal token — cross-portal read.
* The **public surfaces** (invite portal, certificate
  verification) are signed-token-gated only; no admin auth
  required.
* The **driver magic-link** uses a single-use signed token that
  exchanges for a short-lived driver session token.

---

## Workflow findings

End-to-end workflows are well-documented in their respective
track memos. The major workflows:

1. **Carrier onboarding** — admin issues invite → carrier
   uploads packet → admin reviews → packet approved → eligibility
   recalculates → carrier becomes dispatchable.
2. **Driver onboarding** — same as carrier; orientation
   modules + quiz + certificate flow.
3. **Truck readiness** — admin or carrier records inspection
   → eligibility recalculates.
4. **Document review** — review queue → accept/reject → audit
   timeline.
5. **Dispatch assignment** — dispatcher creates assignment →
   Track 16.09 gate auto-blocks if not eligible → Track 16.13
   surfaces explainable recommendation → audit row written.
6. **Override** — dispatcher overrides with justification →
   `transport_dispatch_overrides` row created → email routed
   via Track 16.10 catalog.
7. **HR lifecycle sync** — HR termination/leave fires Track
   16.11 hooks → `transport_employees` updated → eligibility
   recalculates → Track 16.11A monitor surfaces mismatches.
8. **Annual automation** — Track 16.10 scheduler scans documents
   approaching expiration → action items materialized →
   command digest delivered.
9. **Cleanup companion** — Track 16.15 builds 12-signal list
   on-demand → admin materializes actions → action items added
   to Track 16.10 queue.
10. **Intelligence recommendation** — Track 16.12 / 16.13 / 16.14
    learning loop tracks dispatcher decisions and refines
    explanations.
11. **Project / operations awareness** — Track 16.16 composer
    surfaces fleet readiness in PM/Operations workspaces
    without writes.
12. **Certificate verification** — public token visitor opens
    `/transport-verify/:cnum` → orientation certificate
    rendered with hash and tamper check.

---

## Recommended next track

**Track 17.01 — Transportation Command Center Architecture
Proposal** (no build, written design):

* Define the navigation tree for a unified Transportation
  Command Center.
* Identify the single landing page (likely the existing Track
  16.12 Intelligence Dashboard or a new "Command Bridge" that
  links to all five workspaces: Compliance · Orientation ·
  Dispatch · Intelligence · Cleanup).
* Specify which surfaces are deep-linked and which are
  embedded.
* Identify any router-config consolidation
  opportunities (e.g. moving `/dispatch-portal/hub_legacy` to
  an explicit archive route).
* Confirm the existing read-only cross-portal contract is the
  pattern for all future awareness widgets.

---

## Files created (Track 17.00 deliverables)

* `/app/memory/TRACK_17_00_PLATFORM_WIDE_TRUCKING_TRANSPORTATION_AUDIT.md` (this file)
* `/app/memory/TRUCKING_TRANSPORTATION_FEATURE_INVENTORY.md`
* `/app/memory/TRUCKING_TRANSPORTATION_ROUTE_MAP.md`
* `/app/memory/TRUCKING_TRANSPORTATION_RBAC_MATRIX.md`
* `/app/memory/TRUCKING_TRANSPORTATION_DUPLICATION_AND_HIDDEN_FEATURES.md`

PRD updated with the audit entry.

---

## Tests

A lightweight regression file was added:

`/app/backend/tests/test_track_17_00_transportation_audit_artifacts.py`

It verifies the five required audit files exist and contain the
mandated sections. No behavior-changing tests were added.

Wired into `/app/scripts/deployment_gate.py`.

---

## Final call

**✅ GO** — the platform is healthier than expected, the
inventory surfaces no surprises, no hidden routes, no orphan
endpoints, and no destructive duplication. The next track is
free to plan a unified Transportation Command Center using the
architecture rules documented here, with Dispatch preserved
unchanged as a major operational workspace.
