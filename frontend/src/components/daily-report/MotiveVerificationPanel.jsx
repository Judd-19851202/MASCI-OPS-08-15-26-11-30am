// M-2 · M-2-5 · MOTIVE VERIFICATION read-only section embedded in the
// Daily Report. Visibility only — never authors anything, never edits
// the Daily Report, never auto-fills.
import React, { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Radar, MapPin, Clock } from "lucide-react";

export default function MotiveVerificationPanel({ projectNumber, date }) {
  const [assets, setAssets] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    if (!projectNumber || !date) return;
    (async () => {
      setLoading(true);
      try {
        const r = await api.get(
          `/operational-events/project-day/${encodeURIComponent(projectNumber)}/${encodeURIComponent(date)}`
        );
        if (cancelled) return;
        setAssets(r.data?.assets || []);
      } catch {
        if (!cancelled) setAssets([]);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [projectNumber, date]);

  if (!projectNumber || (!loading && assets.length === 0)) return null;

  return (
    <div
      className="rounded border-2 border-slate-300 bg-white p-3 mb-3"
      data-testid="motive-verification-panel"
    >
      <div className="flex items-center gap-2 mb-2">
        <Radar className="w-4 h-4 text-slate-600" />
        <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-red-700 font-bold">
          Motive Verification
        </div>
        <div className="text-xs text-slate-500">· Read-only · Visibility only</div>
      </div>
      {loading ? (
        <div className="text-xs text-slate-500 px-2 py-1">Loading verification data…</div>
      ) : (
        <div className="space-y-1.5" data-testid="motive-verification-list">
          {assets.map((a) => (
            <div
              key={a.asset_key}
              className="flex items-center justify-between gap-2 px-2 py-1.5 rounded bg-slate-50 border border-slate-200"
              data-testid={`motive-verification-row-${a.asset_key.replace(":", "-")}`}
            >
              <div className="min-w-0">
                <div className="font-bold text-slate-900 truncate flex items-center gap-1.5">
                  <MapPin className="w-3.5 h-3.5 text-slate-400" />
                  {a.asset_label || a.asset_key}
                </div>
                <div className="text-[11px] text-slate-600 font-mono flex items-center gap-2">
                  <span className="px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-900 text-[10px] uppercase tracking-wider font-bold">
                    Detected on site
                  </span>
                  <Clock className="w-3 h-3" />
                  <span>
                    {a.first_seen || "—"} – {a.last_seen || (a.still_on_site ? "still on site" : "—")}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
