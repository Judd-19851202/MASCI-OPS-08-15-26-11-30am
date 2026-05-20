// Domain: grading · iter261 Phase H Batch 3 · 5 uplifted

export const TOPICS_GRADING = [
  {
    key: "earthmoving_equipment",
    domain: "grading",
    title: "Earthmoving Equipment & Heavy Iron",
    category: "Tool / Equipment Specific",
    severity: "fatal_risk",
    incident_pattern:
      "Earthmoving struck-by and run-over fatalities follow one of two patterns. Pattern one — the operator can't see a worker on foot near the corner of the cab. Dozers, loaders, motor graders all have blind spots that grow with the size of the iron. Worker walks behind the loader for a quick measurement, operator pivots to reposition, the rear of the cab swings into where the worker is standing. Pattern two — workers in the line of fire of the bucket or blade during loading. Truck driver hops out to wave at the loader, walks within bucket-swing radius, gets hit by the next pivot. The fix is non-negotiable: no foot traffic in active loading zones, eye contact + thumbs up before any equipment moves near workers, hi-vis stays on. The operator is responsible for refusing to move until they can SEE the ground crew.",
    hazards_reviewed:
      "Struck-by equipment · Run-over while spotting · Caught between equipment and fixed object · Rollover · Backing accidents · Swing radius incidents",
    discussion_notes:
      "• Pre-shift walkaround on every piece of iron — fluids, tires, lights, alarms, fire extinguisher.\n• Seat belts worn at all times — no exceptions.\n• Backup alarms operational; spotters used in congested areas or restricted visibility.\n• Establish and enforce no-go zones around equipment swing radius.\n• Workers on the ground wear hi-vis and stay in operator's line of sight.\n• Eye contact + thumbs up before operator moves equipment near workers.\n• Park on level ground, blade/bucket down, brake set, key removed when leaving cab.",
    references_cited:
      "OSHA 29 CFR 1926 Subpart O · OSHA 1926.601 · OSHA 1926.602 · MUTCD Part 6",
    action_items:
      "Pre-op inspections logged · Spotters assigned · No-go zones marked · Equipment parked safely at end of shift",
  },
  {
    key: "backing_spotters",
    domain: "grading",
    title: "Backing Operations & Spotters",
    category: "Procedure / SOP",
    severity: "fatal_risk",
    incident_pattern:
      "Backover fatalities are one of the most preventable categories in heavy civil — and one of the most repeated. The pattern: dump truck or piece of iron backs into a worker on foot in a congested staging area. The driver was watching the mirrors, the worker was looking at their phone or walking with their back to the equipment, the backup alarm beeped in a sea of other alarms and got tuned out. Spotter not present, or spotter was talking to someone else and broke eye contact for 4 seconds. The fix is rigid: backup alarms on every reverse, dedicated spotter for any reverse in a workzone, and lose-sight-of-spotter = stop. The spotter's only job during a back is the back. Not radio, not phone, not chat.",
    hazards_reviewed:
      "Backover incidents · Struck-by reversing equipment · Spotter struck by other vehicle · Communication breakdown · Blind spots",
    discussion_notes:
      "• Back-up alarms operational on every piece of mobile equipment / dump truck.\n• Spotter required when backing in congested areas or near workers.\n• Spotter stands clear of the path of travel, in operator's mirror line of sight.\n• Lose sight of spotter = STOP. Operator never backs blind.\n• Use horn signals: 1 stop, 2 forward, 3 reverse.\n• Hi-vis apparel mandatory for spotters at all times.",
    references_cited: "OSHA 1926.601(b)(4) · OSHA Backover Hazards Bulletin",
    action_items:
      "Designated spotters identified · Spotter PPE verified · Hand signals reviewed · Comms plan in place",
  },
  {
    key: "compaction",
    domain: "grading",
    title: "Compaction Operations",
    category: "Tool / Equipment Specific",
    severity: "serious_injury",
    incident_pattern:
      "Compaction injuries split between two patterns. Acute pattern — roller operator backs over a foot worker who stepped behind to fix a low spot. Pad foot rollers and smooth drums are some of the heaviest equipment on a grading job and they don't stop in the last 6 feet. Operator was looking forward, backup alarm beeped, worker had earbuds in or was distracted, and the close was too fast to react. Chronic pattern — hand-arm vibration syndrome from years of running walk-behind compactors without anti-vibration gloves and without breaks. Operator hands lose grip strength, fine motor control, and circulation. Career-shortening but invisible at 30 years old. The fix is no foot traffic behind a moving roller, anti-vibration gloves on every walk-behind, and 10-minute rotation off the equipment every hour.",
    hazards_reviewed:
      "Hand-arm vibration syndrome · Whole-body vibration on rollers · Struck-by walking compactor · Rollover on slopes · Noise above 85 dBA · Run-over by reversing roller",
    discussion_notes:
      "• Walk-behind compactors: maintain firm grip, anti-vibration gloves, no loose clothing.\n• Vibratory rollers: never operate on slopes greater than mfr-stated max.\n• Roller no-go zones marked; spotters at edges and tapers.\n• Backup alarms required; reversing on slope only with spotter.\n• Take 10-minute break per hour with vibrating equipment to mitigate HAVS.\n• Hearing protection required — most compactors exceed 85 dBA.",
    references_cited:
      "OSHA 1926.95 · NIOSH Hand-Arm Vibration · ACGIH TLV for vibration",
    action_items:
      "Anti-vibration gloves issued · Roller no-go zones marked · Hearing protection required · Operator rotation",
  },
  {
    key: "excavator_safety",
    domain: "grading",
    title: "Excavator Safety",
    category: "Tool / Equipment Specific",
    severity: "fatal_risk",
    incident_pattern:
      "Excavator fatalities are usually swing-radius crush events. The bucket and counterweight together create a 360° killer zone, and the worker in the killer zone usually has a reason for being there — measuring grade, sloping a wall, holding a stick for survey. The operator pivots to load the truck or reposition, the rear counterweight swings into the worker, and the worker is pinned against a slope or an adjacent piece of equipment. Secondary pattern is the quick-coupler bucket release — operator picks the bucket up and the coupler wasn't fully engaged, bucket drops on the laborer underneath. Quick-coupler failures killed dozens of workers industry-wide before the audible engagement standard came in. The fix is hard barricades on swing radius, no workers between excavator and any fixed object, and verified quick-coupler engagement before any lift.",
    hazards_reviewed:
      "Tipping on slopes · Struck-by bucket / counterweight · Crushed in swing radius · Cab fall on slope · Hydraulic line failure · Quick coupler disengagement",
    discussion_notes:
      "• Pre-shift walkaround; check tracks, undercarriage, hydraulics, fluids, cab attachments.\n• Operator buckles seat belt before start.\n• Swing radius marked / barricaded — workers stay outside.\n• Bucket on ground when loading trucks; never swing over operator cab.\n• Quick coupler: positive engagement verified before lifting.\n• Park on level ground, bucket down, key out, brake set when leaving cab.",
    references_cited: "OSHA 1926.602 · Manufacturer Operator Manual",
    action_items:
      "Pre-op inspection logged · Swing radius marked · Quick coupler verified · Park-out routine followed",
  },
  {
    key: "skid_steer",
    domain: "grading",
    title: "Skid Steer / CTL Safety",
    category: "Tool / Equipment Specific",
    severity: "fatal_risk",
    incident_pattern:
      "Skid-steer fatalities have a brutal signature pattern: the operator enters or exits the cab with the lift arms raised, and the arms drop. The lift-arm support pin wasn't installed, the hydraulic seal failed, or the operator bumped a lever stepping out. The arms come down in less than a second and crush the operator at chest level. OSHA's been clear on this for 20 years: enter and exit only with arms LOWERED and bucket flat. The other recurring pattern is the bystander run-over — skid steers and CTLs have zero rear visibility, the operator reverses in a tight pad, and a ground worker walking by gets caught. Backup alarm, spotter for congested reversing, and never enter under raised arms — those three controls eliminate 90% of fatalities.",
    hazards_reviewed:
      "Crushed by lift arms (entry/exit hazard) · Tipping on slope · Struck-by attachments · Run-over by reversing machine · Burns from exhaust/turbo · Quick attach disengagement",
    discussion_notes:
      "• Enter/exit ONLY with arms lowered and bucket flat — never under raised arms.\n• Seat belt and seat bar lowered before start.\n• Quick attach pins fully engaged — verify before lifting.\n• No riders. No standing on attachments.\n• Backing in congested areas requires spotter.\n• Park on level ground, arms down, bucket on ground.",
    references_cited:
      "OSHA 1926.602 · Manufacturer Operator Manual · NIOSH Skid Steer Bulletin",
    action_items:
      "Seat belt enforced · Quick attach verified · Spotter assigned · No riders briefed",
  },
];
