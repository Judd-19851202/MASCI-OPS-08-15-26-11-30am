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
  // iter303 · airport-domain tone benchmark (operator-approved v2)
  // Mental-model-first framing pattern · parallels iter302's custody-first benchmark.
  // Anchor line: "The bolt didn't change. The pavement it sat on changed everything
  // about what the bolt meant." Voice template for the remaining 3 airport topics.
  {
    key: "airport_fod_control",
    domain: "airport",
    title: "FOD Control on the Airside — The Discipline That Closes the Mental-Model Gap",
    severity: "fatal_risk",
    category: "Hazard-Specific",
    role_context: ["foreman", "lead", "operator", "lab_tech", "driver"],
    incident_pattern:
      "FOD doesn't feel like a fatality risk when you're holding it. A bolt. A nut. A two-inch piece of asphalt millings. The contractor's mental model is 'litter to sweep before we leave.' The airfield's mental model is completely different: that same bolt, on the centerline, at engine startup, gets ingested at 8,000 RPM. Air France 4590 was destroyed by debris left on a runway from a previous aircraft. The consequence was total. Closer to home: a 4-inch carriage bolt near a taxiway centerline at end of shift becomes a multi-million-dollar engine teardown, a runway closure, and the end of the contractor's airfield work. The bolt didn't change. The pavement it sat on changed everything about what the bolt meant. Crews who have worked airside know this in their bones. Crews coming from highway, utility, or concrete work usually don't — they treat the airfield like another paving job until something goes wrong. FOD discipline is the bridge between those two understandings, and that bridge gets built one shift at a time.",
    hazards_reviewed:
      "Engine ingestion at startup or rotation · Tire damage / blowout on takeoff roll · FAA Part 139 violation and contract escalation · Runway / taxiway closure during sweep response · Personal protective equipment lost to jet blast becoming FOD itself · Material tracking from work area to active movement areas · End-of-shift cleanup compression / time pressure · Personnel struck by FOD propelled by jet blast",
    discussion_notes:
      "• FOD is not litter. Every object on airside pavement is a potential aircraft incident. The shift from 'cleanup' to 'live hazard' is the discipline.\n• Pocket-check before crossing onto a movement area. Fasteners, pens, ear plugs, sunglasses — anything jet blast can lift is FOD downwind.\n• Tire-knock at the perimeter every trip. Not just end of shift. Every trip, work area to laydown.\n• Open beds tarped before crossing the perimeter. Millings, gravel, banding pieces — if it can blow out, it's FOD by landing.\n• Tools by count, signed in and signed out. Twelve in, twelve out. 'I think I had all' is how a wrench becomes an FAA report.\n• Cable ties, banding clips, tape backing, PPE wrappers — to the trash bag at your feet. Never the pavement. Never 'grab it later.'\n• Shed PPE is FOD. A glove blown loose in prop wash is the same problem as a dropped bolt. Report, retrieve, replace.\n• End-of-shift FOD walk: shoulder-to-shoulder, eyes down, before handoff to Airfield Ops. Walk it. Don't drive it.\n• Find FOD: pick it up. Not 'leave it for the next crew.' Not 'radio it in and wait.' FOD is live until it's in someone's hand.\n• If your zone is the source of a FOD alert from Airfield Ops, your contract is on the line. Take it seriously the first time.",
    references_cited:
      "FAA Part 139 (Airport Operating Certification) · FAA AC 150/5210-24 (FOD Management at Airports) · ICAO Annex 14 · NTSB Air France 4590 Final Report · Airfield Operations SOP · Contract Special Conditions",
    action_items:
      "Pocket-check protocol reviewed · Tool count discipline confirmed (count in / count out) · Tire-knock and tarp procedure verified · FOD-walk responsibility assigned by name · Trash bag at every work position · Communication path to Airfield Ops confirmed",
  },
];
