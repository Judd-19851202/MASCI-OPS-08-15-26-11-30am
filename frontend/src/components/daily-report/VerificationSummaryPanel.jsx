// VER-1-7 · Verification Summary block on the Daily Report.
// Read-only — never authors anything, never mutates the Daily Report.
import React, { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { ShieldCheck, ShieldAlert, ShieldQuestion, Shield } from "lucide-react";

const BADGE = {
  CONFIRMED:            { Icon: ShieldCheck,    bg: "bg-emerald-50",   border: "border-emerald-400", text: "text-emerald-900", label: "Confirmed" },
  PENDING_CONFIRMATION: { Icon: ShieldQuestion, bg: "bg-amber-50",     border: "border-amber-400",   text: "text-amber-900",   label: "Pending Confirmation" },
  MISMATCH:             { Icon: ShieldAlert,    bg: "bg-red-50",       border: "border-red-300",     text: "text-red-800",     label: "Mismatch" },
  QUIET:                { Icon: Shield,         bg: "bg-slate-50",     border: "border-slate-200",   text: "text-slate-700",   label: "Quiet" },
};

export default function VerificationSummaryPanel({ reportId }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    if (!reportId) return;
    (async () => {
      setLoading(true);
      try {
        const r = await api.get(`/verification/daily-report/${encodeURIComponent(reportId)}`);
        if (cancelled) return;
        setData(r.data);
      } catch {
        if (!cancelled) setData(null);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [reportId]);

  if (!reportId || !data) return null;

  return (
    <div
      className="rounded border-2 border-slate-300 bg-white p-3 mb-3"
      data-testid="verification-summary-panel"
    >
      <div className="flex items-center gap-2 mb-2">
        <ShieldCheck className="w-4 h-4 text-slate-600" />
        <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-red-700 font-bold">
          Verification Status
        </div>
        <div className="text-xs text-slate-500">· Read-only · Operator remains author</div>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2" data-testid="verification-grid">
        {[
          ["equipment",         "Equipment"],
          ["dispatch",          "Dispatch"],
          ["material_movement", "Material Movement"],
          ["project_presence",  "Project Presence"],
        ].map(([key, label]) => {
          const s = (data.subjects || {})[key];
          const b = BADGE[s?.state] || BADGE.QUIET;
          const { Icon } = b;
          return (
            <div
              key={key}
              className={`px-3 py-2 rounded border ${b.bg} ${b.border} ${b.text}`}
              data-testid={`verification-subject-${key}`}
              title={s?.reason || ""}
            >
              <div className="font-mono text-[10px] uppercase tracking-wider opacity-80 flex items-center gap-1">
                <Icon className="w-3 h-3" /> {label}
              </div>
              <div className="text-sm font-black mt-0.5">
                {b.label}
              </div>
            </div>
          );
        })}
      </div>
      {loading && <div className="text-[10px] text-slate-400 mt-2 font-mono">Refreshing…</div>}
    </div>
  );
}
