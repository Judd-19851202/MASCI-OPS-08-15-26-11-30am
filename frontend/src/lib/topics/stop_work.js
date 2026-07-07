// Domain: stop_work · TRACK 15.47 · Stop Work Authority — When and How to Stop Work
// Tone: field-real, laborer-comprehension test. 60 seconds.
// Co-located with the public-interaction series because the real-world
// incident that triggered the track had a moment where the work should
// have stopped and didn't.

export const TOPICS_STOP_WORK = [
  {
    key: "stop_work_authority",
    domain: "stop_work",
    title: "Stop Work Authority — When and How to Stop Work",
    category: "Stop Work Authority",
    severity: "fatality",
    incident_pattern:
      "Every fatal incident MASCI has investigated had the same data point in the chain: a moment, sometimes seconds long, where SOMEBODY knew it was wrong and didn't say it. Not because they didn't care. Because they didn't think they had the authority. They didn't think production would forgive them. They didn't think the foreman would back them. Stop Work Authority means EVERY person on the job — laborer, operator, foreman, super, PM — has the standing, the duty, and the protection to halt work the second the work goes unsafe. Not 'after the next pour.' Not 'after lunch.' Now. Examples from real MASCI incidents: a resident becoming aggressive at the trench edge, a hydro-vac coming up empty when it should have hit a known gas main, a backhoe operator who hasn't slept (third 12-hour day), a thunderhead at 3 PM, a near-miss in the previous 60 minutes that did not stop the operation. Each of those is a STOP. Stop now, talk in the cab, restart only after the unsafe condition is gone.",
    hazards_reviewed:
      "Fatality · Catastrophic equipment damage · Workplace violence escalation · Utility strike · Environmental release · Trench collapse · Crew injury · Reputational + legal consequences",
    warning_signs:
      "A crew member said something is wrong and got overruled\nA pre-shift item was checked off in 10 seconds without inspection\n'We'll fix it after this pour' / 'after this load' / 'after lunch'\nA piece of equipment is operating with an alarm on\nA utility one-call sticker is stale or missing\nA crew member is on their third 12-hour day\nThe weather rolled in and nobody mentioned it\nA member of the public is at the barricade and the work didn't stop",
    when_to_stop:
      "STOP IMMEDIATELY when ANY of these are true:\n• A member of the public becomes aggressive within reach of the crew or equipment\n• You see, hear, or are told there is a credible threat or weapon\n• A utility strike risk has changed (one-call sticker stale, hand-dig found nothing where a known utility should be, hydro-vac dry)\n• An excavation has cracking, sloughing, water in the trench, or a worker has expressed unease\n• Any piece of equipment has a safety alarm (overheat, low-oil, hydraulic fault, brake) — NOT a maintenance reminder\n• A near-miss occurred in the previous 60 minutes that has not been formally reviewed\n• A worker is visibly impaired (fatigue, medication, alcohol, emotional)\n• A storm cell is within 10 mi and approaching\n• An overhead utility, drone, or aircraft is closer than planned",
    who_can_stop:
      "EVERY person on the job. Without exception.\n• Laborer — yes, on day one, before they've signed their first PPE sheet\n• Operator — yes, of any piece, in any class\n• Foreman — yes, on any phase\n• Superintendent — yes, on any project\n• Safety — yes, on any sub, any tier\n• Project Manager — yes, including over the GC's protest\nIf the GC, Owner, or DOT pressures continuation: it's STILL STOP. Document the pressure separately. The pressure does not change the call.",
    how_to_stop:
      "1. Say it out loud. The words don't matter. 'Stop. I want a 2-minute reset.' / 'Stop, this isn't right.' / 'I'm calling a Stop Work.'\n2. Hand signal: open palm raised, then closed fist for hold. Same as the lift-and-rigging signal.\n3. Get everyone clear of the line of fire — back the excavator out of the trench, drop the load to a safe rest position, kill the engine.\n4. Crew gathers at a safe assembly point (typically the foreman's truck or the safety meeting tailgate).\n5. State the reason. Plain words.\n6. Decide together: what changes before we restart? Who confirms it changed?\n7. Document — pre-shift sheet gets a note + initials. Foreman calls super.",
    escalation_chain:
      "If the foreman won't honor the Stop Work:\n  → Call the Superintendent.\nIf the Superintendent won't honor:\n  → Call the Safety Manager.\nIf Safety won't honor (this should never happen):\n  → Call the Operations Manager.\nFinal escalation: Owner (Robert / Eric).\nRetaliation for a Stop Work call is grounds for termination of the retaliator — laborer, foreman, super, or PM.\nWritten retaliation report: HR + Operations.",
    restart_requirements:
      "Restart ONLY when ALL of these are true:\n1. The condition that triggered the stop has been corrected (utility located, weather passed, equipment fixed, public escorted out, worker rested, etc.).\n2. The person who called the Stop Work agrees the condition is corrected.\n3. The foreman has signed off in the pre-shift / JHA.\n4. The crew has been re-briefed on what changed.\n5. If a near-miss triggered the stop: an incident has been opened in ForgedOps.\nDocument restart time on the pre-shift form.",
    what_to_do:
      "1. Recognize the trigger from the 'When to Stop' list.\n2. Call it out — words, hand signal, both.\n3. Bring everyone to a safe assembly point.\n4. Talk it out. What changes?\n5. Restart only after restart checklist clears.\n6. Document.",
    what_not_to_do:
      "Do not 'just finish this load' / 'just this pour' / 'just this section.'\nDo not call a Stop Work as a tactic to slow production for unrelated reasons — it burns the call for everyone.\nDo not get into who is at fault during the stop — that is for the post-event review.\nDo not let the GC, Owner, or DOT override the call — document the pressure, hold the stop.\nDo not skip the restart sign-off — that is what makes the Stop Work defensible later.",
    supervisor_actions:
      "Back the call publicly. The first time you don't back a Stop Work call, you have killed the program. Document the call on the pre-shift, in the meeting, and in any incident that flows from it. If the call was unnecessary (judgment of safety after the fact), STILL back it publicly — coach the caller privately. Punishment of a stop-work caller is the fastest way to a fatality.",
    documentation:
      "Pre-shift sheet: Stop Work called at HH:MM by [Name]. Reason: [one line]. Restart at HH:MM after [what changed].\nIf the trigger was a near-miss, harassment, public confrontation, utility issue, or violence: open a ForgedOps incident with the right classification (see the relevant Public-Interaction topic).\nIf the trigger was equipment: equipment Pre-Op record + maintenance work order.\nIf the trigger was weather: log on the daily report.",
    corrective_actions:
      "Track # of Stop Work calls per project per month — UP is good (catching things), DOWN is suspicious.\nIf retaliation occurred: HR investigation within 48 hours; termination is on the table.\nIf the same trigger has caused a Stop Work twice on the same project: PM convenes a structural review.",
    read_aloud:
      "Listen — sixty seconds. If you see something that is about to go wrong, say STOP. Out loud. Open palm in the air. Doesn't matter if you've been here a day or twenty years. Doesn't matter if I'm here, or if the GC is here, or if the owner is here. You can stop the work. We will back you. Every time. If something gets fixed, we restart. If it doesn't get fixed, we don't restart. We have lost people because somebody knew it was wrong and didn't say it. We are not losing another one. Stop Work is your job. It is not optional. It is not for emergencies only. It is for the moment you think 'this isn't right.' Trust that moment.",
    references_cited:
      "OSHA Stop Work Authority (multiple programs — General Duty Clause) · ANSI/ASSP Z10 Section 5.1.4 · MASCI Stop Work Authority Policy · MASCI Workplace Violence Workflow",
    action_items:
      "Every crew briefed pre-shift on Stop Work · Pre-shift sheet has a Stop Work line · Foreman models the call at least once per project · No retaliation tolerated",
  },
];
