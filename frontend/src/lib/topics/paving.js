// Auto-split from monolithic meetingTopicLibrary.js · iter260
// Domain: paving · iter261 Phase H Batch 2 · 3 uplifted + 5 new = 8 topics
// Voice: experienced paving foreman. Plainspoken. No LMS drift.

export const TOPICS_PAVING = [
  {
    key: "asphalt_paving",
    domain: "paving",
    title: "Hot Asphalt & Paving Operations",
    category: "Hazard-Specific",
    severity: "serious_injury",
    incident_pattern:
      "Paving incidents cluster around the back of the truck — the place where hot mix transfers from bed to hopper at 300–325°F. The driver opens the gate, the laborer raking the joint steps too close, and a slop or a sudden release puts hot mix on their boot or their leg. Asphalt sticks. Cotton clothing wicks the heat through. The burn is full-thickness within seconds and the worker tries to pull the boot off — taking the skin with it. Compounding pattern: workers in shorts, t-shirts, or low-cut shoes on 95°F days because 'it was too hot for pants.' Pants and leather boots are the cheapest insurance on the paving train. The discomfort of long sleeves on a hot day is nothing compared to a graft.",
    hazards_reviewed:
      "Severe burns from hot mix (300°F+) · Burns from tack/oil/fuel · Fume inhalation · Struck-by paver, roller, truck · Caught between roller and pavement edge · Heat stress",
    discussion_notes:
      "• Long sleeves, long pants, gloves rated for hot asphalt, leather boots — even in heat.\n• No skin contact with hot mix; raking/lute work upwind of fume plume.\n• Paver and roller no-go zones marked; spotters where workers approach machinery.\n• Truck driver acknowledges crew before dumping; positive comms with screed operator.\n• Fuel and tack handling: bonded containers, no smoking, fire extinguisher within 50 ft.\n• Heat stress program — water, rest, shade rotation. Foreman watching for symptoms.\n• If hot mix contacts skin: do NOT try to pull it off. Cover with clean dry cloth. ER immediately.",
    references_cited:
      "OSHA 1926.95 PPE · NIOSH Asphalt Bulletin · NAPA Worker Safety",
    action_items:
      "Burn-rated PPE issued · No-go zones marked · Heat stress monitoring active · Fire extinguisher onsite · Burn response reviewed",
  },
  {
    key: "tack_prime_coat",
    domain: "paving",
    title: "Tack Coat / Prime Coat Application",
    category: "Hazard-Specific",
    severity: "serious_injury",
    incident_pattern:
      "Tack-coat incidents almost always come from spray-back, not from the truck spraying as intended. The pattern: a clogged nozzle that the operator clears by hand without depressurizing the bar, a kinked hose that releases when a worker moves a barrel, or a worker walking through the spray fan because they didn't see it from the wrong angle. Tack at 140–160°F doesn't kill, but it eats skin and ends up in eyes and mouths. Cutback / emulsified materials add a fire risk when the truck is next to a generator or torch. Most field-tested fix: nobody in the spray-fan envelope, ever — even when the operator says 'it's off.'",
    hazards_reviewed:
      "Burns from hot tack (140°F+) · Fume inhalation · Slip on tacked pavement · Spray-back to operator/worker · Fire / explosion of cutback materials",
    discussion_notes:
      "• Long sleeves, gloves, eye protection — no exposed skin during spray.\n• Cutback materials are flammable — no ignition sources, fire extinguisher staged.\n• Stand upwind of spray bar; nozzle tested at low pressure BEFORE application.\n• Never clear a clogged nozzle without depressurizing the bar first.\n• Track-free time observed before traffic — flag if pedestrians or vehicles approach.\n• Equipment cleaned with approved solvent; spill kits ready.\n• Truck operator and ground crew comms verified before truck moves.",
    references_cited:
      "OSHA 1926.59 (HazCom) · NAPA Tack Coat Best Practices",
    action_items:
      "Burn-rated PPE · Fire extinguisher staged · Comms tested · Spill kit ready · Depressurize-before-clear rule reinforced",
  },
  {
    key: "joint_sealing",
    domain: "paving",
    title: "Joint Sealing — Hot & Cold Pour",
    category: "Hazard-Specific",
    severity: "serious_injury",
    incident_pattern:
      "Joint-sealing burns happen in two predictable moments: pouring from the kettle when the wand is too short and the worker leans in to direct the pour, and refilling the kettle from a melt pot when the lid is cracked and a splash hits the face. Hot pour sealant runs 380–400°F. A drop on a forearm is a serious second-degree burn before you can flick it off. The other recurring incident is the propane backpack heater used inside a tent or barn — CO buildup in minutes, worker passes out, sealant kettle still going. The fix is the basics — long wands, full face shield over goggles, propane outdoors only, and never working a kettle alone.",
    hazards_reviewed:
      "Burns from hot sealant 380°F+ · Fume / vapor inhalation · Slip on freshly sealed joint · Backpack burner / kettle pressure rupture · Solvent fire (cold pour) · CO poisoning from propane indoors",
    discussion_notes:
      "• Hot pour: thermal gloves, long sleeves, face shield over safety glasses while pouring.\n• Long-wand pour gun — do NOT lean over the kettle to direct flow.\n• Kettle pressure relief verified before each shift; never modify safety devices.\n• Propane backpack heater outdoors only — never in a barn, tent, or trailer.\n• Fume control — work upwind; respiratory protection if fumes irritate.\n• Cold pour solvent: SDS review, no smoking, ground containers.\n• Fresh sealant flagged until cured.\n• Two-person rule on the kettle. Never alone.",
    references_cited:
      "OSHA 1926.59 · Manufacturer's Operating Manual · NFPA 58 (Propane)",
    action_items:
      "Thermal PPE issued · Kettle inspected · SDS reviewed · Cured-zone signage · Two-person kettle rule reinforced",
  },
  {
    key: "paving_paver_blind_spots",
    domain: "paving",
    title: "Paver Blind Spots — Screed Crew & Operator Interface",
    category: "Hazard-Specific",
    severity: "fatal_risk",
    role_context: ["paver_operator", "screed_operator", "lead", "rake_crew"],
    incident_pattern:
      "Paver fatalities almost always happen in the same 4-foot zone — between the back of the truck dumping and the front of the paver hopper. The truck driver is watching the hopper, the paver operator is watching the screed, and a laborer steps in to lute a corner or fix a joint. Nobody sees them. The truck driver releases the brake to roll forward into the next-load position, the paver creeps forward to maintain the joint, and the laborer is pinched between the two machines. The other variant is the rake/lute crew working around the wings of the screed when the paver swings to widen — they step backward into the operator's blind spot at the wing's outer edge. The fix is shouting protocol: anyone working within 6 feet of the paver wings or truck-hopper transfer zone calls out their position OUT LOUD to the operator before they enter, and the operator acknowledges OUT LOUD.",
    hazards_reviewed:
      "Pinch between truck and paver during forward creep · Struck by extending screed wing · Run-over by truck reversing to position · Crushed in hopper-fold cycle · Worker in unseen rake-zone behind extending wing",
    discussion_notes:
      "• Verbal callout protocol — laborer entering the front-of-paver zone calls out 'IN FRONT' before stepping in. Operator answers 'CLEAR.' No silent entries.\n• Paver wings are SLOW-MOTION hazards. When the wing is extending, that entire arc is no-go for ground workers.\n• Truck-to-paver interface: only the foreman or designated spotter signals the truck to drop the gate. No freelance signals from the laborer.\n• Screed operator stops the screed before any worker reaches in to lute the joint. Period. Not 'mostly.' Every time.\n• Reflective tape on rake handles helps the operator catch them in peripheral vision.\n• New laborers walk the paver train with the foreman before they touch a lute. Every pinch point shown.\n• Eye contact through the cab glass before stepping into the operator's frame.\n• Radio for night work and noise — voice calls don't carry over a paver at full pitch.",
    references_cited:
      "OSHA 1926.602 · NAPA Paving Train Safety · MASCI Paving SOP",
    action_items:
      "Verbal callout protocol reinforced · Wing-arc no-go zone marked · Stop-the-screed-before-luting habit verified · New-hire paver walkthrough scheduled",
  },
  {
    key: "paving_roller_pinch_zones",
    domain: "paving",
    title: "Roller Pinch Zones — Backing & Edge-of-Mat Crush",
    category: "Hazard-Specific",
    severity: "fatal_risk",
    role_context: ["roller_operator", "lead", "rake_crew"],
    incident_pattern:
      "Roller crush fatalities are some of the most preventable and most repeated incidents in paving. The roller operator is going back and forth on the mat, the visibility from the cab is limited rearward (especially on older smooth-drum rollers without backup cameras), and a laborer steps onto the mat to do a quick touch-up. The operator reverses, the laborer has their back turned, the closing speed is 3 mph — and a 10-ton drum doesn't stop. Most fatalities don't involve the worker being run over from the front; it's the reverse stroke. Compounding factor: rollers running close to the mat edge, where the operator focuses on the line and not on the laborer 8 feet ahead. The fix is rigid — no one on the mat behind a moving roller, ever, and every roller backs up only with the operator's head turned 180°.",
    hazards_reviewed:
      "Worker run over by reversing roller · Crush between two rollers in echelon pattern · Caught between roller drum and edge drop-off · Pinch at vibration toggle / pivot · Falls from roller during mount/dismount",
    discussion_notes:
      "• NO ONE on the mat behind a roller in motion. Period. Touch-ups happen between roller passes, not during.\n• Operator looks 180° behind BEFORE engaging reverse. Backup alarm functional every shift.\n• Echelon (multi-roller) operations — operators coordinate verbally on the radio, NOT by mirror only.\n• Mat edge: roller stays 6 inches off the drop until the joint is built. A drum hanging over the edge can drop the operator down a curb.\n• Vibration toggle is operator-only — no laborer reaches up to the cab to bump it.\n• Mount/dismount only at full stop, parking brake engaged, never with the engine running and the brake off.\n• Radio for night and noisy work — visual signals fail at distance.\n• Operator-to-rake-crew rule: if you can't see them, you don't move. Get eye contact first.",
    references_cited:
      "OSHA 1926.602 · NAPA Roller Operations · MASCI Paving SOP",
    action_items:
      "No-mat-behind-roller rule reinforced · Backup alarm shift-check verified · Echelon radio protocol set · Mount/dismount discipline reviewed",
  },
  {
    key: "paving_asphalt_transfer_burn",
    domain: "paving",
    title: "Asphalt Transfer Burns — Truck to Paver Hopper",
    category: "Hazard-Specific",
    severity: "serious_injury",
    role_context: ["driver", "paver_operator", "lead"],
    incident_pattern:
      "Hopper-transfer burns are common enough that most paving foremen have seen one. The truck driver backs into the paver, the laborer guides the truck with hand signals, and during the dump the gate opens too fast or the truck rolls forward slightly to relieve weight. Hot mix at 310°F+ surges out, splashes off the apron, and hits whoever is closest — usually the screed operator's legs or the laborer's boots. Less common but worse: a laborer in front of the paver during a dump gets hit by a wave of overflow when the hopper fills past its rim. Cotton clothing wicks the heat in. Leather boots either resist or get shed quickly; sneakers melt. Pattern fix is unglamorous — slow dumps, no one in the splash zone, and full PPE on every transfer.",
    hazards_reviewed:
      "Splash burn from hopper-fill overflow · Truck-roll surge during dump · Foot/leg burn through low-cut footwear · Skin burn through cotton clothing · Eye splash from rebound off apron",
    discussion_notes:
      "• Dump rate is SLOW. The driver controls the gate. Operator-paver may also control hopper-fold timing.\n• No laborer within 6 feet of the hopper apron during a dump. Period.\n• Long pants, leather boots — even on the hottest day. Sneakers and shorts have no place on a paving train.\n• Eye protection (safety glasses minimum, face shield preferred for screed operator).\n• Truck driver verifies parking brake AND wheels chocked if the slope is more than a few degrees. A rolling truck during a dump is a fatality risk.\n• Spotter signals the truck to STOP before the dump, not during. Once flowing, no further signals — let the dump complete.\n• If hot mix hits skin: cover with clean dry cloth. Do NOT try to remove it from the skin. ER immediately.\n• Sweep apron between trucks — caked material on the apron deflects the next splash.",
    references_cited:
      "OSHA 1926.95 · NAPA Paving Train SOP · MASCI Hot Mix Handling",
    action_items:
      "PPE for all transfer workers verified · 6-ft splash-zone clearance reinforced · Chock policy reviewed · Burn-response procedure rehearsed",
  },
  {
    key: "paving_night_fatigue",
    domain: "paving",
    title: "Night Paving — Fatigue, Lighting, and Decision Quality",
    category: "Hazard-Specific",
    severity: "serious_injury",
    role_context: ["paver_operator", "roller_operator", "driver", "lead", "rake_crew"],
    incident_pattern:
      "Night paving incidents are not random — they cluster between 2 a.m. and 4 a.m. The crew has been on their feet 8 hours, ate at 11 p.m., and their decision-quality is measurably impaired by then. The operator misjudges a roller reverse. The laborer steps into the wrong zone. The driver backs into a fixed object. Compounding the fatigue is the lighting cone problem: balloon lights on the paver throw 30 feet of bright, and the public on the next highway lane sees only a halo. Workers walking outside the lit zone are invisible. Add cold rain at 3 a.m. and the failure rate doubles. The pattern is preventable with disciplined break rotation, distributed lighting, and a hard stop at 5 a.m. for any non-emergency work.",
    hazards_reviewed:
      "Fatigue-induced equipment-operator error · Worker in unlit zone struck by equipment or vehicle · Crash on shift drive home · Cold/wet exposure compounding fatigue · Stimulant-overuse impairment (energy drinks, caffeine) · Public-driver inattention at night",
    discussion_notes:
      "• Mandatory break rotation every 2 hours. Sit, hydrate, eat. Foreman enforces.\n• Distributed lighting — not just at the paver. Light the rake zone, the truck-pull-in zone, the cone-tender position.\n• Class 3 hi-vis (not Class 2) for night. Reflective tape on legs and arms.\n• No more than ONE energy drink per night. Stimulant crash at 4 a.m. is worse than no stimulant.\n• Foreman watches each crew member for slowed reactions, irritability, glazed eyes — signs of dangerous fatigue. Send them to the truck if needed.\n• Drive-home risk is real. If someone is dragging, they don't drive home. Get them a ride, get them a hotel, get them on a couch.\n• Hard stop time. If the job isn't done by then, it isn't done. Quality and lives both degrade after 12 hours.\n• Cold/wet adds 30% to fatigue load. Plan for it.\n• Public traffic at night drives WORSE than during the day. Treat every intrusion as imminent.",
    references_cited:
      "NIOSH Total Worker Health · CDC Fatigue Studies · MUTCD Part 6 Night · MASCI Night Paving SOP",
    action_items:
      "Break rotation enforced · Distributed lighting verified · Class 3 hi-vis required · Drive-home contingency discussed · Hard-stop time set",
  },
  {
    key: "paving_stringline_trip",
    domain: "paving",
    title: "Stringline & Form Stake Trip Hazards",
    category: "Hazard-Specific",
    severity: "lost_time",
    role_context: ["lead", "rake_crew", "surveyor"],
    incident_pattern:
      "Stringline trips are the most common lost-time injury in paving operations and the easiest one to dismiss. The pattern: a laborer walking between the paver and the truck steps over the stringline once, twice, then misses on the third — catches a toe and goes down hard. Form stakes set 18 inches apart in a curb-and-gutter pour become a forest of trip hazards once dark or once the worker is fatigued. The injury is usually ankle, knee, or wrist when they catch themselves. Same-level falls are the highest-frequency injury type in heavy civil construction overall, and stringlines specifically generate a disproportionate share. The fix is small but real — color-flag every line, light every stake, route walking paths around the layout, not through it.",
    hazards_reviewed:
      "Trip over stringline at ground level · Trip over form stake in curb-gutter layout · Twisted ankle / knee · Wrist fracture on catch-fall · Tool drop onto pavement during fall · Slip on freshly-laid mat during scramble",
    discussion_notes:
      "• Stringline gets a high-vis flag every 10 feet. Not optional.\n• Form stakes get a fluorescent cap or strip — visible at night and in dust.\n• Define a walking path around the layout, not through it. Tape it off if needed.\n• Tool belts and pouches secured — a swinging tool catches lines too.\n• Don't carry materials AND walk through the layout. Two trips is better than one fall.\n• Night work compounds this — add cone-mounted lights or LED strings along the layout.\n• If you trip and catch yourself, report it — even if you 'feel fine.' Strains and sprains become injuries 12 hours later.\n• Layout crew walks the area at the end of their shift and pulls anything unnecessary. Don't leave forests of stakes overnight.",
    references_cited:
      "OSHA 1926.500 (slips/trips) · NAPA Layout Safety · MASCI Paving SOP",
    action_items:
      "Stringline flagging verified · Form stake caps issued · Walking path defined · Near-miss reporting culture reinforced",
  },
];
