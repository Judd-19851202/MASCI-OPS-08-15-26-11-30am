// Domain: fall_protection · iter261 Phase H Batch 3 · 5 uplifted

export const TOPICS_FALL_PROTECTION = [
  {
    key: "fall_protection",
    domain: "fall_protection",
    title: "Fall Protection — General",
    category: "Hazard-Specific",
    severity: "fatal_risk",
    incident_pattern:
      "Falls are the #1 cause of construction fatalities, year after year. The pattern that recurs most often is not the worker who tried to do the right thing — it's the worker who tied off to something that wasn't an engineered anchor. A guardrail post. A piece of conduit. A small angle bracket. Anchor fails at 200 lb instead of holding 5,000 lb, and the worker falls with the gear still attached. The second pattern is the deployed-but-too-long lanyard — worker has the harness on, but the 6-foot lanyard with no SRL means the fall arrest doesn't engage until after they hit the deck below. Fall clearance math wasn't done. Pattern three is the unrescued suspended worker who develops suspension trauma within 15 minutes — gear worked, but no rescue plan, and the worker dies hanging from their harness. The fix is engineered anchors, fall-clearance math done before the work starts, and a rescue plan that names who gets the suspended worker down in under 15 minutes.",
    hazards_reviewed:
      "Falls from elevation · Falls into excavations · Falls through openings · Improper anchor failure · Struck-by falling tools · Suspension trauma",
    discussion_notes:
      "• 100% tie-off above 6 ft in construction.\n• Anchor points rated 5,000 lb minimum or engineered system.\n• Inspect harness / lanyard / SRL before EVERY use — no abrasion, cuts, deployed indicators, corrosion.\n• Calculate fall clearance — anchor + lanyard + free fall + deceleration + safety factor.\n• Rescue plan in place; suspended worker requires rescue within 15 minutes.\n• Tools tethered or in zipped pouches at height.\n• Guardrails, covers, barricades on every hole and edge.",
    references_cited: "OSHA 1926 Subpart M · OSHA 1926.501 · ANSI Z359",
    action_items:
      "Harnesses inspected · Anchor points identified · Rescue plan briefed · Holes covered · Tools tethered",
  },
  {
    key: "ladder_safety",
    domain: "fall_protection",
    title: "Ladder Safety",
    category: "Tool / Equipment Specific",
    severity: "serious_injury",
    incident_pattern:
      "Ladder injuries are some of the most common lost-time injuries in construction and the easiest to write off as 'just clumsy.' They're not clumsy — they're predictable. Pattern one is overreach — worker on an extension ladder leans out to the side to reach one more bolt instead of climbing down and moving the ladder. The center of gravity passes outside the rails and the ladder kicks out sideways. Worker falls 12 feet onto their hip or shoulder. Pattern two is the slide-out — base set on a smooth slab without anti-slip feet, ladder kicks out as the worker descends, fall is straight down. Pattern three is the electrocution — aluminum extension ladder leaned against a building, head contacts an overhead service drop on the way up. Worker becomes the path to ground. Fix: 4:1 angle, three points of contact, tied off at the top, fiberglass near anything electric, and the simple rule — if you have to lean, climb down.",
    hazards_reviewed:
      "Falls from ladder · Ladder slide-out · Tipping · Electrocution from overhead lines · Overreaching · Damaged rungs / rails",
    discussion_notes:
      "• Inspect every ladder before use — no cracks, bent rails, missing feet.\n• 4:1 angle rule for extension ladders.\n• Three points of contact; never carry tools up.\n• Extend 3 ft above landing point, secured at top.\n• Never the top two rungs of a stepladder; never the top of any extension ladder.\n• Non-conductive (fiberglass) only when working near electrical.\n• Don't reach beyond the side rails — get down and move it.",
    references_cited: "OSHA 1926 Subpart X · OSHA 1926.1053 · ANSI A14",
    action_items:
      "Ladders inspected · Defective ladders tagged · Anchor / tie-off where 6 ft+ · Fiberglass for electrical",
  },
  {
    key: "aerial_lift",
    domain: "fall_protection",
    title: "Aerial Lift / Boom Lift Operations",
    category: "Tool / Equipment Specific",
    severity: "fatal_risk",
    incident_pattern:
      "Aerial-lift fatalities split into two patterns. Pattern one is the ejection / catapult — operator drives the boom over uneven ground, the platform whips at the top, and the worker is launched out of the bucket. Tie-off would have caught the fall but the lanyard wasn't anchored to the manufacturer's hard point — it was clipped to a side rail. Pattern two is the crush-against-overhead — operator raises the bucket toward a steel beam or under a deck, doesn't realize the clearance is closing, gets pinned at chest level between the bucket rail and the structure. Worker can't reach the foot controls to back out. Industry-wide, both patterns are killed off by two controls: anchored tie-off to a manufacturer's point, and a second worker on the ground watching clearance who can hit the emergency lower from below. Operator never works alone in the bucket.",
    hazards_reviewed:
      "Falls from platform · Tip-over from overload or uneven ground · Struck-by overhead obstacle · Electrocution from overhead lines · Crushing between platform and structure",
    discussion_notes:
      "• Operator certified and authorized; pre-shift inspection completed.\n• Tie-off in bucket — full body harness, lanyard to manufacturer's anchor.\n• Outriggers (where equipped) fully extended on level ground.\n• Maintain 10 ft minimum from energized lines; more for higher voltage.\n• No climbing on rails or out of bucket — bucket is the only allowed work position.\n• Sound horn before moving; spotter when traveling near workers.",
    references_cited: "OSHA 1926.453 · ANSI A92 · Manufacturer Operator Manual",
    action_items:
      "Pre-shift inspection logged · Operator certified · Tie-off in bucket · Overhead clearance verified",
  },
  {
    key: "scaffold",
    domain: "fall_protection",
    title: "Scaffold Safety",
    category: "Tool / Equipment Specific",
    severity: "fatal_risk",
    incident_pattern:
      "Scaffold fatalities have one classic pattern that keeps repeating: scaffold gets erected by a crew that isn't qualified, the base plate sits on soft ground without mud sills, the height grows beyond the height-to-base ratio, the wind catches the platform on day three, and the whole structure tips. Workers on the top platform fall with the scaffold. Second pattern is the missing guardrail — scaffold was erected correctly, but a section was modified later to fit a wall feature and the guardrail came off and never went back on. Worker steps off the open edge during a routine task. Third is overloading — debris and material piled on the platform exceeds rated capacity, planks deflect or break. The fix is the competent person inspection BEFORE each shift — engineered base, full guardrails, rated capacity not exceeded, and qualified erectors only.",
    hazards_reviewed:
      "Falls from scaffold · Scaffold collapse from improper erection · Struck-by falling material · Electrocution near power lines · Tipping from inadequate base",
    discussion_notes:
      "• Erected, modified, or dismantled only by qualified persons under competent person supervision.\n• Daily inspection by competent person before each shift.\n• Guardrails on all open sides over 10 ft.\n• Toe boards, screens, or debris nets to prevent falling materials.\n• Base on mud sills or base plates on solid ground; height-to-base ratio per mfr.\n• Maintain 10 ft+ from overhead power lines.\n• Access via stairway, ladder tower, or built-in ladder — no climbing braces.",
    references_cited: "OSHA 1926 Subpart L · OSHA 1926.451",
    action_items:
      "Daily inspection logged · Guardrails / toe boards in place · Base verified · Access route in place",
  },
  {
    key: "bridge_overpass",
    domain: "fall_protection",
    title: "Bridge / Overpass Work",
    category: "Hazard-Specific",
    severity: "fatal_risk",
    incident_pattern:
      "Bridge and overpass falls have two killer signatures. First — the worker who goes over the edge of an open deck during a long pour or a long inspection task. By hour 8 the perimeter awareness fades, a worker steps too close to the fascia adjusting a form, and the fall is 40+ feet onto traffic, water, or rocks. Survivable rate is near zero. Second pattern — falling objects into live traffic below. Worker drops a wrench or a chunk of concrete from the deck. Hits a windshield at highway speed. Driver dies, project goes on the front page, lawsuits follow. Both patterns die under the same control set: perimeter PFAS or guardrail before any deck work begins, catch platforms / debris nets to protect lanes below, every tool tethered, and lane closure coordinated for any operation that could drop material.",
    hazards_reviewed:
      "Falls over edge · Falls through deck openings · Live traffic below or adjacent · Dropped objects to lanes below · Struck-by traveling traffic",
    discussion_notes:
      "• Perimeter fall protection BEFORE any deck work.\n• Catch platforms / debris nets to protect lanes below.\n• Tools tethered; small parts in zipped pouches.\n• Coordinate live-traffic closure below for any high-risk operation.\n• Edge work: positive anchor and PFAS — no lone-worker edge tasks.\n• Wind monitoring for high-mast operations.",
    references_cited: "OSHA 1926 Subpart M · AASHTO Bridge Construction · ANSI Z359",
    action_items:
      "Perimeter PFAS in place · Catch platform set · Tools tethered · Lane closure coordinated",
  },
];
