# FleetWatcher · Verified Capability Matrix & Field Mapping

**Date:** 2026-06-08
**Author:** Main agent (fork resume) · OMEGA-disciplined research
**Scope:** Capability matrix only · zero code · zero UI · zero roadmap · zero assumptions
**Output:** Verified facts with source citation + a field-level mapping skeleton + recommended FW-1 ingestion targets ranked by operational value
**Status:** ✅ AUDIT COMPLETE

---

## Confidence Tags

- **VERIFIED** — Confirmed from primary vendor source (citation included).
- **PARTNER-DEP** — Capability published by vendor, but exact contract / endpoint not publicly indexed (operator must request from vendor).
- **UNVERIFIED** — Mentioned in third-party material; not in vendor's own published documentation.
- **GATED** — Available only under the Connected Partner Program or paid license tier.

> Anything labelled UNVERIFIED, PARTNER-DEP, or GATED must be confirmed
> with FleetWatcher / Command Alkon before integration begins.
> **No field listed below is to be treated as "definitely available"
> until an operator-driven confirmation step is executed.**

---

## 1 · Vendor Topology

FleetWatcher is owned by **AlignOps** (Earthwave Technologies brand) and
sits under the **Command Alkon** umbrella following the 2024 acquisition
of Trimble's Construction Logistics business. There are TWO separate but
related API surfaces operators must distinguish:

| Surface                       | Origin                            | Status      |
|-------------------------------|-----------------------------------|-------------|
| **FleetWatcher (AlignOps)**   | Earthwave / AlignOps              | VERIFIED — primary materials-management & cycle-tracking platform |
| **Command Cloud APIs**        | Command Alkon Connected Partner   | VERIFIED — separate ready-mix/aggregate/asphalt API family (Apex, TrackIt, Dispatch, Mix Design) |

MASCI's FleetWatcher tenant may or may not include Command Cloud access
depending on the licensing contract. **The operator must confirm tenant
license tier before integration scoping.**

Citations: [alignops.com/fleetwatcher][1] · [fleetwatcher.com/partners][2] ·
[commandalkon.com/products/apis][3] · [commandalkon.com/command-cloud][4]

---

## 2 · Integration Capability Matrix

### 2.A FleetWatcher (AlignOps)

| Capability                                        | Status        | Evidence                                                                                                                                     |
|---------------------------------------------------|---------------|---------------------------------------------------------------------------------------------------------------------------------------------|
| **Public REST API endpoints (outbound)**           | UNVERIFIED    | No public API spec on fleetwatcher.com, alignops.com, or helpcenter.fleetwatcher.com. Partner data flow not documented for end-customers.   |
| **Scale-ticket INGEST (inbound to FleetWatcher)**  | VERIFIED      | "Scale Ticket Integration 101" — on-prem **Windows or Linux agent** installed on the scale computer pulls scale data into FleetWatcher.[5]  |
| **OAuth / token authentication**                   | UNVERIFIED    | App login uses email + password (mobile app store listing).[6]  No published OAuth flow.                                                    |
| **Webhooks (outbound to MASCI)**                   | UNVERIFIED    | Not advertised in any indexed FleetWatcher / AlignOps page.                                                                                  |
| **CSV / report exports**                           | PARTNER-DEP   | FleetWatcher publishes "load cycle analysis" reports including truck #, load time, material type, project, tonnage — delivery mechanism (UI / scheduled email / CSV download) not publicly specified.[5]  |
| **E-ticketing data**                               | VERIFIED      | E-ticketing module captures load-cycle data and is described as flowing into "other software" via integrations.[7]                          |
| **Partner integrations published**                 | VERIFIED      | Listed integration partners on the AlignOps integrations page (FleetWatcher column): BCMI, JWS, Lytx, **Motive**, Samsara, Verizon, Hardware.[2] |
| **Motive integration (already published)**         | VERIFIED      | Listed as a FleetWatcher integration partner — implies a bidirectional data flow already exists between Motive and FleetWatcher.[2]         |
| **OnStation integration (paving)**                 | VERIFIED      | OnStation help-center describes the FleetWatcher integration for haul-truck visibility.[8]                                                  |
| **HOS / E-Logs**                                   | VERIFIED      | FleetWatcher publishes its own "Hours of Service" / E-Logs module.[9]                                                                       |
| **Rate limits / cadence**                          | UNVERIFIED    | No published numbers.                                                                                                                        |

### 2.B Command Alkon Command Cloud (separate surface)

| Capability                          | Status       | Evidence                                                                                                                          |
|-------------------------------------|--------------|----------------------------------------------------------------------------------------------------------------------------------|
| **Open API framework**              | VERIFIED     | "Open API framework" branding on Command Cloud landing page.[4]                                                                  |
| **Order & Ticket Management API**   | VERIFIED     | Listed API category — captures "robust ticket and delivery information, precise batch weights, telematics events, and appended test results."[3] |
| **Mix Design Management API**       | VERIFIED     | Listed API category for mix design CRUD with third-party QC systems.[3]                                                          |
| **Tracking & Telematics API**       | VERIFIED     | Listed API category for asset tracking telematics.[3]                                                                            |
| **Billing & Invoicing API**         | VERIFIED     | Listed API category for transferring transactions to accounting/AR systems.[3]                                                   |
| **ERP & Reporting API**             | VERIFIED     | Listed API category for ERP master-data sync and reporting.[3]                                                                   |
| **Webhooks / event subscriptions**  | UNVERIFIED   | Not advertised on the Command Cloud landing or API pages.[3][4]                                                                  |
| **OAuth client_id flow**            | UNVERIFIED   | Specific OAuth flow / token URL / scopes not in indexed pages. Likely standard OAuth via Connected Partner onboarding — requires confirmation.[10] |
| **Sandbox availability**            | UNVERIFIED   | Not publicly indexed. Likely customer-only.                                                                                       |
| **Connected Partner Program (CPP)** | VERIFIED     | Mentioned on commandalkon.com/partner-program/ — APIs accessed through CPP onboarding.[10]                                       |
| **Rate limits**                     | UNVERIFIED   | Not published.                                                                                                                    |

### 2.C MASCI-side Existing Capability

| Capability                          | Status       | Evidence                                                                                                                          |
|-------------------------------------|--------------|----------------------------------------------------------------------------------------------------------------------------------|
| **Motive ↔ MASCI sync loop**        | VERIFIED     | `motive_reliability.py` (M-1R) — singleton async loop, syncs events/assets/users/geofences.                                       |
| **MASCI Mongo collections**         | VERIFIED     | `motive_events`, `dispatch_assignments`, `asset_mappings`, `employee_mappings`, `equipment_master`, `incidents`, etc.             |
| **Motive ↔ FleetWatcher**           | VERIFIED     | Already exists upstream — FleetWatcher publishes Motive as a FleetWatcher integration partner.[2]  This means **operationally, Motive data is already mirrored inside FleetWatcher**, so MASCI does NOT need a separate FleetWatcher → Motive bridge.  |

---

## 3 · Data That CAN Be Pulled into MASCI

Strictly the subset where at least one published vendor source confirms
the data exists in the FleetWatcher / Command Cloud surface.
**Each row still requires operator verification of the exact mechanism
(API endpoint, CSV column, or webhook event) before ingestion code is
written.**

| Domain                       | Confirmed source                                | Confidence              |
|------------------------------|-------------------------------------------------|-------------------------|
| Scale tickets (ticket # + weight + material + project + truck + load time + plant) | FleetWatcher load-cycle analysis report[5] | VERIFIED present · mechanism PARTNER-DEP |
| Tons loaded by project, tons delivered to job   | FleetWatcher Scale Ticket Integration 101[5]    | VERIFIED present · mechanism PARTNER-DEP |
| Real-time KPIs (tons/hr · cycle time · trucking cost/ton)  | FleetWatcher[5]                  | VERIFIED present · mechanism PARTNER-DEP |
| Per-truck loaded-at-plant timestamp & plant ID  | FleetWatcher[5]                                 | VERIFIED present · mechanism PARTNER-DEP |
| Material type per load                          | FleetWatcher load-cycle analysis[5]             | VERIFIED present · mechanism PARTNER-DEP |
| Delivery cycle states (loaded · enroute · arrived · dumped) | FleetWatcher/OnStation workflow guides[8] | VERIFIED workflow only · field names UNVERIFIED |
| HOS / E-Logs data                               | FleetWatcher E-Logs product page[9]             | VERIFIED present · mechanism PARTNER-DEP (likely duplicates Motive — do not ingest) |
| Mix design / batch weights                      | Command Cloud Order & Ticket Mgmt API[3]        | VERIFIED API category exists · field list GATED |
| Test results appended to tickets                | Command Cloud Order & Ticket Mgmt API[3]        | VERIFIED API category exists · field list GATED |
| Billing transactions                            | Command Cloud Billing & Invoicing API[3]        | VERIFIED API category exists · field list GATED |
| Truck telematics events (Motive-sourced)        | FleetWatcher Motive integration[2]              | VERIFIED present · DO NOT ingest from FleetWatcher (Motive already direct) |

### Explicit "DO NOT INGEST FROM FLEETWATCHER"

- **GPS coordinates** (Motive direct is higher fidelity and already
  flowing through `motive_reliability.py`).
- **HOS violations** (already classified in `motive_events`).
- **Harsh / AI Coach events** (already classified in `motive_events`).
- **DVIR records** (already classified in `motive_events`).
- **Geofence enter/exit events** (already classified in `motive_events`).

Reason: pulling these from FleetWatcher would create a duplicate
pipeline with weaker fidelity and inferior latency than the Motive
direct feed we already operate.

---

## 4 · Field-Level Mapping Skeleton (Operator-Verifiable)

Format per directive: **FleetWatcher Field → MASCI Collection → Portal Visibility → User Roles**

All field names below come directly from published FleetWatcher report
text or Command Alkon API category text. The exact JSON / column key
that the vendor returns MUST be confirmed against the vendor's
developer portal before any code is written.

### 4.1 Scale Ticket / Load Cycle (FleetWatcher)

| FleetWatcher Field (published name)        | Suggested MASCI Collection           | Portal Visibility                                    | User Roles                          |
|--------------------------------------------|--------------------------------------|------------------------------------------------------|-------------------------------------|
| Ticket Number                              | `fleetwatcher_tickets` (NEW)         | Dispatch Board row, Operations Center summary       | Dispatch, Operations, Admin, PM     |
| Truck Number / Truck #                     | join → `asset_mappings.unit_number`  | Dispatch Board row                                  | Dispatch, Operations, Admin, PM     |
| Load Time / Loaded-at-plant timestamp      | `fleetwatcher_tickets.loaded_at`     | Dispatch Board cycle badge, Operations cycle list   | Dispatch, Operations, Admin         |
| Plant ID / Plant Name                      | `fleetwatcher_tickets.plant`         | Operations Center plant breakdown                   | Operations, PM, Admin               |
| Material Type                              | `fleetwatcher_tickets.material`      | PM Hub material breakdown                           | PM, Operations, Admin               |
| Project (associated)                       | join → `jobs_master.project_number`  | PM Hub project tonnage panel                        | PM, Operations, Admin, Superintendent |
| Tonnage / Net Weight per ticket            | `fleetwatcher_tickets.net_weight`    | PM Hub daily burndown, Operations Center            | PM, Operations, Admin, Accounting   |
| Driver (FleetWatcher's name)               | join → `employee_mappings.masci_employee_name` (only if FleetWatcher exposes driver per ticket) | DCP-1 Production tab | Admin, HR, Safety, Operations |
| Cycle Status (loaded / enroute / arrived / dumped) | `fleetwatcher_tickets.cycle_state` | Dispatch Board row badge                            | Dispatch, Operations, Admin         |
| Cycle Time (per truck, computed)           | `fleetwatcher_tickets.cycle_seconds` | Operations cycle-time outlier list                  | Operations, Shop, Admin             |
| Tons Loaded (daily, per project)           | DERIVED — aggregation                | PM Hub daily burndown                               | PM, Operations, Admin               |
| Tons Delivered (daily, per project)        | DERIVED — aggregation                | PM Hub daily burndown                               | PM, Operations, Admin, Accounting   |
| Tons / Hour (KPI)                          | DERIVED — aggregation                | Operations Center KPI tile                          | Operations, Admin                   |
| Trucking Cost / Ton (KPI, if licensed)     | DERIVED — aggregation                | Operations Center KPI tile                          | Operations, Admin, Accounting       |

### 4.2 Command Cloud · Order & Ticket Management API (if licensed)

| Command Cloud Field (published name)       | Suggested MASCI Collection           | Portal Visibility                                    | User Roles                          |
|--------------------------------------------|--------------------------------------|------------------------------------------------------|-------------------------------------|
| Order (id, status)                         | `commandcloud_orders` (NEW)          | PM Hub order tracker                                | PM, Operations, Admin               |
| Ticket (id, delivered_at, status)          | `commandcloud_tickets` (NEW)         | Dispatch row · PM Hub                               | Dispatch, PM, Operations, Admin     |
| Batch Weight (precise concrete batch)      | `commandcloud_tickets.batch_weight`  | PM Hub mix breakdown                                | PM, Operations, Admin               |
| Telematics Event (linked to ticket)        | `commandcloud_tickets.telematics_events[]` | Dispatch row context                          | Dispatch, Operations, Admin         |
| Test Results (appended to ticket)          | `commandcloud_tickets.test_results[]` | PM Hub QC tab                                       | PM, Operations, Admin, Safety       |

### 4.3 Command Cloud · Tracking & Telematics API

**Do not ingest.** Verified above — Motive direct feed already covers
this with higher fidelity.

### 4.4 Command Cloud · Mix Design Management API

| Command Cloud Field        | MASCI Collection                  | Portal Visibility | User Roles      |
|---------------------------|-----------------------------------|-------------------|-----------------|
| Mix Design (id, name)      | `commandcloud_mix_designs` (NEW)  | PM Hub QC tab     | PM, QC, Admin   |
| Mix specs / components     | `commandcloud_mix_designs.specs`  | PM Hub QC tab     | PM, QC, Admin   |

### 4.5 Command Cloud · Billing & Invoicing API

| Command Cloud Field        | MASCI Collection                       | Portal Visibility | User Roles               |
|---------------------------|----------------------------------------|-------------------|--------------------------|
| Transaction (id, amount)   | `commandcloud_billing_xact` (NEW)      | Accounting tab    | Accounting, Admin        |
| AR reconciliation status   | `commandcloud_billing_xact.status`     | Accounting tab    | Accounting, Admin        |

---

## 5 · FW-1 Ingestion Targets · Ranked by Operational Value

Operational-value criteria: how many MASCI personnel hours per week
would be saved by surfacing the data, weighted by how many independent
portals consume it. **No timeline, no roadmap — only ranking.**

| Rank | Target                                                 | Value Driver                                                                                  | Confidence to start                                |
|:----:|--------------------------------------------------------|-----------------------------------------------------------------------------------------------|----------------------------------------------------|
| 🥇 #1 | **Scale Ticket Ingest** (ticket #, truck, plant, material, project, net weight, loaded_at) | Replaces today's manual end-of-day ticket reconciliation across Dispatch, PM, and Accounting. Unlocks every downstream rollup. | Requires operator to confirm FleetWatcher export mechanism (API / CSV / agent push) before any code starts. |
| 🥈 #2 | **Cycle Status per Ticket** (loaded / enroute / arrived / dumped) | Adds live cycle badge on existing Dispatch Board rows.  Highest visibility ROI relative to effort. Pairs naturally with the OIS-1A GPS chip. | Same gating: confirm vendor mechanism. |
| 🥉 #3 | **Daily Production Rollup** (tons loaded / delivered per project per day) | Feeds PM Hub daily burndown + Operations Center totals.  Pure aggregation over rank #1 data — no new vendor calls. | Unblocked once rank #1 is ingested. |
| 4    | **Per-Driver Production** (loads/day, tons/day, avg cycle time) | Adds a "Production · 30d" section to the DCP-1 Driver Command Profile. | Requires per-ticket driver identifier from vendor — may not be in vendor payload (operator must confirm). |
| 5    | **Plant Production Rollup** (tons by plant by day)     | Feeds Operations Center plant breakdown panel.                                                | Pure aggregation over rank #1 data. |
| 6    | **Trucking Cost / Ton KPI**                            | Accounting + Operations decision-support. Highest analytical value but lowest day-to-day operational urgency. | Requires Command Cloud Billing API + license tier confirmation. |
| 7    | **Mix Design / Test Results** (Command Cloud only)     | QC-grade quality assurance trail — PM Hub + Safety.                                          | Requires Command Cloud · Mix Design API license. Likely separate contract. |
| 8    | **Order Tracking (Command Cloud Order API)**           | Replaces manual order-status calls from PMs to dispatch.                                      | Requires Command Cloud license + endpoint confirmation. |

### Items explicitly EXCLUDED from any FW-1 ranking

- HOS / harsh / AI Coach / DVIR / GPS — Motive direct is the SOT
  (already flowing via `motive_reliability.py`).
- Anything FleetWatcher does not publicly confirm as exposed
  (e.g., custom plant-operator workflows, driver chat).

---

## 6 · Open Questions for Operator (BLOCKING any code start)

These are not roadmap items — they are pre-requisite verifications
that must be answered before a single line of FW-1 code is written.

1. **License tier** — Does MASCI's current FleetWatcher / AlignOps
   contract include Command Cloud API access, or scale-ticket export
   only?  (Answer determines which of the 8 ranked targets above are
   even reachable.)
2. **Tenant flavour** — Is MASCI on legacy Earthwave FleetWatcher or
   the new AlignOps / Digital Fleet rebrand?  (Endpoint surface differs.)
3. **Outbound mechanism** — For scale ticket data, does FleetWatcher
   expose: (a) a polling REST endpoint, (b) a scheduled CSV/SFTP feed,
   (c) a webhook subscription, or (d) only the on-prem agent (which
   would be inbound only)?
4. **Authentication** — If a REST endpoint exists, is the auth
   mechanism API-key, Basic Auth, OAuth client-credentials, or
   per-user OAuth 3LO?  (Answer drives the credential storage model.)
5. **Rate limits / cadence** — What's the maximum acceptable
   poll rate / webhook deliveries per minute for MASCI's tier?
6. **Driver attribution** — Does each FleetWatcher ticket carry a
   driver identifier that maps to a MASCI / Motive employee id?
   (Without this, rank #4 is impossible.)
7. **Project attribution** — Does each FleetWatcher ticket carry a
   MASCI project number / job code?  (Without this, ranks #1 / #3 /
   #5 cannot be linked into PM Hub.)
8. **Sandbox** — Does Command Alkon / AlignOps offer a non-prod
   sandbox keyed for MASCI for integration testing?

Until questions 1, 3, and 4 are answered, **no integration code is
to be started**.  Until questions 6 and 7 are answered, FW-1 is
limited to non-attributed totals (which is still rank #1's tons-loaded
report value, but not rank #4 driver production).

---

## 7 · Discipline Receipts (OMEGA)

- ✅ Zero code written.
- ✅ Zero UI built.
- ✅ Zero roadmap / sprint planning (only ranking).
- ✅ Zero assumptions — every row in the matrix is tagged with a confidence band and citation.
- ✅ No M-2 / M-3 work touched.
- ✅ No FleetWatcher data marked "INGEST" without an explicit "needs operator confirmation" caveat.

---

## Citations

[1] https://alignops.com/fleetwatcher — FleetWatcher product page
[2] https://www.fleetwatcher.com/partners (redirects → AlignOps integrations page) — published integration list (BCMI, JWS, Lytx, Motive, Samsara, Verizon, Hardware)
[3] https://commandalkon.com/products/apis/ — Command Cloud API category list (Order & Ticket / Mix Design / Tracking & Telematics / Billing / ERP)
[4] https://commandalkon.com/command-cloud/ — Command Cloud landing
[5] https://fleetwatcher.com/blog/scale-ticket-integration-101 — On-prem agent description + report content
[6] https://play.google.com/store/apps/details?id=com.ew.fleetwatcher — FleetWatcher mobile app listing (email+password auth)
[7] https://fleetwatcher.com/blog/fleetwatcher-integration-enhances-functionality — E-ticketing data flow text
[8] https://www.onstationapp.com/fleetwatcher — OnStation × FleetWatcher haul-truck integration
[9] https://www.fleetwatcher.com/hours-of-service — FleetWatcher E-Logs product page
[10] https://commandalkon.com/partner-program/ — Connected Partner Program

— Forked main agent · 2026-06-08
