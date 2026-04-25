import React from "react";
import { cn } from "@/lib/utils";

/**
 * Official MASCI logo. Three variants:
 *   - "mark"     : compact M-with-swoosh icon (for tight headers / favicons)
 *   - "wordmark" : MASCI text only
 *   - "lockup"   : full MASCI SAFETY badge with tagline (hero / print header)
 */
export const MasciLogo = ({
  variant = "mark",
  className = "",
  size = "md",
}) => {
  const heightMap = {
    sm: "h-8",
    md: "h-10",
    lg: "h-14",
    xl: "h-20",
    "2xl": "h-28",
  };
  const h = heightMap[size] || heightMap.md;

  if (variant === "lockup") {
    return (
      <img
        src="/masci-full-lockup.png"
        alt="MASCI Safety — Accountability · Discipline · Execution"
        className={cn(h, "w-auto select-none", className)}
        data-testid="masci-logo-lockup"
        draggable={false}
      />
    );
  }
  if (variant === "wordmark") {
    return (
      <img
        src="/masci-wordmark.jpg"
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
      className={cn(h, "w-auto select-none rounded", className)}
      data-testid="masci-logo-mark"
      draggable={false}
    />
  );
};
