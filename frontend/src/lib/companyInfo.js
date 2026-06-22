// Company info persisted on the device (localStorage).
// Used on the printed PDF footer and on photo watermarks for legal/insurance filings.
//
// Track 15.68 · Tenant-aware default. The MASCI defaults below are only
// returned when the active tenant is MASCI; for any other tenant, the
// defaults come from the BrandingProvider doc and the operator's saved
// localStorage overrides (which they fill in via the Admin → Company
// Info panel on first onboarding).

const STORAGE_KEY = "masci.companyInfo.v1";

export const DEFAULT_COMPANY_INFO = {
  company_name: "MASCI General Contractors Inc.",
  tagline: "",
  address: "5752 South Ridgewood Avenue",
  city_state_zip: "Port Orange, FL 32127-6442",
  phone: "386-322-4500",
  email: "safety@mascigc.com",
  website: "mascigc.com",
};

// Track 15.68 · Tenant-neutral defaults for non-MASCI tenants. Used as
// the fallback when localStorage is empty AND the tenant is not MASCI.
const NEUTRAL_COMPANY_INFO = {
  company_name: "",
  tagline: "",
  address: "",
  city_state_zip: "",
  phone: "",
  email: "",
  website: "",
};

function _isMasciTenant() {
  if (typeof window === "undefined") return true;
  try {
    // Best-effort: BrandingProvider stashes the active tenant in
    // sessionStorage on first load. If absent, assume MASCI (the
    // preview deployment).
    const tk = window.sessionStorage.getItem("branding.tenantKey") || "masci";
    return tk === "masci";
  } catch {
    return true;
  }
}

export function getCompanyInfo() {
  if (typeof window === "undefined") return DEFAULT_COMPANY_INFO;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    const stored = raw ? JSON.parse(raw) : null;
    const base = _isMasciTenant() ? DEFAULT_COMPANY_INFO : NEUTRAL_COMPANY_INFO;
    const out = { ...base };
    for (const k of Object.keys(base)) {
      const v = stored?.[k];
      if (typeof v === "string" && v.trim().length > 0) {
        out[k] = v;
      }
    }
    return out;
  } catch {
    return _isMasciTenant() ? DEFAULT_COMPANY_INFO : NEUTRAL_COMPANY_INFO;
  }
}

export function saveCompanyInfo(info) {
  try {
    window.localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ ...DEFAULT_COMPANY_INFO, ...info })
    );
  } catch {
    /* ignore quota errors */
  }
}

/**
 * Best-effort tel: URI for a US phone number. Strips everything except
 * digits and a leading + so dial-out works on iOS/Android.
 */
export function buildTelHref(phone) {
  if (!phone) return "";
  const cleaned = String(phone).replace(/[^\d+]/g, "");
  return cleaned ? `tel:${cleaned}` : "";
}
