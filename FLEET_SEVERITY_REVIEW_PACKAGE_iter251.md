# Fleet Defect Severity Review Package · iter251

**Status:** v1.1-approved-2026-05-19
**Approved:** 2026-05-19 · Operator (Jaymn) · per SEVERITY_RULINGS_iter251.md + CFR § 396.11 refinement pass
**Approval record:** `/app/SEVERITY_RULINGS_iter251.md`
**Generated from:** `/app/backend/fleet_defect_severity.py` + `/app/backend/checklists_fleet.py`
**Audience:** Safety · Shop · Operations · Dispatch leadership
**Purpose:** Redline operational disagreements BEFORE production reliance.

This document drives whether a failed DVIR / weekly inspection puts a truck/trailer **OUT OF SERVICE** (truck cannot operate until shop repair + dispatch re-clearance) or **MONITOR** (truck still operates · shop sees the defect · driver continues with caution).

Drivers do NOT pick severity in the field — this table picks it for them, eliminating in-field judgement calls.

---

## Summary

- **Total classified items:** 109
- **OUT OF SERVICE classifications:** 74
- **MONITOR classifications:** 35
- **OOS-to-monitor ratio:** 2.11 (conservative bias toward OOS)
- **Items flagged UNCERTAIN pending Safety review:** 0
- **Items missing severity classification:** 0 (must be zero before deploy)
- **Orphan severity entries (not used by any checklist):** 0
- **Items missing metadata (rationale / regulation_ref):** 0

---

## Per-Kind Coverage

| Inspection Kind | Truck Items | Trailer Items | Total | Classified | Coverage |
|---|---|---|---|---|---|
| `dvir` (Daily DVIR) | 84 | 25 | 109 | 109 | 100.0% |
| `weekly_lead` (Weekly Lead Driver Inspection) | 9 | 0 | 9 | 9 | 100.0% |
| `weekly_emergency` (Weekly Emergency Equipment Inspection) | 16 | 0 | 16 | 16 | 100.0% |

---

## Full Classification by Category

**Legend:** 🛑 = OUT OF SERVICE · 👁 = MONITOR · ⚠️ = uncertain (Safety review)

### Brakes · 8 OOS · 0 MONITOR

#### 🛑 `Brake chamber / slack adjuster — no visible damage · slack adjuster travel within normal range`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.47 · CVSA OOS §1.d
- **Rationale:** Out-of-adjustment slack adjusters or damaged brake chambers are the most common brake-stroke OOS finding at roadside. Driver checks visually for damage + extended travel · the precise stroke measurement is a shop function. (v1.1 wording clarification 2026-05-19 PM)

#### 🛑 `Brake hoses / lines — no cracks · no abrasion · no leaks`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.45
- **Rationale:** Damaged brake lines lead to sudden air loss or brake fluid loss. OOS until repaired.

#### 🛑 `Brake warning light / low-air buzzer — operates correctly`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.51
- **Rationale:** Driver must have audible/visual warning when air pressure drops below safe threshold. Inoperable warning system masks impending brake failure.

#### 🛑 `Parking brake — holds truck against engine torque`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.41
- **Rationale:** A non-functioning parking brake creates a rollaway hazard particularly on the grades and yard slopes MASCI operates on. Always OOS.

#### 🛑 `Service brakes — apply firmly · stop straight · no pulling`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.40 · CVSA OOS §1.b
- **Rationale:** Service brake failure is the single largest OOS category in CVSA roadside inspections. Inoperable service brake on any axle or stopping-distance failure removes a CMV from service.

#### 🛑 `Trailer brake hoses — no cracks · no abrasion`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.45
- **Rationale:** Brake line integrity · OOS.

#### 🛑 `Trailer hand valve — applies trailer service brakes from tractor · releases fully`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.43 · CVSA OOS §1.b
- **Rationale:** Trailer brake control via tractor hand valve is part of the combined-vehicle braking capacity. Failure renders the combination OOS even if tractor brakes are fine. (v1.1 wording clarification 2026-05-19 PM)

#### 🛑 `Trailer service brakes — engage · release · no drag`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.43 · CVSA OOS §1.b
- **Rationale:** Trailer brake failure compromises combination braking. OOS.


### Tires · 7 OOS · 1 MONITOR

#### 🛑 `Drive / trailer tire tread depth — ≥ 2/32" across full width`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.75(d) · CVSA OOS §6.b
- **Rationale:** Drive/trailer tires below 2/32" tread depth · federal OOS minimum.

#### 🛑 `Steer tire tread depth — ≥ 4/32" across full width`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.75(c) · CVSA OOS §6.a
- **Rationale:** Steer tires below 4/32" tread depth lose wet-weather grip and steering control. Federal OOS minimum.

#### 🛑 `Tire — no sidewall bulge · no exposed cord / belt / ply · no severe cut`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.75(a)(2)(3) · CVSA OOS §6.d
- **Rationale:** Sidewall bulge/cut OR exposed cord/belt/ply indicates compromised tire structural integrity · imminent catastrophic failure risk. Always OOS. (v1.1 · consolidated 2 prior items 2026-05-19 PM)

#### 🛑 `Tire — properly inflated · no audible leak · no flat`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.75(h)
- **Rationale:** Severe under-inflation generates heat and risks blowout · audible leak indicates active deflation · flat tire is unsafe to operate. OOS until repaired. (v1.1 · consolidated 2 prior items 2026-05-19 PM)

#### 🛑 `Trailer tire tread — ≥ 2/32" across full width`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.75(d) · CVSA OOS §6.b
- **Rationale:** Federal OOS minimum.

#### 🛑 `Trailer tire — no exposed cord / belt / sidewall damage`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.75 · CVSA OOS §6.d
- **Rationale:** Imminent failure risk. OOS.

#### 🛑 `Trailer tire — properly inflated · no audible leak`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.75(h)
- **Rationale:** Active deflation. OOS.

#### 👁 `Tire — minor sidewall scuff / cosmetic`
- **Severity:** MONITOR
- **Reference:** operational
- **Rationale:** Cosmetic scuff with no structural compromise is not an FMCSA defect. Monitor so shop tracks wear pattern over time.


### Wheels · 4 OOS · 1 MONITOR

#### 🛑 `Wheel rim — no cracks · no welds · no severe corrosion`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.205
- **Rationale:** Cracked or welded rims fail under load. OOS.

#### 🛑 `Wheel — all lug nuts present`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.205 · CVSA OOS §7.a
- **Rationale:** Any missing lug nut is OOS · risk of wheel separation.

#### 🛑 `Wheel — all lug nuts tight · no loose / clean ring`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.205 · CVSA OOS §7.a
- **Rationale:** Loose lug nuts (telltale rust ring) precede wheel separation. OOS.

#### 🛑 `Wheel — no oil / grease leak from hub seal`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.207
- **Rationale:** Hub seal leak indicates wheel bearing problem · risk of bearing seizure or wheel separation. OOS.

#### 👁 `Wheel — no surface rust streaks (cosmetic)`
- **Severity:** MONITOR
- **Reference:** operational
- **Rationale:** Surface rust is cosmetic and doesn't impair function. Monitor for shop tracking.


### Steering · 3 OOS · 1 MONITOR

#### 🛑 `Power steering — fluid AT or ABOVE MIN · normal effort · no active drip`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.209 · CVSA OOS criteria
- **Rationale:** Active drip / fluid below MIN / abnormal effort / pump whine = imminent steering loss · OOS. (Ruling #1 · 2026-05-19)

#### 🛑 `Steering linkage / drag link / pitman arm — no missing or broken parts`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.209 · CVSA OOS §10
- **Rationale:** Missing or broken steering components = imminent loss of control. Always OOS.

#### 🛑 `Steering wheel free play — within spec (≤ 10° on light truck · ≤ 30° on heavy)`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.209 · CVSA OOS §10
- **Rationale:** Excessive steering free play indicates worn linkage and impaired directional control. OOS.

#### 👁 `Power steering — stable seep / weep · normal effort · fluid AT MIN or above`
- **Severity:** MONITOR
- **Reference:** 49 CFR § 393.209 (operational threshold)
- **Rationale:** Stable seep without active drip + normal steering effort + fluid at or above MIN is Monitor · 5-day shop window. Active drip, abnormal effort, pump squeal, or fluid below MIN escalates to OOS. (Ruling #1 · 2026-05-19)


### Suspension · 2 OOS · 0 MONITOR

#### 🛑 `Suspension — air bags inflate · no leaks · no severe sag`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.207
- **Rationale:** Air suspension failure changes ride height and brake geometry. OOS.

#### 🛑 `Suspension — leaf springs · u-bolts · shackles intact`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.207 · CVSA OOS §9
- **Rationale:** Broken springs or missing U-bolts compromise axle integrity. OOS.


### Structural · 5 OOS · 1 MONITOR

#### 🛑 `Frame — no cracks · no severe rust-through`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.201 · CVSA OOS §3
- **Rationale:** Frame cracks are structural failures · always OOS.

#### 🛑 `Trailer cross members — no broken / missing`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.201
- **Rationale:** Load floor integrity · OOS.

#### 🛑 `Trailer floor — no major holes · structurally sound`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.201
- **Rationale:** Load drop or worker fall-through risk · OOS.

#### 🛑 `Trailer frame — no cracks · no severe rust`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.201 · CVSA OOS §3
- **Rationale:** Structural failure risk. OOS.

#### 🛑 `Trailer headboard / bulkhead — intact`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.106
- **Rationale:** Load-shift protection for cab · OOS if compromised.

#### 👁 `Trailer mudflaps / spray suppression — present · secure · no major tears`
- **Severity:** MONITOR
- **Reference:** 49 CFR § 393.86 · state regs
- **Rationale:** Mudflaps protect following traffic from stones and spray kicked up from drive / trailer tires. Federal rule plus most state codes require functional flaps on commercial trailers. Monitor for partial tear, missing flap, or loose hardware · escalates to OOS if completely absent / dragging on highway. (v1.1 commercial-vehicle addition 2026-05-19 PM)


### Air System · 4 OOS · 0 MONITOR

#### 🛑 `Air pressure — builds to ≥ 95 psi within normal time`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.50 · CVSA OOS §1.f
- **Rationale:** Build-time failure indicates compressor or governor issue · brake performance compromised. OOS.

#### 🛑 `Air system — pressure holds with engine off · ≤ 4 psi/min loss`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.50 · CVSA OOS §1.c
- **Rationale:** Excessive leak-down rate is a federal OOS criterion · risk of brake failure mid-trip.

#### 🛑 `Airlines / gladhands — no audible leaks · seals intact`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.45 · CVSA OOS §1
- **Rationale:** Audible leak = active air loss. OOS until repaired.

#### 🛑 `Low air warning — buzzer + light at ≤ 60 psi`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.51
- **Rationale:** Required warning system. OOS.


### Coupling · 6 OOS · 0 MONITOR

#### 🛑 `Fifth wheel — locked · jaws fully engaged on kingpin`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.70 · CVSA OOS §2.a
- **Rationale:** Unlocked or partially engaged fifth wheel = trailer separation risk. Always OOS.

#### 🛑 `Fifth wheel — mounting bolts present · no cracks`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.70 · CVSA OOS §2.c
- **Rationale:** Mounting failures lead to fifth-wheel separation under load. OOS.

#### 🛑 `Pintle hook — locked · safety pin in place`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.70
- **Rationale:** Pintle hitch failure = trailer separation. OOS.

#### 🛑 `Safety chains — attached · no broken links · proper rating`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.71
- **Rationale:** Required secondary attachment · OOS.

#### 🛑 `Trailer coupler / kingpin — no cracks · no excess wear`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.70 · CVSA OOS §2
- **Rationale:** Coupler failure = trailer separation. OOS.

#### 🛑 `Trailer safety chains — attached · no broken links`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.71
- **Rationale:** Secondary attachment · OOS.


### Landing Gear · 1 OOS · 1 MONITOR

#### 🛑 `Landing gear — cranks freely · pads in place · no damage`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.207
- **Rationale:** Landing gear failure during drop or pickup is property-damage + worker-injury risk. OOS.

#### 👁 `Landing gear — minor cosmetic wear`
- **Severity:** MONITOR
- **Reference:** operational
- **Rationale:** Cosmetic only · monitor.


### Lights · 6 OOS · 7 MONITOR

#### 🛑 `Brake lights — both sides functional`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.25 · CVSA OOS §8.a
- **Rationale:** Both-side brake light failure is an OOS criterion. Critical for trailing-vehicle awareness.

#### 🛑 `Headlights — both low-beams functional · at least one high-beam functional`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.24 · CVSA OOS criteria
- **Rationale:** Both low-beams must be operational at all times. At least one high-beam must function for night ops. Any low-beam failure or both high-beams out = OOS. (Ruling #2 · 2026-05-19)

#### 🛑 `Headlights — low beam · both sides functional`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.24
- **Rationale:** Required lighting for night operation. Loss of either side compromises visibility. OOS for night ops.

#### 🛑 `Tail lights — both sides functional`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.25 · CVSA OOS §8.a
- **Rationale:** Required for rear visibility. Both-side failure is OOS.

#### 🛑 `Trailer brake lights — both sides functional`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.25 · CVSA OOS §8.a
- **Rationale:** Both-side failure is OOS · critical signal to following traffic.

#### 🛑 `Trailer tail lights — both sides functional`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.25 · CVSA OOS §8.a
- **Rationale:** Both-side failure is OOS.

#### 👁 `Clearance / marker lights — all functional`
- **Severity:** MONITOR
- **Reference:** 49 CFR § 393.11
- **Rationale:** Loss of one or two marker lights doesn't impair operational safety in daylight. Monitor; replace at next shop touch.

#### 👁 `Headlights — single high-beam out · both low-beams functional · daylight-only ops`
- **Severity:** MONITOR
- **Reference:** 49 CFR § 393.24 (operational tier)
- **Rationale:** Single high-beam failure with both low-beams functional is Monitor for daylight-only paving/haul ops · 3-day shop window. Escalates to OOS if night work assigned. (Ruling #2 · 2026-05-19)

#### 👁 `Identification lights (3-light cluster · top of cab) — all functional`
- **Severity:** MONITOR
- **Reference:** 49 CFR § 393.11
- **Rationale:** Required commercial lighting · top-of-cab 3-light cluster signals vehicle width to following traffic. Conservative monitor since they don't impede operation. (v1.1 wording clarification 2026-05-19 PM)

#### 👁 `License plate light — functional`
- **Severity:** MONITOR
- **Reference:** state regs
- **Rationale:** State-level requirement · monitor.

#### 👁 `Trailer ABS lamp — operates per startup cycle`
- **Severity:** MONITOR
- **Reference:** 49 CFR § 393.55
- **Rationale:** ABS system status indicator · monitor (system has fallback to standard braking).

#### 👁 `Trailer clearance / marker lights — all functional`
- **Severity:** MONITOR
- **Reference:** 49 CFR § 393.11
- **Rationale:** Conspicuity · monitor.

#### 👁 `Trailer identification light cluster — functional`
- **Severity:** MONITOR
- **Reference:** 49 CFR § 393.11
- **Rationale:** Compliance lighting · monitor.


### Signals · 5 OOS · 1 MONITOR

#### 🛑 `4-way hazard flashers — operate · synchronized`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.25(d)
- **Rationale:** Required emergency warning device. OOS.

#### 🛑 `Strobes / beacons — all flash patterns operational (work-zone / lane closure / paving / shoulder / airport ops)`
- **Severity:** OOS
- **Reference:** MASCI work-zone struck-by control · OSHA 1926 Subpart G
- **Rationale:** Work-zone struck-by is a top OSHA fatality cause in highway construction. Strobe/beacon is a primary worker-protection control · partial pattern = degraded control. OOS for any unit assigned to MOT, paving train, lane closure, shoulder, or airport ops. (Ruling #3 · 2026-05-19)

#### 🛑 `Strobes / beacons — at least one operational`
- **Severity:** OOS
- **Reference:** MASCI operational requirement
- **Rationale:** Total beacon loss in active work zones eliminates upstream-driver warning · OOS.

#### 🛑 `Trailer turn signals — left + right functional`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.25
- **Rationale:** Required for lane changes/turns. OOS.

#### 🛑 `Turn signals — left + right · front + rear functional`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.25
- **Rationale:** Required for safe lane changes/turns. Total side failure is OOS.

#### 👁 `Strobes / beacons — partial pattern acceptable for yard-only / shop-shuffle moves`
- **Severity:** MONITOR
- **Reference:** MASCI operational tier
- **Rationale:** Partial flash pattern acceptable for yard-only or shop-shuffle moves with no work-zone exposure · Monitor with 5-day shop window. Escalates to OOS the moment unit is assigned to work-zone ops. (Ruling #3 · 2026-05-19)


### Alarms · 2 OOS · 0 MONITOR

#### 🛑 `Backup alarm — audible when reverse engaged`
- **Severity:** OOS
- **Reference:** OSHA 1926.601(b)(4) · ANSI Z245.1
- **Rationale:** Required safety device for vehicles with obstructed rear vision. Pedestrian-strike risk. OOS.

#### 🛑 `Raised-bed alarm — audible when bed raised`
- **Severity:** OOS
- **Reference:** MASCI operational standard
- **Rationale:** Critical for power-line strike avoidance and accidental drive-away with bed raised. OOS.


### Horn · 1 OOS · 0 MONITOR

#### 🛑 `Horn — sounds at normal volume`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.81
- **Rationale:** Required equipment. OOS.


### Mirrors · 1 OOS · 1 MONITOR

#### 🛑 `Mirrors — both sides present · adjustable · clear visibility`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.80
- **Rationale:** Required equipment. Total mirror loss on either side is OOS.

#### 👁 `Mirror — minor crack / chip with visible image`
- **Severity:** MONITOR
- **Reference:** operational
- **Rationale:** Cracked mirror that still gives a usable reflected image is monitor-level. Schedule replacement.


### Glass · 1 OOS · 1 MONITOR

#### 🛑 `Windshield — no cracks in driver line of sight`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.60 · CVSA OOS §11.a
- **Rationale:** Cracks in driver sight lines impair visibility. OOS.

#### 👁 `Windshield — minor cracks / pitting outside line of sight`
- **Severity:** MONITOR
- **Reference:** 49 CFR § 393.60
- **Rationale:** Cosmetic damage outside vision area is monitor. Replace at next shop visit.


### Wipers · 2 OOS · 2 MONITOR

#### 🛑 `Driver-side wiper — sweeps cleanly · no streaking · no torn blade`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.78 · CVSA OOS criteria
- **Rationale:** Driver-side visibility is non-negotiable · any streaking, torn blade, or inop wiper on driver side = OOS. Florida/Texas storms develop fast. (Ruling #4 · 2026-05-19)

#### 🛑 `Passenger-side wiper — sweeps cleanly when rain forecast in shift window`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.78
- **Rationale:** Passenger-side wiper must be functional if rain is forecast in the shift window. Driver checks forecast at DVIR submission. (Ruling #4 · 2026-05-19)

#### 👁 `Passenger-side wiper — minor streak acceptable · dry forecast in shift window · 3-day shop window`
- **Severity:** MONITOR
- **Reference:** 49 CFR § 393.78 (operational tier)
- **Rationale:** Minor streak on passenger-side with dry forecast is Monitor with 3-day shop window. Escalates to OOS if forecast updates to rain. (Ruling #4 · 2026-05-19)

#### 👁 `Washer fluid — sprays · reservoir not empty`
- **Severity:** MONITOR
- **Reference:** operational
- **Rationale:** Comfort/maintenance · monitor.


### Hydraulic · 3 OOS · 1 MONITOR

#### 🛑 `Hydraulic system — no active drip · no leak below MIN reservoir · no leak on bed-lift / boom / outrigger / brake-assist circuit`
- **Severity:** OOS
- **Reference:** OSHA 1926.602 · operational
- **Rationale:** Active drip (forms a drop within 60 sec), any leak from brake-assist line, any leak from bed-lift / boom / outrigger pressure circuit, or fluid below MIN reservoir = OOS. Bed-lift failure under load = OSHA-reportable crush hazard. (Ruling #6 · 2026-05-19)

#### 🛑 `Hydraulic — bed raise + lower smoothly · no drift`
- **Severity:** OOS
- **Reference:** operational
- **Rationale:** Bed drift while raised is power-line and crush hazard · OOS.

#### 🛑 `Trailer hydraulic system — no leaks · raises + lowers`
- **Severity:** OOS
- **Reference:** operational · OSHA
- **Rationale:** Hydraulic dump-trailer failure is operational + fire risk. OOS.

#### 👁 `Hydraulic system — stable seep / film without active drip · reservoir AT or ABOVE MIN · not on load-supporting circuit`
- **Severity:** MONITOR
- **Reference:** OSHA 1926.602 (operational tier)
- **Rationale:** Stable seep or film without drip formation + reservoir at or above MIN + not on a load-supporting / brake-assist circuit = Monitor with 5-day shop window. (Ruling #6 · 2026-05-19)


### Pto · 0 OOS · 1 MONITOR

#### 👁 `PTO engages + disengages normally`
- **Severity:** MONITOR
- **Reference:** operational
- **Rationale:** PTO issues stop the work the truck is dispatched for but don't make the truck unsafe to drive. Monitor.


### Fluids · 3 OOS · 2 MONITOR

#### 🛑 `Coolant — proper level · no major leak`
- **Severity:** OOS
- **Reference:** operational
- **Rationale:** Major coolant loss = engine seizure risk. OOS.

#### 🛑 `Engine oil — proper level · no major leak`
- **Severity:** OOS
- **Reference:** operational
- **Rationale:** Major oil leak = engine failure or fire risk. OOS.

#### 🛑 `Fuel — no leaks · cap secure`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.65 · CVSA OOS §4
- **Rationale:** Fuel leak = fire hazard · federal OOS criterion.

#### 👁 `Transmission fluid — proper level`
- **Severity:** MONITOR
- **Reference:** operational
- **Rationale:** Slow consumption is monitor-level · severe loss → engine/trans damage but not immediate roadway danger.

#### 👁 `Windshield washer fluid`
- **Severity:** MONITOR
- **Reference:** operational
- **Rationale:** Comfort · monitor.


### Emergency Equipment · 2 OOS · 5 MONITOR

#### 🛑 `Fire extinguisher — present · charged · sealed · tag current`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.95(a) · CVSA OOS §4.c
- **Rationale:** Federal-required equipment · missing/discharged is OOS.

#### 🛑 `Reflective triangles — 3 present · case intact`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.95(f)
- **Rationale:** Federal-required emergency equipment · missing is OOS.

#### 👁 `Fire extinguisher — minor scuff / tag near expiry`
- **Severity:** MONITOR
- **Reference:** 49 CFR § 393.95(a)
- **Rationale:** Functional but cosmetic/tag-renewal needed · monitor.

#### 👁 `First aid kit — present · sealed · contents not expired`
- **Severity:** MONITOR
- **Reference:** OSHA 1910.151 · MASCI policy
- **Rationale:** Operational + worker-comp expectation · monitor.

#### 👁 `Reflective safety vest — present in cab`
- **Severity:** MONITOR
- **Reference:** OSHA 1926.651 · MUTCD
- **Rationale:** Required PPE for work-zone exits · monitor.

#### 👁 `Reflective triangles — case scuffed (functional)`
- **Severity:** MONITOR
- **Reference:** 49 CFR § 393.95(f)
- **Rationale:** Equipment functional, cosmetic only · monitor.

#### 👁 `Spare fuses — kit present`
- **Severity:** MONITOR
- **Reference:** 49 CFR § 393.95(c)
- **Rationale:** Required (where fuses used). Monitor.


### Reflectors · 0 OOS · 2 MONITOR

#### 👁 `Reflectors — clean · undamaged · in place`
- **Severity:** MONITOR
- **Reference:** 49 CFR § 393.13 (conspicuity)
- **Rationale:** Conspicuity loss is monitor-level unless severe (handled by 'reflective tape' trailer item).

#### 👁 `Trailer reflective tape (DOT conspicuity) — clean · undamaged`
- **Severity:** MONITOR
- **Reference:** 49 CFR § 393.13
- **Rationale:** Conspicuity tape · monitor.


### Tarp · 1 OOS · 1 MONITOR

#### 🛑 `Tarp system — deploys + retracts · no tear > 6"×6" · functional on units assigned to aggregate / asphalt / dust-producing load haul`
- **Severity:** OOS
- **Reference:** Tex. Transp. Code § 725.021 · 49 CFR § 393.100 (load securement)
- **Rationale:** Functional tarp + no tear larger than 6"×6" is required for any unit assigned to aggregate, asphalt, or dust-producing load haul. Uncovered load = state ticket + struck-by debris on highway. OOS for load-haul ops. (Ruling #9 · 2026-05-19)

#### 👁 `Tarp system — minor tear < 6"×6" OR unit assigned to empty / equipment / non-dust haul · 5-day shop window`
- **Severity:** MONITOR
- **Reference:** MASCI operational tier
- **Rationale:** Minor tear (< 6"×6") OR unit assigned to empty / equipment / non-dust haul = Monitor with 5-day shop window. Escalates to OOS the moment unit reassigned to aggregate / asphalt / dust haul. (Ruling #9 · 2026-05-19)


### Interior · 3 OOS · 3 MONITOR

#### 🛑 `Defroster — functional when ambient ≤ 40°F or precipitation forecast in shift window`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.79
- **Rationale:** Defroster must be operational when ambient ≤ 40°F or precipitation forecast · driver cannot safely clear windshield/fogging without it. (Ruling #7 · 2026-05-19)

#### 🛑 `Oil pressure & coolant temp gauges OR equivalent ECM warning system functional`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.51 (spirit) · operational
- **Rationale:** Engine protection signal (oil pressure + coolant temp) must be functional via dash gauge OR ECM warning system. Loss of both = engine destruction risk. OOS. (Ruling #8 · 2026-05-19)

#### 🛑 `Seat belt — present · functional · no fraying`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.93
- **Rationale:** Required occupant restraint · OOS if non-functional.

#### 👁 `Cab heater — functional · escalates to OOS if window fogging affects visibility`
- **Severity:** MONITOR
- **Reference:** 49 CFR § 393.79 (operational tier)
- **Rationale:** Cab heater inop is driver-comfort Monitor only when above 40°F + dry forecast + no fogging. Escalates to OOS if fogging conditions affect windshield visibility (visibility is the actual safety concern, not comfort). 7-day shop window. (Ruling #7 · 2026-05-19)

#### 👁 `Dash gauges (oil / temp) inop on units with ECM check-engine + fault display fully functional · 14-day shop window`
- **Severity:** MONITOR
- **Reference:** 49 CFR § 393.51 (operational tier · modern truck)
- **Rationale:** On modern trucks (≥ 2010 model year) with functional ECM check-engine + fault display, analog dash gauges are supplemental · inop gauges acceptable for Monitor with 14-day shop window. Older / non-ECM trucks remain OOS for oil-pressure or temp gauge failure. (Ruling #8 · 2026-05-19)

#### 👁 `Fuel gauge — functional · driver may estimate by miles · 7-day shop window`
- **Severity:** MONITOR
- **Reference:** operational
- **Rationale:** Fuel gauge inop is Monitor only · driver can estimate by miles + fuel-up records. 7-day shop window. (Ruling #8 · 2026-05-19)


### Body · 1 OOS · 2 MONITOR

#### 🛑 `Body — no frame/cab-mount fracture · no projecting metal or sharp edge · no loose panel/door · no rust-through on cab floor or fuel tank · no damage blocking mirror or windshield visibility`
- **Severity:** OOS
- **Reference:** CVSA OOS criteria · 49 CFR § 393.201 (structural)
- **Rationale:** Objective 5-test rubric replacing vague 'severe damage' wording. OOS only if damage meets one of: (a) frame/cab-mount fracture, (b) projecting metal hazardous to ground personnel, (c) loose panel/door/component at risk of falling, (d) rust-through on cab floor or fuel tank, (e) visibility-blocking damage to mirrors or windshield. Cosmetic damage = Monitor only. (Ruling #5 · 2026-05-19)

#### 👁 `Body — cosmetic dings · scrapes · paint`
- **Severity:** MONITOR
- **Reference:** operational
- **Rationale:** Cosmetic only · monitor for accountability tracking and dispute defense.

#### 👁 `Trailer body — cosmetic damage`
- **Severity:** MONITOR
- **Reference:** operational
- **Rationale:** Cosmetic only · monitor for accountability.


### Exhaust · 1 OOS · 0 MONITOR

#### 🛑 `Exhaust system — no leaks ahead of muffler · no fumes entering cab`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.83 · CVSA OOS criteria
- **Rationale:** Exhaust leaks ahead of the muffler can introduce carbon monoxide into the cab · CO poisoning is a documented commercial-driver fatality cause. Federal rule requires discharge to the outside atmosphere. OOS until repaired. (v1.1 commercial-vehicle addition 2026-05-19 PM)


### Electrical · 1 OOS · 0 MONITOR

#### 🛑 `Battery — securely mounted · no severe corrosion · cables tight`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.30
- **Rationale:** Battery hold-down failure can drop the battery into the engine bay; severe corrosion can break the connection under load creating no-start on remote routes or interrupting safety lighting. OOS for any unsecured battery / heavy corrosion / loose cable. (v1.1 commercial-vehicle addition 2026-05-19 PM)


### Cargo Securement · 1 OOS · 0 MONITOR

#### 🛑 `Cargo securement — chains / binders / straps rated and applied per load (flatbed / service truck)`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.100 · CVSA OOS criteria
- **Rationale:** Load shedding from a CMV is a leading struck-by fatality cause for following traffic. Securement rule applies to any rigid cargo (equipment, pipe, pallets) on flatbed / service truck. Each tie-down rated; minimum count per length per § 393.100. OOS if missing or under-rated. (v1.1 commercial-vehicle addition 2026-05-19 PM)


### Markings · 0 OOS · 1 MONITOR

#### 👁 `DOT number / company markings — legible · readable from 50 ft`
- **Severity:** MONITOR
- **Reference:** 49 CFR § 390.21
- **Rationale:** Federally required CMV identification · legible from 50 feet · letters at least 2 inches tall. Monitor for fading / dirt buildup that obscures the marking. (v1.1 commercial-vehicle addition 2026-05-19 PM)


---

## Operational Sign-Off

Before production reliance, each of the following must redline + sign:

- [ ] **Safety** · approves overall OOS classifications · confirms uncertainty-flagged items
- [ ] **Shop** · confirms repair-routing accuracy · confirms ambiguity-threshold definitions (e.g. "severe damage", "major leak")
- [ ] **Operations** · confirms operational impact estimates (false-positive OOS productivity hit acceptable)
- [ ] **Dispatch leadership** · confirms re-clearance authority + workflow

Severity table currently stamped **`v1.1-approved-2026-05-19`**. After a re-rulings cycle, bump the version stamp + add a new dated rulings record (mirroring `/app/SEVERITY_RULINGS_iter251.md`) and re-run this generator + audit endpoint.

---

## Editing Workflow

1. Operator/Safety propose a change (severity flip, rationale edit, item add/remove).
2. Edit `/app/backend/fleet_defect_severity.py` (table) and the META block in the same file.
3. Run `python3 /app/scripts/generate_fleet_severity_review.py` to regenerate this document.
4. Run `python3 -m pytest /app/backend/tests/test_iter251_fleet_ops_foundation.py /app/backend/tests/test_iter251_severity_audit.py` to validate.
5. Hit `GET /api/admin/fleet/severity-audit` with admin token to confirm verdict.
6. Submit to the operator-side sign-off list above before deploying.

---

*This file is regenerated by `/app/scripts/generate_fleet_severity_review.py`. Do not edit directly — edit `fleet_defect_severity.py` and rerun the generator.*