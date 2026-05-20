// MASCI Safety Meeting topic library — 75+ heavy civil / highway topics.
// Each entry populates topic, category, hazards reviewed, discussion notes,
// references, and action items. Every field stays fully editable.

export const TOPIC_LIBRARY = [
  // ============================================================
  // EARTHWORK / EXCAVATION / UNDERGROUND
  // ============================================================
  {
    key: "trenching_shoring",
    title: "Trenching, Shoring & Excavation Safety",
    category: "Hazard-Specific",
    hazards_reviewed:
      "Cave-in / collapse · Engulfment · Falls into excavation · Struck-by spoil or material · Hazardous atmospheres · Water accumulation · Underground utilities · Equipment falling into trench",
    discussion_notes:
      "• Competent person inspects every excavation daily, after rain, and after any change in conditions.\n• Protective system required at 5 ft+: slope, shore, shield, or bench.\n• Spoil pile and equipment kept ≥2 ft back from edge.\n• Ladder/ramp/steps required within 25 ft of any worker in a 4 ft+ trench.\n• Atmospheric testing required where hazardous atmosphere is suspected.\n• Crews stay clear of equipment swing radius and out from under suspended loads.\n• No one enters a trench without protective system in place — period.",
    references_cited:
      "OSHA 29 CFR 1926 Subpart P · OSHA 1926.651 · OSHA 1926.652 · OSHA Trenching Quick Card",
    action_items:
      "Confirm competent person on site daily · Verify protective system matches soil type · Check 811 ticket valid · Daily inspection logged · Rescue plan reviewed",
  },
  {
    key: "soil_classification",
    title: "Soil Classification (Type A / B / C)",
    category: "Procedure / SOP",
    hazards_reviewed:
      "Wrong protective system used · Trench collapse from unrecognized soil weakness · Layered soils acting as weakest type · Saturated soil reclassified after rain",
    discussion_notes:
      "• Type A: most stable (e.g. clay, hardpan) — slope 3/4:1.\n• Type B: medium (silty soils) — slope 1:1.\n• Type C: least stable (gravel, sand, submerged) — slope 1.5:1.\n• Layered soil = classify as the weakest layer.\n• Previously disturbed soil is automatically Type C.\n• Visual + manual tests by competent person; soil reclassified after rain or freeze/thaw.\n• When in doubt, classify lower (more conservative).",
    references_cited:
      "OSHA 1926 Subpart P Appendix A · OSHA Soil Classification Chart",
    action_items:
      "Soil type recorded daily · Competent person performs visual & manual test · System adjusted after weather change",
  },
  {
    key: "underground_utilities",
    title: "Underground Utilities / 811 Locates",
    category: "Procedure / SOP",
    hazards_reviewed:
      "Utility strike (gas, electric, fiber, water, sewer) · Explosion / fire · Electrocution · Service outage · Worker injury from energized line",
    discussion_notes:
      "• Call 811 (or state equivalent) at minimum 2-3 business days before digging.\n• Verify ticket is current AND unexpired before any dig.\n• Visually verify ALL marks before breaking ground; missing marks = stop, recall.\n• Hand dig within 24 inches of any marked utility (tolerance zone).\n• Treat every unmarked line as live until proven otherwise.\n• Line strike: clear area, evacuate uphill/upwind for gas, no switches/phones near gas, call utility AND 911.\n• Daylight critical utilities (vacuum/hand) before mechanical digging near them.",
    references_cited:
      "OSHA 1926.651(b) · Common Ground Alliance Best Practices · State 811 program",
    action_items:
      "All 811 tickets verified · Mark-outs photographed · Hand-dig tolerance enforced · Spotter assigned for mechanical dig near marks",
  },
  {
    key: "confined_space",
    title: "Confined Space Entry — Manholes, Vaults, Lift Stations",
    category: "Procedure / SOP",
    hazards_reviewed:
      "Hazardous atmosphere (low O2, H2S, methane, CO) · Engulfment · Entrapment · Falls into space · Struck-by lifted manhole cover · Heat stress in enclosed space",
    discussion_notes:
      "• Permit-required Confined Space Entry program before ANY entry.\n• Atmospheric test before entry AND continuously: O2 19.5–23.5%, LEL <10%, H2S <10 ppm, CO <25 ppm.\n• Mechanical ventilation almost always required for sewer/storm structures.\n• Attendant outside at all times — never leaves post.\n• Entrant on retrieval line + harness; non-entry rescue is the goal.\n• Communication maintained continuously (voice, radio, hand signal).\n• Rescue: never go in after a downed worker without retrieval system + SCBA.",
    references_cited:
      "OSHA 1926 Subpart AA · OSHA 1926.1203 · OSHA 1910.146",
    action_items:
      "Permit signed · Gas monitor calibrated · Attendant assigned · Ventilation in place · Rescue plan briefed",
  },
  {
    key: "earthmoving_equipment",
    title: "Earthmoving Equipment & Heavy Iron",
    category: "Tool / Equipment Specific",
    hazards_reviewed:
      "Struck-by equipment · Run-over while spotting · Caught between equipment and fixed object · Rollover · Backing accidents · Swing radius incidents",
    discussion_notes:
      "• Pre-shift walkaround on every piece of iron — fluids, tires, lights, alarms, fire extinguisher.\n• Seat belts worn at all times — no exceptions.\n• Backup alarms operational; spotters used in congested areas or restricted visibility.\n• Establish and enforce no-go zones around equipment swing radius.\n• Workers on the ground wear hi-vis and stay in operator's line of sight.\n• Eye contact + thumbs up before operator moves equipment near workers.\n• Park on level ground, blade/bucket down, brake set, key removed when leaving cab.",
    references_cited:
      "OSHA 29 CFR 1926 Subpart O · OSHA 1926.601 · OSHA 1926.602 · MUTCD Part 6",
    action_items:
      "Pre-op inspections logged · Spotters assigned · No-go zones marked · Equipment parked safely at end of shift",
  },
  {
    key: "backing_spotters",
    title: "Backing Operations & Spotters",
    category: "Procedure / SOP",
    hazards_reviewed:
      "Backover incidents · Struck-by reversing equipment · Spotter struck by other vehicle · Communication breakdown · Blind spots",
    discussion_notes:
      "• Back-up alarms operational on every piece of mobile equipment / dump truck.\n• Spotter required when backing in congested areas or near workers.\n• Spotter stands clear of the path of travel, in operator's mirror line of sight.\n• Lose sight of spotter = STOP. Operator never backs blind.\n• Use horn signals: 1 stop, 2 forward, 3 reverse.\n• Hi-vis apparel mandatory for spotters at all times.",
    references_cited:
      "OSHA 1926.601(b)(4) · OSHA Backover Hazards Bulletin",
    action_items:
      "Designated spotters identified · Spotter PPE verified · Hand signals reviewed · Comms plan in place",
  },
  {
    key: "drilled_shaft",
    title: "Drilled Shaft / Caisson Operations",
    category: "Hazard-Specific",
    hazards_reviewed:
      "Falls into open shaft · Cave-in of shaft sidewall · Struck-by drill stem / Kelly bar · Engulfment from collapsing slurry/casing · Crane / rig tipping · Suspended load swing",
    discussion_notes:
      "• Open shafts ALWAYS covered or barricaded; never leave open and unattended.\n• Set ground crew clear of swing radius of drill rig.\n• Workers stay outside reach of suspended drill stem and casing.\n• Slurry handling — chemical PPE, splash protection, eyewash within 25 ft.\n• Trained signal person for crane support; certified rigger for rebar cages and casings.\n• Trip hazards from rebar, hoses, slurry lines kept controlled.",
    references_cited:
      "OSHA 1926 Subpart P (excavation) · OSHA 1926 Subpart CC (cranes) · DFI Drilled Shaft Safety",
    action_items:
      "Open shafts covered/barricaded · Swing radius marked · Signal person designated · Slurry PPE staged",
  },
  {
    key: "pipe_installation",
    title: "Pipe Installation — RCP / DI / HDPE",
    category: "Hazard-Specific",
    hazards_reviewed:
      "Struck-by suspended pipe · Crushing / pinch points joining pipe · Worker in trench under suspended load · Trench cave-in · Slips on wet/muddy bedding · Back/strain from manual handling",
    discussion_notes:
      "• Workers OUT of trench while pipe is being lowered. Re-enter only after pipe is set and load is released.\n• Use pipe-laying tongs, slings, or pipe lifters — never improvised lifting.\n• Designated signal person for crane / excavator placing pipe.\n• Joint home with mechanical means (come-along, jack, equipment) — not by hand.\n• Tag lines control pipe rotation; workers stay outside the bite.\n• Trench protective system stays in place during pipe install.",
    references_cited:
      "OSHA 1926 Subpart P · OSHA 1926.251 (rigging) · ACPA Concrete Pipe Handbook",
    action_items:
      "Riggers certified · Signal person designated · Tag lines used · Trench shield in place during install",
  },
  {
    key: "compaction",
    title: "Compaction Operations",
    category: "Tool / Equipment Specific",
    hazards_reviewed:
      "Hand-arm vibration syndrome · Whole-body vibration on rollers · Struck-by walking compactor · Rollover on slopes · Noise above 85 dBA · Run-over by reversing roller",
    discussion_notes:
      "• Walk-behind compactors: maintain firm grip, anti-vibration gloves, no loose clothing.\n• Vibratory rollers: never operate on slopes greater than mfr-stated max.\n• Roller no-go zones marked; spotters at edges and tapers.\n• Backup alarms required; reversing on slope only with spotter.\n• Take 10-minute break per hour with vibrating equipment to mitigate HAVS.\n• Hearing protection required — most compactors exceed 85 dBA.",
    references_cited:
      "OSHA 1926.95 · NIOSH Hand-Arm Vibration · ACGIH TLV for vibration",
    action_items:
      "Anti-vibration gloves issued · Roller no-go zones marked · Hearing protection required · Operator rotation",
  },
  {
    key: "dewatering",
    title: "Dewatering / Wellpoint Operations",
    category: "Procedure / SOP",
    hazards_reviewed:
      "Electrical hazards from pumps in water · Trench instability from over-pumping or under-pumping · Discharge hose whip · Slip/trip on wet surfaces · Environmental violation from improper discharge",
    discussion_notes:
      "• GFCI required on all electrical pumps; cords inspected daily for damage.\n• Bond and ground submersible pumps to prevent shock.\n• Pump rate set to maintain stable trench conditions.\n• Discharge directed to approved location — never into wetlands or unprotected slopes without permit.\n• Secure discharge hoses to prevent whip.\n• Pump fuel handling: bonded containers, no smoking, fire extinguisher within 50 ft.",
    references_cited:
      "OSHA 1926.405 · EPA / FDEP discharge regulations · NPDES permit conditions",
    action_items:
      "GFCI verified · Pump bonded · Discharge location approved · Fuel handling area set up · SDS for pump fuel",
  },
  {
    key: "manhole_work",
    title: "Manhole Work & Lift Stations",
    category: "Hazard-Specific",
    hazards_reviewed:
      "Hazardous atmosphere (H2S, methane, low O2) · Falls into open structure · Struck-by lifted cover · Engulfment from sudden inflow · Bloodborne / biohazard from sewage exposure",
    discussion_notes:
      "• Treat every manhole as a permit-required confined space until proven otherwise.\n• Atmospheric test before entry, continuous monitoring.\n• Mechanical fan ventilation required for active sewer/storm structures.\n• Use proper manhole hook to lift covers — never fingers in slots.\n• Barricade and cover any open structure; never leave unattended.\n• Sewage exposure: skin/eye protection, immediate decon if contact, hand hygiene.",
    references_cited:
      "OSHA 1926 Subpart AA (Confined Spaces) · OSHA 1910.1030 (BBP)",
    action_items:
      "Permit signed · Gas monitor calibrated · Ventilation set up · Decon supplies on site",
  },
  {
    key: "saw_cutting",
    title: "Pavement Saw Cutting",
    category: "Tool / Equipment Specific",
    hazards_reviewed:
      "Respirable silica · Cuts / amputations from blade · Kickback · Noise · Heat / hot blade · Struck-by passing traffic · Slurry contamination",
    discussion_notes:
      "• Wet cut whenever possible — water suppression is OSHA Table 1 control for silica.\n• When dry cut required: HEPA vacuum AND respiratory protection.\n• Inspect blade before each use; dispose of cracked or chipped blades.\n• Two-handed grip; no overreach; firm footing.\n• Hearing protection — pavement saws routinely exceed 100 dBA.\n• Slurry: contain it; don't let it run into storm drain (NPDES violation).\n• Eye + face protection from flying chips.",
    references_cited:
      "OSHA 1926.1153 (Silica Table 1) · OSHA 1926.300 · OSHA 1926.95",
    action_items:
      "Wet-cut equipment ready · Respirator if dry · Slurry containment · Hearing & face PPE · Blade inspected",
  },
  {
    key: "curb_gutter",
    title: "Curb & Gutter Operations",
    category: "Hazard-Specific",
    hazards_reviewed:
      "Slip-form machine pinch points · Hot/wet concrete contact · Repetitive bending and lifting · Struck-by passing traffic · Silica from sawing finished concrete · Skin chemical burns",
    discussion_notes:
      "• Workers stay outside slip-form machine no-go zone — typical 6 ft buffer.\n• Hand-finishing crews wear waterproof gloves and boots; rinse skin contact immediately.\n• Lift / move forms with proper body mechanics — keep load close, knees bent.\n• Edge work near live traffic = positive protection (drum line minimum, barrier preferred).\n• Joint sawing follows silica controls (Table 1).\n• Dispose of waste concrete properly; no dumping into storm drains.",
    references_cited:
      "OSHA 1926 Subpart Q · OSHA 1926.1153 · NIOSH Concrete Worker Bulletin",
    action_items:
      "Waterproof PPE issued · No-go zone marked · Lifting plan briefed · Silica Table 1 controls in place",
  },
  {
    key: "mse_wall",
    title: "MSE Wall / Retaining Wall Construction",
    category: "Hazard-Specific",
    hazards_reviewed:
      "Falls from elevated panels · Struck-by panel during placement · Pinch / crush during reinforcement strap install · Backfill compaction edge instability · Material handling strains",
    discussion_notes:
      "• Tag lines control panel rotation during placement.\n• Workers behind panels protected from struck-by during set; outside swing radius.\n• Tie-off required when working at edges 6 ft+; guardrails installed as wall height grows.\n• Compaction equipment kept set distance from wall face per design.\n• Reinforcement straps unrolled with tools, not bare hands.\n• Wall toe stable before next lift placed.",
    references_cited:
      "OSHA 1926 Subpart M · AASHTO LRFD Bridge Design · NCMA Design Manual",
    action_items:
      "Tag lines staged · Fall protection above 6 ft · Compaction setbacks marked · Lifting plan briefed",
  },
  {
    key: "boring_drilling",
    title: "Boring / Directional Drilling (HDD)",
    category: "Hazard-Specific",
    hazards_reviewed:
      "Inadvertent utility strike · High-pressure mud blowout · Pinch points on rod handler · Slips on slurry-covered ground · Frac-out releasing drilling mud to surface · Caught-in rotating drill string",
    discussion_notes:
      "• Pothole / daylight all crossings before bore.\n• Locate strikes are mandatory — verify with utility owner where critical.\n• Never reach into rotating drill string or rod box.\n• Frac-out plan in writing; spill kits onsite.\n• High-pressure jets can cut skin — keep hands clear of nozzle path.\n• Pull-back forces are high — workers stay outside line-of-tension.",
    references_cited:
      "OSHA 1926.601 · DCA Best Practices for HDD · CGA Best Practices",
    action_items:
      "Crossings daylighted · Frac-out plan onsite · Spill kit staged · Tension line zone cleared",
  },
  {
    key: "demolition",
    title: "Demolition Operations",
    category: "Hazard-Specific",
    hazards_reviewed:
      "Falls from height · Struck-by falling debris · Premature collapse · Asbestos / lead exposure · Silica dust · Fire from cutting / hot work · Utility strike on remaining lines",
    discussion_notes:
      "• Engineering survey required before demo — identify floors, walls, materials, utilities.\n• Hazmat survey — asbestos, lead, PCBs identified and abated before demo.\n• Utilities cut, capped, locked out before demo.\n• Drop zones barricaded; spotters at perimeter.\n• Dust controls — water suppression and respiratory PPE.\n• Hot work permits for any cutting, welding, torching.\n• Daily inspection of remaining structure for stability.",
    references_cited:
      "OSHA 1926 Subpart T · OSHA 1926.850 · OSHA 1926.1101 (Asbestos) · OSHA 1926.62 (Lead)",
    action_items:
      "Engineering survey complete · Hazmat survey complete · Utilities locked out · Drop zones marked · Hot work permits ready",
  },

  // ============================================================
  // TRAFFIC / MOT
  // ============================================================
  {
    key: "mot_setup",
    title: "MOT Setup & Work Zone Traffic Control",
    category: "Procedure / SOP",
    hazards_reviewed:
      "Struck-by vehicles entering work zone · Driver inattention / impaired drivers · Inadequate buffer / taper length · Worker exposure during setup and takedown · Night-time visibility · Equipment / vehicle interface inside work zone",
    discussion_notes:
      "• Approved Traffic Control Plan (TCP) on site and matches field conditions.\n• Setup from upstream to downstream; takedown reverse order — never face oncoming traffic.\n• Buffer / taper lengths matched to posted speed.\n• Devices clean, retroreflective, properly spaced.\n• Internal traffic-control plan separates workers from equipment inside the zone.\n• Night work: lighting min 5 fc, all workers in Class 3 hi-vis with retro bands.\n• Public traffic exposure controlled by positive protection where speed/volume warrant.",
    references_cited:
      "MUTCD Part 6 · FHWA Work Zone Safety · OSHA 1926 Subpart G · ATSSA Standards",
    action_items:
      "TCP onsite and signed · Devices match plan · Internal traffic plan briefed · Night lighting verified · Class 3 hi-vis confirmed",
  },
  {
    key: "flaggers",
    title: "Flaggers & Public Traffic Exposure",
    category: "Procedure / SOP",
    hazards_reviewed:
      "Struck by passing motorist · Distracted / impaired drivers · Driver running stop paddle · Lone-worker exposure · Sun glare blinding flagger · Heat / cold stress",
    discussion_notes:
      "• Flagger is a certified position — current cert card on person.\n• Stop paddle, not a flag, in all paid traffic-control work.\n• Flagger station has clear escape route — never trapped between barrier and traffic.\n• Hi-vis Class 3 day, hi-vis with retro at night.\n• Two-way radio comms with crew and other flaggers.\n• Rotate flaggers every 2 hours in heat; provide water, shade, seating between rotations.\n• Position so flagger is visible for full stopping sight distance.",
    references_cited:
      "MUTCD Part 6E · ATSSA Flagger Cert · State Flagger requirements",
    action_items:
      "Flagger certs verified · Stop paddles in good condition · Escape route walked · Rotation schedule posted · Comms tested",
  },
  {
    key: "live_traffic",
    title: "Live Traffic Exposure / Struck-By",
    category: "Hazard-Specific",
    hazards_reviewed:
      "Worker struck by vehicle · Distracted driver · Speeding · Vehicle intrusion through tapers · Limited reaction time at night · Lone worker exposure",
    discussion_notes:
      "• Highest fatality cause in our industry — treat every vehicle as a potential intrusion.\n• Always maintain situational awareness — one eye on traffic when working near open lanes.\n• Stand on the shielded side of barrier or equipment when possible.\n• Never cross open travel lanes on foot — use approved crossing points.\n• Work-zone intrusion alarms / shadow vehicles where speed and volume warrant.\n• Stop, get behind protection, call dispatch if vehicle penetrates buffer.",
    references_cited:
      "FHWA Work Zone Safety · OSHA 1926.201 · MUTCD Part 6 · NIOSH Highway Workers",
    action_items:
      "Buffer integrity verified · Shadow vehicle in place · Workers briefed on escape routes · Intrusion response reviewed",
  },
  {
    key: "mot_moving_trucks",
    title: "MOT Placement from Moving Trucks",
    category: "Procedure / SOP",
    hazards_reviewed:
      "Falls from moving truck · Struck-by passing vehicle · Loss of grip / footing · Improper anchor for tie-off · Communication breakdown · Heat / fatigue",
    discussion_notes:
      "• Workers on the back of moving MOT truck must be 100% tied off to a rated, engineered anchor.\n• No improvised tie-off — guardrails and toolboxes are NOT anchors.\n• Truck speed during placement: 5 mph or less.\n• Driver and workers maintain constant communication via radio or hand signals.\n• No mounting/dismounting while truck is moving.\n• Workers never ride on equipment unless designated platform is provided.",
    references_cited:
      "OSHA 1926.501(b) · OSHA 1926.502 · MUTCD Part 6",
    action_items:
      "Harnesses inspected · Anchor points verified · Driver / crew comms tested · Speed limit enforced",
  },
  {
    key: "lane_closures",
    title: "Lane Closures — Single & Multiple",
    category: "Procedure / SOP",
    hazards_reviewed:
      "Driver running closure · Crew exposed during setup · Inadequate taper for posted speed · Confusing signs · Cone knockover from wind / vehicle wake",
    discussion_notes:
      "• Setup ALWAYS upstream-to-downstream; takedown reverse.\n• First-truck = shadow truck with TMA where speed/volume requires it.\n• Cones / drums replaced if knocked down — re-up immediately.\n• 'Lane Closed' / merge signs visible at full stopping sight distance.\n• Cross-over point clearly delineated; arrow boards aimed correctly.\n• Verify temporary speed reduction signs placed where required.",
    references_cited:
      "MUTCD Part 6 · State DOT Lane Closure Standards · ATSSA Best Practices",
    action_items:
      "Devices match plan · Shadow vehicle in place · Speed reduction signage verified · Knockdown response plan",
  },
  {
    key: "shoulder_closures",
    title: "Shoulder Closures",
    category: "Procedure / SOP",
    hazards_reviewed:
      "Errant vehicle striking shoulder workers · Tight working area · Vehicles using shoulder as escape lane · Edge drop-off hazards",
    discussion_notes:
      "• Treat shoulder as live traffic exposure — full PPE, full TCP.\n• Shadow vehicle / TMA recommended even on shoulder closures at high speed.\n• Watch for edge drop-offs — barricade where applicable.\n• Trench / pit operations on shoulder require positive barrier on travel-lane side.\n• Workers stay shielded by equipment / vehicle when feasible.",
    references_cited:
      "MUTCD Part 6 · FHWA Shoulder Operations · State DOT Standards",
    action_items:
      "Shadow vehicle staged · Edge drop-offs barricaded · Class 3 hi-vis · Position-of-protection identified",
  },
  {
    key: "detour_routing",
    title: "Detour Routing & Road Closures",
    category: "Procedure / SOP",
    hazards_reviewed:
      "Drivers ignoring detour signs · Inadequate advance warning · Confusing or contradictory signage · Emergency vehicle access blocked · Local resident frustration / hostility",
    discussion_notes:
      "• Advance warning signs at all approaching intersections — minimum spacing per MUTCD.\n• 'DETOUR' arrow signs at every turn — no missing arrows.\n• Trailblazer signs along the detour route confirm motorists stay on path.\n• Coordinate with local fire / EMS / police for emergency response routing.\n• Communicate with local residents / businesses in advance.\n• Confirm signs daily — vandalism and theft are common.",
    references_cited:
      "MUTCD Part 6F · State DOT Standard Plans · Local PD coordination",
    action_items:
      "Sign inventory walked daily · Emergency services notified · Local outreach completed",
  },
  {
    key: "pavement_marking",
    title: "Pavement Marking Operations (Striping)",
    category: "Hazard-Specific",
    hazards_reviewed:
      "Struck-by traffic at low operating speed · Methylene chloride / MMA exposure · Hot thermoplastic burns · Glass bead splatter · Slips on wet paint · Fire / explosion (MMA)",
    discussion_notes:
      "• Striping crews work at slow speed — make extra sure motorists see them (additional shadow vehicles, large arrow boards).\n• Hot thermoplastic 400°F+ — long sleeves, thermal gloves, no skin exposure.\n• MMA epoxy: respiratory protection, no smoking, ignition sources removed.\n• Glass beads cause eye injury — full eye/face protection.\n• Workers downstream of paint kettle stay clear of fume plume.\n• Paint truck route pre-walked to verify obstacles cleared.",
    references_cited:
      "OSHA 1926.59 (HazCom) · MUTCD Part 6 · Material SDS",
    action_items:
      "Shadow vehicles staged · Burn-rated PPE · MMA SDS reviewed · Fire extinguisher staged",
  },
  {
    key: "sign_installation",
    title: "Sign Installation & Removal",
    category: "Procedure / SOP",
    hazards_reviewed:
      "Struck-by traffic during install · Lifting strain · Falls from sign-mount aerial · Caught between auger and obstacles · Underground utility strike during post drilling",
    discussion_notes:
      "• 811 ticket required before any post drilling.\n• Two-person lift for any sign over 50 lb or oversized.\n• Aerial work for overhead signs: tie-off in bucket, no climbing on truss.\n• Sign panel slings rated for the load.\n• Auger no-go zones marked; spotter at fence lines and curbs.\n• Re-stripe pavement marks behind temporary signs after sign removal.",
    references_cited:
      "MUTCD Part 6 · OSHA 1926.453 (Aerial Lifts) · OSHA 1926.251",
    action_items:
      "811 ticket valid · Lifting plan · Aerial-lift fall protection · Slings inspected",
  },
  {
    key: "crash_cushion",
    title: "Crash Cushion / Attenuator Setup",
    category: "Procedure / SOP",
    hazards_reviewed:
      "Struck-by traffic during install · Pinch points between modules · Anchor bolt strikes · Heavy module lifts · Hidden damage on used attenuators",
    discussion_notes:
      "• Anchor bolts driven only after locate ticket cleared.\n• Module lifts — engineered slings, signal person, designated drop zone.\n• Workers stand outside line-of-tension during lift.\n• Inspect every module — damaged ones removed from service.\n• Reflective sheeting clean before placement.\n• Truck-mounted attenuator (TMA) on shadow vehicle confirmed operational.",
    references_cited:
      "MASH Test Level Standards · MUTCD Part 6 · State DOT Standards",
    action_items:
      "Locate ticket cleared · Slings inspected · Modules inspected · TMA operational",
  },
  {
    key: "vms_signs",
    title: "Variable Message Signs (VMS / DMS)",
    category: "Tool / Equipment Specific",
    hazards_reviewed:
      "Struck-by traffic during placement · Trailer tipping during lift / level · Electric shock from solar/battery system · Pinch points raising mast · Overhead clearance contact",
    discussion_notes:
      "• Place VMS on stable level ground — outriggers fully extended.\n• Verify overhead clearance before raising mast — power lines, trees.\n• Battery and solar system — keep away from sparks, no smoking around.\n• Lock mast at full height before walking away.\n• Message clear, legible, MUTCD-approved phrasing.\n• Secure trailer with hitch lock when unattended.",
    references_cited:
      "MUTCD Part 6F · Manufacturer's Operator Manual · OSHA 1926.405",
    action_items:
      "Outriggers set · Overhead clearance verified · Mast locked · Hitch locked",
  },
  {
    key: "barrier_placement",
    title: "Concrete / Water-Filled Barrier Placement",
    category: "Hazard-Specific",
    hazards_reviewed:
      "Struck-by passing traffic during placement · Crush from suspended barrier · Pinch points connecting segments · Lifting strain on water-filled units · Failure of improperly connected barrier",
    discussion_notes:
      "• Crew on offset side of placement equipment, never between barrier and live traffic.\n• Barrier slings rated; lift points marked or engineered.\n• Connection pins fully seated before next lift; no improvised connections.\n• Water-filled barrier requires water source — hydrant permit, hose secured.\n• Barrier deflection distance accounted for in design — workers behind it stay outside deflection zone.\n• Reflective delineators on every segment for night visibility.",
    references_cited:
      "MASH Test Levels · MUTCD Part 6 · OSHA 1926.251",
    action_items:
      "Slings rated · Connection pins verified · Deflection zone marked · Reflective delineators in place",
  },

  // ============================================================
  // CONCRETE / PAVING / HOT WORK
  // ============================================================
  {
    key: "concrete_silica",
    title: "Concrete Operations & Respirable Silica",
    category: "Hazard-Specific",
    hazards_reviewed:
      "Respirable crystalline silica (silicosis, lung cancer) · Caustic burns from wet concrete · Skin / eye irritation · Rebar impalement · Forms collapse · Lifting injuries",
    discussion_notes:
      "• OSHA Table 1 — match every dust-generating task to its specified engineered control (water OR vacuum).\n• Respiratory protection (P100 or supplied air) when controls insufficient or task isn't on Table 1.\n• Waterproof gloves, boots, sleeves with wet concrete; rinse skin contact immediately.\n• Rebar caps on every exposed end at trip height or below.\n• Forms inspected and braced before pour; competent person for forming.\n• Eye protection mandatory during cutting, grinding, sawing, chipping.",
    references_cited:
      "OSHA 1926.1153 · OSHA 1926 Subpart Q · NIOSH Silica Bulletin",
    action_items:
      "Table 1 controls in place · Water/vacuum systems checked · Respirators fit-tested · Rebar caps installed",
  },
  {
    key: "concrete_pumping",
    title: "Concrete Pumping",
    category: "Tool / Equipment Specific",
    hazards_reviewed:
      "Pump line whip / failure · Struck-by hose · Caustic spray injuries to eyes/skin · Tipping pump truck on inadequate outriggers · Overhead power line contact · Plug/blockage causing line failure",
    discussion_notes:
      "• Outriggers fully extended on cribbing; ground bearing capacity confirmed.\n• Stay clear of overhead lines — minimum 10 ft (more for higher voltage).\n• Hose handler stays outside potential whip zone; positive comms with operator.\n• Eye/face protection mandatory — burst fittings spray cement under pressure.\n• Clear blockages by reverse, never by disconnecting under pressure.\n• Safety chains on all clamp connections.",
    references_cited:
      "ACPA Concrete Pump Safety · OSHA 1926.701 · OSHA 1926.405",
    action_items:
      "Outriggers cribbed · Overhead clearance verified · Eye/face PPE · Comms tested · Safety chains in place",
  },
  {
    key: "formwork",
    title: "Formwork Safety",
    category: "Procedure / SOP",
    hazards_reviewed:
      "Form collapse · Falls from formwork · Struck-by falling forms · Pinch / crush during stripping · Rebar impalement · Hardware failure under load",
    discussion_notes:
      "• Formwork designed by qualified person for the load (concrete + workers + equipment).\n• No deviation from drawings without engineer approval.\n• Inspect formwork before pour — every brace, every tie, every shore.\n• Workers tie off when working at form height 6 ft+.\n• Stripping: only after concrete reaches required strength; controlled drop zones.\n• Rebar caps on all exposed ends; no walking on top mat without planking.",
    references_cited:
      "OSHA 1926.703 · ACI 347 Formwork · OSHA 1926.703(b)",
    action_items:
      "Form drawings on site · Pre-pour inspection logged · Strip strength verified · Rebar caps in place",
  },
  {
    key: "bridge_deck_pour",
    title: "Bridge Deck Pours",
    category: "Hazard-Specific",
    hazards_reviewed:
      "Falls over edge · Falls through deck openings · Struck-by finishing machine · Concrete spray from pump · Rebar trip / impalement · Heat stress on long pours",
    discussion_notes:
      "• Perimeter guardrail or full PFAS before any deck work begins.\n• Cover or barricade every opening.\n• Finishing machine no-go zones marked; operator and crew comms verified.\n• Heat stress plan in effect — water, ice, shade, rotation.\n• Crew briefing: pour sequence, dump location, comms with mixer drivers.\n• Edge protection at fascia stays in place until parapet poured.",
    references_cited:
      "OSHA 1926 Subpart M · OSHA 1926.502 · AASHTO Bridge Construction",
    action_items:
      "Edge protection in place · Openings covered · Heat plan active · Pour sequence briefed",
  },
  {
    key: "curing_sealing",
    title: "Curing & Sealing Operations",
    category: "Hazard-Specific",
    hazards_reviewed:
      "Solvent vapor inhalation · Skin/eye irritation · Fire / explosion from flammable cures · Slip on wet cure · Spray-back to face during application",
    discussion_notes:
      "• Read SDS before any cure / sealer use; verify required PPE.\n• Solvent-based products: respiratory protection, no smoking, no ignition sources, ground sprayers.\n• Spray downwind; shut off if wind shifts.\n• Eye / face protection mandatory.\n• Slip hazard — flag wet areas, no walking on freshly cured surfaces.\n• Spill kits onsite; environmental compliance for any spill.",
    references_cited:
      "OSHA 1926.59 (HazCom) · Material SDS · NFPA 30 (Flammables)",
    action_items:
      "SDS reviewed · Respirators ready · Wet zones flagged · Spill kits onsite",
  },
  {
    key: "cold_weather_concrete",
    title: "Cold Weather Concrete Operations",
    category: "Hazard-Specific",
    hazards_reviewed:
      "Cold stress / hypothermia · Burns from heated water / steam · CO from heaters in enclosures · Slips on icy surfaces · Frozen-aggregate kickbacks from chute",
    discussion_notes:
      "• Layered clothing, insulated waterproof gloves and boots; cover head and neck.\n• Heated enclosures: ONLY direct-fired heaters with continuous CO monitoring; OR indirect-fired heaters venting outside.\n• Warming areas (heated trailer / shed) within 100 ft of crew.\n• Salt / sand walking surfaces; flag icy areas.\n• Hot water for mix: 140°F max at point of use; gloves required.\n• Buddy system — frostbite first signs are subtle.",
    references_cited:
      "OSHA Cold Stress Bulletin · ACI 306 Cold-Weather Concreting",
    action_items:
      "Cold-weather PPE issued · CO monitoring set · Walking surfaces de-iced · Warming area available",
  },
  {
    key: "asphalt_paving",
    title: "Hot Asphalt & Paving Operations",
    category: "Hazard-Specific",
    hazards_reviewed:
      "Severe burns from hot mix (300°F+) · Burns from tack/oil/fuel · Fume inhalation · Struck-by paver, roller, truck · Caught between roller and pavement edge · Heat stress",
    discussion_notes:
      "• Long sleeves, long pants, gloves rated for hot asphalt, leather boots — even in heat.\n• No skin contact with hot mix; raking/lute work upwind of fume plume.\n• Paver and roller no-go zones marked; spotters where workers approach machinery.\n• Truck driver acknowledges crew before dumping; positive comms with screed operator.\n• Fuel and tack handling: bonded containers, no smoking, fire extinguisher within 50 ft.\n• Heat stress program — water, rest, shade rotation.",
    references_cited:
      "OSHA 1926.95 PPE · NIOSH Asphalt Bulletin · NAPA Worker Safety",
    action_items:
      "Burn-rated PPE issued · No-go zones marked · Heat stress monitoring active · Fire extinguisher onsite",
  },
  {
    key: "milling_operations",
    title: "Milling Operations (Cold Planing)",
    category: "Hazard-Specific",
    hazards_reviewed:
      "Struck-by milling drum / conveyor · Silica / asphalt dust · Caught-in conveyor pinch points · Hot/burning teeth contact · Noise above 95 dBA · Trip on grade transitions",
    discussion_notes:
      "• Workers stay outside drum and conveyor no-go zones during operation.\n• Water spray system on the drum — primary silica/dust control.\n• Respirator if water control insufficient (older mills, dry conditions).\n• Tooth changes: machine fully shut down, locked out, drum cooled.\n• Hearing protection mandatory.\n• Ground crew aware of grade transitions; positive comms with operator.",
    references_cited:
      "OSHA 1926.1153 · NIOSH Asphalt Milling Bulletin · OSHA 1910.147",
    action_items:
      "No-go zones marked · Water spray verified · Hearing protection required · LOTO for tooth changes",
  },
  {
    key: "tack_prime_coat",
    title: "Tack Coat / Prime Coat Application",
    category: "Hazard-Specific",
    hazards_reviewed:
      "Burns from hot tack (140°F+) · Fume inhalation · Slip on tacked pavement · Spray-back to operator/worker · Fire / explosion of cutback materials",
    discussion_notes:
      "• Long sleeves, gloves, eye protection — no exposed skin during spray.\n• Cutback materials are flammable — no ignition sources, fire extinguisher staged.\n• Stand upwind of spray bar; nozzle tested before application.\n• Track-free time observed before traffic — flag if pedestrians or vehicles approach.\n• Equipment cleaned with approved solvent; spill kits ready.\n• Truck operator and ground crew comms verified.",
    references_cited:
      "OSHA 1926.59 (HazCom) · NAPA Tack Coat Best Practices",
    action_items:
      "Burn-rated PPE · Fire extinguisher staged · Comms tested · Spill kit ready",
  },
  {
    key: "joint_sealing",
    title: "Joint Sealing — Hot & Cold Pour",
    category: "Hazard-Specific",
    hazards_reviewed:
      "Burns from hot sealant 380°F+ · Fume / vapor inhalation · Slip on freshly sealed joint · Backpack burner / kettle pressure rupture · Solvent fire (cold pour)",
    discussion_notes:
      "• Hot pour: thermal gloves, long sleeves, face shield while pouring.\n• Kettle pressure relief verified before each shift; never modify safety devices.\n• Fume control — work upwind; respiratory protection if fumes irritate.\n• Cold pour solvent: SDS review, no smoking, ground containers.\n• Fresh sealant flagged until cured.\n• Backpack flame thrower (joint heater) — only outdoors, no ignition sources around fuel cylinder.",
    references_cited:
      "OSHA 1926.59 · Manufacturer's Operating Manual · NFPA 58 (Propane)",
    action_items:
      "Thermal PPE issued · Kettle inspected · SDS reviewed · Cured-zone signage",
  },
  {
    key: "diamond_grinding",
    title: "Diamond Grinding & Grooving",
    category: "Tool / Equipment Specific",
    hazards_reviewed:
      "Respirable silica · Slurry slips · Hot blade contact · Noise · Struck-by passing traffic · Eye injury from chip / spray",
    discussion_notes:
      "• Wet grind for silica control (Table 1) — blade water on continuously.\n• Vacuum slurry to prevent storm drain contamination.\n• Hearing protection — process exceeds 95 dBA.\n• Eye / face protection from chips and spray.\n• Operator stays clear of blade; cool blade before any maintenance.\n• Slurry disposed at approved location.",
    references_cited:
      "OSHA 1926.1153 (Silica Table 1) · ACPA Grinding Best Practices",
    action_items:
      "Water spray verified · Slurry containment · Hearing & eye PPE · Disposal location approved",
  },
  {
    key: "sound_wall",
    title: "Sound Wall / Noise Wall Construction",
    category: "Hazard-Specific",
    hazards_reviewed:
      "Falls from height · Struck-by panel during placement · Crush during column erection · Wind catching panels · Crane tipping · Live traffic adjacent",
    discussion_notes:
      "• Tag lines control panel rotation; workers outside swing radius.\n• Wind speed monitoring — stop placement at mfr / engineer-specified threshold.\n• Tie-off above 6 ft; perimeter guardrail / catch system as wall grows.\n• Crane signal person designated and certified.\n• Live traffic side: positive protection (barrier) between work and travel lane.\n• Foundations cured to design strength before column / panel placement.",
    references_cited:
      "OSHA 1926 Subpart M · OSHA 1926 Subpart CC · AASHTO LRFD",
    action_items:
      "Tag lines staged · Wind monitor on site · Fall protection 6 ft+ · Signal person designated",
  },
  {
    key: "hot_work",
    title: "Hot Work — Welding, Cutting, Grinding",
    category: "Procedure / SOP",
    hazards_reviewed:
      "Fire / explosion · Burns · UV / IR exposure (arc flash) · Welding fume inhalation · Hot slag igniting combustibles · Compressed gas cylinder rupture",
    discussion_notes:
      "• Hot Work Permit required and on site for any cutting/welding/grinding outside designated shop area.\n• Fire watch posted with extinguisher during AND 30 minutes after work.\n• Combustibles within 35 ft removed or shielded with welding blankets.\n• Cylinders chained upright, caps on, oxygen and fuel separated by 20 ft or 5-ft non-combustible barrier.\n• Eye protection — shade matched to amperage; bystanders shielded.\n• Ventilation or supplied air for galvanized, cadmium, or coated metal.",
    references_cited:
      "OSHA 1926 Subpart J · OSHA 1926.352 · NFPA 51B · ANSI Z49.1",
    action_items:
      "Hot work permit signed · Fire watch assigned · Combustibles cleared · Extinguisher staged · Cylinders secured",
  },

  // ============================================================
  // FALL PROTECTION / ELEVATED WORK
  // ============================================================
  {
    key: "fall_protection",
    title: "Fall Protection — General",
    category: "Hazard-Specific",
    hazards_reviewed:
      "Falls from elevation · Falls into excavations · Falls through openings · Improper anchor failure · Struck-by falling tools · Suspension trauma",
    discussion_notes:
      "• 100% tie-off above 6 ft in construction.\n• Anchor points rated 5,000 lb minimum or engineered system.\n• Inspect harness / lanyard / SRL before EVERY use — no abrasion, cuts, deployed indicators, corrosion.\n• Calculate fall clearance — anchor + lanyard + free fall + deceleration + safety factor.\n• Rescue plan in place; suspended worker requires rescue within 15 minutes.\n• Tools tethered or in zipped pouches at height.\n• Guardrails, covers, barricades on every hole and edge.",
    references_cited:
      "OSHA 1926 Subpart M · OSHA 1926.501 · ANSI Z359",
    action_items:
      "Harnesses inspected · Anchor points identified · Rescue plan briefed · Holes covered · Tools tethered",
  },
  {
    key: "ladder_safety",
    title: "Ladder Safety",
    category: "Tool / Equipment Specific",
    hazards_reviewed:
      "Falls from ladder · Ladder slide-out · Tipping · Electrocution from overhead lines · Overreaching · Damaged rungs / rails",
    discussion_notes:
      "• Inspect every ladder before use — no cracks, bent rails, missing feet.\n• 4:1 angle rule for extension ladders.\n• Three points of contact; never carry tools up.\n• Extend 3 ft above landing point, secured at top.\n• Never the top two rungs of a stepladder; never the top of any extension ladder.\n• Non-conductive (fiberglass) only when working near electrical.\n• Don't reach beyond the side rails — get down and move it.",
    references_cited:
      "OSHA 1926 Subpart X · OSHA 1926.1053 · ANSI A14",
    action_items:
      "Ladders inspected · Defective ladders tagged · Anchor / tie-off where 6 ft+ · Fiberglass for electrical",
  },
  {
    key: "aerial_lift",
    title: "Aerial Lift / Boom Lift Operations",
    category: "Tool / Equipment Specific",
    hazards_reviewed:
      "Falls from platform · Tip-over from overload or uneven ground · Struck-by overhead obstacle · Electrocution from overhead lines · Crushing between platform and structure",
    discussion_notes:
      "• Operator certified and authorized; pre-shift inspection completed.\n• Tie-off in bucket — full body harness, lanyard to manufacturer's anchor.\n• Outriggers (where equipped) fully extended on level ground.\n• Maintain 10 ft minimum from energized lines; more for higher voltage.\n• No climbing on rails or out of bucket — bucket is the only allowed work position.\n• Sound horn before moving; spotter when traveling near workers.",
    references_cited:
      "OSHA 1926.453 · ANSI A92 · Manufacturer Operator Manual",
    action_items:
      "Pre-shift inspection logged · Operator certified · Tie-off in bucket · Overhead clearance verified",
  },
  {
    key: "scaffold",
    title: "Scaffold Safety",
    category: "Tool / Equipment Specific",
    hazards_reviewed:
      "Falls from scaffold · Scaffold collapse from improper erection · Struck-by falling material · Electrocution near power lines · Tipping from inadequate base",
    discussion_notes:
      "• Erected, modified, or dismantled only by qualified persons under competent person supervision.\n• Daily inspection by competent person before each shift.\n• Guardrails on all open sides over 10 ft.\n• Toe boards, screens, or debris nets to prevent falling materials.\n• Base on mud sills or base plates on solid ground; height-to-base ratio per mfr.\n• Maintain 10 ft+ from overhead power lines.\n• Access via stairway, ladder tower, or built-in ladder — no climbing braces.",
    references_cited:
      "OSHA 1926 Subpart L · OSHA 1926.451",
    action_items:
      "Daily inspection logged · Guardrails / toe boards in place · Base verified · Access route in place",
  },
  {
    key: "bridge_overpass",
    title: "Bridge / Overpass Work",
    category: "Hazard-Specific",
    hazards_reviewed:
      "Falls over edge · Falls through deck openings · Live traffic below or adjacent · Dropped objects to lanes below · Struck-by traveling traffic",
    discussion_notes:
      "• Perimeter fall protection BEFORE any deck work.\n• Catch platforms / debris nets to protect lanes below.\n• Tools tethered; small parts in zipped pouches.\n• Coordinate live-traffic closure below for any high-risk operation.\n• Edge work: positive anchor and PFAS — no lone-worker edge tasks.\n• Wind monitoring for high-mast operations.",
    references_cited:
      "OSHA 1926 Subpart M · AASHTO Bridge Construction · ANSI Z359",
    action_items:
      "Perimeter PFAS in place · Catch platform set · Tools tethered · Lane closure coordinated",
  },
  {
    key: "cranes_hoisting",
    title: "Crane Lift Operations",
    category: "Tool / Equipment Specific",
    hazards_reviewed:
      "Crane tipping · Struck-by suspended load · Crushed by load · Two-blocking · Overhead line contact · Failure of rigging · Uncertified operator / signal person",
    discussion_notes:
      "• Operator AND signal person certified.\n• Pre-lift plan: load weight, radius, rigging, ground bearing, swing path.\n• Outriggers fully extended on cribbing; ground bearing capacity confirmed.\n• Maintain power-line clearance (Table A-encroachment).\n• Tag lines control load rotation; no workers under suspended load.\n• Anti-two-block device functional; LMI calibrated.\n• Wind speed monitored — stop at mfr / engineer threshold.",
    references_cited:
      "OSHA 1926 Subpart CC · ASME B30 · OSHA 1926.1408",
    action_items:
      "Lift plan signed · Operator/signal certified · Cribbing in place · Tag lines staged · Wind monitor",
  },
  {
    key: "rigging_load_securement",
    title: "Rigging & Load Securement",
    category: "Tool / Equipment Specific",
    hazards_reviewed:
      "Sling failure · Load shift in transit · Improper hitch / connection · Damaged rigging · Pinch points · Falling material from incorrect chock or strap",
    discussion_notes:
      "• Inspect every sling, shackle, hook before use; remove damaged items from service.\n• Match sling capacity to load — derate for hitch type and angle.\n• Shackles screw-pin or bolt-type for overhead lifts; never side-loaded.\n• Working load limit (WLL) tags legible; tagged-out gear quarantined.\n• Workers never under suspended load; tag lines for control.\n• Truck loads: chocks, straps to FMCSA cargo securement standard.",
    references_cited:
      "OSHA 1926.251 · ASME B30.9 (Slings) · FMCSA 49 CFR 393",
    action_items:
      "Rigging inspected · Sling capacities verified · Tag lines staged · Cargo securement reviewed",
  },

  // ============================================================
  // ELECTRICAL
  // ============================================================
  {
    key: "electrical_safety",
    title: "Electrical Safety & Energized Equipment",
    category: "Hazard-Specific",
    hazards_reviewed:
      "Electrocution · Arc flash / blast · Burns · Fall caused by shock · Fire from damaged cords · Unexpected startup",
    discussion_notes:
      "• GFCI on every 120V circuit on the job — temp power, generators, extension cords.\n• Inspect cords daily — no damaged jackets, exposed conductors, missing ground pins.\n• LOTO for any work on electrical systems — verified de-energized with a tester.\n• Maintain 10 ft minimum approach to overhead lines (more for higher voltage).\n• Panels and disconnects covered and labeled.\n• Only qualified persons work on energized equipment, and only when de-energizing isn't feasible.",
    references_cited:
      "OSHA 1926 Subpart K · OSHA 1926.404 · NFPA 70E · OSHA LOTO 1910.147",
    action_items:
      "GFCI verified · Cords inspected · LOTO followed · Overhead clearance maintained",
  },
  {
    key: "loto",
    title: "Lockout / Tagout (LOTO)",
    category: "Procedure / SOP",
    hazards_reviewed:
      "Unexpected startup · Stored energy release (hydraulic, pneumatic, gravity, springs) · Multiple energy sources · Bypassing controls · Removing someone else's lock",
    discussion_notes:
      "• Identify EVERY energy source — electrical, hydraulic, pneumatic, gravity, thermal, chemical.\n• Notify affected employees, shut down using normal procedure, isolate, lock + tag, verify zero energy.\n• Each authorized worker applies their own personal lock — no shared locks.\n• Test for zero energy: start switch, gauges, manual operation as appropriate.\n• Removing your own lock = your responsibility. Removing someone else's requires absent-employee removal procedure.\n• Group LOTO uses lockbox + master tag; everyone signs on, signs off.",
    references_cited:
      "OSHA 1910.147 · OSHA 1926 Subpart K · ANSI Z244.1",
    action_items:
      "LOTO procedure on site · Personal locks issued · Energy sources identified · Verification step trained",
  },
  {
    key: "overhead_power",
    title: "Working Near Overhead Power Lines",
    category: "Hazard-Specific",
    hazards_reviewed:
      "Electrocution from contact · Arc flash from approach · Equipment movement (boom, dump body, ladder) into clearance zone · Induced voltage on parallel objects",
    discussion_notes:
      "• 10 ft minimum clearance for lines up to 50 kV; more for higher voltage.\n• Where 10 ft can't be maintained: de-energize + ground OR install line covers OR use dedicated spotter.\n• Boom equipment near lines — proximity alarms, dedicated spotter, table-A clearances.\n• Dump bodies / ladders — kept low until clear of overhead.\n• If equipment contacts a line: STAY IN CAB. Operator drives out of contact if possible. If not, jump clear and shuffle 30+ ft away.",
    references_cited:
      "OSHA 1926.1408 (Cranes) · OSHA 1926.952 · OSHA 1926.405",
    action_items:
      "Lines identified · Clearance verified · Spotter assigned · Contact response briefed",
  },
  {
    key: "generator_temp_power",
    title: "Generator / Temporary Power Setup",
    category: "Tool / Equipment Specific",
    hazards_reviewed:
      "CO poisoning · Electrical shock · Fire / fuel spill · Backfeed onto utility lines · Generator overloading",
    discussion_notes:
      "• NEVER run a fuel-burning generator indoors or in any enclosed space — CO kills.\n• 20 ft minimum from buildings, vents, and air intakes.\n• Bond generator frame to ground rod where required.\n• GFCI on every 120V outlet — many gen outlets are not internally GFCI-protected.\n• Size circuits for the load; spread loads across phases.\n• If feeding a panel, use a transfer switch (no backfeeding through outlets).\n• Refuel only when cold; bonded fuel containers; no smoking.",
    references_cited:
      "OSHA 1926.405 · NFPA 70 (NEC) · NIOSH CO Bulletin",
    action_items:
      "Generator placement verified · Bonding/grounding in place · GFCI confirmed · Fuel handling area set up",
  },
  {
    key: "light_tower",
    title: "Light Tower Operations",
    category: "Tool / Equipment Specific",
    hazards_reviewed:
      "Tipping during raise / lower · Overhead clearance contact · Burns from hot lights · CO from generator section · Electrical shock from damaged cords",
    discussion_notes:
      "• Place on stable level ground; outriggers fully extended.\n• Verify overhead clearance before raising mast.\n• Lock mast at full height before walking away.\n• Generator: refuel cold, bonded container, no smoking, 20 ft from buildings.\n• Hot lights — let cool before any service or relocation.\n• Inspect cords daily; damaged tower removed from service.",
    references_cited:
      "OSHA 1926.405 · Manufacturer Operator Manual",
    action_items:
      "Outriggers set · Overhead clearance verified · Mast locked · Refuel procedure followed",
  },
  {
    key: "lightning",
    title: "Lightning & Severe Storms",
    category: "Hazard-Specific",
    hazards_reviewed:
      "Direct strike · Side flash · Ground current · Equipment energization · Wind damage · Flash flooding",
    discussion_notes:
      "• 30/30 rule — when thunder follows lightning by 30 seconds or less, stop work and shelter. Wait 30 minutes after the last thunder before resuming.\n• No shelter under isolated trees, equipment cabs (open), or scaffolds.\n• Best shelter: enclosed building, hard-topped vehicle (windows up).\n• Disconnect cranes, equipment, and tools from power before storm.\n• Watch for flash flooding in low-lying areas of work site.",
    references_cited:
      "NWS Lightning Safety · OSHA Lightning Bulletin · NFPA 780",
    action_items:
      "Weather monitoring app installed · Shelter location identified · 30/30 rule briefed · Equipment shutdown plan",
  },

  // ============================================================
  // EQUIPMENT-SPECIFIC
  // ============================================================
  {
    key: "excavator_safety",
    title: "Excavator Safety",
    category: "Tool / Equipment Specific",
    hazards_reviewed:
      "Tipping on slopes · Struck-by bucket / counterweight · Crushed in swing radius · Cab fall on slope · Hydraulic line failure · Quick coupler disengagement",
    discussion_notes:
      "• Pre-shift walkaround; check tracks, undercarriage, hydraulics, fluids, cab attachments.\n• Operator buckles seat belt before start.\n• Swing radius marked / barricaded — workers stay outside.\n• Bucket on ground when loading trucks; never swing over operator cab.\n• Quick coupler: positive engagement verified before lifting.\n• Park on level ground, bucket down, key out, brake set when leaving cab.",
    references_cited:
      "OSHA 1926.602 · Manufacturer Operator Manual",
    action_items:
      "Pre-op inspection logged · Swing radius marked · Quick coupler verified · Park-out routine followed",
  },
  {
    key: "skid_steer",
    title: "Skid Steer / CTL Safety",
    category: "Tool / Equipment Specific",
    hazards_reviewed:
      "Crushed by lift arms (entry/exit hazard) · Tipping on slope · Struck-by attachments · Run-over by reversing machine · Burns from exhaust/turbo · Quick attach disengagement",
    discussion_notes:
      "• Enter/exit ONLY with arms lowered and bucket flat — never under raised arms.\n• Seat belt and seat bar lowered before start.\n• Quick attach pins fully engaged — verify before lifting.\n• No riders. No standing on attachments.\n• Backing in congested areas requires spotter.\n• Park on level ground, arms down, bucket on ground.",
    references_cited:
      "OSHA 1926.602 · Manufacturer Operator Manual · NIOSH Skid Steer Bulletin",
    action_items:
      "Seat belt enforced · Quick attach verified · Spotter assigned · No riders briefed",
  },
  {
    key: "forklift_telehandler",
    title: "Forklift / Telehandler Operations",
    category: "Tool / Equipment Specific",
    hazards_reviewed:
      "Tipping (loaded or unloaded) · Struck-by load · Run-over of pedestrians · Falls from forks (no riders) · Overhead clearance contact · Load too high to see over",
    discussion_notes:
      "• Operator certified (3-year cert + evaluation).\n• Pre-shift inspection logged.\n• Capacity at boom extension is LESS than at retracted — read the chart.\n• Load behind heel of forks; tilt back during travel.\n• Travel forks low, tines about 6 in. above ground.\n• Backing on ramps with load uphill; no riders ever.\n• Outriggers required for telehandler at full reach.",
    references_cited:
      "OSHA 1926.602 · OSHA 1910.178 · ANSI/ITSDF B56.6 · ANSI/ITSDF B56.1",
    action_items:
      "Operator cert current · Capacity chart on machine · Outriggers procedure · No-riders rule briefed",
  },
  {
    key: "dump_truck",
    title: "Dump Truck Operations",
    category: "Tool / Equipment Specific",
    hazards_reviewed:
      "Rollover during dump (uneven ground / soft ground) · Struck-by raised body or tailgate · Overhead line contact during dump · Run-over while spotting · Hot engine / exhaust burns",
    discussion_notes:
      "• Dump on level, firm ground only.\n• Verify NO overhead obstacles (lines, branches, structures) before raising body.\n• Driver stays in cab during dump; spotter outside line-of-fall.\n• Tailgate clear of obstructions before lift; manually swing or release per truck.\n• No one between truck and equipment loading it.\n• Pre-trip inspection daily.",
    references_cited:
      "OSHA 1926.601 · DOT FMCSA Pre-Trip · Manufacturer Operator Manual",
    action_items:
      "Pre-trip log completed · Dump site verified level · Overhead clearance checked · Spotter position briefed",
  },

  // ============================================================
  // GENERAL / PERSONAL SAFETY
  // ============================================================
  {
    key: "ppe_general",
    title: "PPE — Daily Compliance Review",
    category: "Stretch & Flex",
    hazards_reviewed:
      "Head injury · Eye injury · Hearing loss · Foot injury · Hand laceration · Crush injury · Hi-vis non-compliance leading to struck-by",
    discussion_notes:
      "• Hard hat — Type II for traffic / impact zones; replace every 5 years or after impact.\n• Safety glasses with side shields — ANSI Z87 minimum.\n• Hi-vis Class 2 day / Class 3 night for all roadway work.\n• Steel or composite toe boots — no athletic shoes.\n• Cut-resistant gloves for sharp / abrasive work.\n• Hearing protection wherever noise > 85 dBA TWA.\n• PPE inspected before use; damaged PPE removed from service.",
    references_cited:
      "OSHA 1926 Subpart E · OSHA 1926.95 · ANSI Z87 / Z89 / Z41",
    action_items:
      "PPE inventory checked · Damaged PPE replaced · Hi-vis class verified · Hearing protection available",
  },
  {
    key: "stop_work",
    title: "Stop Work Authority",
    category: "Procedure / SOP",
    hazards_reviewed:
      "Imminent danger ignored · Production pressure overriding safety · Hazardous condition allowed to escalate · Near-miss not reported",
    discussion_notes:
      "• EVERY crew member has the authority and the responsibility to stop work for any safety concern.\n• No one will be retaliated against, ever, for stopping work in good faith.\n• Process: Stop. Notify. Correct. Resume. — all four steps.\n• Document the stop-work event so we can learn from it.\n• Stop work covers your own work, your crew, the public — anyone exposed.\n• If you're not sure, stop. Better to lose 5 minutes than a coworker.",
    references_cited:
      "OSHA General Duty Clause 5(a)(1) · MASCI Stop Work Policy",
    action_items:
      "Stop Work poster visible · Crew acknowledged authority · Recent stop-work events reviewed",
  },
  {
    key: "heat_stress",
    title: "Heat Stress / Hydration",
    category: "Hazard-Specific",
    hazards_reviewed:
      "Heat exhaustion · Heat stroke (medical emergency) · Dehydration · Reduced reaction time · Sunburn / UV exposure",
    discussion_notes:
      "• Water, rest, shade — the OSHA-NIOSH heat protocol.\n• 1 cup of water every 15-20 minutes during heavy work in heat.\n• Acclimatize new and returning workers — 20% workload day 1, increase 20% per day.\n• Buddy system — watch your partner for confusion, slurred speech, hot dry skin = heat stroke = 911.\n• Schedule heaviest work for cooler hours when feasible.\n• Heat index posted daily; protocol triggers at 80°F+ heat index.\n• Cool-down breaks in shade or AC every hour during high-heat days.",
    references_cited:
      "OSHA Heat Illness Campaign · NIOSH Criteria · OSHA-NIOSH Heat Tool",
    action_items:
      "Water and ice staged · Shade structure on site · Heat-index protocol posted · Acclimatization plan",
  },
  {
    key: "cold_stress",
    title: "Cold Stress / Hypothermia",
    category: "Hazard-Specific",
    hazards_reviewed:
      "Hypothermia · Frostbite · Reduced manual dexterity · Slips on ice · Cold shock from contact with ice water · Buried in collapsed snow",
    discussion_notes:
      "• Layered clothing: wicking base, insulating mid, wind/water-resistant outer.\n• Cover head, neck, hands, feet — most heat loss is from extremities.\n• Buddy system — frostbite first signs are subtle (numbness, white skin).\n• Warming area within 100 ft, hot drinks (no alcohol, limit caffeine).\n• Shorter work intervals at lower temps; rotate crew.\n• Watch for hypothermia: confusion, slurred speech, shivering — 911 + warm + stable.\n• De-ice walking surfaces before shift.",
    references_cited:
      "OSHA Cold Stress Bulletin · NIOSH Cold Stress · CDC Hypothermia",
    action_items:
      "Cold-weather PPE issued · Warming area set · Buddy system · De-icing supplies staged",
  },
  {
    key: "near_miss",
    title: "Near-Miss Reporting",
    category: "Procedure / SOP",
    hazards_reviewed:
      "Recurring near-misses leading to actual injury · Unreported hazards · Trend data lost · Culture of silence",
    discussion_notes:
      "• A near-miss is a free lesson. Treat it like an injury you got lucky on.\n• Report any unsafe act, unsafe condition, or close call — same shift.\n• Anonymous reporting available; no retaliation.\n• MASCI tracks near-misses for trends — this is how we prevent the next incident.\n• Don't blame the worker; fix the condition or process.\n• Examples: dropped tool from height, vehicle intrusion, suspended load swing wide, almost-trip-and-fall.",
    references_cited:
      "OSHA VPP · ANSI Z10 · MASCI Near-Miss Procedure",
    action_items:
      "Near-miss form available · Reporting reviewed · Recent reports discussed · Corrective actions tracked",
  },
  {
    key: "stretch_flex",
    title: "Stretch & Flex / Daily Huddle",
    category: "Stretch & Flex",
    hazards_reviewed:
      "Strains and sprains · Soft-tissue injuries · Cold muscle injury · Repetitive motion · Slips/trips/falls during first hour of shift",
    discussion_notes:
      "• 5-minute stretch routine before work — neck, shoulders, back, hips, hamstrings.\n• Walk through today's task list and identify anything new or unusual.\n• Confirm crew assignments and equipment for the shift.\n• Identify weather concerns (heat, cold, lightning, wind, rain).\n• Confirm everyone is fit for duty — no impairment, illness, or fatigue concerns.\n• Quick safety reminder relevant to today's work.",
    references_cited:
      "MASCI Daily Huddle SOP · NIOSH Ergonomics",
    action_items:
      "Stretch routine completed · Today's tasks briefed · Weather check · Fit-for-duty confirmed",
  },
  {
    key: "slips_trips",
    title: "Slips, Trips & Falls (Same-Level)",
    category: "Hazard-Specific",
    hazards_reviewed:
      "Slip on wet/oily/icy surfaces · Trip on hoses, rebar, debris · Fall on uneven terrain · Twisted ankle from holes / soft spots · Carrying load while walking",
    discussion_notes:
      "• Most common injury cause on heavy civil — and most preventable.\n• Walking surfaces clear of hoses, cords, rebar — coil and stack.\n• Walk paths defined and marked through the work site.\n• Boots with aggressive tread; replace when worn.\n• Don't carry loads that block your view of feet.\n• Salt/sand or sweep ice and debris.\n• Holes covered or barricaded — flag uneven ground.",
    references_cited:
      "OSHA 1926.25 · OSHA 1926.501 · NIOSH STF",
    action_items:
      "Walk paths marked · Cords/hoses managed · Holes covered · Walking surfaces maintained",
  },
  {
    key: "hand_injury",
    title: "Hand Injury Prevention",
    category: "Hazard-Specific",
    hazards_reviewed:
      "Lacerations · Crush injuries (pinch points) · Punctures · Burns · Amputations from rotating equipment · Repetitive strain",
    discussion_notes:
      "• Match the glove to the hazard — cut-resistant for sharp, chemical for chemical, impact for impact.\n• Identify pinch points before reaching — use tools to position, not hands.\n• Push, don't pull — when pulling fails, your hand goes into what you're pulling against.\n• Never touch a moving blade, drum, conveyor — LOTO before service.\n• Inspect tools daily; remove damaged tools from service.\n• Take a knee or use a stable platform for fine work.",
    references_cited:
      "OSHA 1926.95 · BLS Injury Statistics · MASCI Hand Safety Policy",
    action_items:
      "Task-appropriate gloves issued · Pinch points identified · Tools inspected · LOTO procedures briefed",
  },
  {
    key: "hearing_conservation",
    title: "Hearing Conservation",
    category: "Hazard-Specific",
    hazards_reviewed:
      "Permanent noise-induced hearing loss · Tinnitus · Communication difficulty masking other hazards · Cumulative damage over career",
    discussion_notes:
      "• OSHA action level 85 dBA TWA — most heavy iron exceeds this.\n• Earplugs OR earmuffs — both for impact noise (jackhammer, milling drum, demolition).\n• Replace foam plugs daily; clean reusables daily.\n• Annual audiogram per the hearing conservation program.\n• Watch for early signs: ringing in ears, having to turn up TV, missing conversations.\n• Quiet hand signals during high-noise work; pre-arrange comms.",
    references_cited:
      "OSHA 1926.101 · OSHA 1910.95 · NIOSH REL",
    action_items:
      "Hearing protection available · Worn during high-noise work · Annual audiogram scheduled",
  },
  {
    key: "respiratory_protection",
    title: "Respiratory Protection",
    category: "Procedure / SOP",
    hazards_reviewed:
      "Silica · Asbestos · Welding fumes · Asphalt / paint solvents · Diesel exhaust · CO · Mold / dust · Inadequate fit allowing exposure",
    discussion_notes:
      "• Respirator required when engineering controls are insufficient.\n• Annual fit testing — quantitative or qualitative — recorded.\n• Medical clearance before respirator use.\n• Match cartridge to contaminant — P100 for particulates, OV for organic vapors.\n• Inspect respirator before each use; user seal check every donning.\n• Beards / facial hair break the seal — clean shave at sealing surface.\n• Cartridges have service life — change per the schedule.",
    references_cited:
      "OSHA 1910.134 · OSHA 1926.103 · NIOSH respirator certification",
    action_items:
      "Fit tests current · Cartridges in stock · Seal-check procedure briefed · Schedule for cartridge change",
  },
  {
    key: "fatigue",
    title: "Fatigue & Drowsy Driving",
    category: "Hazard-Specific",
    hazards_reviewed:
      "Drowsy driving (commute) · Reduced reaction time on equipment · Decision-making errors · Microsleep · Increased injury rate at end of long shifts",
    discussion_notes:
      "• Most likely fatal injury cause in our industry isn't on-site — it's the drive home.\n• 7-9 hours sleep is non-negotiable for safe operation.\n• Long shifts, night shifts, and consecutive 10s/12s elevate risk significantly.\n• Buddy system — say something if a coworker is showing signs of fatigue.\n• Pull over and nap if drowsy on the drive home — coffee + cold AC is a myth.\n• Report fatigue to foreman — better than a crash.",
    references_cited:
      "NIOSH Fatigue at Work · NHTSA Drowsy Driving · NSC",
    action_items:
      "Crew briefed on fatigue signs · Buddy check at end of shift · Sleep before long shifts emphasized",
  },
  {
    key: "drug_alcohol",
    title: "Drug & Alcohol Policy / Fit for Duty",
    category: "Procedure / SOP",
    hazards_reviewed:
      "Impaired operation of equipment / vehicle · Reduced reaction time · Poor decision-making · Increased injury rate · Legal / DOT violations",
    discussion_notes:
      "• Zero tolerance for alcohol or drugs (including marijuana) on company time or DOT-covered roles.\n• Prescription meds — disclose to supervisor if they may impair operation.\n• Random testing per DOT and MASCI policy.\n• 'Fit for duty' = clear-headed, well-rested, healthy enough to do the work.\n• Reasonable suspicion testing if behavior, smell, or eyes suggest impairment.\n• Self-report and EAP referral protected — get help, don't hide.",
    references_cited:
      "DOT 49 CFR Part 40 · MASCI Substance Abuse Policy · OSHA Drug-Free Workplace",
    action_items:
      "Policy posted · Random testing schedule current · EAP contact info available",
  },
  {
    key: "bloodborne",
    title: "Bloodborne Pathogens & First Aid Response",
    category: "Procedure / SOP",
    hazards_reviewed:
      "Exposure to blood / OPIM · HIV / Hep B / Hep C · Improper PPE during response · Improper sharps handling · Failure to report exposure",
    discussion_notes:
      "• Treat ALL blood and body fluids as potentially infectious — universal precautions.\n• Disposable gloves, eye protection, mask if splash risk.\n• Clean spill with approved disinfectant; sharps in puncture-resistant container.\n• Wash hands thoroughly after any response, glove or no glove.\n• Report any exposure incident immediately — Hep B vaccine and follow-up available.\n• First-aid kit stocked, location known, trained responders identified.",
    references_cited:
      "OSHA 1910.1030 · OSHA 1926.50 (First Aid) · CDC BBP",
    action_items:
      "First-aid kit checked · Trained responders identified · Spill kit available · Reporting procedure briefed",
  },
  {
    key: "hazcom_sds",
    title: "Hazard Communication / SDS",
    category: "Procedure / SOP",
    hazards_reviewed:
      "Chemical exposure from unknown product · Wrong PPE for chemical · Storage incompatibilities (flammable + oxidizer) · Improper disposal · Pictograms misunderstood",
    discussion_notes:
      "• Every chemical on site has an SDS — readily accessible.\n• Read SDS before first use: hazards, PPE, storage, first aid, spill response.\n• Container labels intact and legible — no unmarked transfer containers.\n• 9 GHS pictograms — know what each one means.\n• Storage segregation: flammables apart from oxidizers, acids apart from bases.\n• Disposal per SDS and EPA / state requirements — not into storm drains.",
    references_cited:
      "OSHA 1926.59 · OSHA 1910.1200 · GHS",
    action_items:
      "SDS binder current · Labels checked · Storage segregation verified · Disposal location identified",
  },
  {
    key: "wildlife_insects",
    title: "Wildlife / Insect Bites & Stings",
    category: "Hazard-Specific",
    hazards_reviewed:
      "Bee / wasp stings (anaphylaxis) · Snake bites · Fire ant attacks · Tick / mosquito-borne illness · Alligator / wildlife encounters · Spider bites · Animal-vehicle strikes",
    discussion_notes:
      "• Walk paths cleared; eyes on the ground in tall grass.\n• Heavy boots and long pants in brush areas.\n• Insect repellent with DEET 20-30%.\n• Bee/wasp allergy — EpiPen on site, location known to crew.\n• Snake bite: keep victim calm, immobilize bitten area, 911 — NO ice, NO tourniquet, NO suction.\n• Fire ants: vacate area, brush off, treat stings; allergic reaction = 911.\n• Alligators in FL waterways — never approach, never feed, 30 ft minimum.",
    references_cited:
      "CDC Vector-Borne Diseases · OSHA Quick Card Wildlife · State Wildlife Agency",
    action_items:
      "First-aid kit includes sting/bite supplies · EpiPen location known · Repellent stocked",
  },
  {
    key: "site_walk",
    title: "Daily Site Walk / Hazard Assessment",
    category: "Stretch & Flex",
    hazards_reviewed:
      "New hazards from yesterday's work · Weather-induced changes (water, frost, wind damage) · Equipment / material moved · Public encroachment · Utility work since last shift",
    discussion_notes:
      "• Foreman walks the entire work zone before crews start.\n• Look for anything new or different from yesterday: water in trench, displaced barricades, knockdowns, theft, vandalism.\n• Verify protective systems still in place.\n• Check for trip hazards from overnight equipment / material movement.\n• Reset / replace anything missing or damaged before crews enter.\n• Document and brief findings to crew at huddle.",
    references_cited:
      "MASCI Site Walk SOP · OSHA Competent Person",
    action_items:
      "Walk completed before crews start · Findings briefed · Corrections logged",
  },
  {
    key: "housekeeping_cleanup",
    title: "End-of-Shift Cleanup & Housekeeping",
    category: "Stretch & Flex",
    hazards_reviewed:
      "Trip hazards from material left out · Theft of unsecured tools / equipment · Public injury from open hazards overnight · Storm drain contamination from spills · Vandalism / encroachment",
    discussion_notes:
      "• 15 minutes of housekeeping at end of every shift — non-negotiable.\n• Tools and small equipment locked up; large equipment parked safely.\n• Open trenches / structures covered, barricaded, lighted.\n• MOT devices restored to night-time configuration; lights checked.\n• Trash and debris collected; no plastic / waste left to blow into storm drains.\n• Walk the site one last time before leaving.",
    references_cited:
      "OSHA 1926.25 · MASCI Housekeeping Standard",
    action_items:
      "Tools secured · Excavations covered/lit · MOT verified · Walk-through completed",
  },
  {
    key: "new_hire_orientation",
    title: "New Hire / New-to-Site Orientation",
    category: "Procedure / SOP",
    hazards_reviewed:
      "Unfamiliarity with site hazards · Unknown equipment / procedures · Higher injury rate in first 30 days · Missed PPE / training requirements · Cultural mismatch on Stop Work",
    discussion_notes:
      "• EVERY new hire and EVERY person new to this site gets a site-specific orientation.\n• Walk the site, point out hazards, evacuation routes, first-aid kit, fire extinguishers.\n• Review project-specific TCP, JHP for their crew, and any active permits.\n• Reinforce Stop Work Authority — they have it from minute one.\n• Pair with experienced buddy for first 1-3 days.\n• Confirm required certs / training current before they start.",
    references_cited:
      "OSHA 1926.21 · MASCI New Hire Procedure",
    action_items:
      "Site orientation completed · Buddy assigned · Training records verified · Stop Work Authority briefed",
  },
  {
    key: "subcontractor_coordination",
    title: "Subcontractor Coordination",
    category: "Procedure / SOP",
    hazards_reviewed:
      "Conflicting work activities · Unfamiliar with each other's hazards · Different safety standards · Communication breakdown · Schedule pressure overriding sequence",
    discussion_notes:
      "• Every sub onsite has had pre-mob safety review with MASCI.\n• Daily coordination meeting — who's where, what activities, conflicts identified.\n• Subs follow MASCI safety standards or higher — never lower.\n• MASCI Stop Work Authority extends to ALL workers regardless of employer.\n• JHP / pre-task plan shared between conflicting trades.\n• Incidents reported to MASCI same day.",
    references_cited:
      "OSHA Multi-Employer Citation Policy · MASCI Subcontractor Pre-Qual",
    action_items:
      "Sub safety reps identified · Daily coordination scheduled · Stop Work Authority extended · JHPs cross-shared",
  },
  {
    key: "emergency_action_plan",
    title: "Emergency Action Plan / Evacuation",
    category: "Procedure / SOP",
    hazards_reviewed:
      "Site-wide emergencies (fire, gas leak, severe weather, active threat) · Inadequate evacuation · Failure to account for personnel · Blocked emergency egress · Delayed 911 response",
    discussion_notes:
      "• Every site has a posted EAP — assembly point, primary and secondary evacuation routes, 911 directions, on-site emergency contacts.\n• Account for ALL personnel at the assembly point — buddy system or sign-in.\n• Never re-enter for tools, vehicles, or material.\n• 911 caller stays on line; provide site address and gate access info.\n• Equipment ops shut down equipment safely if time allows; otherwise evacuate immediately.\n• Drill the EAP every 90 days or after major site changes.",
    references_cited:
      "OSHA 1926.35 · NFPA 101 · State / Local Emergency Management",
    action_items:
      "EAP posted · Assembly point known · 911 address verified · Drill scheduled",
  },
  {
    key: "fire_prevention",
    title: "Fire Prevention & Extinguisher Use",
    category: "Procedure / SOP",
    hazards_reviewed:
      "Hot work ignition · Fuel spill / vapor ignition · Smoking near flammables · Improper extinguisher selection · Untrained worker fighting fire · Vehicle/equipment fire",
    discussion_notes:
      "• Combustibles 35 ft+ from any hot work; extinguisher staged.\n• ABC dry chemical for most jobsite fires; CO2 for electrical; foam for fuels.\n• PASS: Pull, Aim, Squeeze, Sweep — only fight a fire smaller than a wastebasket and only with a clear escape path.\n• When in doubt — get out and call 911.\n• No smoking around fuel, grease, or solvents — designated areas only.\n• Inspect all extinguishers monthly; recharge after any use.",
    references_cited:
      "OSHA 1926 Subpart F · NFPA 10 · NFPA 51B",
    action_items:
      "Extinguishers inspected · PASS technique briefed · Designated smoking areas · Hot work permits in use",
  },
  {
    key: "spill_response",
    title: "Spill Response & Environmental Compliance",
    category: "Procedure / SOP",
    hazards_reviewed:
      "Fuel / oil release to soil or storm drain · Chemical spill · Environmental fines · Slip on spilled material · Vapor inhalation",
    discussion_notes:
      "• Spill kit available wherever fuel, oil, hydraulic fluid, chemicals are used or stored.\n• Stop the source first — shut valves, close containers.\n• Contain the spill — absorbent boom, socks, pads.\n• Clean up and dispose properly — contaminated materials are hazardous waste.\n• Report spills per state/EPA threshold — minor spills tracked, reportable spills called in within required time.\n• Storm drain protection mats during fueling.",
    references_cited:
      "EPA SPCC · State / FDEP requirements · NFPA 30",
    action_items:
      "Spill kits onsite · SDS for site chemicals available · Reporting threshold known · Storm drain mats deployed",
  },
  {
    key: "mental_health",
    title: "Mental Health & Suicide Prevention",
    category: "Other",
    hazards_reviewed:
      "Construction industry has elevated suicide rate · Stigma preventing help-seeking · Substance abuse · Family / financial stress · Co-worker grief",
    discussion_notes:
      "• Construction workers have one of the highest suicide rates of any industry — this matters.\n• Look out for each other: changes in mood, withdrawal, increased substance use, talk of hopelessness.\n• It's OK to ask: 'Are you OK? Are you thinking about hurting yourself?' Asking does NOT plant the idea — it can save a life.\n• 988 — Suicide & Crisis Lifeline (call or text). MASCI EAP for confidential help.\n• Reduce stigma — talking about mental health is strength, not weakness.\n• Encourage healthy coping: sleep, exercise, time off, peer support.",
    references_cited:
      "CDC Construction Suicide Data · 988 Lifeline · MASCI EAP · CIASP",
    action_items:
      "988 / EAP info posted · Crew check-in encouraged · Stigma reduction discussed",
  },

  // ============================================================
  // TRUCKING / FLEET · DUMP-BED STRIKE FAMILY · iter251 Phase B
  // ------------------------------------------------------------
  // Operator directive (2026-05-19): dump-bed strikes are an actively
  // observed catastrophic-risk pattern. Five dedicated topics with the
  // incident_pattern voice. Designed for drivers and yard leads, not
  // foremen reading off a slide.
  // ============================================================
  {
    key: "dump_bed_overhead_strike",
    title: "Dump Bed Strikes — Overhead Lines, Bridges, Signs, Conveyors",
    category: "Hazard-Specific",
    domain: "trucking",
    role_context: ["driver", "lead", "spotter"],
    incident_pattern:
      "Most overhead strikes happen at the dump site itself — not in transit. The driver finishes a load, the bed is still partially raised, and the truck rolls forward to clear the pile. Within three or four feet of forward travel, the raised bed catches an overhead line, a low bridge, a plant conveyor, or an overhead sign. By the time the driver realizes what happened, the line is on the ground or the conveyor is bent. Many of these strikes are fatal when the line is energized.",
    hazards_reviewed:
      "Electrocution from energized overhead lines · Bridge / sign / structure strike · Plant conveyor strike · Utility-strike outages · Roll-over from sudden stop with raised bed",
    discussion_notes:
      "• Before raising the bed — look up. Lines · bridges · signs · plant conveyors · overhead structures.\n• Maintain a 20-foot clearance from any energized line. If you can't be sure it's de-energized, treat it as live.\n• Set the parking brake before raising. The truck should NOT roll while the bed is in motion.\n• Do not move the truck until the bed is fully seated. Watch the in-cab indicator or the mirror — do not assume.\n• At unfamiliar dump sites (asphalt plants, MOT yards, customer sites), walk the area first. Know your overhead picture.\n• If a strike happens to an energized line: STAY IN THE CAB. Call 911. Wait for the utility to confirm the line is de-energized before stepping out. Stepping out with the truck energized has killed drivers.",
    references_cited:
      "OSHA 1926.601 · OSHA 1926.1408 (Power Line Clearance) · DOT FMCSA · Utility Strike Awareness",
    action_items:
      "Overhead walk-around discussed · Bed-up indicator reviewed · Energized-line response procedure reviewed · 20-foot clearance rule reinforced",
  },
  {
    key: "dump_bed_traveling_raised",
    title: "Traveling With the Bed Up — The Quiet Killer",
    category: "Hazard-Specific",
    domain: "trucking",
    role_context: ["driver", "lead"],
    incident_pattern:
      "After dumping, the driver becomes task-focused on exiting the area — checking mirrors, looking for the next load, watching ground spotters. The bed is still partially raised. The truck pulls forward, the driver shifts focus to the road, and the bed is now 6, 8, sometimes 14 feet in the air for the entire drive out. The strike happens at the first overhead obstruction — usually within 50 feet of the dump pile. Drivers describe it the same way every time: 'I forgot the bed was up.'",
    hazards_reviewed:
      "Catastrophic overhead strike · Utility line contact · Rollover from raised CG at highway speed · Bridge / sign impact · License-revocation incident",
    discussion_notes:
      "• The bed-down check is the FIRST thing after dumping — not the last. Before mirrors. Before radio. Before the next move.\n• Watch the in-cab body-up indicator. If your truck doesn't have one, you check the side mirror BEFORE rolling forward. Period.\n• Body-up alarms are not optional — if yours is broken, that truck doesn't haul until it's fixed. Tell Shop.\n• Plant exits, yard exits, and job-site exits are the most common strike points. Slow down at the exit and re-check.\n• Highway speed with the bed even partially raised raises your center of gravity dangerously — a curve at 55 mph can become a rollover.\n• If you realize the bed is up mid-travel: do NOT brake hard. Slow steadily. Find a safe pullout. Lower the bed there.",
    references_cited:
      "OSHA 1926.601 · DOT FMCSA Pre-Trip · Manufacturer Operator Manual · Body-Up Alarm Spec",
    action_items:
      "Bed-down-first habit reinforced · Body-up alarm operational check verified · Plant/yard exit awareness reviewed",
  },
  {
    key: "dump_bed_pto_habits",
    title: "PTO Disengagement and Bed-Down Habits",
    category: "Procedure / SOP",
    domain: "trucking",
    role_context: ["driver", "lead"],
    incident_pattern:
      "PTO-related bed-up incidents almost always trace back to habit, not equipment. The driver gets in a rhythm — dump, mirror check, roll. The bed-down step gets compressed or skipped. On hot days, fatigued drivers, busy plants with multiple trucks queueing, the muscle memory takes over. The truck moves before the PTO is disengaged and before the bed is fully seated. The next operation — backing under a conveyor, pulling into a yard, entering a plant scale — is when the strike happens.",
    hazards_reviewed:
      "Bed-up travel due to skipped PTO-down step · Hydraulic damage · Overhead strike · Mechanical failure from PTO-engaged transit · License-revocation incident",
    discussion_notes:
      "• PTO-down before truck-roll. Every dump. Every time. No exceptions.\n• Sequence: dump → bed-down → PTO-disengage → confirm indicator → mirror-check → roll.\n• If a queueing plant or busy customer site is making you compress the sequence, slow down. The plant will wait. The overhead line will not.\n• If your truck has an interlock (PTO-engaged prevents transmission engagement), do not bypass it. The interlock is the last defense.\n• Train new drivers on this sequence on Day 1. Make the bed-down step explicit and verbal.\n• After every dump, before moving — say out loud or to yourself: 'Bed down. PTO out. Mirror check.' Habit beats hurry.",
    references_cited:
      "OSHA 1926.601 · DOT FMCSA · Manufacturer PTO Spec · Plant Queueing SOP",
    action_items:
      "Dump sequence verbalized · PTO interlock function verified · Driver habit reinforcement discussed",
  },
  {
    key: "dump_bed_soft_ground_tipover",
    title: "Soft-Ground Tip-Overs — The Bed-Up Rollover",
    category: "Hazard-Specific",
    domain: "trucking",
    role_context: ["driver", "lead", "spotter"],
    incident_pattern:
      "A raised dump bed makes the truck top-heavy. A loaded raised bed makes it dangerously top-heavy. The risk is highest at the moment the material starts releasing unevenly — sticky asphalt, frozen material, half a load that's bridged. The driver feels the truck list, often misreads it as the bed releasing, and lifts higher. The center of gravity moves further outboard, the soft side compresses, and the truck rolls. Most soft-ground tip-overs happen on the second or third dump of the morning when the ground hasn't been disturbed yet.",
    hazards_reviewed:
      "Rollover with raised bed · Driver crush in cab roll · Material avalanche onto crew · Adjacent equipment / spotter struck-by · Soft fill / wet fill / freshly-disturbed ground tip-over",
    discussion_notes:
      "• Dump on level, firm ground. If the ground gives under foot, it'll give under 80,000 lb with a raised bed.\n• Loads that don't release evenly — STOP RAISING. Lower the bed. Investigate. Hot asphalt, frozen material, and bridged loads are the warning signs.\n• If you feel the truck list to one side as the bed comes up — that's not normal release. Lower the bed immediately. Get out and check.\n• Freshly placed fill, recent rain, freeze-thaw days — assume the ground is soft until proven otherwise. Walk it before backing in.\n• Never sit in the cab with seatbelt unbuckled during a dump. If the truck rolls, the seatbelt is what keeps you alive.\n• Spotters stay outside the line of fall — including the SIDES, not just the rear. A bed-up rollover throws material 30+ feet sideways.",
    references_cited:
      "OSHA 1926.601 · OSHA Roll-Over Protection · Manufacturer Operator Manual",
    action_items:
      "Ground-firmness check discussed · Uneven-release response reviewed · Seatbelt-during-dump policy reinforced · Spotter line-of-fall reviewed",
  },
  {
    key: "dump_bed_wind_raised",
    title: "High-Wind Raised-Bed Operations",
    category: "Hazard-Specific",
    domain: "trucking",
    role_context: ["driver", "lead"],
    incident_pattern:
      "A raised dump bed is a sail. At 30 mph sustained wind, an empty raised bed catches enough force to push the truck sideways or accelerate a tip-over that was already marginal. The worst incidents happen when crews are in a hurry to finish before a weather front arrives — bed up, gust hits, truck on three wheels before the driver can respond. The pattern repeats most often on exposed sites: bridge decks, levees, embankments, plant yards with open prevailing-wind exposure.",
    hazards_reviewed:
      "Wind-induced rollover with raised bed · Sustained-wind side load · Gust-front sudden load · Crew struck-by from uncontrolled tip · Material release in wind",
    discussion_notes:
      "• If sustained winds exceed 25–30 mph, consider whether the dump can wait. Empty raised beds at speed in side wind have rolled trucks.\n• Gusts are worse than sustained — a 50 mph gust into a raised bed is several thousand pounds of side load instantly.\n• Position the truck so the bed comes up INTO the wind, not crosswise to it. Reduces the sail effect.\n• Watch the sky and the radar. Weather fronts that move in fast (squall lines, summer thunderstorms) bring 50–70 mph gust fronts ahead of the rain.\n• If a gust hits with the bed up: hold the controls steady. Do NOT make sudden inputs. Most wind tip-overs are aggravated by panic steering.\n• On exposed sites — bridge decks, levees, plant yards with open exposure — set a wind threshold for the crew and call it before it gets bad.",
    references_cited:
      "OSHA 1926.601 · Manufacturer Wind-Operation Limits · NWS Gust-Front Awareness",
    action_items:
      "Crew wind threshold discussed · Bed-into-wind orientation reviewed · Weather-watch responsibility assigned",
  },

  // ============================================================
  // TRUCKING / FLEET · PHASE C EXPANSION · iter251
  // ------------------------------------------------------------
  // Operator directive (2026-05-19): 6 driver-oriented topics
  // beyond dump-bed strikes. Same incident_pattern voice. For
  // drivers, dispatchers, yard leads — not foremen on a slide.
  // ============================================================
  {
    key: "trucking_backing_struck_by",
    title: "Backing Accidents — Spotter Use and the Last 10 Feet",
    category: "Hazard-Specific",
    domain: "trucking",
    role_context: ["driver", "spotter", "lead"],
    incident_pattern:
      "Backing-related incidents are the single most common type of truck accident in heavy civil — and almost every fatality happens in the final 10 feet of the maneuver. The driver has already cleared the wide swing, is creeping back to position, and stops checking mirrors as confidently as they should. A laborer steps behind to grab a tool. A bucket is set down where the driver can't see it. A spotter walks out of the visual frame to take a call. The truck contacts something — a person, a piece of equipment, a wall — at 1 to 3 mph. That's enough to kill someone, total a pickup, or take a leg off.",
    hazards_reviewed:
      "Struck-by / run-over of ground workers · Crushing pinch with adjacent equipment · Property damage at the dump pile / loading pad · Spotter struck while signaling · Pedestrian worker on the blind side",
    discussion_notes:
      "• Use a spotter any time you are backing in a congested area, around personnel, or at any dock / pile / scale where you can't see your path clearly.\n• G-O-A-L: Get Out And Look. Before backing into a tight space, get out, walk the path, look up and look down. Then back.\n• Agree on hand signals BEFORE backing — the spotter should know YOUR signals and YOU should know what their stop-signal looks like.\n• If you lose sight of the spotter for ANY reason — stop. Don't guess. Don't keep rolling. Wait until you see them again.\n• Use the horn — one tap before motion, two taps for reverse. Wakes up anyone in the area before the wheels move.\n• The last 10 feet is when you slow DOWN, not speed up to finish. That's where the strike happens.\n• Spotters: stay outside the swing radius and the run-over path. Never stand directly behind the wheels. Stay where the driver can SEE you in the mirror.",
    references_cited:
      "OSHA 1926.601 · OSHA 1926.602 · FMCSA Backing SOP · MASCI Spotter Field Card",
    action_items:
      "G-O-A-L habit discussed · Spotter hand signals reviewed · Lost-sight-of-spotter rule reinforced · Last-10-feet slow-down reinforced",
  },
  {
    key: "trucking_shoulder_pulloff_struck_by",
    title: "Roadway Pull-Offs and Shoulder Positioning",
    category: "Hazard-Specific",
    domain: "trucking",
    role_context: ["driver", "lead"],
    incident_pattern:
      "Most struck-by-vehicle fatalities of professional drivers don't happen in transit — they happen after the truck is already stopped on the shoulder. The driver pulls off for a tire check, a load adjustment, a phone call, or a mechanical problem. They step out, walk around the cab, and are hit by a passing motorist who drifted onto the shoulder. The combination of a lit shoulder, a phone-distracted public driver, and a truck driver in a dark uniform makes this pattern terrible and predictable. It happens at night more than day, and on rural two-lanes more than interstates.",
    hazards_reviewed:
      "Struck by passing motorist on shoulder · Cab-side door opens into live traffic · Tire blowout debris from passing vehicle · Trapped between truck and barrier · Fall from cab onto loose shoulder",
    discussion_notes:
      "• Pull off as far right as the shoulder allows. If the shoulder is narrow, find the next exit, mile marker pullout, or wide spot — don't stop on a 6-foot shoulder if you can avoid it.\n• Hazards on the moment you stop. Triangles or flares deployed per FMCSA (10 ft behind · 100 ft behind · 100 ft ahead within 10 minutes). On a divided road, all three behind.\n• Exit on the PASSENGER side whenever possible. Never step out of the cab into a live traffic lane.\n• Reflective vest on BEFORE you open the door — Type II Class 2 minimum, Type III Class 3 at night. Vest in the cab, not under the seat.\n• At night: cab dome light on, four-way flashers on, headlights set so you don't blind oncoming traffic. Don't stand between your truck and oncoming headlights — drivers literally cannot see you in that silhouette.\n• Phone call, paperwork, GPS, food — none of those is worth doing on the shoulder. Take the next exit.\n• If a tire blew and you have to be near the rim — stand on the BARRIER side of the truck, never the traffic side. A second blow-out throws debris a long way.",
    references_cited:
      "FMCSA 49 CFR 392.22 (warning devices) · FMCSA 392.71 · OSHA 1926.201 · ANSI/ISEA 107 (PPE)",
    action_items:
      "Shoulder-positioning preference reinforced · Triangle / flare placement reviewed · Passenger-side exit habit discussed · Reflective vest at-the-door rule reinforced",
  },
  {
    key: "trucking_tarp_load_securement",
    title: "Tarp and Load Securement on the Road",
    category: "Hazard-Specific",
    domain: "trucking",
    role_context: ["driver", "lead"],
    incident_pattern:
      "Lost-load and lost-tarp incidents follow a tight pattern: the driver does a careful load check at the yard, then runs the first 5–10 miles on a slow road. Once they hit the highway and the wind load comes up, anything that wasn't tied tight enough starts to walk. A loose tarp lifts, slips a strap, and either becomes a parachute on the next vehicle behind or releases material across two lanes. Aggregate, asphalt millings, demo debris — once a chunk hits a car at 70 mph it's a lawsuit at best and a fatality at worst. Most of these failures are traceable to a single skipped strap or a tarp clip that was already cracked.",
    hazards_reviewed:
      "Material released into live traffic · Tarp ripped off — windshield strike on following vehicle · Load shift causing rollover or off-tracking · Strap failure from chafing or pre-existing damage · Backhaul material left in bed releasing on bumps",
    discussion_notes:
      "• Pre-trip the load AND the tarp. Walk all four sides. Look at every strap, every binder, every clip. Replace anything cracked, frayed, or worn — do not wait for it to fail on the road.\n• Tarp coverage is required for any haul that can lose material — aggregate, millings, dirt, sand, demo. 'Empty' beds still hold dust and small debris that flies out at speed.\n• Strap pattern: per FMCSA, at least one tie-down for the first 5 ft of cargo length and one more every 10 ft after. Heavy / awkward loads need more, not less.\n• Re-check at the first stop. The first 5–10 highway miles are where everything settles. Pull off (legally), walk it, retighten anything that loosened.\n• Tarp clips and corner ties — these are the most common failure point. Inspect them like they matter. They do.\n• If you lose a tarp at speed: pull off safely, hazards on, do NOT chase the tarp on foot into traffic. Call dispatch. Call the highway patrol. Get back-up before retrieving.\n• Backhaul tip: a 'clean' truck is not clean. Sweep the bed and check the corners before you leave the dump pile. A handful of millings at 70 mph is a windshield strike.",
    references_cited:
      "FMCSA 49 CFR 393 Subpart I (cargo securement) · FMCSA Driver Handbook · NACS Tarp Inspection · MASCI Tarp SOP",
    action_items:
      "Tarp and strap pre-trip discussed · First-stop re-check habit reinforced · Backhaul sweep reinforced · Tarp-clip replacement threshold reviewed",
  },
  {
    key: "trucking_kingpin_coupling_failure",
    title: "Trailer Kingpin and Coupling Failures",
    category: "Hazard-Specific",
    domain: "trucking",
    role_context: ["driver", "lead", "shop"],
    incident_pattern:
      "Trailer drops follow a recognizable sequence: the driver couples in a hurry — visual check only, no tug-test, jaws look closed, safety pin gets eyeballed. The first 100 feet of motion goes fine because the trailer is sitting on the fifth wheel by gravity. Then a slight grade, a bump, a turn, and the kingpin slides forward out of unsealed jaws. The trailer drops onto the deck plate or onto the pavement. If anyone is between the cab and the trailer at that moment — a yard worker, another driver doing a walk-around, a mechanic — the result is catastrophic. The pattern is older than most drivers in the seat, and it still kills people every year.",
    hazards_reviewed:
      "Trailer drop / unintended decoupling · Crush between dropped trailer and cab · Landing-gear collapse with shifting load · Wrong-pin engagement / false-lock · Glad-hand and electrical disconnect during run",
    discussion_notes:
      "• Coupling check is THREE checks, not one: visual (jaws closed around the kingpin) · safety latch / locking-pin engaged · TUG-TEST in low gear against trailer brakes.\n• Tug-test means: trailer brakes set, low gear, gently pull forward. The pin grabs the jaws. NO motion = good. ANY motion = recouple immediately.\n• Visual inspection: get UNDER the fifth wheel with a flashlight. You want to SEE the jaws closed around the kingpin, not just the lock handle 'in.' Locking handles can be 'in' on a false-lock.\n• Landing gear up all the way and crank handle stowed. A landing leg riding even slightly down can catch on rough pavement and shear off.\n• Glad hands seated · safety chains or rigging where required · electrical pigtail latched. These are walk-around items, not 'I'll check after lunch' items.\n• Never stand between the cab and the trailer during coupling/uncoupling. Communicate with anyone in the area — make sure they're clear. Yard fatalities almost always involve a person in this space.\n• If you feel anything weird on the road — vibration, a clunk, a sudden movement — pull off NOW. Don't run another five miles to the next exit. Drops have happened on the highway.",
    references_cited:
      "FMCSA 49 CFR 393.70 (coupling devices) · CVSA Out-Of-Service Criteria · OEM fifth-wheel manual · MASCI Coupling Card",
    action_items:
      "Three-step coupling check reinforced · Tug-test method reviewed · Under-the-trailer visual habit reinforced · Stay-out-of-the-pinch-zone rule discussed",
  },
  {
    key: "trucking_overweight_axle_law",
    title: "Overweight, Axle Loading and Bridge Law",
    category: "Procedure / SOP",
    domain: "trucking",
    role_context: ["driver", "lead", "dispatch"],
    incident_pattern:
      "Overweight tickets and axle violations almost never come from a driver who DECIDED to run heavy. They come from a driver who got loaded by a plant operator, didn't check the ticket, didn't scale on the way out, and rolled past a portable weigh team. The pattern repeats most often in two scenarios: hot-mix asphalt out of a busy plant where loader operators are running long days and over-pouring 'just a little,' and aggregate hauls where the customer is paying by the ton and the supplier loads to the rim. The driver eats the ticket, the company eats the points on its DOT score, and a state-level Bridge Law violation can shut a job down.",
    hazards_reviewed:
      "Brake fade / brake fire on grades from overload · Tire blowout from over-axle loading · Bridge / culvert structural damage · DOT points on operating authority · License-affecting citations · Steering loss from front-axle overload",
    discussion_notes:
      "• Know your truck's tare, your axle ratings, and your gross. Have them written down in the cab — not in your head, not 'about,' but exact.\n• Check the ticket at the plant BEFORE you leave the scale. If the numbers don't add up or the truck feels heavy on the suspension, ask the loader to take a scoop off.\n• Federal bridge law is not just gross weight — it's how the weight is distributed. A legal-gross truck can still be illegal on a tandem or on the steer axle. Spread loads, slide the fifth wheel, slide the trailer axle.\n• If you go through a CAT scale or a state portable on the route, USE IT. Better to know you're 800 lb over and slide the axle than to find out at the chicken coop.\n• Overload on the steer axle is the most dangerous — that's where steering authority lives. An overloaded steer in a corner can wash out and become a rollover.\n• Hot mix out of a plant: the temperature affects the way the load settles. A perfect scale at the plant can shift on the road. Drive accordingly — softer braking, longer following distance.\n• Dispatch tip: if a customer is consistently asking for over-axle hauls, document it and escalate. Don't let it become 'the way we run that customer.'",
    references_cited:
      "FMCSA 49 CFR 393 · Federal Bridge Formula (23 USC 127) · State DOT axle tables · MASCI Plant Loading SOP",
    action_items:
      "Tare / rating / gross verified in cab · Scale-on-the-way-out habit reinforced · Steer-axle awareness discussed · Overload escalation path discussed",
  },
  {
    key: "trucking_blind_spots_pedestrian",
    title: "Blind Spots and Pedestrian Workers Around Trucks",
    category: "Hazard-Specific",
    domain: "trucking",
    role_context: ["driver", "lead", "spotter", "office"],
    incident_pattern:
      "Pedestrian-strike fatalities on heavy civil sites almost always happen in a specific zone — the front quarter on the passenger side, or the immediate area in front of the cab — and they almost always happen during the first 2 seconds of vehicle motion. A laborer is checking a tire, picking up a tool, signaling another piece of equipment, or simply standing in the wrong place. The driver checks mirrors, sees nothing, and engages. The truck rolls forward 5 to 10 feet before the driver sees a hi-vis vest hit the ground. The fix is not better mirrors — it's a hard pre-motion habit and a job-site culture where ground workers know not to stand in those zones.",
    hazards_reviewed:
      "Pedestrian struck-by / run-over from cab blind spot · Right-side mirror gap on wide cab trucks · Pedestrian behind truck during reverse · Worker in pinch zone during turn · New-driver unfamiliarity with mirror coverage",
    discussion_notes:
      "• Before any motion — driver does a 360 walk-around or a full mirror + over-the-shoulder sweep. Eye contact with anyone visible.\n• Use the horn. One tap before forward motion, two taps for reverse. If someone is close, roll the window down and call out before moving.\n• The blind spots: directly in front of the bumper (the 'kill zone'), the front-right quarter, the area immediately behind the trailer, and the right-side turn pinch zone. Ground workers should NEVER stand in those.\n• Hi-vis vest is a tool, not a permission slip. A vest does not let you stand in a blind spot.\n• On a busy site — plant yards, paving trains, dump piles — make eye contact with the driver before you walk near the truck. If you don't get acknowledgment, don't move into the zone.\n• New drivers: take 15 minutes with each truck and KNOW where every mirror covers and where it doesn't. Right-side mirrors on day cabs vs sleepers vs cabovers all differ — do not assume.\n• Site supervisors and office personnel visiting the field: same rule applies. Stay out of cab blind spots, especially around running equipment.\n• If you're the spotter or ground worker, position yourself where the DRIVER can see YOU in the mirror — not where you can see the truck. They are different things.",
    references_cited:
      "OSHA 1926.601 · OSHA 1926.602 · NIOSH Internal Traffic Control · MASCI Site Pedestrian SOP",
    action_items:
      "Pre-motion walk-around habit reinforced · Kill-zone awareness for ground crew reviewed · New-driver mirror-coverage check assigned · Office-visitor blind-spot rule discussed",
  },

  // ============================================================
  // DEWATERING / WELLPOINT · PHASE D · iter251
  // ------------------------------------------------------------
  // Catastrophic-risk operational lessons for dewatering crews.
  // Voice: experienced superintendent. Drivers, jet-rig operators,
  // ground crew, foremen. Real incidents, not LMS theory.
  // ============================================================
  {
    key: "dewatering_jetting_rig_overhead_strike",
    title: "Jetting Rig Overhead Powerline Strikes",
    category: "Hazard-Specific",
    domain: "dewatering",
    role_context: ["operator", "lead", "spotter"],
    incident_pattern:
      "Jetting-rig powerline contacts almost never happen during steady jetting — they happen during repositioning. The rig is set, the operator finishes a header, and now needs to move to the next stab. They retract a little, swing the boom, and the boom mast — usually fully extended from the last header — sweeps into the overhead line. The driver is focused on the ground crew and the next stab, not on what's 30 feet above. Around utility yards, behind grocery stores, on the back side of pump stations — overhead lines are everywhere and the masts on jet rigs are tall enough to find them.",
    hazards_reviewed:
      "Electrocution of operator or ground crew · Mast contact with energized line during reposition · Step potential around energized rig · Outage / fire from utility damage · Burns from arc flash",
    discussion_notes:
      "• Before the rig comes off the trailer — walk the site. Look up. Identify EVERY overhead line within 50 feet of any place the mast will travel.\n• 20-foot minimum clearance from energized lines under OSHA 1926.1408. If the line is below 50 kV. Bigger voltage = bigger clearance.\n• Lower the mast BEFORE you reposition. Every time. The 30 seconds it costs you is the cheapest insurance you'll buy.\n• Designate a spotter whose ONLY job is watching the mast and the lines during any reposition. Not multitasking. Not also signaling ground crew. Just the mast and the lines.\n• If you don't know whether a line is energized, treat it as live. Call the utility. Get a confirmed de-energize and ground BEFORE you work close to it.\n• Contact happens: STAY ON THE RIG. Keep ground crew back at least one rig-length plus the line. Call 911 and the utility. Step-potential has killed more people than the initial contact.\n• If you HAVE to exit: bunny-hop with feet together. Never have two body parts on the ground at the same time until 30 feet clear.",
    references_cited:
      "OSHA 29 CFR 1926.1408 · OSHA 1926.416 · NESC clearances · MASCI Jet Rig Setup SOP",
    action_items:
      "Overhead walk-around done · Mast-down-before-reposition habit reinforced · Designated mast-spotter assigned · Contact-response procedure reviewed",
  },
  {
    key: "dewatering_suction_line_entrapment",
    title: "Suction-Line Entrapment and Engulfment",
    category: "Hazard-Specific",
    domain: "dewatering",
    role_context: ["operator", "lead"],
    incident_pattern:
      "Suction-line engulfment is one of the least talked-about fatalities in dewatering, and one of the most preventable. A wellpoint header gets clogged, the operator pulls a stinger to check the screen, and water rushes through the open line. Anyone within a few feet — boots in the trench bottom, hand reaching for the screen, kneeling beside the line — can be pulled into the suction by hydraulic action. Even a 6-inch suction at full vacuum will hold a hand or a boot to the inlet hard enough that the worker cannot self-release. Several documented fatalities in our region trace back to a single 'just gonna check the screen' action.",
    hazards_reviewed:
      "Hand or limb pulled into suction inlet · Engulfment in collapsing wellpoint trench · Drowning in unscreened sump · Hose-whip injury · Pinch / amputation at strainer",
    discussion_notes:
      "• Vacuum off BEFORE anyone touches a suction line, header, stinger, screen, or strainer. Period. No exceptions. No 'I'll be quick about it.'\n• Lockout the pump at the controls AND verify zero pressure at the gauge before anyone gets near the inlet.\n• If you must work near a flowing line, use a long-handled tool. Never put a hand or arm in the suction zone.\n• Strainer screens prevent entrapment AND prevent screen failures — inspect them daily, replace any cracked or worn one.\n• Wellpoint trenches should be properly shored or sloped. Engulfment risk is real if the trench wall fails while someone is at the bottom servicing a header.\n• Sump pits with open suction inlets need barriers or grates. A kid, a worker, a dog — anything that falls in is in trouble immediately.\n• Train new crew on suction physics — explain why a 6-inch hose at 25 inches Hg will not let go of a hand. Make it real, not theoretical.",
    references_cited:
      "OSHA 29 CFR 1926 Subpart P · OSHA 1910.147 (LOTO) · Manufacturer pump operation manual · MASCI Dewatering SOP",
    action_items:
      "Vacuum-off-before-touch rule reinforced · Lockout at pump controls verified · Strainer inspection assigned · New-crew suction physics briefing scheduled",
  },
  {
    key: "dewatering_diesel_pump_fueling_fires",
    title: "Diesel Pump Fueling Fires",
    category: "Hazard-Specific",
    domain: "dewatering",
    role_context: ["operator", "lead", "driver"],
    incident_pattern:
      "Diesel pump fires almost never happen at the fuel station — they happen on-site during refueling of running or recently-shut-down equipment. The pump has been running 12 hours, the muffler and turbo are at 800–1000°F, the operator is rushing to fuel up before the next storm, and a fuel splash hits hot metal. The fire is instant and immediately threatens the operator standing 18 inches from the fill spout. Most of these fires turn into burn injuries, not fatalities — but they ruin a worker's life and shut a job down. The pattern is preventable with one simple discipline: cool-down time and clean fueling.",
    hazards_reviewed:
      "Fuel splash onto hot exhaust / turbo · Static discharge ignition during transfer · Spill creating slip + fire hazard · Burn injury to fueler · Equipment loss · Environmental release",
    discussion_notes:
      "• Shut the pump OFF before fueling. Allow 5–10 minutes of cooldown if the engine has been running hard. The exhaust manifold and turbo stay hot long after shutdown.\n• No smoking · no cell-phone calls · no open flames within 25 feet of fueling. This is not optional.\n• Maintain bond between the fuel container or hose and the pump frame during transfer. Static is a real ignition source.\n• Don't top off. The expansion when fuel warms can push fuel out the vent and onto the engine.\n• Fuel transfer at night with a flashlight — not with a hot work-light propped on the pump. Lights run hot.\n• Spill kit on every dewatering site. Absorbent pads, sock, drain mat. Drain mat goes UNDER the fill point every time.\n• If a fire starts: ABC extinguisher within reach (within 10 ft of fueling point). Pull the operator clear FIRST. Then fight the fire. Never fight a fire alone.",
    references_cited:
      "NFPA 30 · OSHA 1926.152 · EPA SPCC · DOT 49 CFR 173 · MASCI Fueling SOP",
    action_items:
      "Cooldown-before-fueling habit discussed · Extinguisher within 10 ft verified · Spill kit + drain mat at every pump · Bonding-during-transfer reviewed",
  },
  {
    key: "dewatering_wellpoint_trench_collapse",
    title: "Wellpoint Trench Collapse Around Headers",
    category: "Hazard-Specific",
    domain: "dewatering",
    role_context: ["operator", "lead", "ground_crew"],
    incident_pattern:
      "Wellpoint trench collapses follow a tight pattern: the trench is dug to a moderate depth (4–8 ft), the header laid, the wellpoints jetted. Three days into pumping, the soil between points has been pulled tighter and the trench walls look stable. A worker steps down into the trench to service a clogged point or repair a leak. The dewatering has actually changed the soil structure — saturated material above an now-dry section creates a sliding plane. The wall fails inward with no warning. The worker, even if they live, is buried to the chest in seconds. Once-stable trenches are not stable forever when water content changes.",
    hazards_reviewed:
      "Burial / suffocation from collapsed trench wall · Crush injury from wall failure · Drowning in trench bottom from sudden inrush · Struck-by from falling header / equipment · Hypothermia in long-duration burial",
    discussion_notes:
      "• Trench protection at 5 ft+ is not optional — slope, bench, shore, or trench box. Dewatering does NOT replace shoring.\n• Trenches over 4 ft need a ladder or ramp within 25 ft of any worker.\n• Reclassify the soil after dewatering has been running. Saturated-to-dry transitions create unstable layers. Talk to your competent person.\n• Spoil pile at least 2 ft from the edge. Equipment paths at least one trench-depth back. Vibration from running pumps loosens edge material over hours.\n• Service a wellpoint from ABOVE the trench whenever possible. The risk of being in the trench to fix a point is not worth the time saved.\n• Never work alone in a wellpoint trench. The first 60 seconds after a collapse is when survival happens — only if someone topside sees it.\n• Daily inspection by a competent person — and after any rain, freeze-thaw, or vibration event.",
    references_cited:
      "OSHA 29 CFR 1926 Subpart P · OSHA 1926.651 · OSHA 1926.652 · MASCI Dewatering Trench SOP",
    action_items:
      "Trench protection reviewed for current depth · Soil reclassification done after pumping start · Above-trench service habit reinforced · Daily competent-person inspection assigned",
  },
  {
    key: "dewatering_rotating_shaft_belt",
    title: "Rotating Shaft and Belt Entanglement",
    category: "Hazard-Specific",
    domain: "dewatering",
    role_context: ["operator", "lead", "mechanic"],
    incident_pattern:
      "Belt and shaft entanglement injuries on dewatering pumps usually happen when a guard is off for a service task and the engine gets bumped or restarted by someone who didn't know a crew member was working on it. A glove, a sleeve, a shirt tail, a hood drawstring catches a v-belt or a coupling. The pump engine is making 1800 RPM at the coupling — the entire arm is in before the worker can react. Hoodies, loose sleeves, and unbuttoned cuffs are the leading factor in nearly every documented incident. The second factor is missing LOTO when a guard is off.",
    hazards_reviewed:
      "Arm / hand pulled into v-belt or coupling · Crush / amputation from rotating shaft · Death from clothing caught in PTO · Burn from belt friction · Eye injury from belt failure",
    discussion_notes:
      "• Guards in place ANY time the engine is running. No exceptions. If the guard is broken, the pump doesn't run until it's fixed.\n• Lockout the engine at the kill switch AND remove the key before any guard comes off. Verify with a start-attempt before reaching in.\n• Sleeves buttoned · shirts tucked · NO hoodie drawstrings · NO loose jewelry near rotating equipment.\n• Snug gloves only — and consider gloves OFF when working close to rotating shafts. Loose glove fingers grab v-belts.\n• Train new operators to identify EVERY pinch point on the pump before they ever touch it running. Walk it down. Point at each one.\n• Belt service is engine-OFF service. Tensioning, alignment, replacement — all engine-off, with the key in your pocket.\n• If a guard is off for inspection — assign one person as the lock holder. Their key stays in their pocket. No one else can start.",
    references_cited:
      "OSHA 29 CFR 1910.147 (LOTO) · OSHA 1910.219 · ANSI B11 · Manufacturer pump operation manual",
    action_items:
      "Guards-in-place rule reinforced · LOTO before guard removal verified · Clothing standards (no drawstrings) discussed · New-operator pinch-point walk-down assigned",
  },
  {
    key: "dewatering_discharge_hose_whip",
    title: "Discharge Hose Whip and Pressure Release",
    category: "Hazard-Specific",
    domain: "dewatering",
    role_context: ["operator", "lead", "ground_crew"],
    incident_pattern:
      "Discharge-hose whip incidents happen because a hose connection fails or a section breaks free under pressure. A 6 or 8-inch discharge hose at 60–80 psi carries enormous stored energy. When a coupling lets go, the hose end becomes a whip — moving fast enough to break bones, throw workers, or knock someone off a trench bank. The pattern is usually a worn cam-lock or quick-connect coupling, a missing safety pin or clip, or a hose that wasn't restrained where it should have been. The whip travels along the path of least resistance — usually toward whoever is nearest.",
    hazards_reviewed:
      "Hose-whip strike to head / chest · Pressure release knocking worker into trench · Slip injury from sudden water release · Coupling failure projectile · Burns from heated discharge (hot oil pumps)",
    discussion_notes:
      "• Inspect every cam-lock and coupling on every shift. Look for worn cams, missing safety clips, deformed gaskets. Replace anything questionable.\n• Safety pins / clips on every coupling. They are not optional. They are what keeps the hose connected when a cam fatigues.\n• Restrain discharge hoses where they change direction, where they cross a path, where they go over a bank. Use rope ties, sandbags, or proper restraints — not stacked rocks.\n• When pressurizing a line, no one stands in line with the hose. Everyone steps off-axis BEFORE the pump starts.\n• If a hose lets go: KILL THE PUMP from the control side first. Don't try to grab the hose. Hose ends weigh enough to break a hand at 60 psi.\n• Whip-checks (woven safety cables) on every coupling on long discharge runs. Standard equipment, not optional.\n• Daily walk of the entire discharge run — look for stress points, kinks, abrasion, exposed restraint, leaks. Catch the failure BEFORE the whip.",
    references_cited:
      "OSHA 29 CFR 1926.302 · ASME B31.3 · Manufacturer hose / coupling ratings · MASCI Discharge SOP",
    action_items:
      "Coupling inspection assigned to each shift · Safety pins verified on all couplings · Whip-checks deployed on long runs · Pump-off-before-touch reinforced",
  },
  {
    key: "dewatering_spoil_edge_instability",
    title: "Spoil Placement Around Wellpoint Trench Edges",
    category: "Hazard-Specific",
    domain: "dewatering",
    role_context: ["operator", "lead", "equipment_operator"],
    incident_pattern:
      "Most wellpoint trench-edge failures don't start with the trench wall — they start with the spoil pile. Spoil placed too close to the edge adds surcharge load. Equipment running parallel to the trench transmits vibration through the spoil into the wall. Three days of pumping plus the static load of a 4-foot spoil pile plus the dynamic load of a passing excavator equals a wall section that slides into the trench with no warning. The crew member servicing a header at the bottom never sees it coming. The fix is unglamorous and known: keep spoil back, keep equipment back, and inspect daily.",
    hazards_reviewed:
      "Trench collapse from spoil surcharge · Engulfment of worker in trench bottom · Equipment slide into trench · Struck-by from spoil avalanche · Hose / header damage from collapsed wall",
    discussion_notes:
      "• Spoil pile minimum 2 feet from trench edge. For deeper trenches, push it farther — 1 trench-depth back is the safer benchmark.\n• No equipment paths within one trench-depth of the edge. Excavators, loaders, dump trucks — all back from the lip.\n• Use plywood or steel road plates if you must cross or work near the edge. Distributes load and reduces local stress.\n• Equipment running parallel to a wellpoint trench transmits vibration. Vibration loosens edge soil. Move the equipment path or stop running it for the duration.\n• Compounding effect: pumping pulls water from the trench wall. Loss of pore pressure makes wet soil settle and dry soil crack. The wall you set yesterday is not the wall you have today.\n• Daily competent-person inspection of the spoil and edge, not just the trench bottom. The edge tells you the future.\n• If you see ANY tension crack, fissure, or slumping at the edge — pull workers OUT immediately. Re-inspect before letting anyone back in.",
    references_cited:
      "OSHA 29 CFR 1926.651(j) · OSHA 1926.652 Appendix B · MASCI Trench Edge SOP",
    action_items:
      "Spoil setback verified · Equipment path moved back · Daily edge inspection assigned · Tension-crack response reviewed",
  },
  {
    key: "dewatering_night_work_struck_by",
    title: "Nighttime Dewatering Visibility and Struck-By",
    category: "Hazard-Specific",
    domain: "dewatering",
    role_context: ["operator", "lead", "ground_crew", "driver"],
    incident_pattern:
      "Nighttime dewatering work is more dangerous than day work for one specific reason: visibility cones. Operators see the area lit by their work-lights and assume everyone else does too. The truck driver pulling onto the site sees a halo of glare and a black field beyond. The ground worker servicing a header in the unlit zone is invisible. Most nighttime struck-by incidents on dewatering jobs happen when a delivery truck, a transfer rig, or a customer vehicle enters a lit work zone and the driver does not see a worker outside the lit cone. The pattern repeats because lighting is set up for the WORK, not for the visibility of the workers.",
    hazards_reviewed:
      "Struck-by from vehicle entering site at night · Worker in unlit zone invisible to driver · Trip / fall in unlit area · Equipment contact with poorly-lit obstructions · Fatigue + reduced reaction time",
    discussion_notes:
      "• Light the work AND the worker paths. A single tower light on the pump is not enough. Light the routes between the trailer, the pumps, and the trench.\n• Hi-vis reflective Class 3 at night — not Class 2. Sleeves, vest, pants. The reflective tape is what makes you visible in a headlight beam.\n• Every worker has a personal light — headlamp or chest light — that turns toward incoming vehicles. Driver's eye-tracking goes to motion of light. Use that.\n• Designated entry / exit lane for vehicles. Marked with cones or barricades. No driver freelances through a dewatering work area at night.\n• Driver of any incoming vehicle: stop at the site edge. Make radio or eye contact with the lead before entering. NEVER assume the area is clear.\n• Fatigue is real. Night shifts after long days produce reaction times like blood alcohol over the legal limit. Watch each other. Force breaks. Send people home.\n• Severe weather at night — call it earlier than you would in daylight. You cannot see what's coming.",
    references_cited:
      "OSHA 29 CFR 1926.56 · ANSI/ISEA 107 (Class 3) · MUTCD nighttime work zones · MASCI Night Work SOP",
    action_items:
      "Worker-path lighting reviewed · Class 3 hi-vis required for night shift · Personal lights distributed · Entry lane defined and marked · Fatigue check-in time set",
  },

  // ============================================================
  // SHOP / MECHANIC · PHASE E · iter251
  // ------------------------------------------------------------
  // Shop-floor incident patterns. Voice: long-tenured wrench
  // talking to younger mechanics. Real injuries. No LMS gloss.
  // ============================================================
  {
    key: "shop_jack_stand_failure",
    title: "Jack-Stand Failures — Under-the-Truck Fatalities",
    category: "Hazard-Specific",
    domain: "shop",
    role_context: ["mechanic", "lead"],
    incident_pattern:
      "Almost every jack-stand fatality follows the same sequence: a mechanic raises a heavy truck or trailer on the floor jack, sets two stands, slides under to start work, and the truck shifts. Sometimes it's because the stands were placed on a rusted frame member, sometimes because the ground sloped just enough, sometimes because they were undersized for the load. The truck doesn't fall all the way — it just settles 2 inches. That's enough to crush a chest. There is no warning. The mechanic is alone, often at end-of-shift, and no one finds them for an hour. We have lost mechanics in this industry to this exact pattern more times than anyone wants to count.",
    hazards_reviewed:
      "Crush fatality from vehicle drop · Stand sinking into soft floor · Wrong stand rating for load · Single stand instead of pair · Working alone under load · Hydraulic jack creep / failure",
    discussion_notes:
      "• Floor jack is for LIFTING, never for HOLDING. The moment the load is at height, jack stands rated to the load go under PROPER lift points.\n• Stands rated to AT LEAST the load weight, with margin. A 40,000-lb truck doesn't go on 6-ton stands. Read the rating, do the math.\n• Both stands engaged — not just one with the jack still under as the second hold. A bumped jack handle drops the truck.\n• Wheels chocked on the OPPOSITE end. Trans in gear or park. Parking brake ON. Belt-and-suspenders.\n• Place stands on the FRAME, not on plastic skirts, not on body panels, not on rusted-through structure. Tap and look before you set.\n• Concrete floor only. Asphalt soft-spots can fail under a single stand. If you have to work on asphalt, use a steel plate to spread the load.\n• Tug-test BEFORE you slide under. Lean on the truck, shake it. If anything moves more than the rocking of suspension, redo the lift.\n• Don't work alone under a vehicle. If you must, set a check-in time with someone who will look for you if you don't text back.",
    references_cited:
      "OSHA 29 CFR 1910.244 · ANSI/PASE 5/MH29 (jack stands) · OEM lift-point manuals · MASCI Shop Lift SOP",
    action_items:
      "Lift-point map for common units posted · Stand rating check assigned · Tug-test habit reinforced · Solo-under-vehicle check-in protocol set",
  },
  {
    key: "shop_lockout_tagout_bypass",
    title: "Lockout / Tagout — The Bypass That Kills",
    category: "Procedure / SOP",
    domain: "shop",
    role_context: ["mechanic", "lead", "operator"],
    incident_pattern:
      "LOTO failures don't kill the worker who set the lockout — they kill the worker who DIDN'T. The pattern: a piece of equipment is in the shop for hydraulic service. The lead mechanic locks it out properly. A second mechanic, helping out, doesn't have a personal lock on it. A third mechanic, finishing his shift, sees the equipment and decides to 'just bump' the controls to check something. The second mechanic, hand inside the cylinder area, gets crushed. The first mechanic's lock was correct. The system failed because not every person under the equipment had their own lock on it.",
    hazards_reviewed:
      "Stored hydraulic energy release · Crush from cylinder collapse · Electrical re-energization during service · Belt restart during alignment · Pneumatic release of stored air · Counterweight drop",
    discussion_notes:
      "• One worker, one lock. EVERY person who has any part of their body in or near the danger zone hangs THEIR OWN lock. No 'I'll share a lock' shortcuts.\n• Tag the lock with who set it and when. So the third mechanic walking up knows whose lockout this is and doesn't undo it.\n• Verify zero energy: cycle the controls, check the gauges, drop hydraulic pressure to zero, drain stored air. EVERY service.\n• Block hydraulic cylinders mechanically. A cylinder support, a wood block, a chain — something that holds the load if the seal fails.\n• Don't trust 'the boss said it's locked.' Verify with your own eyes. Put your own lock on it. Try to start it.\n• Removing a lockout: ONLY the worker who set it. If they're not on-site, follow the lock-removal procedure — usually requires supervisor authorization and a documented attempt to reach the original locker.\n• New mechanics: walk a LOTO procedure with the lead on Day 1. Every. Single. Time.",
    references_cited:
      "OSHA 29 CFR 1910.147 · OEM service manuals · MASCI Shop LOTO Standard",
    action_items:
      "One-worker-one-lock rule reinforced · Lock tagging discussed · Zero-energy verification reviewed · Cylinder blocking practice assigned · New-mechanic LOTO walkthrough scheduled",
  },
  {
    key: "shop_brake_spring_energy",
    title: "Brake Spring Stored Energy Release",
    category: "Hazard-Specific",
    domain: "shop",
    role_context: ["mechanic", "lead"],
    incident_pattern:
      "Brake chamber spring releases have killed and blinded mechanics for decades, and they keep doing it. The pattern is always the same: a mechanic is replacing a brake chamber or working a slack adjuster on a unit with no caged spring. They strike a stuck pin with a hammer, or unbolt a chamber that's still holding its spring force, and the chamber comes apart with the energy of a small explosion. The internal spring is rated to 2,000 lb of force. When that releases six inches from a face, it's a fatal facial impact. Caging the spring is not optional and never has been.",
    hazards_reviewed:
      "Spring brake chamber release projectile · Facial / chest trauma from chamber component · Eye loss from spring shrapnel · Hearing damage from release · Pinch injury during caging",
    discussion_notes:
      "• ALWAYS cage the spring before touching a brake chamber service bolt, slack adjuster, or pushrod. Caging tools are cheap. New mechanics cost more.\n• Use the chamber's caging port — slide the caging tool in, turn it 90°, pull tight. Verify the cage is engaged before removing any service bolt.\n• Stand to the SIDE during release verification. Not in front, not behind — to the side. The release path is straight out.\n• Eye protection is non-negotiable. Not safety glasses — a full face shield over safety glasses for brake work.\n• If you can't cage it because the port is rusted shut, treat the unit as out-of-service for shop work. Cut the chamber off as a unit and replace it with the spring still caged in the OLD chamber.\n• Pop-off plugs on the chamber pushrod end — never tamper with them. They are PRESSURE-rated, not service-rated.\n• Train every new shop hand on cage installation in the first week. Make them do it with a chamber in their hands.",
    references_cited:
      "FMCSA Brake Service · OEM brake chamber manuals · OSHA 1910.132 (PPE) · MASCI Brake Shop SOP",
    action_items:
      "Spring caging tool inventory verified · Caging-before-service habit reinforced · Face-shield requirement reviewed · New-hand training scheduled",
  },
  {
    key: "shop_tire_cage_explosion",
    title: "Tire Cage Explosions and Multi-Piece Rims",
    category: "Hazard-Specific",
    domain: "shop",
    role_context: ["mechanic", "tire_tech", "lead"],
    incident_pattern:
      "Tire-cage incidents are not what people think. The famous old fatalities — multi-piece rims separating during inflation — are still happening because some equipment still runs on those rims. A loader rim, a road-grader rim, an older over-the-road rim. The mechanic deflates, dismounts, reassembles, inflates without a cage, and the lock ring separates at 80 psi. The energy is equivalent to a small explosive charge. There is video. We have all seen it. The fix is older than most of the people working in shops today — and people are still dying because the cage was 'just for a second' set aside.",
    hazards_reviewed:
      "Lock-ring separation projectile during inflation · Mechanic in line of fire · Multi-piece rim corrosion failure · Single-piece rim cracking · Inflation hose recoil · Tire bead explosion",
    discussion_notes:
      "• Tire cage for EVERY inflation, every time. Single-piece rims included — bead failures happen on those too.\n• Stand to the SIDE during inflation. Never in front of the rim. Long inflation hose with in-line gauge so you stand outside the trajectory.\n• Inspect rims BEFORE you mount. Lock rings, side rings, gutters — look for cracks, corrosion, deformation. If the ring doesn't seat clean, the rim doesn't go back in service.\n• Multi-piece rims need to match. Mixing manufacturers or sizes is what causes most separations. If you're not sure it matches, scrap it.\n• Inflate in stages. Bead seat at lower pressure, verify seating, then take it up to running pressure.\n• Bead lubricant — water and soap only. NEVER use solvent-based lubricants. They can ignite under high heat.\n• Old hands sometimes skip the cage because they 'know' the rim. The rim does not know them. Use the cage.",
    references_cited:
      "OSHA 29 CFR 1910.177 · OEM rim service manuals · TIA tire service standards · MASCI Tire Shop SOP",
    action_items:
      "Cage-every-inflation rule reinforced · Rim inspection step verified · Bead lubricant policy reviewed · Multi-piece rim policy discussed",
  },
  {
    key: "shop_welding_fire_watch",
    title: "Welding Fire Watch and Hot-Work Cleanup",
    category: "Hazard-Specific",
    domain: "shop",
    role_context: ["welder", "fire_watch", "lead"],
    incident_pattern:
      "Shop fires from welding almost never happen during the weld — they happen 20 to 60 minutes AFTER. The welder cuts a brace, grinds the bead, blows the slag away, and walks off. A spark that landed in oily rags on a shelf, behind a 55-gallon drum, or in cardboard packaging smolders. The shop is empty by then. The smoke detector kicks at 1:30 a.m. and the fire department arrives to a fully-involved building. The fix is decades-old: cleanup, fire watch, post-weld inspection. We know this. We keep losing buildings to skipped fire watches.",
    hazards_reviewed:
      "Slow-smolder fire in oily / dusty materials · Hidden fire behind / under equipment · Burn / smoke injury · Total-loss building fire · Spark ignition of flammable liquid · Vapor ignition during cutting",
    discussion_notes:
      "• Hot-work permit for every welding / cutting / grinding job. Old habit, still right. Permit names the welder, the location, the fire watch, and the end time.\n• Clear a 35-foot radius before sparks fly. Move oily rags, fuel containers, cardboard, sawdust, hydraulic fluid drums. EVERYTHING combustible.\n• Wet down what you can't move. Welding blankets over what you can. Steel shields over openings into adjacent rooms.\n• Fire watch STAYS for 30 minutes after the last spark. Phone in hand. Eyes on every place a spark could have landed.\n• Check ABOVE and BELOW grates, into floor drains, behind any equipment within the 35-ft radius. Sparks travel.\n• Charged extinguisher within arm's reach during AND after. Confirm it's not the empty one from the last drill.\n• Last welder out at end of shift: walk the whole shop. Touch surfaces, smell the air. Smoke and heat tell you what eyes don't.",
    references_cited:
      "NFPA 51B · OSHA 29 CFR 1910.252 · NFPA 241 · MASCI Hot Work Permit SOP",
    action_items:
      "Hot-work permits required + posted · 35-ft clear-zone enforced · Fire-watch duration verified · End-of-shift walk discussed",
  },
  {
    key: "shop_hydraulic_stored_energy",
    title: "Hydraulic Stored Energy in Cylinders, Hoses, and Accumulators",
    category: "Hazard-Specific",
    domain: "shop",
    role_context: ["mechanic", "lead"],
    incident_pattern:
      "Hydraulic injection injuries look minor and kill people. A pinhole in a hose at 2,500 psi sprays oil through skin like a hypodermic needle. The mechanic sees a tiny puncture in their hand, washes it, bandages it, goes home. Within 24 hours the hand is swollen, the tissue is dying from oil contamination, and the emergency room is amputating. Compounded with raw cylinder pressure release — a loose fitting backs off and the cylinder discharges across the shop — and a fitting becomes a projectile. Stored hydraulic energy is invisible. It kills mechanics who don't respect it.",
    hazards_reviewed:
      "Hydraulic injection injury through skin · Fitting / hose projectile · Cylinder uncontrolled extension at energy release · Crush from load drop when pressure bleeds · Burn from hot oil · Eye injury from sprayed oil",
    discussion_notes:
      "• Never search for a hydraulic leak with your hand. Use cardboard, paper, or a piece of wood. If you find a leak, replace the hose — don't band-aid it.\n• Drop pressure to zero BEFORE disconnecting any fitting. Cycle the controls with the engine off. Watch the gauge. Verify ZERO.\n• Hydraulic accumulators stay pressurized AFTER zero on the system gauge. Discharge them per the OEM procedure before touching any line connected to them.\n• If oil contacts skin under pressure — ER NOW. Even if it 'looks like nothing.' Tell them it was a hydraulic injection. Surgery clock starts immediately.\n• Long-handled tools when working close to a pressurized hose. Stand off-axis when cracking a fitting.\n• Hose inspections weekly. Cracks, abrasion, bulges, leaks. Replace before failure.\n• Eye protection AND face shield for any open hydraulic work. Closed system is a different rule — open system is full PPE.\n• Block cylinders mechanically before working on them. Hydraulic pressure can disappear and the load can still drop if a seal lets go.",
    references_cited:
      "OSHA 29 CFR 1910.147 · Fluid Power Society safety · OEM service manuals · MASCI Hydraulic Service SOP",
    action_items:
      "Pinhole-search-with-cardboard rule discussed · Accumulator discharge procedure reviewed · ER-immediately-for-injection policy reinforced · Cylinder blocking verified",
  },
  {
    key: "shop_under_bed_crush_zone",
    title: "Crush Zones Under Beds, Booms, and Equipment",
    category: "Hazard-Specific",
    domain: "shop",
    role_context: ["mechanic", "operator", "lead"],
    incident_pattern:
      "The body-prop pin on a dump bed exists for one reason: to keep mechanics alive when the bed comes down unexpectedly. Most under-bed fatalities happen because the prop was 'just for a minute' set aside while the mechanic reached up to free a stuck pin or grease a pivot. A hydraulic seal lets go. A control switch is bumped. A leak that's been minor finally gives. The bed comes down. The mechanic, hands raised, gets pinned between bed and frame. There is no escape from that pinch — it's measured in fractions of a second, not seconds.",
    hazards_reviewed:
      "Crush between bed and frame on dump trucks · Under-boom crush on excavators / cranes · Pinch in counterweight rotation · Crush under unsupported attachment · Drop of bucket / blade with engine off",
    discussion_notes:
      "• Body-prop pin engaged ANY time a mechanic is under a raised bed. Not 'most of the time.' EVERY time. Even for 30 seconds of grease work.\n• Boom or arm: lower it ALL THE WAY DOWN before any service. If you must work under one raised, block it with cribbing rated for the load.\n• Stinger pins on stinger steer / tag-axles — pin them in or out, do not work under them in mid-position. Hydraulic cushion will not hold.\n• Counterweight rotation on excavators — clear the swing radius before service. Even with the engine off, hydraulics can creep.\n• Bucket / blade — drop to ground or block before service. Hydraulic seal failures drop loads. Mechanical blocks don't.\n• Communicate at shift change. New mechanic taking over a job needs to know what's blocked, what's pinned, what's pressurized.\n• If a body prop doesn't engage cleanly, the truck doesn't go under work. Fix the prop first.",
    references_cited:
      "OSHA 29 CFR 1910.147 · OEM body prop manuals · ANSI / SAE blocking standards · MASCI Shop SOP",
    action_items:
      "Body-prop-pin-always rule reinforced · Cribbing inventory verified · Counterweight clear-zone reviewed · Shift-handoff communication discussed",
  },
  {
    key: "shop_battery_explosion",
    title: "Battery Charging, Boost, and Hydrogen Explosion",
    category: "Hazard-Specific",
    domain: "shop",
    role_context: ["mechanic", "lead", "driver"],
    incident_pattern:
      "Battery explosions look like a movie effect and they happen in real life. A mechanic is boosting a dead truck, the dead battery has been discharged for weeks, and the cells have outgassed hydrogen into the case. The boost clamp arcs at the post, the spark ignites the hydrogen, and the battery case bursts. Acid and plastic fragment fly in every direction — into the mechanic's face, eyes, arms. The injuries are sometimes blinding and always burning. The fix is older than the truck: connect last to a ground, not to the battery, and check for case bulging or off-gassing before you touch it.",
    hazards_reviewed:
      "Hydrogen explosion during boost / charge · Acid burn to eyes / skin · Acid spray from cracked case · Boost-cable arc / fire · Battery case rupture from internal short · Lifting injury from heavy commercial batteries",
    discussion_notes:
      "• Look at the battery BEFORE you connect. Bulging case = OUT OF SERVICE. Replace, do not boost.\n• Boost connection sequence: red-positive to dead-positive · red-positive to live-positive · black-negative to live-negative · black-negative to DEAD-VEHICLE GROUND (frame), NOT to the dead battery post.\n• That last connection is where the arc happens. Putting it on a frame ground keeps the arc AWAY from hydrogen at the cells.\n• Eye protection on. Acid is not survivable in the eyes without immediate flushing — 15+ minutes at the eyewash station.\n• Ventilation during charging. Open the hood. Don't charge a sealed truck in a closed bay without ventilation.\n• Disconnect negative FIRST when removing a battery. Connect negative LAST when installing. Reduces arc risk at the cell.\n• Commercial batteries are HEAVY — 70+ lbs. Two-person carry or proper lifter. Backs and toes are typical injuries.\n• Acid spill kit and eye-wash station tested every month. Untested eye-wash is a useless eye-wash.",
    references_cited:
      "OSHA 29 CFR 1910.151 · OSHA 1910.305 · OEM battery service manuals · MASCI Battery Service SOP",
    action_items:
      "Battery visual inspection step added · Boost-to-ground-not-battery sequence reinforced · Eyewash monthly test scheduled · Two-person lift policy reviewed",
  },

  // ============================================================
  // ASPHALT PLANT / CRUSHER / LAB / AIRPORT · PHASE F · iter251
  // ------------------------------------------------------------
  // Plant, crusher pad, lab bench, and airport movement areas.
  // Voice: experienced plant operator / lab tech / airfield lead.
  // ============================================================
  {
    key: "plant_conveyor_entanglement",
    title: "Conveyor Belt Entanglement — Tail Pulleys and Pinch Points",
    category: "Hazard-Specific",
    domain: "plant",
    role_context: ["plant_operator", "groundman", "lead"],
    incident_pattern:
      "Conveyor entanglement fatalities at aggregate and asphalt plants follow a sickeningly predictable pattern. A laborer goes near a running tail pulley to clear a buildup of fines or a piece of tramp metal. They reach in with a shovel, the shovel catches the belt, and they're pulled into the pinch point between belt and pulley. The conveyor doesn't stop on its own. By the time the operator hits the e-stop from the control house, the worker is already gone. EVERY conveyor incident report we've ever read includes the line 'guard was off' or 'I was just going to grab it real quick.'",
    hazards_reviewed:
      "Entanglement at tail / head / take-up pulley · Pinch at idler rollers · Loose clothing catching belt · Climbing on running belt · Cleaning under running belt · Crush from belt stops/starts during service",
    discussion_notes:
      "• NO ONE near a running tail pulley or head pulley. Period. Build-up is cleared with the belt LOCKED OUT, not running.\n• Guards on all pinch points whenever the conveyor runs. If a guard is off for service, the conveyor is LOCKED OUT.\n• Tramp metal cleared with the belt off, not 'I'll grab it before the next dump.' Magnets and metal detectors are there to prevent that very situation.\n• No reaching into a running belt with a shovel, broom, bar, hand. No exceptions.\n• Pull-cord e-stops along the full length, tested weekly. Operators should know exactly where the closest cord is.\n• Walking under a belt — wear hard hat, watch for material drop, never stand under a belt that's being cleaned upstream.\n• Climbing on a belt — only with belt locked out and tagged. Never on a running belt.\n• New plant workers: walk the conveyor system on Day 1 with the lead. Point at every pinch point. Show every e-stop.",
    references_cited:
      "OSHA 29 CFR 1910.147 · MSHA 30 CFR Part 56 · NSSGA conveyor safety · MASCI Plant SOP",
    action_items:
      "No-touch-running-belt rule reinforced · Guard inspection assigned · Pull-cord function tested · New-worker conveyor walkthrough scheduled",
  },
  {
    key: "plant_baghouse_silo_hazards",
    title: "Baghouse Cleanout and Silo Entry Hazards",
    category: "Hazard-Specific",
    domain: "plant",
    role_context: ["plant_operator", "lead", "mechanic"],
    incident_pattern:
      "Silo and baghouse fatalities almost always involve someone going inside without a confined-space permit. The pattern: a baghouse is plugging up, production is dropping, and someone climbs into the housing to break the bridge of material. They don't tell anyone exactly where they are. The bridge fails, material avalanches down, and they're engulfed. Asphalt silos add hot bitumen vapors and the risk of falling into hot material. Aggregate silos add fine dust at suffocation densities. Both have killed plant workers in the last 5 years across this industry. The fix is the same fix it's always been: confined-space permit, atmospheric testing, attendant, retrieval line.",
    hazards_reviewed:
      "Engulfment in flowing material · Asphyxiation from low O2 in silo atmosphere · Burn from hot bitumen contact · Bridge collapse on workers · Crush from rotating clean-out equipment · Falls from baghouse access platforms",
    discussion_notes:
      "• Confined-space entry permit BEFORE anyone enters a silo, baghouse, or storage vessel. No 'just gonna pop in real quick.'\n• Atmospheric testing — O2, LEL, CO, H2S minimum. Continuous monitoring while occupied. Asphalt silos: also test for VOCs.\n• Attendant outside at all times. They DO NOT enter to rescue. They call rescue. They maintain communication.\n• Retrieval line and full-body harness for the entrant. Asphalt silos add heat-resistant PPE.\n• Material isolation BEFORE entry. Lockout the silo feed. Lockout the discharge. Verify the bridge is broken from OUTSIDE if possible.\n• Bridge-breaking from outside whenever possible — long bars, air lances, vibrators. Going inside should be the last option, not the first.\n• Baghouse access platforms — full guardrails, fall protection above 6 ft, never trust a platform with corroded grating.\n• Asphalt silo emergencies: the worker is on the hot side. Get them out FAST. Have rescue plan written and rehearsed.",
    references_cited:
      "OSHA 29 CFR 1926 Subpart AA · OSHA 1910.146 · NIOSH silo entry · MASCI Confined Space SOP",
    action_items:
      "Confined-space permit policy reinforced · Atmospheric monitor calibrated · Bridge-from-outside tools available · Rescue plan reviewed",
  },
  {
    key: "plant_asphalt_burns_oil_exposure",
    title: "Hot Asphalt Burns and Bitumen Vapor Exposure",
    category: "Hazard-Specific",
    domain: "plant",
    role_context: ["plant_operator", "driver", "lab_tech", "lead"],
    incident_pattern:
      "Asphalt burns are not like normal burns. The material is 300–350°F when it hits skin and it STICKS — it doesn't run off like hot water. The worker cannot get it off in time to prevent third-degree burns. The most common scenario is a sampler at the load-out, a driver climbing on the truck, or a lab tech at the kettle. A splash, a contact with a hot line, a sudden release of trapped material — and what would have been a flinch is now a hospital trip with skin grafts. Bitumen vapors at the plant compound the issue with respiratory irritation and long-term exposure concerns.",
    hazards_reviewed:
      "Third-degree burn from hot asphalt contact · Burn from steam release at load-out · Vapor inhalation (PAH exposure) · Eye burn from splash · Slip on cooled spilled binder · Burn through clothing",
    discussion_notes:
      "• Long sleeves, long pants, gloves with cuffs. Asphalt-rated boots — leather, not synthetic. Synthetic boots melt INTO the foot.\n• Face shield over safety glasses for any load-out work, sampling, or kettle work. Splashes go for the face.\n• Stand UPWIND of the spout when loading. Drivers: stay in the cab during load-out where allowed. If you must be out, eye protection.\n• Never use water to wash hot asphalt off skin. Cool with cold compresses if possible, then to the ER. Water can drive the heat in deeper.\n• Sampling: long-handled samplers. Never reach into a kettle or load-out chute with a short tool. The splash distance is real.\n• Bitumen vapors — work upwind, take breaks, report symptoms (headache, eye burning, throat irritation). Long-term monitoring matters.\n• Eye-wash and emergency shower within 25 feet of asphalt operations. Tested monthly.\n• If a worker is burned: cover the burn with a clean dry cloth (do NOT try to remove asphalt from skin). To ER immediately.",
    references_cited:
      "OSHA 29 CFR 1910.132 · ACGIH TLV for bitumen · NIOSH asphalt fume guidance · MASCI Plant Burn SOP",
    action_items:
      "PPE for plant work verified · Long-handle sampler usage discussed · Eye wash / shower tested · Burn response procedure reviewed",
  },
  {
    key: "plant_burner_systems",
    title: "Burner Systems — Light-Off and Flameout Hazards",
    category: "Hazard-Specific",
    domain: "plant",
    role_context: ["plant_operator", "lead"],
    incident_pattern:
      "Burner-related incidents at hot-mix plants follow two patterns. The first is light-off explosion: the burner cycles through ignition, fails to light, but fuel keeps feeding. The unburned fuel pools in the drum. When ignition finally catches, the accumulated fuel explodes — blowing the drum end out, throwing flame across the plant pad, and injuring anyone nearby. The second is flameout during operation: the flame goes out, fuel continues, and the next light-off behaves the same. Both are caused by skipped purge cycles, weak ignition sources, or operating outside the control envelope. Modern flame-safeguard systems prevent this — IF they're maintained and not bypassed.",
    hazards_reviewed:
      "Light-off explosion in drum · Flashback to fuel line · Burn from drum-end blowout · Hearing damage from explosion · CO buildup in plant operating area · Fuel leak ignition",
    discussion_notes:
      "• Purge cycle EVERY light-off. Not 'when I think about it.' EVERY time. The purge clears any unburned fuel from prior attempts.\n• Don't bypass the flame-safeguard system. If it's tripping repeatedly, FIX the cause — don't jumper around it.\n• Light-off sequence: purge → pilot ignition → main burner ignition → flame detected → full fire. Each step verified before next.\n• If the flame goes out during operation: shut fuel off IMMEDIATELY, complete a purge cycle, then re-light. Do not just keep feeding.\n• Burner area clear of personnel during light-off. Set the rule, enforce it. If something fails, you don't want anyone in the line of fire.\n• Daily inspection of fuel lines, valves, pilot, flame scanner. Leaks at the burner are catastrophic if they pool and find ignition.\n• CO monitoring in the plant pad area. Inversions and tight wind conditions trap exhaust. Workers need to know if it's accumulating.\n• If you smell unburned fuel near the burner — STOP. Shut down. Investigate before relighting.",
    references_cited:
      "NFPA 86 · OSHA 29 CFR 1910.106 · OEM burner manuals · MASCI Plant Burner SOP",
    action_items:
      "Purge cycle protocol reinforced · Flame-safeguard tampering policy discussed · Daily fuel-line inspection assigned · CO monitor verified",
  },
  {
    key: "plant_loader_blind_spots_haul_road",
    title: "Loader Blind Spots and Haul-Road Interactions",
    category: "Hazard-Specific",
    domain: "plant",
    role_context: ["loader_operator", "driver", "lead"],
    incident_pattern:
      "Plant pad and haul-road incidents almost always involve a loader and a haul truck or a pickup. The loader operator has good visibility in the direction the bucket is facing — and poor visibility BEHIND and to the right. A truck driver pulls into position, a foreman walks the pad to inspect material, or a sales rep wanders out from the office. The loader backs up to reposition for the next dump, and the gap between the bucket and the truck closes. The pattern is constant traffic, constant motion, and a loader operator who can't see everyone all the time. Pad supervision and traffic discipline are what prevent these.",
    hazards_reviewed:
      "Struck-by from backing loader · Pickup driver in loader blind spot · Crushed between loader and stockpile · Sales / visitor in active pad area · Material avalanche during loader operation",
    discussion_notes:
      "• Loader operators: backup-alarm functional, EVERY shift. If it's broken, the loader doesn't run.\n• Pull-up/pull-out lane for haul trucks — defined and signed. Drivers stay in cab during load whenever possible.\n• Visitors / sales / management on the pad: hi-vis vest + hard hat, escorted, never in active loader path. If you're not loading, you're somewhere else.\n• Loader operator does NOT load if anyone is in the backing zone. Pause, signal them clear, then operate.\n• Haul road has a posted speed limit and a one-way pattern. Enforce it. Side-by-side traffic on a haul road is a head-on waiting to happen.\n• Watch the stockpile face. A loader undercutting a face creates an overhang that can collapse without warning. Keep faces sloped to the angle of repose.\n• Foremen on the pad: stand where you can see the loader's eyes through the cab glass. If you can't, the operator can't see you either.\n• Night plant operations: loader operator with cab-light off, drivers with headlights aimed away from the operator. Glare blinds the loader to ground workers.",
    references_cited:
      "OSHA 29 CFR 1926.602 · MSHA 30 CFR Part 56 · NSSGA Plant Safety · MASCI Pad Traffic SOP",
    action_items:
      "Backup-alarm shift-check verified · Visitor escort policy reviewed · Stockpile face slope inspected · Night-glare procedure discussed",
  },
  {
    key: "plant_crusher_clearing_jams",
    title: "Crusher Jams — Clearing Blocked Crushers Safely",
    category: "Hazard-Specific",
    domain: "plant",
    role_context: ["crusher_operator", "lead", "mechanic"],
    incident_pattern:
      "Crusher clearing incidents are some of the worst injuries in the aggregate industry. A piece of tramp metal or oversize feed jams the crusher. The operator climbs onto the feed conveyor or into the crusher mouth with a pry bar to free the material. The crusher is still energized, the operator is in a tight space with stored hydraulic / mechanical energy, and either the jam releases violently (throwing the material and the worker) or someone bumps a control and the crusher starts. Limbs are lost. Workers are killed. The pattern is the same one shop people see with LOTO — but worse, because crushers have enormous stored energy.",
    hazards_reviewed:
      "Crusher start-up while occupied · Sudden jam release projectile · Crush in feed throat · Falls from feed conveyor · Stored hydraulic / spring energy release · Tramp metal projectile",
    discussion_notes:
      "• LOTO the crusher before ANY jam-clearing work. Main motor disconnect. Hydraulic isolation. Personal lock for every worker involved.\n• Verify zero energy. Try-start at the control. Drop hydraulic pressure. Block any movable component mechanically.\n• Never clear a jam by hand from the feed throat. Use long-handled tools from OUTSIDE the crushing zone.\n• If you must enter — confined-space treatment. Attendant. Retrieval. Communication.\n• Tramp metal management — magnet, metal detector, scalper. PREVENT the jam before it happens.\n• Oversized material — kicked off at the scalper, not allowed to reach the crusher mouth.\n• When releasing a jam, stand off-axis from the throat. Released material can shoot back fast.\n• Crusher operators: train new hands on jam-clearing procedure with the crusher locked out, walking through every step BEFORE they encounter a real jam.",
    references_cited:
      "OSHA 29 CFR 1910.147 · MSHA 30 CFR Part 56 · NSSGA Crusher Safety · OEM crusher manual",
    action_items:
      "Crusher LOTO procedure reviewed · Long-handle tools available · Tramp metal management discussed · New-hand jam-clearing training scheduled",
  },
  {
    key: "plant_lab_solvents_ignition",
    title: "Asphalt Lab — Solvents, Ovens, and Ignition Risk",
    category: "Hazard-Specific",
    domain: "plant",
    role_context: ["lab_tech", "lead"],
    incident_pattern:
      "Asphalt-lab fires usually involve solvents and ovens. A tech runs an extraction using trichloroethylene or perchloroethylene, vents to the hood, sets the rotovap, and walks away. A backflow into the oven, a hot spot in the heating element, an arcing motor — and the solvent vapor finds ignition. The fire is fast and the smoke is toxic. Lab techs working alone are at the highest risk because no one sees the early warning signs. The other pattern is the ignition-point apparatus during AC ignition-loss testing — open flame, hot solids, near combustibles. These labs are tighter than people think.",
    hazards_reviewed:
      "Solvent vapor ignition · Burn from heated apparatus · Inhalation of TCE / perc / fumes · Glass breakage with hot oil · Eye splash from extracted binder · Slip on solvent spill",
    discussion_notes:
      "• Ventilation hood operational and tested. EVERY extraction run uses the hood. If the hood is down, the test waits.\n• Solvent containers labeled, capped, stored in a flammable cabinet between uses.\n• Hot work — ovens, ignition-point apparatus, kettles — kept physically separate from solvent work. Hot side / cold side discipline.\n• PPE: nitrile gloves, eye protection, lab coat. NO loose hair, NO scarves, NO lab coats with strings or ties.\n• Eye wash and emergency shower within 10 seconds of any apparatus. Tested weekly.\n• Solvent waste containers metal, capped, grounded. Not glass, not open jars on a shelf.\n• No eating, drinking, or storing food in the lab. Bitumen and solvents transfer to hands and into mouths.\n• Lab tech working alone after hours — call-in protocol. Someone knows you're in there. They check in if you don't text out.",
    references_cited:
      "OSHA 29 CFR 1910.1450 (Lab Standard) · NFPA 45 · ACGIH TLVs · MASCI Lab SOP",
    action_items:
      "Hood function test verified · Solvent storage audit done · Hot side / cold side layout discussed · After-hours check-in protocol set",
  },
  {
    key: "plant_silo_burn_avalanche",
    title: "Asphalt Silo Drag Slat and Material Avalanche",
    category: "Hazard-Specific",
    domain: "plant",
    role_context: ["plant_operator", "driver", "lead"],
    incident_pattern:
      "Asphalt silo loadout is a dangerous interface — hot material at 300°F+ sitting in a silo, released through a gate, falling 8–15 feet into a truck bed below. The pattern of injury is two-fold: drivers under the silo during a drop get burns from splash or overflow, and drag-slat conveyors above the silo can throw material if a buildup releases unexpectedly. The classic incident is a driver climbing the silo platform to check the load level, leaning over, and getting hit by a sudden material release as the gate opens. Or a maintenance worker on the drag slat platform when an upstream jam clears.",
    hazards_reviewed:
      "Burn from sudden material release at gate · Fall from silo platform · Crush from drag-slat chain · Burn from drag-slat oil leak · Toxic vapor inhalation at top of silo · Stuck driver under hot silo",
    discussion_notes:
      "• Driver under the silo: in the cab during load. Always. Climb out only after the gate has closed and the chute drained.\n• Silo top access: harness and tie-off above 6 ft. Even on a railed platform, fall protection during any task that involves leaning.\n• Drag-slat conveyors are LOTO whenever a worker is on the platform for service or inspection. Walking past for visual check from a safe distance is one thing — service work needs full LOTO.\n• Communication between loadout operator and driver — radio or horn signal. Driver knows when the gate is about to open.\n• Silo gate misfires — if a gate isn't sealing, take the silo OUT OF SERVICE for repair. Do not work around a misfiring gate.\n• Vapors at the silo top — bitumen vapors collect in the top space. Don't open the inspection hatch in calm wind without ventilation. Take a break upwind after exposure.\n• Truck bed under the silo: visual confirmation before opening the gate. Empty bed, properly positioned. Foreman gives the OK.",
    references_cited:
      "OSHA 29 CFR 1926.501 · MSHA Silo Safety · OEM silo / drag-slat manuals · MASCI Loadout SOP",
    action_items:
      "Driver-in-cab-at-loadout rule reinforced · Silo top fall protection verified · Drag-slat LOTO procedure reviewed · Gate-misfire OOS rule discussed",
  },
  {
    key: "airport_movement_area_awareness",
    title: "Airport Movement Areas — Runway, Taxiway, and ATC Discipline",
    category: "Hazard-Specific",
    domain: "airport",
    role_context: ["operator", "driver", "lead", "spotter"],
    incident_pattern:
      "Airport-job incidents involve aircraft, not just ground equipment. The pattern repeats: a crew is doing paving or pavement repair at the edge of a runway or taxiway. The lead has cleared the work zone with ATC. The clearance was for one hour. The crew runs over the clearance because a piece of equipment broke down. ATC, assuming the zone is clear at the agreed time, releases the runway. An aircraft is rolling in 90 seconds. The worker pulling a piece of equipment off doesn't know the clearance has lapsed. The most consistent finding in airport-related fatalities is communication breakdown — between ATC, the lead, and the workers on the ground.",
    hazards_reviewed:
      "Aircraft strike of worker or equipment in active movement area · Jet blast / prop wash · FOD created by site debris · Equipment incursion into active runway · Communication breakdown with ATC · Confusion at low-vis or night operations",
    discussion_notes:
      "• Movement-area work requires ATC clearance and a CONFIRMED window. The lead has the radio. The lead is on it.\n• If the work window is about to expire — STOP. Pull everyone and everything out. Do NOT push the time. ATC will re-clear; aircraft cannot land twice.\n• Workers all carry radios on the operations frequency the airport authority assigns. Listen first, talk second.\n• FOD discipline — every wrench, every cone, every scrap of debris accounted for before clearing the area. A loose bolt destroys a jet engine.\n• Hi-vis at airfield specs — not the same as construction hi-vis. ANSI 207 Public Safety colors where required. Read the contract spec.\n• Equipment in active zone — escorted, marked, and on ATC radio. Pickups too. No one freelances onto a taxiway.\n• Jet blast / prop wash zones — even small aircraft create wind that can throw a person or a cone. Stay clear of holding aircraft.\n• Night / low-vis ops — extra coordination, extra lighting, extra check-ins. Don't push through bad-vis without authority alignment.",
    references_cited:
      "FAA AC 150/5210-5 · FAA AC 150/5370-2 · TSA / airport-specific procedures · MASCI Airport Operations SOP",
    action_items:
      "ATC clearance protocol reinforced · FOD accountability reviewed · Radio discipline discussed · Window-expiry pullout drill assigned",
  },
  {
    key: "airport_jet_blast_fueling",
    title: "Jet Blast, Prop Wash, and Airfield Fueling Awareness",
    category: "Hazard-Specific",
    domain: "airport",
    role_context: ["operator", "driver", "lead"],
    incident_pattern:
      "Workers underestimate jet blast and prop wash. A regional turboprop spooling up generates 100+ mph of wash behind it. A commercial jet at idle thrust generates winds capable of flipping a pickup. The pattern: a crew is positioning equipment near a holding aircraft, the pilot bumps thrust to begin taxi, and a worker, a cone, or a piece of equipment gets thrown. Combine that with the airfield fueling environment — Jet-A is everywhere, ignition sources must be controlled, and a static spark is a Class B fire instantly. Airfield work has its own hazards that don't exist anywhere else.",
    hazards_reviewed:
      "Worker / equipment thrown by jet blast · Prop wash injury to ground crew · Jet-A static ignition · Vapor cloud ignition near fueling ops · Hearing damage from aircraft noise · FOD from blown debris",
    discussion_notes:
      "• Stay clear of holding aircraft. A 100-foot clearance is a starting point, not a maximum. If you can see the engine, the engine can hit you with blast.\n• Hearing protection in any active movement area. Aircraft noise damages hearing in minutes of exposure.\n• Jet-A fueling areas — no spark sources within 50 feet. No cell phones, no flashlights without intrinsic safety rating, no metal-on-metal.\n• Tie down or weigh down EVERYTHING near a taxiway. Cones, sawhorses, equipment. What stays put in normal wind blows away in prop wash.\n• Fueling operations have their own crew. Construction crews don't intersect with fueling ops. Stay clear of fuel trucks and refueling aircraft.\n• Static grounding for any fueling-adjacent work. Bonding cables, grounding rods. Static is the silent ignition source.\n• If you feel wind suddenly — look around. An aircraft is moving somewhere you didn't expect. Verify position before continuing.\n• Eye protection — debris in airfield work is everywhere. Open faceshields aren't enough at busy airfields.",
    references_cited:
      "FAA AC 150/5230-4 · NFPA 407 (aircraft fuel servicing) · OSHA 1926.101 (hearing) · MASCI Airfield SOP",
    action_items:
      "Aircraft clearance distance reinforced · Hearing protection verified · Fueling-adjacent ignition control discussed · Tie-down policy for cones / equipment reviewed",
  },

  // ============================================================
  // OFFICE / ADMIN · PHASE G · iter251
  // ------------------------------------------------------------
  // Operationally realistic topics for non-field staff who
  // still touch the work — site visits, parking lots, severe
  // weather accountability, lone-worker realities.
  // ============================================================
  {
    key: "office_distracted_driving",
    title: "Distracted Driving — Phones, Coffee, and the Commute",
    category: "Hazard-Specific",
    domain: "office",
    role_context: ["office", "manager", "estimator", "sales"],
    incident_pattern:
      "Distracted-driving crashes hit office staff at a rate the field doesn't see, because office staff drive MORE — between jobs, between meetings, to lunches and back. The pattern is benign individually: a quick text from a PM, a glance at the navigation, a sip of coffee while merging. Stack three of those small things in 10 seconds and you've crossed a centerline at 65 mph. The most consistent factor in office-staff crashes isn't impairment — it's the cumulative inattention of a busy person doing six things while driving. The fix is policy and habit, not technology.",
    hazards_reviewed:
      "Head-on / off-road crash from inattention · Rear-end at signal change · Phone-handling violation citation · Speeding in school / construction zones · Fatigue from over-scheduled days · Eating / drinking while driving",
    discussion_notes:
      "• Phone face-down or in a holder, in DRIVE-DO-NOT-DISTURB mode. Calls go to voicemail. Texts wait.\n• Hands-free is still distracted. Cognitive load matters, not just hand position. Save the call for the parking lot.\n• Navigation set BEFORE you put the truck in gear. Re-routing while driving is a leading cause of office-related crashes.\n• Coffee, food, paperwork — pull over. The 90 seconds it costs is the cheapest insurance you'll buy.\n• Schedule margin. If your day has zero margin, every late meeting becomes a speeding trip. Build slack into your calendar.\n• Construction zones — both ways. Slow down through MASCI's OWN zones first. Lead the culture.\n• Severe weather — pull over and wait. Rain at 70 mph is not driving, it's gambling.\n• If you're tired, you're driving impaired. Pull over for 20 minutes. The meeting will wait.",
    references_cited:
      "NHTSA Distracted Driving · State hands-free laws · MASCI Fleet Vehicle Policy",
    action_items:
      "DND-while-driving policy reinforced · Hands-free still risky message discussed · Schedule-margin discipline reviewed · Severe-weather pull-over rule discussed",
  },
  {
    key: "office_site_visit_ppe",
    title: "Site Visit PPE and Visitor Expectations",
    category: "Procedure / SOP",
    domain: "office",
    role_context: ["office", "manager", "estimator", "sales", "visitor"],
    incident_pattern:
      "Most office-staff site injuries happen in the first 5 minutes of arriving at a jobsite. The pattern: arrive in office clothes, no hi-vis, no hard hat, walk toward the foreman to find them, and step into the swing radius of an excavator or into a backing dump truck path. The visitor doesn't know the site, the operators don't know the visitor is coming, and the foreman is 200 feet away. Office staff often think 'I'm just popping in for 5 minutes' justifies skipping PPE. The crew has worked all morning building a culture of PPE and the visitor undermines it instantly. The fix is PPE in the vehicle, no exceptions.",
    hazards_reviewed:
      "Struck-by equipment on first arrival · Trip / fall on rough site terrain · Eye injury from blown debris · Head injury from low overhead · Heat stress without water / shade · Visitor undermining crew PPE culture",
    discussion_notes:
      "• PPE kit in every office vehicle: hard hat, Class 2 hi-vis vest, safety glasses, leather gloves, safety boots (or shoe covers as a fallback for ONE site visit).\n• Put PPE on BEFORE you exit the vehicle. Not after you walk 50 feet across the parking area. Before.\n• Find the foreman by RADIO or PHONE before walking. The foreman comes to YOU at a safe meeting point — not the other way around.\n• Stay in marked walking paths. Do not cut across active work zones, even if it adds 100 feet.\n• Sign in at the gangbox / sign-in sheet. The site knows who's on-site.\n• Don't show up at lunch with no announcement. Schedule the visit. Let the foreman tell the crew.\n• Heat / cold — bring water, dress for the weather, know where the break trailer is.\n• Lead by example. The crew sees if YOUR PPE is right. They follow that signal.",
    references_cited:
      "OSHA 1926.95 / .96 / .100 / .102 (PPE) · ANSI/ISEA 107 · MASCI Visitor SOP",
    action_items:
      "PPE kit in every office vehicle verified · Find-the-foreman-first habit reinforced · Scheduled-visit policy reviewed · Visitor sign-in enforced",
  },
  {
    key: "office_parking_lot_struck_by",
    title: "Parking Lots, Backing, and Pedestrian Awareness",
    category: "Hazard-Specific",
    domain: "office",
    role_context: ["office", "visitor", "driver"],
    incident_pattern:
      "Parking-lot incidents at MASCI sites and customer offices happen at the slowest speeds and still produce the most ankle, knee, and back injuries on the admin side. The pattern: an admin or PM is walking from a vehicle to the office door, looking at their phone for the meeting confirmation. A backing pickup driver, also distracted, never sees them. The contact is at 3–5 mph. The pedestrian doesn't go down hard but twists out of the way — knee, ankle, back. Other variant: stepping out of a cab into a parked vehicle next to yours. Door-edge meets the next door, owner is upset, claim filed. Slow speeds, big outcomes.",
    hazards_reviewed:
      "Backing vehicle struck-by · Slip on wet / icy parking lot · Step off curb into vehicle path · Door-strike to adjacent vehicle · Tripping on parking blocks · Visibility issues in winter / low-light",
    discussion_notes:
      "• Phone DOWN while walking. Eyes on the lot, on backup lights, on movement. The text waits.\n• Walk in marked crosswalks where they exist. Where they don't, pick the safest path and stick to it.\n• When backing — back BEFORE the kids and pedestrians come out. Or pull through if available. Or back camera, mirror sweep, AND quick over-the-shoulder. Cameras alone are not enough.\n• Step out of your vehicle into a CLEAR space — don't open the door blind into the next lane.\n• Winter / wet — boots with grip on the soles, not dress shoes. A slip in the parking lot still happens at MASCI age.\n• Park in lit spaces at night. Visibility of YOUR vehicle matters as much as visibility from YOUR vehicle.\n• Watch for office staff and visitors at customer sites — they're not used to construction-vehicle scale. Slow down extra in customer parking.",
    references_cited:
      "OSHA General Duty · NHTSA Pedestrian Safety · MASCI Fleet Policy",
    action_items:
      "Phone-down-while-walking habit discussed · Backing-camera-plus-mirror rule reviewed · Winter footwear discussion · Customer-lot extra-caution reinforced",
  },
  {
    key: "office_heat_stress_visits",
    title: "Heat Stress on Summer Site Visits",
    category: "Hazard-Specific",
    domain: "office",
    role_context: ["office", "manager", "estimator", "visitor"],
    incident_pattern:
      "Heat injuries to office staff during site visits in summer follow a specific pattern. The visitor arrives in business-casual clothes, doesn't have water, walks the site for 30–45 minutes in 95°F+ heat, and only realizes they're in trouble when they're already symptomatic — headache, lightheadedness, nausea. They drove themselves to the site, and now they have to drive themselves home while heat-symptomatic, which is its own crash risk. Office staff have lower heat tolerance than the field crew because they're not heat-acclimatized. A 20-minute walk for a field hand is a serious health risk for someone who sat in AC all morning.",
    hazards_reviewed:
      "Heat exhaustion progressing to heat stroke · Crash from driving while heat-symptomatic · Dehydration · Sunburn / eye damage from prolonged exposure · Underestimating heat without acclimation",
    discussion_notes:
      "• Water bottle in the vehicle, every site visit, May through October. Drink before, during, and after the visit.\n• Schedule summer site visits in the morning or late afternoon. Avoid 11 a.m. to 3 p.m. heat peak.\n• Hat that shades the face and neck. Sunscreen. Long sleeves are actually cooler than bare skin in direct sun.\n• Take breaks in the break trailer or in your vehicle with AC. Don't 'tough it out.'\n• Watch for symptoms in yourself and others: headache, nausea, irritability, dizziness, sudden quietness. Heat exhaustion progresses to heat stroke FAST.\n• If symptoms appear: get into shade or AC, drink water with electrolytes, cool the body. If symptoms don't resolve in 15 minutes — ER.\n• Driving while heat-symptomatic is impaired driving. Get someone to drive you. Call dispatch. Wait it out at the break trailer.\n• New hires and visitors are NOT acclimatized. Treat them more conservatively than the field crew.",
    references_cited:
      "OSHA Heat Stress · NIOSH Heat Stress · CDC Heat Illness · MASCI Heat Policy",
    action_items:
      "Water-in-vehicle habit reinforced · Morning-visit scheduling reviewed · Symptom-awareness discussed · Don't-drive-impaired rule reinforced",
  },
  {
    key: "office_lone_worker_checkin",
    title: "Lone Worker / Site Check-In Realities",
    category: "Procedure / SOP",
    domain: "office",
    role_context: ["office", "manager", "estimator", "visitor"],
    incident_pattern:
      "Lone-worker incidents at MASCI typically involve a PM, an estimator, or a sales rep who drove to a remote jobsite, parked, walked the project alone, and either had a medical event (heart, stroke, fall) or got into a tense interaction with a customer or trespasser. No one knew exactly where they were. The phone hadn't moved for 45 minutes. By the time someone followed up, the situation had become serious. The fix is unglamorous: tell someone where you're going, set a check-in time, and follow through. We have not had a fatality from this — but we've had close calls that have changed how seriously we take check-ins.",
    hazards_reviewed:
      "Medical event with no one to respond · Slip / fall with no observer · Tense interaction with trespasser · Vehicle breakdown in low-signal area · Hostile customer / dispute escalation · Lost / disoriented in unfamiliar area",
    discussion_notes:
      "• Tell someone — dispatch, an admin, your manager — where you're going and when you expect to be back. Text works.\n• Set a check-in TIME, not just an intent. 'I'll text by 2:30.' If 2:30 passes with no text, that person calls you.\n• Phone charged before leaving the office. Bring a charger and a charged power bank for longer trips.\n• Don't enter a hostile situation alone. Customer dispute escalating? Pull back, call your manager, return with a partner.\n• Trespassers / unknown people on the site — don't engage alone. Call site security or local LE. You are not a security guard.\n• Vehicle breakdown in a remote area — stay with the vehicle if it's safe. Walking out can put you in worse trouble.\n• Medical history — if you have any condition that could leave you unresponsive, the check-in protocol is twice as important.\n• At the end of the visit, text the same person 'clear.' Closes the loop.",
    references_cited:
      "OSHA Lone Worker · ANSI/ASSP Z490 · MASCI Field Visit Policy",
    action_items:
      "Check-in time discipline reinforced · Phone-charging habit discussed · Hostile-interaction de-escalation policy reviewed · End-of-visit 'clear' text habit set",
  },
  {
    key: "office_severe_weather_accountability",
    title: "Severe Weather Accountability for Crews and Visitors",
    category: "Procedure / SOP",
    domain: "office",
    role_context: ["office", "manager", "dispatch", "lead"],
    incident_pattern:
      "Severe-weather events catch office staff at the worst time — driving back from a site visit, midway through a customer meeting, or as the office is closing for the day. The pattern of failure is accountability: the office assumes all crews are pulled in, but two trucks are still out. The field assumes the office has called everyone, but three site visitors are still on site. When a tornado warning hits or a lightning storm rolls in, no one knows for sure who is where. The fix is one person — usually dispatch or admin — owning a check-the-roll process during weather events.",
    hazards_reviewed:
      "Worker / visitor caught in tornado / severe thunderstorm · Lightning strike on site · Flash flooding of low-lying jobsites · Hail damage to crew and equipment · Hypothermia / heat from extended exposure during storm",
    discussion_notes:
      "• One person is the weather POC during a severe-weather event. Usually dispatch or admin. They have the list. They make the calls.\n• Check the radar BEFORE leaving the office in summer thunderstorm season. Watch for fast-moving fronts.\n• Lightning rule: when you SEE lightning OR HEAR thunder, the field crew pulls in. 30/30 rule — 30 minutes after the last strike before resuming.\n• Tornado warning: into the safest available structure. Field crew into the office or substantial building, NOT into a vehicle, NOT into a trailer.\n• Severe rain / flash flood: avoid low-lying jobsites until conditions clear. Many heavy-civil sites are designed to flood — they're channels.\n• Hail: get vehicles under cover where possible. People away from windows.\n• Account for ALL personnel during a severe event. Office, field, drivers, visitors. The POC checks every name on the list.\n• Site visitors: notify them before they leave the office that weather is coming. Tell them to head straight back when conditions degrade.",
    references_cited:
      "NWS Severe Weather Awareness · OSHA Lightning Safety · MASCI Severe Weather SOP",
    action_items:
      "Weather POC designated · 30/30 lightning rule reviewed · Tornado-shelter mapping verified · Visitor weather-notify habit discussed",
  },
  {
    key: "office_slips_trips_falls",
    title: "Slips, Trips, and Falls in the Office Environment",
    category: "Hazard-Specific",
    domain: "office",
    role_context: ["office"],
    incident_pattern:
      "Office slip-and-fall incidents are unglamorous and very real. The pattern: spilled coffee in the kitchenette goes uncleaned for an hour, someone steps in it in dress shoes, and goes down. Or a power cord run across a doorway during a temporary setup, never picked up. Or a stairway with one bulb burned out, and someone misses the last step in the dim corner. None of these are dramatic — but they account for more lost-time office injuries than any other cause. Knees, ankles, hips, wrists. People work injured for weeks because they're embarrassed by a hallway fall.",
    hazards_reviewed:
      "Slip on spilled liquid · Trip over power cord / mat edge · Fall on stairs in low light · Slip on icy entryway · Fall from chair / step stool used as ladder · Slip in restroom",
    discussion_notes:
      "• Clean up spills immediately. Don't wait for someone else. The person who walks through it next might be you.\n• Wet-floor signs when something can't be cleaned right away. They actually work.\n• Power cords during temporary setups — taped down or routed around the path. No cords across walking surfaces.\n• Stairway lighting — report burned-out bulbs the same day. Office facilities replace them.\n• Winter entry mats — kept in place, replaced when worn out. The first 6 feet inside the door is where most winter slips happen.\n• Step stool, not chair, for reaching anything high. We have step stools. Use them.\n• Restroom floor cleanliness — report wet floors to facilities. The person who slipped in there last month was you.\n• Holding 4 things and walking? You're going to drop one or fall over one. Two trips is better than one fall.",
    references_cited:
      "OSHA 1910.22 · NSC slips/trips guidance · MASCI Office Safety Policy",
    action_items:
      "Spill-cleanup-now habit reinforced · Stair-lighting reporting reviewed · Cord-management for temp setups discussed · Step-stool-not-chair rule reinforced",
  },
  {
    key: "office_fatigue_mental_load",
    title: "Fatigue and Mental Load — When You're Tired, You're Impaired",
    category: "Hazard-Specific",
    domain: "office",
    role_context: ["office", "manager", "estimator", "pm"],
    incident_pattern:
      "Mental fatigue is the office equivalent of heat stress in the field — slower to develop, easier to ignore, just as dangerous. The pattern: a PM works 11-hour days for two weeks during a busy season, sleeps badly, lives on coffee. Errors creep in — a job number transposed, a quote that's missing a line item, a critical email that doesn't get sent. The PM blames themselves for not being sharp. The real cause is sustained sleep debt and decision fatigue. Long-term, this pattern leads to depression, family stress, and physical illness. We have lost good people to burnout that started this exact way.",
    hazards_reviewed:
      "Decision errors from sleep deprivation · Crash from driving fatigued · Email / contract errors with downstream impact · Burnout / mental health decline · Family stress · Physical illness from sustained sleep debt",
    discussion_notes:
      "• Sleep is not optional. Seven hours minimum. Less than that for a week is impaired-driving-level cognitive impact.\n• Take your time off. Vacation accruing doesn't help anyone — used vacation does.\n• Decision fatigue is real. The decisions you make at 5 p.m. after 10 hours of meetings are not your best decisions. Batch important calls earlier in the day.\n• When you catch yourself making errors, don't push harder — stop. Walk. Hydrate. Eat. Come back.\n• Mental health is not weakness. Talk to someone. EAP is confidential and useful. Coworkers are useful. Family is useful.\n• Watch your coworkers. Withdrawn, irritable, error-prone — these are the early signs. Check in on each other.\n• Phone off after hours when you can. The job will be there tomorrow. Your mental reserves won't if you don't rebuild them.\n• 988 — Suicide & Crisis Lifeline (call or text). MASCI EAP for confidential help. Construction has one of the highest suicide rates of any industry. This matters.",
    references_cited:
      "CDC Fatigue · NIOSH Total Worker Health · 988 Suicide & Crisis Lifeline · MASCI EAP",
    action_items:
      "Sleep priority discussed · Vacation use policy reviewed · Decision-fatigue awareness raised · 988 / EAP info shared",
  },
];

export const CUSTOM_TOPIC_KEY = "__custom__";

export function findTopic(key) {
  return TOPIC_LIBRARY.find((t) => t.key === key);
}
