// HelpTip — iter148 (Phase 2.5). Small info-icon next to a confusing
// form field. Clicking/hovering reveals a short, professional popover.
//
// Design constraints (per user mandate):
//   * Lightweight — no tutorial spam, no auto-popup, no nag tooltips.
//   * Click-only on touch devices (hover doesn't fire there).
//   * Keyboard-accessible via the shadcn Popover primitive.
//   * One-line tag-line + optional 1-2 sentence body. NO walls of text.
//
// Usage:
//   <label className="flex items-center gap-1.5">
//     Priority
//     <HelpTip
//       label="What's the difference between priority and severity?"
//       body="Priority drives WHEN we act (Open queue ordering). Severity is the underlying risk level of the finding itself."
//     />
//   </label>

import React from "react";
import { Info } from "lucide-react";
import {
  Popover, PopoverContent, PopoverTrigger,
} from "@/components/ui/popover";

export function HelpTip({ label, body, testId, side = "top" }) {
  return (
    <Popover>
      <PopoverTrigger asChild>
        <button
          type="button"
          className="inline-flex items-center justify-center w-4 h-4 rounded-full text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
          aria-label={label || "Help"}
          data-testid={testId || "help-tip"}
        >
          <Info className="w-3.5 h-3.5" />
        </button>
      </PopoverTrigger>
      <PopoverContent
        side={side}
        align="start"
        className="max-w-xs p-3 text-xs"
      >
        {label && (
          <div className="font-bold text-slate-900 mb-1 leading-snug">{label}</div>
        )}
        {body && (
          <div className="text-slate-700 leading-relaxed">{body}</div>
        )}
      </PopoverContent>
    </Popover>
  );
}

export default HelpTip;
