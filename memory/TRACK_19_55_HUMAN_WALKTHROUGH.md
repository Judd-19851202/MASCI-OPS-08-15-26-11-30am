# TRACK 19.55 · Human Walkthrough

Each persona was walked through the Fleet Unit Thread pilot. The
question tested for each: can they understand this unit in under 15
seconds?

## CEO / COO opens `/fleet/unit/412`
- Mission Overview names the unit, its operational health tier ("Critical / Attention Needed / Good"), why, timeline count, attention count.
- Attention section (Section 2) lists everything blocking the day.
- Operational Guidance button opens the certified Guidance Card.
- Verdict: **15-second read achieved.** CEO instantly knows if the unit is a story to escalate.

## Operations Manager
- Sees the exact same mission tier.
- Universal Action Queue lists max 5 concrete steps.
- Relationships section shows operator · project · WO · shop history — one click into each.
- Verdict: **No hunting.** Every dependency is on one page.

## Fleet Manager
- Opens the unit from Fleet Visibility (clicks the unit number chip).
- Sees availability tier + OOS status in Mission Overview.
- Section 8 Operational Intelligence surfaces the fleet_intelligence score, attention chip, trend.
- Verdict: **Same view leadership sees.** No portal-specific variant.

## Shop Manager
- Scrolls to Attention → sees open OOS / open defect items with severity chips.
- Clicks "Take action" → routed to `/shop/units/:unit/history` (existing Track 13.26 workflow).
- Verdict: **Direct action path preserved.**

## Dispatcher
- Sees "Currently out of service" node in the relationship graph.
- Knows immediately not to schedule this unit.
- Verdict: **Cross-portal readiness confirmed at a glance.**

## Project Manager
- Sees the Project node in the relationship graph — click routes to `/pm/command-center`.
- Sees which project this unit is currently associated with.
- Verdict: **No hunting across 5 portals.**

## Superintendent
- Sees attention + action queue with the "Assign or complete N open defects" line.
- Knows who to call (Shop Manager labelled as owner).
- Verdict: **Actionable, not descriptive.**

## Mechanic
- Sees the timeline section (Track 13.26 backbone) with every event in chronological order.
- Sees "Review recent inspection failure with mechanic" in the Action Queue.
- Verdict: **The mechanic reads the story of the unit from the same page everyone else reads.**

## Safety Director
- Sees safety-flavoured items ("Defect", "OOS") coloured red in the timeline.
- Sees Attention items rated CRITICAL/HIGH.
- Verdict: **Safety context is not siloed.**

## New employee (first day)
- Lands on the page from a Fleet Visibility link.
- Reads Mission Overview → knows this is a unit, understands its state.
- Reads Attention → knows what matters.
- Reads Action Queue → knows what to do.
- Reads Decision Boundary (via Guidance Card) → knows the platform never makes the call.
- Verdict: **No training required.** The Universal Thread teaches itself.

## Aggregate findings
- The 10-section standard reads identically to every persona.
- No section adds filler — empty states are honest.
- Every node is clickable · every action deep-links to an existing workflow · no dead ends.
- The pilot proves the standard: Employee / Project / Incident / Vendor / Asset threads can inherit the shell verbatim in future tracks.
