// Phase 10D · Daily Report compliance engine smoke test.
// Run with: node /app/frontend/src/lib/dailyReportCompliance.test.mjs
import { computeDailyReportCompliance } from "./dailyReportCompliance.js";

function assert(cond, label) {
  if (!cond) { console.error("FAIL:", label); process.exit(1); }
  console.log("ok:", label);
}

// 1. Empty form → Action Required (many missing)
let r = computeDailyReportCompliance({});
assert(r.status === "Action Required", "empty form is Action Required");
assert(r.requirements.some((x) => x.id === "project"), "project requirement fires");
assert(r.requirements.some((x) => x.id === "prepared_by"), "prepared_by requirement fires");
assert(r.requirements.some((x) => x.id === "signature"), "signature requirement fires");

// 2. Fully clean form → Ready to Submit
const happy = {
  project_name: "Test", project_number: "001", location: "Site A",
  prepared_by: "Foreman A",
  excavation_activity_today: "No",
  masci_crews: [{ headcount: 3 }],
  photos: Array.from({ length: 6 }, (_, i) => ({ url: `p${i}` })),
  prepared_by_signature: "data:image/png;base64,xxx",
};
r = computeDailyReportCompliance(happy);
assert(r.status === "Ready to Submit", "happy path is Ready to Submit");
assert(r.requirements.length === 0, "happy path has 0 requirements");

// 3. Excavation activity YES no link → danger
r = computeDailyReportCompliance({ ...happy, excavation_activity_today: "Yes", linked_excavation_ids: [] });
assert(r.requirements.some((x) => x.id === "excavation_link"), "excavation link requirement fires");
assert(r.status === "Action Required", "excavation link missing → Action Required");

// 4. Excavation activity YES + linked → passes the gate
r = computeDailyReportCompliance({ ...happy, excavation_activity_today: "Yes", linked_excavation_ids: ["EX-2026-001"] });
assert(!r.requirements.some((x) => x.id === "excavation_link"), "excavation link gate cleared");

// 5. Photos under minimum → danger
r = computeDailyReportCompliance({ ...happy, photos: [{ url: "1" }, { url: "2" }] });
assert(r.requirements.some((x) => x.id === "photos"), "photos requirement fires");

// 6. Incident + safety not notified → danger
r = computeDailyReportCompliance({ ...happy, safety_incidents_today: "Yes" });
assert(r.requirements.some((x) => x.id === "safety_notified"), "safety_notified requirement fires");
assert(r.requirements.some((x) => x.id === "incident_report"), "incident_report requirement fires");

// 7. Weather YES no row → warn
r = computeDailyReportCompliance({ ...happy, weather_impact: "Yes", constraints: [] });
assert(r.requirements.some((x) => x.id === "weather_row"), "weather row warning fires");
assert(r.status === "Needs Review", "weather without row is Needs Review");

// 8. Coaching language only — never punitive
r = computeDailyReportCompliance({});
const titles = r.requirements.map((x) => x.title).join(" ");
assert(!/Failed|Rejected|Violation/i.test(titles), "no punitive vocabulary");

console.log("PASS — all 8 DR compliance scenarios green");
