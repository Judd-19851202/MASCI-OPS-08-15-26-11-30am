// TRACK 25.01 · Admin Operating System (AOS) feature flag.
//
// Phase B rollout gate. `masci.admin.nav.v3` controls whether the new
// consolidated navigation + Executive Home Dashboard renders. Default is
// OFF; enabling it is a per-browser opt-in during preview.
//
// Never gate a critical fix behind this flag. It is UX only.
//
// Sources (highest wins):
//   1. localStorage["masci.admin.nav.v3"] === "on" | "off"
//   2. process.env.REACT_APP_ADMIN_NAV_V3 === "on"
//   3. default: "off"

const FLAG_KEY = "masci.admin.nav.v3";

function readLocal() {
  try {
    return (
      typeof window !== "undefined" && window.localStorage
        ? window.localStorage.getItem(FLAG_KEY)
        : null
    );
  } catch (_e) {
    return null;
  }
}

export function isAdminNavV3Enabled() {
  const ls = readLocal();
  if (ls === "on") return true;
  if (ls === "off") return false;
  const env =
    typeof process !== "undefined" &&
    process.env &&
    process.env.REACT_APP_ADMIN_NAV_V3;
  return env === "on";
}

export function setAdminNavV3(enabled) {
  try {
    if (typeof window !== "undefined" && window.localStorage) {
      window.localStorage.setItem(FLAG_KEY, enabled ? "on" : "off");
    }
  } catch (_e) {
    /* no-op */
  }
}

export const ADMIN_NAV_V3_FLAG_KEY = FLAG_KEY;
