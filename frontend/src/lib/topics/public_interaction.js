// Domain: public_interaction · TRACK 15.46 / 15.47 · Public Interaction & Conflict De-Escalation
// Tone discipline: field-real, 5:30 AM read-aloud. No HR language.
// Schema-extended (TRACK 15.47): each topic now carries warning_signs,
// what_to_do, what_not_to_do, supervisor_actions, documentation,
// corrective_actions, and a read_aloud block the foreman can read
// directly to the crew. Existing fields (incident_pattern, hazards_
// reviewed, discussion_notes, references_cited, action_items) are
// preserved — older topic-reader code keeps working.

export const TOPICS_PUBLIC_INTERACTION = [
  {
    key: "angry_public_de_escalation",
    domain: "public_interaction",
    title: "Dealing With Angry Members of the Public",
    category: "Public Interaction & Conflict De-Escalation",
    severity: "serious_injury",
    incident_pattern:
      "Heavy-civil work happens in front of the public. People who live on the street we are tearing up, drivers whose commute we just rerouted, business owners whose driveway is blocked. The pattern when it goes wrong: a frustrated resident walks up to the foreman at 7:00 AM already angry from yesterday's noise. Foreman is busy, snaps back, voice rises, the resident escalates, the crew stops working to watch. Within 30 seconds a verbal confrontation is filmed by a third person and uploaded. In rare cases the situation goes physical — a thrown object, a shove, a weapon shown. The lesson: every public interaction is a potential incident. The crew member who responds with patience and a phone-call to the superintendent prevents a viral video, a workplace-violence report, and in the worst cases an injury.",
    hazards_reviewed:
      "Verbal confrontation · Aggressive behavior · Threat of physical violence · Weapons · Reputational harm · Workplace-violence incident · Personal injury",
    warning_signs:
      "Approach without eye contact then sudden eye contact · pointing finger · stepping past barricade · raised voice that gets LOUDER instead of louder-then-softer · clenched fists · phone held up to record · 'do you know who I am' · 'I pay your taxes' · referring to a weapon",
    what_to_do:
      "1. Lower your voice. Theirs goes up — yours goes down. It works.\n2. Hands visible, palms out, no pointing, half-turn (don't square up).\n3. Acknowledge the impact in their words: 'I hear you. This is affecting your day.'\n4. Route the complaint: 'Let me get my superintendent on the phone — they can give you the answers I can't.'\n5. If they won't disengage: walk back behind the barricade or to a crew vehicle.\n6. If a weapon shows, a credible threat is made, or you are touched: STOP. Retreat. Call 911. Then call the superintendent.\n7. Document immediately in writing: time, location, what was said, what was done, who else witnessed.",
    what_not_to_do:
      "Do not argue. You are not the decision-maker.\nDo not film them — let the company handle documentation.\nDo not post about it on social media — ever.\nDo not touch them, even to guide them.\nDo not say 'calm down' — it never works.\nDo not promise anything (schedule, money, access) you cannot deliver.",
    supervisor_actions:
      "Get on the phone within 2 minutes. Take ownership of the answer. If the encounter went verbal-only, file a Public-Interaction incident the same day with classification 'Public Interaction · Verbal Confrontation'. If physical contact occurred, file with classification 'Physical Contact' or 'Physical Assault' and call 911. Notify Operations Manager and Safety Manager directly.",
    documentation:
      "Open a ForgedOps incident under type 'Public / Third Party'.\nClassifications: Public Interaction + Verbal Confrontation (and Threat / Physical Contact / Workplace Violence if applicable).\nWitness rows: name + role + phone + email + statement for every crew member who saw it.\nIf police involved: agency, officer, badge, case number.\nPhotos: barricade position, residence address, witnesses (do not photograph the aggressor without consent).",
    corrective_actions:
      "Re-run this pre-shift topic with crew before next shift on the same project.\nPost superintendent phone number in every cab.\nIf same address has now generated two incidents: brief the entire crew + safety manager + project manager before the next shift on that project.",
    read_aloud:
      "Listen up — 60 seconds. If someone from the public walks up to you angry, here is what you do. ONE: lower your voice. TWO: hands open, don't point. THREE: tell them 'I hear you' — that is not agreement, that is just acknowledging. FOUR: tell them 'Let me get my supervisor on the phone.' FIVE: if they touch you, show a weapon, or say they want to hurt you — STOP, back up, call 911, then call me. You are not paid to argue. You are paid to come home tonight. We document EVERY interaction, even the small ones, because the small ones become the big ones.",
    references_cited:
      "OSHA Workplace Violence Prevention Guidance · MASCI Workplace Violence Policy · MASCI Incident Reporting SOP · Track 15.47 Workplace Violence Workflow",
    action_items:
      "Superintendent phone number posted in cab · Workplace-violence reporting form known · 'Walk away' rehearsed in pre-shift",
  },

  {
    key: "public_near_children",
    domain: "public_interaction",
    title: "Members of the Public Near Children",
    category: "Public Interaction & Conflict De-Escalation",
    severity: "serious_injury",
    incident_pattern:
      "School zones, parent pickup lines, parks, sidewalks. When the work is near children, the public watches differently. Parents project their child onto our crew at all times. A piece of plywood that falls inside our barricade — fine. The same plywood, in front of a parent who just saw their kid walk past — that parent will be at the foreman by the next morning. Worse: a child wanders into the work zone. Even with a parent visible, even with barricades. The pattern when it goes wrong: an operator backs up, a kid is 10 feet away outside the barricade, the parent loses it, the operator gets accused publicly. Cameras come out. The crew is now defending itself in a public forum it cannot win.",
    hazards_reviewed:
      "Child enters work zone · Parent fear escalation · Camera/social-media exposure · Backing equipment near pedestrians · Falsified accusations · Distracted operator",
    warning_signs:
      "Parent watching with phone out · child closer to barricade than the parent · school dismissal time approaching · 'is this safe?' questions from a parent · a parent calling a school administrator while watching the crew",
    what_to_do:
      "1. Before any backing or swinging movement, eyes on every pedestrian within 50 ft INCLUDING children.\n2. Spotter for every backing operation when school is within 500 ft of the site.\n3. Treat school dismissal windows like a hard work-stop window: no backing, no swinging, no lifting overhead between 2:45-3:30 PM local school day.\n4. If a parent approaches: stop, remove gloves, lower your voice, acknowledge the concern with their child's name if you heard it.\n5. Direct ALL questions to the foreman or PM. Operator does not negotiate.\n6. If a child crosses the barricade: STOP everything. Reset the barricade. File an incident — 'Public / Third Party · Public Interaction · Near-Miss'.",
    what_not_to_do:
      "Do not say 'this is safe, ma'am' — you cannot guarantee it. Say 'we follow the safety procedure and I'll get the supervisor over.'\nDo not back up without a spotter when school is in dismissal window.\nDo not laugh, joke, or take photos near a school zone — parents will assume the worst.\nDo not engage the parent's video. Acknowledge they're recording, stay calm, and route them to the supervisor.",
    supervisor_actions:
      "Pre-plan school dismissal windows on every project within 500 ft of a school. Coordinate with school resource officer ahead of mobilization. If a parent escalates, get there in person — phone is not enough when a child is involved. File a Public-Interaction incident every time, even verbal-only.",
    documentation:
      "Incident type 'Public / Third Party'.\nClassifications: Public Interaction + (Verbal Confrontation if applicable) + (Near-Miss if a child crossed the barricade).\nDescribe the dismissal window if relevant.\nNote which school by name.\nPhoto of barricade configuration BEFORE and AFTER the encounter.",
    corrective_actions:
      "Verify barricade gap is < 30 inches anywhere near a school.\nVerify spotter assigned for every backing op during dismissal window.\nNotify school resource officer of the incident within 24 hours.",
    read_aloud:
      "Kids are different. Adults stay outside the barricade. Kids don't. They run, they chase a ball, they don't see the excavator. If you are working near a school or a park: no backing without a spotter — none. Between two-forty-five and three-thirty, no swinging the bucket, no lifting overhead. If a parent walks up — even if they are angry — stop, take a breath, get the supervisor. Do not argue with a parent. You will not win that argument. The supervisor exists for this exact moment.",
    references_cited:
      "OSHA Construction Standards 1926 Subpart G (Signs and Barricades) · FDOT MOT manual school-zone provisions · MASCI Public-Interaction Policy",
    action_items:
      "School-zone dismissal window logged in JHA · Spotter assigned for backing ops · School resource officer contact on file",
  },

  {
    key: "verbal_threats_harassment",
    domain: "public_interaction",
    title: "Verbal Threats & Harassment",
    category: "Public Interaction & Conflict De-Escalation",
    severity: "serious_injury",
    incident_pattern:
      "A verbal threat looks like nothing — until it is the thing the deposition is built on. Real-life heavy-civil pattern: a member of the public yells from across the street 'I'll catch you in the parking lot.' Crew laughs it off. Three days later the same person is waiting at shift change in the same parking lot. The threat the crew didn't document is the threat the company cannot prove. The harassment pattern: same resident, every morning, at the foreman's window, for a week. By Thursday the foreman is short. By Friday the foreman snaps. By Saturday the foreman is on the front page of the local Facebook group. EVERY verbal threat or harassment incident is reported, even the ones that 'felt minor'. The minor ones are the ones that become the major ones.",
    hazards_reviewed:
      "Direct verbal threat · Implied verbal threat · Repeated harassment · Stalking-pattern behavior · Crew member retaliation · Reputational harm",
    warning_signs:
      "Same person, multiple days, same crew\n'Threat from across the street'\nNamed threat ('I'll catch YOU')\nReferences to weapons, vehicles, or 'after work'\nKnowing personal info (your truck, your home street, your wife)\nA crew member who has 'stopped saying anything about it'",
    what_to_do:
      "1. Document the FIRST one. Time, location, who said it, who heard it, exact words.\n2. Tell the supervisor BEFORE end of shift. Not next week.\n3. If the threat is specific (name, time, location, weapon) — call 911. Specific = credible.\n4. If the same person has done it twice — call 911. Pattern = stalker.\n5. Vary your post-shift route. Don't park in the same place two days in a row when you are the target.\n6. Travel in pairs leaving the site if a credible threat exists.",
    what_not_to_do:
      "Do not handle it 'as a crew.' This is what the company is for.\nDo not confront the aggressor 'after hours.' That is exactly what the threat wants.\nDo not minimize ('he was just running his mouth').\nDo not share personal info — never confirm your home street, your wife's name, your truck's plate.",
    supervisor_actions:
      "Open an incident the SAME day. Classification 'Public Interaction + Threat' minimum; add 'Harassment' if pattern. If credible, escalate to Operations Manager and Safety Manager that day. Coordinate with HR and Legal if the threat names a specific employee. Verify the targeted crew member's welfare check — do not assume they are 'fine'.",
    documentation:
      "Verbatim quote of the threat.\nWitness rows (with phone, email, employer) for every person who heard it.\nIf police involved: agency, officer, case number.\nSocial-media check: did the threat get repeated online? (Yes → flag media_filmed = true.)\nKeep the documentation even if no further action is taken — patterns are only visible in the documentation.",
    corrective_actions:
      "Targeted crew member's route to/from site varied for next 2 weeks.\nIf pattern of harassment: project barrier re-evaluation + sheriff coordination.\nWelfare check on the named employee within 24 hours.",
    read_aloud:
      "If someone yells a threat at you — even if you think it's nothing — tell me before you go home. Not tomorrow. Today. If they used your name, said where they'd find you, or talked about a weapon: that's not nothing. That is a 911 call. Do not handle it 'as a crew.' Do not go look for them. That is what the threat wants. We document EVERY single one because patterns are only visible when we count them.",
    references_cited:
      "OSHA Workplace Violence Prevention Guidance · MASCI Workplace Violence Policy · 18 U.S.C. § 875 (Interstate Threats) — applicable if threat is electronic · Florida § 836.10 Written Threats",
    action_items:
      "All verbal threats documented same day · Targeted crew member welfare-checked · Route variation in place if pattern",
  },

  {
    key: "physical_confrontations",
    domain: "public_interaction",
    title: "Physical Confrontations",
    category: "Public Interaction & Conflict De-Escalation",
    severity: "serious_injury",
    incident_pattern:
      "Pushing, shoving, an open hand to the chest, an attempted punch, an object thrown. Once contact is made, the situation has crossed the line where 'de-escalation' no longer applies. The pattern when it goes wrong: a crew member 'doesn't want to seem like a baby' and lets the shove go unreported. Two weeks later in an unrelated argument the same aggressor swings — and now the company has no record that there was a first incident. The other pattern: a crew member shoves back. Now both parties are charged with battery. The company's defense disappears. Rule: once they touch you, you stop, you retreat, you call 911. You do not push back. You do not chase. You do not 'set them straight.' Your job is to be the cleanest signal in the camera-phone video that hits the news cycle.",
    hazards_reviewed:
      "Open-hand shove · Thrown object · Closed-fist strike · Grabbed PPE / clothing · Vehicle used as weapon · Mutual combat charges · Retaliation injury · Reputational harm",
    warning_signs:
      "Crew member already inside arm's-reach of the aggressor · aggressor's body shifts (weight transferred forward, shoulders square) · aggressor pulls back like a wind-up · a thrown object that misses · a 'second person' joining the aggressor",
    what_to_do:
      "1. The MOMENT you are touched: stop. Hands visible. Step back, not forward.\n2. Call 911. Then call the supervisor.\n3. If others on the crew are within reach, get between THEM and the aggressor — defensive only, no offensive contact.\n4. If you are knocked down: stay down until aggressor disengages. Standing up too soon invites a second strike.\n5. Photograph the location, the barricade, your PPE, and any visible injury within 5 minutes. The body camera footage from the deputy will arrive later — your photos cover the gap.\n6. Seek medical evaluation even if you feel fine. Concussion symptoms can be delayed.",
    what_not_to_do:
      "Do not push back. Do not chase. Do not 'pull rank.'\nDo not say 'I'm gonna sue you' or any threat back — you become the aggressor in the video.\nDo not leave the scene before deputies arrive.\nDo not delete photos / videos / dashcam footage.\nDo not talk to the press, the aggressor's family, or post on social media about it.",
    supervisor_actions:
      "Same-day incident report — classifications: Public Interaction + Physical Contact + Physical Assault + (Workplace Violence if pattern). Call 911 if not already called. Call Operations Manager, Safety Manager, HR, Legal IMMEDIATELY. Direct welfare check on the struck employee — physical AND psychological. Coordinate with the deputy on the case number. Make sure the witness contact info is captured BEFORE the witnesses leave the site.",
    documentation:
      "Classifications: Physical Contact = TRUE; Physical Assault = TRUE.\nThreat description: verbatim quote if a threat preceded the contact.\nWitness rows with phone, email, employer — minimum 2 if available.\nPolice fields: agency, officer, badge, case number, report number.\nMedical fields: treatment_provided, medical_facility, sent_home.\nAttachments: police_report (when obtained), medical, witness_statement, photo, video.",
    corrective_actions:
      "Welfare check on struck employee within 24 hours (physical + mental health).\nProject barrier re-evaluation — was the barricade enough?\nPolice report obtained and attached to incident.\nLegal / insurance notified within 24 hours.\nReview by Executive within 72 hours.",
    read_aloud:
      "If someone touches you — pushes you, swings at you, throws something at you — STOP. Hands open. Step back, not forward. Do not push back. The second you push back, it stops being a video of THEM assaulting you and it becomes a video of TWO PEOPLE fighting. We lose the case. You lose the case. You stop. You retreat. You call 911. Then you call me. Then you take pictures of the spot, the barricade, your hands, your shirt. Even if you feel fine — you get checked out. Concussions show up an hour later.",
    references_cited:
      "OSHA 29 CFR 1904 (Recordkeeping) · MASCI Workplace Violence Policy · Florida § 784.03 Battery · Track 15.47 Workplace Violence Workflow",
    action_items:
      "Same-day incident filed · 911 called · Witness contact captured · Welfare check completed · Police case # logged",
  },

  {
    key: "recording_employees_social_media",
    domain: "public_interaction",
    title: "Recording Employees / Social Media Encounters",
    category: "Public Interaction & Conflict De-Escalation",
    severity: "moderate",
    incident_pattern:
      "Phones are out for everything now. A passerby films a crew taking a break, posts 'why are these guys sitting around when my taxes pay them.' By lunch the video has 40,000 views. By dinner the project manager is on the phone with the owner. The pattern when it goes wrong: a crew member sees the phone, says something sharp ('mind your business'), and now the same passerby has a video clip of a MASCI employee being rude. The clip is the only thing the public sees. Truth doesn't matter. Tone matters. Lesson: assume the phone is recording from the moment a stranger is within 30 feet, and behave the way you'd want your wife and your mom to see it on the local news.",
    hazards_reviewed:
      "Out-of-context video clip · Reputational harm · Crew retaliation captured on video · Doxxing of crew members · Owner / GC backlash · Project delays",
    warning_signs:
      "Phone held up at chest height (recording posture)\nPhone with the back camera facing the crew (filming, not just looking)\nA passerby narrating out loud ('Look at these guys…')\nA passerby driving by SLOWLY with phone visible\nA passerby asking your name, your boss's name, the project owner's name on camera",
    what_to_do:
      "1. Assume you are on camera the moment a stranger is within 30 ft. Act accordingly.\n2. If approached on camera: stay polite, stay short. 'Sir/Ma'am, the project manager can give you that information. Let me get them on the phone.'\n3. Do NOT respond to taunts. Walk to the barricade or to a crew vehicle.\n4. Note the time, the description, and tell the foreman.\n5. If you see your face or your truck plate posted publicly: tell the supervisor and then tell HR. Do NOT respond to the post yourself.",
    what_not_to_do:
      "Do not say 'turn that off' — Florida is a one-party-consent state, public spaces are filmable, you have no legal ground.\nDo not point at the camera.\nDo not give your last name, your home town, or your boss's name on camera.\nDo not post a counter-video.\nDo not comment on the original post.\nDo not let crew share the link in the crew group chat.",
    supervisor_actions:
      "If a viral clip appears: notify Project Manager, Operations Manager, and HR THAT DAY. Do not engage the post. Document the URL + screenshots before it gets deleted. Set the social_media_posted flag on any related incident. Reach out to Owner / GC ahead of them seeing it from a third party.",
    documentation:
      "Open an incident type 'Public / Third Party' even if no interaction occurred — viral exposure IS an incident.\nClassifications: Public Interaction + (Verbal Confrontation if relevant).\nMedia filmed = TRUE.\nSocial media posted = TRUE if a public post has surfaced.\nAttach: photo of the device if filmed openly, screenshot of the post (URL captured), any responses by the crew.",
    corrective_actions:
      "Project-specific crew briefing on 'assume the phone is on'.\nReview crew social-media policy compliance.\nIf doxxing has occurred: HR + Legal + IT (privacy) loop.",
    read_aloud:
      "When you're at work, assume the phone is on. Always. If somebody walks up with a camera — be polite. Be short. Say 'the project manager can answer that, let me get them on the phone.' Do not argue with the camera. Do not point at the camera. Do not say something you wouldn't want your kid to see. We are guests on this street. The way we act on camera is the way the public will remember MASCI.",
    references_cited:
      "Florida § 934 (Wiretapping — public spaces exempt) · MASCI Social Media Policy · MASCI Public-Interaction SOP",
    action_items:
      "Crew briefed on 'assume on-camera' · Foreman knows incident classification for social-media events · Social-media URL captured if viral",
  },

  {
    key: "media_public_questions",
    domain: "public_interaction",
    title: "Media & Public Questions",
    category: "Public Interaction & Conflict De-Escalation",
    severity: "moderate",
    incident_pattern:
      "A news van pulls up. A reporter steps out, mic in hand, crew with camera 10 ft behind. They walk toward the foreman with a friendly 'just a few questions about the project.' The foreman tries to be helpful, says something inaccurate about the schedule, the reporter rolls with it, and now the GC + Owner + DOT are on the phone with the PM by lunch. The pattern when it goes wrong is NOT being mean — it is being helpful. Crew members do not have the context to speak for the project. Media questions go to ONE PERSON: the designated project spokesperson (PM or Operations). Same for public questions about scope, schedule, cost, ownership, displacement, or noise variance. 'I don't have that information, the project manager can answer that, let me get you their card.' That's the line.",
    hazards_reviewed:
      "Misquoted by media · Inaccurate schedule / scope statement · Crew member becoming the public face of a controversy · Owner / GC trust damage · Project delays from political backlash",
    warning_signs:
      "Camera-and-mic walking up\nA car parked across the street with someone holding a notebook\n'Just a quick question'\nA question that starts with 'why is it taking so long'\nA question that mentions a councilperson or commissioner by name",
    what_to_do:
      "1. Polite, short. 'I appreciate you asking, but the project manager handles all media questions. Let me get their contact info.'\n2. Foreman keeps the PM business card in the cab.\n3. Do not say no comment — say 'the project manager handles those questions and can answer fully.'\n4. Notify PM that media was on-site within 5 minutes.\n5. Document: media outlet, reporter name, time, what they asked.",
    what_not_to_do:
      "Do not estimate the schedule.\nDo not estimate the cost.\nDo not say the name of the owner or the GC unless they're already public.\nDo not say 'the GC made us do this' or 'the DOT made us do this.'\nDo not say 'no comment' — sounds like you're hiding something.\nDo not let the camera film inside the work zone without PM approval.",
    supervisor_actions:
      "Foreman keeps a media contact protocol card in every cab — PM's phone first, Operations second. If media shows up unannounced, the PM is notified within 5 minutes. If a controversial story is brewing, the PM coordinates a unified response with Owner + GC before any crew engagement.",
    documentation:
      "Note the outlet, reporter, station/paper, time, location, and the questions asked.\nDoes not always require an incident — but if the encounter was contentious, file with classification 'Public Interaction'.\nIf the encounter was filmed: media filmed = TRUE.",
    corrective_actions:
      "PM contact card refreshed in every cab.\nIf same outlet returns multiple times: PM coordinates a single on-camera response with Owner approval.",
    read_aloud:
      "If a reporter walks up, smile, be polite, hand them the PM's card, and tell them 'the project manager handles those questions and can answer fully.' Do not estimate the schedule. Do not say the cost. Do not blame the GC or the DOT. Do not say 'no comment' — it sounds bad. The line is: 'the project manager handles that.' Then you call me.",
    references_cited:
      "MASCI Media Relations SOP · MASCI Public-Interaction Policy · Owner contract media clauses (project-specific)",
    action_items:
      "PM contact card in every cab · Foreman trained on 'one-line response' · Media encounter logged",
  },

  {
    key: "trespassing_into_work_zones",
    domain: "public_interaction",
    title: "Trespassing Into Work Zones",
    category: "Public Interaction & Conflict De-Escalation",
    severity: "serious_injury",
    incident_pattern:
      "Citizens cut through. They have done it every day for five years and we are now in the way. Pedestrians slip behind a barricade because the detour is 200 ft longer. Kids on bikes ride straight through. Dog walkers cross at the gap. Worst pattern: someone steps into a trench while the operator is swinging. The lesson on near-misses says one thing — every trespass is a potential strike. The other pattern: the trespasser is hostile. Refuses to leave. Pulls a phone out. The crew member who tries to physically remove them becomes the story. Rule: trespassers are escorted out verbally. If they refuse, you stop work, call the deputy, and document. You do not put hands on them.",
    hazards_reviewed:
      "Pedestrian struck by equipment · Pedestrian falls into excavation · Hostile trespasser · Crew-initiated contact (battery) · Reputational harm · Owner / city liability",
    warning_signs:
      "A worn dirt path through the barricade gap (people have been cutting through)\nA bike or dog walker who slows down approaching the barricade\nA cyclist with earbuds — they cannot hear backup alarms\nA person in headphones walking toward an active operation\nA person sitting on equipment / leaning on barricades",
    what_to_do:
      "1. STOP the active operation if a person is inside the work zone. Hand signal. Verbal call. Horn.\n2. Walk toward them with hands visible. 'Sir/Ma'am — there's an active dig here, I need you to step back to the sidewalk for your safety.'\n3. If they comply: thank them, escort them to the barricade, reset the barricade behind them.\n4. If they refuse: stop work. Call 911 non-emergency. Document with photo.\n5. If they show hostility or pull a phone: same answer — stop work, call deputy, document.\n6. NEVER put hands on a trespasser. Never. Even a guiding hand on the shoulder is battery.",
    what_not_to_do:
      "Do not chase. Do not corner.\nDo not place hands on the trespasser, even to 'guide' them.\nDo not yell — voice up = trespass escalates.\nDo not assume they understand English. Use hand signals + slow speech.\nDo not let them sit on equipment 'for a minute' — once they're hurt, it's our liability.",
    supervisor_actions:
      "Pre-shift verify barricade integrity — any gap < 30 inches → recommit. If the same address / corner shows a worn path through: redesign the barricade. If the trespass was hostile or repeated, file an incident with classification 'Public Interaction + Trespass' (informal classification). Coordinate with the City / Sheriff / DOT for any required signage upgrades.",
    documentation:
      "Open incident type 'Public / Third Party' for any hostile or repeat trespass.\nClassifications: Public Interaction + (Trespass via free-text).\nIf the trespasser was struck or injured: severity escalates immediately — type becomes 'Injury / Illness' co-classified as 'Public Interaction'.\nPhotos of the barricade BEFORE and AFTER the encounter.\nWitness rows for every crew member who saw it.",
    corrective_actions:
      "Barricade re-design within 24 hours if path-of-desire confirmed.\nAdditional MOT signage requested through PM.\nIf trespass is at a school, school resource officer notified.",
    read_aloud:
      "If somebody is inside the barricade — STOP. Hand signal, horn, whatever it takes. Walk toward them with your hands visible. Tell them 'there's an active dig here, please step back to the sidewalk for your safety.' If they listen — thank them and reset the barricade behind them. If they don't listen — STOP work, call 911 non-emergency, take a picture. You do not put hands on anyone. Ever. Even guiding them by the elbow is battery. We don't win that fight.",
    references_cited:
      "OSHA 29 CFR 1926 Subpart G (Barricades and Signs) · Florida § 810.09 Trespass on Property Other Than Structure · MASCI Public-Interaction SOP",
    action_items:
      "Pre-shift barricade integrity check · Path-of-desire identified and mitigated · No-touch rule reinforced",
  },

  {
    key: "drone_overhead_survey_ops",
    domain: "public_interaction",
    title: "Drone & Overhead Survey Operations",
    category: "Public Interaction & Conflict De-Escalation",
    severity: "moderate",
    incident_pattern:
      "Drones are now part of survey, progress documentation, owner-facing dashboards. The crew gets used to overhead activity. The public does not. A drone over a residential neighborhood at 8 AM generates a Nextdoor post by 8:15 alleging surveillance. By noon there's a phone call to the city. By the next morning the same neighbor is at the foreman with 'why are you spying on me.' The other pattern is the actual safety one: a drone flown by a hobbyist crosses our work zone. Excavator boom and rotor blades in the same airspace = lost drone in the bucket or a panicked operator. Rule: every overhead op is announced, posted, and crew-briefed; every public question gets the PM-spokesperson treatment.",
    hazards_reviewed:
      "Public-privacy concern · Drone collision with equipment · FAA noncompliance · Crew distraction · Reputational harm",
    warning_signs:
      "A neighbor outside watching the drone\nA hobbyist drone visible in the air during our op\nA neighbor approaching with phone and a 'why are you flying over my pool' question\nA city official on-site asking for the FAA Part 107 paperwork\nA crew member looking up instead of at the trench while equipment is moving",
    what_to_do:
      "1. Post drone operations 24 hours ahead on the project signage AND on the project's public schedule.\n2. Pilot in Command (PiC) on-site with Part 107 paperwork in hand.\n3. Pre-flight crew briefing — equipment shuts down for the survey pass.\n4. If a public question comes during flight: pilot maintains line-of-sight; foreman handles the question with the PM-spokesperson line.\n5. If a hobbyist drone enters our airspace: pilot lands ours immediately. Foreman notes the time and direction the hobbyist drone came from.",
    what_not_to_do:
      "Do not fly without a Part 107 PiC.\nDo not fly without crew briefing.\nDo not fly over an active excavation with people in the trench.\nDo not engage with the privacy question on camera — route to PM.\nDo not 'reposition' the drone closer to a neighbor's property to get a better shot.",
    supervisor_actions:
      "Verify Part 107 paperwork before every flight. Coordinate with city / FAA if airspace authorization is required. Brief the crew before every flight. Post the schedule. If a privacy complaint is raised: PM responds in writing with the project's reason for the survey and confirmation that residential property is not the survey target.",
    documentation:
      "Flight log: pilot, time, duration, purpose, paperwork ref.\nPublic interaction during flight: incident type 'Public / Third Party' if the encounter was contentious; classification 'Public Interaction'.\nIf hobbyist drone entered our airspace: file incident type 'Public / Third Party' + 'Near-Miss' + describe trajectory.",
    corrective_actions:
      "Drone operations posted on public-facing project schedule.\nPart 107 paperwork on-site every flight.\nIf hobbyist drone entered airspace: FAA notification + PM notifies Owner.",
    read_aloud:
      "When the survey drone is up, two things matter. ONE — we are not flying over the trench while people are in it. Equipment stops, crew is briefed, then we fly. TWO — if a neighbor walks up asking why we're flying over their pool, we are polite and short. 'The project manager handles those questions, let me get their card.' Do not get into 'I'm not spying on you' on camera. You will lose. The PM handles privacy questions. We just fly safe.",
    references_cited:
      "14 CFR Part 107 (Small Unmanned Aircraft Systems) · FAA LAANC airspace authorization · MASCI Drone Operations SOP · MASCI Public-Interaction Policy",
    action_items:
      "Part 107 paperwork on-site · Flight schedule posted · Crew briefed pre-flight · Privacy questions routed to PM",
  },
];
