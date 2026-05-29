import React, { useEffect, useState } from "react";
import { Mail, ChevronDown, ChevronRight, CheckCircle2, AlertCircle } from "lucide-react";
import { api } from "@/lib/api";

export default function AutoEmailRoutingPanel() {
  const [data, setData] = useState(null);
  const [openPm, setOpenPm] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const r = await api.get("/auto-email/routing-table");
        if (alive) setData(r.data);
      } catch {
        /* silently fail — admin sees the standard load state */
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => { alive = false; };
  }, []);

  if (loading || !data) return null;

  const enabled = !!data.auto_email_enabled;

  return (
    <section
      className="bg-white border border-slate-200 rounded-md p-5 sm:p-6 mb-8"
      data-testid="auto-email-routing-panel"
    >
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-3">
          <div className="inline-flex items-center justify-center w-10 h-10 rounded-md bg-slate-900 text-white">
            <Mail className="w-5 h-5" />
          </div>
          <div>
            <h2 className="font-display text-lg sm:text-xl font-black tracking-tight text-slate-900">
              Auto-Email Routing
            </h2>
            <p className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 mt-0.5">
              Who receives each submitted report
            </p>
          </div>
        </div>
        <span
          className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded font-mono text-[10px] uppercase tracking-[0.2em] font-bold ${
            enabled
              ? "bg-emerald-50 text-emerald-700 border border-emerald-300"
              : "bg-amber-50 text-amber-800 border border-amber-300"
          }`}
          data-testid="auto-email-status-badge"
        >
          {enabled ? (
            <><CheckCircle2 className="w-3.5 h-3.5" /> Live — Resend connected</>
          ) : (
            <><AlertCircle className="w-3.5 h-3.5" /> Standby — set RESEND_API_KEY</>
          )}
        </span>
      </div>

      <div className="mt-5 grid grid-cols-1 lg:grid-cols-2 gap-x-8 gap-y-4">
        <div>
          <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 mb-1.5">
            Compliance forms → PM + Office
          </div>
          <p className="text-xs text-slate-600 leading-relaxed mb-1">
            Site Inspections, Safety Meetings, JHPs, Incident Reports.
          </p>
          <ul className="text-sm text-slate-800 space-y-0.5">
            {(data.always_cc || []).map(e => (
              <li key={e} className="font-mono text-xs">+ {e}</li>
            ))}
          </ul>
        </div>
        <div>
          <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 mb-1.5">
            Operational forms → PM only
          </div>
          <p className="text-xs text-slate-600 leading-relaxed mb-1">
            Daily Job Reports, Equipment Pre-Op. PM only — no office CC.
          </p>
          <p className="text-xs text-slate-500 italic">
            Knox McRae (26-06) goes to Jaymn naturally as the assigned PM.
          </p>
        </div>
      </div>

      <div className="mt-5 border-t-2 border-slate-100 pt-4">
        <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 mb-2">
          Project Managers ({(data.project_managers || []).length})
        </div>
        <ul className="space-y-1">
          {(data.project_managers || []).map(pm => {
            const open = openPm === pm.pm_name;
            return (
              <li key={pm.pm_name} className="border border-slate-200 rounded">
                <button
                  type="button"
                  onClick={() => setOpenPm(open ? null : pm.pm_name)}
                  className="w-full flex items-center justify-between gap-3 px-3 py-2 text-left hover:bg-slate-50"
                  data-testid={`pm-row-${pm.pm_name.replace(/\s+/g, "-").toLowerCase()}`}
                >
                  <div className="flex items-center gap-2 min-w-0">
                    {open ? <ChevronDown className="w-4 h-4 text-slate-400 shrink-0" /> : <ChevronRight className="w-4 h-4 text-slate-400 shrink-0" />}
                    <span className="font-bold text-slate-900 truncate">{pm.pm_name}</span>
                    <span className="font-mono text-xs text-slate-500 truncate hidden sm:inline">{pm.pm_email}</span>
                  </div>
                  <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-red-700 font-bold shrink-0">
                    {pm.jobs.length} {pm.jobs.length === 1 ? "job" : "jobs"}
                  </span>
                </button>
                {open && (
                  <ul className="px-3 pb-3 pt-1 space-y-1 bg-slate-50">
                    <li className="font-mono text-xs text-slate-500 sm:hidden mb-1">{pm.pm_email}</li>
                    {pm.jobs.map(j => (
                      <li key={j.project_number} className="flex items-baseline gap-2 text-sm">
                        <span className="font-mono text-xs text-red-700 font-bold w-20 shrink-0">{j.project_number}</span>
                        <span className="text-slate-700 truncate">{j.project_name}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </li>
            );
          })}
        </ul>
      </div>
    </section>
  );
}
