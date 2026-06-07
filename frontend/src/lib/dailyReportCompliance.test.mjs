// Phase 10D · Path A simplification smoke test.
import { computeDailyReportCompliance } from "./dailyReportCompliance.js";

function assert(cond, label) {
  if (!cond) { console.error("FAIL:", label); process.exit(1); }
  console.log("ok:", label);
}

// 1. Empty → Action Required, no paragraphs
let r = computeDailyReportCompliance({});
assert(r.status === "Action Required", "empty form Action Required");
assert(r.items.length > 0, "items present");
assert(r.items.every((it) => !("why" in it) && !("action" in it)), "no paragraph 'why'/'action' on items");
assert(r.items.every((it) => it.label && it.label.split(" ").length <= 4), "labels are ≤ 4 words");

// 2. Happy → Ready to Submit
const happy = {
  project_name: "T", prepared_by: "F", excavation_activity_today: "No",
  masci_crews: [{}], photos: Array.from({length: 6}, () => ({})),
  prepared_by_signature: "x",
};
r = computeDailyReportCompliance(happy);
assert(r.status === "Ready to Submit", "happy → Ready to Submit");
assert(r.items.length === 0, "no items when ready");

// 3. Excavation YES + no link
r = computeDailyReportCompliance({ ...happy, excavation_activity_today: "Yes", linked_excavation_ids: [] });
assert(r.items.some((x) => x.id === "excavation_link"), "excavation link required");
assert(r.items.find((x) => x.id === "excavation_link").label === "Link Excavation", "label is 'Link Excavation'");

// 4. Items have jumpTo
r = computeDailyReportCompliance({});
assert(r.items.every((it) => it.jumpTo), "every item has jumpTo");

// 5. No paragraph why/action fields anywhere
const flat = JSON.stringify(r);
assert(!flat.includes("Owners and the GC"), "no Owners/GC paragraph");
assert(!flat.includes("Daily Report must name"), "no 'must name' paragraph");

console.log("PASS — Path A compact compliance engine verified");
