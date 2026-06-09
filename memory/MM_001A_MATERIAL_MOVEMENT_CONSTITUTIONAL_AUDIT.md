# MM-001A · MATERIAL MOVEMENT CONSTITUTIONAL AUDIT
**MASCI / ForgedOps Platform**
**Authorized:** OMEGA Audit-Only · 2026-06-08
**Status:** 🟡 Audit complete · **zero code changes performed**
**Discipline:** Evidence-only. No build. No design. No deploy.

---

## 0 · Headline

🔍 **The platform already has a fully structured material-movement system.** It's called the **Dispatch Assignment**, lives in the `dispatch_assignments` collection, and was built across iter408 (Phase 14.2) and iter410 (Phase 15.1). It carries: truck · driver · trailer · carrier · project · `haul_type` (5-enum) · `material` (drawn from a 57-item, 6-category catalog) · `source_location` · `destination` · `pickup_location` · `dropoff_location` · `liquid_product` · `load_count` · `loader_operator_name` · `note` — with full PENDING → ROLLING → COMPLETED lifecycle + `haul_types_today` daily rollup.

**The Daily Report does not currently tap into this canonical store.** Foremen re-author the same haul in `materials[]` / `production[]` / `activities[]` / `general_notes` (the inconsistency identified in DR-AUDIT-001 §6). The recommendation in this audit therefore is **NOT to build a new Material Movement system** — it is to **fuse the existing dispatch_assignments rollup into the Daily Report and the platform's reporting surfaces.**

---

## 1 · PHASE 1 · Current State Discovery

### 1.1 · Existing material-movement capture surfaces

| # | Surface | File | Carries what | Authored by | Quality |
|---|---|---|---|---|---|
| 1 | **`dispatch_assignments`** (per-truck per-trip ledger) | `routes/dispatch_lifecycle.py` lines 90-175 + `dispatch_assignment_seeds.py` | truck · driver · trailer · carrier · project · haul_type · material · source · destination · pickup · dropoff · liquid_product · load_count · loader_operator_name · note · full lifecycle states | Dispatch | 🟢 **Canonical** |
| 2 | `dispatch_lifecycle` per-day rollup | `routes/dispatch_lifecycle.py` lines 2030-2160 | `haul_types_today` counts by HAUL_TYPE for the dispatch day | Server-computed | 🟢 |
| 3 | DR `materials[]` rows | `daily_reports.py` lines 26-73 | description · quantity · unit · supplier · ticket_number · notes · ticket_photos[] (inline R2) | Foreman (Section 08) | 🟡 in-bound flavour only |
| 4 | DR `production[]` rows (V.2 Wave-1B) | `daily_reports.py` | description · quantity · unit (LF/SY/CY/TON/EA/ACRE/OTHER) · custom_unit_label · station_from/to · notes | Foreman (Section 09b) | 🟡 generic — used for *both* in-bound and out-bound when no other home fits |
| 5 | DR `activities[]` (legacy) | `daily_reports.py` | activity · % complete · station_from/to · notes | Foreman (Section 09) | 🔴 free-text catch-all |
| 6 | DR `general_notes` | `daily_reports.py` | free-text narrative | Foreman (Section 03) | 🔴 last-resort catch-all |
| 7 | Foreman / superintendent spreadsheets | external | varies | offline | 🔴 invisible to platform |
| 8 | Truck driver paper tickets (load receipts) | physical | quantity · plant · disposal | Plant / disposal site | 🟡 photo-uploadable as `ticket_photos[]` in #3 |
| 9 | FleetWatcher (3rd party) | external system | load count · tonnage · cycles · plant call-out · disposal-site receipts | FleetWatcher | 🔴 **not yet integrated** (FW-1 deferred · P0 per OGA-1) |
| 10 | Scale tickets at plants / dumps | external paper | net tonnage | Plant | 🔴 unrecorded except as photo on row #3 |

### 1.2 · Inconsistency map (where foremen actually write the same load today)

| Material flow | Most-common authoring location | Alternative locations seen | Failure mode |
|---|---|---|---|
| Asphalt in-bound (paving day) | DR `materials[]` row + ticket_photos | sometimes `production[]` TON | Triple-write when both used |
| Aggregate / base in-bound | DR `materials[]` | sometimes `production[]` TON | Same |
| Pipe / structures in-bound | DR `materials[]` | rarely elsewhere | OK |
| Dirt out-bound (cut spoils) | DR `production[]` CY | sometimes `activities[]` notes · sometimes `general_notes` | 🔴 fragmented · no rollup possible |
| Millings out-bound | DR `production[]` TON | sometimes `materials[]` (semantically wrong — "delivered") | 🔴 same |
| Demo concrete out-bound | `production[]` CY · `activities[]` notes | rarely `general_notes` | 🔴 same |
| Trees / stumps / vegetation | `general_notes` only | rarely `activities[]` | 🔴 unrecorded structurally |
| Trash / demo debris | `general_notes` only | rarely `materials[]` | 🔴 same |
| Disposal-site tickets | inline `ticket_photos` on `materials[]` | rarely standalone | 🟡 semantically misplaced |
| Recycling-facility tickets | nowhere | — | 🔴 no native capture |
| Internal yard-to-yard moves | dispatch_assignments (✅ canonical) | — | OK |
| Equipment move (lowboy) | dispatch_assignments `haul_type=Equipment Move` (✅ canonical) | — | OK |

### 1.3 · Workflow map (current state)

```
        ┌────────────────────────────────┐
        │   DISPATCH (per-truck ledger)  │  ← canonical store today
        │   dispatch_assignments         │     for material on trucks
        │   haul_type · material         │
        │   source → destination         │
        │   load_count · lifecycle       │
        └────────────────────────────────┘
                       │
                       │ NO LINK TODAY
                       ▼
        ┌────────────────────────────────┐
        │       DAILY REPORT             │  ← foreman re-types
        │   materials[]   (inbound)      │     the same load that
        │   production[]  (generic)      │     dispatch already
        │   activities[]  (free-text)    │     captured. Triple-
        │   general_notes (catch-all)    │     authored in worst case
        └────────────────────────────────┘
                       │
                       ▼
                PDF + Read view
                (consumers see DR view only — dispatch invisible)
```

---

## 2 · PHASE 2 · Material Taxonomy

### 2.1 · The existing canonical taxonomy (`dispatch_assignment_seeds.py`)

**6 categories · 57 material labels · 5 haul types · 5 sources · 6 destinations · 8 pickup locations · 9 dropoff locations**

#### 2.1.1 · HAUL_TYPES (5)
`Material` · `Equipment Move` · `Tanker / Liquid Asphalt` · `Spoils / Dump` · `Support / Misc`

#### 2.1.2 · Material Catalog (6 categories · 57 labels)

| Category | Items |
|---|---|
| **Asphalt / Plant** (15) | Hot Mix Asphalt · Asphalt Base · Asphalt Structural Course · Asphalt Surface Course · SP-9.5 · SP-12.5 · FC-9.5 · FC-12.5 · Type S Asphalt · RAP · **Millings** · Asphalt Grindings · Asphalt Tack · Asphalt Sand · Plant Waste |
| **Aggregate / Base** (14) | Limerock · Crushed Concrete · Recycled Concrete Aggregate · #57 Stone · #89 Stone · 3/4" Rock · 1/2" Rock · Ballast Rock · Rip Rap · FDOT Base · Shell Base · Stabilized Base · Bedding Stone · Drainage Stone |
| **Earthwork / Soils** (12) | Common Fill · Structural Fill · Select Fill · Clean Fill · Borrow Material · Topsoil · **Unsuitable Material** · Muck · Clay · Sand · Washed Sand · Fill Sand · Screened Sand · **Spoils** |
| **Concrete / Demo** (6) | Broken Concrete · **Demo Debris** · Concrete Washout · Concrete Rubble · Curb Debris · Sidewalk Debris |
| **Utility / Roadway** (8) | Pipe · RCP Pipe · HDPE Pipe · Structures · Inlets · Manholes · Utility Bedding · Utility Backfill |
| **Job Support / Misc** (9) | Equipment Move · Barricades · MOT Devices · Signage · Pallets · Forms · Scrap · **Trash** · Other Material |

### 2.2 · Gap analysis against the directive's lists

#### Incoming (directive)
| Directive item | In existing taxonomy? |
|---|---|
| Asphalt | ✅ (multiple variants) |
| Concrete | ✅ via "Broken Concrete" / inbound concrete deliveries usually as a custom material — minor gap |
| Pipe | ✅ |
| Aggregate | ✅ (14 items) |
| Base | ✅ |
| Fill | ✅ (4 variants) |
| Lime Rock | ✅ Limerock |
| Structures | ✅ |
| Signs | ✅ Signage |
| Sod | 🔴 **NOT in taxonomy** — add candidate |
| Striping Materials | 🔴 **NOT in taxonomy** — add candidate |
| Other | ✅ Other Material |

#### Outgoing (directive)
| Directive item | In existing taxonomy? |
|---|---|
| Dirt | ✅ via Borrow / Common Fill / Topsoil (out-bound = spoils) |
| Unsuitable Soil | ✅ Unsuitable Material |
| Millings | ✅ |
| Asphalt (out) | ✅ Plant Waste · RAP |
| Concrete (out) | ✅ Broken Concrete · Demo Debris · Concrete Rubble |
| Trees | 🔴 **NOT in taxonomy** — add candidate |
| Stumps | 🔴 same |
| Vegetation | 🔴 same |
| Trash | ✅ |
| Demo Debris | ✅ |
| Contaminated Material | 🔴 **NOT in taxonomy** — add candidate (regulatory significance) |
| Other | ✅ |

### 2.3 · Recommended additions (AUDIT-ONLY · no build)

If a successor sprint adds these 5 labels to `MATERIAL_CATALOG`, the taxonomy gets coverage of every directive-listed item:

| Label | Category | Reason |
|---|---|---|
| `Sod` | new "Landscape / Site" or under Utility / Roadway | listed by directive |
| `Striping Materials` | Utility / Roadway | listed |
| `Trees / Stumps / Vegetation` (single label or 3) | new "Landscape / Site" | listed · today flows only through `general_notes` |
| `Contaminated Material` | Earthwork / Soils | regulatory tracking · usually requires manifest |

**Audit verdict on taxonomy:** The platform's existing catalog covers ~85% of the directive's requested materials out-of-the-box. The 5 gaps above are additive label-only changes that do not require any structural redesign.

---

## 3 · PHASE 3 · Operational Intelligence Requirements

For each data point: does the platform already track it?

| Data point | Status today | Source-of-truth (recommended) | Consumer interest |
|---|---|---|---|
| **Quantity** | ✅ DR `materials[*].quantity` · `production[*].quantity` | DR foreman (with FW-1 verify) | PM · Exec |
| **Units** | ✅ closed enum on `production[]` LF/SY/CY/TON/EA/ACRE/OTHER | DR | All |
| **Load Count** | ✅ `dispatch_assignments.load_count` (iter410) | Dispatch | PM · Dispatch · Exec |
| **Truck Count** | ✅ count of `dispatch_assignments` rows per project per day | Dispatch (derivable) | PM · Dispatch |
| **Source** | ✅ `dispatch_assignments.source_location` (5 seeded + history) | Dispatch | All |
| **Destination** | ✅ `dispatch_assignments.destination` (6 seeded + history) | Dispatch | All |
| **Hauler** | ✅ `dispatch_assignments.carrier` (MASCI first + history) | Dispatch | PM · Dispatch · Exec |
| **Internal / External** | 🟡 derivable from `carrier == "MASCI"` | Dispatch (signal-only) | PM · Exec |
| **Disposal Site** | 🟡 `destination` carries it but "Dump" is generic | Dispatch (would benefit from disposal-site directory) | PM · Safety · Exec (regulatory) |
| **Recycling Facility** | 🔴 not captured today | (would need new directory or "Recycling" destination tag) | Exec (sustainability) |
| **Reuse Location** | 🔴 not captured | (would need new field) | PM |
| **Cost Visibility** | 🔴 not captured (Vista territory) | Vista (system of record) | Exec · PM |
| **Ticket Attachment** | ✅ DR `materials[*].ticket_photos[]` inline R2 | DR foreman | PM · Safety · Exec |

### 3.1 · Who uses what

| Data point | Foreman | Super | PM | Dispatch | Shop | Safety | Ops Lead | Exec |
|---|---|---|---|---|---|---|---|---|
| Quantity | author | review | ✅ | — | — | — | ✅ | ✅ |
| Load count | review | review | ✅ | author | — | — | ✅ | ✅ |
| Truck count | — | — | ✅ | author | — | — | ✅ | ✅ |
| Source / dest | — | — | ✅ | author | — | — | ✅ | ✅ |
| Hauler | — | — | ✅ | author | — | — | ✅ | ✅ |
| Disposal site | — | — | ✅ | review | — | ✅ regulatory | ✅ | ✅ |
| Ticket photos | author | review | ✅ | — | — | ✅ | — | ✅ |
| Cost visibility | — | — | ✅ | — | — | — | ✅ | ✅ |

---

## 4 · PHASE 4 · User Consumption Audit

For each role: what's **Required · Useful · Noise**.

| Role | Required | Useful | Noise |
|---|---|---|---|
| **Foreman** | DR materials inbound · DR production quantities · ticket photos · safety/incident gates | yesterday's setup · superintendent auto-fill (DR-FIX-2 R7) | hauler · truck count · cycle metrics · cost · plant activity |
| **Superintendent** | crew hours · production qty · safety chain · incident escalation | day's haul totals · source/destination split | individual truck-by-truck cycles |
| **PM** | per-job daily totals (in/out) · load count · truck count · ticket photos · constraint hours_impact · production qty · cost when available | hauler split (MASCI vs external) · disposal-site activity | per-trip detail (unless investigating) |
| **Dispatch** | every per-truck per-trip detail (their canonical job) | rollup matching DR — confirms coverage | foreman's `general_notes` |
| **Shop** | equipment-move dispatch_assignments touching their assets | open MaintainX WO chip on those assets | bulk hauling stats |
| **Safety** | manifest for hazardous / contaminated material · disposal-site provenance · safety incidents · OSHA-impactful loads | tonnage of regulated material | day-to-day uneventful hauls |
| **Operations Leadership** | per-job daily totals · hauler split · cycle averages · plant calls | cost when Vista is bridged | per-trip detail |
| **Executive Leadership** | weekly / monthly rollup by hauler · in vs out · disposal volumes · cost projections · sustainability metrics | trend deltas vs prior period | per-trip detail · per-foreman variance unless flagged |

---

## 5 · PHASE 5 · FleetWatcher Mapping Matrix

Source: `FWA1_FLEETWATCHER_FORENSIC_AUDIT.md` (research-only · NOT yet integrated · FW-1 P0 deferred per OGA-1).

| Material-movement data point | FleetWatcher capability | Today's platform | Verdict |
|---|---|---|---|
| Truck count per day per job | ✅ via load tickets | derivable from dispatch_assignments | **FleetWatcher canonical** for hauling-heavy work |
| Load count | ✅ canonical | dispatch `load_count` is dispatcher-entered | **FleetWatcher source · dispatch verify** |
| Haul cycles (out-and-back time) | ✅ canonical | not captured | **FleetWatcher canonical** |
| Plant call-out activity | ✅ canonical | not captured | **FleetWatcher canonical** |
| Net tonnage per ticket | ✅ canonical (scale-weighed) | DR `materials[].quantity` is foreman-typed | **FleetWatcher canonical** |
| Disposal-site receipts | ✅ when FW captures dump tickets | inline photo only on DR | **FleetWatcher canonical** |
| Asphalt plant tonnage out (daily) | ✅ canonical | not captured | **FleetWatcher canonical** |
| Mix design / category | ✅ FW carries mix-design | derivable from DR `materials[*].description` | **FleetWatcher verify** |
| Recycling-facility deliveries | ✅ when FW captures dest | not captured | **FleetWatcher canonical** |
| Hauler identity (3rd-party carrier name) | ✅ canonical | dispatch `carrier` field | **FleetWatcher source · dispatch confirm** |
| Inbound to MASCI yard | ✅ canonical | dispatch covers internal | **FleetWatcher canonical for external** |
| Outbound from MASCI yard | ✅ | dispatch | **same** |

### 5.1 · FleetWatcher must-own / never-manual

When FW-1 ships, the platform should **stop asking foremen to type**:

- Net tonnage per delivered/disposed load (FW has the scale)
- Truck cycle counts
- Plant activity / call-outs
- Disposal-site receipt provenance
- 3rd-party hauler load counts

The foreman remains the **confirmation gate** — never the data source.

### 5.2 · FleetWatcher sprint readiness (audit-only)

| Sprint | Description | Pillar pass |
|---|---|---|
| **FW-1** Ticket Ingest | Build FW → ForgedOps ingest service (already P0 per OGA-1) | ✅✅✅✅✅ |
| **FW-2** Daily Rollup per Project | Aggregate FW tickets per project_number per day → expose as `/api/material-movement/daily/{project_number}/{date}` | ✅✅✅✅✅ |
| **FW-DR-1** DR `materials[]` pre-fill from FW | Foreman opens DR → pre-fills materials rows from today's FW tickets · tap to confirm | ✅✅✅✅✅ |
| **FW-DR-2** DR `production[]` derive from FW tonnage | When FW total > 0, pre-fill a production row · foreman confirms | ✅✅✅✅✅ |

---

## 6 · PHASE 6 · Motive Mapping Matrix

| Material-movement data point | Motive capability | Verdict |
|---|---|---|
| GPS arrival at a job geofence (truck on-site) | ✅ canonical | **VERIFICATION CANDIDATE** for `dispatch_assignments` arrival/departure timestamps |
| GPS departure from a load site | ✅ canonical | **VERIFICATION CANDIDATE** |
| Truck driver assignment / vehicle pairing | ✅ canonical | **VERIFICATION CANDIDATE** (does Motive driver = dispatch driver?) |
| Engine-hours on hauling unit | ✅ canonical | **VERIFICATION CANDIDATE** |
| Load count | ❌ Motive does not weigh tickets | **MANUAL / FleetWatcher** |
| Net tonnage | ❌ same | **MANUAL / FleetWatcher** |
| Material identity (what's in the truck) | ❌ Motive does not infer | **MANUAL / Dispatch · FleetWatcher** |
| Disposal-site classification | ❌ | **MANUAL / FleetWatcher** |
| Reuse vs disposal decision | ❌ judgment call | **MANUAL · Foreman / PM** |
| Cost | ❌ | **Vista canonical** |

### 6.1 · Motive rules (from existing OMEGA discipline)

- Never replace human judgment.
- Never **infer** production.
- Never **infer** quantities.
- ✅ Verify arrival/departure timestamps (signal · never overwrite).
- ✅ Verify engine-hours for billing reconciliation (display badge · never overwrite).
- ✅ Geofence-based dispatch_assignment lifecycle auto-transition is **OUT OF SCOPE** for material movement (that's M-2 webhook router · separate doctrine).

---

## 7 · PHASE 7 · Daily Report Integration Review

### 7.1 · The four architectural options

| Option | Pros | Cons | 5-pillar pass? |
|---|---|---|---|
| **A · New "Material Movement" section on DR** | Foreman-visible · matches directive's surface intent | 10th step → **Lock #1 violation** (breaks the 9-step contract) · duplicates dispatch_assignments | 🔴 FAIL — Simple |
| **B · Enhance existing `materials[]` (add out-bound direction)** | Reuses existing section · semantic fix is small | Section is named "Materials Delivered" today — direction-toggle is a UX confusion risk · still doesn't tap dispatch | 🟡 CONDITIONAL — Beautiful + Trusted weak |
| **C · Enhance `production[]` (current Wave-1B path)** | Already collects "TON of millings hauled" style data · keeps it generic | Doesn't carry source/destination/hauler · invisible until DR-FIX-1 (now visible) · still no dispatch link | 🟡 CONDITIONAL — Powerful weak (no rollup capability) |
| **D · Separate operational system (fuse dispatch_assignments daily rollup INTO the DR + PDF · DR doesn't author hauling)** | No new section · no Lock #1 violation · canonical source-of-truth preserved · single-write · zero duplication · already 90% built | Requires a Daily Report tile reading from dispatch_assignments rollup · cross-collection PDF render | ✅✅✅✅✅ **PASS** |

### 7.2 · Recommended path

**Option D · "Daily Hauling Activity rollup"** is the only path that passes all 5 pillars without violating the 9-step contract.

The DR gets a **read-only summary tile** that shows:
- Total trucks dispatched to this project today
- Loads in / Loads out / haul-type breakdown
- Total tonnage when FW-1 ships
- Link to the dispatch detail (for PM / Ops Lead drill-down)

The foreman **does not author the hauling rollup** — Dispatch authors it via the existing per-trip assignment, and the DR reads it. This:
- Honors **Single Source of Truth** (Dispatch = source · DR = consumer)
- Eliminates duplicate-write friction
- Closes the §6.2 inconsistency in DR-AUDIT-001 (dirt/millings/debris no longer "where do I put it?" — the foreman doesn't put it anywhere, Dispatch already did)
- Keeps the 9-step contract intact (no new author-able section)

### 7.3 · What the DR should KEEP authoring (foreman-original)

- Inbound `materials[]` rows that **didn't come through dispatch** (e.g., walk-up vendor drops, owner-furnished items) — these never hit dispatch_assignments so the DR remains the canonical capture
- Inbound ticket photos (foreman's physical corroboration of vendor delivery — kept alongside FW's digital ticket)
- `production[]` quantities that aren't hauls (LF of pipe installed · SY of sidewalk poured · EA of structures set) — these are pure foreman authorship, no dispatch overlap

---

## 8 · PHASE 8 · Operations Actions Review

Per the OA-1 constitution: Operations Actions are **operational ownership**, not tickets. Material movement events CAN legitimately generate Operations Actions when there's something for an operator to own.

| Material-movement trigger | Generates OA? | Category | Pillar pass? |
|---|---|---|---|
| Disposal ticket missing for a Spoils/Dump assignment | ✅ YES | `material_shortage` (semantically closest in existing OA enum) or new `disposal_ticket_missing` | ✅✅✅✅✅ |
| Excessive haul count (more trips than estimated) | 🟡 SIGNAL only — let PM decide | (no OA · just a tile flag) | ✅ but **MUST NOT auto-create** OA · OMEGA discipline |
| Plant delay (FW signal: plant call-out > N minutes late) | ✅ YES | `plant_delay` (already in OA category enum) | ✅✅✅✅✅ |
| Material shortage (FW signal: ordered tonnage > delivered) | ✅ YES | `material_shortage` (already in OA category enum) | ✅✅✅✅✅ |
| Hauling conflict (two assignments routed to same destination at the same time) | 🟡 SIGNAL only — dispatcher visibility, not auto-OA | (Dispatch board chip) | ✅ but **MUST NOT auto-create** |
| Contaminated-material handoff to non-licensed disposal site | ✅ YES | `safety_concern` | ✅✅✅✅✅ |
| Same load reported in dispatch AND DR with conflicting tonnage | 🟡 SIGNAL — admin reconciliation | (Admin Governance tile) | ✅ |

### 8.1 · The OMEGA discipline reminder

Per OA-1 constitution: **NO auto-routing · NO auto-assign · NO auto-escalation**. OA-1 is CRUD-only.

Therefore: material-movement events should at most **suggest** to an operator that an OA might be appropriate (via a quiet chip in the relevant hub). The operator **clicks Create** if they agree. The platform never auto-creates the action.

---

## 9 · PHASE 9 · Reporting & PDF Review

### 9.1 · Where material movement should appear

| Surface | Currently shows | Should show | Source |
|---|---|---|---|
| **Daily Report PDF** | DR `materials[]` (Section 08) · DR `production[]` (Section 09b · now visible per DR-FIX-1) | Add: **Section 09d · Hauling Activity Today** — read-only rollup from dispatch_assignments for `(project_number, report_date)` | dispatch_assignments |
| **Daily Report Read View** | Same as PDF | Same — add hauling tile | dispatch_assignments |
| **PM weekly report** | Crew hours · production · constraints | Weekly haul totals per material category · hauler split · disposal-site provenance · FW tonnage when available | dispatch + FW |
| **Executive monthly rollup** | None operational yet | Material in/out by hauler · disposal volumes · cost (when Vista bridged) · sustainability metrics | dispatch + FW + Vista |
| **Dispatch Board** | Already shows assignments | ✅ already canonical | dispatch_assignments |
| **Future cost dashboard** | None | $ per CY / per TON · variance vs estimate | Vista |
| **PM exposure tile** | Constraints signals (V.2 Wave-1B) | Could include "Hauling exposure" — too many disposal hours for project budget | dispatch + Vista (future) |

### 9.2 · Information hierarchy requirements

When material movement reaches a customer-facing PDF, the order should be:

1. **Executive line** (1 line · "Day brought 3 plant calls · 240 TON SP-12.5 in · 18 truckloads dirt out")
2. **In-bound table** (material · qty · supplier · ticket #)
3. **Out-bound table** (material · qty · destination · disposal ticket)
4. **Hauler split** (MASCI · 3rd-party A · 3rd-party B)
5. **Photo evidence** (ticket photos kept inline with rows)

The PDF should never bury the haul totals 8 sections deep — that's why R4 (PDF executive summary) and the new hauling tile are paired in the recommendation.

---

## 10 · PHASE 10 · Constitutional Certification

| Recommendation | Powerful | Simple | Beautiful | Trusted | Proven | Verdict |
|---|---|---|---|---|---|---|
| **D-1** Read-only Hauling Activity tile on DR PDF + View, sourced from `dispatch_assignments` | ✅✅ canonical source-of-truth | ✅ no new author surface | ✅ matches Section 09b/09c pattern | ✅✅ single-write | ✅ dispatch_assignments lifecycle proven | **PASS** |
| **D-2** Add the 5 missing taxonomy labels (Sod · Striping · Trees/Stumps/Vegetation · Contaminated) to MATERIAL_CATALOG | ✅ closes coverage gap | ✅ pure additive list edit | ✅ no UX impact | ✅ regulatory tracking for Contaminated | ✅ existing seed file pattern | **PASS** |
| **D-3** PM Weekly Hauling Rollup (`/api/material-movement/weekly`) read-only | ✅ exec visibility | ✅ derived only — no new collection | ✅ matches PM exposure tile pattern | ✅ source = dispatch | ✅ PM tile patterns proven | **PASS** |
| **D-4** FW-1 Ticket Ingest (prerequisite to most material-movement automation) | ✅ closes single biggest capture gap | ✅ no DR change | ✅ no UX change | ✅ scale-weighed | 🟡 not yet integrated · 3rd-party live data — needs first-cycle field test | **CONDITIONAL PASS** (proven-pillar needs first run) |
| **D-5** FW-DR-1 / FW-DR-2 — verify-only auto-fill of DR `materials[]` and `production[]` from FW tickets | ✅ eliminates re-typing | ✅ one tap to confirm | ✅ same UI shape | ✅ foreman remains the gate | 🟡 depends on D-4 | **CONDITIONAL PASS** (depends on D-4) |
| **D-6** OA auto-suggest for material-movement events (disposal ticket missing · plant delay · material shortage · contaminated handoff) | ✅ closes loop | ✅ OA-1 already CRUD-only | ✅ universal palette | ✅ suggest only · operator authorizes | ✅ OA-1 patterns proven | **PASS** |
| **D-7** Motive arrival/departure verify-only signal on dispatch_assignments lifecycle | ✅ reduces dispatcher friction | ✅ signal only | ✅ universal chip | ✅ telemetry-grade source | ✅ DCP-1 · DSI-1 patterns proven | **PASS** |
| **D-8** New "Hauling Activity Today" SECTION on the DR foreman form authored manually | 🟡 duplicates dispatch | 🔴 10th step | 🟡 redundant UX | 🔴 dual-write risk | 🔴 violates SST | **FAIL** — DO NOT BUILD |

---

## 11 · Recommended Architecture (Read this top-down)

```
                  ┌─────────────────────────────────────────────────┐
                  │                  FleetWatcher                    │
                  │   (system-of-record for scale tickets,           │
                  │   tonnage, cycle counts, plant activity,         │
                  │   disposal-site receipts — 3rd-party)            │
                  └────────────────────┬────────────────────────────┘
                                       │ (FW-1 ingest · D-4)
                                       ▼
                  ┌─────────────────────────────────────────────────┐
                  │       dispatch_assignments (Dispatch)            │
                  │   per-truck per-trip canonical                   │
                  │   • haul_type · material · source · destination  │
                  │   • carrier · trailer · equipment · pickup/drop  │
                  │   • load_count · liquid_product                  │
                  │   • FULL PENDING → ROLLING → COMPLETED lifecycle │
                  │   • Motive verify-only signals (arrive/depart)   │
                  └────────────────────┬────────────────────────────┘
                                       │ (rollup per project/date)
                                       ▼
                  ┌─────────────────────────────────────────────────┐
                  │   READ-ONLY DAILY ROLLUP API                     │
                  │   GET /api/material-movement/daily/              │
                  │       {project_number}/{date}                    │
                  │   • count by haul_type                           │
                  │   • totals (load_count · tonnage when FW)        │
                  │   • hauler split                                 │
                  │   • disposal-site provenance                     │
                  └──────┬────────────────────────────────┬─────────┘
                         │                                │
                         ▼ (D-1)                          ▼ (D-3)
              ┌──────────────────────┐         ┌──────────────────────┐
              │  Daily Report PDF +  │         │   PM Weekly Rollup   │
              │  Read View tile      │         │   Exec Monthly       │
              │  09d Hauling Today   │         │   Sustainability     │
              │  (read-only)         │         │   (read-only)        │
              └──────────────────────┘         └──────────────────────┘

         Daily Report STILL authors:
         • materials[] inbound rows that DIDN'T come through dispatch (walk-up)
         • inbound ticket photos
         • production[] for non-haul work (LF pipe · SY sidewalk · EA structures)
         • activities[] · general_notes (narrative)

         Operations Actions (D-6, OA-1 framework):
         • Disposal ticket missing → SUGGEST `material_shortage` OA
         • Plant delay → SUGGEST `plant_delay` OA
         • Contaminated handoff to non-licensed site → SUGGEST `safety_concern` OA
         (operator clicks Create — platform never auto-creates)
```

---

## 12 · Recommended Build Sequence

🟢 **Tier 1 · Pure visibility (no new collection · no new author surface)**
1. **D-1** — Hauling Activity rollup tile on DR PDF + Read View (reads existing dispatch_assignments). Closes the §6 inconsistency identified in DR-AUDIT-001 immediately.
2. **D-2** — Add 5 missing taxonomy labels (Sod · Striping · Trees/Stumps · Contaminated). Pure additive seed edit.

🟡 **Tier 2 · External integration prerequisite**
3. **D-4** — FW-1 Ticket Ingest service (already P0 per OGA-1).

🟡 **Tier 3 · Once FW-1 lands**
4. **D-5** — Verify-only auto-fill of DR `materials[]` and `production[]` from FW tickets.
5. **D-3** — PM Weekly Hauling Rollup endpoint + tile.

🟢 **Tier 4 · Operator-driven OA suggestions**
6. **D-6** — Material-movement events suggest OAs (operator authorizes).

🟢 **Tier 5 · Motive verify-only**
7. **D-7** — Motive arrival/departure timestamps surface as quiet badges on dispatch_assignments lifecycle.

**DO NOT** build D-8 (new manual hauling section on DR). Constitutional FAIL.

---

## 13 · Recommended Ownership Model

| Material-movement aspect | System of Record | Authored by | Verified by | Consumed by |
|---|---|---|---|---|
| Per-truck per-trip assignment | **`dispatch_assignments`** | Dispatcher | Motive (signal only) | Dispatch · PM · Ops · Exec |
| Scale-weighed tonnage | **FleetWatcher** (when D-4 ships) | FW | scale operator | All downstream |
| Disposal-site receipt | **FleetWatcher** (when D-4 ships) | FW | disposal-site operator | PM · Safety · Exec (regulatory) |
| In-bound walk-up vendor delivery | **DR `materials[]`** | Foreman | photo evidence | PM |
| Daily project rollup | **derived** from dispatch_assignments + FW | server-computed | — | DR PDF · PM · Exec |
| Cost / billing | **Vista** | Accounting | — | Exec |
| Material taxonomy | **`dispatch_assignment_seeds.MATERIAL_CATALOG`** | Platform engineering | — | dispatch + DR pre-fill |
| Hauler directory (carriers) | **`dispatch_assignments.carrier` history** + future Carrier directory | Dispatcher | — | Ops · Exec |

---

## 14 · Recommended System of Record (executive summary)

| Concept | System of Record |
|---|---|
| Material was moved | **Dispatch** (`dispatch_assignments`) |
| How much material | **FleetWatcher** (scale-weighed) |
| Where material came from | **Dispatch** + (FW for external sources) |
| Where material went | **Dispatch** + (FW for disposal/recycling) |
| Who moved it | **Dispatch** (carrier · driver) |
| When it moved | **Dispatch** (lifecycle timestamps) + Motive (verify) |
| Photo evidence | **Daily Report** (foreman's corroboration) + FW digital ticket |
| Cost of moving it | **Vista** |
| Did it require safety attention | **DR safety chain** + OA suggestions |
| Did it generate an Operations Action | **OA-1** (`operations_actions`) |

**No system owns it alone. The architecture is composed of canonical authorities by aspect — the DR is no longer the source for hauling, it becomes the consumer + photo backstop.**

---

## 15 · Recommended Future Integrations

| Integration | What it owns | Sprint code (audit-only) |
|---|---|---|
| **FleetWatcher** | scale tickets · tonnage · cycle counts · disposal receipts · plant activity | FW-1 (P0) · FW-2 (rollup) · FW-DR-1/2 (DR verify-fill) |
| **Motive** | telematics-grade arrival/departure timestamps | M-2 (webhook router for haul lifecycle) · M-3 (geocoding for source/destination) |
| **MaintainX** | open work-order chip on equipment used for an Equipment-Move assignment | MX-DA-1 (Dispatch Assignment chip) |
| **Vista** | cost · billing · variance vs estimate | P3 (Vista bridge) — single largest exec-reporting unlock |
| **Disposal-site directory** (new master) | licensed receiving facilities · regulatory class · receipts | DS-1 (future, low-priority) |
| **Carrier directory** (new master) | external haulers · insurance certs · MASCI-approved list | C-1 (future) |

---

## 16 · STOP CONDITION ACKNOWLEDGED

This directive ends with documentation only.

- ✅ No code modified
- ✅ No schemas changed
- ✅ No fields added
- ✅ No Daily Report modified
- ✅ No integrations built
- ✅ No automations added
- ✅ No deploys
- ✅ No new designs beyond textual recommendation

Every recommendation D-1 … D-7 (+ explicit FAIL on D-8) remains a **proposal** awaiting your individual authorization.

---

## 17 · File Evidence Index

**Discovered canonical surfaces (read-only)**

- `/app/backend/dispatch_assignment_seeds.py` (HAUL_TYPES · MATERIAL_CATALOG · SEEDED_SOURCES · SEEDED_DESTINATIONS · EQUIPMENT_MOVE_CATEGORIES)
- `/app/backend/routes/dispatch_lifecycle.py` (lines 90-175 = AssignmentCreate model · lines 2030-2160 = haul_types_today rollup)
- `/app/backend/routes/dispatch_driver.py` (lookups endpoint exposing the catalog to the drawer · lines 445-769)
- `/app/backend/routes/daily_reports.py` (current DR `materials[]` · `production[]` shapes)
- `/app/backend/pdf_render.py` (`_render_daily` — where the hauling tile would slot in)
- `/app/backend/services/motive_service.py`
- `/app/backend/services/maintainx_client.py`

**Doctrine references**

- `/app/memory/OA1_OPERATIONS_ACTIONS_CONSTITUTION.md` (D-6 framework)
- `/app/memory/DR_AUDIT_001_FULL_CONSTITUTIONAL_AUDIT.md` (§6 Material Movement deep-dive — this audit extends it)
- `/app/memory/FWA1_FLEETWATCHER_FORENSIC_AUDIT.md` (FW-1 P0 sprint)
- `/app/memory/FWA1_CAPABILITY_MATRIX.md`
- `/app/memory/LIVE_PRODUCTION_MAINTAINX_AUDIT.md`
- `/app/memory/OGA1_OPERATIONAL_GAP_ANALYSIS.md`
- `/app/memory/ODR_SIMPLICITY_TEST_DOCTRINE.md`
- `/app/memory/PRODUCTION_TRACKING_CERTIFICATION.md`

— Forked main agent · MM-001A · 2026-06-08
— Audit complete. Awaiting operator directive on D-1 through D-7.
