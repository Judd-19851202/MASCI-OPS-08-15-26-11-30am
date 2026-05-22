// SystemHealth.jsx — Iter130. Lightweight admin-only operational
// status panel. Pulls /api/admin/system-health and renders simple
// green/yellow/red status cards. No charts, no analytics, no bloat.
import React, { useEffect, useState } from "react";
import { Activity, RefreshCcw, CheckCircle2, AlertTriangle, XCircle, Loader2 } from "lucide-react";
import AdminShell from "@/components/AdminShell";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { operationalError } from "@/lib/errors";

const STATUS = {
  green:  { cls: "border-emerald-300 bg-emerald-50", chip: "bg-emerald-700", Icon: CheckCircle2, label: "OK" },
  yellow: { cls: "border-amber-300 bg-amber-50",     chip: "bg-amber-600",   Icon: AlertTriangle, label: "WARN" },
  red:    { cls: "border-red-400 bg-red-50",         chip: "bg-red-700",     Icon: XCircle,       label: "FAIL" },
};

export default function SystemHealth() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try { setData((await api.get("/admin/system-health")).data); }
    catch (e) { toast.error(operationalError(e, "Failed to load health")); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);

  const overall = data?.overall || "yellow";
  const ov = STATUS[overall];

  return (
    <AdminShell title="System Health" section="system">
      <div className="max-w-7xl mx-auto" data-testid="admin-system-health-page">
        <div className="bg-white border border-slate-200 rounded-md p-5 mb-4 flex items-start gap-3">
          <div className={`inline-flex items-center justify-center w-12 h-12 rounded-md ${ov.chip} text-white shrink-0`}>
            <Activity className="w-6 h-6" />
          </div>
          <div className="flex-1">
            <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600 font-bold">
              Operational Status · iter130
            </span>
            <h1 className="font-display text-2xl font-black tracking-tight mt-0.5">
              System Health
            </h1>
            <p className="text-sm text-slate-600 mt-1">
              Lightweight operational probe. No analytics — just the things that wake people up.
            </p>
          </div>
          <Button onClick={load} variant="outline" size="sm" disabled={loading} data-testid="health-refresh">
            {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCcw className="w-3.5 h-3.5" />}
          </Button>
        </div>

        {/* Overall banner */}
        <div className={`border-2 ${ov.cls} rounded-md p-4 mb-4 flex items-center gap-3`} data-testid={`health-overall-${overall}`}>
          <ov.Icon className="w-6 h-6" />
          <div>
            <div className="font-mono text-[10px] uppercase tracking-[0.18em] font-bold">Overall</div>
            <div className="font-display text-xl font-black">{ov.label}</div>
          </div>
          <div className="ml-auto text-xs text-slate-600 font-mono">
            Checked {(data?.checked_at || "").slice(0, 16).replace("T", " ")} UTC
          </div>
        </div>

        {loading && !data ? (
          <div className="text-center py-12 text-slate-500"><Loader2 className="w-6 h-6 animate-spin mx-auto" /></div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3" data-testid="health-cards">
            {(data?.cards || []).map((c) => {
              const s = STATUS[c.status] || STATUS.yellow;
              return (
                <div key={c.key} className={`border-2 ${s.cls} rounded-md p-4`} data-testid={`health-card-${c.key}`}>
                  <div className="flex items-center gap-2 mb-1">
                    <s.Icon className="w-4 h-4" />
                    <div className="font-mono text-[10px] uppercase tracking-[0.18em] font-bold">{c.label}</div>
                    <span className={`ml-auto px-1.5 py-0.5 rounded text-[9px] font-mono uppercase tracking-[0.18em] font-bold ${s.chip} text-white`}>
                      {s.label}
                    </span>
                  </div>
                  <div className="text-sm text-slate-800 font-medium leading-snug">{c.detail}</div>
                  {Array.isArray(c.children) && c.children.length > 0 && (
                    <ul className="mt-2 pt-2 border-t border-slate-200 space-y-1">
                      {c.children.map((ch) => (
                        <li key={ch.provider} className="text-xs flex items-center gap-2">
                          <span className={`w-1.5 h-1.5 rounded-full ${STATUS[ch.status]?.chip || "bg-slate-400"}`} />
                          <span className="font-mono uppercase tracking-wide">{ch.provider}</span>
                          <span className="text-slate-600">— {ch.detail}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </AdminShell>
  );
}
