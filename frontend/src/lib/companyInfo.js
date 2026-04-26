// Company info persisted on the device (localStorage).
// Used on the printed PDF footer and on photo watermarks for legal/insurance filings.

const STORAGE_KEY = "masci.companyInfo.v1";

export const DEFAULT_COMPANY_INFO = {
  company_name: "MASCI General Contractors Inc.",
  tagline: "No Shortcuts · No Exceptions",
  address: "5752 South Ridgewood Avenue",
  city_state_zip: "Port Orange, FL 32127-6442",
  phone: "386-322-4500",
  email: "safety@mascigc.com",
  website: "mascigc.com",
};

export function getCompanyInfo() {
  if (typeof window === "undefined") return DEFAULT_COMPANY_INFO;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return DEFAULT_COMPANY_INFO;
    const stored = JSON.parse(raw);
    // Smart merge: a stored field overrides default ONLY if it is a
    // non-empty string. Blank/missing fields fall back to defaults so users
    // who saved with old empty defaults still get the new MASCI values.
    const out = { ...DEFAULT_COMPANY_INFO };
    for (const k of Object.keys(DEFAULT_COMPANY_INFO)) {
      const v = stored?.[k];
      if (typeof v === "string" && v.trim().length > 0) {
        out[k] = v;
      }
    }
    return out;
  } catch {
    return DEFAULT_COMPANY_INFO;
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
