import React from "react";
import { CheckCircle2, AlertTriangle, ShieldX } from "lucide-react";
import { gradeToneClasses } from "@/lib/grading";

/**
 * Grade badge — compact pill for dashboard rows.
 */
export const GradePill = ({ grade, testId }) => {
  if (!grade || grade.total === 0) {
    return (
      <span
        className="inline-flex items-center px-2 py-0.5 bg-slate-100 text-slate-500 text-[10px] font-mono uppercase tracking-wider rounded"
        data-testid={testId}
      >
        —
      </span>
    );
  }
  const cls = gradeToneClasses(grade);
  const Icon =
    grade.status === "FAIL"
      ? grade.auto_fail_count > 0
        ? ShieldX
        : AlertTriangle
      : CheckCircle2;
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-1 ${cls} text-[11px] font-mono font-bold uppercase tracking-wider rounded`}
      data-testid={testId}
    >
      <Icon className="w-3 h-3" />
      {grade.score}% · {grade.status}
    </span>
  );
};

/**
 * Grade banner — full-width banner for the report view + live grade on the form.
 */
export const GradeBanner = ({ grade, label = "Inspection Grade" }) => {
  if (!grade) return null;
  const cls = gradeToneClasses(grade);
  const Icon =
    grade.status === "FAIL"
      ? grade.auto_fail_count > 0
        ? ShieldX
        : AlertTriangle
      : CheckCircle2;
  const empty = grade.total === 0;
  return (
    <div
      className={`${empty ? "bg-slate-100 text-slate-700" : cls} rounded-md p-4 sm:p-5 flex items-center justify-between gap-4 print-section`}
      data-testid="grade-banner"
    >
      <div className="flex items-center gap-3 sm:gap-4 min-w-0">
        <div className="shrink-0 w-12 h-12 sm:w-14 sm:h-14 rounded-md bg-black/20 flex items-center justify-center">
          <Icon className="w-6 h-6 sm:w-8 sm:h-8" />
        </div>
        <div className="min-w-0">
          <div className="font-mono text-[10px] sm:text-xs uppercase tracking-[0.25em] opacity-90">
            {label}
          </div>
          <div className="font-display font-black text-3xl sm:text-4xl leading-none mt-1">
            {empty ? "—" : `${grade.score}%`}
            {!empty && (
              <span className="text-base sm:text-lg ml-2 align-middle">
                {grade.status}
              </span>
            )}
          </div>
          {!empty && grade.auto_fail_count > 0 && (
            <div className="font-mono text-[10px] uppercase tracking-wider mt-1">
              {grade.auto_fail_count} auto-fail item{grade.auto_fail_count === 1 ? "" : "s"} triggered
            </div>
          )}
        </div>
      </div>
      <div className="text-right font-mono text-[10px] sm:text-xs uppercase tracking-wider leading-tight shrink-0">
        <div>
          <span className="text-base sm:text-lg font-bold">{grade.yes}</span> yes
        </div>
        <div>
          <span className="text-base sm:text-lg font-bold">{grade.no}</span> no
        </div>
        <div className="opacity-75">
          / {grade.total} item{grade.total === 1 ? "" : "s"}
        </div>
      </div>
    </div>
  );
};
