// Domain: electrical · iter261 Phase H Batch 4 · 4 uplifted

export const TOPICS_ELECTRICAL = [
  {
    key: "electrical_safety",
    domain: "electrical",
    title: "Electrical Safety & Energized Equipment",
    category: "Hazard-Specific",
    severity: "fatal_risk",
    incident_pattern:
      "Electrical fatalities on construction sites cluster around three recurring shortcuts. First — the extension cord with a missing ground pin used in a wet area because 'it's just for an hour.' Worker grabs a metal tool, becomes the path to ground, dies on a job-trailer step. Second — the panel work done 'live' because shutting down would inconvenience another trade. Arc flash blows when a screwdriver bridges two phases; worker dies of thermal injuries in the next 72 hours. Third — assumed-dead circuit. Worker walks up, doesn't test, touches a bus that someone else energized at the breaker. Every one of these is preventable by the same controls: GFCI on every 120V cord, no live work without a documented exception, and test-before-touch with a meter the worker personally trusts.",
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
    domain: "electrical",
    title: "Lockout / Tagout (LOTO)",
    category: "Procedure / SOP",
    severity: "fatal_risk",
    incident_pattern:
      "LOTO failures kill workers in one signature pattern: assumed energy state. Pattern one — a mechanic locks out the electrical disconnect but doesn't account for the hydraulic accumulator, the stored pressure releases when the line opens, and the boom drops on the worker underneath. Pattern two — a crew shares a lock or uses a 'one-lock-for-the-team' approach. One worker finishes their task, removes the lock, equipment energizes, the next worker is still inside the machine. Pattern three — someone removes a lock that isn't theirs because the original locker went home. Equipment energizes with the second-shift worker still in the danger zone. The fix is non-negotiable: every authorized worker applies a personal lock, every energy source isolated (electrical AND hydraulic AND pneumatic AND gravity AND springs), and zero-energy verification with a tester before touching anything.",
    hazards_reviewed:
      "Unexpected startup · Stored energy release (hydraulic, pneumatic, gravity, springs) · Multiple energy sources · Bypassing controls · Removing someone else's lock",
    discussion_notes:
      "• Identify EVERY energy source — electrical, hydraulic, pneumatic, gravity, thermal, chemical.\n• Notify affected employees, shut down using normal procedure, isolate, lock + tag, verify zero energy.\n• Each authorized worker applies their own personal lock — no shared locks.\n• Test for zero energy: start switch, gauges, manual operation as appropriate.\n• Removing your own lock = your responsibility. Removing someone else's requires absent-employee removal procedure.\n• Group LOTO uses lockbox + master tag; everyone signs on, signs off.",
    references_cited: "OSHA 1910.147 · OSHA 1926 Subpart K · ANSI Z244.1",
    action_items:
      "LOTO procedure on site · Personal locks issued · Energy sources identified · Verification step trained",
  },
  {
    key: "generator_temp_power",
    domain: "electrical",
    title: "Generator / Temporary Power Setup",
    category: "Tool / Equipment Specific",
    severity: "fatal_risk",
    incident_pattern:
      "Generator fatalities have two distinct profiles. Profile one is CO poisoning — generator placed too close to a tent, an open garage door, a partially enclosed trailer, or under the eave of a building. Exhaust accumulates, crew working nearby goes from headache to nausea to unconsciousness without realizing what's happening. Multi-victim deaths from this exact pattern happen every storm-cleanup season. Profile two is utility backfeed — generator wired into a panel without a transfer switch, lineman working on what they believe is a de-energized line gets killed because the generator pushed voltage back up the service drop. The fix on both: 20-foot minimum distance from any opening, never indoors or under a roof, transfer switch mandatory when feeding a panel, and GFCI on every outlet because most builder-grade gens are not internally GFCI-protected.",
    hazards_reviewed:
      "CO poisoning · Electrical shock · Fire / fuel spill · Backfeed onto utility lines · Generator overloading",
    discussion_notes:
      "• NEVER run a fuel-burning generator indoors or in any enclosed space — CO kills.\n• 20 ft minimum from buildings, vents, and air intakes.\n• Bond generator frame to ground rod where required.\n• GFCI on every 120V outlet — many gen outlets are not internally GFCI-protected.\n• Size circuits for the load; spread loads across phases.\n• If feeding a panel, use a transfer switch (no backfeeding through outlets).\n• Refuel only when cold; bonded fuel containers; no smoking.",
    references_cited: "OSHA 1926.405 · NFPA 70 (NEC) · NIOSH CO Bulletin",
    action_items:
      "Generator placement verified · Bonding/grounding in place · GFCI confirmed · Fuel handling area set up",
  },
  {
    key: "light_tower",
    domain: "electrical",
    title: "Light Tower Operations",
    category: "Tool / Equipment Specific",
    severity: "serious_injury",
    incident_pattern:
      "Light-tower incidents follow predictable scripts. The mast-up-into-a-line script: tower placed on a paving job at dusk, operator raises the mast without scanning overhead, mast clips a service drop, the tower frame energizes, ground worker leaning on it gets the transfer. The other script is the wind-tip — tower placed on soft shoulder gravel with outriggers extended but not cribbed, wind gust at 3 a.m. takes it sideways, mast comes down across a lane or onto a parked vehicle. CO from the generator section is a third pattern — tower parked under an overpass for night work, fumes pool under the deck, the crew downwind shows up symptomatic. The fix is the routine that nobody loves but works: outriggers cribbed, scan overhead before mast goes up, place 20 feet from anything enclosed.",
    hazards_reviewed:
      "Tipping during raise / lower · Overhead clearance contact · Burns from hot lights · CO from generator section · Electrical shock from damaged cords",
    discussion_notes:
      "• Place on stable level ground; outriggers fully extended.\n• Verify overhead clearance before raising mast.\n• Lock mast at full height before walking away.\n• Generator: refuel cold, bonded container, no smoking, 20 ft from buildings.\n• Hot lights — let cool before any service or relocation.\n• Inspect cords daily; damaged tower removed from service.",
    references_cited: "OSHA 1926.405 · Manufacturer Operator Manual",
    action_items:
      "Outriggers set · Overhead clearance verified · Mast locked · Refuel procedure followed",
  },
];
