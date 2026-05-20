// Domain: concrete · iter261 Phase H Batch 2 · 12 uplifted

export const TOPICS_CONCRETE = [
  {
    key: "drilled_shaft",
    domain: "concrete",
    title: "Drilled Shaft / Caisson Operations",
    category: "Hazard-Specific",
    severity: "fatal_risk",
    incident_pattern:
      "Drilled-shaft fatalities split between two patterns. First — an open shaft left uncovered while the crew breaks for lunch, or partially barricaded with caution tape only, and a worker walks through and falls in. A 20-foot drop into wet slurry is unsurvivable without immediate rescue. Second — the Kelly bar or rebar cage swinging into ground crew during placement. The rig operator focuses on the hole, the crew focuses on the cage, and someone steps into the swing arc to make a final tie. The fix is rigid: shafts covered or hard-barricaded the moment the bit comes out, swing radius marked on the ground, and only one signal person at the rig.",
    hazards_reviewed:
      "Falls into open shaft · Cave-in of shaft sidewall · Struck-by drill stem / Kelly bar · Engulfment from collapsing slurry/casing · Crane / rig tipping · Suspended load swing",
    discussion_notes:
      "• Open shafts ALWAYS covered or hard-barricaded; never left open and unattended — including during lunch.\n• Set ground crew clear of swing radius of drill rig. Marked on the ground.\n• Workers stay outside reach of suspended drill stem and casing.\n• Slurry handling — chemical PPE, splash protection, eyewash within 25 ft.\n• Trained signal person for crane support; certified rigger for rebar cages and casings.\n• Trip hazards from rebar, hoses, slurry lines kept controlled.",
    references_cited:
      "OSHA 1926 Subpart P (excavation) · OSHA 1926 Subpart CC (cranes) · DFI Drilled Shaft Safety",
    action_items:
      "Open shafts covered/barricaded · Swing radius marked · Signal person designated · Slurry PPE staged",
  },
  {
    key: "saw_cutting",
    domain: "concrete",
    title: "Pavement Saw Cutting",
    category: "Tool / Equipment Specific",
    severity: "serious_injury",
    incident_pattern:
      "Saw-cutting incidents are dominated by two issues: silica exposure that doesn't hurt until 10 years later, and blade kickback in real time. The kickback pattern is consistent — operator pushes the saw into a hard spot too fast, the blade binds, the saw jumps back at the legs. Steel-toed boots stop the saw body; nothing stops a 14-inch wet blade catching a thigh. Second-most-common is operating downwind of the cut without respiratory protection 'because the water spray was on' — but if the spray nozzles are clogged or the water tank is low, the silica plume is invisible at the operator's face. The fix is dry-fitting the cut line, two-handed grip, and respiratory protection as backup whenever water is the primary control.",
    hazards_reviewed:
      "Respirable silica · Cuts / amputations from blade · Kickback · Noise · Heat / hot blade · Struck-by passing traffic · Slurry contamination",
    discussion_notes:
      "• Wet cut whenever possible — water suppression is OSHA Table 1 control for silica.\n• When dry cut required: HEPA vacuum AND respiratory protection.\n• Inspect blade before each use; dispose of cracked or chipped blades.\n• Two-handed grip; no overreach; firm footing. Watch for kickback when the cut binds.\n• Hearing protection — pavement saws routinely exceed 100 dBA.\n• Slurry: contain it; don't let it run into storm drain (NPDES violation).\n• Eye + face protection from flying chips.",
    references_cited:
      "OSHA 1926.1153 (Silica Table 1) · OSHA 1926.300 · OSHA 1926.95",
    action_items:
      "Wet-cut equipment ready · Respirator if dry · Slurry containment · Hearing & face PPE · Blade inspected",
  },
  {
    key: "curb_gutter",
    domain: "concrete",
    title: "Curb & Gutter Operations",
    category: "Hazard-Specific",
    severity: "lost_time",
    incident_pattern:
      "Curb-and-gutter injuries are usually back, knee, and hand — the slow-burn kind that ends careers without ever showing up on an incident log. Hand-finishers spend 6-8 hours bent over fresh concrete, chemical burns build up from wet concrete contact through cotton gloves, and the next morning the hands are cracked and bleeding. Pattern fatality risk is lower than other concrete domains but the lifetime injury cost is the highest. The struck-by pattern that DOES kill curb crews is the slip-form machine — operator misjudges the pinch zone around the auger or screed and a finisher reaches in to fix a flaw with the machine still moving. The fix is waterproof gloves and boots, no reaching into a running slip-form, and rotating crew every couple hours to reduce the bend-and-finish overuse.",
    hazards_reviewed:
      "Slip-form machine pinch points · Hot/wet concrete contact · Repetitive bending and lifting · Struck-by passing traffic · Silica from sawing finished concrete · Skin chemical burns",
    discussion_notes:
      "• Workers stay outside slip-form machine no-go zone — typical 6 ft buffer.\n• Hand-finishing crews wear waterproof gloves and boots; rinse skin contact immediately.\n• Lift / move forms with proper body mechanics — keep load close, knees bent.\n• Edge work near live traffic = positive protection (drum line minimum, barrier preferred).\n• Joint sawing follows silica controls (Table 1).\n• Dispose of waste concrete properly; no dumping into storm drains.\n• Rotate hand-finishers every 2 hours — overuse is the long injury.",
    references_cited:
      "OSHA 1926 Subpart Q · OSHA 1926.1153 · NIOSH Concrete Worker Bulletin",
    action_items:
      "Waterproof PPE issued · No-go zone marked · Lifting plan briefed · Silica Table 1 controls in place · Finisher rotation set",
  },
  {
    key: "mse_wall",
    domain: "concrete",
    title: "MSE Wall / Retaining Wall Construction",
    category: "Hazard-Specific",
    severity: "fatal_risk",
    incident_pattern:
      "MSE wall fatalities come from two sources: panel drops during placement and wall-toe collapse from improper compaction setback. The panel drop pattern — a 2-ton precast panel suspended by the crane, tag lines partially deployed, a worker steps in to guide it home, the wind catches the face. The panel swings 4 feet, pins the worker against the soldier pile. Wall-toe collapse pattern — compaction equipment running too close to a green wall (loose backfill, panels not yet stitched to soil reinforcement), the toe shifts outward, and the wall begins to fail upward. The crew on top is the at-risk population. Fix is the engineer's drawings, treated as gospel: compaction setbacks, lift heights, panel stitching sequence.",
    hazards_reviewed:
      "Falls from elevated panels · Struck-by panel during placement · Pinch / crush during reinforcement strap install · Backfill compaction edge instability · Material handling strains",
    discussion_notes:
      "• Tag lines control panel rotation during placement. Both lines, both hands, both sides.\n• Workers behind panels protected from struck-by during set; outside swing radius.\n• Tie-off required when working at edges 6 ft+; guardrails installed as wall height grows.\n• Compaction equipment kept set distance from wall face per design. NO improvisation.\n• Reinforcement straps unrolled with tools, not bare hands.\n• Wall toe stable before next lift placed.",
    references_cited:
      "OSHA 1926 Subpart M · AASHTO LRFD Bridge Design · NCMA Design Manual",
    action_items:
      "Tag lines staged · Fall protection above 6 ft · Compaction setbacks marked · Lifting plan briefed",
  },
  {
    key: "concrete_silica",
    domain: "concrete",
    title: "Concrete Operations & Respirable Silica",
    category: "Hazard-Specific",
    severity: "serious_injury",
    incident_pattern:
      "Silica is the slow killer of concrete crews. Workers spend careers cutting, grinding, chipping, jackhammering — none of which feels dangerous in the moment. The dust looks like normal job-site dust. The lung damage builds over decades. By the time silicosis or lung cancer shows up, the worker is in their 50s and the exposure was the 80s and 90s. Compounding pattern: the wet-cut nozzle was 'mostly working' all summer; the HEPA vacuum hose was disconnected for a week; the respirator was hanging on a hook but not worn because 'it gets sweaty.' OSHA Table 1 spelled out the controls for every task. The shortcut is the silicosis. Wet, vacuum, respire — in that order.",
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
    domain: "concrete",
    title: "Concrete Pumping",
    category: "Tool / Equipment Specific",
    severity: "fatal_risk",
    incident_pattern:
      "Concrete-pump fatalities come from boom contact with overhead power and from line whip after a blockage clears violently. The overhead pattern: operator extends the boom on a residential job, doesn't fully check above, contacts a 13kV service drop. Electrocution travels through the pump truck. The whole crew within 30 feet is at risk from step potential. The line-whip pattern: a blockage builds, operator reverses to clear, then forwards too aggressively. The plug shoots out, the whole boom whips downward in a recoil arc, and the hose-end worker is in the swing zone. 100% of these fatalities are preventable through clearance verification + slow blockage clearing + nobody in the boom swing arc.",
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
    domain: "concrete",
    title: "Formwork Safety",
    category: "Procedure / SOP",
    severity: "fatal_risk",
    incident_pattern:
      "Formwork-collapse fatalities are catastrophic and multi-victim. The pattern: a deep beam form or a slab form is pre-poured for crew convenience, the design loads were not verified for the actual concrete head, and the pour starts. At the moment fresh concrete reaches a critical depth, the bracing fails — usually one shore or one tie giving way and the rest cascading. The pour is happening, workers are on the deck or under the deck, and the collapse takes the form, the concrete, and the workers down together. Industry-wide, formwork collapse is one of the highest-fatality single events because there is no escape time. The fix is the engineer's drawings, treated as inviolable, pre-pour competent-person inspection of every brace and tie, and no deviations without re-engineering.",
    hazards_reviewed:
      "Form collapse · Falls from formwork · Struck-by falling forms · Pinch / crush during stripping · Rebar impalement · Hardware failure under load",
    discussion_notes:
      "• Formwork designed by qualified person for the load (concrete + workers + equipment).\n• No deviation from drawings without engineer approval. NONE.\n• Inspect formwork before pour — every brace, every tie, every shore. Competent person signs off.\n• Workers tie off when working at form height 6 ft+.\n• Stripping: only after concrete reaches required strength; controlled drop zones.\n• Rebar caps on all exposed ends; no walking on top mat without planking.",
    references_cited:
      "OSHA 1926.703 · ACI 347 Formwork · OSHA 1926.703(b)",
    action_items:
      "Form drawings on site · Pre-pour inspection logged · Strip strength verified · Rebar caps in place",
  },
  {
    key: "bridge_deck_pour",
    domain: "concrete",
    title: "Bridge Deck Pours",
    category: "Hazard-Specific",
    severity: "fatal_risk",
    incident_pattern:
      "Bridge-deck fatalities are dominated by edge falls. A deck pour involves long hours, fatigue, heat, and a perimeter that the crew has been working near all day. By hour 8, edge awareness slips, a worker steps too close to the fascia, and the fall is 40+ feet onto rocks, equipment, or moving traffic below. The other fatal pattern is falls THROUGH the deck — deck-form openings for utility penetrations or expansion joints left uncovered during the pour. A worker walking the wet deck steps where the form isn't. Both patterns share a fix: perimeter guardrail or full personal-fall-arrest before any deck work begins, every opening covered or barricaded, and rotation to manage fatigue on multi-hour pours.",
    hazards_reviewed:
      "Falls over edge · Falls through deck openings · Struck-by finishing machine · Concrete spray from pump · Rebar trip / impalement · Heat stress on long pours",
    discussion_notes:
      "• Perimeter guardrail or full PFAS before any deck work begins.\n• Cover or barricade every opening. No exceptions.\n• Finishing machine no-go zones marked; operator and crew comms verified.\n• Heat stress plan in effect — water, ice, shade, rotation.\n• Crew briefing: pour sequence, dump location, comms with mixer drivers.\n• Edge protection at fascia stays in place until parapet poured.",
    references_cited:
      "OSHA 1926 Subpart M · OSHA 1926.502 · AASHTO Bridge Construction",
    action_items:
      "Edge protection in place · Openings covered · Heat plan active · Pour sequence briefed",
  },
  {
    key: "curing_sealing",
    domain: "concrete",
    title: "Curing & Sealing Operations",
    category: "Hazard-Specific",
    severity: "lost_time",
    incident_pattern:
      "Curing-and-sealing incidents are mostly chemical exposure and slip hazards. The pattern is a worker spraying a solvent-based cure on a hot day, no respirator, applicator drift in the wind, headache by lunch, dizziness by 2 p.m. The exposure isn't fatal but the headache crew goes home impaired and the drive home gets dangerous. Second pattern is solvent fire — a worker on the rinse step uses a solvent-based cleaner near a hot exhaust or a torch on the next deck, vapors find ignition, flash fire. The fix is the SDS — read it, follow the PPE, and respect the wind. Solvent-based cures aren't for shorts-and-t-shirt weather.",
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
    domain: "concrete",
    title: "Cold Weather Concrete Operations",
    category: "Hazard-Specific",
    severity: "lost_time",
    incident_pattern:
      "Cold-weather concrete operations move CO poisoning from 'theoretical' to 'this winter.' The pattern: a crew sets up heated enclosures around a pour to protect the concrete from freezing, the heaters are propane direct-fired without continuous CO monitoring, and within 2-3 hours the CO inside the enclosure climbs to dangerous levels. The crew working inside doesn't notice — CO has no smell — and the first symptoms are headache and confusion. By the time someone steps outside for a break, they're already impaired. Multi-person fatalities have happened from this exact pattern. The fix is mandatory: indirect-fired heaters with combustion venting outside the enclosure, OR continuous CO monitoring on every direct-fired setup, OR the enclosure stays open.",
    hazards_reviewed:
      "Cold stress / hypothermia · Burns from heated water / steam · CO from heaters in enclosures · Slips on icy surfaces · Frozen-aggregate kickbacks from chute",
    discussion_notes:
      "• Layered clothing, insulated waterproof gloves and boots; cover head and neck.\n• Heated enclosures: ONLY direct-fired heaters with continuous CO monitoring; OR indirect-fired heaters venting outside.\n• Warming areas (heated trailer / shed) within 100 ft of crew.\n• Salt / sand walking surfaces; flag icy areas.\n• Hot water for mix: 140°F max at point of use; gloves required.\n• Buddy system — frostbite first signs are subtle. CO impairment too.",
    references_cited:
      "OSHA Cold Stress Bulletin · ACI 306 Cold-Weather Concreting",
    action_items:
      "Cold-weather PPE issued · CO monitoring set · Walking surfaces de-iced · Warming area available",
  },
  {
    key: "diamond_grinding",
    domain: "concrete",
    title: "Diamond Grinding & Grooving",
    category: "Tool / Equipment Specific",
    severity: "serious_injury",
    incident_pattern:
      "Diamond-grinding incidents share a profile with milling — long-term silica exposure dominates, with acute injuries from spray and blade contact secondary. The grinder runs water on the blade, but on long shifts the water tank empties or a nozzle clogs and the silica plume rises. The operator on the rig doesn't see it from the cab. The follow-vehicle and the spotter behind the rig get the worst of it because they're at plume height. Compounding pattern is slurry slip — workers in dress boots not rated for wet concrete walk through slurry, lose footing, end up under or next to the rig. Fix is hourly nozzle checks, dedicated water-tender, and slurry vacuum to keep walking surfaces clear.",
    hazards_reviewed:
      "Respirable silica · Slurry slips · Hot blade contact · Noise · Struck-by passing traffic · Eye injury from chip / spray",
    discussion_notes:
      "• Wet grind for silica control (Table 1) — blade water on continuously.\n• Vacuum slurry to prevent storm drain contamination AND to prevent slip hazard.\n• Hearing protection — process exceeds 95 dBA.\n• Eye / face protection from chips and spray.\n• Operator stays clear of blade; cool blade before any maintenance.\n• Slurry disposed at approved location.\n• Hourly nozzle inspection on long shifts; water tank refill before empty.",
    references_cited:
      "OSHA 1926.1153 (Silica Table 1) · ACPA Grinding Best Practices",
    action_items:
      "Water spray verified · Slurry containment · Hearing & eye PPE · Disposal location approved",
  },
  {
    key: "sound_wall",
    domain: "concrete",
    title: "Sound Wall / Noise Wall Construction",
    category: "Hazard-Specific",
    severity: "serious_injury",
    incident_pattern:
      "Sound-wall incidents come from wind catching panels during placement. A precast noise-wall panel is 18-25 feet tall and acts as a sail. Wind picks up, the panel swings the load far beyond the operator's expectation, and the ground crew gets caught between the panel and a column or barrier. The other recurring pattern is live-traffic interface — sound walls are built right next to highways by definition, and the ground crew positions itself between the wall and the lane. A vehicle leaving the lane has nowhere to go but into the work zone. The fix is wind-speed monitoring with a hard threshold, tag lines properly deployed, and positive protection between work and travel lane.",
    hazards_reviewed:
      "Falls from height · Struck-by panel during placement · Crush during column erection · Wind catching panels · Crane tipping · Live traffic adjacent",
    discussion_notes:
      "• Tag lines control panel rotation; workers outside swing radius.\n• Wind speed monitoring — stop placement at mfr / engineer-specified threshold.\n• Tie-off above 6 ft; perimeter guardrail / catch system as wall grows.\n• Crane signal person designated and certified.\n• Live traffic side: positive protection (barrier) between work and travel lane.\n• Foundations cured to design strength before column / panel placement.",
    references_cited:
      "OSHA 1926 Subpart M · OSHA 1926 Subpart CC · AASHTO LRFD",
    action_items:
      "Tag lines staged · Wind monitor on site · Fall protection 6 ft+ · Signal person designated",
  },
];
