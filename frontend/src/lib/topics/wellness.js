// Domain: wellness · iter261 Phase H Batch 4 · 6 uplifted
// Tone discipline: experienced field leadership talking honestly about operational realities
// that affect judgment and safety. NOT corporate wellness, NOT therapy language, NOT poster fluff.

export const TOPICS_WELLNESS = [
  {
    key: "heat_stress",
    domain: "wellness",
    title: "Heat Stress / Hydration",
    category: "Hazard-Specific",
    severity: "serious_injury",
    incident_pattern:
      "Heat doesn't kill workers directly most of the time — it kills them through degraded judgment. The pattern: worker is mildly dehydrated by hour 4 of a hot day, gets a little sloppy on a backing call, misjudges the gap by 2 feet, gets struck-by. By hour 6 the same worker would be in heat exhaustion territory, but the incident already happened. Heat-stroke fatalities are smaller in number but follow a brutal script: the new hire or the returning worker not yet acclimatized works a full day at 95°F, refuses to admit they're struggling because it's day one, stops sweating around 2 p.m., collapses at 3 p.m. with a core temp of 106°F. By the time EMS arrives the brain damage is done. The fix has been the same for 40 years: water-rest-shade, 20% workload day one for unacclimatized workers, and a foreman who knows what 'stopped sweating' looks like.",
    hazards_reviewed:
      "Heat exhaustion · Heat stroke (medical emergency) · Dehydration · Reduced reaction time · Sunburn / UV exposure",
    discussion_notes:
      "• Water, rest, shade — the OSHA-NIOSH heat protocol.\n• 1 cup of water every 15-20 minutes during heavy work in heat.\n• Acclimatize new and returning workers — 20% workload day 1, increase 20% per day.\n• Buddy system — watch your partner for confusion, slurred speech, hot dry skin = heat stroke = 911.\n• Schedule heaviest work for cooler hours when feasible.\n• Heat index posted daily; protocol triggers at 80°F+ heat index.\n• Cool-down breaks in shade or AC every hour during high-heat days.",
    references_cited: "OSHA Heat Illness Campaign · NIOSH Criteria · OSHA-NIOSH Heat Tool",
    action_items:
      "Water and ice staged · Shade structure on site · Heat-index protocol posted · Acclimatization plan",
  },
  {
    key: "cold_stress",
    domain: "wellness",
    title: "Cold Stress / Hypothermia",
    category: "Hazard-Specific",
    severity: "serious_injury",
    incident_pattern:
      "Cold-stress incidents in our region usually show up during night paving in late fall, or storm cleanup after a freeze. The pattern isn't dramatic frostbite — it's slow judgment loss. Worker is cold and wet by hour 3, hands lose fine motor control, foreman radios for a tool swap and the worker fumbles a wrench off a deck onto a worker below. Or the operator's reaction time drops 20% from cold and they're 0.2 seconds slow on a backing-stop call. Hypothermia fatalities here usually trace back to someone getting wet — fell into a dewatering hole, took a hose blast to the chest, soaked their boots in standing water — and then continuing to work because the truck is at the other end of the job. Wet plus 45°F is more dangerous than dry plus 25°F. The fix is dry clothes within 100 feet, mandatory warming rotation when conditions slip, and a culture where 'I'm cold and wet' gets the worker sent to the truck without a fight.",
    hazards_reviewed:
      "Hypothermia · Frostbite · Reduced manual dexterity · Slips on ice · Cold shock from contact with ice water · Buried in collapsed snow",
    discussion_notes:
      "• Layered clothing: wicking base, insulating mid, wind/water-resistant outer.\n• Cover head, neck, hands, feet — most heat loss is from extremities.\n• Buddy system — frostbite first signs are subtle (numbness, white skin).\n• Warming area within 100 ft, hot drinks (no alcohol, limit caffeine).\n• Shorter work intervals at lower temps; rotate crew.\n• Watch for hypothermia: confusion, slurred speech, shivering — 911 + warm + stable.\n• De-ice walking surfaces before shift.",
    references_cited: "OSHA Cold Stress Bulletin · NIOSH Cold Stress · CDC Hypothermia",
    action_items:
      "Cold-weather PPE issued · Warming area set · Buddy system · De-icing supplies staged",
  },
  {
    key: "fatigue",
    domain: "wellness",
    title: "Fatigue & Drowsy Driving",
    category: "Hazard-Specific",
    severity: "fatal_risk",
    incident_pattern:
      "The single most likely way a MASCI worker dies from this job isn't on a paver, isn't in a trench, isn't under a piece of iron. It's the drive home after a 12-hour shift, on the interstate, at 5:30 a.m. The worker has had 4 hours of sleep, a high-stress shift, two coffees, and one energy drink. Microsleep hits at 65 mph somewhere between the job and the house. No skid marks. NHTSA has tracked this pattern for decades. The on-shift version is just as predictable — operator on hour 11 of a 12, blink rate drops, reaction time on a backing call goes from 0.4 to 0.9 seconds, and someone on the ground gets hit. The fix is unglamorous: 7-9 hours of real sleep before any shift over 8 hours, foreman pulls anyone showing the signs (irritability, glazed eyes, slow speech), and 'I'm too tired to drive home' gets the worker a couch or a ride instead of a casket. Coffee + cold AC is not a fix. It's a delay.",
    hazards_reviewed:
      "Drowsy driving (commute) · Reduced reaction time on equipment · Decision-making errors · Microsleep · Increased injury rate at end of long shifts",
    discussion_notes:
      "• Most likely fatal injury cause in our industry isn't on-site — it's the drive home.\n• 7-9 hours sleep is non-negotiable for safe operation.\n• Long shifts, night shifts, and consecutive 10s/12s elevate risk significantly.\n• Buddy system — say something if a coworker is showing signs of fatigue.\n• Pull over and nap if drowsy on the drive home — coffee + cold AC is a myth.\n• Report fatigue to foreman — better than a crash.",
    references_cited: "NIOSH Fatigue at Work · NHTSA Drowsy Driving · NSC",
    action_items:
      "Crew briefed on fatigue signs · Buddy check at end of shift · Sleep before long shifts emphasized",
  },
  {
    key: "drug_alcohol",
    domain: "wellness",
    title: "Drug & Alcohol Policy / Fit for Duty",
    category: "Procedure / SOP",
    severity: "fatal_risk",
    incident_pattern:
      "Impairment incidents on construction sites rarely look like the stereotype — drunk worker stumbling around. They look like the worker who took a leftover prescription painkiller for a back issue and is operating a finishing machine at 60% of their normal reaction time. Or the worker who used marijuana the night before, legal in their state, but is still impaired the next morning on a paver. Or the worker who's drinking a 32oz energy drink with caffeine plus a pre-workout supplement, hands shake, judgment narrow, makes a call they wouldn't make on a normal day. The fatal pattern usually involves two things: impairment plus a moving piece of iron. Pre-shift the worker felt fine. By 10 a.m. the impairment is showing in small ways the foreman almost catches. By noon the incident has happened. The fix is honest: disclose prescriptions that may impair, zero tolerance on company time for alcohol and recreational use including marijuana regardless of state law, EAP referral protected from punishment, and reasonable-suspicion testing when behavior shows it.",
    hazards_reviewed:
      "Impaired operation of equipment / vehicle · Reduced reaction time · Poor decision-making · Increased injury rate · Legal / DOT violations",
    discussion_notes:
      "• Zero tolerance for alcohol or drugs (including marijuana) on company time or DOT-covered roles.\n• Prescription meds — disclose to supervisor if they may impair operation.\n• Random testing per DOT and MASCI policy.\n• 'Fit for duty' = clear-headed, well-rested, healthy enough to do the work.\n• Reasonable suspicion testing if behavior, smell, or eyes suggest impairment.\n• Self-report and EAP referral protected — get help, don't hide.",
    references_cited:
      "DOT 49 CFR Part 40 · MASCI Substance Abuse Policy · OSHA Drug-Free Workplace",
    action_items: "Policy posted · Random testing schedule current · EAP contact info available",
  },
  {
    key: "bloodborne",
    domain: "wellness",
    title: "Bloodborne Pathogens & First Aid Response",
    category: "Procedure / SOP",
    severity: "serious_injury",
    incident_pattern:
      "Exposure incidents on construction sites usually happen in the first 5 minutes of a real injury, before anyone has time to think. A worker takes a deep laceration from a tie wire or a sharp edge, blood is everywhere, a coworker reaches in to apply pressure with bare hands because that's the human instinct. If the injured worker has Hepatitis B or C and the responder has a cut on their hand they didn't think about, the responder is now exposed. Industry pattern: most jobsite exposures happen NOT during sterile first-aid response but during the panic-driven first minute. The fix is muscle memory — gloves are stocked at every truck, the trained responder for each crew is known by name, and 'gloves first, then help' is drilled until it's automatic. Sharps — broken glass, tie wire stubs, rebar caps — go into a puncture-resistant container, not into a regular trash bag where the next worker reaches in and gets stuck.",
    hazards_reviewed:
      "Exposure to blood / OPIM · HIV / Hep B / Hep C · Improper PPE during response · Improper sharps handling · Failure to report exposure",
    discussion_notes:
      "• Treat ALL blood and body fluids as potentially infectious — universal precautions.\n• Disposable gloves, eye protection, mask if splash risk.\n• Clean spill with approved disinfectant; sharps in puncture-resistant container.\n• Wash hands thoroughly after any response, glove or no glove.\n• Report any exposure incident immediately — Hep B vaccine and follow-up available.\n• First-aid kit stocked, location known, trained responders identified.",
    references_cited: "OSHA 1910.1030 · OSHA 1926.50 (First Aid) · CDC BBP",
    action_items:
      "First-aid kit checked · Trained responders identified · Spill kit available · Reporting procedure briefed",
  },
  {
    key: "mental_health",
    domain: "wellness",
    title: "Mental Health & Suicide Prevention",
    category: "Other",
    severity: "fatal_risk",
    incident_pattern:
      "Construction has the second-highest suicide rate of any U.S. industry — about 4x the national average. The workers we lose to this don't look like the stereotype. They show up to work, do the job, joke with the crew, and then we hear about it on a Monday. The recognizable pattern from foremen who've seen it: worker becomes quieter over a couple weeks, starts skipping the after-work routine they used to like, drinks more, picks fights they wouldn't normally, or gives away tools and clothes that meant something to them. Then the call comes. The on-shift pattern is different but related — worker dealing with home stress, divorce, kid in trouble, money problems — carries it onto a paver or into a trench. Judgment narrows, the line of fire stops registering, and a worker who would normally never step into a swing radius does it because their mind is somewhere else. The fix is not posters. It's foremen and crew leads who know the signs, ask the direct question ('Are you OK? Are you thinking of hurting yourself?'), and know the two numbers: 988 for crisis, and the MASCI EAP for confidential help. Asking does not plant the idea. Asking has saved more lives in this industry than any single intervention.",
    hazards_reviewed:
      "Elevated suicide rate in construction · Stigma preventing help-seeking · Substance use as coping · Home stress carried onto site · Judgment degradation around equipment / live traffic · Crew grief after a loss",
    discussion_notes:
      "• Construction workers have one of the highest suicide rates of any U.S. industry — this is operational reality, not abstract.\n• Signs to know: withdrawal, mood change, increased drinking, giving away possessions, talk of being a burden.\n• Direct question is OK: 'Are you OK? Are you thinking about hurting yourself?' Asking does not plant the idea.\n• 988 — Suicide & Crisis Lifeline (call or text). MASCI EAP for confidential help.\n• Home stress carried onto site shows up as narrowed attention — line of fire, swing radius, backing calls all suffer.\n• Pull a worker out of a high-risk task if their head isn't on the job. Better than the alternative.\n• After a loss — crew grief is real. Talk about it, don't pretend it didn't happen.",
    references_cited: "CDC Construction Suicide Data · 988 Lifeline · MASCI EAP · CIASP",
    action_items:
      "988 / EAP info posted · Crew check-in encouraged · Foreman watching for signs · Direct-question discipline reinforced",
  },
];
