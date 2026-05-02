import React from "react";
import { Link } from "react-router-dom";
import { cn } from "@/lib/utils";

/**
 * Official MASCI logos. Three variants — these are the ONLY brand assets
 * used anywhere in the app:
 *
 *   - "mark"     → /masci-mark.png         (bold red M — the new 2026 mark)
 *   - "wordmark" → /masci-wordmark.png     (red MASCI text)
 *   - "lockup"   → /masci-full-lockup.png  (new M badge + MASCI HUB text
 *                                           + Accountability · Adapt · Overcome)
 *
 * Each logo ships in TWO derived forms:
 *   1. Default     — transparent canvas. Floats cleanly on the slate-900
 *                    dark headers used across the app.
 *   2. -onlight    — transparent canvas AND every near-white element
 *                    (MASCI tagline text, etc.) recolored to pure black.
 *                    Drops onto white pages (Cheat Sheet, View page print
 *                    body) without an ugly black plate. Red brand
 *                    elements are preserved untouched. Pass `onLight`
 *                    to opt in.
 *                    Pass `onLight` to opt in.
 *
 * Mark + wordmark are sized by HEIGHT; the lockup is sized by WIDTH because
 * of its landscape badge proportions.
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

const SRC = {
  mark: { dark: "/masci-mark.png", light: "/masci-mark-onlight.png" },
  wordmark: {
    dark: "/masci-wordmark.png",
    light: "/masci-wordmark-onlight.png",
  },
  lockup: {
    dark: "/masci-full-lockup.png",
    light: "/masci-full-lockup-onlight.png",
  },
};

export const MasciLogo = ({
  variant = "mark",
  className = "",
  size = "md",
  onLight = false,
  homeLink = null, // e.g. "/" or "/admin" — wraps the logo in a clickable Link
}) => {
  const src = SRC[variant]?.[onLight ? "light" : "dark"] || SRC.mark.dark;

  const wrap = (img) =>
    homeLink ? (
      <Link
        to={homeLink}
        aria-label="Go to home"
        className="inline-block focus:outline-none focus:ring-2 focus:ring-red-700 rounded"
        data-testid="masci-logo-home-link"
      >
        {img}
      </Link>
    ) : (
      img
    );

  if (variant === "lockup") {
    const w = LOCKUP_WIDTH_MAP[size] || LOCKUP_WIDTH_MAP.md;
    return wrap(
      <img
        src={src}
        alt="MASCI Hub — Accountability · Adapt · Overcome"
        className={cn(w, "h-auto select-none", homeLink && "cursor-pointer", className)}
        data-testid="masci-logo-lockup"
        draggable={false}
      />
    );
  }
  const h = HEIGHT_MAP[size] || HEIGHT_MAP.md;
  if (variant === "wordmark") {
    return wrap(
      <img
        src={src}
        alt="MASCI"
        className={cn(h, "w-auto select-none", homeLink && "cursor-pointer", className)}
        data-testid="masci-logo-wordmark"
        draggable={false}
      />
    );
  }
  return wrap(
    <img
      src={src}
      alt="MASCI"
      className={cn(h, "w-auto select-none", homeLink && "cursor-pointer", className)}
      data-testid="masci-logo-mark"
      draggable={false}
    />
  );
};
