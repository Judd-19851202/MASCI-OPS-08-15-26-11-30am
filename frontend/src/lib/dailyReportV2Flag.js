// DR-ROI-001 · Track B feature flag helper.
// V2 remains OFF by default. Pilot users can opt in via localStorage;
// production kill switch via REACT_APP_DR_V2_ENABLED.
//
// This file has ZERO side effects on the V1 Daily Report code path.

const LS_KEY = "dr_v2_optin";

/** Returns true if the V2 Daily Report should be active for this session. */
export function isDailyReportV2Enabled() {
  try {
    if (typeof window === "undefined") return false;
    if (window.localStorage?.getItem(LS_KEY) === "1") return true;
  } catch (_) {
    /* localStorage unavailable — SSR / private mode */
  }
  const env = (process.env.REACT_APP_DR_V2_ENABLED || "").toLowerCase();
  return env === "1" || env === "true";
}

/** Pilot opt-in (from a settings UI or QA console). */
export function setDailyReportV2OptIn(on) {
  try {
    if (typeof window === "undefined") return;
    if (on) window.localStorage.setItem(LS_KEY, "1");
    else window.localStorage.removeItem(LS_KEY);
  } catch (_) { /* ignore */ }
}
