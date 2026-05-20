// Domain: general · iter261 Phase H Batch 5 · 20 topics (18 uplifted + 2 new)
// Cross-cutting operational topics. Each carries incident_pattern + severity.
// Note: stretch_flex and site_walk overlap conceptually (both daily-huddle adjacent).
// Both preserved for now; future cycle may merge into single 'daily_huddle' topic.

export const TOPICS_GENERAL = [
  {
    key: "demolition",
    domain: "general",
    title: "Demolition Operations",
    category: "Hazard-Specific",
    severity: "fatal_risk",
    incident_pattern:
      "Demolition fatalities cluster around premature collapse and hidden hazardous materials. The collapse pattern — a worker pulls a structural member that the engineering survey didn't flag as load-bearing, an upper floor or wall drops in seconds, and the crew below has no time to clear. The hazmat pattern — asbestos or lead paint not surveyed before demo, dust released into the work zone, the exposure shows up as a respiratory cancer 20 years later. Add overhead utility strikes from the bucket and fuel-line fires from torches, and you have an industry-wide fatality rate among the highest in construction. The fix is the engineering survey treated as a contract, hazmat abatement before mechanical demo, and a structural inspection of the remaining structure every single day.",
    hazards_reviewed:
      "Falls from height · Struck-by falling debris · Premature collapse · Asbestos / lead exposure · Silica dust · Fire from cutting / hot work · Utility strike on remaining lines",
    discussion_notes:
      "• Engineering survey required before demo — identify floors, walls, materials, utilities.\n• Hazmat survey — asbestos, lead, PCBs identified and abated before demo.\n• Utilities cut, capped, locked out before demo.\n• Drop zones barricaded; spotters at perimeter.\n• Dust controls — water suppression and respiratory PPE.\n• Hot work permits for any cutting, welding, torching.\n• Daily inspection of remaining structure for stability.",
    references_cited:
      "OSHA 1926 Subpart T · OSHA 1926.850 · OSHA 1926.1101 (Asbestos) · OSHA 1926.62 (Lead)",
    action_items:
      "Engineering survey complete · Hazmat survey complete · Utilities locked out · Drop zones marked · Hot work permits ready",
  },
  {
    key: "hot_work",
    domain: "general",
    title: "Hot Work — Welding, Cutting, Grinding",
    category: "Procedure / SOP",
    severity: "fatal_risk",
    incident_pattern:
      "Hot-work fires almost never start during the work. They start 20-45 minutes after the work stops, when the fire watch left, the crew left, and a smoldering ember finally reaches flammables. The pattern: spark from grinding falls into a tarp pile or oily rag bin, smolders quietly while the crew breaks for lunch, ignites 30 minutes after they leave, and the building or fuel tank goes up. NFPA tracked this for decades — the post-work watch is when fires actually erupt. The other recurring pattern is the cylinder rupture from improper storage — oxygen and acetylene stored together, cylinder tips and snaps off the regulator, becomes a rocket. The fix is the hot work permit, fire watch DURING and 30 minutes AFTER, combustibles cleared or shielded, and cylinders chained upright with 20 feet between oxygen and fuel.",
    hazards_reviewed:
      "Fire / explosion · Burns · UV / IR exposure (arc flash) · Welding fume inhalation · Hot slag igniting combustibles · Compressed gas cylinder rupture",
    discussion_notes:
      "• Hot Work Permit required and on site for any cutting/welding/grinding outside designated shop area.\n• Fire watch posted with extinguisher during AND 30 minutes after work.\n• Combustibles within 35 ft removed or shielded with welding blankets.\n• Cylinders chained upright, caps on, oxygen and fuel separated by 20 ft or 5-ft non-combustible barrier.\n• Eye protection — shade matched to amperage; bystanders shielded.\n• Ventilation or supplied air for galvanized, cadmium, or coated metal.",
    references_cited: "OSHA 1926 Subpart J · OSHA 1926.352 · NFPA 51B · ANSI Z49.1",
    action_items:
      "Hot work permit signed · Fire watch assigned · Combustibles cleared · Extinguisher staged · Cylinders secured",
  },
  {
    key: "forklift_telehandler",
    domain: "general",
    title: "Forklift / Telehandler Operations",
    category: "Tool / Equipment Specific",
    severity: "fatal_risk",
    incident_pattern:
      "Forklift and telehandler fatalities follow two scripts. Script one — the tipover. Operator picks a load near the rated capacity at retracted boom, then extends the boom to set the load high; capacity at extension is 30-50% of capacity at retracted, the load chart shows it, the operator didn't check, the machine goes over sideways. Operator gets crushed because the seat belt wasn't on. Script two — pedestrian struck-by. Operator backs up in a congested yard, blind spot covers the worker walking past, alarm beeps but the worker has earbuds in. Both die under the same controls: certified operator, load chart consulted, outriggers extended at full boom, seat belt on, spotter for any movement near pedestrians.",
    hazards_reviewed:
      "Tipping (loaded or unloaded) · Struck-by load · Run-over of pedestrians · Falls from forks (no riders) · Overhead clearance contact · Load too high to see over",
    discussion_notes:
      "• Operator certified (3-year cert + evaluation).\n• Pre-shift inspection logged.\n• Capacity at boom extension is LESS than at retracted — read the chart.\n• Load behind heel of forks; tilt back during travel.\n• Travel forks low, tines about 6 in. above ground.\n• Backing on ramps with load uphill; no riders ever.\n• Outriggers required for telehandler at full reach.",
    references_cited: "OSHA 1926.602 · OSHA 1910.178 · ANSI/ITSDF B56.6 · ANSI/ITSDF B56.1",
    action_items:
      "Operator cert current · Capacity chart on machine · Outriggers procedure · No-riders rule briefed",
  },
  {
    key: "ppe_general",
    domain: "general",
    title: "PPE — Daily Compliance Review",
    category: "Procedure / SOP",
    severity: "serious_injury",
    incident_pattern:
      "PPE failure incidents almost never happen because the worker didn't know the requirement. They happen because the PPE was off for 'just one minute' — hard hat off because the cab is air-conditioned, glasses off because they fogged, hi-vis off because it was hot, gloves off to feel a fitting. That's the minute the incident happens. Pattern two — wrong PPE for the hazard. Class 2 hi-vis used for night work where Class 3 is required, basic safety glasses used during grinding where a face shield is needed, leather gloves used near chemicals where nitrile is required. The fix is the foreman who treats PPE as the floor, not the goal — and a culture where 'I'll be right back' isn't a free pass to remove the gear.",
    hazards_reviewed:
      "Head injury · Eye injury · Hearing loss · Foot injury · Hand laceration · Crush injury · Hi-vis non-compliance leading to struck-by",
    discussion_notes:
      "• Hard hat — Type II for traffic / impact zones; replace every 5 years or after impact.\n• Safety glasses with side shields — ANSI Z87 minimum.\n• Hi-vis Class 2 day / Class 3 night for all roadway work.\n• Steel or composite toe boots — no athletic shoes.\n• Cut-resistant gloves for sharp / abrasive work.\n• Hearing protection wherever noise > 85 dBA TWA.\n• PPE inspected before use; damaged PPE removed from service.",
    references_cited: "OSHA 1926 Subpart E · OSHA 1926.95 · ANSI Z87 / Z89 / Z41",
    action_items:
      "PPE inventory checked · Damaged PPE replaced · Hi-vis class verified · Hearing protection available",
  },
  {
    key: "stop_work",
    domain: "general",
    title: "Stop Work Authority",
    category: "Procedure / SOP",
    severity: "fatal_risk",
    incident_pattern:
      "The fatal pattern that Stop Work Authority is designed to break is the 'I had a bad feeling but kept going' moment. Every after-action review of a serious incident in this industry has the same line in it somewhere: someone on the crew thought something was wrong, didn't say anything, and the worker died. The fix isn't a poster — it's a foreman who has demonstrably backed up a crew member who stopped work in the past, so the rest of the crew believes they actually can. Stop Work is cultural muscle memory. The crews that have it in their bones have fewer fatalities; the crews that have it on paper but not in practice are the ones that keep showing up in the OSHA reports.",
    hazards_reviewed:
      "Imminent danger ignored · Production pressure overriding safety · Hazardous condition allowed to escalate · Near-miss not reported",
    discussion_notes:
      "• EVERY crew member has the authority and the responsibility to stop work for any safety concern.\n• No one will be retaliated against, ever, for stopping work in good faith.\n• Process: Stop. Notify. Correct. Resume. — all four steps.\n• Document the stop-work event so we can learn from it.\n• Stop work covers your own work, your crew, the public — anyone exposed.\n• If you're not sure, stop. Better to lose 5 minutes than a coworker.",
    references_cited: "OSHA General Duty Clause 5(a)(1) · MASCI Stop Work Policy",
    action_items:
      "Stop Work poster visible · Crew acknowledged authority · Recent stop-work events reviewed",
  },
  {
    key: "near_miss",
    domain: "general",
    title: "Near-Miss Reporting",
    category: "Procedure / SOP",
    severity: "serious_injury",
    incident_pattern:
      "The same near-miss happens 3-10 times before it becomes a real injury. That's not statistics in the abstract — that's the pattern from MASCI's own incident reviews and from every safety study going back 50 years. Worker drops a wrench from the deck, lands 4 feet from a coworker, nobody reports it, two weeks later the same drop hits someone's hard hat, then a month after that the same setup kills a worker. The fix is reporting the FREE lessons — the close calls where nobody got hurt. They get tracked, the trends get fixed, the actual injury never happens. The crews that report near-misses honestly have fewer real injuries; the crews that suppress them are the ones generating the next OSHA log.",
    hazards_reviewed:
      "Recurring near-misses leading to actual injury · Unreported hazards · Trend data lost · Culture of silence",
    discussion_notes:
      "• A near-miss is a free lesson. Treat it like an injury you got lucky on.\n• Report any unsafe act, unsafe condition, or close call — same shift.\n• Anonymous reporting available; no retaliation.\n• MASCI tracks near-misses for trends — this is how we prevent the next incident.\n• Don't blame the worker; fix the condition or process.\n• Examples: dropped tool from height, vehicle intrusion, suspended load swing wide, almost-trip-and-fall.",
    references_cited: "OSHA VPP · ANSI Z10 · MASCI Near-Miss Procedure",
    action_items:
      "Near-miss form available · Reporting reviewed · Recent reports discussed · Corrective actions tracked",
  },
  {
    key: "stretch_flex",
    domain: "general",
    title: "Stretch & Flex / Daily Huddle",
    category: "Stretch & Flex",
    severity: "lost_time",
    incident_pattern:
      "Most soft-tissue injuries in construction happen in the first 90 minutes of the shift. Worker climbs out of the truck cold and stiff, jumps straight into shoveling or lifting, and the back or shoulder gives at 7:30 a.m. The injury logs at MASCI and across the industry show the same morning concentration. Stretch & Flex isn't about flexibility — it's about getting blood into cold muscles before they're asked to do the work. Five minutes saves a back injury that ends a career. The crews that skip it have measurably higher back/shoulder/knee claims. The huddle piece matters too — the brief where weather, fit-for-duty, and today's hazards get named before anyone touches a tool.",
    hazards_reviewed:
      "Strains and sprains · Soft-tissue injuries · Cold muscle injury · Repetitive motion · Slips/trips/falls during first hour of shift",
    discussion_notes:
      "• 5-minute stretch routine before work — neck, shoulders, back, hips, hamstrings.\n• Walk through today's task list and identify anything new or unusual.\n• Confirm crew assignments and equipment for the shift.\n• Identify weather concerns (heat, cold, lightning, wind, rain).\n• Confirm everyone is fit for duty — no impairment, illness, or fatigue concerns.\n• Quick safety reminder relevant to today's work.",
    references_cited: "MASCI Daily Huddle SOP · NIOSH Ergonomics",
    action_items:
      "Stretch routine completed · Today's tasks briefed · Weather check · Fit-for-duty confirmed",
  },
  {
    key: "slips_trips",
    domain: "general",
    title: "Slips, Trips & Falls (Same-Level)",
    category: "Hazard-Specific",
    severity: "serious_injury",
    incident_pattern:
      "Same-level falls are the most common injury type in heavy civil — usually the ones nobody talks about because they don't make OSHA reports. Worker catches a stringline with a toe, lands wrong on a wrist, six weeks of light duty. Worker steps off a slope onto loose riprap, ankle rolls, six months of PT. The fatal version exists too — worker carrying a piece of pipe trips over a hose, falls onto a rebar cap, impalement. The injuries are predictable: rebar, hoses, stringlines, soft spots, ice, oil sheen, debris piles. The fix is housekeeping rotated through the day, not just at end-of-shift — and aggressive-tread boots replaced when they polish smooth.",
    hazards_reviewed:
      "Slip on wet/oily/icy surfaces · Trip on hoses, rebar, debris · Fall on uneven terrain · Twisted ankle from holes / soft spots · Carrying load while walking",
    discussion_notes:
      "• Most common injury cause on heavy civil — and most preventable.\n• Walking surfaces clear of hoses, cords, rebar — coil and stack.\n• Walk paths defined and marked through the work site.\n• Boots with aggressive tread; replace when worn.\n• Don't carry loads that block your view of feet.\n• Salt/sand or sweep ice and debris.\n• Holes covered or barricaded — flag uneven ground.",
    references_cited: "OSHA 1926.25 · OSHA 1926.501 · NIOSH STF",
    action_items:
      "Walk paths marked · Cords/hoses managed · Holes covered · Walking surfaces maintained",
  },
  {
    key: "hand_injury",
    domain: "general",
    title: "Hand Injury Prevention",
    category: "Hazard-Specific",
    severity: "serious_injury",
    incident_pattern:
      "Hands are the most-injured body part in construction. The pattern that recurs is reaching with bare hands into a pinch point because gloves were 'in the way' — pulling a tape measure into a fitting, guiding a rebar bundle, freeing a stuck bolt. The hand goes where the energy is, and the result is a crush injury or a degloving. Amputations from rotating equipment are smaller in count but life-changing — worker reaches into a moving conveyor or saw to clear a jam without LOTO. The fix is gloves matched to the hazard (cut-resistant for sharp, impact-rated for heavy material), tools used to position instead of hands, and LOTO before any rotating-equipment service. 'Just for a second' is the line that costs fingers.",
    hazards_reviewed:
      "Lacerations · Crush injuries (pinch points) · Punctures · Burns · Amputations from rotating equipment · Repetitive strain",
    discussion_notes:
      "• Match the glove to the hazard — cut-resistant for sharp, chemical for chemical, impact for impact.\n• Identify pinch points before reaching — use tools to position, not hands.\n• Push, don't pull — when pulling fails, your hand goes into what you're pulling against.\n• Never touch a moving blade, drum, conveyor — LOTO before service.\n• Inspect tools daily; remove damaged tools from service.\n• Take a knee or use a stable platform for fine work.",
    references_cited: "OSHA 1926.95 · BLS Injury Statistics · MASCI Hand Safety Policy",
    action_items:
      "Task-appropriate gloves issued · Pinch points identified · Tools inspected · LOTO procedures briefed",
  },
  {
    key: "hearing_conservation",
    domain: "general",
    title: "Hearing Conservation",
    category: "Hazard-Specific",
    severity: "serious_injury",
    incident_pattern:
      "Noise-induced hearing loss is the most under-counted occupational injury in construction. It happens gradually, painlessly, and by the time a worker notices the TV needs to be louder and they're missing the punchline of jokes, the high-frequency hearing is already gone — permanently. Most heavy iron and most cutting/grinding operations exceed 85 dBA TWA. The pattern is the worker who used to wear plugs in their 20s, got out of the habit in their 30s 'because it didn't seem that loud,' and at 50 needs hearing aids. Career-shortening but invisible until it's irreversible. The fix is plugs OR muffs (BOTH for jackhammer, milling drum, demolition), worn whenever the noise crosses the threshold, and the annual audiogram that catches the early shift before it becomes loss.",
    hazards_reviewed:
      "Permanent noise-induced hearing loss · Tinnitus · Communication difficulty masking other hazards · Cumulative damage over career",
    discussion_notes:
      "• OSHA action level 85 dBA TWA — most heavy iron exceeds this.\n• Earplugs OR earmuffs — both for impact noise (jackhammer, milling drum, demolition).\n• Replace foam plugs daily; clean reusables daily.\n• Annual audiogram per the hearing conservation program.\n• Watch for early signs: ringing in ears, having to turn up TV, missing conversations.\n• Quiet hand signals during high-noise work; pre-arrange comms.",
    references_cited: "OSHA 1926.101 · OSHA 1910.95 · NIOSH REL",
    action_items:
      "Hearing protection available · Worn during high-noise work · Annual audiogram scheduled",
  },
  {
    key: "respiratory_protection",
    domain: "general",
    title: "Respiratory Protection",
    category: "Procedure / SOP",
    severity: "serious_injury",
    incident_pattern:
      "Respiratory exposure incidents have the longest delay between cause and effect of any safety hazard in construction. Worker grinds concrete or breathes asphalt fume on hot days through their 20s and 30s, doesn't wear the respirator because it's sweaty and 'the dust isn't that bad.' Silicosis or lung cancer shows up in their 50s. By then the exposure was 20 years ago and the worker has no recourse. Pattern two — the wrong cartridge. Worker grabs a P100 thinking it'll handle solvent vapors; it won't, organic vapor needs an OV cartridge. They smell the solvent through the mask, think it's a fit issue, swap to a different mask but still wrong cartridge. The fix is fit-test current, cartridge matched to contaminant via SDS, clean-shaven seal surface, and the discipline to actually wear it.",
    hazards_reviewed:
      "Silica · Asbestos · Welding fumes · Asphalt / paint solvents · Diesel exhaust · CO · Mold / dust · Inadequate fit allowing exposure",
    discussion_notes:
      "• Respirator required when engineering controls are insufficient.\n• Annual fit testing — quantitative or qualitative — recorded.\n• Medical clearance before respirator use.\n• Match cartridge to contaminant — P100 for particulates, OV for organic vapors.\n• Inspect respirator before each use; user seal check every donning.\n• Beards / facial hair break the seal — clean shave at sealing surface.\n• Cartridges have service life — change per the schedule.",
    references_cited: "OSHA 1910.134 · OSHA 1926.103 · NIOSH respirator certification",
    action_items:
      "Fit tests current · Cartridges in stock · Seal-check procedure briefed · Schedule for cartridge change",
  },
  {
    key: "hazcom_sds",
    domain: "general",
    title: "Hazard Communication / SDS",
    category: "Procedure / SOP",
    severity: "serious_injury",
    incident_pattern:
      "HazCom incidents happen when a worker grabs an unlabeled container thinking it's one thing and it's another. Pattern one — the transfer container. Foreman decanted gasoline into a windshield-washer-fluid jug last week to save a trip, didn't label it; new worker grabs it thinking it's washer fluid, sprays into a hot engine compartment, fire. Pattern two — the storage incompatibility. Chlorine bleach and ammonia-based cleaner stored next to each other in a storage trailer, a spill mixes them, chloramine gas in a confined space. The fix is unglamorous: every container labeled, every chemical with an SDS within 30 seconds of where it's used, and segregated storage that respects the SDS warnings (flammables apart from oxidizers, acids apart from bases).",
    hazards_reviewed:
      "Chemical exposure from unknown product · Wrong PPE for chemical · Storage incompatibilities (flammable + oxidizer) · Improper disposal · Pictograms misunderstood",
    discussion_notes:
      "• Every chemical on site has an SDS — readily accessible.\n• Read SDS before first use: hazards, PPE, storage, first aid, spill response.\n• Container labels intact and legible — no unmarked transfer containers.\n• 9 GHS pictograms — know what each one means.\n• Storage segregation: flammables apart from oxidizers, acids apart from bases.\n• Disposal per SDS and EPA / state requirements — not into storm drains.",
    references_cited: "OSHA 1926.59 · OSHA 1910.1200 · GHS",
    action_items:
      "SDS binder current · Labels checked · Storage segregation verified · Disposal location identified",
  },
  {
    key: "site_walk",
    domain: "general",
    title: "Daily Site Walk / Hazard Assessment",
    category: "Procedure / SOP",
    severity: "serious_injury",
    incident_pattern:
      "Conditions change overnight. Rain fills a trench, the storm drops a barricade, a passerby pulls cones for fun, a subcontractor relocates a piece of equipment without telling anyone, a vehicle clipped a sign at 2 a.m. The foreman who walks the site BEFORE the crew arrives catches all of it; the foreman who skips the walk learns about it the hard way when a worker steps where they shouldn't. The pattern that recurs — water in an excavation that the crew assumes is fine, sloughing soils, collapse during the workday because soil saturation changed the strength overnight. Same with frost in winter — what was stable yesterday is loose today. The fix is the 15-minute walk before any crew touches a tool, with corrections made and briefed at huddle.",
    hazards_reviewed:
      "New hazards from yesterday's work · Weather-induced changes (water, frost, wind damage) · Equipment / material moved · Public encroachment · Utility work since last shift",
    discussion_notes:
      "• Foreman walks the entire work zone before crews start.\n• Look for anything new or different from yesterday: water in trench, displaced barricades, knockdowns, theft, vandalism.\n• Verify protective systems still in place.\n• Check for trip hazards from overnight equipment / material movement.\n• Reset / replace anything missing or damaged before crews enter.\n• Document and brief findings to crew at huddle.",
    references_cited: "MASCI Site Walk SOP · OSHA Competent Person",
    action_items:
      "Walk completed before crews start · Findings briefed · Corrections logged",
  },
  {
    key: "housekeeping_cleanup",
    domain: "general",
    title: "End-of-Shift Cleanup & Housekeeping",
    category: "Procedure / SOP",
    severity: "serious_injury",
    incident_pattern:
      "The shift-end housekeeping shortcut creates three predictable next-day problems. One — trip hazards left out turn into morning slips when the crew arrives in low light. Two — open excavations or unguarded edges left under poor barricading become a public injury overnight (kids find construction sites, drunk drivers find construction sites). Three — tools and small equipment left out get stolen, and the next day's job stops for 90 minutes while replacements arrive. The fix is the 15-minute discipline at end of every shift — non-negotiable. Tools locked up, openings covered or barricaded with lights, MOT verified for night configuration, and a final walk of the site by the foreman.",
    hazards_reviewed:
      "Trip hazards from material left out · Theft of unsecured tools / equipment · Public injury from open hazards overnight · Storm drain contamination from spills · Vandalism / encroachment",
    discussion_notes:
      "• 15 minutes of housekeeping at end of every shift — non-negotiable.\n• Tools and small equipment locked up; large equipment parked safely.\n• Open trenches / structures covered, barricaded, lighted.\n• MOT devices restored to night-time configuration; lights checked.\n• Trash and debris collected; no plastic / waste left to blow into storm drains.\n• Walk the site one last time before leaving.",
    references_cited: "OSHA 1926.25 · MASCI Housekeeping Standard",
    action_items:
      "Tools secured · Excavations covered/lit · MOT verified · Walk-through completed",
  },
  {
    key: "new_hire_orientation",
    domain: "general",
    title: "New Hire / New-to-Site Orientation",
    category: "Procedure / SOP",
    severity: "fatal_risk",
    incident_pattern:
      "New hires and workers new to a site have injury rates 3-5x higher in the first 30 days than experienced workers. The pattern is consistent across the industry: the new worker doesn't know which trench has been benched, doesn't know which gate the trucks use, doesn't know that the south end of the site has an active overhead line, doesn't know that the swing radius on the excavator at the corner is the killer zone. They walk into something an experienced worker would have skirted. Pattern two — the new hire who's afraid to use Stop Work Authority because they're new. They see something wrong, they don't speak up because they don't want to look stupid on day three. The fix is the formal orientation with a site walk, the buddy assignment for 1-3 days, and explicit reinforcement that Stop Work belongs to them from minute one.",
    hazards_reviewed:
      "Unfamiliarity with site hazards · Unknown equipment / procedures · Higher injury rate in first 30 days · Missed PPE / training requirements · Cultural mismatch on Stop Work",
    discussion_notes:
      "• EVERY new hire and EVERY person new to this site gets a site-specific orientation.\n• Walk the site, point out hazards, evacuation routes, first-aid kit, fire extinguishers.\n• Review project-specific TCP, JHP for their crew, and any active permits.\n• Reinforce Stop Work Authority — they have it from minute one.\n• Pair with experienced buddy for first 1-3 days.\n• Confirm required certs / training current before they start.",
    references_cited: "OSHA 1926.21 · MASCI New Hire Procedure",
    action_items:
      "Site orientation completed · Buddy assigned · Training records verified · Stop Work Authority briefed",
  },
  {
    key: "subcontractor_coordination",
    domain: "general",
    title: "Subcontractor Coordination",
    category: "Procedure / SOP",
    severity: "fatal_risk",
    incident_pattern:
      "Multi-employer fatalities follow a signature pattern: each contractor knows their own hazards but doesn't know what the other contractors are doing. Sub A is excavating; Sub B is doing overhead utility work above the same area. Sub A doesn't know Sub B is up there until something falls. Or — Sub C is doing hot work in one corner, Sub D is fueling equipment in the next corner, the vapors find the spark. OSHA's multi-employer citation policy holds the GC accountable for what the subs do because the GC is the only entity that sees the whole picture. The fix is the daily coordination meeting — who's where, what activities, what conflicts. Subs follow MASCI standards or higher, never lower; Stop Work Authority extends to every worker regardless of badge.",
    hazards_reviewed:
      "Conflicting work activities · Unfamiliar with each other's hazards · Different safety standards · Communication breakdown · Schedule pressure overriding sequence",
    discussion_notes:
      "• Every sub onsite has had pre-mob safety review with MASCI.\n• Daily coordination meeting — who's where, what activities, conflicts identified.\n• Subs follow MASCI safety standards or higher — never lower.\n• MASCI Stop Work Authority extends to ALL workers regardless of employer.\n• JHP / pre-task plan shared between conflicting trades.\n• Incidents reported to MASCI same day.",
    references_cited: "OSHA Multi-Employer Citation Policy · MASCI Subcontractor Pre-Qual",
    action_items:
      "Sub safety reps identified · Daily coordination scheduled · Stop Work Authority extended · JHPs cross-shared",
  },
  {
    key: "emergency_action_plan",
    domain: "general",
    title: "Emergency Action Plan / Evacuation",
    category: "Procedure / SOP",
    severity: "fatal_risk",
    incident_pattern:
      "Emergency-action failures during real events follow predictable scripts. Worker collapses from heat stroke; the crew calls 911 but can't give the dispatcher the actual address because the project number isn't the same as the cross-street address. Ambulance loses 8 minutes finding the gate. By the time they arrive the worker is gone. Or — fire breaks out near a fuel truck; crew evacuates but nobody does the headcount at the assembly point. Two workers thought to be evacuated are actually still inside the trailer. The fix is the EAP posted on every site with the 911 address, the gate access info, the assembly point, and the buddy or sign-in system that confirms every worker accounted for. Drill it every 90 days because nobody remembers a plan they've never practiced.",
    hazards_reviewed:
      "Site-wide emergencies (fire, gas leak, severe weather, active threat) · Inadequate evacuation · Failure to account for personnel · Blocked emergency egress · Delayed 911 response",
    discussion_notes:
      "• Every site has a posted EAP — assembly point, primary and secondary evacuation routes, 911 directions, on-site emergency contacts.\n• Account for ALL personnel at the assembly point — buddy system or sign-in.\n• Never re-enter for tools, vehicles, or material.\n• 911 caller stays on line; provide site address and gate access info.\n• Equipment ops shut down equipment safely if time allows; otherwise evacuate immediately.\n• Drill the EAP every 90 days or after major site changes.",
    references_cited: "OSHA 1926.35 · NFPA 101 · State / Local Emergency Management",
    action_items:
      "EAP posted · Assembly point known · 911 address verified · Drill scheduled",
  },
  {
    key: "fire_prevention",
    domain: "general",
    title: "Fire Prevention & Extinguisher Use",
    category: "Procedure / SOP",
    severity: "fatal_risk",
    incident_pattern:
      "Construction-site fires usually start small and get big in a hurry. Most start at one of three places: a fuel point where vapor finds an ignition source, a hot-work area where the fire watch left too early, or a piece of equipment where a hydraulic line failed and sprayed onto a turbo. The pattern that kills workers is the untrained extinguisher response — worker grabs an extinguisher for a fire that's already too big, depletes the bottle in 8 seconds, gets cornered. Extinguishers are for wastebasket-sized fires with a clear escape path. Bigger than that, get out and call 911. The other pattern is the wrong extinguisher — ABC dry chemical on a grease fire doesn't work, water on an electrical fire kills the worker. Know what's at risk where the extinguisher is staged, and know when to walk away.",
    hazards_reviewed:
      "Hot work ignition · Fuel spill / vapor ignition · Smoking near flammables · Improper extinguisher selection · Untrained worker fighting fire · Vehicle/equipment fire",
    discussion_notes:
      "• Combustibles 35 ft+ from any hot work; extinguisher staged.\n• ABC dry chemical for most jobsite fires; CO2 for electrical; foam for fuels.\n• PASS: Pull, Aim, Squeeze, Sweep — only fight a fire smaller than a wastebasket and only with a clear escape path.\n• When in doubt — get out and call 911.\n• No smoking around fuel, grease, or solvents — designated areas only.\n• Inspect all extinguishers monthly; recharge after any use.",
    references_cited: "OSHA 1926 Subpart F · NFPA 10 · NFPA 51B",
    action_items:
      "Extinguishers inspected · PASS technique briefed · Designated smoking areas · Hot work permits in use",
  },
  {
    key: "general_lone_worker_field",
    domain: "general",
    title: "Lone Worker / Field Solo Operations",
    category: "Hazard-Specific",
    severity: "fatal_risk",
    incident_pattern:
      "Lone-worker fatalities have the cruelest pattern in construction: an incident happens and nobody knows for hours. Driver pulls off the shoulder for what should be a 5-minute check, slips and falls into a culvert or has a cardiac event, vehicle stays parked with hazards on for half a day before anyone notices. Surveyor walks an alignment alone, gets bitten by something venomous, has no phone signal, sits down in the brush and isn't found until the next morning. Estimator does a site visit at a closed project, falls into a partially-collapsed structure, has a fractured leg and a dead phone battery. The fix is mandatory check-in protocols — designated times, designated contacts, escalation procedure when check-in misses. Lone work without a check-in plan is what kills these workers, not the original incident.",
    hazards_reviewed:
      "Unwitnessed medical event · Unwitnessed slip/fall in remote area · No-comms zone for cell phone · Wildlife encounter alone · Vehicle breakdown in remote area · Lone work after dark · Missed check-in",
    discussion_notes:
      "• Every lone-worker assignment has a designated check-in schedule: e.g., 'I'll text at 10:00, 12:00, 2:00, and when I leave the site.'\n• Designated contact on the other end — supervisor, dispatcher, or partner. Not just 'someone.'\n• Escalation if check-in missed: contact attempts, then 911 if no response in 30 minutes.\n• Cell coverage verified before leaving the office. Note dead zones.\n• Vehicle stays accessible — keys in pocket, fuel above half, water in cab.\n• Hi-vis worn even for short out-of-vehicle exposures near roadways.\n• 'Quick check' that becomes a 45-minute task is the most dangerous pattern. Update the check-in if scope changes.\n• Wildlife awareness — snakes, alligators, dogs — when working alone.",
    references_cited: "OSHA General Duty Clause 5(a)(1) · MASCI Lone Worker SOP · ANSI/ISEA Z308",
    action_items:
      "Check-in schedule briefed · Designated contact named · Escalation procedure in place · Cell coverage verified",
  },
  {
    key: "general_line_of_fire",
    domain: "general",
    title: "Line of Fire Awareness",
    category: "Hazard-Specific",
    severity: "fatal_risk",
    incident_pattern:
      "Line of fire is the universal pattern under almost every struck-by and caught-between fatality in construction. The worker is in the wrong place at the wrong moment — between an excavator swing and a fixed object, behind a backing truck, under a suspended load, on the downhill side of stored material that shifts, in the trajectory of a tensioned line that snaps. Most fatalities aren't because the worker didn't know it was dangerous; they're because the worker didn't think the line of fire applied to them right then. 'I'm just stepping in for two seconds to tie this off.' The fix is mental discipline: before stepping into any position, ask 'if energy releases right now — bucket swings, line snaps, load drops, material shifts, machine moves — where does it go?' If you're in that path, change positions. Foremen and crew leads reinforce the habit until it's automatic.",
    hazards_reviewed:
      "Between equipment and fixed object · Under suspended load · Behind backing equipment · Inside swing radius · Tensioned-line snap-back zone · Downhill of stored material · Inside hose-whip zone on pressurized lines",
    discussion_notes:
      "• Before stepping anywhere, ask: 'If energy releases right now — load drops, bucket swings, line snaps, material shifts — where does it go?'\n• If you're in that path, MOVE before doing the task.\n• Suspended loads: never under, never in the swing arc.\n• Backing equipment: never behind without spotter contact AND alarm.\n• Tensioned lines (rigging, tow straps, banding): stand outside the snap-back zone (~1.5x the line length to each side).\n• Stored material on slopes: stand uphill, not downhill, even for 'just looking.'\n• Pressurized hoses (concrete pump, hydraulic, water blast): outside whip zone, always.\n• Crew lead reinforces the habit at huddle — 'where's the line of fire?' on every task.",
    references_cited:
      "OSHA Struck-By Fatalities Bulletin · OSHA Caught-Between Bulletin · MASCI Line of Fire SOP",
    action_items:
      "Line-of-fire question habit briefed · Tasks reviewed for line of fire · No-go zones marked · Foreman reinforcement during shift",
  },
];
