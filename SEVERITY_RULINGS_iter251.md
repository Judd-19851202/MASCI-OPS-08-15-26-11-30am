# Fleet Severity Table · Operator Rulings · v1 Approved

**Status**: 🔒 LOCKED · operator-approved 2026-05-19
**Version**: `v1-approved-2026-05-19`
**Ruler**: Operator (Jaymn)
**Reviewer chain**: Operator → (Safety field-deployment sign-off pending)
**Iteration**: iter251 Phase A · governance gate before Phase B (driver UX)
**Audit-trail**: This document is immutable. Future changes require a NEW dated rulings record + version bump.

---

## Governing Philosophy (operator-stated)

The classifications must encourage **honest DVIR reporting**, not punish it.

The system shall be:
- safety-defensible
- DOT/FMCSA-aware
- operationally realistic
- driver-friendly
- not shutdown-happy
- not fear-driven
- not checkbox theater

The classifications shall NOT:
- make every tiny issue OOS
- create a fear culture where drivers hide defects
- produce false shutdowns
- become vague subjective thresholds

The classifications SHALL:
- preserve unsafe-equipment guards
- carry clear DOT/FMCSA logic
- use objective, field-readable wording
- allow tiered MONITOR with shop-window timing
- escalate conservatively to OOS for visibility, brake, and load-securement risks

---

## Rulings (9 items · all 9 resolved)

### Ruling #1 · Power steering — split by drip rate
- **Before**: single line `Power steering — no leaks · fluid at proper level · normal effort` · OOS · uncertain
- **After**:
  - 🛑 **OOS** · `Power steering — fluid AT or ABOVE MIN · normal effort · no active drip` (§ 393.209 · CVSA OOS)
  - 👁 **Monitor** · `Power steering — stable seep / weep · normal effort · fluid AT MIN or above` (5-day shop window)
- **Operator note**: "active drip" must remain objective and easy for drivers to understand.

### Ruling #2 · Headlights — high beam tiered by day/night
- **Before**: `Headlights — high beam · both sides functional` · OOS · uncertain
- **After**:
  - 🛑 **OOS** · `Headlights — both low-beams functional · at least one high-beam functional` (§ 393.24 · CVSA)
  - 👁 **Monitor** · `Headlights — single high-beam out · both low-beams functional · daylight-only ops` (3-day shop window)
- **Operator note**: any low-beam failure = OOS · both high-beams out = OOS · any night assignment = OOS until repaired.

### Ruling #3 · Strobes / beacons — upgraded to OOS for work-zone ops
- **Before**: `Strobes / beacons — all flash patterns operational` · MONITOR · uncertain
- **After**:
  - 🛑 **OOS** · `Strobes / beacons — all flash patterns operational (work-zone / lane closure / paving / shoulder / airport ops)` (MASCI struck-by control · OSHA 1926 Subpart G)
  - 👁 **Monitor** · `Strobes / beacons — partial pattern acceptable for yard-only / shop-shuffle moves` (5-day shop window)
  - 🛑 **OOS** · `Strobes / beacons — at least one operational` (unchanged · total beacon loss is always OOS)
- **Operator note**: work-zone visibility is a primary struck-by control · operational policy, not just DOT minimum.

### Ruling #4 · Wipers — driver-side strict · passenger conditional
- **Before**: single line `Wipers — both blades sweep windshield cleanly · no streaking` · OOS · uncertain
- **After**:
  - 🛑 **OOS** · `Driver-side wiper — sweeps cleanly · no streaking · no torn blade` (§ 393.78)
  - 🛑 **OOS** · `Passenger-side wiper — sweeps cleanly when rain forecast in shift window` (§ 393.78)
  - 👁 **Monitor** · `Passenger-side wiper — minor streak acceptable · dry forecast in shift window · 3-day shop window`
- **Operator note**: Driver-side visibility is non-negotiable. Texas/Florida storm conditions change rapidly.

### Ruling #5 · Body "severe damage" rubric — 5-test objective criteria
- **Before**: `Body — no severe damage affecting safe operation` · OOS · uncertain
- **After**: replaced with **objective 5-test rubric**:
  - 🛑 **OOS** · `Body — no frame/cab-mount fracture · no projecting metal or sharp edge · no loose panel/door · no rust-through on cab floor or fuel tank · no damage blocking mirror or windshield visibility` (CVSA OOS · § 393.201)
  - 👁 **Monitor** · `Body — cosmetic dings · scrapes · paint` (unchanged · accountability tracking only)
- **Operator note**: cosmetic damage must NOT flood the OOS system. 4-test rubric was upgraded to 5-test rubric to include rust-through.

### Ruling #6 · Hydraulic leaks — tiered by drip rate + circuit role
- **Before**: `Hydraulic system — no visible leaks` · OOS · uncertain
- **After**:
  - 🛑 **OOS** · `Hydraulic system — no active drip · no leak below MIN reservoir · no leak on bed-lift / boom / outrigger / brake-assist circuit` (OSHA 1926.602)
  - 👁 **Monitor** · `Hydraulic system — stable seep / film without active drip · reservoir AT or ABOVE MIN · not on load-supporting circuit` (5-day shop window)
- **Operator emphasis**: anything affecting bed support · outriggers · booms · brake-assist · load retention leans conservative/OOS.

### Ruling #7 · Heater / defroster — visibility-driven, not comfort-driven
- **Before**: `Cab — heater / defroster operational (cold/wet weather)` · MONITOR · uncertain
- **After**:
  - 🛑 **OOS** · `Defroster — functional when ambient ≤ 40°F or precipitation forecast in shift window` (§ 393.79)
  - 👁 **Monitor** · `Cab heater — functional · escalates to OOS if window fogging affects visibility` (7-day shop window)
- **Operator note**: Visibility is the actual safety concern, not comfort.

### Ruling #8 · Dash gauges — tiered by truck class (legacy vs ECM)
- **Before**: `Cab — dash gauges functional (oil pressure · temp · fuel)` · OOS · uncertain
- **After**:
  - 🛑 **OOS** · `Oil pressure & coolant temp gauges OR equivalent ECM warning system functional` (§ 393.51 · operational)
  - 👁 **Monitor** · `Fuel gauge — functional · driver may estimate by miles · 7-day shop window`
  - 👁 **Monitor** · `Dash gauges (oil / temp) inop on units with ECM check-engine + fault display fully functional · 14-day shop window`
- **Operator note**: do NOT treat a modern ECM-equipped truck the same as an old analog-only truck. Practical and defensible.

### Ruling #9 · Tarp — split by load-haul scope (6"×6" objective threshold)
- **Before**: `Tarp system — deploys + retracts · no major tears` · MONITOR · uncertain
- **After**:
  - 🛑 **OOS** · `Tarp system — deploys + retracts · no tear > 6"×6" · functional on units assigned to aggregate / asphalt / dust-producing load haul` (Tex. Transp. Code § 725.021 · § 393.100)
  - 👁 **Monitor** · `Tarp system — minor tear < 6"×6" OR unit assigned to empty / equipment / non-dust haul · 5-day shop window`
- **Operator note**: 6"×6" is reasonable and objective. Aggregate/asphalt/dust = critical.

---

## Table Stats (before → after)

| Metric | Before (v1-DRAFT) | After (v1-approved-2026-05-19) |
|---|---|---|
| Total severity entries | 97 | **107** |
| OOS classifications | 69 | **73** |
| Monitor classifications | 28 | **34** |
| OOS / Monitor ratio | 2.46 | **2.15** (still conservative · ≥ 1.5 threshold) |
| Uncertain items | 9 | **0** |
| Coverage all 3 kinds | 100% | **100%** |
| Verdict | NEEDS_REVIEW | **READY_FOR_SAFETY_SIGNOFF** |

The OOS/Monitor ratio decrease (2.46 → 2.15) reflects the operator's stated philosophy: **add more tiered Monitor language so drivers report honestly without triggering false shutdowns**, while preserving conservative OOS bias.

---

## Future UX guidance (operator instruction · for Phase B)

When the driver-facing DVIR UX is built:

1. **No giant red "FAILED" culture.** Use calm operational language:
   - `Monitor` (shop-fix scheduled · keep operating)
   - `Repair Required` (intermediate state · shop must address before next shift)
   - `Out of Service` (truck cannot operate until cleared)
2. Severity outcomes must be **clear · calm · operational · non-panic-inducing**.
3. Driver submitting a defect = positive accountability act. The UX shall thank, not scold.
4. Show the shop-window timer for Monitor items (5-day · 7-day · 14-day · 3-day) so drivers see the path forward.
5. For escalating MONITOR → OOS thresholds (weather, ambient temp, work-zone assignment), the UX should explain why the same defect classification changed.

---

## Version stamp + Re-audit

After applying all 9 rulings:
- `severity_table_version` bumped: `v1-DRAFT-pending-safety-review` → **`v1-approved-2026-05-19`**
- `SEVERITY_TABLE_APPROVAL` block added · single source of truth · exposed via `GET /api/admin/fleet/severity-audit`
- Audit verdict flipped from `NEEDS_REVIEW` → **`READY_FOR_SAFETY_SIGNOFF`**

## Sign-off chain

- [x] Operator (Jaymn) · 2026-05-19 · all 9 rulings approved · this document
- [ ] Safety · field-deployment sign-off (after Phase B driver UX shipped to mascidocs.com)
- [ ] Shop · operational sign-off (after first 30 days of field DVIRs)
- [ ] Dispatch · re-clearance authority sign-off (after first 30 days)

Once Safety signs off on field deployment, `SEVERITY_TABLE_APPROVAL.status` updates from
`"approved · pending Safety field deployment"` → `"approved · Safety-signed YYYY-MM-DD"` and the
version bumps to `v1-safety-signed-YYYY-MM-DD`.

---

🔒 **This document is the audit-of-record for the v1-approved-2026-05-19 severity table.** Any future severity-table change MUST reference this file in the new rulings record and bump the version stamp.

---

# v1.1 Refinement Pass · 2026-05-19 PM

**Status**: 🔒 LOCKED · operator-approved 2026-05-19 PM
**Version stamp**: `v1-approved-2026-05-19` → **`v1.1-approved-2026-05-19`**
**Audit verdict**: `READY_FOR_SAFETY_SIGNOFF` (preserved)

## Operator brief (2026-05-19 PM)
Pre-production sign-off refinement pass requested:
1. Driver Name field → searchable employee picker + "+ Add to roster" fallback (operationally lightweight · case-insensitive dedup)
2. DOT/FMCSA/commercial DVIR alignment review (semis, dumps, trailers · NOT generic passenger inspection)
3. HelpTip density tuning (slightly denser where genuinely helpful · still calm/short/collapsible)
4. Inspection wording pass (field-clear, commercially accurate, non-ambiguous, no overlap)

## v1.1 changes

### Added · 5 commercial-vehicle items (§ 396.11 alignment)
- 🛑 **OOS** · `Exhaust system — no leaks ahead of muffler · no fumes entering cab` (§ 393.83 · CO poisoning prevention)
- 🛑 **OOS** · `Battery — securely mounted · no severe corrosion · cables tight` (§ 393.30 · safety lighting + remote-route reliability)
- 🛑 **OOS** · `Cargo securement — chains / binders / straps rated and applied per load (flatbed / service truck)` (§ 393.100 · load-shed struck-by prevention)
- 👁 **Monitor** · `DOT number / company markings — legible · readable from 50 ft` (§ 390.21 · CMV identification)
- 👁 **Monitor** · `Trailer mudflaps / spray suppression — present · secure · no major tears` (§ 393.86 · spray protection for following traffic)

### Consolidated · 2 redundant tire pairs (no signal loss)
- ❌ `Tire — no exposed cord / belt / ply` + `Tire — no severe sidewall damage (bulge / cut / cord exposed)` → ✅ **`Tire — no sidewall bulge · no exposed cord / belt / ply · no severe cut`** (OOS · single item)
- ❌ `Tire — properly inflated (no flat · no severe under-inflation)` + `Tire — no audible air leak` → ✅ **`Tire — properly inflated · no audible leak · no flat`** (OOS · single item)

### Tightened · 4 wordings for commercial field clarity
- `Trailer air brakes — engage with hand valve · release fully` → **`Trailer hand valve — applies trailer service brakes from tractor · releases fully`** (explicit re: "hand valve = tractor hand control")
- `Brake chamber / slack adjuster — no visible damage · proper stroke` → **`Brake chamber / slack adjuster — no visible damage · slack adjuster travel within normal range`** (driver-checkable language · removed shop-only "proper stroke" jargon)
- `Identification lights (3-light cluster) — all functional` → **`Identification lights (3-light cluster · top of cab) — all functional`** (anchored location for drivers)
- (Existing wordings audited · others retained as-is)

### Removed · 1 low-operational-value item
- ❌ `Cab — interior cleanliness` (MONITOR) — operationally low-signal · cabin cleanliness is a yard/shop responsibility, not a DVIR signal. Removed from severity table, daily DVIR checklist, and weekly lead checklist.

### Driver UX additions (frontend NewFleetDVIR.jsx)
- 🟢 Driver Name field now uses **`EmployeeCombo`** (searchable picker · same UX as Request PO) + "+ Add to roster" fallback via existing `POST /api/employees/add` endpoint (case-insensitive dedup · trim whitespace · idempotent · no HR approval queue).
- 🟢 **3 new collapsible HelpTips** in Truck Walk-Around section:
  - "Air brakes · what to listen for" (95 psi build · gladhand leaks · 4 psi/min leak-down rule)
  - "Tires · quick check" (tread depth · wear bars · sidewall feel-test · hiss listen)
- 🟢 **1 new collapsible HelpTip** in Trailer Walk-Around section:
  - "Coupling · the most common roadside finding" (kingpin seated · jaws closed · safety pin · tug-test)
- All 4 new tips: short · operational · field-practical · collapsed by default · zero preachy LMS tone.

## Table stats (v1 → v1.1)

| Metric | v1-approved | v1.1-approved |
|---|---|---|
| Total severity entries | 107 | **109** |
| OOS classifications | 73 | **74** |
| Monitor classifications | 34 | **35** |
| OOS/Monitor ratio | 2.15 | **2.11** (still conservative · ≥ 1.5 floor) |
| Uncertain items | 0 | **0** |
| Verdict | READY_FOR_SAFETY_SIGNOFF | **READY_FOR_SAFETY_SIGNOFF** |

## Coverage matrix · v1.1 against 49 CFR § 396.11 mandatory inspection items

| § 396.11 mandatory item | v1.1 coverage |
|---|---|
| Service brakes (incl. trailer connections) | ✅ Service brakes · Trailer hand valve · Brake hoses · Brake warning · Brake chamber/slack adjuster |
| Parking (hand) brake | ✅ Parking brake — holds against torque |
| Steering mechanism | ✅ Free play · Linkage/drag link/pitman · Power steering (split) |
| Lighting devices and reflectors | ✅ Low + high beams · brake · tail · clearance · ID cluster · plate · reflectors · trailer set |
| Tires | ✅ Steer 4/32" · Drive/trailer 2/32" · Consolidated sidewall · Consolidated inflation |
| Horn | ✅ Horn — sounds at normal volume |
| Windshield wipers | ✅ Driver-side strict · Passenger conditional by forecast |
| Rear vision mirrors | ✅ Both sides · Minor crack chip MONITOR |
| Coupling devices | ✅ Fifth wheel locked · mounting bolts · safety chains · pintle hook · Trailer coupler/kingpin · Trailer safety chains |
| Wheels and rims | ✅ Lugs present · Lugs tight · Rim cracks · Hub seal |
| Emergency equipment | ✅ Fire extinguisher · Reflective triangles · Fuses · First aid · Vest |
| **+ Air brake system** (CMV-specific) | ✅ Pressure build · Leak-down · Gladhands · Low-air warning |
| **+ Suspension** | ✅ Leaf springs/u-bolts · Air bags |
| **+ Exhaust** (v1.1 new) | ✅ § 393.83 added |
| **+ Battery** (v1.1 new) | ✅ § 393.30 added |
| **+ Cargo securement** (v1.1 new) | ✅ § 393.100 added (flatbed/service scope) |
| **+ DOT marking** (v1.1 new) | ✅ § 390.21 added |
| **+ Mudflaps** (v1.1 new trailer) | ✅ § 393.86 added |

Coverage is now **defensibly aligned with commercial DVIR realities** without becoming compliance theater. Operationally usable · short list · objective thresholds.

## Files touched in v1.1 cycle
- MOD · `backend/fleet_defect_severity.py` (+changelog comment · +SEVERITY_TABLE_APPROVAL.v1_1_refinements · +5 new items + metadata · 2 consolidations · 4 wording tightens · 1 removal · 2 new category constants)
- MOD · `backend/checklists_fleet.py` (truck list +6 new items / -2 consolidated + 4 tightened wordings · trailer list +1 mudflap · weekly lead list -1 cleanliness · emergency list +1 ID-cluster wording)
- MOD · `frontend/src/pages/NewFleetDVIR.jsx` (Driver name → EmployeeCombo · +3 truck helptips · +1 coupling helptip · `<>` fragment around trailer map)
- MOD · `frontend/src/lib/i18n.js` (~8 new EN→ES translation entries for driver-combo placeholder + 4 new helptips)
- MOD · `backend/tests/test_iter251_severity_v1_approved.py` (version assertion v1.1 · size 107→109)
- REGEN · `/app/FLEET_SEVERITY_REVIEW_PACKAGE_iter251.md` (now reflects v1.1 · 109 items)

## Sign-off chain (preserved · status of approval-bands unchanged)

- [x] Operator (Jaymn) · 2026-05-19 · all 9 v1 rulings approved
- [x] Operator (Jaymn) · 2026-05-19 PM · v1.1 commercial-vehicle refinement pass approved
- [ ] Safety · field-deployment sign-off (after Phase 2 driver UX shipped to mascidocs.com)
- [ ] Shop · operational sign-off (after first 30 days of field DVIRs)
- [ ] Dispatch · re-clearance authority sign-off (after first 30 days)

---

🔒 **v1.1 is the current production-target version.** No further severity-table edits without a new dated rulings record + version bump.

