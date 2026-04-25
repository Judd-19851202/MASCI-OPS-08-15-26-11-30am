// Company info persisted on the device (localStorage).
// Used on the printed PDF footer and on photo watermarks for legal/insurance filings.

const STORAGE_KEY = "masci.companyInfo.v1";

export const DEFAULT_COMPANY_INFO = {
  company_name: "MASCI",
  tagline: "No Shortcuts · No Exceptions",
  address: "",
  city_state_zip: "",
  phone: "",
  email: "",
  license_number: "",
  website: "",
};

export function getCompanyInfo() {
  if (typeof window === "undefined") return DEFAULT_COMPANY_INFO;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return DEFAULT_COMPANY_INFO;
    return { ...DEFAULT_COMPANY_INFO, ...JSON.parse(raw) };
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
