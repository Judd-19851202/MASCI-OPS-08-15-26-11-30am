// CollapseCard.jsx — iter383 · Phase 5C.1 · Smart Operational Disclosure.
//
// Visible-but-collapsed section header with operational status badge.
// Replaces the "hide everything behind one button" pattern with
// "every section is always visible · status is always communicated ·
// content expands on tap".
//
// Status tones (very restrained, field-first — no consumer UI brightness):
//   emerald = complete / has entries
//   amber   = incomplete / needs attention
//   slate   = optional / inactive (default)
//   rose    = required + missing (operational risk)
//
// forceOpen + lockOpen props let the parent override (e.g., severity
// auto-escalation on the incident form locks Tier-2 cards open).

import React, { useState, useEffect } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";

const TONE = {
  emerald: "bg-emerald-50 text-emerald-800 border-emerald-200",
  amber:   "bg-amber-50 text-amber-800 border-amber-200",
  slate:   "bg-slate-50 text-slate-700 border-slate-200",
  rose:    "bg-rose-50 text-rose-800 border-rose-200",
};

export function CollapseCard({
  title,
  statusLabel,
  statusTone = "slate",
  defaultOpen = false,
  forceOpen = false,
  lockOpen = false,
  testId,
  children,
}) {
  const [open, setOpen] = useState(defaultOpen || forceOpen);
  useEffect(() => {
    if (forceOpen) setOpen(true);
  }, [forceOpen]);

  const isOpen = open || forceOpen;
  const Chevron = isOpen ? ChevronUp : ChevronDown;
  const toneClass = TONE[statusTone] || TONE.slate;

  return (
    <div
      className="border border-slate-200 rounded-md bg-white"
      data-testid={testId ? `${testId}-card` : undefined}
    >
      <button
        type="button"
        onClick={() => { if (!lockOpen) setOpen((o) => !o); }}
        disabled={lockOpen}
        className={`w-full flex items-center justify-between gap-3 px-3 py-3 text-left ${
          lockOpen ? "cursor-default" : "hover:bg-slate-50"
        }`}
        data-testid={testId ? `${testId}-toggle` : undefined}
        aria-expanded={isOpen}
      >
        <div className="flex-1 min-w-0">
          <div className="font-mono text-[11px] uppercase tracking-[0.2em] text-slate-600">
            {title}
          </div>
          {statusLabel && (
            <span
              className={`inline-block mt-1 px-2 py-0.5 rounded text-[11px] border ${toneClass}`}
              data-testid={testId ? `${testId}-status` : undefined}
            >
              {statusLabel}
            </span>
          )}
        </div>
        {!lockOpen && (
          <Chevron className="w-4 h-4 text-slate-500 shrink-0" />
        )}
      </button>
      {isOpen && (
        <div
          className="border-t border-slate-100 p-3"
          data-testid={testId ? `${testId}-body` : undefined}
        >
          {children}
        </div>
      )}
    </div>
  );
}

export default CollapseCard;
