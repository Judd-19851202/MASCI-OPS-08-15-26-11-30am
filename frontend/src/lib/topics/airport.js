// Auto-split from monolithic meetingTopicLibrary.js · iter260
// Domain: airport · 2 topics
// Edit content here; index.js aggregates all domains.

export const TOPICS_AIRPORT = [
  {
    key: "airport_movement_area_awareness",
    domain: "airport",
    title: "Airport Movement Areas — Runway, Taxiway, and ATC Discipline",
    severity: "fatal_risk",
    category: "Hazard-Specific",
    role_context: ["operator","driver","lead","spotter"],
    incident_pattern: "Airport-job incidents involve aircraft, not just ground equipment. The pattern repeats: a crew is doing paving or pavement repair at the edge of a runway or taxiway. The lead has cleared the work zone with ATC. The clearance was for one hour. The crew runs over the clearance because a piece of equipment broke down. ATC, assuming the zone is clear at the agreed time, releases the runway. An aircraft is rolling in 90 seconds. The worker pulling a piece of equipment off doesn't know the clearance has lapsed. The most consistent finding in airport-related fatalities is communication breakdown — between ATC, the lead, and the workers on the ground.",
    hazards_reviewed: "Aircraft strike of worker or equipment in active movement area · Jet blast / prop wash · FOD created by site debris · Equipment incursion into active runway · Communication breakdown with ATC · Confusion at low-vis or night operations",
    discussion_notes: "• Movement-area work requires ATC clearance and a CONFIRMED window. The lead has the radio. The lead is on it.\n• If the work window is about to expire — STOP. Pull everyone and everything out. Do NOT push the time. ATC will re-clear; aircraft cannot land twice.\n• Workers all carry radios on the operations frequency the airport authority assigns. Listen first, talk second.\n• FOD discipline — every wrench, every cone, every scrap of debris accounted for before clearing the area. A loose bolt destroys a jet engine.\n• Hi-vis at airfield specs — not the same as construction hi-vis. ANSI 207 Public Safety colors where required. Read the contract spec.\n• Equipment in active zone — escorted, marked, and on ATC radio. Pickups too. No one freelances onto a taxiway.\n• Jet blast / prop wash zones — even small aircraft create wind that can throw a person or a cone. Stay clear of holding aircraft.\n• Night / low-vis ops — extra coordination, extra lighting, extra check-ins. Don't push through bad-vis without authority alignment.",
    references_cited: "FAA AC 150/5210-5 · FAA AC 150/5370-2 · TSA / airport-specific procedures · MASCI Airport Operations SOP",
    action_items: "ATC clearance protocol reinforced · FOD accountability reviewed · Radio discipline discussed · Window-expiry pullout drill assigned",
  },
  {
    key: "airport_jet_blast_fueling",
    domain: "airport",
    title: "Jet Blast, Prop Wash, and Airfield Fueling Awareness",
    severity: "fatal_risk",
    category: "Hazard-Specific",
    role_context: ["operator","driver","lead"],
    incident_pattern: "Workers underestimate jet blast and prop wash. A regional turboprop spooling up generates 100+ mph of wash behind it. A commercial jet at idle thrust generates winds capable of flipping a pickup. The pattern: a crew is positioning equipment near a holding aircraft, the pilot bumps thrust to begin taxi, and a worker, a cone, or a piece of equipment gets thrown. Combine that with the airfield fueling environment — Jet-A is everywhere, ignition sources must be controlled, and a static spark is a Class B fire instantly. Airfield work has its own hazards that don't exist anywhere else.",
    hazards_reviewed: "Worker / equipment thrown by jet blast · Prop wash injury to ground crew · Jet-A static ignition · Vapor cloud ignition near fueling ops · Hearing damage from aircraft noise · FOD from blown debris",
    discussion_notes: "• Stay clear of holding aircraft. A 100-foot clearance is a starting point, not a maximum. If you can see the engine, the engine can hit you with blast.\n• Hearing protection in any active movement area. Aircraft noise damages hearing in minutes of exposure.\n• Jet-A fueling areas — no spark sources within 50 feet. No cell phones, no flashlights without intrinsic safety rating, no metal-on-metal.\n• Tie down or weigh down EVERYTHING near a taxiway. Cones, sawhorses, equipment. What stays put in normal wind blows away in prop wash.\n• Fueling operations have their own crew. Construction crews don't intersect with fueling ops. Stay clear of fuel trucks and refueling aircraft.\n• Static grounding for any fueling-adjacent work. Bonding cables, grounding rods. Static is the silent ignition source.\n• If you feel wind suddenly — look around. An aircraft is moving somewhere you didn't expect. Verify position before continuing.\n• Eye protection — debris in airfield work is everywhere. Open faceshields aren't enough at busy airfields.",
    references_cited: "FAA AC 150/5230-4 · NFPA 407 (aircraft fuel servicing) · OSHA 1926.101 (hearing) · MASCI Airfield SOP",
    action_items: "Aircraft clearance distance reinforced · Hearing protection verified · Fueling-adjacent ignition control discussed · Tie-down policy for cones / equipment reviewed",
  },
];
