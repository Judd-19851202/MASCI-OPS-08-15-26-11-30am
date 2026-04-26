import React from "react";
import { cn } from "@/lib/utils";

/**
 * Official MASCI logos. Three variants — these are the ONLY brand assets
 * used anywhere in the app:
 *
 *   - "mark"     → /masci-mark.png         (red M with white swoosh)
 *   - "wordmark" → /masci-wordmark.png     (red MASCI text)
 *   - "lockup"   → /masci-full-lockup.png  (full MASCI SAFETY badge)
 *
 * All 3 source files have a SOLID BLACK canvas baked in. Mark + wordmark
 * are sized by HEIGHT; the lockup is sized by WIDTH because of its
 * landscape badge proportions.
 */

const HEIGHT_MAP = {
  sm: "h-8",
  md: "h-10",
  lg: "h-14",
  xl: "h-20",
  "2xl": "h-28",
};

const LOCKUP_WIDTH_MAP = {
  sm: "w-40",
  md: "w-56",
  lg: "w-72",
  xl: "w-80",
  "2xl": "w-96",
  "3xl": "w-[28rem]",
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
        alt="MASCI Safety — No Shortcuts · No Exceptions"
        className={cn(w, "h-auto select-none rounded-md", className)}
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
        className={cn(h, "w-auto select-none rounded-sm", className)}
        data-testid="masci-logo-wordmark"
        draggable={false}
      />
    );
  }
  return (
    <img
      src="/masci-mark.png"
      alt="MASCI"
      className={cn(h, "w-auto select-none rounded-sm", className)}
      data-testid="masci-logo-mark"
      draggable={false}
    />
  );
};
