import React from "react";
import { useT } from "@/lib/i18n";

/**
 * TRACK 19.11 · Reusable Platform Primitive · ProgressRail
 * ---------------------------------------------------------
 * Compact multi-step progress indicator for operational forms.
 *
 * Consumed by Equipment Pre-Op (Track 19.11 MAIN) and reusable
 * by DVIR / Safety Meeting / Toolbox Meeting in subsequent tracks.
 *
 * Bilingual (labels are passed pre-translated by the parent). This
 * component only renders positional state.
 *
 * States per step: "done" | "current" | "todo".
 * Click-to-jump for "done" steps (rewind); optional.
 */
export function ProgressRail({
  steps = [],
  currentIndex = 0,
  onJump = null,
  testId = "progress-rail",
}) {
  const { t } = useT();
  const total = steps.length || 1;
  const doneCount = steps.filter((_, i) => i < currentIndex).length;
  const pct = Math.round((doneCount / total) * 100);

  return (
    <div
      className="w-full space-y-2"
      data-testid={testId}
      role="progressbar"
      aria-valuenow={pct}
      aria-valuemin={0}
      aria-valuemax={100}
    >
      {/* Compact percentage strip (mobile-first) */}
      <div className="flex items-center justify-between text-[10px] font-mono uppercase tracking-[0.18em] text-slate-500">
        <span>
          {t("Step")} {Math.min(currentIndex + 1, total)} / {total}
        </span>
        <span data-testid={`${testId}-pct`}>{pct}%</span>
      </div>
      <div className="relative h-1.5 rounded-full bg-slate-200 overflow-hidden">
        <div
          className="absolute inset-y-0 left-0 bg-red-700 transition-all duration-300"
          style={{ width: `${pct}%` }}
        />
      </div>
      {/* Optional per-step chip row (visible only on wider screens to avoid crowding) */}
      <ol className="hidden sm:flex flex-wrap gap-1.5 pt-1">
        {steps.map((s, i) => {
          const state = i < currentIndex ? "done" : i === currentIndex ? "current" : "todo";
          const clickable = state === "done" && onJump;
          return (
            <li key={s.key || i}>
              <button
                type="button"
                disabled={!clickable}
                onClick={clickable ? () => onJump(i) : undefined}
                className={`px-2 py-0.5 rounded-md text-[10px] font-mono uppercase tracking-[0.15em] border transition-colors ${
                  state === "done"
                    ? "bg-emerald-50 text-emerald-800 border-emerald-300 hover:bg-emerald-100 cursor-pointer"
                    : state === "current"
                    ? "bg-red-700 text-white border-red-800"
                    : "bg-slate-50 text-slate-400 border-slate-200"
                } disabled:cursor-default`}
                data-testid={`${testId}-step-${i}`}
                data-step-state={state}
              >
                <span className="mr-1 opacity-70">{String(i + 1).padStart(2, "0")}</span>
                {s.label}
              </button>
            </li>
          );
        })}
      </ol>
    </div>
  );
}

export default ProgressRail;
