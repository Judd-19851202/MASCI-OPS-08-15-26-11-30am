// Domain: utilities · iter261 Phase H Batch 3 · 2 uplifted

export const TOPICS_UTILITIES = [
  {
    key: "underground_utilities",
    domain: "utilities",
    title: "Underground Utilities / 811 Locates",
    category: "Procedure / SOP",
    severity: "fatal_risk",
    incident_pattern:
      "Utility-strike fatalities cluster around three patterns: gas line strike with delayed ignition, fiber strike with no injury but massive liability, and underground electric strike with operator electrocution. The gas pattern is the killer — bucket nicks a 2-inch gas main, no immediate fire, gas pools in the trench while the crew keeps working, ignition source (cell phone, light switch, vehicle starter) lights it off, and the trench becomes a flash fire. Multi-fatality common. The electric pattern is faster but smaller body count — bucket teeth bite a primary, voltage transfers to the excavator, operator gets hit, ground crew gets step-potential. Every fatality in this category traces back to the same root: an unmarked or mis-marked utility, OR a crew that mechanically dug inside the 24-inch tolerance zone of a marked utility. The fix is non-negotiable: hand-dig inside the tolerance zone. No exceptions.",
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
    key: "overhead_power",
    domain: "utilities",
    title: "Working Near Overhead Power Lines",
    category: "Hazard-Specific",
    severity: "fatal_risk",
    incident_pattern:
      "Overhead-line fatalities are catastrophic, often multi-victim, and follow one signature pattern: boom equipment contacts a primary, the equipment becomes energized, the operator is okay inside the cab (Faraday-cage effect), but a worker on the ground touching the equipment or near it gets the full transfer. Common scenarios — crane boom contacts during a pick, dump body raised under a line, ladder slipped against a service drop, even an excavator stick swinging into a low-hanging primary. The killer step is the helpful worker who runs to the equipment to see what's wrong — they touch the metal and become the path to ground. Burn injuries are catastrophic. The fix is 10-foot clearance minimum (more for higher voltage), spotter dedicated to clearance, and if equipment contacts a line: STAY IN THE CAB. Drive out of contact if possible, jump clear and shuffle-step 30 feet if not.",
    hazards_reviewed:
      "Electrocution from contact · Arc flash from approach · Equipment movement (boom, dump body, ladder) into clearance zone · Induced voltage on parallel objects",
    discussion_notes:
      "• 10 ft minimum clearance for lines up to 50 kV; more for higher voltage.\n• Where 10 ft can't be maintained: de-energize + ground OR install line covers OR use dedicated spotter.\n• Boom equipment near lines — proximity alarms, dedicated spotter, table-A clearances.\n• Dump bodies / ladders — kept low until clear of overhead.\n• If equipment contacts a line: STAY IN CAB. Operator drives out of contact if possible. If not, jump clear and shuffle 30+ ft away.",
    references_cited: "OSHA 1926.1408 (Cranes) · OSHA 1926.952 · OSHA 1926.405",
    action_items:
      "Lines identified · Clearance verified · Spotter assigned · Contact response briefed",
  },
];
