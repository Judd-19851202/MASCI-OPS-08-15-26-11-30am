// IntegrationProbesPanel — Iter142 (Phase-1 Iter D). Renders the
// /api/admin/integrations/health probe roll-up inside Deploy Readiness.
// Color-coded chip per probe with latency, message, and a "Re-run +
// emit alerts" button (admin-gated).
import React, { useCallback, useEffect, useState } from "react";
import {
  CheckCircle2, AlertTriangle, XCircle, PowerOff, Loader2, Radio, Zap,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { toast } from "sonner";

const STATUS = {
  ok:       { Icon: CheckCircle2, dot: "bg-emerald-500", text: "text-emerald-900", chip: "bg-emerald-50 border-emerald-300" },
  degraded: { Icon: AlertTriangle, dot: "bg-amber-500",   text: "text-amber-900",   chip: "bg-amber-50 border-amber-300"   },
  down:     { Icon: XCircle,       dot: "bg-red-600",     text: "text-red-900",     chip: "bg-red-50 border-red-300"       },
  disabled: { Icon: PowerOff,      dot: "bg-slate-400",   text: "text-slate-700",   chip: "bg-slate-50 border-slate-300"   },
};

export default function IntegrationProbesPanel() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [emitting, setEmitting] = useState(false);

  const load = useCallback(async (emit = false) => {
    if (emit) setEmitting(true); else setLoading(true);
    try {
      const r = await api.get(`/admin/integrations/health${emit ? "?emit_alerts=true" : ""}`);
      setData(r.data);
      if (emit) {
        const n = r.data?.alerts_emitted || 0;
        toast.success(n > 0 ? `Emitted ${n} alert${n === 1 ? "" : "s"}` : "No new alerts");
      }
    } catch {
      toast.error("Could not load integration health");
    } finally {
      setLoading(false);
      setEmitting(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  return (
    <div className="bg-white border-2 border-slate-300 rounded-md overflow-hidden" data-testid="integration-probes-panel">
      <div className="bg-slate-50 border-b-2 border-slate-200 px-4 py-2 flex items-center justify-between flex-wrap gap-2">
        <div className="font-mono text-[10px] uppercase tracking-[0.2em] font-bold text-slate-700 flex items-center gap-2">
          <Radio className="w-3.5 h-3.5" /> Live Integration Probes
          {data && (
            <span className={`px-1.5 py-0 rounded text-[9px] font-bold uppercase ${
              data.overall_status === "ok" ? "bg-emerald-100 text-emerald-900"
              : data.overall_status === "degraded" ? "bg-amber-100 text-amber-900"
              : "bg-red-100 text-red-900"
            }`} data-testid="integration-probes-overall">
              {data.overall_status}
            </span>
          )}
        </div>
        <Button
          onClick={() => load(true)}
          disabled={loading || emitting}
          size="sm"
          variant="outline"
          className="border-2 h-8 text-xs"
          data-testid="integration-probes-emit"
        >
          {emitting ? <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" /> : <Zap className="w-3.5 h-3.5 mr-1" />}
          Re-run + Alert
        </Button>
      </div>
      {loading ? (
        <div className="p-6 text-center text-slate-500"><Loader2 className="w-5 h-5 animate-spin mx-auto" /></div>
      ) : !data ? (
        <div className="p-4 text-sm text-slate-500">No probe data.</div>
      ) : (
        <ul className="divide-y divide-slate-100">
          {data.probes.map((p) => {
            const s = STATUS[p.status] || STATUS.disabled;
            const Icon = s.Icon;
            return (
              <li key={p.id} className="px-4 py-3 flex items-center gap-3 flex-wrap" data-testid={`integration-probe-${p.id}`}>
                <Icon className={`w-5 h-5 shrink-0 ${s.text}`} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <div className="font-bold text-sm text-slate-900">{p.name}</div>
                    <span className={`px-1.5 py-0 rounded border text-[9px] uppercase tracking-wider font-mono font-bold ${s.chip} ${s.text}`}>
                      {p.status}
                    </span>
                    {p.mocked && (
                      <span className="px-1.5 py-0 rounded border border-slate-300 bg-slate-50 text-slate-700 text-[9px] uppercase tracking-wider font-mono font-bold">
                        mocked
                      </span>
                    )}
                    {typeof p.latency_ms === "number" && p.latency_ms > 0 && (
                      <span className="text-[10px] font-mono text-slate-500">{p.latency_ms}ms</span>
                    )}
                  </div>
                  <div className="text-xs text-slate-600 mt-0.5 break-words">{p.message}</div>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
