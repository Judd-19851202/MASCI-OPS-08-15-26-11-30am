// statusBadges TR-0005 extension self-test.
// Run via: cd /app/frontend && node src/lib/statusBadges.test.mjs
//
// This is a lightweight node-runnable smoke check (no jest harness needed)
// that proves the TR-0005 extension preserves backwards-compatibility AND
// the new domains + canonical labels behave as designed.

import {
  tintFor,
  labelFor,
  STATUS_DOMAINS,
  STATUS_LABEL_MAP,
} from "./statusBadges.js";

let failures = 0;
function assert(cond, label) {
  if (cond) {
    console.log(`  ok · ${label}`);
  } else {
    console.error(`  FAIL · ${label}`);
    failures += 1;
  }
}

// ─── Backwards compatibility ────────────────────────────────────
console.log("\n[1] Backwards compatibility (existing 7 domains untouched)");
assert(STATUS_DOMAINS.po, "po domain still registered");
assert(STATUS_DOMAINS.task, "task domain still registered");
assert(STATUS_DOMAINS.priority, "priority domain still registered");
assert(STATUS_DOMAINS.doc_exp, "doc_exp domain still registered");
assert(STATUS_DOMAINS.lifecycle, "lifecycle domain still registered");
assert(STATUS_DOMAINS.ca, "ca domain still registered");
assert(STATUS_DOMAINS.severity, "severity domain still registered");
assert(
  tintFor("po", "Approved").includes("emerald"),
  "tintFor(po, Approved) still returns emerald"
);
assert(
  tintFor("lifecycle", "Active").includes("emerald"),
  "tintFor(lifecycle, Active) still returns emerald"
);

// ─── New domains present ────────────────────────────────────────
console.log("\n[2] New TR-0005 domains registered");
for (const k of [
  "incident",
  "daily_report",
  "qaqc",
  "site_inspection",
  "asset_transfer",
  "dispatch",
  "fleet_dvir",
  "constraint",
]) {
  assert(STATUS_DOMAINS[k], `${k} domain registered`);
}

// ─── New domain tints work ──────────────────────────────────────
console.log("\n[3] New domain tints");
assert(
  tintFor("qaqc", "DEFICIENCY_RAISED").includes("amber"),
  "qaqc DEFICIENCY_RAISED is amber"
);
assert(
  tintFor("qaqc", "CLOSED").includes("emerald"),
  "qaqc CLOSED is emerald"
);
assert(
  tintFor("incident", "reopened").includes("rose"),
  "incident reopened is rose"
);
assert(
  tintFor("asset_transfer", "In Transit").includes("blue"),
  "asset_transfer In Transit is blue"
);
assert(
  tintFor("fleet_dvir", "Out of Service").includes("rose"),
  "fleet_dvir Out of Service is rose"
);
assert(
  tintFor("constraint", "monitoring").includes("amber"),
  "constraint monitoring is amber"
);
assert(
  tintFor("dispatch", "Pending Review").includes("amber"),
  "dispatch Pending Review is amber"
);

// ─── Unknown domain falls back ──────────────────────────────────
console.log("\n[4] Fallback tint for unknown domain/value");
assert(
  tintFor("unknown_domain", "Anything").includes("slate"),
  "unknown domain falls back to slate"
);
assert(
  tintFor("qaqc", "MARTIAN_STATE").includes("slate"),
  "unknown value within known domain falls back to slate"
);

// ─── labelFor · canonical mapping ───────────────────────────────
console.log("\n[5] Canonical operator-target labels");
assert(
  labelFor("qaqc", "DEFICIENCY_RAISED") === "Needs Revision",
  "qaqc DEFICIENCY_RAISED → Needs Revision"
);
assert(
  labelFor("qaqc", "PENDING_RE_INSPECTION") === "Needs Correction",
  "qaqc PENDING_RE_INSPECTION → Needs Correction"
);
assert(
  labelFor("qaqc", "CLOSED") === "Closed",
  "qaqc CLOSED → Closed"
);
assert(
  labelFor("incident", "open") === "Action Required",
  "incident open → Action Required"
);
assert(
  labelFor("incident", "reopened") === "Reopened",
  "incident reopened → Reopened"
);
assert(
  labelFor("daily_report", "PENDING_REVIEW") === "Pending Verification",
  "daily_report PENDING_REVIEW → Pending Verification"
);
assert(
  labelFor("asset_transfer", "In Transit") === "Pending Closure",
  "asset_transfer In Transit → Pending Closure"
);
assert(
  labelFor("constraint", "monitoring") === "Pending Verification",
  "constraint monitoring → Pending Verification"
);

// ─── labelFor · humanize fallback ───────────────────────────────
console.log("\n[6] labelFor falls back to humanized value when no mapping");
assert(
  labelFor("qaqc", "MARTIAN_STATE") === "Martian State",
  "unknown qaqc value humanizes (SCREAMING_SNAKE → Title Case)"
);
assert(
  labelFor("po", "Approved") === "Approved",
  "po Approved passes through unchanged (no label map for po; title-case already)"
);
assert(
  labelFor("nonexistent", "in_progress") === "In Progress",
  "unmapped domain humanizes snake_case"
);
assert(
  labelFor("incident", null) === "" && labelFor("incident", undefined) === "",
  "labelFor handles null/undefined safely"
);

// ─── Result ──────────────────────────────────────────────────────
console.log("");
if (failures === 0) {
  console.log("✅ ALL TESTS PASSED · TR-0005 extension is safe to ship.");
  process.exit(0);
} else {
  console.error(`❌ ${failures} TEST(S) FAILED · do not ship.`);
  process.exit(1);
}
