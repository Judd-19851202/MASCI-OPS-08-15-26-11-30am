/**
 * Track 15.68B · Tenant-aware filename helper.
 *
 * Replaces hardcoded `MASCI_${id}.pdf` patterns scattered through the
 * app with `${brandSlug.toUpperCase()}_${id}.pdf`. Reads the slug from
 * sessionStorage (populated by BrandingProvider on first load). MASCI
 * tenant produces `MASCI_*.pdf` filenames; Customer #2 produces e.g.
 * `CUSTOMER_2_CONSTRUCTION_LLC_*.pdf`.
 */
export function brandSlug() {
  if (typeof window === "undefined") return "MASCI";
  try {
    const s = window.sessionStorage.getItem("branding.slug");
    if (!s) return "MASCI";
    return s.toUpperCase();
  } catch {
    return "MASCI";
  }
}

export function brandFilename(...parts) {
  const slug = brandSlug();
  const joined = parts.filter(Boolean).map(String).join("_");
  return `${slug}_${joined}`;
}

// Track 15.68B · companyName helper for "|| MASCI" fallback sweeps.
export function brandCompanyName(defaultName = "Customer") {
  if (typeof window === "undefined") return defaultName;
  try {
    return window.sessionStorage.getItem("branding.companyName") || defaultName;
  } catch {
    return defaultName;
  }
}

export default brandFilename;
