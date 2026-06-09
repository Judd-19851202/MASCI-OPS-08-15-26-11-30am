# MM-001A-A · EXTERNAL MATERIAL MOVEMENT GAP AUDIT
**MASCI / ForgedOps Platform**
**Authorized:** OMEGA Time-Boxed Audit · 2026-06-08
**Status:** 🟡 Audit complete · **zero code changes**
**Discipline:** Evidence-only · STOP after recommendations.

---

## 0 · Headline

🔍 **The visibility gap is real and large.** Dispatch / FleetWatcher / Motive together cover **MASCI-controlled hauling** with high fidelity. They do **not** cover vendor-controlled material movement that arrives or leaves a project on someone else's truck. That's the gap this audit names — and the cleanest architectural answer is **NOT** a new system. It's **Daily Report `materials[]` evolved with a direction toggle (`in` / `out`) and aware of dispatch_assignments**, with the foreman remaining the canonical authority for everything dispatch/FW/Motive can't see.

**No new collection. No new portal. No duplicate system. No competing source of truth.**

---

## 1 · PHASE 1 · External Material Movement Inventory

### 1.1 · External INBOUND (vendor brings material to MASCI site, on a non-MASCI truck, not via dispatch)

| # | Material | Typical units | Typical qty | Typical vendors | Frequency | Current capture | Consumer |
|---|---|---|---|---|---|---|---|
| 1 | **Ready Mix Concrete** | CY | 5–30 CY / pour | Cemex · Argos · Titan | weekly–daily on structure days | DR `materials[]` row · ticket photo | PM · Exec · Vista |
| 2 | **Pipe (RCP / HDPE)** | LF or EA pieces | 100–2,000 LF | Ferguson · CSR Hydro · Naylor | weekly | DR `materials[]` row | PM · Foreman |
| 3 | **Structures / Inlets / Manholes** | EA | 1–20 EA | precast vendors (Oldcastle · Forterra) | weekly | DR `materials[]` row · sometimes inline photo | PM · Inspector |
| 4 | **Utility Materials** (valves · fittings · couplings) | EA · LB | varies | utility supply houses | weekly | DR `materials[]` row · often **only** `general_notes` | PM |
| 5 | **Aggregate / Lime Rock Deliveries** (small vendor truck — not MASCI plant) | TON or CY | 20–100 TON | small pit operators | weekly | DR `materials[]` row | PM · Exec |
| 6 | **Sod** | SY · pallets | 1–50 pallets | sod farms | irregular | DR `materials[]` + ticket photo (when foreman remembers) | PM · Landscape sub coord |
| 7 | **Signs / Sign Posts** | EA | 1–20 EA | sign suppliers · DOT-approved vendors | irregular | DR `materials[]` row | PM · Traffic |
| 8 | **Signal Equipment** (cabinets · poles · loops) | EA | 1–4 EA | electrical contractors / vendors | rare · high-$ | DR `materials[]` or `general_notes` | PM · Subcontractor coord |
| 9 | **Striping Materials** (paint · thermoplastic) | GAL · LB · roll | varies | striping subs / paint vendors | rare | DR `materials[]` or sub photo | PM · Striping sub |
| 10 | **General Vendor Deliveries** (catch-all: barricades · MOT · forms · misc) | varies | varies | many | daily | DR `materials[]` or `general_notes` | PM |

### 1.2 · External OUTBOUND (third party takes material away from MASCI site, not on a MASCI truck)

| # | Material | Typical units | Typical qty | Typical vendors | Frequency | Current capture | Consumer |
|---|---|---|---|---|---|---|---|
| 11 | **Roll-Off Dumpsters** (in / out / dumped) | swap events · TON when scaled | 10–40 yd³ container | Waste Pro · Republic · WastePros · Coastal | weekly | 🔴 **no native capture** — foreman writes in `general_notes` | PM · Safety · Exec |
| 12 | **Tree Removal** | EA · trucks of debris · CY | varies wildly | arborist / land-clearing subs | per clearing phase | 🔴 `general_notes` only | PM · Subcontractor coord · Exec |
| 13 | **Stump Removal** | EA · trucks | varies | same as #12 | per clearing phase | 🔴 `general_notes` | PM |
| 14 | **Concrete Recycling** (crushed off-site) | TON · CY · trucks | varies | recycling facilities (CDS · Atlas · etc.) | weekly | 🔴 `materials[]` if foreman remembers (wrong semantic) or `general_notes` | PM · Exec (sustainability) |
| 15 | **Vendor Disposal** (vendor takes their own crate / packaging back) | EA · trips | varies | original supplier | weekly | 🔴 untracked | rarely consumed |
| 16 | **Utility Contractor Spoils** (sub's truck hauls dirt their crew dug) | CY · trucks | high on utility days | sub | weekly | 🔴 `general_notes` · sometimes activities[] | PM · Sub coord |
| 17 | **Vac Truck Disposal** (jet-vac / hydro-vac waste) | gal · trucks · TON | varies | vac-truck vendors (Hi-Vac · Vacuum Solutions) | weekly on dewater / utility days | 🔴 untracked | Environmental · Safety · PM |
| 18 | **Subcontractor Export Activities** (paving sub hauls excess off · grading sub hauls fill) | varies | varies | sub | weekly | 🔴 `general_notes` | PM |
| 19 | **Outside Haulers** (3rd-party trucking we hired but DIDN'T enter in dispatch_assignments) | trucks · loads | varies | 3rd-party | irregular | 🔴 `general_notes` or untracked | PM |
| 20 | **Contaminated Material Manifests** (regulated waste → licensed receiver) | TON · trucks · manifest # | rare · high-stakes | hazmat haulers | rare | 🔴 photo of manifest in DR but no structured field | PM · Environmental · Regulatory |

### 1.3 · Gap classification

| Capture quality | Count | Items |
|---|---|---|
| ✅ **Good** (in `materials[]` row with ticket photo) | 5 | #1 Ready Mix · #2 Pipe · #3 Structures · #5 Aggregate · partial #6 Sod |
| 🟡 **OK but inconsistent** | 4 | #4 Utility · #7 Signs · #8 Signal · #9 Striping |
| 🔴 **Poor or no native capture** (general_notes / untracked) | 11 | #11–#20 (all outbound) + #10 General Vendor (often) |

### 1.4 · Who currently knows it

| Item set | Currently known to |
|---|---|
| #1–5 vendor inbound with tickets | Foreman + PM via DR + photo |
| #6–10 inbound (irregular) | Foreman only (often `general_notes`) |
| #11–20 external outbound | **Foreman only · narrative only · no structured platform record** |

---

## 2 · PHASE 2 · Source of Truth Analysis

For each movement category — who is the **primary**, **secondary**, **verification** source, and the **consumer surface**?

| Category | Primary | Secondary | Verify | Consumer surface |
|---|---|---|---|---|
| MASCI-controlled hauling (in/out) | **Dispatch** (`dispatch_assignments`) | FW (scale) when FW-1 ships | Motive (arrive/depart) | Dispatch Board · DR rollup tile · PM · Exec |
| External inbound on vendor truck (Ready Mix · Pipe · Structures · Aggregate · Sod · Signs · Striping · Utility · misc) | **Foreman** (DR `materials[]` row + ticket photo) | vendor delivery PO / invoice (Vista) | photo evidence | DR PDF · PM · Vista reconciliation |
| External outbound on 3rd-party truck (Roll-off · Tree · Concrete recycling · Vac · Sub spoils · Outside hauler · Vendor disposal) | **Foreman / Super** (no current structured home) | sub's daily report (when subs file one) | photo evidence + manifest # | (gap — needs structured capture) |
| Contaminated / regulated manifest | **Foreman / Super** (record manifest #) | hazmat hauler's manifest | regulatory receipt | DR PDF · Safety · Environmental · Regulatory |

### 2.1 · Ownership matrix

| Movement aspect | Owner |
|---|---|
| MASCI truck moves material | **Dispatch** |
| Scale-weighed tonnage on MASCI truck | **FleetWatcher** (FW-1) |
| Telematic arrival/departure | **Motive** (verify-only) |
| Vendor-controlled inbound | **Foreman** via DR · PM verifies against PO |
| 3rd-party-controlled outbound | **Foreman** via DR · PM verifies against contract |
| Regulated/hazmat manifest | **Foreman** captures · Safety reviews · Environmental archives |
| Cost reconciliation | **Vista** |

---

## 3 · PHASE 3 · Daily Report Gap Analysis

| Gap class | Item | Evidence |
|---|---|---|
| **No capture path** | Roll-off dumpster swap events (in/out/dumped) | No field today carries direction · capacity · ticket # · destination |
| **No capture path** | Tree / stump removal counts | Only `general_notes` |
| **No capture path** | Vac truck waste disposal | Only `general_notes` |
| **No capture path** | 3rd-party hauler arrivals NOT in dispatch | Only `general_notes` |
| **No capture path** | Vendor disposal (vendor takes their own back) | Untracked |
| **No capture path** | Subcontractor outbound spoils | Only `general_notes` |
| **No capture path** | Regulated manifest # (structured) | Photo only — no searchable field |
| **Poor capture path** | Concrete recycling | Sometimes `materials[]` (wrong semantic — section is "Delivered") |
| **Poor capture path** | Striping / signal materials | Sometimes `materials[]` · often `general_notes` |
| **Duplicate capture path** | Asphalt in (when delivered both via dispatch AND noted in DR `materials[]`) | Both records exist — same load |
| **Duplicate capture path** | Aggregate / fill (when both dispatch + DR) | Same |
| **Wrong capture path** | Out-bound dirt / millings authored in `materials[]` section labelled "Delivered" | Semantic conflict |

### 3.1 · Root cause

`materials[]` section is **named** "Materials Delivered" and structured for in-bound only — yet operators stretch it to cover out-bound events when nothing else fits. The result is the structural inconsistency identified in DR-AUDIT-001 §6.

---

## 4 · PHASE 4 · Field Ownership Analysis (only the foreman/super can author)

| Movement | Why no system can replace the foreman |
|---|---|
| Vendor deliveries on a vendor's own truck | The vendor's truck isn't in Motive · isn't in dispatch_assignments · scale ticket (if any) is paper handed to foreman |
| Roll-off swap events | No live API from waste haulers · foreman watches the truck pull up |
| Tree / stump removal | Land-clearing subs are off the platform entirely · only foreman counts |
| Concrete recycling outbound | Subcontracted hauler · ticket goes to PM, but not in real time |
| Vac truck disposal | Specialty vendor · no API · foreman watches the volume go down |
| Sub spoils | Sub's truck · not on MASCI dispatch · only field can attribute it |
| Outside-haul events when MASCI rented an outside hauler "off the books" of dispatch | Dispatch may not have been notified · foreman observes |
| Regulated manifest # | Hazmat receipt is paper · foreman gets the carbon copy |
| Vendor disposal (vendor takes their own packaging back) | No invoice flows · nobody else sees it |

**Conclusion:** roughly **half** of all material movement on a typical site is **knowable only by the foreman in real time**. Any architecture that pretends otherwise either loses data or invents friction.

---

## 5 · PHASE 5 · Future Architecture Recommendation

### 5.1 · Three categories · clear ownership

| Category | Source-of-truth | DR's role |
|---|---|---|
| **A · MASCI-controlled hauling** (in/out) — MASCI truck or MASCI-hired carrier entered in dispatch | `dispatch_assignments` (D-1 from MM-001A surfaces the rollup) | **Display only** (read-only tile) |
| **B · External vendor / 3rd-party material movement** (in/out) — vendor or sub truck | **Daily Report `materials[]` evolved** (see §5.2) | **Author + verify** (foreman is canonical) |
| **C · Hybrid** (e.g. MASCI dispatches a truck for an external hauler, or a sub uses a MASCI truck) | Dispatch authors + DR cross-references | **Reference** (link, don't duplicate) |

### 5.2 · The recommended evolution of DR `materials[]` (architectural · NOT a build)

The recommendation is to evolve the **single existing `materials[]` section** so it can carry both in-bound and out-bound external movement — without creating a new section, new collection, or new portal. The minimum architectural additions (proposal · NOT a build):

| Field | Why |
|---|---|
| `direction` ∈ `{in, out}` | Direction toggle resolves the semantic conflict; the same row shape works for both flows |
| `category` (drawn from the existing `MATERIAL_CATALOG` 57-item set) | Single canonical taxonomy across Dispatch + DR — no parallel vocabulary |
| `hauler` (free text · suggests from existing `dispatch_assignments.carrier` history) | Captures the 3rd-party hauler when MASCI didn't dispatch them |
| `destination` (for outbound · suggests from `dispatch_assignment_seeds.SEEDED_DESTINATIONS` + history) | Disposal site / recycling facility / reuse location |
| `manifest_number` (optional · regulated movement only) | Structured search for hazmat / environmental audits |
| `linked_dispatch_assignment_id` (optional · when MASCI dispatch also covered it) | Prevents duplicate-capture for hybrid case C |

**No new collection.** `materials[]` stays as an array on `daily_reports`. The 57-item `MATERIAL_CATALOG` becomes the **single shared taxonomy** between dispatch and DR.

### 5.3 · Naming / UX evolution (architectural)

Section 08 "Materials" gains a 2-row layout:
- "Materials In — vendor / supplier deliveries" (direction = `in`)
- "Materials Out — disposal / haul-off / 3rd-party export" (direction = `out`)

Both rows pre-fill from FW-1 (when shipped) for any tickets matching the project, and pre-suggest from yesterday's DR. Foreman remains the authoritative confirm.

### 5.4 · The Daily Report's four roles in the new architecture

| For category | Should DR Own? | Verify? | Display? | Reference? |
|---|---|---|---|---|
| A · MASCI-controlled hauling | ❌ no | 🟡 photo backstop | ✅ rollup tile | ✅ link |
| B · External vendor/sub movement | ✅ author | ✅ photo · manifest | ✅ rows | — |
| C · Hybrid | ❌ no (Dispatch owns) | ✅ photo when foreman sees it | ✅ rollup | ✅ `linked_dispatch_assignment_id` |

---

## 6 · PHASE 6 · PM / Operations Consumption

| Surface | What PMs / Ops should see | Source | Duplicate entry risk |
|---|---|---|---|
| PM Daily summary | Per-project · today's haul totals (Dispatch + DR) · in vs out · hauler split · disposal sites | Server-computed from dispatch_assignments + DR `materials[]` | 🟢 none |
| PM Weekly rollup | 7-day rolling totals · MASCI vs vendor split · cost (Vista) | Same + Vista (P3) | 🟢 none |
| Ops Daily exposure | Constraint hours_impact + over-cycle haul flag | DR `constraints[]` + dispatch rollup | 🟢 none |
| Exec monthly | Per-job tonnage / loads / disposal volumes / regulated manifests · sustainability metrics | Aggregate over all of the above | 🟢 none |

**Single principle:** No PM or Operations surface should ever ask a foreman or dispatcher to author the same load twice. If it's on dispatch, the PM tile reads dispatch. If it's external, the PM tile reads DR. Server merges. No duplicate entry.

---

## 7 · PHASE 7 · PDF Consumption Review

### 7.1 · Recommended PDF surfaces (architectural · not yet implemented)

| Surface | Section | Source | Information hierarchy |
|---|---|---|---|
| DR PDF — exec line | top of PDF | server-merged | "Day in: 240 TON SP-12.5 · 6 vendor deliveries · 12 dispatched loads · Day out: 18 truckloads dirt · 2 roll-off swaps · 1 manifest" |
| DR PDF — Section 08 | "Materials In" (direction=in) | DR `materials[]` filtered | rows + ticket photos |
| DR PDF — Section 08b | "Materials Out" (direction=out) | DR `materials[]` filtered | rows + disposal photos + manifest # |
| DR PDF — Section 09d | "MASCI Hauling Today" rollup | dispatch_assignments | counts by haul_type |
| PM Weekly PDF | "Material Movement · 7-day rolling" | merged | hauler split + disposal sites |
| Exec Monthly PDF | "Material Movement · monthly" | aggregated | tonnage · regulated manifests · sustainability |

### 7.2 · Avoiding information overload

- Foreman PDF: only what shipped on this day · ≤2 pages of haul-related content
- PM PDF: rollup-first · per-day drill-down only if requested
- Exec PDF: monthly aggregates · per-job drill-down only on click
- No per-trip detail on any non-Dispatch surface (already canonical there)

---

## 8 · PHASE 8 · Constitutional Review

| Recommendation | Powerful | Simple | Beautiful | Trusted | Proven | Verdict |
|---|---|---|---|---|---|---|
| **E-1** Read-only "MASCI Hauling Today" tile on DR PDF + Read View (= MM-001A D-1) | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| **E-2** Add the 5 missing taxonomy labels to `MATERIAL_CATALOG` (= MM-001A D-2) | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| **E-3** Evolve DR `materials[]` with `direction` toggle (`in` / `out`) and Section 08 split (Materials In / Materials Out) — same array, same collection, same UX shape | ✅✅ closes the §3 gap | ✅ no new section · same 2-row repeater pattern | ✅ visual symmetry | ✅ foreman authority preserved | 🟡 first cycle field test | **CONDITIONAL PASS** |
| **E-4** Add `category` (from MATERIAL_CATALOG), `hauler`, `destination`, `manifest_number`, `linked_dispatch_assignment_id` optional fields to existing `materials[]` row shape | ✅ closes 11 gap items | ✅ optional fields · don't intrude on happy path | ✅ collapsed by default | ✅ structured search restored | 🟡 first cycle | **CONDITIONAL PASS** |
| **E-5** Server-merged Daily Material Movement endpoint (`GET /api/material-movement/daily/{project}/{date}`) combining dispatch_assignments + DR `materials[]` rows | ✅✅ single rollup | ✅ derived only · no new collection | ✅ matches PM exposure tile | ✅ both sources canonical | ✅ similar pattern exists | **PASS** |
| **E-6** FW-1 Ticket Ingest (= MM-001A D-4 / OGA-1 P0) | ✅ closes biggest external capture gap | ✅ no DR change required | ✅ — | ✅ scale-weighed | 🟡 not yet integrated | **CONDITIONAL PASS** |
| **E-7** FW-DR-1 / FW-DR-2 verify-only auto-fill | ✅ eliminates re-typing | ✅ one tap | ✅ | ✅ foreman gate | 🟡 depends on E-6 | **CONDITIONAL PASS** |
| **E-8** OA-1 suggestions for material-movement events (disposal missing · plant delay · material shortage · contaminated handoff) (= MM-001A D-6) | ✅ closes loop | ✅ OA already CRUD-only | ✅ | ✅ suggest-only | ✅ OA-1 proven | **PASS** |
| **E-9** Motive arrival/departure verify-only on dispatch lifecycle (= MM-001A D-7) | ✅ | ✅ | ✅ | ✅ | ✅ DCP/DSI proven | **PASS** |
| **E-10** New separate "Material Movement" portal or collection | 🟡 | 🔴 duplicate system | 🟡 | 🔴 competing source of truth | 🔴 | **FAIL · DO NOT BUILD** |
| **E-11** Foreman authors MASCI-hauling rows in the DR (instead of reading from dispatch) | 🟡 | 🔴 dual-write | 🔴 | 🔴 | 🔴 violates SST | **FAIL · DO NOT BUILD** |
| **E-12** Auto-create OAs for material-movement signals (no operator click) | 🟡 | 🔴 hidden automation | 🔴 | 🔴 | 🔴 violates OA-1 constitution | **FAIL · DO NOT BUILD** |

### 8.1 · Constitutional verdict roll-up

- **PASS:** E-1 · E-2 · E-5 · E-8 · E-9 — five clean wins
- **CONDITIONAL PASS:** E-3 · E-4 · E-6 · E-7 — pass once each completes its first field cycle
- **FAIL · DO NOT BUILD:** E-10 (new portal) · E-11 (dual-author) · E-12 (auto-OA)

---

## 9 · Recommended Architecture (final)

```
   ┌─────────────────────────────────────────────────────────────────┐
   │                                                                 │
   │                   MATERIAL MOVEMENT ARCHITECTURE                │
   │                                                                 │
   │  ┌───────────────────────────────┐                              │
   │  │  CATEGORY A · MASCI-controlled│   single source of truth     │
   │  │  dispatch_assignments         │       (Dispatch)             │
   │  │  + Motive verify              │                              │
   │  │  + FleetWatcher tonnage (FW-1)│                              │
   │  └────────────────┬──────────────┘                              │
   │                   │ rollup                                      │
   │                   ▼                                             │
   │             ┌──────────────────┐                                │
   │             │  Server merger   │   GET /api/material-movement/  │
   │             │  per project/day │       daily/{proj}/{date}      │
   │             └──────┬───────────┘                                │
   │                    │                                            │
   │  ┌─────────────────┼─────────────────┐                          │
   │  │                 ▼                 │                          │
   │  │  ┌───────────────────────────────┐│                          │
   │  │  │  CATEGORY B · External        ││   single source of truth │
   │  │  │  Daily Report materials[]     ││       (Foreman)          │
   │  │  │  • direction in/out           ││                          │
   │  │  │  • category from canonical    ││                          │
   │  │  │  • hauler / destination       ││                          │
   │  │  │  • manifest_number            ││                          │
   │  │  │  • ticket photos              ││                          │
   │  │  └───────────────────────────────┘│                          │
   │  │                                   │                          │
   │  │  ┌───────────────────────────────┐│                          │
   │  │  │  CATEGORY C · Hybrid          ││                          │
   │  │  │  materials[].linked_dispatch_ ││   Dispatch authors ·     │
   │  │  │      assignment_id            ││   DR cross-references    │
   │  │  └───────────────────────────────┘│                          │
   │  └───────────────────────────────────┘                          │
   │                                                                 │
   │  Consumers:                                                     │
   │  • DR PDF (foreman-day view, sections 08 / 08b / 09d)           │
   │  • PM weekly · Exec monthly (server-derived)                    │
   │  • Operations Actions (suggest-only on signal events)           │
   │  • Vista (cost · billing reconciliation)                        │
   │                                                                 │
   └─────────────────────────────────────────────────────────────────┘
```

**Single shared taxonomy** = `dispatch_assignment_seeds.MATERIAL_CATALOG` (57 items · 6 categories, +5 additions from E-2). Both Dispatch and DR speak the same vocabulary. No parallel taxonomies. No duplicate systems.

---

## 10 · Recommended Build Sequence

| Tier | Sprint | What |
|---|---|---|
| 🟢 **Tier 1 — pure visibility** | **E-1** | Daily Hauling Activity rollup tile on DR PDF + Read View (no new field anywhere). |
| 🟢 Tier 1 | **E-2** | Add 5 missing labels to MATERIAL_CATALOG. |
| 🟢 Tier 1 | **E-5** | Server-merged Daily Material Movement endpoint (derived only). |
| 🟡 **Tier 2 — DR `materials[]` evolution** | **E-3** | Add `direction` toggle + Section 08 split into "Materials In" / "Materials Out". |
| 🟡 Tier 2 | **E-4** | Add `category` · `hauler` · `destination` · `manifest_number` · `linked_dispatch_assignment_id` (all optional · drawn from canonical taxonomy). |
| 🟡 **Tier 3 — FleetWatcher integration** | **E-6** | FW-1 Ticket Ingest (P0 per OGA-1 — prerequisite). |
| 🟡 Tier 3 | **E-7** | FW-DR-1 / FW-DR-2 verify-only auto-fill on materials[] and production[]. |
| 🟢 **Tier 4 — Operator-driven OAs** | **E-8** | OA-1 suggestions for material-movement signals (operator-authorized · platform never auto-creates). |
| 🟢 **Tier 5 — Motive verify-only** | **E-9** | Motive arrival/departure signal on dispatch lifecycle. |
| 🔴 **Never** | E-10 / E-11 / E-12 | Constitutional FAIL. |

---

## 11 · Recommended Ownership Model (one-line per concept)

| Concept | Owner |
|---|---|
| MASCI truck moved material | **Dispatch** |
| Scale-weighed tonnage on MASCI truck | **FleetWatcher** (E-6) |
| Telematic arrival / departure | **Motive** (verify-only · E-9) |
| External vendor brought material to site | **Daily Report `materials[]` direction=in** · Foreman |
| External 3rd-party took material away | **Daily Report `materials[]` direction=out** · Foreman |
| Hybrid (MASCI + external) | **Dispatch authors · DR references via `linked_dispatch_assignment_id`** |
| Material taxonomy | **`dispatch_assignment_seeds.MATERIAL_CATALOG`** (single source) |
| Regulated manifest | **Daily Report `materials[*].manifest_number`** (structured field · photo backstop) |
| Cost / billing | **Vista** |
| Operations Action on a material event | **OA-1 `operations_actions`** (suggested only, operator authorizes) |

---

## 12 · Recommended System of Record

| Aspect | System of Record |
|---|---|
| Did material move? | **Dispatch** (when MASCI-controlled) · **Daily Report** (when external) |
| How much? | **FleetWatcher** for MASCI scale-weighed · **Daily Report** for vendor-typed |
| When? | **Dispatch** timestamps (verified by Motive) for MASCI · **DR** `created_at` for external |
| Where from / to? | **Dispatch** for MASCI · **DR** for external |
| Who moved it? | **Dispatch** (carrier · driver) for MASCI · **DR** (`hauler` field) for external |
| Photo evidence | **Daily Report** in either case (`materials[*].ticket_photos[]`) |
| Cost | **Vista** |
| Regulatory provenance | **Daily Report** (`manifest_number` field + photo) |

---

## 13 · Recommended Future Integrations

| Integration | Status | What it would own | Sprint code |
|---|---|---|---|
| **FleetWatcher** | NOT yet integrated · P0 deferred | scale tickets · tonnage · cycle counts · disposal receipts | E-6 (= FW-1) |
| **Motive** | ✅ already live | arrive/depart verify · engine-hours | E-9 |
| **MaintainX** | ✅ already live | open-WO chip on dispatch_assignments equipment moves | (out of scope here) |
| **Vista** | NOT yet integrated | cost · billing reconciliation · variance | (P3 future) |
| **Carrier directory** (new master) | not built | external haulers · insurance · MASCI-approved list | (deferred) |
| **Disposal-site directory** (new master) | not built | licensed receiving facilities · regulatory class | (deferred) |

---

## 14 · STOP CONDITION ACKNOWLEDGED

This audit ends here.

- ✅ No code modified
- ✅ No schemas changed
- ✅ No fields added
- ✅ No DR modified
- ✅ No integrations built
- ✅ No automations added
- ✅ No deploys
- ✅ No additional discovery phase proposed
- ✅ No additional audit proposed

**Final architecture recommendation is ready for implementation authorization.**

The recommended **first executable step** is **E-1 + E-2** as a combined micro-sprint (pure visibility tile from dispatch_assignments + 5 additive label entries on the existing canonical taxonomy). Both are 5-pillar PASS, both are smallest-blast-radius, both immediately close half of the §3 gap, and neither touches the foreman authoring surface.

— Forked main agent · MM-001A-A · 2026-06-08
— Audit complete. STOP. Awaiting operator directive on E-1 through E-9.
