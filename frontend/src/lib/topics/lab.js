// iter302 · Dedicated `lab` domain for asphalt-lab safety topics.
// Domain: lab · 4 topics (initial bounded set per operator-approved audit iter301)
// Voice benchmark: lab_nuclear_gauge_handling (operator-approved tone gate).
// All 4 topics maintain custody-first / chemistry-first operational realism,
// NOT radiation/OSHA panic. Bilingual mirror lives in `./lab.es.js`.

export const TOPICS_LAB = [
  {
    key: "lab_nuclear_gauge_handling",
    domain: "lab",
    title: "Nuclear Density Gauge — Custody, Transport, and Response",
    severity: "fatal_risk",
    category: "Hazard-Specific",
    role_context: ["lab_tech", "inspector", "lead", "driver"],
    incident_pattern:
      "Nuclear gauge incidents at the field/lab level rarely involve radiation harm to a worker — they involve a lost gauge, a stolen gauge, or a damaged gauge that suddenly becomes a federal incident. The pattern repeats every year. A tech finishes a paving density test late in the day, secures the gauge in the open truck bed instead of inside the cab, runs into the gas station, comes back to find the truck broken into. Or the tech sets the gauge down on the shoulder during a quick string-line check, and a truck rolls over it. Or the gauge sits in a parked vehicle overnight in an unsecured yard and gets pried out by morning. None of these scenarios cause direct injury — but every one of them triggers an NRC report, a multi-day shutdown of testing operations, and a fine that runs into the tens of thousands. The technician who lost the gauge usually didn't fail at safety. They failed at custody. In nuclear gauge work, custody IS the safety.",
    hazards_reviewed:
      "Theft from unattended vehicle · Damage from vehicle strike during roadway testing · Source rod damage from drop or pinch · Unauthorized use by non-licensed personnel · Loss in transit (improperly secured case) · Public/civilian contact with abandoned gauge · NRC reportable incident from any of the above · Personal radiation exposure from prolonged improper handling",
    discussion_notes:
      "• Custody, not radiation, is the day-to-day risk. The gauge never leaves your line of sight outside its storage cabinet.\n• Transport: gauge in the locked case, case secured inside the cab. Never the open bed, never the toolbox.\n• Storage: end-of-day return to the licensed location. No overnight in vehicles, in unsecured offices, or 'I'll bring it back tomorrow.'\n• Authorized users only. If you're not on the NRC license, you don't touch the gauge — not even bench-to-truck.\n• On the roadway: gauge at the technician's feet or in the case beside them. Never on the pavement behind you. Never in the wheel path.\n• If a gauge is struck, dropped, or damaged — stop. Step back six feet. Call the RSO. Do not pick it up to assess.\n• If a gauge is lost or stolen: notify the RSO within the hour. The 24-hour NRC clock starts at discovery, not at end-of-shift.\n• Public interaction: 'This is a regulated instrument, please give us six feet.' Calm voice. Curiosity does not become contact.\n• Site awareness: trucks, rollers, and screed crews move constantly. The gauge stays at the tech's feet — not where a roller will crush it.\n• PPE: standard high-vis + steel-toe. No extra PPE on the gauge in normal operation. Radiation badges, if RSO-issued, are worn every use.",
    references_cited:
      "10 CFR 30 · 10 CFR 71 · NRC Materials License · State Radiation Control Program · ANSI N43.3 · Company RSO SOP",
    action_items:
      "Custody line-of-sight reinforced · Transport security verified (case locked, inside cab) · Authorized-user list reviewed · Lost/stolen/damaged escalation path identified by name · RSO contact verified for current shift · Radiation badge presence confirmed",
  },
  {
    key: "lab_oven_burns_chemistry",
    domain: "lab",
    title: "Lab Ovens, Hot Pans, and Bitumen-Extraction Chemistry",
    severity: "fatal_risk",
    category: "Hazard-Specific",
    role_context: ["lab_tech", "lead"],
    incident_pattern:
      "The serious lab-oven incident is rarely the burn. The burn is real — a 325°F pan grabbed without gauntlets puts a tech in urgent care for the rest of the shift — but the incident that kills is the chemistry one. A bitumen-extraction job uses a flammable solvent (toluene, hexane, or one of the perc/N-propyl-bromide replacements). The tech opens the oven to swap a sample, leaves the solvent rag on the bench, the vapor migrates toward the oven's heated mass, and a hot plate or stir-bar electrical arc finds the cloud. Flash fire. The lab is a closed space. The exit is one door. Most of these incidents trace back to two compressions: solvent reuse to save cost (vapor concentration climbs) and 'I'll just do this one quick' fume hood discipline. The oven didn't do it. The vapor did. The oven was just the ignition source waiting.",
    hazards_reviewed:
      "Contact burns from oven, pan, or sample tongs · Flash fire from solvent vapor + ignition source · Solvent-vapor inhalation in a closed lab · Hot-surface ignition of nearby flammables · Eye burns from solvent splash during hot extraction · Slip on solvent or asphalt residue near oven · Pressure release from sealed sample heated past expansion · Inadequate egress in a small lab during fire",
    discussion_notes:
      "• Gauntlets — wrist-length leather or aramid — for any oven pan above 200°F. Cotton work gloves are not gloves at 325°F.\n• Two-hand carry on any pan above 250°F. One hand carries are how techs drop hot pans on their own feet.\n• Solvent rags go into the covered metal can. Not the bench. Not the trash. Not 'just for a minute.'\n• Fume hood sash at the marked operating height. If the airflow indicator is yellow or red, you do not run hot extraction in that hood.\n• Solvent reuse is fine for cost. Solvent reuse without checking the can fill level is how vapor concentration climbs above LEL.\n• When the oven opens, the bench solvent goes away. Either capped, or in the hood, or back in the cabinet. Open oven + open solvent + same bench = wait.\n• Sealed samples never go in the oven. Pressure release from a capped tin at 325°F has put glass through a lab tech's forearm.\n• Egress: know the exit before you light off. Lab fires double in size every 30 seconds. You don't problem-solve toward the door.\n• If a small fire starts in the hood: close the sash, kill the gas, hit the suppression. Do not reach in to grab the sample.\n• If the room flashes: leave. The sample is replaceable. The lab is replaceable. You are not.",
    references_cited:
      "OSHA 1910.1450 (Lab Standard) · NFPA 45 (Lab Fire Protection) · ASTM D2172 (Bitumen Extraction) · AASHTO T 164 · Company Lab SOP",
    action_items:
      "Gauntlet condition checked · Solvent-can fill level verified · Fume hood sash + airflow indicator confirmed · Egress path clear and known · Suppression system location identified · Sealed-sample policy reaffirmed",
  },
  {
    key: "lab_core_drilling_silica",
    domain: "lab",
    title: "Pavement Core Drilling — Silica, Saw Kickback, and Wet-Cut Discipline",
    severity: "serious_injury",
    category: "Hazard-Specific",
    role_context: ["lab_tech", "inspector"],
    incident_pattern:
      "Pavement coring at the lab bench looks routine until something binds. The diamond bit hits a hard aggregate fragment, the core locks in the barrel, and the saw torque transfers to the technician's wrists. The injury is almost always a forearm laceration, a wrist sprain, or — when the tech tried to free a bound bit with the saw still spinning — a torn tendon. Underneath that mechanical risk runs the silent one: respirable crystalline silica. Wet-cut is required for a reason, but the reason is invisible. The water suppresses dust at the cutting interface; the slurry then dries on the bench, on the floor, on the tech's clothes, and on the racks where cores live overnight. The next morning that dried slurry kicks up as airborne dust. Five years of that on a daily lab cycle is the difference between a healthy retirement and silicosis at fifty-eight.",
    hazards_reviewed:
      "Forearm/wrist laceration from kickback during bind · Tendon strain from torque transfer on a stuck bit · Respirable crystalline silica from dry-cut OR dried-slurry resuspension · Eye injury from slurry splash · Electrical shock from wet saw without GFCI · Slip on wet bench or floor · Hand injury from sample handling without gloves",
    discussion_notes:
      "• Wet-cut is not optional. The water line stays on while the saw is on. No dry shortcuts to 'just finish this last core.'\n• If the bit binds, you do not pry it free with the saw spinning. Release the trigger. Wait for full stop. Then assess.\n• Two hands on the saw — the front handle plus the rear grip. One-hand cuts are how the wrist gets twisted on a bind.\n• Splash goggles for the technician. Standard safety glasses are not splash-rated against slurry.\n• GFCI on every wet-saw outlet. If the GFCI trips, you do not bypass it. You find out why.\n• Slurry cleanup is part of the cut, not a separate task. Wet sponge, then dispose per spill plan. Do not let it dry on the bench.\n• Cores out of the saw go on a rack with a drip tray. Not on the bench. Not on the floor. Drying slurry is dust on Day Two.\n• Floors swept wet, not dry. A broom on dry slurry is the worst possible silica delivery method.\n• PPE at minimum: splash goggles, nitrile or chemical-resistant gloves, apron. Coring without an apron leaves silica slurry on clothes that the tech takes home.\n• N95 or better in the lab if dried slurry is visible. If you can see the dust, the dust is already past the threshold.",
    references_cited:
      "OSHA 1926.1153 (Respirable Crystalline Silica) · ASTM D5361 (Sampling Asphalt Pavements) · NIOSH Hierarchy of Controls · Company Lab SOP",
    action_items:
      "Wet-cut water line verified · GFCI tested on saw outlet · Splash goggles and gloves issued · Slurry cleanup protocol reviewed · Core rack with drip tray in use · Floor wet-sweep schedule confirmed",
  },
  {
    key: "lab_solvent_handling_ppe",
    domain: "lab",
    title: "Lab Solvents — Selection, PPE, and Rag Disposal Realities",
    severity: "serious_injury",
    category: "Hazard-Specific",
    role_context: ["lab_tech", "lead"],
    incident_pattern:
      "Lab solvent injuries don't usually happen in big dramatic events. They happen one shift at a time. A tech reuses extraction solvent across multiple samples to save cost. The fume hood was 'mostly closed.' Latex gloves were used because that's what the supply closet had. Solvent-soaked rags went into the regular trash because the metal can was full. None of those decisions caused an injury that day. Five years later, the tech has chronic dermatitis on the forearms, a tremor that may or may not be reproductive-toxin exposure from the perc replacement, and a near-fire incident from a self-heating rag pile that smoldered in a covered plastic tote overnight. The solvent doesn't have to be the one OSHA wrote the SDS about. The lab-side reality is that the modern solvent inventory — N-propyl bromide, perchloroethylene, toluene, hexane, mineral spirits, dichloromethane — is a chronic-exposure problem managed by daily PPE and hood discipline, not by acute-incident response.",
    hazards_reviewed:
      "Chronic skin contact from glove permeation (latex fails almost all asphalt solvents) · Inhalation exposure from inadequate fume hood discipline · Reproductive and neurological toxicity from perc/NPB replacements · Eye contact splash without splash-rated PPE · Self-heating rag-pile fire from incorrect disposal · Solvent ignition from open container near oven or hot plate · Cross-contamination from solvent reuse without monitoring",
    discussion_notes:
      "• Glove material matters. Latex is permeable to almost every asphalt-extraction solvent within minutes. Nitrile, neoprene, or chemical-rated only.\n• Glove inspection before each task. A pinhole is a 100% breach for organic solvents.\n• Fume hood sash at the marked operating height — usually 18 inches. Higher sash = lost capture velocity.\n• Verify hood airflow daily. The indicator is yellow or red? You do not run solvent work in that hood until Facilities clears it.\n• Splash goggles, not safety glasses, when pouring or transferring. Glasses lose to a sideways splash.\n• Apron for any extraction or pour. Solvent on lab coats migrates to street clothes when the tech leaves.\n• Solvent reuse is legitimate, but log the use-count and the visual color. A solvent past its useful life smells different and looks different. Trust both.\n• Soaked rags go into the covered metal can. Not plastic. Not the trash. Empty the can to the waste cabinet before it fills past two-thirds.\n• At end of shift: empty the rag can. A full can left overnight is the most common self-heating fire in asphalt labs.\n• If you feel lightheaded, get out. Lightheadedness is the first sign — and the only sign — for several common solvents. You do not 'push through it.'",
    references_cited:
      "OSHA 1910.1450 (Lab Standard) · OSHA 1910.1000 (PELs) · NFPA 45 · NIOSH Pocket Guide · EPA TSCA (perc / N-propyl bromide restrictions) · Company SDS Library",
    action_items:
      "Glove material confirmed appropriate for solvents in use · Hood sash + airflow verified · Splash goggles + apron issued · Rag can emptied end-of-shift · Solvent reuse log present · Lightheadedness response reviewed",
  },
];
