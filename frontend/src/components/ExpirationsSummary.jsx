/**
 * ExpirationsSummary.jsx · Sprint A · DocExp-60/90
 * Universal expiration intelligence panel — reused on HR, Safety,
 * Operations Center, Admin. Pure read-only. Bands match the
 * server-side classifier in /api/operations/expirations/summary.
 */
import React, { useEffect, useState } from "react";
import { Calendar, AlertTriangle, Loader2, RefreshCw } from "lucide-react";
import { api } from "@/lib/api";
import { sanitizeOperatorError, sanitizeOperatorReference } from "@/lib/operatorLanguage";
import { KpiInlineHelp } from "@/components/KpiInlineHelp";

const BAND_PILL = {
  expired: "bg-rose-100 text-rose-900 border-rose-300",
  in_30:   "bg-rose-100 text-rose-900 border-rose-300",
  in_60:   "bg-amber-100 text-amber-900 border-amber-300",
  in_90:   "bg-yellow-100 text-yellow-900 border-yellow-300",
  healthy: "bg-emerald-100 text-emerald-900 border-emerald-300",
};
const BAND_LABEL = {
  expired: "Expired",
  in_30:   "≤30 days",
  in_60:   "≤60 days",
  in_90:   "≤90 days",
  healthy: "Healthy",
};

export default function ExpirationsSummary({ title = "Document Expirations", className = "" }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");
  const [activeBand, setActiveBand] = useState("in_30");

  const load = async () => {
    setLoading(true); setErr("");
    try {
      // TRACK 14.0-PLATFORM-STABILITY · Background widget read; a 401
      // (e.g. PM viewing admin/safety hub without portal token) must
      // not pop the global Session Expired modal. The widget shows
      // its own inline error band instead.
      const r = await api.get("/operations/expirations/summary", { skipSessionStatus: true });
      setData(r.data);
    } catch (e) { setErr(sanitizeOperatorError(e?.response?.data?.detail, "Failed to load expirations")); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);

  if (loading) return (<div className={`bg-white border border-slate-200 rounded-md p-4 ${className}`}><Loader2 className="w-4 h-4 inline animate-spin mr-2" /> Loading expirations…</div>);
  if (err) return (<div className={`bg-rose-50 border-2 border-rose-200 rounded-md p-4 text-sm text-rose-800 ${className}`}><AlertTriangle className="w-4 h-4 inline mr-1" /> {err}</div>);
  if (!data) return null;

  const list = data.bands?.[activeBand] || [];

  return (
    <section className={`bg-white border border-slate-200 border-l-4 border-l-amber-600 rounded-md p-5 ${className}`} data-testid="docexp-panel">
      <div className="flex items-center justify-between gap-3 mb-3 flex-wrap">
        <div className="flex items-center gap-2">
          <Calendar className="w-4 h-4 text-amber-700" />
          <span className="font-mono text-[10px] uppercase tracking-[0.22em] text-amber-700 font-bold">SPRINT A · DOCEXP-60/90</span>
        </div>
        <button onClick={load} className="text-[10px] font-mono uppercase tracking-wider text-slate-500 hover:text-slate-800 inline-flex items-center gap-1" data-testid="docexp-refresh"><RefreshCw className="w-3 h-3" /> Refresh</button>
      </div>
      <div className="mb-3 flex items-center gap-2">
        <h3 className="font-display text-lg font-black tracking-tight text-slate-900">{title}</h3>
        <KpiInlineHelp metadata={data?.kpi_metadata} fallbackLabel={title} testId="docexp-title-help" />
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 mb-4">
        {["expired", "in_30", "in_60", "in_90", "healthy"].map((b) => (
          <button
            key={b}
            type="button"
            onClick={() => setActiveBand(b)}
            data-testid={`docexp-tile-${b}`}
            className={`rounded-md border-2 p-3 text-center transition ${BAND_PILL[b]} ${activeBand === b ? "ring-2 ring-slate-900" : "opacity-90 hover:opacity-100"}`}
          >
            <div className="text-2xl font-black leading-none">{data.counts?.[b] ?? 0}</div>
            <div className="text-[9px] font-mono uppercase tracking-[0.16em] mt-1 font-bold">{BAND_LABEL[b]}</div>
          </button>
        ))}
      </div>

      {list.length > 0 ? (
        <ul className="bg-slate-50 border border-slate-200 rounded-md px-3 py-1 max-h-72 overflow-auto" data-testid={`docexp-list-${activeBand}`}>
          {list.map((d, i) => (
            <li key={`${d.id}-${i}`} className="flex items-center gap-2 py-1.5 border-b border-slate-100 last:border-0 text-xs">
              <span className={`inline-block px-1.5 py-0.5 rounded border text-[10px] font-mono uppercase tracking-wider font-bold ${BAND_PILL[activeBand]}`}>{BAND_LABEL[activeBand]}</span>
              <span className="text-slate-900 truncate flex-1 font-bold">{sanitizeOperatorReference(d.title, "Document record")}</span>
              <span className="text-[10px] text-slate-500 truncate max-w-[200px]">{sanitizeOperatorReference(d.owner_name, "—") || "—"}</span>
              <span className="text-[10px] font-mono text-slate-500 shrink-0">{d.expiration_date || "—"}</span>
            </li>
          ))}
        </ul>
      ) : (
        <div className="text-xs text-slate-500 italic py-2" data-testid={`docexp-empty-${activeBand}`}>No documents in this band.</div>
      )}
    </section>
  );
}
