// Phase 10C · Pure compliance engine — quick smoke test via node REPL.
// Run with: node /app/frontend/src/lib/excavationCompliance.test.mjs
import { computeExcavationCompliance } from "./excavationCompliance.js";

function assert(cond, label) {
  if (!cond) {
    console.error("FAIL:", label);
    process.exit(1);
  } else {
    console.log("ok:", label);
  }
}

// 1. Empty / new form — visible sections are minimal
let r = computeExcavationCompliance({});
assert(r.status === "Ready" || r.status === "Needs Review", "empty status is non-blocking");
assert(!r.visibleSections.has("7"), "Section 7 hidden when no depth");
assert(!r.visibleSections.has("10"), "Section 10 hidden when no water");

// 2. Shallow trench — still no access section
r = computeExcavationCompliance({ depth_ft: 3, soil_classification: "Type B", protective_system: "Sloping" });
assert(!r.visibleSections.has("7"), "Section 7 hidden at 3 ft");
assert(r.status === "Ready", "3 ft Type B sloping = Ready");

// 3. 4 ft trench — access required
r = computeExcavationCompliance({ depth_ft: 4, soil_classification: "Type B", protective_system: "Sloping" });
assert(r.visibleSections.has("7"), "Section 7 visible at 4 ft");
assert(r.derived.depth_ge_4ft === true, "depth_ge_4ft auto-derived true");
assert(r.derived.depth_ge_5ft === false, "depth_ge_5ft auto-derived false");

// 4. 6 ft + Type C with no protective + no CP → Action Required
r = computeExcavationCompliance({ depth_ft: 6, soil_classification: "Type C", protective_system: "Not Required" });
assert(r.status === "Action Required", "6 ft Type C no PS → Action Required");
const codes = r.requirements.map((x) => x.id);
assert(codes.includes("ps_missing"), "ps_missing fires");
assert(codes.includes("cp"), "competent person required");

// 5. Suggested protective for Type C at 6 ft includes shoring/shielding
r = computeExcavationCompliance({ depth_ft: 6, soil_classification: "Type C" });
assert(/Shoring|Trench Box|Sloping/.test(r.suggestedPs), "Type C 6 ft suggestion includes valid system: " + r.suggestedPs);

// 6. Utility work pending locate → danger
r = computeExcavationCompliance({ work_type: "Utility Work", locate_status: "Pending" });
assert(r.requirements.some((x) => x.id === "locate_pending"), "locate_pending requirement fires");
assert(r.visibleSections.has("8"), "Section 8 visible for utility work");

// 7. Rain event → reinspection requirement
r = computeExcavationCompliance({ rain_event_observed: true });
assert(r.requirements.some((x) => x.id === "rain"), "rain reinspection requirement");

// 8. Roadway → Section 6b visible
r = computeExcavationCompliance({ work_type: "Roadway Excavation" });
assert(r.visibleSections.has("6b"), "Section 6b visible for Roadway work");

console.log("PASS — all 8 compliance scenarios green");
