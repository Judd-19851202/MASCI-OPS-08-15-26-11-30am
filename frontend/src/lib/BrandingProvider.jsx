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
  platform_short_name: "Ops Hub",
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

export function BrandingProvider({ children }) {
  const [branding, setBranding] = useState({ ...NEUTRAL_DEFAULTS, loading: true });

  const load = useCallback(async () => {
    try {
      const r = await fetch(BRANDING_URL, { credentials: "omit" });
      if (!r.ok) throw new Error(`branding fetch ${r.status}`);
      const data = await r.json();
      setBranding({ ...NEUTRAL_DEFAULTS, ...data, loading: false });
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
