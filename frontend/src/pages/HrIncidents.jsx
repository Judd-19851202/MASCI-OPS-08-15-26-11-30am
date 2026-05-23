// iter353f · HR Incidents List Page.
// Route: /hr/incidents
// Read-only — HR does NOT have closeout authority. Filters by date
// window, severity, status, and free-text search. Surfaces an
// OSHA-relevant summary (total / recordable / open) and supports CSV
// export of the current filtered view.
import React, { useCallback, useEffect, useMemo, useState } from "react";
import axios from "axios";
import { Link, useNavigate } from "react-router-dom";
import {
  ArrowLeft, Download, Search, RefreshCw, AlertTriangle, ShieldCheck, CircleSlash, Home, FileText,
} from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { MasciLogo } from "@/components/MasciLogo";
import { getHrToken } from "@/lib/hrAuth";
import { operationalError } from "@/lib/errors";
import { useT } from "@/lib/i18n";
import { LifecycleGuide } from "@/components/LifecycleGuide";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

function SummaryCard({ icon: Icon, label, value, tint = "slate", testid }) {
  const tints = {
    slate:   "border-slate-300 bg-white text-slate-900",
    amber:   "border-amber-400 bg-amber-50 text-amber-900",
    rose:    "border-rose-400 bg-rose-50 text-rose-900",
    emerald: "border-emerald-400 bg-emerald-50 text-emerald-900",
  };
  return (
    <div className={`border-2 ${tints[tint]} rounded-md p-3`} data-testid={testid}>
      <div className="flex items-center gap-2">
        <Icon className="w-4 h-4 opacity-70" />
        <div className="font-mono text-[10px] uppercase tracking-[0.18em] opacity-70">{label}</div>
      </div>
      <div className="font-display text-2xl font-black mt-1 leading-none">{value}</div>
    </div>
  );
}

export default function HrIncidents() {
  const { t } = useT();
  const nav = useNavigate();
  const [data, setData] = useState({ items: [], count: 0, summary: {} });
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");
  const [q, setQ] = useState("");
  const [days, setDays] = useState("365");
  const [severity, setSeverity] = useState("any");
  const [status, setStatus] = useState("any");

  const params = useMemo(() => {
    const p = { limit: 500, days: parseInt(days, 10) };
    if (q.trim()) p.q = q.trim();
    if (severity !== "any") p.severity = severity;
    if (status !== "any") p.status = status;
    return p;
  }, [q, days, severity, status]);

  const load = useCallback(async () => {
    setLoading(true); setErr("");
    try {
      const r = await axios.get(`${API}/hr/incidents`, {
        headers: { "X-HR-Token": getHrToken() || "" },
        params,
      });
      setData(r.data || { items: [] });
    } catch (e) {
      setErr(operationalError(e, t("Could not load incidents.")));
    } finally {
      setLoading(false);
    }
  }, [params, t]);

  useEffect(() => { load(); }, [load]);

  const exportCsv = () => {
    const rows = data.items || [];
    if (!rows.length) return;
    const headers = ["incident_date", "person_name", "project_name", "incident_type", "severity", "status", "description"];
    const csv = [headers.join(",")].concat(
      rows.map((r) => headers.map((h) => `"${String(r[h] ?? "").replace(/"/g, '""')}"`).join(","))
    ).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = `hr_incidents_${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(a); a.click(); a.remove();
    window.URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center gap-3">
          <Button variant="ghost" size="sm" onClick={() => nav(-1)} data-testid="hr-inc-back">
            <ArrowLeft className="w-4 h-4 mr-1" /> {t("Back")}
          </Button>
          <Link to="/" className="hidden sm:flex items-center gap-2 ml-2">
            <Home className="w-4 h-4 text-slate-400" />
            <MasciLogo size={26} />
          </Link>
          <div className="ml-auto">
            <Button size="sm" onClick={exportCsv} disabled={loading || !data.items?.length} className="bg-purple-700 hover:bg-purple-800 text-white" data-testid="hr-inc-export-csv">
              <Download className="w-4 h-4 mr-1" /> {t("Export CSV")}
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-5 space-y-4">
        <div>
          <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-purple-700 font-bold">{t("HR · OSHA & Labor")}</div>
          <h1 className="font-display text-2xl sm:text-3xl font-black text-slate-900 mt-1">{t("Incidents")}</h1>
          {/* iter367 · legacy intro paragraph replaced by the LifecycleGuide below
              to honor the "one coaching surface per page" directive. */}
        </div>

        {/* iter367 · operational coaching uniformity — short, field-direct. */}
        <LifecycleGuide
          id="hr-incidents"
          icon={AlertTriangle}
          accent="purple"
          title={t("How HR sees incidents")}
          summary={t("Read-only view across the OSHA window. Closeout and CAPA action happen in the Safety portal.")}
          sections={[
            { label: t("Why this matters"), body: t("HR owns OSHA recordkeeping and labor-side accountability. Spotting a recordable here triggers the 300/301 workflow even though the incident itself is owned by Safety.") },
            { label: t("Source of truth"), body: t("Every row links straight to the original Safety incident. If something looks wrong, fix it in Safety — this view aggregates and never edits.") },
          ]}
        />

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3" data-testid="hr-inc-summary">
          <SummaryCard icon={FileText} label={t("In window")} value={data.summary?.total_in_window ?? 0} tint="slate" testid="hr-inc-tile-total" />
          <SummaryCard icon={AlertTriangle} label={t("Recordable")} value={data.summary?.recordable_in_window ?? 0} tint={data.summary?.recordable_in_window ? "rose" : "slate"} testid="hr-inc-tile-recordable" />
          <SummaryCard icon={CircleSlash} label={t("Open")} value={data.summary?.open_in_window ?? 0} tint={data.summary?.open_in_window ? "amber" : "slate"} testid="hr-inc-tile-open" />
          <SummaryCard icon={ShieldCheck} label={t("Shown")} value={data.count ?? 0} tint="slate" testid="hr-inc-tile-shown" />
        </div>

        <div className="bg-white border border-slate-200 rounded-md p-3 grid grid-cols-1 sm:grid-cols-5 gap-2 items-end" data-testid="hr-inc-filters">
          <div className="sm:col-span-2">
            <label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold flex items-center gap-1.5 mb-1">
              <Search className="w-3 h-3" /> {t("Search")}
            </label>
            <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder={t("Person · project · description")} className="h-9 text-sm" data-testid="hr-inc-search" />
          </div>
          <div>
            <label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold mb-1 block">{t("Window")}</label>
            <Select value={days} onValueChange={setDays}>
              <SelectTrigger className="h-9 text-sm" data-testid="hr-inc-window"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="30">{t("30 days")}</SelectItem>
                <SelectItem value="90">{t("90 days")}</SelectItem>
                <SelectItem value="365">{t("1 year (OSHA 300)")}</SelectItem>
                <SelectItem value="1825">{t("5 years")}</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold mb-1 block">{t("Severity")}</label>
            <Select value={severity} onValueChange={setSeverity}>
              <SelectTrigger className="h-9 text-sm" data-testid="hr-inc-severity"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="any">{t("Any")}</SelectItem>
                <SelectItem value="recordable">{t("Recordable")}</SelectItem>
                <SelectItem value="lost_time">{t("Lost time")}</SelectItem>
                <SelectItem value="first_aid">{t("First aid")}</SelectItem>
                <SelectItem value="near_miss">{t("Near miss")}</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold mb-1 block">{t("Status")}</label>
            <Select value={status} onValueChange={setStatus}>
              <SelectTrigger className="h-9 text-sm" data-testid="hr-inc-status"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="any">{t("Any")}</SelectItem>
                <SelectItem value="open">{t("Open")}</SelectItem>
                <SelectItem value="closed">{t("Closed")}</SelectItem>
                <SelectItem value="resolved">{t("Resolved")}</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="sm:col-span-5 flex justify-end">
            <Button variant="outline" size="sm" onClick={load} disabled={loading} data-testid="hr-inc-refresh">
              <RefreshCw className={`w-3.5 h-3.5 mr-1 ${loading ? "animate-spin" : ""}`} /> {t("Refresh")}
            </Button>
          </div>
        </div>

        {err ? (
          <div className="bg-rose-50 border border-rose-300 rounded-md p-3 text-sm text-rose-900" data-testid="hr-inc-error">{err}</div>
        ) : null}

        {!loading && !err && data.items?.length === 0 ? (
          <div className="bg-white border-2 border-dashed border-slate-200 rounded-md p-8 text-center text-sm text-slate-500" data-testid="hr-inc-empty">
            {t("No incidents in this window.")}
          </div>
        ) : null}

        {data.items?.length > 0 ? (
          <div className="bg-white border border-slate-200 rounded-md overflow-x-auto" data-testid="hr-inc-table">
            <table className="w-full text-sm min-w-[900px]">
              <thead className="bg-slate-50">
                <tr className="text-left text-[10px] font-mono uppercase tracking-[0.18em] text-slate-500">
                  <th className="px-3 py-2 w-24">{t("Date")}</th>
                  <th className="px-3 py-2">{t("Person")}</th>
                  <th className="px-3 py-2">{t("Project")}</th>
                  <th className="px-3 py-2 w-32">{t("Severity")}</th>
                  <th className="px-3 py-2 w-32">{t("Status")}</th>
                  <th className="px-3 py-2">{t("Description")}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {data.items.map((r) => (
                  <tr key={r.id} data-testid={`hr-inc-row-${r.id}`}>
                    <td className="px-3 py-2 font-mono text-[11px] text-slate-600 whitespace-nowrap">{r.incident_date || "—"}</td>
                    <td className="px-3 py-2 font-semibold text-slate-900">{r.person_name || "—"}</td>
                    <td className="px-3 py-2 text-slate-600 text-xs">{r.project_name || "—"}</td>
                    <td className="px-3 py-2 text-xs">{r.severity || "—"}</td>
                    <td className="px-3 py-2 text-xs">{r.status || "—"}</td>
                    <td className="px-3 py-2 text-xs text-slate-700 max-w-md truncate" title={r.description || ""}>{r.description || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}

        <div className="text-[11px] text-slate-500 font-mono pt-2 border-t border-slate-200" data-testid="hr-inc-footer">
          {t("Read-only · HR labor / OSHA view · closeout owned by Safety")}
        </div>
      </main>
    </div>
  );
}
