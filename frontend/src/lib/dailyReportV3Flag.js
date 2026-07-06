// TRACK 23.1 · Client-side hook for the V3 UI feature flag.
//
// Doctrine: the flag ONLY controls which shell renders at /daily/new.
// It never affects backend behavior, payload contract, or downstream
// side-effects. Rollback = one flag flip in `ui_flags.dr_v3`.
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

/**
 * @returns {{ enabled: boolean|null, source: string, scope: string, loading: boolean }}
 *   `enabled === null` while loading — callers should preserve the
 *   current UI (typically the V1 shell) until we know.
 */
export function useDailyReportV3Flag({ user = "", project = "" } = {}) {
  const [state, setState] = useState({
    enabled: null,
    source: "loading",
    scope: "loading",
    loading: true,
  });

  useEffect(() => {
    let cancelled = false;
    const params = new URLSearchParams();
    if (user) params.set("user", user);
    if (project) params.set("project", project);

    // Admin URL override — anyone with ?dr_v3=1 in the address bar
    // sees V3. We persist that choice in sessionStorage so subsequent
    // page loads (and reloads) keep V3 without re-typing the param.
    // ?dr_v3=0 explicitly opts back out for that tab.
    const search = new URLSearchParams(window.location.search);
    const urlOverride = search.get("dr_v3");
    try {
      if (urlOverride === "1" || urlOverride === "true") {
        sessionStorage.setItem("dr_v3_admin_override", "1");
      } else if (urlOverride === "0" || urlOverride === "false") {
        sessionStorage.removeItem("dr_v3_admin_override");
      }
    } catch { /* ignore private-mode sessionStorage rejections */ }
    let sessionOverride = null;
    try {
      sessionOverride = sessionStorage.getItem("dr_v3_admin_override");
    } catch { /* ignore */ }
    if (sessionOverride === "1") params.set("force_v3", "1");

    const qs = params.toString();
    const path = "/feature-flags/dr-v3" + (qs ? `?${qs}` : "");
    api
      .get(path)
      .then(({ data }) => {
        if (cancelled) return;
        setState({
          enabled: !!data?.enabled,
          source: data?.source || "unknown",
          scope: data?.scope || "unknown",
          loading: false,
        });
      })
      .catch(() => {
        if (cancelled) return;
        // Fail closed — stick with V1 if the flag endpoint is down.
        setState({ enabled: false, source: "error", scope: "fallback", loading: false });
      });
    return () => {
      cancelled = true;
    };
  }, [user, project]);

  return state;
}
