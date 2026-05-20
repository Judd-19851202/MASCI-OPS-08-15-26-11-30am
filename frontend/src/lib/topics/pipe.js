// Domain: pipe · iter261 Phase H Batch 2 · 3 uplifted

export const TOPICS_PIPE = [
  {
    key: "pipe_installation",
    domain: "pipe",
    title: "Pipe Installation — RCP / DI / HDPE",
    category: "Hazard-Specific",
    severity: "fatal_risk",
    incident_pattern:
      "Pipe install fatalities follow a tight pattern: a worker is in the trench guiding a length of RCP or DI as the excavator lowers it, the load swings as the bucket pivots, and the worker gets pinned against the trench wall or under the pipe. Concrete pipe ranges from 1,000 lb (12-inch) to 15,000+ lb (60-inch). The boom doesn't have to drop — a 6-inch swing crushes a chest. Second variant is during home — workers using bars and tongs to seat the bell joint, the pipe shifts under tension, and a hand goes into the bell. Always recoverable in writing — never recoverable in person. Fix is well-known: nobody in the trench under or near a swinging load, period; tag lines control pipe attitude from a safe stance; home the joint with mechanical advantage, not body weight.",
    hazards_reviewed:
      "Struck-by suspended pipe · Crushing / pinch points joining pipe · Worker in trench under suspended load · Trench cave-in · Slips on wet/muddy bedding · Back/strain from manual handling",
    discussion_notes:
      "• Workers OUT of trench while pipe is being lowered. Re-enter only after pipe is set and load is RELEASED.\n• Use pipe-laying tongs, slings, or pipe lifters — never improvised lifting.\n• Designated signal person for crane / excavator placing pipe. Only one voice.\n• Joint home with mechanical means (come-along, jack, equipment) — not by hand.\n• Tag lines control pipe rotation; workers stay OUTSIDE the bite.\n• Trench protective system stays in place during pipe install. No 'we'll pull the box just for this lift.'\n• Hand position discipline at the bell joint — fingers never inside the bell.",
    references_cited:
      "OSHA 1926 Subpart P · OSHA 1926.251 (rigging) · ACPA Concrete Pipe Handbook",
    action_items:
      "Riggers certified · Signal person designated · Tag lines used · Trench shield in place during install · Hand-position discipline reinforced",
  },
  {
    key: "manhole_work",
    domain: "pipe",
    title: "Manhole Work & Lift Stations",
    category: "Hazard-Specific",
    severity: "fatal_risk",
    incident_pattern:
      "Manhole fatalities are catastrophic AND multi-victim — almost half of confined-space fatalities are would-be rescuers who entered without their own PPE. The pattern: one worker drops into a sewer or storm structure for a quick look, doesn't sense the low-O2 or H2S immediately, collapses. A second worker sees them down and jumps in to help — collapses. By the time the third worker calls 911 there are two unconscious people at the bottom of a 10-foot pit and the rescue team is 20 minutes out. Every confined-space training course tells this story and the industry loses workers to it every year. The fix is rigid: permit, atmospheric test, attendant, retrieval line — and zero unplanned entries. EVER. Including the boss. Including the foreman. Including the engineer.",
    hazards_reviewed:
      "Hazardous atmosphere (H2S, methane, low O2) · Falls into open structure · Struck-by lifted cover · Engulfment from sudden inflow · Bloodborne / biohazard from sewage exposure · Multi-victim rescue without PPE",
    discussion_notes:
      "• Treat EVERY manhole as a permit-required confined space until proven otherwise.\n• Atmospheric test before entry, continuous monitoring inside. O2, LEL, CO, H2S minimum.\n• Mechanical fan ventilation required for active sewer/storm structures.\n• Use proper manhole hook to lift covers — never fingers in slots.\n• Barricade and cover any open structure; never leave unattended.\n• Attendant OUTSIDE. Their job is to MONITOR and to CALL RESCUE. They do NOT enter.\n• If your partner goes down: do NOT jump in. Call rescue. Stay topside. Throw the retrieval line.\n• Sewage exposure: skin/eye protection, immediate decon if contact, hand hygiene before eating.",
    references_cited:
      "OSHA 1926 Subpart AA (Confined Spaces) · OSHA 1910.1030 (BBP)",
    action_items:
      "Permit signed · Gas monitor calibrated · Ventilation set up · Decon supplies on site · Don't-jump-in rule reinforced",
  },
  {
    key: "boring_drilling",
    domain: "pipe",
    title: "Boring / Directional Drilling (HDD)",
    category: "Hazard-Specific",
    severity: "fatal_risk",
    incident_pattern:
      "HDD utility strikes are some of the most consequential incidents in heavy civil — a single bad bore can hit a 12kV feeder, a high-pressure gas main, or a fiber bundle serving a whole city. The pattern is consistent: the operator gets a locate, the marks are imprecise, and the drill head drifts in soft material into the tolerance zone of an unmarked utility. The strike happens at the drill head 8-15 feet underground; the operator on the surface sees nothing for the first few seconds. Gas main strike → ignition risk grows by the minute. Power strike → arc-flash potential rolls back to the surface through the drill stem. The fix is rigorous daylighting at every crossing, real-time tracking on a sonde, and a hard rule: if the locate is uncertain, the bore stops and goes mechanical or hand-dug for that section.",
    hazards_reviewed:
      "Inadvertent utility strike · High-pressure mud blowout · Pinch points on rod handler · Slips on slurry-covered ground · Frac-out releasing drilling mud to surface · Caught-in rotating drill string",
    discussion_notes:
      "• Pothole / daylight ALL crossings before bore. No 'we'll see when we get there.'\n• Locate strikes are mandatory — verify with utility owner where critical.\n• Never reach into rotating drill string or rod box. Use long-handled tools.\n• Frac-out plan in writing; spill kits onsite.\n• High-pressure jets can cut skin — keep hands clear of nozzle path.\n• Pull-back forces are high — workers stay OUTSIDE line-of-tension.\n• Real-time sonde tracking — if depth drifts unexpectedly, STOP. Investigate before continuing.\n• If you hit something — STOP immediately. Don't try to clear. Withdraw the drill head. Identify before resuming.",
    references_cited:
      "OSHA 1926.601 · DCA Best Practices for HDD · CGA Best Practices",
    action_items:
      "Crossings daylighted · Frac-out plan onsite · Spill kit staged · Tension line zone cleared · Stop-and-identify-on-hit habit reinforced",
  },
];
