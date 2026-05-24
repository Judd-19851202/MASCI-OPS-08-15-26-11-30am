/**
 * PmHaulActivityTile.jsx · iter409 · Phase 14.3.
 *
 * Calm production-awareness tile rendered on the PM Hub.
 *
 * Doctrine
 * --------
 *   - Production awareness, NOT dispatch management. PM cannot
 *     issue, reassign, or transition work from this tile.
 *   - Derived from `dispatch_assignments` + `haul_cycles` via
 *     `GET /api/dispatch/haul-activity?project_numbers=...`. Zero
 *     new collection. Zero new write surface.
 *   - Refreshes on a calm cadence (60s). Not a live dispatch board.
 *   - Renders nothing when there is nothing to say. Calm by default.
 */
import React, { useEffect, useMemo, useState } from "react";
import {
  Truck, AlertTriangle, Wrench, Activity, Clock, Package,
} from "lucide-react";
import { useT } from "@/lib/i18n";

const API = process.env.REACT_APP_BACKEND_URL;
const POLL_MS = 60000;

function buildHeaders() {
  const headers = { "Content-Type": "application/json" };
  const read = (k) => {
    try { return localStorage.getItem(k) || ""; } catch { return ""; }
  };
  const attach = (h, k) => {
    const v = read(k);
    if (v) headers[h] = v;
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

export default function PmHaulActivityTile({
  projectNumbers = [],
  testId = "pm-haul-activity-tile",
}) {
  const { t } = useT();
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);

  const qs = useMemo(() => {
    const arr = (projectNumbers || []).filter(Boolean);
    if (!arr.length) return "";
    return `?project_numbers=${encodeURIComponent(arr.join(","))}`;
  }, [projectNumbers]);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const r = await fetch(`${API}/api/dispatch/haul-activity${qs}`, {
          headers: buildHeaders(),
        });
        const j = await r.json().catch(() => null);
        if (!cancelled && j && j.ok) setSummary(j);
      } catch {
        /* silent — tile stays empty */
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    const id = setInterval(load, POLL_MS);
    return () => { cancelled = true; clearInterval(id); };
  }, [qs]);

  // Calm-by-default: only render when there's something to say AND the
  // PM actually has projects in scope. If projectNumbers is empty and
  // tenant-wide reveals zero activity, we still show the empty card so
  // PMs understand the tile exists.
  if (loading) {
    return (
      <div
        className="bg-white border border-slate-200 border-l-4 border-l-amber-600 rounded-md p-5"
        data-testid={`${testId}-loading`}
      >
        <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-amber-700 font-bold">
          {t("Haul activity")} · {t("loading")}…
        </div>
      </div>
    );
  }

  const s = summary || {};
  const totalToday = (s.loads_completed_today || 0)
    + (s.equipment_moves_completed_today || 0);
  const nothingToSay =
    !s.loads_completed_today &&
    !s.active_hauls &&
    !s.equipment_moves_active &&
    !s.equipment_moves_completed_today &&
    !s.waiting_on_plant &&
    !s.waiting_on_dump &&
    !s.breakdown_impacts;

  return (
    <div
      className="bg-white border border-slate-200 border-l-4 border-l-amber-600 rounded-md p-5"
      data-testid={testId}
    >
      <div className="flex items-start gap-3 mb-3">
        <div className="inline-flex items-center justify-center w-10 h-10 rounded-md bg-amber-600 text-white shrink-0">
          <Truck className="w-5 h-5" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-baseline gap-2 flex-wrap">
            <h3 className="font-display text-base sm:text-lg font-black tracking-tight text-slate-900">
              {t("Haul activity on your projects")}
            </h3>
            <span className="px-1.5 py-0.5 border border-slate-200 bg-slate-50 rounded text-[10px] font-mono uppercase tracking-wider text-slate-600">
              {t("production awareness · read-only")}
            </span>
          </div>
          <p className="text-xs text-slate-600 mt-0.5">
            {t("What's moving on your jobs today. PM never operates dispatch — this is glanceable awareness only.")}
          </p>
        </div>
      </div>

      {nothingToSay ? (
        <div
          className="text-sm text-slate-500 italic py-2"
          data-testid={`${testId}-empty`}
        >
          {t("Nothing to report — your jobs are quiet right now.")}
        </div>
      ) : (
        <>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3" data-testid={`${testId}-stats`}>
            <Stat
              icon={Activity}
              label={t("Loads today")}
              value={totalToday}
              tone={totalToday ? "active" : "calm"}
              testId={`${testId}-loads-today`}
              hint={
                s.material_loads_completed_today || s.equipment_moves_completed_today
                  ? `${s.material_loads_completed_today || 0} · ${s.equipment_moves_completed_today || 0} ${t("eq")}`
                  : ""
              }
            />
            <Stat
              icon={Truck}
              label={t("Active hauls")}
              value={s.active_hauls || 0}
              tone={s.active_hauls ? "active" : "calm"}
              testId={`${testId}-active-hauls`}
            />
            <Stat
              icon={Package}
              label={t("Equipment moves")}
              value={s.equipment_moves_active || 0}
              tone={s.equipment_moves_active ? "active" : "calm"}
              testId={`${testId}-equipment-moves`}
              hint={t("inbound + active")}
            />
            <Stat
              icon={Clock}
              label={t("Waiting on plant")}
              value={s.waiting_on_plant || 0}
              tone={s.waiting_on_plant ? "warn" : "calm"}
              testId={`${testId}-wait-plant`}
            />
            <Stat
              icon={Clock}
              label={t("Waiting on site")}
              value={s.waiting_on_dump || 0}
              tone={s.waiting_on_dump ? "warn" : "calm"}
              testId={`${testId}-wait-site`}
            />
            <Stat
              icon={Wrench}
              label={t("Breakdown impacts")}
              value={s.breakdown_impacts || 0}
              tone={s.breakdown_impacts ? "danger" : "calm"}
              testId={`${testId}-breakdown`}
            />
          </div>

          {Array.isArray(s.top_materials) && s.top_materials.length > 0 ? (
            <div className="mt-4 pt-3 border-t border-slate-100" data-testid={`${testId}-materials`}>
              <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold mb-1.5">
                {t("Top materials today")}
              </div>
              <div className="flex flex-wrap gap-1.5">
                {s.top_materials.map((m) => (
                  <span
                    key={m.label}
                    className="inline-flex items-center gap-1 px-2 py-1 rounded-md border border-slate-200 bg-slate-50 text-xs text-slate-800"
                    data-testid={`${testId}-material-chip`}
                  >
                    <span className="font-bold">{m.label}</span>
                    <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500">
                      ×{m.loads}
                    </span>
                  </span>
                ))}
              </div>
            </div>
          ) : null}
        </>
      )}
    </div>
  );
}

function Stat({ icon: Icon, label, value, tone = "calm", hint = "", testId }) {
  const valueCls =
    tone === "danger" ? "text-rose-700"
    : tone === "warn" ? "text-amber-700"
    : tone === "active" ? "text-slate-900"
    : "text-slate-400";
  const labelCls =
    tone === "danger" ? "text-rose-700"
    : tone === "warn" ? "text-amber-700"
    : "text-slate-500";
  return (
    <div data-testid={testId} className="min-h-[64px]">
      <div className={`font-mono text-[10px] uppercase tracking-[0.18em] font-bold flex items-center gap-1 ${labelCls}`}>
        <Icon className="w-3 h-3" /> {label}
      </div>
      <div className={`font-display text-2xl font-black leading-none mt-1 ${valueCls}`}>
        {value}
      </div>
      {hint ? (
        <div className="font-mono text-[9px] uppercase tracking-wider text-slate-400 mt-1">
          {hint}
        </div>
      ) : null}
    </div>
  );
}
