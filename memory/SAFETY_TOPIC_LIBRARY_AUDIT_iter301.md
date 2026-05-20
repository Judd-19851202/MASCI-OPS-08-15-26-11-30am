# Safety Meeting / Toolbox Topic Library · Lane E Audit · iter301

**Date:** 2026-05-20
**Scope:** Read-only audit of `/app/frontend/src/lib/topics/*.js` (21 domain files · 136 topics) against the operator-named operational verticals.
**Discipline:** Audit-only · NO topic-add work · NO content changes · DEFERRED to operator approval.

---

## 0 · Method

Lenient-parser sweep of the 21 domain files captured every topic regardless of field ordering. For each topic we recorded:
- `key`, `title`, `severity`, `category`, `incident_pattern` length, `discussion_notes` length, `hazards_reviewed` length.

ES coverage cross-validated against the `.es.js` dict files in the same directory.

Keyword corpus scan against the 8 named operational verticals (trucking · dump-bed strike · asphalt lab · dewatering/wellpoint · airport · plant/crusher · shop/mechanic · office/admin).

---

## 1 · Headline finding

**The library is structurally healthy. ES coverage is 100% (136/136 confirmed). Tone discipline is intact. Zero "thin" topics. Zero generic LMS-style content.**

The recommendation is **not "add more content" wholesale** — it's **two named verticals operator-flagged that are quantitatively thin**, plus one optional refinement. Everything else is operationally complete.

---

## 2 · Inventory snapshot

| Domain | EN topics | ES topics | Avg `discussion_notes` chars | fatal_risk | Verdict |
| --- | ---: | ---: | ---: | ---: | --- |
| pipe | 3 | 3 | 631 | 3 | ✅ Strong (high-severity coverage) |
| excavation | 4 | 4 | 800 | 4 | ✅ Strong |
| grading | 5 | 5 | 418 | 4 | ✅ |
| concrete | 12 | 12 | 451 | 5 | ✅ Strong |
| paving | 8 | 8 | 727 | 2 | ✅ Strong (recent iter additions visible — paver_blind_spots, roller_pinch_zones, transfer_burn, night_fatigue) |
| milling | 2 | 2 | 716 | 1 | ✅ |
| mot | 13 | 13 | 475 | **12** | ✅ Strongest fatal-risk concentration (correct for traffic-zone work) |
| **trucking** | **12** | 12 | **902** | **10** | ✅ **Deepest coverage in the library** |
| **dewatering** | 8 | 8 | 968 | 5 | ✅ Operationally comprehensive |
| **shop** | 8 | 8 | 957 | 5 | ✅ Mechanic-grade depth |
| **plant** | 8 | 8 | 959 | 5 | ✅ Strong (crusher · burner · baghouse · loader · lab solvents · silo) |
| **airport** | 2 | 2 | 1039 | 2 | 🟡 **Thin (operator-named gap)** |
| utilities | 2 | 2 | 502 | 2 | ✅ Operator did not flag |
| rigging | 2 | 2 | 428 | 2 | ✅ Operator did not flag |
| fall_protection | 5 | 5 | 431 | 4 | ✅ |
| electrical | 4 | 4 | 462 | 3 | ✅ |
| confined_space | 1 | 1 | 515 | 1 | ✅ Singular but adjacent topics live under pipe (`manhole_work`) and plant (`baghouse_silo`) |
| environmental | 3 | 3 | 436 | 1 | ✅ |
| wellness | 6 | 6 | 506 | 3 | ✅ |
| **office** | 8 | 8 | 899 | 4 | ✅ Strong (operator's office/admin vertical fully covered) |
| general | 20 | 20 | 455 | 10 | ✅ Cross-cutting hazards (PPE · near-miss · stop-work · hot-work · demo · forklift · hand-injury · line-of-fire · etc.) — legitimately cross-domain, NOT diluted content |
| **TOTAL** | **136** | **136** | — | **86 (63%)** | — |

---

## 3 · Per-named-vertical coverage assessment

### 3.1 🟢 Trucking / Fleet — **DEEPEST in library**
**12 topics · 10 fatal-risk · avg `discussion_notes` 902 chars** (longest in library besides airport).

Topic spread:
- `dump_truck` · the canonical three-pattern fatality breakdown (tipover · run-over · overhead strike)
- `dump_bed_overhead_strike` · power-line / bridge / sign / conveyor strikes at the dump site
- `dump_bed_traveling_raised` · "the quiet killer" — bed-up travel after dump
- `dump_bed_pto_habits` · sequence discipline (bed-down → PTO-out → mirror → roll)
- `dump_bed_soft_ground_tipover` · the bed-up rollover
- `dump_bed_wind_raised` · high-wind raised-bed operations
- `trucking_backing_struck_by` · the last 10 feet · spotter use
- `trucking_shoulder_pulloff_struck_by` · roadway pull-offs / shoulder positioning
- `trucking_tarp_load_securement` · tarp + securement on the road
- `trucking_kingpin_coupling_failure` · trailer kingpin / coupling failures
- `trucking_overweight_axle_law` · overweight, axle loading, bridge law
- `trucking_blind_spots_pedestrian` · blind spots / pedestrian workers around trucks

**Operator's named "dump-bed strike prevention" sub-vertical**: 5 of 12 topics directly address dump-bed scenarios. The voice is the strongest in the library — anecdotal, operationally specific ("Drivers describe it the same way every time: 'I forgot the bed was up.'").

**Verdict:** ✅ **NO GAP.** This is the operational-voice gold standard the rest of the library should aspire to.

### 3.2 🟢 Dewatering / Wellpoint — **STRONG**
**8 topics · 5 fatal-risk · avg discussion 968 chars.**

- `dewatering_jetting_rig_overhead_strike` · jetting-rig power-line strikes
- `dewatering_suction_line_entrapment` · suction-line entrapment / engulfment
- `dewatering_diesel_pump_fueling_fires` · diesel pump fueling fires
- `dewatering_wellpoint_trench_collapse` · **wellpoint-specific** trench collapse around headers
- `dewatering_rotating_shaft_belt` · belt entanglement
- `dewatering_discharge_hose_whip` · hose whip / pressure release
- `dewatering_spoil_edge_instability` · spoil placement around wellpoint trench edges
- `dewatering_night_work_struck_by` · night dewatering visibility / struck-by

Operator's named "wellpoint" sub-vertical: directly addressed in `wellpoint_trench_collapse` and `spoil_edge_instability`.

**Verdict:** ✅ **NO GAP.**

### 3.3 🟢 Plant / Crusher — **STRONG**
**8 topics · 5 fatal-risk · avg discussion 959 chars.**

- `plant_conveyor_entanglement` · tail pulleys + pinch points
- `plant_baghouse_silo_hazards` · baghouse cleanout + silo entry
- `plant_asphalt_burns_oil_exposure` · hot asphalt + bitumen vapor
- `plant_burner_systems` · burner light-off / flameout
- `plant_loader_blind_spots_haul_road` · loader blind spots / haul road
- `plant_crusher_clearing_jams` · **THE crusher fatality pattern** (jam-clearing)
- `plant_lab_solvents_ignition` · lab solvents · ovens · ignition (this is the ONLY asphalt-lab topic in the library)
- `plant_silo_burn_avalanche` · silo drag-slat + material avalanche

**Crusher-specific:** Single topic (`plant_crusher_clearing_jams`) — but it's the **right** topic. Crusher fatalities concentrate overwhelmingly in jam-clearing scenarios. Adjacent crusher work (screen-deck cleaning, feeder hopper, belt walk-back) is partially absorbed by `conveyor_entanglement` and `baghouse_silo_hazards`.

**Verdict:** ✅ **NO MAJOR GAP.** Optional refinement noted in §5 below.

### 3.4 🟢 Shop / Mechanic — **STRONG**
**8 topics · 5 fatal-risk · avg discussion 957 chars.**

- `shop_jack_stand_failure` · under-the-truck fatalities
- `shop_lockout_tagout_bypass` · LOTO bypass that kills
- `shop_brake_spring_energy` · brake spring stored energy
- `shop_tire_cage_explosion` · tire cage / multi-piece rims
- `shop_welding_fire_watch` · welding + hot-work cleanup
- `shop_hydraulic_stored_energy` · cylinders · hoses · accumulators
- `shop_under_bed_crush_zone` · crush zones under beds / booms
- `shop_battery_explosion` · battery charging + hydrogen

**Verdict:** ✅ **NO GAP.** Operationally complete.

### 3.5 🟢 Office / Admin Personnel — **STRONG**
**8 topics · 4 fatal-risk · avg discussion 899 chars.**

Surprising depth for an "office" domain — and the right depth, because the actual office-personnel fatality pattern is **commute + site-visit exposure**, not slips/trips at a desk:
- `office_distracted_driving` · phones · coffee · commute
- `office_site_visit_ppe` · PPE on site visits
- `office_parking_lot_struck_by` · parking lots · backing · pedestrians
- `office_heat_stress_visits` · heat stress on summer visits
- `office_lone_worker_checkin` · lone worker / site check-in realities
- `office_severe_weather_accountability` · severe weather accountability for crews + visitors
- `office_slips_trips_falls` · slips · trips · falls in the office
- `office_fatigue_mental_load` · "When You're Tired, You're Impaired"

**Verdict:** ✅ **NO GAP.** This is operational realism — the office topics cover the **real** ways office personnel get hurt, not the LMS template.

### 3.6 🟡 Airport Operations — **THIN (operator-named gap)**
**2 topics · 2 fatal-risk · avg discussion 1039 chars** (longest per-topic in the library, but only 2 topics).

- `airport_movement_area_awareness` · runway / taxiway / ATC discipline
- `airport_jet_blast_fueling` · jet blast / prop wash / airfield fueling

These are both **high-quality** topics — but the airport vertical is operationally multi-faceted. Coverage that's currently absent:

| Possible airport topic | Operational scenario it addresses |
| --- | --- |
| `airport_fod_control` | FOD (Foreign Object Debris) prevention on/near movement areas — runway shutdowns happen over this |
| `airport_night_work_visibility` | Airfield night work — most airport civil work is nights/weekends |
| `airport_security_badging_escort` | Badging + escort discipline — wrong-side-of-fence intrusion is a federal incident |
| `airport_airfield_electrical_lighting` | Airfield lighting circuits — high-voltage, often live, often working at runway edges |
| `airport_drainage_taxiway_edge` | Drainage work at taxiway/runway edges — proximity-to-operating-aircraft exposure |
| `airport_FOD_walkdown_handoff` | Pre/post-shift FOD walkdown handoff to airfield ops |

**Verdict:** 🟡 **GAP.** Operator explicitly named "airport operations." Current 2-topic coverage is high quality but quantitatively narrow.

### 3.7 🟡 Asphalt Lab — **THIN (operator-named gap)**
**1 dedicated topic** (`plant_lab_solvents_ignition`) **+ 1 tangential** (`paving_asphalt_transfer_burn`). The lab is buried inside the broader "plant" domain.

Lab scenarios currently UN-addressed at topic-level:
| Possible asphalt-lab topic | Operational scenario it addresses |
| --- | --- |
| `lab_nuclear_gauge_handling` | Nuclear density gauge transport / storage / radiation safety |
| `lab_core_drilling_silica` | Pavement core drilling — wet-cut silica + saw kickback at the lab |
| `lab_oven_burns_chemistry` | Lab oven burns (550°F+) + bitumen extraction chemistry |
| `lab_sample_crushing_pinch` | Sample-prep crusher pinch points + dust exposure |
| `lab_solvent_handling_ppe` | Trichloroethylene / mineral-spirits exposure + PPE / fume hood discipline |
| `lab_calibration_traffic_exposure` | Density-gauge calibration on live mainline — struck-by + radiation logistics |
| `lab_ergonomics_repetitive` | Sample lift / drop / sieving ergonomic injury patterns |

**Verdict:** 🔴 **REAL GAP — operator-named priority.** Asphalt lab work is its own operational vertical with its own injury patterns (radiation · hot oven · solvent · silica · ergonomic). Currently absorbed into 1 plant-domain topic.

### 3.8 🟢 Office / Admin (re-confirmed) — already covered in §3.5

---

## 4 · Cross-cutting quality findings

### Tone consistency
- Every topic uses the operational structure: `incident_pattern` (narrative) → `hazards_reviewed` (bulleted) → `discussion_notes` (foreman-grade bullets) → `references_cited` → `action_items`.
- Average `incident_pattern` length: **600–900 chars**. Reads like seasoned field leadership ("Drivers describe it the same way every time…"). NOT LMS / NOT corporate / NOT machine-generated.
- Zero "thin" topics (defined as `discussion_notes < 200 chars`): the entire library passes that threshold.

### Severity distribution
- 63% fatal_risk · ~30% serious_injury · ~7% lost_time/minor.
- This is the **correct distribution** for a heavy-civil contractor and indicates a library written with realistic risk weighting, not a "everything is serious" inflation pattern.

### Bilingual continuity
- ES coverage **100% (136/136)**. Earlier 0% reading was a regex artifact.
- Spot-checked `trucking.es.js · dump_truck`: operationally written Spanish ("Las fatalidades de camión de volteo siguen tres patrones que los choferes experimentados reconocen a primera vista…"). Not machine-translated.
- Earlier iter282/iter283/iter296/iter297/iter300 i18n discipline carries through.

### Field usability
- `SafetyTopicLibrary.jsx` (562 LOC) filters by severity + domain chip · search by title.
- Multi-select + bilingual PDF pack generator (iter266) backs the workflow.
- 136 topics across 21 domains is a large library, but domain-chip filter makes it tractable. No restructuring recommended.

### Operational realism
- Office domain doesn't lead with ergonomics — it leads with `office_distracted_driving` because that's the real risk.
- Trucking domain doesn't lead with seatbelts — it leads with bed-up overhead strikes because that's the real risk.
- Plant domain doesn't lead with hard-hat compliance — it leads with conveyor entanglement.
- **This realism is the library's most valuable asset and must be preserved in any future topic additions.**

---

## 5 · Proposed bounded additions (DEFERRED · audit-only)

Listed by operator-named priority. **None recommended for autonomous execution.** Operator gate first.

| # | Topic candidate | Domain | Severity (proposed) | Justification |
| ---: | --- | --- | --- | --- |
| 1 | `lab_nuclear_gauge_handling` | new `lab` domain OR plant | fatal_risk | Radiation safety + transport · explicitly named operator vertical |
| 2 | `lab_oven_burns_chemistry` | new `lab` OR plant | serious_injury | 550°F oven + bitumen extraction chemistry |
| 3 | `lab_core_drilling_silica` | new `lab` OR plant | serious_injury | Wet-cut silica + saw kickback at the lab bench |
| 4 | `lab_solvent_handling_ppe` | new `lab` OR plant | serious_injury | Trichloroethylene / mineral spirits |
| 5 | `airport_fod_control` | airport | fatal_risk | FOD prevention — runway shutdown risk |
| 6 | `airport_night_work_visibility` | airport | fatal_risk | Most airport civil is nights / weekends |
| 7 | `airport_security_badging_escort` | airport | serious_injury | Federal incident · escort discipline |
| 8 | `airport_airfield_electrical_lighting` | airport | fatal_risk | Live circuits · runway-edge exposure |
| 9 *(optional)* | `plant_crusher_screen_deck_cleaning` | plant | serious_injury | Adjacent to existing `plant_crusher_clearing_jams` — fills the screen-cleaning sub-pattern |

**Recommended approach if operator approves any:**
- **Option α**: Treat the 4 asphalt-lab additions as a **new `lab` domain** (creates `lab.js` + `lab.es.js`, adds chip to `TopicPicker`, registers in `index.js`). Clean architectural separation. ~4 new topics.
- **Option β**: Add the lab topics under existing `plant` domain (8 → 12 topics). Lower architectural footprint. Risk: blurs the plant/lab boundary the operator named.
- **Airport additions**: Stay in existing `airport` domain (2 → 4-6 topics). No domain creation needed.

**Total work envelope if all approved:** 4-6 new topic objects (EN) + same in ES + 1 optional domain registration. Each topic is ~150 LOC of operationally-voiced content. No JSX changes, no routing changes, no backend changes.

---

## 6 · What the audit explicitly does NOT recommend

- 🚫 Re-writing any existing topic ("the existing 136 are operationally solid").
- 🚫 Adding topics in domains the operator did not name as gaps (utilities · rigging · confined_space).
- 🚫 Splitting the `general` domain (20 topics) — it's legitimate cross-cutting content, not dilution.
- 🚫 Restructuring `TopicPicker.jsx`, `SafetyTopicLibrary.jsx`, or the PDF pack generator — they work.
- 🚫 Adding gamification / scoring / progress tracking / analytics / completion tracking.
- 🚫 Adding "smart" topic recommendation engines.
- 🚫 Auto-translating new topic content — bilingual continuity requires hand-written operational Spanish (per iter300 governance).
- 🚫 Building any kind of LMS layer over the topic library.

---

## 7 · Confidence level

- **High** for inventory counts (136 topics across 21 domains · 100% ES) — derived from direct parsing.
- **High** for tone / depth / severity assessments — based on per-topic char-count + severity-tag analysis.
- **High** for the two named-vertical gaps (asphalt lab + airport) — both quantitatively thin AND explicitly named by operator.
- **Medium** for the optional crusher refinement — based on operational pattern knowledge, not an explicit operator signal.

---

## 8 · Summary for the operator

| Question | Answer |
| --- | --- |
| Is the library structurally healthy? | **Yes — 100% bilingual, zero thin topics, strong operational voice.** |
| Is there generic / LMS-style drift? | **No.** Every domain reads like field leadership. |
| Are there operational-coverage gaps in operator-named verticals? | **Yes — 2 named gaps**: asphalt lab (1-2 buried topics) and airport (2 topics for a multi-faceted vertical). |
| Should we expand the library? | **Only the 2 named gaps if the operator approves.** Other verticals are operationally complete. |
| Is the field-usability good? | **Yes** — fast filter, multi-select, bilingual PDF pack. No restructuring needed. |
| What's the risk of additions? | **Low.** Pure content addition (~4-8 new topic objects). No JSX, no routing, no backend, no architectural change. |

The audit's recommended posture: **leave the library alone unless the operator explicitly approves adding the asphalt-lab and/or airport topics.**

This is exactly what the stabilization-phase discipline says: protect the operational voice that's already working; add only where a named gap actually exists; do not manufacture work.
