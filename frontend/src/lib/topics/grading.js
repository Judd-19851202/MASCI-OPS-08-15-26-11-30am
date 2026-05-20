// Auto-split from monolithic meetingTopicLibrary.js · iter260
// Domain: grading · 5 topics
// Edit content here; index.js aggregates all domains.

export const TOPICS_GRADING = [
  {
    key: "earthmoving_equipment",
    domain: "grading",
    title: "Earthmoving Equipment & Heavy Iron",
    category: "Tool / Equipment Specific",
    hazards_reviewed: "Struck-by equipment · Run-over while spotting · Caught between equipment and fixed object · Rollover · Backing accidents · Swing radius incidents",
    discussion_notes: "• Pre-shift walkaround on every piece of iron — fluids, tires, lights, alarms, fire extinguisher.\n• Seat belts worn at all times — no exceptions.\n• Backup alarms operational; spotters used in congested areas or restricted visibility.\n• Establish and enforce no-go zones around equipment swing radius.\n• Workers on the ground wear hi-vis and stay in operator's line of sight.\n• Eye contact + thumbs up before operator moves equipment near workers.\n• Park on level ground, blade/bucket down, brake set, key removed when leaving cab.",
    references_cited: "OSHA 29 CFR 1926 Subpart O · OSHA 1926.601 · OSHA 1926.602 · MUTCD Part 6",
    action_items: "Pre-op inspections logged · Spotters assigned · No-go zones marked · Equipment parked safely at end of shift",
  },
  {
    key: "backing_spotters",
    domain: "grading",
    title: "Backing Operations & Spotters",
    category: "Procedure / SOP",
    hazards_reviewed: "Backover incidents · Struck-by reversing equipment · Spotter struck by other vehicle · Communication breakdown · Blind spots",
    discussion_notes: "• Back-up alarms operational on every piece of mobile equipment / dump truck.\n• Spotter required when backing in congested areas or near workers.\n• Spotter stands clear of the path of travel, in operator's mirror line of sight.\n• Lose sight of spotter = STOP. Operator never backs blind.\n• Use horn signals: 1 stop, 2 forward, 3 reverse.\n• Hi-vis apparel mandatory for spotters at all times.",
    references_cited: "OSHA 1926.601(b)(4) · OSHA Backover Hazards Bulletin",
    action_items: "Designated spotters identified · Spotter PPE verified · Hand signals reviewed · Comms plan in place",
  },
  {
    key: "compaction",
    domain: "grading",
    title: "Compaction Operations",
    category: "Tool / Equipment Specific",
    hazards_reviewed: "Hand-arm vibration syndrome · Whole-body vibration on rollers · Struck-by walking compactor · Rollover on slopes · Noise above 85 dBA · Run-over by reversing roller",
    discussion_notes: "• Walk-behind compactors: maintain firm grip, anti-vibration gloves, no loose clothing.\n• Vibratory rollers: never operate on slopes greater than mfr-stated max.\n• Roller no-go zones marked; spotters at edges and tapers.\n• Backup alarms required; reversing on slope only with spotter.\n• Take 10-minute break per hour with vibrating equipment to mitigate HAVS.\n• Hearing protection required — most compactors exceed 85 dBA.",
    references_cited: "OSHA 1926.95 · NIOSH Hand-Arm Vibration · ACGIH TLV for vibration",
    action_items: "Anti-vibration gloves issued · Roller no-go zones marked · Hearing protection required · Operator rotation",
  },
  {
    key: "excavator_safety",
    domain: "grading",
    title: "Excavator Safety",
    category: "Tool / Equipment Specific",
    hazards_reviewed: "Tipping on slopes · Struck-by bucket / counterweight · Crushed in swing radius · Cab fall on slope · Hydraulic line failure · Quick coupler disengagement",
    discussion_notes: "• Pre-shift walkaround; check tracks, undercarriage, hydraulics, fluids, cab attachments.\n• Operator buckles seat belt before start.\n• Swing radius marked / barricaded — workers stay outside.\n• Bucket on ground when loading trucks; never swing over operator cab.\n• Quick coupler: positive engagement verified before lifting.\n• Park on level ground, bucket down, key out, brake set when leaving cab.",
    references_cited: "OSHA 1926.602 · Manufacturer Operator Manual",
    action_items: "Pre-op inspection logged · Swing radius marked · Quick coupler verified · Park-out routine followed",
  },
  {
    key: "skid_steer",
    domain: "grading",
    title: "Skid Steer / CTL Safety",
    category: "Tool / Equipment Specific",
    hazards_reviewed: "Crushed by lift arms (entry/exit hazard) · Tipping on slope · Struck-by attachments · Run-over by reversing machine · Burns from exhaust/turbo · Quick attach disengagement",
    discussion_notes: "• Enter/exit ONLY with arms lowered and bucket flat — never under raised arms.\n• Seat belt and seat bar lowered before start.\n• Quick attach pins fully engaged — verify before lifting.\n• No riders. No standing on attachments.\n• Backing in congested areas requires spotter.\n• Park on level ground, arms down, bucket on ground.",
    references_cited: "OSHA 1926.602 · Manufacturer Operator Manual · NIOSH Skid Steer Bulletin",
    action_items: "Seat belt enforced · Quick attach verified · Spotter assigned · No riders briefed",
  },
];
