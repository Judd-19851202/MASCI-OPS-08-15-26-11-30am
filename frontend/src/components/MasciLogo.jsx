import React from "react";
import { cn } from "@/lib/utils";

/**
 * Official MASCI logo. Three variants:
 *   - "mark"     : compact M-with-swoosh icon (for tight headers / favicons)
 *   - "wordmark" : MASCI text only
 *   - "lockup"   : full MASCI SAFETY badge with tagline (hero / print header)
 *
 * Mark / wordmark are sized by HEIGHT (the natural way for a tall logomark
 * and a horizontal wordmark). Lockup is sized by WIDTH because it has a 3:2
 * aspect ratio and contains stacked text — undersizing it by height
 * compresses the brand text into illegible mush. The width-based map below
 * keeps the lockup readable at every breakpoint and on the printed PDF.
 */

const HEIGHT_MAP = {
  sm: "h-8",
  md: "h-10",
  lg: "h-14",
  xl: "h-20",
  "2xl": "h-28",
};

const LOCKUP_WIDTH_MAP = {
  sm: "w-40",     // 160px
  md: "w-56",     // 224px
  lg: "w-72",     // 288px
  xl: "w-80",     // 320px
  "2xl": "w-96",  // 384px
  "3xl": "w-[28rem]", // 448px
};

export const MasciLogo = ({
  variant = "mark",
  className = "",
  size = "md",
}) => {
  if (variant === "lockup") {
    const w = LOCKUP_WIDTH_MAP[size] || LOCKUP_WIDTH_MAP.md;
    return (
      <img
        src="/masci-full-lockup.png"
        alt="MASCI Safety — Accountability · Discipline · Execution"
        className={cn(w, "h-auto select-none", className)}
        data-testid="masci-logo-lockup"
        draggable={false}
      />
    );
  }
  const h = HEIGHT_MAP[size] || HEIGHT_MAP.md;
  if (variant === "wordmark") {
    return (
      <img
        src="/masci-wordmark.png"
        alt="MASCI"
        className={cn(h, "w-auto select-none", className)}
        data-testid="masci-logo-wordmark"
        draggable={false}
      />
    );
  }
  return (
    <img
      src="/masci-mark.png"
      alt="MASCI"
      className={cn(h, "w-auto select-none", className)}
      data-testid="masci-logo-mark"
      draggable={false}
    />
  );
};
