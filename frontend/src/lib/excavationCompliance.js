// Phase 10C · Field-First Rearchitecture
//
// Pure function. Reads the in-progress excavation form state and returns a
// live operational summary the foreman can read at a glance:
//
//   • overall status (Ready / Needs Review / Action Required)
//   • plain-English explanations for every triggered requirement
//   • smart suggestions (protective system, access count, etc.)
//   • derived booleans (depth_ge_4ft, depth_ge_5ft) so the form doesn't
//     need to ask the foreman to do arithmetic OSHA already knows.
//
// "The platform thinks first, asks second."
//
// Returned shape:
//   {
//     status: "Ready" | "Needs Review" | "Action Required",
//     statusReason: "…",                       // one-line summary
//     requirements: [                           // contextual cards
//       { id, severity, title, why, action }   // each renders as a chip
//     ],
//     suggestion: { protective_system, soil, … },
//     derived: { depth_ge_4ft, depth_ge_5ft, ... },
//     visibleSections: Set<string>             // controls progressive disclosure
//   }

const PROTECTIVE_SUGGESTIONS = {
  // Soil → depth → suggestion (matches OSHA 1926 Subpart P Appendix B/C)
  "Type A":      { lt5: "Not Required", "5to10": "Sloping (3/4H:1V) or Trench Box", gt10: "Trench Box or engineered shoring" },
  "Type B":      { lt5: "Not Required", "5to10": "Sloping (1H:1V) or Trench Box",   gt10: "Trench Box or engineered shoring" },
  "Type C":      { lt5: "Not Required", "5to10": "Sloping (1.5H:1V) or Trench Box / Shoring", gt10: "Trench Box or engineered shoring" },
  "Stable Rock": { lt5: "Not Required", "5to10": "Not Required (rock)",             gt10: "Engineer review required" },
};

function suggestProtective(soil, depthFt) {
  if (!soil || soil === "Unknown / Needs Review") {
    return "Needs Safety Review (soil not classified)";
  }
  const table = PROTECTIVE_SUGGESTIONS[soil];
  if (!table) return "Needs Safety Review";
  if (depthFt < 5) return table.lt5;
  if (depthFt <= 10) return table["5to10"];
  return table.gt10;
}

function ladderCount(lengthFt) {
  // OSHA: ladder/ramp/stair within 25 ft of lateral travel for any crew
  // member. For a 50 ft trench you need at least 2 access points.
  if (!lengthFt || lengthFt <= 0) return 1;
  return Math.max(1, Math.ceil(lengthFt / 50));
}

export function computeExcavationCompliance(f) {
  const depthFt = Number(f.depth_ft) || 0;
  const lengthFt = Number(f.length_ft) || 0;
  const isGe4 = depthFt >= 4;
  const isGe5 = depthFt >= 5;
  const soil = f.soil_classification || "Unknown / Needs Review";
  const ps = f.protective_system || "";
  const work = f.work_type || "";

  // Derived flags — the form doesn't ask the foreman to mark these any more.
  const derived = {
    depth_ge_4ft: isGe4,
    depth_ge_5ft: isGe5,
  };

  // Suggested protective system
  const suggestedPs = suggestProtective(soil, depthFt);

  // Build the requirement list — each item is rendered as a chip the
  // foreman can read at a glance. Severity drives color.
  const requirements = [];
  const add = (id, severity, title, why, action) =>
    requirements.push({ id, severity, title, why, action });

  if (depthFt > 0) {
    if (isGe5) {
      add("depth_5", "info",
        `Trench is ${depthFt} ft deep`,
        "OSHA requires a competent person, an inspection before crew entry, AND a protective system (sloping, shoring, shielding, or benching).",
        "Confirm protective system + competent person below.");
    } else if (isGe4) {
      add("depth_4", "info",
        `Trench is ${depthFt} ft deep`,
        "OSHA requires safe access/egress within 25 ft of any worker.",
        "Confirm access/egress is installed below.");
    }
  }

  // Soil
  if (soil === "Unknown / Needs Review") {
    add("soil_unknown", "warn", "Soil not classified yet",
      "The protective system depends on soil type. A competent person must classify it before entry.",
      "Pick a soil type or leave 'Unknown / Needs Review' so Safety follows up.");
  } else if (soil === "Type C" && isGe5) {
    add("soil_c_deep", "warn", "Type C soil at 5 ft+",
      "Type C soil is the loosest. OSHA requires steeper sloping (1.5H:1V) or shielding.",
      `Suggested system: ${suggestedPs}.`);
  }

  // Protective system vs depth
  if (isGe5) {
    if (ps === "Not Required" || ps === "Needs Safety Review" || ps === "") {
      add("ps_missing", "danger", "Protective system needed",
        `At ${depthFt} ft deep in ${soil} soil, OSHA requires a protective system.`,
        `Suggested: ${suggestedPs}.`);
    } else if (ps === "Sloping" && soil === "Type C" && depthFt > 6) {
      add("ps_sloping_typec", "warn", "Sloping in deep Type C",
        "Sloping in Type C soil deeper than 6 ft requires extreme angles or a trench box.",
        "Confirm 1.5H:1V slope OR switch to Trench Box.");
    }
  }

  // Access / Egress (auto-required at 4 ft+)
  if (isGe4) {
    const n = ladderCount(lengthFt);
    add("access_required", "info",
      `Ladder access required — ${n} ladder${n !== 1 ? "s" : ""}`,
      `A ${lengthFt || "?"} ft trench at ${depthFt} ft deep needs ${n} ladder/ramp/stair so no worker is more than 25 ft from one.`,
      "Confirm access/egress installed.");
    if (f.access_egress_installed === false) {
      add("access_missing", "danger", "Access/egress not installed",
        "OSHA forbids crew entry at 4 ft+ without compliant access/egress.",
        "Install ladder(s) before crew descends.");
    }
  }

  // Utility locate — only relevant for digging that exposes utilities
  const isUtility = /Utility|Sanitary|Storm|Water Main|Electrical|Drainage/.test(work);
  if (isUtility && f.locate_status !== "Complete" && f.locate_status !== "Not Required") {
    add("locate_pending", "danger", "Utility locate not complete",
      `${work || "Utility work"} requires a valid locate ticket before exposing utilities.`,
      "Call 811. Wait for clearance. Then resume.");
  }

  // Water
  if (f.water_present === true && !f.dewatering_active) {
    add("water", "warn", "Water present — no active dewatering",
      "Standing water reduces soil cohesion fast. Re-evaluate as Type C until dewatered.",
      "Start dewatering or stop work and call Safety.");
  }

  // Atmosphere
  if (f.hazardous_atmosphere_concern === true && !f.atmospheric_testing_completed) {
    add("atmos", "danger", "Atmospheric testing not completed",
      "Sewer / fuel / landfill / confined spaces can hide methane, H2S, CO, or O2 deficiency.",
      "Test with a 4-gas monitor before crew descent.");
  }

  // Reinspection
  if (f.reinspection_required === true && !f.reinspection_completed) {
    add("reinspect", "danger", "Reinspection still needed",
      "A condition changed (rain / soil / utility strike). OSHA requires a fresh competent-person inspection.",
      "Have the competent person re-inspect before crew re-entry.");
  }
  if (f.rain_event_observed === true && !f.reinspection_completed) {
    add("rain", "danger", "Rain event — reinspection required",
      "Rain re-classifies soil cohesion. The competent person must re-inspect.",
      "Complete reinspection before resuming work.");
  }

  // Competent person at 5 ft+
  if (isGe5 && !(f.competent_person_name || f.competent_person_id)) {
    add("cp", "danger", "Competent person not designated",
      "Every trench 5 ft+ needs a designated competent person on-site, trained and authorized.",
      "Pick a competent person from the roster.");
  }

  // Spoils setback
  if (f.spoils_2ft_from_edge === false) {
    add("spoils", "danger", "Spoils too close to the edge",
      "Soil within 2 ft of the edge adds load that can collapse the wall.",
      "Move spoils back at least 2 ft.");
  }

  // Trench box selected but no asset linked
  const assets = f.assigned_asset_ids || [];
  if ((ps === "Trench Box / Shielding" || ps === "Combination") && assets.length === 0) {
    add("tb_no_asset", "warn", "Trench Box selected — no asset linked",
      "Link the specific TB-XX asset(s) so its tabulated data and inspection status are on the record.",
      "Pick the Trench Box(es) in Section 6.");
  }

  // Road plates
  const roadPlates = f.road_plate_ids || [];
  if (work === "Roadway Excavation" && roadPlates.length === 0 && f.road_plates_used !== false) {
    add("rp", "warn", "Road plates — confirm registry IDs",
      "Roadway excavation usually means plates over open trench at end of day.",
      "Pick the RP-XXX assets in Section 6b, OR mark 'Road Plates Used? = No'.");
  }

  // Overall status
  const hasDanger = requirements.some((r) => r.severity === "danger");
  const hasWarn = requirements.some((r) => r.severity === "warn");
  let status = "Ready";
  let statusReason = "Every OSHA requirement so far is satisfied — submit when you're done.";
  if (hasDanger) {
    status = "Action Required";
    statusReason = "One or more OSHA-required items need attention before the crew enters.";
  } else if (hasWarn) {
    status = "Needs Review";
    statusReason = "Workable — Safety will follow up on the highlighted items.";
  }

  // Progressive disclosure — only show sections that apply.
  // (Sections always visible: 1 Job, 1b Personnel, 2 Dimensions, 3 Work Type,
  // 4 Soil, 5 Protective, 6 Assets, 9 Spoils, 12 Competent Person, 14 Notes.)
  const visibleSections = new Set([
    "1", "1b", "2", "3", "4", "5", "6", "9", "12", "13", "14",
  ]);
  if (isGe4) visibleSections.add("7");
  if (isUtility || f.utility_locate_required === true) visibleSections.add("8");
  if (work === "Roadway Excavation" || f.road_plates_used === true) visibleSections.add("6b");
  if (f.water_present === true || f.seepage_present === true) visibleSections.add("10");
  if (f.hazardous_atmosphere_concern === true || /Sanitary|Storm|Sewer|Confined/.test(work)) {
    visibleSections.add("11");
  }

  return {
    status,
    statusReason,
    requirements,
    suggestedPs,
    derived,
    visibleSections,
    counts: {
      danger: requirements.filter((r) => r.severity === "danger").length,
      warn: requirements.filter((r) => r.severity === "warn").length,
      info: requirements.filter((r) => r.severity === "info").length,
    },
  };
}
