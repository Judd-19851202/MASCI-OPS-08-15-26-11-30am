/**
 * BrandingProvider — Track 15.67 Phase 3
 * =======================================
 *
 * Fetches `/api/branding/current` ONCE at app boot and exposes the
 * active tenant's customer-visible strings via the `useBranding()`
 * hook. Components import this hook instead of hardcoding MASCI
 * strings. Cache is invalidated when an admin saves the tenant
 * branding doc (the TenantBrandingPanel calls `refreshBranding()`
 * directly after a successful save).
 *
 * Shape:
 *   {
 *     tenant_key,            // "masci" | "tenant_x" | …
 *     company_name,          // "MASCI" / "Demo Construction LLC"
 *     platform_display_name, // "MASCI Operations Platform"
 *     platform_short_name,   // "MASCI Hub"
 *     support_email,
 *     safety_email,
 *     hr_email,
 *     operations_email,
 *     logo_url,
 *     primary_color,
 *     marketing_url,
 *     loading,               // true while first fetch in flight
 *     refresh,               // () => Promise<void>
 *   }
 */
import React, { createContext, useContext, useEffect, useState, useCallback } from "react";

// Tenant-neutral defaults — the resolver always returns the active
// tenant's strings, but if the API call fails (offline / 503) we render
// generic strings instead of a crash. NEVER include "MASCI" in these.
const NEUTRAL_DEFAULTS = {
  tenant_key: "",
  company_name: "Customer",
  platform_display_name: "Operations Platform",
  // TRACK 18.04 · "Hub" eliminated from user-facing branding fallback.
  // Falls back to the company name when present; otherwise just "Ops".
  platform_short_name: "Ops",
  support_email: "",
  safety_email: "",
  hr_email: "",
  operations_email: "",
  logo_url: "",
  primary_color: "#0F766E",
  marketing_url: "",
};

const BrandingContext = createContext({
  ...NEUTRAL_DEFAULTS,
  loading: true,
  refresh: async () => {},
});

const BRANDING_URL = `${process.env.REACT_APP_BACKEND_URL}/api/branding/current`;

// Track 15.68 · Tenant preview override. URL param `?tenantPreview=customer2`
// (or sessionStorage `branding.previewTenant`) flows through as an
// `X-Tenant-Preview` header — preview/dev only; backend refuses it in
// production. Used for visual QA of Customer #2 chrome without
// flipping the live tenant.
function getPreviewTenant() {
  if (typeof window === "undefined") return "";
  try {
    const url = new URL(window.location.href);
    const fromQuery = url.searchParams.get("tenantPreview");
    if (fromQuery) {
      window.sessionStorage.setItem("branding.previewTenant", fromQuery);
      return fromQuery;
    }
    return window.sessionStorage.getItem("branding.previewTenant") || "";
  } catch {
    return "";
  }
}

export function BrandingProvider({ children }) {
  const [branding, setBranding] = useState({ ...NEUTRAL_DEFAULTS, loading: true });

  const load = useCallback(async () => {
    try {
      const previewTk = getPreviewTenant();
      const headers = {};
      if (previewTk) headers["X-Tenant-Preview"] = previewTk;
      const r = await fetch(BRANDING_URL, { credentials: "omit", headers });
      if (!r.ok) throw new Error(`branding fetch ${r.status}`);
      const data = await r.json();
      // Track 15.68B · derive slug for filename templates etc.
      const slugBase = (data.company_name || "tenant").toString();
      data.slug = slugBase
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "_")
        .replace(/^_+|_+$/g, "")
        .slice(0, 32) || "tenant";
      try {
        window.sessionStorage.setItem("branding.tenantKey", data.tenant_key || "masci");
        window.sessionStorage.setItem("branding.shortName", data.platform_short_name || "Ops");
        window.sessionStorage.setItem("branding.slug", data.slug);
        window.sessionStorage.setItem("branding.companyName", data.company_name || "");
      } catch { /* sessionStorage may be unavailable */ }
      // Track 15.68D · Override the static index.html title for non-MASCI
      // tenants so Customer #2 never sees "MASCI" in the browser tab
      // before a usePageTitle() call site fires.
      try {
        if (typeof document !== "undefined" && (data.tenant_key && data.tenant_key !== "masci")) {
          const display = data.platform_display_name || "Operations Platform";
          if (document.title && document.title.includes("MASCI")) {
            document.title = display;
          }
        }
      } catch { /* document may be unavailable */ }
      setBranding({ ...NEUTRAL_DEFAULTS, ...data, loading: false, previewTenant: previewTk });
    } catch (_e) {
      setBranding((prev) => ({ ...prev, loading: false }));
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const value = {
    ...branding,
    refresh: load,
  };

  return (
    <BrandingContext.Provider value={value}>
      {children}
    </BrandingContext.Provider>
  );
}

export function useBranding() {
  return useContext(BrandingContext);
}

export default BrandingProvider;
