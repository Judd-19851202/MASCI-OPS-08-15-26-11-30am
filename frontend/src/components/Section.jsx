import React from "react";
import { cn } from "@/lib/utils";

export const Section = ({ number, title, children, className = "" }) => {
  return (
    <section
      className={cn(
        "bg-white border-2 border-slate-300 rounded-md p-5 sm:p-7 print:break-inside-avoid",
        className
      )}
      data-testid={`section-${number}`}
    >
      <div className="flex items-baseline gap-3 mb-5 pb-3 border-b-2 border-slate-200">
        <span className="font-mono text-xs uppercase tracking-[0.2em] text-yellow-600">
          Section {number}
        </span>
        <h2 className="font-display text-xl sm:text-2xl font-bold text-slate-900">
          {title}
        </h2>
      </div>
      <div className="space-y-5">{children}</div>
    </section>
  );
};

export const ChecklistRow = ({ label, children, testId }) => (
  <div
    className="grid grid-cols-1 md:grid-cols-[1fr_220px] gap-3 md:gap-6 items-start md:items-center py-3 border-b border-slate-100 last:border-b-0"
    data-testid={testId}
  >
    <span className="text-base text-slate-800 leading-snug">{label}</span>
    <div>{children}</div>
  </div>
);
