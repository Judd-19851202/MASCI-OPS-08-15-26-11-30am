// Auto-split from monolithic meetingTopicLibrary.js · iter260
// Domain: electrical · 4 topics
// Edit content here; index.js aggregates all domains.

export const TOPICS_ELECTRICAL = [
  {
    key: "electrical_safety",
    domain: "electrical",
    title: "Electrical Safety & Energized Equipment",
    category: "Hazard-Specific",
    hazards_reviewed: "Electrocution · Arc flash / blast · Burns · Fall caused by shock · Fire from damaged cords · Unexpected startup",
    discussion_notes: "• GFCI on every 120V circuit on the job — temp power, generators, extension cords.\n• Inspect cords daily — no damaged jackets, exposed conductors, missing ground pins.\n• LOTO for any work on electrical systems — verified de-energized with a tester.\n• Maintain 10 ft minimum approach to overhead lines (more for higher voltage).\n• Panels and disconnects covered and labeled.\n• Only qualified persons work on energized equipment, and only when de-energizing isn't feasible.",
    references_cited: "OSHA 1926 Subpart K · OSHA 1926.404 · NFPA 70E · OSHA LOTO 1910.147",
    action_items: "GFCI verified · Cords inspected · LOTO followed · Overhead clearance maintained",
  },
  {
    key: "loto",
    domain: "electrical",
    title: "Lockout / Tagout (LOTO)",
    category: "Procedure / SOP",
    hazards_reviewed: "Unexpected startup · Stored energy release (hydraulic, pneumatic, gravity, springs) · Multiple energy sources · Bypassing controls · Removing someone else's lock",
    discussion_notes: "• Identify EVERY energy source — electrical, hydraulic, pneumatic, gravity, thermal, chemical.\n• Notify affected employees, shut down using normal procedure, isolate, lock + tag, verify zero energy.\n• Each authorized worker applies their own personal lock — no shared locks.\n• Test for zero energy: start switch, gauges, manual operation as appropriate.\n• Removing your own lock = your responsibility. Removing someone else's requires absent-employee removal procedure.\n• Group LOTO uses lockbox + master tag; everyone signs on, signs off.",
    references_cited: "OSHA 1910.147 · OSHA 1926 Subpart K · ANSI Z244.1",
    action_items: "LOTO procedure on site · Personal locks issued · Energy sources identified · Verification step trained",
  },
  {
    key: "generator_temp_power",
    domain: "electrical",
    title: "Generator / Temporary Power Setup",
    category: "Tool / Equipment Specific",
    hazards_reviewed: "CO poisoning · Electrical shock · Fire / fuel spill · Backfeed onto utility lines · Generator overloading",
    discussion_notes: "• NEVER run a fuel-burning generator indoors or in any enclosed space — CO kills.\n• 20 ft minimum from buildings, vents, and air intakes.\n• Bond generator frame to ground rod where required.\n• GFCI on every 120V outlet — many gen outlets are not internally GFCI-protected.\n• Size circuits for the load; spread loads across phases.\n• If feeding a panel, use a transfer switch (no backfeeding through outlets).\n• Refuel only when cold; bonded fuel containers; no smoking.",
    references_cited: "OSHA 1926.405 · NFPA 70 (NEC) · NIOSH CO Bulletin",
    action_items: "Generator placement verified · Bonding/grounding in place · GFCI confirmed · Fuel handling area set up",
  },
  {
    key: "light_tower",
    domain: "electrical",
    title: "Light Tower Operations",
    category: "Tool / Equipment Specific",
    hazards_reviewed: "Tipping during raise / lower · Overhead clearance contact · Burns from hot lights · CO from generator section · Electrical shock from damaged cords",
    discussion_notes: "• Place on stable level ground; outriggers fully extended.\n• Verify overhead clearance before raising mast.\n• Lock mast at full height before walking away.\n• Generator: refuel cold, bonded container, no smoking, 20 ft from buildings.\n• Hot lights — let cool before any service or relocation.\n• Inspect cords daily; damaged tower removed from service.",
    references_cited: "OSHA 1926.405 · Manufacturer Operator Manual",
    action_items: "Outriggers set · Overhead clearance verified · Mast locked · Refuel procedure followed",
  },
];
