# Fleet Operations Foundation · iter251 Architecture
*Authored: 2026-05-19 · Status: PROPOSAL (operator-approval gate before any code)*

This is an architecture document, not an implementation. Nothing in this file ships
until you explicitly approve it phase-by-phase, mirroring the iter248 Legacy Records
delivery cadence.

---

## 1. Operational Context (verified against the live codebase, not assumed)

The platform already has stronger fleet foundations than you may realise.
This proposal is a **thin operational layer on top of proven infrastructure**, not a
greenfield system.

| Asset | Status today | iter251 usage |
|---|---|---|
| `equipment_master` collection | 589 units · already categorized · includes 41 Dump Trucks, 53 Trailers, 12 Tractor-Trailer Trucks, 17 Service Trucks, 11 Pickup Trucks, 6 Water Trucks, 3 Flatbed Trucks, 4 Misc Trucks, 2 Supv/Mgmt Trucks · ~149 fleet units total | **Reuse as-is** — no schema change, no migration |
| `equipment_inspections` collection | Battle-tested Pre-Op schema (`checklist` dict, `fail_count`, `out_of_service: "Yes"\|"No"`, photos, signatures, OOS modal stop-work UX) | **Reuse with an added `kind` field** (`pre_op` / `dvir` / `weekly_lead` / `weekly_emergency`) — single discriminator, zero collection sprawl |
| `checklists.py` (738 lines) | Holds Pre-Op item lists per equipment type | Extend with FMCSA-aligned DVIR sections — same module, same generator pattern |
| Dispatch portal (`/dispatch`) | Hub + login + RBAC already in place · already owns daily-report-read scope, dispatch utilization views | Receives **fleet status board** as a new section |
| Shop portal (`/shop`) | Hub + login + `shop_parts.py` route · operational mechanic console | Receives **active-defects board** as a new section |
| Safety dashboard | Already aggregates safety-critical signals | Receives **emergency-equipment failure alerts** as a new feed item |
| Public tile pattern | `Hub.jsx` Section 1 "Today in the Field" has 3 tiles (Field · QA/QC · Safety) | Add a 4th tile: **Trucking / Fleet Ops** |
| `PhotoUpload` widget | Mobile-first, iOS-Safari-fixed, compress+progress | Reused as-is for defect photos |
| RBAC infra | Mature: portal-scoped tokens, anon-blocked endpoints, audit on writes | Reused as-is |

**Implication**: ~70% of what you described already exists. We are adding workflow
discipline + DVIR checklists + defect lifecycle, not platform plumbing.

---

## 2. Operational Architecture Proposal

### 2.1 Collections (NEW = 2 only)

```
equipment_master              ← REUSE (no schema change)
equipment_inspections         ← REUSE + add `kind` discriminator field
fleet_defects                 ← NEW · defect lifecycle (open → repaired/cleared)
fleet_status                  ← NEW · 1 row per truck/trailer · derived current state
```

**`fleet_defects`** is the single source of truth for defect visibility. Every
failed checklist item produces a `fleet_defects` row at submission time. Status
flows `open` → `acknowledged` → `repaired` → `cleared`. Repair lifecycle lives
here in MASCI OPS as a thin visibility layer; **deep repair management is
explicitly deferred to MaintainX integration** (we surface the right identifiers,
we don't recreate MaintainX).

**`fleet_status`** is a derived projection — one document per fleet unit holding
the current state (`available` · `oos` · `defect_open` · `out_of_service_reason`,
plus refs to latest DVIR, oldest open defect, mileage, hours). Rebuilt on every
inspection submission. Lets the Dispatch board read 149 units in one query
instead of joining inspections + defects per render.

**Why two NEW collections, not zero**: defects need their own document because
their lifecycle (open/repaired) is independent of the inspection that created
them, and we need a single normalized place to query "all open OOS items right
now". Trying to keep this in `equipment_inspections.checklist` would force every
Dispatch board render to scan every historical inspection — operationally
unworkable past 90 days.

### 2.2 Identifier Strategy (Motive + MaintainX integration-ready)

Every fleet entity carries clean canonical identifiers that map to external
systems later — but iter251 does **NOT** implement any integration sync.

```
truck_unit_number     : str  · canonical · e.g. "MGC-447"   (already in equipment_master)
trailer_unit_number   : str  · canonical · e.g. "TR-203"
vin                   : str  · already in equipment_master.vin_serial_number
license_plate         : str  · already in equipment_master.plate
driver_employee_id    : str  · references db.employees.id (canonical)
inspection_id         : str  · uuid4 · prefixed DVIR-YYYY-NNNNN for human display
defect_id             : str  · uuid4 · prefixed DEF-YYYY-NNNNN
external_refs         : {motive_id, maintainx_work_order_id}  ← reserved · empty in iter251
```

**Future Motive integration**: `vin` + `truck_unit_number` are stable enough to map
to Motive's vehicle records. We will NOT call any Motive API in iter251.

**Future MaintainX integration**: each `fleet_defects` row reserves
`external_refs.maintainx_work_order_id`. When MaintainX is wired in, a defect can
be linked to a work order with a single field write. No schema migration needed.

### 2.3 Why this is NOT a TMS / fleet ERP / telematics

| Operator boundary | iter251 stance |
|---|---|
| ELD / HOS / DOT logs | NOT BUILT |
| Sleeper / interstate carrier workflows | NOT BUILT |
| GPS / telematics / dashcams | Owned by Motive (future · not iter251) |
| Route optimization | NOT BUILT |
| Maintenance ERP / work orders / parts / labor | Owned by MaintainX (future · not iter251) |
| Fuel systems | NOT BUILT |
| AI dispatch | NOT BUILT |
| Carrier-scale TMS | NOT BUILT |

We ship: **DVIR · weekly lead driver · weekly emergency equipment · defect
visibility · OOS control · audit history**. That's it.

---

## 3. Workflow Proposal

### 3.1 Daily DVIR (Pre-Trip)

Driver opens `/fleet` public tile → "Daily DVIR" → picks truck (searchable
combobox over equipment_master where `category` ∈ {Dump Trucks, Tractor Trailer
Trucks, Service Trucks, Pickup Trucks, Flatbed Trucks, Water Trucks, Misc
Trucks, Supervisor/Mgmt Trucks}) → optionally picks **one or more trailers** →
fills FMCSA-aligned checklist → captures defect photos per failed item →
signs → submits.

On submit:
1. `equipment_inspections` row written (`kind="dvir"`)
2. For each FAIL item: a `fleet_defects` row inserted with `severity` looked up
   from a static severity table
3. If any defect has `severity="oos"`: `fleet_status` for that truck flipped to
   `oos`, Dispatch sees it immediately, Safety dashboard gets a feed item
4. Driver shown a clear post-submit confirmation: green (PASS · cleared to
   operate) · amber (defects logged, cleared to operate, shop notified) · red
   (OUT OF SERVICE · do not operate, dispatch + shop notified, supervisor
   call required)

**Reuses the existing `MAJOR_OUT_OF_SERVICE_ITEMS` stop-work-modal UX
already proven in `NewEquipmentInspection.jsx`** — drivers already know that
pattern, no UX learning curve.

### 3.2 Post-Trip DVIR (optional iter251 deliverable · operator decision)

Same form, `kind="dvir_post_trip"`, defaults pre-filled from morning DVIR,
focuses on damage / new defects / fluids consumed.
**Recommend deferring to Phase 2** to keep iter251 scope tight.

### 3.3 Weekly Lead Driver Inspection (`kind="weekly_lead"`)

Truck-boss-only routing. Different checklist — cleanliness, body damage,
recurring issues, tire wear, fluid leaks, organization, abuse/damage. Generates
defects same as DVIR. Submitted weekly per truck.

### 3.4 Weekly Emergency Equipment Inspection (`kind="weekly_emergency"`)

Compliance-focused: headlights, turn signals, brake lights, running lights,
strobes, backup alarm, horn, raised-bed alarm, extinguisher, triangles, first
aid. Surfaces to **both** Dispatch and Safety dashboards because emergency-
equipment failure is a safety AND operational concern.

### 3.5 Defect Lifecycle (universal across all 3 inspection kinds)

```
                    ┌─── opened by failed checklist item ──┐
                    ▼                                       │
   ┌─────────────────────────────────────┐                  │
   │  fleet_defects.status = "open"      │                  │
   │  severity ∈ {oos, monitor}          │                  │
   │  category ∈ {brakes, tires, lights, │                  │
   │    coupling, fluids, signals,       │                  │
   │    emergency_equipment, body,       │                  │
   │    suspension, hydraulics, ...}     │                  │
   └─────────────────────────────────────┘                  │
                    │                                       │
   ┌────────────────┴──────────────┐                        │
   ▼                               ▼                        │
   acknowledged                  repaired                   │
   (Shop saw it)                 (Shop closed)              │
                                   │                        │
                                   ▼                        │
                                cleared                     │
                                (Dispatch re-enabled        │
                                 the truck for assign)      │
```

**Repair photos + notes** captured by Shop personnel at close-out. Audit trail
preserved permanently. Repair-lifecycle deepening (parts, labor, mechanic
assignment) is **explicitly deferred to MaintainX integration** — iter251 stops
at "Shop says this is fixed; Dispatch re-enables the truck".

---

## 4. RBAC / Ownership Proposal

### 4.1 Submission rights (who can submit each inspection kind)

| Inspection kind | Submitter roles | Auth model |
|---|---|---|
| Daily DVIR | Any signed-in employee with driver scope, OR anonymous via `/fleet` public tile (same pattern as Field daily reports today) | Public-tile OR signed-in driver |
| Weekly Lead Driver | Lead Driver / Truck Boss role · OR Admin override | Signed-in only |
| Weekly Emergency Equipment | Lead Driver / Safety Officer · OR Admin override | Signed-in only |

### 4.2 Read / management surfaces

| Action | Dispatch | Shop | Safety | Admin |
|---|---|---|---|---|
| View fleet status board (149 units, current state) | ✅ primary | read-only | read-only summary | ✅ |
| View open defects list | ✅ read-only | ✅ primary (own queue) | ✅ filtered by emergency-equipment subset | ✅ |
| Mark defect `acknowledged` | — | ✅ | — | ✅ |
| Mark defect `repaired` | — | ✅ | — | ✅ |
| Mark defect `cleared` (re-enable truck) | ✅ primary | ✅ | — | ✅ |
| Flip truck `OOS → available` manually | ✅ | — | — | ✅ |
| Edit / void an inspection | — | — | — | ✅ only |
| View inspection audit trail | ✅ | ✅ | ✅ filtered | ✅ |

### 4.3 New endpoints (admin-strict + portal-scoped)

```
GET  /api/fleet/units                          (signed-in driver)   list selectable trucks/trailers
POST /api/fleet/dvir                           (signed-in or public_tile)  submit DVIR
POST /api/fleet/weekly-lead                    (lead_driver|admin)  submit weekly lead inspection
POST /api/fleet/weekly-emergency               (lead_driver|safety|admin)  submit weekly emergency
GET  /api/fleet/inspections                    (dispatch|shop|safety|admin)  list with scope filter
GET  /api/fleet/inspections/{id}               (dispatch|shop|safety|admin)
GET  /api/dispatch/fleet/status                (dispatch_user|admin)  fleet status board
GET  /api/dispatch/fleet/defects               (dispatch_user|admin)  open defects scoped by severity
POST /api/dispatch/fleet/defects/{id}/clear    (dispatch_user|admin)  re-enable truck post-repair
POST /api/dispatch/fleet/units/{unit}/oos      (dispatch_user|admin)  manual OOS flip
GET  /api/shop/fleet/defects                   (shop_user|admin)  shop queue
POST /api/shop/fleet/defects/{id}/ack          (shop_user|admin)
POST /api/shop/fleet/defects/{id}/repair       (shop_user|admin)  + repair_notes + photos
GET  /api/safety/fleet/emergency-equipment     (safety_user|admin)  filtered defects view
```

All endpoints `require_admin_strict` OR portal-scoped tokens. **All writes
audited** to a `fleet_audit` collection (same pattern as `legacy_import_audit`).

---

## 5. FMCSA Alignment Review

We are aligning to FMCSA **operational intent**, not building a federally
compliant ELD. MASCI is local/in-state — we don't fall under interstate carrier
regulations for HOS, but DVIR (49 CFR § 396.11 driver vehicle inspection
reports) is a sensible operational baseline regardless. The checklist below
matches the intent of § 396.11 + § 393 Parts and Accessories:

### Tractor / Truck section
brakes (service · parking · trailer-air) · tires (tread · pressure · sidewall) ·
wheels & lugs (lugs tight · rim condition · seal leaks) · steering (play ·
linkage · power-steering fluid) · horn · mirrors (cab · west-coast · convex) ·
windshield (cracks · pitting) · wipers · lights (head · tail · clearance ·
identification · reflectors) · strobes / beacons · suspension (springs · u-bolts
· air bags) · hydraulic systems · PTO systems · backup alarm · raised-bed alarm
· leaks (oil · fuel · coolant · hydraulic · air) · coupling devices (fifth-wheel
· kingpin · safety chains) · airlines (gladhands · hoses · pressure) · safety
equipment (extinguisher · triangles · first aid · spare fuses)

### Trailer section
tires · lights (clearance · tail · brake · identification · ABS lamp) · brakes ·
coupler · safety chains · landing gear · tarp systems · hydraulic systems ·
reflective tape (DOT conspicuity) · structural damage (frame · cross members ·
floor · headboard)

### Emergency Equipment section (weekly)
fire extinguisher (charge · seal · inspection tag) · 3 reflective triangles ·
spare fuses · reflective vest · first-aid kit (if your insurance requires)

This list lives in `checklists.py` and is **editable by you / safety** without
needing a code review — same approach we use for the Pre-Op checklists today.

---

## 6. Defect Severity Proposal

Severity is a **static lookup table** per checklist item. Driver does not pick
severity; the platform does. This eliminates "judgement calls in the field".

```python
# fleet_defect_severity.py  ← single source of truth · editable, version-tracked
FLEET_DEFECT_SEVERITY = {
    # ── OUT OF SERVICE (truck cannot operate until cleared) ──
    "Service brakes - functional":        "oos",
    "Parking brake - functional":         "oos",
    "Steering - free play within spec":   "oos",
    "Tire - tread depth ≥ 4/32 steer · 2/32 drive":   "oos",
    "Tire - no exposed cord / belt":      "oos",
    "Tire - no severe sidewall damage":   "oos",
    "Wheel - all lug nuts present & tight":           "oos",
    "Coupling - fifth wheel locked · kingpin engaged":"oos",
    "Coupling - safety chains attached":  "oos",
    "Air system - no leaks · pressure builds 95 psi": "oos",
    "Lights - headlights low/high beam functional":   "oos",
    "Lights - brake lights both functional":          "oos",
    "Fire extinguisher - present · charged · sealed": "oos",
    # ── MONITOR (truck can operate · log + photo · shop notified) ──
    "Mirror - cracked or chipped (visible image)":    "monitor",
    "Body - cosmetic damage":             "monitor",
    "Cab - cleanliness":                  "monitor",
    "Beacon - one flash pattern impaired (others OK)":"monitor",
    "Interior - minor wear":              "monitor",
    "Triangles - case scuffed":           "monitor",
    # ... ~120 items total · safety + ops co-authored
}
```

Falls back to `"monitor"` (safer default) if a checklist item is added without
a severity entry. Adding items requires a follow-up PR to assign severity — a
forcing function for thoughtful classification.

---

## 7. Dashboard-Routing Proposal

### 7.1 Dispatch dashboard surface
- **Fleet Status Board** (top-line · 149 units): unit · last-DVIR-date ·
  driver · status pill (available/oos/defect_open) · most-recent open defect
- **Open OOS List**: filter on `severity=oos status=open` · click-through to
  inspection
- **Activity feed**: latest 25 inspections submitted today

### 7.2 Shop dashboard surface
- **My Defect Queue**: all `fleet_defects` with `status=open` ordered by
  (severity desc, created_at asc)
- **Acknowledged**: defects I've marked as seen but haven't repaired yet
- **Repair History**: defects I've closed in the last 30 days · audit
- Filter by truck unit or defect category

### 7.3 Safety dashboard surface
- **Emergency Equipment Alerts**: defects where category ∈
  `{emergency_equipment, lights, signals, alarms, extinguisher, triangles}`
- **Recurring Safety Issues**: trucks with ≥ 3 defects of the same category in
  the last 90 days (flagging chronic safety problems)
- **Weekly Audit Status**: which trucks have/haven't had their weekly
  emergency-equipment inspection this week

### 7.4 No new dashboards · these are sections on the existing portal hubs.

---

## 8. Mobile UX Proposal

### 8.1 Public-tile flow (`/fleet`)
- Identical visual language to `/field` (amber accent gives way to a navy/cyan
  accent for fleet · distinct but consistent)
- Two big buttons: **Submit DVIR** · **Submit Weekly Inspection** (lead-driver
  only · hidden if not signed in)
- Truck/trailer combobox uses existing `EquipmentCombo` pattern · pre-filtered
  to `category` ∈ fleet categories
- Driver name combobox uses existing `EmployeeCombo`
- Checklist rendered as tap-to-toggle PASS / FAIL / N/A pills · same as Pre-Op
- FAIL prompts:
  - For OOS items: full-screen "STOP — Out of Service" modal · driver must
    confirm they will not operate · supervisor name field · photo required
  - For Monitor items: amber inline alert · photo optional but encouraged ·
    short note field
- Bottom-fixed Submit button with payload size estimate (reused iter250
  soft-warning pattern)

### 8.2 Dispatch/Shop/Safety dashboard surfaces
- Mobile-first tables that collapse to cards on `<768px`
- Status pills color-coded · large tap targets · sticky filter chips
- One-tap "Mark Repaired" / "Mark Cleared" with confirmation modal

### 8.3 Offline tolerance (Phase 3 · not Phase 1)
DVIRs are mostly submitted in good signal at the yard, but Phase 3 considers
draft-save resilience similar to Daily Reports auto-save today.

---

## 9. Phased Rollout Recommendation

**Each phase is its own operator-approval gate.** Same cadence as iter248
Legacy Records.

### Phase A · Foundation (iter251)
- `equipment_inspections.kind` field added (default `pre_op` for backfill)
- `fleet_defects` collection + lifecycle endpoints
- `fleet_status` derived projection + rebuild-on-submit hook
- Severity lookup table seeded
- `checklists.py` extended with DVIR (truck + trailer + emergency) section
  generators
- `/api/fleet/dvir` submission endpoint with OOS routing logic
- Audit trail (`fleet_audit` collection)
- 25+ unit tests · pre-deploy gate

### Phase B · Driver UX (iter252 · gated on A)
- Public tile **"Trucking / Fleet Ops"** on `Hub.jsx`
- `/fleet` landing page (driver entry point)
- `NewDvirInspection.jsx` (mobile-first form · reuses `EquipmentCombo`,
  `EmployeeCombo`, `PhotoUpload`, `SignaturePad`)
- OOS stop-work modal (reused from Pre-Op)
- View / print DVIR PDF

### Phase C · Dispatch & Shop visibility (iter253 · gated on B)
- Dispatch Hub: fleet status board section · open OOS list section
- Shop Hub: defect queue · acknowledge + repair flows
- Safety dashboard: emergency-equipment alerts section
- Cross-portal audit views

### Phase D · Weekly Lead + Weekly Emergency (iter254 · gated on C)
- Weekly inspection forms (separate checklists, same engine)
- Truck-boss role gating
- Weekly cadence reporting (who's submitted this week, who hasn't)

### Phase E · Defect lifecycle hardening (iter255 · gated on D)
- Shop repair-photo capture · repair-notes capture
- Audit-PDF export per defect
- Recurring-issue detection (90-day window)
- Integration-ready external_refs surfaced in Defect detail view

### Phase F · Motive + MaintainX integration (iter256+ · separate operator approval)
- NOT scoped here. iter251-255 finishes the foundation. Integration is its own
  workstream that calls `integration_playbook_expert_v2` BEFORE any code.

---

## 10. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Drivers don't adopt the form (operational orphan) | Medium | High — fleet visibility never materialises | Mobile-first UX · OOS stop-work UX already familiar from Pre-Op · supervisor-led rollout · post-Phase-B field test with 2-3 drivers before broad rollout |
| OOS false positive locks operationally-fine truck | Medium | Medium — productivity hit | Dispatch can clear an OOS state with an audited override · severity table is conservative-default-monitor (force explicit OOS designation) |
| OOS false negative — safety incident from missed defect | Low | Severe | Severity table reviewed by Safety · OOS modal explicitly requires driver confirmation · all defects audited permanently |
| `fleet_defects` collection growth | Low | Low | Defects close out · estimate 5-10 open at any time · cleared defects stay forever for audit (negligible storage) |
| Premature MaintainX/Motive coupling | Low | High — refactor cost | Integration code explicitly OUT of Phase A-E · `external_refs` reserved but unused · clean cut-line |
| Scope creep into TMS / ELD / route opt | Medium (organisational pressure) | High — derails operational focus | Architecture document explicitly enumerates what is NOT being built · operator-approval gates at each phase boundary |
| Defect classification disagreement (driver vs shop) | Medium | Low | Severity is platform-determined, not driver-chosen · escalation goes through Safety, not the form |
| Trailer multi-coupling edge cases (B-train, doubles) | Low | Low | Schema supports trailer array · UI defaults to single trailer · multi-trailer is data-supported even if UX adds it in Phase D |
| Pre-deploy gate HOLD | High (auth-sensitive new endpoints) | Procedural · low actual risk | Same operator-ack pattern as iter248 Phase A and iter249 Phase B · expected behaviour |

**Overall risk verdict**: LOW-MEDIUM. Plumbing already exists. The hard part is
discipline (severity table accuracy, role-routing accuracy) — not engineering.

---

## 11. Implementation Sequencing (Phase A only · the rest gated)

Phase A breakdown · ~5 working sessions of implementation if approved · each
deliverable has its own acceptance criteria.

1. **Severity table seed** (`backend/fleet_defect_severity.py`)
   - 120 items · OOS + monitor split · authored from FMCSA § 393 reference
   - Reviewed by Safety before merge (operator-side gate)
2. **Schema additions**
   - `equipment_inspections.kind` field with default `pre_op` backfill (zero downtime)
   - `fleet_defects` collection with indexes on `(unit, status, severity)`
   - `fleet_status` collection with index on `unit` (unique)
   - `fleet_audit` collection (append-only)
3. **DVIR checklist generator** (`backend/checklists.py` extension)
   - `dvir_truck_items()` · `dvir_trailer_items()` · `dvir_emergency_items()`
   - Returns same shape as existing Pre-Op item lists
4. **Submission endpoint** (`backend/routes/fleet_ops.py`)
   - `POST /api/fleet/dvir` · payload → `equipment_inspections` row → severity-classified
     `fleet_defects` rows → `fleet_status` projection rebuild → audit
5. **Read endpoints** (admin + portal-scoped previews · UI not yet wired)
   - `GET /api/dispatch/fleet/status` (returns 149-unit board JSON)
   - `GET /api/shop/fleet/defects` (returns Shop queue JSON)
6. **Tests** (`backend/tests/test_iter251_fleet_ops_foundation.py`)
   - Severity classification correctness
   - DVIR submission round-trip
   - OOS detection produces correct `fleet_status` flip
   - Defect lifecycle state machine (open → ack → repair → cleared)
   - Anon RBAC on all new endpoints
   - Audit chain captures every action
7. **Pre-deploy gate**
   - Will return HOLD (auth-sensitive new endpoints) — same procedural pattern
     as iter248/249 · ack required from operator before deploy

**No frontend code in Phase A.** Phase B owns the driver UX. This is the same
discipline iter248 Legacy Records Phase A used (backend foundation first,
operator approves, THEN UX in next phase).

---

## 12. What I Will NOT Touch In Phase A (operator-stated boundaries)

❌ ELD · HOS · DOT logs · sleeper · interstate workflows
❌ GPS · telematics · dashcams · driver-behavior tracking
❌ Route optimization · dispatch AI · ML/AI anywhere in the fleet stack
❌ Maintenance ERP · parts · labor · mechanic scheduling
❌ Motive API integration (reserved, not implemented)
❌ MaintainX API integration (reserved, not implemented)
❌ Fuel systems · IFTA reporting · mileage taxes
❌ Carrier-scale TMS · multi-yard routing · cross-state dispatch
❌ Public driver-self-onboarding · driver scorecards · driver leaderboards
❌ Phase B (frontend) · Phase C (dashboards) · Phase D (weekly forms) · Phase E (repair lifecycle hardening)

These are all gated on explicit phase-by-phase operator approval.

---

## 13. Open Decisions For You

Before I write Phase A code, three operator-side decisions:

**D1. Severity table authorship.**  Do you want to draft the OOS / Monitor
designations yourself (with Safety), or shall I propose a complete v1 table
from FMCSA § 393 + § 396 references that you redline before merge?
  - 13a) I draft v1, you redline
  - 13b) You + Safety draft, I implement
  - 13c) Joint working session

**D2. Public tile vs signed-in only for daily DVIR.**  Drivers may not all
have signed-in accounts. Field daily reports today work both ways. Same here?
  - 13a) Public tile + signed-in (mirrors Field DRs) — recommended
  - 13b) Signed-in only (tighter audit, harder adoption)

**D3. Phase A scope confirmation.**  Backend foundation + tests + pre-deploy
gate. No frontend, no public tile, no dashboards. Phases B-E gated separately.
  - 13a) Yes, Phase A only as described
  - 13b) Combine Phase A + B (backend + driver UX in one swing)
  - 13c) Other (please describe)

---

## 14. Document Lifecycle

This file lives at `/app/FLEET_OPS_FOUNDATION_iter251_ARCHITECTURE.md`.
Operator commentary / redlines / decisions get appended here as they happen,
identical to how `/app/LEGACY_RECORDS_ARCHITECTURE_iter248.md` evolved.

When all 5 phases ship, this becomes the canonical reference for the Fleet
Operations Foundation surface.
