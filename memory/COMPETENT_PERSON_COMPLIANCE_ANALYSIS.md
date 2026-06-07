# Competent Person Compliance Analysis

**Reference:** §1926.650 (definition), §1926.651(k) (CP-led inspections), §1926.652 (CP-led soil classification + protective-system selection).

---

## What §1926 expects of a Competent Person

1. **Identify** existing and predictable hazards in the surroundings, or working conditions which are unsanitary, hazardous, or dangerous to employees.
2. **Authorize** prompt corrective measures to eliminate them.
3. **Inspect** excavations, adjacent areas, and protective systems for evidence of cave-ins, failure, hazardous atmospheres, or other hazards:
   - daily
   - before each shift
   - as conditions change
   - after every rainstorm or other hazard-increasing event
   - as needed throughout the shift
4. **Classify soil** using at least one visual test AND at least one manual test per Appendix A; reclassify after rain / freeze / thaw / other state change.
5. **Select protective system** per Appendix B/C/D/E/F based on soil class, depth, surcharge load, water condition, and adjacent structures.
6. **Verify** that any manufactured protective system on site has accompanying tabulated data.
7. **Authorize** crew descent only after hazardous atmospheres tested (when required).

---

## Coverage by responsibility

| # | CP Responsibility | Color | Evidence |
|---|---|---|---|
| 1 | Identify hazards | 🟡 | Inspection findings field + checklist captures known hazards; no surrounding-area capture. |
| 2 | Authorize corrective measures | 🟢 | Inspection Fail + Major/Critical → automatic Inspection Hold + Maintenance Hold + Safety Hold + repair stub via `event_fanout`. CP cannot fail an inspection without the system acting on it. |
| 3a | Daily inspections | 🟢 | `Daily Visual` inspection type; Daily Posture dashboard tracks today's completed / outstanding. |
| 3b | Before each shift | 🟡 | Daily Visual cadence exists but doesn't auto-prompt "second inspection if a second shift starts". |
| 3c | As conditions change | 🟡 | CP can fire an additional Daily Visual any time; no prompt. |
| 3d | **After rainstorms or other hazard events** | 🔴 | Not captured. No weather-event trigger; CP must remember independently. |
| 3e | As needed throughout the shift | 🟡 | Supported through repeated Daily Visuals; no prompt. |
| 4 | **Soil classification** (visual + manual test, reclassify after change) | 🔴 | No soil class field. No Appendix A test record. |
| 5 | **Select protective system** per Appendix B–F | 🔴 | No excavation record, no design selection field. |
| 6 | Tabulated data verification | 🟢 | `tabulated_data_missing` flag fires Certification Hold; reportable + visible on public QR landing's DO NOT USE banner. |
| 7 | Atmospheric testing authorisation | 🔴 | Not captured. |

**Score: 3 GREEN / 4 YELLOW / 4 RED out of 11 → 27 % strong + 36 % partial → 64 % some coverage.**

---

## CP-specific enforcement that DOES exist (strong point)

`inspections.py` lines 90–96:

```python
if (
    payload.inspection_type in {"Monthly Competent Person", "Annual Review"}
    and not payload.competent_person_confirmed
):
    raise HTTPException(422, "competent_person_confirmed must be true for "
                              "Monthly Competent Person or Annual Review inspections")
```

The platform **refuses** to record a Monthly CP or Annual inspection without a competent-person attestation. This is a robust data-layer enforcement of the §1926.651(k) "by the competent person" requirement at the cadence level.

Additionally:
- Phase 7.5C `event_fanout` ensures the CP attestation rides into the bell + email + digest of every failed inspection
- The Daily Posture dashboard shows the current CP attestation status of the most recent inspection per asset
- Audit log captures `competent_person_confirmed` on every inspection event

---

## Where the CP is **on their own** (gaps)

1. **No rain-event trigger.** A storm passes overhead, the regulation requires a fresh inspection, the platform doesn't prompt. A weather webhook + Pulse trigger is straightforward future work.
2. **No soil classification field.** The single most important Subpart P decision the CP makes is not recorded.
3. **No excavation context.** The CP inspects a *box* (asset); the regulation inspects an *excavation* (system). Until G-1 (Excavation Record) lands, the CP's daily inspection of the dig itself is not in the system.
4. **No atmospheric reading capture.** When a CP authorises descent into a > 4 ft excavation with potential hazardous atmosphere, the gas-meter readings aren't recorded anywhere structured.

---

## Risk implication

If MASCI experiences a §1926 citation event, the system today can defend:
- Daily / Monthly-CP / Annual inspection of the protective-system *assets*
- Tabulated data discipline
- Repair / hold workflow audit

The system cannot today defend:
- The CP's soil-class call on a given excavation
- The CP's protective-system selection rationale
- Post-rain re-inspection cadence
- Atmospheric authorisation for descent

These are evidence-quality gaps, not philosophical ones. They become defensible the day G-1 + G-5 ship.

---

## Recommendation

The **CP-attestation primitive** that already exists (`competent_person_confirmed`) is the right hook on which to hang every future CP workflow:
- attach it to soil classification entries
- attach it to atmospheric readings
- attach it to evacuation acknowledgements

Re-using one well-tested primitive across new surfaces is cheaper than building a new identity / role layer.
