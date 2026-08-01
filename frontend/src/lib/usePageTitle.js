// Sets document.title for the current view and restores the previous
// value on unmount. Track 15.68A: caller passes the suffix (e.g.
// "Admin Guide") and the hook reads the tenant's
// `branding.platform_short_name` from sessionStorage to build the full
// title "Admin Guide · {tenant short}" — never hardcodes "MASCI".

import { useEffect } from "react";

function _tenantSuffix() {
  if (typeof window === "undefined") return "";
  try {
    const tk = window.sessionStorage.getItem("branding.tenantKey") || "masci";
    if (tk === "masci") return "MASCI";
    // Read from a parallel cache populated by BrandingProvider; falls back to "Ops".
    const cached = window.sessionStorage.getItem("branding.shortName");
    return cached || "Ops";
  } catch {
    return "MASCI";
  }
}

export function usePageTitle(title) {
  useEffect(() => {
    if (!title) return;
    const previous = document.title;
    // If the caller embedded the literal "MASCI" suffix, swap it for the
    // active tenant's short brand. Keeps every existing usePageTitle()
    // call site working without modification.
    const suffix = _tenantSuffix();
    const rewritten = title
      .replace(/· MASCI Operations Platform$/, `· ${suffix} Operations Platform`)
      .replace(/· MASCI Hub$/, `· ${suffix} Operations Platform`)
      .replace(/· MASCI$/, `· ${suffix}`)
      .replace(/^MASCI · /, `${suffix} · `)
      .replace(/^MASCI Hub · /, `${suffix} Operations Platform · `)
      .replace(/\bMASCI Hub\b/g, `${suffix} Operations Platform`);
    document.title = rewritten;
    return () => {
      document.title = previous;
    };
  }, [title]);
}

export default usePageTitle;
