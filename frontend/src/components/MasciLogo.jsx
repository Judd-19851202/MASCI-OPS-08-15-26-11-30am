import React from "react";
import { cn } from "@/lib/utils";

/**
 * Official MASCI logo.
 *
 * Three variants:
 *   - "mark"     : compact M-with-crosshair emblem (favicons, tight headers)
 *   - "wordmark" : "MASCI" red text only
 *   - "lockup"   : DOM-composed M emblem + "MASCI SAFETY" + slogan stripe.
 *
 * The lockup intentionally does NOT use the prebaked masci-full-lockup.png
 * — that asset has faded gray "SAFETY" + tagline text rendered into the
 * pixels, which prints washed-out. Composing here from the clean mark.png
 * + crisp CSS typography keeps the brand sharp at every breakpoint and on
 * the printed PDF.
 */

const HEIGHT_MAP = {
  sm: "h-8",
  md: "h-10",
  lg: "h-14",
  xl: "h-20",
  "2xl": "h-28",
};

// Mark heights inside the composed lockup (the wordmark + emblem stack
// scales together off this).
const LOCKUP_MARK_HEIGHT = {
  sm: 36,
  md: 48,
  lg: 64,
  xl: 80,
  "2xl": 100,
  "3xl": 124,
};

const LOCKUP_TITLE_PX = {
  sm: 22,
  md: 30,
  lg: 40,
  xl: 50,
  "2xl": 62,
  "3xl": 78,
};

export const MasciLogo = ({
  variant = "mark",
  className = "",
  size = "md",
  onDark = false,
}) => {
  if (variant === "lockup") {
    const markH = LOCKUP_MARK_HEIGHT[size] || LOCKUP_MARK_HEIGHT.md;
    const titlePx = LOCKUP_TITLE_PX[size] || LOCKUP_TITLE_PX.md;
    const safetyPx = Math.round(titlePx * 0.72);
    const taglinePx = Math.max(9, Math.round(titlePx * 0.22));

    // Color theme — inverted on dark headers so SAFETY + tagline stay
    // legible on the slate-900 Hub / Admin / View page bars.
    const safetyColor = onDark ? "#F8FAFC" : "#0F172A";
    const taglineColor = onDark ? "#CBD5E1" : "#0F172A";
    const sloganColor = onDark ? "#FCA5A5" : "#C8102E";

    return (
      <div
        className={cn("select-none", className)}
        data-testid="masci-logo-lockup"
        role="img"
        aria-label="MASCI Safety — Accountability · Discipline · Execution"
      >
        <div
          style={{
            // Inline display so callers' className (e.g. `hidden sm:block`
            // wrapping us) controls VISIBILITY but the inner layout stays
            // a horizontal flex composition every time we're rendered.
            display: "flex",
            alignItems: "center",
            gap: Math.round(markH * 0.18),
          }}
        >
        <img
          src="/masci-mark.png"
          alt=""
          width={markH}
          height={markH}
          draggable={false}
          style={{
            height: markH,
            width: markH,
            objectFit: "contain",
            flex: "0 0 auto",
            // Keep this sharp on print
            imageRendering: "-webkit-optimize-contrast",
          }}
        />
        <div className="leading-none flex flex-col" style={{ gap: 2 }}>
          {/* MASCI · SAFETY title row */}
          <div
            style={{
              display: "flex",
              alignItems: "baseline",
              gap: Math.round(titlePx * 0.18),
              fontFamily: "'Archivo Black', 'Inter', system-ui, sans-serif",
              letterSpacing: "-0.02em",
              lineHeight: 1,
            }}
          >
            <span
              style={{
                color: "#C8102E",
                fontSize: titlePx,
                fontWeight: 900,
              }}
            >
              MASCI
            </span>
            <span
              style={{
                color: safetyColor,
                fontSize: safetyPx,
                fontWeight: 900,
                letterSpacing: "0.02em",
              }}
            >
              SAFETY
            </span>
          </div>
          {/* Tagline */}
          <div
            style={{
              fontFamily:
                "'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, monospace",
              fontSize: taglinePx,
              letterSpacing: "0.25em",
              textTransform: "uppercase",
              color: taglineColor,
              fontWeight: 700,
              marginTop: Math.round(titlePx * 0.08),
            }}
          >
            Accountability · Discipline · Execution
          </div>
          {/* Slogan stripe */}
          <div
            style={{
              fontFamily:
                "'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, monospace",
              fontSize: taglinePx,
              letterSpacing: "0.32em",
              textTransform: "uppercase",
              color: sloganColor,
              fontWeight: 800,
              marginTop: 2,
            }}
          >
            No Shortcuts · No Exceptions
          </div>
        </div>
        </div>
      </div>
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
