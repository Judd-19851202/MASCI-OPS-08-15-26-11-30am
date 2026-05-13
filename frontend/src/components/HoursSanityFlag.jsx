// HoursSanityFlag.jsx — iter100
//
// Two sanity flags that catch payroll typos before they become checks:
//
//   1. <DailyHoursFlag hours={n} /> — single-day flag. Lights up when a
//      foreman enters more than 16 hrs for one person on one day (a
//      double-shift that almost never happens — usually a missing
//      decimal: "60" instead of "6.0", "120" instead of "12.0").
//
//   2. <WeeklyHoursFlag totalHours={n} /> — weekly rollup flag. Lights
//      up on the HR Time Verification screen when an employee's total
//      for the week exceeds 80 hrs. 80 hrs/week = 16 hrs/day average,
//      almost certainly a data-entry error and worth flagging before
//      payroll signs off.
//
// Both render as compact amber/red chips with an alert-triangle icon
// and a hover tooltip explaining what triggered them. Designed to be
// IGNORABLE (don't block submission) — humans validate, don't gatekeep.

import React from "react";
import { AlertTriangle } from "lucide-react";

const SINGLE_DAY_LIMIT = 16; // hrs/day — crosses into "double shift" territory
const WEEKLY_LIMIT = 80;     // hrs/week — crosses into "this is impossible" territory

function chipBase(severity) {
  if (severity === "red") {
    return "inline-flex items-center gap-1 px-2 py-0.5 rounded bg-red-50 border border-red-300 text-red-800 text-[11px] font-mono uppercase tracking-wide font-bold";
  }
  return "inline-flex items-center gap-1 px-2 py-0.5 rounded bg-amber-50 border border-amber-300 text-amber-900 text-[11px] font-mono uppercase tracking-wide font-bold";
}

export function DailyHoursFlag({ hours, testId = "daily-hours-flag" }) {
  const n = parseFloat(hours);
  if (!isFinite(n) || n <= SINGLE_DAY_LIMIT) return null;
  const severity = n > 24 ? "red" : "amber";
  return (
    <span
      className={chipBase(severity)}
      title={`${n} hrs in a single day. Double-check — almost certainly a typo (60 ≠ 6.0, 120 ≠ 12.0).`}
      data-testid={testId}
    >
      <AlertTriangle className="w-3 h-3" />
      Check hrs ({n}h)
    </span>
  );
}

export function WeeklyHoursFlag({ totalHours, testId = "weekly-hours-flag" }) {
  const n = parseFloat(totalHours);
  if (!isFinite(n) || n <= WEEKLY_LIMIT) return null;
  const severity = n > 120 ? "red" : "amber";
  return (
    <span
      className={chipBase(severity)}
      title={`${n} hrs for the week — averages ${(n / 7).toFixed(1)} hrs/day. Verify with the foreman before payroll.`}
      data-testid={testId}
    >
      <AlertTriangle className="w-3 h-3" />
      Verify week ({n}h)
    </span>
  );
}

export default DailyHoursFlag;
