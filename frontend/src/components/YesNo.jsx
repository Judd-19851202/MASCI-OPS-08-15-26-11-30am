import React from "react";
import { cn } from "@/lib/utils";

/**
 * Segmented YES / NO (or YES / NO / N/A) toggle. Tap-friendly, high-contrast.
 *
 * Props:
 *   value: "" | "Yes" | "No" | "N/A"
 *   onChange: (v) => void
 *   options: array of strings, e.g. ["Yes", "No"] or ["Yes", "No", "N/A"]
 *   testId: data-testid prefix
 */
export const YesNo = ({
  value,
  onChange,
  options = ["Yes", "No"],
  testId = "yesno",
  size = "md",
}) => {
  const heightCls = size === "lg" ? "h-14" : "h-12";
  return (
    <div
      role="radiogroup"
      className={cn(
        "inline-flex w-full overflow-hidden rounded-md border-2 border-slate-300 bg-white",
        heightCls
      )}
      data-testid={testId}
    >
      {options.map((opt) => {
        const active = value === opt;
        const isYes = opt.toLowerCase() === "yes";
        const isNo = opt.toLowerCase() === "no";
        const activeCls = active
          ? isYes
            ? "bg-green-600 text-white"
            : isNo
            ? "bg-red-600 text-white"
            : "bg-slate-800 text-white"
          : "bg-white text-slate-700 hover:bg-slate-100";
        return (
          <button
            key={opt}
            type="button"
            role="radio"
            aria-checked={active}
            onClick={() => onChange(opt)}
            data-testid={`${testId}-${opt.replace("/", "-").toLowerCase()}`}
            className={cn(
              "flex-1 text-base font-bold tracking-wide uppercase transition-colors duration-150 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-inset",
              activeCls,
              "border-r border-slate-300 last:border-r-0"
            )}
          >
            {opt}
          </button>
        );
      })}
    </div>
  );
};
