// Domain: environmental · iter261 Phase H Batch 4 · 3 uplifted

export const TOPICS_ENVIRONMENTAL = [
  {
    key: "lightning",
    domain: "environmental",
    title: "Lightning & Severe Storms",
    category: "Hazard-Specific",
    severity: "fatal_risk",
    incident_pattern:
      "Lightning fatalities on construction sites come from one stubborn pattern: 'one more pour' or 'one more load.' Crew sees lightning in the distance, foreman counts thunder, decides the storm is still 5 miles out, keeps working. Strike radius is closer than the eye reads — lightning can hit 10 miles ahead of the rain. Worker holding a metal rake on a paving deck, worker on a crane, worker on top of a fuel truck, worker holding a rebar tie wire — any of them becomes the lightning rod. Pattern two is the assumed-safe shelter — workers cluster under an open-sided pavilion or under a piece of equipment thinking they're protected. Side-flash and ground current still find them. The fix is the 30/30 rule, treated as inviolable: thunder within 30 seconds of lightning = stop work, into hard shelter, 30 minutes of silence before resuming. No exceptions for the last truck of asphalt.",
    hazards_reviewed:
      "Direct strike · Side flash · Ground current · Equipment energization · Wind damage · Flash flooding",
    discussion_notes:
      "• 30/30 rule — when thunder follows lightning by 30 seconds or less, stop work and shelter. Wait 30 minutes after the last thunder before resuming.\n• No shelter under isolated trees, equipment cabs (open), or scaffolds.\n• Best shelter: enclosed building, hard-topped vehicle (windows up).\n• Disconnect cranes, equipment, and tools from power before storm.\n• Watch for flash flooding in low-lying areas of work site.",
    references_cited: "NWS Lightning Safety · OSHA Lightning Bulletin · NFPA 780",
    action_items:
      "Weather monitoring app installed · Shelter location identified · 30/30 rule briefed · Equipment shutdown plan",
  },
  {
    key: "wildlife_insects",
    domain: "environmental",
    title: "Wildlife / Insect Bites & Stings",
    category: "Hazard-Specific",
    severity: "serious_injury",
    incident_pattern:
      "Wildlife and insect incidents look minor in the abstract and turn fatal in real life when the worker is allergic and the response is slow. The pattern: laborer reaches into a meter box or steps off a piece of equipment into a fire-ant mound, takes 15-30 stings in seconds, has a known bee allergy, develops anaphylaxis in the field. EpiPen is in the truck a quarter mile away. By the time someone runs and gets back, throat is closing. Second pattern is the snake bite that the worker doesn't take seriously — small puncture, didn't see what it was, keeps working until the leg starts swelling 90 minutes later. Treatment window is closing. Florida and Texas fieldwork have the highest concentration of these incidents. The fix is small but real: ask the crew about allergies at orientation, keep EpiPens on every project where bee-allergic workers are present, and treat every snake bite as venomous until ER says otherwise.",
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
    key: "spill_response",
    domain: "environmental",
    title: "Spill Response & Environmental Compliance",
    category: "Procedure / SOP",
    severity: "serious_injury",
    incident_pattern:
      "Spill incidents rarely kill workers directly but generate two real-world outcomes that hurt crews: the storm-drain release that turns into a six-figure fine plus a stop-work order, and the fuel-puddle ignition that takes out equipment, vehicles, and sometimes operators. The pattern: hose nozzle drips during refueling onto a sloped paver surface, fuel runs 40 feet to a storm grate before anyone notices. Inspector sees the sheen at the next outfall and ties it back to the project number on the dump truck across the street. The fix is the unglamorous stuff: spill kits within 50 feet of every fuel point, storm-drain mats during ALL fueling (not just when it looks risky), and an absolute rule that 'stop the source' is step one. Don't try to push a spreading puddle back upstream — shut the valve, then deal with what's already out. Reporting threshold known by every foreman before the spill happens, not after.",
    hazards_reviewed:
      "Fuel / oil release to soil or storm drain · Chemical spill · Environmental fines · Slip on spilled material · Vapor inhalation",
    discussion_notes:
      "• Spill kit available wherever fuel, oil, hydraulic fluid, chemicals are used or stored.\n• Stop the source first — shut valves, close containers.\n• Contain the spill — absorbent boom, socks, pads.\n• Clean up and dispose properly — contaminated materials are hazardous waste.\n• Report spills per state/EPA threshold — minor spills tracked, reportable spills called in within required time.\n• Storm drain protection mats during fueling.",
    references_cited: "EPA SPCC · State / FDEP requirements · NFPA 30",
    action_items:
      "Spill kits onsite · SDS for site chemicals available · Reporting threshold known · Storm drain mats deployed",
  },
];
