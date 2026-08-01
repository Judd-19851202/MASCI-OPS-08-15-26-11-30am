import React from "react";
import { Link } from "react-router-dom";
import { cn } from "@/lib/utils";
import { useBranding } from "@/lib/BrandingProvider";

/**
 * Track 15.68 · Tenant-aware logo component.
 *
 * MASCI tenant (default) renders the original 3 brand assets:
 *   - "mark"     → /masci-mark.png
 *   - "wordmark" → /masci-wordmark.png
 *   - "lockup"   → /masci-full-lockup.png
 *
 * Any other tenant renders `branding.logo_url` (from
 * `/api/branding/current`). When no logo is configured, falls back to
 * a generic SVG monogram derived from `branding.company_name` so
 * Customer #2 never sees a MASCI asset and never sees a broken image.
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
  "4xl": "w-[34rem]",
  "5xl": "w-[40rem]",
};

const MASCI_SRC = {
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

function GenericMonogram({ companyName = "Customer", primaryColor = "#0F766E", className = "", testId = "tenant-logo-generic" }) {
  const letter = (companyName || "C").trim().slice(0, 1).toUpperCase();
  return (
    <div
      className={cn("inline-flex items-center justify-center rounded-md select-none font-display font-black text-white", className)}
      style={{ background: primaryColor, aspectRatio: "1", width: "auto" }}
      data-testid={testId}
      aria-label={`${companyName} logo`}
    >
      <span className="px-2">{letter}</span>
    </div>
  );
}

export const MasciLogo = ({
  variant = "mark",
  className = "",
  size = "md",
  onLight = false,
  homeLink = null,
}) => {
  const branding = useBranding();
  // Treat empty tenant_key as MASCI (default during first load).
  const isMasci = !branding?.tenant_key || branding.tenant_key === "masci";
  const masciSrc = MASCI_SRC[variant]?.[onLight ? "light" : "dark"] || MASCI_SRC.mark.dark;

  const wrap = (img) =>
    homeLink ? (
      <Link
        to={homeLink}
        aria-label="Go to MASCI Operations Platform Home"
        className="inline-block focus:outline-none focus:ring-2 focus:ring-red-700 rounded"
        data-testid="masci-logo-home-link"
      >
        {img}
      </Link>
    ) : (
      img
    );

  // Non-MASCI tenant — render branding.logo_url or generic monogram.
  if (!isMasci) {
    const h = HEIGHT_MAP[size] || HEIGHT_MAP.md;
    const w = variant === "lockup" ? (LOCKUP_WIDTH_MAP[size] || LOCKUP_WIDTH_MAP.md) : null;
    if (branding.logo_url) {
      return wrap(
        <img
          src={branding.logo_url}
          alt={branding.company_name || "Tenant"}
          className={cn(w || h, "w-auto select-none", homeLink && "cursor-pointer", className)}
          data-testid="tenant-logo-img"
          draggable={false}
          onError={(e) => {
            // Hide broken images — fallback monogram renders below.
            e.currentTarget.style.display = "none";
          }}
        />
      );
    }
    return wrap(
      <GenericMonogram
        companyName={branding.company_name}
        primaryColor={branding.primary_color}
        className={cn(w || h, "w-auto", className)}
      />
    );
  }

  // MASCI tenant — preserve historical behaviour exactly.
  if (variant === "lockup") {
    const w = LOCKUP_WIDTH_MAP[size] || LOCKUP_WIDTH_MAP.md;
    return wrap(
      <img
        src={masciSrc}
          alt="MASCI Operations Platform"
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
        src={masciSrc}
          alt="MASCI Operations Platform"
        className={cn(h, "w-auto select-none", homeLink && "cursor-pointer", className)}
        data-testid="masci-logo-wordmark"
        draggable={false}
      />
    );
  }
  return wrap(
    <img
      src={masciSrc}
      alt="MASCI Operations Platform"
      className={cn(h, "w-auto select-none", homeLink && "cursor-pointer", className)}
      data-testid="masci-logo-mark"
      draggable={false}
    />
  );
};

// Track 15.68 · Tenant-neutral export alias so new code reads cleaner.
export const TenantLogo = MasciLogo;
export default MasciLogo;
