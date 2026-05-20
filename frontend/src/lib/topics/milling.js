// Domain: milling · iter261 Phase H Batch 2 · 1 uplift + 1 new = 2 topics

export const TOPICS_MILLING = [
  {
    key: "milling_operations",
    domain: "milling",
    title: "Milling Operations (Cold Planing)",
    category: "Hazard-Specific",
    severity: "fatal_risk",
    incident_pattern:
      "Milling fatalities split between two patterns. First — a worker reaches near or into the drum to clear a stuck rock, free a piece of tramp metal, or change a tooth, with the machine running or with stored hydraulic energy in the drum lift. The drum drops or rotates 6 inches and takes an arm. Second — a laborer walks behind the conveyor as it swings to off-load into the truck, and the conveyor tail-end catches them. The drum stops fast when shut off, but stored energy in the lift cylinders does not. Lockout is the universal fix and the universally skipped step on small touch-ups. 'Just one tooth' has cost hands.",
    hazards_reviewed:
      "Struck-by milling drum / conveyor · Silica / asphalt dust · Caught-in conveyor pinch points · Hot/burning teeth contact · Noise above 95 dBA · Trip on grade transitions · Stored hydraulic energy on drum lift",
    discussion_notes:
      "• Workers stay outside drum and conveyor no-go zones during operation. Marked with hi-vis cones.\n• Water spray system on the drum — primary silica/dust control. Confirm flow on every shift.\n• Respirator if water control insufficient (older mills, dry conditions, indoor cuts).\n• Tooth changes: machine fully shut down, LOCKED OUT, drum cooled, drum lift BLOCKED with rated cribbing.\n• 'Just one tooth' still requires full LOTO. The pattern is shortcut → injury.\n• Hearing protection mandatory.\n• Ground crew aware of grade transitions; positive comms with operator.\n• Conveyor swing zone — ground workers stay clear. The swing is faster than people expect.",
    references_cited:
      "OSHA 1926.1153 · NIOSH Asphalt Milling Bulletin · OSHA 1910.147",
    action_items:
      "No-go zones marked · Water spray verified · Hearing protection required · LOTO for tooth changes · Drum lift cribbing on-site",
  },
  {
    key: "milling_silica_exposure",
    domain: "milling",
    title: "Milling Silica Exposure & Water-Spray Discipline",
    category: "Hazard-Specific",
    severity: "serious_injury",
    role_context: ["milling_operator", "lead", "ground_crew"],
    incident_pattern:
      "Silica exposure on milling jobs is a SLOW catastrophe — not the kind that shows up in a fatality log this year. The worker breathes dust for 5–10 years of paving seasons. Silicosis builds in lung tissue at exposure levels the worker never realized were dangerous. The job feels normal. The cough at 50 doesn't. The pattern of failure is consistent: water spray nozzles clogged or partly clogged, the operator doesn't see it from the cab, and the dust plume rises off the drum invisibly. Or the spray runs out mid-shift and the operator keeps cutting because the truck is waiting. The OSHA silica rule of 50 µg/m³ (8-hour) is exceeded easily on a dry mill with poor spray. The fix is daily nozzle inspection, a spare water tank, and respiratory protection as the second line of defense — not the first.",
    hazards_reviewed:
      "Long-term silicosis from cutting concrete/asphalt with silica content · Acute respiratory irritation · Eye irritation from airborne particulates · Visibility loss from dust plume hiding hazards · Operator-cab dust accumulation",
    discussion_notes:
      "• Water spray is PRIMARY silica control. Check every nozzle BEFORE cutting starts.\n• Spare water tank or refill plan — never run dry mid-shift to 'finish this one.'\n• Visible dust plume = control failure. Stop cutting. Diagnose. Fix the nozzles.\n• Respiratory protection (P100 or supplied air) for dry-mill conditions, indoor cuts, or when water fails.\n• Don't stand downwind of the cut. Position support equipment upwind too.\n• Cab filter system on the mill — change per OEM, not 'when I remember.'\n• OSHA silica rule says 50 µg/m³ 8-hour. Air sampling required on high-exposure jobs.\n• Long-sleeve work clothing — silica adheres to skin and gets carried home to families.\n• Shower / change before leaving site if exposed. Doesn't help YOU, helps your family.",
    references_cited:
      "OSHA 29 CFR 1926.1153 (Silica) · NIOSH Asphalt Milling Bulletin · ACGIH TLV",
    action_items:
      "Nozzle inspection assigned to each shift · Spare water plan reviewed · Respirator fit-tested for exposed workers · Cab filter change scheduled · Take-home contamination habit discussed",
  },
];
