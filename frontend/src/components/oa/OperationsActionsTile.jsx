/**
 * OA-1 · OperationsActionsTile.jsx
 * Reusable hub entry tile linking into the cross-portal
 * /operations-actions surface. Identical look across all 7 portals.
 */
import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ChevronRight, ClipboardCheck } from "lucide-react";
import { useT } from "@/lib/i18n";
import { oaApi } from "@/lib/oa";

export default function OperationsActionsTile({ className = "" }) {
  const { t } = useT();
  const [summary, setSummary] = useState(null);
  useEffect(() => {
    (async () => {
      try {
        const r = await oaApi.summary();
        setSummary(r.data);
      } catch {
        /* silent — tile still renders */
      }
    })();
  }, []);

  const mine = summary?.mine_open ?? 0;
  const totalOpen = summary?.total_open ?? 0;

  return (
    <Link
      to="/operations-actions"
      data-testid="hub-tile-operations-actions"
      className={`block bg-white border border-slate-200 border-l-4 border-l-indigo-500 hover:shadow-md hover:border-slate-300 rounded-md p-4 transition-all duration-150 relative ${className}`}
    >
      {mine > 0 ? (
        <span
          className="absolute top-3 right-3 inline-flex items-center justify-center min-w-[28px] h-7 px-2 rounded-full bg-rose-600 text-white text-xs font-black border-2 border-white shadow"
          data-testid="hub-tile-oa-mine-badge"
        >
          {mine}
        </span>
      ) : null}
      <div className="flex items-center gap-3">
        <ClipboardCheck className="w-6 h-6 text-indigo-700 shrink-0" />
        <div className="flex-1 min-w-0">
          <p className="font-mono text-[10px] uppercase tracking-[0.22em] text-indigo-700 font-bold">OA-1 · {t("Operations Actions")}</p>
          <h3 className="font-display text-base sm:text-lg font-black tracking-tight text-slate-900 mt-0.5">
            {t("Operations Actions")}
          </h3>
          <p className="text-xs text-slate-600 mt-1">
            {t("Operations Action — operational ownership, not a ticket.")}
            {totalOpen > 0 ? (
              <span className="ml-1 text-slate-700 font-mono">· {totalOpen} {t("Open")}</span>
            ) : null}
          </p>
        </div>
        <ChevronRight className="w-5 h-5 text-slate-400 shrink-0" />
      </div>
    </Link>
  );
}
