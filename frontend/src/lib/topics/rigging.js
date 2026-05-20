// Domain: rigging · iter261 Phase H Batch 3 · 2 uplifted

export const TOPICS_RIGGING = [
  {
    key: "cranes_hoisting",
    domain: "rigging",
    title: "Crane Lift Operations",
    category: "Tool / Equipment Specific",
    severity: "fatal_risk",
    incident_pattern:
      "Crane fatalities cluster around four predictable patterns. One — boom contacts overhead primary, operator survives in cab (Faraday), ground crew touching the crane gets killed by transfer. Two — load drops because the rigging was wrong: sling overloaded for the hitch angle, shackle pin backed out, choker slipped. Workers under the load are killed instantly. Three — crane tips because outriggers were on dirt instead of cribbing, or the lift radius exceeded the load chart, or the operator extended the boom past the engineered limit to make a 'short reach.' Whole crane goes over. Four — two-blocking, where the hook block hits the boom tip and either snaps the load line or rips the boom apart. The fix is the lift plan, treated as a contract: weight verified, radius verified, ground bearing engineered, outriggers fully cribbed, qualified signal person, and nobody under the load. Ever.",
    hazards_reviewed:
      "Crane tipping · Struck-by suspended load · Crushed by load · Two-blocking · Overhead line contact · Failure of rigging · Uncertified operator / signal person",
    discussion_notes:
      "• Operator AND signal person certified.\n• Pre-lift plan: load weight, radius, rigging, ground bearing, swing path.\n• Outriggers fully extended on cribbing; ground bearing capacity confirmed.\n• Maintain power-line clearance (Table A-encroachment).\n• Tag lines control load rotation; no workers under suspended load.\n• Anti-two-block device functional; LMI calibrated.\n• Wind speed monitored — stop at mfr / engineer threshold.",
    references_cited: "OSHA 1926 Subpart CC · ASME B30 · OSHA 1926.1408",
    action_items:
      "Lift plan signed · Operator/signal certified · Cribbing in place · Tag lines staged · Wind monitor",
  },
  {
    key: "rigging_load_securement",
    domain: "rigging",
    title: "Rigging & Load Securement",
    category: "Tool / Equipment Specific",
    severity: "fatal_risk",
    incident_pattern:
      "Rigging-failure fatalities have a depressing repetition: someone used a sling that was clearly damaged because 'it'll work for one more lift,' or the rigger derated wrong for the hitch angle and the sling broke at 60% of nominal capacity. A 2-ton load dropping 6 feet on a worker is unsurvivable. Pattern two — shackles side-loaded during a basket hitch, screw pin backs out under vibration, load releases. Pattern three — chains and binders on a flatbed not torqued enough; load shifts in transit, takes out a worker on the next bend. The fix is mechanical and boring: inspect every sling, shackle, hook before EACH lift; remove damaged gear from service immediately; never side-load a shackle; match capacity to hitch type AND angle. Workers never under a suspended load — tag lines do the steering from outside the kill zone.",
    hazards_reviewed:
      "Sling failure · Load shift in transit · Improper hitch / connection · Damaged rigging · Pinch points · Falling material from incorrect chock or strap",
    discussion_notes:
      "• Inspect every sling, shackle, hook before use; remove damaged items from service.\n• Match sling capacity to load — derate for hitch type and angle.\n• Shackles screw-pin or bolt-type for overhead lifts; never side-loaded.\n• Working load limit (WLL) tags legible; tagged-out gear quarantined.\n• Workers never under suspended load; tag lines for control.\n• Truck loads: chocks, straps to FMCSA cargo securement standard.",
    references_cited: "OSHA 1926.251 · ASME B30.9 (Slings) · FMCSA 49 CFR 393",
    action_items:
      "Rigging inspected · Sling capacities verified · Tag lines staged · Cargo securement reviewed",
  },
];
