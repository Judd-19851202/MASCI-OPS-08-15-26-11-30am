// MASCI Safety Meeting topic library — prefill content for heavy civil
// highway/utility construction. Each entry populates the meeting form's
// topic title, category, hazards reviewed, discussion notes, references,
// and action items. Every field remains fully editable after prefill.

export const TOPIC_LIBRARY = [
  // ============================================================
  // EARTHWORK / EXCAVATION / UNDERGROUND
  // ============================================================
  {
    key: "trenching_shoring",
    title: "Trenching, Shoring & Excavation Safety",
    category: "Hazard-Specific",
    hazards_reviewed:
      "Cave-in / collapse · Engulfment · Falls into excavation · Struck-by spoil or material · Hazardous atmospheres in trench · Water accumulation · Underground utilities · Equipment falling into trench",
    discussion_notes:
      "• Competent person must inspect every excavation daily, after rain, and after any change in conditions.\n• Protective system required in any trench 5 ft or deeper: slope, shore, shield, or bench.\n• Spoil pile and equipment kept ≥2 ft back from edge.\n• Ladder, ramp, or steps required within 25 ft of any worker in a trench 4 ft+ deep.\n• Atmospheric testing required for trenches >4 ft deep where hazardous atmosphere is suspected.\n• Crews stay clear of equipment swing radius and out from under suspended loads.\n• No one enters a trench without protective system in place — period.",
    references_cited:
      "OSHA 29 CFR 1926 Subpart P · OSHA 1926.651 · OSHA 1926.652 · OSHA Trenching Quick Card",
    action_items:
      "Confirm competent person on site daily · Verify protective system matches soil type · Check 811 ticket valid before next dig · Daily inspection logged · Rescue plan reviewed",
  },
  {
    key: "underground_utilities",
    title: "Underground Utilities / 811 Locates",
    category: "Procedure / SOP",
    hazards_reviewed:
      "Utility strike (gas, electric, fiber, water, sewer) · Explosion / fire · Electrocution · Service outage · Worker injury from energized line · Spoils contaminating mark-outs",
    discussion_notes:
      "• Call 811 (or state equivalent) at minimum 2-3 business days before digging.\n• Verify ticket is valid AND unexpired before any dig — re-ticket if expired or extended.\n• Visually verify ALL marks before breaking ground; missing marks = stop, recall.\n• Hand dig within 24 inches of any marked utility (tolerance zone).\n• Treat every unmarked line as live until proven otherwise.\n• If a line is struck: clear area, evacuate uphill/upwind for gas, do NOT operate switches/phones near gas, call utility AND 911.\n• Daylight critical utilities (vacuum or hand) before mechanical digging near them.",
    references_cited:
      "OSHA 1926.651(b) · Common Ground Alliance Best Practices · State 811 program (Sunshine 811 / 811 USA / etc.)",
    action_items:
      "Verify all 811 tickets onsite are current · Mark-outs photographed before dig · Hand-dig tolerance zone enforced · Spotter assigned for mechanical digging near marks",
  },
  {
    key: "earthmoving_equipment",
    title: "Earthmoving Equipment & Heavy Iron",
    category: "Tool / Equipment Specific",
    hazards_reviewed:
      "Struck-by equipment · Run-over while spotting · Caught between equipment and fixed object · Rollover · Backing accidents · Swing radius incidents · Equipment falling into trench · Pinch points",
    discussion_notes:
      "• Pre-shift walkaround on every piece of iron — check fluids, tires, lights, alarms, fire extinguisher.\n• Seat belts worn at all times — no exceptions.\n• Backup alarms operational; spotters used in congested areas and any time visibility is restricted.\n• Establish and enforce no-go zones around equipment swing radius.\n• Workers on the ground wear hi-vis and stay in operator's line of sight.\n• Eye contact + thumbs up rule before operator moves equipment near workers.\n• Park on level ground, blade/bucket down, parking brake set, key removed when leaving cab.",
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
      "OSHA 1926.601(b)(4) · OSHA Backover Hazards Safety Bulletin",
    action_items:
      "Designated spotters identified per crew · Spotter PPE verified · Hand signals reviewed · Communication plan in place",
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
      "• Approved Traffic Control Plan (TCP) on site and matches field conditions.\n• Setup from upstream to downstream; takedown reverse order — never face oncoming traffic.\n• Buffer / taper lengths matched to posted speed.\n• Devices (cones, drums, barricades) clean, retroreflective, properly spaced.\n• Internal traffic-control plan separates workers from equipment inside the zone.\n• Night work: lighting min 5 fc, all workers in Class 3 hi-vis with retroreflective bands.\n• Public traffic exposure controlled by positive protection where speed/volume warrant.",
    references_cited:
      "MUTCD Part 6 · FHWA Work Zone Safety · OSHA 1926 Subpart G · ATSSA Standards",
    action_items:
      "TCP onsite and signed · Devices match plan · Internal traffic plan briefed · Night lighting verified · Class 3 hi-vis confirmed for all crew",
  },
  {
    key: "flaggers",
    title: "Flaggers & Public Traffic Exposure",
    category: "Procedure / SOP",
    hazards_reviewed:
      "Struck by passing motorist · Distracted / impaired drivers · Driver running stop paddle · Lone-worker exposure · Sun glare blinding flagger · Heat / cold stress on long stations",
    discussion_notes:
      "• Flagger is a certified position — current cert card on person.\n• Stop paddle, not a flag, in all paid traffic-control work.\n• Flagger station has clear escape route — never trapped between barrier and traffic.\n• Hi-vis Class 3 day, hi-vis with retro at night.\n• Two-way radio comms with crew and other flaggers.\n• Rotate flaggers every 2 hours in heat; provide water, shade, and seating between rotations.\n• Position so the flagger is visible to oncoming traffic for the full stopping sight distance.",
    references_cited:
      "MUTCD Part 6E · ATSSA Flagger Cert · FDOT/State Flagger requirements",
    action_items:
      "Flagger certs verified · Stop paddles in good condition · Escape route walked · Rotation schedule posted · Comms tested",
  },
  {
    key: "live_traffic",
    title: "Live Traffic Exposure / Struck-By",
    category: "Hazard-Specific",
    hazards_reviewed:
      "Worker struck by vehicle entering work zone · Distracted driver · Speeding · Vehicle intrusion through tapers · Limited reaction time during night work · Lone worker exposure",
    discussion_notes:
      "• Highest fatality cause in our industry — treat every passing vehicle as a potential intrusion.\n• Always maintain situational awareness: keep one eye on traffic when working near open lanes.\n• Stand on the shielded side of barrier or equipment whenever possible.\n• Never cross open travel lanes on foot — use approved crossing points.\n• Work-zone intrusion alarms / shadow vehicles encouraged where speed and volume warrant.\n• Stop work, get behind protection, and call dispatch if a vehicle penetrates the buffer.",
    references_cited:
      "FHWA Work Zone Safety · OSHA 1926.201 · MUTCD Part 6 · NIOSH Topic Page – Highway Workers",
    action_items:
      "Buffer integrity verified · Shadow vehicle in place where applicable · Workers briefed on escape routes · Intrusion response reviewed",
  },
  {
    key: "mot_moving_trucks",
    title: "MOT Placement from Moving Trucks",
    category: "Procedure / SOP",
    hazards_reviewed:
      "Falls from moving truck · Struck-by passing vehicle · Loss of grip / footing · Improper anchor point for tie-off · Communication breakdown driver/worker · Heat / fatigue on long deployments",
    discussion_notes:
      "• Workers on the back of a moving MOT truck must be 100% tied off to a rated, engineered anchor.\n• No improvised tie-off — guardrails and toolboxes are NOT anchors.\n• Truck speed during placement: 5 mph or less.\n• Driver and workers maintain constant communication via radio or hand signals.\n• No mounting/dismounting while truck is moving.\n• Workers never ride on equipment unless designated platform is provided.",
    references_cited:
      "OSHA 1926.501(b) · OSHA 1926.502 · MUTCD Part 6",
    action_items:
      "Harnesses inspected · Anchor points verified · Driver / crew comms tested · Speed limit enforced",
  },

  // ============================================================
  // CONCRETE / PAVING / HOT WORK
  // ============================================================
  {
    key: "concrete_silica",
    title: "Concrete Operations & Respirable Silica",
    category: "Hazard-Specific",
    hazards_reviewed:
      "Respirable crystalline silica (silicosis, lung cancer) · Caustic / chemical burns from wet concrete · Skin / eye irritation · Rebar impalement · Forms collapse · Lifting injuries from rebar / forms",
    discussion_notes:
      "• OSHA Table 1 — match every dust-generating task to its specified engineered control (water OR vacuum).\n• Respiratory protection (P100 or supplied air) required when controls are insufficient or task isn't on Table 1.\n• Wear waterproof gloves, boots, sleeves when handling wet concrete; rinse skin contact immediately.\n• Rebar caps on every exposed end at trip height or below.\n• Forms inspected and braced before pour; designated competent person for forming.\n• Eye protection mandatory during cutting, grinding, sawing, chipping.",
    references_cited:
      "OSHA 1926.1153 (Silica) · OSHA Silica in Construction · OSHA 1926.700 Subpart Q · NIOSH Silica Bulletin",
    action_items:
      "Table 1 controls in place · Water / vacuum systems checked · Respirators fit-tested · Rebar caps installed · SDS for concrete chemicals on site",
  },
  {
    key: "asphalt_paving",
    title: "Hot Asphalt & Paving Operations",
    category: "Hazard-Specific",
    hazards_reviewed:
      "Severe burns from hot mix (300°F+) · Burns from tack/oil/fuel · Fume inhalation · Struck-by paver, roller, truck · Caught between roller and pavement edge · Heat stress · Skin irritation",
    discussion_notes:
      "• Long sleeves, long pants, gloves rated for hot asphalt, leather boots — even in hot weather.\n• No skin contact with hot mix; raking/lute work upwind of fume plume when possible.\n• Paver and roller no-go zones marked; spotters used where workers approach machinery.\n• Truck driver acknowledges crew before dumping; positive comms with screed operator.\n• Fuel and tack handling: bonded containers, no smoking, fire extinguisher within 50 ft.\n• Heat stress program in effect — water, rest, shade rotation.",
    references_cited:
      "OSHA 1926.95 PPE · NIOSH Asphalt Bulletin · OSHA Heat Illness · NAPA Worker Safety",
    action_items:
      "Burn-rated PPE issued · Paver / roller no-go zones marked · Heat stress monitoring active · Fire extinguisher onsite · Tack/fuel storage compliant",
  },
  {
    key: "hot_work",
    title: "Hot Work — Welding, Cutting, Grinding",
    category: "Procedure / SOP",
    hazards_reviewed:
      "Fire / explosion · Burns · UV / IR exposure to eyes (arc flash) · Welding fume inhalation · Hot slag igniting combustibles · Compressed gas cylinder rupture",
    discussion_notes:
      "• Hot Work Permit required and on site for any cutting, welding, grinding outside designated shop area.\n• Fire watch posted with extinguisher during work AND for 30 minutes after.\n• Combustibles within 35 ft removed or shielded with welding blankets.\n• Cylinders chained upright, caps on when not in use, oxygen and fuel separated by 20 ft or 5-ft non-combustible barrier.\n• Eye protection: shade matched to amperage; bystanders shielded by curtains or screens.\n• Ventilation or supplied air for galvanized, cadmium, or coated metal cutting.",
    references_cited:
      "OSHA 1926 Subpart J · OSHA 1926.352 · NFPA 51B Hot Work · ANSI Z49.1",
    action_items:
      "Hot work permit signed · Fire watch assigned · Combustibles cleared/shielded · Extinguisher staged · Cylinders secured",
  },

  // ============================================================
  // FALL PROTECTION / LADDERS / ELEVATED
  // ============================================================
  {
    key: "fall_protection",
    title: "Fall Protection — General",
    category: "Hazard-Specific",
    hazards_reviewed:
      "Falls from elevation · Falls into excavations · Falls through openings · Improper anchor failure · Struck by falling tools / debris · Suspension trauma after a fall",
    discussion_notes:
      "• 100% tie-off above 6 ft in construction.\n• Anchor points rated 5,000 lb minimum or engineered system.\n• Inspect harness, lanyard, SRL before EVERY use — no abrasion, cuts, deployed indicators, corrosion, missing labels.\n• Calculate fall clearance — anchor + lanyard + free fall + deceleration + safety factor.\n• Rescue plan in place; suspended worker requires rescue within 15 minutes (suspension trauma).\n• Tools tethered or in zipped pouches when working at height.\n• Guardrails, covers, barricades on every hole and edge.",
    references_cited:
      "OSHA 1926 Subpart M · OSHA 1926.501 · ANSI Z359 · OSHA Fall Protection eTool",
    action_items:
      "Harnesses inspected · Anchor points identified · Rescue plan briefed · Holes covered/barricaded · Tools tethered",
  },
  {
    key: "ladder_safety",
    title: "Ladder Safety",
    category: "Tool / Equipment Specific",
    hazards_reviewed:
      "Falls from ladder · Ladder slide-out · Tipping · Electrocution from contact with overhead lines (metal ladder) · Overreaching · Damaged rungs / rails",
    discussion_notes:
      "• Inspect every ladder before use — no cracks, bent rails, missing feet, paint covering defects.\n• 4:1 angle rule for extension ladders (1 ft out for every 4 ft up).\n• Three points of contact at all times — never carry tools up; hoist in a bucket or wear belt.\n• Extend 3 ft above landing point, secured at top.\n• Never the top two rungs of a stepladder; never the top of any extension ladder.\n• Non-conductive (fiberglass) only when working near electrical.\n• Don't reach beyond the side rails — get down and move the ladder.",
    references_cited:
      "OSHA 1926 Subpart X · OSHA 1926.1053 · ANSI A14",
    action_items:
      "All ladders inspected · Defective ladders tagged out · Anchor / tie-off where 6 ft+ exposure · Fiberglass for electrical work",
  },

  // ============================================================
  // ELECTRICAL
  // ============================================================
  {
    key: "electrical_safety",
    title: "Electrical Safety & Energized Equipment",
    category: "Hazard-Specific",
    hazards_reviewed:
      "Electrocution · Arc flash / arc blast · Burns · Fall caused by shock · Fire from damaged cords or panels · Energized equipment unexpectedly starting",
    discussion_notes:
      "• GFCI on every 120V circuit on the job — temp power, generators, extension cords.\n• Inspect cords daily — no damaged jackets, exposed conductors, missing ground pins.\n• Lockout / Tagout for any work on electrical systems — verified de-energized with a tester.\n• Maintain 10 ft minimum approach to overhead lines (more for higher voltage).\n• Panels, boxes, and disconnects must be covered and labeled.\n• Only qualified persons work on energized equipment and only when de-energizing isn't feasible.",
    references_cited:
      "OSHA 1926 Subpart K · OSHA 1926.404 · NFPA 70E · OSHA LOTO 1910.147",
    action_items:
      "GFCI verified · Cords inspected · LOTO procedure followed · Overhead clearance maintained · Qualified-person status verified",
  },
  {
    key: "loto",
    title: "Lockout / Tagout (LOTO)",
    category: "Procedure / SOP",
    hazards_reviewed:
      "Unexpected startup / energization · Stored energy release (hydraulic, pneumatic, gravity, springs) · Multiple-energy-source incidents · Bypassing controls · Removing someone else's lock",
    discussion_notes:
      "• Identify EVERY energy source — electrical, hydraulic, pneumatic, gravity, thermal, chemical.\n• Notify affected employees, shut down using normal procedure, isolate, lock + tag, verify zero energy.\n• Each authorized worker applies their own personal lock — no shared locks.\n• Test for zero energy: start switch, gauges, manual operation as appropriate.\n• Removing your own lock = your responsibility. Removing someone else's requires the absent-employee removal procedure.\n• Group LOTO uses lockbox + master tag; everyone signs on, signs off.",
    references_cited:
      "OSHA 1910.147 · OSHA 1926 Subpart K · ANSI Z244.1",
    action_items:
      "LOTO procedure on site · Personal locks issued · Energy sources identified · Verification step trained",
  },

  // ============================================================
  // PPE / GENERAL
  // ============================================================
  {
    key: "ppe_general",
    title: "PPE — Daily Compliance Review",
    category: "Stretch & Flex",
    hazards_reviewed:
      "Head injury · Eye injury / foreign body · Hearing loss · Foot injury · Hand laceration · Crush injuries · Hi-vis non-compliance leading to struck-by",
    discussion_notes:
      "• Hard hat — Type II preferred for traffic / impact zones; replaced every 5 years or after impact.\n• Safety glasses with side shields — ANSI Z87 minimum, tinted only outdoors.\n• Hi-vis Class 2 day / Class 3 night for all roadway/highway work.\n• Steel or composite toe boots — no athletic shoes on site.\n• Cut-resistant gloves for sharp / abrasive work; chemical gloves for chemical work.\n• Hearing protection wherever noise exceeds 85 dBA TWA — that's most equipment work.\n• PPE must be inspected before use; damaged PPE is removed from service.",
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
      "OSHA General Duty Clause 5(a)(1) · MASCI Stop Work Policy · ANSI/ASSP Z10",
    action_items:
      "Stop Work poster visible · Crew acknowledged authority · Recent stop-work events reviewed · Reporting form available",
  },
  {
    key: "heat_stress",
    title: "Heat Stress / Hydration",
    category: "Hazard-Specific",
    hazards_reviewed:
      "Heat exhaustion · Heat stroke (medical emergency) · Dehydration · Reduced reaction time / impaired decision-making · Sunburn / UV exposure",
    discussion_notes:
      "• Water, rest, shade — the OSHA-NIOSH heat protocol.\n• 1 cup of water every 15-20 minutes during heavy work in heat.\n• Acclimatize new and returning workers — 20% workload day 1, increase 20% per day.\n• Buddy system — watch your partner for confusion, slurred speech, hot dry skin = heat stroke = 911.\n• Schedule heaviest work for cooler hours when feasible.\n• Heat index posted daily; protocol triggers at 80°F+ heat index.\n• Cool-down breaks in shade or AC every hour during high-heat days.",
    references_cited:
      "OSHA Heat Illness Campaign · NIOSH Criteria · OSHA-NIOSH Heat Tool",
    action_items:
      "Water and ice staged · Shade structure on site · Heat-index protocol posted · Acclimatization plan for new hires",
  },
  {
    key: "near_miss",
    title: "Near-Miss Reporting",
    category: "Procedure / SOP",
    hazards_reviewed:
      "Recurring near-misses leading to actual injury · Unreported hazards remaining in place · Trend data lost · Culture of silence",
    discussion_notes:
      "• A near-miss is a free lesson. Treat it like an injury you got lucky on.\n• Report any unsafe act, unsafe condition, or close call — same shift.\n• Anonymous reporting available; no retaliation.\n• MASCI tracks near-misses for trends — this is how we prevent the next incident.\n• Don't blame the worker; fix the condition or process.\n• Examples: dropped tool from height, vehicle intrusion that didn't strike, suspended load that swung wide, almost-trip-and-fall.",
    references_cited:
      "OSHA Voluntary Protection Program · ANSI Z10 · MASCI Near-Miss Procedure",
    action_items:
      "Near-miss form available · Reporting reviewed · Recent reports discussed · Corrective actions tracked",
  },
  {
    key: "stretch_flex",
    title: "Stretch & Flex / Daily Huddle",
    category: "Stretch & Flex",
    hazards_reviewed:
      "Strains and sprains · Soft-tissue injuries · Cold muscle injury · Repetitive motion · Slips/trips/falls during the first hour of shift",
    discussion_notes:
      "• 5-minute stretch routine before work — neck, shoulders, back, hips, hamstrings.\n• Walk through today's task list and identify anything new or unusual.\n• Confirm crew assignments and equipment for the shift.\n• Identify weather concerns (heat, cold, lightning, wind, rain).\n• Confirm everyone is fit for duty — no impairment, illness, or fatigue concerns.\n• Quick safety reminder relevant to today's work.",
    references_cited:
      "MASCI Daily Huddle SOP · NIOSH Ergonomics",
    action_items:
      "Stretch routine completed · Today's tasks briefed · Weather check · Fit-for-duty confirmed",
  },
];

export const CUSTOM_TOPIC_KEY = "__custom__";

export function findTopic(key) {
  return TOPIC_LIBRARY.find((t) => t.key === key);
}
