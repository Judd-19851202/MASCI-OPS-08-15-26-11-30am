# Fleet Defect Severity Review Package · iter251

**Status:** v1-DRAFT-pending-safety-review
**Generated from:** `/app/backend/fleet_defect_severity.py` + `/app/backend/checklists_fleet.py`
**Audience:** Safety · Shop · Operations · Dispatch leadership
**Purpose:** Redline operational disagreements BEFORE production reliance.

This document drives whether a failed DVIR / weekly inspection puts a truck/trailer **OUT OF SERVICE** (truck cannot operate until shop repair + dispatch re-clearance) or **MONITOR** (truck still operates · shop sees the defect · driver continues with caution).

Drivers do NOT pick severity in the field — this table picks it for them, eliminating in-field judgement calls.

---

## Summary

- **Total classified items:** 97
- **OUT OF SERVICE classifications:** 69
- **MONITOR classifications:** 28
- **OOS-to-monitor ratio:** 2.46 (conservative bias toward OOS)
- **Items flagged UNCERTAIN pending Safety review:** 9
- **Items missing severity classification:** 0 (must be zero before deploy)
- **Orphan severity entries (not used by any checklist):** 0
- **Items missing metadata (rationale / regulation_ref):** 0

### ⚠️ ITEMS PENDING SAFETY DECISION
These items are classified but Safety must confirm the classification before production reliance. Each carries an `uncertainty_note` describing the operational tension.

- **`Body — no severe damage affecting safe operation`** · current: **OOS** (body) · ref: `operational`
  - *Subjective threshold · Safety to define 'severe' rubric.*
- **`Cab — dash gauges functional (oil pressure · temp · fuel)`** · current: **OOS** (interior) · ref: `49 CFR § 393.51`
  - *Modern trucks with computer-fault warning may be more permissive · Shop to confirm.*
- **`Cab — heater / defroster operational (cold/wet weather)`** · current: **MONITOR** (interior) · ref: `49 CFR § 393.79`
  - *Seasonal sensitivity · Safety to set wet/cold OOS policy.*
- **`Headlights — high beam · both sides functional`** · current: **OOS** (lights) · ref: `49 CFR § 393.24`
  - *Single high-beam out (low still functional) may be MONITOR in daytime ops. Safety to set policy.*
- **`Hydraulic system — no visible leaks`** · current: **OOS** (hydraulic) · ref: `operational · OSHA`
  - *'Visible leak' threshold needs Shop guidance · pinhole vs active drip differs operationally.*
- **`Power steering — no leaks · fluid at proper level · normal effort`** · current: **OOS** (steering) · ref: `49 CFR § 393.209`
  - *Borderline case: a minor weep with normal effort may be MONITOR. Safety to confirm threshold.*
- **`Strobes / beacons — all flash patterns operational`** · current: **MONITOR** (signals) · ref: `MASCI operational requirement`
  - *MASCI work zone exposure may justify OOS for any beacon loss. Safety + Ops to confirm.*
- **`Tarp system — deploys + retracts · no major tears`** · current: **MONITOR** (tarp) · ref: `MASCI policy · state load-cover regs`
  - *State load-cover requirements may upgrade this to OOS for some loads · Safety/Ops to confirm.*
- **`Wipers — both blades sweep windshield cleanly · no streaking`** · current: **OOS** (wipers) · ref: `49 CFR § 393.78`
  - *Dry-summer days a wiper issue is arguably monitor. Conservative OOS chosen.*

---

## Per-Kind Coverage

| Inspection Kind | Truck Items | Trailer Items | Total | Classified | Coverage |
|---|---|---|---|---|---|
| `dvir` (Daily DVIR) | 74 | 23 | 97 | 97 | 100.0% |
| `weekly_lead` (Weekly Lead Driver Inspection) | 10 | 0 | 10 | 10 | 100.0% |
| `weekly_emergency` (Weekly Emergency Equipment Inspection) | 16 | 0 | 16 | 16 | 100.0% |

---

## Full Classification by Category

**Legend:** 🛑 = OUT OF SERVICE · 👁 = MONITOR · ⚠️ = uncertain (Safety review)

### Brakes · 8 OOS · 0 MONITOR

#### 🛑 `Brake chamber / slack adjuster — no visible damage · proper stroke`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.47 · CVSA OOS §1.d
- **Rationale:** Out-of-adjustment slack adjusters or damaged brake chambers are the most common brake-stroke OOS finding at roadside. Conservative OOS.

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

#### 🛑 `Trailer air brakes — engage with hand valve · release fully`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.43 · CVSA OOS §1.b
- **Rationale:** Trailer brake control is part of the combined-vehicle braking capacity. Failure renders the combination OOS even if tractor brakes are fine.

#### 🛑 `Trailer brake hoses — no cracks · no abrasion`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.45
- **Rationale:** Brake line integrity · OOS.

#### 🛑 `Trailer service brakes — engage · release · no drag`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.43 · CVSA OOS §1.b
- **Rationale:** Trailer brake failure compromises combination braking. OOS.


### Tires · 9 OOS · 1 MONITOR

#### 🛑 `Drive / trailer tire tread depth — ≥ 2/32" across full width`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.75(d) · CVSA OOS §6.b
- **Rationale:** Drive/trailer tires below 2/32" tread depth · federal OOS minimum.

#### 🛑 `Steer tire tread depth — ≥ 4/32" across full width`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.75(c) · CVSA OOS §6.a
- **Rationale:** Steer tires below 4/32" tread depth lose wet-weather grip and steering control. Federal OOS minimum.

#### 🛑 `Tire — no audible air leak`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.75
- **Rationale:** Audible leak indicates active deflation. OOS until repaired.

#### 🛑 `Tire — no exposed cord / belt / ply`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.75(a)(3) · CVSA OOS §6.d
- **Rationale:** Exposed cord/belt indicates imminent catastrophic tire failure. Always OOS.

#### 🛑 `Tire — no severe sidewall damage (bulge / cut / cord exposed)`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.75(a)(2)
- **Rationale:** Sidewall bulges/cuts compromise tire structural integrity. Always OOS.

#### 🛑 `Tire — properly inflated (no flat · no severe under-inflation)`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.75(h)
- **Rationale:** Severe under-inflation generates heat and risks blowout. Flat tire is unsafe to operate. OOS.

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


### Steering · 3 OOS · 0 MONITOR

#### 🛑 ⚠️ `Power steering — no leaks · fluid at proper level · normal effort`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.209
- **Rationale:** Loss of power steering mid-maneuver greatly increases driver effort and crash risk. OOS for major leaks or pump failure.
- **Uncertainty note:** *Borderline case: a minor weep with normal effort may be MONITOR. Safety to confirm threshold.*

#### 🛑 `Steering linkage / drag link / pitman arm — no missing or broken parts`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.209 · CVSA OOS §10
- **Rationale:** Missing or broken steering components = imminent loss of control. Always OOS.

#### 🛑 `Steering wheel free play — within spec (≤ 10° on light truck · ≤ 30° on heavy)`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.209 · CVSA OOS §10
- **Rationale:** Excessive steering free play indicates worn linkage and impaired directional control. OOS.


### Suspension · 2 OOS · 0 MONITOR

#### 🛑 `Suspension — air bags inflate · no leaks · no severe sag`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.207
- **Rationale:** Air suspension failure changes ride height and brake geometry. OOS.

#### 🛑 `Suspension — leaf springs · u-bolts · shackles intact`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.207 · CVSA OOS §9
- **Rationale:** Broken springs or missing U-bolts compromise axle integrity. OOS.


### Structural · 5 OOS · 0 MONITOR

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


### Lights · 6 OOS · 6 MONITOR

#### 🛑 `Brake lights — both sides functional`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.25 · CVSA OOS §8.a
- **Rationale:** Both-side brake light failure is an OOS criterion. Critical for trailing-vehicle awareness.

#### 🛑 ⚠️ `Headlights — high beam · both sides functional`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.24
- **Rationale:** Required equipment. OOS if both inoperative.
- **Uncertainty note:** *Single high-beam out (low still functional) may be MONITOR in daytime ops. Safety to set policy.*

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

#### 👁 `Identification lights (3-light cluster) — all functional`
- **Severity:** MONITOR
- **Reference:** 49 CFR § 393.11
- **Rationale:** Compliance lighting · monitor.

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


### Signals · 4 OOS · 1 MONITOR

#### 🛑 `4-way hazard flashers — operate · synchronized`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.25(d)
- **Rationale:** Required emergency warning device. OOS.

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

#### 👁 ⚠️ `Strobes / beacons — all flash patterns operational`
- **Severity:** MONITOR
- **Reference:** MASCI operational requirement
- **Rationale:** Worksite visibility · partial pattern loss is monitor-level if at least one beacon still operates.
- **Uncertainty note:** *MASCI work zone exposure may justify OOS for any beacon loss. Safety + Ops to confirm.*


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


### Wipers · 1 OOS · 1 MONITOR

#### 🛑 ⚠️ `Wipers — both blades sweep windshield cleanly · no streaking`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.78
- **Rationale:** Required for wet-weather visibility. Single-blade failure or severe streaking is OOS for wet/winter ops.
- **Uncertainty note:** *Dry-summer days a wiper issue is arguably monitor. Conservative OOS chosen.*

#### 👁 `Washer fluid — sprays · reservoir not empty`
- **Severity:** MONITOR
- **Reference:** operational
- **Rationale:** Comfort/maintenance · monitor.


### Hydraulic · 3 OOS · 0 MONITOR

#### 🛑 ⚠️ `Hydraulic system — no visible leaks`
- **Severity:** OOS
- **Reference:** operational · OSHA
- **Rationale:** Major hydraulic leaks risk fire (oil on hot surfaces) + loss of bed control. OOS.
- **Uncertainty note:** *'Visible leak' threshold needs Shop guidance · pinhole vs active drip differs operationally.*

#### 🛑 `Hydraulic — bed raise + lower smoothly · no drift`
- **Severity:** OOS
- **Reference:** operational
- **Rationale:** Bed drift while raised is power-line and crush hazard · OOS.

#### 🛑 `Trailer hydraulic system — no leaks · raises + lowers`
- **Severity:** OOS
- **Reference:** operational · OSHA
- **Rationale:** Hydraulic dump-trailer failure is operational + fire risk. OOS.


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


### Tarp · 0 OOS · 1 MONITOR

#### 👁 ⚠️ `Tarp system — deploys + retracts · no major tears`
- **Severity:** MONITOR
- **Reference:** MASCI policy · state load-cover regs
- **Rationale:** Load-loss potential is a haul-completion issue, not immediate roadway danger. Monitor unless tear is catastrophic.
- **Uncertainty note:** *State load-cover requirements may upgrade this to OOS for some loads · Safety/Ops to confirm.*


### Interior · 2 OOS · 2 MONITOR

#### 🛑 ⚠️ `Cab — dash gauges functional (oil pressure · temp · fuel)`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.51
- **Rationale:** Missing engine gauges mask catastrophic failures · OOS.
- **Uncertainty note:** *Modern trucks with computer-fault warning may be more permissive · Shop to confirm.*

#### 🛑 `Seat belt — present · functional · no fraying`
- **Severity:** OOS
- **Reference:** 49 CFR § 393.93
- **Rationale:** Required occupant restraint · OOS if non-functional.

#### 👁 ⚠️ `Cab — heater / defroster operational (cold/wet weather)`
- **Severity:** MONITOR
- **Reference:** 49 CFR § 393.79
- **Rationale:** Defroster needed for wet/cold visibility · monitor in dry summer but should be OOS in winter (driver discretion / dispatch policy).
- **Uncertainty note:** *Seasonal sensitivity · Safety to set wet/cold OOS policy.*

#### 👁 `Cab — interior cleanliness`
- **Severity:** MONITOR
- **Reference:** operational
- **Rationale:** Accountability + lead-driver visibility · monitor.


### Body · 1 OOS · 2 MONITOR

#### 🛑 ⚠️ `Body — no severe damage affecting safe operation`
- **Severity:** OOS
- **Reference:** operational
- **Rationale:** Severe body damage that impairs safe operation (e.g. detached panel, hanging fender) is OOS.
- **Uncertainty note:** *Subjective threshold · Safety to define 'severe' rubric.*

#### 👁 `Body — cosmetic dings · scrapes · paint`
- **Severity:** MONITOR
- **Reference:** operational
- **Rationale:** Cosmetic only · monitor for accountability tracking and dispute defense.

#### 👁 `Trailer body — cosmetic damage`
- **Severity:** MONITOR
- **Reference:** operational
- **Rationale:** Cosmetic only · monitor for accountability.


---

## Operational Sign-Off

Before production reliance, each of the following must redline + sign:

- [ ] **Safety** · approves overall OOS classifications · confirms uncertainty-flagged items
- [ ] **Shop** · confirms repair-routing accuracy · confirms ambiguity-threshold definitions (e.g. "severe damage", "major leak")
- [ ] **Operations** · confirms operational impact estimates (false-positive OOS productivity hit acceptable)
- [ ] **Dispatch leadership** · confirms re-clearance authority + workflow

Once signed, update `severity_table_version` in `fleet_defect_severity.py` from `v1-DRAFT-pending-safety-review` to `v1-approved-YYYY-MM-DD` and re-run this generator + the audit endpoint.

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