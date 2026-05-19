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
