// Grading engine for an inspection.
// Score = Yes / (Yes + No) * 100. N/A and blank are skipped.
// Status: FAIL if any auto-fail item is "No", or score < PASS_THRESHOLD; else PASS.
import {
  PPE_ITEMS,
  SITE_HAZARD_ITEMS,
  CONDITIONAL_SECTIONS,
} from "@/lib/inspectionSchema";

export const PASS_THRESHOLD = 74; // anything below this is a fail

const YES = "Yes";
const NO = "No";

function tally(value, autoFail, acc) {
  const v = (value || "").toString();
  if (v === YES) acc.yes += 1;
  else if (v === NO) {
    acc.no += 1;
    if (autoFail) acc.autoFailItems += 1;
  }
  // N/A and blank are skipped
}

export function computeGrade(data) {
  const acc = { yes: 0, no: 0, autoFailItems: 0 };
  if (!data) return finalize(acc);

  // PPE Compliance
  PPE_ITEMS.forEach((it) => tally(data.ppe_compliance?.[it.key], false, acc));

  // Site Hazards
  SITE_HAZARD_ITEMS.forEach((it) =>
    tally(data.site_hazards?.[it.key], false, acc)
  );

  // Conditional sections — only counted if applies === "Yes"
  CONDITIONAL_SECTIONS.forEach((sec) => {
    const block = data[sec.key];
    if (!block || block.applies !== YES) return;
    sec.items.forEach((it) =>
      tally(block.items?.[it.key], it.autoFail, acc)
    );
  });

  return finalize(acc);
}

function finalize({ yes, no, autoFailItems }) {
  const total = yes + no;
  const score = total === 0 ? 100 : Math.round((yes / total) * 100);
  const failed = autoFailItems > 0 || (total > 0 && score < PASS_THRESHOLD);
  return {
    yes,
    no,
    total, // applicable items (yes + no)
    auto_fail_count: autoFailItems,
    score,
    status: failed ? "FAIL" : "PASS",
    pass_threshold: PASS_THRESHOLD,
  };
}

export function gradeToneClasses(grade) {
  if (!grade) return "bg-slate-200 text-slate-700";
  if (grade.status === "FAIL") return "bg-red-700 text-white";
  if (grade.score >= 90) return "bg-green-700 text-white";
  if (grade.score >= 80) return "bg-green-600 text-white";
  return "bg-yellow-500 text-slate-900"; // 74-79 = pass-but-warn
}
