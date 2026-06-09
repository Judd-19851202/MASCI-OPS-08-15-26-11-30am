/**
 * MM-001B · E-1 · MaterialMovementTile
 * Read-only visibility tile fetched from /api/material-movement/daily/...
 * NO authoring · NO editing · NO synchronization.
 * Doctrine: MM_001A_A_EXTERNAL_MATERIAL_MOVEMENT_GAP_AUDIT.md
 */
import React, { useEffect, useState } from "react";
import { Truck, ArrowDownCircle, ArrowUpCircle, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { useT } from "@/lib/i18n";

export default function MaterialMovementTile({ projectNumber, reportDate }) {
  const { t } = useT();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const r = await api.get(`/material-movement/daily/${encodeURIComponent(projectNumber)}/${encodeURIComponent(reportDate)}`);
        if (!cancelled) {
          setData(r.data);
          setLoading(false);
        }
      } catch {
        if (!cancelled) {
          setData(null);
          setLoading(false);
        }
      }
    })();
    return () => { cancelled = true; };
    // eslint-disable-next-line
  }, [projectNumber, reportDate]);

  if (loading) {
    return (
      <section className="bg-white border border-slate-200 rounded-md p-4" data-testid="mm-tile-loading">
        <Loader2 className="w-4 h-4 inline animate-spin mr-2 text-slate-500" />
        <span className="text-xs text-slate-500">{t("Loading material movement…")}</span>
      </section>
    );
  }

  const d = data || { dispatch: { assignments: 0, loads: 0, trucks: 0, by_haul_type: {}, rows: [] }, incoming: [], outgoing: [] };
  const dispatchTotal = d.dispatch?.assignments || 0;
  const incomingTotal = (d.incoming || []).length;
  const outgoingTotal = (d.outgoing || []).length;
  if (dispatchTotal === 0 && incomingTotal === 0 && outgoingTotal === 0) {
    return null;  // Hide empty tile — no haul day shouldn't add visual noise
  }

  return (
    <section className="bg-white border border-slate-200 border-l-4 border-l-indigo-500 rounded-md p-4" data-testid="mm-tile-root">
      <div className="flex items-center gap-2 mb-3">
        <Truck className="w-4 h-4 text-indigo-700" />
        <h2 className="font-mono text-[11px] uppercase tracking-[0.2em] text-indigo-700 font-bold">
          09d · {t("Material Movement Today")}
        </h2>
      </div>

      {/* Dispatch summary */}
      {dispatchTotal > 0 && (
        <div className="mb-3" data-testid="mm-tile-dispatch">
          <div className="text-[10px] font-mono uppercase tracking-wider text-slate-600 font-bold mb-1">
            {t("MASCI Hauling")}
          </div>
          <div className="text-sm text-slate-700">
            {t("Assignments")}: <span className="font-bold">{d.dispatch.assignments}</span> ·{" "}
            {t("Loads")}: <span className="font-bold">{d.dispatch.loads}</span> ·{" "}
            {t("Trucks")}: <span className="font-bold">{d.dispatch.trucks}</span>
          </div>
          {Object.keys(d.dispatch.by_haul_type || {}).length > 0 && (
            <div className="flex flex-wrap gap-1.5 mt-1.5">
              {Object.entries(d.dispatch.by_haul_type).map(([k, v]) => (
                <span key={k} data-testid={`mm-tile-haul-${k}`} className="px-1.5 py-0.5 rounded border border-slate-300 bg-slate-50 text-[10px] font-mono">
                  {k}: {v}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Incoming */}
      {incomingTotal > 0 && (
        <div className="mb-3" data-testid="mm-tile-incoming">
          <div className="text-[10px] font-mono uppercase tracking-wider text-slate-600 font-bold mb-1 flex items-center gap-1">
            <ArrowDownCircle className="w-3 h-3 text-emerald-700" /> {t("Incoming")}
          </div>
          <table className="w-full text-xs border border-slate-200">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-2 py-1 text-left">{t("Material")}</th>
                <th className="px-2 py-1 text-left">{t("Qty")}</th>
                <th className="px-2 py-1 text-left">{t("Unit")}</th>
                <th className="px-2 py-1 text-left">{t("Source")}</th>
              </tr>
            </thead>
            <tbody>
              {d.incoming.map((r, i) => (
                <tr key={i} className="border-t border-slate-100">
                  <td className="px-2 py-1">{r.material}</td>
                  <td className="px-2 py-1">{r.quantity ?? ""}</td>
                  <td className="px-2 py-1">{r.unit}</td>
                  <td className="px-2 py-1">{r.source}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Outgoing */}
      {outgoingTotal > 0 && (
        <div data-testid="mm-tile-outgoing">
          <div className="text-[10px] font-mono uppercase tracking-wider text-slate-600 font-bold mb-1 flex items-center gap-1">
            <ArrowUpCircle className="w-3 h-3 text-rose-700" /> {t("Outgoing")} ({t("from Production")})
          </div>
          <table className="w-full text-xs border border-slate-200">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-2 py-1 text-left">{t("Material")}</th>
                <th className="px-2 py-1 text-left">{t("Qty")}</th>
                <th className="px-2 py-1 text-left">{t("Unit")}</th>
                <th className="px-2 py-1 text-left">{t("Notes")}</th>
              </tr>
            </thead>
            <tbody>
              {d.outgoing.map((r, i) => (
                <tr key={i} className="border-t border-slate-100">
                  <td className="px-2 py-1">{r.material}</td>
                  <td className="px-2 py-1">{r.quantity ?? ""}</td>
                  <td className="px-2 py-1">{r.unit}</td>
                  <td className="px-2 py-1 text-slate-500">{r.station_from}{r.station_to ? ` → ${r.station_to}` : ""}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
