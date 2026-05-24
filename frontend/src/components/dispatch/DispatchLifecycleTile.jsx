/**
 * DispatchLifecycleTile.jsx · iter396 · DLS Cross-Portal Convergence.
 *
 * One calm card that surfaces "haul activity that affects the role
 * reading this hub". Same component, three scopes:
 *
 *   <DispatchLifecycleTile scope="pm" projectNumbers={["A","B"]} />
 *      → only findings on the PM's projects
 *
 *   <DispatchLifecycleTile scope="shop" />
 *      → only BREAKDOWN_ACTIVE findings (Shop's high-value signal)
 *
 *   <DispatchLifecycleTile scope="fl" />
 *      → starvation + long-wait signals affecting production
 *
 * Discipline:
 *   • READ ONLY · no edit affordance · no portal escape into Dispatch.
 *   • Reads `/api/dispatch/governance/findings` — the same endpoint the
 *     dispatch board uses. No new API surface.
 *   • Calm by default · only renders if there is operational content.
 *   • Tone-matched to the host hub: PM tile uses PM accent; Shop tile
 *     uses Shop accent; FL tile uses FL accent.
 *
 * The tile NEVER replicates the dispatch board. It is a glanceable
 * signal that something on the role's work is worth knowing about.
 */
import React, { useEffect, useMemo, useState } from "react";
import { Activity, Truck, Wrench, AlertTriangle, Clock } from "lucide-react";
import { useT } from "@/lib/i18n";

const API = process.env.REACT_APP_BACKEND_URL;
const POLL_MS = 60000;                              // calm cadence

/**
 * Build the right `fetch` headers for each role. We attach EVERY
 * portal token we find; the backend uses _require_any_portal_token,
 * so whichever the user actually has becomes the gate.
 */
function buildHeaders() {
  const headers = { "Content-Type": "application/json" };
  const safeRead = (k) => {
    try { return localStorage.getItem(k) || ""; } catch { return ""; }
  };
  const attach = (header, key) => {
    const v = safeRead(key);
    if (v) headers[header] = v;
  };
  attach("X-Admin-Token", "masci.admin.token");
  attach("X-Dispatch-Token", "masci.dispatch.token");
  attach("X-PM-Token", "masci.pm.token");
  attach("X-Shop-Token", "masci.shop.token");
  attach("X-Safety-Token", "masci.safety.token");
  attach("X-HR-Token", "masci.hr.token");
  attach("X-FL-Token", "masci.fl.token");
  return headers;
}

const SCOPE_CONFIG = {
  pm: {
    titleKey: "Haul activity on your projects",
    subKey: "live dispatch signal · project-scoped",
    icon: Truck,
    accent: "border-l-amber-600 text-amber-700",
    iconBg: "bg-amber-600 text-white",
    emptyKey: "No haul activity currently affecting your projects.",
  },
  shop: {
    titleKey: "Trucks in breakdown right now",
    subKey: "operational downtime signal",
    icon: Wrench,
    accent: "border-l-rose-700 text-rose-800",
    iconBg: "bg-rose-700 text-white",
    emptyKey: "No trucks in BREAKDOWN — fleet operating cleanly.",
  },
  fl: {
    titleKey: "Production-impacting haul signals",
    subKey: "starvation + extended wait",
    icon: Clock,
    accent: "border-l-orange-600 text-orange-700",
    iconBg: "bg-orange-600 text-white",
    emptyKey: "No paving-impacting haul signals right now.",
  },
};

function filterFindings(findings, scope) {
  if (!Array.isArray(findings)) return [];
  if (scope === "shop") {
    return findings.filter((f) => f.kind === "BREAKDOWN_ACTIVE");
  }
  if (scope === "fl") {
    return findings.filter(
      (f) =>
        f.kind === "WAIT_THRESHOLD_EXCEEDED" ||
        f.kind === "ASSIGNMENT_STUCK" ||
        f.kind === "BREAKDOWN_ACTIVE",
    );
  }
  // pm → the backend already project-filtered via ?project_numbers=
  return findings;
}

export default function DispatchLifecycleTile({
  scope = "pm",
  projectNumbers = null,
  testId = "dispatch-lifecycle-tile",
}) {
  const { t } = useT();
  const cfg = SCOPE_CONFIG[scope] || SCOPE_CONFIG.pm;
  const [counts, setCounts] = useState({});
  const [findings, setFindings] = useState([]);
  const [loaded, setLoaded] = useState(false);

  const projectsParam = useMemo(() => {
    if (scope !== "pm") return "";
    if (!Array.isArray(projectNumbers) || projectNumbers.length === 0) return "";
    return `?project_numbers=${encodeURIComponent(projectNumbers.join(","))}`;
  }, [scope, projectNumbers]);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const r = await fetch(
          `${API}/api/dispatch/governance/findings${projectsParam}`,
          { headers: buildHeaders() },
        );
        if (!r.ok) {
          if (!cancelled) { setFindings([]); setCounts({}); setLoaded(true); }
          return;
        }
        const j = await r.json().catch(() => ({}));
        if (cancelled) return;
        const filtered = filterFindings(j.findings, scope);
        setFindings(filtered.slice(0, 5));
        setCounts(j.counts || {});
        setLoaded(true);
      } catch {
        if (!cancelled) setLoaded(true);
      }
    };
    load();
    const id = setInterval(load, POLL_MS);
    return () => { cancelled = true; clearInterval(id); };
  }, [scope, projectsParam]);

  // Calm by default — don't render until we have a determinate answer
  // for the role. Hides loading flicker on the host hub.
  if (!loaded) return null;

  const Icon = cfg.icon;
  const headlineCount = findings.length;
  const hasContent = headlineCount > 0;

  return (
    <section
      data-testid={testId}
      className={`bg-white border border-slate-200 border-l-4 ${cfg.accent.split(" ")[0]} rounded-md p-4 sm:p-5`}
    >
      <header className="flex items-start gap-3 flex-wrap">
        <div className={`inline-flex items-center justify-center w-10 h-10 rounded-md ${cfg.iconBg}`}>
          <Icon className="w-5 h-5" />
        </div>
        <div className="flex-1 min-w-[200px]">
          <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500 font-bold">
            {t("Dispatch Lifecycle System")}
          </div>
          <h3 className="font-display text-lg font-black tracking-tight text-slate-900 mt-0.5">
            {t(cfg.titleKey)}
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">{t(cfg.subKey)}</p>
        </div>
        <div className="text-right">
          <div
            className={`font-display text-3xl font-black leading-none ${hasContent ? cfg.accent.split(" ").pop() : "text-slate-400"}`}
            data-testid={`${testId}-count`}
          >
            {headlineCount}
          </div>
          <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 mt-1">
            {headlineCount === 1 ? t("signal") : t("signals")}
          </div>
        </div>
      </header>

      {hasContent ? (
        <ul className="mt-3 divide-y divide-slate-100 border-t border-slate-100" data-testid={`${testId}-list`}>
          {findings.map((f, idx) => (
            <li
              key={`${f.kind}-${f.assignment_id || f.truck_id}-${idx}`}
              className="py-2 flex items-start gap-2 text-sm"
              data-testid={`${testId}-finding-${idx}`}
            >
              <AlertTriangle className={`w-3.5 h-3.5 mt-0.5 shrink-0 ${
                f.severity === "critical" ? "text-rose-700" :
                f.severity === "high"     ? "text-amber-700" :
                                            "text-slate-400"
              }`} />
              <span className="text-slate-800">{f.headline}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-3 text-sm text-slate-500" data-testid={`${testId}-empty`}>
          {t(cfg.emptyKey)}
        </p>
      )}

      <p className="mt-3 text-[11px] text-slate-400 italic flex items-center gap-1">
        <Activity className="w-3 h-3" />
        {t("Read-only · refreshes every minute · dispatch owns these states.")}
      </p>
    </section>
  );
}
